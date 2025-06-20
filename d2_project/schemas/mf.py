from __future__ import annotations

# ==== Standard Libraries ====

from dataclasses import dataclass
from dataclasses import field
from json import JSONDecodeError
from types import MappingProxyType
from typing import TYPE_CHECKING

# ==== Local Modules ====

import d2_project.config.config as d2_project_config
import d2_project.core.utils.general as general_utils
import d2_project.core.utils.mf as mf_utils
import d2_project.core.validators as d2_project_validators
import d2_project.schemas.general as general_schemas

# ==== Type Checking ====

if TYPE_CHECKING:
    from typing import Any
    from requests.models import Response
    from pathlib import Path

# ==== Classes ====

@dataclass(frozen=True, init=False)
class BungieResponseData:
    _attrs_conversion = MappingProxyType({
        'error_code': 'ErrorCode',
        'throttle_seconds': 'ThrottleSeconds',
        'error_status': 'ErrorStatus',
        'message': 'Message',
        'message_data': 'MessageData',
        'response': 'Response'
    })

    error_code: int = field(init=False)
    throttle_seconds: int = field(init=False)
    error_status: str = field(init=False)
    message: str = field(init=False)
    message_data: dict[str, Any] = field(init=False)
    response: dict[str, Any] = field(init=False)

    # ==== Initialisation ====

    def __init__(self, raw_data: Response) -> None:
        """
        Initializes BungieResponseData by parsing and validating a
        requests.Response object.

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
                k: json_data[v] for k, v in self._attrs_conversion.items()
            }

            if (diff := set(json_data) - set(self._attrs_conversion.values())):
                raise ValueError(
                    "Unexpected components in response: " +
                    ", ".join(f"{k}={json_data[k]!r}" for k in diff)
                )

        except JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse json response: {e}"
            ) from e

        except KeyError as e:
            raise ValueError(
                f"Missing required field in response: {e}."
            ) from e

        for key, val in attrs.items():
            object.__setattr__(self, key, val)

        self._handle_error_code()

    # ==== Error Handling ====

    def _handle_error_code(self) -> None:
        """
        Validates the error_code to determine if the response indicates success.

        Raises:
            PermissionError: If the error code indicates an API key issue.
            self.APIError: For other unexpected Bungie API errors.
        """
        if self.error_code != 1:
            if self.error_code in (2101, 2102):
                raise PermissionError(
                    f"Issue with the API key. Error code: {self.error_code}, "
                    f"error message: '{self.message}'.")
            raise self.APIError(
                msg="Unexpected Bungie API error.",
                response_data=self
            )

    # ==== Custom Exceptions ====

    class APIError(Exception):
        """
        Exception raised for errors returned by the Bungie API.

        This exception is intended to represent non-permission-related
        errors in Bungie's API response.
        """
        def __init__(
            self,
            *,
            msg: str,
            response_data: 'BungieResponseData | None' = None
        ) -> None:
            """
            Initializes the APIError exception.

            Args:
                msg (str): Description of the error.
                response_data (core.schemas.BungieResponseData | None,
                optional): The BungieResponseData instance related to this
                    error.
            """
            if response_data:
                msg = f"{msg.rstrip()} Response data: '{response_data}'."

            super().__init__(msg)

@dataclass(frozen=True, init=False)
class ManifestLocationData(BungieResponseData):
    mf_remote_path: str = field(init=False)
    mf_url: str = field(init=False)
    mf_name: str = field(init=False)
    lang: str = field(init=False)

    # ==== Initialisation ====

    def __init__(self, raw_data: Response):
        super().__init__(raw_data)
        self._validate_response_structure()
        self._set_lang()
        self._extract_mf_path()
        d2_project_config.sanity.check_remote_mf_dir(
            remote_path=self.mf_remote_path
        )
        self._extract_mf_name()
        self._construct_mf_url()

    def _set_lang(self):
        object.__setattr__(self, 'lang', d2_project_config.settings.mf_lang)

    def _validate_response_structure(self):
        pass

    def _extract_mf_path(self):
        object.__setattr__(
            self,
            'mf_remote_path',
            self.response['mobileWorldContentPaths'][self.lang]
        )

    def _extract_mf_name(self):
        object.__setattr__(
            self,
            'mf_name',
            self.mf_remote_path.split('/')[-1]
        )

    def _construct_mf_url(self):
        object.__setattr__(
            self,
            'mf_url',
            general_schemas.ParsedURL.from_base_and_path(
                base_url=d2_project_config.settings.mf_loc_base_url,
                path=self.mf_remote_path
            )
        )

@dataclass(init=False)
class InstalledManifestData:
    name: str = field(init=False)
    path: Path = field(init=False)
    is_pattern_expected: bool = False
    extension: str = field(init=False)
    computed_checksum: general_schemas.MD5Checksum = field(init=False)
    expected_checksum: general_schemas.MD5Checksum = field(init=False)
    checksum_match: bool = field(init=False)

    # ==== Initialisation ====

    def __init__(self) -> None:
        self._find_and_set_path()
        self._extract_and_set_name()
        self._determine_pattern_expected()
        self._extract_and_set_extension()
        self._extract_and_set_expected_checksum()
        self._compute_and_set_computed_checksum()
        self._compute_and_set_checksum_match()

    def _find_and_set_path(self) -> None:
        if not (
            mf_dir_path := d2_project_config.settings.mf_dir_path
        ).is_dir():
            raise NotADirectoryError(
                f"{mf_dir_path} is not a directory"
            )

        mf_candidates: list[Path] = []
        for entry in d2_project_config.settings.mf_dir_path.iterdir():
            if (
                entry.suffix == (
                    d2_project_config.settings.mf_extension
                )
                and entry.is_file()
            ):
                mf_candidates.append(entry)

                # Raise early once more than one candidate found
                if len(mf_candidates) > 1:
                    raise FileExistsError(
                        f"Directory {d2_project_config.settings.mf_dir_path} "
                        f"contains too many compatible manifest files, "
                        f"including both {mf_candidates[0]} and "
                        f"{mf_candidates[1]}."
                    )

        # Returns None if no candidate found
        if not mf_candidates:
            object.__setattr__(self, 'path', None)
            return None

        # len(mf_candidates) == 1
        object.__setattr__(self, 'path', mf_candidates[0])

    def _extract_and_set_name(self) -> None:
        name: str | None = None

        if self.path:
            name = self.path.name

        object.__setattr__(self, 'name', name)

    def _determine_pattern_expected(self) -> None:
        if self.path:
            d2_project_validators.str_matches_pattern(
                value=self.name,
                stringpattern=d2_project_validators.FileNameStringPattern(
                    pattern=d2_project_config.settings.expected_mf_name_regex
                )
            )

            object.__setattr__(self, 'is_pattern_expected', True)

    def _extract_and_set_extension(self):
        extension: str | None = None
        if self.is_pattern_expected:
            extension = self.path.suffix
        object.__setattr__(self, 'extension', extension)

    def _extract_and_set_expected_checksum(self):
        expected_checksum: general_schemas.MD5Checksum | None = None
        expected_checksum_str: str

        if self.is_pattern_expected:
            expected_checksum_str = self.path.stem.split('_')[-1]
            expected_checksum = general_schemas.MD5Checksum(
                expected_checksum_str
            )
        elif self.path:
            expected_checksum_str = self.path.stem[-32:]

            d2_project_validators.str_matches_pattern(
                value=expected_checksum_str,
                stringpattern=d2_project_validators.lc_checksum_stringpattern
            )

            expected_checksum = general_schemas.MD5Checksum(
                expected_checksum_str
            )

        object.__setattr__(self, 'expected_checksum', expected_checksum)

    def _compute_and_set_computed_checksum(self):
        computed_checksum: general_schemas.MD5Checksum | None = None
        if self.path:
            computed_checksum = (
                general_schemas.MD5Checksum.calc(self.path)
            )
        object.__setattr__(self, 'computed_checksum', computed_checksum)

    def _compute_and_set_checksum_match(self):
        checksum_match: bool = False
        if self.expected_checksum and self.computed_checksum:
            if self.computed_checksum == self.expected_checksum:
                checksum_match = True
        object.__setattr__(self, 'checksum_match', checksum_match)

    # ==== Global Methods ====

    def update_manifest(
        self,
        mf_loc_data: ManifestLocationData,
        *,
        force_update: bool = False
    ) -> InstalledManifestData:
        bak_path: Path | None = general_utils.append_suffix(
                path=self.path,
                suffix=d2_project_config.settings.mf_bak_ext,
                overwrite=force_update
            ) if self.path else None

        try:
            mf_utils.dl_and_extract_mf_zip(
                url=general_schemas.ParsedURL.from_base_and_path(
                    base_url=d2_project_config.settings.mf_loc_base_url,
                    path=mf_loc_data.mf_remote_path
                ).url,
                mf_dir_path=d2_project_config.settings.mf_dir_path,
                mf_zip_structure=dict(
                    d2_project_config.settings.mf_zip_structure
                ),
            )

            files_to_keep: set[Path] = {(new_local_manifest := InstalledManifestData()).path}

            if bak_path is not None:
                files_to_keep.add(bak_path)

            general_utils.rm_sibling_files(
                files_to_keep=files_to_keep
            )

            return new_local_manifest

        except:
            if bak_path:
                general_utils.rm_sibling_files({bak_path})

                general_utils.rm_final_suffix(path=bak_path)

            return self
