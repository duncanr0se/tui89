
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired

# A layout that arranges its children in columns
class BoxLayout(Sheet):

    # list of relative widths or absolute values
    _portions = None

    def __init__(self, portions):
        super().__init__()
        self._portions = portions

    def add_child(self, child):
        super().add_child(child)


class HorizontalLayout(BoxLayout):

    def __init__(self, columns):
        super().__init__(columns)

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "HorizontalLayout({}x{}@{},{}: {} cols)".format(
            width, height, tx, ty, len(self._portions))

    # Box layouts don't need to be full of children; they leave empty
    # space at the end if the children are exhausted before the
    # columns are all filled. Each child is given an offset so they
    # are placed at the left / top of the box cell they occupy.
    def allocate_space(self, allocation):
        # Work out max height of children; use as height of layout.
        # Split allocation width into chunks as specified by columns list.
        # Allocate each child the width, height given by its corresponding
        # column.
        #
        # What the hell, let's just be really inefficient first. Fix it
        # up to be more efficient later...
        self._region = allocation
        (width, height) = allocation
        totalSegments = 0
        for column in self._portions:
            totalSegments += column
        segmentSize = width // totalSegments
        surplus = width - segmentSize*totalSegments
        for index, child in enumerate(self._children):
            callocx = self._portions[index] * segmentSize
            if surplus > 0:
                callocx += 1
                surplus -= 1
            child.allocate_space((callocx, height))

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((offset, 0))
            offset += child.width()
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear((0, 0), self._region)
        for child in self._children:
            child.render()


# A layout that arranges its children in rows
class VerticalLayout(BoxLayout):

    def __init__(self, rows):
        super().__init__(rows)

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "VerticalLayout({}x{}@{},{}: {} rows)".format(
            width, height, tx, ty, len(self._portions))

    # Box layouts don't need to be full of children; they leave empty
    # space at the end if the children are exhausted before the
    # columns are all filled. Each child is given an offset so they
    # are placed at the left / top of the box cell they occupy.
    def allocate_space(self, allocation):
        # Work out max height of children; use as height of layout.
        # Split allocation width into chunks as specified by columns list.
        # Allocate each child the width, height given by its corresponding
        # column.
        #
        # What the hell, let's just be really inefficient first. Fix it
        # up to be more efficient later...
        self._region = allocation
        (width, height) = allocation
        totalSegments = 0
        for row in self._portions:
            totalSegments += row
        segmentSize = height // totalSegments
        # collect rounding errors as surplus
        surplus = height - segmentSize*totalSegments
        for index, child in enumerate(self._children):
            callocy = self._portions[index] * segmentSize
            # if there is surplous, dole it out to each child until it
            # is exhausted
            if surplus > 0:
                callocy += 1
                surplus -= 1
            child.allocate_space((width, callocy))

    # perhaps this should be the thing that calls compose-space
    # followed by allocate-space? With compose-space on kids in turn
    # calling layout? Probably best to follow same pattern as DUIM if
    # only for consistency in my own stuff...
    #
    # maybe allocate_space should call layout() if the region changes?
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
