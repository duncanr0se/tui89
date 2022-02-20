
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

    _vertical_sb = None
    _horizontal_sb = None

    # One of "double", "spacing", "single", "scrolling", "title"
    #     - double :: draw border using double bars; will draw title;
    #     - single :: draw border using single bars; will draw title;
    #     - spacing :: draw border using spaces;
    #     - scrolling :: border only on bottom and rhs, and populated
    #           with scroll bars if they are provided; no title
    #     - title :: border only on top; will draw title;
    #     - None :: no border? Not sure this is useful... maybe if
    #           a spacer is needed that could draw bars later?
    _border = None

    def __init__(self, title=None, style="double", default_pen=None):
        super().__init__(default_pen)
        self._title = title
        supported = ["double", "single", "spacing"]
        if style not in supported:
            raise NotImplementedError("Border layout only supports {} style currently"
                                      .format(supported))
        self._border = style

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "BorderLayout({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._title)

    def add_child(self, child):
        if self._children:
            raise RuntimeError("BorderLayout supports a single child only")
        super().add_child(child)

    def set_scrollbars(self, vertical_scrollbar=None, horizontal_scrollbar=None):
        if vertical_scrollbar is not None:
            self._vertical_sb = vertical_scrollbar
            vertical_scrollbar._parent = self

        if horizontal_scrollbar is not None:
            self._horizontal_sb = horizontal_scrollbar
            horizontal_scrollbar._parent = self

    # specialise find_highest_sheet... to cater for scroll bars.
    def find_highest_sheet_containing_position(self, parent_coord):
        coord = self._transform.inverse().apply(parent_coord)
        if self.region_contains_position(coord):
            if self._vertical_sb is not None:
                container = self._vertical_sb.find_highest_sheet_containing_position(coord)
                if container is not None:
                    return container
                if self._horizontal_sb is not None:
                    container = self._horizontal_sb.find_highest_sheet_containing_position(coord)
                    if container is not None:
                        return container
            # only 1 child in a border layout
            for child in self._children:
                container = child.find_highest_sheet_containing_position(coord)
                if container is not None:
                    return container
            return self
        # this sheet doesn't contain the position
        return None

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

        if self._vertical_sb is not None:
            child_request = self._vertical_sb.compose_space()
            # use the minimum width and the border pane's height
            self._vertical_sb.allocate_space((xSpaceReqMin(child_request), height-2))
        if self._horizontal_sb is not None:
            child_request = self._horizontal_sb.compose_space()
            # use minimum height and border pane's width
            self._horizontal_sb.allocate_space((width-3, ySpaceReqMin(child_request)))

    def layout(self):
        # single child
        for child in self._children:
            child.move_to((1, 1))
            child.layout()
        (rw, rh) = self._region
        if self._vertical_sb is not None:
            self._vertical_sb.move_to((rw-1, 1))
            self._vertical_sb.layout()
        if self._horizontal_sb is not None:
            # how wide should horizontal bars be? turbo vision looks
            # to give about 50% of the pane width...
            self._horizontal_sb.move_to((1, rh-1))
            self._horizontal_sb.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear((0, 0), self._region)
        self._draw_border()
        for child in self._children:
            child.render()
        if self._vertical_sb is not None:
            self._vertical_sb.render()
        if self._horizontal_sb is not None:
            self._horizontal_sb.render()

    border_chars = {
        "double": {
            "nw":   u'╔', "top": u'═',    "ne": u'╗',
            "left": u'║',              "right": u'║',
            "sw":   u'╚', "bottom": u'═', "se": u'╝'
        },
        "single": {
            "nw":   u'┌', "top": u'─',    "ne": u'┐',
            "left": u'│',              "right": u'│',
            "sw":   u'└', "bottom": u'─', "se": u'┘'
        },
        "spacing": {
            "nw":   ' ', "top": ' ',    "ne": ' ',
            "left": ' ',              "right": ' ',
            "sw":   ' ', "bottom": ' ', "se": ' '
        }
    }

    def _draw_border(self):
        pen = self.default_pen()
        (left, top) = (0, 0)
        (width, height) = self._region
        right = self.width()-1
        bottom = self.height()-1

        # todo: deal with long titles
        charset = self.border_chars[self._border]
        # top border - make allowances for a title
        self.print_at(charset["nw"], (left, top), pen)
        self.move((1, top))
        if self._title:
            # LHS of bar + title
            bar_width = right - 1
            title = ' ' + self._title + ' '
            title_width = len(title)
            side_bar_width = (bar_width - title_width) // 2
            self.draw((side_bar_width, top), charset["top"], pen)
            self.print_at(title, (side_bar_width, top), pen)
            self.move((side_bar_width + title_width, top))
            self.draw((right, top), charset["top"], pen)
        else:
            self.draw((right, top), charset["top"], pen)
        self.print_at(charset["ne"], (right, top), pen)

        # left border
        self.move((left, top + 1))
        self.draw((left, bottom), charset["left"], pen)

        # right border - might be scroll bar
        if self._vertical_sb is None:
            self.move((right, top + 1))
            self.draw((right, bottom), charset["right"], pen)
        else:
            # scrollbar will draw itself
            pass

        # bottom border - might be scroll bar
        self.print_at(charset["sw"], (left, bottom), pen)
        if self._horizontal_sb is None:
            self.move((1, bottom))
            self.draw((right, bottom), charset["bottom"], pen)
            self.print_at(charset["se"], (right, bottom), pen)
        else:
            self.print_at(u'─', (right-1, bottom), pen)
            self.print_at(u'┘', (right, bottom), pen)
            # scrollbar will draw itself
