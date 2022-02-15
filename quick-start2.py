from asciimatics.screen import Screen
from time import sleep

def demo(screen):
    screen.print_at("Hello, world!", 0, 0)
    screen.refresh()
    sleep(10)

Screen.wrapper(demo)
