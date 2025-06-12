import tempfile
import shutil
import errno
import re
from pathlib import Path
from typing import IO

import requests

import utils
from schemas import URL, MD5Checksum, BungieResponseData
from errors import DownloadError

suffix_manipulator = utils.SuffixManip()

def request_bungie(url: URL, key: str | None = None) -> BungieResponseData:
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

    response = requests.get(url.url, headers=headers)
    
    if not response.ok:
        raise ConnectionError(
            f"Request to Bungie failed with status {response.status_code}: "
            f"{response.reason}"
        )
    
    return BungieResponseData(response)
    

def extract_mf_path(response: BungieResponseData, lang: str) -> str:
    """
    Function to extract manifest path from Bungie response data.

    This function tries to extract and return the manifest path from 
    returned Bungie response data passed as the custom BungieResponseData 
    TypedDict. If a KeyError occurs, one of two things happens:
        1. If one key of 'Response' or 'mobileWorldContentPaths' is missing, 
            a KeyError is raised;
        2. If the lang key is missing, a ValueError is raised, giving
            context on available languages.

    Args:
        response (BungieResponseData): Bungie's response data, as custom
            BungieResponseData TypedDict.
        lang (str): Desired manifest language (defaults to 'en')

    Returns:
        str: Remote relative manifest path.
    """
    try:
        return response.response['mobileWorldContentPaths'][lang]

    except KeyError as e:
        match e.args[0]:
            case 'mobileWorldContentPaths':
                raise KeyError(
                    "Missing 'mobileWorldContentPaths' key in Bungie API "
                    "response nested under 'Response' key."
                ) from e
                
            case missing_lang: # Catches all remaining KeyErrors
                available = response.response['Response']['mobileWorldContentPaths'].keys()

                raise ValueError(
                    f"Language '{missing_lang}' currently unsupported. "
                    f"Supported languages: {', '.join(available)}"
                ) from e

def fetch_remote_mf_path(
    url: URL,
    key: str,
    lang: str
) -> str:
    """
    Fetch the relative remote path to the latest manifest.

    This function makes a request to a URL. The potential errors returned in 
    the response are then handled by '_handle_bungie_errs'. Finally, the 
    path to the manifest is extracted with _extract_mf_path in the language 
    requested.

    Args:
        url (str, optional): URL for requesting the manifest location.
        key (str): API key supplied by Bungie.
        lang (str): Desired manifest language (defaults
            to 'en')

    Raises:
        ValueError: If passed URL is invalid.
    """
    response = request_bungie(url=url, key=key)

    return extract_mf_path(response=response, lang=lang)

def validate_remote_mf_dir(
    remote_path: str, 
    expected_dir: str, 
    strict: bool = True
) -> None:
    if not remote_path.startswith(expected_dir) and strict:
        raise ValueError(
            f"Invalid remote manifest format: '{remote_path}'. " 
            f"Bungie may have changed manifest path format."
        )
    # Log 

def validate_mf_name(name: str) -> None:
    if not re.fullmatch(r"^world_sql_content_[a-fA-F0-9]{32}\.content$", name):
        raise ValueError(
            f"File name '{name}' does not match expected manifest name format."
        )

def extract_remote_mf_name(
    remote_path: str,
    expected_lang_dir: str,
    lang: str,
    strict: bool = True
) -> str:
    validate_remote_mf_dir(
        remote_path=remote_path, 
        strict=strict, 
        expected_dir=f"{expected_lang_dir}{lang}/"
    )
    name = remote_path.split('/')[-1]
    validate_mf_name(name=name)
    return name

def fetch_current_mf_path(
    mf_dir_path: Path, 
    mf_ext: str
) -> Path | None:
    """
    Fetch the path to the active manifest database from the manifest directory.
    
    This function searches the given directory for files matching the
    specified manifest file extension. If exactly one matching file is 
    found, its path is returned. If more than one is found, a 
    FileExistsError is raised. If none are found, returns None.
    
    Args:
        mf_dir_path (str | Path | None): The Path to the manifest
            directory (default is Path('manifest')).
        mf_ext (str): The file extension of manifest databases 
            (default is '.content').

    Returns: 
        Path | None: The path to the manifest file, or None if none found.

    Raises:
        NotADirectoryError: If the provided path passed is not a directory.
        FileExistsError: If two - too many - manifest files are found.
    """
    mf_dir_path = Path(mf_dir_path)

    if not mf_dir_path.is_dir():
        raise NotADirectoryError(f"{mf_dir_path} is not a directory")
    
    mf_candidates = []
    for entry in mf_dir_path.iterdir():
        if entry.suffix == mf_ext and entry.is_file():
            mf_candidates.append(entry)
            
            # Raise early once more than one candidate found
            if len(mf_candidates) > 1:
                raise FileExistsError(
                    f"Directory {mf_dir_path} contains too many compatible "
                    f"manifest files, including both {mf_candidates[0]} and "
                    f"{mf_candidates[1]}"
                )

    # 'fetch_current_mf_path' returns None if no candidate found
    if not mf_candidates:
        return None
    
    # len(mf_candidates) == 1
    return mf_candidates[0]

