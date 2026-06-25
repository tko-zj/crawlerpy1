"""
HTTP客户端模块
提供HTTP请求封装，支持GET/POST请求，支持代理、超时、重试、SSL验证等功能
"""

import io
import re
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Optional, Union

# 默认User-Agent
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/76.0.3809.132 Safari/537.36 C845D9D38B3A68F4F74057DB542AD252 tx/2.0"
)

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 15

# 默认响应长度限制（字节）
DEFAULT_RESPONSE_LENGTH = 10240

# 默认重试次数
DEFAULT_RETRY = 0

# Content-Type映射
CONTENT_TYPES = {
    "json": "application/json",
    "xml": "application/xml",
    "soap": "application/soap+xml",
    "multipart": "multipart/form-data",
    "form": "application/x-www-form-urlencoded; charset=utf-8",
}


class Response:
    """
    自定义响应类，包含原始响应和响应文本
    """
    
    def __init__(self, response: requests.Response):
        """
        初始化响应对象
        
        Args:
            response: requests库的Response对象
        """
        self.response = response
        self.status_code = response.status_code
        self.headers = response.headers
        self.text = response.text
        self.content = response.content
        self.url = response.url
        self.request = response.request
        
        # 带Range头后一般webserver响应都是206 PARTIAL CONTENT，修正为200 OK
        if self.status_code == 206:
            self.status_code = 200
            self.response.status_code = 200
            self.response.status = "200 OK"


class ReqInfo:
    """
    HTTP请求元素的封装，可以快速进行简单的http请求
    """
    
    def __init__(
        self,
        verb: str = "GET",
        url: str = "",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None
    ):
        """
        初始化ReqInfo
        
        Args:
            verb: HTTP方法
            url: 请求URL
            headers: 请求头
            body: 请求体
        """
        self.verb = verb
        self.url = url
        self.headers = headers or {}
        self.body = body or b""
    
    def request(self) -> Response:
        """
        使用默认选项发送请求
        
        Returns:
            Response: 响应对象
        """
        return request(self.verb, self.url, self.headers, self.body, None)
    
    def request_with_options(self, options: Optional['ReqOptions']) -> Response:
        """
        使用指定选项发送请求
        
        Args:
            options: 请求选项
            
        Returns:
            Response: 响应对象
        """
        return request(self.verb, self.url, self.headers, self.body, options)
    
    def clone(self) -> 'ReqInfo':
        """
        克隆当前请求信息
        
        Returns:
            ReqInfo: 新的ReqInfo对象
        """
        return ReqInfo(
            verb=self.verb,
            url=self.url,
            headers=self.headers.copy() if self.headers else {},
            body=self.body
        )
    
    def set_header(self, name: str, value: str) -> None:
        """
        设置请求头
        
        Args:
            name: 头名称
            value: 头值
        """
        if self.headers is None:
            self.headers = {}
        self.headers[name] = value


class ReqOptions:
    """
    请求选项配置类
    """
    
    def __init__(
        self,
        timeout: int = 0,
        retry: int = 0,
        verify_ssl: bool = False,
        allow_redirect: bool = False,
        proxy: str = ""
    ):
        """
        初始化请求选项
        
        Args:
            timeout: 超时时间（秒），0为默认值
            retry: 重试次数，0为默认值，-1代表关闭重试
            verify_ssl: 是否验证SSL证书，默认False
            allow_redirect: 是否允许重定向，默认False
            proxy: 代理地址，支持http/https代理，如 http://127.0.0.1:8080
        """
        self.timeout = timeout
        self.retry = retry
        self.verify_ssl = verify_ssl
        self.allow_redirect = allow_redirect
        self.proxy = proxy


