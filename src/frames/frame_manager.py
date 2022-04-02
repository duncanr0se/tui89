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

import signal

from collections import deque

from asciimatics.screen import Screen
from asciimatics.widgets.utilities import THEMES
from asciimatics.event import KeyboardEvent, MouseEvent
from asciimatics.exceptions import ResizeScreenError

from sheets.sheet import Sheet
from dcs.ink import Pen
from geometry.regions import Region
from geometry.points import Point
from frames.commands import find_command

from logging import getLogger

logger = getLogger(__name__)

class FrameManager():
    """Manages application frames.

    Intermediary between the display (screen) and the widgets.
    """
    # LaF is the purview of the frame manager, so keep all the pen
    # stuff here.

    # Pens are fully formed and include background and fill
    # information.
    #
    # They are indexed by:
    #
    #     "role" - which is generally the same as the name of the type
    #     of widget;
    #
    #     "state" - state changes imply visual indicators. In general
    #     only "default" and "focus" states are supported, but labels
    #     also have a "accelerator" state indicator and some widgets
    #     have a "pressed" state.
    #
    #     "pen" - usually "pen", can be "accelerator". Editable items
    #     have a "cursor" pen providing the cursor colours.
    #
    # If desired pen not found in role / state, try to find it in role
    # / default state (and log it).
    # If desired pen not found in role / default state, log it and use
    # role / default / "pen".
    #
    # FIXME: add "brush" pen for backgrounds / fills.
    #
    # Are menu buttons any different in any way to regular buttons,
    # other than by colour scheme and callback? Use same role but
    # override in menubar / menubox containers?
    #
    # pen method walks hierarchy until top sheet at which point
    # default defined in frame is returned. Any level can override
    # binding to the pen.
    #
    THEMES = {
        "toplevel": {
            "default": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_WHITE, ' ')
            },
            "alert": {
                "pen": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_RED, ' ')
            },
            "info": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN, ' ')
            },
            "yes/no": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_MAGENTA, ' ')
            },
            "composite": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE, ' ')
            }
         },
        "shadow": {
            "default": {
                # "partial pen" - needs to be merged with some
                # background before use
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, None, None)
            }
        },
        # border role used by border panes and separator panes
        "border": {
            "default": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_WHITE, ' ')
            },
            "alert": {
                "pen": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_RED, ' ')
            },
            "info": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_CYAN, ' ')
            },
            "yes/no": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_MAGENTA, ' ')
            },
            "composite": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE, ' ')
            }
        },
        "button": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_GREEN, ' '),
                "accelerator": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_GREEN, ' ')
            },
            "focus": {
                "pen": Pen(Screen.COLOUR_CYAN, Screen.A_BOLD, Screen.COLOUR_GREEN, ' ')
            },
            "transient": {
                "pen": Pen(Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_MAGENTA, ' ')
            }
        },
        "buttonbox": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_CYAN, ' '),
                "accelerator": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN, ' ')
            },
            "focus": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_GREEN, ' '),
            }
        },
        "editable": {
            "default": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_CYAN, ' '),
                "area_pen": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_CYAN, ' ')
            },
            "selected": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_GREEN, ' '),
                "area_pen": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_GREEN, ' ')
            },
            "focus": {
                "pen": Pen(Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLUE, ' '),
                "area_pen": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_BLUE, ' '),
                "cursor": Pen(Screen.COLOUR_YELLOW, Screen.A_REVERSE, Screen.COLOUR_BLUE, ' ')
            }
        },
        "label": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE, ' '),
                "accelerator": Pen(Screen.COLOUR_YELLOW, Screen.A_BOLD, Screen.COLOUR_WHITE, ' ')
            }
        },
        "menubar": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE, ' ')
            }
        },
        "menubox": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE, ' ')
            },
            "border": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE, ' ')
            }
        },
        "menubutton": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE, ' '),
                "accelerator": Pen(Screen.COLOUR_RED, Screen.A_BOLD, Screen.COLOUR_WHITE, ' ')
            },
            "focus": {
                "pen": Pen(Screen.COLOUR_CYAN, Screen.A_BOLD, Screen.COLOUR_GREEN, ' '),
                "accelerator": Pen(Screen.COLOUR_RED, Screen.A_BOLD, Screen.COLOUR_GREEN, ' ')
            },
            "transient": {
                "pen": Pen(Screen.COLOUR_GREEN, Screen.A_NORMAL, Screen.COLOUR_MAGENTA, ' ')
            }
        },
        "optionbox": {
            "default": {
                "accelerator": Pen(Screen.COLOUR_RED, Screen.A_BOLD, Screen.COLOUR_CYAN, ' ')
            }
        },
        "undefined": {
            "default": {
                "pen": Pen(Screen.COLOUR_GREEN, Screen.A_BOLD, Screen.COLOUR_YELLOW, 'X')
            }
        },
        "shadow": {
            "default": {
                "pen": Pen(Screen.COLOUR_BLACK, Screen.A_NORMAL, None, ' ')
            }
        },
        "scroll": {
            "default": {
                "pen": Pen(Screen.COLOUR_CYAN, Screen.A_REVERSE, Screen.COLOUR_BLUE, ' ')
            }
        }
    }