def dl_bungie_content(
    file: IO[bytes], 
    url: URL,
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
        with requests.get(url.url, stream=stream) as response:
            response.raise_for_status()
            
            # Option to stream large files
            if stream:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            else:
                file.write(response.content)

        return True 

    except requests.RequestException as e:
        raise DownloadError(
            url=url, 
            stream=stream, 
            original_exception=e
        ) from e

    except OSError as e:
        raise OSError(f"Error writing file {file.name}: {e}") from e

def dl_mf_zip(zip_path: str | Path, url: URL) -> None:
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
    # Leverages Python's short-circuit evaluation
    output_path: Path = Path(zip_path or 'manifest.zip')

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
        utils.mv_item(
            src=tmp_path, 
            dst=output_path, 
            overwrite=True 
        )

    except (OSError, shutil.Error) as e:
        if not write_success:
            raise # Re-raise errors from dl_bungie_content()
        raise OSError(
            f"Error moving file {tmp_path} to {output_path}: {e}"
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

def extract_expected_md5(mf: Path) -> MD5Checksum:
    """
    Extract the expected MD5 hash from the manifest file name.

    Args:
        mf_path (Path): The path to the manifest file. The filename
            must contain the expected MD5 as the final underscore-delimited
            part (before the file extension).

    Returns:
        str: The expected MD5 hash string extracted from the filename.
    """
    validate_mf_name(mf.name)
    
    return MD5Checksum(mf.stem.split('_')[-1])

def fetch_mf_update_path(
    key: str, 
    url: URL,
    lang: str,
    mf_dir_path: Path,
    expected_remote_lang_dir: str,
    mf_ext: str,
    strict: bool = True,
    force_update: bool = False
) -> str | None:
    """
    Check with Bungie whether an update to the manifest is required.

    This function collects both the current manifest's name and the name of
    the newest available manifest from Bungie. Both names are validated and
    then compared. New manifest path is returned if they match, otherwise 
    None is returned.

    Args:
        key (str): API key supplied by Bungie.
        url (str): URL for Bungie's manifest location access.
        lang (str): Desired manifest language.
        force_update (bool): Forces function to return path.

    Returns:
        str: New manifest remote path.
        None: If no update is required.
    """
    current_mf_path: Path | None = fetch_current_mf_path(
        mf_dir_path=mf_dir_path, 
        mf_ext=mf_ext
    )

    current_mf_name: str = ''

    if current_mf_path:
        current_mf_name = current_mf_path.name

        validate_mf_name(current_mf_name)

    new_mf_path: str = fetch_remote_mf_path(url=url, key=key, lang=lang)

    new_mf_name: str = extract_remote_mf_name(
        remote_path=new_mf_path,
        expected_lang_dir=expected_remote_lang_dir,
        lang=lang,
        strict=strict
    )

    if current_mf_name == new_mf_name and not force_update:
        return None 

    return new_mf_path

def update_manifest(
    key: str, 
    dl_url_root: str, 
    mf_finder_url: URL, 
    expected_remote_lang_dir: str,
    zip_path: Path,
    mf_dir_path: Path,
    mf_ext: str,
    bak_ext: str,
    lang: str,
    strict: bool = True,
    force_update: bool = False
):
    if not mf_dir_path.is_dir():
        raise NotADirectoryError(
            f"Path '{mf_dir_path}' does not refer to a directory."
        )
    
    current_mf_path: Path | None = None

    new_mf_remote_path = fetch_mf_update_path(
        key=key, 
        url=mf_finder_url,
        expected_remote_lang_dir=expected_remote_lang_dir,
        lang=lang,
        force_update=force_update,
        mf_dir_path=mf_dir_path,
        mf_ext=mf_ext,
        strict=strict
    )

    if not new_mf_remote_path:
        return None
    
    dl_url = URL(
        url=dl_url_root, 
        path=new_mf_remote_path
    )

    dl_mf_zip(zip_path=Path(zip_path), url=dl_url)

    current_mf_path: Path | None = fetch_current_mf_path(
        mf_dir_path=mf_dir_path,
        mf_ext=mf_ext
    )

    if current_mf_path:
        current_mf_path = suffix_manipulator.append(
            path=current_mf_path, 
            suffix=bak_ext,
            overwrite=True
        )

    try:
        utils.extract_zip(
            zip_path=zip_path, 
            extract_to=mf_dir_path, 
            expected_file_count=1,
            expected_dir_count=0
        )

    except:
        if current_mf_path:
            utils.rm_sibling_files(
                files_to_keep={current_mf_path.resolve()}
            )
            suffix_manipulator.rm_final(path=current_mf_path)
        raise
    new_mf_local_path = fetch_current_mf_path(
        mf_dir_path=mf_dir_path, 
        mf_ext=mf_ext
    )
    if not new_mf_local_path:
        raise FileNotFoundError(
            f"No manifest file found in {mf_dir_path.resolve()}."
        )
    
    expected_md5: MD5Checksum = extract_expected_md5(mf=new_mf_local_path)
    computed_md5: MD5Checksum = utils.calc_file_md5(path=new_mf_local_path)
    computed_md5.assert_equals(expected=expected_md5, strict=strict)
