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

from asciimatics.screen import Screen

from sheets.sheet import Sheet

from sheets.spacereq import SpaceReq, FILL

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.boxlayout import VerticalLayout, HorizontalLayout
from sheets.buttons import Button
from frames.frame import Frame
from sheets.separators import HorizontalSeparator

from dcs.ink import Pen

from frames.commands import find_command
from sheets.textentry import TextEntry

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

    def __repr__(self):
        (left, _, right, _) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "TextArea({}@{},{})".format(right-left, tx, ty)

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
            self.display_at((0, line-self._text_line), display_text, pen)

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
            self.display_at((insertion_pt_x, insertion_pt_y), cursor, cursor_pen)

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

    # _insertion_point min needs always be in visible window;
    # attempting to move left out of visible region scrolls text
    # right; attempting to move right out of visible region scrolls
    # text left.
    #
    # Move start moves start of text to start of visible region, and
    # move end moves end of text to end of visible region.
    #
    # Keep cursor in visible region. self._insertion_point indicates
    # where in the text the cursor is placed. The display must always
    # show the cursor.
    def move_start(self):
        self._insertion_point = 0
        self._text_offset = 0
        return True

    def move_end(self):
        line = self._lines[self._insertion_line]
        self._insertion_point = len(line)
        self._text_offset = max(len(line)-self.width()+1, 0)
        return True

    def move_forward(self):
        line = self._lines[self._insertion_line]
        self._insertion_point = min(self._insertion_point+1, len(line))
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset += 1
        return True

    def move_backward(self):
        self._insertion_point = max(self._insertion_point-1, 0)
        if self._insertion_point < self._text_offset:
            self._text_offset -= 1
        return True

    def move_up(self):
        # vertical movement does not affect the insertion point
        self._insertion_line = max(self._insertion_line-1, 0)
        if self._insertion_line < self._text_line:
            self._text_line -= 1
        return True

    def page_up(self):
        # vertical movement does not affect the insertion point;
        # Cursor ends up at top of screen
        page_size = self.height()-1
        self._insertion_line = max(self._insertion_line-page_size, 0)
        if self._insertion_line < self._text_line:
            self._text_line = self._insertion_line
        return True

    def move_down(self):
        # vertical movement does not affect the insertion point
        self._insertion_line = min(self._insertion_line+1, len(self._lines)-1)
        if self._insertion_line-self._text_line >= self.height():
            self._text_line += 1
        return True

    def page_down(self):
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
        return True

    def delete(self):
        line = self._lines[self._insertion_line]
        if self._insertion_point < len(line):
            line = line[:self._insertion_point] + line[self._insertion_point+1:]
            self._lines[self._insertion_line] = line
        return True

    def backspace(self):
        line = self._lines[self._insertion_line]
        if self._insertion_point > 0:
            line = line[:self._insertion_point-1] + line[self._insertion_point:]
            self._lines[self._insertion_line] = line
            self.move_backward()
        return True
