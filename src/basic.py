from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError, StopApplication

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from frames.frame import Frame
from sheets.sheet import Sheet
from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.buttons import Button, RadioButton, CheckBox, MenuButton
from sheets.boxlayout import HorizontalLayout, VerticalLayout
from sheets.dialog import Dialog, alert
from sheets.scrollbar import Scrollbar
from sheets.viewport import Viewport
from sheets.label import Label
from sheets.separators import HorizontalSeparator, VerticalSeparator
from sheets.listlayout import ListLayout
from sheets.menubar import MenubarLayout
from sheets.menubox import MenuBox

from dcs.ink import Pen

import sys
import logging

def demo(screen):

    logging.basicConfig(filename="tui.log", level=logging.DEBUG)

    frame = Frame(screen)
    top_level_sheet = TopLevelSheet(frame)

    border_layout = BorderLayout(title="Basic")
    top_level_sheet.add_child(border_layout)

    child_sheet = HorizontalLayout([(15, "char"), (20, "%"), 1, 2])
    border_layout.add_child(child_sheet)

    oneb = BorderLayout(title="buttons", style="single")
    child_sheet.add_child(oneb)

    one = VerticalLayout([1, 1, 1])
    oneb.add_child(one)

    button = Button(label="Press me!", decorated=True)
    # Single line is supported; lines with \n in aren't displayed
    # properly.
    # Multiline (as separate lines) isn't supported by the dialog
    # (yet).
    # Long lines overflow the dialog (as expected)
    # fixme: implement clipping
    # fixme: implement wrapping
    # fixme: dialog sizing to fit text better, with existing scheme
    #     as a maximum.
    dialog = Dialog(title="dialog!", text="Hello! I like pancakes!!")

    def btn_cb(button):
        # sets dialog up, but doesn't draw it. That happens in
        # render(). Perhaps the dialog layout should happen in
        # lay_out_frame()? Maybe it's independent.
        button.frame().show_dialog(dialog)

    button.on_click = btn_cb
    one.add_child(button)
    one.add_child(RadioButton(label="Radio", decorated=False))
    one.add_child(CheckBox(label="Check"))

    border2 = BorderLayout(title="list", style="single")
    child_sheet.add_child(border2)
    listlayout = ListLayout()
    border2.add_child(listlayout)
    label = Label("A label")
    listlayout.add_child(label)
    hseparator = HorizontalSeparator(style="single", size=8)
    listlayout.add_child(hseparator)
    vseparator = VerticalSeparator(style="double", size=8)
    listlayout.add_child(vseparator)

    green_bg = Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_GREEN)
    green_border = BorderLayout(title="green", style="spacing", default_pen=green_bg)
    child_sheet.add_child(green_border)
    green_vert = VerticalLayout([1, 10])
    menubar = MenubarLayout()
    green_border.add_child(green_vert)
    green_vert.add_child(menubar)

    menu1 = MenuButton(label="File")
    menu2 = MenuButton(label="Edit")
    menu3 = MenuButton(label="View")
    menu4 = MenuButton(label="Help")

    menubar.set_children([menu1, menu2, menu3, menu4])

    # top level sheet < dialog < menu
    # MenuBox = BorderLayout(style="single").add_child(ListLayout)
    file_menu = MenuBox()
    fm1 = MenuButton(label="Open")
    fm2 = HorizontalSeparator()
    fm3 = MenuButton(label="Save")
    fm4 = MenuButton(label="Save As")
    fm5 = HorizontalSeparator()

    def default_on_click(widget):
        alert(widget.frame(), "Button clicked: {}".format(widget._label))
        widget.frame().menu_quit()
    fm1.on_click = default_on_click
    fm3.on_click = default_on_click
    fm4.on_click = default_on_click

    fm6 = MenuButton(label="Exit")

    def app_quit(widget):
        raise StopApplication("Exit Menu")

    fm6.on_click = app_quit

    file_menu.set_items([fm1, fm2, fm3, fm4, fm5, fm6])

    menu1.set_menu_box(file_menu)

    spacer = Sheet(default_pen=frame.theme("focus_edit_text"))
    green_vert.add_child(spacer)

    border4 = BorderLayout(title="scrolling", style="single")
    child_sheet.add_child(border4)
    vbar = Scrollbar(orientation="vertical")
    hbar = Scrollbar(orientation="horizontal")
    # setting bars on the border pane is just a VISUAL thing to
    # get the bars displayed neatly in the border. The bars could
    # be anywhere and still control the scrolled pane.
    border4.set_scrollbars(vbar, hbar)
    # Content pane is the thing being scrolled

    # Need a sheet mode to deal with stuff that doesn't fit. Clip for
    # usual sheets, overflow for children of viewports. Scrolling just
    # changes the transform of the scrolled child and calls "redraw"
    # on the viewport to show the new area. How to store stuff that's
    # drawn so these calculations can be performed?

    # viewport clips, content pane overflows. How to copy from content
    # pane to viewport?
    contentpane = Sheet()
    # scroller provides the viewport onto the scrolled sheet.
    # Maybe it should be called "Viewport"?
    # Use the transform to display different areas of the
    # contentpane.
    # Bars passed here are to control the viewport, NOT for
    # display.
    viewport = Viewport(contentpane, vertical_bar=vbar, horizontal_bar=hbar)
    border4.add_child(viewport)

    # these are not appearing, perhaps because the "render" method is
    # causing it to be immediately overdrawn?
    def draw():
        pen = frame.theme("selected_focus_control")
        contentpane.display_at((0, 0), "Hello, world!", pen)
        contentpane.display_at((10, 30), "What's the world coming to?", pen)
        contentpane.display_at((100, 60), "Goodbye, cruel world!", pen)
    contentpane.render = draw

    frame.lay_out_frame()

#    child_sheet.print_at('Hello, world!', (0, 0))
#    child_sheet.print_at('{}x{}'.format(str(screen.width), str(screen.height)), (0, 1))
#    child_sheet.print_at('{}'.format(child_sheet), (0, 2))
#    child_sheet.print_at('and now for something completely different; a longish string!', (156, 10))

    # render() or refresh()? refresh() should be called each time
    # around the event loop...
    # currently render() method on top sheet calls refresh() but that
    # won't wash now that Frame is introduced.
    frame.render()

    # Should the frame manage a menu and status bar (unless I decide
    # to manage that stuff manually). Need to decide when to call
    # refresh() / redraw() in that case... but then need to decide how
    # to deal with the events. And focus. And input. Etc., etc.

    # The frame directs events to the dialog, if there is one, in
    # preference to any other sheet (conceptually the dialog is always
    # highest in z-order)
    frame.start_frame()

# This isn't working, not sure why. Maybe there's a better way to deal
# with screen resize...
while True:
    try:
        Screen.wrapper(demo, unicode_aware=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
