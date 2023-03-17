import os

from datetime import datetime


ABSOLUTE_PATH = os.path.dirname(__file__)
LOG_DIR = "logs"

os.makedirs(os.path.join(ABSOLUTE_PATH, LOG_DIR), exist_ok=True)

LOG_FORMATTER = "%(name)s | %(asctime)s | %(levelname)s | %(message)s"
LOG_FILE = os.path.join(
    ABSOLUTE_PATH, LOG_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_log.txt"
)
