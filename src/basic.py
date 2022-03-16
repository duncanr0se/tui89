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
from asciimatics.exceptions import ResizeScreenError, StopApplication

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from frames.frame import Frame
from sheets.sheet import Sheet
from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.buttons import Button, RadioButton, CheckBox, MenuButton
from sheets.boxlayout import HorizontalLayout, VerticalLayout
from sheets.dialog import Dialog, alert, yes_no, MultivalueDialog
from sheets.scrollbar import Scrollbar
from sheets.viewport import Viewport
from sheets.label import Label
from sheets.separators import HorizontalSeparator, VerticalSeparator
from sheets.listlayout import ListLayout, ButtonBox
from sheets.menubar import MenubarLayout
from sheets.menubox import MenuBox
from sheets.textentry import TextEntry
from sheets.textarea import TextArea
from sheets.optionbox import OptionBox
from controls.listcontrol import ListControl

from dcs.ink import Pen

import sys
import logging
from logging import getLogger

logger = getLogger(__name__)

def demo(screen):

    logging.basicConfig(filename="tui.log", level=logging.DEBUG)

    frame = Frame(screen)
    # FIXME: should top-level-sheets be special? They really aren't in
    # this implementation.
    top_level_sheet = TopLevelSheet()

    # grafting early doesn't break things; likely still better to do
    # later. Code might be simpler if early grafting was not
    # permitted.
    #top_level_sheet.graft(frame)

    border_layout = BorderLayout(title="Basic")
    top_level_sheet.add_child(border_layout)

    child_sheet = HorizontalLayout([(18, "char"), (20, "%"), 1, 1])
    border_layout.add_child(child_sheet)

    #### "buttons"

    oneb = BorderLayout(title="buttons", style="single")
    child_sheet.add_child(oneb)

    one = VerticalLayout([(7, "%"), (7, "%"), (7, "%"), (26, "%"), (23, "%"), 1, 1])
    oneb.add_child(one)

    button = Button(label="Pancakes!", decorated=True)
    button.on_click_callback = _make_dialog_callback()
    one.add_child(button)

    button = Button(label="Yes/No", decorated=True)
    # fixme: dialog needs to expose "button callback" which gets
    # called when one of the dialog buttons is pushed
    button.on_click_callback = _make_yesno_callback()
    one.add_child(button)

    button = Button(label="Multivalue", decorated=True)
    button.on_click_callback = _make_multivalue_callback(frame)
    one.add_child(button)

    # "button box"
    buttonbox = ButtonBox()
    boxradio1 = RadioButton(label="Red")
    boxradio2 = RadioButton(label="Green")
    boxradio3 = RadioButton(label="Blue")
    buttonbox.set_children([boxradio1, boxradio2, boxradio3])
    one.add_child(buttonbox)

    one.add_child(RadioButton(label="Radio1", decorated=False))
    one.add_child(RadioButton(label="Radio2", decorated=False))
    one.add_child(CheckBox(label="Check"))

    #### "list"

    border2 = BorderLayout(title="list", style="single")
    child_sheet.add_child(border2)
    listlayout = ListLayout()
    border2.add_child(listlayout)

    row1 = HorizontalLayout([1, 1])
    listlayout.add_child(row1)
    row1.add_child(Label("Label:"))
    row1.add_child(Label("This is a label"))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    row2 = HorizontalLayout([])
    listlayout.add_child(row2)
    row2.add_child(Label("HSeparator:"))
    row2.add_child(HorizontalSeparator(style="single", size=8))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    row3 = HorizontalLayout([])
    listlayout.add_child(row3)
    row3.add_child(Label("VSeparator:", valign="center"))
    row3.add_child(VerticalSeparator(style="double", size=8))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    row4 = HorizontalLayout([])
    listlayout.add_child(row4)
    row4.add_child(Label("Long label:"))
    row4.add_child(Label("This label should be truncated to fit the available space"))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    # right align
    row5 = HorizontalLayout([])
    listlayout.add_child(row5)
    row5.add_child(Label("Right align:"))
    row5.add_child(Label("align", align="right"))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    # center align
    row6 = HorizontalLayout([])
    listlayout.add_child(row6)
    row6.add_child(Label("Center align:"))
    row6.add_child(Label("align", align="center"))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    # left align
    row7 = HorizontalLayout([])
    listlayout.add_child(row7)
    row7.add_child(Label("Left align:"))
    row7.add_child(Label("align", align="left"))

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    row8 = HorizontalLayout([])
    listlayout.add_child(row8)
    entry = TextEntry()
    label = Label("Text entry:", label_widget=entry)
    row8.add_child(label)
    row8.add_child(entry)

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    row9 = HorizontalLayout([])
    listlayout.add_child(row9)
    area = TextArea(lines=6)
    label = Label("Text Area:", label_widget=area, valign="center")
    row9.add_child(label)
    row9.add_child(area)

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    row10 = HorizontalLayout([])
    listlayout.add_child(row10)
    box = OptionBox(options=["Red", "Green", "Blue", "Yellow"])
    label = Label("Option box:", label_widget=box)
    row10.add_child(label)
    row10.add_child(box)

    listlayout.add_child(HorizontalSeparator(style="spacing"))

    # List Control

    row11 = HorizontalLayout([])
    listlayout.add_child(row11)
    list_control = ListControl(options=["One", "Two", "Three", "Four", "Five",
                                        "Six", "Seven", "Eight", "Nine", "Ten",
                                        "Eleven", "Twelve", "Thirteen", "Fourteen",
                                        "Not a number! Instead something longer"])
    # list control with many items to check scrollbar behaviour
    # list_control = ListControl(options=[str(x) for x in range(0, 100)])
    label = Label("List control:", label_widget=list_control, valign="center")
    row11.add_child(label)
    row11.add_child(list_control)

    #### "green"

    green_bg = Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_GREEN, ' ')
    # associate the pen with the sheet;
    #
    # fixme: the pens being used are not clear any more. The interface
    # sucks. It's a good job I have intimate knowledge of the
    # internals, but this is really not satisfactory and needs
    # reworking.
    green_border = BorderLayout(title="green", style="spacing")
    child_sheet.add_child(green_border)
    green_border.set_pen(pen=green_bg, role="border", state="default", which="pen")
    # fixme: not sure it's right that the boxlayouts force more space
    # on their children than the children can cope with. Removing
    # spacer sheet and making the ratio 1 forces the menubar to fill
    # the available space. Seems wrong.
    green_vert = VerticalLayout([(1, "char"), 1])
    menubar = _make_menubar()
    green_border.add_child(green_vert)
    green_vert.add_child(menubar)

    spacer = Sheet() #default_pen=frame.theme("focus_edit_text"))
    green_vert.add_child(spacer)

    #### "scrolling"

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

    def draw():
        pen = frame.pen("undefined", "default", "pen")
        contentpane.display_at((0, 0), "Hello, world!", pen)
        contentpane.display_at((10, 30), "What's the world coming to?", pen)
        contentpane.display_at((60, 60), "Goodbye, cruel world!", pen)
    contentpane.render = draw

    ####

    top_level_sheet.graft(frame)

    frame.lay_out_frame()

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


