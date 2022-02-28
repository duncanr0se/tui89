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
from sheets.spacereq import SpaceReq, FILL
from dcs.ink import Pen

class Label(Sheet):

    _label_text = None

    def __init__(self, label_text="", default_pen=None, pen=None, align=None):
        super().__init__(default_pen=default_pen, pen=pen)
        self._label_text = label_text
        valid_aligns = { None, "left", "right", "center", "centre" }
        if align not in valid_aligns:
            raise RuntimeError("label align not in valid set", align, valid_aligns)
        self._align = align

    def __repr__(self):
        (width, height) = self._region
        return "Label({}x{}, '{}')".format(width, height, self._label_text)

    def pen(self):
        if self._pen is None:
            self._pen = Frame.THEME["tv"]["label"]
        return self._pen

    def add_child(self):
        raise RuntimeError("children not allowed")

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        pen = self.frame().theme("label")
        display_text = self._label_text
        # truncate so it's possible to see at least 3+ label chars +
        # "...". If text has 3 or fewer characters and doesn't fit in
        # the available space, then that's just tough. Text will be
        # clipped.
        if len(display_text)>self.width() and len(display_text)>3:
            display_text = display_text[:self.width()-3]
            display_text += "..."
        if self._align is None or self._align == "left":
            coord = (0, 0)
        elif self._align == "right":
            coord = (self.width()-len(display_text), 0)
        else: #self._align == "center" or self._align == "centre":
            coord = ((self.width()-len(display_text)) // 2, 0)
        self.display_at(coord, display_text, pen)

    # layout
    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # todo: check if this needs a smaller minimum (3 chars + "..."?)
        return SpaceReq(len(self._label_text), len(self._label_text), FILL, 1, 1, FILL)
