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

from sheets.sheet import Sheet

from sheets.spacereq import FILL, SpaceReq

from logging import getLogger

logger = getLogger(__name__)

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings
class ListLayout(Sheet):

    def __init__(self):
        super().__init__()

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((0, offset))
            offset += child.height()
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # layouts always clear their background; concrete widgets may
        # choose to do so if they need to but most will fill their
        # region anyway and they can rely on empty space being the
        # default background colour.
        self.clear((0, 0), self._region)
        for child in self._children:
            child.render()

    # give each child as much space as they want
    def allocate_space(self, allocation):
        # height = sum of all heights
        # width = max of all widths
        # min = max of all mins
        # max = FILL

        self._region = allocation
        (width, height) = allocation

        # simple sauce; loop over kids and allocate them the space
        # they want, hope they don't want too much! Use the list
        # control (built-in scrolling) if more space is needed...
        for child in self._children:
            sr = child.compose_space()
            ch = sr.y_preferred() if sr.y_preferred() < FILL else sr.y_min()
            child.allocate_space((width, ch))

    def compose_space(self):
        reqheight = 0
        reqwidth = 0
        minwidth = 0
        minheight = 0
        for child in self._children:
            sr = child.compose_space()
            minwidth = max(minwidth, sr.x_min())
            # horizontal separators have their desired space set to
            # FILL, which is probably not ideal...
            if sr.x_preferred() < FILL:
                reqwidth = max(reqwidth, sr.x_preferred())
            minheight += sr.y_min()
            reqheight += sr.y_preferred()
        return SpaceReq(minwidth, reqwidth, FILL, minheight, reqheight, FILL)


class ButtonBox(ListLayout):

    def pen(self, role="undefined", state="default", pen="pen"):
        # If "buttonbox" is used in place of all other roles, the
        # background is filled in the buttonbox colours instead of in
        # the colour of the parent.
        if role == "button":
            role = "buttonbox"
        return super().pen(role=role, state=state, pen=pen)
