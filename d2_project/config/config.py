"""Generate configuration and sanity classes from TOML files.

This module contains Settings and Sanity class definitions and instances
generated using their respective TOML files. These classes are also capable of
regenerating the TOML files by calling self.regenerate_toml() which uses the
class defaults to regenerate a TOML file.
"""

# ==== Import Annotations From __future__ ====
from __future__ import annotations

# ==== Standard Library Imports ====
from dataclasses import MISSING, dataclass, fields
from functools import cached_property
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

# ==== Non-Standard Library Imports ====
import toml

# ==== Local Module Imports ====
import d2_project.core.errors as d2_project_errors
import d2_project.core.logger as d2_project_logger
import d2_project.core.validators as d2_project_validators

# ==== Type Checking ====
if TYPE_CHECKING:
    from logging import Logger
    from typing import Any

# ==== Logging Config ====
_logger: Logger = d2_project_logger.get_logger(__name__)


# ==== Dataclasses Needed For TypeAliases ====
@dataclass(frozen=True)
class _CustomDictStructure:
    """Parent class for custom dict structures for method sharing."""

    def to_dict(self) -> dict[str, int]:
        """Convert instance to dictionary.

        Returns:
            dict[str, int]: Dictionary of instance fields and values.

        """
        return {f.name: getattr(self, f.name) for f in fields(self)}


# ==== Type Checking ====
if TYPE_CHECKING:
    # ==== Standard Library Imports ====
    from typing import Self, TypeAlias

    # ==== Custom TypeAlias Import ====
    # Values to convert to and from TOML files.
    TomlValue: TypeAlias = (
        bool
        | Path
        | int
        | float
        | str
        | tuple[str, ...]
        | _CustomDictStructure
    )


