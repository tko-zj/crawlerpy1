"""
Task module for crawlergo.
Contains TaskConfig, Result, CrawlerTask classes for managing crawler tasks.
"""

import asyncio
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import timedelta
from typing import List, Optional, Dict, Any, Set

from . import config
from .browser import BrowserManager
from .model import Request, URL, GetUrl, GetRequest
from .filter import SimpleFilter, SmartFilter


class TaskConfig:
    """
    Task configuration class.
    """

    def __init__(
        self,
        max_crawl_count: int = 0,
        filter_mode: str = "",
        extra_headers: Optional[Dict[str, Any]] = None,
        extra_headers_string: str = "",
        all_domain_return: bool = False,
        sub_domain_return: bool = False,
        no_headless: bool = False,
        dom_content_loaded_timeout: timedelta = None,
        tab_run_timeout: timedelta = None,
        path_by_fuzz: bool = False,
        fuzz_dict_path: str = "",
        path_from_robots: bool = False,
        max_tabs_count: int = 0,
        chromium_path: str = "",
        chromium_ws_url: str = "",
        event_trigger_mode: str = "",
        event_trigger_interval: timedelta = None,
        before_exit_delay: timedelta = None,
        encode_url_with_charset: bool = False,
        ignore_keywords: Optional[List[str]] = None,
        proxy: str = "",
        custom_form_values: Optional[Dict[str, str]] = None,
        custom_form_keyword_values: Optional[Dict[str, str]] = None,
        max_run_time: int = 0,
    ):
        self.MaxCrawlCount = max_crawl_count
        self.FilterMode = filter_mode
        self.ExtraHeaders = extra_headers or {}
        self.ExtraHeadersString = extra_headers_string
        self.AllDomainReturn = all_domain_return
        self.SubDomainReturn = sub_domain_return
        self.NoHeadless = no_headless
        self.DomContentLoadedTimeout = dom_content_loaded_timeout or config.DomContentLoadedTimeout
        self.TabRunTimeout = tab_run_timeout or config.TabRunTimeout
        self.PathByFuzz = path_by_fuzz
        self.FuzzDictPath = fuzz_dict_path
        self.PathFromRobots = path_from_robots
        self.MaxTabsCount = max_tabs_count or config.MaxTabsCount
        self.ChromiumPath = chromium_path
        self.ChromiumWSUrl = chromium_ws_url
        self.EventTriggerMode = event_trigger_mode or config.DefaultEventTriggerMode
        self.EventTriggerInterval = event_trigger_interval or config.EventTriggerInterval
        self.BeforeExitDelay = before_exit_delay or config.BeforeExitDelay
        self.EncodeURLWithCharset = encode_url_with_charset
        self.IgnoreKeywords = ignore_keywords or config.DefaultIgnoreKeywords
        self.Proxy = proxy
        self.CustomFormValues = custom_form_values or {}
        self.CustomFormKeywordValues = custom_form_keyword_values or {}
        self.MaxRunTime = max_run_time

    @classmethod
    def with_max_crawl_count(cls, max_crawl_count: int):
        def apply(cfg: "TaskConfig"):
            if cfg.MaxCrawlCount == 0:
                cfg.MaxCrawlCount = max_crawl_count
        return apply

    @classmethod
    def with_filter_mode(cls, filter_mode: str):
        def apply(cfg: "TaskConfig"):
            if cfg.FilterMode == "":
                cfg.FilterMode = filter_mode
        return apply

    @classmethod
    def with_extra_headers(cls, headers: Dict[str, Any]):
        def apply(cfg: "TaskConfig"):
            if cfg.ExtraHeaders is None:
                cfg.ExtraHeaders = headers
        return apply

    @classmethod
    def with_extra_headers_string(cls, headers_str: str):
        def apply(cfg: "TaskConfig"):
            if cfg.ExtraHeadersString == "":
                cfg.ExtraHeadersString = headers_str
        return apply

    @classmethod
    def with_all_domain_return(cls, enabled: bool):
        def apply(cfg: "TaskConfig"):
            if not cfg.AllDomainReturn:
                cfg.AllDomainReturn = enabled
        return apply

    @classmethod
    def with_sub_domain_return(cls, enabled: bool):
        def apply(cfg: "TaskConfig"):
            if not cfg.SubDomainReturn:
                cfg.SubDomainReturn = enabled
        return apply

    @classmethod
    def with_no_headless(cls, enabled: bool):
        def apply(cfg: "TaskConfig"):
            if not cfg.NoHeadless:
                cfg.NoHeadless = enabled
        return apply

    @classmethod
    def with_dom_content_loaded_timeout(cls, timeout: timedelta):
        def apply(cfg: "TaskConfig"):
            if cfg.DomContentLoadedTimeout is None or cfg.DomContentLoadedTimeout == timedelta(0):
                cfg.DomContentLoadedTimeout = timeout
        return apply

    @classmethod
    def with_tab_run_timeout(cls, timeout: timedelta):
        def apply(cfg: "TaskConfig"):
            if cfg.TabRunTimeout is None or cfg.TabRunTimeout == timedelta(0):
                cfg.TabRunTimeout = timeout
        return apply

    @classmethod
    def with_path_by_fuzz(cls, enabled: bool):
        def apply(cfg: "TaskConfig"):
            if not cfg.PathByFuzz:
                cfg.PathByFuzz = enabled
        return apply

    @classmethod
    def with_fuzz_dict_path(cls, path: str):
        def apply(cfg: "TaskConfig"):
            if cfg.FuzzDictPath == "":
                cfg.FuzzDictPath = path
        return apply

    @classmethod
    def with_path_from_robots(cls, enabled: bool):
        def apply(cfg: "TaskConfig"):
            if not cfg.PathFromRobots:
                cfg.PathFromRobots = enabled
        return apply

    @classmethod
    def with_max_tabs_count(cls, count: int):
        def apply(cfg: "TaskConfig"):
            if cfg.MaxTabsCount == 0:
                cfg.MaxTabsCount = count
        return apply

    @classmethod
    def with_chromium_path(cls, path: str):
        def apply(cfg: "TaskConfig"):
            if cfg.ChromiumPath == "":
                cfg.ChromiumPath = path
        return apply

    @classmethod
    def with_event_trigger_mode(cls, mode: str):
        def apply(cfg: "TaskConfig"):
            if cfg.EventTriggerMode == "":
                cfg.EventTriggerMode = mode
        return apply

    @classmethod
    def with_event_trigger_interval(cls, interval: timedelta):
        def apply(cfg: "TaskConfig"):
            if cfg.EventTriggerInterval is None or cfg.EventTriggerInterval == timedelta(0):
                cfg.EventTriggerInterval = interval
        return apply

    @classmethod
    def with_before_exit_delay(cls, delay: timedelta):
        def apply(cfg: "TaskConfig"):
            if cfg.BeforeExitDelay is None or cfg.BeforeExitDelay == timedelta(0):
                cfg.BeforeExitDelay = delay
        return apply

    @classmethod
    def with_encode_url_with_charset(cls, enabled: bool):
        def apply(cfg: "TaskConfig"):
            if not cfg.EncodeURLWithCharset:
                cfg.EncodeURLWithCharset = enabled
        return apply

    @classmethod
    def with_ignore_keywords(cls, keywords: List[str]):
        def apply(cfg: "TaskConfig"):
            if cfg.IgnoreKeywords is None or len(cfg.IgnoreKeywords) == 0:
                cfg.IgnoreKeywords = keywords
        return apply

    @classmethod
    def with_proxy(cls, proxy: str):
        def apply(cfg: "TaskConfig"):
            if cfg.Proxy == "":
                cfg.Proxy = proxy
        return apply

    @classmethod
    def with_custom_form_values(cls, values: Dict[str, str]):
        def apply(cfg: "TaskConfig"):
            if cfg.CustomFormValues is None or len(cfg.CustomFormValues) == 0:
                cfg.CustomFormValues = values
        return apply

    @classmethod
    def with_custom_form_keyword_values(cls, values: Dict[str, str]):
        def apply(cfg: "TaskConfig"):
            if cfg.CustomFormKeywordValues is None or len(cfg.CustomFormKeywordValues) == 0:
                cfg.CustomFormKeywordValues = values
        return apply


