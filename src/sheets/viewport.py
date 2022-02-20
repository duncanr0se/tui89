
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import xSpaceReqMin
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import ySpaceReqMin
from sheets.spacereq import FILL
from geometry.transforms import Transform

class Viewport(Sheet):

    # Viewport's region give the extents of the VISIBLE region.

    # Viewport's "scrolling region" gives the extents of the SCROLLED
    # region.

    # scrolled sheet transform gets changed when the scrollbars are
    # altered.

    _vertical_sb = None
    _horizontal_sb = None

    # fixme: scrolled_sheet, or just use _children?
    _scrolled_sheet = None

    _scroll_extents = ((0, 0), (1, 1))

    def __init__(self, contentpane, vertical_bar=None, horizontal_bar=None):
        super().__init__()
        self._scrolled_sheet = contentpane
        self.add_child(contentpane)
        self._vertical_sb = vertical_bar
        self._horizontal_sb = horizontal_bar
        if self._vertical_sb is not None:
            self._vertical_sb._viewport = self
            # is this really necessary?
#            self._vertical_sb._scrolled_sheet = contentpane
        if self._horizontal_sb is not None:
            self._horizontal_sb._viewport = self
            # is this really necessary?
#            self._horizontal_sb._scrolled_sheet = contentpane

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Viewport({}x{}@{},{})".format(width, height, tx, ty)

    def add_child(self, child):
        if self._children:
            raise RuntimeError("Viewport supports a single child only")
        super().add_child(child)

    # fixme: is the ability to make the scrollbars dynamic wanted?
    def set_scrollbars(self, vertical_scrollbar=None, horizontal_scrollbar=None):
        raise NotImplementedError("No dynamic bars for now")