class Session:
    """
    HTTP会话类，包含请求选项和会话配置
    """
    
    def __init__(self, options: Optional[ReqOptions] = None):
        """
        初始化会话
        
        Args:
            options: 请求选项
        """
        if options is None:
            options = ReqOptions()
        
        self.options = options
        self.client = self._create_client(options)
    
    def _create_client(self, options: ReqOptions) -> requests.Session:
        """
        根据选项创建requests会话
        
        Args:
            options: 请求选项
            
        Returns:
            requests.Session: 配置好的会话对象
        """
        session = requests.Session()
        
        # 设置超时
        timeout = options.timeout if options.timeout > 0 else DEFAULT_TIMEOUT
        
        # 配置适配器，处理重试
        retry_count = options.retry
        if retry_count == 0:
            retry_count = DEFAULT_RETRY
        elif retry_count == -1:
            retry_count = 0
        
        if retry_count > 0:
            adapter = HTTPAdapter(
                max_retries=retry_count,
                pool_connections=10,
                pool_maxsize=10
            )
            session.mount('http://', adapter)
            session.mount('https://', adapter)
        
        # 设置代理
        if options.proxy:
            session.proxies = {
                'http': options.proxy,
                'https': options.proxy
            }
        
        return session
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Response:
        """
        GET请求
        
        Args:
            url: 请求URL
            headers: 请求头
            
        Returns:
            Response: 响应对象
        """
        return self.do_request("GET", url, headers, None)
    
    def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None
    ) -> Response:
        """
        POST请求
        
        Args:
            url: 请求URL
            headers: 请求头
            body: 请求体
            
        Returns:
            Response: 响应对象
        """
        return self.do_request("POST", url, headers, body)
    
    def request(
        self,
        verb: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None
    ) -> Response:
        """
        自定义类型的请求
        
        Args:
            verb: HTTP方法
            url: 请求URL
            headers: 请求头
            body: 请求体
            
        Returns:
            Response: 响应对象
        """
        return self.do_request(verb, url, headers, body)
    
    def do_request(
        self,
        verb: str,
        url: str,
        headers: Optional[Dict[str, str]],
        body: Optional[bytes]
    ) -> Response:
        """
        执行实际的HTTP请求
        
        Args:
            verb: HTTP方法
            url: 请求URL
            headers: 请求头
            body: 请求体
            
        Returns:
            Response: 响应对象
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        verb = verb.upper()
        headers = headers or {}
        
        # 处理URL中的%号
        url = self._escape_percent_sign(url)
        
        # 创建请求
        try:
            req = requests.Request(verb, url, headers=headers, data=body)
            prepared = self.client.prepare_request(req)
        except Exception as e:
            # 多数情况下是url中包含%
            url = self._escape_percent_sign(url)
            req = requests.Request(verb, url, headers=headers, data=body)
            prepared = self.client.prepare_request(req)
        
        # 设置默认的headers头
        default_headers = {
            "User-Agent": DEFAULT_UA,
            "Range": f"bytes=0-{DEFAULT_RESPONSE_LENGTH}",
            "Connection": "close"
        }
        
        for key, value in default_headers.items():
            if key not in headers:
                prepared.headers[key] = value
        
        # 设置默认的Content-Type头
        if verb == "POST" and "Content-Type" not in headers:
            prepared.headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        
        # 覆盖Connection头
        prepared.headers["Connection"] = "close"
        
        # 设置超时
        timeout = self.options.timeout if self.options.timeout > 0 else DEFAULT_TIMEOUT
        
        # 是否允许重定向
        allow_redirect = self.options.allow_redirect
        
        # 发送请求
        try:
            resp = self.client.send(
                prepared,
                timeout=timeout,
                verify=self.options.verify_ssl,
                allow_redirects=allow_redirect
            )
        except Exception as e:
            raise Exception(f"error occurred during request: {e}")
        
        return Response(resp)
    
    @staticmethod
    def _escape_percent_sign(raw: str) -> str:
        """
        转义URL中的百分号
        
        Args:
            raw: 原始URL
            
        Returns:
            str: 转义后的URL
        """
        return raw.replace("%", "%25")


def url_parse(source_url: str) -> 'requests.models.PreparedRequest':
    """
    解析URL（主要用于兼容）
    
    Args:
        source_url: 原始URL
        
    Returns:
        PreparedRequest: 解析后的请求对象
    """
    return requests.Request('GET', source_url).prepare()


def _escape_percent_sign(raw: str) -> str:
    """
    转义URL中的百分号
    
    Args:
        raw: 原始URL
        
    Returns:
        str: 转义后的URL
    """
    return raw.replace("%", "%25")


def get_session_by_options(options: Optional[ReqOptions]) -> Session:
    """
    根据配置获取一个session
    
    Args:
        options: 请求选项
        
    Returns:
        Session: 会话对象
    """
    return Session(options)


def get(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    options: Optional[ReqOptions] = None
) -> Response:
    """
    GET请求
    
    Args:
        url: 请求URL
        headers: 请求头
        options: 请求选项
        
    Returns:
        Response: 响应对象
    """
    session = get_session_by_options(options)
    return session.do_request("GET", url, headers, None)


def request(
    verb: str,
    url: str,
    headers: Optional[Dict[str, str]],
    body: Optional[bytes],
    options: Optional[ReqOptions]
) -> Response:
    """
    自定义请求类型
    
    Args:
        verb: HTTP方法
        url: 请求URL
        headers: 请求头
        body: 请求体
        options: 请求选项
        
    Returns:
        Response: 响应对象
    """
    session = get_session_by_options(options)
    return session.do_request(verb, url, headers, body)


# 为了向后兼容，保留一些别名
HttpGet = get
HttpRequest = request
HttpSession = Session
HttpReqInfo = ReqInfo
HttpOptions = ReqOptions
