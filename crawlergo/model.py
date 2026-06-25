"""
Data models module for crawlergo.
Contains URL and Request data models with URL parsing, root domain extraction, file extension extraction, and other utility methods.
"""

import json
import re
import hashlib
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urlparse, parse_qs, urlunparse, unquote

try:
    from tldextract import extract as tld_extract
    HAS_TLDEXTRACT = True
except ImportError:
    HAS_TLDEXTRACT = False

from . import config


class URL:
    """
    URL wrapper class providing additional utility methods.
    """

    def __init__(self, url: Union[str, 'URL']):
        """
        Initialize URL from string or another URL object.

        Args:
            url: URL string or URL object
        """
        if isinstance(url, URL):
            self._parsed = url._parsed
        else:
            self._parsed = urlparse(url)

    @property
    def scheme(self) -> str:
        return self._parsed.scheme

    @property
    def netloc(self) -> str:
        return self._parsed.netloc

    @property
    def hostname(self) -> str:
        """Return hostname from netloc."""
        return self._parsed.hostname or ""

    @property
    def port(self) -> Optional[int]:
        return self._parsed.port

    @property
    def path(self) -> str:
        return self._parsed.path or "/"

    @property
    def query(self) -> str:
        return self._parsed.query

    @property
    def fragment(self) -> str:
        return self._parsed.fragment

    @property
    def username(self) -> Optional[str]:
        return self._parsed.username

    @property
    def password(self) -> Optional[str]:
        return self._parsed.password

    def __str__(self) -> str:
        """Return full URL string."""
        return urlunparse((
            self.scheme,
            self.netloc,
            self.path,
            self.params,
            self.query,
            self.fragment
        ))

    def __repr__(self) -> str:
        return f"URL('{str(self)}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, URL):
            return False
        return str(self) == str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    @property
    def params(self) -> str:
        return self._parsed.params

    def get_url(self) -> str:
        """Return full URL string."""
        return str(self)

    def query_map(self) -> Dict[str, Any]:
        """
        Return query parameters as a dictionary.
        Single values are returned as-is, multiple values as lists.
        """
        parsed = parse_qs(self.query)
        result = {}
        for key, value in parsed.items():
            if len(value) == 1:
                result[key] = value[0]
            else:
                result[key] = value
        return result

    def no_query_url(self) -> str:
        """
        Return URL without query parameters.
        """
        return f"{self.scheme}://{self.netloc}{self.path}"

    def no_fragment_url(self) -> str:
        """
        Return URL without fragment.
        """
        return urlunparse((
            self.scheme,
            self.netloc,
            self.path,
            self.params,
            self.query,
            ""
        ))

    def no_scheme_fragment_url(self) -> str:
        """
        Return URL without scheme and fragment.
        """
        return f"://{self.netloc}{self.path}"

    def navigation_url(self) -> str:
        """
        Return navigation URL (no scheme and fragment).
        """
        return self.no_scheme_fragment_url()

    def root_domain(self) -> str:
        """
        Return root domain.

        Example: a.b.c.360.cn returns 360.cn
        """
        domain = self.hostname.lower()
        if not domain:
            return ""

        if HAS_TLDEXTRACT:
            extracted = tld_extract(domain)
            if extracted.suffix:
                return f"{extracted.domain}.{extracted.suffix}"
            return ""

        # Fallback without tldextract
        # Simple approach: find public suffix
        parts = domain.split('.')
        if len(parts) < 2:
            return ""

        # Common TLDs that are public suffixes
        public_suffixes = [
            'com', 'net', 'org', 'gov', 'edu', 'co', 'uk', 'io', 'ai', 'app',
            'com.au', 'co.uk', 'com.cn', 'co.jp', 'ne.jp', 'or.jp', 'ac.jp',
            'ad.jp', 'ac.uk', 'org.uk', 'gov.uk', 'edu.cn', 'com.hk', 'org.hk'
        ]

        # Check for two-part public suffix
        if len(parts) >= 2:
            two_part = '.'.join(parts[-2:])
            if two_part in public_suffixes:
                return '.'.join(parts[-3:]) if len(parts) >= 3 else domain

        # Check for single-part public suffix
        if parts[-1] in public_suffixes and len(parts) >= 3:
            return '.'.join(parts[-3:])

        # Default: return last two parts
        return '.'.join(parts[-2:])

    def filename(self) -> str:
        """
        Return filename from URL path.
        Returns the last path component if it contains a dot.
        """
        parts = self.path.rstrip('/').split('/')
        last_part = parts[-1] if parts else ""
        if '.' in last_part:
            return last_part
        return ""

    def file_ext(self) -> str:
        """
        Return file extension from URL path (lowercase, without dot).
        """
        import os
        _, ext = os.path.splitext(self.path)
        if ext:
            return ext[1:].lower()
        return ""

    def parent_path(self) -> str:
        """
        Return parent path. If current path is root, return empty string.
        """
        if self.path == "/":
            return ""

        path = self.path.rstrip('/')

        if '/' not in path:
            return "/"

        parts = path.rsplit('/', 1)
        parent = parts[0] if parts[0] else "/"
        return parent


