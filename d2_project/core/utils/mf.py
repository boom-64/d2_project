"""Utilities pertaining to manifest installation."""

from __future__ import annotations

# ==== Standard Libraries ====
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

# ==== Non-Standard Libraries ====
import requests

# ==== Local Modules ====
import d2_project.core.logger as d2_project_logger
import d2_project.core.utils.general as general_utils

# ==== Type Checking ====

if TYPE_CHECKING:
    from logging import Logger
    from typing import IO

    from requests.models import Response

# ==== Logging Config ====
_logger: Logger = d2_project_logger.get_logger(__name__)

# ==== Functions ====


def request_bungie(
    url: str,
    *,
    key: str | None = None,
) -> Response:
    """Make GET request to Bungie URL and return parsed response.

    This function makes a GET request to Bungie with optional use of an
    API key. If the response fails, a ConnectionError is raised. The
    response is parsed and returned with the custom TypedDict
    BungieResponseData. If the parsing fails, a ValueError is raised.

    Args:
        url (str): Optional complete URL to be queried.
        key (str | None): Optional API key to pass in request.

    Raises:
        ConnectionError: If the HTTP request fails (non-2xx status).

    Returns:
        BungieResponseData: Parsed JSON response from Bungie.

    """
    headers = {"X-API-KEY": key} if key else None

    response = requests.get(url, headers=headers, timeout=(3, 5))

    if not response.ok:
        _logger.exception(
            "Request to Bungie failed with status %s: %s.",
            response.status_code,
            response.reason,
        )
        raise ConnectionError

    return response


def dl_bungie_content(
    *,
    file: IO[bytes],
    file_path: Path,
    url: str,
    stream: bool = True,
) -> bool:
    """Download and write Bungie content to a file.

    This function tries to stream the content of the response to the passed
    file, streaming if stream is passed. If an error occurs with the request
    itself, a custom DownloadError is raised with the URL, whether the
    content is being streamed and the original exception raised. If another
    OSError occurs, i.e. with writing the file, an OSError is raised.

    Args:
        file (IO[bytes]): The (open) file to write the content to.
        file_path (Path): Path to file.
        url (str): The URL to query for the content.
        stream (bool): Whether or not to stream the file (defaults to True).

    Returns:
        bool: To distinguish between errors writing the file with this
            function and other contexts.

    Raises:
        ValueError: If passed URL is invalid.
        DownloadError: If an error occurs with the request.
        OSError: If another OSError occurs with writing the file.

    """
    try:
        with requests.get(url, stream=stream, timeout=(3, 10)) as response:
            response.raise_for_status()

            # Option to stream large files
            if stream:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            else:
                file.write(response.content)

    except requests.RequestException:
        _logger.exception(
            "Failed to download content from %s (stream=%s).",
            url,
            stream,
        )
        raise

    except OSError:
        _logger.exception("Error writing file %s", file_path.resolve())
        raise

    return True


def dl_and_extract_mf_zip(
    *,
    url: str,
    mf_dir_path: Path,
    mf_zip_structure: dict[str, int],
    overwrite: bool = False,
) -> None:
    """Download and extract archive containing manifest files.

    Args:
        url (str): URL to manifest archive.
        mf_dir_path (Path): Directory to install manifest to.
        mf_zip_structure (dict[str, int]): Expected structure of archive.
        overwrite (bool, optional): Whether to overwrite existing manifests
            (defaults to False).

    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)

        dl_bungie_content(
            url=url,
            file=tmp,
            file_path=tmp_path,
            stream=True,
        )

        tmp.flush()
    try:
        general_utils.extract_zip(
            zip_path=tmp_path,
            extract_to=mf_dir_path,
            expected_dir_count=mf_zip_structure["expected_dir_count"],
            expected_file_count=mf_zip_structure["expected_file_count"],
            overwrite=overwrite,
        )
    finally:
        tmp_path.unlink(missing_ok=True)
