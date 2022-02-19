
from sheets.sheet import Sheet
from dcs.ink import Pen
from sheets.spacereq import FILL

from asciimatics.event import MouseEvent
from asciimatics.screen import Screen

class Scrollbar(Sheet):

    _orientation = None
    # one of "origin" or "terminal"
    _highlight = None

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

    def compose_space(self):
        absolute_min = 2
        preferred = FILL
        max = FILL

        if self._orientation == "vertical":
            return ((1, 1, 1), (absolute_min, preferred, max))
        else:
            return ((absolute_min, preferred, max), (1, 1, 1))

    # fixme: scroll bar button press event action
    def handle_event(self, event):
        if isinstance(event, MouseEvent):
            if event.x == 0 and event.y == 0 and event.buttons == MouseEvent.LEFT_CLICK:
                # (0, 0) is always a button
                self._highlight = "origin"
                self.invalidate()
            if self._orientation == "vertical":
                if event.x == 0 and event.y == self.height()-1 \
                   and event.buttons == MouseEvent.LEFT_CLICK:
                    self._highlight = "terminal"
                    self.invalidate()
            if self._orientation == "horizontal":
                if event.y == 0 and event.x == self.width()-1 \
                   and event.buttons == MouseEvent.LEFT_CLICK:
                    self._highlight = "terminal"
                    self.invalidate()
            if event.buttons == 0:
                # fixme: invoke the "scroll" callback
                self._highlight = None
                self.invalidate()
            return False
