"""
Configuration module for crawlergo.
Contains all configuration constants, filter modes, event trigger modes, request source types, static resource suffixes, and form filling configurations.
"""

import re
from typing import List, Set, Dict, Any, Optional
from datetime import timedelta

# Default User Agent
DefaultUA: str = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.0 Safari/537.36"

# Maximum number of tabs
MaxTabsCount: int = 10

# Tab run timeout
TabRunTimeout: timedelta = timedelta(seconds=20)

# Default input text
DefaultInputText: str = "Crawlergo"

# Form input keyword
FormInputKeyword: str = "Crawlergo"

# Suspect URL regex pattern
SuspectURLRegex: str = r'(?:"|\')(((?:[a-zA-Z]{1,10}://|//)[^"\'/]{1,}\.[a-zA-Z]{2,}[^"\']{0,})|((?:/|\.\./|\./)[^"\'><,;|*()(%%$^/\\\[\]][^"\'><,;|()]{1,})|([a-zA-Z0-9_\-/]{1,}/[a-zA-Z0-9_\-/]{1,}\.(?:[a-zA-Z]{1,4}|action)(?:[\?|#][^"|\']{0,}|))|([a-zA-Z0-9_\-/]{1,}/[a-zA-Z0-9_\-/]{3,}(?:[\?|#][^"|\']{0,}|))|([a-zA-Z0-9_\-]{1,}\.(?:php|asp|aspx|jsp|json|action|html|js|txt|xml)(?:[\?|#][^"|\']{0,}|)))(?:"|\')'

# URL regex pattern
URLRegex: str = r'((https?|ftp|file):)?//[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]'

# Attribute URL regex (empty in original)
AttrURLRegex: str = ""

# DOM content loaded timeout
DomContentLoadedTimeout: timedelta = timedelta(seconds=5)

# Event trigger interval (milliseconds)
EventTriggerInterval: timedelta = timedelta(milliseconds=100)

# Before exit delay
BeforeExitDelay: timedelta = timedelta(seconds=1)

# Default event trigger mode
DefaultEventTriggerMode: str = EventTriggerAsync

# Maximum crawl count
MaxCrawlCount: int = 200

# Maximum run time
MaxRunTime: timedelta = timedelta(hours=60)

# Request methods
GET: str = "GET"
POST: str = "POST"
PUT: str = "PUT"
DELETE: str = "DELETE"
HEAD: str = "HEAD"
OPTIONS: str = "OPTIONS"

# Filter modes
SimpleFilterMode: str = "simple"
SmartFilterMode: str = "smart"
StrictFilterMode: str = "strict"

# Event trigger modes
EventTriggerAsync: str = "async"
EventTriggerSync: str = "sync"

# Request source types
FromTarget: str = "Target"         # Initial target input
FromNavigation: str = "Navigation" # Page navigation request
FromXHR: str = "XHR"               # Ajax async request
FromDOM: str = "DOM"               # Request parsed from DOM
FromJSFile: str = "JavaScript"     # Parsed from JS scripts
FromFuzz: str = "PathFuzz"         # Initial path fuzz
FromRobots: str = "robots.txt"     # robots.txt
FromComment: str = "Comment"       # Comments in page
FromWebSocket: str = "WebSocket"
FromEventSource: str = "EventSource"
FromFetch: str = "Fetch"
FromHistoryAPI: str = "HistoryAPI"
FromOpenWindow: str = "OpenWindow"
FromHashChange: str = "HashChange"
FromStaticRes: str = "StaticResource"
FromStaticRegex: str = "StaticRegex"

# Content types
JSON: str = "application/json"
URLENCODED: str = "application/x-www-form-urlencoded"
MULTIPART: str = "multipart/form-data"

# Static file suffixes
StaticSuffix: List[str] = [
    "png", "gif", "jpg", "mp4", "mp3", "mng", "pct", "bmp", "jpeg", "pst", "psp", "ttf",
    "tif", "tiff", "ai", "drw", "wma", "ogg", "wav", "ra", "aac", "mid", "au", "aiff",
    "dxf", "eps", "ps", "svg", "3gp", "asf", "asx", "avi", "mov", "mpg", "qt", "rm",
    "wmv", "m4a", "bin", "xls", "xlsx", "ppt", "pptx", "doc", "docx", "odt", "ods", "odg",
    "odp", "exe", "zip", "rar", "tar", "gz", "iso", "rss", "pdf", "txt", "dll", "ico",
    "gz2", "apk", "crt", "woff", "map", "woff2", "webp", "less", "dmg", "bz2", "otf", "swf",
    "flv", "mpeg", "dat", "xsl", "csv", "cab", "exif", "wps", "m4v", "rmvb",
]

# Static suffix set for fast lookup
StaticSuffixSet: Set[str] = set(suffix.lower() for suffix in StaticSuffix)

# Script file suffixes
ScriptSuffix: List[str] = [
    "php", "asp", "jsp", "asa",
]

# Script suffix set for fast lookup
ScriptSuffixSet: Set[str] = set(suffix.lower() for suffix in ScriptSuffix)

# Default ignore keywords
DefaultIgnoreKeywords: List[str] = ["logout", "quit", "exit"]

# Allowed form names
AllowedFormName: List[str] = ["default", "mail", "code", "phone", "username", "password", "qq", "id_card", "url", "date", "number"]

# Input text map for form filling
InputTextMap: Dict[str, Dict[str, Any]] = {
    "mail": {
        "keyword": ["mail"],
        "value": "crawlergo@gmail.com",
    },
    "code": {
        "keyword": ["yanzhengma", "code", "ver", "captcha"],
        "value": "123a",
    },
    "phone": {
        "keyword": ["phone", "number", "tel", "shouji"],
        "value": "18812345678",
    },
    "username": {
        "keyword": ["name", "user", "id", "login", "account"],
        "value": "crawlergo@gmail.com",
    },
    "password": {
        "keyword": ["pass", "pwd"],
        "value": "Crawlergo6.",
    },
    "qq": {
        "keyword": ["qq", "wechat", "tencent", "weixin"],
        "value": "123456789",
    },
    "IDCard": {
        "keyword": ["card", "shenfen"],
        "value": "511702197409284963",
    },
    "url": {
        "keyword": ["url", "site", "web", "blog", "link"],
        "value": "https://crawlergo.nice.cn/",
    },
    "date": {
        "keyword": ["date", "time", "year", "now"],
        "value": "2018-01-01",
    },
    "number": {
        "keyword": ["day", "age", "num", "count"],
        "value": "10",
    },
}

# Continue resource list type alias
ContinueResourceList = List[str]

# Pre-compiled regex patterns for performance
_fix_path_regex = re.compile(r"^/{2,}")
_multiple_hash_regex = re.compile(r"#+")
