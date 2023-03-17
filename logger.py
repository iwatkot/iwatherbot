import logging
import sys

import globals as g


class Logger(logging.getLoggerClass()):
    """Handles logging to the file and stroudt with timestamps."""

    def __init__(self, name: str):
        super().__init__(name)
        self.setLevel(logging.DEBUG)
        self.stdout_handler = logging.StreamHandler(sys.stdout)
        self.file_handler = logging.FileHandler(
            filename=g.LOG_FILE, mode="a", encoding="utf-8"
        )
        self.fmt = g.LOG_FORMATTER
        self.stdout_handler.setFormatter(logging.Formatter(g.LOG_FORMATTER))
        self.file_handler.setFormatter(logging.Formatter(g.LOG_FORMATTER))
        self.addHandler(self.stdout_handler)
        self.addHandler(self.file_handler)


def get_log_file() -> str:
    """Returns the path to the main_log file."""
    return g.LOG_FILE
