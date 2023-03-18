import os
import json

from datetime import datetime


ABSOLUTE_PATH = os.path.dirname(__file__)
LOG_DIR = os.path.join(ABSOLUTE_PATH, "logs")

TMP_DIR = os.path.join(ABSOLUTE_PATH, "tmp")

MEDIA_DIR = os.path.join(ABSOLUTE_PATH, "media")

BACKGROUNDS_DIR = os.path.join(MEDIA_DIR, "backgrounds")
ICONS_DIR = os.path.join(MEDIA_DIR, "icons")

FONTS_DIR = os.path.join(ABSOLUTE_PATH, MEDIA_DIR, "fonts/static")
ARIMO_BOLD = os.path.join(FONTS_DIR, "Arimo-Bold.ttf")

with open(
    os.path.join(ABSOLUTE_PATH, MEDIA_DIR, "conditions.json"), "r", encoding="utf8"
) as f:
    CONDITIONS = json.load(f)

with open(
    os.path.join(ABSOLUTE_PATH, MEDIA_DIR, "conditions_types.json"),
    "r",
    encoding="utf8",
) as f:
    CONDITIONS_TYPES = json.load(f)

LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_FILE = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_log.txt")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)
