"""Custom validators for use across codebase."""

from __future__ import annotations

# ==== Standard Libraries ====
import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

# ==== Non-Standard Libraries ====
import validators

# ==== Type Checking ====
if TYPE_CHECKING:
    from pathlib import Path

# ==== Logging Config ====
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

_logger = logging.getLogger(__name__)


# ==== String Patterns ====
@dataclass
class _ComparePattern:
    """Class for comparing patterns.

    Attributes:
        pattern (str): Pattern to compare.
        pattern_for (str): Short description of pattern purpose.

    """

    pattern: str
    pattern_for: str


lc_checksum_pattern: _ComparePattern = _ComparePattern(
    pattern=r"^[a-f0-9]{32}$",
    pattern_for="(lowercase) checksum",
)

file_suffix_pattern: _ComparePattern = _ComparePattern(
    pattern=r"\.[A-Za-z0-9._-]+",
    pattern_for="file suffix",
)

url_path_pattern: _ComparePattern = _ComparePattern(
    pattern="^/?(?:[A-Za-z0-9._~!$&'()*+,;=:@%-]+/)*[A-Za-z0-9._~!$&'()*+,;=:@%-]*/?$",
    pattern_for="URL path",
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


def str_matches_pattern(*, value: str, pattern: str, pattern_for: str) -> bool:
    """Validate string-pattern match.

    Args:
        value (str): Value to check.
        pattern (str): Pattern to check against.
        pattern_for (str): Short description of pattern purpose.

    Raises:
        ValueError: If pattern match fails.

    """
    does_match: bool
    if not (does_match := bool(re.fullmatch(pattern, value))):
        _logger.exception(
            "Value %s not a valid %s: Expected pattern: %s.",
            value,
            pattern,
            pattern_for,
        )
        raise ValueError
    return does_match


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
