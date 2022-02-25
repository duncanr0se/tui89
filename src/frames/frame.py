
from collections import deque

from asciimatics.screen import Screen
from asciimatics.widgets.utilities import THEMES
from asciimatics.event import KeyboardEvent, MouseEvent

from sheets.sheet import Sheet
from dcs.ink import Pen
from frames.commands import find_command

from logging import getLogger

logger = getLogger(__name__)

class Frame():

    THEMES = {
        "tv": {
            "background": (Screen.COLOUR_BLUE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "shadow": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "scroll": (Screen.COLOUR_CYAN, Screen.A_REVERSE, Screen.COLOUR_BLUE),
            "button": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_GREEN),
            "pushed_button": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_RED),
            "menubar": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE),
            "alert": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_RED),
            "info": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_CYAN),
            "yes/no": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_GREEN),
            "composite": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE),

            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "invalid": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "borders": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "edit_text": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
            "readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "focus_readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_CYAN),
            "focus_button": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_GREEN),
            "control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "selected_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "focus_control": (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "selected_focus_control": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN),
            "field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "selected_field": (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "focus_field": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "selected_focus_field": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
        }
    }

    #_screen = None
    #_top_level_sheet = None
    #_dialog = None
    #_invalidated = None
    #_menu = None

    def __init__(self, screen):
        self._delayed_calls = []
        self._dialog = None
        self._focus = None
        self._invalidated_sheets = deque()
        self._menu = None
        self._screen = screen
        self._top_level_sheet = None

    def __repr__(self):
        (width, height) = self._region
        return "Frame({}x{})".format(width, height)

    def default_pen(self):
        return self.theme("borders")

    def set_top_level_sheet(self, sheet):
        self._top_level_sheet = sheet
        sheet._frame = self

    def top_level_sheet(self):
        return self._top_level_sheet

    def theme(self, ink_name):
        (fg, attr, bg) = Frame.THEMES["tv"][ink_name]
        return Pen(fg=fg, attr=attr, bg=bg)

    def start_frame(self):
        # TODO: test just running this loop, see how quickly the
        # system can respond to mouse and key events. Not sure if
        # latency is in the TUI code and need to find speedups there,
        # or just in the event loop. Wonder if the event loop piece
        # can be done in an async way?
        while True:
            self._screen.wait_for_input(60)
            event = self._screen.get_event()
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

    def focus(self):
        return self._focus

    def set_focus(self, focus):
        logger.debug("setting focus to %s", focus)
        self._focus = focus
        focus.set_focus()

    # FIXME: handling focus better
    def _handle_key_event(self, event):
        # Handle accelerators from the "command table"
        # Who handles navigation? The frame or the sheets?

        command = find_command(event)
        if command is not None:
            if command.apply(self):
                return True

        # Do what if there is no focus?
        if self.focus() is None:
            # Pass event to top level sheet to pass down the sheet
            # hierarchy (start at bottom of z-order). Layouts can deal
            # with keyboard navigation if appropriate before passing
            # finally to leaf sheet.

            # Set the focus to the highest priority top level
            # sheet. When it is asked to deal with an event it can
            # identify a more specific focus, if it is coded to.
            if self._menu:
                self.set_focus(self._menu)
            elif self._dialog:
                self.set_focus(self._dialog)
            else:
                self.set_focus(self._top_level_sheet)

        # When a top level sheet, a dialog, or a menu is displayed it
        # takes control of the current focus. When a menu or dialog is
        # closed, the frame focus is cleared and the branch above is
        # entered so the next highest priority focus can be selected.
        handled = self.focus().accept_key_event(event)
        # Could introduce some extra steps here if handled == False
        # but for now there are none
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

        # TODO: better handling of top level sheets would simplify
        # this mess.
        event_top_level = None
        if self._menu is not None:
            event_top_level = self._menu
        if event_top_level is None and self._dialog is not None:
            event_top_level = self._dialog
        if event_top_level is None:
            event_top_level = self._top_level_sheet

        sheet = event_top_level.find_highest_sheet_containing_position((event.x, event.y))
        if not sheet and event_top_level == self._menu:
            # Check if event occurred in the (modal) dialog (if there
            # is one) or in the top level sheet otherwise
            # Dispose of menu since there was a click outside it
            self.menu_quit()
            if self._dialog is not None:
                event_top_level = self._dialog
            else:
                event_top_level = self._top_level_sheet
            sheet = event_top_level.find_highest_sheet_containing_position((event.x, event.y))
        if sheet:
            transform = sheet.get_screen_transform()
            (sx, sy) = transform.inverse().apply((event.x, event.y))
            # if the child declines to deal with the event, pass it
            # back up the widget hierarchy in case a parent wants to
            # do something with the event. This allows some parents to
            # handle all the mouse activity for all of its children.
            sheet.handle_event(MouseEvent(sx, sy, event.buttons))

    def lay_out_frame(self):
        self._top_level_sheet.allocate_space((self._screen.width, self._screen.height))
        self._top_level_sheet.layout()

    def show_dialog(self, dialog):
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

        dialog.allocate_space((dwidth, dheight))
        dx = (self._screen.width - dwidth) // 2
        dy = (self._screen.height - dheight) // 2

        dialog.move_to((dx, dy))
        dialog.layout()
        self._focus = None
        self.render()

    def dialog_quit(self):
        if self._dialog is not None:
            # detach will also recursively move all children into a
            # detached state
            self._dialog.detach()
            self._dialog = None
            self._focus = None
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

        menu.allocate_space((dwidth, dheight))

        menu.move_to(coord)
        menu.layout()
        self._focus = None
        self.render()

    def menu_quit(self):
        if self._menu is not None:
            # detach will also recursively move all children into a
            # detached state
            self._menu.detach()
            self._menu = None
            self._focus = None
            self.render()

    def render(self):
        # clear the screen first? Might be flickery... read the docs,
        # work out how to do this.
        self._top_level_sheet.render()
        if self._dialog is not None:
            self._dialog.render()
        if self._menu is not None:
            self._menu.render()
        self._screen.refresh()

    def invalidate(self, sheet):
        self._invalidated_sheets.append(sheet)

    def render_invalidated_sheets(self):
        while len(self._invalidated_sheets) > 0:
            sheet = self._invalidated_sheets.popleft()
            if not sheet.is_detached():
                sheet.render()
        self._screen.refresh()
