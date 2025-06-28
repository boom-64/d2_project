"""Schemas pertaining to manifest objects."""

from __future__ import annotations

# ==== Standard Libraries ====
from dataclasses import Field, dataclass, fields
from functools import cached_property
from typing import TYPE_CHECKING, Any, TypeVar, cast

# ==== Non-Standard Libraries ====
import langcodes

# ==== Local Modules ====
import d2_project.config.config as d2_project_config
import d2_project.core.errors as d2_project_errors
import d2_project.core.logger as d2_project_logger
import d2_project.core.utils.general as general_utils
import d2_project.core.utils.mf as mf_utils
import d2_project.core.validators as d2_project_validators
import d2_project.schemas.general as general_schemas

# ==== Type Checking ====
if TYPE_CHECKING:
    from logging import Logger
    from pathlib import Path

    from requests.models import Response

# ==== Logging Config ====
_logger: Logger = d2_project_logger.get_logger(__name__)

# ==== Local Variables ====
T = TypeVar("T")


# ==== Classes ===
@dataclass(frozen=True)
class BungieResponseData:
    """Class for handling Bungie response data.

    Attributes:
        raw_data (Response): Raw data from Bungie.

    Properties:
        error_code (int): Bungie error code.
        throttle_seconds (int): Throttle seconds from Bungie.
        error_status (str): Error message received.
        message (str): Message from Bungie.
        message_data (dict[str, Any]): Message data received.
        response (dict[str, Any]): Response data e.g. manifest location.

    """

    raw_data: Response

    class BungieResponseField[T]:  # pylint: disable=too-few-public-methods
        """Class for BungieResponseData fields."""

        def __init__(self, field_name: str, return_type: type[T]) -> None:
            """Initialise class."""
            self.field_name: str = field_name
            self.return_type: type[T] = return_type

        def __get__(
            self,
            obj: BungieResponseData | None,
            objtype: type[BungieResponseData] | None = None,
        ) -> T:
            """Get dunder method."""
            if obj is None:
                return self  # type: ignore[reportReturnType]
            try:
                return cast("T", obj.raw_data_as_json[self.field_name])
            except KeyError:
                _logger.exception(
                    "Missing field '%s' in Bungie response.",
                    self.field_name,
                )
                raise

    error_code = BungieResponseField(
        "ErrorCode",
        int,
    )
    throttle_seconds = BungieResponseField(
        "ThrottleSeconds",
        int,
    )
    error_status = BungieResponseField(
        "ErrorStatus",
        str,
    )
    message = BungieResponseField(
        "Message",
        str,
    )
    message_data = BungieResponseField(
        "MessageData",
        dict[str, Any],
    )
    response = BungieResponseField(
        "Response",
        dict[str, Any],
    )

    def __post_init__(self) -> None:
        """Post-initalisation tasks, specifically handling error_code."""
        self._handle_error_code(self.error_code)

    def _handle_error_code(self, error_code: int) -> None:
        """Determine if the response indicates success from error_code.

        Raises:
            PermissionError: If the error code indicates an API key issue.
            ValueError: For other unexpected Bungie API errors.

        """
        if error_code == 1:
            return

        if error_code in (2101, 2102):
            _logger.error(
                "Issue with the API key. Error code: %s, error message: '%s'",
                error_code,
                self.message,
            )
            raise PermissionError

        _logger.error(
            "Unknown Bungie API error. Error code: %s, Raw message data as"
            " json: %s.",
            error_code,
            self.raw_data_as_json,
        )
        raise ValueError

    @cached_property
    def raw_data_as_json(self) -> dict[str, Any]:
        """Convert raw data to dict."""
        json_data: dict[str, Any] = self.raw_data.json()
        diff: set[str] = set(json_data) - set(
            d2_project_config.sanity.expected_bungie_response_data_fields,
        )

        if not diff:
            return json_data

        _logger.exception(
            "Unexpected components in response: %s",
            ", ".join(f"{k}={json_data[k]!r}" for k in diff),
        )
        raise ValueError


