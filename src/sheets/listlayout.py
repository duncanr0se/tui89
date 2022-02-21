
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import FILL

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings
class ListLayout(Sheet):

    # see if class will work without this call...
#    def __init__(self):
#        super().__init__()

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
        # min? not sure how small it can go
        # max? FILL

        self._region = allocation
        (width, height) = allocation

        # simple sauce; loop over kids and allocate them the space
        # they want, hope they don't want too much! Use the list
        # control (built-in scrolling) if more space is needed...

        for child in self._children:
            sr = child.compose_space()
            ch = ySpaceReqDesired(sr)
            child.allocate_space((width, ch))

    def compose_space(self):
        reqheight = 0
        reqwidth = 0
        for child in self._children:
            sr = child.compose_space()
            reqwidth = max(reqwidth, xSpaceReqDesired(sr))
            reqheight += ySpaceReqDesired(sr)
        return ((1, reqwidth, FILL), (1, reqheight, FILL))
