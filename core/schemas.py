from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from json.decoder import JSONDecodeError
from types import MappingProxyType
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

import validators

import core.errors
import core.error_handlers

if TYPE_CHECKING:
    from typing import Any
    from urllib.parse import ParseResult
    from requests import Response
    from pathlib import Path

@dataclass(frozen=True)
class MD5Checksum:
    val: str

    def __post_init__(self) -> None:
        lc_val: str = self.val.lower()

        if not re.fullmatch(r'^[a-f0-9]{32}$', lc_val):
            raise ValueError(f"Invalid MD5 checksum: {self.val}")

        object.__setattr__(self, 'val', lc_val)

    def assert_equals(self, *, expected: Any, strict: bool=False):
        if self == expected:
            return
        if strict:
            raise core.errors.ChecksumMismatchError(
                computed=self, expected=expected
            )
        logging.warning(f"Checksum mismatch: {self.val} != {expected.val}.")

    @classmethod
    def calc(cls, path: Path) -> 'MD5Checksum':
        """
        Calculate the MD5 hash of the given file.

        Args:
            path (Path): Path to the file.

        Returns:
            MD5Checksum: The hexadecimal MD5 hash of the file contents.

        Raises:
            TypeError: If 'path' type is not Path.
            ValueError: If 'path' does not refer to a file.
        """
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
    def from_full_url(cls, full_url: str) -> 'ParsedURL':
        """
        Creates a URL instance by parsing a full URL string.

        Args:
            full_url (str): The full URL to parse and validate.

        Returns:
            ParsedURL: An instance of the URL class with parsed components.

        Raises:
            ValueError: If the passed full_url is not a valid URL according
                to validators.url().
        """
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
    def from_base_and_path(cls, *, base_url: str, path: str) -> 'ParsedURL':
        """
        Creates a URL instance from a base URL and a path.

        Args:
            base_url (str): The base URL, including scheme and netloc.
            path (str): The path component to append to the base URL.

        Returns:
            URL: An instance of the URL class with the combined URL.

        Raises:
            ValueError: If the reconstructed URL is invalid according to
                validators.url().
        """
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
                    "Unexpected components in response: " +
                    ", ".join(f"{k}={json_data[k]!r}" for k in diff)
                )

        except JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse json response: {e}"
            ) from e

        except KeyError as e:
            raise ValueError(
                f"Missing required field in response: {e}."
            ) from e

        for key, val in attrs.items():
            object.__setattr__(self, key, val)

        core.error_handlers.bungie_error_code(
            code = self.error_code,
            msg = self.message,
            response_data=json_data
        )
