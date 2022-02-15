from asciimatics.screen import ManagedScreen
from asciimatics.scene import Scene
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from time import sleep

def demo():
    with ManagedScreen() as screen:
        screen.print_at("Hello, world!", 0, 0)
        screen.refresh()
        sleep(10)

demo()
