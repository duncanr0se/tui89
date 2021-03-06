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

from asciimatics.event import MouseEvent

from geometry.transforms import Transform, IDENTITY_TRANSFORM
from geometry.regions import Region
from geometry.points import Point
from sheets.sheet import Sheet
from sheets.spacereq import SpaceReq, FILL
from dcs.ink import Pen
from sheets.label import Label
from sheets.buttons import Button, MenuButton
from sheets.dialog import alert
from sheets.menubox import MenuBox
from sheets.separators import VerticalSeparator
from frames.commands import find_command

# +---------------+
# | Option 1    ↓ |
# +---------------+
# | Option 2      |
# | Option 3      |
#     ...
#
class OptionBox(Sheet):
    """Drop-down option box.

    Display selected line of text along with a button that displays a
    popup listbox containing selectable options.
    """

    default_text = "-- select --"

    def __init__(self,
                 options=None):
        super().__init__()

        self._options = [] if options is None else options
        self._children = []
        self._label = Label(OptionBox.default_text, align="center")
        self.add_child(self._label)
        self._drop_label = Label(u'▼', align="left")
        self.add_child(self._drop_label)
        self._option_list = None
        self._has_open_popup = False
        self._pressed = False

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "OptionBox({}x{}@{},{}: '{}')".format(self._region.region_width(),
                                                     self._region.region_height(),
                                                     tx, ty,
                                                     self._label._label_text)

    def value(self):
        value = self._label._label_text
        return value if value != OptionBox.default_text else None

    def set_options(self, options):
        self._options = options
        self.invalidate()

    def layout(self):
        self._label.move_to(Point(0, 0))
        (left, _, right, _) = self._region.ltrb()
        w = right-left
        self._drop_label.move_to(Point(w-3, 0))

    def handle_key_event(self, kevent):
        command = find_command(kevent, command_table="optionbox")
        if command is not None:
            return command.apply(self)
        return False

    def handle_event(self, mevent):
        if mevent.buttons == MouseEvent.LEFT_CLICK:
            self._pressed = True
            self.invalidate()
            return True
        if mevent.buttons == 0:
            if self._pressed:
                return self.activate()
        return False

    def accepts_focus(self):
        return True

    def is_focus(self):
        # todo: try just using the default and see what happens. Maybe
        # it's ok for the colour scheme to be different whilst the
        # option popup is open...
        return super().is_focus() or self._has_open_popup

    def _on_menubox_detached_callback(self, arg):
        # self=OptionBox; arg=MenuBox
        self._has_open_popup = False

    def open_popup(self):
        self._has_open_popup = True

    def menu_click_callback(self, button):
        self._label._label_text = button._label._label_text
        button.frame().menu_quit()
        self.frame().set_focus(self)

    def activate(self):
        self._pressed = False
        # focus is set on self but then immediately moved to the
        # menubox. Keep focus l&f for main control even when menu is
        # present.
        self.frame().set_focus(self)
        # fixme: could cache this menubox instead of rebuilding it
        # each time
        menubox = MenuBox(width=self.width())
        menubox.set_items([MenuButton(label=button, on_click=self.menu_click_callback) \
                           for button in self._options])

        # The menubox is not a child of the optionbox so doesn't
        # inherit pens in the usual way.
        # Instead we have this horrible hack that works, but requires
        # way more knowledge of the internals than is preferable.
        self._force_popup_colours(menubox)

        coord = Point(0, 1)
        transform = self.get_screen_transform()
        tcoord = transform.transform_point(coord)
        self.open_popup()
        menubox.on_detached_callback = self._on_menubox_detached_callback
        self.frame().show_popup(menubox, tcoord)

    # The menubox is not a child of the optionbox so doesn't
    # inherit pens in the usual way.
    # Instead we have this horrible hack that works, but requires
    # way more knowledge of the internals than is preferable.
    def _force_popup_colours(self, menubox):
        # Force menubutton colours
        force_pen = self.pen(role="optionbox", state="default", pen="accelerator")
        menubox.set_pen(force_pen, role="menubutton", state="default", which="accelerator")

        force_pen = self.pen(role="menubutton", state="focus", pen="accelerator")
        menubox.set_pen(force_pen, role="menubutton", state="focus", which="accelerator")

        force_pen = self.pen(role="editable", state="focus", pen="pen")
        menubox.set_pen(force_pen, role="menubutton", state="default", which="pen")
        # Force menubox colours
        menubox.set_pen(force_pen, role="menubox", state="default", which="pen")
        menubox.set_pen(force_pen, role="menubox", state="border", which="pen")

    def pen(self, role="undefined", state="default", pen="pen"):
        # "label" consists of labels making up "non-popup" parts of
        # optionbox
        if role == "undefined" or role == "label":
            role = "editable"
        if self.is_focus():
            state = "focus"
        if self._pressed:
            role, state = "button", "transient"
        return super().pen(role=role, state=state, pen=pen)

    def render(self):
        self._draw_background(self.pen())
        self._draw_label()
        self._draw_button()

    def _draw_background(self, pen):
        (l, t, r, b) = self._region.ltrb()
        # don't clear the space that will be used by the dropshadow of
        # the popup
        self.clear(Region(l, t, r-1, b), pen)

    def _draw_label(self):
        self._label.render()

    def _draw_button(self):
        self._drop_label.render()

    def allocate_space(self, region):
        (l, t, r, b) = region.ltrb()
        self._region = region
        # give last 1 char of width to the drop shadow, the next 2
        # chars of width to the "|v| button" and the rest to the label
        self._label.allocate_space(Region(l, t, r-3, b))
        self._drop_label.allocate_space(Region(l, t, l+2, t+1))

    def compose_space(self):
        label_sr = self._label.compose_space()
        # +2 is for the |v| "button", +1 is for drop shadow
        return SpaceReq(label_sr.x_min()+2+1, label_sr.x_preferred()+2+1, FILL,
                        1, 1, FILL)
