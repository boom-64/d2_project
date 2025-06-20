# ==== Standard Libraries ====

from dataclasses import dataclass
from string import Template
from pathlib import Path
from types import MappingProxyType

# ==== Non-Standard Libraries ====

import toml

# ==== Local Modules ====

# import core.errors
# import core.manifest
import core.utils.general
#import core.utils.mf

# ==== Classes ====

@dataclass(frozen=True)
class Sanity:

    # ==== Flags ====

    strict: bool = False

    # ==== Remote Manifest Location Attributes ====

    expected_remote_lang_dir: str = '/common/destiny_content/sqlite/'

    # ==== Class Methods ====

    @classmethod
    def from_toml(cls, path: Path):
        data = toml.load(path)
        return cls(**data)

    # ==== Methods ====

    def check_remote_mf_dir(
        self,
        remote_path: str,
    ) -> None:
        if not remote_path.startswith(self.expected_remote_lang_dir):
            if self.strict:
                raise ValueError(
                    f"Invalid remote manifest format: '{remote_path}'. "
                    f"Bungie may have changed manifest path format."
                )

            print(f"{remote_path} != {self.expected_remote_lang_dir}")

    def disable_strict(self):
        object.__setattr__(self, 'strict', False)

@dataclass(frozen=True)
class Settings:

    # ==== Manifest Filename Attributes ====

    _expected_mf_name_template_str: str = '^${starts_with}[a-fA-F0-9]{32}${extension}$$'
    extension: str = '.content'
    starts_with: str = 'world_sql_content_'
    mf_zip_structure: MappingProxyType = MappingProxyType({
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

    mf_dir_path: Path = Path('manifest').resolve()
    mf_bak_ext: str = '.bak'

    # ==== Properties ====

    @property
    def expected_mf_name_template(self) -> Template:
        return Template(self._expected_mf_name_template_str)

    @property
    def expected_mf_name_regex(self) -> str:
        return self.expected_mf_name_template.substitute(
            starts_with=self.starts_with,
            extension=self.extension
        )

    # ==== Class Methods ====

    @classmethod
    def from_toml(cls, path: Path):
        data = toml.load(path)
        return cls(**data)

    # ==== Public Methods ====

settings: Settings = Settings.from_toml(Path('config/settings.toml'))
core.utils.general.regenerate_toml(
    data_class=settings,
    path=Path('settings.toml'),
    exclude_fields=None
)

sanity: Sanity = Sanity.from_toml(Path('config/sanity.toml'))
core.utils.general.regenerate_toml(
    data_class=sanity,
    path=Path("sanity.toml"),
    exclude_fields={'strict'}
)
