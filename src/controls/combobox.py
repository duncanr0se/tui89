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
from asciimatics.screen import Screen

from geometry.transforms import Transform, IDENTITY_TRANSFORM
from geometry.regions import Region

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
from sheets.dialog import MultivalueDialog

from logging import getLogger

logger = getLogger(__name__)

# +---------------+
# | Text entry  ↓ |
# +---------------+
# | Option 1      |
# | Option 2      |
#     ...
#
class ComboBox(Sheet):
    """Drop-down option box.

    Display selected line of text along with a button that displays a
    popup listbox containing selectable options.
    """

    default_text = "-- combo --"

    def __init__(self,
                 options=None):
        super().__init__()
        if options is None:
            options = []
        self._options = options
        self._children = []
        self._entry = TextEntry(text=ComboBox.default_text, owner=self)
        self.add_child(self._entry)

        self._drop_label = Label(u'▼', align="left", owner=self)
        self.add_child(self._drop_label)

        self._option_list = None
        self._has_open_popup = False
        self._pressed = False

        self._widget_focus = None

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "ComboBox({}x{}@{},{}: '{}')".format(self._region.region_width(),
                                                    self._region.region_height(),
                                                    tx, ty,
                                                    self._entry._text)

    def value(self):
        if self._entry is None:
            return None
        value = self._entry._text
        return value if value != ComboBox.default_text else None

    def set_options(self, options):
        self._options = options
        self.invalidate()

    #####                                                   LAYOUT #

    def layout(self):
        self._entry.move_to((0, 0))
        w = self._region.region_width()
        self._drop_label.move_to((w-3, 0))

    def allocate_space(self, region):
        (l, t, r, b) = region.ltrb()
        self._region = region
        # give last char of the width to the drop shadow, the next 2
        # chars of width to the "|v| button" and the rest to the label
        self._entry.allocate_space(Region(l, t, r-3, b))
        self._drop_label.allocate_space(Region(l, t, l+2, t+1))

    def compose_space(self):
        label_sr = self._entry.compose_space()
        # +2 is for the |v| "button", +1 is for the drop shadow
        return SpaceReq(label_sr.x_min()+2+1, label_sr.x_preferred()+2+1, FILL,
                        1, 1, FILL)

    #####                                                   EVENT HANDLING #

    def handle_key_event(self, kevent):

        # FIXME: if the combobox value is not the default value when
        # the list is constructed and shown due to the control gaining
        # focus then the list contents should be restricted to those
        # that match the combobox value. Add a "More..." note to the
        # drop down when it is filtered... also shrink the dropdown
        # when there are few entries to display...

        ignored_combobox_keys = []
        if self._widget_focus is not None \
           and self._widget_focus == self._option_list:
            ignored_combobox_keys = [Screen.ctrl("j"),
                                     Screen.ctrl("n"),
                                     Screen.KEY_DOWN]

        if kevent.key_code not in ignored_combobox_keys:
            command = find_command(kevent, command_table="combobox")
            if command is not None:
                result = command.apply(self)
                if result:
                    return True

        if self._widget_focus == self._entry:
            if not self._has_open_popup:
                self.show_popup_box()
            # deal with text entry events
            prev_text = self._entry._text
            result = self._entry.handle_key_event(kevent)
            if result:
                text = self._entry._text
                if text != prev_text:
                    if self._has_open_popup:
                        text = text.upper()
                        update_elts = [elt for elt in self._options \
                                       if text in elt.upper()]
                        self._option_list.update_elts(update_elts)
                # fixme: is this invalidation necessary?
                self._entry.invalidate()
                return True

        # send to list control to deal with navigation and value changes
        if self._option_list is not None and self._option_list.is_attached():
            return self._option_list.handle_key_event(kevent)

        return False

    def handle_event(self, mevent):
        if mevent.buttons == MouseEvent.LEFT_CLICK:
            self._pressed = True
            self.invalidate()
            return True
        if mevent.buttons == 0:
            if self._pressed:
                return self.activate()
        return False

    #####                                                   MISCELLANEOUS #

    def _on_menubox_detached_callback(self, arg):
        # self=ComboBox; arg=Dialog
        self._has_open_popup = False
        self._widget_focus = self._entry

    def open_popup(self):
        self._has_open_popup = True

    def close_list(self):
        self._has_open_popup = False
        self._option_list.frame().dialog_quit()

    def option_select_callback(self, from_value=None, to_value=None):
        logger.debug("     setting entry value to %s", to_value)
        self._entry.set_value(to_value)

    #####                                                   FOCUS HANDLING #

    def accepts_focus(self):
        return True

    def is_focus(self):
        # fixme: this _has_open_popup thing feels like a hack
        # fixme: what if the control is not a direct descendent of the
        # frame?
        return super().is_focus() or self._has_open_popup

    def set_focus(self, widget_focus):
        # fixme: are note-focus-in/out calls needed here?
        logger.debug("----> %s setting widget focus to %s", self, widget_focus)
        self._widget_focus = widget_focus

    # "control" protocol
    def is_widget_focus(self, widget):
        return self.is_focus() and widget == self._widget_focus

    def find_focus_candidate(self):
        # Do not descend into children; we know the control accepts
        # the focus and deals with key events on behalf of its
        # children.
        return self

    def find_next_focus(self, current_focus, found_current=False):
        # Due to the nature of the control it is known that self
        # accepts focus.
        if not found_current and self == current_focus:
            return (True, None)
        if found_current:
            return (True, self)
        return (False, None)

    def find_prev_focus(self, current_focus, previous_candidate=None, indent="__"):
        if self == current_focus:
            return (True, previous_candidate)
        return (False, self)

    def note_focus_in(self):
        # If the _pressed flag hasn't been cleared already, clear it
        # now
        self._pressed = False
        if not self._has_open_popup:
            self.show_popup_box()

    def note_focus_out(self):
        if self._has_open_popup:
            self.frame().dialog_quit()
            self._has_open_popup = False

    #####

    def activate(self):
        self._pressed = False
        self.owner().set_focus(self)

    # command handlers
    def move_to_list(self):
        if self._has_open_popup:
            return self._option_list.control_focus_first_child()
        else:
            return False

    def move_to_entry(self):
        # fixme: this works but the visual cues as to what has focus
        # inside the control are not clear.
        logger.debug("___ move to entry entered")

        if self._has_open_popup and self._option_list.is_attached():
            first_child = None
            for child in self._option_list._listbox._children:
                if child.accepts_focus():
                    first_child = child
                    break

            logger.debug("___ first child of %s is %s", self._option_list, first_child)

            if first_child is not None:
                if self._option_list._widget_focus == first_child:
                    self._widget_focus = self._entry
                    return True
        return False

    def commit(self):
        if self._has_open_popup:
            self.frame().dialog_quit()
        # If the list of entries does not contain the current value of
        # the text entry, add the value in the text entry to the list.
        if self._entry._text not in self._options:
            # add new entries to the start so they're easier to find
            self._options.insert(0, self._entry._text)
        # FIXME: is some event needed here? value-changed?
        return True

    def focus(self):
        return self

    def show_popup_box(self):
        # fixme: could cache the popup instead of rebuilding it each
        # time
        self._option_list = ListControl(options=self._options, owner=self)

        logger.debug("ooooo ListControl for %s with owner=%s",
                     self, self._option_list.owner())

        self._option_list.on_value_changed = self.option_select_callback
        # The menubox is not a child of the optionbox so doesn't
        # inherit pens in the usual way.
        # Instead we have this horrible hack that works, but requires
        # way more knowledge of the internals than is preferable.
        # fixme: add a "delegated parent" or similar for this case?
        # Perhaps everything should have a "colour delegate" that
        # defaults to the parent?
        # fixme: get pen from the OWNER instead of from the PARENT?
        # This will eventually get back to the frame still... perhaps
        # an extra level in the pen structure is needed so the colours
        # can be defined externally completely; instead of "role,
        # style, pen" could have "control, role, style, pen"
        self._force_popup_colours(self._option_list)
        # adding a child with a specific height to the dialog forces
        # the dialog to take the size of the child. FIXME: would it be
        # better to be able to force a specific size on the dialog?
        # extra -1 to account for drop shadow around the dialog
        content = Sheet(width=self._region.region_width()-1, height=5)
        content.add_child(self._option_list)
        dialog = MultivalueDialog(dispose_on_click_outside=True, owner=self)

        coord = self.get_screen_transform().apply((0, 1))

        dialog.on_detached_callback = self._on_menubox_detached_callback

        dialog.add_child(content)

        self.open_popup()
        self.frame().show_dialog(dialog, coord)

    # The popup is not a child of the optionbox so doesn't inherit
    # pens in the usual way.
    # Instead we have this horrible hack that works, but requires way
    # more knowledge of the internals than is preferable.
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

    #####                                                   PENS + DRAWING #

    def pen(self, role="undefined", state="default", pen="pen"):
        # "label" consists of labels making up "non-popup" parts of
        # optionbox
        if role == "undefined" or role == "label":
            role = "editable"
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
        (l, t, r, b) = self._region.ltrb()
        # leave space for the popup drop shadow
        self.clear(Region(l, t, r-1, b), pen)

    # fixme: when the widget is selected via mouse click, for now, it
    # is given focus but when drawn the default text is not
    # cleared. Probably will work better when mouse events are being
    # dealt with, but check this case is covered at that time.
    def _draw_entry(self):
        self._entry.render()

    def _draw_button(self):
        # this isn't taking widget's focus into account
        self._drop_label.render()

