from __future__ import annotations

# ==== Standard Libraries ====

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

# ==== Non-Standard Libraries ====

import requests
from requests.models import Response

# ==== Local Modules ====

import d2_project.core.errors as d2_project_errors
import d2_project.core.utils.general as general_utils

# ==== Type Checking ====

if TYPE_CHECKING:
    from typing import IO

# ==== Functions ====

def request_bungie(
    url: str,
    *,
    key: str | None = None
) -> Response:
    """
    Function to make GET request to Bungie URL and return parsed response.

    This function makes a GET request to Bungie with optional use of an
    API key. If the response fails, a ConnectionError is raised. The
    response is parsed and returned with the custom TypedDict
    BungieResponseData. If the parsing fails, a ValueError is raised.

    Args:
        url (str): Optional complete URL to be queried.
        key (str | None): Optional API key to pass in request.

    Raises:
        ConnectionError: If the HTTP request fails (non-2xx status).
        ValueError: If passed URL is invalid or if response parsing fails.

    Returns:
        BungieResponseData: Parsed JSON response from Bungie.
    """
    headers = {"X-API-KEY": key} if key else None

    response = requests.get(url, headers=headers, timeout=(3, 5))

    if not response.ok:
        raise ConnectionError(
            f"Request to Bungie failed with status {response.status_code}: "
            f"{response.reason}"
        )

    return response

def dl_bungie_content(
    *,
    file: IO[bytes],
    url: str,
    stream: bool = True
) -> bool:
    """
    Function to download and write Bungie content to a file.

    This function tries to stream the content of the response to the passed
    file, streaming if stream is passed. If an error occurs with the request
    itself, a custom DownloadError is raised with the URL, whether the
    content is being streamed and the original exception raised. If another
    OSError occurs, i.e. with writing the file, an OSError is raised.

    Args:
        file (IO[bytes]): The (open) file to write the content to.
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

        return True

    except requests.RequestException as e:
        raise d2_project_errors.DownloadError(
            url=url,
            stream=stream,
            original_exception=e
        ) from e

    except OSError as e:
        raise OSError(f"Error writing file {file.name}: {e}") from e

def dl_and_extract_mf_zip(
    *,
    url: str,
    mf_dir_path: Path,
    mf_zip_structure: dict[str, int],
    overwrite: bool = False
) -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = Path(tmp.name)

        dl_bungie_content(
            url=url,
            file=tmp,
            stream=True
        )

        tmp.flush()
    try:
        general_utils.extract_zip(
            zip_path=tmp_path,
            extract_to=mf_dir_path,
            expected_dir_count=mf_zip_structure['expected_dir_count'],
            expected_file_count=mf_zip_structure['expected_file_count'],
            overwrite=overwrite
        )
    finally:
        tmp_path.unlink(missing_ok=True)
