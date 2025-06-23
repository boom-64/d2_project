"""Generate configuration and sanity classes from TOML files.

This module contains configuration and sanity class definitions and
instances generated using their respective TOML files. These classes
are also capable of regenerating the TOML files by calling
utils.general.regenerate_toml() on a class instance which uses the class
defaults to regenerate a TOML file.
"""

# ==== Import Annotations From __future__ ====

from __future__ import annotations

# ==== Standard Library Imports ====
import re
import textwrap
from dataclasses import MISSING, dataclass, fields
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

# ==== Non-Standard Library Imports ====
import toml

# ==== Local Module Imports ====
import d2_project.core.errors as d2_project_errors

# ==== Dataclasses Needed For TypeAliases ====
# Cannot use TypeAliases from below here.


@dataclass(frozen=True)
class ManifestZipStructure:
    """Dataclass for manifest zip structure.

    Attributes:
        expected_file_count (int): Expected number of files in the archive.
        expected_dir_count (int): Expected number of directories in the
            archive.

    """

    expected_file_count: int
    expected_dir_count: int

    def to_dict(self) -> dict[str, int]:
        """Convert instance to dictionary.

        Returns:
            dict[str, int]: Dictionary of instance fields and values.

        """
        return {f.name: getattr(self, f.name) for f in fields(self)}


_manifest_zip_structure = ManifestZipStructure(
    expected_dir_count=0,
    expected_file_count=1,
)

# ==== Type Checking ====

if TYPE_CHECKING:
    # ==== Standard Library Imports ====

    from typing import Self, TypeAlias

    # ==== Custom TypeAlias Import ====

    TomlValue: TypeAlias = (
        bool | Path | int | float | str | ManifestZipStructure
    )


@dataclass(frozen=True)
class SettingsSanity:
    """Superclass for Settings and Sanity classes.

    This class is for sharing regenerate_toml() and related functions, as well
    as from_toml().
    """

    def regenerate_toml(
        self,
        path: Path,
        *,
        exclude_fields: set[str] | None = None,
    ) -> None:
        """Regenerate TOML file from class attribute defaults.

        This function regenerates a TOML file at the given path 'path' from
        the class's attribute defaults, ignoring fields with names listed
        in 'exclude_fields'. It serialises each field using
        _toml_serialise_value() and writes them to the path in a structured
        fstring format for TOML, overwriting any existing file of the same
        path.

        Args:
            path (Path): Path to TOML file to write to.
            exclude_fields (set[str] | None, optional): Optional set of
                fields to ignore. (defaults to None).

        """
        with Path.open(path, "w", encoding="utf-8") as toml_open:
            for field in fields(self):
                if exclude_fields is not None and field.name in exclude_fields:
                    continue

                serialised_lines: list[str] = [""]
                if field.default != MISSING:
                    serialised_lines = self._toml_serialise_value(
                        value=field.default,
                    ).splitlines()

                toml_open.write(f"# {field.name} = {serialised_lines[0]}\n")
                toml_open.writelines(
                    f"# {line}\n" for line in serialised_lines[1:]
                )

    def _needs_triple_quotes(self, s: str) -> bool:
        """Determine whether a string needs triple quotes.

        This function determines whether or not a string requires triple
        quotes for a TOML file.

        Args:
            s (str): String to check.

        Returns:
            bool: Whether the string contains the listed special
                characters.

        """
        special_chars: list[str] = ["\n", "\r", '"', "'"]

        return any(c in s for c in special_chars)

    def _is_bare_key(self, s: str) -> bool:
        """Determine whether a given key string is bare for TOML file.

        This function determines whether a key for a TOML file, passed as a
        string, is a fullmatch with a regex representing allowed characters
        in a TOML key. Returns True if key can be bare, otherwise returning
        False.

        Args:
            s (str): Key to be checked.

        Returns:
            bool: Whether the string can be used as a bare key.

        """
        return re.fullmatch(r"[A-Za-z0-9_-]+", s) is not None

    def _toml_serialise_value(self, value: TomlValue) -> str:
        """Serialise value for use in TOML file.

        This function converts values from attribute field defaults into
        strings for writing to a TOML file, converting types to usable TOML
        types in the process.

        Args:
            value (TomlValue): Value to serialise.

        Returns:
            str: Serialised value.

        """
        serialised: str = ""

        if isinstance(value, bool):
            serialised = "true" if value else "false"

        if isinstance(value, Path):
            serialised = f'"{value}"'

        if isinstance(value, (int, float)):
            serialised = str(value)

        if isinstance(value, str):
            if self._needs_triple_quotes(value):
                escaped: str = value.replace('"""', '\\"""')
                serialised = (
                    '"""\n' + textwrap.indent(escaped, "    ") + '\n"""'
                )
            else:
                serialised = f'"{value}"'

        # Must be ManifestZipStructure instance
        if isinstance(value, ManifestZipStructure):
            if not value:
                serialised = "{ }"
            else:
                parts: list[str] = []
                for attribute in fields(value):
                    key: str = (attribute_name := attribute.name)
                    if not self._is_bare_key(attribute_name):
                        key = f'"{attribute_name}"'
                    serialised_value_str: str = self._toml_serialise_value(
                        getattr(
                            value,
                            attribute.name,
                        ),
                    )
                    parts.append(
                        f"{key} = {serialised_value_str}",
                    )

                serialised = "{ " + ", ".join(parts) + " }"

        return serialised

    # ==== Class Methods ====

    @classmethod
    def from_toml(cls, path: Path) -> Self:
        """Generate config instance object from TOML file at 'path'.

        This function generates the 'sanity/settings' object for use
        across the project codebase. It returns a Sanity/Settings class
        instance with any attributes set in 'path' replacing the defaults
        of Sanity/Settings.

        Args:
            path (Path): Path to a configured TOML file.

        Returns:
            Sanity: The usable instance of Sanity.

        """
        data = toml.load(path)
        return cls(**data)


