
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

    # FIXME: experiment with scrolling layout containing widgets,
    # esp. when it comes to dealing with events...

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
        self.clear((0, 0), self._region)
        for child in self._children:
            child.render()
        # fixme: how to deal with events?

    # FIME: this seems often to be over-eager to clip the text
    def _clip_text(self, coord, text):
        # measure text, cut off any that would be rendered before x=0
        # + cut off any that would be rendered after 'width'
        # coord is fixed elsewhere

        text_len = len(text)
        (x, y) = coord
        (w, h) = self._region

        if x < 0:
            text = text[abs(x):]
        if x > w:
            text = None
        if y < 0:
            text = None
        if y > h:
            text = None

        if text is not None:
            overflow = x+len(text) - w
            if overflow > 0:
                # change overflow to represent just the portion of the
                # text that is overflowing
                overflow -= x
                text = text[:overflow]

        if text == "":
            text = None

        return text

    def _clip(self, coord):
        (x, y) = coord
        (w, h) = self._region
        cx = max(min(x, w), 0)
        cy = max(min(y, h), 0)
        return (cx, cy)

    # drawing
    def clear(self, origin, region):
        porigin = self._transform.apply(origin)
        self._parent.clear(porigin, region)

    # drawing
    def print_at(self, text, coord, pen):
        # capture full extents of print
        self._capture_print_at(text, coord)
        # clip to region prior to drawing
        text = self._clip_text(coord, text)
        if text is not None:
            coord = self._clip(coord)
            parent_coord = self._transform.apply(coord)
            self._parent.print_at(text, parent_coord, pen)

    # drawing
    def move(self, coord):
        self._capture_move(coord)
        coord = self._clip(coord)
        parent_coord = self._transform.apply(coord)
        self._parent.move(parent_coord)

    # drawing
    # rework contract for this to make it clear single
    # graphic characters are required; there may be
    # multiple characters in the string for multibyte
    # characters. Perhaps.
    def draw(self, coord, char, pen):
        self._capture_draw(coord, char)
        coord = self._clip(coord)
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

    # 0,0
    #  +----------+----------------+
    #  |          |                |
    #  |          |                |
    #  ...

    #       sheet_max-viewport_width,0
    #  +----------------+----------+
    #  |                |          |
    #  |                |          |
    #  ...

    # slug offset
    #      v
    #  +---+----------+------------+
    #  |<t>|          |            |
    #  |   |<  slug  >|            |
    #  ...     size
    #   <    bar size / width     >

    def scroll_left_line(self):
        # scrolling LEFT moves scrolled sheet to the RIGHT.
        # if LHS of scrolled sheet is already showing, don't allow
        # scrolling in this direction.
        # LHS will be showing if transform is >= 0.
        delta = 1
        trans = self._scrolled_sheet._transform
        x = min(0, trans._dx+delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        # invalidate self, or invalidate scrolled sheet?
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_right_line(self):
        #
        # FIXME: +definitely coming in here but scrolling by a page; why?
        #
        delta = 1
        trans = self._scrolled_sheet._transform
        # 0,0
        (sw, sh) = self._scroll_extents[1]
        tmax = self.width() - sw
        # -89
        x = max(tmax, trans._dx-delta)
        # -1
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_up_line(self):
        delta = 1
        trans = self._scrolled_sheet._transform
        y = min(0, trans._dy+delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_down_line(self):
        delta = 1
        trans = self._scrolled_sheet._transform
        (sw, sh) = self._scroll_extents[1]
        # -1 is a hack, work out why the drawing position is wrong...
        tmax = self.height()-1 - sh
        y = max(tmax, trans._dy-delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_left_page(self):
        delta = self.width()-1
        trans = self._scrolled_sheet._transform
        x = min(0, trans._dx+delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        # invalidate self, or invalidate scrolled sheet?
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_right_page(self):
        delta = self.width()-1
        trans = self._scrolled_sheet._transform
        (sw, sh) = self._scroll_extents[1]
        tmax = self.width() - sw
        x = max(tmax, trans._dx-delta)
        # fixme: don't update transform if it doesn't change
        self._scrolled_sheet._transform = Transform(x, trans._dy)
        self._horizontal_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_up_page(self):
        delta = self.height()-1
        trans = self._scrolled_sheet._transform
        y = min(0, trans._dy+delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()

    def scroll_down_page(self):
        delta = self.height()-1
        trans = self._scrolled_sheet._transform
        (sw, sh) = self._scroll_extents[1]
        tmax = self.height()-1 - sh
        y = max(tmax, trans._dy-delta)
        self._scrolled_sheet._transform = Transform(trans._dx, y)
        self._vertical_sb.update_scroll_offset(self._scrolled_sheet)
        self.invalidate()
