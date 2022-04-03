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

import pyperclip

from asciimatics.screen import Screen

from sheets.sheet import Sheet

from sheets.spacereq import SpaceReq, FILL
from geometry.points import Point
from frames.frame import Frame

from dcs.ink import Pen

from frames.commands import find_command
from mixins.valuemixin import ValueMixin

from logging import getLogger

logger = getLogger(__name__)

class TextEntry(Sheet, ValueMixin):
    """Text entry widget."""

    def __init__(self, text="", owner=None):
        super().__init__(owner=owner)
        self._children = []
        self._text = text
        # insertion point = where in the text the cursor is
        self._insertion_point = 0
        # text offset = where in the box the text is (relative to 0)
        self._text_offset = 0
        # tuple of (start, end) of current text selection or None if
        # no text is selected. This is a pair of offsets into the text
        # value. The selection range is a half open interval which
        # includes the start but excludes the end.
        self._text_selection = None

        # ValueMixin init
        self._value = None

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "TextEntry({}@{},{}: '{}')".format(self._region.region_width(),
                                                  tx, ty, self._text)

    def reset(self):
        self._text = ""
        self._text_offset = 0
        self._insertion_point = 0
        self.reset_selection()

    def reset_selection(self):
        self._text_selection=None

    def set_value(self, value):
        self.reset()
        super().set_value(value)
        # fixme: just use value directly and remove _text?
        self._text = value
        self.invalidate()

    def accepts_focus(self):
        return True

    def compose_space(self):
        # arbitrary: assume 20x1 edit field by default
        return SpaceReq(10, 20, FILL, 1, 1, FILL)

    def pen(self, role="undefined", state="default", pen="pen"):
        if role == "undefined":
            role = "editable"
        state = "focus" if self.is_focus() and state=="default" else state
        return super().pen(role=role, state=state, pen=pen)

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        display_text = self._text[self._text_offset:self._text_offset+self.width()]

        pen = self.pen(role="editable", state="default", pen="pen")

        # draw background
        bgpen = Pen(pen.bg(), pen.attr(), pen.bg())
        self.display_at(Point(0, 0), ' ' * self.width(), bgpen)

        # draw text
        if self._text_selection is not None:
            selected_pen = self.pen(role="editable", state="selected", pen="pen")
            selection_start=max(self._text_selection[0]-self._text_offset, 0)
            selection_end=max(min(self._text_selection[1]-self._text_offset,
                                  len(display_text)),
                              0)

            pre_selection=display_text[:selection_start]
            selected=display_text[selection_start:selection_end]
            post_selected=display_text[selection_end:]

            if pre_selection != "":
                self.display_at(Point(0, 0), pre_selection, pen)
            if selected != "":
                self.display_at(Point(selection_start, 0), selected, selected_pen)
            if post_selected != "":
                self.display_at(Point(selection_end, 0), post_selected, pen)
        else:
            self.display_at(Point(0, 0), display_text, pen)

        # draw cursor if focus
        if self.is_focus():
            visual_insertion_pt = self._insertion_point-self._text_offset
            # draw character under cursor or space for cursor using an
            # inverted pen
            cursor = self._text[self._insertion_point] \
                if self._insertion_point < len(self._text) \
                   else ' '
            cursor_pen = self.pen(role="editable", state="focus", pen="cursor")
            self.display_at(Point(visual_insertion_pt, 0), cursor, cursor_pen)

        # text entry boxes are leaf panes and don't have any children
        #for child in self._children:
        #    child.render()

    # events - top level sheets don't pass event on to a parent,
    # instead they return False to indicate the event is not handled
    # and expect the Frame to take any further necessary action
    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="textentry")
        if command is not None:
            result = command.apply(self)
            self.invalidate()
            return result

        # named keys have been dealt with already or are not handled
        if key_event.key_code < 0:
            return False

        self._insert_char_code(chr(key_event.key_code))
        return True

    def _insert_char_code(self, char):
        (start, end) = (self._insertion_point, self._insertion_point)

        if self._text_selection is not None:
            (start, end) = self._text_selection

        self._update_text_for_cut_or_paste(start, end, char)
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        self.invalidate()

    def activate(self):
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        self.frame().set_focus(self)

    # Keep cursor in visible region. self._insertion_point indicates
    # where in the text the cursor is placed. The display must always
    # show the cursor.
    def move_start(self):
        self._move_start_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_start_1(self):
        self._insertion_point = 0
        self._text_offset = 0

    def move_end(self):
        self._move_end_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_end_1(self):
        self._insertion_point = len(self._text)
        self._text_offset = max(len(self._text)-self.width()+1, 0)

    def move_forward(self):
        self._move_forward_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_forward_1(self):
        self._insertion_point = min(self._insertion_point+1, len(self._text))
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset += 1

    def move_forward_word(self):
        self._move_forward_word_1()
        self.reset_selection()
        return True

    def _move_forward_word_1(self):
        # skip whitespace before next word, if there is any.
        start = self.skip_start_ws()
        for index in range(start, len(self._text)):
            if not self._text[index].isalnum():
                # found the space
                self._insertion_point = index
                if self._insertion_point-self._text_offset >= self.width():
                    self._text_offset = self._insertion_point-self.width()+1
                return
        self._insertion_point = len(self._text)
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset = self._insertion_point-self.width()+1

    def skip_start_ws(self):
        index = self._insertion_point
        while index < len(self._text)-1 and not self._text[index].isalnum():
            index += 1
        return index

    def skip_end_ws(self):
        # move index back 1 so it points between words instead of
        # at the start of the word we want to move off (if
        # repeated "back word" commands are received)
        index = min(self._insertion_point-1, len(self._text)-1)
        while index > 0 and not self._text[index].isalnum():
                index -= 1
        return index

    def move_backward(self):
        self._move_backward_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_backward_1(self):
        self._insertion_point = max(self._insertion_point-1, 0)
        if self._insertion_point < self._text_offset:
            self._text_offset -= 1

    def move_backward_word(self):
        self._move_backward_word_1()
        self.reset_selection()
        return True

    def _move_backward_word_1(self):
        start = self.skip_end_ws()
        while self._text[start].isalnum() and start > 0:
            start -= 1
        # increment start since it points at a space instead of at the
        # start of the word. Note if the start of the text is hit the
        # start is set to 0 (it's unlikely that there is whitespace
        # before the first text in entry).
        self._insertion_point = start+1 if start > 0 else 0
        if self._insertion_point < self._text_offset:
            self._text_offset = self._insertion_point

    def delete(self):
        # delete text selection or character to right of insertion point
        if self._text_selection is not None:
            (start, end) = self._text_selection
            self._update_text_for_cut_or_paste(start, end, "")
        elif self._insertion_point < len(self._text):
            self._text = self._text[:self._insertion_point] \
                + self._text[self._insertion_point+1:]
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def backspace(self):
        # delete text selection or character to left of insertion point
        if self._text_selection is not None:
            (start, end) = self._text_selection
            self._update_text_for_cut_or_paste(start, end, "")
        elif self._insertion_point > 0:
            self._text = self._text[:self._insertion_point-1] + self._text[self._insertion_point:]
            self.move_backward()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def extend_selection_char_right(self):
        self._extend_selection_right(self._move_forward_1)

    def extend_selection_word_right(self):
        self._extend_selection_right(self._move_forward_word_1)

    def extend_selection_end_of_line(self):
        self._extend_selection_right(self._move_end_1)

    def _extend_selection_right(self, fun):
        oip = self._insertion_point
        (start, end) = (-1, -1)

        # Update insertion point to end of next word
        fun()

        if self._text_selection is None:
            start=oip
            end=self._insertion_point

        # Old insertion point is either at start or end of current
        # selection.

        elif oip == self._text_selection[0]:
            # old insertion point at start of selection, move start as
            # well as end (if insertion pt > end)
            start=min(self._insertion_point, self._text_selection[1])
            end=max(self._insertion_point, self._text_selection[1])

        else:
            # old insertion point at end of selection; just update
            # end.
            start=self._text_selection[0]
            end=self._insertion_point

        self._text_selection=(start, end)

    def extend_selection_char_left(self):
        self._extend_selection_left(self._move_backward_1)

    def extend_selection_word_left(self):
        self._extend_selection_left(self._move_backward_word_1)

    def extend_selection_start_of_line(self):
        self._extend_selection_left(self._move_start_1)

    def _extend_selection_left(self, fun):
        oip = self._insertion_point
        (start, end) = (-1, -1)

        fun()

        if self._text_selection is None:
            # If no existing selection, selection goes from old
            # insertion point to updated insertion point.
            start=self._insertion_point
            end=oip

        elif oip == self._text_selection[1]:
            # If old insertion point was at max end of existing
            # selection, we're moving the end of the selection to the
            # left.
            start=min(self._insertion_point, self._text_selection[0])
            end=max(self._insertion_point, self._text_selection[0])

        else:
            # Old insertion point was at min end of existing
            # selection, just set start to new insertion point and
            # leave end as it is.
            start=self._insertion_point
            end=self._text_selection[1]

        self._text_selection=(start, end)

    def clipboard_copy_to(self):
        # put text covered by selection on the system clipboard
        if self._text_selection is not None:
            (start, end) = self._text_selection
            text = self._text[start:end]
            pyperclip.copy(text)
            self.reset_selection()
            return True
        return False

    def clipboard_cut_to(self):
        # put the text covered by the current selection on the system
        # clipboard and remove the text from the entry
        if self._text_selection is not None:
            (start, end) = self._text_selection
            text = self._text[start:end]
            pyperclip.copy(text)

            self._update_text_for_cut_or_paste(start, end, "")
            self.reset_selection()
            return True
        return False

    def clipboard_paste_from(self):
        # replace text covered by selection with the contents of the
        # system clipboard. If there is no selection just insert the
        # text at the insertion point.
        text=pyperclip.paste()

        if text == "":
            return False

        (start, end) = (self._insertion_point, self._insertion_point)

        if self._text_selection is not None:
            (start, end) = self._text_selection

        self._update_text_for_cut_or_paste(start, end, text)
        self.reset_selection()
        return True

    def _update_text_for_cut_or_paste(self, start, end, text):
        pre=self._text[:start]
        post=self._text[end:]
        self._text=pre+text+post
        # insertion point needs to be at the end of "text" and
        # on-screen
        self._insertion_point=start+len(text)
        if self._insertion_point >= self.width():
            self._text_offset=self._insertion_point-self.width()+1
        # if deleting a selection the insertion point can end up off
        # screen at a -ve offset. Make sure the insertion point is
        # always visible.
        if self._insertion_point < self._text_offset:
            self._text_offset=self._insertion_point
