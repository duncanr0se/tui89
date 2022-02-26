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

    #_style = None
    #_size = None

    def __init__(self, style="single", size=None, default_pen=None, pen=None):
        super().__init__(default_pen=default_pen, pen=pen)
        self._style = style
        self._size = size

    def add_child(self):
        raise RuntimeError("children not allowed")

class HorizontalSeparator(Separator):

    _line_chars = {
        "double": u'═',
        "single": u'─',
        "spacing": ' '
    }

#    def __init__(self, style="single", size=None):
#        super().__init__(style, size)

    def __repr__(self):
        (width, height) = self._region
        return "HorizontalSeparator({})".format(width)

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        # todo: label truncation
        pen = self.pen()
        (w, h) = self._region
        self.move((0, 0))
        self.draw_to((w, 0), HorizontalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        length = FILL if self._size is None else self._size
        return SpaceReq(1, length, FILL, 1, 1, 1)


class VerticalSeparator(Separator):

    _line_chars = {
        "double": u'║',
        "single": u'│',
        "spacing": ' '
    }

#    def __init__(self, style="single", size=None):
#        super().__init__(style, size)

    def __repr__(self):
        (width, height) = self._region
        return "VerticalSeparator({})".format(height)

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        # todo: label truncation
        pen = self.pen()
        (w, h) = self._region
        self.move((0, 0))
        self.draw_to((0, h), VerticalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # Can shrink to 0 although that's probably not useful...
        length = FILL if self._size is None else self._size
        return SpaceReq(1, 1, 1, 1, length, FILL)
