
from sheets.sheet import Sheet
from dcs.ink import Pen

class TopLevelSheet(Sheet):

    _frame = None

    def __init__(self, frame, default_pen=None):
        super().__init__(default_pen=default_pen)
        self._frame = frame
        frame.set_top_level_sheet(self)

    def __repr__(self):
        (width, height) = self._region
        return "TopLevelSheet({}x{})".format(width, height)

    def clear(self, origin, region):
        pen = self.default_pen()
        (x, y) = self._transform.apply(origin)
        (w, h) = region
        for line in range(0, h):
            self._frame._screen.move(x, y + line)
            self._frame._screen.draw(x + w, y + line, u' ', colour=pen.bg(), bg=pen.bg())

    def default_pen(self):
        if self._default_pen is None:
            return self.frame().default_pen()
        return super().default_pen()

    def print_at(self, text, coord, pen):
        (x, y) = self._transform.apply(coord)
        self._frame._screen.print_at(text, x, y, colour=pen.fg(), attr=pen.attr(), bg=pen.bg())

    def move(self, coord):
        (x, y) = self._transform.apply(coord)
        self._frame._screen.move(x, y)

    def draw(self, coord, char, pen):
        (x, y) = self._transform.apply(coord)
        self._frame._screen.draw(x, y, char, colour=pen.fg(), bg=pen.bg())

    def add_child(self, child):
        if self._children:
            raise RuntimeError("TopLevelSheet supports a single child only")
        super().add_child(child)

    def top_level_sheet(self):
        return self;

    def frame(self):
        return self._frame

    # When are things laid out? After space allocation? Or as part of
    # space allocation? When is compose-space called?
    # Pretty sure the below is wrong! How to constrain children to fit
    # in available space (or to overflow)?
    def allocate_space(self, allocation):
        self._region = allocation
        for child in self._children:
            # child of top level sheet MAY NOT have a transform
            child.move_to((0, 0))
            child.allocate_space(self._region)

    def layout(self):
        for child in self._children:
            child.layout()

    def get_screen_transform(self):
        return self._transform

    def handle_event(self, event):
        # False == not handled, not that anybody cares at this point
        return False

    # attach from lowest z-order up
    def attach(self, frame):
        self._frame = frame
        for child in self._children:
            child.attach()

    # detach from highest z-order down
    def detach(self):
        # fixme: sheet lifecycle events? (mapped, detached, etc)
        for child in self._children:
            child.detach()
        self._frame = None

    def is_detached(self):
        return self._frame is None
