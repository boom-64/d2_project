"""
config/config.py

Generates configuration and sanity classes from TOML files.

This module contains configuration and sanity class definitions and
instances generated using their respective TOML files. These classes
are also capable of regenerating the TOML files by calling
utils.general.regenerate_toml() on a class instance which uses the class
defaults to regenerate a TOML file.
"""

# ==== Standard Library Imports ====

from dataclasses import dataclass
from string import Template
from pathlib import Path
from types import MappingProxyType

# ==== Non-Standard Library Imports ====

import toml

# ==== Dataclasses ====

@dataclass(frozen=True)
class Sanity:
    """
    Class for generating 'sanity' object for sanity checking.

    This class is used to generate a 'sanity' object for use across the
    program with callable sanity checkers for each non-flag attribute.

    The class instance should be generated using 'Sanity.from_toml()' with
    one positional arg being the path to a TOML file, by default
    'sanity.toml' in the same directory as this file. Attributes can be set
    in the TOML file to overwrite the defaults listed here.

    The method 'd2_project.utils.general.regenerate_toml()' can be used to
    regenerate a TOML file with the defaults here at the passed path.

    Attributes:
        strict (bool): Whether the sanity checkers should raise or log and
            silently fail.
        expected_remote_lang_dir (str): The expected remote path of the
            language directory each containing a manifest location.

    Class methods:
        from_toml(): Generator for 'sanity: Sanity' object.

    Methods:
        check_remote_mf_dir(): Sanity checker for 'expected_remote_lang_dir'
            attribute.
        disable_strict(): Sets 'self.strict' to False.
    """
    # ==== Flags ====

    strict: bool = False

    # ==== Remote Manifest Location Attributes ====

    expected_remote_lang_dir: str = '/common/destiny_content/sqlite/'

    # ==== Class Methods ====

    @classmethod
    def from_toml(cls, path: Path):
        """
        Generator for config.sanity object from TOML file at 'path'.

        This function generates the 'sanity' object for use across the
        project codebase. It returns a Sanity class instance with any
        attributes set in 'path' replacing the defaults of Sanity.

        Args:
            path (Path): Path to a configured TOML file.

        Returns:
            Sanity: The usable instance of Sanity.
        """
        data = toml.load(path)
        return cls(**data)

    # ==== Methods ====

    def check_remote_mf_dir(
        self,
        remote_path: str,
    ) -> None:
        """
        Sanity checker for remote manifest directory.

        This function checks a remote path (to the manifest directory)
        against the attribute value for expected_remote_lang_dir. If the
        Sanity instance is in strict mode, on failure a ValueError is
        raised. If strict==False, the failure is logged.

        Args:
            remote_path (str): The remote path to check.

        Raises:
            ValueError: If self.strict and the check fails.
        """
        if not remote_path.startswith(self.expected_remote_lang_dir):
            if self.strict:
                raise ValueError(
                    f"Invalid remote manifest format: '{remote_path}'. "
                    f"Bungie may have changed manifest path format."
                )

            print(f"{remote_path} != {self.expected_remote_lang_dir}")

    def disable_strict(self):
        """
        Sets Sanity instance attribute 'strict' to False.
        """
        object.__setattr__(self, 'strict', False)

@dataclass(frozen=True)
class Settings:
    """
    Class for generating 'settings' object for sanity checking.

    This class is used to generate a 'settings' object for use across the
    program.

    The class instance should be generated using 'Settings.from_toml()' with
    one positional arg being the path to a TOML file, by default
    'settings.toml' in the same directory as this file. Attributes can be set
    in the TOML file to overwrite the defaults listed here.

    The method 'd2_project.utils.general.regenerate_toml()' can be used to
    regenerate a TOML file with the defaults here at the passed path.

    Attributes:
        _expected_mf_name_template_str (str): Converted Template object for
            use in Settings.expected_mf_name_template().
        mf_extension (str): Manifest filename extension.
        mf_starts_with (str): Manifest filename start.
        mf_zip_structure (MappingProxyType): Zip structure of Bungie's
            manifest archive.
        mf_finder_url:

    Properties:

    Class methods:
        from_toml(): Generator for 'sanity: Sanity' object.
    """
    # ==== Private Manifest Filename Attributes ====

    _expected_mf_name_template_str: str = '^${starts_with}[a-fA-F0-9]{32}${extension}$$'

    # ==== Public Manifest Filename Attributes

    mf_extension: str = '.content'
    mf_starts_with: str = 'world_sql_content_'
    mf_zip_structure: MappingProxyType[str, int] = MappingProxyType({
        'expected_dir_count': 0,
        'expected_file_count': 1
    })

    # ==== Bungie Request Attributes ====

    mf_finder_url: str = 'https://www.bungie.net/Platform/Destiny/Manifest'
    mf_loc_base_url: str = 'https://www.bungie.net'
    mf_lang: str = 'en'
    api_key: str = 'd4705221d56b4040b8c5c6b4ebd58757'
    force_update: bool = True

    # ==== Local Filesystem Attributes ====

    mf_dir_path: Path = Path(__file__).resolve().parents[1] / 'manifest'
    mf_bak_ext: str = '.bak'

    # ==== Properties ====

    @property
    def expected_mf_name_template(self) -> Template:
        return Template(self._expected_mf_name_template_str)

    @property
    def expected_mf_name_regex(self) -> str:
        return self.expected_mf_name_template.substitute(
            starts_with=self.mf_starts_with,
            extension=self.mf_extension
        )

    # ==== Class Methods ====

    @classmethod
    def from_toml(cls, path: Path):
        data = toml.load(path)
        return cls(**data)

# ==== Instance Generation ====

settings: Settings = Settings.from_toml(
    Path(__file__).resolve().parent / "settings.toml"
)

sanity: Sanity = Sanity.from_toml(
    Path(__file__).resolve().parent / "sanity.toml"
)

# ==== TOML Regeneration ====

# import d2_project.core.utils.general as general_utils

"""
general_utils.regenerate_toml(
    data_class=settings,
    path=Path(__file__).resolve().parent / "settings.toml",
    exclude_fields=None
)
"""

"""
general_utils.regenerate_toml(
    data_class=sanity,
    path=Path(__file__).resolve().parent / "settings.toml",
    exclude_fields={'strict'}
)
"""
