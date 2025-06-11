from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, ParseResult
import validators
import re
from json.decoder import JSONDecodeError
import logging
from requests import Response
from typing import Any

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

@dataclass(frozen=True, init=False)
class BungieResponseData:
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
    _attrs_conversion: dict[str, str] = {
        'error_code': 'ErrorCode',
        'throttle_seconds': 'ThrottleSeconds',
        'error_status': 'ErrorStatus',
        'message': 'Message',
        'message_data': 'MessageData',
        'response': 'Response'
    }

    error_code: int = field(init=False)
    throttle_seconds: int = field(init=False)
    error_status: str = field(init=False)
    message: str = field(init=False)
    message_data: dict[str, Any] = field(init=False)
    response: dict[str, Any] = field(init=False)

    def __init__(self, raw_data: Response) -> None:
        """
        Initializes BungieResponseData by parsing and validating a requests.Response object.

        Args:
            raw_data (Response): The raw response object returned by `requests.get()`.

        Raises:
            ValueError: If the JSON decoding fails, required fields are missing,
                or unexpected fields are present in the response.
        """
        try:
            json_data = raw_data.json()
            attrs = {k: json_data[v] for k, v in self._attrs_conversion.items()}

            if (diff := set(json_data) - set(self._attrs_conversion.values())):
                raise ValueError(
                    f"Unexpected components in response: " +
                    ", ".join(f"{k}={json_data[k]!r}" for k in diff)
                )

        except JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse json response: {e}"
            ) from e

        except KeyError as e:
            raise ValueError(f"Missing required field in response: {e}.")

        for key, val in attrs.items():
            object.__setattr__(self, key, val)

        self._validate()

    def _validate(self) -> None:
        """
        Validates the error_code to determine if the response indicates success.

        Raises:
            PermissionError: If the error code indicates an API key issue.
            APIError: For other unexpected Bungie API errors.
        """
        if self.error_code != 1:
            if self.error_code in (2101, 2102):
                raise PermissionError(f"Issue with the API key. Error code: {self.error_code}, error message: '{self.message}'.")
            raise self.APIError(msg="Unexpected Bungie API error.", response_data=self)

    class APIError(Exception):
        """
        Exception raised for errors returned by the Bungie API.

        This exception is intended to represent non-permission-related errors
        in Bungie's API response.
        """ 
        def __init__(self, msg: str, response_data: 'BungieResponseData | None' = None) -> None:
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
