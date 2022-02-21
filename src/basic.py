from asciimatics.screen import Screen
from asciimatics.exceptions import ResizeScreenError

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.frame import Frame
from sheets.sheet import Sheet
from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.buttons import Button
from sheets.buttons import RadioButton
from sheets.buttons import CheckBox
from sheets.boxlayout import HorizontalLayout
from sheets.boxlayout import VerticalLayout
from sheets.dialog import Dialog
from sheets.scrollbar import Scrollbar
from sheets.viewport import Viewport
from sheets.label import Label
from sheets.separators import HorizontalSeparator
from sheets.separators import VerticalSeparator

from dcs.ink import Pen

import sys


def demo(screen):
    frame = Frame(screen)
    top_level_sheet = TopLevelSheet(frame)

    border_layout = BorderLayout(title="Basic")
    top_level_sheet.add_child(border_layout)

    child_sheet = HorizontalLayout([1, 2, 1, 1])
    border_layout.add_child(child_sheet)

    oneb = BorderLayout(title="buttons")
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
    dialog = Dialog(frame, title="dialog!",
                    text="Hello! I like pancakes!!")

    def btn_cb():
        # sets dialog up, but doesn't draw it. That happens in
        # render(). Perhaps the dialog layout should happen in
        # lay_out_frame()? Maybe it's independent.
        frame.show_dialog(dialog)

    button.on_click = btn_cb
    one.add_child(button)
    one.add_child(RadioButton(label="Radio", decorated=False))
    one.add_child(CheckBox(label="Check"))

    border2 = BorderLayout(title="two", style="single")
    child_sheet.add_child(border2)
    vlayout = VerticalLayout([1, 1, 1])
    border2.add_child(vlayout)
    label = Label("A label")
    vlayout.add_child(label)
    hseparator = HorizontalSeparator(style="single", size=8)
    vlayout.add_child(hseparator)
    vseparator = VerticalSeparator(style="double", size=8)
    vlayout.add_child(vseparator)

    green_bg = Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_GREEN)
    child_sheet.add_child(BorderLayout(title="green", style="spacing", default_pen=green_bg))

    border4 = BorderLayout(title="scrolling")
    child_sheet.add_child(border4)
    # MAKE THE BORDER LAYOUT WORK AS A SCROLLER, THEN IT CAN BE
    # WRAPPED AROUND ALL SORTS OF STUFF.
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
        contentpane.print_at("Hello, world!", (0, 0), pen)
        contentpane.print_at("What's the world coming to?", (10, 30), pen)
        contentpane.print_at("Goodbye, cruel world!", (100, 60), pen)
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
