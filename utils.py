import hashlib
import logging
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import validators

from errors import ChecksumMismatchError 
from schemas import MD5Checksum

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def mv_item(
    src: Path, 
    dst: Path,
    overwrite: bool = False
) -> None:
    """
    Move a file or directory from 'src' to 'dst'.

    If 'dst' is an existing directory, the source item is moved inside it 
    with the same name. If 'dst' is a file path, the source is moved/renamed 
    to that path directly.

    Args:
        src (Path): Path to the source file or directory.
        dst (Path): Destination directory or file path.
        overwrite (bool): If True, overwrite existing files or directories 
            at the destination. If False and a target exists, raises 
                FileExistsError.

    Raises:
        FileNotFoundError: If the source path does not exist.
        IsADirectoryError: If attempting to move directory onto file path.
        FileExistsError: If the target path exists and 'overwrite' is False.

    Notes:
        Do not call this function many times rather than using shutil.move.
    """
    src = src.resolve()
    dst = dst.resolve()

    if not src.exists():
        raise FileNotFoundError(f"Entry to be moved '{src}' does not exist") 

    # Validate entry type compatibility and assign 'target_path'
    target_path: Path = dst
    if dst.is_dir():
        target_path = dst / src.name
    elif src.is_dir():
        raise IsADirectoryError(
            f"Cannot move directory '{src}' to file path '{dst}'."
        )

    # Check and clear 'target_path' if 'overwrite==True', else raise
    if target_path.exists():
        if not overwrite:
            raise FileExistsError(
                f"An item '{target_path}' already exists."
            )
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink()
    
    shutil.move(str(src), str(target_path))

def calc_file_md5(path: Path) -> str:
    """
    Calculate the MD5 hash of the given file.

    Args:
        path (str | Path): Path to the file.

    Returns:
        str: The hexadecimal MD5 hash of the file contents.

    Raises:
        ValueError: If 'path' does not refer to a file.
    """
    if not path.is_file():
        raise ValueError(
            f"Provided path '{path}' does not refer to a file."
        )

    # Assign 'hasher' - an MD5 hash object.
    hasher = hashlib.md5()
    
    with path.open('rb') as f:
        # Update 'hasher' with each 8KB chunk
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    # Return 'hexdigest()' of 'hasher' MD5 hash object
    return hasher.hexdigest()

def validate_md5(val: str, name: str | None = None) -> None:
    """
    Validates that the provided string is a valid MD5 checksum.

    An MD5 checksum is expected to be a 32-character hexadecimal string. If 
    the input does not meet this format, a ValueError is raised.

    Args:
        val (str): The string to validate as an MD5 checksum.
        name (Optional[str]): A label used in the error message to indicate
            the source or purpose of the checksum being validated.

    Raises:
        ValueError: If the input is not a valid 32-character hexadecimal MD5 
            checksum.
    """
    # Check 'val' is of MD5 checksum format (double-length hex string)
    if not re.fullmatch(r'[0-9a-fA-F]{32}', val):
        raise ValueError(f"{name} value '{val}' is not a valid MD5 checksum")

def verify_md5_match(
    actual: str, 
    expected: str, 
    strict: bool = True
) -> None:
    """
    Verifies that an MD5 checksum matches the expected value.

    Args:
        actual (str): The actual MD5 checksum to verify.
        expected (str): The expected MD5 checksum to compare against.
        strict (bool): If False, do not raise an error on mismatch; 
            return instead (default: True).

    Returns:
        None. 
    
    Raises:
        ChecksumMismatchError: If the checksums do not match and allow_fail 
        is False.
    """
    validate_md5(val=actual, name='calculated actual checksum')
    validate_md5(val=expected, name='extracted expected checksum')

    # Return if 'actual'=='expected'
    if actual.lower() == expected.lower():
        return

    # Log if 'allow_fail==True'
    if not strict:
        logging.warning(
            f"MD5 mismatch ignored, expected {expected}, got {actual}"
        )
        return

    # Raise if not returned yet
    raise ChecksumMismatchError(actual=actual, expected=expected)

