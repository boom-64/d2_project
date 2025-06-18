from __future__ import annotations

# ==== Standard Libraries ====

import re
from typing import TYPE_CHECKING

# ==== Type Checking ====

if TYPE_CHECKING:
    from pathlib import Path

# ==== Functions ====

def lc_checksum(checksum_candidate: str) -> str:
    lc_val: str = checksum_candidate.lower()

    if re.fullmatch(r'^[a-f0-9]{32}$', lc_val):
        return lc_val

    raise ValueError(f"Invalid MD5 checksum: {checksum_candidate}")

def expected_entry_count(
    *,
    entry_type: str,
    actual: int,
    entry_source: Path,
    expected: int
) -> None:
    """
    Validates that the actual number of entries matches the expected count.

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
        source_path (Path): Path to the source (e.g., directory or archive)
            where entries were counted. Used for error messages.

    Raises:
        ValueError: If 'expected' is negative or does not match 'actual'.
    """
    # Raise if expected is negative
    if expected < 0:
        raise ValueError(
            f"Expected '{entry_type}' count = {expected}: cannot have "
            f"negative number of '{entry_type}'s in archive."
        )

    # Raise if 'actual' != 'expected'
    if actual != expected:
        raise ValueError(
            f"Unexpected '{entry_type}' count in '{entry_source}': "
            f"expected {expected}, found {actual}."
        )

def file_name(*, name: str, pattern: str) -> None:
    if not re.fullmatch(pattern, name):
        raise ValueError(
            f"File name '{name}' does not match expected file name format: "
            f"{pattern}."
        )

def entry_is_file(path: Path) -> None:
    """
    Validate that the given path refers to an existing file.

    Args:
        path (Path): The path to validate.

    Raises:
        ValueError: If the path does not refer to a file.
    """
    if not path.is_file():
        raise ValueError(f"Passed 'path={path}' must refer to file.")

def file_suffix(suffix: str) -> None:
    """
    Validate the suffix string.

    Ensures the suffix is a string, starts with a '.', and matches allowed
    characters.

    Args:
        suffix (str): The suffix string to validate.

    Raises:
        ValueError: If the suffix is not a string or does not match the
            allowed pattern.
    """
    if not re.fullmatch(r'\.[A-Za-z0-9._-]+', suffix):
        raise ValueError(f"New suffix '{suffix}' not a compatible suffix.")
