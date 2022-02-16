
from sheets.sheet import Sheet
from sheets.spacereq import FILL


class Button(Sheet):

    _label = None

    # simple class that draws a border around itself and manages a
    # single child - todo, complicate this up by making it support
    # scrolling!

    def __init__(self, label=None):
        super().__init__()
        self._label = label

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
        # 8 = '  < ' + ' >  ' -- add extra slop for desired size
        label_length = len(self._label) + 8 if self._label else 8
        return ((2, label_length, FILL), (2, 2, FILL))

    def allocate_space(self, allocation):
        # todo: check region > minimum composed space
        self._region = allocation

    def layout(self):
        # default Button has no children
        pass

    def render(self):


        # pull this out into some kind of utility module
        hierarchy = []
        x = self
        tls = self.top_level_sheet()
        while x != tls:
            hierarchy.append(x)
            x = x._parent
            if x == tls:
                hierarchy.append(x)


        # draw rectangle for button, then draw text over the top
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        # need to think about the drawing model also; is pixel origin
        # at top-left of pixel, or in the middle? Perhaps should make
        # it in the middle since we're dealing with text. Does that
        # support dealing sensibly with boxes 0,0,20,20 and
        # 0,20,20,40? Maybe "size" needs to be an inner dimension?

        # draw rectangle for button, then draw text over the top
        (colour, attr, bg) = self.top_level_sheet().theme()["button"] # and "focus_button" for later
        (width, height) = self._region
        self.move((0, 0))
        self.draw((width-1, 0), ' ', colour=colour, bg=bg)
        # todo: draw shadow
        # assume single-line label, for now
        label_length = len(self._label) + 6 if self._label else 6
        center_x = (width - label_length) // 2
        # todo: truncate label if it's too long...
        (colour, attr, bg) = self.top_level_sheet().theme()["label"]
        self.print_at('< ' + self._label + ' >', (center_x, 0), colour=colour, attr=attr, bg=bg)


class RadioButton(Button):

    def render(self):
        # draw rectangle for button, then draw text over the top
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # draw rectangle for button, then draw text over the top
        (width, height) = self._region
        self.move((0, 0))
        for coord in (width-1, 0), (width-1, height-1), (0, height-1), (0, 0):
            self.draw(coord, '*')
        # assume single-line label, for now
        label_length = len(self._label) + 6 if self._label else 6
        center_x = (width - label_length) // 2
        center_y = height // 2
        # todo: truncate label if it's too long...
        self.print_at('( ) ' + self._label, (center_x, center_y))


class CheckBox(Button):

    def render(self):
        # draw rectangle for button, then draw text over the top
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        # draw rectangle for button, then draw text over the top
        (width, height) = self._region
        self.move((0, 0))
        for coord in (width-1, 0), (width-1, height-1), (0, height-1), (0, 0):
            self.draw(coord, '*')
        # assume single-line label, for now
        label_length = len(self._label) + 6 if self._label else 6
        center_x = (width - label_length) // 2
        center_y = height // 2
        # todo: truncate label if it's too long...
        self.print_at('[ ] ' + self._label, (center_x, center_y))