class Result:
    """
    Crawling result structure.
    """

    def __init__(self):
        self.ReqList: List[Request] = []  # 同域名结果
        self.AllReqList: List[Request] = []  # 所有请求
        self.AllDomainList: List[str] = []  # 所有域名列表
        self.SubDomainList: List[str] = []  # 子域名列表
        self._result_lock = threading.Lock()

    def add_result(self, req: Request):
        """Add a request to result list with lock."""
        with self._result_lock:
            self.ReqList.append(req)

    def add_all_result(self, req: Request):
        """Add a request to all result list with lock."""
        with self._result_lock:
            self.AllReqList.append(req)


class TabTask:
    """
    Single tab task for crawling a URL.
    """

    def __init__(
        self,
        crawler_task: "CrawlerTask",
        browser: BrowserManager,
        req: Request,
    ):
        self.crawler_task = crawler_task
        self.browser = browser
        self.req = req

    def task(self):
        """
        Execute the tab task.
        """
        # This will be implemented with the Tab class from browser.py
        pass


class CrawlerTask:
    """
    Crawler task main logic class.
    """

    def __init__(
        self,
        targets: List[Request],
        task_config: TaskConfig,
    ):
        self.Browser: Optional[BrowserManager] = None
        self.RootDomain: str = ""  # 当前爬取根域名 用于子域名收集
        self.Targets: List[Request] = []  # 输入目标
        self.Result: Result = Result()  # 最终结果
        self.Config: TaskConfig = task_config  # 配置信息
        self._filter = None  # 过滤对象
        self._pool: Optional[ThreadPoolExecutor] = None  # 线程池
        self._task_count_lock = threading.Lock()  # 已爬取的任务总数锁
        self._crawled_count: int = 0  # 爬取过的数量
        self.Start: float = 0  # 开始时间

    def new_crawler_task(
        targets: List[Request],
        task_config: TaskConfig,
    ) -> "CrawlerTask":
        """
        Create a new crawler task.

        Args:
            targets: List of target requests
            task_config: Task configuration

        Returns:
            CrawlerTask instance
        """
        crawler_task = CrawlerTask(targets, task_config)

        # Initialize filter based on filter mode
        if not targets:
            raise ValueError("targets cannot be empty")

        base_filter = SimpleFilter(targets[0].URL.hostname)

        if task_config.FilterMode == config.SmartFilterMode:
            crawler_task._filter = SmartFilter(base_filter, strict_mode=False)
        elif task_config.FilterMode == config.StrictFilterMode:
            crawler_task._filter = SmartFilter(base_filter, strict_mode=True)
        else:
            crawler_task._filter = base_filter

        # If only one target, add a variant with alternate scheme (http <-> https)
        if len(targets) == 1:
            target = targets[0]
            new_url_str = target.URL.get_url()
            if target.URL.scheme == "http":
                new_url_str = new_url_str.replace("http://", "https://", 1)
            else:
                new_url_str = new_url_str.replace("https://", "http://", 1)
            new_url = GetUrl(new_url_str)
            if new_url:
                new_req = Request(
                    url=new_url,
                    method=target.Method,
                    headers=target.Headers.copy(),
                    post_data=target.PostData,
                    source=target.Source,
                    redirection_flag=target.RedirectionFlag,
                    proxy=target.Proxy,
                )
                targets = targets + [new_req]

        crawler_task.Targets = targets[:]

        for req in targets:
            req.Source = config.FromTarget

        # Apply default configuration
        _zero_timedelta = timedelta(0)
        if task_config.TabRunTimeout is None or task_config.TabRunTimeout == _zero_timedelta:
            task_config.TabRunTimeout = config.TabRunTimeout
        if task_config.MaxTabsCount == 0:
            task_config.MaxTabsCount = config.MaxTabsCount
        if task_config.MaxCrawlCount == 0:
            task_config.MaxCrawlCount = config.MaxCrawlCount
        if task_config.DomContentLoadedTimeout is None or task_config.DomContentLoadedTimeout == _zero_timedelta:
            task_config.DomContentLoadedTimeout = config.DomContentLoadedTimeout
        if task_config.EventTriggerInterval is None or task_config.EventTriggerInterval == _zero_timedelta:
            task_config.EventTriggerInterval = config.EventTriggerInterval
        if task_config.BeforeExitDelay is None or task_config.BeforeExitDelay == _zero_timedelta:
            task_config.BeforeExitDelay = config.BeforeExitDelay
        if task_config.EventTriggerMode == "":
            task_config.EventTriggerMode = config.DefaultEventTriggerMode
        if not task_config.IgnoreKeywords:
            task_config.IgnoreKeywords = config.DefaultIgnoreKeywords

        # Parse extra headers JSON string
        if task_config.ExtraHeadersString:
            try:
                task_config.ExtraHeaders = json.loads(task_config.ExtraHeadersString)
            except json.JSONDecodeError:
                raise ValueError("custom headers can't be Unmarshal")

        # Initialize browser
        if task_config.ChromiumWSUrl:
            crawler_task.Browser = BrowserManager(
                ws_endpoint=task_config.ChromiumWSUrl,
                extra_headers=task_config.ExtraHeaders,
            )
        else:
            crawler_task.Browser = BrowserManager(
                chromium_path=task_config.ChromiumPath,
                extra_headers=task_config.ExtraHeaders,
                proxy=task_config.Proxy,
                no_headless=task_config.NoHeadless,
            )

        crawler_task.Browser.init_browser()
        crawler_task.RootDomain = targets[0].URL.root_domain()

        # Create thread pool
        crawler_task._pool = ThreadPoolExecutor(max_workers=task_config.MaxTabsCount)

        return crawler_task

    def generate_tab_task(self, req: Request) -> TabTask:
        """
        Generate a tab task for a request.

        Args:
            req: Request to crawl

        Returns:
            TabTask instance
        """
        return TabTask(
            crawler_task=self,
            browser=self.Browser,
            req=req,
        )

    def run(self):
        """
        Start the crawling task.
        """
        # Ensure pool and browser are closed on exit
        try:
            self._run_impl()
        finally:
            if self._pool:
                self._pool.shutdown(wait=True)
            if self.Browser:
                self.Browser.close()

    def _run_impl(self):
        """
        Internal run implementation.
        """
        self.Start = time.time()

        # Get paths from robots.txt if enabled
        if self.Config.PathFromRobots:
            reqs_from_robots = get_paths_from_robots(self.Targets[0])
            print(f"get paths from robots.txt: {len(reqs_from_robots)}")
            self.Targets.extend(reqs_from_robots)

        # Get paths by fuzz if enabled
        if self.Config.FuzzDictPath:
            if self.Config.PathByFuzz:
                print("`--fuzz-path` is ignored, using `--fuzz-path-dict` instead")
            reqs_by_fuzz = get_paths_by_fuzz_dict(self.Targets[0], self.Config.FuzzDictPath)
            self.Targets.extend(reqs_by_fuzz)
        elif self.Config.PathByFuzz:
            reqs_by_fuzz = get_paths_by_fuzz(self.Targets[0])
            print(f"get paths by fuzzing: {len(reqs_by_fuzz)}")
            self.Targets.extend(reqs_by_fuzz)

        self.Result.AllReqList = self.Targets[:]

        # Filter initial targets
        init_tasks = []
        for req in self.Targets:
            if self._filter.do_filter(req):
                print(f"filter req: {req.URL.get_url()}")
                continue
            init_tasks.append(req)
            self.Result.add_result(req)

        print(f"filter repeat, target count: {len(init_tasks)}")

        # Submit initial tasks to pool
        for req in init_tasks:
            if not is_ignored_by_keyword_match(req, self.Config.IgnoreKeywords):
                self.add_task2pool(req)

        # Wait for all tasks to complete
        self._pool.shutdown(wait=True)
        self._pool = None

        # Deduplicate all requests
        seen_ids: Set[str] = set()
        unique_all_req_list = []
        for req in self.Result.AllReqList:
            req_id = req.unique_id()
            if req_id not in seen_ids:
                seen_ids.add(req_id)
                unique_all_req_list.append(req)
        self.Result.AllReqList = unique_all_req_list

        # Collect all domains
        self.Result.AllDomainList = all_domain_collect(self.Result.AllReqList)
        # Collect subdomains
        self.Result.SubDomainList = sub_domain_collect(self.Result.AllReqList, self.RootDomain)

    def add_task2pool(self, req: Request):
        """
        Add a task to the thread pool with real-time filtering.

        Args:
            req: Request to add
        """
        with self._task_count_lock:
            if self._crawled_count >= self.Config.MaxCrawlCount:
                return
            self._crawled_count += 1

            # Check max run time
            if self.Start > 0:
                elapsed = time.time() - self.Start
                if elapsed >= self.Config.MaxRunTime:
                    return

        task = self.generate_tab_task(req)
        if self._pool:
            self._pool.submit(task.task)

    def tab_task_task(self):
        """
        Tab task execution - placeholder for actual tab crawling implementation.
        This would integrate with the browser module to crawl a single tab.
        """
        pass


