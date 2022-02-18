
from sheets.sheet import Sheet

from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import xSpaceReqMin
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import ySpaceReqMin

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.boxlayout import VerticalLayout
from sheets.buttons import Button

class Dialog(TopLevelSheet):

    # top level sheet with an implicit border layout (unlike standard
    # top level sheet where the user gets to pick the contained
    # layout)

    # on creation, create the border to use and the row layout
    # wrapped in that border. The dialog "content pane" is the
    # first child of the vertical layout, the "button pane"
    # is the second.
    _wrapper = None
    _title = None

    def __init__(self, frame, title=None):
        # Can't call super here or this dialog is set as the frame's
        # top level sheet! Ouch, maybe make this a frame after all...
        #super().__init__(frame=frame)
        self._children = []
        self._frame = frame
        self._title = title if title is not None else "unnamed"
        border = BorderLayout(title="[INFO] - " + title)
        self.add_child(border)
        self._wrapper = VerticalLayout([4, 1])
        border.add_child(self._wrapper)
        self._wrapper.add_child(self._make_content_pane())
        self._wrapper.add_child(self._make_button_pane())
        # if dialog becomes a frame, move defaults into frame
        self._default_bg_pen = frame.theme("invalid")
        self._default_fg_pen = frame.theme("invalid")

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Dialog({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._title)

    def _make_content_pane(self):
        return Sheet()

    def _make_button_pane(self):
        button = Button("OK", decorated=True)
        button.allocate_space((11, 4))

        def callback():
            self._frame.dialog_quit()

        button.on_click = callback
        return button

    # same as space allocation for BorderLayout EXCEPT the dialog also
    # makes space for a drop shadow.  Could just use the one from the
    # parent if "border width" could be specified...
    def allocate_space(self, allocation):
        self._region = allocation
        (width, height) = allocation
        (calloc_x, calloc_y) = (width - 1, height - 1)
        border_layout = self._children[0]
        border_request = border_layout.compose_space()
        # if desired or max space are less than allocation, reduce allocation to max space
        # else set allocation to desired
        # Desired space must be <= max space so no need to check it...

        # Don't allow space allocated to widget to be smaller than
        # the widget's minimum; it won't all fit on the screen,
        # but that's the widget's problem...
        calloc_x = max(xSpaceReqMin(border_request),
                       min(xSpaceReqDesired(border_request), calloc_x))
        calloc_y = max(ySpaceReqMin(border_request),
                       min(ySpaceReqDesired(border_request), calloc_y))
        border_layout.allocate_space((calloc_x, calloc_y))

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        for child in self._children:
            child.render()

        self._draw_dropshadow()

    def _draw_dropshadow(self):
        pen = self.frame().theme("shadow")
        (width, height) = self._region
        dropshadow_right = u'█'
        dropshadow_below = u'█'
        self.move((width-1, 1))
        self.draw((width-1, height-1), dropshadow_right, pen)
        # x is not included when using "draw" but is when using
        # "print_at". Maybe that's as it should be?
        self.draw((1, height-1), dropshadow_below, pen)
