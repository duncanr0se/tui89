
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import xSpaceReqMin
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import ySpaceReqMin

class BorderLayout(Sheet):

    _title = None

    # simple class that draws a border around itself and manages a
    # single child - todo, complicate this up by making it support
    # scrolling!

    def __init__(self, title=None):
        super().__init__()
        self._title = title

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "BorderLayout({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._title)

    def add_child(self, child):
        if self._children:
            raise RuntimeError("BorderLayout supports a single child only")
        super().add_child(child)

    # BorderLayout expects its children to completely fill it, but
    # it's not an arse about it, it's happy for kids to be their
    # preferred size if they want to be. However, it does insist on
    # their origin being (0, 0). For more flexibility add a different
    # layout type as the child of the border box.
    def allocate_space(self, allocation):
        self._region = allocation
        (width, height) = allocation
        (calloc_x, calloc_y) = (width - 2, height - 2)
        for child in self._children:
            child_request = child.compose_space()
            # if desired or max space are less than allocation, reduce allocation to max space
            # else set allocation to desired
            # By definition desired space <= max space so no need to check it
            # Don't allow space allocated to widget to be smaller than
            # the widget's minimum; it won't all fit on the screen,
            # but that's the widget's problem...
            calloc_x = max(xSpaceReqMin(child_request),
                           min(xSpaceReqDesired(child_request), calloc_x))
            calloc_y = max(ySpaceReqMin(child_request),
                           min(ySpaceReqDesired(child_request), calloc_y))
            child.allocate_space((calloc_x, calloc_y))

    def layout(self):
        # single child
        for child in self._children:
            child.move_to((1, 1))
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear((0, 0), self._region)
        self._draw_border()
        for child in self._children:
            child.render()

    def _draw_border(self):
        pen = self.top_level_sheet()._default_fg_pen
        if pen is None:
            pen = self.frame().theme("borders")

        (left, top) = (0, 0)
        (width, height) = self._region
        right = self.width()-1
        bottom = self.height()-1

        # todo: deal with long titles
        # todo: deal with scrolling...

        # top border - make allowances for a title
        self.print_at(u'╔', (left, top), pen)
        self.move((1, top))
        if self._title:
            # LHS of bar + title
            bar_width = right - 1
            title = ' ' + self._title + ' '
            title_width = len(title)
            side_bar_width = (bar_width - title_width) // 2
            self.draw((side_bar_width, top), u'═', pen)
            self.print_at(title, (side_bar_width, top), pen)
            self.move((side_bar_width + title_width, top))
            self.draw((right, top), u'═', pen)
        else:
            self.draw((right, top), u'═', pen)
        self.print_at(u'╗', (right, top), pen)

        # left border
        self.move((left, top + 1))
        self.draw((left, bottom), u'║', pen)

        # right border - might be scroll bar
        self.move((right, top + 1))
        self.draw((right, bottom), u'║', pen)

        # bottom border - might be scroll bar
        self.print_at(u'╚', (left, bottom), pen)
        self.move((1, bottom))
        self.draw((right, bottom), u'═', pen)
#        self.print_at(u'─', (right-1, bottom), colour, attr, bg)
#        self.print_at(u'┘', (right, bottom), colour, attr, bg)
        self.print_at(u'╝', (right, bottom), pen)
