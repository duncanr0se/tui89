
from sheets.sheet import Sheet
from dcs.ink import Pen
from sheets.spacereq import FILL

from asciimatics.event import MouseEvent
from asciimatics.screen import Screen

class Scrollbar(Sheet):

    _orientation = None
    # one of "origin" or "terminal"
    _highlight = None

    _scrolled_sheet_extent = None
    _slug_size = None
    _slug_offset = None

    _viewport = None

    def __init__(self, orientation="vertical"):
        super().__init__()
        self._orientation = orientation

    def render(self):
        pen = self.frame().theme("scroll")
        # could make all these parts individual sheets, but
        # just render them directly for now.
        #
        # Components:
        # ARROW BUTTON - one at each end
        # TROUGH - background of scrollbar
        # SLUG - foreground of scrollbar representing extents of
        # scrolled sheet
        arrow_left = u'◀'
        arrow_right = u'▶'
        arrow_up = u'▲'
        arrow_down = u'▼'
        trough = u'▓'
        slug = u'█'

        # u'█' | u'░'

        # draw "origin arrow". Bars go from top to bottom, and
        # from left to right
        origin_arrow = arrow_left if self._orientation == "horizontal" else arrow_up
        terminal_arrow = arrow_right if self._orientation == "horizontal" else arrow_down
        (rw, rh) = self._region
        size = rw if self._orientation == "horizontal" else rh

        button_click_pen = self.frame().theme("borders")

        if self._highlight == "origin":
            save_pen = pen
            pen = button_click_pen
            self.print_at(origin_arrow, (0, 0), pen)
            pen = save_pen
        else:
            self.print_at(origin_arrow, (0, 0), pen)

        if self._orientation == "horizontal":
            self.move((1, 0))
            self.draw((size-1, 0), trough, pen)
            if self._highlight == "terminal":
                save_pen = pen
                pen = button_click_pen
                self.print_at(terminal_arrow, (size-1, 0), pen)
                pen = save_pen
            else:
                self.print_at(terminal_arrow, (size-1, 0), pen)
        else:
            self.move((0, 1))
            self.draw((0, size-1), trough, pen)
            if self._highlight == "terminal":
                save_pen = pen
                pen = button_click_pen
                self.print_at(terminal_arrow, (0, size-1), pen)
                pen = save_pen
            else:
                self.print_at(terminal_arrow, (0, size-1), pen)
        # draw slug
        if self._slug_size is not None:
            if self._slug_offset is None:
                self._slug_offset = 0
            if self._orientation == "horizontal":
                # move past button
                self.move((1 + self._slug_offset, 0))
                # draw up to other button
                self.draw((self._slug_offset + self._slug_size, 0), slug, pen)
            else:
                # move past buttons
                self.move((0, 1 + self._slug_offset))
                # draw up to other button
                self.draw((0, self._slug_offset + self._slug_size), slug, pen)

    def compose_space(self):
        absolute_min = 2
        preferred = FILL
        max = FILL

        if self._orientation == "vertical":
            return ((1, 1, 1), (absolute_min, preferred, max))
        else:
            return ((absolute_min, preferred, max), (1, 1, 1))

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

    # something in either the extents update or the offset update is
    # not right because the further to the right you scroll, the less
    # the scroll affects the display.

    # fixme: I think that the extents are being updated when the sheet
    # is scrolled to the left, when it should not be. Need to be sure
    # to hold extents in the coords of the SCROLLED SHEET, not of the
    # VIEWPORT which is what we're doing currently.
    def update_extents(self, scrolled_sheet_extent, viewport_extent):
        # normalise extents; this method is responsible for setting
        # the slug size
        self._scrolled_sheet_extent = scrolled_sheet_extent
        if viewport_extent < scrolled_sheet_extent:
            # input: bar length, scrolled sheet extent, viewport extent
            (w, h) = self._region
            bar_length = w-2 if self._orientation == "horizontal" else h-2
            slug_ratio = (viewport_extent / scrolled_sheet_extent)
            self._slug_size = max(slug_ratio * bar_length, 1)
        else:
            self._slug_size = None

    def update_scroll_offset(self, scrolled_sheet):
        # position slug in scrollbar
        extent = self._scrolled_sheet_extent
        (rw, rh) = self._region
        bar_size = rw if self._orientation == "horizontal" else rh
        lines_per_bar_unit = bar_size / extent
        transform = scrolled_sheet._transform
        delta = transform._dy if self._orientation == "vertical" else transform._dx
        offset = abs(delta) * lines_per_bar_unit
        # if not at end of scroll range make sure sb reflects there
        # are remaining lines, don't abut the slug + button unless
        # there is no scroll in that direction remaining - good idea,
        # but this isn't working as it stands. Fix it.
        offset_min = 0
        offset_max = bar_size - 1 - self._slug_size
        if offset == offset_min and delta > offset_min:
            offset = 1
        if offset == offset_max and delta < offset_max:
            offset = offset_max-1
        self._slug_offset = int(offset)

    # fixme: display scroll sheet transform / extents somewhere! Would be
    # a useful indicator. In bottom border of containing border pane.
