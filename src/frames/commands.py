#
# Copyright 2022 Duncan Rose
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication

from logging import getLogger

logger = getLogger(__name__)

# keycode :: Command object map
# Commands the frame deals with go in this map

# TODO: need to be able to find keys for accelerators for commands to
# show in menus and on buttons etc. For now, the different top level
# sheets are responsible for doing this. (won't be efficient!)
COMMANDS = {}


class Command():

    def __init__(self, name, func):
        self._func = func
        self._name = name

    def __repr__(self):
        return "Command('{}')".format(self._name)

    def apply(self, client):
        dclient = "None" if client is None else client
        logger.debug("applying command %s with client %s", self, dclient)
        return self._func(client)


def register_command(keys, command, command_table="global"):
    if not command_table in COMMANDS:
        COMMANDS[command_table] = {}
    for key in keys:
        # FIXME: check if key is already bound
        # FIXME: deal with "C-x C-c" type commands?
        COMMANDS[command_table][key] = command

def find_command(key_event, command_table="global"):
    cmd = None
    if key_event.key_code:
        try:
            cmd = COMMANDS[command_table][key_event.key_code]
        except KeyError:
            pass
    return cmd


### Commands on Frame
def populate_global():
    #### global commands

    # QUIT / EXIT
    def _quit_command(client):
        raise StopApplication("quit")

    keycode = Screen.ctrl('w')
    register_command([keycode], Command("quit", _quit_command))

    # NEXT FOCUS
    def _find_next_focus(client):
        focus_updated = client.cycle_focus_forward()
        return True

    keycode = Screen.KEY_TAB
    register_command([keycode], Command("next focus", _find_next_focus))

    # PREV FOCUS
    def _find_prev_focus(client):
        focus_updated = client.cycle_focus_backward()
        return True

    keycode = Screen.KEY_BACK_TAB
    register_command([keycode], Command("previous focus", _find_prev_focus))


### Commands on menuboxes (popup menus)
def populate_menubox():
    #### generic menubox commands; specific menus could set up
    #### command tables of their own, but do not currently.

    # ESC - exit menu
    def _close(menubox):
        menubox.frame().menu_quit()
        return True

    keycode = [Screen.KEY_ESCAPE]
    register_command(keycode, Command("close popup", _close), command_table="menubox")

    # CTRL-P, UP-ARROW - up item
    def _prev(menubox):
        selected = menubox.find_focused_child()
        if selected is not None:
            if menubox.cycle_focus_backward(selected):
                return True
#        if menubox.has_menubar_button():
#            # FIXME: close self, select menubar button
#            return True
        return False

    keycode = [Screen.ctrl("p"), Screen.KEY_UP]
    register_command(keycode, Command("previous", _prev), command_table="menubox")

    # CTRL-N, DOWN-ARROW - down item
    def _next(menubox):
        selected = menubox.find_focused_child()
        if selected is None:
            return menubox.focus_first_child()
        else:
            return menubox.cycle_focus_forward(selected)

    keycode = [Screen.ctrl("n"), Screen.KEY_DOWN]
    register_command(keycode, Command("next", _next), command_table="menubox")

    # FIXME: KEY_LEFT and KEY_RIGHT should select prev and next menu
    # items if menubox is shown from a menubar. Also KEY_UP should
    # close the menu and put the focus back to the menubar in this
    # case.

### Commands on dialogs
def populate_dialog():
    # ESC - exit menu
    def _close(dialog):
        dialog.frame().dialog_quit()
        return True

    keycode = [Screen.KEY_ESCAPE]
    register_command(keycode, Command("close dialog", _close), command_table="dialog")

    # the on_click_callback for dialog buttons needs to return the
    # dialog values where necessary, or the caller (creator of the
    # dialog) needs to keep a reference to the dialog so any contained
    # values can be recovered