def GetUrl(_url: str, *parent_urls: URL) -> Optional[URL]:
    """
    Parse and normalize URL string.

    Args:
        _url: URL string to parse
        parent_urls: Optional parent URLs for relative URL resolution

    Returns:
        Parsed URL object or None if parsing fails
    """
    _url = _url.strip()

    if not _url:
        return None

    # Fix multiple hash symbols
    if _url.count('#') > 1:
        _url = re.sub(r"#+", "#", _url)

    # If no parent URLs, try direct parsing
    if not parent_urls:
        try:
            parsed = urlparse(_url)
            if not parsed.scheme and not parsed.netloc:
                # Try adding scheme
                if _url.startswith('//'):
                    _url = 'http:' + _url
                else:
                    _url = 'http://' + _url
                parsed = urlparse(_url)

            u = URL(_url)
            if not u.path:
                u._parsed = urlparse(_url.rstrip('/') + '/')
            return u
        except Exception:
            return None

    # Has parent URLs, resolve relative URL
    parent = parent_urls[0]

    if _url.startswith('http://') or _url.startswith('https://'):
        u = URL(_url)
    elif _url.startswith('javascript:') or _url.startswith('mailto:'):
        return None
    else:
        try:
            # Resolve relative URL against parent
            if _url.startswith('//'):
                resolved = parent.scheme + ':' + _url
            elif _url.startswith('/'):
                # Absolute path
                resolved = f"{parent.scheme}://{parent.netloc}{_url}"
            else:
                # Relative path
                base_path = parent.path.rstrip('/')
                if '/' in base_path:
                    base_dir = base_path.rsplit('/', 1)[0]
                else:
                    base_dir = ''
                resolved = f"{parent.scheme}://{parent.netloc}{base_dir}/{_url}"

            u = URL(resolved)
        except Exception:
            return None

    # Fix double slashes in path
    if u.path.startswith('//'):
        u._parsed = urlparse(urlunparse((
            u.scheme,
            u.netloc,
            re.sub(r"^/+", "/", u.path),
            u.params,
            u.query,
            u.fragment
        )))

    if not u.path:
        u._parsed = urlparse(urlunparse((
            u.scheme,
            u.netloc,
            "/",
            u.params,
            u.query,
            u.fragment
        )))

    return u


class Filter:
    """Filter metadata for request deduplication."""

    def __init__(
        self,
        marked_query_map: Optional[Dict[str, Any]] = None,
        query_keys_id: str = "",
        query_map_id: str = "",
        marked_post_data_map: Optional[Dict[str, Any]] = None,
        post_data_id: str = "",
        marked_path: str = "",
        fragment_id: str = "",
        path_id: str = "",
        unique_id: str = ""
    ):
        self.MarkedQueryMap = marked_query_map or {}
        self.QueryKeysId = query_keys_id
        self.QueryMapId = query_map_id
        self.MarkedPostDataMap = marked_post_data_map or {}
        self.PostDataId = post_data_id
        self.MarkedPath = marked_path
        self.FragmentID = fragment_id
        self.PathId = path_id
        self.UniqueId = unique_id


