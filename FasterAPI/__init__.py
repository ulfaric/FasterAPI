from __future__ import annotations

import logging

import colorlog

# set up logging
logger = logging.getLogger("FasterAPI")
stream_handler = logging.StreamHandler()

# Define log colors
cformat = "%(log_color)s%(levelname)s:\t%(message)s"
colors = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red,bg_white",
}

stream_formatter = colorlog.ColoredFormatter(cformat, log_colors=colors)
stream_handler.setFormatter(stream_formatter)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)
