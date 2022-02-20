
class Pen():

    _foreground = None
    _attribute = None
    _background = None

    def __init__(self, fg=7, attr=0, bg=0):
        self._foreground = fg
        self._attribute = attr
        self._background = bg

    def fg(self):
        return self._foreground

    def attr(self):
        return self._attribute

    def bg(self):
        return self._background