def add_suffix(path: Path, suffix: str, overwrite: bool = False) -> Path:
    """
    Add suffix to end of a file.

    This function first validates the passed variables, ensuring the file
    path passed is a file (raising ValueError if not) and that the passed
    suffix is a compatible file extension (again raising ValueError if not).
    A new path is created combining the file path and new suffix. If this
    path refers to an existing file, and overwrite=False, a FileExistsError 
    is raised. Otherwise, the file is renamed with the new path.

    Args:
        path (Path, str): Path to file to rename.
        suffix (str): Suffix to append to file. 
        overwrite (bool): Whether or not to overwrite files with matching 
            name.

    Returns:
        Path: Path to file under new file name.

    Raises:
        ValueError: If either the passed path doesn't refer to a file or if
            the passed suffix isn't a compatible file suffix.
        FileExistsError: If the new path refers to an already existing file.
    """
    if not path.is_file():
        raise ValueError(f"Passed path '{path}' must refer to a file.")
    
    # Check 'suffix' is a usable suffix
    if not re.fullmatch(r'\.[A-Za-z0-9._-]+', suffix):
        raise ValueError(f"New suffix {suffix} not a compatible suffix.")

    # Assign 'new_path'
    new_path = path.with_name(path.name + suffix)

    # Raise if filename clash with 'new_path' and 'overwrite==False'
    if new_path.exists() and not overwrite:
        raise FileExistsError(f"File with new name {new_path} already exists.")
    
    path.replace(new_path)
   
    return new_path

def rm_suffix(path: Path, overwrite: bool = False) -> Path:
    """
    Remove the file extension (suffix) from a file path.

    This function renames the specified file by removing its final suffix 
    (file extension). For example, "file.txt" becomes "file", and 
    "archive.tar.gz" becomes "archive.tar".

    Args:
        path (Path): The path to the file whose suffix should be removed.
        overwrite (bool): Whether or not to overwrite a possible file
            matching the new name of the file.

    Returns:
        Path: A new Path object pointing to the renamed file.

    Raises:
        ValueError: If the path does not refer to a file, or the file has no 
            suffix.
        FileExistsError: If a file with the new name already exists.
    """
    path = Path(path)

    if not path.is_file():
        raise ValueError(f"Passed path {path} must be a file.")

    if not path.suffix:
        raise ValueError(f"File {path} has no suffix to be removed.")
    
    new_path = path.with_suffix('')

    # Raise if filename clash with 'new_path' and 'overwrite==False'
    if new_path.exists() and not overwrite:
        raise FileExistsError(f"File with new name {new_path} already exists.")

    path.replace(new_path)

    return new_path

