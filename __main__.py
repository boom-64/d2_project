from __future__ import annotations

import utils.mf_utils

import config.settings

utils.mf_utils.update_manifest(
    remote_config=config.settings.REMOTE,
    remote_validation_config=config.settings.REMOTE_VALIDATION,
    local_config=config.settings.LOCAL,
    flags=config.settings.FLAGS
)
