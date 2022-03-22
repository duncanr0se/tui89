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

    # fixme: dropdown should always be shown when the control is the
    # focus; typing in the combo box filters the items shown in the
    # list to those that match the text entered. The user can then
    # either press "return" to "commit" the text that's entered and
    # add a new option to the box (if there isn't already an option
    # matching that text) or can select from the list.
    #
    # Note that the "list" is actually a multivalue dialog that wraps
    # a list control. This allows the "list" to appear over its
    # background without causing a relayout and redraw of the parent
    # container of the combo box.
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
        self._entry = TextEntry(text=ComboBox.default_text, owner=self)
        self.add_child(self._entry)

        self._drop_label = Label(u'▼', align="left", owner=self)
        self.add_child(self._drop_label)

        self._option_list = None
        self._has_open_popup = False
        self._pressed = False
        #
        # FIXME: THIS ISN'T USED ANYWHERE, IS IT NEEDED?
        #
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

    #####                                                   LAYOUT #

    def layout(self):
        self._entry.move_to((0, 0))
        (left, _, right, _) = self._region
        w = right-left
        self._drop_label.move_to((w-2, 0))

    def allocate_space(self, region):
        (l, t, r, b) = region
        self._region = region
        # give last 2 chars of width to the "|v| button" and the rest
        # to the label
        self._entry.allocate_space((l, t, r-2, b))
        self._drop_label.allocate_space((l, t, l+2, t+1))

    def compose_space(self):
        label_sr = self._entry.compose_space()
        # +2 is for the |v| "button"
        return SpaceReq(label_sr.x_min()+2, label_sr.x_preferred()+2, FILL,
                        1, 1, FILL)

    #####                                                   EVENT HANDLING #

    # if events are not handled, send them to the "textentry" and
    # handle them there.

    # events by type:
    # GLOBAL
    # ctrl+w, tab, shift+tab
    #
    # DIALOG
    # esc
    #
    # TEXT ENTRY
    # ctrl+a, home, ctrl+e, end, ctrl+f, →, ctrl+b, ←, ctrl+d, del,
    # backspace, newline, esc
    #
    # LIST CONTROL
    # esc, pgup, pgdn, ctrl+p, ↑, cltr+n, ↓
    #
    # OPTION BOX [NOT ACTUALLY USED, BUT FYI]
    # return

    # Note that even when the popup is on screen the text entry has
    # the focus. This confuses the "cycle_focus" methods on the frame
    # which expects the focus to be in the active popup, if there is
    # an active popup...

    # Perhaps need some way to feed all the events through to the
    # control and treat all parts of the control as atomic parts when
    # viewed outside the control for tabbing and propagation to parent
    # behaviours. Not sure quite how to do that. Add more hacks to
    # support it, for now.

    # Should the control take over handling of all the events for its
    # region? Probably yes it should - including deciding on where the
    # focus is. How would this work?

    # Is it enough to set the control as the parent of the dialog box?

    # Perhaps the popup needs an "owner" to send events to?

    # DEAL WITH BEHAVIOURS ONE BY ONE AND RATIONALISE THEM BETTER
    # LATER.

    # handle key events indicating commands in the "combobox" command
    # table, this is automatic as long as the handle_key_event method
    # is implemented here because it is the parent of the textentry;

    # if (keyboard) events are still not handled, send them to the
    # multivalue dialog and handle them there;

    # if they still are not handled, pass them on to the parent sheet
    # for handling;

    def handle_key_event(self, kevent):
        # nearly all the events we might be interested in here are
        # already dealt with by the other widgets within the
        # control. Need to make THIS widget the control and then it
        # can override the default behaviours of its contained
        # widgets.
        #
        # FIXME: combo box needs to handle TAB/S-TAB and close the
        # list control, and then pass the TAB/S-TAB on to the
        # frame. What a mess!

        # FIXME: PRETTY SURE THIS CAN ALL BE MADE TO WORK BUT IT'S A
        # HORRIBLE MESS. THE CONTROLS WANT TO HANDLE THE SAME KEY
        # EVENTS IN DIFFERENT WAYS AND IN DIFFERENT ORDERS.
        #
        # DRAW THE DIFFERENT ACTORS OUT ON PAPER, DECIDE ON HOW EVENTS
        # SHOULD BE SENT TO WIDGETS AND WHAT COMMANDS ARE NEEDED.

        #   +-----------------+
        #   | TEXT ENTRY | DL |
        #   +-----------------+
        #   |+---------------+|
        #   || LABEL         ||
        #   |+----           +|
        #   || ...           ||
        #   |+--             +|
        #   ||LIST CONTROL   ||
        #   |+---------------+|
        #   |DIALOG           |
        #   +-----------------+

        # COMBOBOX CONTROL HAS FOCUS; IF POPUP IS OPEN, POPUP CAN HAVE
        # FOCUS. NEED A WAY TO ESCAPE THE POPUP (UPWARDS, OPPOSITE OF
        # CTRL+N). FIXME: FOR NOW THIS IS A BUG IN MULTIVALUE DIALOGS
        # THAT CONTAIN LIST CONTROLS.

        # Combobox does not receive or interpret key or mouse events
        # on the popup.

        # See if there's a combobox specific command for the keypress
        logger.debug("=== COMBOBOX handle_key_event for event %s", kevent)
        command = find_command(kevent, command_table="combobox")
        if command is not None:
            logger.debug("=== COMBOBOX got command for event %s", command)
            return command.apply(self)

        # see if textentry wants to handle the event...
        command = find_command(kevent, command_table="textentry")
        if command is not None:
            prev_text = self._entry._text
            result = command.apply(self._entry)
            # update dropdown if there has been a change in the text
            if self._has_open_popup:
                text = self._entry._text
                if text != prev_text:
                    text = text.upper()
                    update_elts = [elt for elt in self._options \
                                   if text in elt.upper()]
                    self._option_list.update_elts(update_elts)
            self._entry.invalidate()
            return result

        # FIXME: this is probably not quite right if the list control
        # actually has the focus.
        if kevent.key_code >= 0:
            self._entry._insert_char_code(kevent.key_code)
            # use the value of the textentry to filter the elements in
            # the list control popup
            # fixme: really this filtering also needs to be done when
            # any change to the textentry occurs. IMPLEMENT
            # "VALUE-CHANGED" callback
            if self._has_open_popup:
                text = self._entry._text.upper()
                update_elts = [elt for elt in self._options \
                               if text in elt.upper()]
                self._option_list.update_elts(update_elts)
            return True
        return self._parent.handle_key_event(kevent)

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

    def open_popup(self):
        self._has_open_popup = True

    def close_list(self):
        self._has_open_popup = False
        self._option_list.frame().dialog_quit()

    def option_select_callback(self, from_value=None, to_value=None):
        self._entry.reset()
        self._entry._text = to_value
        self.owner().set_focus(self)

    #####                                                   FOCUS HANDLING #

    def accepts_focus(self):
        return True

    def is_focus(self):
        # fixme: this _has_open_popup thing feels like a hack
        return super().is_focus() or self._has_open_popup

    # "control" protocol
    def is_widget_focus(self, widget):
        # all children of the combobox should appear like they have
        # the focus if the combobox is the frame focus.
        return self.is_focus()

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
        (l, _, r, _) = self._region
        content = Sheet(width=r-l, height=5)
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

