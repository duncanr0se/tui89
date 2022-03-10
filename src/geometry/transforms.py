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

class Transform:
    """Transform coordinates by a translation."""
    _dx = 0
    _dy = 0

    def __init__(self, dx, dy):
        self._dx = dx
        self._dy = dy

    def __repr__(self):
        return "Transform({},{})".format(self._dx, self._dy)

    def apply(self, coord):
        (x, y) = coord
        return (x + self._dx, y + self._dy)

    def inverse(self):
        return Transform(-self._dx, -self._dy)

    def add_transform(self, other):
        return Transform(self._dx + other._dx, self._dy + other._dy)

    def transform_point(self, point):
        return self.apply(point)

    def transform_region(self, region):
        (l, t, r, b) = region
        (l, t) = self.apply((l, t))
        (r, b) = self.apply((r, b))
        return (l, t, r, b)

# no-op transform
IDENTITY_TRANSFORM = Transform(0, 0)
