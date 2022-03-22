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
import operator

logger = getLogger(__name__)

class Dialog(TopLevelSheet):
    """Dialog popup.

    Top level sheet type containing an implicit border layout (unlike
    standard top level sheet where the user gets to pick the contained
    layout) which contains a box layout in turn.

    The box layout contains the dialog content pane and button pane,
    in that order.

    Dialog styles:

        + info
        + alert
        + yes/no
    """
    def __init__(self,
                 style="info",
                 title=None,
                 text=None,
                 border_style="double",
                 drop_shadow=True,
                 dispose_on_click_outside=False,
                 owner=None):
        super().__init__()
        self._children = []
        self._title = title if title is not None else "unnamed"
        self._style = style
        self._border_style=border_style
        self._dispose_on_click_outside=dispose_on_click_outside

        self._drop_shadow = drop_shadow
        self._text = text

        self._owner = owner

        self._make_dialog_shell()

    def _make_dialog_shell(self):
        # FIXME: this is a bit of a mess. Allow user to specify
        # content pane and button pane; make one or both optional; add
        # separator if have both when rendering; make sure to relayout
        # / recalculate sizes when either pane updated. Or - don't
        # allow changes after dialog has already been layed out?

        # FIXME: layout needs to size AND move children, not just move
        # them. Or does it...?

        # FIXME: make this box layout configurable; maybe the user
        # wants a horizontal layout
        border = BorderLayout(title=self._title, style=self._border_style)
        self.add_child(border)
        self._wrapper = VerticalLayout([1, (1, "char"), (3, "char")])
        border.add_child(self._wrapper)
        self._wrapper.add_child(self._make_content_pane(self._text))
        self._wrapper.add_child(HorizontalSeparator())
        self._wrapper.add_child(self._make_button_pane())

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
        # fixme: should allow caller to pass in arbitrary buttons -
        # and arbitrary callbacks. Need a way to return values from
        # the dialog - or make clear this is done asynchronously via a
        # callback and make it the caller's problem.
        if self._style == "yes/no":
            yes = Button("Yes", decorated=True, width=11)
            no = Button("No", decorated=True, width=11)
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
        # fixme: deal with multi-line text
        text_size = 0 if self._text is None else len(self._text)
        # fixme: padding shouldn't be present (use spacing
        # pane) or at least should be configurable...
        (cp_minx, cp_prefx, cp_maxx) = (text_size, text_size+4, FILL)
        (cp_miny, cp_prefy, cp_maxy) = (1, 5, FILL)
        # Include size for the separator
        cp_miny = min(cp_miny+1, FILL)
        cp_prefy = min(cp_prefy+1, FILL)
        cp_maxy = min(cp_maxy+1, FILL)
        # Space req for label+separator
        content_pane_size = SpaceReq(cp_minx, cp_prefx, cp_maxx,
                                     cp_miny, cp_prefy, cp_maxy)
        # Also hard-code the button pane (minimum + preferred)
        # sizes for now
        # FIXME: hardcoded index
        button_pane = self._wrapper._children[2]
        button_pane_size = button_pane.compose_space()
        # combine content pane sr + button pane sr
        # FIXME: tidy this by passing the combining fn for each
        # component of the sr to the combine_spacereqs method. For the
        # below that would be "max" and "operator.add".
        all_max = (max, max, max)
        all_add = (operator.add, operator.add, operator.add)
        sr = combine_spacereqs(content_pane_size, button_pane_size, all_max, all_add)

        # border adds +1 on each side
        border = 2
        if self._drop_shadow:
            # shadow adds +1 on right + bottom
            border += 1
        border_adds = SpaceReq(0, border, 0, 0, border, 0)
        sr = combine_spacereqs(sr, border_adds, all_add, all_add)

        logger.debug("DIALOG DIALOG DIALOG: cp sr=%s, button sr=%s, combind sr=%s",
                     content_pane_size, button_pane_size, sr)
        return sr

    # same as space allocation for BorderLayout EXCEPT the dialog also
    # makes space for a drop shadow.  Could just use the one from the
    # parent if "border width" could be specified...
    def allocate_space(self, allocation):
        (left, top, right, bottom) = allocation
        self._region = allocation
        (width, height) = (right-left, bottom-top)
        # border layout fills whole dialog apart from space needed by
        # drop shadow
        if self._drop_shadow:
            (border_width, border_height) = (width-1, height-1)
        else:
            (border_width, border_height) = (width, height)

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

        # region includes space for the border, don't clear where the
        # border will go if the dialog has a border.
        (l, t, r, b) = self._region
        if self._drop_shadow:
            r -= 1
            b -= 1
        self.clear((l, t, r, b), self.pen())

        for child in self._children:
            child.render()

        if self._text is not None:
            pen = self.pen()
            # fixme: use a real pane type to hold the text
            cp_height = self._content_pane.height()
            cp_width = self._content_pane.width()
            cp_yoffset = cp_height // 2
            cp_xoffset = (cp_width-len(self._text)) // 2
            self._content_pane.display_at((cp_xoffset, cp_yoffset), self._text, pen)

        if self._drop_shadow:
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
        if self._owner is not None:
            return self._owner.handle_key_event(key_event)
        return False

    def find_focus_candidate(self):
        if self._owner is not None:
            return self._owner.find_focus_candidate()
        return super().find_focus_candidate()


class MultivalueDialog(Dialog):

    def __init__(self,
                 drop_shadow=True,
                 dispose_on_click_outside=False,
                 owner=None):
        super().__init__(drop_shadow=drop_shadow,
                         dispose_on_click_outside=dispose_on_click_outside,
                         owner=owner)

    def _make_dialog_shell(self):
        # caller is entirely responsible for populating multivalue
        # dialog
        pass

    def compose_space(self):
        spacereq = None
        # if dialog is a shell it's entire content is defined by
        # the size of its single child
        for child in self._children:
            spacereq = child.compose_space()
        # shell dialog with no children. Should probably be an
        # error but for now return a default space requirement
        if spacereq is None:
            spacereq = SpaceReq(10, 10, 10, 10, 10, 10)

        if self._drop_shadow:
            border = 1
            border_adds = SpaceReq(0, border, 0, 0, border, 0)
            all_add = (operator.add, operator.add, operator.add)
            spacereq = combine_spacereqs(spacereq, border_adds, all_add, all_add)
        return spacereq

    def allocate_space(self, allocation):
        (left, top, right, bottom) = allocation
        self._region = allocation
        # allocate all space to the single child
        for child in self._children:
            if self._drop_shadow:
                allocation = (left, top, right-1, bottom-1)
            child.allocate_space(allocation)

    def render(self):
        # region includes space for the border, don't clear where the
        # border will go if the dialog has a border.
        (l, t, r, b) = self._region
        if self._drop_shadow:
            r -= 1
            b -= 1
        self.clear((l, t, r, b), self.pen())

        for child in self._children:
            child.render()

        if self._drop_shadow:
            self._draw_dropshadow()


def alert(frame, message):
    dialog = Dialog(title="=[ ALERT ]=", style="alert", text=message)
    frame.show_dialog(dialog)

def info(frame, message):
    dialog = Dialog(title="=[ INFO ]=", style="info", text=message)
    frame.show_dialog(dialog)

def yes_no(frame, message):
    dialog = Dialog(title="=[ YES or NO ]=", style="yes/no", text=message)
    frame.show_dialog(dialog)
