from asciimatics.widgets import Button, CheckBox, DatePicker, Divider, DropdownList, FileBrowser, Frame, Label, Layout, ListBox, MultiColumnListBox, PopUpDialog, PopupMenu, RadioButtons, Text, TextBox, TimePicker
from asciimatics.event import MouseEvent
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication
from asciimatics.widgets.utilities import THEMES
import sys

###

# Use as top-level layout in borderless Frame

class BorderLayout(Layout):

    _widget = None
    _layout = None
    _title = None

    def __init__(self, title=None):
        # Need an option to only take enough space for its kid, or to take
        # as much space as its parent allows.
        super().__init__([], fill_frame=True)
        self._title = title


    def add_widget(self, widget):
        # if there's already an assigned widget, error
        if self._widget:
            raise RuntimeError("Already a child assigned to border layout")
        if self._layout:
            raise RuntimeError("Already a layout assigned to border layout")
        self._widget = widget


    def add_layout(self, layout):
        if self._layout:
            raise RuntimeError("Can't add second layout to border")
        if self._widget:
            raise RuntimeError("Can't add layout to border with existing widget")
        layout.register_frame(self._frame)
        self._layout = layout

    # fix() then update()

    def fix(self, start_x, start_y, max_width, max_height):
        self.x = start_x
        self.y = start_y
        self.width = max_width - start_x
        self.height = max_height - start_y

        # fixme: need to do this the same way frame does and support
        # multiple layouts. Bah.
        if self._layout:
            self._layout.fix(start_x + 1, start_y + 1, self.width - 2, self.height - 2)

        # fixme: what if widget wants to be smaller than the available
        # space? This might just work already
        if self._widget:
            offset = 0
            this._widget.set_layout(start_x + 1, start_y + 1, offset, self.width - 2, self.height - 2)

        return self.height


    def update(self, frame_no):
        canvas = self._frame.canvas
        (left, top, right, bottom) = (self.x, self.y, self.width - 1, self.height - 1)
        (colour, attr, bg) = self._frame.palette["borders"]

        # top border - make allowances for a title
        canvas.print_at(u'╔', left, top, colour, attr, bg)
        canvas.move(1, top)

        if self._title:
            # LHS of bar + title
            bar_width = right - 1
            title = ' ' + self._title + ' '
            title_width = len(title)
            extra_needed = False
            if (bar_width - title_width) % 2 == 1:
                extra_needed = True
            side_bar_width = bar_width // 2
            canvas.draw(side_bar_width, top, char=u'═', colour=colour, bg=bg)
            canvas.print_at(' ' + self._title + ' ', side_bar_width, top, colour=colour, bg=bg)
            canvas.move(side_bar_width + title_width, top)
            canvas.draw(right, top, char=u'═', colour=colour, bg=bg)
        else:
            canvas.draw(right, top, char=u'═', colour=colour, bg=bg)
        canvas.print_at(u'╗', right, top, colour, attr, bg)

        # left border
        self._frame.canvas.move(left, top + 1)
        self._frame.canvas.draw(left, bottom, char=u'║', colour=colour, bg=bg)

        # right border - might be scroll bar
        self._frame.canvas.move(right, top + 1)
        self._frame.canvas.draw(right, bottom, char=u'║', colour=colour, bg=bg)

        # bottom border - might be scroll bar
        canvas.print_at(u'╚', left, bottom, colour, attr, bg)
        canvas.move(1, bottom)
        canvas.draw(right - 1, bottom, char=u'═', colour=colour, bg=bg)
        canvas.print_at(u'─', right - 1, bottom, colour, attr, bg)
        canvas.print_at(u'┘', right, bottom, colour, attr, bg)

        child = self._layout or self._widget
        child.update(frame_no)


    def focus(self, force_first=False, force_last=False, force_column=None, force_widget=None):
        self._has_focus = True
        if self._layout:
            self._layout.focus(force_first, force_last, force_column, force_widget)

        if self._widget:
            self._widget.focus()


    def blur(self):
        self._has_focus = False
        child = self._layout or self._widget
        if child:
            child.blur()


    def clear_widgets(self):
        this._layout = None
        this._widget = None


    def get_current_widget(self):
        if self._layout:
            return self._layout.get_current_widget()
        return self._widget

    # so much stuff is implemented directly in the widget, it sucks

    # see "process_event" and find widget for focus type stuff in
    # layout.py

    # todo: scroll bars
    # todo: nested boxes etc.
    # todo: keyboard / mouse is ignored currently

###

