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

from sheets.sheet import Sheet

from sheets.spacereq import FILL, SpaceReq
from sheets.separators import Separator
from sheets.buttons import Button
from frames.frame import Frame
from frames.commands import find_command

from logging import getLogger

logger = getLogger(__name__)

# A layout that arranges its children in a row. Each child is
# packed as closely as possible to its siblings
class MenubarLayout(Sheet):

    def __repr__(self):
        (w, h) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return f"Menubar({w}x{h}@{tx},{ty})"

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((offset, 0))
            offset += child.width()
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # layouts always clear their background; concrete widgets may
        # choose to do so if they need to but most will fill their
        # region anyway and they can rely on empty space being the
        # default background colour.
        (w, h) = self._region
        self.clear((0, 0), self._region)
        logger.info("render on menubar %s", self)
        self.move((0, 0))
        self.draw_to((w, 0), ' ', self.pen(role="menubar", state="default", pen="pen"))
        for child in self._children:
            child.render()

    # give each child as much space as they want
    def allocate_space(self, allocation):
        # height = 1
        # width = sum of all widths

        # make scrollbar as wide as its parent allows
        self._region = allocation
        (width, height) = allocation

        # simple sauce; loop over kids and allocate them the space
        # they want, hope they don't want too much! Use the list
        # control (built-in scrolling) if more space is needed...

        for child in self._children:
            sr = child.compose_space()
            cw = sr.x_preferred()
            # fixme: take the minimum of the button
            child.allocate_space((cw, 1))

    def compose_space(self):
        return SpaceReq(1, FILL, FILL, 1, 1, 1)

    # fixme: add some functions to take a bunch of labels and
    # callbacks and build menus out of them?

    # events - top level sheets don't pass event on to a parent,
    # instead they return False to indicate the event is not handled
    # and expect the Frame to take any further necessary action
    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="menubar")
        if command is not None:
            return command.apply(self)

        return False

    def find_focused_child(self):
        for child in self._children:
            if not isinstance(child, Separator):
                if child.is_focus():
                    return child
        return None

    def focus_first_child(self):
        for child in self._children:
            if isinstance(child, Button):
                self.frame().set_focus(child)
                return True
        return False

    def cycle_focus_backward(self, selected):
        found = False
        for child in reversed(self._children):
            if found:
                if isinstance(child, Button):
                    self.frame().set_focus(child)
                    return True
            if child == selected:
                found = True
        return False

    def cycle_focus_forward(self, selected):
        found = False
        for child in self._children:
            if found:
                if isinstance(child, Button):
                    self.frame().set_focus(child)
                    return True
            if child == selected:
                found = True
        return False
