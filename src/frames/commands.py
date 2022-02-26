
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
        focus_updated = client._select_next_focus()
        return True

    keycode = Screen.KEY_TAB
    register_command([keycode], Command("next focus", _find_next_focus))

    # PREV FOCUS
    def _find_prev_focus(client):
        focus_updated = client._select_prev_focus()
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
        selected = menubox._find_selected()
        if selected is not None:
            return menubox._select_previous(selected)
        return False

    keycode = [Screen.ctrl("p"), Screen.KEY_UP]
    register_command(keycode, Command("previous", _prev), command_table="menubox")

    # CTRL-N, DOWN-ARROW - down item
    def _next(menubox):
        selected = menubox._find_selected()
        if selected is None:
            return menubox._select_first()
        else:
            return menubox._select_next(selected)

    keycode = [Screen.ctrl("n"), Screen.KEY_DOWN]
    register_command(keycode, Command("next", _next), command_table="menubox")


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
        selected = menubar._find_selected()
        if selected is not None:
            return menubar._select_previous(selected)
        return False

    keycode = [Screen.ctrl("k"), Screen.KEY_LEFT]
    register_command(keycode, Command("previous", _prev), command_table="menubar")

    # CTRL-L, RIGHT-ARROW - next item
    def _next(menubar):
        selected = menubar._find_selected()
        if selected is None:
            return menubar._select_first()
        else:
            return menubar._select_next(selected)

    keycode = [Screen.ctrl("l"), Screen.KEY_RIGHT]
    register_command(keycode, Command("next", _next), command_table="menubar")

# FIXME: "select previous" on menubox should select menubar containing
# button that spawned menu box in the first place, if there is
# one. Need to capture the menubar in the menubox state since the
# menubar isn't actually a parent of the menubox.

#
# actually populate the command tables.
#
populate_global()
populate_menubox()
populate_dialog()
populate_button()
populate_menubar()

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

# "find_focus" -> perform depth-first search to find first child with
# no children, set it as the focus.

# FIXME: focus colour scheme; make focused items display with magenta
# backgrounds since magenta isn't used for anything else.
