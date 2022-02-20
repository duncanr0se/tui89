
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired

# A layout that arranges its children in columns
class BoxLayout(Sheet):

    # List of relative widths or absolute values.

    # List defines ratios for children. If not set, all children are
    # allocated equal space. If provided, defines both the layout for
    # the children and the number of children.

    # Possible values:

    #   - [] :: no sizing information given, all children allocated
    #           equal major space.
    #   - [N1, N2, ..., Nn] :: each N defines a ratio to be allocated
    #           to the corresponding child. For example [2, 3, 5]
    #           defines a layout where the first child has 2/10ths of
    #           available major space, second has 3/10ths, and 3rd
    #           has 1/2. Calculated by summing elements then calculating
    #           percentages
    #   - [(N1, "char"), (N2, "char"), ...] :: each N defines a number
    #           of units to allocate to the corresponding child.
    #   - [(N1, "ratio"), (N2, "ratio"), ...] :: each N defines a
    #           ratio of the overall space; same as [N1, N2, ...]
    #   - [(N1, "%"), (N2, "%"), ...] :: define a specific percentage
    #           of the available space to allocate to corresponding
    #           child.
    #
    # The different forms above may be mixed; for example, [(N1, "char"),
    # (N2, "%"), (N3, "char"), (N4, "ratio"), (N5, "ratio")]. In this
    # case the explicit ("char") sizes are allocated first; any "percentage"
    # values are converted to ratios, and then all ratios are calculated
    # using the space remaining after fixed sizes have been set.

    # FIXME: if anything needs unit tests, it's probably the above!
    _portions = None

    def __init__(self, portions):
        super().__init__()
        self._portions = portions

    def add_child(self, child):
        super().add_child(child)

    def major_size_component(self, sheet):
        pass

    # perhaps this should be the thing that calls compose-space
    # followed by allocate-space? With compose-space on kids in turn
    # calling layout? Probably best to follow same pattern as DUIM if
    # only for consistency in my own stuff...
    #
    # maybe allocate_space should call layout() if the region changes?
    def layout(self):
        offset = 0
        for child in self._children:
            child.move_to((offset, 0))
            offset += self.major_size_component(child)
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

    def major_size_component(self, sheet):
        return sheet.width()


    def minor_size_component(self, sheet):
        return sheet.height()


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

    def major_size_component(self, sheet):
        return sheet.height()

    def minor_size_component(self, sheet):
        return sheet.width()
