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

from sheets.spacereq import SpaceReq, FILL, combine_spacereqs

from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.boxlayout import VerticalLayout, HorizontalLayout
from sheets.buttons import Button
from frames.frame import Frame
from sheets.separators import HorizontalSeparator

from dcs.ink import Pen

from frames.commands import find_command

class TextEntry(Sheet):
    """Text entry widget."""

    def __init__(self, text="", default_pen=None, pen=None):
        super().__init__(default_pen=default_pen, pen=pen)
        self._children = []
#        border = BorderLayout(title=title)
#        self.add_child(border)
        self._text = text
        self._default_pen = default_pen
        self._pen = pen
        self._focus = None
        self._cursor_pen = None
        # insertion point = where in the text the cursor is
        self._insertion_point = 0
        # text offset = where in the box the text is (relative to 0)
        self._text_offset = 0

    def __repr__(self):
        (width, height) = self._region
        tx = self._transform._dx
        ty = self._transform._dy
        return "TextEntry({}@{},{}: '{}')".format(width, tx, ty, self._text)

    def pen(self):
        if self.is_focus():
            self._pen = self.frame().theme("focus_edit_text")
        else:
            self._pen = self.frame().theme("edit_text")
        return self._pen

    def cursor_pen(self):
        if self._cursor_pen is None:
            current_pen = self.pen()
            self._cursor_pen = Pen(current_pen.fg(), Screen.A_REVERSE, current_pen.bg())
        #return self.frame().theme("focus_edit_text")
        return self._cursor_pen

    def accepts_focus(self):
        return True

    def is_focus(self):
        return self.frame()._focus == self

    def compose_space(self):
        # arbitrary: assume 20x1 edit field by default
        return SpaceReq(10, 20, FILL, 1, 1, FILL)

    def render(self):
        if not self._region:
            raise RuntimeError("render invoked before space allocation")

        display_text = self._text[self._text_offset:self._text_offset+self.width()]

        pen = self.pen()

        # draw background
        bgpen = Pen(pen.bg(), pen.attr(), pen.bg())
        self.display_at((0, 0), ' ' * self.width(), bgpen)

        # draw text
        self.display_at((0, 0), display_text, pen)

        # draw cursor if focus
        if self.is_focus():
            visual_insertion_pt = self._insertion_point-self._text_offset
            # draw character under cursor or space for cursor using an
            # inverted pen
            cursor = self._text[self._insertion_point] \
                if self._insertion_point < len(self._text) \
                   else ' '
            self.display_at((visual_insertion_pt, 0), cursor, self.cursor_pen())

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

        pos = self._insertion_point
        self._text = self._text[:pos] + chr(key_event.key_code) + self._text[pos:]
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
        self._insertion_point = len(self._text)
        self._text_offset = max(len(self._text)-self.width()+1, 0)
        return True

    def move_forward(self):
        self._insertion_point = min(self._insertion_point+1, len(self._text))
        if self._insertion_point-self._text_offset >= self.width():
            self._text_offset += 1
        return True

    def move_backward(self):
        self._insertion_point = max(self._insertion_point-1, 0)
        if self._insertion_point < self._text_offset:
            self._text_offset -= 1
        return True

    def delete(self):
        if self._insertion_point < len(self._text):
            self._text = self._text[:self._insertion_point] + self._text[self._insertion_point+1:]
        return True

    def backspace(self):
        if self._insertion_point > 0:
            self._text = self._text[:self._insertion_point-1] + self._text[self._insertion_point:]
            self.move_backward()
        return True
