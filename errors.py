import schemas

class BungieAPIError(Exception):
    """
    Custom exception for errors returned by the Bungie API.

    This exception is raised when an error occurs while interacting with 
    the Bungie API. It includes an optional error code returned by the 
    API to help identify the issue.

    Attributes:
        error_code (int | None): Optional error code provided by the Bungie 
            API.

    Args:
        message (str): Human-readable description of the error.
        error_code (int | None, optional): Numeric code representing the 
            error, if available.
    """ 
    def __init__(self, message: str, error_code: int | None = None) -> None:
        super().__init__(message)

        self.error_code = error_code

class ChecksumMismatchError(Exception):
    """
    Custom exception for checksum mismatches.

    This exception is raised when a calculated checksum does not match the
    expected checksum. It includes both the expected and actual checksums.

    Attributes:
        expected (str): Expected checksum.
        actual (str): Actual checksum calculated.
    Args:
        expected (str): The expected checksum value.
        actual (str): The actual checksum that was calculated.   """
    def __init__(self, expected: str, actual: str) -> None:
        self.expected = expected
        self.actual = actual

        message = f"Checksum mismatch: expected {expected}, got {actual}"
        super().__init__(message)

class DownloadError(Exception):
    """
    Custom exception for exceptions which occur during a download.

    This exception is raised when a file fails to download. It includes
    the source URL of the download, whether or not the file is being 
    streamed, and the original exception.

    Attributes:
        url (str): The source URL of the downloading file.
        stream (bool): Signifies whether or not the file was being 
            streamed. True for streaming; False for not.
        original_exception (Exception): The original exception.
    
    Args:
        url (str): The source URL of the downloading file.
        stream (bool): Signifies whether or not the file was being 
            streamed. True for streaming; False for not.
        original_exception (Exception): The original exception.
    """
    def __init__(self, url: schemas.URL, stream: bool, original_exception: Exception):
        self.url = url
        self.stream = stream
        self.original_exception = original_exception
        message = (
            f"Failed to download content from {url} "
            f"(stream={stream}): {original_exception}"
        )
        super().__init__(message)
