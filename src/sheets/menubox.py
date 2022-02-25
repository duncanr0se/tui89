
from sheets.sheet import Sheet
from sheets.spacereq import FILL, SpaceReq
from sheets.borderlayout import BorderLayout
from sheets.listlayout import ListLayout
from sheets.toplevel import TopLevelSheet
from sheets.separators import Separator
from sheets.buttons import Button

from frames.commands import find_command

from asciimatics.screen import Screen

# A layout that arranges its children in a column. Each child is
# packed as closely as possible to its siblings. Layout takes minimum
# width necessary to provide its children with the width they request.
class MenuBox(TopLevelSheet):

    def __init__(self, default_pen=None, pen=None):
        # fixme: TopLevelSheet constructor does some nasty stuff with
        # frames - do not call it for other top level sheet
        # types. Rework TopLevelSheet to make it safe.
        #super().__init__(default_pen=default_pen, pen=pen)
        self._children = []
        self._border = BorderLayout(style="single")
        self.add_child(self._border)
        self._item_pane = ListLayout()
        self._border.add_child(self._item_pane)
        self._default_pen=default_pen
        self._pen=pen
        self._focus = None

    def __repr__(self):
        return "MenuBox({} entries)".format(len(self._item_pane._children))

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

    # events
    def accepts_focus(self):
        # won't get focus by default because not a leaf pane (has
        # children) but when children fail to handle an event and pass
        # it back to their parent this indicates that the parent will
        # attempt to do something with the event
        return True

    # events
    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="menubox")
        if command is not None:
            return command.apply(self)

        return False

    # FIXME: on mouse event, see if the widget the mouse event occurs
    # on accepts the focus and if it does, set the top level's focus
    # to that widget

    def _find_selected(self):
        for child in self._item_pane._children:
            if not isinstance(child, Separator):
                if child._pressed == True:
                    return child
        return None

    def _select_first(self):
        for child in self._item_pane._children:
            if isinstance(child, Button):
                child._pressed = True
                child.invalidate()
                return True
        return False

    def _select_previous(self, selected):
        found = False
        for child in reversed(self._item_pane._children):
            if found:
                if isinstance(child, Button):
                    selected._pressed = False
                    child._pressed = True
                    selected.invalidate()
                    child.invalidate()
                    return True
            if child == selected:
                found = True
        return False

    def _select_next(self, selected):
        found = False
        for child in self._item_pane._children:
            if found:
                if isinstance(child, Button):
                    selected._pressed = False
                    child._pressed = True
                    selected.invalidate()
                    child.invalidate()
                    return True
            if child == selected:
                found = True
        return False

    def _activate(self, selected):
        return selected.activate()
