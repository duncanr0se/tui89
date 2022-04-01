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
from geometry.points import Point
from sheets.sheet import Sheet
from sheets.spacereq import SpaceReq, FILL
from dcs.ink import Pen
from mixins.valuemixin import ValueMixin
from frames.commands import find_command

from logging import getLogger

logger = getLogger(__name__)

class Label(Sheet):
    """Line of text.

    Display a line of text. Text may be left, right, or center aligned
    in the region allocated to the Label.

    If the label is shrunk the text displayed will be truncated and
    elipses appended to indicate that part of the label is omitted.
    """
    def __init__(self,
                 label_text="",
                 align=None,
                 valign=None,
                 label_widget=None,
                 owner=None):
        super().__init__(owner=owner)
        self._accelerator_char = None
        self._label_text = label_text
        valid_aligns = { None, "left", "right", "center", "centre" }
        if align not in valid_aligns:
            raise RuntimeError("label align not in valid set", align, valid_aligns)
        self._align = align
        # if a label is associated with a widget then an accelerator
        # will be generated in the frame's accelerator table and when
        # the accelerator is used the associated widget's "activate"
        # method is invoked. For buttons this will do the same thing
        # as a button click, for text entry widgets it sets the focus
        # in the widget.
        self._label_widget = label_widget
        self._valign = valign

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "Label({}x{}@{},{}: '{}')".format(self._region.region_width(),
                                                 self._region.region_height(),
                                                 tx, ty,
                                                 self._label_text)

    def add_child(self):
        raise RuntimeError("children not allowed")

    def render(self):
        state = "default"
        if self._label_widget is not None:
            if self._label_widget.is_focus():
                state="focus"
        pen = self.pen(role="label", state=state, pen="pen")
        # fixme: decide where label should be if height>1
        self._draw_background(pen)
        display_text = self.truncate_text_to_width(self._label_text, self.width())
        coord = Point(self._x_align_offset(display_text), self._y_align_offset())
        self.display_at(coord, display_text, pen)
        # overwrite accelerator (if present ofc) in accelerator colour scheme
        if self._label_widget is not None:
            accel_char = self.frame().accelerator_for_widget(self._label_widget)

            if accel_char is not None:
                accelerator_index = self._find_index_of_accelerator(display_text,
                                                                    accel_char)
                if accelerator_index >= 0:
                    accelerator_pen = self.pen(role="label", state="default", pen="accelerator")
                    (x, y) = coord.xy()
                    self.display_at(Point(x+accelerator_index, y),
                                    accel_char, accelerator_pen)

    def _x_align_offset(self, text):
        return self.line_offset(self._align, text, self.width())

    def _y_align_offset(self):
        # assumes labels are all single line
        if self._valign == "top" or self._valign is None:
            return 0
        if self._valign in {"center", "centre"}:
            return max((self.height()-1) // 2, 0)
        else:
            return max(self.height()-1, 0)

    def _draw_background(self, pen):
        self.clear(self._region, pen)

    def _find_index_of_accelerator(self, display_text, accel_char):
        return display_text.find(accel_char)

    def truncate_text_to_width(self, display_text, width):
        """Truncate text to fit widget.

        Truncate so it's possible to see at least 3+ label chars +
        "...". If text has 6 or fewer characters and doesn't fit in
        the available space, then that's just tough. Text will be
        clipped.
        """
        if len(display_text)>width and len(display_text)>6:
            display_text = display_text[:width-3]
            display_text += "..."
        return display_text

    def line_offset(self, align, text, width):
        """Calculate offset of text for given alignment.

        Alignment must be one of:
           + "left",
           + "right",
           + {"center", "center"}
        """
        if align is None or align == "left":
            return 0
        elif align == "right":
            return width-len(text)
        else:
            # align == "center" or "centre"
            return (width-len(text)) // 2

    def compose_space(self):
        # Prefer enough room for the label. Can take as much room as offered.
        # Won't shrink below 3 chars from label + "..." (= 6 chars)
        label_min = min(len(self._label_text), 6)
        return SpaceReq(label_min, len(self._label_text), FILL, 1, 1, FILL)

    # Buttons have labels; when accelerator on label is clicked the
    # associated widget is activated. This happens automatically if
    # the label is associated with the button via the label's
    # "label_widget" initarg.

    # This functionality is supported for all widgets that are
    # associated with a label and that implement an "activate" method.

    def detach(self):
        if self._label_widget is not None:
            self.frame().discard_accelerator(self._label_widget)
        super().detach()

    def attach(self):
        super().attach()
        if self._label_widget is not None:
            self.frame().register_accelerator(self._label_text, self._label_widget)


class ValueLabel(Label, ValueMixin):
    # label that accepts focus and has a value (= the label's text)
    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "ValueLabel({}x{}@{},{}: '{}')".format(self._region.region_width(),
                                                      self._region.region_height(),
                                                      tx, ty,
                                                      self._label_text)

    def value(self):
        return self._label_text

    def accepts_focus(self):
        return True

    def pen(self, role="undefined", state="default", pen="pen"):
        role="label" if role=="undefined" else role
        state = "focus" if self.is_focus() else state
        return super().pen(role=role, state=state, pen=pen)

    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="valuelabel")
        if command is not None:
            return command.apply(self)
        return False

    # FIXME: should be "activatable label"? "ActiveValueLabel"?
    def activate(self):
        if hasattr(self, "on_activate"):
            self.on_activate(self)
