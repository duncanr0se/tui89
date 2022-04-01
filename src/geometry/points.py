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

class Point:
    """Singular point"""

    def __init__(self, x, y):
        self._x=x
        self._y=y

    def __repr__(self):
        return "Point({},{})".format(self._x, self._y)

    def point_x(self):
        return self._x

    def point_y(self):
        return self._y

    def xy(self):
        return (self._x, self._y)
