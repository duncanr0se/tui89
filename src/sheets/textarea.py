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
        # _text_selection = region of area selected
        self._text_selection = None

    def __repr__(self):
        tx = self._transform._dx
        ty = self._transform._dy
        return "TextArea({}x{}@{},{})".format(self._region.region_width(),
                                              self._region.region_height(),
                                              tx, ty)

    def reset_selection(self):
        self._text_selection=None

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
            if self._text_selection is not None:
                if self._text_selection.ltrb()[1] <= line < self._text_selection.ltrb()[3]:
                    selected_pen = self.pen(role="editable", state="selected", pen="area_pen")
                    selection_start = max(self._text_selection.ltrb()[0]-self._text_offset, 0)
                    selection_end = max(min(self._text_selection.ltrb()[2]-self._text_offset,
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
        line = self._lines[self._insertion_line]
        self._insertion_point = len(line)
        self._text_offset = max(len(line)-self.width()+1, 0)

    def move_forward(self):
        self._move_forward_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_forward_1(self):
        line = self._lines[self._insertion_line]
        self._insertion_point = min(self._insertion_point+1, len(line))
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset += 1

    def move_backward(self):
        self._move_backward_1()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def _move_backward_1(self):
        self._insertion_point = max(self._insertion_point-1, 0)
        if self._insertion_point < self._text_offset:
            self._text_offset -= 1

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
        line = self._lines[self._insertion_line]
        if self._insertion_point < len(line):
            line = line[:self._insertion_point] + line[self._insertion_point+1:]
            self._lines[self._insertion_line] = line
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def backspace(self):
        line = self._lines[self._insertion_line]
        if self._insertion_point > 0:
            line = line[:self._insertion_point-1] + line[self._insertion_point:]
            self._lines[self._insertion_line] = line
            self.move_backward()
        self.reset_selection()  # fixme: move to a more generic call site to avoid duplication
        return True

    def extend_selection_char_left(self):
        # selection here is a 2d region
        logger.debug("insertion line=%s", self._insertion_line)
        self._insertion_point = min(self._insertion_point,
                                    len(self._lines[self._insertion_line]))
        left = self._insertion_point
        top = self._insertion_line
        right = self._insertion_point
        bottom = self._insertion_line+1

        if self._text_selection is None:
            # If no existing selection, selection start is current
            # pos-1 and selection end is current pos
            left=max(left-1, 0)
        elif self._text_selection.ltrb()[0] < self._insertion_point:
            # if we've selected right and now we're selecting left,
            # need to reduce the end and leave the start
            left=self._text_selection.ltrb()[0]
            top=self._text_selection.ltrb()[1]
            right=right-1
            bottom=self._text_selection.ltrb()[3]
        else:
            # otherwise reduce the start by 1 and leave the end
            left=max(left-1, 0)
            top=self._text_selection.ltrb()[1]
            right=self._text_selection.ltrb()[2]
            bottom=self._text_selection.ltrb()[3]

        self._text_selection=Region(left, top, right, bottom)
        logger.debug("selection extended; current selection is %s", self._text_selection)
        return self._move_backward_1()

    def extend_selection_char_right(self):
        logger.debug("insertion line=%s", self._insertion_line)
        self._insertion_point = min(self._insertion_point,
                                    len(self._lines[self._insertion_line]))
        left = self._insertion_point
        top = self._insertion_line
        right = self._insertion_point
        bottom = self._insertion_line+1

        if self._text_selection is None:
            # If no existing selection, selection start is current pos
            # and selection end is current pos+1
            right = min(right+1, len(self._lines[self._insertion_line]))
        elif self._text_selection.ltrb()[1] > self._insertion_point:
            # if we've selected left and now we're selecting right,
            # need to increase the start and leave the end
            left=left+1
            top=self._text_selection.ltrb()[1]
            right=self._text_selection.ltrb()[2]
            bottom=self._text_selection.ltrb()[3]
        else:
            # otherwise leave the start and increase the end by 1
            left=self._text_selection.ltrb()[0]
            top=self._text_selection.ltrb()[1]
            right=min(right+1, len(self._lines[self._insertion_line]))
            bottom=self._text_selection.ltrb()[3]

        self._text_selection=Region(left, top, right, bottom)
        logger.debug("selection extended; current selection is %s", self._text_selection)
        return self._move_forward_1()
