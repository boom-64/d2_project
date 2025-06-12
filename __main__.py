from pathlib import Path

from utils import mf_utils
from core import schemas 

api_key = 'd4705221d56b4040b8c5c6b4ebd58757'

url_root = 'https://www.bungie.net'
loc_path = '/Platform/Destiny/Manifest'
mf_finder_url = schemas.ParsedURL.from_base_and_path(
    base_url=url_root, 
    path=loc_path
)

lang = 'en'
expected_remote_lang_dir='/common/destiny_content/sqlite/'

zip_path = Path('manifest.zip')
mf_dir_path = Path('manifest')

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
