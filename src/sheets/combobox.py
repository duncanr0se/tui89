#
# Copyright 2022 Duncan Rose
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from asciimatics.event import MouseEvent

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.sheet import Sheet
from sheets.spacereq import SpaceReq, FILL
from dcs.ink import Pen
from sheets.label import Label
from sheets.buttons import Button, MenuButton
from sheets.dialog import alert
from sheets.menubox import MenuBox
from sheets.separators import VerticalSeparator
from frames.commands import find_command
from sheets.textentry import TextEntry
from controls.listcontrol import ListControl

# +---------------+
# | Option 1    ↓ |
# +---------------+
# | Option 2      |
# | Option 3      |
#     ...
#
class ComboBox(Sheet):
    """Drop-down option box.

    Display selected line of text along with a button that displays a
    popup listbox containing selectable options.
    """

    default_text = "-- combo --"

    # fixme: dropdown should always be shown when the control is the
    # focus; typing in the combo box filters the items shown in the
    # list to those that match the text entered. The user can then
    # either press "return" to "commit" the text that's entered and
    # add a new option to the box (if there isn't already an option
    # matching that text) or can select from the list.
    #
    # fixme: think this is a control rather than a widget. It mediates
    # the behaviour of a bunch of contained widgets in a non-trivial
    # way...
    #
    # fixme: maybe this shouldn't be a drop down; maybe it should just
    # be a list control selector that can sometimes also update the
    # list. Then it could also be used to identify leaf nodes in tree
    # controls?
    #
    # + combo box - shows selected item, list pops up, text entry can
    # update or filter list. If text does not match anything in list,
    # display "return to add" prompt (where? in status bar? would be
    # best).
    #
    # + fixed combo box - as above except list is always shown as a
    # fixed list, not a popup
    #
    # + filter combo box - as above except list could be a tree, and
    # combo text is used to highlight and navigate to existing entries
    # not to add new entries.

    def __init__(self,
                 options=None):
        super().__init__()
        if options is None:
            options = []
        self._options = options
        self._children = []
        self._entry = TextEntry(text=ComboBox.default_text)
        self.add_child(self._entry)
        self._drop_label = Label(u'▼', align="left")
        self.add_child(self._drop_label)
        self._option_list = None
        self._has_open_popup = False
        self._pressed = False
        # when one of the options in the combo box is selected this
        # value is used to indicate which option it is. When new text
        # is added to the combo box, that text is added as an option
        # when it is committed and that option's index is captured
        # here.
        #
        # The allows the code to differentiate between an untouched
        # combo box, a combox box where text has been entered but not
        # committed, and a combo box holding a valid selection.
        self._selected_option_index = -1

    def __repr__(self):
        (left, top, right, bottom) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "ComboBox({}x{}@{},{}: '{}')".format(right-left, bottom-top,
                                                     tx, ty,
                                                     self._entry._text)

    def value(self):
        value = self._entry._text
        return value if value != ComboBox.default_text else None

    def set_options(self, options):
        self._options = options
        self.invalidate()

    def layout(self):
        self._entry.move_to((0, 0))
        (left, _, right, _) = self._region
        w = right-left
        self._drop_label.move_to((w-2, 0))

#    def handle_key_event(self, kevent):
#        command = find_command(kevent, command_table="optionbox")
#        if command is not None:
#            return command.apply(self)
#        return self._parent.handle_key_event(kevent)

    def handle_event(self, mevent):
        raise RuntimeError("mouse click over combobox!")
        if mevent.buttons == MouseEvent.LEFT_CLICK:
            self._pressed = True
            self.invalidate()
            return True
        if mevent.buttons == 0:
            if self._pressed:
                return self.activate()
        return False

    def accepts_focus(self):
        return True

    def is_focus(self):
        # FIXME: this is horrible; the combo box should have the focus
        # and manage the child widgets accordingly. Probably that will
        # work fine once mouse + keyboard events are dealt with by the
        # combo box.
        return self.frame()._focus in [self, self._entry] or \
            self._has_open_popup

#    def _on_menubox_detached_callback(self, arg):
#        # self=OptionBox; arg=MenuBox
#        self._has_open_popup = False

    def open_popup(self):
        self._has_open_popup = True

    def menu_click_callback(self, button):
        pass
