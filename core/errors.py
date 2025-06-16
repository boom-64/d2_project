from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import core.schemas #Need to type-check exception arguments

class DownloadError(Exception):
    """
    Custom exception for exceptions which occur during a download.

    This exception is raised when a file fails to download. It includes
    the source URL of the download, whether or not the file is being 
    streamed, and the original exception.

    Attributes/args:
        url (schemas.ParsedURL): The source URL of the downloading file.
        stream (bool): Signifies whether or not the file was being 
            streamed. True for streaming; False for not.
        original_exception (Exception): The original exception.
    """
    def __init__(
        self, 
        *,
        url: core.schemas.ParsedURL, 
        stream: bool, 
        original_exception: Exception
    ):
        self.stream = stream
        self.original_exception = original_exception

        message = (
            f"Failed to download content from {url} "
            f"(stream={stream}): {original_exception}"
        )

        super().__init__(message)

class ChecksumMismatchError(Exception):
    """
    Custom exception for checksum mismatches.

    This exception is raised when a calculated checksum does not match 
    the expected checksum. It includes both the expected and actual 
    checksums.

    Attributes/args:
        expected (MD5Checksum): Expected checksum.
        computed (MD5Checksum): Actual checksum calculated.
    """
    expected: core.schemas.MD5Checksum
    computed: core.schemas.MD5Checksum

    def __init__(
        self,
        *,
        expected: core.schemas.MD5Checksum, 
        computed: core.schemas.MD5Checksum
    ) -> None:
        self.expected = expected
        self.computed = computed

        super().__init__(
            f"Checksum mismatch: expected {self.expected.val}, got "
            f"{self.computed.val}."
        )

class BungieAPIError(Exception):
        """
        Exception raised for errors returned by the Bungie API.

        This exception is intended to represent non-permission-related 
        errors in Bungie's API response.
        """ 
        def __init__(
            self,
            *,
            msg: str, 
            response_data: core.schemas.BungieResponseData | None = None
        ) -> None:
            """
            Initializes the APIError exception.

            Args:
                msg (str): Description of the error.
                response_data (BungieResponseData | None, optional): The
                    BungieResponseData instance related to this error.
            """
            if response_data:
                msg = f"{msg.rstrip()} Response data: '{response_data}'."
            
            super().__init__(msg)
