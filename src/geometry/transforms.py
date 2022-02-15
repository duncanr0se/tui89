
class Transform():
    """Transform coordinates by a translation."""
    _dx = 0
    _dy = 0

    def __init__(self, dx, dy):
        self._dx = dx
        self._dy = dy

    def __repr__(self):
        return "Transform({},{})".format(self._dx, self._dy)

    def apply(self, coord):
        (x, y) = coord
        return (x + self._dx, y + self._dy)

    def invert(self):
        return Transform(-self._dx, -self._dy)


# no-op transform
IDENTITY_TRANSFORM = Transform(0, 0)
