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

class Pen():

    _foreground = None
    _attribute = None
    _background = None

    def __init__(self, fg=7, attr=0, bg=0):
        self._foreground = fg
        self._attribute = attr
        self._background = bg

    def fg(self):
        return self._foreground

    def attr(self):
        return self._attribute

    def bg(self):
        return self._background