def _make_dialog_callback():
    # Single line is supported; lines with \n in aren't displayed
    # properly.
    # Multiline (as separate lines) isn't supported by the dialog
    # (yet).
    # Long lines overflow the dialog (as expected)
    # fixme: implement wrapping
    # fixme: dialog sizing to fit text better, with existing scheme
    #     as a maximum.
    dialog = Dialog(title="dialog!", text="Hello! I like pancakes!!")

    def btn_cb(button):
        # sets dialog up, but doesn't draw it. That happens in
        # render(). Perhaps the dialog layout should happen in
        # lay_out_frame()? Maybe it's independent.
        button.frame().show_dialog(dialog)
        # get error before dialog is on screen. So not really modal...
        #
        # not sure what I was expecting; but need to work out how to
        # make use of dialogs as they are and get values back out of
        # them. I always had trouble with the async stuff :/
        #
        #raise RuntimeError("back from show_dialog")

    return btn_cb

def _make_yesno_callback():
    def btn_cb(button):
        yes_no(button.frame(), "Isn't it a lovely day?")
    return btn_cb

def _make_menubar():
    menubar = MenubarLayout()
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
    fm1.on_click_callback = default_on_click
    fm3.on_click_callback = default_on_click
    fm4.on_click_callback = default_on_click

    fm6 = MenuButton(label="Exit")

    def app_quit(widget):
        raise StopApplication("Exit Menu")

    fm6.on_click_callback = app_quit

    file_menu.set_items([fm1, fm2, fm3, fm4, fm5, fm6])

    menu1.set_menu_box(file_menu)

    return menubar


def _make_multivalue_callback(frame):
    def do_it(button):
        dialog = MultivalueDialog()
        # because this is a sheet it does not allocate space for its
        # children (at all). Only use as a placeholder.
        content = Sheet(width=20, height=10)
        layout = ListLayout()

        mbar = MenubarLayout()
        menu1 = MenuButton(label="One")
        menu2 = MenuButton(label="Two")
        mbar.set_children([menu1, menu2])

        label = Label("01234567890123456789")

        list_control = ListControl(options=["One", "Two", "Three", "Four", "Five",
                                            "Six", "Seven", "Eight", "Nine", "Ten",
                                            "Eleven", "Twelve", "Thirteen", "Fourteen",
                                            "Not a number! Instead something longer"])

        layout.add_child(mbar)
        layout.add_child(HorizontalSeparator(style="spacing"))
        layout.add_child(label)
        layout.add_child(HorizontalSeparator(style="spacing"))
        layout.add_child(list_control)

        logger.debug("MultivalueDialog children=%s", dialog._children)

        content.add_child(layout)

        dialog.add_child(content)
        frame.show_dialog(dialog)
    return do_it


# This isn't working, not sure why. Maybe there's a better way to deal
# with screen resize...
while True:
    try:
        Screen.wrapper(demo, unicode_aware=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
