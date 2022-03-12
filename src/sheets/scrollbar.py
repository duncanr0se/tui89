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
from dcs.ink import Pen
from sheets.spacereq import FILL, SpaceReq

from asciimatics.event import MouseEvent
from asciimatics.screen import Screen

import math
from logging import getLogger

logger = getLogger(__name__)

class Scrollbar(Sheet):

    def __init__(self, orientation="vertical"):
        super().__init__()
        # one of {"origin", "terminal"} indicating which button (if
        # any) to highlight
        self._highlight = None
        # one of {"horizontal", "vertical"}
        self._orientation = orientation
        self._scrolled_sheet_extent = None
        # the offset of the slug from the scrollbar origin
        self._slug_offset = None
        self._slug_size = None
        self._viewport = None

    def pen(self, role="undefined", state="default", pen="pen"):
        # By default draw in "scroll" colours - do this way for all
        # widgets by default. These colours can be intercepted by
        # parents if necessary.
        if role == "undefined":
            role = "scroll"
        return super().pen(role=role, state=state, pen=pen)

    def render(self):
        # could make all these parts individual sheets, but
        # just render them directly for now.
        #
        # Components:
        # ARROW BUTTON - one at each end
        # TROUGH - background of scrollbar
        # SLUG - foreground of scrollbar representing extents of

        # u'█' | u'░' | u'▓'

        self._draw_origin_button()
        self._draw_trough()
        self._draw_terminal_button()
        self._draw_slug()

    def _draw_origin_button(self):
        # draw "origin arrow". Bars go from top to bottom, and
        # from left to right
        arrow_left = u'◀'
        arrow_up = u'▲'
        origin_arrow = arrow_left if self._orientation == "horizontal" else arrow_up
        pen = self.pen()
        button_click_pen = self.pen("button", "transient", "pen")
        if self._highlight == "origin":
            save_pen = pen
            pen = button_click_pen
            self.display_at((0, 0), origin_arrow, pen)
            pen = save_pen
        else:
            self.display_at((0, 0), origin_arrow, pen)

    def _draw_trough(self):
        trough = u'░'
        pen = self.pen()
        (l, t, r, b) = self._region
        (rw, rh) = (r-l, b-t)
        size = rw if self._orientation == "horizontal" else rh
        if self._orientation == "horizontal":
            self.move((1, 0))
            self.draw_to((size, 0), trough, pen)
        else:
            self.move((0, 1))
            self.draw_to((0, size), trough, pen)

    def _draw_terminal_button(self):
        arrow_right = u'▶'
        arrow_down = u'▼'
        terminal_arrow = arrow_right if self._orientation == "horizontal" else arrow_down
        pen = self.pen()
        button_click_pen = self.pen("button", "transient", "pen")
        (l, t, r, b) = self._region
        (rw, rh) = (r-l, b-t)
        size = rw if self._orientation == "horizontal" else rh
        if self._orientation == "horizontal":
            # "terminal" = right button (horiz bar) or bottom button
            # (vert bar)
            if self._highlight == "terminal":
                save_pen = pen
                pen = button_click_pen
                self.display_at((size-1, 0), terminal_arrow, pen)
                pen = save_pen
            else:
                self.display_at((size-1, 0), terminal_arrow, pen)
        else:
            if self._highlight == "terminal":
                save_pen = pen
                pen = button_click_pen
                self.display_at((0, size-1), terminal_arrow, pen)
                pen = save_pen
            else:
                self.display_at((0, size-1), terminal_arrow, pen)

    def _draw_slug(self):
        slug = u'█'
        pen = self.pen()
        if self._slug_size is not None:
            if self._slug_offset is None:
                self._slug_offset = 0
            if self._orientation == "horizontal":
                # move past button
                self.move((1 + self._slug_offset, 0))
                # draw up to other button
                # :1+ to move past origin button;
                # :offset for offset;
                # :slug size for slug size;
                # :+1 because slug size is a SIZE, not an extent and
                # high coordinate is not included in draw_to
                self.draw_to((1+self._slug_offset+self._slug_size+1, 0), slug, pen)
            else:
                # move past buttons
                self.move((0, 1 + self._slug_offset))
                # draw up to other button
                self.draw_to((0, 1+self._slug_offset+self._slug_size+1), slug, pen)

    def compose_space(self):
        absolute_min = 2
        preferred = FILL
        max = FILL

        if self._orientation == "vertical":
            return SpaceReq(1, 1, 1, absolute_min, preferred, max)
        else:
            return SpaceReq(absolute_min, preferred, max, 1, 1, 1)

    # fixme: use right-click in gutter to jump to offset directly
    def handle_event(self, event):
        if isinstance(event, MouseEvent):
            if event.x == 0 and event.y == 0 and event.buttons == MouseEvent.LEFT_CLICK:
                # (0, 0) is always a button
                self._highlight = "origin"
                if self._orientation == "vertical":
                    self._viewport.scroll_up_line()
                if self._orientation == "horizontal":
                    self._viewport.scroll_left_line()
                self.invalidate()
                return
            if self._orientation == "vertical":
                if event.x == 0 and event.y == self.height()-1 \
                   and event.buttons == MouseEvent.LEFT_CLICK:
                    self._highlight = "terminal"
                    self._viewport.scroll_down_line()
                    self.invalidate()
                    return
            if self._orientation == "horizontal":
                if event.y == 0 and event.x == self.width()-1 \
                   and event.buttons == MouseEvent.LEFT_CLICK:
                    self._highlight = "terminal"
                    self._viewport.scroll_right_line()
                    self.invalidate()
                    return
            # if click in the gutter invoke "scroll_left|up|right|down_page"
            # - use the slug_offset and slug_size to work out whether click
            #   was ahead of slug or behind slug
            if self._orientation == "vertical" and event.buttons == MouseEvent.LEFT_CLICK:
                # was click in the gutter above the slug?
                if event.x == 0 and event.y < self._slug_offset:
                    self._viewport.scroll_up_page()
                    self.invalidate()
                    return
                # was click in the gutter below the slug?
                if event.x == 0 and event.y > self._slug_offset+self._slug_size:
                    self._viewport.scroll_down_page()
                    self.invalidate()
                    return
            if self._orientation == "horizontal" and event.buttons == MouseEvent.LEFT_CLICK:
                # was click in the gutter left of the slug?
                if event.y == 0 and event.x < self._slug_offset:
                    self._viewport.scroll_left_page()
                    self.invalidate()
                    return
                # was click in the gutter right of the slug?
                if event.y == 0 and event.x > self._slug_offset+self._slug_size:
                    self._viewport.scroll_right_page()
                    self.invalidate()
                    return
            if event.buttons == 0:
                # fixme: invoke the "scroll" callback
                self._highlight = None
                self.invalidate()
                return
            return False

    def update_extents(self, scrolled_sheet_ltrb, viewport_size):
        logger.debug("update_extents sheet %s viewport %s",
                     scrolled_sheet_ltrb, viewport_size)
        # normalise extents; this method is responsible for setting
        # the slug size
        (l, t, r, b) = scrolled_sheet_ltrb
        # left+top are always 0 so width+height are right+bottom
        self._scrolled_sheet_extent = r if self._orientation == "horizontal" else b
        self._viewport_extent = viewport_size
        if viewport_size > self._scrolled_sheet_extent:
            slug_ratio = 1.0
        else:
            slug_ratio = viewport_size / self._scrolled_sheet_extent
        bar_size = self._trough_size()
        self._slug_size = math.floor(bar_size * slug_ratio)

        # don't allow slug size to go below 1
        self._slug_size = max(self._slug_size, 1)

        logger.debug("slug_ratio = %s, slug_size = %s", slug_ratio, self._slug_size)

    def _trough_size(self):
        (l, t, r, b) = self._region
        (w, h) = (r-l, b-t)
        return w-2 if self._orientation == "horizontal" else h-2

    def update_scroll_offset(self, scrolled_sheet):
        # position slug in scrollbar
        transform = scrolled_sheet._transform
        viewport_offset = transform._dy if self._orientation == "vertical" else transform._dx
        offset_ratio = abs(viewport_offset) / self._scrolled_sheet_extent
        bar_size = self._trough_size()
        self._slug_offset = math.ceil(bar_size * offset_ratio)

        # ensure offset < bar size
        self._slug_offset = min(self._slug_offset, bar_size-1)

        logger.debug("viewport_offset=%s, viewport_extent=%s, sheet_extent=%s, offset_ratio=%s, bar_size=%s, slug_size=%s, slug_offset=%s",
                     viewport_offset,
                     self._viewport_extent,
                     self._scrolled_sheet_extent,
                     offset_ratio,
                     bar_size,
                     self._slug_size,
                     self._slug_offset)

    # fixme: display scroll sheet transform / extents somewhere! Would be
    # a useful indicator. In bottom border of containing border pane.
