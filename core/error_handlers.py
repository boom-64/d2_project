import core.errors

def bungie_error_code(code, msg, response_data) -> None:
        """
        Validates the error_code to determine if the response indicates success.

        Raises:
            PermissionError: If the error code indicates an API key issue.
            APIError: For other unexpected Bungie API errors.
        """
        if code != 1:
            if code in (2101, 2102):
                raise PermissionError(
                    f"Issue with the API key. Error code: {code}, "
                    f"error message: '{msg}'.")
            raise core.errors.APIError(
                msg="Unexpected Bungie API error.", 
                response_data=response_data
            )
