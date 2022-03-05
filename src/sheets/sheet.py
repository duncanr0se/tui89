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

      + a default pen indicating the foreground and background to use
    to draw by default;

      + may be attached to a display device;
    """
    def __init__(self):
        self._attached = False
        self._children = []
        self._parent = None
        # sheets that manage pens need to set this to a dict()
        self._pens = None
        self._region = None
        self._transform = IDENTITY_TRANSFORM

    def __repr__(self):
        (width, height) = self._region
        return "Sheet({}x{})".format(width, height)

    # drawing
    #
    # Make "unspecified" a really horrid colour scheme if that's even
    # possible...
    def pen(self, role="unspecified", state="default", pen="pen"):
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
    def clear(self, origin, region):
        porigin = self._transform.apply(origin)
        self._parent.clear(porigin, region)

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
        return SpaceReq(1, FILL, FILL, 1, FILL, FILL)

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

    # events
    def find_focus_candidate(self):
        logger.debug("find_focus invoked on %s", self)
        # depth first search to find the first descendent with no
        # children; use that as the focus. Keyboard navigation or
        # selection with the mouse can be used to find a different
        # focus.
        for child in self._children:
            focus = child.find_focus_candidate()
            if focus is not None:
                return focus
        if self.accepts_focus():
            logger.debug("find_focus_candidate identified %s", self)
            return self
        return None

    def find_next_focus(self, current_focus, found_current=False):
        logger.debug("self=%s, current_focus=%s, found=%s", self, current_focus, found_current)

        # in words:
        #
        # walk sheet hierarchy until find current focus. Once found
        # continue walking sheet hierarchy until find next potential
        # focus candidate, or run out of sheets to check.
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

        for child in self._children:
            (found_current, next) = child.find_next_focus(current_focus,
                                                          found_current=found_current)
            if next is not None:
                return (True, next)

        # failed to find anything suitable
        return (found_current, None)

    def find_prev_focus(self, current_focus, previous_candidate=None):
        logger.debug("find_prev_focus entered; current_focus %s, prev candidate %s, self %s",
                     current_focus, previous_candidate, self)
        # returns (True, candidate) if the current focus is found, and
        # (False, candidate) otherwise.
        if self == current_focus:
            logger.debug("self == current_focus, returning previous_candidate %s",
                         previous_candidate)
            return (True, previous_candidate)

        candidate = previous_candidate

        if self.accepts_focus():
            candidate = self

        for child in self._children:
            (found, candidate) = child.find_prev_focus(current_focus,
                                                       previous_candidate=candidate)
            if found:
                logger.debug("found current focus, returning prev focus %s", candidate)
                return (True, candidate)

        return (False, candidate)

    # events
    def accepts_focus(self):
        return False

    # events
    def is_focus(self):
        return False

    # events
    def handle_key_event(self, event):
        # by default pass event to the next sheet in the hierarchy to
        # deal with. Top level sheet types terminate this walk by
        # returning False to their caller (= the Frame)
        return self._parent.handle_key_event(event)

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
