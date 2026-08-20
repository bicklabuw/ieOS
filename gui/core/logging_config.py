# gui/core/logging_config.py
"""Configure process-wide logging for ieOS (threads, display, navigation)."""
from __future__ import annotations

import logging
import sys


def configure_logging(*, verbose: bool = False, quiet: bool = False) -> None:
    """
    Attach a single stderr handler to the root logger.

    - Default: INFO
    - ``verbose``: DEBUG
    - ``quiet``: WARNING (takes precedence over verbose if both are set)
    """
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    root = logging.getLogger()
    root.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(threadName)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
