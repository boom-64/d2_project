# ==== Local Modules ====

# import core.errors
# import core.validators
# import core.utils.general
import core.utils.mf

import config.config
# import sanity

# import schemas.general_schemas
import schemas.mf
# import schemas.sanity_checkers

# ==== Execution ====

mf_loc_data: schemas.mf.ManifestLocationData = (
    schemas.mf.ManifestLocationData(
        core.utils.mf.request_bungie(
            url=config.config.settings.mf_finder_url,
            key=config.config.settings.api_key
        )
    )
)

installed_mf_data: schemas.mf.InstalledManifestData = (
    schemas.mf.InstalledManifestData()
)

if mf_loc_data.mf_name != installed_mf_data.name:
    installed_mf_data.update_manifest(mf_loc_data)

if config.config.settings.force_update:
    installed_mf_data.update_manifest(mf_loc_data, force_update=True)
