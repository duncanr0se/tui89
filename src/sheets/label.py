
from asciimatics.event import MouseEvent

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.sheet import Sheet
from sheets.spacereq import FILL
from dcs.ink import Pen

class Label(Sheet):

    _label_text = None

    def __init__(self, label_text="", default_pen=None):
        super().__init__(default_pen)
        self._label_text = label_text

    def __repr__(self):
        (width, height) = self._region
        return "Label({}x{}, '{}')".format(width, height, self._label_text)

    def default_pen(self):
        if self._default_pen is None:
            return Frame.THEME["tv"]["label"]
        return super().default_pen()

    def add_child(self):
        raise RuntimeError("children not allowed")

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        # todo: label truncation
        pen = self.frame().theme("label")
        self.print_at(self._label_text, (0, 0), pen)

    # layout
    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # Can shrink to 0 although that's probably not useful...
        return ((0, len(self._label_text), FILL), (0, 1, FILL))