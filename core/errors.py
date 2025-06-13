from core import schemas

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
        url: schemas.ParsedURL, 
        stream: bool, 
        original_exception: Exception
    ):
        self.url = url
        self.stream = stream
        self.original_exception = original_exception
        message = (
            f"Failed to download content from {url} "
            f"(stream={stream}): {original_exception}"
        )
        super().__init__(message)
