# ==== Local Modules ====

import config.sanity
import core.errors
import core.validators
import utils.general_utils
import utils.mf_utils

# ==== Functions ====

def remote_mf_dir(
    *,
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

def mf_filename(
    name: str,
    expected_pattern: str
) -> bool:
    if not utils.mf_utils.