@dataclass(frozen=True)
class ManifestLocationData(BungieResponseData):
    """Class for data pertaining to the latest manifest's location.

    Properties:
        mf_remote_path (str): Remote path to manifest.
        mf_url (str): URL to manifest.
        mf_name (str): Filename of manifest.

    """

    # ==== Initialisation ====

    def __post_init__(self) -> None:
        """Initialise class."""
        super().__post_init__()
        d2_project_config.sanity.check_remote_mf_dir(
            remote_path=self.remote_mf_path,
        )
        d2_project_validators.str_matches_pattern(
            value=self.remote_mf_name,
            pattern=d2_project_config.settings.expected_mf_name_regex,
            pattern_for="manifest file",
            log_func=_logger.exception,
        )

    def _get_delved_remote_mf_langs(self) -> dict[str, str]:
        response_delver: dict[str, Any] = self.response
        mf_response_structure = (
            d2_project_config.settings.mf_response_structure
        )
        key = cast(Field[Any], None)  # noqa: TC006
        try:
            for key in (fields(mf_response_structure))[:-1]:
                response_delver = response_delver[
                    getattr(
                        mf_response_structure,
                        key.name,
                    )
                ]

        except KeyError:
            missing_field_value: str = (
                getattr(mf_response_structure, key.name)
                if key
                else "<unknown>"
            )
            _logger.exception(
                "Missing required field in response: %s.",
                missing_field_value,
            )
            raise
        return response_delver

    @property
    def remote_mf_path(self) -> str:
        """Get remote manifest path."""
        delved_langs: dict[str, str] = self._get_delved_remote_mf_langs()
        desired_mf_lang: str = d2_project_config.settings.desired_mf_lang

        delved_remote_mf_path_key: str | None = (
            langcodes.closest_supported_match(
                desired_mf_lang,
                list(delved_langs.keys()),
            )
        )

        if delved_remote_mf_path_key is not None:
            return delved_langs[delved_remote_mf_path_key]

        _logger.error(
            "Manifest language '%s' (%s) currently unavailable. Available "
            "languages: %s.",
            desired_mf_lang,
            langcodes.Language.get(desired_mf_lang).display_name(),
            ", ".join(
                [
                    langcodes.Language.get(lang).display_name()
                    for lang in delved_langs
                ],
            ),
        )

        raise ValueError

    @property
    def remote_mf_name(self) -> str:
        """Get remote manifest name from path."""
        return self.remote_mf_path.split("/")[-1]

    @property
    def remote_mf_url(self) -> general_schemas.ParsedURL:
        """Construct URL from path."""
        return general_schemas.ParsedURL.from_base_and_path(
            base_url=d2_project_config.settings.mf_loc_base_url,
            path=self.remote_mf_path,
        )


