# ==== Local Modules ====

# import core.errors
# import core.validators

import utils.general_utils
import utils.mf_utils

import config.settings
# import config.sanity

import schemas.general_schemas
import schemas.mf_schemas
# import schemas.sanity_checkers

# ==== Execution ====

mf_loc_data: schemas.mf_schemas.ManifestLocationData = (
    schemas.mf_schemas.ManifestLocationData(
        utils.mf_utils.request_bungie(
            url=config.settings.Assumed.mf_finder_url,
            key=config.settings.Exposed.key
        )
    )
)

installed_mf_data: schemas.mf_schemas.InstalledManifestData = (
    schemas.mf_schemas.InstalledManifestData()
)

print(installed_mf_data)

utils.mf_utils.dl_mf_zip(
    zip_path=config.settings.Exposed.zip_path,
    url=schemas.general_schemas.ParsedURL.from_base_and_path(
        base_url=config.settings.Assumed.mf_base_url,
        path=mf_loc_data.mf_remote_path
    ).url
)
"""
utils.general_utils.extract_zip(
    zip_path=config.settings.Exposed.zip_path,
    extract_to=config.settings.Exposed.mf_dir_path,
    expected_dir_count=0,
    expected_file_count=1,
)
"""
