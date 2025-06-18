# ==== Local Modules ====

import core.errors
import schemas.general_schemas
import schemas.mf_schemas
import schemas.sanity_checkers
import core.validators
import utils.fs_utils
import utils.mf_utils
import config.sanity
import config.settings

data = schemas.mf_schemas.ManifestLocationData(
    utils.mf_utils.request_bungie(
        url=config.settings.Assumed.mf_finder_url,
        key=config.settings.Exposed.key
    )
)

print(data)