### Commands on buttons
def populate_button():
    # FIXME: if parents delegated (found a focus) for events then
    # dialogs or menuboxes (or menubars) could end up in here without
    # any special logic. And that's the way it should be - containers
    # need to find a focus widget and then events need to bubble up to
    # the parents into the top-level-sheet and finally into the frame
    # where it is then *not* handled (frame had opportunity to handle
    # first - maybe should have frame pre- and post- handlers?)

    # FIXME: when event handling process is properly tied down, move
    # these command tables into the widgets they are acting upon.
    def _activate(button):
        button.activate()
        return True

    keycode = [ord(" "),  Screen.ctrl("j")]
    register_command(keycode, Command("activate", _activate), command_table="button")


### Commands on menubars
def populate_menubar():
    # CTRL-K, LEFT-ARROW - previous item
    def _prev(menubar):
        selected = menubar.find_focused_child()
        if selected is not None:
            return menubar.cycle_focus_backward(selected)
        return False

    keycode = [Screen.ctrl("k"), Screen.KEY_LEFT]
    register_command(keycode, Command("previous", _prev), command_table="menubar")

    # CTRL-L, RIGHT-ARROW - next item
    def _next(menubar):
        selected = menubar.find_focused_child()
        if selected is None:
            return menubar.focus_first_child()
        else:
            return menubar.cycle_focus_forward(selected)

    keycode = [Screen.ctrl("l"), Screen.KEY_RIGHT]
    register_command(keycode, Command("next", _next), command_table="menubar")

    # CTRL-N, DOWN-ARROW - open item
    # FIXME: need to support going up from the menubox back into the
    # menubar also...
    def _activate(menubar):
        button = menubar.find_focused_child()
        if button is not None:
            button.activate()
            return True
        return False

    keycode = [Screen.ctrl("n"), Screen.KEY_DOWN]
    register_command(keycode, Command("open", _activate), command_table="menubar")

# FIXME: "select previous" on menubox should select menubar containing
# button that spawned menu box in the first place, if there is
# one. Need to capture the menubar in the menubox state since the
# menubar isn't actually a parent of the menubox.

### Commands on text entry boxes
def populate_textentry():
    # CTRL-A, HOME - start of line
    def _start_of_line(entry):
        return entry.move_start()
    keycode = [Screen.KEY_HOME, Screen.ctrl("a")]
    register_command(keycode, Command("move start", _start_of_line), command_table="textentry")

    # CTRL-E, END - end of line
    def _end_of_line(entry):
        return entry.move_end()
    keycode = [Screen.KEY_END, Screen.ctrl("e")]
    register_command(keycode, Command("move end", _end_of_line), command_table="textentry")

    # CTRL-F, KEY_RIGHT - forward 1 char
    def _forward(entry):
        return entry.move_forward()
    keycode = [Screen.KEY_RIGHT, Screen.ctrl("f")]
    register_command(keycode, Command("forward", _forward), command_table="textentry")

    # CTRL-B, KEY_LEFT - backward 1 char
    def _backward(entry):
        return entry.move_backward()
    keycode = [Screen.KEY_LEFT, Screen.ctrl("b")]
    register_command(keycode, Command("backward", _backward), command_table="textentry")

    # CTRL-D, DELETE - delete forward
    def _delete(entry):
        return entry.delete()
    keycode = [Screen.ctrl("d"), Screen.KEY_DELETE]
    register_command(keycode, Command("delete", _delete), command_table="textentry")

    # BACKSPACE - delete backward
    def _backspace(entry):
        return entry.backspace()
    keycode = Screen.KEY_BACK
    register_command([keycode], Command("backspace", _backspace), command_table="textentry")

    # NEWLINE - silently ignore
    def _nop(entry):
        return True
    keycode = Screen.ctrl("j")
    register_command([keycode], Command("eat nl", _nop), command_table="textentry")

    # NEXT FOCUS
    def _find_next_focus(entry):
        focus_updated = entry.frame().cycle_focus_forward()
        return True

    keycode = Screen.KEY_ESCAPE
    register_command([keycode], Command("next focus", _find_next_focus),
                     command_table="textentry")

    # PRINTING CHAR - insert char; implemented in widget itself
    pass


# FIXME: textarea + textentry command tables are almost
# identical. Implement command table inheritance to reduce
# duplication.

