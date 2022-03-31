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

import time

from asciimatics.event import MouseEvent
from asciimatics.screen import Screen

from sheets.sheet import Sheet
from sheets.spacereq import SpaceReq, FILL
from geometry.regions import Region
from frames.commands import find_command

from dcs.ink import Pen

from logging import getLogger
from sheets.label import Label

logger = getLogger(__name__)

class Button(Sheet):
    """Push button sheet.

    Init params:
        - label
        - decorated
        - label_align
        - width

    Buttons have a label; can be decorated, or not; have no children;

    Can be aligned left, center, or right.
    Can have fixed width forced using "width".
    """
    def __init__(self,
                 label="--",
                 decorated=True,
                 label_align="center",
                 width=None):
        super().__init__()
        self._label = Label(label_text=label, align=label_align, label_widget=self)
        self.add_child(self._label)
        self._decorated = decorated
        self._width = width
        self._pressed = False
        # Function of 1 arg (button that was clicked)
        self.on_click_callback = None

    def __repr__(self):
        if not self._attached or self._region is None:
            return "Button(detached: '{}')".format(self._label._label_text)
        else:
            tx = self._transform._dx
            ty = self._transform._dy
            return "Button({}x{}@{},{}: '{}')".format(self._region.region_width(),
                                                      self._region.region_height(),
                                                      tx, ty,
                                                      self._label._label_text)

    ####

    # This might be better done in the method in sheet.py. Could set a
    # flag or something else to indicate that the sheet has a reduced
    # hit box for mouse events. For now just use this override.
    #
    # Deny containing position if not over actual button (i.e.,
    # consider padding and shadow to be outside the sheet)
    def find_highest_sheet_containing_position(self, parent_coord, log_indent="  "):
        coord = self._transform.inverse().apply(parent_coord)
        if self.region_contains_position(coord):
            (x, y) = coord
            # Is the mouse over the button background?
            (l, t, r, b) = self._button_background_region()
            # fixme: "r" seems to include the shadow on the
            # rhs. Investigate
            if l <= x < r and t <= y < b:
                return self
        return None

    ####

    # default button expects to be able to fit its label + some
    # padding. It can grow as big as you like, but won't go smaller
    # than 2x4.  How about dealing with multi-line labels? Image
    # buttons?
    def compose_space(self):

        # Undecorated buttons can shrink to 1x1; decorated buttons
        # also, but they retain space for the decoration.

        # FIXME: actually, since labels can only shrink to 6x1,
        # buttons are not going to shrink down to 1x1. Need to address
        # this if using buttons for ends of scroll bars!

        label_sr = self._label.compose_space()

        x_padding = 2
        y_padding = 0

        if self._decorated:
            x_padding += 3  # left border + right border + shadow
            y_padding += 2  # top border + shadow

        # supplied width overrides calculated size
        if self._width is not None:
            fw = self._width
            return SpaceReq(fw, fw, fw,
                            label_sr.y_min(),
                            label_sr.y_preferred()+y_padding,
                            FILL)
        else:
            return SpaceReq(label_sr.x_min(),
                            label_sr.x_preferred()+x_padding,
                            FILL,
                            label_sr.y_min(),
                            label_sr.y_preferred()+y_padding,
                            FILL)

    def allocate_space(self, allocation):
        self._region = allocation
        bg_region = self._button_background_region()
        (width, height) = (bg_region.region_width(), bg_region.region_height())
        # single child (the label)
        for child in self._children:
            if self._label._align == "left":
                # left aligned labels leave a gap of 1 before the
                # label - if possible. This reduces the amount of
                # space available to the label.
                if width > len(self._label._label_text)+1:
                    width -= 1
            child.allocate_space(Region(0, 0, 0+width, 0+height))

    def layout(self):
        (l, t, r, b) = self._button_background_region().ltrb()
        # single child (the label)
        for child in self._children:
            coord = (l, t)
            # if label is left aligned and there is space to leave 1
            # char padding between the button's left side and the
            # label, then leave the space.
            if self._label._align == "left":
                if r-l > len(self._label._label_text)+1:
                    coord = (l+1, t)
            child.move_to(coord)

    # decorated buttons fill excess space with padding; undecorated
    # buttons fill x-space with their background and y-space with
    # padding.
    # button background > padding decoration > drop shadow decoration
    def _draw_padding(self):
        pen = self._parent.pen()
        pen = Pen(pen.bg(), pen.attr(), pen.bg())
        self.clear(self._region, pen)

    def _draw_button_background(self):
        # fixme: method on Pen to return a "draw in bg colour" pen
        pen = self.pen()
        pen = Pen(pen.bg(), pen.attr(), pen.bg())
        # temporarily overide pen so we can see extents; todo: define
        # a "debug" pen
        # pen = Pen(Screen.COLOUR_YELLOW, pen.attr(), Screen.COLOUR_YELLOW)

        (left, top, right, bottom) = self._button_background_region().ltrb()

        # problem is that pens are not being given the correct width +
        # it looks like there's a bug when drawing the drop shadow
        # that causes it to be drawn in the wrong place.
        self.move((left, top))
        self.draw_to((right, top), ' ', pen)

    # gives the region of just the button background (coloured part of
    # button visual not including padding or dropshadow)
    def _button_background_region(self):
        (_, _, right, _) = self._region.ltrb()
        (width, height) = (self._region.region_width(), self._region.region_height())

        # If width is large enough to hold the label but not
        # the decoration, draw the button background over the whole
        # region width.
        # If insufficient space for dropshadow, draw padding.
        # If insufficient space for padding, just draw background.

        # room for shadow if width > label length+3 (left-pad,
        # right-pad + shadow)
        x_shadow = width >= len(self._label._label_text)+3 and self._decorated
        # room for padding if width > label length+2 (left-pad,
        # right-pad)
        x_padding = width >= len(self._label._label_text)+2 and self._decorated

        # bottom shadow uses same line as bottom padding
        y_padding = height >= 3 and self._decorated

        left = 1 if x_padding else 0
        top = 1 if y_padding else 0

        if x_shadow:
            right -= 1
        if x_padding:
            right -= 1

        # center button background in available height
        top_padding = max((height-4) // 2, 0)
        top += top_padding
        # button backgrounds are currently always 1 high
        bottom = top+1

        # left, bottom not included in region
        return Region(left, top, right, bottom)

    def _draw_button_dropshadow(self):
        # if the region isn't big enough for the decoration, don't
        # draw it even for decorated buttons
        shadow_pen = self.pen(role="shadow")
        bg_pen = self._parent.pen()
        # in case pen is already fully merged, manually merge the
        # bg. Add "pen-fully-merged?" type method? Also - this should
        # never happen, shadow_pen should always be a partial pen.
        #pen = shadow_pen.merge(bg_pen)
        pen = Pen(shadow_pen.fg(), shadow_pen.attr(), bg_pen.bg(), bg_pen.fill())

        (wl, wt, wr, wb) = self._region.ltrb()
        (left, top, right, bottom) = self._button_background_region().ltrb()

        # is region wide enough to include side dropshadow? - Yes if
        # widget rhs and button background rhs leaves space for the
        # dropshadow and padding (= 2)
        draw_dropshadow_side = (wr-right)>=2
        # is region high enough to include bottom dropshadow?
        draw_dropshadow_below = (wb-bottom) >= 1

        dropshadow_right = u'▄'
        dropshadow_below = u'▀'

        # left, top, right + bottom are the BACKGROUND
        # region. Dropshadow is drawn outside this region.
        if draw_dropshadow_side:
            self.display_at((right, top), dropshadow_right, pen)
        if draw_dropshadow_below:
            self.move((left+1, bottom))
            # +1 right is right of button background and drop shadow
            # is immediately to the right of the button rhs
            self.draw_to((right+1, bottom), dropshadow_below, pen)

    def pen(self, role="undefined", state="default", pen="pen"):
        if role == "undefined":
            role = "button"
        # force role of "button" on labels - this will force labels to
        # be drawn with the fg/bg specified for the button role.
        if role == "label":
            role = "button"

        if self.is_focus():
            state="focus"

        # deal with transitory colour scheme
        # check transitory state first
        if self._pressed:
            state = "transient"

        return super().pen(role=role, state=state, pen=pen)

    def _draw_button_label(self):
        self._label.render()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # draw decoration first so it doesn't overdraw the
        # background or label
        if self._decorated:
            self._draw_padding()
            self._draw_button_dropshadow()

        self._draw_button_background()
        self._draw_button_label()

    # FIXME: event handling methods are unclear
    def handle_event(self, event):
        if isinstance(event, MouseEvent):
            return self._handle_mouse_event(event)

    def _handle_mouse_event(self, event):
        if event.buttons == MouseEvent.LEFT_CLICK:
            self._pressed = True
            self.invalidate()
            return True
        if event.buttons == 0:
            if self._pressed:
                return self.activate()
        return False

    def handle_key_event(self, event):
        command = find_command(event, command_table="button")
        if command is not None:
            return command.apply(self)
        return False

    def accepts_focus(self):
        return True

    def activate(self):
        self._pressed = False
        self.invalidate()
        return self.on_click_callback and self.on_click_callback(self)


class RadioButton(Button):

    def __init__(self, label="--",
                 label_align="left",
                 decorated=False,
                 selected=False):
        super().__init__(label="( ) " + label,
                         label_align=label_align,
                         decorated=decorated)
        self._selected = selected

    # Needs to be part of a button group to be useful; a button group
    # is a bunch of RadioButton instances that share the same parent
    # sheet.
    #
    # FIXME: split label and visual selection indicator - also for checkbox

    def _handle_mouse_event(self, event):
        # Need more complexity here; there should only ever be a
        # single radio button in the same group active
        if event.buttons == MouseEvent.LEFT_CLICK:
            self.activate()
            return True
        return False

    def is_selected(self):
        return self._selected

    def buttons_in_group(self):
        group = []
        for sibling in self._parent._children:
            if isinstance(sibling, RadioButton):
                group.append(sibling)
        return group

    def _disable_others(self):
        # find all other radio buttons that are selected (fixme: work
        # out if selected by having a flag instead of checking visual
        # state) and unselect them.
        siblings = self.buttons_in_group()
        for sibling in siblings:
            if sibling != self:
                if sibling.is_selected():
                    sibling.set_selected(False)

    def activate(self):
        if self.is_selected():
            return None
        self.set_selected(True)
        # fixme: should be a delayed action
        return self.on_click_callback and self.on_click_callback(self)

    def set_selected(self, selected):
        if selected:
            self._selected = True
            self._label._label_text = "(•)" + self._label._label_text[3:]
            self._disable_others()
        else:
            self._selected = False
            self._label._label_text = "( )" + self._label._label_text[3:]
        self.invalidate()

    def render(self):
        # if no buttons in the group have "selected" set and this is
        # the first button in the group, select this one so there is
        # always a radio button selected in any group.
        group = self.buttons_in_group()
        sibling_selected = False
        for sibling in group:
            if sibling.is_selected():
                sibling_selected = True
        if not sibling_selected:
            self._selected = True
            self._label._label_text = "(•)" + self._label._label_text[3:]
        super().render()


class CheckBox(Button):

    def __init__(self, label="--",
                 label_align="left",
                 decorated=False):
        super().__init__(label="[ ] " + label,
                         label_align=label_align,
                         decorated=decorated)

    # fixme: make Label subscriptable? Really should not be hacking
    # around with the label contents this way
    def _handle_mouse_event(self, event):
        if event.buttons == MouseEvent.LEFT_CLICK:
            if self._label._label_text[:3] == "[ ]":
                self.activate()
            else:
                self._label._label_text = "[ ]" + self._label._label_text[3:]
            self.invalidate()
        return False

    # key event invokes activate() which needs to queue the visual
    # changes
    def activate(self):
        if self._label._label_text[:3] == "[ ]":
            self._label._label_text = "[✘]" + self._label._label_text[3:]
        else:
            self._label._label_text = "[ ]" + self._label._label_text[3:]
        self.invalidate()
        # fixme: should be a delayed action
        return self.on_click_callback and self.on_click_callback(self)


class MenuButton(Button):

    def __init__(self, label="--",
                 label_align="left",
                 decorated=False,
                 on_click=None):
        super().__init__(label=label,
                         label_align=label_align,
                         decorated=decorated)
        self._menubox = None
        if on_click is not None:
            self.on_click_callback = on_click

    def pen(self, role="undefined", state="default", pen="pen"):
        # FIXME: Ugh, this isn't how pen composition / inheritance is
        # supposed to work... find a better way.
        # Problem is that there are 2 roles involved here; one for the
        # button and another for the label. Perhaps the parent of the
        # label needs to be able to set a role for its label child?
        # Note that for menubuttons they only ever have a single child
        # (the label) and if the button "pen" method didn't force
        # labels to be buttons it would all work fine. Perhaps that
        # should be done through states? Or pens? In any case in this
        # example everything works if role is always hard-coded to
        # "menubutton".
        # if role == "undefined" or role == "button" or role == "label":
        role = "menubutton"
        return super().pen(role=role, state=state, pen=pen)

    def set_menu_box(self, menubox):
        self._menubox = menubox
        def show_menu(button):
            # fixme: this should probably be done by the frame?
            # Otherwise how to do nested menus?
            coord = (0, 1)
            transform = button.get_screen_transform()
            tcoord = transform.apply(coord)
            button.frame().show_popup(menubox, tcoord)
        self.on_click_callback = show_menu
