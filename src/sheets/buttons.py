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

from sheets.sheet import Sheet
from sheets.spacereq import SpaceReq, FILL

from frames.commands import find_command

from dcs.ink import Pen

from logging import getLogger

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
                 width=None,
                 default_pen=None,
                 pressed_pen=None,
                 pen=None):
        super().__init__(default_pen=default_pen, pen=pen)
        self._label = label
        self._decorated = decorated
        if label_align != "center":
            raise RuntimeError("Only center alignment supported for button labels currently")
        self._label_align = label_align
        self._width = width
        self._pressed = False
        self._pressed_pen=pressed_pen
        self._focus_pen = None
        # Function of 1 arg (button that was clicked)
        self.on_click_callback = None

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Button({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._label)

    ####

    def add_child(self, child):
        # default Button has no children
        pass

    # default button expects to be able to fit its label + some
    # padding. It can grow as big as you like, but won't go smaller
    # than 2x4.  How about dealing with multi-line labels? Image
    # buttons?
    def compose_space(self):

        # Undecorated buttons can shrink to 1x1; decorated buttons
        # also, but they retain space for the decoration.

        button_length = len(self._label) + 2
        button_height = 1

        # decoration includes 1 unit wide border around the button
        # + dropshadow.
        if self._decorated:
            # 2 for padding + 1 for dropshadow
            button_length += 3
            button_height += 3

        # supplied width overrides calculated size
        if self._width is not None:
            fw = self._width
            return SpaceReq(fw, fw, fw,
                            button_height, button_height, button_height)
        else:
            return SpaceReq(button_height, button_length, FILL,
                            button_height, button_height, button_height)

    def allocate_space(self, allocation):
        # fixme: this is just wrong. The allocation is the allocation,
        # although the widget can decide not to fill it when drawing
        # it still must accept it as its allocation.
#        if force:
#            self._region = allocation
#        else:
            # how much space to take? Does allocation need
            # restricting? Is it ok to say "thanks but no thanks" when
            # given space?  todo: cache space requirement
            sr = self.compose_space()
            # force region to be within the sheet's space
            # composition. If this causes the sheet render to overflow
            # its bounds, so be it.
            (aw, ah) = allocation
            aw = max(sr.x_min(), min(sr.x_preferred(), aw))
            ah = max(sr.y_min(), min(sr.y_preferred(), aw))
            self._region = (aw, ah)

    def layout(self):
        # default Button has no children
        pass

    def _draw_padding(self):
        # fixme: method on Pen to return a "draw in bg colour" pen
        pen = self._parent.pen()
        pen = Pen(pen.bg(), pen.attr(), pen.bg())
        (width, height) = self._region
        for y in range(0, height-1):
            self.move((0, y))
            self.draw_to((width, y), ' ', pen)

    def _draw_button_background(self):
        # fixme: method on Pen to return a "draw in bg colour" pen
        pen = self.pen()
        pen = Pen(pen.bg(), pen.attr(), pen.bg())
        (width, height) = self._region
        xoffset = 1 if self._decorated else 0
        yoffset = 1 if self._decorated else 0
        self.move((xoffset, yoffset))
        # looks like "draw" and "print_at" have different semantics of
        # when they do and don't draw. Width in "draw" appears not to
        # be inclusive when drawing left to right. Weird.
        width = width-2 if self._decorated else width
        self.draw_to((width, yoffset), ' ', pen)

    def _draw_button_dropshadow(self):
        shadow_pen = self.frame().theme("shadow")
        bg_pen = self._parent.pen()
        pen = Pen(shadow_pen.fg(), shadow_pen.attr(), bg_pen.bg())
        (width, height) = self._region
        dropshadow_right = u'▄'
        dropshadow_below = u'▀'
        self.display_at((width-2, 1), dropshadow_right, pen)
        self.move((2, 2))
        self.draw_to((width-1, 2), dropshadow_below, pen)

    def _draw_button_label(self):
        pen = self.pen()
        (width, height) = self._region
        # assume single-line label, for now
        label_length = len(self._label) if self._label else 2
        center_x = (width - label_length) // 2
        # todo: truncate label if it's too long...
        button_label = self._label
        yoffset = 1 if self._decorated else 0
        self.display_at((center_x, yoffset), button_label, pen)

    # There are 4 pens that affect the appearance of buttons:
    #   - resting button: use frame "button" colours
    #   - focused button: use frame "focus_button" colours
    #   - clicked button: use frame "pushed_button" colours
    #   - mnemonic pen for button label: use frame "button_mnemonic" colours
    def pen(self):
        if self._pressed_pen is None:
            self._pressed_pen = self.frame().theme("pushed_button")
        if self._pen is None:
            self._pen = self.frame().theme("button")
        if self._focus_pen is None:
            self._focus_pen = self.frame().theme("focus_button")

        # check transitory state first
        if self._pressed:
            return self._pressed_pen
        # if button is the current focus use focus colour; otherwise
        # use the default
        logger.debug("is_focus = %s", self.is_focus())
        if self.is_focus():
            return self._focus_pen
        return self._pen

    def is_focus(self):
        return self.frame()._focus == self

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

    def handle_event(self, event):
        if isinstance(event, MouseEvent):
            return self._handle_mouse_event(event)

    def _handle_mouse_event(self, event):
        if event.buttons == MouseEvent.LEFT_CLICK:
            self._pressed = True
            self.invalidate()
        if event.buttons == 0:
            if self._pressed:
                return self.activate()
        return False

    def handle_key_event(self, event):
        command = find_command(event, command_table="button")
        if command is not None:
            return command.apply(self)
        return self._parent.handle_key_event(event)

    def accepts_focus(self):
        return True

    def activate(self):
        self._pressed = False
        self.invalidate()
        return self.on_click_callback and self.on_click_callback(self)


class RadioButton(Button):

    def __init__(self, label="--",
                 decorated=False,
                 default_pen=None, pen=None, pressed_pen=None):
        super().__init__(label="( ) " + label,
                         decorated=decorated,
                         default_pen=default_pen, pen=pen, pressed_pen=pressed_pen)

    # needs to be part of a button group to be useful
    #
    # For now define a button group as a bunch of RadioButton
    # instances that share the same parent sheet.
    #
    # FIXME: split label and visual selection indicator - also for checkbox

    def _handle_mouse_event(self, event):
        # Need more complexity here; there should only ever be a
        # single radio button in the same group active
        if event.buttons == MouseEvent.LEFT_CLICK:
            if self._label[:3] == "( )":
                self.activate()
            else:
                self._label = "( )" + self._label[3:]
            self.invalidate()
        return False

    def _disable_others(self):
        # find all other radio buttons that are selected (fixme: work
        # out if selected by having a flag instead of checking visual
        # state) and unselect them.
        siblings = self._parent._children
        for sibling in siblings:
            if sibling != self:
                if isinstance(sibling, RadioButton):
                    if sibling._label[:3] == "(•)":
                        sibling._label = "( )" + sibling._label[3:]
                        sibling.invalidate()

    # key event invokes activate() which needs to queue the visual
    # changes
    def activate(self):
        if self._label[:3] == "( )":
            self._label = "(•)" + self._label[3:]
        else:
            self._label = "( )" + self._label[3:]
        self._disable_others()
        self.invalidate()
        # fixme: should be a delayed action
        return self.on_click_callback and self.on_click_callback(self)

class CheckBox(Button):

    def __init__(self, label="--",
                 decorated=False,
                 default_pen=None, pen=None, pressed_pen=None):
        super().__init__(label="[ ] " + label, decorated=decorated,
                         default_pen=default_pen, pen=pen, pressed_pen=pressed_pen)

    def _handle_mouse_event(self, event):
        if event.buttons == MouseEvent.LEFT_CLICK:
            if self._label[:3] == "[ ]":
                self.activate()
            else:
                self._label = "[ ]" + self._label[3:]
            self.invalidate()
        return False

    # key event invokes activate() which needs to queue the visual
    # changes
    def activate(self):
        if self._label[:3] == "[ ]":
            self._label = "[✘]" + self._label[3:]
        else:
            self._label = "[ ]" + self._label[3:]
        self.invalidate()
        # fixme: should be a delayed action
        return self.on_click_callback and self.on_click_callback(self)

class MenuButton(Button):

    def __init__(self, label="--", decorated=False,
                 default_pen=None, pen=None, pressed_pen=None):
        super().__init__(label=label, decorated=decorated,
                         default_pen=default_pen, pen=pen, pressed_pen=pressed_pen)
        self._menubox = None

    def pen(self):
        # Button states:
        #   - resting
        #   - focus
        #   - pressed - not sure if needed
        # +
        #   - mnemonic
        #
        # fixme: mnemonic pen
        if self._pen is None:
            self._pen = self.frame().theme("menu")

        if self._focus_pen is None:
            self._focus_pen = self.frame().theme("focus_menu")
        # also set self._pressed_pen here if no initarg supplied
        # to prevent looking up the pen when _pressed_pen is
        # needed
        if self._pressed_pen is None:
            self._pressed_pen = self.frame().theme("pushed_menu")
        # still want the pressed toggle to be an effect
        return super().pen()

    def pressed_pen(self):
        return self._pressed_pen

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
