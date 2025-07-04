"""Main script for testing."""

# ==== Local Modules ====

import d2_project.config.config as d2_project_config
import d2_project.core.utils.mf as mf_utils
import d2_project.schemas.mf as mf_schemas

# ==== Execution ====

mf_loc_data: mf_schemas.ManifestLocationData = mf_schemas.ManifestLocationData(
    mf_utils.request_bungie(
        url=d2_project_config.settings.mf_finder_url,
        key=d2_project_config.settings.api_key,
    ),
)

installed_mf_data: mf_schemas.InstalledManifestData = (
    mf_schemas.InstalledManifestData()
)

if mf_loc_data.remote_mf_name != (
    installed_mf_data.installed_mf_path.name
    if installed_mf_data.installed_mf_path is not None
    else None
):
    installed_mf_data.update_manifest(mf_loc_data)

elif d2_project_config.settings.force_update:
    installed_mf_data.update_manifest(mf_loc_data, force_update=True)
