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

from sheets.sheet import Sheet

from sheets.spacereq import FILL, SpaceReq
from sheets.boxlayout import HorizontalLayout
from sheets.listlayout import ListLayout
from sheets.scrollbar import Scrollbar
from sheets.viewport import Viewport
from sheets.label import Label, ValueLabel
from sheets.buttons import Button
from frames.commands import find_command
from geometry.transforms import Transform

from mixins.valuemixin import ValueMixin

from logging import getLogger

logger = getLogger(__name__)

# A control that wraps a list layout and vertical bar in a scroller.
class ListControl(Sheet, ValueMixin):

    def __init__(self, options=[], owner=None):
        super().__init__(owner=owner)

        self._options = options
        self._layout = HorizontalLayout([1, (1, "char")], owner=self)
        self.add_child(self._layout)

        self._listbox = ListLayout(owner=self)
        if len(options) > 0:
            self._fab_listbox_children(options)
        self._vbar = Scrollbar(orientation="vertical")

        self._viewport = Viewport(self._listbox, vertical_bar=self._vbar, owner=self)

        self._layout.add_child(self._viewport)
        self._layout.add_child(self._vbar)

        # controls contain and manage embedded child widgets; record
        # which of them has focus.
        self._widget_focus = None

        # ValueMixin init
        self._value = None

    # fixme: this focus handling is still terrible. Think about it
    # more.
    def set_focus(self, focus):
        logger.debug("---> %s setting widget focus to %s", self, focus)
        if self._widget_focus is not None:
            self._widget_focus.note_focus_out()
        self._widget_focus = focus
        if self._owner:
            self._owner.set_focus(self)
        if self._widget_focus is not None:
            self._widget_focus.note_focus_in()
        self.frame().invalidate(self)

    def is_widget_focus(self, widget):
        return self._widget_focus == widget

    def __repr__(self):
        num_children = len(self._listbox._children)
        if self._value is not None:
            return "ListControl(value='{}', {} entries)".format(self._value, num_children)
        else:
            return "ListControl({} entries)".format(num_children)

    def _fab_listbox_children(self, options):
        for opt in options:
            # fixme: there's no reason these items should be
            # restricted to just being strings wrapped in new
            # labels... make also work with arbitrary widgets
            label = ValueLabel(label_text=opt, owner=self)
            self._listbox.add_child(label)
            # self._listbox.add_child(Button(label=opt, decorated=False))
            # self._listbox.add_child(Button(label=opt))
            #
            # FIXME: not sure this is the best way to do this...
            label.on_activate = self._handle_child_activation

    def _handle_child_activation(self, child):
        logger.debug("   _handle_child_activation entered for child %s with value %s of control %s",
                     child, child.value(), self)
        self.set_value(child.value())
        logger.debug("   value of %s updated to %s", self, child.value())

    def update_elts(self, updated_elts):
        """Modify list elements.

        Remove children from layout that do not exist in updated_elts;
        add elements from updated_elts that do not exist in the layout
        to the layout.
        """
        # TODO: highlight list entries that match a supplied value

        # TODO: bit of a hammer to crack a nut - maybe should have
        # "filter" method and then add only new ones?
        self._listbox.clear_children()
        self._fab_listbox_children(updated_elts)
        # does invalidate relayout as well as redraw? NOPE. Need a
        # method that redoes the space calc, lays out children, and
        # renders them ("relayout"?)
        self._layout.allocate_space(self._region)
        self._listbox.layout()
        # fixme: update scrollbars; reduce size of containing dialog
        # if list has shrunk to a point where there's empty space.
        self.invalidate()

    def pen(self, role="undefined", state="default", pen="pen"):
        overridden_roles = ["undefined", "label", "button"]
        if role in overridden_roles:
            role = "buttonbox"
        return super().pen(role, state, pen)

    def allocate_space(self, allocation):
        (l, t, r, b) = allocation
        self._region = allocation
        for child in self._children:
            child.allocate_space(allocation)

    def compose_space(self):
        # default size for list control is 10x10
        for c in self._children:
            # single child.
            child_sr = c.compose_space()
            sr = SpaceReq(5, 10, FILL, 5, 10, FILL)
            return sr

    def layout(self):
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    def render(self):
        self.clear(self._region)
        super().render()

    def activate(self):
        self.owner().set_focus(self)
        if self._widget_focus is None:
            result = self.control_focus_first_child()
        else:
            result = True
        return result

    def handle_key_event(self, event):

        logger.debug("   handle_key_event entered for event %s", event)

        # If there's a widget higher in the z-order that can handle
        # the event let it do so.
        # It is only controls that have a widget focus.
        # FIXME: this is now the wrong way around - should be control
        # then focus
        if self._widget_focus is not None:
            result = self._widget_focus.handle_key_event(event)
            if result:
                return True
        # Try to handle the event ourselves
        command = find_command(event, command_table="listcontrol")
        if command is not None:
            result = command.apply(self)
            if result:
                return True
        # It was the owner's handle_key_event method that called this
        # one! There's nothing higher in the z-order to pass the event
        # to and 'self' doesn't want to deal with it, so indicate it's
        # unhandled.
        return False

    def accepts_focus(self):
        # True if there are children and any of the children accept
        # focus.

        # When the frame actually sets the focus on a "tab stop"
        # control a focus delegate is found using the
        # "find_tab_stop_focus" method that actually takes the
        # focus. It is known that such a delegate (child) exists
        # because the control only returns True to "accepts_focus"
        # queries if there is such a child.

        # fixme: how to actually set the focus on the child it should
        # be set on when the widget receives the focus?
        for child in self._listbox._children:
            if child.accepts_focus():
                return True
        return False

    # FIXME: change this for controls; should just have focus forward
    # / backward which works either on embedded widgets, if focus is
    # inside a control (managed by the control) or across controls and
    # widgets at the top level (managed by the frame) otherwise. This
    # should supercede the "is_tabstop" hackery.
    def find_next_focus_same_level(self):
        # this is just be "find next focus" invoked on the parent
        # sheet passing "self" as current focus, and refusing to
        # descend into the children.

        # for this to work, this needs to accept the focus? Or maybe
        # have a flag to say "tab navigation stops here!" or
        # something? Basic logic is want to make one of the control's
        # children the focus, but don't want to navigate down to the
        # control's children (or at least, don't want to appear to
        # navigate down the children).

        # So - list control contains list of ValueLabels. When tab
        # navigation lands on list control, want to select the first
        # label as focus, but a subsequent tab does NOT select the
        # next label, it instead moves focus off the list control
        # altogether.

        # also - list control needs to return True for accepts_focus
        # call for this to work I think
        (found, widget) = self._parent.find_next_focus(self)
        if found:
            self.owner().set_focus(widget)
            return True
        return False

    def page_up(self):
        # fixme: update focus? - yes, focus last visible item
        # fixme: update scrollbar based off some event or notification
        # methods instead of manually.
        self._viewport.scroll_up_page()
        self._vbar.invalidate()
        return True

    def page_down(self):
        # fixme: update focus? - yes, focus first visible item
        # fixme: update scrollbar based off some event or notification
        # methods instead of manually.
        self._viewport.scroll_down_page()
        self._vbar.invalidate()
        return True

    def find_focused_child(self):
        for child in self._listbox._children:
            if child.is_focus():
                return child
        return None

    # FIXME: is_visible?
    def child_out_of_view(self, child):
        # returns True if child (left, top) is outside the viewport.
        # need to get child coords in viewport coord system.
        # hierarhcy:
        #
        # + list control [self]
        #     + horizontal layout
        #         + viewport
        #             + listbox
        #                 + items
        child_to_viewport_transform = child.delta_transform(self._viewport)
        region = child_to_viewport_transform.transform_region(child._region)
        in_view = self._viewport.region_intersects_region(region)
        logger.debug(f"***** IN_VIEW={in_view}")
        return not in_view

    def scroll_into_view(self, child):
        # 1. everything is line based
        # 2. listcontrol only scrolls vertically
        #
        # "scrolled sheet" is the listlayout.
        # "child" is one of the listlayout elements.
        #
        child_to_viewport_transform = child.delta_transform(self._viewport)
        delta = child_to_viewport_transform._dy
        # fixme: works for now because listcontrol entries all have
        # height=1. Not good enough for general use! Implement "scroll
        # by delta" in viewport?
        # fixme: doesn't quite work! if use shit-tab and end up on the
        # list, line nav scrolls by a single line but selected entry
        # is multiple lines away from appearing visually.
        if delta == 0:
            # nothing to do
            return
        elif delta > 0:
            lines = max(delta+1-self._viewport.height(), 1)
            self._viewport.scroll_down_lines(lines)
        else:
            # if negative delta, always want to scroll to (0, 0)
            lines = abs(delta)
            self._viewport.scroll_up_lines(lines)

    # moves focus within control
    def control_cycle_focus_backward(self, selected):
        found = False
        for child in reversed(self._listbox._children):
            if found:
                if child.accepts_focus():
                    self.set_focus(child)
                # fixme: maybe do this in a "note" method?
                if self.child_out_of_view(child):
                    self.scroll_into_view(child)
                    self._vbar.invalidate()
                return True
            if child == selected:
                found = True
        return False

    # return control's widget focus
    def focus(self):
        return self._widget_focus

    # Focus is managed by a widget or sheets "owner". For basic
    # widgets added to the application top level sheet the owner will
    # be the application frame. For widgets added to controls the
    # owner is the control containing the widget.
    # This should be transparent to widgets or sheets that are NOT
    # controls or frames.

    # moves focus within control
    def control_focus_first_child(self):
        for child in self._listbox._children:
            if child.accepts_focus():
                self.set_focus(child)
                return True
        return False

    # moves focus within control
    def control_cycle_focus_forward(self, selected):
        found = False
        for child in self._listbox._children:
            if found:
                if child.accepts_focus():
                    self.set_focus(child)
                # fixme: maybe do this in a "note" method?
                if self.child_out_of_view(child):
                    self.scroll_into_view(child)
                    self._vbar.invalidate()
                return True
            if child == selected:
                found = True
        return False

    # fixme: should be able to select member of the list and have that
    # been the value of the widget / control.

    # def find_next_focus(self, current_focus, found_current):
        # logger.debug("LISTCONTROL - FIND NEXT FOCUS. CALLING ON SUPER")
        # result = super().find_next_focus(current_focus, found_current)
        # logger.debug("RESULT IS {}", result)
        # return result

    # find focus within FRAME
    def find_focus_candidate(self):
        # Don't descend into children; return self if self accepts
        # focus.
        if self.accepts_focus():
            return self
        return None

    # find focus within FRAME
    def find_next_focus(self, current_focus, found_current):
        if not found_current and self == current_focus:
            return (True, None)
        if found_current and self.accepts_focus():
            return (True, self)
        return (found_current, None)

    # find focus within FRAME
    def find_prev_focus(self, current_focus, previous_candidate, indent):
        if self == current_focus:
            return (True, previous_candidate)
        if self.accepts_focus():
            return (False, self)
        return (False, previous_candidate)

    def note_focus_in(self):
        if self._widget_focus is None:
            self.control_focus_first_child()
