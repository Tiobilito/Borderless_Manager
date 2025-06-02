import os
import sys

BASE_PATH = getattr(sys, '_MEIPASS', os.path.abspath("."))
CONFIG_PATH = os.path.join(BASE_PATH, "config.json")
ICON_PATH = os.path.join(BASE_PATH, "resources", "icon.ico")
BORDERLESS_PROGRAMS_PATH = os.path.join(BASE_PATH, "borderless_programs.json")
