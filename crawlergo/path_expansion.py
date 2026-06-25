"""
路径扩展模块
提供从robots.txt获取路径和路径fuzz功能
"""

import re
import threading
from typing import List

from . import config
from .http_client import get, ReqOptions
from .model import Request, URL, GetUrl, GetRequest


# 内置路径字典
PATH_STR = (
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


class FuzzTask:
    """单次fuzz任务"""
    def __init__(self, nav_req: Request, path: str):
        self.nav_req = nav_req
        self.path = path


# 用于存储验证通过的URL
_validate_url_lock = threading.Lock()
_validate_url = set()


def _fuzz_worker(fuzz_task: FuzzTask) -> None:
    """
    执行单个fuzz任务的工作线程

    Args:
        fuzz_task: fuzz任务对象
    """
    global _validate_url

    url = f"{fuzz_task.nav_req.URL.scheme}://{fuzz_task.nav_req.URL.netloc}/{fuzz_task.path}"

    options = ReqOptions(
        timeout=2,
        allow_redirect=False,
        proxy=fuzz_task.nav_req.Proxy
    )

    try:
        resp = get(url, fuzz_task.nav_req.Headers, options)
        if 200 <= resp.status_code < 300:
            with _validate_url_lock:
                _validate_url.add(url)
        elif resp.status_code == 301:
            location = resp.headers.get("Location")
            if location:
                redirect_url = GetUrl(location)
                if redirect_url and redirect_url.hostname == fuzz_task.nav_req.URL.hostname:
                    with _validate_url_lock:
                        _validate_url.add(url)
    except Exception:
        pass


def _do_fuzz(nav_req: Request, path_list: List[str]) -> List[Request]:
    """
    执行fuzz操作

    Args:
        nav_req: 导航请求
        path_list: 路径列表

    Returns:
        请求列表
    """
    global _validate_url
    _validate_url = set()

    threads = []
    for path in path_list:
        path = path.strip().lstrip("/").rstrip("\n")
        if not path:
            continue
        task = FuzzTask(nav_req, path)
        t = threading.Thread(target=_fuzz_worker, args=(task,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    result = []
    for _url in _validate_url:
        url_obj = GetUrl(_url)
        if not url_obj:
            continue
        req = GetRequest(config.GET, url_obj)
        req.Source = config.FromFuzz
        result.append(req)

    return result


def get_paths_from_robots(nav_req: Request) -> List[Request]:
    """
    从robots.txt文件中获取路径信息

    Args:
        nav_req: 导航请求

    Returns:
        从robots.txt提取的请求列表
    """
    result = []

    url_find_regex = re.compile(r"(?:Disallow|Allow):.*?(/.+)")
    url_regex = re.compile(r"(/.+)")

    base_url = nav_req.URL.no_query_url().rstrip("/")
    robots_url = f"{base_url}/robots.txt"

    options = ReqOptions(
        allow_redirect=False,
        timeout=5,
        proxy=nav_req.Proxy
    )

    try:
        resp = get(robots_url, nav_req.Headers, options)
    except Exception:
        return result

    if resp.status_code < 200 or resp.status_code >= 300:
        return result

    url_list = url_find_regex.findall(resp.text)
    for _url in url_list:
        _url = _url.strip()
        match = url_regex.search(_url)
        if not match:
            continue
        path = match.group(1)
        url_obj = GetUrl(path, nav_req.URL)
        if not url_obj:
            continue
        req = GetRequest(config.GET, url_obj)
        req.Source = config.FromRobots
        result.append(req)

    return result


def get_paths_by_fuzz(nav_req: Request) -> List[Request]:
    """
    使用内置常见路径列表进行fuzz

    Args:
        nav_req: 导航请求

    Returns:
        fuzz发现的有效路径请求列表
    """
    path_list = PATH_STR.split("/")
    return _do_fuzz(nav_req, path_list)


def get_paths_by_fuzz_dict(nav_req: Request, dict_path: str) -> List[Request]:
    """
    使用字典文件进行fuzz

    Args:
        nav_req: 导航请求
        dict_path: 字典文件路径

    Returns:
        fuzz发现的有效路径请求列表
    """
    try:
        with open(dict_path, "r", encoding="utf-8") as f:
            path_list = [line.strip() for line in f if line.strip()]
    except Exception:
        return []

    return _do_fuzz(nav_req, path_list)
