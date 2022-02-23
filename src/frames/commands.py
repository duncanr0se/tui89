
from asciimatics.screen import Screen
from asciimatics.exceptions import StopApplication

# keycode :: Command object map
# Commands the frame deals with go in this map

# TODO: need to be able to find keys for accelerators for commands to
# show in menus and on buttons etc. For now, the different top level
# sheets are responsible for doing this. (won't be efficient!)
COMMANDS = {}


class Command():

    def __init__(self, name, func):
        self._func = func
        self._name = name

    def apply(self, client):
        return self._func(client)


def quit_command(client):
    raise StopApplication("quit")

def register_command(keys, command):
    for key in keys:
        # FIXME: check if key is already bound
        # FIXME: deal with modifier keys
        COMMANDS[key] = command

def find_command(key_event):
    cmd = None
    if key_event.key_code:
        try:
            cmd = COMMANDS[key_event.key_code]
        except KeyError:
            pass
    return cmd


#### global commands

# QUIT / EXIT
keycode = Screen.ctrl('w')
register_command([keycode], Command("quit", quit_command))

# QUIT_POPUP - maybe this should be added by specific
# top-level-sheets?
#register_command([Screen.KEY_ESCAPE], Command("quit_popup", exit_popup))
