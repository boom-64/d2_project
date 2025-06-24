"""Schemas pertaining to manifest objects."""

from __future__ import annotations

# ==== Standard Libraries ====
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

# ==== Local Modules ====
import d2_project.config.config as d2_project_config
import d2_project.core.errors as d2_project_errors
import d2_project.core.utils.general as general_utils
import d2_project.core.utils.mf as mf_utils
import d2_project.core.validators as d2_project_validators
import d2_project.schemas.general as general_schemas

# ==== Type Checking ====

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from requests.models import Response

# ==== Local Variables ====
_bungie_response_data_attrs_conversion = {
    "error_code": "ErrorCode",
    "throttle_seconds": "ThrottleSeconds",
    "error_status": "ErrorStatus",
    "message": "Message",
    "message_data": "MessageData",
    "response": "Response",
}

# ==== Classes ===


@dataclass(frozen=True, init=False)
class BungieResponseData:
    """Custom class for response from Bungie.

    Attributes:
        _attrs_conversion ()
        error_code (int): Error code supplied by Bungie.
        throttle_seconds (int): Rate-limiting info.
        error_status (str): Error status supplied by Bungie.
        message (str): Error message received from Bungie.
        message_data (str): Message data from Bungie.
        response (dict[str, any]): Response data.

    """

    error_code: int = field(init=False)
    throttle_seconds: int = field(init=False)
    error_status: str = field(init=False)
    message: str = field(init=False)
    message_data: dict[str, Any] = field(init=False)
    response: dict[str, Any] = field(init=False)

    # ==== Initialisation ====

    def __init__(self, raw_data: Response) -> None:
        """Initialize BungieResponseData by parsing and validating response.

        Args:
            raw_data (Response): The raw response object returned by
                'requests.get()'.

        Raises:
            ValueError: If the JSON decoding fails, required fields are
                missing, or unexpected fields are present in the response.
            KeyError:
            ValueError:

        """
        try:
            json_data = raw_data.json()
            attrs = {
                k: json_data[v]
                for k, v in (_bungie_response_data_attrs_conversion.items())
            }

            if diff := set(json_data) - set(
                _bungie_response_data_attrs_conversion.values(),
            ):
                raise ValueError(
                    "Unexpected components in response: "
                    + ", ".join(f"{k}={json_data[k]!r}" for k in diff),
                )

        except KeyError as e:
            raise d2_project_errors.MissingBungieResponseFieldError(e) from e

        for key, val in attrs.items():
            object.__setattr__(self, key, val)

        self._handle_error_code()

    # ==== Error Handling ====

    def _handle_error_code(self) -> None:
        """Determine if the response indicates success from error_code.

        Raises:
            PermissionError: If the error code indicates an API key issue.
            self.APIError: For other unexpected Bungie API errors.

        """
        if self.error_code != 1:
            if self.error_code in (2101, 2102):
                raise d2_project_errors.APIPermissionError(
                    error_code=self.error_code,
                    error_message=self.message,
                )
            raise d2_project_errors.UnknownAPIError(response_data=self)


@dataclass(frozen=True, init=False)
class ManifestLocationData(BungieResponseData):
    """Class for data pertaining to the latest manifest's location.

    Attributes:
        mf_remote_path (str): Remote path to manifest.
        mf_url (str): URL to manifest.
        mf_name (str): Filename of manifest.
        lang (str): Language of manifest.

    """

    mf_remote_path: str = field(init=False)
    mf_url: str = field(init=False)
    mf_name: str = field(init=False)
    lang: str = field(init=False)

    # ==== Initialisation ====

    def __init__(self, raw_data: Response) -> None:
        """Initialise class."""
        super().__init__(raw_data)
        self._validate_response_structure()
        self._set_lang()
        self._extract_mf_path()
        d2_project_config.sanity.check_remote_mf_dir(
            remote_path=self.mf_remote_path,
        )
        self._extract_mf_name()
        self._construct_mf_url()

    def _set_lang(self) -> None:
        object.__setattr__(self, "lang", d2_project_config.settings.mf_lang)

    def _validate_response_structure(self) -> None:
        pass

    def _extract_mf_path(self) -> None:
        object.__setattr__(
            self,
            "mf_remote_path",
            self.response["mobileWorldContentPaths"][self.lang],
        )

    def _extract_mf_name(self) -> None:
        object.__setattr__(
            self,
            "mf_name",
            self.mf_remote_path.split("/")[-1],
        )

    def _construct_mf_url(self) -> None:
        object.__setattr__(
            self,
            "mf_url",
            general_schemas.ParsedURL.from_base_and_path(
                base_url=d2_project_config.settings.mf_loc_base_url,
                path=self.mf_remote_path,
            ),
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
        mf_candidates: list[Path] = []
        for entry in d2_project_config.settings.mf_dir_path.iterdir():
            if (
                entry.suffix == (d2_project_config.settings.mf_extension)
                and entry.is_file()
            ):
                mf_candidates.append(entry)

                # Raise early once more than one candidate found
                if len(mf_candidates) > 1:
                    raise d2_project_errors.TooManyManifestsError(
                        mf_dir_path=d2_project_config.settings.mf_dir_path,
                        mf_candidates=mf_candidates,
                    )

        # Returns None if no candidate found
        if not mf_candidates:
            return None

        # Must have len(mf_candidates) == 1
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

        if self.installed_mf_path and self.filename_pattern_expected:  # pyright: ignore[reportUnnecessaryComparison]
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
                url=general_schemas.ParsedURL.from_base_and_path(
                    base_url=d2_project_config.settings.mf_loc_base_url,
                    path=mf_loc_data.mf_remote_path,
                ).url,
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

        else:
            return new_local_manifest
