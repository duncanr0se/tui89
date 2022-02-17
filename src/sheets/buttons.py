
import time

from asciimatics.event import MouseEvent

from sheets.sheet import Sheet
from sheets.spacereq import FILL


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
        (bgc, bga, bgbg) = self.top_level_sheet().frame().theme()["background"]
        (width, height) = self._region
        self.move((0, 0))
        self.draw((width-1, 0), ' ', colour=bgc, bg=bgbg)
        self.draw((width-1, height-1), ' ', colour=bgc, bg=bgbg)
        self.draw((0, height-1), ' ', colour=bgc, bg=bgbg)
        self.draw((0, 1), ' ', colour=bgc, bg=bgbg)

    def _draw_button_background(self):
        (colour, attr, bg) = self.top_level_sheet().frame().theme()["button"]
        (width, height) = self._region
        xoffset = 1 if self._decorated else 0
        yoffset = 1 if self._decorated else 0
        self.move((xoffset, yoffset))
        # looks like "draw" and "print_at" have different semantics of
        # when they do and don't draw. Width in "draw" appears not to
        # be inclusive when drawing left to right. Weird.
        width = width-2 if self._decorated else width
        self.draw((width, yoffset), ' ', colour=colour, bg=bg)

    def _draw_button_dropshadow(self):
        (scolour, sattr, sbg) = self.top_level_sheet().frame().theme()["shadow"]
        (width, height) = self._region
        dropshadow_right = u'▄'
        dropshadow_below = u'▀'
        self.print_at(dropshadow_right, (width-2, 1), colour=scolour, attr=sattr, bg=sbg)
        self.move((2, 2))
        # x is not included when using "draw" but is when using
        # "print_at". Maybe that's as it should be?
        self.draw((width-1, 2), dropshadow_below, colour=scolour, bg=sbg)

    def _draw_button_label(self):
        (colour, attr, bg) = self.top_level_sheet().frame().theme()["button"]
        (width, height) = self._region
        # assume single-line label, for now
        label_length = len(self._label) if self._label else 2
        center_x = (width - label_length) // 2
        # todo: truncate label if it's too long...
        button_label = self._label or "--"
        yoffset = 1 if self._decorated else 0
        self.print_at(button_label, (center_x, yoffset), colour=colour, attr=attr, bg=bg)

    def render(self):
        # draw rectangle for button, then draw text over the top
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        # need to think about the drawing model also; is pixel origin
        # at top-left of pixel, or in the middle? Perhaps should make
        # it in the middle since we're dealing with text. Does that
        # support dealing sensibly with boxes 0,0,20,20 and
        # 0,20,20,40? Maybe "size" needs to be an inner dimension?

        # fixme: add frame() method to Sheet

        self._draw_button_background()

        if self._decorated:
            self._draw_padding()
            self._draw_button_dropshadow()

        self._draw_button_label()

    # Fixme: need a special version of "region_contains_position" here
    # so we can account for the strangeness that is decorated buttons.
    # Currently buttons deal with mouse clicks outside their visible
    # area (but inside the bounds if padding and shadows are included).

    def handle_event(self, event):
        if isinstance(event, MouseEvent):
            return self._handle_mouse_event(event)

    def _handle_mouse_event(self, event):
        # Ignore double click + right click

        # If the event is a button release after a left press - todo,
        # should record this as a click event at a higher level? -
        # with no presses or releases between then invoke the button
        # pressed callback. Not sure quite how to work this out though
        # so for now just hack it..?

        if event.buttons == MouseEvent.LEFT_CLICK:
            self._left_click_time = time.time()
            return True

        if event.buttons == 0:
            # this timing is a bit rubbish; not sure we're getting the
            # raw events. It's possible asciimatics is doing something
            # to sythesise double clicks, or the frame's event
            # handling isn't quite right - try looping until no events
            # remain before blocking in case that's it.  Tried a tight
            # loop but behaviour is the same. It might be necessary to
            # just activate on left-click for consistency although I
            # hate that. Stick with this for now, see how it goes.
            if time.time() - self._left_click_time < 0.5:
                # fixme: Document this callback behaviour and how to
                # create the callbacks.
                return self.on_click and self.on_click()

        return False


class RadioButton(Button):

    def __init__(self, label="--", decorated=False):
        super().__init__(label="( ) " + label, decorated=decorated)


class CheckBox(Button):

    def __init__(self, label="--", decorated=False):
        super().__init__(label="[ ] " + label, decorated=decorated)
