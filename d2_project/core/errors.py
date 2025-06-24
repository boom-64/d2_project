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
    from typing import Any

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


class DirToFileError(IsADirectoryError):
    """Custom exception for when a dir is moved to a path where a file exists.

    Attributes:
        dir (Path): Directory to move.
        file (Path): Target of move (file).
        message (str): Message passed to IsADirectoryError.

    """

    def __init__(self, *, src_dir: Path, dst_file: Path) -> None:
        """Initialise class."""
        self.src_dir: Path = src_dir
        self.dst_file: Path = dst_file
        message: str = (
            f"Cannot move directory '{src_dir}' to file path '{dst_file}'."
        )
        super().__init__(message)
        self.message: str = message


class DestinationExistsError(FileExistsError):
    """Custom exception to avoid file overwrites.

    Attributes:
        src (Path): Source file.
        dst (Path): Target destination path.
        message (str): Message passed to FileExistsError.

    """

    def __init__(self, src: Path, dst: Path) -> None:
        """Initialise class."""
        self.src: Path = src
        self.dst: Path = dst
        message: str = (
            f"Cannot move file: destination '{dst}' already exists. "
            f"Source: '{src}'."
        )
        super().__init__(message)
        self.message: str = message


class NonSiblingsError(ValueError):
    """Custom exception for when files aren't siblings.

    Attributes:
        sample_file (Path): Sample file.
        checked_file (Path): File checked.
        message (str): Message passed to ValueError.

    """

    def __init__(self, *, sample_file: Path, checked_file: Path) -> None:
        """Initialise class."""
        self.sample_file: Path = sample_file
        self.checked_file: Path = checked_file
        message: str = (
            f"Passed file-to-keep '{sample_file}' not in same directory as "
            f"other passed file '{checked_file}' - all passed files must be "
            f"siblings."
        )
        super().__init__(message)
        self.message: str = message


class NoSuffixError(ValueError):
    """Custom exception for when no removable suffix found.

    Attributes:
        file (Path): File with no suffix.
        message (str): Message passed to ValueError.

    """

    def __init__(self, file: Path) -> None:
        """Initialise class."""
        self.file: Path = file
        message: str = f"File {file} has no suffix to be removed."
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


class ExtractionTargetNotADirectoryError(NotADirectoryError):
    """Custom exception for when extracting to non-directory path.

    Attributes:
        extract_to (Path): Path to extract.
        message (str): Message passed to NotADirectoryError.

    """

    def __init__(self, extract_to: Path) -> None:
        """Initialise class."""
        self.extract_to: Path = extract_to
        message: str = (
            f"Must extract to a directory; {extract_to} is not a directory."
        )
        super().__init__(message)
        self.message: str = message


class NoFilesToKeepError(ValueError):
    """Custom exception for rm_sibling_files().

    Attributes:
        message (str): Message passed to ValueError.

    """

    def __init__(self) -> None:
        """Initialise class."""
        message: str = (
            "Passed files_to_keep empty: must include a non-zero exception "
            "file count."
        )
        super().__init__(message)
        self.message: str = message


class FileExistsAtPathError(FileExistsError):
    """Custom exception for avoiding file overwrites.

    Attributes:
        path (Path): Path of existing file.
        message (str): Message passed to FileExistsError.

    """

    def __init__(self, path: Path) -> None:
        """Initialise class."""
        self.path: Path = path
        message: str = f"File with path '{path}' already exists."
        super().__init__(message)
        self.message: str = message


class FileDeleteFailedError(OSError):
    """Custom exception for when file deletion fails.

    Attributes:
        item_name (str): Name of item whose deletion failed.
        directory (Path): Parent directory of file.
        original_exception (Exception): Original exception.
        message (str): Message to pass to OSError.

    """

    def __init__(
        self,
        *,
        item_name: str,
        directory: Path,
        original_exception: Exception,
    ) -> None:
        """Initialise class."""
        self.item_name: str = item_name
        self.directory: Path = directory
        self.original_exception = original_exception
        message: str = (
            f"Failed to delete item '{item_name}' from '{directory}': "
            f"{original_exception}."
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


class APIPermissionError(PermissionError):
    """Custom exception for known API errors.

    Attributes:
        error_code (int): The error code returned by Bungie.
        error_message (str): The message received from Bungie.
        message (str): The message passed to PermissionError.

    """

    def __init__(self, *, error_code: int, error_message: str) -> None:
        """Initialise class."""
        self.error_code: int = error_code
        self.error_message: str = error_message

        message: str = (
            f"Issue with the API key. Error code: {error_code}, error "
            f"message: '{error_message}'."
        )

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


class UnexpectedBungieResponseFieldError(ValueError):
    """Custom exception for when unexpected field arrives in Bungie response.

    Attributes:
        extra_components (set[str]): Set of extra components received.
        received_data (dict[str, Any]): Received data.
        message (str): Message passed to ValueError.

    """

    def __init__(
        self,
        *,
        extra_components: set[str],
        received_data: dict[str, Any],
    ) -> None:
        """Initialise class."""
        self.extra_componets: set[str] = extra_components
        self.received_data: dict[str, Any] = received_data
        message: str = "Unexpected components in response: " + ", ".join(
            f"{k}={received_data[k]!r}" for k in extra_components
        )
        super().__init__(message)
        self.message: str = message
