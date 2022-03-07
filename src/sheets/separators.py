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

from sheets.sheet import Sheet
from sheets.spacereq import FILL, SpaceReq
from dcs.ink import Pen

class Separator(Sheet):

    def __init__(self, style="single", size=None):
        super().__init__()
        validstyles = ["double", "single", "spacing"]
        if style not in validstyles:
            raise RuntimeError(f"style {style} not in {validstyles}")
        self._style = style
        self._size = size

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
        (width, height) = self._region
        return "HorizontalSeparator({})".format(width)

    # drawing / redisplay
    def render(self):
        pen = self.pen()
        (w, h) = self._region
        self.clear((0, 0), (w, h))
        y = self.center(h-1)
        self.move((0, y))
        self.draw_to((w, y), HorizontalSeparator._line_chars[self._style], pen)

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
        (width, height) = self._region
        return "VerticalSeparator({})".format(height)

    # drawing / redisplay
    def render(self):
        pen = self.pen()
        (w, h) = self._region
        self.clear((0, 0), (w, h))
        x = self.center(w-1)
        self.move((x, 0))
        self.draw_to((x, h), VerticalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # Can shrink to 0 although that's probably not useful...
        length = FILL if self._size is None else self._size
        return SpaceReq(1, 1, FILL, 1, length, FILL)
