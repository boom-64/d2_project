from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import core.schemas

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
