
from asciimatics.screen import Screen
from asciimatics.widgets.utilities import THEMES
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import StopApplication

from sheets.sheet import Sheet
from dcs.ink import Pen

# should the frame be a sheet? Hrm.
class Frame():

    _screen = None
    _top_level_sheet = None
    _dialog = None

    def __init__(self, screen):
        self._screen = screen

        THEMES["tv"] = {
            "background": (Screen.COLOUR_BLUE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "shadow": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "disabled": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "invalid": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_RED),
            "label": (Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "borders": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "scroll": (Screen.COLOUR_CYAN, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "title": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "edit_text": (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE),
            "focus_edit_text": (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN),
            "readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_BLUE),
            "focus_readonly": (Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_CYAN),
            "button": (Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_GREEN),
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

    def __repr__(self):
        (width, height) = self._region
        return "Frame({}x{})".format(width, height)

    def set_top_level_sheet(self, sheet):
        self._top_level_sheet = sheet
        sheet._frame = self

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
        sheet = self._top_level_sheet.find_highest_sheet_containing_position((event.x, event.y))
        if sheet:
            # fixme: rename to "convert_to_screen_coordinate"?
            transform = sheet.get_screen_transform()
            (sx, sy) = transform.inverse().apply((event.x, event.y))
            # if the child declines to deal with the event, pass it
            # back up the widget hierarchy in case a parent wants to
            # do something with the event. This allows some parents to
            # handle all the mouse activity for all of its children.
            sheet.handle_event(MouseEvent(sx, sy, event.buttons))

    # what about resizes and space allocation and layout type stuff?
    # Does the frame have anything to do with that? Probably should
    # have a "layout_frame" method that kicks it all off.
    def lay_out_frame(self):
        self._top_level_sheet.allocate_space((self._screen.width, self._screen.height))
        self._top_level_sheet.layout()

    def show_dialog(self, dialog):
        if self._dialog is not None:
            raise RuntimeError("Can't have multiple dialogs currently")
        self._dialog = dialog
        dwidth = self._screen.width // 2
        dheight = self._screen.height // 2
        dx = (self._screen.width - dwidth) // 2
        dy = (self._screen.height - dheight) // 2
        dialog.allocate_space((dwidth, dheight))
        dialog.move_to((dx, dy))
        dialog.layout()
        self.render()

    def dialog_quit(self):
        if self._dialog is not None:
            self._dialog = None
            self.render()

    def render(self):
        # clear the screen first? Might be flickery... read the docs,
        # work out how to do this.
        self._top_level_sheet.render()
        if self._dialog is not None:
            self._dialog.render()
        self._screen.refresh()
