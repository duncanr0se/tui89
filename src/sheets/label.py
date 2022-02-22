
from asciimatics.event import MouseEvent

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.sheet import Sheet
from sheets.spacereq import SpaceReq, FILL
from dcs.ink import Pen

class Label(Sheet):

    _label_text = None

    def __init__(self, label_text="", default_pen=None, pen=None):
        super().__init__(default_pen=default_pen, pen=pen)
        self._label_text = label_text

    def __repr__(self):
        (width, height) = self._region
        return "Label({}x{}, '{}')".format(width, height, self._label_text)

    def pen(self):
        if self._pen is None:
            self._pen = Frame.THEME["tv"]["label"]
        return self._pen

    def add_child(self):
        raise RuntimeError("children not allowed")

    # drawing / redisplay
    def render(self):
        # todo: label alignment
        # todo: label truncation
        pen = self.frame().theme("label")
        self.display_at((0, 0), self._label_text, pen)

    # layout
    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # todo: check if this needs a smaller minimum (3 chars + "..."?)
        return SpaceReq(len(self._label_text), len(self._label_text), FILL, 1, 1, FILL)
