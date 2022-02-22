
import time

from asciimatics.event import MouseEvent

from sheets.sheet import Sheet
from sheets.spacereq import FILL
from sheets.spacereq import xSpaceReqMin
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqMin
from sheets.spacereq import ySpaceReqDesired

from dcs.ink import Pen

class Button(Sheet):
    """Push button sheet.

    Init params:
        - label
        - decorated
        - label_align
        - width
    Buttons have a label;
    can be decorated, or not;
    have no children;

    Can be aligned left, center, or right.
    Can have fixed width forced using "width".
    """
    _label = None
    _label_align = None

    # event support

    on_click = None
    # on_button_down?
    # on_button_up?
    # on_double_click?

    _pressed = False

    _width = None

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
        self._pressed_pen=pressed_pen

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
            return ((fw, fw, fw), (button_height, button_height, button_height))
        else:
            return ((button_height, button_length, FILL),
                    (button_height, button_height, button_height))

    def allocate_space(self, allocation, force=False):
        if force:
            self._region = allocation
        else:
            # how much space to take? Does allocation need
            # restricting? Is it ok to say "thanks but no thanks" when
            # given space?  todo: cache space requirement
            sr = self.compose_space()
            # force region to be within the sheet's space
            # composition. If this causes the sheet render to overflow
            # its bounds, so be it.
            (aw, ah) = allocation
            aw = max(xSpaceReqMin(sr), min(xSpaceReqDesired(sr), aw))
            ah = max(ySpaceReqMin(sr), min(ySpaceReqDesired(sr), aw))
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
            self.draw((width, y), ' ', pen)

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
        self.draw((width, yoffset), ' ', pen)

    def _draw_button_dropshadow(self):
        shadow_pen = self.frame().theme("shadow")
        bg_pen = self._parent.pen()
        pen = Pen(shadow_pen.fg(), shadow_pen.attr(), bg_pen.bg())
        (width, height) = self._region
        dropshadow_right = u'▄'
        dropshadow_below = u'▀'
        self.print_at(dropshadow_right, (width-2, 1), pen)
        self.move((2, 2))
        self.draw((width-1, 2), dropshadow_below, pen)

    def _draw_button_label(self):
        pen = self.pen()
        (width, height) = self._region
        # assume single-line label, for now
        label_length = len(self._label) if self._label else 2
        center_x = (width - label_length) // 2
        # todo: truncate label if it's too long...
        button_label = self._label
        yoffset = 1 if self._decorated else 0
        self.print_at(button_label, (center_x, yoffset), pen)

    def pen(self):
        if self._pressed:
            return self.pressed_pen()
        if self._pen is None:
            self._pen = self.frame().theme("button")
        return self._pen

    def pressed_pen(self):
        if self._pressed_pen is None:
            self._pressed_pen = self.frame().theme("pushed_button")
        return self._pressed_pen

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
                self._pressed = False
                self.invalidate()
                return self.on_click and self.on_click(self)
        return False


class RadioButton(Button):

    def __init__(self, label="--",
                 decorated=False,
                 default_pen=None, pen=None, pressed_pen=None):
        super().__init__(label="( ) " + label,
                         decorated=decorated,
                         default_pen=default_pen, pen=pen, pressed_pen=pressed_pen)

    # needs to be part of a button group to be useful


class CheckBox(Button):

    def __init__(self, label="--",
                 decorated=False,
                 default_pen=None, pen=None, pressed_pen=None):
        super().__init__(label="[ ] " + label, decorated=decorated,
                         default_pen=default_pen, pen=pen, pressed_pen=pressed_pen)

    def _handle_mouse_event(self, event):
        if event.buttons == MouseEvent.LEFT_CLICK:
            if self._label[:3] == "[ ]":
                self._label = "[X]" + self._label[3:]
            else:
                self._label = "[ ]" + self._label[3:]
            self.invalidate()
        return False


class MenuButton(Button):

    _menubox = None

    def __init__(self, label="--", decorated=False,
                 default_pen=None, pen=None, pressed_pen=None):
        super().__init__(label=label, decorated=decorated,
                         default_pen=default_pen, pen=pen, pressed_pen=pressed_pen)

    # override to return parent's pen
    def pen(self):
        if self._pen is None:
            self._pen = self._parent.pen()
            # also set self._pressed_pen here if no initarg supplied
            # to prevent looking up the pen when _pressed_pen is
            # needed
            if self._pressed_pen is None:
                self._pressed_pen = Pen(self._pen.bg(), self._pen.attr(), self._pen.fg())
        # still want the pressed toggle to be an effect
        return super().pen()

    # returns inverse of standard pen to show visual difference unless
    # overridden by initarg.
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

        self.on_click = show_menu
