# ==== Local Modules ====

# import core.errors
# import core.validators

# import utils.general_utils
import utils.mf_utils

import config
# import sanity

# import schemas.general_schemas
import schemas.mf_schemas
# import schemas.sanity_checkers

# ==== Execution ====

mf_loc_data: schemas.mf_schemas.ManifestLocationData = (
    schemas.mf_schemas.ManifestLocationData(
        utils.mf_utils.request_bungie(
            url=config.settings.mf_finder_url,
            key=config.settings.api_key
        )
    )
)

installed_mf_data: schemas.mf_schemas.InstalledManifestData = (
    schemas.mf_schemas.InstalledManifestData()
)

if mf_loc_data.mf_name != installed_mf_data.name:
    installed_mf_data.update_manifest(mf_loc_data)

installed_mf_data.update_manifest(mf_loc_data)