### Commands on text entry boxes
def populate_textarea():
    # CTRL-A, HOME - start of line
    def _start_of_line(entry):
        return entry.move_start()
    keycode = [Screen.KEY_HOME, Screen.ctrl("a")]
    register_command(keycode, Command("move start", _start_of_line), command_table="textarea")

    # CTRL-E, END - end of line
    def _end_of_line(entry):
        return entry.move_end()
    keycode = [Screen.KEY_END, Screen.ctrl("e")]
    register_command(keycode, Command("move end", _end_of_line), command_table="textarea")

    # CTRL-F, KEY_RIGHT - forward 1 char
    def _forward(entry):
        return entry.move_forward()
    keycode = [Screen.KEY_RIGHT, Screen.ctrl("f")]
    register_command(keycode, Command("forward", _forward), command_table="textarea")

    # CTRL-B, KEY_LEFT - backward 1 char
    def _backward(entry):
        return entry.move_backward()
    keycode = [Screen.KEY_LEFT, Screen.ctrl("b")]
    register_command(keycode, Command("backward", _backward), command_table="textarea")

    # CTRL-N, KEY_DOWN - down 1 line
    def _down(entry):
        return entry.move_down()
    keycode = [Screen.KEY_DOWN, Screen.ctrl("n")]
    register_command(keycode, Command("down", _down), command_table="textarea")

    # PG_DN - down 1 page
    def _page_down(entry):
        return entry.page_down()
    keycode = [Screen.KEY_PAGE_DOWN]
    register_command(keycode, Command("page down", _page_down), command_table="textarea")

    # CTRL-P, KEY_UP - up 1 line
    def _up(entry):
        return entry.move_up()
    keycode = [Screen.KEY_UP, Screen.ctrl("p")]
    register_command(keycode, Command("up", _up), command_table="textarea")

    # PG_UP - up 1 page
    def _page_up(entry):
        return entry.page_up()
    keycode = [Screen.KEY_PAGE_UP]
    register_command(keycode, Command("page up", _page_up), command_table="textarea")

    # CTRL-D, DELETE - delete forward
    def _delete(entry):
        return entry.delete()
    keycode = [Screen.ctrl("d"), Screen.KEY_DELETE]
    register_command(keycode, Command("delete", _delete), command_table="textarea")

    # BACKSPACE - delete backward
    def _backspace(entry):
        return entry.backspace()
    keycode = Screen.KEY_BACK
    register_command([keycode], Command("backspace", _backspace), command_table="textarea")

    # NEWLINE - silently ignore
    def _open_below(entry):
        return entry.open_below()
    keycode = Screen.ctrl("j")
    register_command([keycode], Command("open below", _open_below), command_table="textarea")

    # NEXT FOCUS
    def _find_next_focus(entry):
        focus_updated = entry.frame().cycle_focus_forward()
        return True

    keycode = Screen.KEY_ESCAPE
    register_command([keycode], Command("next focus", _find_next_focus),
                     command_table="textarea")

    # PRINTING CHAR - insert char; implemented in widget itself
    pass

### Commands on option boxes
def populate_optionbox():

    def _activate(optionbox):
        optionbox.activate()
        return True

    keycode = [ord(" "),  Screen.ctrl("j"), Screen.KEY_DOWN]
    register_command(keycode, Command("activate", _activate), command_table="optionbox")

#
# actually populate the command tables.
#
populate_global()
populate_menubox()
populate_dialog()
populate_button()
populate_menubar()
populate_textentry()
populate_textarea()
populate_optionbox()

# when a new TOP LEVEL SHEET type is displayed, it needs to identify
# the FOCUS WIDGET. Until that TOP LEVEL SHEET is closed (or
# superceded), the TOP LEVEL SHEET is responsible for event handling
# within it.

# in general the TOP LEVEL SHEET finds a layout widget and selects the
# highest z-order child or that widget to take the focus. If keyboard
# events that widget does not handle are received, the events bubble
# up the sheet's parent hierarchy (down the z-order) until a sheet is
# found to handle the event, or the top-level sheet is reached. If the
# top-level sheet elects not to handle the event, the event is
# returned to the Frame as unhandled.

# "find_focus_candidate" -> perform depth-first search to find first
# child with no children, set it as the focus.

# FIXME: focus colour scheme; make focused items display with magenta
# backgrounds since magenta isn't used for anything else.
