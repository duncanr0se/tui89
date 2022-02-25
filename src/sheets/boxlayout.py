
from sheets.sheet import Sheet

import math
from logging import getLogger

logger = getLogger(__name__)

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
    #           ratio of the available space; same as [N1, N2, ...]
    #   - [(N1, "%"), (N2, "%"), ...] :: define a specific percentage
    #           of the available space to allocate to corresponding
    #           child.
    #
    # The different forms above may be mixed; for example, [(N1,
    # "char"), (N2, "%"), (N3, "char"), (N4, "ratio"), (N5,
    # "ratio")]. In this case the explicit ("char") sizes are
    # allocated first; any "percentage" values are populated as
    # percentages of the remaining space, and then all ratios are
    # calculated using the space remaining after fixed sizes and
    # percentages have been set.

    # FIXME: if anything needs unit tests, it's probably the above!
    #_portions = None

    def __init__(self, portions, default_pen=None, pen=None):
        super().__init__(default_pen=default_pen, pen=pen)
        self._portions = portions

    def add_child(self, child):
        super().add_child(child)

    def major_size_component(self, sheet):
        pass

    def minor_size_component(self, sheet):
        pass

    # x-offset for horizontal box; y-offset for vertical box
    def move_to_major_offset(self, sheet, offset):
        pass

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

        major_component = self._major_region_component(allocation)
        minor_component = self._minor_region_component(allocation)

        # fix up empty portions
        if len(self._portions) == 0:
            self._portions = [(1, "ratio")] * len(self._children)

        def _destructure(column):
            try:
                iterator = iter(column)
                # (N, "char"), (N, "%"), (N, "ratio")
                return column
            except TypeError:
                # not iterable
                # N
                return (column, "ratio")

        # allocate fixed size allocations
        totalFixedSpace = 0
        for index, column in enumerate(self._portions):
            (n, unit) = _destructure(column)
            if unit == "char":
                totalFixedSpace += n
                child = self._children[index]
                child_region = self._make_region(n, minor_component)
                child.allocate_space(child_region)

        major_component -= totalFixedSpace

        # allocate percentage size allocations
        totalPercentageSpace = 0
        for index, column in enumerate(self._portions):
            (n, unit) = _destructure(column)
            if unit == "%":
                percentageRequirement = math.ceil(n / 100.0 * major_component)
                totalPercentageSpace += percentageRequirement
                child = self._children[index]
                child_region = self._make_region(percentageRequirement, minor_component)
                child.allocate_space(child_region)

        major_component -= totalPercentageSpace

        # allocate remaining width to ratios
        totalSegments = 0
        for column in self._portions:
            (n, unit) = _destructure(column)
            if unit == "ratio":
                totalSegments += n

        # SPLIT ANYTHING REMAINING IN SPECIFIED RATIOS
        segmentSize = major_component // totalSegments
        surplus = major_component - segmentSize*totalSegments

        for index, column in enumerate(self._portions):
            (n, unit) = _destructure(column)
            if unit == "ratio":
                child = self._children[index]
                callocq = n * segmentSize
                if surplus > 0:
                    callocq += 1
                    surplus -= 1
                child_region = self._make_region(callocq, minor_component)
                child.allocate_space(child_region)


    # perhaps this should be the thing that calls compose-space
    # followed by allocate-space? With compose-space on kids in turn
    # calling layout? Probably best to follow same pattern as DUIM if
    # only for consistency in my own stuff...
    #
    # maybe allocate_space should call layout() if the region changes?
    def layout(self):
        offset = 0
        for child in self._children:
            self.move_to_major_offset(child, offset)
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

    def _major_region_component(self, allocation):
        (width, height) = allocation
        return width

    def _minor_region_component(self, allocation):
        (width, height) = allocation
        return height

    def _make_region(self, major, minor):
        return (major, minor)

    def major_size_component(self, sheet):
        return sheet.width()


    def minor_size_component(self, sheet):
        return sheet.height()

    def move_to_major_offset(self, sheet, offset):
        sheet.move_to((offset, 0))


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

    def _major_region_component(self, allocation):
        (width, height) = allocation
        return height

    def _minor_region_component(self, allocation):
        (width, height) = allocation
        return width

    def _make_region(self, major, minor):
        return (minor, major)

    def major_size_component(self, sheet):
        return sheet.height()

    def minor_size_component(self, sheet):
        return sheet.width()

    def move_to_major_offset(self, sheet, offset):
        sheet.move_to((0, offset))
