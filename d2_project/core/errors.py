"""Custom errors."""

# ==== Import Annotations from __future__ ====
from __future__ import annotations

# ==== Standard Library Imports ====
from typing import TYPE_CHECKING

# ==== Type Checking ====
if TYPE_CHECKING:
    from pathlib import Path

# ==== Classes ====

class DownloadError(ConnectionError):
    """Custom exception for exceptions which occur during a download.

    This exception is raised when a file fails to download. It includes
    the source URL of the download, whether or not the file is being
    streamed, and the original exception.

    Attributes/args:
        url (str): The source URL of the downloading file.
        stream (bool): Signifies whether or not the file was being
            streamed. True for streaming; False for not.
        original_exception (Exception): The original exception.

    """

    def __init__(
        self,
        *,
        url: str,
        stream: bool,
        original_exception: Exception,
    ) -> None:
        """Initialise class."""
        self.url = url
        self.stream = stream
        self.original_exception = original_exception

        message: str = (
            f"Failed to download content from {url} "
            f"(stream={stream}): {original_exception}"
        )

        super().__init__(message)

class ManifestRemotePathError(ValueError):
    """Custom exception for unexpected manifest remote paths.

    Attributes:
        path (str): Manifest remote path.

    """

    def __init__(self, *, path: str) -> None:
        """Initialise class."""
        self.path = path
        message: str = (
            f"Invalid remote manifest format: '{self.path}'. "
            f"Bungie may have changed manifest path format."
        )
        super().__init__(message)

class UnxpectedCountError(ValueError):
    """Custom exception for unexpected file/dir counts.

    Attributes:
        entry_type (str): What the count is of e.g. file, dir.
        expected (int): Expected count.
        actual (int): Actual count.
        entry_source (Path): Source of entries in the filesystem.
        message (str): Message to be passed to ValueError.

    """

    def __init__(
        self,
        *,
        entry_type: str,
        expected: int,
        actual: int,
        entry_source: Path | None = None,
    ) -> None:
        """Initialise class."""
        self.entry_type: str = entry_type
        self.expected: int = expected
        self.actual: int = actual
        self.entry_source: Path | None = entry_source
        message: str

        if expected < 0:
            message = (
                f"Expected '{entry_type}' count = {expected}: cannot have "
                f"negative number of '{entry_type}'s in archive."
            )

        else:
            message = (
                f"Unexpected '{entry_type}' count in '{entry_source}': "
                f"expected {expected}, found {actual}."
            )
        super().__init__(message)
        self.message: str = message
