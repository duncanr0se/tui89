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
from sheets.spacereq import FILL
from geometry.transforms import Transform
from sheets.dialog import alert

from logging import getLogger

logger = getLogger(__name__)

class Viewport(Sheet):

    # Viewport's region give the extents of the VISIBLE region.

    # Viewport's "scrolling region" gives the extents of the SCROLLED
    # region.

    # scrolled sheet transform gets changed when the scrollbars are
    # altered.

    # fixme: scrolled_sheet, or just use _children?
    # _scrolled_sheet = None

    def __init__(self, contentpane, vertical_bar=None, horizontal_bar=None):
        super().__init__()
        self._scrolled_sheet = contentpane
        self.add_child(contentpane)
        self._vertical_sb = vertical_bar
        self._horizontal_sb = horizontal_bar
        if self._vertical_sb is not None:
            self._vertical_sb._viewport = self
        if self._horizontal_sb is not None:
            self._horizontal_sb._viewport = self
        self._scrolled_ltrb = (0, 0, 1, 1)

    def __repr__(self):
        if self._region is None:
            return "Viewport(=unallocated= for {})".format(self._scrolled_sheet)
        else:
            (left, top, right, bottom) = self._region
            tx = self._transform._dx
            ty = self._transform._dy
            return "Viewport({}x{}@{},{} for {})".format(right-left,
                                                         bottom-top, tx, ty,
                                                         self._scrolled_sheet)

    def add_child(self, child):
        if self._children:
            raise RuntimeError("Viewport supports a single child only")
        super().add_child(child)

    # fixme: is the ability to make the scrollbars dynamic wanted?
    def set_scrollbars(self, vertical_scrollbar=None, horizontal_scrollbar=None):
        raise NotImplementedError("No dynamic bars for now")

