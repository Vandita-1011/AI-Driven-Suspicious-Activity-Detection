"""
DataFrame Schema Validators
============================
Utility functions that validate pandas DataFrames against expected schemas.

Used by the DatasetLoader (after CSV loading) and preprocessing stages
to catch schema violations early with meaningful error messages.

All functions raise ``SchemaValidationError`` on failure.
All functions log a DEBUG message on success for traceability.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.exceptions.engine_exceptions import SchemaValidationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_columns(
    df: pd.DataFrame,
    required_cols: list[str],
    table_name: str = "DataFrame",
) -> None:
    """Ensures a DataFrame contains all required columns.

    Args:
        df:            DataFrame to validate.
        required_cols: List of column names that must be present.
        table_name:    Display name used in error messages.

    Raises:
        SchemaValidationError: If one or more required columns are absent.
    """
    existing = set(df.columns)
    missing = [col for col in required_cols if col not in existing]

    if missing:
        raise SchemaValidationError(
            message=f"'{table_name}' is missing required columns.",
            table_name=table_name,
            missing_cols=missing,
        )

    logger.debug(
        "✔ Column validation passed for '%s' (%d cols checked)",
        table_name, len(required_cols),
    )


def validate_no_nulls(
    df: pd.DataFrame,
    columns: list[str],
    table_name: str = "DataFrame",
) -> None:
    """Ensures specified columns have no missing values.

    Args:
        df:         DataFrame to validate.
        columns:    List of columns to check for nulls.
        table_name: Display name used in error messages.

    Raises:
        SchemaValidationError: If any specified column contains nulls.
    """
    for col in columns:
        if col in df.columns:
            n_nulls = df[col].isna().sum()
            if n_nulls > 0:
                raise SchemaValidationError(
                    message=f"'{table_name}.{col}' contains {n_nulls} missing value(s).",
                    table_name=table_name,
                )
                
    logger.debug(
        "✔ Null check passed for '%s' (%d cols checked)",
        table_name, len(columns),
    )



def validate_no_duplicates(
    df: pd.DataFrame,
    id_column: str,
    table_name: str = "DataFrame",
) -> None:
    """Ensures an ID column contains no duplicate values (primary key check).

    Args:
        df:        DataFrame to validate.
        id_column: Column that must be unique.
        table_name: Display name used in error messages.

    Raises:
        SchemaValidationError: If duplicates are found.
    """
    if not df[id_column].is_unique:
        n_dupes = int(df[id_column].duplicated().sum())
        raise SchemaValidationError(
            message=(
                f"'{table_name}.{id_column}' has {n_dupes} duplicate value(s). "
                "Primary key must be unique."
            ),
            table_name=table_name,
        )

    logger.debug("✔ Duplicate check passed for '%s.%s'", table_name, id_column)


def validate_not_empty(
    df: pd.DataFrame,
    table_name: str = "DataFrame",
) -> None:
    """Ensures a DataFrame is not empty (has at least one row).

    Args:
        df:         DataFrame to validate.
        table_name: Display name used in error messages.

    Raises:
        SchemaValidationError: If the DataFrame has zero rows.
    """
    if df.empty:
        raise SchemaValidationError(
            message=f"'{table_name}' loaded with 0 rows. Expected non-empty data.",
            table_name=table_name,
        )

    logger.debug("✔ Non-empty check passed for '%s' (%d rows)", table_name, len(df))


def validate_foreign_key(
    child_df: pd.DataFrame,
    child_col: str,
    parent_df: pd.DataFrame,
    parent_col: str,
    child_table: str = "child",
    parent_table: str = "parent",
    allow_nulls: bool = True,
) -> None:
    """Validates referential integrity between two DataFrames.

    Args:
        child_df:     DataFrame containing the foreign key column.
        child_col:    Foreign key column name in child_df.
        parent_df:    DataFrame containing the referenced primary key.
        parent_col:   Primary key column name in parent_df.
        child_table:  Display name for the child table.
        parent_table: Display name for the parent table.
        allow_nulls:  If True, null values in child_col are accepted
                      (optional / nullable foreign key).

    Raises:
        SchemaValidationError: If any non-null child FK value has no
                               matching value in the parent column.
    """
    valid_keys: set = set(parent_df[parent_col].dropna())
    child_keys: pd.Series = child_df[child_col]

    if allow_nulls:
        child_keys = child_keys.dropna()

    invalid_mask = ~child_keys.isin(valid_keys)
    n_invalid = int(invalid_mask.sum())

    if n_invalid > 0:
        sample = child_keys[invalid_mask].head(5).tolist()
        raise SchemaValidationError(
            message=(
                f"FK violation: '{child_table}.{child_col}' → "
                f"'{parent_table}.{parent_col}'. "
                f"{n_invalid} orphan reference(s) found. "
                f"Sample invalid values: {sample}"
            ),
            table_name=child_table,
        )

    logger.debug(
        "✔ FK validation passed: '%s.%s' → '%s.%s'",
        child_table, child_col, parent_table, parent_col,
    )


def validate_dtypes(
    df: pd.DataFrame,
    expected_dtypes: dict[str, Any],
    table_name: str = "DataFrame",
) -> list[str]:
    """Checks column dtypes against expected types.

    Returns a list of warning strings rather than raising — dtype coercion
    is handled by the DataCleaner, so this function is informational.

    Args:
        df:              DataFrame to check.
        expected_dtypes: Dict mapping column names to expected dtype strings,
                         e.g. ``{'amount': 'float64', 'customer_id': 'object'}``.
        table_name:      Display name used in warning messages.

    Returns:
        List of warning strings for mismatched dtypes (empty if all match).
    """
    warnings_list: list[str] = []

    for col, expected in expected_dtypes.items():
        if col not in df.columns:
            continue
        actual = str(df[col].dtype)
        if actual != str(expected):
            msg = (
                f"'{table_name}.{col}': expected dtype '{expected}', "
                f"got '{actual}'"
            )
            warnings_list.append(msg)
            logger.debug("dtype mismatch — %s", msg)

    if not warnings_list:
        logger.debug(
            "✔ dtype check passed for '%s' (%d cols checked)",
            table_name, len(expected_dtypes),
        )

    return warnings_list


def validate_value_range(
    df: pd.DataFrame,
    column: str,
    min_val: float | None = None,
    max_val: float | None = None,
    table_name: str = "DataFrame",
) -> None:
    """Checks that a numeric column's values fall within an expected range.

    Args:
        df:         DataFrame to validate.
        column:     Numeric column name.
        min_val:    Minimum acceptable value (inclusive). None = no lower bound.
        max_val:    Maximum acceptable value (inclusive). None = no upper bound.
        table_name: Display name used in error messages.

    Raises:
        SchemaValidationError: If any value falls outside the specified range.
    """
    series = df[column].dropna()

    if min_val is not None:
        n_below = int((series < min_val).sum())
        if n_below > 0:
            raise SchemaValidationError(
                message=(
                    f"'{table_name}.{column}': {n_below} value(s) below "
                    f"minimum {min_val}. Min found: {series.min()}"
                ),
                table_name=table_name,
            )

    if max_val is not None:
        n_above = int((series > max_val).sum())
        if n_above > 0:
            raise SchemaValidationError(
                message=(
                    f"'{table_name}.{column}': {n_above} value(s) above "
                    f"maximum {max_val}. Max found: {series.max()}"
                ),
                table_name=table_name,
            )

    logger.debug(
        "✔ Range check passed for '%s.%s' [%s, %s]",
        table_name, column, min_val, max_val,
    )

def validate_timestamp(
    df: pd.DataFrame,
    column: str,
    table_name: str = "DataFrame",
) -> None:
    """Checks if a column can be successfully parsed as a timestamp.
    
    Args:
        df: DataFrame to validate.
        column: The column to validate.
        table_name: Display name used in error messages.
        
    Raises:
        SchemaValidationError: If parsing fails.
    """
    if column not in df.columns:
        return
        
    try:
        # Just test if to_datetime works without raising error on first few rows
        # For full validation, we attempt parsing. If there are NaT and original was not null, it's an error.
        original_nulls = df[column].isna().sum()
        parsed = pd.to_datetime(df[column], errors='coerce')
        new_nulls = parsed.isna().sum()
        
        if new_nulls > original_nulls:
            failed_count = new_nulls - original_nulls
            raise SchemaValidationError(
                message=f"'{table_name}.{column}': {failed_count} value(s) could not be parsed as timestamp.",
                table_name=table_name
            )
    except Exception as e:
        raise SchemaValidationError(
            message=f"'{table_name}.{column}' timestamp validation failed: {str(e)}",
            table_name=table_name
        )
        
    logger.debug("✔ Timestamp check passed for '%s.%s'", table_name, column)

