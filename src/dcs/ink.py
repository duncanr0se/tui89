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

from logging import getLogger

logger = getLogger(__name__)

class Pen():

    def __init__(self, fg=7, attr=0, bg=0, fill=' '):
        self._foreground = fg
        self._attribute = attr
        self._background = bg
        self._fill = fill

    def __repr__(self):
        type = "Pen"
        if self.fg() is None or self.bg() is None or self.attr() is None or self.fill() is None:
            type = "PartialPen"
        return f"{type}(fg={self.fg()},attr={self.attr()},bg={self.bg()},fill='{self.fill()}')"

    def fg(self):
        return self._foreground

    def attr(self):
        return self._attribute

    def bg(self):
        return self._background

    def fill(self):
        return self._fill


    def merge(self, other):
        logger.debug("merge %s into %s", other, self)
        fg = other.fg() if self.fg() is None else self.fg()
        attr = other.attr() if self.attr() is None else self.attr()
        bg = other.bg() if self.bg() is None else self.bg()
        fill = other.fill() if self.fill() is None else self.fill()

        return Pen(fg, attr, bg, fill)
