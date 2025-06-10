from pathlib import Path

import mf_utils
import utils
from schemas import URL

api_key = 'd4705221d56b4040b8c5c6b4ebd58757'
url_root = 'https://www.bungie.net'
loc_path = '/Platform/Destiny/Manifest'
lang = 'en'
expected_remote_lang_dir='/common/destiny_content/sqlite/'
zip_path = Path('manifest.zip')
mf_dir_path = Path('manifest')
mf_finder_url = URL(url=url_root, path=loc_path)
mf_ext='.content'
bak_ext='.bak'
mf_utils.update_manifest(
    key=api_key,
    dl_url_root=url_root,
    mf_finder_url=mf_finder_url,
    expected_remote_lang_dir=expected_remote_lang_dir,
    force_update=True,
    lang=lang,
    strict=True,
    zip_path=zip_path,
    mf_dir_path=mf_dir_path,
    mf_ext=mf_ext,
    bak_ext=bak_ext
)
