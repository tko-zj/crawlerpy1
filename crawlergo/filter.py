"""
Filter module for crawlergo.
Provides filtering functionality for request deduplication, static resource filtering, domain filtering, and smart filtering with parameter marking.
"""

import re
import hashlib
import threading
from abc import ABC, abstractmethod
from typing import Dict, Any, Set, Optional, List, Union

from . import config
from .model import Request, URL, Filter, GetRequest, GetUrl


# Mark constants for parameter values
CustomValueMark = "{{Crawlergo}}"
FixParamRepeatMark = "{{fix_param}}"
FixPathMark = "{{fix_path}}"
TooLongMark = "{{long}}"
NumberMark = "{{number}}"
ChineseMark = "{{chinese}}"
UpperMark = "{{upper}}"
LowerMark = "{{lower}}"
UrlEncodeMark = "{{urlencode}}"
UnicodeMark = "{{unicode}}"
BoolMark = "{{bool}}"
ListMark = "{{list}}"
TimeMark = "{{time}}"
MixAlphaNumMark = "{{mix_alpha_num}}"
MixSymbolMark = "{{mix_symbol}}"
MixNumMark = "{{mix_num}}"
NoLowerAlphaMark = "{{no_lower}}"
MixStringMark = "{{mix_str}}"

# Constants for threshold values
MaxParentPathCount = 32
MaxParamKeySingleCount = 8
MaxParamKeyAllCount = 10
MaxPathParamEmptyCount = 10
MaxPathParamKeySymbolCount = 5

# Regex patterns
chinese_regex = re.compile(r"[\u4e00-\u9fa5]+")
urlencode_regex = re.compile(r"(?:%[A-Fa-f0-9]{2,6})+")
unicode_regex = re.compile(r"(?:\\u\w{4})+")
only_alpha_regex = re.compile(r"^[a-zA-Z]+$")
only_alpha_upper_regex = re.compile(r"^[A-Z]+$")
alpha_upper_regex = re.compile(r"[A-Z]+")
alpha_lower_regex = re.compile(r"[a-z]+")
replace_num_regex = re.compile(r"[0-9]+\.[0-9]+|\d+")
only_number_regex = re.compile(r"^[0-9]+$")
number_regex = re.compile(r"[0-9]+")
one_number_regex = re.compile(r"[0-9]")
num_symbol_regex = re.compile(r"\.|_|-")
time_symbol_regex = re.compile(r"-|:|\s")
only_alpha_num_regex = re.compile(r"^[0-9a-zA-Z]+$")
marked_string_regex = re.compile(r"^{{.+}}$")
html_replace_regex = re.compile(r"\.shtml|\.html|\.htm")

# Special symbol list for hasSpecialSymbol function
special_symbols = ["{", "}", " ", "|", "#", "@", "$", "*", ",", "<", ">", "/", "?", "\\", "+", "="]


class FilterHandler(ABC):
    """
    Abstract base class for filter handlers.
    """

    @abstractmethod
    def do_filter(self, req: Request) -> bool:
        """
        Filter a request.

        Args:
            req: Request object to filter

        Returns:
            bool: True if request should be filtered (ignored), False to keep
        """
        pass