# ==== Dataclasses ====
@dataclass(frozen=True)
class ConfigSuperclass:
    """Superclass for Settings and Sanity classes.

    This class is for sharing regenerate_toml() and related functions, as well
    as from_toml().

    Attributes:
        _exclude_fields_from_toml (tuple[str, ...]): Placeholder for fields to
            be excluded from generated toml.

    """

    _exclude_fields_from_toml: tuple[str, ...] = ()

    def regenerate_toml(
        self,
        path: Path,
    ) -> None:
        """Regenerate TOML file from class attribute defaults.

        This function regenerates a TOML file at the given path 'path' from
        the class's attribute defaults, ignoring fields with names listed
        in 'self.exclude_fields'. It serialises each field using
        self._toml_serialise_value() and writes them to the path in a
        structured fstring format for TOML, overwriting any existing file of
        the same path.

        Args:
            path (Path): Path to TOML file to write to.

        """
        with Path.open(path, "w", encoding="utf-8") as toml_open:
            for field in fields(self):
                _exclude_fields_from_toml: tuple[str, ...] = (
                    self._exclude_fields_from_toml
                )
                if (
                    _exclude_fields_from_toml
                    and field.name in _exclude_fields_from_toml
                ):
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

    def _is_bare_key(self, s: str) -> bool:
        """Determine whether a given key string is bare for TOML file.

        This function determines whether a key for a TOML file, passed as a
        string, is a fullmatch with a regex representing allowed characters
        in a TOML key. Returns True if key can be bare, otherwise returning
        False.

        Args:
            s (str): Key to be checked.

        Returns:
            bool: Whether or not the string can be used as a bare key.

        """
        try:
            toml_bare_key_pattern: d2_project_validators.ComparePattern = (
                d2_project_validators.toml_bare_key_pattern
            )
            return d2_project_validators.str_matches_pattern(
                value=s,
                pattern=toml_bare_key_pattern.pattern,
                pattern_for=toml_bare_key_pattern.pattern_for,
                log_func=None,
            )
        except d2_project_errors.PatternMismatchError:
            return False

    def _toml_serialise_string_value(self, string_value: str) -> str:
        """Serialise string for use in TOML file.

        Args:
            string_value (str): Value to serialise.

        Returns:
            str: Serialised value.

        """
        needs_triple_quotes_pattern = (
            d2_project_validators.toml_needs_triple_quotes_pattern
        )

        try:
            d2_project_validators.str_matches_pattern(
                value=string_value,
                pattern=needs_triple_quotes_pattern.pattern,
                pattern_for=needs_triple_quotes_pattern.pattern_for,
                log_func=None,
            )

        except d2_project_errors.PatternMismatchError:
            return f'"{string_value}"'

        escaped = string_value.replace('"""', '\\"""')
        indented = "\n".join("    " + line for line in escaped.splitlines())
        return '"""\n' + indented + '\n"""'

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
        serialised: str

        match value:
            case bool():
                serialised = "true" if value else "false"

            case Path():
                serialised = f'"{value}"'

            case int() | float():
                serialised = str(value)

            case str():
                serialised = self._toml_serialise_string_value(value)

            case _CustomDictStructure() if not value:
                serialised = "{ }"

            case _CustomDictStructure():
                parts: list[str] = []

                for attribute in fields(value):
                    attribute_name: str = attribute.name

                    key: str = attribute_name
                    if not self._is_bare_key(attribute_name):
                        key = f'"{attribute_name}"'

                    serialised_value_str: str = self._toml_serialise_value(
                        getattr(value, attribute.name),
                    )

                    parts.append(f"{key} = {serialised_value_str}")

                serialised = "{ " + ", ".join(parts) + " }"

            case _:
                # Default case for sequences/iterables
                serialised_str_list: list[str] = [
                    self._toml_serialise_string_value(entry) for entry in value
                ]
                serialised = (
                    "[\n  " + ",\n  ".join(serialised_str_list) + ",\n]"
                )

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
            SettingsSanity: The usable instance of Settings or Sanity.

        """
        if not path.is_file():
            instance = cls()
            instance.regenerate_toml(path)
            return instance
        data = toml.load(path)
        dataclass_mappings: dict[
            str,
            type[_ManifestZipStructure | _ManifestResponseStructure],
        ] = {
            "mf_zip_structure": _ManifestZipStructure,
            "mf_response_structure": _ManifestResponseStructure,
        }
        for key, dataclass_type in dataclass_mappings.items():
            if key in data and isinstance(data[key], dict):
                data[key] = dataclass_type(**data[key])

        return cls(**data)


# ==== Sanity Class ====


@dataclass(frozen=True)
class Sanity(ConfigSuperclass):
    """Class for generating 'sanity' object for sanity checking.

    This class is used to generate a 'sanity' object for use across the
    program with callable sanity checkers for each non-flag attribute.

    The class instance should be generated using 'SettingsSanity.from_toml()'
    with one positional arg being the path to a TOML file, by default
    'sanity.toml' in the same directory as this file. Attributes can be set
    in the TOML file to overwrite the defaults listed here.

    Attributes:
        _exclude_fields_from_toml (tuple[str, ...]): Excluded fields from TOML.
        strict (bool): Whether the sanity checkers should raise or log and
            silently fail.
        expected_remote_lang_dir (str): The expected remote path of the
            language directory each containing a manifest location.
        expected_bungie_response_data_fields (tuple[str, ...]): The expected
            fields in Bungie response.

    """

    # ==== Excluded Fields From TOML ====
    _exclude_fields_from_toml: tuple[str, ...] = (
        "_exclude_fields_from_toml",
        "strict",
    )
    # ==== Flags ====
    strict: bool = False

    # ==== Remote Manifest Location Attributes ====
    expected_remote_lang_dir: str = "/common/destiny_content/sqlite/"
    expected_bungie_response_data_fields: tuple[str, ...] = (
        "ErrorCode",
        "ThrottleSeconds",
        "ErrorStatus",
        "Message",
        "MessageData",
        "Response",
    )

    # ==== Post-Initialisation ====
    def __post_init__(self) -> None:
        """Post-initialisation."""
        d2_project_validators.str_matches_pattern(
            value=self.expected_remote_lang_dir,
            pattern=d2_project_validators.url_path_pattern.pattern,
            pattern_for=d2_project_validators.url_path_pattern.pattern_for,
            log_func=_logger.exception,
        )

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
        clean_erld: str = "/" + self.expected_remote_lang_dir.strip("/") + "/"
        if not remote_path.startswith(clean_erld):
            _logger.warning(
                "Unexpected remote manifest path format: '%s'. Bungie may have"
                " changed manifest path format from '%s/$MANIFEST_NAME'.",
                remote_path,
                clean_erld,
            )

            if self.strict:
                raise ValueError

    def check_extra_bungie_response_fields(
        self,
        json_data: dict[str, Any],
    ) -> None:
        """Check for extra fields in Bungie response.

        Args:
            json_data (dict[str, Any]): Bungie response JSON data.

        """
        diff: set[str] = set(json_data) - set(
            self.expected_bungie_response_data_fields,
        )

        if diff:
            _logger.exception(
                "Unexpected components in response: %s",
                ", ".join(f"{k}={json_data[k]!r}" for k in diff),
            )
            raise ValueError

    def disable_strict(self) -> None:
        """Set Sanity instance attribute 'strict' to False."""
        object.__setattr__(self, "strict", False)


# ==== Settings Attribute Classes ====


@dataclass(frozen=True)
class _ManifestZipStructure(_CustomDictStructure):
    """Dataclass for manifest zip structure.

    Attributes:
        expected_file_count (int): Expected number of files in the archive.
        expected_dir_count (int): Expected number of directories in the
            archive.

    """

    expected_file_count: int
    expected_dir_count: int


@dataclass(frozen=True)
class _ManifestResponseStructure(_CustomDictStructure):
    """Dataclass for manifest response structure.

    Attributes:
        keyX: Dict keys parents to children

    """

    key_0: str
    key_1: str


_default_manifest_zip_structure: _ManifestZipStructure = _ManifestZipStructure(
    expected_file_count=1,
    expected_dir_count=0,
)

_default_mf_response_structure: _ManifestResponseStructure = (
    _ManifestResponseStructure(
        key_0="mobileWorldContentPaths",
        key_1="$desired_mf_lang",
    )
)
# ==== Settings Class ====


@dataclass(frozen=True)
class Settings(ConfigSuperclass):  # pylint: disable=too-many-instance-attributes
    """Class for generating 'settings' object for sanity checking.

    This class is used to generate a 'settings' object for use across the
    program.

    The class instance should be generated using 'SettingsSanity.from_toml()'
    with one positional arg being the path to a TOML file, by default
    'settings.toml' in the same directory as this file. Attributes can be set
    in the TOML file to overwrite the defaults listed here.

    Attributes:
        _exclude_fields_from_toml (tuple[str, ...]): Fields to exclude from
            TOML.
        _expected_mf_name_template_str (str): Converted Template object for
            use in Settings.expected_mf_name_template().
        desired_mf_lang (str): Desired manifest language.
        mf_extension (str): Manifest filename extension.
        mf_starts_with (str): Manifest filename start.
        mf_zip_structure (_ManifestZipStructure): Zip structure of Bungie's
            manifest archive.
        mf_finder_url (url): Bungies manifest finder URL.
        mf_loc_base_url (str): Base URL for manifest location.
        _mf_response_structure (_ManifestResponseStructure): Response
            structure.
        force_update (bool): Whether to force manifest update.
        _api_key_path_str (str): Path to API key TOML file.
        _mf_dir_path (str): Path to manifest directory as str.
        mf_bak_ext (str): Backup manifest file extension.

    """

    # ==== TOML-Excluded Fields ====
    _exclude_fields_from_toml: tuple[str, ...] = tuple(
        "exclude_fields_from_toml",
    )
    # ==== Private Manifest Filename Attributes ====
    _expected_mf_name_template_str: str = (
        "^${starts_with}[a-fA-F0-9]{32}${extension}$$"
    )
    desired_mf_lang: str = "en"

    # ==== Public Manifest Filename Attributes
    mf_extension: str = ".content"
    mf_starts_with: str = "world_sql_content_"
    mf_zip_structure: _ManifestZipStructure = _default_manifest_zip_structure

    # ==== Bungie Request Attributes ====
    mf_finder_url: str = "https://www.bungie.net/Platform/Destiny2/Manifest"
    mf_loc_base_url: str = "https://www.bungie.net"
    _mf_response_structure: _ManifestResponseStructure = (
        _default_mf_response_structure
    )
    force_update: bool = True

    # ==== Local Filesystem Attributes ====
    _api_key_path_str: str = str(
        Path(__file__).resolve().parents[1] / "api_key.toml",
    )
    _mf_dir_path: str = str(Path(__file__).resolve().parents[1] / "manifest")
    mf_bak_ext: str = ".bak"

    # ==== Post-Initialisation ====
    def __post_init__(self) -> None:
        """Post-initialisation."""
        for suffix in (self.mf_extension, self.mf_bak_ext):
            d2_project_validators.str_is_valid_suffix(
                value=suffix,
                log_func=_logger.exception,
            )
        for url in (self.mf_finder_url, self.mf_loc_base_url):
            d2_project_validators.str_is_valid_url(url)
        if not self.mf_dir_path.is_dir():
            _logger.critical(
                "Configured 'mf_dir_path='%s' is not a directory.",
                self.mf_dir_path,
            )
            raise NotADirectoryError

    # ==== Properties ====

    @cached_property
    def _api_key_path(self) -> Path:
        """Convert _api_key_path_str to Path object.

        Returns:
            Path: Path to API key TOML.

        """
        return Path(self._api_key_path_str)

    @cached_property
    def api_key(self) -> str:
        """Return API key from _api_key_path.

        Returns:
            str: API key string.

        """
        api_key_path: Path = self._api_key_path
        try:
            data: dict[str, str] = toml.load(api_key_path)
            return data["api_key"]
        except:
            _logger.exception(
                "Failed to read API key from path '%s'.",
                api_key_path,
            )
            raise

    @cached_property
    def _expected_mf_name_template(self) -> Template:
        """Converts _expected_mf_name_template_str to Template.

        This function converts the configurable
        _expected_mf_name_template_str attribute to a Template object for
        substitution with expected_mf_name_regex().

        Returns:
            Template: Template for expected manifest filename.

        """
        return Template(self._expected_mf_name_template_str)

    @cached_property
    def expected_mf_name_regex(self) -> str:
        """Substitutes template with configurable extension and start.

        This function substitutes mf_extension and mf_starts_with into the
        Template from _expected_mf_name_template().

        Returns:
            str: Regular expression for expected manfifest filename
                structure.

        """
        return self._expected_mf_name_template.substitute(
            starts_with=self.mf_starts_with,
            extension=self.mf_extension,
        )

    @cached_property
    def mf_response_structure(self) -> _ManifestResponseStructure:
        """Substitute and return _mf_response_structure.

        Returns:
            _ManifestResponseStructure: Subsitituted Manifest response
                structure.

        """
        return _ManifestResponseStructure(
            key_0=self._mf_response_structure.key_0,
            key_1=Template(self._mf_response_structure.key_1).substitute(
                desired_mf_lang=self.desired_mf_lang,
            ),
        )

    @cached_property
    def mf_dir_path(self) -> Path:
        """Return Path(self._mf_dir_path).

        Returns:
            Path: Path object from _mf_dir_path.

        """
        return Path(self._mf_dir_path)


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
settings.regenerate_toml(settings_toml)
sanity.regenerate_toml(
    sanity_toml,
)
"""
