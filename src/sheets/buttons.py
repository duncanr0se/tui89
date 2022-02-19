
import time

from asciimatics.event import MouseEvent

from sheets.sheet import Sheet
from sheets.spacereq import FILL

from dcs.ink import Pen

class Button(Sheet):

    _label = None

    # event support
    _left_click_time = 0

    on_click = None
    # on_button_down?
    # on_button_up?
    # on_double_click?

    # todo: work out how underlying library calculates double click,
    # think it might be screwing our single click! Quck single click
    # doesn't register.

    # simple class that draws a border around itself and manages a
    # single child - todo, complicate this up by making it support
    # scrolling!

    _pressed = False

    # fixme: add width, align, ... options
    def __init__(self, label=None, decorated=True):
        super().__init__()
        self._label = label
        self._decorated = decorated

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Button({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._label)

    def add_child(self, child):
        # default Button has no children
        pass

    # default button expects to be able to fit its label + < and >, as
    # well as some padding. It can grow as big as you like, but won't
    # go smaller than 2x4.
    # How about dealing with multi-line labels? Image buttons?
    def compose_space(self):

        # QUERY: should all buttons be a fixed size?
        # Calculate space needed for decorated and vanilla cases
        button_length = len(self._label) + 2 if self._label else 4
        button_height = 1

        if self._decorated:
            # 2 for padding + dropshadow
            button_length += 3
            button_height += 3

        # Undecorated buttons can shrink to 1x1; decorated buttons
        # also, but they retain space for the decoration.
        return ((button_height, button_length, FILL), (button_height, button_height, FILL))

    def allocate_space(self, allocation):
        # todo: check region > minimum composed space
        self._region = allocation

    def layout(self):
        # default Button has no children
        pass

    def _draw_padding(self):
        pen = self.top_level_sheet()._default_bg_pen
        (width, height) = self._region
        self.move((0, 0))
        self.draw((width-1, 0), ' ', pen)
        self.draw((width-1, height-1), ' ', pen)
        self.draw((0, height-1), ' ', pen)
        self.draw((0, 1), ' ', pen)

    def _draw_button_background(self):
        if self._pressed:
            pen = self.frame().theme("selected_focus_field")
        else:
            pen = self.frame().theme("button")
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
        bg_pen = self.top_level_sheet()._default_bg_pen
        pen = Pen(shadow_pen.fg(), shadow_pen.attr(), bg_pen.bg())
        (width, height) = self._region
        dropshadow_right = u'▄'
        dropshadow_below = u'▀'
        self.print_at(dropshadow_right, (width-2, 1), pen)
        self.move((2, 2))
        # x is not included when using "draw" but is when using
        # "print_at". Maybe that's as it should be?
        self.draw((width-1, 2), dropshadow_below, pen)

    def _draw_button_label(self):
        if self._pressed:
            pen = self.frame().theme("selected_focus_field")
        else:
            pen = self.frame().theme("button")
        (width, height) = self._region
        # assume single-line label, for now
        label_length = len(self._label) if self._label else 2
        center_x = (width - label_length) // 2
        # todo: truncate label if it's too long...
        button_label = self._label or "--"
        yoffset = 1 if self._decorated else 0
        self.print_at(button_label, (center_x, yoffset), pen)

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        # fixme: need to know the state of the sheet so if we're asked
        # to draw ourselves we don't end up actually doing anything.
        # This would prevent the "dialog exit button redrawn after dialog
        # already closed" issue being seen currently.
#        if self.top_level_sheet().is_detached():
#            return

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
                return self.on_click and self.on_click()
        return False


class RadioButton(Button):

    def __init__(self, label="--", decorated=False):
        super().__init__(label="( ) " + label, decorated=decorated)


class CheckBox(Button):

    def __init__(self, label="--", decorated=False):
        super().__init__(label="[ ] " + label, decorated=decorated)
