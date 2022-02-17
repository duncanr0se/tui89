
from sheets.sheet import Sheet

from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import xSpaceReqMin
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import ySpaceReqMin

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout

class Dialog(TopLevelSheet):

    # top level sheet with an implicit border layout (unlike standard
    # top level sheet where the user gets to pick the contained
    # layout)

    _layout = None
    _title = None

    def __init__(self, frame, title=None):
        # Can't call super here or this dialog is set as the frame's
        # top level sheet! Ouch, maybe make this a frame after all...
        #super().__init__(frame=frame)
        self._frame = frame
        self._children = []
        self._title = title if title is not None else "unnamed"
        self._layout = BorderLayout(title="[INFO] - " + title)
        self._layout._parent = self

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Dialog({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._title)

    def add_child(self, child):
        self._layout.add_child(child)

    # same as space allocation for BorderLayout EXCEPT the dialog also
    # makes space for a drop shadow.  Could just use the one from the
    # parent if "border width" could be specified...
    def allocate_space(self, allocation):
        self._region = allocation
        (width, height) = allocation
        (calloc_x, calloc_y) = (width - 1, height - 1)
        child_request = self._layout.compose_space()
        # if desired or max space are less than allocation, reduce allocation to max space
        # else set allocation to desired
        # Desired space must be <= max space so no need to check it...

        # Don't allow space allocated to widget to be smaller than
        # the widget's minimum; it won't all fit on the screen,
        # but that's the widget's problem...
        calloc_x = max(xSpaceReqMin(child_request),
                       min(xSpaceReqDesired(child_request), calloc_x))
        calloc_y = max(ySpaceReqMin(child_request),
                       min(ySpaceReqDesired(child_request), calloc_y))
        self._layout.allocate_space((calloc_x, calloc_y))

    def clear(self, origin, region):
        # don't clear anything; border layout will do instead
        pass

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self._layout.render()
        self._draw_dropshadow()

    def _draw_dropshadow(self):
        (scolour, sattr, sbg) = self.frame().theme()["shadow"]
        (width, height) = self._region
        dropshadow_right = u'█'
        dropshadow_below = u'█'
        self.move((width-1, 1))
        self.draw((width-1, height-1), dropshadow_right, colour=scolour, bg=sbg)
        # x is not included when using "draw" but is when using
        # "print_at". Maybe that's as it should be?
        self.draw((1, height-1), dropshadow_below, colour=scolour, bg=sbg)
