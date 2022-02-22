
from asciimatics.event import MouseEvent

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.sheet import Sheet
from sheets.spacereq import FILL
from dcs.ink import Pen

class Separator(Sheet):

    _style = None
    _size = None

    def __init__(self, style="single", size=None):
        super().__init__()
        self._style = style
        self._size = size

    def add_child(self):
        raise RuntimeError("children not allowed")

class HorizontalSeparator(Separator):

    _line_chars = {
        "double": u'═',
        "single": u'─',
        "spacing": ' '
    }

    def __init__(self, style="single", size=None):
        super().__init__(style, size)

    def __repr__(self):
        (width, height) = self._region
        return "HorizontalSeparator({})".format(width)

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        # todo: label truncation
        pen = self.frame().theme("borders")
        (w, h) = self._region
        self.move((0, 0))
        self.draw((w, 0), HorizontalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        length = FILL if self._size is None else self._size
        return ((0, length, FILL), (0, 1, 1))


class VerticalSeparator(Separator):

    _line_chars = {
        "double": u'║',
        "single": u'│',
        "spacing": ' '
    }

    def __init__(self, style="single", size=None):
        super().__init__(style, size)

    def __repr__(self):
        (width, height) = self._region
        return "VerticalSeparator({})".format(height)

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        # todo: label truncation
        pen = self.frame().theme("borders")
        (w, h) = self._region
        self.move((0, 0))
        self.draw((0, h), VerticalSeparator._line_chars[self._style], pen)

    # layout
    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # Can shrink to 0 although that's probably not useful...
        length = FILL if self._size is None else self._size
        return ((0, 1, 1), (0, length, FILL))
