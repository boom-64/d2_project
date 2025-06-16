from dataclasses import dataclass, field
from pathlib import Path

import core.schemas

@dataclass
class RemoteConfig:
    key: str
    lang: str
    mf_finder_path: str
    base_url: core.schemas.ParsedURL
    mf_ext: str
    mf_finder_url: core.schemas.ParsedURL = field(init=False) 

    def __post_init__(self):
        self._tidy_attrs()
        self._gen_mf_finder_url()

    def _tidy_attrs(self):
        self.key = self.key.strip()
        self.lang = self.lang.strip()
        self.mf_ext = self.mf_ext.strip()
        self.mf_finder_path = self.mf_finder_path.strip().strip('/')

    def _gen_mf_finder_url(self):
        self.mf_finder_url = core.schemas.ParsedURL.from_base_and_path(
            base_url=self.base_url.url, path=self.mf_finder_path
        )

@dataclass
class LocalConfig:
    mf_dir_path: Path
    zip_path: Path
    bak_ext: str

@dataclass
class Flags:
    strict: bool = True
    force_update: bool = False

@dataclass
class RemoteValidationConfig:
    expected_remote_lang_dir: str
    expected_mf_ext: str

#------------------------------------------------------------------------------

LOCAL = LocalConfig(
    mf_dir_path=Path('manifest').resolve(),
    zip_path=Path('manifest.zip').resolve(),
    bak_ext='.bak'
)

REMOTE = RemoteConfig(
    key='d4705221d56b4040b8c5c6b4ebd58757',
    mf_finder_path='Platform/Destiny/Manifest',
    base_url=core.schemas.ParsedURL.from_full_url('https://www.bungie.net'),
    lang='en',
    mf_ext='.content'
)

REMOTE_VALIDATION = RemoteValidationConfig(
    expected_mf_ext='.content',
    expected_remote_lang_dir='/common/destiny_content/sqlite/'
)
FLAGS = Flags(
    strict=True,
    force_update=True
)
