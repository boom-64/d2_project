import re
from pathlib import Path

def append(*, path: Path, suffix: str, overwrite: bool = False) -> Path:
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
    _validate_file(path)

    suffix = _validate_suffix(suffix=suffix)

    new_path: Path = path.with_name(path.name + suffix)

    return _update_filename(old_path=path, new_path=new_path, overwrite=overwrite)

def rm_final(*, path: Path, overwrite: bool = False) -> Path:
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
    _validate_file(path)

    if not path.suffix:
        raise ValueError(f"File '{path}' has no suffix to be removed.")

    new_path: Path = path.with_suffix('')

    return _update_filename(old_path=path, new_path=new_path, overwrite=overwrite)
    
def _validate_file(path: Path) -> None:
    """
    Validate that the given path refers to an existing file.

    Args:
        path (Path): The path to validate.

    Raises:
        ValueError: If the path does not refer to a file.
    """
    if not path.is_file():
        raise ValueError(f"Passed 'path={path}' must refer to file.")

def _validate_suffix(suffix: str) -> str:
    """
    Validate and normalize the suffix string.

    Ensures the suffix is a string, starts with a '.', and matches allowed 
    characters.

    Args:
        suffix (str): The suffix string to validate.

    Returns:
        str: Normalized suffix starting with '.'.

    Raises:
        ValueError: If the suffix is not a string or does not match the 
            allowed pattern.
    """
    if not suffix.startswith('.'):
        suffix = '.' + suffix

    if not re.fullmatch(r'\.[A-Za-z0-9._-]+', suffix):
        raise ValueError(f"New suffix '{suffix}' not a compatible suffix.")
    
    return suffix

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
