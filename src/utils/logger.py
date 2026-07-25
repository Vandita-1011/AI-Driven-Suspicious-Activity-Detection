"""
Centralized Logging Setup
==========================
Factory function and setup routine for the AI engine's logging system.

Design:
  - All loggers share a single root configuration.
  - Two handlers: console (StreamHandler) + rotating file (RotatingFileHandler).
  - ``setup_logging()`` is idempotent — safe to call multiple times.
  - ``get_logger(__name__)`` is the only import modules need.

Usage:
    from src.utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Loaded %d transactions", n)
    logger.warning("Low data quality: %s", detail)
    logger.error("Engine failed: %s", error)
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

# Module-level guard — prevents adding duplicate handlers on repeated calls
_logging_configured: bool = False


def setup_logging(
    log_dir: str = "logs",
    log_file: str = "ai_engine.log",
    level: str = "INFO",
    log_format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    date_format: str = "%Y-%m-%d %H:%M:%S",
    max_bytes: int = 10_485_760,
    backup_count: int = 5,
    console_enabled: bool = True,
    file_enabled: bool = True,
) -> None:
    """Configures the root logger with console and rotating file handlers.

    This function is idempotent — calling it more than once has no effect.
    It is called automatically by ``load_settings()`` in ``src/config/settings.py``.

    Args:
        log_dir:         Directory where log files are stored (relative to project root).
        log_file:        Name of the rotating log file.
        level:           Logging level string ('DEBUG', 'INFO', 'WARNING', 'ERROR').
        log_format:      Log message format string.
        date_format:     Timestamp format string.
        max_bytes:       Maximum size (bytes) of each log file before rotation.
        backup_count:    Number of backup files to keep alongside the active log.
        console_enabled: Write log output to stdout.
        file_enabled:    Write log output to a rotating file in ``log_dir``.
    """
    global _logging_configured
    if _logging_configured:
        return

    numeric_level: int = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # ── Console handler ────────────────────────────────────────────────
    if console_enabled:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # ── Rotating file handler ──────────────────────────────────────────
    if file_enabled:
        # Resolve log_dir relative to project root (3 levels up from this file)
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        abs_log_dir = os.path.join(project_root, log_dir)
        os.makedirs(abs_log_dir, exist_ok=True)
        log_path = os.path.join(abs_log_dir, log_file)

        file_handler = RotatingFileHandler(
            filename=log_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    _logging_configured = True


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Returns a named logger for a module.

    If ``setup_logging()`` has not been called yet, a basic console
    configuration is applied automatically so logs are never silently
    dropped during early startup or unit tests.

    Args:
        name:  Module name — always pass ``__name__``.
        level: Optional per-logger level override. Leaves the root
               level unchanged; only affects this logger and its children.

    Returns:
        A configured ``logging.Logger`` instance.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing %d transactions", n)
    """
    global _logging_configured

    if not _logging_configured:
        # Fallback basic config — avoids silently lost logs before Settings load
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )
        # Mark as configured so basicConfig is only applied once
        _logging_configured = True

    logger = logging.getLogger(name)

    if level is not None:
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(numeric_level)

    return logger


def reset_logging() -> None:
    """Resets the logging configuration (for unit testing only).

    After calling this, the next ``setup_logging()`` or ``get_logger()``
    call will re-initialise the handlers.
    """
    global _logging_configured
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()
    _logging_configured = False
