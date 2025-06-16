from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from pathlib import Path

import core.validators

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def mv_item(
    *,
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
        Do not call this function many times instead of using shutil.move().
    """
    src = src.resolve()
    dst = dst.resolve()

    if not src.exists():
        raise FileNotFoundError(f"Entry to be moved '{src}' does not exist.")

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

def extract_zip(
    *,
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
                        core.validators.expected_entry_count(
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

def rm_file(file: Path) -> None:
    if not file.is_file():
        raise ValueError(f"Path 'file={file}' does not refer to a file")
    file.unlink()

def append_suffix(*, path: Path, suffix: str, overwrite: bool = False) -> Path:
    """
    Append a suffix to the filename of the given file path.

    For example, appending ".bak" to "file.txt" results in "file.txt.bak".

    Args:
        path (Path): Path to the existing file.
        suffix (str): The suffix to append. Must start with a '.' or it will
            be prepended.
        overwrite (bool): Whether to overwrite if the target file already 
            exists (defaults to False).

    Returns:
        Path: The new Path object with the appended suffix.
    """
    core.validators.entry_is_file(path)

    suffix = core.validators.file_suffix(suffix=suffix)

    new_path: Path = path.with_name(path.name + suffix)

    return _update_filename(
        old_path=path, 
        new_path=new_path, 
        overwrite=overwrite
    )

def rm_final_suffix(*, path: Path, overwrite: bool = False) -> Path:
    """
    Remove the final suffix (file extension) from the given file path.

    For example, 'archive.tar.gz' becomes 'archive.tar' after one call.

    Args:
        path (Path): Path to the existing file.
        overwrite (bool): Whether to overwrite if the target file already 
            exists (defaults to False).

    Returns:
        Path: The new Path object with the final suffix removed.

    Raises:
        ValueError: If the given (validated) file has no suffix.
    """
    core.validators.entry_is_file(path)

    if not path.suffix:
        raise ValueError(f"File '{path}' has no suffix to be removed.")

    new_path: Path = path.with_suffix('')

    return _update_filename(
        old_path=path, 
        new_path=new_path, 
        overwrite=overwrite
    )
    
def _update_filename(old_path: Path, new_path: Path, overwrite: bool) -> Path:
    """
    Rename the file from 'old_path' to 'new_path'.

    Checks if the new path exists and handles overwriting accordingly.

    Args:
        old_path (Path): Original file path.
        new_path (Path): New file path after renaming.
        overwrite (bool): Whether to overwrite the new_path if it exists.

    Returns:
        Path: The new Path object after renaming.

    Raises:
        FileExistsError: If 'new_path' exists and overwrite is False.
    """
    if new_path.exists() and not overwrite:
        raise FileExistsError(f"File with path '{new_path}' already exists.")
 
    old_path.replace(new_path)

    return new_path