# fiddle frame
def make_frame(screen, width, height):

    # setting the themes up is really nothing to do with making the
    # frame...
    THEMES["default"]["borders"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE)
    THEMES["default"]["edit_text"] = (Screen.COLOUR_YELLOW, Screen.A_NORMAL, Screen.COLOUR_BLUE)
    THEMES["default"]["focus_edit_text"] = (Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN)

    _frame = Frame(screen, width, height, has_border=False, can_scroll=False)
    border = BorderLayout(title="A title")
    _frame.add_layout(border)

    layout = Layout([1, 2])
    border.add_layout(layout)

    #
    # BUTTON
    #
    layout.add_widget(Label("Button:"), 0)

    def x_on_click():
        pass

    layout.add_widget(Button("Button", x_on_click), 1)

    #
    # CHECKBOX
    #
    layout.add_widget(Label("Checkbox:"), 0)
    layout.add_widget(CheckBox("Checkbox"), 1)

    #
    # DATEPICKER
    #
    layout.add_widget(Label("Date picker:"), 0)
    layout.add_widget(DatePicker(), 1)

    #
    # DIVIDER
    #
    layout.add_widget(Label("Divider:"), 0)
    layout.add_widget(Divider(), 1)

    #
    # DROPDOWNLIST
    #
    layout.add_widget(Label("DropdownList:"), 0)
    layout.add_widget(DropdownList([("first", 0), ("second", 1), ("third", 3)]), 1)

    #
    # FILEBROWSER
    #
    layout.add_widget(Label("FileBrowser:"), 0)
    layout.add_widget(FileBrowser(10, "/"), 1)

    #
    # FILEBROWSER IN FRAME
    #
    # <todo>
    #
    # LISTBOX
    #
    layout.add_widget(Divider(draw_line=False, height=9), 0)
    layout.add_widget(Label("ListBox:"), 0)
    layout.add_widget(ListBox(5, [("first", 0), ("second", 1), ("third", 3)]), 1)

    #
    # MULTICOLUMNLISTBOX
    #
    layout.add_widget(Divider(draw_line=False, height=4), 0)
    layout.add_widget(Label("MultiColumnListBox:"), 0)
    layout.add_widget(MultiColumnListBox(5, ["<30%", "^40%", ">30%"],
                                         [(["one", "row", "here"], 0),
                                          (["second", "row", "here"], 1),
                                          (["third", "row", "here"], 2)]
    ), 1)

    #
    # POPUPDIALOG
    #
    layout.add_widget(Divider(draw_line=False, height=4), 0)
    layout.add_widget(Label("PopUpDialog:"), 0)

    def _show_dialog():
        _frame._scene.add_effect(PopUpDialog(screen, "Here's a dialog!", ["OK"], has_shadow=True))

    layout.add_widget(Button("Show Dialog", _show_dialog), 1)

    #
    # POPUPMENU
    #
    layout.add_widget(Label("PopupMenu:"), 0)

    def _no_op():
        pass

    def _quit():
        raise StopApplication("User requested exit")

    def _show_menu():
        # Perhaps menus should accept "has_shadow" like Frame does?
        _frame._scene.add_effect(PopupMenu(screen, [("Open", _no_op), ("Save", _no_op), ("Exit", _quit)], 1, 1))

    layout.add_widget(Button("Show Menu", _show_menu), 1)

    #
    # RADIOBUTTONS
    #
    layout.add_widget(Label("RadioButtons:"), 0)
    layout.add_widget(RadioButtons([("One", 1), ("Two", 2), ("Three", 3)]), 1)

    #
    # todo: scrollbar
    #
    #
    # TEXT
    #
#    layout.add_widget(Divider(draw_line=False, height=2), 0)
#    layout.add_widget(Label("Text:"), 0)
#    layout.add_widget(Text(), 1)

    #
    # TEXTFIELD
    #
#    layout.add_widget(Label("TextBox:"), 0)
#    layout.add_widget(TextBox(10), 1)

    #
    # TIMEPICKER
    #
#    layout.add_widget(Divider(draw_line=False, height=9), 0)
    layout.add_widget(Label("TimePicker:"), 0)
    layout.add_widget(TimePicker(), 1)

    _frame.fix()
    return _frame

# outer frame can't scroll; contents inside frame should be able to
# though, not sure quite how that's going to work. Experiment...
def x_make_frame(screen, width, height):
    _frame = Frame(screen, width, height, title=u"My Frame", can_scroll=True)
    # work out how to set the colours for the borders...
