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
from geometry.regions import Region

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.boxlayout import VerticalLayout, HorizontalLayout
from sheets.buttons import Button
from frames.frame import Frame
from sheets.separators import HorizontalSeparator

from dcs.ink import Pen

from frames.commands import find_command
from sheets.textentry import TextEntry

from logging import getLogger

logger = getLogger(__name__)

# This is a TextEntry subtype
class TextArea(TextEntry):
    """Text area widget."""

    def __init__(self, text=[], lines=10):
        super().__init__()
        self._children = []
#        border = BorderLayout(title=title)
#        self.add_child(border)
        # lines are a ordered list of lines
        self._lines = text
        if len(self._lines) == 0:
            self._lines.append("")
        # How many lines to display in the text area
        self._visible_lines = lines
        # insertion point = where in the text the cursor is
        self._insertion_point = 0
        # insertion point = which line in the text contains the cursor
        self._insertion_line = 0
        # text offset = where on the x-axis the text is (relative to 0)
        self._text_offset = 0
        # text_line = which line of text the cursor is on (relative to 0)
        self._text_line = 0
        # _horizontal_text_selection = (left, right) of area selected
        self._text_selection = None
        # _vertical_text_selection = (top, bottom) of area selected
        self._vertical_text_selection = None

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "TextArea({}x{}@{},{})".format(self._region.region_width(),
                                              self._region.region_height(),
                                              tx, ty)

    def reset_selection(self):
        self._text_selection=None
        self._vertical_text_selection=None

    def compose_space(self):
        # arbitrary: assume 20xlines edit field by default
        return SpaceReq(10, 20, FILL, 1, self._visible_lines, FILL)

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        pen = self.pen(role="editable", state="default", pen="area_pen")

        # draw background
        self.clear(self._region)

        # draw text
        #
        # Need 2 values; _text_offset is where the text is positioned
        # in the x axis, and _text_line indicates where it is
        # positioned in the y axis.
        #
        #         +---------------+
        #  |Here is some text.    |
        #  |Another line of text but this is longer
        #         |^             ^|
        #  |<    >| `disply text' |
        # text offset             |
        #         |<  self.width >|
        #
        # _insertion_line = index into self._lines of the line
        # containing the cursor
        #
        # _insertion_point = index into line where cursor is
        # positioned
        #
        # _text_offset = start of visible portion of line
        #
        # _text_line = index into self._lines of the line that is
        # displayed first in the text area, i.e., the line at the top
        # of the text area visual.
        #
        # Do this calculation for each line
        for line in range(self._text_line, self._text_line + self.height()):
            if line >= len(self._lines):
                break
            display_text = self._lines[line]
            display_text = display_text[self._text_offset:self._text_offset+self.width()]

            # if line is in selected region, draw any selected text in
            # the selection colour instead of in the default colour.
            if self._vertical_text_selection is not None:
                (top, bottom) = self._vertical_text_selection
                if top <= line < bottom:
                    selected_pen = self.pen(role="editable", state="selected", pen="area_pen")
                    selection_start = max(self._text_selection[0]-self._text_offset, 0)
                    selection_end = max(min(self._text_selection[1]-self._text_offset,
                                            len(display_text)),
                                        0)

                    pre_selection=display_text[:selection_start]
                    selected=display_text[selection_start:selection_end]
                    post_selected=display_text[selection_end:]

                    if pre_selection != "":
                        self.display_at(Point(0, line-self._text_line), pre_selection, pen)
                    if selected != "":
                        self.display_at(Point(selection_start, line-self._text_line),
                                        selected, selected_pen)
                    if post_selected != "":
                        self.display_at(Point(selection_end, line-self._text_line),
                                        post_selected, pen)
                else:
                    self.display_at(Point(0, line-self._text_line), display_text, pen)
            else:
                self.display_at(Point(0, line-self._text_line), display_text, pen)

        # draw cursor if focus
        if self.is_focus():
            line = self._lines[self._insertion_line]
            # adjust x cursor point if insertion_point>line length;
            # cursor is drawn at end of line, but don't adjust
            # insertion point in case continue navigating up/down.
            cursor_pos = min(self._insertion_point, len(line))
            insertion_pt_x = cursor_pos-self._text_offset
            insertion_pt_y = self._insertion_line-self._text_line
            # draw character under cursor or space for cursor using an
            # inverted pen
            cursor = line[cursor_pos] \
                if cursor_pos < len(line) \
                   else ' '
            cursor_pen = self.pen(role="editable", state="focus", pen="cursor")
            self.display_at(Point(insertion_pt_x, insertion_pt_y), cursor, cursor_pen)

    # events - top level sheets don't pass event on to a parent,
    # instead they return False to indicate the event is not handled
    # and expect the Frame to take any further necessary action
    def handle_key_event(self, key_event):
        command = find_command(key_event, command_table="textarea")
        if command is not None:
            result = command.apply(self)
            self.invalidate()
            return result

        # named keys have been dealt with already or are not handled
        if key_event.key_code < 0:
            return False

        # FIXME: add commands to support usual editing operations:
        #
        # SHIFT+KEY_RIGHT=402
        # SHIFT+KEY_UP=337
        # SHIFT+KEY_LEFT=393
        # SHIFT+KEY_DOWN=336
        # CTRL+KEY_LEFT (back word)
        # CTRL+KEY_RIGHT (forward word)
        # CTRL+KEY_UP (up paragraph)
        # CTRL+KEY_DOWN (down paragraph)

        line = self._lines[self._insertion_line]
        # adjust pos if insertion point > line length. This happens
        # from up/down motion to lines shorter than the original line
        pos = min(self._insertion_point, len(line))
        line = line[:pos] + chr(key_event.key_code) + line[pos:]
        self._lines[self._insertion_line] = line
        self.move_forward()
        self.invalidate()
        return True

    def activate(self):
        self.frame().set_focus(self)

    # def move_start(self): -- USE PARENT IMPLEMENTATION
    # def _move_start_1(self):
    # def move_end(self):

    # fixme: could super method if there was a current line accessor
    def _move_end_1(self):
        line = self._lines[self._insertion_line]
        self._insertion_point = len(line)
        self._text_offset = max(len(line)-self.width()+1, 0)

    # def move_forward(self):

    # fixme: could super method if there was a current line accessor
    def _move_forward_1(self):
        line = self._lines[self._insertion_line]
        self._insertion_point = min(self._insertion_point+1, len(line))
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset += 1

    def _move_forward_word_1(self):
        start = self.skip_start_ws()
        text = self._lines[self._insertion_line]
        for index in range(start, len(text)):
            if not text[index].isalnum():
                # found the space
                self._insertion_point = index
                if self._insertion_point-self._text_offset >= self.width():
                    self._text_offset = self._insertion_point-self.width()+1
                return
        self._insertion_point = len(text)
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset = self._insertion_point-self.width()+1

    def skip_start_ws(self):
        text = self._lines[self._insertion_line]
        index = self._insertion_point
        while index < len(text)-1 and not text[index].isalnum():
            index += 1
        return index

    def skip_end_ws(self):
        # move index back 1 so it points between words instead of
        # at the start of the word we want to move off (if
        # repeated "back word" commands are received)
        text = self._lines[self._insertion_line]
        index = min(self._insertion_point-1, len(text)-1)
        while index > 0 and not text[index].isalnum():
            index -= 1
        return index

    # def move_backward(self):
    # def _move_backward_1(self):

    # fixme: move backward word

    # fixme: could super method if there was a current line accessor
    def _move_backward_word_1(self):
        text = self._lines[self._insertion_line]
        start = self.skip_end_ws()
        while text[start].isalnum() and start > 0:
            start -= 1
        # increment start since it points at a space instead of at the
        # start of the word. Note if the start of the text is hit the
        # start is set to 0 (it's unlikely that there is whitespace
        # before the first text in entry).
        self._insertion_point = start+1 if start > 0 else 0
        if self._insertion_point < self._text_offset:
            self._text_offset = self._insertion_point

    def move_up(self):
        # vertical movement does not affect the insertion point
        self._move_up_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_up_1(self):
        # vertical movement does not affect the insertion point
        self._insertion_line = max(self._insertion_line-1, 0)
        if self._insertion_line < self._text_line:
            self._text_line -= 1

    def page_up(self):
        # vertical movement does not affect the insertion point;
        # Cursor ends up at top of screen
        self._page_up_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _page_up_1(self):
        # vertical movement does not affect the insertion point;
        # Cursor ends up at top of screen
        page_size = self.height()-1
        self._insertion_line = max(self._insertion_line-page_size, 0)
        if self._insertion_line < self._text_line:
            self._text_line = self._insertion_line

    def move_down(self):
        # vertical movement does not affect the insertion point
        self._move_down_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_down_1(self):
        # vertical movement does not affect the insertion point
        self._insertion_line = min(self._insertion_line+1, len(self._lines)-1)
        if self._insertion_line-self._text_line >= self.height():
            self._text_line += 1

    def page_down(self):
        # vertical movement does not affect the insertion point;
        # Cursor ends up at bottom of screen
        self._page_down_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _page_down_1(self):
        # vertical movement does not affect the insertion point;
        # Cursor ends up at bottom of screen
        page_size = self.height()-1
        self._insertion_line = min(self._insertion_line+page_size, len(self._lines)-1)
        if self._insertion_line-self._text_line >= self.height():
            self._text_line = self._insertion_line-page_size
        return True

    def open_below(self):
        self._lines.insert(self._insertion_line+1, "")
        self.move_down()
        self.move_start()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def delete(self):
        # delete text selection or character to right of insertion point
        text = self._lines[self._insertion_line]
        if self._text_selection is not None:
            (start, end) = self._text_selection
            self._update_text_for_cut_or_paste(start, end, "")
        if self._insertion_point < len(text):
            text = text[:self._insertion_point] + text[self._insertion_point+1:]
            self._lines[self._insertion_line] = text
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def backspace(self):
        # delete text selection or character to left of insertion point
        text = self._lines[self._insertion_line]
        if self._text_selection is not None:
            (start, end) = self._text_selection
            self._update_text_for_cut_or_paste(start, end, "")
        if self._insertion_point > 0:
            text = text[:self._insertion_point-1] + text[self._insertion_point:]
            self._lines[self._insertion_line] = text
            self.move_backward()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    # fixme: have 2 selections, a left-right selection that is
    # identical to the one already implemented for textentry, and a
    # top-bottom selection that is distict to the textarea.

    # def extend_selection_char_right(self):
    # def extend_selection_word_right(self):
    # def extend_selection_end_of_line(self):

    def _extend_selection_right(self, fun):
        super()._extend_selection_right(fun)
        if self._vertical_text_selection is None:
            self._vertical_text_selection = (self._insertion_line,
                                             self._insertion_line+1)
        else:
            (top, bottom) = self._vertical_text_selection
            if self._insertion_line < top:
                top = self._insertion_line
            if self._insertion_line >= bottom:
                bottom = self._insertion_line+1
            self._vertical_text_selection=(top, bottom)

    # def extend_selection_char_left(self):
    # def extend_selection_word_left(self):
    # def extend_selection_start_of_line(self):

    def _extend_selection_left(self, fun):
        super()._extend_selection_left(fun)
        if self._vertical_text_selection is None:
            self._vertical_text_selection = (self._insertion_line,
                                             self._insertion_line+1)
        else:
            (top, bottom) = self._vertical_text_selection
            if self._insertion_line < top:
                top = self._insertion_line
            if self._insertion_line >= bottom:
                bottom = self._insertion_line+1
            self._vertical_text_selection=(top, bottom)

    # fixme: could just use super's implementations if could access
    # current line's text
    def clipboard_copy_to(self):
        # put text covered by selection on the system clipboard
        if self._text_selection is not None:
            (start, end) = self._text_selection
            text = self._lines[self._insertion_line][start:end]
            pyperclip.copy(text)
            self.reset_selection()
            return True
        return False

    def clipboard_cut_to(self):
        # put the text covered by the current selection on the system
        # clipboard and remove the text from the entry
        if self._text_selection is not None:
            (start, end) = self._text_selection
            text = self._lines[self._insertion_line][start:end]
            pyperclip.copy(text)

            self._update_text_for_cut_or_paste(start, end, "")
            self.reset_selection()
            return True
        return False

    # fixme: what about cutting out a rectangle? this method needs to
    # be way cleverer...
    def _update_text_for_cut_or_paste(self, start, end, text):
        _text = self._lines[self._insertion_line]
        pre=_text[:start]
        post=_text[end:]
        self._lines[self._insertion_line]=pre+text+post
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
