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

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM
from geometry.points import Point
from sheets.sheet import Sheet
from sheets.spacereq import FILL, SpaceReq
from dcs.ink import Pen

class Separator(Sheet):

    _validstyles = ["double", "single", "spacing"]

    def __init__(self, style="single", size=None):
        super().__init__()

        self._validate_style(style)

        self._style = style
        self._size = size

    def _validate_style(self, style):
        if style not in Separator._validstyles:
            raise RuntimeError(f"style {style} not in {validstyles}")

    def add_child(self):
        raise RuntimeError("children not allowed")

    def pen(self, role="undefined", state="default", pen="pen"):
        if role == "undefined":
            role = "border"
        return super().pen(role=role, state=state, pen=pen)

    def center(self, size):
        return max(size // 2, 0)


class HorizontalSeparator(Separator):

    _line_chars = {
        "double": u'═',
        "single": u'─',
        "spacing": ' '
    }

    def __repr__(self):
        return "HorizontalSeparator({})".format(self._region.region_width())

    # drawing / redisplay
    def render(self):
        pen = self.pen()
        (l, t, r, b) = self._region.ltrb()
        (w, h) = (r-l, b-t)
        self.clear(self._region)
        y = self.center(h-1)
        self.move(Point(l, y))
        self.draw_to(Point(r, y), HorizontalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        length = FILL if self._size is None else self._size
        return SpaceReq(1, length, FILL, 1, 1, FILL)


class VerticalSeparator(Separator):

    _line_chars = {
        "double": u'║',
        "single": u'│',
        "spacing": ' '
    }

    def __repr__(self):
        return "VerticalSeparator({})".format(self._region.region_height())

    # drawing / redisplay
    def render(self):
        pen = self.pen()
        (l, t, r, b) = self._region.ltrb()
        (w, h) = (r-l, b-t)
        self.clear(self._region)
        x = self.center(w-1)
        self.move(Point(x, t))
        self.draw_to(Point(x, h), VerticalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        length = FILL if self._size is None else self._size
        return SpaceReq(1, 1, FILL, 1, length, FILL)