def validate_expected_entry_count(
    entry_type: str, 
    expected: int | None, 
    actual: int, 
    entry_source: Path | str
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
            no validation is performed. 
        actual (int): The actual number of entries found.
        source_path (Path): Path to the source (e.g., directory or archive) 
            where entries were counted. Used for error messages.

    Raises:
        ValueError: If 'expected' is negative or does not match 'actual'.
    """
    # Only execute if 'expected' is not None
    if expected is not None:
        # Raise if expected is negative
        if expected < 0:
            raise ValueError(
                f"Expected {entry_type} count = {expected}: cannot have "
                f"negative number of {entry_type}s in archive."
            )
        
        # Raise if 'actual' != 'expected'
        if actual != expected:
            raise ValueError(
                f"Unexpected {entry_type} count in {entry_source}: "
                f"expected {expected}, found {actual}."
            )

def extract_zip(
    zip_path: Path, 
    extract_to: Path,
    overwrite: bool = False,
    expected_file_count: int | None = None,
    expected_dir_count: int | None = None
) -> None:
    """ 
    Extracts an archive to a target dir w/ optnl file/dir count validation.

    This function validates input paths and ensures the extraction 
    destination exists. If 'expected_file_count' or 'expected_dir_count' is 
    provided, the archive is first inspected and the actual file/directory 
    counts are checked. Contents are then extracted to a temporary directory 
    and moved to the final destination.

    Args:
        zip_path (Path): Path to the ZIP archive.
        extract_to (Path): Directory to extract files into.
        overwrite (bool): Whether to overwrite entries if they exist.
        expected_file_count (int, optional): Expected # of files in the zip.
        expected_dir_count (int, optional): Expected # of dirs in the zip.

    Returns:
        None.

    Raises:
        FileNotFoundError: If 'zip_path' doesn't point to a file.
        NotADirectoryError: If 'extract_to' exists but is not a directory.
        ValueError: If the expected file or directory count is violated.
    """
    has_expectation: bool = (
        expected_file_count is not None or expected_dir_count is not None
    )

    if not zip_path.is_file():
        raise FileNotFoundError(f"File {zip_path} is not a file.")

    # Raise if 'extract_to' exists AND isn't a directory
    if extract_to.exists() and not extract_to.is_dir():
        raise NotADirectoryError(
            f"Must extract to a directory; {extract_to} is not a directory."
        )

    # Create 'extract_to' directory, if none exists
    extract_to.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        # Assign 'tmp_path' (path to tmp)
        tmp_path: Path = Path(tmp)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Execute if some count of dirs and/or files expected
            if has_expectation:
                # Assign 'zip_contents' for re-use
                zip_contents = zip_ref.infolist()

                # Validate expected counts of files and/or dirs
                for entry_type, expected, predicate in [
                    ('file', expected_file_count, lambda e: not e.is_dir()),
                    ('dir', expected_dir_count, lambda e: e.is_dir())
                ]:
                    # Execute only if expected_*_count passed
                    if expected is not None:
                        validate_expected_entry_count(
                            entry_type=entry_type,
                            expected=expected,
                            actual=sum(
                                1 for e in zip_contents if predicate(e)
                            ),
                            entry_source=zip_path
                        )
            # Extract archive (at 'zip_path') contents to 'tmp'
            zip_ref.extractall(tmp)
        
        # Move each file in 'tmp' to 'extract_to', overwriting existing 
        # files if 'overwrite'==True
        for file in tmp_path.iterdir():
            mv_item(
                src=file, 
                dst=extract_to, 
                overwrite=overwrite 
            )

def rm_sibling_files(files_to_keep: set[Path]) -> None:
    """
    Removes all files and symlinks in the directory containing the specified 
    files, except for the files listed in 'files_to_keep'.

    Args:
        files_to_keep (set[Path]): A set of file paths to preserve. All 
            files must exist and reside in the same directory.

    Returns: 
        None.

    Raises:
        ValueError: If 'files_to_keep' is empty or if the files are not all
            in the same directory.
        FileNotFoundError: If any path in 'files_to_keep' does not exist or 
            is not a file.
        OSError: If an error occurs while attempting to delete a file.
    """
    keep = {f.resolve() for f in files_to_keep}

    # Validate non-emptiness of 'files_to_keep' and assign 'sample_file'
    try:
        sample_file = next(iter(keep))
    except StopIteration as e:
        raise ValueError(
            "Passed files_to_keep empty: must include a non-zero exception "
            "file count"
        ) from e

    directory = sample_file.parent

    # Validate 'files_to_keep'
    for f in keep:
        if not f.is_file():
            raise FileNotFoundError(
                f"Passed file-to-keep '{f}' does not exist."
            )
        if f.parent != directory:
            raise ValueError(
                f"Passed file-to-keep '{f}' not in same directory as other "
                f"passed file '{sample_file}' - all passed files must be "
                f"siblings."
            )

    # Unlink non-'files_to_keep' paths
    for item in directory.iterdir():
        if item not in keep and (item.is_file() or item.is_symlink()):
            try:
                item.unlink()
            except OSError as e:
                raise OSError(
                    f"Failed to delete item '{item.name}' from '{directory}': "
                    f"{e}"
                ) from e