def is_ignored_by_keyword_match(req: Request, ignore_keywords: List[str]) -> bool:
    """
    Check if request URL contains any ignore keyword.

    Args:
        req: Request to check
        ignore_keywords: List of keywords to ignore

    Returns:
        True if request should be ignored
    """
    url_str = req.URL.get_url()
    for keyword in ignore_keywords:
        if keyword in url_str:
            return True
    return False


def all_domain_collect(req_list: List[Request]) -> List[str]:
    """
    Collect all unique domains from request list.

    Args:
        req_list: List of requests

    Returns:
        List of unique domain names
    """
    unique_domains: Set[str] = set()
    domain_list: List[str] = []

    for req in req_list:
        domain = req.URL.hostname()
        if domain and domain not in unique_domains:
            unique_domains.add(domain)
            domain_list.append(domain)

    return domain_list


def sub_domain_collect(req_list: List[Request], root_domain: str) -> List[str]:
    """
    Collect subdomains from request list.

    Args:
        req_list: List of requests
        root_domain: Root domain to filter subdomains

    Returns:
        List of subdomains
    """
    unique_domains: Set[str] = set()
    sub_domain_list: List[str] = []

    for req in req_list:
        domain = req.URL.hostname()
        if not domain or domain in unique_domains:
            continue
        unique_domains.add(domain)
        if domain.endswith("." + root_domain):
            sub_domain_list.append(domain)

    return sub_domain_list


