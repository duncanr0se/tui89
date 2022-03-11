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
from sheets.boxlayout import HorizontalLayout
from sheets.listlayout import ListLayout
from sheets.scrollbar import Scrollbar
from sheets.viewport import Viewport
from sheets.label import Label, ValueLabel
from sheets.buttons import Button

from logging import getLogger

logger = getLogger(__name__)

# A control that wraps a list layout and vertical bar in a scroller.
class ListControl(Sheet):

    def __init__(self, options=[]):
        super().__init__()
        self._options = options
        self._layout = HorizontalLayout([1, (1, "char")])
        self.add_child(self._layout)

        self._listbox = ListLayout()
        if len(options) > 0:
            for opt in options:
                # fixme: there's no reason these items should be
                # restricted to just being strings wrapped in new
                # labels... make also work with arbitrary widgets
                self._listbox.add_child(ValueLabel(label_text=opt))
                # self._listbox.add_child(Button(label=opt, decorated=False))
                # self._listbox.add_child(Button(label=opt))
        self._vbar = Scrollbar(orientation="vertical")

        self._viewport = Viewport(self._listbox, vertical_bar=self._vbar)

        self._layout.add_child(self._viewport)
        self._layout.add_child(self._vbar)

    def pen(self, role="undefined", state="default", pen="pen"):
        overridden_roles = ["undefined", "label", "button"]
        if role in overridden_roles:
            role = "buttonbox"
        return super().pen(role, state, pen)

    def allocate_space(self, allocation):
        (l, t, r, b) = allocation
        self._region = allocation
        for child in self._children:
            child.allocate_space(allocation)

    def compose_space(self):
        # default size for list control is 10x10
        for c in self._children:
            # single child.
            child_sr = c.compose_space()
            sr = SpaceReq(5, 10, FILL, 5, 10, FILL)
            return sr

    def layout(self):
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    def activate(self):
        # self.frame().set_focus(self)
        # self.invalidate()
        # callback?
        pass

    # fixme: should be able to select member of the list and have that
    # been the value of the widget / control.

    # def find_next_focus(self, current_focus, found_current):
        # logger.debug("LISTCONTROL - FIND NEXT FOCUS. CALLING ON SUPER")
        # result = super().find_next_focus(current_focus, found_current)
        # logger.debug("RESULT IS {}", result)
        # return result
