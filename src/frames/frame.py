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

import signal

from collections import deque

from asciimatics.screen import Screen
from asciimatics.widgets.utilities import THEMES
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import ResizeScreenError

from sheets.sheet import Sheet
from dcs.ink import Pen
from geometry.regions import Region
from geometry.points import Point
from frames.commands import find_command
from frames.frame_manager import FrameManager

from logging import getLogger

logger = getLogger(__name__)

class Frame():
    """Represents a TUI application.

    Intermediary between the display (screen) and the widgets.
    Deals with event loop and redrawing damage regions.
    """
    def _resize_handler(self, *_):
        # Could just do a "lay_out_frame" call? Seems unnecessarily
        # wasteful to kill and recreate the Screen.

        # The only thing we need to know from the Screen are the
        # dimensions which are set when the screen is
        # instantiated. Should be able to update those values here and
        # then call "lay_out_frame()" followed by "render()" on the
        # top sheet.
        raise ResizeScreenError("resize!!")

    def __init__(self, screen):
        # override screen resized handler from asciimatics for
        # immediate handling
        screen._signal_state.set(signal.SIGWINCH, self._resize_handler)
        self._dialog = None
        self._focus = None
        self._invalidated_sheets = deque()
        self._menu = None
        self._screen = screen
        self._top_level_sheet = None

    def __repr__(self):
        return "Frame({}x{})".format(self._screen.width, self._screen.height)

    def pen(self, role, state, pen):
        if role not in FrameManager.THEMES:
            logger.info(f"Role entry '{role}' not found. Using role 'undefined'")
            role = "undefined"
        # If desired pen not found in role / state, try to find it in
        # role / default state (and log it).
        #
        # If desired pen not found in role / default state, log it and
        # use role / default / "pen".
        if state not in FrameManager.THEMES[role]:
            logger.info("State entry '%s' not found for role '%s'. Using state 'default'",
                        state, role)
            state = "default"
        if pen not in FrameManager.THEMES[role][state]:
            if state != "default":
                logger.info("Pen type '%s' not found for theme[%s][%s]. "
                            + "Looking in state 'default'",
                            pen, role, state)
                state = "default"
            if pen not in FrameManager.THEMES[role][state]:
                logger.info("Pen type '%s' not found for theme[%s][%s]. Using 'pen'",
                            pen, role, state)
                pen = "pen"
        try:
            return FrameManager.THEMES[role][state][pen]
        except KeyError:
            raise KeyError(f"Failed to find FrameManager.THEMES[{role}][{state}][{pen}]")

    def set_top_level_sheet(self, sheet):
        self._top_level_sheet = sheet
        sheet._frame = self

    def top_level_sheet(self):
        return self._top_level_sheet

    def start_frame(self):
        # If the frame has no focus find one now. FIXME: what if there
        # isn't a suitable focus candidate?

        # Is there any need to pick a focus at all? The user can
        # select one using keyboard navigation, or the app developer
        # can set one if they want. I think there's no need to do
        # this.

