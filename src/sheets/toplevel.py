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
from dcs.ink import Pen

from logging import getLogger

logger = getLogger(__name__)

class TopLevelSheet(Sheet):

    def __init__(self):
        super().__init__()
        self._accelerator_to_widget = dict()
        self._frame = None

    def __repr__(self):
        (left, top, right, bottom) = self._region
        return "TopLevelSheet({}x{})".format(right-left, bottom-top)

    def pen(self, role="undefined", state="default", pen="pen"):
        if role == "undefined":
            role = "toplevel"
        # default method looks for requested pen but if it can't find
        # it it passes the query to its parent.
        spen = None
        if self._pens is not None:
            if role in self._pens:
                if state in self._pens[role]:
                    if pen in self._pens[role][state]:
                        spen = self._pens[role][state][pen]
        # If not found get from frame
        if spen is None:
            spen = self.frame().pen(role, state, pen)
        return spen

    def clear(self, region_ltrb, pen):
        # top level transform = top level -> "screen"
        transformed_region = self._transform.transform_region(region_ltrb)
        (l, t, r, b) = transformed_region
        # Python range() does not include the upper bound
        for line in range(t, b):
            self._frame._screen.move(l, line)
            self._frame._screen.draw(r, line, pen.fill(), colour=pen.fg(), bg=pen.bg())

    def display_at(self, coord, text, pen):
        (x, y) = self._transform.apply(coord)
        self._frame._screen.print_at(text, x, y, colour=pen.fg(), attr=pen.attr(), bg=pen.bg())

    def move(self, coord):
        (x, y) = self._transform.apply(coord)
        self._frame._screen.move(x, y)

    def draw_to(self, coord, char, pen):
        if len(char) > 1:
            raise RuntimeError("draw_to accepts single drawing char", char)
        (x, y) = self._transform.apply(coord)
        # Asciimatic's screen x/y are double the "character
        # positions". Make allowances.
        (from_x, from_y) = (self._frame._screen._x, self._frame._screen._y)
        from_x = from_x // 2
        from_y = from_y // 2

        # only draw straight lines
        if x == from_x:
            # vertical
            min_y = min(from_y, y)
            max_y = max(from_y, y)
            # upper end of range is excluded
            for y in range(min_y, max_y):
                self._frame._screen.print_at(char, x, y, colour=pen.fg(),
                                             attr=pen.attr(), bg=pen.bg())
        else:
            # horizontal
            min_x = min(x, from_x)
            max_x = max(x, from_x)
            # upper end of range is excluded
            for x in range(min_x, max_x):
                self._frame._screen.print_at(char, x, y, colour=pen.fg(),
                                             attr=pen.attr(), bg=pen.bg())

    def add_child(self, child):
        if self._children:
            raise RuntimeError("TopLevelSheet supports a single child only")
        super().add_child(child)

    def top_level_sheet(self):
        return self;

    def frame(self):
        return self._frame

    # When are things laid out? After space allocation? Or as part of
    # space allocation? When is compose-space called?
    # Pretty sure the below is wrong! How to constrain children to fit
    # in available space (or to overflow)?
    def allocate_space(self, allocation):
        (left, top, right, bottom) = allocation
        self._region = allocation
        for child in self._children:
            # child of top level sheet MAY NOT have a transform
            child.move_to((0, 0))
            child.allocate_space(self._region)

    def layout(self):
        for child in self._children:
            child.layout()

    def get_screen_transform(self):
        return self._transform

    def handle_event(self, event):
        # False == not handled, not that anybody cares at this point
        return False

    def graft(self, frame):
        frame.set_top_level_sheet(self)
        self.attach(frame)

    # attach from lowest z-order up
    def attach(self, frame):
        self._frame = frame
        for child in self._children:
            child.attach()

    # detach from highest z-order down
    def detach(self):
        # fixme: sheet lifecycle events? (mapped, detached, etc)
        for child in self._children:
            child.detach()
        self._frame = None
        if self.on_detached_callback is not None:
            self.on_detached_callback(self)

    def is_detached(self):
        return self._frame is None

    def is_attached(self):
        return self._frame is not None

    # events
    def handle_key_event(self, event):
        return False
