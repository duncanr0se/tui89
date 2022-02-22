
from sheets.sheet import Sheet

from sheets.spacereq import FILL, SpaceReq

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings
class ListLayout(Sheet):

    # see if class will work without this call... test pen, default pen
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
            ch = sr.y_preferred()
            child.allocate_space((width, ch), force=True)

    def compose_space(self):
        reqheight = 0
        reqwidth = 0
        minwidth = 0
        minheight = 0
        for child in self._children:
            sr = child.compose_space()
            minwidth = max(minwidth, sr.x_min())
            # horizontal separators have their desired space set to
            # FILL, which is probably not ideal...
            if sr.x_preferred() != FILL:
                reqwidth = max(reqwidth, sr.x_preferred())
            minheight += sr.y_min()
            reqheight += sr.y_preferred()
        return SpaceReq(minwidth, reqwidth, FILL, minheight, reqheight, FILL)