@dataclass
class InstalledManifestData:
    """Dataclass for installed manifest data.

    Properties:
        installed_mf_path (Path | None): Path to installed manifest if one
            exists, else None.
        filename_pattern_expected (bool | None): Whether or not manifest name
            matches the expected filename pattern if manifest exists, else
            None.
        installed_mf_extension (str): Extension of installed manifest if one
            exists, else None.
        expected_checksum (schemas.general.MD5Checksum): Expected checksum from
            manifest filename if one exists, else None.
        computed_checksum (schemas.general.MD5Checksum): Checksum computed from
            manifest if file exists, else None
        checksum_match (bool): Whether expected_checksum matches
            computed_checksum if both exist, else None.

    """

    # ==== Properties ====
    @property
    def installed_mf_path(self) -> Path | None:
        """Get path to installed manifest if one exists.

        Raises:
            NotADirectoryError: _description_
            FileExistsError: _description_

        Returns:
            Path: Path to existing manifest if one exists.
            None: If no installed manifest exists.

        """
        mf_dir_path: Path = d2_project_config.settings.mf_dir_path

        mf_candidates: list[Path] = []
        for entry in mf_dir_path.iterdir():
            if (
                entry.suffix == (d2_project_config.settings.mf_extension)
                and entry.is_file()
            ):
                mf_candidates.append(entry)

                # Raise early once more than one candidate found
                if len(mf_candidates) > 1:
                    _logger.exception(
                        "Directory '%s contains too many manifest candidates, "
                        "including both '%s' and '%s'.",
                        mf_dir_path,
                        mf_candidates[0].name,
                        mf_candidates[1].name,
                    )
                    raise FileExistsError

        # Returns None if no candidate found
        if not mf_candidates:
            return None

        # Must have len(_mf_candidates) == 1
        return mf_candidates[0]

    @property
    def filename_pattern_expected(self) -> bool | None:
        """Whether or not filename pattern expected if mf exists else None.

        Returns:
            bool: If manifest exists, whether filename matches expected pattern
                listed in d2_project_config.settings.
            None: If manifest doesn't exist.

        """
        if self.installed_mf_path and self.installed_mf_path.name:
            try:
                return d2_project_validators.str_matches_pattern(
                    value=self.installed_mf_path.name,
                    pattern=d2_project_config.settings.expected_mf_name_regex,
                    pattern_for="(expected) manifest name",
                    log_func=_logger.exception,
                )
            except d2_project_errors.PatternMismatchError:
                return False
        return None

    @property
    def expected_checksum(self) -> general_schemas.MD5Checksum | None:
        """Get expected checksum for manifest if manifest exists.

        Returns:
            general_schemas.MD5Checksum: Expected checksum if manifest exists.
            None: Else None.

        """
        expected_checksum: general_schemas.MD5Checksum | None = None
        expected_checksum_str: str

        if self.installed_mf_path and self.filename_pattern_expected:
            expected_checksum_str = self.installed_mf_path.stem.split("_")[-1]
            expected_checksum = general_schemas.MD5Checksum(
                expected_checksum_str,
            )
        elif self.installed_mf_path:
            expected_checksum_str = self.installed_mf_path.stem[-32:]

            d2_project_validators.str_matches_pattern(
                value=expected_checksum_str,
                pattern=d2_project_validators.lc_checksum_pattern.pattern,
                pattern_for=d2_project_validators.lc_checksum_pattern.pattern_for,
                log_func=_logger.exception,
            )

            expected_checksum = general_schemas.MD5Checksum(
                expected_checksum_str,
            )

        return expected_checksum

    @property
    def computed_checksum(self) -> general_schemas.MD5Checksum | None:
        """Compute checksum if manifest exists else return None.

        Returns:
            general_schemas.MD5Checksum: Computed checksum for existing
                manifest.
            None: If none exists.\

        """
        if self.installed_mf_path:
            return general_schemas.MD5Checksum.calc(
                self.installed_mf_path,
            )
        return None

    @property
    def checksum_match(self) -> bool | None:
        """Get whether or not checksum matches expected.

        Returns:
            bool: If manifest exists, whether or not checksum matches expected.
            None: If no manifest exists.

        """
        if self.expected_checksum and self.computed_checksum:
            return self.computed_checksum == self.expected_checksum
        return None

    # ==== Global Methods ====

    def update_manifest(
        self,
        mf_loc_data: ManifestLocationData,
        *,
        force_update: bool = False,
    ) -> InstalledManifestData:
        """Update manifest if update required, or force if flag passed.

        Args:
            mf_loc_data (ManifestLocationData): Location data of remote
                manifest.
            force_update (bool, optional): Whether or not to force update
                (defaults to False).

        Returns:
            InstalledManifestData: Manifest data of old manifest if no update
                occured, else new manifest.

        """
        bak_path: Path | None = (
            general_utils.append_suffix(
                path=self.installed_mf_path,
                suffix=d2_project_config.settings.mf_bak_ext,
                overwrite=force_update,
            )
            if self.installed_mf_path
            else None
        )

        try:
            mf_utils.dl_and_extract_mf_zip(
                url=mf_loc_data.remote_mf_url.url,
                mf_dir_path=d2_project_config.settings.mf_dir_path,
                mf_zip_structure=d2_project_config.settings.mf_zip_structure.to_dict(),
            )
            new_local_manifest: InstalledManifestData = InstalledManifestData()
            files_to_keep: set[Path] = (
                {
                    new_local_manifest.installed_mf_path,
                }
                if new_local_manifest.installed_mf_path
                else set()
            )

            if bak_path is not None:
                files_to_keep.add(bak_path)

            general_utils.rm_sibling_files(
                files_to_keep=files_to_keep,
            )

        except:
            if bak_path:
                general_utils.rm_sibling_files({bak_path})

                general_utils.rm_final_suffix(path=bak_path)

            raise

        return new_local_manifest
