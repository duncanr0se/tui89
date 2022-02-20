
from collections import deque

from asciimatics.screen import Screen
from asciimatics.widgets.utilities import THEMES
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import StopApplication

from sheets.sheet import Sheet
from dcs.ink import Pen

from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqDesired

# should the frame be a sheet? Hrm.
class Frame():

    _screen = None
    _top_level_sheet = None
    _dialog = None
    _invalidated = None

    def __init__(self, screen):
        self._screen = screen

        THEMES["tv"] = {
            "background": (Screen.COLOUR_BLUE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "shadow": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "scroll": (Screen.COLOUR_CYAN, Screen.A_REVERSE, Screen.COLOUR_BLUE),
            "button": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_GREEN),

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
        self._invalidated = deque()

    def __repr__(self):
        (width, height) = self._region
        return "Frame({}x{})".format(width, height)

    def set_top_level_sheet(self, sheet):
        self._top_level_sheet = sheet
        sheet._frame = self
        sheet._default_pen = self.theme("borders")

    def top_level_sheet(self):
        return self._top_level_sheet

    def theme(self, ink_name):
        (fg, attr, bg) = THEMES["tv"][ink_name]
        return Pen(fg=fg, attr=attr, bg=bg)

    def start_frame(self):
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

            # if event has caused widget to need redrawing, do it now
            self.render_invalidated()

    def _handle_key_event(self, event):
        if event.key_code > 0:
            if chr(event.key_code) in ('Q', 'q'):
                raise StopApplication("User quit")
        else:
            if event.key_code == Screen.KEY_ESCAPE:
                self.dialog_quit()

    def _handle_mouse_event(self, event):
        # find sheet under mouse, send it the event

        # Need to compose transforms from sheet up to screen and see
        # if mouse event happened in that sheet.

        # If it did and it has children, see repeat the process with
        # its children until find the sheet highest in the z-order
        # where the event occurred. Then invoke "mouse_down" or
        # "mouse_up" on the sheet. Also - need timestamp for event.

        # How about handling mouse move for highlighting? Perhaps
        # don't handle the mouse at all? Should be fine for setting
        # focus and clicking widgets, so just do that.

        # Just (very) rudimentary mouse handling, this is supposed to
        # be a keyboard-driven ui toolkit...

        # start at top level sheet which must contain the event by
        # definition since it takes up the whole of the screen. Ask it
        # for the highest child it knows of that contains the
        # "untransformed" position.
        # If there's a dialog on screen, look in the dialog for the
        # sheet that's going to handle the event; otherwise look in
        # the top level sheet.
        # Note: this makes dialogs capture the mouse and become modal,
        # in effect. That's probably ok for a TUI, for now. Might be
        # good to support multiple dialogs in future so a dialog can
        # pop up an alert and so on.
        event_top_level = self._dialog if self._dialog is not None else self._top_level_sheet

        # this is failing to find the button in the dialog; because
        # the dialog doesn't have sensible 'children', it instead has
        # the 'layout' slot. Would likely be easier to make dialog
        # a frame... carry on this way for now.

        sheet = event_top_level.find_highest_sheet_containing_position((event.x, event.y))
        if sheet:
            # fixme: rename to "convert_to_screen_coordinate"?
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

        # if dialog becomes a frame, move defaults into frame
        dialog._default_pen = self.theme("invalid")

        dwidth = self._screen.width // 2
        dheight = self._screen.height // 2

        dialog_spacereq = self._dialog.compose_space()

        # use dialog desired size if it's smaller than
        # the default
        dwidth = min(xSpaceReqDesired(dialog_spacereq), dwidth)
        dheight = min(ySpaceReqDesired(dialog_spacereq), dheight)

        dialog.allocate_space((dwidth, dheight))
        dx = (self._screen.width - dwidth) // 2
        dy = (self._screen.height - dheight) // 2

        dialog.move_to((dx, dy))
        dialog.layout()
        self.render()

    def dialog_quit(self):
        if self._dialog is not None:
            # detach will also recursively move all children into a
            # detached state
            self._dialog.detach()
            self._dialog = None
            self.render()

    def render(self):
        # clear the screen first? Might be flickery... read the docs,
        # work out how to do this.
        self._top_level_sheet.render()
        if self._dialog is not None:
            self._dialog.render()
        self._screen.refresh()

    def invalidate(self, sheet):
        self._invalidated.append(sheet)

    def render_invalidated(self):
        while len(self._invalidated) > 0:
            sheet = self._invalidated.popleft()
            if not sheet.is_detached():
                sheet.render()
        self._screen.refresh()
