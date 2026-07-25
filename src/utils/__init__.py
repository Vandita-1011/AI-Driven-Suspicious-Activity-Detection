"""
Utils Package
=============
Shared utility functions used across all engine modules.

Sub-modules:
    logger      get_logger() factory — centralised logging setup
    timer       Timer context manager and @timed decorator
    validators  DataFrame schema validation helpers
    io_helpers  Safe CSV loading, JSON I/O, path resolution

Usage:
    from src.utils.logger import get_logger
    from src.utils.timer import timed, Timer
    from src.utils.validators import validate_columns
    from src.utils.io_helpers import load_csv_safe, save_json, resolve_path
"""
from src.utils.logger import get_logger, setup_logging
from src.utils.timer import Timer, timed
from src.utils.validators import (
    validate_columns,
    validate_no_duplicates,
    validate_not_empty,
    validate_foreign_key,
    validate_dtypes,
)
from src.utils.io_helpers import (
    get_project_root,
    resolve_path,
    load_csv_safe,
    save_json,
    save_dataframe,
    load_json,
)

__all__ = [
    "get_logger", "setup_logging",
    "Timer", "timed",
    "validate_columns", "validate_no_duplicates", "validate_not_empty",
    "validate_foreign_key", "validate_dtypes",
    "get_project_root", "resolve_path", "load_csv_safe",
    "save_json", "save_dataframe", "load_json",
]
