from __future__ import annotations

# ==== Standard Libraries ====
import re
from dataclasses import dataclass
from string import Template
from typing import TYPE_CHECKING

# ==== Type Checking ====

if TYPE_CHECKING:
    from pathlib import Path

# ==== String Patterns ====

@dataclass
class StringPattern:
    pattern: str
    errormsg: Template | None = None

lc_checksum_stringpattern = StringPattern(
    pattern=r"^[a-f0-9]{32}$",
    errormsg=Template("Value '$value not a valid checksum."),
)

file_suffix_stringpattern: StringPattern = StringPattern(
    pattern = r"\.[A-Za-z0-9._-]+",
    errormsg=Template("New suffix '$value' not a compatible suffix."),
)

class FileNameStringPattern(StringPattern):
    errormsg = Template(
        "File '$value' does not match expected file name pattern: '$pattern$.",
    )

# ==== Functions ====

def str_starts_with(value: str, starts_with: str, *, strict: bool) -> None:
    """Check whether or not a string starts with a certain string.

    This function checks whether a string starts with a certain string,
    raising a ValueError if 'strict=True' passed. Otherwise, the failure is
    logged.

    Args:
        value (str): The string to check.
        starts_with (str): The string to look for at the start of 'value'.
        strict (bool): Determines result of failure.

    Raises:
        ValueError: If 'strict==True' and the check fails.

    """
    if not value.startswith(starts_with):
        if strict:
            raise ValueError(
                f"String {value} does not begin with {starts_with} as "
                f"expected.",
            )
        pass
        # Log

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
    # Raise if expected is negative
    if expected < 0:
        raise ValueError(
            f"Expected '{entry_type}' count = {expected}: cannot have "
            f"negative number of '{entry_type}'s in archive.",
        )

    # Raise if 'actual' != 'expected'
    if actual != expected:
        raise ValueError(
            f"Unexpected '{entry_type}' count in '{entry_source}': "
            f"expected {expected}, found {actual}.",
        )

def str_matches_pattern(*, value: str, stringpattern: StringPattern) -> None:
    if not re.fullmatch(stringpattern.pattern, value):
        raise ValueError(
            stringpattern.errormsg or Template(
                "Value '$value' does not match expected pattern: '$pattern'.",
            ).safe_substitute(
                value=value,
                pattern=stringpattern.pattern,
            ),
        )

def entry_is_file(path: Path) -> None:
    """Validate that the given path refers to an existing file.

    Args:
        path (Path): The path to validate.

    Raises:
        ValueError: If the path does not refer to a file.

    """
    if not path.is_file():
        raise ValueError(f"Passed 'path={path}' must refer to file.")
