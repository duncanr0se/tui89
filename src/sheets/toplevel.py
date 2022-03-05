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
        (width, height) = self._region
        return "TopLevelSheet({}x{})".format(width, height)

    def pen(self, role="toplevel", state="default", pen="pen"):
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
        logger.debug("returning pen for use: %s", spen)
        return spen

    def clear(self, origin, region):
        pen = self.pen()
        (x, y) = self._transform.apply(origin)
        (w, h) = region
        for line in range(0, h):
            self._frame._screen.move(x, y + line)
            self._frame._screen.draw(x + w, y + line, u' ', colour=pen.bg(), bg=pen.bg())

    def display_at(self, coord, text, pen):
        (x, y) = self._transform.apply(coord)
        try:
            self._frame._screen.print_at(text, x, y, colour=pen.fg(), attr=pen.attr(), bg=pen.bg())
        except AttributeError:
            raise AttributeError("error", pen)

    def move(self, coord):
        (x, y) = self._transform.apply(coord)
        self._frame._screen.move(x, y)

    def draw_to(self, coord, char, pen):
        if len(char) > 1:
            raise RuntimeError("draw_to accepts single drawing char", char)
        (x, y) = self._transform.apply(coord)
        self._frame._screen.draw(x, y, char, colour=pen.fg(), bg=pen.bg())

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

    def is_detached(self):
        return self._frame is None

    def is_attached(self):
        return self._frame is not None

    # events
    def handle_key_event(self, event):
        return False
