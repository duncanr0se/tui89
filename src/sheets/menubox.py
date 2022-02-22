
from sheets.sheet import Sheet
from sheets.spacereq import FILL, SpaceReq
from sheets.borderlayout import BorderLayout
from sheets.listlayout import ListLayout
from sheets.toplevel import TopLevelSheet

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings. Layout takes minimum
# width necessary to provide its children with the width they request.
class MenuBox(TopLevelSheet):

    def __init__(self, default_pen=None, pen=None):
        # fixme: TopLevelSheet constructor does some nasty stuff with
        # frames - do not call it for othre top level sheet
        # types. Rework TopLevelSheet to make it safe.
        #super().__init__(default_pen=default_pen, pen=pen)
        self._children = []
        self._border = BorderLayout(style="single")
        self.add_child(self._border)
        self._item_pane = ListLayout()
        self._border.add_child(self._item_pane)
        self._default_pen=default_pen
        self._pen=pen

    def layout(self):
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    # Set default pen for self and children
    def default_pen(self):
        if self._default_pen is None:
            self._default_pen = self.frame().theme("menubar")
        return self._default_pen

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear((0, 0), self._region)
        for child in self._children:
            child.render()

    # allocate smallest space possible to fit children - probably need
    # some extra parameter to say we're trying to minimise
    def allocate_space(self, allocation):
        (awidth, aheight) = allocation
        cw = awidth
        ch = aheight
        for child in self._children:
            sr = child.compose_space()
            ch = sr.y_preferred()
            cw = sr.x_preferred()
            child.allocate_space((cw, ch))
            self._region = (min(cw, awidth), min(ch, aheight))

    def compose_space(self):
        # Sheet hierarchy is:
        #
        # menubox
        #   + borderlayout - how does this know to minimise region?
        #       + listlayout
        #           + button
        #           + button
        #           + separator
        #           + button
        reqwidth = 0
        reqheight = 0
        for child in self._children:
            sr = child.compose_space()
            reqwidth = max(reqwidth, sr.x_preferred())
            reqheight += sr.y_preferred()
        return SpaceReq(reqwidth, reqwidth, reqwidth, reqheight, reqheight, reqheight)

    def set_items(self, items):
        self._item_pane.set_children(items)
