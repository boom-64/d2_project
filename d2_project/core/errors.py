"""Custom errors."""
# ==== Classes ====

class DownloadError(ConnectionError):
    """Custom exception for exceptions which occur during a download.

    This exception is raised when a file fails to download. It includes
    the source URL of the download, whether or not the file is being
    streamed, and the original exception.

    Attributes/args:
        url (str): The source URL of the downloading file.
        stream (bool): Signifies whether or not the file was being
            streamed. True for streaming; False for not.
        original_exception (Exception): The original exception.

    """

    def __init__(
        self,
        *,
        url: str,
        stream: bool,
        original_exception: Exception,
    ) -> None:
        """Initialise class."""
        self.url = url
        self.stream = stream
        self.original_exception = original_exception

        message: str = (
            f"Failed to download content from {url} "
            f"(stream={stream}): {original_exception}"
        )

        super().__init__(message)

class ManifestRemotePathError(ValueError):
    """Custom exception for unexpected manifest remote paths.

    Attributes:
        path (str): Manifest remote path.

    """

    def __init__(
        self,
        *,
        path: str,
    ) -> None:
        """Initialise class."""
        self.path = path
        message: str = (
            f"Invalid remote manifest format: '{self.path}'. "
            f"Bungie may have changed manifest path format."
        )
        super().__init__(message)
