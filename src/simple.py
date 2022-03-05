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
from sheets.dialog import Dialog, alert, yes_no
from sheets.scrollbar import Scrollbar
from sheets.viewport import Viewport
from sheets.label import Label
from sheets.separators import HorizontalSeparator, VerticalSeparator
from sheets.listlayout import ListLayout
from sheets.menubar import MenubarLayout
from sheets.menubox import MenuBox
from sheets.textentry import TextEntry

from dcs.ink import Pen

import sys
import logging
from logging import getLogger

def demo(screen):

    logging.basicConfig(filename="simple.log", level=logging.DEBUG)

    frame = Frame(screen)
    # FIXME: should top-level-sheets be special? They really aren't in
    # this implementation.
    top_level_sheet = TopLevelSheet()

    # grafting early doesn't break things; likely still better to do
    # later. Code might be simpler if early grafting was not
    # permitted.
    #top_level_sheet.graft(frame)

    border_layout = BorderLayout(title="Simple")
    top_level_sheet.add_child(border_layout)

    button = Button(label="Pancakes!", decorated=True)
    button.on_click_callback = _make_dialog_callback()
    border_layout.add_child(button)

    top_level_sheet.graft(frame)
    frame.lay_out_frame()
    frame.render()

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

    return btn_cb


# This isn't working, not sure why. Maybe there's a better way to deal
# with screen resize...
while True:
    try:
        Screen.wrapper(demo, unicode_aware=True)
        sys.exit(0)
    except ResizeScreenError:
        pass
