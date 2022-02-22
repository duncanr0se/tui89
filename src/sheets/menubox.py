
from sheets.sheet import Sheet
from sheets.spacereq import xSpaceReqMax
from sheets.spacereq import xSpaceReqDesired
from sheets.spacereq import ySpaceReqMax
from sheets.spacereq import ySpaceReqDesired
from sheets.spacereq import FILL
from sheets.borderlayout import BorderLayout
from sheets.listlayout import ListLayout
from sheets.toplevel import TopLevelSheet

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings. Layout takes minimum
# width necessary to provide its children with the width they request.
class MenuBox(TopLevelSheet):

    def __init__(self):
        self._children = []
        self._border = BorderLayout(style="single")
        self.add_child(self._border)
        self._item_pane = ListLayout()
        self._border.add_child(self._item_pane)

    def layout(self):
        for child in self._children:
            child.move_to((0, 0))
            child.layout()

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")
        self.clear((0, 0), self._region)
        for child in self._children:
            child.render()

    def allocate_space(self, allocation):

        self._region = allocation
        (width, height) = allocation

        for child in self._children:
            sr = child.compose_space()
            ch = ySpaceReqDesired(sr)
            child.allocate_space((width, ch))

    def compose_space(self):
        reqheight = 0
        reqwidth = 0
        for child in self._children:
            sr = child.compose_space()
            reqwidth = max(reqwidth, xSpaceReqDesired(sr))
            reqheight += ySpaceReqDesired(sr)
        return ((1, reqwidth, FILL), (reqheight, reqheight, FILL))

    def set_items(self, items):
        self._item_pane.set_children(items)
