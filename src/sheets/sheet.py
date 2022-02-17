
from asciimatics.event import MouseEvent

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
    def print_at(self, text, coord, colour=7, attr=0, bg=0):
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
    def draw(self, coord, char, colour=7, bg=0):
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
        for child in self._children:
            child.render()

    # genealogy
    def add_child(self, child):
        self._children.append(child)
        child._parent = self

    # genealogy
    def top_level_sheet(self):
        return self._parent.top_level_sheet()

    def find_highest_sheet_containing_position(self, parent_coord):
        # parent coord is in the parent's coordinate system
        # transform parent coord into this sheet's coord space.
        coord = self._transform.inverse().apply(parent_coord)
        # If this sheet's region does not contain the transformed
        # coord then none of the child sheets will contain it, by
        # definition. Return false.
        if self.region_contains_position(coord):
            # If this sheet has children, recurse through them from last
            # (highest in z-order) to first and test each one.
            if len(self._children) > 0:
                for child in reversed(self._children):
                    container = child.find_highest_sheet_containing_position(coord)
                    if container is not None:
                        return container
            # no child contains the position, but we know we contain
            # it. Must be us!
            return self
        # If we reached this point we either have no children, or none
        # of the children contain the position. In any case, we're not
        # returning a useful result.
        return None

    def region_contains_position(self, coord):
        # coord is in the sheet's coordinate system
        (rx, ry) = self._region
        (cx, cy) = coord
        # yes if its on the left or top boundary, no if it's on the
        # right or bottom boundary.
        return cx < rx and cy < ry and cx >= 0 and cy >= 0

    def get_screen_transform(self):
        # navigate parents until get to top level sheet composing
        # transforms all the way up
        return self._transform.add_transform(self._parent.get_screen_transform())

    # layout layout types must override this to actually do layout
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

    def handle_event(self, event):
        # coordinates in event are in the coordinate system of self
        # default is to decline to handle the event and ask our parent
        # to handle it. The top level sheet overrides this method and
        # just returns None.
        # Sheets that want to do something with the event need to provide
        # their own overrides for this method.
        (px, py) = self._transform.apply((event.x, event.y))
        self._parent.handle_event(MouseEvent(px, py, event.buttons))
