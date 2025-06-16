from __future__ import annotations

from typing import TYPE_CHECKING

import core.errors # To raise custom errors

if TYPE_CHECKING:
    import core.schemas # To type check response data

def bungie_error_code(
    *,
    code: int,
    msg: str,
    response_data: core.schemas.BungieResponseData
) -> None:
    """
    Validates the error_code to determine if the response indicates success.

    Args:
        code (int): Error code provided by Bungie.
        msg (str): Error message provided by Bungie.
        response_data (core.schemas.BungieResponseData): Full Bungie
            response.

    Raises:
        PermissionError: If the error code indicates an API key issue.
        core.errors.BungieAPIError: For other unexpected Bungie API errors.
    """
    if code != 1:
        if code in (2101, 2102):
            raise PermissionError(
                f"Issue with the API key. Error code: {code}, "
                f"error message: '{msg}'.")
        raise core.errors.BungieAPIError(
            msg="Unexpected Bungie API error.",
            response_data=response_data
        )
