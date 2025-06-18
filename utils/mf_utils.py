from __future__ import annotations

# ==== Standard Libraries ====

import errno
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

# ==== Non-Standard Libraries ====

import requests
from requests.models import Response

# ==== Local Modules ====

import core.errors
import core.validators
import utils.general_utils

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
        raise core.errors.DownloadError(
            url=url,
            stream=stream,
            original_exception=e
        ) from e

    except OSError as e:
        raise OSError(f"Error writing file {file.name}: {e}") from e

def dl_mf_zip(
    *,
    zip_path: Path,
    url: str
) -> None:
    """
    Function to download manifest zip from Bungie

    This function tries to write content downloaded with _dl_bungie_content
    to a tempfile.NamedTemporaryFile. A variable write_success is used to
    distinguish between write errors and future move errors. The function
    then tries to move the temporary file to the passed path 'zip_path'. If
    an OSError or shutil.Error occurs and the writing of the file was
    successful, an OSError is raised giving context of which file was moving
    where. Finally, any remaining temporary file is removed should it exist,
    with any errors which might suggest that the file has been cleared up
    ignored.

    Args:
        zip_path (str | Path): Path to move zip file to when successfully
            written (default 'manifest.zip' set in function body).
        url (str (optional)): The URL to query for the content.

    Returns:
        None

    Raises:
        ValueError: If URL passed is invalid.
        OSError: If an error occurs moving the file, or if an unexpected
            OSError occurs in temporary file cleanup.
    """
    tmp_path: Path | None = None
    write_success: bool = False # Stores write success of dl_bungie_content()

    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

            # Archive will be big so stream
            write_success = dl_bungie_content(
                url=url,
                file=tmp_file,
                stream=True
            )

        # Overwriting existing archives is fine
        utils.general_utils.mv_item(
            src=tmp_path,
            dst=zip_path,
            overwrite=True
        )

    except (OSError, shutil.Error) as e:
        if not write_success:
            raise # Re-raise errors from dl_bungie_content()
        raise OSError(
            f"Error moving file {tmp_path} to {zip_path}: {e}"
        ) from e

    finally:
        if tmp_path:
            try:
                tmp_path.unlink() # 'tmp_path' refers to a NamedTemporaryFile

            except (FileNotFoundError, PermissionError):
                pass # Ignore cases where file unreachable

            except OSError as e:
                if e.errno not in (errno.ENOENT, errno.EPERM, errno.EACCES):
                    raise
