"""Central logging configuration used by the application.

This module configures a console handler and a rotating file handler and
applies a consistent formatter. Importing this module has the side effect
of initializing the root logger for the process.
"""

import logging
from logging.handlers import RotatingFileHandler

# --- handlers ---
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)       # terminal: WARNING and above only

file_handler = RotatingFileHandler(
    filename="app.log",
    maxBytes=5 * 1024 * 1024,                   # rotate when file hits 5 MB
    backupCount=3,                              # keep up to 3 old rotated files:
                                                #   app.log        <- current, always being written to
                                                #   app.log.1      <- previous file (most recent rotation)
                                                #   app.log.2      <- one before that
                                                #   app.log.3      <- oldest kept; .4 would be deleted
    encoding="utf-8",                           # handles non-ASCII characters safely
)
file_handler.setLevel(logging.DEBUG)            # file: everything

# --- formatter ---
formatter = logging.Formatter(
    fmt=(
        "%(asctime)s | "        # timestamp: when the event occurred
        "%(levelname)s | "      # level: DEBUG / INFO / WARNING / ERROR / CRITICAL
        "%(filename)s:"         # source file where the log call was made
        "%(lineno)d | "         # line number in that file
        "%(message)s"           # message: what you passed to logger.info(...) etc.
    ),
    datefmt="%Y-%m-%d %H:%M:%S",               # drop milliseconds for readability
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# --- root logger ---
logging.basicConfig(
    level=logging.DEBUG,                        # this is the GATE, not a duplicate of handler levels
                                                # a log record must pass this first before reaching any handler
                                                # if this were WARNING, DEBUG and INFO would be killed here,
                                                # and the file handler would never see them —
                                                # regardless of the file handler's own level setting
    handlers=[console_handler, file_handler]
)