class Options:
    """Request options for customization."""

    def __init__(
        self,
        headers: Optional[Dict[str, Any]] = None,
        post_data: str = ""
    ):
        self.Headers = headers or {}
        self.PostData = post_data


class Request:
    """
    HTTP Request model.
    """

    def __init__(
        self,
        url: URL,
        method: str,
        headers: Optional[Dict[str, Any]] = None,
        post_data: str = "",
        filter_obj: Optional[Filter] = None,
        source: str = "",
        redirection_flag: bool = False,
        proxy: str = ""
    ):
        self.URL = url
        self.Method = method.upper() if method else "GET"
        self.Headers = headers or {}
        self.PostData = post_data
        self.Filter = filter_obj or Filter()
        self.Source = source
        self.RedirectionFlag = redirection_flag
        self.Proxy = proxy

    def format_print(self) -> None:
        """Print formatted request."""
        lines = [f"{self.Method} {self.URL.get_url()} HTTP/1.1\r"]
        for key, value in self.Headers.items():
            lines.append(f"{key}: {value}\r")
        lines.append("\r")
        if self.Method == config.POST:
            lines.append(self.PostData)
        print("".join(lines))

    def simple_print(self) -> None:
        """Print simple request info."""
        result = f"{self.Method} {self.URL.get_url()}"
        if self.Method == config.POST:
            result += f" {self.PostData}"
        print(result)

    def simple_format(self) -> str:
        """Return simple formatted request string."""
        result = f"{self.Method} {self.URL.get_url()}"
        if self.Method == config.POST:
            result += f" {self.PostData}"
        return result

    @staticmethod
    def _str_md5(s: str) -> str:
        """Calculate MD5 hash of string."""
        return hashlib.md5(s.encode('utf-8')).hexdigest()

    def no_header_id(self) -> str:
        """
        Generate request ID without headers.
        Used for deduplication.
        """
        return self._str_md5(f"{self.Method}{self.URL.get_url()}{self.PostData}")

    def unique_id(self) -> str:
        """
        Generate unique request ID.
        Includes redirection flag for separate tracking.
        """
        if self.RedirectionFlag:
            return self._str_md5(f"{self.no_header_id()}Redirection")
        return self.no_header_id()

    def post_data_map(self) -> Dict[str, Any]:
        """
        Parse POST data into dictionary.

        Supports application/x-www-form-urlencoded and application/json.

        Returns:
            Dictionary of parsed POST data, or {"key": post_data_str} on parse failure.
        """
        content_type = self._get_content_type()
        if not content_type:
            return {"key": self.PostData}

        if content_type.startswith(config.JSON):
            try:
                return json.loads(self.PostData)
            except (json.JSONDecodeError, TypeError):
                return {"key": self.PostData}

        elif content_type.startswith(config.URLENCODED):
            try:
                parsed = parse_qs(self.PostData)
                result = {}
                for key, value in parsed.items():
                    if len(value) == 1:
                        result[key] = value[0]
                    else:
                        result[key] = value
                return result
            except Exception:
                return {"key": self.PostData}

        return {"key": self.PostData}

    def query_map(self) -> Dict[str, List[str]]:
        """
        Return GET query parameters as dictionary.
        """
        return self.URL.query_map()

    def _get_content_type(self) -> Optional[str]:
        """
        Extract Content-Type header from request.

        Returns:
            Content-Type string or None if not found.
        """
        for key in ['Content-Type', 'Content-type', 'content-type']:
            if key in self.Headers:
                return str(self.Headers[key])
        return None


def GetRequest(
    method: str,
    url: URL,
    *options: Options
) -> Request:
    """
    Factory function to create Request object.

    Args:
        method: HTTP method
        url: URL object
        options: Optional Options for headers and post_data

    Returns:
        Request object
    """
    headers = {}
    post_data = ""

    if options:
        opt = options[0]
        if opt.Headers:
            headers = opt.Headers
        if opt.PostData:
            post_data = opt.PostData

    return Request(
        url=url,
        method=method.upper() if method else "GET",
        headers=headers,
        post_data=post_data
    )
