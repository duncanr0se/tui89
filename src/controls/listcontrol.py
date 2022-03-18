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

    def __init__(self, options=[]):
        super().__init__()
        self._options = options
        self._layout = HorizontalLayout([1, (1, "char")])
        self.add_child(self._layout)

        self._listbox = ListLayout()
        if len(options) > 0:
            self._fab_listbox_children(options)
        self._vbar = Scrollbar(orientation="vertical")

        self._viewport = Viewport(self._listbox, vertical_bar=self._vbar)

        self._layout.add_child(self._viewport)
        self._layout.add_child(self._vbar)

        # ValueMixin init
        self._value = None

    def __repr__(self):
        return "ListControl({} entries)".format(len(self._listbox._children))

    def _fab_listbox_children(self, options):
        for opt in options:
            # fixme: there's no reason these items should be
            # restricted to just being strings wrapped in new
            # labels... make also work with arbitrary widgets
            label = ValueLabel(label_text=opt)
            self._listbox.add_child(label)
            # self._listbox.add_child(Button(label=opt, decorated=False))
            # self._listbox.add_child(Button(label=opt))
            label.on_activate = self._handle_child_activation

    def _handle_child_activation(self, child):
        self.set_value(child.value())

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
        result = self.focus_first_child()
        if result:
            # callback?
            True
        return False

    # FIXME: perhaps something like this should be the default?
    # Perhaps a "CommandServer" mixin is needed that has this as its
    # default method?
    def handle_key_event(self, event):
        command = find_command(event, command_table="listcontrol")
        if command is not None:
            return command.apply(self)
        return self._parent.handle_key_event(event)

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
            self.frame().set_focus(widget)
            return True
        return False

    def is_tab_stop(self):
        return True

    def find_tab_stop_focus(self):
        # fixme: what if the listbox contains widgets that have
        # children themselves? Need a "do-sheet-tree" method...
        for child in self._listbox._children:
            if child.accepts_focus():
                return child
        return None

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
        (child_left, child_top, _, _) = child._region
        position = child_to_viewport_transform.apply((child_left, child_top))
        in_view = self._viewport.region_contains_position(position)
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

    def cycle_focus_backward(self, selected):
        found = False
        for child in reversed(self._listbox._children):
            if found:
                if child.accepts_focus():
                    self.frame().set_focus(child)
                    # fixme: maybe do this in a "note" method?
                    if self.child_out_of_view(child):
                        self.scroll_into_view(child)
                        self._vbar.invalidate()
                    return True
            if child == selected:
                found = True
        return False

    def focus_first_child(self):
        child = self.find_tab_stop_focus()
        if child is not None:
            self.frame().set_focus(child)
            return True
        return False

    def cycle_focus_forward(self, selected):
        found = False
        for child in self._listbox._children:
            if found:
                if child.accepts_focus():
                    self.frame().set_focus(child)
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