#    THEMES["default"]["borders"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE)
#    _frame.palette["borders"] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE)
    # Add 2-column layout
    layout = Layout([1, 2])
    _frame.add_layout(layout)
    #
    # BUTTON
    #
    layout.add_widget(Label("Button:"), 0)

    def x_on_click():
        pass

    layout.add_widget(Button("Button", x_on_click), 1)
    #
    # CHECKBOX
    #
    layout.add_widget(Label("Checkbox:"), 0)
    layout.add_widget(CheckBox("Checkbox"), 1)
    #
    # DATEPICKER
    #
    layout.add_widget(Label("Date picker:"), 0)
    layout.add_widget(DatePicker(), 1)
    #
    # DIVIDER
    #
    layout.add_widget(Label("Divider:"), 0)
    layout.add_widget(Divider(), 1)
    #
    # DROPDOWNLIST
    #
    layout.add_widget(Label("DropdownList:"), 0)
    layout.add_widget(DropdownList([("first", 0), ("second", 1), ("third", 3)]), 1)
    #
    # FILEBROWSER
    #
    layout.add_widget(Label("FileBrowser:"), 0)
    layout.add_widget(FileBrowser(10, "/"), 1)
    #
    # FILEBROWSER IN FRAME
    #
    # <todo>
    #
    # LISTBOX
    #
    layout.add_widget(Divider(draw_line=False, height=9), 0)
    layout.add_widget(Label("ListBox:"), 0)
    layout.add_widget(ListBox(5, [("first", 0), ("second", 1), ("third", 3)]), 1)
    #
    # MULTICOLUMNLISTBOX
    #
    layout.add_widget(Divider(draw_line=False, height=4), 0)
    layout.add_widget(Label("MultiColumnListBox:"), 0)
    layout.add_widget(MultiColumnListBox(5, ["<30%", "^40%", ">30%"],
                                         [(["one", "row", "here"], 0),
                                          (["second", "row", "here"], 1),
                                          (["third", "row", "here"], 2)]
    ), 1)
    #
    # POPUPDIALOG
    #
    layout.add_widget(Divider(draw_line=False, height=4), 0)
    layout.add_widget(Label("PopUpDialog:"), 0)

    def _show_dialog():
        _frame._scene.add_effect(PopUpDialog(screen, "Here's a dialog!", ["OK"], has_shadow=True))

    layout.add_widget(Button("Show Dialog", _show_dialog), 1)
    #
    # POPUPMENU
    #
    layout.add_widget(Label("PopupMenu:"), 0)

    def _no_op():
        pass

    def _quit():
        raise StopApplication("User requested exit")

    def _show_menu():
        # Perhaps menus should accept "has_shadow" like Frame does?
        _frame._scene.add_effect(PopupMenu(screen, [("Open", _no_op), ("Save", _no_op), ("Exit", _quit)], 1, 1))

    layout.add_widget(Button("Show Menu", _show_menu), 1)
    #
    # RADIOBUTTONS
    #
    layout.add_widget(Label("RadioButtons:"), 0)
    layout.add_widget(RadioButtons([("One", 1), ("Two", 2), ("Three", 3)]), 1)
    #
    # todo: scrollbar
    #
    #
    # TEXT
    #
    layout.add_widget(Divider(draw_line=False, height=2), 0)
    layout.add_widget(Label("Text:"), 0)
    layout.add_widget(Text(), 1)
    #
    # TEXTFIELD
    #
    layout.add_widget(Label("TextBox:"), 0)
    layout.add_widget(TextBox(10), 1)
    #
    # TIMEPICKER
    #
    layout.add_widget(Divider(draw_line=False, height=9), 0)
    layout.add_widget(Label("TimePicker:"), 0)
    layout.add_widget(TimePicker(), 1)
    #
    # todo: vertical divider, but can't really do as stand-alone widget
    #   - add another layout for it? Probably need a few layout types
    #     to do what is wanted...
    #

    # Gotta say, a lot of these widgets look like crap. Perhaps I need
    # to implement my own TUI widgets on top of these? Should be able
    # to create a "turbo-vision look-alike" widget set. Either that or
    # hack the existing widgets to be a little more flexible?
    # Layouts are very limited for a "TUI" in these packages :(
    # ... but I feel asciimatics is probably a slightly better basis to build upon
    # todo: change border colour to white, change border style to double lines?

    # Built-in scroll bars are a bit rubbish.
    # How to wrap a border around another pane? Should be able to do this!

    # Layouts can be nested; need a border layout. Need to make these
    # take up as much space as is available.

    # Menus need separators! And shadows! They are already specific
    # Frame subtypes, just not very good ones.

    # Need: horizontal + vertical scroll bars; make border widget same
    # widget that is responsible for scrolling also.

    # Need: Menu bar - proper menu bar that can have menus attached

    # Need: status bar and information panels

    # Need: support for command tables

    # It all starts with the border layout...
    _frame.fix()
    return _frame

def start_frame(screen, scene):
    (width, height) = screen.dimensions
    frame = make_frame(screen, width, height)
    screen.play([
        Scene([frame], -1)
    ], stop_on_resize=True, start_scene=scene, allow_int=True)

###

last_scene = None
while True:
    try:
        Screen.wrapper(start_frame, catch_interrupt=False, arguments=[last_scene])
        sys.exit(0)
    except ResizeScreenError as e:
        last_scene = e.scene