class SimpleFilter(FilterHandler):
    """
    Simple filter for basic request deduplication and filtering.
    Provides unique filtering, static resource filtering, and domain filtering.
    """

    def __init__(self, host: str = ""):
        """
        Initialize SimpleFilter.

        Args:
            host: Host to limit filtering to (empty means all hosts)
        """
        self.host_limit = host
        self.unique_set: Set[str] = set()
        self.static_suffix_set: Set[str] = config.StaticSuffixSet.copy()
        # Add common web suffixes
        for suffix in ["js", "css", "json"]:
            self.static_suffix_set.add(suffix)

    def do_filter(self, req: Request) -> bool:
        """
        Main filtering method.

        Args:
            req: Request to filter

        Returns:
            bool: True if filtered (should be ignored), False otherwise
        """
        # Check domain filter first
        if self.host_limit and self.domain_filter(req):
            return True

        # Check unique filter
        if self.unique_filter(req):
            return True

        # Check static resource filter
        if self.static_filter(req):
            return True

        return False

    def unique_filter(self, req: Request) -> bool:
        """
        Request deduplication based on Method + URL + PostData.

        Args:
            req: Request to check

        Returns:
            bool: True if request is duplicate (should be filtered), False otherwise
        """
        unique_id = req.unique_id()
        if unique_id in self.unique_set:
            return True
        else:
            self.unique_set.add(unique_id)
            return False

    def static_filter(self, req: Request) -> bool:
        """
        Filter static resources based on file extension.

        Args:
            req: Request to check

        Returns:
            bool: True if request is a static resource (should be filtered), False otherwise
        """
        file_ext = req.URL.file_ext()
        if not file_ext:
            return False
        return file_ext in self.static_suffix_set

    def domain_filter(self, req: Request) -> bool:
        """
        Filter requests outside the specified domain.
        Only keeps requests from the specified host.

        Args:
            req: Request to check

        Returns:
            bool: True if request is outside domain (should be filtered), False otherwise
        """
        host = req.URL.hostname
        port = req.URL.port

        if host == self.host_limit or host == self.host_limit:
            return False

        # Handle port 80 for http
        if self.host_limit.endswith(":80") and port is None and req.URL.scheme == "http":
            if host + ":80" == self.host_limit:
                return False

        # Handle port 443 for https
        if self.host_limit.endswith(":443") and port is None and req.URL.scheme == "https":
            if host + ":443" == self.host_limit:
                return False

        return True


