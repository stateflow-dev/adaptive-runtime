"""
Structured logger for Adaptive Runtime.
"""

import logging
import sys
import os
from datetime import datetime

# Enable ANSI colors on Windows
if sys.platform == "win32":
    os.system("")  # activates VT100 mode in Windows 10+


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_RuntimeFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


class _RuntimeFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: "\033[36m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        ts = datetime.now().strftime("%H:%M:%S")
        tag = record.name.split(".")[-1].upper()
        return f"{color}[{ts}][{tag}]{self.RESET} {record.getMessage()}"
