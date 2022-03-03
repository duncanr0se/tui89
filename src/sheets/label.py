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

class Label(Sheet):
    """Line of text.

    Display a line of text. Text may be left, right, or center aligned
    in the region allocated to the Label.

    If the label is shrunk the text displayed will be truncated and
    elipses appended to indicate that part of the label is omitted.
    """
    def __init__(self,
                 label_text="",
                 default_pen=None,
                 pen=None,
                 align=None,
                 label_widget=None):
        super().__init__(default_pen=default_pen, pen=pen)
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

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "Label({}x{}@{},{}: '{}')".format(width, height, tx, ty,
                                                 self._label_text)

    def pen(self):
        if self._pen is None:
            self._pen = self.frame().theme("label")
        return self._pen

    def add_child(self):
        raise RuntimeError("children not allowed")

    def render(self):
        pen = self.pen()
        # fixme: paint background, decide where label should be if height>1
        display_text = self.truncate_text_to_width(self._label_text, self.width())
        coord = (self.line_offset(self._align, display_text, self.width()), 0)
        self.display_at(coord, display_text, pen)
        # overwrite accelerator (if present ofc) in accelerator colour scheme

        if self._label_widget is not None:
            accel_char = self.frame().accelerator_for_widget(self._label_widget)

            if accel_char is not None:
                accelerator_index = self._find_index_of_accelerator(display_text,
                                                                    accel_char)
                if accelerator_index >= 0:
                    accelerator_pen = self.frame().theme("selected_focus_control")
                    (x, _) = coord
                    self.display_at((x+accelerator_index, 0),
                                    accel_char, accelerator_pen)

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
