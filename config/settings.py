# ==== Standard Libraries ====

from dataclasses import dataclass
from pathlib import Path

# ==== Classes ====

@dataclass
class ManifestNameProperties:
    expected_mf_name_pattern = r"^world_sql_content_[a-fA-F0-9]{32}\.content$"
    extension = '.content'
    starts_with = 'world_sql_content_'

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
