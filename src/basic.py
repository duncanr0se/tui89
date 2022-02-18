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
#       - border (✔)
#       - row (✔)
#       - column (✔)
#       - grid?
#       - stack?
#   - buttons (✔)
#       - radio buttons (✔)
#       - check boxes (✔)
#       - menu button
#   - button group?
#   - label
#   - scroll bars
#   - scroller - can border be used for this?
#   - menu bar
#   - menu
#   - status bar
#   - dialog box (✔)
#   - text entry
#   - text box
#   - horizontal / vertical separators
#   - padding
#   - list
#   - tree

# PRIORITIES:
#
# --1.-- Event handling - decide how to do this, do we want something
# declarative and semantically high-level for defining event handlers
# (like DUIM) or is something basic sufficient? Basic for now.  - send
# event to topmost sheet where event occurred / send keyboard events
# to current focus.
#
# --1.5.-- Dialogs; need some way to provide feedback without having
# to throw exceptions everywhere... keep them basic, just a new
# sheet type.
#
# 1.6. extend dialogs so they are actually useful for displaying stuff
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

# test / fix screen resize!

# need to do something about events! - see draw_next_frame() in
# screen.py

# and we need command tables or some other way to tie keys
# and ui to commands.

# specialise "region_contains_position" for decorated buttons and
# other decorated widgets... not sure quite how to do that so that
# border can be ignored for mouse click location but included for
# other "does this point inhabit the widget space" queries...
# Note if the button was wrapped in a spacing pane, this problem
# would solve itself I think...

# more flexibility for borders; DOUBLE, SINGLE, SPACE, NONE... could
# also combine into a spacing pane.

# click detection is really ropey. Have implemented button down =
# button activate but really don't like it. Will have to write "are
# you sure?" dialogs all over as a work-around (or investigate button
# click behaviour, maybe there's some better fix)

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

    oneb = BorderLayout(title="buttons")
    child_sheet.add_child(oneb)

    one = VerticalLayout([1, 1, 1])
    oneb.add_child(one)

    # could do with a way to give "pressed" visual feedback but not
    # sure how. Maybe redraw on button down, and do the click on
    # button up, if the mouse is still over the button?
    button = Button(label="Press me!", decorated=True)
    dialog = Dialog(frame, title="dialog!")

    def btn_cb():
        # sets dialog up, but doesn't draw it. That happens in
        # render(). Perhaps the dialog layout sould happen in
        # lay_out_frame()? Maybe it's independent.
        frame.show_dialog(dialog)

    button.on_click = btn_cb
    one.add_child(button)
    one.add_child(RadioButton(label="Radio", decorated=False))
    one.add_child(CheckBox(label="Check"))

    inner_bl = BorderLayout(title="two")
    child_sheet.add_child(inner_bl)
    child_sheet.add_child(BorderLayout(title="three"))
    child_sheet.add_child(BorderLayout(title="four"))

#    inner_bl.add_child(button)

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

    # Should the frame manage a menu and status bar (unless I decide
    # to manage that stuff manually). Need to decide when to call
    # refresh() / redraw() in that case... but then need to decide how
    # to deal with the events. And focus. And input. Etc., etc.

    # The frame needs to be sure to direct events to the dialog, if there
    # is one, in preference to any other sheet (conceptually the dialog
    # is always highest in z-order)
    frame.start_frame()


Screen.wrapper(demo, unicode_aware=True)
