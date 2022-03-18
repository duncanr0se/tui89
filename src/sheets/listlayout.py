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

class ListLayout(Sheet):
    """A layout that arranges its children in a column.

    Each child is packed as closely as possible to its siblings.
    """
    def __init__(self):
        super().__init__()

    def __repr__(self):
        (l, t, r, b) = self._region
        return f"ListLayout({r-l}x{b-t}: {len(self._children)} entries)"

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((0, offset))
            offset += child.height()
            child.layout()

    # fixme: manipulating children should be done in the Sheet type I
    # think - no need to replicate this logic all over.
    def clear_children(self):
        while len(self._children) > 0:
            # pop removes last elt in list, so this detaches highest
            # z-order first
            child = self._children.pop()
            child.detach()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # layouts always clear their background; concrete widgets may
        # choose to do so if they need to but most will fill their
        # region anyway and they can rely on empty space being the
        # default background colour.
        self.clear(self._region)
        for child in self._children:
            child.render()

    def allocate_space(self, allocation):
        (l, t, r, b) = allocation
        self._region = allocation

        # meta indexes
        (WIDGET, SPACEREQ, HEIGHT)=range(0, 3)

        # Loop over children and allocate space to fixed-size items
        # and items that can't shrink (height = 1). Then allocate
        # remaining space to items that can shrink to make them fit.

        # First: see if they fit naturally. Memoise space requirements
        # so they don't have to be calculated again later.
        child_meta = []
        total_child_size = 0
        allocated_space = 0
        for child in self._children:
            sr = child.compose_space()
            # allocate space to widgets that won't shrink (fixed
            # height) or that can't shrink (height=1) instead of
            # remembering them for later
            ch = sr.y_preferred() if sr.y_preferred() < FILL else sr.y_min()
            if sr.y_min() == sr.y_preferred():
                child.allocate_space((l, t, r, t+ch))
                allocated_space += ch
            else:
                child_meta.append([child, sr, ch])
            total_child_size += ch

        # fixed-height elements already have space allocated; see if
        # there's room to allocate resizable elements directly
        if len(child_meta) > 0:
            if total_child_size <= self.height():
                # there's room for all; just allocate requested sizes
                for child in child_meta:
                    child[WIDGET].allocate_space((l, t, r, t+child[HEIGHT]))
                return

        # work out how much to take off remaining resizable items
        while len(child_meta) > 0:
            remaining_space = max(0, self.height()-allocated_space)
            space_per_item = remaining_space // len(child_meta)
            logger.info("----> remaining_space=%s, space_per_item=%s",
                        remaining_space, space_per_item)
            child = child_meta.pop()
            # allocate as much space as possible to the widget
            # without going below its minimum
            widget_height = max(space_per_item, child[SPACEREQ].y_min())
            logger.info("----> widget_height=%s", widget_height)
            child[WIDGET].allocate_space((l, t, r, t+widget_height))
            allocated_space += widget_height


    def compose_space(self):
        (reqheight, reqwidth, minwidth, minheight) = (0,)*4
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
