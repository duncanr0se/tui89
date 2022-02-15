from asciimatics.screen import Screen
from time import sleep

from geometry.transforms import Transform
from geometry.transforms import IDENTITY_TRANSFORM

from sheets.sheet import Sheet
from sheets.toplevel import TopLevelSheet
from sheets.borderlayout import BorderLayout
from sheets.buttons import Button
from sheets.buttons import RadioButton
from sheets.buttons import CheckBox
from sheets.boxlayout import HorizontalLayout
from sheets.boxlayout import VerticalLayout

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
#   - menu bar
#   - menu
#   - status bar
#   - dialog box
#   - text entry
#   - text box
#   - horizontal / vertical separators
#   - padding

# need to do something about events!

# make existing stuff prettier / more correct (alignment of text in
# buttons, themes, colours, attributes, etc.)

# and we need command tables or some other way to tie keys
# and ui to commands.

# drawing is a separate thing altogether...

# look at other stuff asciimatics does (save / restore form state
# etc.) and decide if that's something that could be useful.Pretty
# sure it isn't...
def demo(screen):
    top_level_sheet = TopLevelSheet(screen)
    border_layout = BorderLayout(title="Basic")
    top_level_sheet.add_child(border_layout)

#    child_sheet = Sheet()
#    child_sheet = CheckBox(label="PRESS ME!")
    child_sheet = VerticalLayout([1, 2, 1, 1])
#    child_sheet = HorizontalLayout([1, 2, 1, 1])
    border_layout.add_child(child_sheet)

    child_sheet.add_child(BorderLayout(title="one"))
    child_sheet.add_child(BorderLayout(title="two"))
    child_sheet.add_child(BorderLayout(title="three"))
    child_sheet.add_child(BorderLayout(title="four"))

    # is space allocation part of layout? not sure
    top_level_sheet.allocate_space((screen.width, screen.height))
    top_level_sheet.layout()

#    child_sheet.print_at('Hello, world!', (0, 0))
#    child_sheet.print_at('{}x{}'.format(str(screen.width), str(screen.height)), (0, 1))
#    child_sheet.print_at('{}'.format(child_sheet), (0, 2))
#    child_sheet.print_at('and now for something completely different; a longish string!', (156, 10))

    top_level_sheet.render()

    sleep(10)


Screen.wrapper(demo, unicode_aware=True)
