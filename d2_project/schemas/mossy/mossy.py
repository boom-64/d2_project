"""Mossy schemas."""

from __future__ import annotations

import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup

import d2_project.config.config as d2_project_config
import d2_project.core.logger as d2_project_logger
import d2_project.core.validators as d2_project_validators

if TYPE_CHECKING:
    from logging import Logger
    from typing import IO

_logger: Logger = d2_project_logger.get_logger(__name__)


@dataclass(frozen=True)
class CurrentMossyCSV:
    """Class for holding information about currently installed Mossy csv.

    Attributes:
        path (Path | None): Path to currently installed Mossy csv, if one
        exists, or None if none exists.

    """

    path: Path | None

    @property
    def current_ver(self) -> str | None:
        """Get current version code from self.path.

        Returns:
            str: current version code from self.path.
            None: If self.path == None.

        """
        if self.path is not None:
            return self.path.stem.split("_")[-1]
        return None

    @classmethod
    def from_dir(cls, mossy_csv_dir: Path) -> CurrentMossyCSV:
        """Generate class instance from Mossy CSV directory path.

        Args:
            mossy_csv_dir (Path): Path to Mossy CSV directory.

        Returns:
            CurrentMossyCSV: Class instance.

        Raises:
            FileExistsError: If too many compatible Mossy CSVs in dir.

        """
        candidates: list[Path] = [
            file
            for file in mossy_csv_dir.iterdir()
            if d2_project_validators.str_matches_pattern(
                value=file.name,
                pattern=(
                    d2_project_validators.mossy_csv_filename_pattern.pattern
                ),
            )
        ]

        if len(candidates) == 1:
            return cls(candidates[0])

        if len(candidates) == 0:
            return cls(None)

        _logger.error("Too many candidates: %s", candidates)
        raise FileExistsError

    def update_mossy_csv(
        self,
        *,
        force_update: bool = False,
    ) -> CurrentMossyCSV:
        """Update Mossy CSV.

        Args:
            force_update (bool): Whether or not to force CSV update.

        """
        target_path: Path | None = None

        find_title_response: requests.Response = requests.get(
            d2_project_config.settings.mossy_find_title_url,
            timeout=5,
        )

        title_tag = BeautifulSoup(
            find_title_response.text,
            "html.parser",
        ).find("title")

        if title_tag is None:
            _logger.error("No 'title' tag found in Sheets HTML.")

            raise ValueError

        ver_pattern: str = r"^v[1-9]\d*(\.[1-9]\d*)*$"
        words: list[str] = title_tag.text.split(" ")

        versions: list[str] = [
            word
            for word in words
            if re.fullmatch(ver_pattern, word) is not None
        ]

        if len(versions) > 1:
            _logger.error(
                "Title contains too many version-like strings: %s",
                versions,
            )

            raise ValueError

        latest_ver: str = versions[0]
        if self.current_ver != latest_ver or force_update:
            tmp: IO[bytes] | None = None  # Safe initialisation
            tmp_path: str | None = None  # Safe initialisation
            csv_export_url: str = (
                d2_project_config.settings.mossy_csv_export_url
            )

            response = requests.get(
                csv_export_url,
                timeout=5,
            )

            if not response.ok:
                _logger.error(
                    "Connection to '%s' failed. Error: %s",
                    csv_export_url,
                    response.status_code,
                )

                raise ConnectionError

            try:
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    delete=False,
                ) as tmp:
                    tmp_path = tmp.name
                    tmp.write(response.content)

                target_path = mossy_csv_dir / (
                    "mossy_csv_" + latest_ver + ".csv"
                )
                shutil.move(tmp_path, str(target_path))

            finally:
                if tmp_path is not None and Path(tmp_path).exists():
                    Path(tmp_path).unlink()

        return CurrentMossyCSV(target_path)


mossy_csv_dir = Path("d2_project/schemas/mossy")
current_mossy_csv = CurrentMossyCSV.from_dir(mossy_csv_dir)
current_mossy_csv.update_mossy_csv(force_update=True)