class SmartFilter(SimpleFilter):
    """
    Smart filter with advanced parameter marking and deduplication.
    Extends SimpleFilter with intelligent marking for parameter values,
    path components, and statistics-based filtering.
    """

    def __init__(self, base: Optional[SimpleFilter] = None, strict_mode: bool = False):
        """
        Initialize SmartFilter.

        Args:
            base: Base SimpleFilter to inherit from
            strict_mode: Enable strict filtering mode
        """
        if base:
            super().__init__(base.host_limit)
            self.unique_set = base.unique_set
            self.static_suffix_set = base.static_suffix_set
        else:
            super().__init__("")

        self.strict_mode = strict_mode
        self.filter_location_set: Set[str] = set()
        self.filter_param_key_repeat_count: Dict[str, int] = {}
        self.filter_param_key_single_values: Dict[str, Set[str]] = {}
        self.filter_path_param_key_symbol: Dict[str, int] = {}
        self.filter_param_key_all_values: Dict[str, Set[str]] = {}
        self.filter_path_param_empty_values: Dict[str, Set[str]] = {}
        self.filter_parent_path_values: Dict[str, Set[str]] = {}
        self.unique_marked_ids: Set[str] = set()

        # Thread lock for sync maps
        self._lock = threading.Lock()

    def do_filter(self, req: Request) -> bool:
        """
        Main smart filtering method with intelligent marking.

        Args:
            req: Request to filter

        Returns:
            bool: True if filtered, False otherwise
        """
        # First pass: basic filtering
        if super().do_filter(req):
            return True

        # Calculate fragment ID
        req.Filter.FragmentID = self.calc_fragment_id(req.URL.fragment)

        # Mark based on method
        if req.Method in (config.GET, config.DELETE, config.HEAD, config.OPTIONS):
            self.get_mark(req)
            self.repeat_count_statistic(req)
        elif req.Method in (config.POST, config.PUT):
            self.post_mark(req)

        # Deduplicate by marked ID
        unique_id = req.Filter.UniqueId
        if unique_id in self.unique_marked_ids:
            return True

        # Global numeric parameter marking
        self.global_filter_location_mark(req)

        # Process GET/DELETE/HEAD/OPTIONS requests
        if req.Method in (config.GET, config.DELETE, config.HEAD, config.OPTIONS):
            # Mark over-threshold parameters
            self.over_count_mark(req)

            # Recalculate QueryMapId
            req.Filter.QueryMapId = get_param_map_id(req.Filter.MarkedQueryMap)
            # Recalculate PathId
            req.Filter.PathId = get_path_id(req.Filter.MarkedPath)
        else:
            # Recalculate PostDataId
            req.Filter.PostDataId = get_param_map_id(req.Filter.MarkedPostDataMap)

        # Recalculate unique ID
        req.Filter.UniqueId = get_marked_unique_id(req)

        # Check again with new ID
        new_unique_id = req.Filter.UniqueId
        if new_unique_id in self.unique_marked_ids:
            return True

        # Add to result set
        self.unique_marked_ids.add(new_unique_id)
        return False

    def pre_query_mark(self, raw_query: str) -> str:
        """
        Pre-mark raw query string before decoding.

        Args:
            raw_query: Raw query string

        Returns:
            str: Marked query string
        """
        if chinese_regex.search(raw_query):
            return chinese_regex.sub(ChineseMark, raw_query)
        elif urlencode_regex.search(raw_query):
            return urlencode_regex.sub(UrlEncodeMark, raw_query)
        elif unicode_regex.search(raw_query):
            return unicode_regex.sub(UnicodeMark, raw_query)
        return raw_query

    def get_mark(self, req: Request) -> None:
        """
        Mark GET request parameters and path.

        Args:
            req: Request to mark
        """
        # Pre-mark before decoding
        url = URL(req.URL)
        url._parsed = urlparse(url.get_url())
        # Note: This is a simplified version; the actual implementation
        # would need to handle RawQuery marking properly

        query_map = req.query_map()
        query_map = mark_param_name(query_map)
        query_map = self.mark_param_value(query_map, req)
        marked_path = mark_path(req.URL.path)

        # Calculate IDs
        if query_map:
            query_key_id = get_keys_id(query_map)
            query_map_id = get_param_map_id(query_map)
        else:
            query_key_id = ""
            query_map_id = ""

        path_id = get_path_id(marked_path)

        req.Filter.MarkedQueryMap = query_map
        req.Filter.QueryKeysId = query_key_id
        req.Filter.QueryMapId = query_map_id
        req.Filter.MarkedPath = marked_path
        req.Filter.PathId = path_id

        # Calculate marked unique ID
        req.Filter.UniqueId = get_marked_unique_id(req)

    def post_mark(self, req: Request) -> None:
        """
        Mark POST request parameters and path.

        Args:
            req: Request to mark
        """
        post_data_map = req.post_data_map()
        post_data_map = mark_param_name(post_data_map)
        post_data_map = self.mark_param_value(post_data_map, req)
        marked_path = mark_path(req.URL.path)

        # Calculate IDs
        if post_data_map:
            post_data_map_id = get_param_map_id(post_data_map)
        else:
            post_data_map_id = ""

        path_id = get_path_id(marked_path)

        req.Filter.MarkedPostDataMap = post_data_map
        req.Filter.PostDataId = post_data_map_id
        req.Filter.MarkedPath = marked_path
        req.Filter.PathId = path_id

        # Calculate marked unique ID
        req.Filter.UniqueId = get_marked_unique_id(req)

    def mark_param_value(self, param_map: Dict[str, Any], req: Request) -> Dict[str, Any]:
        """
        Mark parameter values based on their content.

        Args:
            param_map: Parameter map to mark
            req: Original request

        Returns:
            Dict[str, Any]: Marked parameter map
        """
        marked_param_map = {}
        for key, value in param_map.items():
            # Handle boolean
            if isinstance(value, bool):
                marked_param_map[key] = BoolMark
                continue

            # Handle list/slice
            if isinstance(value, (list, tuple)):
                marked_param_map[key] = ListMark
                continue

            # Handle numeric
            if isinstance(value, (int, float)):
                marked_param_map[key] = NumberMark
                continue

            # Handle string
            if not isinstance(value, str):
                continue

            # Check for Crawlergo marker - indicates numeric parameter
            if "Crawlergo" in value:
                name = req.URL.hostname + req.URL.path + req.Method + key
                self.filter_location_set.add(name)
                marked_param_map[key] = CustomValueMark
            # All uppercase letters
            elif only_alpha_upper_regex.match(value):
                marked_param_map[key] = UpperMark
            # Value length >= 16
            elif len(value) >= 16:
                marked_param_map[key] = TooLongMark
            # All numbers (possibly with symbols)
            elif only_number_regex.match(value) or only_number_regex.match(num_symbol_regex.sub("", value)):
                marked_param_map[key] = NumberMark
            # Contains Chinese
            elif chinese_regex.search(value):
                marked_param_map[key] = ChineseMark
            # URL encoded
            elif urlencode_regex.search(value):
                marked_param_map[key] = UrlEncodeMark
            # Unicode
            elif unicode_regex.search(value):
                marked_param_map[key] = UnicodeMark
            # Time-like pattern
            elif only_number_regex.match(time_symbol_regex.sub("", value)):
                marked_param_map[key] = TimeMark
            # Alphanumeric mix
            elif only_alpha_num_regex.match(value) and number_regex.search(value):
                marked_param_map[key] = MixAlphaNumMark
            # Contains special symbols
            elif has_special_symbol(value):
                marked_param_map[key] = MixSymbolMark
            # More than 3 numbers - treat as numeric parameter
            elif len(one_number_regex.sub("0", value)) >= 3:
                marked_param_map[key] = MixNumMark
            # Strict mode processing
            elif self.strict_mode:
                if not alpha_lower_regex.search(value):
                    marked_param_map[key] = NoLowerAlphaMark
                else:
                    count = 0
                    if alpha_lower_regex.search(value):
                        count += 1
                    if alpha_upper_regex.search(value):
                        count += 1
                    if number_regex.search(value):
                        count += 1
                    if "_" in value or "-" in value:
                        count += 1
                    if count >= 3:
                        marked_param_map[key] = MixStringMark
                    else:
                        marked_param_map[key] = value
            else:
                marked_param_map[key] = value

        return marked_param_map

    def global_filter_location_mark(self, req: Request) -> None:
        """
        Mark global numeric parameters.

        Args:
            req: Request to process
        """
        name = req.URL.hostname + req.URL.path + req.Method

        if req.Method in (config.GET, config.DELETE, config.HEAD, config.OPTIONS):
            for key in req.Filter.MarkedQueryMap:
                full_name = name + key
                if full_name in self.filter_location_set:
                    req.Filter.MarkedQueryMap[key] = CustomValueMark
        elif req.Method in (config.POST, config.PUT):
            for key in req.Filter.MarkedPostDataMap:
                full_name = name + key
                if full_name in self.filter_location_set:
                    req.Filter.MarkedPostDataMap[key] = CustomValueMark

    def repeat_count_statistic(self, req: Request) -> None:
        """
        Collect statistics for parameter repetition.

        Args:
            req: Request to process
        """
        query_key_id = req.Filter.QueryKeysId
        path_id = req.Filter.PathId

        if query_key_id:
            # All parameter names repetition count
            with self._lock:
                if query_key_id in self.filter_param_key_repeat_count:
                    self.filter_param_key_repeat_count[query_key_id] += 1
                else:
                    self.filter_param_key_repeat_count[query_key_id] = 1

            for key, value in req.Filter.MarkedQueryMap.items():
                param_query_key = query_key_id + key

                # Single URL parameter repetition count
                if param_query_key in self.filter_param_key_single_values:
                    self.filter_param_key_single_values[param_query_key].add(str(value))
                else:
                    self.filter_param_key_single_values[param_query_key] = {str(value)}

                # All URLs parameter repetition count
                if key not in self.filter_param_key_all_values:
                    self.filter_param_key_all_values[key] = {str(value)}
                else:
                    self.filter_param_key_all_values[key].add(str(value))

                # Empty value parameter count per path
                if value == "":
                    if path_id not in self.filter_path_param_empty_values:
                        self.filter_path_param_empty_values[path_id] = {key}
                    else:
                        self.filter_path_param_empty_values[path_id].add(key)

                # Marked value occurrence count per path
                path_id_key = path_id + key
                value_str = str(value)
                if marked_string_regex.match(value_str):
                    with self._lock:
                        if path_id_key in self.filter_path_param_key_symbol:
                            self.filter_path_param_key_symbol[path_id_key] += 1
                        else:
                            self.filter_path_param_key_symbol[path_id_key] = 1

        # Parent path statistics
        parent_path = req.URL.parent_path()
        if not parent_path or in_common_script_suffix(req.URL.file_ext()):
            return

        from .utils import str_md5
        parent_path_id = str_md5(parent_path)
        current_path = req.Filter.MarkedPath.replace(parent_path, "", 1)

        if parent_path_id not in self.filter_parent_path_values:
            self.filter_parent_path_values[parent_path_id] = {current_path}
        else:
            self.filter_parent_path_values[parent_path_id].add(current_path)

    def over_count_mark(self, req: Request) -> None:
        """
        Mark parameters that exceed repetition thresholds.

        Args:
            req: Request to process
        """
        query_key_id = req.Filter.QueryKeysId
        path_id = req.Filter.PathId

        if req.Filter.QueryKeysId:
            # Single URL parameter count exceeds threshold and has more than 3 different values
            if query_key_id in self.filter_param_key_repeat_count:
                count = self.filter_param_key_repeat_count[query_key_id]
                if count > MaxParamKeySingleCount:
                    for key in req.Filter.MarkedQueryMap:
                        param_query_key = query_key_id + key
                        if param_query_key in self.filter_param_key_single_values:
                            if len(self.filter_param_key_single_values[param_query_key]) > 3:
                                req.Filter.MarkedQueryMap[key] = FixParamRepeatMark

            for key in req.Filter.MarkedQueryMap:
                # All URLs parameter count exceeds threshold
                if key in self.filter_param_key_all_values:
                    if len(self.filter_param_key_all_values[key]) > MaxParamKeyAllCount:
                        req.Filter.MarkedQueryMap[key] = FixParamRepeatMark

                path_id_key = path_id + key
                # Path-specific parameter mark count exceeds threshold
                if path_id_key in self.filter_path_param_key_symbol:
                    if self.filter_path_param_key_symbol[path_id_key] > MaxPathParamKeySymbolCount:
                        req.Filter.MarkedQueryMap[key] = FixParamRepeatMark

            # Handle empty parameter values per path
            if path_id in self.filter_path_param_empty_values:
                if len(self.filter_path_param_empty_values[path_id]) > MaxPathParamEmptyCount:
                    new_marker_query_map = {}
                    for key, value in req.Filter.MarkedQueryMap.items():
                        if value == "":
                            new_marker_query_map[FixParamRepeatMark] = ""
                        else:
                            new_marker_query_map[key] = value
                    req.Filter.MarkedQueryMap = new_marker_query_map

        # Handle path-level pseudo-static
        parent_path = req.URL.parent_path()
        if not parent_path or in_common_script_suffix(req.URL.file_ext()):
            return

        from .utils import str_md5
        parent_path_id = str_md5(parent_path)

        if parent_path_id in self.filter_parent_path_values:
            if len(self.filter_parent_path_values[parent_path_id]) > MaxParentPathCount:
                if parent_path.endswith("/"):
                    req.Filter.MarkedPath = parent_path + FixPathMark
                else:
                    req.Filter.MarkedPath = parent_path + "/" + FixPathMark

    def calc_fragment_id(self, fragment: str) -> str:
        """
        Calculate fragment ID from URL fragment.

        Args:
            fragment: URL fragment string

        Returns:
            str: Fragment ID or empty string
        """
        if not fragment or not fragment.startswith("/"):
            return ""

        try:
            fake_url = GetUrl(fragment)
            if not fake_url:
                return ""
            fake_req = GetRequest(config.GET, fake_url)
            self.get_mark(fake_req)
            return fake_req.Filter.UniqueId
        except Exception:
            return ""


