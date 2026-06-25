from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional, List
import threading


class BrowserManager:
    def __init__(
        self,
        chromium_path: str = "",
        extra_headers: Optional[dict] = None,
        proxy: str = "",
        no_headless: bool = False,
        ws_endpoint: str = ""
    ):
        """
        初始化浏览器管理器

        Args:
            chromium_path: Chromium可执行文件路径
            extra_headers: 额外的请求头
            proxy: 代理地址
            no_headless: 是否禁用无头模式
            ws_endpoint: WebSocket端点，用于连接已运行的Chrome
        """
        self.chromium_path = chromium_path
        self.extra_headers = extra_headers or {}
        self.proxy = proxy
        self.no_headless = no_headless
        self.ws_endpoint = ws_endpoint

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.tabs: List[BrowserContext] = []
        self.lock = threading.Lock()

    def init_browser(self) -> "BrowserManager":
        """
        初始化Chrome headless浏览器
        """
        self.playwright = sync_playwright().start()

        if self.ws_endpoint:
            # 通过wsEndpoint连接已运行的Chrome
            self.browser = self.playwright.chromium.connect_over_cdp(self.ws_endpoint)
            self.context = self.browser.contexts[0] if self.browser.contexts else self.browser.new_context()
        else:
            # 创建新的浏览器实例
            browser_args = [
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--ignore-certificate-errors",
                "--disable-images",
                "--disable-web-security",
                "--disable-xss-auditor",
                "--allow-running-insecure-content",
                "--disable-webgl",
                "--disable-popup-blocking",
                "--window-size=1920,1080",
            ]

            launch_options = {
                "headless": not self.no_headless,
                "args": browser_args,
            }

            if self.chromium_path:
                launch_options["executable_path"] = self.chromium_path

            if self.proxy:
                launch_options["proxy"] = {"server": self.proxy}

            self.browser = self.playwright.chromium.launch(**launch_options)
            self.context = self.browser.new_context(
                extra_http_headers=self.extra_headers
            )

        return self

    def new_tab(self, timeout: int = 30000) -> tuple:
        """
        创建新标签页

        Args:
            timeout: 超时时间（毫秒）

        Returns:
            (BrowserContext, cancel_func) 元组
        """
        with self.lock:
            ctx = self.browser.new_context(
                extra_http_headers=self.extra_headers
            )
            self.tabs.append(ctx)

        def cancel():
            with self.lock:
                if ctx in self.tabs:
                    self.tabs.remove(ctx)
                ctx.close()

        return ctx, cancel

    def close(self):
        """
        关闭浏览器
        """
        # 关闭所有标签页
        with self.lock:
            for ctx in self.tabs:
                try:
                    ctx.close()
                except Exception:
                    pass
            self.tabs.clear()

        # 关闭主上下文
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass

        # 关闭浏览器
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass

        # 停止playwright
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass


# 兼容旧版本的类名
Browser = BrowserManager
