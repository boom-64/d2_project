from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, ParseResult
import validators
import re
from json.decoder import JSONDecodeError
import logging
from requests import Response
from typing import Any
from types import MappingProxyType
from pathlib import Path
import hashlib

import core._typing

@dataclass(frozen=True)
class MD5Checksum:
    val: str

    def __post_init__(self) -> None:
        core._typing.ensure_type(name='self.val', val=self.val, expected_types=str)

        lowercase_val: str = self.val.lower()

        if not re.fullmatch(r'^[a-f0-9]{32}$', lowercase_val):
            raise ValueError(f"Invalid MD5 checksum: {self.val}")

        object.__setattr__(self, 'val', lowercase_val)

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
            *,
            expected: 'MD5Checksum', 
            computed: 'MD5Checksum'
        ) -> None:
            self.expected = expected
            self.computed = computed

            super().__init__(
                f"Checksum mismatch: expected {self.expected.val}, got "
                f"{self.computed.val}."
            )

    def assert_equals(self, *, expected: Any, strict: bool=False):
        core._typing.ensure_type(
            name='expected', 
            val=expected, 
            expected_types=MD5Checksum
        ) 
        if self == expected:
            return
        if strict:
            raise self.MismatchError(computed=self, expected=expected)
        logging.warning(f"Checksum mismatch: {self.val} != {expected.val}.")

    @classmethod
    def calc(cls, path: Any) -> 'MD5Checksum':
        """
        Calculate the MD5 hash of the given file.

        Args:
            path (Any): Path to the file. Raises if type not Path.

        Returns:
            MD5Checksum: The hexadecimal MD5 hash of the file contents.

        Raises:
            TypeError: If 'path' type is not Path.
            ValueError: If 'path' does not refer to a file.
        """
        core._typing.ensure_type(
            name='path',
            val=path,
            expected_types=Path
        )
        if not path.is_file():
            raise ValueError(
                f"Provided path '{path}' does not refer to a file."
            )

        # Assign 'hasher' - an MD5 hash object.
        hasher = hashlib.md5()
    
        with path.open('rb') as f:
            # Update 'hasher' with each 8KB chunk
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)

        # Return 'hexdigest()' of 'hasher' MD5 hash object
        return cls(hasher.hexdigest())

@dataclass(frozen=True)
class ParsedURL:
    """
    Represents a URL with its base URL and path components.

    This class parses the provided URL into its base URL and path 
    components. It also allows reconstruction of the full URL from these 
    components.

    Attributes:
        url (str): The full URL, including the base URL and path.
        base_url (str): The base URL, consisting of the scheme (e.g., 
            'https') and netloc (e.g., 'example.com').
        path (str): The path component of the URL. Defaults to an empty 
            string if not provided.

    Methods:
        from_full_url(full_url: str) -> 'URL':
            Creates a URL instance from a full URL string.

        from_base_and_path(base_url: str, path: str) -> 'URL':
            Creates a URL instance from a base URL and a path.

    Raises:
        TypeError: If any argument types are incorrect.
        ValueError: If the reconstructed URL is valid according to the 
            'validators.url()' check.
    """
    url: str
    base_url: str
    path: str

    @classmethod
    def from_full_url(cls, full_url: Any) -> 'ParsedURL':
        """
        Creates a URL instance by parsing a full URL string.

        Args:
            full_url (Any): The full URL to parse and validate. Will raise 
                if type is not str.

        Returns:
            URL: An instance of the URL class with parsed components.

        Raises:
            ValueError: If the passed full_url is not a string or is not a 
            valid URL according to validators.url().
        """
        core._typing.ensure_type(
            name='full_url',
            val=full_url,
            expected_types=str
        )
        full_url = full_url.strip().rstrip('/')

        if not validators.url(full_url):
            raise ValueError(f"Passed URL '{full_url}' is invalid.")

        parsed_url: ParseResult = urlparse(full_url)

        computed_base_url: str = f"{parsed_url.scheme}://{parsed_url.netloc}"
        computed_path: str = parsed_url.path.strip('/')

        return cls(
            url=full_url, 
            base_url=computed_base_url, 
            path=computed_path
        )

    @classmethod
    def from_base_and_path(cls, *, base_url: Any, path: Any) -> 'ParsedURL':
        """
        Creates a URL instance from a base URL and a path.

        Args:
            base_url (Any): The base URL, including scheme and netloc. Will 
                raise if type is not str.
            path (Any): The path component to append to the base URL. Will 
                raise if type is not str.

        Returns:
            URL: An instance of the URL class with the combined URL.

        Raises:
            TypeError: If the passed values aren't strings.
            ValueError: If the reconstructed URL is invalid according to 
                validators.url().
        """
        for name, val in (('base_url', base_url), ('path', path)):
            core._typing.ensure_type(
                name=name,
                val=val,
                expected_types=str
            )

        cleaned_base_url = base_url.strip().rstrip('/')
        cleaned_path = path.strip().strip('/')

        computed_url = urljoin(cleaned_base_url + '/', cleaned_path) 

        parsed_url: ParseResult = urlparse(computed_url)
        full_path = parsed_url.path

        if not validators.url(computed_url):
            raise ValueError(f"Reconstructed URL '{computed_url}' is invalid.")

        return cls(url=computed_url, base_url=cleaned_base_url, path=full_path)

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
    _attrs_conversion = MappingProxyType({
        'error_code': 'ErrorCode',
        'throttle_seconds': 'ThrottleSeconds',
        'error_status': 'ErrorStatus',
        'message': 'Message',
        'message_data': 'MessageData',
        'response': 'Response'
    })

    error_code: int = field(init=False)
    throttle_seconds: int = field(init=False)
    error_status: str = field(init=False)
    message: str = field(init=False)
    message_data: dict[str, Any] = field(init=False)
    response: dict[str, Any] = field(init=False)

    def __init__(self, raw_data: Response) -> None:
        """
        Initializes BungieResponseData by parsing and validating a 
        requests.Response object.

        Args:
            raw_data (Response): The raw response object returned by 
                'requests.get()'.

        Raises:
            ValueError: If the JSON decoding fails, required fields are 
                missing, or unexpected fields are present in the response.
        """
        try:
            json_data = raw_data.json()
            attrs = {
                k: json_data[v] for k, v in self._attrs_conversion.items()
            }

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
        
        for name, val, expected_types in (
            ('error_code', self.error_code, int),
            ('throttle_seconds', self.throttle_seconds, int),
            ('error_status', self.error_status, str),
            ('message', self.message, str),
            ('message_data', self.message_data, dict),
            ('response', self.response, dict),
        ):
            core._typing.ensure_type(
                name=name, 
                val=val, 
                expected_types=expected_types
            )

        self._validate_error_code()

    def _validate_error_code(self) -> None:
        """
        Validates the error_code to determine if the response indicates success.

        Raises:
            PermissionError: If the error code indicates an API key issue.
            APIError: For other unexpected Bungie API errors.
        """
        if self.error_code != 1:
            if self.error_code in (2101, 2102):
                raise PermissionError(
                    f"Issue with the API key. Error code: {self.error_code}, "
                    f"error message: '{self.message}'.")
            raise self.APIError(
                msg="Unexpected Bungie API error.", 
                response_data=self
            )

    class APIError(Exception):
        """
        Exception raised for errors returned by the Bungie API.

        This exception is intended to represent non-permission-related 
        errors in Bungie's API response.
        """ 
        def __init__(
            self,
            *,
            msg: str, 
            response_data: 'BungieResponseData | None' = None
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
