# ==== Standard Libraries ====

from dataclasses import dataclass
from dataclasses import field
from string import Template
from pathlib import Path

# ==== Classes ====

@dataclass(frozen=True)
class ManifestNameProperties:

    # ==== Initialised Attributes ====

    expected_mf_name_pattern: Template = Template(
        "^${starts_with}[a-fA-F0-9]${extension}$$"
    )
    extension: str = '.content'
    starts_with: str = 'world_sql_content_'

    # ==== Uninitialised Attributes ====

    expected_mf_name_regex: str = field(init=False)

    # ==== Post-Initialisation ====

    def __post_init__(self):
        self._set_expected_mf_name_pattern()

    # ==== Private Methods ====

    def _set_expected_mf_name_pattern(self):
        object.__setattr__(
            self,
            'expected_mf_name_regex',
            self.expected_mf_name_pattern.substitute(
                starts_with=self.starts_with,
                extension=self.extension
            )
        )

print(ManifestNameProperties())

@dataclass(frozen=True)
class Assumed:
    mf_finder_url = 'https://www.bungie.net/Platform/Destiny/Manifest'
    mf_base_url = 'https://www.bungie.net'

@dataclass(frozen=True)
class Exposed:
    lang = 'en'
    key = 'd4705221d56b4040b8c5c6b4ebd58757'
    mf_dir_path = Path('manifest').resolve()
    zip_path = Path('manifest.zip').resolve()
    bak_ext = '.bak'