def get_paths_from_robots(nav_req: Request) -> List[Request]:
    """
    Get paths from robots.txt file.

    Args:
        nav_req: Navigation request

    Returns:
        List of requests from robots.txt
    """
    import re
    from .http_client import get as http_get

    result: List[Request] = []
    url_find_regex = re.compile(r'(?:Disallow|Allow):.*?(/.+)')
    url_regex = re.compile(r'(/.+)')

    robots_url = nav_req.URL.no_query_url() + "/robots.txt"

    try:
        resp = http_get(
            robots_url,
            headers=nav_req.Headers,
            timeout=5,
            allow_redirect=False,
            proxy=nav_req.Proxy,
        )
        if not resp or resp.status_code < 200 or resp.status_code >= 300:
            return result

        url_list = url_find_regex.findall(resp.text)
        for _url in url_list:
            _url = _url.strip()
            match = url_regex.search(_url)
            if not match:
                continue
            path = match.group(1)
            url, err = GetUrl(path, nav_req.URL)
            if err:
                continue
            req = GetRequest(config.GET, url)
            req.Source = config.FromRobots
            result.append(req)
    except Exception:
        pass

    return result


# Default fuzz path strings
_PATH_FUZZ_STR = (
    "11/123/2017/2018/message/mis/model/abstract/account/act/action"
    "/activity/ad/address/ajax/alarm/api/app/ar/attachment/auth/authority/award/back/backup/bak/base"
    "/bbs/bbs1/cms/bd/gallery/game/gift/gold/bg/bin/blacklist/blog/bootstrap/brand/build/cache/caches"
    "/caching/cacti/cake/captcha/category/cdn/ch/check/city/class/classes/classic/client/cluster"
    "/collection/comment/commit/common/commons/components/conf/config/mysite/confs/console/consumer"
    "/content/control/controllers/core/crontab/crud/css/daily/dashboard/data/database/db/default/demo"
    "/dev/doc/download/duty/es/eva/examples/excel/export/ext/fe/feature/file/files/finance/flashchart"
    "/follow/forum/frame/framework/ft/group/gss/hello/helper/helpers/history/home/hr/htdocs/html/hunter"
    "/image/img11/import/improve/inc/include/includes/index/info/install/interface/item/jobconsume/jobs"
    "/json/kindeditor/l/languages/lib/libraries/libs/link/lite/local/log/login/logs/mail/main"
    "/maintenance/manage/manager/manufacturer/menus/models/modules/monitor/movie/mysql/n/nav/network"
    "/news/notice/nw/oauth/other/page/pages/passport/pay/pcheck/people/person/php/phprpc"
    "/phptest/picture/pl/platform/pm/portal/post/product/project/protected/proxy/ps/public/qq/question"
    "/quote/redirect/redisclient/report/resource/resources/s/save/schedule/schema/script/scripts/search"
    "/security/server/service/shell/show/simple/site/sites/skin/sms/soap/sola/sort/spider/sql/stat"
    "/static/statistics/stats/submit/subways/survey/sv/syslog/system/tag/task/tasks/tcpdf/template"
    "/templates/test/tests/ticket/tmp/token/tool/tools/top/tpl/txt/upload/uploadify/uploads/url/user"
    "/util/v1/v2/vendor/view/views/web/weixin/widgets/wm/wordpress/workspace/ws/www/www2/wwwroot/zone"
    "/admin/admin_bak/mobile/m/js"
)


