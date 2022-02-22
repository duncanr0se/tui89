
from sheets.sheet import Sheet

from sheets.spacereq import FILL, SpaceReq
from sheets.frame import Frame
from dcs.ink import Pen

# A layout that arranges its children in a row. Each child is
# packed as closely as possible to its siblings
class MenubarLayout(Sheet):

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((offset, 0))
            offset += child.width()
            child.layout()

    # override default pen for this sheet and all its children
    def default_pen(self):
        if self._default_pen is None:
            (fg, attr, bg) = Frame.THEMES["tv"]["menubar"]
            self._default_pen = Pen(fg=fg, attr=attr, bg=bg)
        return self._default_pen

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # layouts always clear their background; concrete widgets may
        # choose to do so if they need to but most will fill their
        # region anyway and they can rely on empty space being the
        # default background colour.
        (w, h) = self._region
        self.clear((0, 0), self._region)
        self.move((0, 0))
        self.draw((w, 0), ' ', self.pen())
        for child in self._children:
            child.render()

    # give each child as much space as they want
    def allocate_space(self, allocation):
        # height = 1
        # width = sum of all widths

        # make scrollbar as wide as its parent allows
        self._region = allocation
        (width, height) = allocation

        # simple sauce; loop over kids and allocate them the space
        # they want, hope they don't want too much! Use the list
        # control (built-in scrolling) if more space is needed...

        for child in self._children:
            sr = child.compose_space()
            cw = sr.x_preferred()
            # fixme: take the minimum of the button
            child.allocate_space((cw, 1))

    def compose_space(self):
        return SpaceReq(1, FILL, FILL, 1, 1, 1)

    # fixme: add some functions to take a bunch of labels and
    # callbacks and build menus out of them?
