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
from sheets.spacereq import SpaceReq, FILL
from geometry.regions import Region
from geometry.points import Point
from dcs.ink import Pen
from frames.frame import Frame

from logging import getLogger

logger = getLogger(__name__)

class BorderLayout(Sheet):
    """Sheet that draws a border around itself.

    Manages a single child and can display scroll bars in the space
    reserved for the border.

    Initargs:
        - title
        - style

    The following border styles are recognised:
        - double : border made of double bars
        - single : border made of single bars
        - spacing : empty space used for border
        - scrolling : border on bottom and right sides of sheet
                 only
        - title : border only on top edge

    All border styles display borders on all sides of the sheet
    except for "scrolling" which displays borders on just the
    right and bottom edges, and "title" which displays a border
    only on the top edge.

    If the title initarg is provided then all styles of border
    layout render the title along the top edge of the sheet
    except for the "scrolling" style which does not show the
    title.
    """
    supported_styles = ["double", "single", "spacing"]

    def __init__(self,
                 title=None,
                 style="double"):

        super().__init__()

        self._validate_style(style)

        self._border = style
        self._horizontal_sb = None
        self._title = title
        self._vertical_sb = None
        # todo: title align

    def _validate_style(self, style):
        if style not in BorderLayout.supported_styles:
            raise NotImplementedError("Border layout only supports {} style currently"
                                      .format(supported_styles))

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "BorderLayout({}x{}@{},{}: '{}')".format(
            self._region.region_width(),
            self._region.region_height(),
            tx, ty, self._title)

    def add_child(self, child):
        if self._children:
            raise RuntimeError("BorderLayout supports a single child only")
        super().add_child(child)

    def set_scrollbars(self, vertical_scrollbar=None, horizontal_scrollbar=None):
        if vertical_scrollbar is not None:
            self._vertical_sb = vertical_scrollbar
            vertical_scrollbar._parent = self
            if self.is_attached():
                vertical_scrollbar.attach()

        if horizontal_scrollbar is not None:
            self._horizontal_sb = horizontal_scrollbar
            horizontal_scrollbar._parent = self
            if self.is_attached():
                horizontal_scrollbar.attach()

    # specialise find_highest_sheet... to cater for scroll bars.
    def find_highest_sheet_containing_position(self, parent_coord, log_indent=" "):
        coord = self._transform.inverse().transform_point(parent_coord)
        if self._region.region_contains_position(coord):
            logger.debug("%s found sheet containing position %s %s",
                         log_indent, coord, self)
            if self._vertical_sb is not None:
                container = self._vertical_sb.find_highest_sheet_containing_position(coord,
                                                                                     log_indent+"  ")
                if container is not None:
                    return container
                if self._horizontal_sb is not None:
                    container = self._horizontal_sb.find_highest_sheet_containing_position(coord, log_indent+"  ")
                    if container is not None:
                        return container
            # only 1 child in a border layout
            for child in self._children:
                container = child.find_highest_sheet_containing_position(coord, log_indent+"  ")
                if container is not None:
                    return container
            return self
        # this sheet doesn't contain the position
        return None

    def attach(self):
        super().attach()
        if self._horizontal_sb is not None:
            self._horizontal_sb.attach()
        if self._vertical_sb is not None:
            self._vertical_sb.attach()

    def detach(self):
        if self._vertical_sb is not None:
            self._vertical_sb.detach()
        if self._horizontal_sb is not None:
            self._horizontal_sb.detach()
        super().detach()

    # Ask children how much space it needs, add in the border, use
    # that as the space request
    def compose_space(self):
        sr = SpaceReq(1, 10, FILL, 1, 10, FILL)
        # Border layout has single child
        for child in self._children:
            sr = child.compose_space()
        xmin = min(sr.x_min()+2, FILL)
        xdes = min(sr.x_preferred()+2, FILL)
        xmax = min(sr.x_max()+2, FILL)

        ymin = min(sr.y_min()+2, FILL)
        ydes = min(sr.y_preferred()+2, FILL)
        ymax = min(sr.y_max()+2, FILL)
        return SpaceReq(xmin, xdes, xmax, ymin, ydes, ymax)

        
    # BorderLayout expects its children to completely fill it, but
    # it's not an arse about it, it's happy for kids to be their
    # preferred size if they want to be. However, it does insist on
    # their origin being (0, 0). For more flexibility add a different
    # layout type as the child of the border box.
    def allocate_space(self, allocation):
        self._region = allocation
        (calloc_x, calloc_y) = (allocation.region_width()-2,
                                allocation.region_height()-2)
        for child in self._children:
            # borderlayout has a single child - give it all the space
            # the border doesn't need for itself without allocating
            # more than the child's maximum. It doesn't matter if the
            # child ends up too small it will just overflow its
            # bounds.
            child_request = child.compose_space()
            calloc_x = min(calloc_x, child_request.x_max())
            calloc_y = min(calloc_y, child_request.y_max())
            child.allocate_space(Region(0, 0, 0+calloc_x, 0+calloc_y))
        # deal with scrollbars specially because they aren't treated
        # as children of the border pane.
        if self._vertical_sb is not None:
            child_request = self._vertical_sb.compose_space()
            # use the minimum width and the border pane's inner height
            self._vertical_sb.allocate_space(Region(0, 0, child_request.x_min(),
                                                    allocation.region_height()-2))
        if self._horizontal_sb is not None:
            child_request = self._horizontal_sb.compose_space()
            # use minimum height and border pane's width and border
            # pane's inner width; + an extra reduction because the
            # horizontal bar rhs is offset by an extra unit for L+F
            self._horizontal_sb.allocate_space(Region(0, 0, allocation.region_width()-3,
                                                      child_request.y_min()))

    def layout(self):
        # single child
        for child in self._children:
            child.move_to(Point(1, 1))
            child.layout()
        (_, _, right, bottom) = self._region.ltrb()
        if self._vertical_sb is not None:
            self._vertical_sb.move_to(Point(right-1, 1))
            self._vertical_sb.layout()
        if self._horizontal_sb is not None:
            # fixme: how wide should horizontal bars be? turbo vision
            # looks to give about 50% of the pane width...
            self._horizontal_sb.move_to(Point(1, bottom-1))
            self._horizontal_sb.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear(self._region)
        self._draw_border()
        for child in self._children:
            child.render()
        if self._vertical_sb is not None:
            self._vertical_sb.render()
        if self._horizontal_sb is not None:
            self._horizontal_sb.render()

    border_chars = {
        "double": {
            "nw":   u'???', "top": u'???',    "ne": u'???',
            "left": u'???',              "right": u'???',
            "sw":   u'???', "bottom": u'???', "se": u'???'
        },
        "single": {
            "nw":   u'???', "top": u'???',    "ne": u'???',
            "left": u'???',              "right": u'???',
            "sw":   u'???', "bottom": u'???', "se": u'???'
        },
        "spacing": {
            "nw":   ' ', "top": ' ',    "ne": ' ',
            "left": ' ',              "right": ' ',
            "sw":   ' ', "bottom": ' ', "se": ' '
        }
    }

    def pen(self, role="undefined", state="default", pen="pen"):
        # use defaults for sheet, if there are any
        if role == "undefined":
            role = "border"
        drawing_pen = super().pen(role=role, state=state, pen=pen)
        return drawing_pen

    def _draw_border(self):
        pen = self.pen(role="border", state="default", pen="pen")
        self._cached_pen = pen
        (left, top, right, bottom) = self._region.ltrb()

        # todo: deal with long titles
        charset = self.border_chars[self._border]
        # top border - make allowances for a title
        self.display_at(Point(left, top), charset["nw"], pen)
        self.move(Point(1, top))
        if self._title:
            # LHS of bar + title
            bar_width = right-left
            title = ' ' + self._title + ' '
            title_width = len(title)
            side_bar_width = (bar_width - title_width) // 2
            self.draw_to(Point(side_bar_width+1, top), charset["top"], pen)
            self.display_at(Point(side_bar_width, top), title, pen)
            self.move(Point(side_bar_width + title_width, top))
            self.draw_to(Point(right, top), charset["top"], pen)
        else:
            self.draw_to(Point(right, top), charset["top"], pen)
        self.display_at(Point(right-1, top), charset["ne"], pen)

        # left border
        self.move(Point(left, top+1))
        self.draw_to(Point(left, bottom), charset["left"], pen)

        # right border - might be scroll bar
        if self._vertical_sb is None:
            self.move(Point(right-1, top + 1))
            self.draw_to(Point(right-1, bottom), charset["right"], pen)
        else:
            # scrollbar will draw itself
            pass

        # bottom border - might be scroll bar
        self.display_at(Point(left, bottom-1), charset["sw"], pen)
        if self._horizontal_sb is None:
            self.move(Point(left+1, bottom-1))
            self.draw_to(Point(right, bottom-1), charset["bottom"], pen)
            self.display_at(Point(right-1, bottom-1), charset["se"], pen)
        else:
            self.display_at(Point(right-2, bottom-1), u'???', pen)
            self.display_at(Point(right-1, bottom-1), u'???', pen)
            # scrollbar will draw itself
