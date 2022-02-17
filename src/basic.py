from asciimatics.screen import Screen

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.frame import Frame
from sheets.sheet import Sheet
from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.buttons import Button
from sheets.buttons import RadioButton
from sheets.buttons import CheckBox
from sheets.boxlayout import HorizontalLayout
from sheets.boxlayout import VerticalLayout
from sheets.dialog import Dialog

# add more widgets
#   - layouts
#       - row (tick)
#       - column (tick)
#       - grid?
#       - stack?
#   - buttons (tick)
#       - radio buttons (tick)
#       - check boxes (tick)
#       - menu button
#   - button group?
#   - labels
#   - scroll bars
#   - scroller - can border be used for this?
#   - menu bar
#   - menu
#   - status bar
#   - dialog box
#   - text entry
#   - text box
#   - horizontal / vertical separators
#   - padding
#   - list
#   - tree

# Widget sizes: should be large enough to exactly contain
# content. Think the sizes for border panes are too big by 1
# unit. Need to investigate how curses / asciimatic measures the
# terminal dimensions. Is the last column inclusive, or exclusive?

# PRIORITIES:
#
# 1. Event handling - decide how to do this, do we want something
# declarative and semantically high-level for defining event handlers
# (like DUIM) or is something basic sufficient? Basic for now.  - send
# event to topmost sheet where event occurred / send keyboard events
# to current focus.
#
# 1.5. Dialogs; need some way to provide feedback without having
# to throw exceptions everywhere... keep them basic, just a new
# sheet type.
#
# 2. Once event handling is in place, need to experiment with
# scrolling / overflowing a screen buffer with content / clipping
# etc. and work out how scrolling is actually going to work in tandem
# with asciimetrics handling of the screen / buffers.
#
# 3. Then implement scroll bars / scrolling. Make all border panes
# handle scrolling transparently.
#
# 4. Then - more widgets, event handling, focus, input, tab order.
#      - how about having a widget that shows the event stream?
#
# 5. Menus / command tables / status bars

# When a button is created, it should be possible to add an
# accelerator key to some global / command map and handle that
# accelerator at the frame level.

# tidying

# add frame() method to sheet

# create "pen" to capture colour, attr, bg instead of passing them
# around everywhere. Current (fg, attr, bg) approach doesn't work well
# when dealing with different widgets - adding a border frame to a
# dialog for example doesn't use the dialog bg colour, rather the bg
# colour is overridden by the frame drawing code. Not good!

# need to do something about events! - see draw_next_frame() in
# screen.py

# make existing stuff prettier / more correct (alignment of text in
# buttons, themes, colours, attributes, etc.)

# and we need command tables or some other way to tie keys
# and ui to commands.

# specialise "region_contains_position" for decorated buttons and
# other decorated widgets... not sure quite how to do that so that
# border can be ignored for mouse click location but included for
# other "does this point inhabit the widget space" queries...

# drawing is a separate thing altogether...

# capture drawing ops when done by sheets and convert into changes on
# the screen only once per event loop? Have top level sheet mediate
# between drawn ops in the tui + actual screen manipulations in
# asciimatics? Problem we need to avoid is that asciimatics model
# might make scrolling really hard to implement. Let's wait and see
# what happens when we get around to it.

# more flexibility for borders; DOUBLE, SINGLE, SPACE, NONE... could
# also combine into a spacing pane.

# look at other stuff asciimatics does (save / restore form state
# etc.) and decide if that's something that could be useful.Pretty
# sure it isn't...
def demo(screen):
    frame = Frame(screen)
    top_level_sheet = TopLevelSheet(frame)

    border_layout = BorderLayout(title="Basic")
    top_level_sheet.add_child(border_layout)

#    child_sheet = Sheet()
#    child_sheet = CheckBox(label="PRESS ME!")
#    child_sheet = VerticalLayout([1, 2, 1, 1])
    child_sheet = HorizontalLayout([1, 2, 1, 1])
    border_layout.add_child(child_sheet)

    child_sheet.add_child(BorderLayout(title="one"))
    inner_bl = BorderLayout(title="two")
    child_sheet.add_child(inner_bl)
    child_sheet.add_child(BorderLayout(title="three"))
    child_sheet.add_child(BorderLayout(title="four"))

#    button = Button(label="Press me!", decorated=True)
#    button = RadioButton(label="Press me!", decorated=False)
    button = CheckBox(label="Press me!")

    def btn_cb():
        raise RuntimeError("** BIG BOOM! **")

    button.on_click = btn_cb
    inner_bl.add_child(button)

    frame.lay_out_frame()

#    child_sheet.print_at('Hello, world!', (0, 0))
#    child_sheet.print_at('{}x{}'.format(str(screen.width), str(screen.height)), (0, 1))
#    child_sheet.print_at('{}'.format(child_sheet), (0, 2))
#    child_sheet.print_at('and now for something completely different; a longish string!', (156, 10))

    # render() or refresh()? refresh() should be called each time
    # around the event loop...
    # currently render() method on top sheet calls refresh() but that
    # won't wash now that Frame is introduced.
    frame.render()

    # when the dialog is shown - the main window doesn't handle mouse
    # events properly. This is expected dialog behaviour except that
    # behaviour hasn't been written yet!
    dialog = Dialog(frame, title="dialog!")
    # sets dialog up, but doesn't draw it. That happens in
    # render(). Perhaps the dialog layout sould happen in
    # lay_out_frame()? Maybe it's independent.
    frame.show_dialog(dialog)

    # Should the frame manage a menu and status bar (unless I decide
    # to manage that stuff manually). Need to decide when to call
    # refresh() / redraw() in that case... but then need to decide how
    # to deal with the events. And focus. And input. Etc., etc.

    # The frame needs to be sure to direct events to the dialog, if there
    # is one, in preference to any other sheet (conceptually the dialog
    # is always highest in z-order)
    frame.start_frame()


Screen.wrapper(demo, unicode_aware=True)
