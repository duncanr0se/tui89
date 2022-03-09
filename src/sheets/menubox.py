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
from sheets.borderlayout import BorderLayout
from sheets.listlayout import ListLayout
from sheets.toplevel import TopLevelSheet
from sheets.separators import Separator
from sheets.buttons import Button

from frames.commands import find_command

from asciimatics.screen import Screen

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings. Layout takes minimum
# width necessary to provide its children with the width they request.
class MenuBox(TopLevelSheet):

    def __init__(self, width=None):
        super().__init__()
        self._children = []
        self._border = BorderLayout(style="single")
        self.add_child(self._border)
        self._item_pane = ListLayout()
        self._border.add_child(self._item_pane)
        # fixme: this should probably be a standard sheet initarg
        self._width_override = width

    def __repr__(self):
        return "MenuBox({} entries)".format(len(self._item_pane._children))

    def pen(self, role="menubox", state="default", pen="pen"):
        if role == "undefined":
            role = "menubox"
        # override border colours
        if role == "border":
            role, state, pen = "menubox", "border", "pen"
        drawing_pen = super().pen(role=role, state=state, pen=pen)
        return drawing_pen

    def layout(self):
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        (left, top, right, bottom) = self._region
        self.clear((left, top), (right-left, bottom-top), self.pen())
        for child in self._children:
            child.render()

    # allocate smallest space possible to fit children - probably need
    # some extra parameter to say we're trying to minimise
    def allocate_space(self, allocation):
        (l, t, r, b) = allocation
        (awidth, aheight) = (r-l, b-t)
        cw = awidth
        ch = aheight
        # single child - the border layout.
        for child in self._children:
            sr = child.compose_space()
            ch = sr.y_preferred()
            if self._width_override is None:
                cw = sr.x_preferred()
            child.allocate_space((l, t, l+cw, t+ch))
            self._region = (l, t, l+min(cw, awidth), t+min(ch, aheight))

    def compose_space(self):
        # Sheet hierarchy is:
        #
        # menubox
        #   + borderlayout - how does this know to minimise region?
        #       + listlayout
        #           + button
        #           + button
        #           + separator
        #           + button
        reqwidth = 0
        reqheight = 0
        for child in self._children:
            sr = child.compose_space()
            reqwidth = max(reqwidth, sr.x_preferred())
            reqheight += sr.y_preferred()
        if self._width_override is not None:
            reqwidth = self._width_override
        return SpaceReq(reqwidth, reqwidth, reqwidth, reqheight, reqheight, reqheight)

    def set_items(self, items):
        self._item_pane.set_children(items)

    # events
    def accepts_focus(self):
        # won't get focus by default because not a leaf pane (has
        # children) but when children fail to handle an event and pass
        # it back to their parent this indicates that the parent will
        # attempt to do something with the event
        # FIXME: not necessary and adds nothing - for now at least.
        return True

    # events - top level sheets don't pass event on to a parent,
    # instead they return False to indicate the event is not handled
    # and expect the Frame to take any further necessary action
    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="menubox")
        if command is not None:
            return command.apply(self)

        return False

    def find_focused_child(self):
        for child in self._item_pane._children:
            if not isinstance(child, Separator):
                if child.is_focus():
                    return child
        return None

    def focus_first_child(self):
        for child in self._item_pane._children:
            if isinstance(child, Button):
                self.frame().set_focus(child)
                return True
        return False

    def cycle_focus_backward(self, selected):
        found = False
        for child in reversed(self._item_pane._children):
            if found:
                if isinstance(child, Button):
                    self.frame().set_focus(child)
                    return True
            if child == selected:
                found = True
        return False

    def cycle_focus_forward(self, selected):
        found = False
        for child in self._item_pane._children:
            if found:
                if isinstance(child, Button):
                    self.frame().set_focus(child)
                    return True
            if child == selected:
                found = True
        return False