def get_paths_by_fuzz(nav_req: Request) -> List[Request]:
    """
    Get paths by fuzzing with common path list.

    Args:
        nav_req: Navigation request

    Returns:
        List of valid requests from fuzzing
    """
    path_list = _PATH_FUZZ_STR.split("/")
    return _do_fuzz(nav_req, path_list)


def get_paths_by_fuzz_dict(nav_req: Request, dict_path: str) -> List[Request]:
    """
    Get paths by fuzzing with dictionary file.

    Args:
        nav_req: Navigation request
        dict_path: Path to dictionary file

    Returns:
        List of valid requests from fuzzing
    """
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            path_list = [line.strip() for line in f if line.strip()]
    except Exception:
        path_list = []

    return _do_fuzz(nav_req, path_list)


def _do_fuzz(nav_req: Request, path_list: List[str]) -> List[Request]:
    """
    Perform fuzzing with path list.

    Args:
        nav_req: Navigation request
        path_list: List of paths to fuzz

    Returns:
        List of valid requests
    """
    from .http_client import get as http_get

    validated_urls: Set[str] = set()
    result: List[Request] = []

    def check_path(path: str):
        nonlocal validated_urls
        path = path.strip("/")
        path = path.strip("\n")

        url = f"{nav_req.URL.scheme}://{nav_req.URL.hostname()}/{path}"

        try:
            resp = http_get(
                url,
                headers=nav_req.Headers,
                timeout=2,
                allow_redirect=False,
                proxy=nav_req.Proxy,
            )
            if resp and resp.status_code >= 200 and resp.status_code < 300:
                validated_urls.add(url)
            elif resp and resp.status_code == 301:
                location = resp.headers.get("Location", "")
                if location:
                    redirect_url, _ = GetUrl(location)
                    if redirect_url and redirect_url.hostname() == nav_req.URL.hostname():
                        validated_urls.add(url)
        except Exception:
            pass

    # Use thread pool for parallel fuzzing
    with ThreadPoolExecutor(max_workers=20) as fuzz_pool:
        futures = [fuzz_pool.submit(check_path, path) for path in path_list]
        for future in futures:
            future.result()

    # Convert validated URLs to requests
    for _url in validated_urls:
        url, err = GetUrl(_url)
        if err:
            continue
        req = GetRequest(config.GET, url)
        req.Source = config.FromFuzz
        result.append(req)

    return result


# Function aliases for Go-style naming
NewCrawlerTask = CrawlerTask.new_crawler_task
GetPathsFromRobots = get_paths_from_robots
GetPathsByFuzz = get_paths_by_fuzz
GetPathsByFuzzDict = get_paths_by_fuzz_dict
AllDomainCollect = all_domain_collect
SubDomainCollect = sub_domain_collect
IsIgnoredByKeywordMatch = is_ignored_by_keyword_match
