"""
IO Helper Utilities
====================
Safe file I/O utilities for loading CSVs and writing output files.

All paths are resolved relative to the project root directory,
which is determined automatically from this file's location.

No caller should need to know the absolute project path — always
use ``resolve_path()`` instead of hard-coding OS-specific paths.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from src.exceptions.engine_exceptions import DataLoadError
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Project root = AI-Driven-Suspicious-Activity-Detection/
# This file is at: src/utils/io_helpers.py → 3 levels up
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


def get_project_root() -> Path:
    """Returns the absolute path to the project root directory.

    Returns:
        Absolute ``Path`` to ``AI-Driven-Suspicious-Activity-Detection/``.
    """
    return _PROJECT_ROOT


def resolve_path(*parts: str) -> Path:
    """Resolves a path relative to the project root.

    Args:
        *parts: Path components joined together. All relative to project root.

    Returns:
        Absolute ``Path`` object.

    Example:
        resolve_path("dataset", "transaction.csv")
        # → /path/to/AI-Driven-Suspicious-Activity-Detection/dataset/transaction.csv
    """
    return _PROJECT_ROOT.joinpath(*parts)


def load_csv_safe(
    file_path: str | Path,
    table_name: str = "",
    low_memory: bool = False,
    **pandas_kwargs: Any,
) -> pd.DataFrame:
    """Safely loads a CSV file into a pandas DataFrame.

    Args:
        file_path:     Absolute or project-root-relative path to the CSV.
        table_name:    Display name used in log messages and error messages.
        low_memory:    Passed to ``pd.read_csv()``. Default False for correct dtype inference.
        **pandas_kwargs: Additional kwargs forwarded to ``pd.read_csv()``.

    Returns:
        Loaded ``pd.DataFrame``.

    Raises:
        DataLoadError: If the file does not exist or cannot be parsed.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path

    display = table_name or path.name

    if not path.exists():
        raise DataLoadError(
            message=f"CSV file not found: {path}",
            file_path=str(path),
        )

    try:
        df = pd.read_csv(path, low_memory=low_memory, **pandas_kwargs)
        logger.info(
            "Loaded '%s': %d rows × %d columns from %s",
            display, len(df), len(df.columns), path.name,
        )
        return df
    except Exception as exc:
        raise DataLoadError(
            message=f"Failed to parse '{display}': {exc}",
            file_path=str(path),
        ) from exc


def save_json(
    data: dict | list,
    file_path: str | Path,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> None:
    """Saves a Python object as a formatted JSON file.

    Creates parent directories automatically.

    Args:
        data:         Dict or list to serialise.
        file_path:    Target file path (absolute or project-root-relative).
        indent:       JSON indentation spaces.
        ensure_ascii: If False, Unicode characters are written as-is.

    Raises:
        OSError: If the file cannot be written.
    """
    path = _resolve_output_path(file_path)

    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=indent, ensure_ascii=ensure_ascii, default=str)

    logger.info("Saved JSON output → %s (%d bytes)", path.name, path.stat().st_size)


def load_json(file_path: str | Path) -> dict | list:
    """Loads a JSON file and returns the parsed Python object.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed ``dict`` or ``list``.

    Raises:
        DataLoadError: If the file does not exist or contains invalid JSON.
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path

    if not path.exists():
        raise DataLoadError(
            message=f"JSON file not found: {path}",
            file_path=str(path),
        )

    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise DataLoadError(
            message=f"Invalid JSON in '{path.name}': {exc}",
            file_path=str(path),
        ) from exc


def save_dataframe(
    df: pd.DataFrame,
    file_path: str | Path,
    fmt: str = "csv",
) -> None:
    """Saves a DataFrame to disk in the specified format.

    Args:
        df:        DataFrame to save.
        file_path: Target file path (absolute or project-root-relative).
        fmt:       Output format — ``'csv'`` or ``'parquet'``.

    Raises:
        ValueError: If an unsupported format is specified.
    """
    path = _resolve_output_path(file_path)

    if fmt == "csv":
        df.to_csv(path, index=False)
    elif fmt == "parquet":
        df.to_parquet(path, index=False)
    else:
        raise ValueError(
            f"Unsupported output format: '{fmt}'. Supported: 'csv', 'parquet'."
        )

    logger.info(
        "Saved DataFrame (%d rows) → %s [%s]", len(df), path.name, fmt
    )


def ensure_dir(dir_path: str | Path) -> Path:
    """Creates a directory (including parents) if it does not already exist.

    Args:
        dir_path: Directory path to create.

    Returns:
        Absolute ``Path`` to the created / existing directory.
    """
    path = Path(dir_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── Internal helpers ─────────────────────────────────────────────────────────

def _resolve_output_path(file_path: str | Path) -> Path:
    """Resolves an output path and ensures its parent directory exists."""
    path = Path(file_path)
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
