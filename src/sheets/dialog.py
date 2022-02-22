
from sheets.sheet import Sheet

from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import xSpaceReqMin
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import ySpaceReqMin
from sheets.spacereq import combine_spacereqs
from sheets.spacereq import add_to_preferred
from sheets.spacereq import FILL

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.boxlayout import VerticalLayout
from sheets.buttons import Button
from sheets.frame import Frame

from dcs.ink import Pen

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

    _text = None

    _content_pane = None

    _okButton = None

    _style = None

    prefix = {
        "alert": "[ALERT] - ",
        "info": "[INFO] - ",
        "yes/no": "[YES or NO] - ",
        "composite": ""
    }

    def __init__(self, title=None, text=None, style="info",
                 default_pen=None, pen=None):
        # Can't call super here or this dialog is set as the frame's
        # top level sheet! Ouch, maybe make this a frame after all...
        #super().__init__(frame=frame)
        self._children = []
        self._title = title if title is not None else "unnamed"
        self._style = style
        border = BorderLayout(title=Dialog.prefix[style] + title)
        self.add_child(border)
        self._wrapper = VerticalLayout([4, 1])
        border.add_child(self._wrapper)
        # fixme: scrolling dialog content?
        self._wrapper.add_child(self._make_content_pane(text))
        self._wrapper.add_child(self._make_button_pane())
        self._text = text
        self._default_pen = default_pen
        self._pen = pen

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Dialog({}x{}@{},{}: '{}')".format(width, height, tx, ty, self._title)

    def _make_content_pane(self, text):
        # could instead write "find_content_pane", "find_button_pane" methods...
        self._content_pane = Sheet()
        return self._content_pane

    def _make_button_pane(self):
        self._okButton = Button("OK", decorated=True, width=11)

        def callback(button):
            button.frame().dialog_quit()

        self._okButton.on_click = callback
        return self._okButton

    def default_pen(self):
        if self._default_pen is None:
            # FIXME: make constructing pens easier!
            # Surely we have a _frame reference now?
            (fg, attr, bg) = Frame.THEMES["tv"][self._style]
            self._default_pen = Pen(fg=fg, attr=attr, bg=bg)
        return self._default_pen

    def compose_space(self):
        # make sufficient space for:
        # content pane + button pane
        # + border
        # + drop shadow
        #
        # content pane should be big enough to hold the
        # text + some padding (fixme: put in a padding
        # pane when we have one)
        #
        # Content pane doesn't actually know the text it
        # is wrapping (yet!) so frig the size here. Do
        # this properly (make content pane some widget that
        # already knows its text) at some point.
        #
        # fixme: need to be able to draw to a sheet before
        # it's attached, or calculate size for text before
        # it's attached. Going to need this for scrolling
        # anyway...
        #
        # fixme: deal with multi-line text
        text_size = len(self._text)
        # fixme: padding shouldn't be present (use spacing
        # pane) or at least should be configurable...
        content_pane_size = ((text_size, text_size+4, FILL), (1, 5, FILL))
        #
        # Also hard-code the button pane (minimum + preferred)
        # sizes for now
        # FIXME: hardcoded index
        button_pane = self._wrapper._children[1]
        button_pane_size = button_pane.compose_space()
        vbox_pane_size = combine_spacereqs(content_pane_size, button_pane_size)
        # border adds +1 on each side
        # shadow adds +1 on right + bottom
        border_adds = (3, 3)
        vbox_pane_size = add_to_preferred(vbox_pane_size, border_adds)
        return vbox_pane_size

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

        pen = self.pen()
        # fixme: use a real pane type to hold the text
        self._content_pane.print_at(self._text, (2, 2), pen)

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



def alert(frame, message):
    dialog = Dialog(title="???", style="alert", text=message)
    frame.show_dialog(dialog)