#        if self._focus is None:
#            focus_sheet = self._top_level_sheet.find_focus_candidate()
#            self.set_focus(focus_sheet)

        # TODO: test just running this loop, see how quickly the
        # system can respond to mouse and key events. Not sure if
        # latency is in the TUI code and need to find speedups there,
        # or just in the event loop. Wonder if the event loop piece
        # can be done in an async way?
        while True:
            self._screen.wait_for_input(60)
            event = self._screen.get_event()
            self._process_event(event)

    # called to handle events when input events occur; can also be
    # called arbitrarily to redraw invalidated sheets
    def _process_event(self, event=None):
        # are keyboard events handled by the frame and then passed
        # DOWN the sheet hierarchy? Or are they dealt with by the
        # frame and then passed to the focus widget otherwise?
        # What about tabbing between controls?

        # In the interests of keeping it simple; Frame handles
        # accelerators and tab navigation, and passes everything
        # else down to whichever sheet has keyboard focus.
        # QUERY: HOW IS <TAB> HANDLED? - consider text fields +
        # boxes.
        # What to do about mnemonics?
        if isinstance(event, KeyboardEvent):
            self._handle_key_event(event)
        # mouse events go to frontmost sheet under pointer and then
        # travel up the ancestor stack (= down the z-order) until
        # the top sheet is reached or some intermediary sheet elects
        # to handle the event
        if isinstance(event, MouseEvent):
            self._handle_mouse_event(event)

        # FIXME: deal with TUI synthetic events also
        # call_later, button_pressed, those kinds of things. Not
        # sure if want to create a hierarchy of events or to just
        # keep it simple.

        # if event has caused widget to need redrawing, do it now
        self.render_invalidated_sheets()

    def _handle_key_event(self, event):

        logger.debug("_HANDLE_KEY_EVENT entered for frame %s and event %s [keycode %s]",
                     self, event, event.key_code)

        # Handle accelerators from the default "command table". Why
        # don't TAB / S+TAB work here?
        command = find_command(event)
        if command is not None:

            logger.debug("________ got command for %s of %s", self, command)

            if command.apply(self):
                return True

        # fixme: just use the focus widget? What if there isn't one?
        focus_top_level = self._get_focus_top_level()

        logger.debug("________ key event not handled, trying to handle in top level %s",
                     focus_top_level)

        #
        # FIXME: pretty sure logically if a different top level is in
        # play the event should just be sent to that top level and
        # then assumed to be handled. Something like:
        #
        #if focus_top_level != self:
        #    handled = focus_top_level.handle_key_event(event)
        #    logger.debug("________ top level is not frame, returning final result %s",
        #                 handled)
        #    return handled
        #
        # HOWEVER when this code is in place dialogs (for example) are
        # never actually rendered - even though they are registered as
        # the focus_top_level for the frame...
        handled = focus_top_level.handle_key_event(event)
        if handled:

            logger.debug("________ key event handled by %s", focus_top_level)

            return True

        # Ask current frame focus to handle it
        if self.focus() is not None:

            logger.debug("________ key event not handled, sending to frame focus %s",
                         self.focus())

            handled = self.focus().handle_key_event(event)
        # If the key event wasn't handled yet look for the key in the
        # accelerator table and if the active top-level contains the
        # identified widget, activate that widget.
        # Hold accelerators in one of multiple dicts based on
        # top-level sheet.  Can then check exactly the right accels
        # and just activate.
        if not handled:

            logger.debug("________ key event not handled, looking for accelerator")

            if event.key_code > 0:
                key = chr(event.key_code)
                if key.isalpha():
                    if key in self.accelerator_table(focus_top_level):
                        widget = self.accelerator_table(focus_top_level)[key]
                        if widget is not None:
                            if focus_top_level.find_widget(widget) is not None:
                                widget.activate()
                                handled = True
        # Could introduce some extra steps here if handled == False
        # but for now there are none

        logger.debug("________ key event handled at end: %s", handled)

        return handled

    def _handle_mouse_event(self, event):
        # find sheet under mouse, send it the event. Only handles
        # button events.

        # Compose transforms from sheet up to screen and see if mouse
        # event happened in that sheet.

        # If it did and it has children, repeat the process with its
        # children until find the sheet highest in the z-order where
        # the event occurred. Then invoke "mouse_down" or "mouse_up"
        # on the sheet.

        # menu > dialog > default top level

        # Check for clicks over an open menu; if clicks occur outside
        # the bounds of an active menu the menu will be closed;

        # FIXME: do the same with dialogs, but need to add a dialog
        # initarg to indicate this behaviour (wanted for dialogs that
        # are part of comboboxes etc. but perhaps not any other
        # dialogs).

        # If event not handled by a menu and there's a dialog on
        # screen, look in the dialog for the sheet that's going to
        # handle the event;

        # Note: this makes dialogs capture the mouse and become modal,
        # in effect. That's probably ok for a TUI, for now. Might be
        # good to support multiple dialogs in future so a dialog can
        # pop up an alert and so on.

        # If the event is not handled by a menu or a dialog, start at
        # top level sheet (which must contain the event by definition
        # since it takes up the whole of the screen) and search for
        # the highest child that contains the "untransformed"
        # position.

        event_top_level = self._get_focus_top_level()

        sheet = event_top_level.find_highest_sheet_containing_position(Point(event.x, event.y))
        if not sheet and event_top_level == self._menu:
            # Check if event occurred in the (modal) dialog (if there
            # is one) or in the top level sheet otherwise
            # Dispose of menu since there was a click outside it
            self.menu_quit()
        if not sheet and event_top_level == self._dialog \
           and self._dialog._dispose_on_click_outside:
            self.dialog_quit()

        event_top_level = self._get_focus_top_level()

        sheet = event_top_level.find_highest_sheet_containing_position(Point(event.x, event.y))
        if sheet:
            # mouse events come in to the event handler with screen
            # coordinates; convert to the coordinates used by the
            # highest (in z-order) sheet containing that screen
            # position.
            # transform = sheet → screen
            transform = sheet.get_screen_transform()
            # inverse = screen → sheet
            (sx, sy) = transform.inverse().transform_point(Point(event.x, event.y)).xy()
            # if the child declines to deal with the event, pass it
            # back up the widget hierarchy in case a parent wants to
            # do something with the event. This allows some parents to
            # handle all the mouse activity for all of its children
            # (e.g., radio button group)
            if sheet.accepts_focus():
                self.set_focus(sheet)
            sheet.handle_event(MouseEvent(sx, sy, event.buttons))

    def lay_out_frame(self):
        region = Region(0, 0, self._screen.width, self._screen.height)
        self._top_level_sheet.allocate_space(region)
        self._top_level_sheet.layout()

    def show_dialog(self, dialog, coord=None):
        if self._dialog is not None:
            raise RuntimeError("Can't have multiple dialogs currently")
        # Rename this method to "attach_dialog", or "graft_dialog" or
        # similar.
        # When a top-level-sheet has attach(frame) called on it, it
        # recursively calls attach on all its kids (could use an event
        # for this?). When the t-l-s has the frame reference removed,
        # it recursively calls detach on all its kids.
        self._dialog = dialog

        # Allow top level sheets to be grafted / detached from the
        # frame. This allows sheet hierarchies to be shown, hidden
        # then shown again.
        # For now this only works for dialogs, should have proper
        # "graft / detach / attach" methods that work for all top
        # levels, if not for all sheets.
        dialog.attach(self)

        dwidth = self._screen.width // 2
        dheight = self._screen.height // 2

        dialog_spacereq = self._dialog.compose_space()

        # use dialog desired size if it's smaller than
        # the default
        dwidth = min(dialog_spacereq.x_preferred(), dwidth)
        dheight = min(dialog_spacereq.y_preferred(), dheight)

        dialog.allocate_space(Region(0, 0, dwidth, dheight))
        if coord is None:
            dx = (self._screen.width - dwidth) // 2
            dy = (self._screen.height - dheight) // 2
            coord = Point(dx, dy)

        if dialog._widget_focus is None:
            focus_sheet = dialog.find_focus_candidate()
            dialog.set_widget_focus(focus_sheet)

        dialog.move_to(coord)
        dialog.layout()
        # self.render()
        dialog.render()

    def dialog_quit(self):
        if self._dialog is not None:
            # detach will also recursively move all children into a
            # detached state
            self._dialog.detach()
            self._dialog = None
            self.render()

    def show_popup(self, menu, coord):
        if self._menu is not None:
            raise RuntimeError("Can't have multiple menus currently")
        # Rename this method to "attach_dialog", or "graft_dialog" or
        # similar.
        # When a top-level-sheet has attach(frame) called on it, it
        # recursively calls attach on all its kids (could use an event
        # for this?). When the t-l-s has the frame reference removed,
        # it recursively calls detach on all its kids.
        self._menu = menu

        # Allow top level sheets to be grafted / detached from the
        # frame. This allows sheet hierarchies to be shown, hidden
        # then shown again.
        # For now this only works for dialogs, should have proper
        # "graft / detach / attach" methods that work for all top
        # levels, if not for all sheets.
        menu.attach(self)

        dwidth = self._screen.width // 2
        dheight = self._screen.height // 2

        menu_spacereq = self._menu.compose_space()

        # use dialog desired size if it's smaller than
        # the default
        dwidth = min(menu_spacereq.x_preferred(), dwidth)
        dheight = min(menu_spacereq.y_preferred(), dheight)

        menu.allocate_space(Region(0, 0, dwidth, dheight))

        menu.move_to(coord)
        menu.layout()
        menu.render()

    def menu_quit(self):
        if self._menu is not None:
            # detach will also recursively move all children into a
            # detached state
            self._menu.detach()
            self._menu = None
            self.render()

    def render(self):
        self._top_level_sheet.render()
        if self._dialog is not None:
            self._dialog.render()
        if self._menu is not None:
            self._menu.render()
        self._screen.refresh()

    def invalidate(self, sheet):
        if sheet not in self._invalidated_sheets:
            self._invalidated_sheets.append(sheet)

    def render_invalidated_sheets(self):
        while len(self._invalidated_sheets) > 0:
            sheet = self._invalidated_sheets.popleft()
            if not sheet.is_detached():
                sheet.render()
        self._screen.refresh()

    #### focus #########################################################

    def focus(self):
        "Return the sheet that will be sent key events"
        return self._focus

    # updates sheet that will deal with key events
    def set_focus(self, focus):
        if self._focus == focus:
            return
        logger.debug("setting focus to %s", focus)
        if self._focus is not None and not self._focus.is_detached():
            self._focus.note_focus_out()
            self._focus.invalidate()

        self._focus = focus
        if self._focus is not None:
            self._focus.note_focus_in()
            self._focus.invalidate()
        self._process_event()

    def _get_focus_top_level(self):
        focus_top_level = self._top_level_sheet

        # if the popup is owned its owner is responsible for
        # distributing events to it

        if self._dialog is not None and self._dialog.owner() is self:
            focus_top_level = self._dialog
        if self._menu is not None and self._menu.owner() is self:
            focus_top_level = self._menu
        return focus_top_level

    def cycle_focus_forward(self):
        # returns True if the focus was updated and False otherwise
        focus_top_level = self._get_focus_top_level()

        if self._focus is None:
            widget=focus_top_level.find_focus_candidate()
            self.set_focus(widget)
            return True

        # repeat "find_focus_candidate" walk looking for current focus
        # and then continue to next focus candidate - set focus on
        # that candidate and return True. If run out of candidates,
        # retain current focus and return False
        (found, focus_sheet) = focus_top_level.find_next_focus(self._focus)

        if found and focus_sheet is not None:
            self.set_focus(focus_sheet)
            return True
        return False

    def cycle_focus_backward(self):
        logger.debug("cycle_focus_backward entered")
        focus_top_level = self._get_focus_top_level()
        logger.debug("top-level %s", focus_top_level)

        if self._focus is None:
            widget=focus_top_level.find_focus_candidate(from_end=True)
            self.set_focus(widget)
            return True

        # repeat find_focus_candidate walk looking for current focus
        # and then return that last focus candidate seen. If no
        # previous candidates retain current focus and return False
        (found, focus_sheet) = focus_top_level.find_prev_focus(self._focus,
                                                               previous_candidate=None)

        logger.debug("found=%s, new_focus %s", found, focus_sheet)

        if found and focus_sheet is not None:
            self.set_focus(focus_sheet)
            return True

        return False

    #### accelerators ##################################################

    # Accelerators are unique to specific top levels; since top levels
    # are modal only one can be active at a time, so it's fine to
    # duplicate accelerators across top-levels.

    def accelerator_table(self, widget):
        # fixme: could maybe just support case-insensitive
        # accelerators?

        # fixme: if accelerators were displayed next to activatable
        # widget instead of in the label itself, could use
        # accelerators not present in the label. This would allow up
        # to 52 accelerators per top level (assuming case sensitive
        # accelerators).

        # fixme: if number of accelerators is an issue, could also
        # maybe only register accelerators for button groups etc. when
        # the group has focus?
        tls = widget.top_level_sheet()
        return tls._accelerator_to_widget

    def register_accelerator(self, label, widget):
        # don't try to create an accelerator for labels with no alph
        # chars in it. Developer should create a related label that
        # can provide an accelerator instead and display it somewhere
        # in the ui.
        base_set = [x for x in label if x.isalpha()]
        if len(base_set)>0:
            accelerator = self.accelerator_from_label(label, widget.top_level_sheet())
            if accelerator is not None:
                self.accelerator_table(widget)[accelerator] = widget

    def discard_accelerator(self, widget):
        accelerator = self.accelerator_for_widget(widget)
        if accelerator is not None:
            del self.accelerator_table(widget)[accelerator]

    def accelerator_for_widget(self, widget):
        for key, value in self.accelerator_table(widget).items():
            if value == widget:
                return key
        return None

    def accelerator_from_label(self, label, top_level):
        # check first char of words first
        accel_candidates = ""
        for c in [x[0] for x in label.split()]:
            if c.isalpha() and c not in accel_candidates:
                accel_candidates += c

        # add chars from label ignoring non-alpha
        for c in label:
            if c.isalpha() and c not in accel_candidates:
                accel_candidates += c

        for c in accel_candidates:
            if c not in self.accelerator_table(top_level):
                # reserve O and K (in any case) for ok buttons
                if c in "OoKk" and label.casefold() != "ok".casefold():
                    continue
                logger.debug("Found accelerator %s for label %s", c, label)
                return c
        # Is there anything to be done here? Maybe just fail to make
        # an accelerator instead of just failing?
        # raise RuntimeError("Ran out of accelerators for label", label)
        return None
