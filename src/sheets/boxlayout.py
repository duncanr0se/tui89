
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired

# A layout that arranges its children in columns
class HorizontalLayout(Sheet):

    # list of relative widths or absolute values
    _columns = None

    def __init__(self, columns):
        super().__init__()
        self._columns = columns

    def add_child(self, child):
        super().add_child(child)

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
        for column in self._columns:
            totalSegments += column
        segmentSize = width // totalSegments
        surplus = width - segmentSize*totalSegments
        for index, child in enumerate(self._children):
            callocx = self._columns[index] * segmentSize
            if surplus > 0:
                callocx += 1
                surplus -= 1
            child.allocate_space((callocx, height))

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((offset, 0))
            offset += child.width()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        for child in self._children:
            child.render()


# A layout that arranges its children in rows
class VerticalLayout(Sheet):

    # list of relative widths or absolute values
    _rows = None

    def __init__(self, rows):
        super().__init__()
        self._rows = rows

    def add_child(self, child):
        super().add_child(child)

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
        for row in self._rows:
            totalSegments += row
        segmentSize = height // totalSegments
        surplus = height - segmentSize*totalSegments
        for index, child in enumerate(self._children):
            callocy = self._rows[index] * segmentSize
            if surplus > 0:
                callocy += 1
                surplus -= 1
            child.allocate_space((width, callocy))

    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((0, offset))
            offset += child.height()
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        for child in self._children:
            child.render()
