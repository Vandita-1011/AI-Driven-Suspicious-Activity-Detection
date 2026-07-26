"""
Execution Timing Utilities
===========================
Wall-clock timing for pipeline stages — both as a context manager and decorator.

Usage (context manager):
    from src.utils.timer import Timer

    with Timer("Feature Engineering") as t:
        features = pipeline.build()
    print(f"Elapsed: {t.elapsed_seconds:.3f}s")

Usage (decorator):
    from src.utils.timer import timed

    @timed("Data Loading")
    def load_data() -> DatasetContext:
        ...
"""
from __future__ import annotations

import functools
import time
from typing import Any, Callable, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class Timer:
    """Context manager that measures wall-clock execution time.

    Attributes:
        name:             Human-readable label for the timed operation.
        elapsed_seconds:  Elapsed time in seconds (available after ``__exit__``).
        elapsed_ms:       Elapsed time in milliseconds.

    Example:
        with Timer("Risk Fusion") as t:
            result = fusion.fuse(engine_results)
        print(f"Fused {n} transactions in {t.elapsed_ms:.1f}ms")
    """

    def __init__(self, name: str = "Operation", log: bool = True) -> None:
        """Initialises a Timer.

        Args:
            name: Label shown in the log output.
            log:  If True, automatically logs start (DEBUG) and end (INFO).
        """
        self.name = name
        self.log = log
        self.elapsed_seconds: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        if self.log:
            logger.debug("⏱  Starting: %s", self.name)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.elapsed_seconds = time.perf_counter() - self._start
        if self.log:
            if exc_type is None:
                logger.info(
                    "✅ %s completed in %.3fs", self.name, self.elapsed_seconds
                )
            else:
                logger.error(
                    "❌ %s failed after %.3fs (%s: %s)",
                    self.name, self.elapsed_seconds, exc_type.__name__, exc_val,
                )
        # Do not suppress exceptions

    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds."""
        return self.elapsed_seconds * 1_000.0


def timed(stage_name: Optional[str] = None) -> Callable:
    """Decorator that measures and logs the execution time of a function.

    Args:
        stage_name: Human-readable label for the stage. Defaults to the
                    decorated function's ``__name__`` if not provided.

    Returns:
        Decorator that wraps the target function with a ``Timer``.

    Example:
        @timed("Preprocessing Stage")
        def run_preprocessing(df: pd.DataFrame) -> pd.DataFrame:
            ...
    """
    def decorator(func: Callable) -> Callable:
        label = stage_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with Timer(label):
                return func(*args, **kwargs)

        return wrapper
    return decorator
