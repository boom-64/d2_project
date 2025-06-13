from pathlib import Path

from core.schemas import ParsedURL
from utils.mf_utils import update_manifest

update_manifest(
    key='d4705221d56b4040b8c5c6b4ebd58757',
    dl_url_root='https://www.bungie.net',
    mf_finder_url= ParsedURL.from_base_and_path(
        base_url='https://www.bungie.net', 
        path='/Platform/Destiny/Manifest'
    ),
    expected_remote_lang_dir='/common/destiny_content/sqlite/',
    force_update=True,
    lang='en',
    strict=True,
    zip_path=Path('manifest.zip').resolve(),
    mf_dir_path=Path('manifest').resolve(),
    mf_ext='.content',
    bak_ext='.bak'
)