def mark_param_name(param_map: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark parameter names based on their format.

    Args:
        param_map: Parameter map to process

    Returns:
        Dict[str, Any]: Marked parameter map
    """
    marked_param_map = {}
    for key, value in param_map.items():
        # Pure alphabetic - keep as is
        if only_alpha_regex.match(key):
            marked_param_map[key] = value
        # Key length >= 32 - too long
        elif len(key) >= 32:
            marked_param_map[TooLongMark] = value
        else:
            # Replace numbers with marker
            new_key = replace_num_regex.sub(NumberMark, key)
            marked_param_map[new_key] = value
    return marked_param_map


def mark_path(path: str) -> str:
    """
    Mark path components based on their content.

    Args:
        path: URL path to mark

    Returns:
        str: Marked path
    """
    path_parts = path.split("/")
    for index, part in enumerate(path_parts):
        if len(part) >= 32:
            path_parts[index] = TooLongMark
        elif only_number_regex.match(num_symbol_regex.sub("", part)):
            path_parts[index] = NumberMark
        elif part.endswith(".html") or part.endswith(".htm") or part.endswith(".shtml"):
            part = html_replace_regex.sub("", part)
            # Mixed case
            if number_regex.search(part) and alpha_upper_regex.search(part) and alpha_lower_regex.search(part):
                path_parts[index] = MixAlphaNumMark
            # Pure number
            elif only_number_regex.match(num_symbol_regex.sub("", part)):
                path_parts[index] = NumberMark
        elif has_special_symbol(part):
            path_parts[index] = MixSymbolMark
        elif chinese_regex.search(part):
            path_parts[index] = ChineseMark
        elif unicode_regex.search(part):
            path_parts[index] = UnicodeMark
        elif only_alpha_upper_regex.match(part):
            path_parts[index] = UpperMark
        elif only_number_regex.match(num_symbol_regex.sub("", part)):
            path_parts[index] = NumberMark
        elif len(one_number_regex.sub("0", part)) > 3:
            path_parts[index] = MixNumMark

    return "/".join(path_parts)


def get_marked_unique_id(req: Request) -> str:
    """
    Calculate marked unique request ID.

    Args:
        req: Request to calculate

    Returns:
        str: MD5 hash of unique request ID
    """
    from .utils import str_md5

    if req.Method in (config.GET, config.DELETE, config.HEAD, config.OPTIONS):
        param_id = req.Filter.QueryMapId
    else:
        param_id = req.Filter.PostDataId

    unique_str = req.Method + param_id + req.Filter.PathId + req.URL.hostname + req.Filter.FragmentID

    if req.RedirectionFlag:
        unique_str += "Redirection"

    if req.URL.path == "/" and not req.URL.query and req.URL.scheme == "https":
        unique_str += "https"

    return str_md5(unique_str)


def get_keys_id(data_map: Dict[str, Any]) -> str:
    """
    Calculate unique ID from parameter keys.

    Args:
        data_map: Parameter map

    Returns:
        str: MD5 hash of sorted keys
    """
    from .utils import str_md5

    keys = sorted(data_map.keys())
    id_str = "".join(keys)
    return str_md5(id_str)


def get_param_map_id(data_map: Dict[str, Any]) -> str:
    """
    Calculate unique ID from marked parameter map.

    Args:
        data_map: Marked parameter map

    Returns:
        str: MD5 hash of parameters
    """
    from .utils import str_md5

    mark_replace_regex = re.compile(r"{{.+}}")
    keys = sorted(data_map.keys())
    id_str = ""

    for key in keys:
        id_str += key
        value = data_map[key]
        if isinstance(value, str):
            id_str += mark_replace_regex.sub("{{mark}}", value)

    return str_md5(id_str)


def get_path_id(path: str) -> str:
    """
    Calculate unique ID from marked path.

    Args:
        path: Marked path

    Returns:
        str: MD5 hash of path
    """
    from .utils import str_md5
    return str_md5(path)


def has_special_symbol(s: str) -> bool:
    """
    Check if string contains special symbols.

    Args:
        s: String to check

    Returns:
        bool: True if contains special symbols
    """
    for sym in special_symbols:
        if sym in s:
            return True
    return False


def in_common_script_suffix(suffix: str) -> bool:
    """
    Check if suffix is a common script suffix.

    Args:
        suffix: File extension to check

    Returns:
        bool: True if common script suffix
    """
    return suffix.lower() in config.ScriptSuffixSet


# Import urlparse for internal use
from urllib.parse import urlparse