#    # specialise find_highest_sheet... to cater for scroll bars.
#    def find_highest_sheet_containing_position(self, parent_coord):
#        coord = self._transform.inverse().apply(parent_coord)
#        if self.region_contains_position(coord):
#            if self._vertical_sb is not None:
#                container = self._vertical_sb.find_highest_sheet_containing_position(coord)
#                if container is not None:
#                    return container
#                if self._horizontal_sb is not None:
#                    container = self._horizontal_sb.find_highest_sheet_containing_position(coor#d)
#                    if container is not None:
#                        return container
#            # only 1 child in a border layout
#            for child in self._children:
#                container = child.find_highest_sheet_containing_position(coord)
#                if container is not None:
#                    return container
#            return self
#        # this sheet doesn't contain the position
#        return None

    # FIXME: experiment with scrolling layout containing widgets,
    # esp. when it comes to dealing with events...

    # Viewport has no view of how much space it needs. Just pick some
    # not-unreasonable default.

    # Give the child as much space as is available, 'cause why not?
    def allocate_space(self, allocation):
        (l, t, r, b) = allocation
        self._region = allocation
        # the scrolled sheet has no "allocation" per se, it just accepts
        # pretty much everything.
        # Only use FILL in directions that the sheet can scroll;
        # otherwise fix the size.
        horiz_scrolling = False if self._horizontal_sb is None else True
        vert_scrolling = False if self._vertical_sb is None else True

        scroller_sr = self._scrolled_sheet.compose_space()
        width = FILL if horiz_scrolling else min(scroller_sr.x_preferred(), r-l)
        height = FILL if vert_scrolling else min(scroller_sr.y_preferred(), b-t)
        self._scrolled_sheet.allocate_space((0, 0, width, height))

    def layout(self):
        # single child
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear(self._region)
        for child in self._children:
            child.render()
        # fixme: how to deal with events?

    def _clip_text(self, coord, text):
        # measure text, cut off any that would be rendered before x=0
        # + cut off any that would be rendered after 'width'
        # coord is fixed elsewhere
        (x, y) = coord
        (l, t, r, b) = self._region
        (w, h) = (r-l, b-t)

        if y < 0 or y >= h:
            return ""

        if x < 0:
            text = text[abs(x):]
        if x < w:
            text = text[:w-x]

        return text

    def _clip(self, coord):
        (x, y) = coord
        (l, t, r, b) = self._region
        (w, h) = (r-l, b-t)

        if x >= w or y >= h:
            # coord does not intersect viewport region at all
            return None

        cx = max(min(x, w), 0)
        cy = max(min(y, h), 0)
        return (cx, cy)

    def _clip_region(self, region):
        (vl, vt, vr, vb) = self._region
        (rl, rt, rr, rb) = region
        left = vl if rl < vl else rl
        top = vt if rt < vt else rt
        right = vr if rr > vr else rr
        bottom = vb if rb > vb else rb
        return (left, top, right, bottom)

    # drawing
    def clear(self, region, pen=None):
        # Clip the region being cleared so it remains inside the
        # viewport
        clipped_region = self._clip_region(region)
        transformed_region = self._transform.transform_region(clipped_region)
        self._parent.clear(transformed_region, pen)

    # drawing
    def display_at(self, coord, text, pen):

        # capture full extents of print
        self._capture_print_at(text, coord)
        # clip to region prior to drawing
        text = self._clip_text(coord, text)
        if text != '':
            coord = self._clip(coord)
            if coord is not None:
                parent_coord = self._transform.apply(coord)
                self._parent.display_at(parent_coord, text, pen)

    # drawing
    def move(self, coord):
        self._capture_move(coord)
        coord = self._clip(coord)
        parent_coord = self._transform.apply(coord)
        self._parent.move(parent_coord)

    # drawing
    # rework contract for this to make it clear single
    # graphic characters are required; there may be
    # multiple characters in the string for multibyte
    # characters. Perhaps.
    def draw_to(self, coord, char, pen):
        self._capture_draw(coord, char)
        coord = self._clip(coord)
        parent_coord = self._transform.apply(coord)
        self._parent.draw_to(parent_coord, char, pen)

    def _capture_print_at(self, text, coord):
        # capture scroller extents in the coord system of the scrolled
        # sheet
        trans = self._scrolled_sheet._transform
        ccoord = trans.inverse().apply(coord)
        self.update_scroll_extents(ccoord)
        (x, y) = ccoord
        # not sure if it's safe to take the length of the text like
        # this...
        self.update_scroll_extents((x + len(text), y))

    def _capture_move(self, coord):
        trans = self._scrolled_sheet._transform
        ccoord = trans.inverse().apply(coord)
        self.update_scroll_extents(ccoord)

    def _capture_draw(self, coord, char):
        trans = self._scrolled_sheet._transform
        ccoord = trans.inverse().apply(coord)
        self.update_scroll_extents(coord)

    def update_scroll_extents(self, coord):
        # A new "point" has been created; need to ensure the scrolled
        # sheet is big enough to contain it and update the scrollbar
        # visuals accordingly. Note that the scrolled sheet never gets
        # expanded in a negative direction, expansion is always along
        # the positive x/y axis.
        #
        # scroll extents AND coord are in the coord system of the
        # scrolled sheet.  Keep scrolled extents and LTRB.
        #
        # Note that the "scrolled extents" is the ltrb of the scrolled
        # sheet.

        if self.ltrb_contains_position(self._scrolled_ltrb, coord):
            # nothing to do
            return

        (l, t, r, b) = self._scrolled_ltrb
        (cx, cy) = coord

        # Need the LTRB to contain the point; since points on the
        # right or bottom of the LTRB are not included in the LTRB,
        # increment the R + B values to include the new points.

        # extend along x axis?
        if r <= cx:
            r = cx+1

        # extend along y axis?
        if b <= cy:
            b = cy+1

        self._scrolled_ltrb = (l, t, r, b)

        logger.debug("viewport region=%s, scroll_extents=%s, transform=%s",
                     self._region,
                     self._scrolled_ltrb,
                     self._scrolled_sheet._transform)

        if self._vertical_sb is not None:
            self._vertical_sb.update_extents(self._scrolled_ltrb, self.height())

        if self._horizontal_sb is not None:
            self._horizontal_sb.update_extents(self._scrolled_ltrb, self.width())

    def ltrb_contains_position(self, ltrb, position):
        (l, t, r, b) = ltrb
        (x, y) = position
        return l <= x < r and t <= y < b

    def scroll_left_line(self):
        logger.info(">>> SCROLL LEFT LINE <<< for viewport {}".format(self))
        # scrolling LEFT moves scrolled sheet to the RIGHT.
        # if LHS of scrolled sheet is already showing, don't allow
        # scrolling in this direction.
        # LHS will be showing if transform is >= 0.
        delta = 1
        trans = self._scrolled_sheet._transform
        x = min(0, trans._dx+delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        # invalidating the viewport will redraw the scrolled sheet
        # beneath it
        self.invalidate()

    def scroll_right_line(self):
        logger.info(">>> SCROLL RIGHT LINE <<< for viewport {}".format(self))
        delta = 1
        trans = self._scrolled_sheet._transform
        (l,t,r,b) = self._scrolled_ltrb
        (sw, sh) = (r-l),(b-t)
        tmax = self.width() - sw
        x = max(tmax, trans._dx-delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_up_line(self):
        logger.info(">>> SCROLL UP LINE <<< for viewport {}".format(self))
        delta = 1
        trans = self._scrolled_sheet._transform
        y = min(0, trans._dy+delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_down_line(self):
        logger.info(">>> SCROLL DOWN LINE <<< for viewport {}".format(self))
        delta = 1
        trans = self._scrolled_sheet._transform
        (l,t,r,b) = self._scrolled_ltrb
        (sw, sh) = (r-l),(b-t)
        tmax = self.height() - sh
        y = max(tmax, trans._dy-delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_left_page(self):
        logger.info(">>> SCROLL LEFT PAGE <<< for viewport {}".format(self))
        delta = self.width()-1
        trans = self._scrolled_sheet._transform
        x = min(0, trans._dx+delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_right_page(self):
        logger.info(">>> SCROLL RIGHT PAGE <<< for viewport {}".format(self))
        delta = self.width()-1
        trans = self._scrolled_sheet._transform
        (l,t,r,b) = self._scrolled_ltrb
        (sw, sh) = (r-l),(b-t)
        tmax = self.width() - sw
        x = max(tmax, trans._dx-delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_up_page(self):
        logger.info(">>> SCROLL UP PAGE <<< for viewport {}".format(self))
        delta = self.height()-1
        trans = self._scrolled_sheet._transform
        y = min(0, trans._dy+delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_down_page(self):
        logger.info(">>> SCROLL DOWN PAGE <<< for viewport {}".format(self))
        delta = self.height()-1
        trans = self._scrolled_sheet._transform
        (l,t,r,b) = self._scrolled_ltrb
        (sw, sh) = (r-l),(b-t)
        tmax = self.height() - sh
        y = max(tmax, trans._dy-delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()
