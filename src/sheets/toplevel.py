
from sheets.sheet import Sheet

class TopLevelSheet(Sheet):

    _frame = None

    def __init__(self, frame):
        super().__init__()
        self._frame = frame
        frame.set_top_level_sheet(self)

    def __repr__(self):
        (width, height) = self._region
        return "TopLevelSheet({}x{})".format(width, height)

    def clear(self, origin, region):
        (colour, attr, bg) = self._frame.theme()["background"]
        (x, y) = origin
        (w, h) = region
        for line in range(0, h):
            self._frame._screen.move(x, y + line)
            self._frame._screen.draw(x + w, y + line, u' ', colour=colour, bg=bg)

    def print_at(self, text, coord, colour=7, attr=0, bg=0):
        (x, y) = coord
        self._frame._screen.print_at(text, x, y, colour=colour, attr=attr, bg=bg)

    def move(self, coord):
        (x, y) = coord
        self._frame._screen.move(x, y)

    def draw(self, coord, char, colour=7, bg=0):
        (x, y) = coord
        self._frame._screen.draw(x, y, char, colour=colour, bg=bg)

    #def render(self):
    #    for child in self._children:
    #        child.render()

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
