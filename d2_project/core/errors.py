"""Custom errors for use across codebase."""

# ==== Import Annotations from __future__ ====
from __future__ import annotations

# ==== Standard Library Imports ====
from typing import TYPE_CHECKING

# ==== Non-Standard Library Imports ====
import iso639

# ==== Type Checking ====
if TYPE_CHECKING:
    from pathlib import Path

    import d2_project.schemas.mf as mf_schemas


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
        message (str): Message passed to ValueError.

    """

    def __init__(self, *, path: str) -> None:
        """Initialise class."""
        self.path = path
        message: str = (
            f"Invalid remote manifest format: '{self.path}'. "
            f"Bungie may have changed manifest path format."
        )
        super().__init__(message)
        self.message: str = message


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


class BungieConnectionError(ConnectionError):
    """Custom exception for when Bungie connection fails.

    Attributes:
        status_code (int): Status code received from Bungie.
        reason (str): Reason for error received from Bungie.
        message (str): Message passed to ConnectionError.

    """

    def __init__(self, *, status_code: int, reason: str) -> None:
        """Initialise class."""
        self.status_code: int = status_code
        message: str = (
            f"Request to Bungie failed with status {status_code}: {reason}."
        )
        super().__init__(message)
        self.message: str = message


class FileWriteError(OSError):
    """Custom exception for when files fail to write.

    Attributes:
        file (Path): File where write failed.
        original_exception (Exception): Original exception.
        message (str): Message passed to OSError.

    """

    def __init__(self, *, file: Path, original_exception: Exception) -> None:
        """Initialise class."""
        self.file: Path = file
        self.original_exception = original_exception
        message: str = (
            f"Error writing file {file.resolve()}: {original_exception}"
        )
        super().__init__(message)
        self.message: str = message


class IsNotFileError(ValueError):
    """Custom exception for when path needs to refer to file.

    Attributes:
        path (Path): Path to compare.
        message (str): Message to pass to ValueError.

    """

    def __init__(self, path: Path) -> None:
        """Initialise class."""
        self.path: Path = path
        message: str = f"Passed path '{path}' must refer to file."
        super().__init__(message)
        self.message: str = message


class PatternMismatchError(ValueError):
    """Custom exception for string pattern mismatch.

    Attributes:
        value (str): Value compared to pattern.
        pattern (str): Pattern compared against.
        pattern_for (str): Short descriptor of pattern usage.
        message (str): Message to pass to ValueError.

    """

    def __init__(self, *, value: str, pattern: str, pattern_for: str) -> None:
        """Initialise class."""
        self.value: str = value
        self.pattern: str = pattern
        self.pattern_for: str = pattern_for
        message: str = (
            f"Value {value} not a valid {pattern_for}: Expected pattern: "
            f"{pattern}."
        )
        super().__init__(message)
        self.message: str = message


class InvalidURLError(ValueError):
    """Custom exception for invalid URL arguments passed.

    Attributes:
        url (str): Invalid URL.
        message (str): Message passed to ValueError.

    """

    def __init__(self, url: str) -> None:
        """Initialise class."""
        self.url: str = url
        message: str = f"Passed URL '{url}' is an invalid URL."
        super().__init__(message)
        self.message: str = message


class UnknownAPIError(Exception):
    """Exception raised for errors returned by the Bungie API.

    This exception is intended to represent non-permission-related
    errors in Bungie's API response.

    Attributes:
        response_data (mf_schemas.BungieResponseData | None, optional): The
            BungieResponseData instance related to thiscerror.
        message (str): Message to pass to Exception.

    """

    def __init__(
        self,
        *,
        response_data: mf_schemas.BungieResponseData | None = None,
    ) -> None:
        """Initialise the APIError exception."""
        message: str = "Unknown Bungie API error."
        if response_data:
            message += f" Response data: '{response_data}'"

        super().__init__(message)
        self.message: str = message


class MissingBungieResponseFieldError(ValueError):
    """Custom exception for missing Bungie response fields.

    Attributes:
        original_key_error (Exception): Original KeyError raised.
        message (str): Message raised to ValueError.

    """

    def __init__(self, original_key_error: KeyError) -> None:
        """Initialise class."""
        self.original_key_error: KeyError = original_key_error
        message: str = (
            f"Missing required field in response: {original_key_error}."
        )
        super().__init__(message)
        self.message: str = message


class TooManyManifestsError(FileExistsError):
    """Custom exception for when too many compatible manifests exist.

    Attributes:
        mf_dir_path (Path): Path to manifest directory.
        mf_candidates (list[Path]): List of manifest candidates in mf_dir_path.
        message (str): Message to pass to FileExistsError.

    """

    def __init__(
        self,
        *,
        mf_dir_path: Path,
        mf_candidates: list[Path],
    ) -> None:
        """Initialise class."""
        self.mf_dir_path: Path = mf_dir_path
        self.mf_candidates: list[Path] = mf_candidates
        message: str = (
            f"Directory '{mf_dir_path} contains too many manifest candidates, "
            f"including both '{mf_candidates[0].name}' and "
            f"'{mf_candidates[1].name}'."
        )
        super().__init__(message)
        self.message: str = message


class ManifestLangUnavailableError(ValueError):
    """Custom exception for when a manifest language is currently unavailable.

    Attributes:
        mf_lang (str): Desired manifest language.
        available_langs (list): List of available languages.

    """

    def __init__(
        self,
        *,
        desired_mf_lang: iso639.Language,
        available_langs: list[str],
    ) -> None:
        """Initialise class."""
        self.desired_mf_lang: iso639.Language | None = desired_mf_lang or None
        self.available_langs: list[str] = available_langs
        available_lang_names: list[str] = [
            iso639.Language.match(code.split("-")[0]).name
            for code in available_langs
        ]
        message: str = (
            f"Language {desired_mf_lang.name} unavailable. Available "
            f"languages: {', '.join(available_lang_names)}."
        )
        super().__init__(message)
        self.message: str = message
