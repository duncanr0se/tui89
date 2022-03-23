#
# Copyright 2022 Duncan Rose
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from asciimatics.event import MouseEvent

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.spacereq import FILL, SpaceReq
from dcs.ink import Pen

from logging import getLogger

logger = getLogger(__name__)

# ALL sheets are "drawing sheets". ALL sheets have children. ALL
# sheets participate in layout.
class Sheet():
    """Region of the screen.

    Sheets have:

      +  a parent;

      + a transform that converts coords in the sheet's coordinate
    system into coordinates in the parent sheet's coordinate system;

      + a region;

      + children - children at the end of the child list are higher in
      the z-order (get rendered last);

      + may be attached to a display device;
    """
    def __init__(self, width=None, height=None, owner=None):
        self._attached = False
        self._children = []
        self._parent = None
        self._pens = None
        self._region = None
        self._transform = IDENTITY_TRANSFORM
        # specify owner to deal with focus / events. By default this
        # is the application Frame but can be overridden by sheets
        # that group other sheets to perform a function, i.e., by
        # controls.
        self._owner = owner
        # explicit width+height
        self._width = width
        self._height = height

        self.on_detached_callback = None

    def __repr__(self):
        # FIXME: what to do if sheet has no region? Should it be
        # possible?
        if self._region is None:
            return "Sheet(=unallocated= {})".format(type(self))
        else:
            (left, top, right, bottom) = self._region
            return "Sheet({}x{})".format(right-left, bottom-top)

    def owner(self):
        return self.frame() if self._owner is None else self._owner

    # drawing
    #
    # Delegate to top-level-sheet for colourscheme if nothing
    # specified
    def pen(self, role="undefined", state="default", pen="pen"):
        if self._pens is None:
            return self._parent.pen(role=role, state=state, pen=pen)
        # default method looks for requested pen but if it can't find
        # it it passes the query to its parent.
        if role in self._pens:
            if state in self._pens[role]:
                if pen in self._pens[role][state]:
                    return self._pens[role][state][pen]
        return self._parent.pen(role=role, state=state, pen=pen)

    # FIXME: this is a pretty horrible way to set colours for a
    # sheet. It works but is low level. Find a better interface for
    # devs to call.
    def set_pen(self, pen, role="button", state="default", which="pen"):
        if self._pens is None:
            self._pens = dict()
        if not role in self._pens:
            self._pens[role] = dict()
        if not state in self._pens[role]:
            self._pens[role][state] = dict()
        self._pens[role][state][which] = pen

    # drawing
    def clear(self, region_ltrb, pen=None):
        # in order for pens to work properly this method needs to pass
        # the pen up to the top-level.

        # fixme: at this point if the pen is None (such as when the
        # vbox contained in the green border) it calls the default
        # pen() method for the vbox which provides the helpful
        # "toplevel/default/pen" defaults in the pen method in this
        # file.

        # The fact that it queries the parent for this information
        # whilst passing these args is kinda irrelevent.

        # So for sure this logic is wrong, but how to fix?

        # Maybe use special values that tell the parent "overwrite
        # me". So could fill in defaults for the border layout if any
        # of its children pass "undefined" for the role?
        if pen is None:
            pen = self.pen()
        transformed_ltrb = self._transform.transform_region(region_ltrb)
        self._parent.clear(transformed_ltrb, pen)

    # drawing
    def display_at(self, coord, text, pen):
        # transform coords all the way up to the top-level-sheet and
        # invoke print_at on t-l-s. Has to be better than expecting
        # every sheet in the hierarchy to implement the drawing
        # methods... or maybe not. Hrm.
        parent_coord = self._transform.apply(coord)
        self._parent.display_at(parent_coord, text, pen)

    # drawing
    def move(self, coord):
        parent_coord = self._transform.apply(coord)
        self._parent.move(parent_coord)

    # drawing
    # if multiple chars are provided, only the first
    # is used (except for the last rendering where
    # other parts of the content are also rendered).
    # also ignores bottommost/rightmost coordinate.
    # Not sure if only true when drawing ltr or ttb,
    # might not occur for rtl / btt.
    def draw_to(self, coord, char, pen):
        parent_coord = self._transform.apply(coord)
        self._parent.draw_to(parent_coord, char, pen)

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
        if self.is_attached():
            child.attach()

    # genealogy
    def set_children(self, children):
        self._children = children
        for child in children:
            child._parent = self
            if self.is_attached():
                child.attach()

    # genealogy
    def frame(self):
        if self.is_detached():
            raise RuntimeError("Sheet {} not attached".format(self))
        return self.top_level_sheet().frame()

    def is_attached(self):
        return self._attached

    def is_detached(self):
        return not self._attached

    def top_level_sheet(self):
        return self._parent.top_level_sheet()

    def find_highest_sheet_containing_position(self, parent_coord, log_indent="  "):
        # parent coord is in the parent's coordinate system
        # transform parent coord into this sheet's coord space.
        coord = self._transform.inverse().apply(parent_coord)
        # If this sheet's region does not contain the transformed
        # coord then none of the child sheets will contain it, by
        # definition. Return false.
        if self.region_contains_position(coord):
            logger.debug("%s found sheet containing position %s %s",
                         log_indent, coord, self)
            # If this sheet has children, recurse through them from last
            # (highest in z-order) to first and test each one.
            if len(self._children) > 0:
                for child in reversed(self._children):
                    container = child.find_highest_sheet_containing_position(coord,
                                                                             log_indent+"  ")
                    if container is not None:
                        return container
            # no child contains the position, but we know we contain
            # it. Must be us!
            return self
        # If we reached this point we either have no children, or none
        # of the children contain the position. In any case, we're not
        # returning a useful result.
        logger.debug(f"%s sheet %s does not contain position %s",
                     log_indent, self, coord)
        return None

    def region_contains_position(self, coord):
        # coord is in the sheet's coordinate system
        (left, top, right, bottom) = self._region
        (cx, cy) = coord
        # yes if its on the left or top boundary, no if it's on the
        # right or bottom boundary.
        return left <= cx < right and top <= cy < bottom

    def get_screen_transform(self):
        # navigate parents until get to top level sheet composing
        # transforms all the way up
        return self._transform.add_transform(self._parent.get_screen_transform())

    def delta_transform(self, target):
        # navigate parents until get to the target sheet, composing
        # transforms along the way
        if self == target:
            return IDENTITY_TRANSFORM
        return self._transform.add_transform(self._parent.delta_transform(target))

    # layout layout types must override this to actually do layout
    def allocate_space(self, allocation):
        """
        Forces LTRB region onto sheet.

        Coordinates are in the coordinate system of the sheet.
        """
        # Force error if allocation is not an LTRB
        (left, top, right, bottom) = allocation
        self._region = allocation
        for child in self._children:
            child.allocate_space(allocation)

    # layout
    def compose_space(self):
        """
        Allows sheet to request a space allocation.

        Requested allocation is in the sheet's coordinate system and
        the request may not be honoured depending on the layout
        containing the sheet.

        Returns a tuple of 2 tuples of (MINIMUM, DESIRED, MAXIUMUM)
        """
        # basic 10x5 default
        spacereq = SpaceReq(10, FILL, FILL, 5, FILL, FILL)
        for child in self._children:
            # override default with child requirement when there's a
            # child
            spacereq = child.compose_space()
        # override with fixed dimensions
        (xmin, xpref, xmax) = \
            (spacereq.x_min(), spacereq.x_preferred(), spacereq.x_max()) \
            if self._width is None else (self._width,)*3
        (ymin, ypref, ymax) = \
            (spacereq.y_min(), spacereq.y_preferred(), spacereq.y_max()) \
            if self._height is None else (self._height,)*3

        return SpaceReq(xmin, xpref, xmax, ymin, ypref, ymax)

    # layout
    def layout(self):
        """
        Specify locations (origins) of the sheet's children.

        X and Y are in the coordinate system of the child sheet
        being updated.
        """
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    # layout
    def width(self):
        if not self._region:
            raise RuntimeError(f"Width of sheet {self} queried before region set")
        (left, _, right, _) = self._region
        return right-left

    # layout
    def height(self):
        if not self._region:
            raise RuntimeError(f"Height of sheet {self} queried before region set")
        (_, top, _, bottom) = self._region
        return bottom-top

    # events
    def find_focus_candidate(self):
        # depth first search to find the first leaf descendent that
        # accepts the focus; use that as the focus.
        # Keyboard navigation or selection with the mouse can be used
        # to find a different focus.
        for child in self._children:
            focus = child.find_focus_candidate()
            if focus is not None:
                return focus
        if self.accepts_focus():
            return self
        return None

    def find_next_focus(self, current_focus, found_current=False):
        """Find next widget in tab order.

        Treats widgets that are "tab stop" widgets as a single atomic
        widget for the purposes of tab order and navigation.
        """
        logger.debug("self=%s, current_focus=%s, found=%s", self, current_focus, found_current)

        # in words:
        #
        # walk sheet hierarchy until find current focus. Once found
        # continue walking sheet hierarchy until find next potential
        # focus candidate, or run out of sheets to check.
        #
        # if the current focus is a tab stop sheet (fixme: tab stop ->
        # "focus delegating") or the next focus candidate is a child
        # of a tab stop sheet, do not use the tab stop sheet's
        # child. Instead continue the walk to find a focus candidate
        # that is outside the tab stop control. "TAB navigation
        # navigates between WIDGETS where a WIDGET may be a control
        # containing child widgets; the child widgets are not found
        # during tab navigation". This should apply to menus + button
        # boxes also I think.
        #
        # if run out of candidates, return None indicating there is no
        # suitable "next focus"
        #
        # Method returns a pair of (found, next_focus)
        #
        # Note: this method is designed to stop when it can't find a
        # next focus. I think that wrapping is better behaviour.

        if not found_current and self == current_focus:
            found_current = True

        if found_current and self != current_focus and self.accepts_focus():
            return (True, self)

        # fixme: this breaks navigation because the widget with the
        # focus isn't actually the widget that wants to be found
        # during this walk. Need to properly design this "focus
        # delegation" functionality. Think the problem is that the
        # widget with the focus inside the list control isn't actually
        # discoverable using this walk.

        # Don't walk children of sheet's reporting True for
        # "is_tab_stop".
        # fixme: This is wrong! Still need to walk the kids in case
        # the tab stop contains the current focus.

        # If the focus is found within the tab stop widget, return
        # that the current focus was found but as yet no focus is
        # found.

        # So no return in the loop below, but need to break early if
        # self is a tab stop.
        for child in self._children:
            (found_current, next) = child.find_next_focus(current_focus,
                                                          found_current=found_current)
            if next is not None:
                return (True, next)

        # failed to find anything suitable
        return (found_current, None)

    def find_prev_focus(self, current_focus, previous_candidate=None, indent="__"):
        """Find previous widget in tab order.

        Treats widgets that are "tab stop" widgets as a single atomic
        widget for the purposes of tab order and navigation.
        """
        # returns (True, candidate) if the current focus is found, and
        # (False, widget) otherwise.
        if self == current_focus:
            return (True, previous_candidate)

        # update previous_candidate if self is not a tab stop. Don't
        # want tab-stop to be "previous" for any of its own children,
        # so tab stops are not set as the "previous" widget until
        # AFTER their children have been walked to find the current
        # focus.
        if self.accepts_focus():
            previous_candidate = self

        candidate = previous_candidate

        for child in self._children:
            (found, candidate) = child.find_prev_focus(current_focus,
                                                       candidate,
                                                       indent+"__")
            if found:
                return (True, candidate)

        return (False, candidate)

    # events
    def accepts_focus(self):
        return False

    # events
    def is_focus(self):
        # Deal with nested control widgets; this is done by walking
        # the "owner" hierarchy until an owner is directly owned by
        # the Frame.

        # if sheet's owner is the frame and the owner says this sheet
        # is the focus - it's the focus.
        #
        # otherwise the sheet must be contained in a control; the
        # sheet is only the focus if the sheet is the control's
        # widget-focus and the control is the frame focus.
        if self.accepts_focus():
            if self.owner() == self.frame():
                # frame is owner case
                return self.owner().focus() == self
            # owned sheets are not the focus if the owned sheet is not
            # the frame focus
            if self.owner().is_focus():
                # ask owner if this sheet is focused within it
                return self.owner().is_widget_focus(self)
        return False

    def note_focus_out(self):
        # frame invokes this when the sheet is replaced as the frame's
        # focus by another sheet
        pass

    def note_focus_in(self):
        # frame invokes this when the sheet is made the frame's focus
        if hasattr(self, "_pressed"):
            # If "pressed" flag is not cleared, clear it now
            self._pressed = False

    # events
    def handle_key_event(self, event):
        # No handler by default
        return False

    # FIXME: rename to "handle-mouse-event"?
    # events
    def handle_event(self, event):
        # coordinates in event are in the coordinate system of self
        # default is to decline to handle the event and ask our parent
        # to handle it. The top level sheet overrides this method and
        # just returns None.
        # Sheets that want to do something with the event need to provide
        # their own overrides for this method.
        (px, py) = self._transform.apply((event.x, event.y))
        self._parent.handle_event(MouseEvent(px, py, event.buttons))

    def invalidate(self):
        # Invalidated = dirty, in need of redraw
        # add to list of invalidated sheets in frame that will
        # be redrawn on the next iteration of the event loop
        self.frame().invalidate(self)

    # attached / detached = linked to frame, available to be
    # displayed
    def is_detached(self):
        return not self._attached

    def detach(self):
        # detach from top down - fixme: not sure this is the best
        # order. Ditto for "attach()"
        for child in reversed(self._children):
            child.detach()
        self._attached = False
        if self.on_detached_callback is not None:
            return self.on_detached_callback(self)

    def attach(self):
        # attach from bottom up
        self._attached = True
        for child in self._children:
            child.attach()

    def find_widget(self, widget):
        if self == widget:
            return self
        for child in self._children:
            found = child.find_widget(widget)
            if found is not None:
                return found
        return None