#        self._entry.reset()
#        self._entry._text = button._label._label_text
#        button.frame().menu_quit()
#        self.frame().set_focus(self._entry)

    # FIXME: want to do something slightly different depending on if
    # this is activated by mouse or by label navigation... or do we?
    def activate(self):
        self._pressed = False
        # focus is set on self but then immediately moved to the
        # menubox. Keep focus l&f for main control even when menu is
        # present.
        #
        # fixme: should the text be cleared if it is the default
        # holding text?
        #
        # Always clear the text. It's either already saved in the
        # valid options (return pressed) or it isn't wanted?
        #
        # Reset control to default text if it loses the focus without
        # the entered text (if any) being committed.
        if self._selected_option_index < 0:
            self._entry.reset()
        self.show_menu_box()
        # FIXME: this isn't going to work - or is it? Might need to
        # rethink how popups are handled so that they aren't top level
        # sheets - or so that they are not modal.
        self.frame().set_focus(self._entry)

    def show_menu_box(self):
        # fixme: could cache this menubox instead of rebuilding it
        # each time
        # menubox = MenuBox(width=self.width())
        # menubox.set_items([MenuButton(label=button, on_click=self.menu_click_callback) \
                           # for button in self._options])
        listcontrol = ListControl(options=self._options)
        # The menubox is not a child of the optionbox so doesn't
        # inherit pens in the usual way.
        # Instead we have this horrible hack that works, but requires
        # way more knowledge of the internals than is preferable.
        self._force_popup_colours(listcontrol)

        coord = (0, 1)
        # transform = self.get_screen_transform()
        # tcoord = transform.apply(coord)
        #menubox.on_detached_callback = self._on_menubox_detached_callback
        #
        # FIXME: the list control is *not* a popup. How to get it on
        # screen? Need to attach it to the widget, somehow.
        #self.frame().show_popup(menubox, tcoord)
        #
        # FIXME: maybe popup menus shouldn't be top level sheets? They
        # could just be ordinary sheets... probably. Not sure about
        # dialogs.
        self.add_child(listcontrol)

        # fixme: must be able to do this more cleanly. Suspect need
        # relayout parent method that does the space composition /
        # allocation and lays children out as expected.
        # fixme: relayout_parent... or at least compose / allocate space
        # fixme: the parent no longer knows its correct extents so
        # doesn't handle mouse events that it should handle...
        # fixme: reduce region when list control is closed...
        #
        # fixme: this is not sufficient; the combo box has the right
        # extents but the listlayout / boxlayout it is placed into
        # does not. Need to properly lay out the control, or make it a
        # frame. Bah.
        (l, t, r, b) = self._region
        self._region = (l, t, r, b+5)
        #
        listcontrol.allocate_space((0, 1, self.width(), 5))
        self.open_popup()
        listcontrol.move_to(coord)
        listcontrol.layout()
        # FIXME: might not need to invalidate the whole combo control...
        # self.invalidate()
        listcontrol.render()

    # The menubox is not a child of the optionbox so doesn't
    # inherit pens in the usual way.
    # Instead we have this horrible hack that works, but requires
    # way more knowledge of the internals than is preferable.
    def _force_popup_colours(self, menubox):
        # Force menubutton colours
        force_pen = self.pen(role="optionbox", state="default", pen="accelerator")
        menubox.set_pen(force_pen, role="menubutton", state="default", which="accelerator")

        force_pen = self.pen(role="menubutton", state="focus", pen="accelerator")
        menubox.set_pen(force_pen, role="menubutton", state="focus", which="accelerator")

        force_pen = self.pen(role="editable", state="focus", pen="pen")
        menubox.set_pen(force_pen, role="menubutton", state="default", which="pen")
        # Force menubox colours
        menubox.set_pen(force_pen, role="menubox", state="default", which="pen")
        menubox.set_pen(force_pen, role="menubox", state="border", which="pen")

    def pen(self, role="undefined", state="default", pen="pen"):
        # "label" consists of labels making up "non-popup" parts of
        # optionbox
        if role == "undefined" or role == "label":
            # role = "editable"
            role, state = "button", "transient"
        # FIXME: pretty sure focus is generally set to the textentry,
        # NOT this widget. Which is a bit sucky. This widget needs to
        # take the focus.
        if self.is_focus():
            state = "focus"
        if self._pressed:
            role, state = "button", "transient"
        return super().pen(role=role, state=state, pen=pen)

    def render(self):
        self._draw_background(self.pen())
        self._draw_entry()
        self._draw_button()

    def _draw_background(self, pen):
        self.clear(self._region, pen)

    # fixme: when the widget is selected via mouse click, for now, it
    # is given focus but when drawn the default text is not
    # cleared. Probably will work better when mouse events are being
    # dealt with, but check this case is covered at that time.
    def _draw_entry(self):
        self._entry.render()

    def _draw_button(self):
        # this isn't taking widget's focus into account
        self._drop_label.render()

    def allocate_space(self, region):
        (l, t, r, b) = region
        self._region = region
        # give last 2 chars of width to the "|v| button" and the rest
        # to the label
        self._entry.allocate_space((l, t, r-2, b))
        self._drop_label.allocate_space((l, t, l+2, t+1))

    def compose_space(self):
        # fixme: might need to do something different here...
        label_sr = self._entry.compose_space()
        # +2 is for the |v| "button"
        return SpaceReq(label_sr.x_min()+2, label_sr.x_preferred()+2, FILL,
                        1, 1, FILL)
