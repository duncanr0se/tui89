
from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.spacereq import FILL

# ALL sheets are "drawing sheets". ALL sheets have children. ALL
# sheets participate in layout.
class Sheet():

    _parent = None
    _region = None  # width x height allocated to the sheet, at 0,0
    _transform = IDENTITY_TRANSFORM  # sheet coords -> parent coords

    # children at the front are lower in the z-order (get rendered
    # first)
    _children = None

    def __init__(self):
        self._children = []

    def __repr__(self):
        (width, height) = self._region
        return "Sheet({}x{})".format(width, height)

    # drawing
    def clear(self, origin, region):
        porigin = self._transform.apply(origin)
        self._parent.clear(porigin, region)

    # drawing
    def print_at(self, text, coord, colour=None, attr=None, bg=None):
        # transform coords all the way up to the top-level-sheet and
        # invoke print_at on t-l-s. Has to be better than expecting
        # every sheet in the hierarchy to implement the drawing
        # methods... or maybe not. Hrm.
        parent_coord = self._transform.apply(coord)
        self._parent.print_at(text, parent_coord, colour=colour, attr=attr, bg=bg)

    # drawing
    def move(self, coord):
        parent_coord = self._transform.apply(coord)
        self._parent.move(parent_coord)

    # drawing
    def draw(self, coord, char, colour=None, bg=None):
        parent_coord = self._transform.apply(coord)
        self._parent.draw(parent_coord, char, colour=colour, bg=bg)

    # screenpos
    def move_to(self, coord):
        # this moves the child relative to its parent; coord is in
        # parent's coordinate space
        (x, y) = coord
        self._transform = Transform(x, y)

    # drawing / redisplay
    def render(self):
        pass

    # genealogy
    def add_child(self, child):
        self._children.append(child)
        child._parent = self

    # genealogy
    def top_level_sheet(self):
        return self._parent.top_level_sheet()

    # layout
    # layout types must override this to actually do layout
    def allocate_space(self, allocation):
        """
        Forces width and height onto sheet.

        Width and Height are in the coordinate system of the sheet.
        """
        self._region = allocation

    # layout
    def compose_space(self):
        """
        Allows sheet to request a space allocation.

        Requested allocation is in the sheet's coordinate system and
        the request may not be honoured depending on the layout
        containing the sheet.

        Returns a tuple of 2 tuples of (MINIMUM, DESIRED, MAXIUMUM)
        """
        return ((0, FILL, FILL), (0, FILL, FILL))

    # layout
    def layout(self):
        """
        Specify locations (origins) of the sheet's children.

        X and Y are in the coordinate system of the child sheet
        being updated.
        """
        pass

    # layout
    def width(self):
        if not self._region:
            raise RuntimeError("Width queried before region set")
        (width, height) = self._region
        return width

    # layout
    def height(self):
        if not self._region:
            raise RuntimeError("Height queried before region set")
        (width, height) = self._region
        return height
