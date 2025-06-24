"""Simple logging configuration utility for the project."""
from __future__ import annotations

import logging
import os

from rich.logging import RichHandler


def setup_logging(level: str | int | None = None) -> None:
    """Configure root logger.

    If the environment variable ``LOG_FORMAT`` is set to ``json`` and the optional
    dependency ``python-json-logger`` is available, logs will be emitted in
    structured JSON format (useful for Stackdriver / Cloud Logging). Otherwise we
    fall back to colourful Rich output.
    """

    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    log_format = os.getenv("LOG_FORMAT", "rich").lower()

    if log_format == "json":
        try:
            from pythonjsonlogger import jsonlogger  # type: ignore

            handler: logging.Handler = logging.StreamHandler()
            formatter = jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
            handler.setFormatter(formatter)
            logging.basicConfig(level=level, handlers=[handler])
        except ImportError:  # pragma: no cover – optional dependency
            # Fallback to rich if json logger isn't installed
            logging.basicConfig(
                level=level,
                format="%(message)s",
                datefmt="[%X]",
                handlers=[RichHandler(markup=True, show_path=False, show_level=False, show_time=False)],
            )
    else:
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(markup=True, show_path=False, show_level=False, show_time=False)],
        ) 