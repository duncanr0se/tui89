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

class Region:
    """Rectangular region"""

    def __init__(self, left, top, right, bottom):
        self._left=left
        self._top=top
        self._right=right
        self._bottom=bottom

    def __repr__(self):
        return "Region({},{},{},{})".format(self._left, self._top,
                                            self._right, self._bottom)

    def region_contains_position(self, coord):
        (cx, cy) = coord.xy()
        # yes if its on the left or top boundary, no if it's on the
        # right or bottom boundary.
        return self._left <= cx < self._right \
            and self._top <= cy < self._bottom

    def region_intersects_region(self, region):
        (l2, t2, r2, b2) = region.ltrb()
        return (self._left <= l2 < self._right or self._left < r2 <= self._right) \
            and (self._top <= t2 < self._bottom or self._top < b2 <= self._bottom)

    def region_width(self):
        return self._right-self._left

    def region_height(self):
        return self._bottom-self._top

    def ltrb(self):
        return (self._left, self._top, self._right, self._bottom)
