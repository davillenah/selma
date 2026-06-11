"""
file: src/selma/infrastructure/logging.py
wire_sizing - Logger Configuration
version: 1.0.0

PURPOSE
-------
Provide a shared logger for the wire_sizing project.

FEATURES
--------
- Console logging
- File logging
- Consistent formatting
- Reusable across engine / validators / loaders

OUTPUT
------
Log file is written to:
    outputs/wire_sizing_debug.log
"""

from __future__ import annotations

import logging
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "outputs"
LOG_FILE = OUTPUT_DIR / "wire_sizing_debug.log"


def get_logger(name: str = "wire_sizing") -> logging.Logger:
    """
    Create or return a configured logger.

    Parameters
    ----------
    name : str
        Logger name

    Returns
    -------
    logging.Logger
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # prevent duplicate handlers

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger