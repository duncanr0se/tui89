from asciimatics.screen import ManagedScreen
from asciimatics.scene import Scene
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from time import sleep

@ManagedScreen
def demo(screen=None):
    screen.print_at(u"☎ Hello, world!", 0, 0, screen.COLOUR_GREEN, screen.A_REVERSE)
    screen.move(10, 10)
    screen.draw(20, 15, thin=True)
    screen.refresh()
    sleep(10)

demo()
