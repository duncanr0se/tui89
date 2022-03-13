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

from asciimatics.screen import Screen

from sheets.sheet import Sheet

from sheets.spacereq import SpaceReq, FILL, combine_spacereqs

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.boxlayout import VerticalLayout, HorizontalLayout
from sheets.buttons import Button
from frames.frame import Frame
from sheets.separators import HorizontalSeparator

from dcs.ink import Pen

from frames.commands import find_command

from logging import getLogger

logger = getLogger(__name__)

class Dialog(TopLevelSheet):
    """Dialog popup.

    Top level sheet type containing an implicit border layout (unlike
    standard top level sheet where the user gets to pick the contained
    layout) which contains a box layout in turn.

    The box layout contains the dialog content pane and button pane,
    in that order.
    """
    def __init__(self, title=None, text=None, style="info"):
        super().__init__()
        self._children = []
        self._title = title if title is not None else "unnamed"
        self._style = style
        border = BorderLayout(title=title)
        self.add_child(border)
        # FIXME: make this box layout configurable; maybe the user
        # wants a horizontal layout
        # FILL isn't a requirement, it's a non-requirement so should
        # be ignored for composition / allocation.
        self._wrapper = VerticalLayout([1, (1, "char"), (3, "char")])
        border.add_child(self._wrapper)
        # fixme: scrolling dialog content?
        self._wrapper.add_child(self._make_content_pane(text))
        self._wrapper.add_child(HorizontalSeparator())
        self._wrapper.add_child(self._make_button_pane())
        self._text = text

    def __repr__(self):
        (left, top, right, bottom) = self._region
        (width, height) = (right-left, bottom-top)
        tx = self._transform._dx
        ty = self._transform._dy
        return "Dialog({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._title)

    def _make_content_pane(self, text):
        # could instead write "find_content_pane", "find_button_pane" methods...
        self._content_pane = Sheet()
        return self._content_pane

    def _make_button_pane(self):
        # fixme: should allow caller to pass in arbitrary buttons
        if self._style == "yes/no":
            yes = Button("YES", decorated=True, width=11)
            no = Button("NO", decorated=True, width=11)
            hbox = HorizontalLayout([])
            hbox.add_child(yes)
            hbox.add_child(no)

            # fixme: callback needs to be supplied by caller
            def yncallback(button):
                # save frame because the call to dialog_quit destroys
                # the reference held in button arg
                bframe = button.frame()
                button.frame().dialog_quit()
                # fixme: stash value somewhere so it can be retrieved
                alert(bframe, "You clicked: {}".format(button._label))
            yes.on_click_callback = yncallback
            no.on_click_callback = yncallback
            return hbox
        else:
            okButton = Button("OK", decorated=True, width=11)

            def callback(button):
                button.frame().dialog_quit()

            okButton.on_click_callback = callback
            return okButton

    def compose_space(self):
        # make sufficient space for:
        # content pane + button pane
        # + border
        # + drop shadow
        #
        # content pane should be big enough to hold the
        # text + some padding (fixme: put in a padding
        # pane when we have one)
        #
        # Content pane doesn't actually know the text it
        # is wrapping (yet!) so frig the size here. Do
        # this properly (make content pane some widget that
        # already knows its text) at some point.
        #
        # fixme: need to be able to draw to a sheet before
        # it's attached, or calculate size for text before
        # it's attached. Going to need this for scrolling
        # anyway...
        #
        # fixme: deal with multi-line text
        text_size = len(self._text)
        # fixme: padding shouldn't be present (use spacing
        # pane) or at least should be configurable...
        content_pane_size = SpaceReq(text_size, text_size+4, FILL, 1, 5, FILL)
        #
        # Also hard-code the button pane (minimum + preferred)
        # sizes for now
        # FIXME: hardcoded index
        button_pane = self._wrapper._children[2]
        button_pane_size = button_pane.compose_space()
        vbox_pane_size = combine_spacereqs(content_pane_size, button_pane_size)
        # border adds +1 on each side
        # shadow adds +1 on right + bottom
        border_adds = SpaceReq(0, 3, 0, 0, 3, 0)
        vbox_pane_size = combine_spacereqs(vbox_pane_size, border_adds)
        return vbox_pane_size

    # same as space allocation for BorderLayout EXCEPT the dialog also
    # makes space for a drop shadow.  Could just use the one from the
    # parent if "border width" could be specified...
    def allocate_space(self, allocation):
        (left, top, right, bottom) = allocation
        self._region = allocation
        (width, height) = (right-left, bottom-top)
        # border layout fills whole dialog apart from space needed by
        # drop shadow
        (border_width, border_height) = (width - 1, height - 1)
        border_layout = self._children[0]
        border_request = border_layout.compose_space()
        # give all the space to the child without allocating more than the child's maximum.
        border_width = min(border_width, border_request.x_max())
        border_height = min(border_height, border_request.y_max())
        border_layout.allocate_space((left, top, left+border_width, top+border_height))

    def pen(self, role="undefined", state="info", pen="pen"):
        if role == "undefined":
            role = "toplevel"

        if role == "toplevel" or role == "border":
            state = self._style

        logger.debug(f"finding pen: {role}, {state}, {pen}")
        return super().pen(role=role, state=state, pen=pen)

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        for child in self._children:
            child.render()

        pen = self.pen()
        # fixme: use a real pane type to hold the text
        self._content_pane.display_at((2, 2), self._text, pen)

        self._draw_dropshadow()

    def _draw_dropshadow(self):
        # fixme: shadow pen in toplevel? Or is shadow a role?
        # fixme: this pen management is really not pleasant.
        shadow_pen = self.pen(role="shadow", state="default")
        default_pen = self.pen()
        shadow_pen = shadow_pen.merge(default_pen)
        logger.debug("merged shadow pen is %s", shadow_pen)
        (left, top, right, bottom) = self._region
        dropshadow_right = u'█'
        dropshadow_below = u'█'
        self.move((right-1, 1))
        # drawing vertical line so max y is not included in the
        # render, so "bottom" is the correct max extent.
        self.draw_to((right-1, bottom), dropshadow_right, shadow_pen)
        self.move((left+1, bottom-1))
        # drawing left->right, high x value is excluded but high y
        # value is included.
        self.draw_to((right, bottom-1), dropshadow_below, shadow_pen)

    # events - top level sheets don't pass event on to a parent,
    # instead they return False to indicate the event is not handled
    # and expect the Frame to take any further necessary action
    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="dialog")
        if command is not None:
            return command.apply(self)

        return False


def alert(frame, message):
    dialog = Dialog(title="=[ ALERT ]=", style="alert", text=message)
    frame.show_dialog(dialog)

def info(frame, message):
    dialog = Dialog(title="=[ INFO ]=", style="info", text=message)
    frame.show_dialog(dialog)

def yes_no(frame, message):
    dialog = Dialog(title="=[ YES or NO ]=", style="yes/no", text=message)
    frame.show_dialog(dialog)
