from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse, ParseResult
import validators

class MD5Checksum(str):
    pass

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
