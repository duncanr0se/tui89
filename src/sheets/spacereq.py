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

FILL = 8080  # Go with DUIM's 100 screens


class SpaceReq():

    def __init__(self, minx, desx, maxx, miny, desy, maxy):
        self._xmax = _fill_or(maxx)
        self._xmin = _fill_or(minx)
        self._xpref = _fill_or(desx)
        self._ymax = _fill_or(maxy)
        self._ymin = _fill_or(miny)
        self._ypref = _fill_or(desy)

    def __repr__(self):
        return "SpaceReq([{},{},{}], [{},{},{}])".format(
            self.x_min() if self.x_min() < FILL else "FILL",
            self.x_preferred() if self.x_preferred() < FILL else "FILL",
            self.x_max() if self.x_max() < FILL else "FILL",
            self.y_min() if self.y_min() < FILL else "FILL",
            self.y_preferred() if self.y_preferred() < FILL else "FILL",
            self.y_max() if self.y_max() < FILL else "FILL")

    def x_max(self):
        return self._xmax

    def x_preferred(self):
        return self._xpref

    def x_min(self):
        return self._xmin

    def y_max(self):
        return self._ymax

    def y_preferred(self):
        return self._ypref

    def y_min(self):
        return self._ymin


def _fill_or(n):
    return n if n < FILL else FILL

def combine_spacereqs(sr1, sr2):
    min_x = _fill_or(sr1._xmin + sr2._xmin)
    pref_x = _fill_or(sr1._xpref + sr2._xpref)
    max_x = _fill_or(sr1._xmax + sr2._xmax)

    min_y = _fill_or(sr1._ymin + sr2._ymin)
    pref_y = _fill_or(sr1._ypref + sr2._ypref)
    max_y = _fill_or(sr1._ymax + sr2._ymax)

    return SpaceReq(min_x, pref_x, max_x, min_y, pref_y, max_y)
