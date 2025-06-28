"""Custom validators for use across codebase."""

from __future__ import annotations

# ==== Standard Libraries ====
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

# ==== Non-Standard Libraries ====
import validators

# ==== Local Modules ====
import d2_project.core.errors as d2_project_errors
import d2_project.core.logger as d2_project_logger

# ==== Type Checking ====
if TYPE_CHECKING:
    from collections.abc import Callable
    from logging import Logger
    from pathlib import Path

# ==== Logging Config ====
_logger: Logger = d2_project_logger.get_logger(__name__)


# ==== ComparePatterns ====
@dataclass
class ComparePattern:
    """Class for comparing patterns.

    Attributes:
        pattern (str): Pattern to compare.
        pattern_for (str): Short description of pattern purpose.

    """

    pattern: str
    pattern_for: str


lc_checksum_pattern: ComparePattern = ComparePattern(
    pattern=r"^[a-f0-9]{32}$",
    pattern_for="(lowercase) checksum",
)

file_suffix_pattern: ComparePattern = ComparePattern(
    pattern=r"\.[A-Za-z0-9._-]+",
    pattern_for="file suffix",
)

url_path_pattern: ComparePattern = ComparePattern(
    pattern="^/?(?:[A-Za-z0-9._~!$&'()*+,;=:@%-]+/)*[A-Za-z0-9._~!$&'()*+,;=:@%-]*/?$",
    pattern_for="URL path",
)

toml_bare_key_pattern: ComparePattern = ComparePattern(
    pattern=r"[A-Za-z0-9_-]+",
    pattern_for="TOML bare key",
)

toml_needs_triple_quotes_pattern: ComparePattern = ComparePattern(
    pattern=r".*[\n\r\"'].*",
    pattern_for="TOML triple-quotable string",
)


# ==== Functions ====
def expected_entry_count(
    *,
    entry_type: str,
    actual: int,
    entry_source: Path,
    expected: int,
) -> None:
    """Validate that the actual number of entries matches the expected count.

    This function checks whether the number of observed entries (e.g., files
    or directories) in a given archive or directory matches the expected
    count. If the expected count is 'None', the check is skipped. If the
    expected count is negative or does not match the actual count, a
    ValueError is raised.

    Args:
        entry_type (str): A string describing the type of entry being
            counted (e.g., "file", "directory").
        expected (int, optional): The expected number of entries. If 'None',
            no validation is performed (default is None).
        actual (int): The actual number of entries found.
        entry_source (Path): Path to the source (e.g., directory or archive)
            where entries were counted. Used for error messages.

    Raises:
        ValueError: If 'expected' is negative or does not match 'actual'.

    """
    # Raise if expected is negative or actual != expected
    if expected < 0:
        _logger.exception(
            "Expected '%s' count = %s: cannot have negative number of '%s's in"
            " archive.",
            entry_type,
            expected,
            entry_type,
        )
        raise ValueError

    if actual != expected:
        _logger.exception(
            "Unexpected '%s' count in '%s': expected %s, found %s.",
            entry_type,
            entry_source,
            expected,
            actual,
        )
        raise ValueError


def str_matches_pattern(
    *,
    value: str,
    pattern: str,
    pattern_for: str,
    log_func: Callable[..., None] | None = None,
) -> bool:
    """Validate string-pattern match.

    Args:
        value (str): Value to check.
        pattern (str): Pattern to check against.
        pattern_for (str): Short description of pattern purpose.
        log_func (Callable[..., None] | None): Logging function (defaults to
            None).

    Returns:
        bool: Returns True if match success.

    Raises:
        d2_project_errors.PatternMismatchError: If pattern match fails

    """
    if re.fullmatch(pattern, value):
        return True

    if log_func is not None:
        log_func(
            "Value %s not a valid %s: Expected pattern: %s.",
            value,
            pattern,
            pattern_for,
        )
    raise d2_project_errors.PatternMismatchError(
        value=value,
        pattern=pattern,
        pattern_for=pattern_for,
    )


def entry_is_file(path: Path) -> None:
    """Validate that the given path refers to an existing file.

    Args:
        path (Path): The path to validate.

    Raises:
        ValueError: If the path does not refer to a file.

    """
    if not path.is_file():
        _logger.exception(
            "Passed path '%s' must refer to a file.",
            path.resolve(),
        )
        raise ValueError


def str_is_valid_url(value: str) -> None:
    """Validate URL."""
    if not validators.url(value):
        raise ValueError
