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

sr_x = 0
sr_y = 1
sr_min = 0
sr_pref = 1
sr_max = 2

class SpaceReq():

    def __init__(self, minx, desx, maxx, miny, desy, maxy):
        self._xmax = maxx
        self._xmin = minx
        self._xpref = desx
        self._ymax = maxy
        self._ymin = miny
        self._ypref = desy

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


def combine_spacereqs(sr1, sr2):
    min_x = sr1._xmin + sr2._xmin
    pref_x = sr1._xpref + sr2._xpref
    max_x = sr1._xmax + sr2._xmax

    min_y = sr1._ymin + sr2._ymin
    pref_y = sr1._ypref + sr2._ypref
    max_y = sr1._ymax + sr2._ymax

    return SpaceReq(min_x, pref_x, max_x, min_y, pref_y, max_y)
