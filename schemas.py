from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, ParseResult
import validators
import re
import logging
from typing import Any, TypedDict

@dataclass(frozen=True)
class MD5Checksum:
    val: str

    def __post_init__(self):
        val = self.val.lower()
        if not re.fullmatch(r'^[a-f0-9]{32}$', val):
            raise ValueError(f"Invalid MD5 checksum: {self.val}")
        object.__setattr__(self, 'val', val)


    class MismatchError(Exception):
        """
        Custom exception for checksum mismatches.

        This exception is raised when a calculated checksum does not match 
        the expected checksum. It includes both the expected and actual 
        checksums.

        Attributes:
            expected (MD5Checksum): Expected checksum.
            computed (MD5Checksum): Actual checksum calculated.
        Args:
            expected (MD5Checksum): The expected checksum value.
            computed (MD5Checksum): The actual checksum that was calculated.
        """
        expected: 'MD5Checksum'
        computed: 'MD5Checksum'
        def __init__(
            self, 
            expected: 'MD5Checksum', 
            computed: 'MD5Checksum'
        ) -> None:
            self.expected = expected
            self.computed = computed

            message = (
                f"Checksum mismatch: expected {self.expected.val}, got "
                f"{self.computed.val}"
            )
            super().__init__(message)

    def assert_equals(self, *, expected: 'MD5Checksum', strict: bool=False):
        if not isinstance(expected, MD5Checksum):
            raise TypeError(
                f"Cannot compare MD5Checksum with '{expected}' of type "
                f"'{type(expected)}'."
            )
        if self == expected:
            return
        if strict:
            raise self.MismatchError(computed=self, expected=expected)
        logging.warning(f"Checksum mismatch: {self.val} != {expected.val}.")

@dataclass(init=False, frozen=True)
class URL:
    """
    A class representing a URL with its base URL and path components.

    This class parses the provided URL into its base URL and path 
    components. It also allows for reconstruction of the full URL from these 
    components.

    Attributes:
        url (str): The full URL, including the base URL and path.
        base_url (str): The base URL, consisting of the scheme (e.g., 
            'https') and netloc (e.g., 'example.com').
        path (str | None): The path component of the URL. Defaults to an 
            empty string if not provided.

    Methods:
        __init__(url, path=''):
            Initializes a URL object with the given URL and optional path.
            The path is appended to the parsed base URL to form the full 
            URL.

    Args:
        url (str): The full URL to be parsed and validated. Must be a valid 
            URL.
        path (str, optional): The optional additional path to be appended to 
            the parsed URL. Defaults to an empty string.

    Raises:
        ValueError: If the provided URL or reconstructed URL is invalid 
            according to the 'validators.url' check.
    """
    url: str = field(init=False)
    base_url: str = field(init=False)
    path: str | None = field(init=False)

    def __init__(self, *, url: str, path: str = ''):
        if not validators.url(url):
            raise ValueError(f"Passed URL '{url}' is invalid.")

        path = path.strip().strip('/')
        url = url.strip().rstrip('/')

        parsed_url: ParseResult = urlparse(url)
        attrs: dict[str, str] = {}

        attrs['base_url'] = f"{parsed_url.scheme}://{parsed_url.netloc}"
        attrs['path'] = (parsed_url.path + '/' + path).strip('/') 
        attrs['url'] = urljoin(attrs['base_url'] + '/', attrs['path']) 

        if not validators.url(attrs['url']):
            raise ValueError(f"Reconstructed URL '{attrs['url']}' is invalid.")

        for key, val in attrs.items(): 
            object.__setattr__(self, key, val)

class BungieResponseData(TypedDict):
    """
    TypedDict representing the structure of a typical Bungie API response.

    This dictionary is used for type hinting structured JSON responses 
    returned by Bungie API GET requests. Bungie's responses follow a 
    common schema that includes metadata about the request status, 
    throttling, and the actual response payload.

    Keys:
        ErrorCode (int): Numeric status code indicating success or failure,
            and indicating the type of failure.
        ThrottleSeconds (int): Number of seconds clients should wait before 
            retrying.
        ErrorStatus (str): Short string description of the error or status.
        Message (str): Human-readable message about the response.
        MessageData (dict[str, Any]): Additional data or details about the 
            message.
        Response (dict[str, Any]): The main payload of the response; 
            structure varies by endpoint.
    """
    ErrorCode: int
    ThrottleSeconds: int
    ErrorStatus: str
    Message: str
    MessageData: dict[str, Any]
    Response: dict[str, Any]
