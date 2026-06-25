"""
crawlergo - A powerful web crawler based on Chrome headless mode

Python port of the Go crawlergo project
"""

from .config import (
    # Constants
    DefaultUA,
    MaxTabsCount,
    TabRunTimeout,
    DefaultInputText,
    FormInputKeyword,
    SuspectURLRegex,
    URLRegex,
    AttrURLRegex,
    DomContentLoadedTimeout,
    EventTriggerInterval,
    BeforeExitDelay,
    DefaultEventTriggerMode,
    MaxCrawlCount,
    MaxRunTime,
    # HTTP Methods
    GET, POST, PUT, DELETE, HEAD, OPTIONS,
    # Filter Modes
    SimpleFilterMode, SmartFilterMode, StrictFilterMode,
    # Event Trigger Modes
    EventTriggerAsync, EventTriggerSync,
    # Request Sources
    FromTarget, FromNavigation, FromXHR, FromDOM, FromJSFile,
    FromFuzz, FromRobots, FromComment, FromWebSocket, FromEventSource,
    FromFetch, FromHistoryAPI, FromOpenWindow, FromHashChange,
    FromStaticRes, FromStaticRegex,
    # Content Types
    JSON, URLENCODED, MULTIPART,
    # Static suffixes
    StaticSuffixSet, ScriptSuffixSet,
    # Default ignore keywords
    DefaultIgnoreKeywords,
    # Allowed form names
    AllowedFormName,
    # Input text map
    InputTextMap,
)

from .task import TaskConfig, Result, CrawlerTask

__version__ = '0.1.0'
__all__ = [
    'TaskConfig', 'Result', 'CrawlerTask',
]