@dataclass(frozen=True)
class Sanity(SettingsSanity):
    """Class for generating 'sanity' object for sanity checking.

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

    expected_remote_lang_dir: str = "/common/destiny_content/sqlite/"

    # ==== Methods ====

    def check_remote_mf_dir(
        self,
        remote_path: str,
    ) -> None:
        """Sanity checker for remote manifest directory.

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
                raise d2_project_errors.ManifestRemotePathError(
                    path=remote_path,
                )

            print(f"{remote_path} != {self.expected_remote_lang_dir}")

    def disable_strict(self) -> None:
        """Set Sanity instance attribute 'strict' to False."""
        object.__setattr__(self, "strict", False)


@dataclass(frozen=True)
class Settings(SettingsSanity):
    """Class for generating 'settings' object for sanity checking.

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
        mf_finder_url (url): Bungies manifest finder URL.
        mf_loc_base_url (str): Base URL for manifest location.
        mf_lang (str): Desired manifest language.
        api_key (str): API key.
        force_update (bool): Whether to force manifest update.
        mf_dir_path (Path): Path to manifest directory.
        mf_bak_ext (str): Backup manifest file extension.

    Properties:
        expected_mf_name_template (Template): Template for expected
            manifest name format.
        expected_mf_name_regex (str): Template with substituted values.

    Class methods:
        from_toml(): Generator for 'sanity: Sanity' object.

    """

    # ==== Private Manifest Filename Attributes ====

    _expected_mf_name_template_str: str = (
        "^${starts_with}[a-fA-F0-9]{32}${extension}$$"
    )

    # ==== Public Manifest Filename Attributes

    mf_extension: str = ".content"
    mf_starts_with: str = "world_sql_content_"
    mf_zip_structure: ManifestZipStructure = _manifest_zip_structure

    # ==== Bungie Request Attributes ====

    mf_finder_url: str = "https://www.bungie.net/Platform/Destiny/Manifest"
    mf_loc_base_url: str = "https://www.bungie.net"
    mf_lang: str = "en"
    api_key: str = "d4705221d56b4040b8c5c6b4ebd58757"
    force_update: bool = True

    # ==== Local Filesystem Attributes ====

    mf_dir_path: Path = Path(__file__).resolve().parents[1] / "manifest"
    mf_bak_ext: str = ".bak"

    # ==== Properties ====

    @property
    def expected_mf_name_template(self) -> Template:
        """Converts _expected_mf_name_template_str to Template.

        This function converts the configurable
        _expected_mf_name_template_str attribute to a Template object for
        substitution with expected_mf_name_regex().

        Returns:
            Template: Template for expected manifest filename.

        """
        return Template(self._expected_mf_name_template_str)

    @property
    def expected_mf_name_regex(self) -> str:
        """Substitutes template with configurable extension and start.

        This function substitutes mf_extension and mf_starts_with into the
        Template from expected_mf_name_template().

        Returns:
            str: Regular expression for expected manfifest filename
                structure.

        """
        return self.expected_mf_name_template.substitute(
            starts_with=self.mf_starts_with,
            extension=self.mf_extension,
        )


# ==== Instance Generation ====

settings: Settings = Settings.from_toml(
    Path(__file__).resolve().parent / "settings.toml",
)

sanity: Sanity = Sanity.from_toml(
    Path(__file__).resolve().parent / "sanity.toml",
)

# ==== TOML Regeneration ====
"""
sanity_toml: Path = Path(__file__).resolve().parent / "sanity.toml"
settings_toml: Path = Path(__file__).resolve().parent / "settings.toml"
settings.regenerate_toml(settings_toml,)
sanity.regenerate_toml(sanity_toml, exclude_fields={'strict'},)
"""