#    # specialise find_highest_sheet... to cater for scroll bars.
#    def find_highest_sheet_containing_position(self, parent_coord):
#        coord = self._transform.inverse().apply(parent_coord)
#        if self.region_contains_position(coord):
#            if self._vertical_sb is not None:
#                container = self._vertical_sb.find_highest_sheet_containing_position(coord)
#                if container is not None:
#                    return container
#                if self._horizontal_sb is not None:
#                    container = self._horizontal_sb.find_highest_sheet_containing_position(coor#d)
#                    if container is not None:
#                        return container
#            # only 1 child in a border layout
#            for child in self._children:
#                container = child.find_highest_sheet_containing_position(coord)
#                if container is not None:
#                    return container
#            return self
#        # this sheet doesn't contain the position
#        return None

    # Viewport has no view of how much space it needs. Just pick some
    # not-unreasonable default.

    # Give the child as much space as is available, 'cause why not?
    def allocate_space(self, allocation):
        self._region = allocation
        # the scrolled sheet has no "allocation" per se, it just accepts
        # pretty much everything.
        self._scrolled_sheet.allocate_space((FILL, FILL))

    def layout(self):
        # single child
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        for child in self._children:
            child.render()
        # fixme: how to get scroller extents?
        # fixme: how to update the scrollbars?
        # fixme: how to update the transforms?
        # fixme: how to deal with events?

    # drawing
    def clear(self, origin, region):
        porigin = self._transform.apply(origin)
        self._parent.clear(porigin, region)

    # drawing
    def print_at(self, text, coord, pen):
        self._capture_print_at(text, coord)
        parent_coord = self._transform.apply(coord)
        self._parent.print_at(text, parent_coord, pen)

    # drawing
    def move(self, coord):
        self._capture_move(coord)
        parent_coord = self._transform.apply(coord)
        self._parent.move(parent_coord)

    # drawing
    # rework contract for this to make it clear single
    # graphic characters are required; there may be
    # multiple characters in the string for multibyte
    # characters. Perhaps.
    def draw(self, coord, char, pen):
        self._capture_draw(coord, char)
        parent_coord = self._transform.apply(coord)
        self._parent.draw(parent_coord, char, pen)

    def _capture_print_at(self, text, coord):
        # capture scroller extents in the coord system of the scrolled
        # sheet
        trans = self._scrolled_sheet._transform
        ccoord = trans.inverse().apply(coord)
        self.update_scroll_extents(ccoord)
        (x, y) = ccoord
        # not sure if it's safe to take the length of the text like
        # this...
        self.update_scroll_extents((x + len(text), y))

    def _capture_move(self, coord):
        trans = self._scrolled_sheet._transform
        ccoord = trans.inverse().apply(coord)
        self.update_scroll_extents(ccoord)

    def _capture_draw(self, coord, char):
        trans = self._scrolled_sheet._transform
        ccoord = trans.inverse().apply(coord)
        self.update_scroll_extents(coord)

    def update_scroll_extents(self, coord):
        # scroll extents are in the coord system of the scrolled sheet.
        # should these be kept as LTRBs?
        (el, et) = self._scroll_extents[0]
        (ew, eh) = self._scroll_extents[1]
        (er, eb) = (el + ew, et + eh)

        (cx, cy) = coord

        extents_updated = False
        if cx < el:
            el = cx
            extents_updated = True
        if cx > er:
            er = cx
            extents_updated = True
        if cy < et:
            et = cy
            extents_updated = True
        if cy > eb:
            eb = cy
            extents_updated = True

        # update scrollbars if extents changed
        if extents_updated:
            # viewport region + scrollbar extents are both in the
            # viewport sheet's coordinate space
            # Origin for viewport is always (0, 0)
            (rw, rh) = self._region

            ew = er - el
            eh = eb - et

            self._scroll_extents = ((el, et), (ew, eh))

            # vertical range is "eh" with slug size "rh"
            if self._vertical_sb is not None:
                self._vertical_sb.update_extents(eh, rh)
            # horizontal range is "ew" with slug size "rw"
            if self._horizontal_sb is not None:
                self._horizontal_sb.update_extents(ew, rw)

    def scroll_left_line(self):
        # scrolling LEFT moves scrolled sheet to the RIGHT.
        # if LHS of scrolled sheet is already showing, don't allow
        # scrolling in this direction.
        # LHS will be showing if transform is >= 0.
        trans = self._scrolled_sheet._transform
        x = trans._dx
        if x < 0:
            self._scrolled_sheet._transform = Transform(x+1, trans._dy)
            # invalidate self, or invalidate scrolled sheet?
            self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
            self.invalidate()

    # fixme: disallow scrolling if already displaying max extent of
    # scroller
    def scroll_right_line(self):
        trans = self._scrolled_sheet._transform
        x = trans._dx
        self._scrolled_sheet._transform = Transform(x-1, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_up_line(self):
        trans = self._scrolled_sheet._transform
        y = trans._dy
        if y < 0:
            self._scrolled_sheet._transform = Transform(trans._dx, y+1)
            self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
            self.invalidate()

    # fixme: disallow scrolling if already displaying max extent of
    # scroller
    def scroll_down_line(self):
        trans = self._scrolled_sheet._transform
        y = trans._dy
        self._scrolled_sheet._transform = Transform(trans._dx, y-1)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    # fixme: when scrolling by the page, need to just set the transform
    # to 0 / max depending on which way being scrolled when reach the
    # end of the scroll range.
    def scroll_left_page(self):
        trans = self._scrolled_sheet._transform
        x = trans._dx
        delta = self.width()-1
        if x < 0:
            self._scrolled_sheet._transform = Transform(x+delta, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    # fixme: disallow scrolling if already displaying max extent of
    # scroller
    def scroll_right_page(self):
        trans = self._scrolled_sheet._transform
        x = trans._dx
        delta = self.width()-1
        self._scrolled_sheet._transform = Transform(x-delta, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_up_page(self):
        trans = self._scrolled_sheet._transform
        y = trans._dy
        delta = self.height()-1
        if y < 0:
            self._scrolled_sheet._transform = Transform(trans._dx, y+delta)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    # fixme: disallow scrolling if already displaying max extent of
    # scroller
    def scroll_down_page(self):
        trans = self._scrolled_sheet._transform
        y = trans._dy
        delta = self.height()-1
        self._scrolled_sheet._transform = Transform(trans._dx, y-delta)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()
