"""
Tab module for crawlergo.
Implements Tab class with browser page control, form filling, event triggering, and request interception.
"""

import asyncio
import base64
import json
import re
import threading
import time
from typing import Optional, List, Dict, Any, Callable
from urllib.parse import urlparse, urlencode

from playwright.sync_api import sync_playwright, Page, BrowserContext, Route, Request as PlaywrightRequest, Response as PlaywrightResponse
from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError

from . import config
from . import js_scripts as js
from .model import URL, Request, GetUrl, GetRequest, Options


class TabConfig:
    """Tab configuration options."""

    def __init__(
        self,
        tab_run_timeout: float = 20.0,
        dom_content_loaded_timeout: float = 5.0,
        event_trigger_mode: str = "async",
        event_trigger_interval: float = 0.1,
        before_exit_delay: float = 1.0,
        encode_url_with_charset: bool = False,
        ignore_keywords: Optional[List[str]] = None,
        proxy: str = "",
        custom_form_values: Optional[Dict[str, str]] = None,
        custom_form_keyword_values: Optional[Dict[str, str]] = None,
    ):
        self.TabRunTimeout = tab_run_timeout
        self.DomContentLoadedTimeout = dom_content_loaded_timeout
        self.EventTriggerMode = event_trigger_mode
        self.EventTriggerInterval = event_trigger_interval
        self.BeforeExitDelay = before_exit_delay
        self.EncodeURLWithCharset = encode_url_with_charset
        self.IgnoreKeywords = ignore_keywords or []
        self.Proxy = proxy
        self.CustomFormValues = custom_form_values or {}
        self.CustomFormKeywordValues = custom_form_keyword_values or {}


class Tab:
    """
    Tab class for managing a single browser tab/page.
    Handles navigation, form filling, event triggering, and request interception.
    """

    def __init__(
        self,
        browser_context: BrowserContext,
        navigate_req: Request,
        tab_config: TabConfig,
        extra_headers: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a new Tab.

        Args:
            browser_context: Playwright BrowserContext
            navigate_req: Initial navigation request
            tab_config: Tab configuration
            extra_headers: Extra HTTP headers to include
        """
        self.ctx = browser_context
        self.cancel_func: Optional[Callable] = None
        self.NavigateReq = navigate_req
        self.ExtraHeaders = extra_headers or {}
        self.ResultList: List[Request] = []
        self.TopFrameId = ""
        self.LoaderID = ""
        self.NavNetworkID = ""
        self.PageCharset = ""
        self.FoundRedirection = False
        self.DocBodyNodeId: Optional[int] = None
        self.config = tab_config

        self.lock = threading.Lock()

        # Wait groups for synchronization
        self.WG = threading.Semaphore(0)
        self.collect_link_WG = threading.Semaphore(0)
        self.loaded_WG = threading.Semaphore(0)
        self.form_submit_WG = threading.Semaphore(0)
        self.remove_lis_WG = threading.Semaphore(0)
        self.dom_WG = threading.Semaphore(0)
        self.fill_form_WG = threading.Semaphore(0)

        # Internal flags
        self._dom_content_loaded_run = False
        self._page: Optional[Page] = None
        self._pending_requests: Dict[str, threading.Event] = {}

    def start(self) -> None:
        """
        Start tab crawling/navigation.
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Crawling {self.NavigateReq.Method} {self.NavigateReq.URL.get_url()}")

        try:
            # Create new page
            self._page = self.ctx.new_page()

            # Set up route interception for request blocking
            self._setup_route_interception()

            # Set up bindings for addLink callback
            self._page.expose_function("addLink", self._handle_add_link)
            self._page.expose_function("Test", self._handle_test)

            # Add initialization script
            self._page.add_init_script(js.TabInitJS)

            # Set extra headers
            if self.ExtraHeaders:
                self._page.set_extra_http_headers(self.ExtraHeaders)

            # Navigate to target
            nav_url = self.NavigateReq.URL.get_url()
            self._page.goto(nav_url, timeout=self.config.DomContentLoadedTimeout * 1000)

            # Wait for DOM content loaded
            self._wait_for_dom_content_loaded()

            # Execute after DOM tasks
            self._after_dom_run()

            # Wait for all tasks
            self._wait_for_tasks()

            # Collect links
            self._collect_links()

            # Encode URLs if needed
            if self.config.EncodeURLWithCharset:
                self._detect_charset()
                self._encode_all_url_with_charset()

        except Exception as e:
            logger.warning(f"Navigation error: {e}")
        finally:
            if self._page:
                self._page.close()

    def _setup_route_interception(self) -> None:
        """Set up route interception for request handling."""
        def handle_route(route: Route) -> None:
            request = route.request
            url = request.url

            # Check if this is the main navigation request
            if not self.NavNetworkID and request.resource_type == "document":
                self.NavNetworkID = request.url

            # Check ignore keywords
            for keyword in self.config.IgnoreKeywords:
                if keyword in url:
                    route.abort()
                    return

            # Check for static resources
            parsed = urlparse(url)
            path = parsed.path
            if '.' in path:
                ext = path.rsplit('.', 1)[-1].lower()
                if ext in config.StaticSuffixSet:
                    route.abort()
                    return

            # Continue request
            route.continue_()

        self.ctx.route("**/*", handle_route)

    def _handle_add_link(self, data: str) -> None:
        """Handle addLink binding callback."""
        try:
            payload = json.loads(data)
            name = payload.get("name")
            seq = payload.get("seq")
            args = payload.get("args", [])

            if name == "addLink" and len(args) > 1:
                self.add_result_url(config.GET, args[0], args[1])

            # Deliver result
            result_js = js.make_deliver_result(name, seq, "s")
            if self._page:
                self._page.evaluate(result_js)
        except Exception:
            pass

    def _handle_test(self, data: str) -> None:
        """Handle Test binding callback."""
        pass

    def _wait_for_dom_content_loaded(self) -> None:
        """Wait for DOM content to be loaded."""
        if self._page:
            try:
                self._page.wait_for_load_state("domcontentloaded", timeout=self.config.DomContentLoadedTimeout * 1000)
            except PlaywrightTimeoutError:
                pass

    def _wait_for_tasks(self) -> None:
        """Wait for all background tasks to complete."""
        # For simplicity, we use synchronous execution
        # In async version, this would await all tasks
        pass

    def _after_dom_run(self) -> None:
        """Execute tasks after DOMContentLoaded."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("afterDOMRun start")

        # Get body node ID
        if not self._get_body_node_id():
            logger.debug("no body document NodeID, exit.")
            return

        # Execute fill form and set observer in parallel
        fill_form_thread = threading.Thread(target=self._fill_form)
        observer_thread = threading.Thread(target=self._set_observer_js)

        fill_form_thread.start()
        observer_thread.start()

        fill_form_thread.join()
        observer_thread.join()

        logger.debug("afterDOMRun end")

        # Schedule after loaded run
        after_loaded_thread = threading.Thread(target=self._after_loaded_run)
        after_loaded_thread.start()

    def _get_body_node_id(self) -> bool:
        """Get body node ID for later queries."""
        if not self._page:
            return False

        try:
            # Wait briefly for body to be available
            self._page.wait_for_selector("body", timeout=3000)
            body = self._page.query_selector("body")
            if body:
                # Store the handle for later use
                self.DocBodyNodeId = body
                return True
        except Exception:
            pass
        return False

    def _fill_form(self) -> None:
        """Fill form inputs, textareas, and select elements."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("fillForm start")

        fill_form = FillForm(tab=self)
        fill_form.fill_input()
        fill_form.fill_multi_select()
        fill_form.fill_textarea()

        logger.debug("fillForm end")

    def _set_observer_js(self) -> None:
        """Set up DOM node mutation observer."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("setObserverJS start")

        if self._page:
            self._page.evaluate(js.ObserverJS)

        logger.debug("setObserverJS end")

    def _after_loaded_run(self) -> None:
        """Execute tasks after page Load event."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("afterLoadedRun start")

        # Form submission
        form_submit_thread = threading.Thread(target=self._form_submit)
        form_submit_thread.start()
        form_submit_thread.join()

        logger.debug("formSubmit end")

        # Event triggering based on mode
        if self.config.EventTriggerMode == config.EventTriggerAsync:
            threads = []
            for func in [self._trigger_javascript_protocol, self._trigger_inline_events, self._trigger_dom2_events]:
                t = threading.Thread(target=func)
                threads.append(t)
                t.start()

            for t in threads:
                t.join()
        elif self.config.EventTriggerMode == config.EventTriggerSync:
            self._trigger_inline_events()
            time.sleep(self.config.EventTriggerInterval)
            self._trigger_dom2_events()
            time.sleep(self.config.EventTriggerInterval)
            self._trigger_javascript_protocol()

        # Wait before exit
        time.sleep(self.config.BeforeExitDelay)

        # Remove DOM listeners
        remove_thread = threading.Thread(target=self._remove_dom_listener)
        remove_thread.start()
        remove_thread.join()

        logger.debug("afterLoadedRun end")

    def _form_submit(self) -> None:
        """Auto-submit forms."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("formSubmit start")

        # Set form targets
        self._set_form_to_frame()

        # Try different submission methods
        threads = []
        for func in [self._click_submit, self._click_all_button]:
            t = threading.Thread(target=func)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    def _set_form_to_frame(self) -> None:
        """Set form target to hidden iframe."""
        if not self._page:
            return

        try:
            # Generate random frame name
            import secrets
            frame_name = secrets.token_hex(4)

            # Create hidden iframe
            self._page.evaluate(js.make_new_frame(frame_name, frame_name))

            # Set all forms to target the iframe
            forms = self._page.query_selector_all("form")
            for form in forms:
                form.evaluate(f"this.target = '{frame_name}'")
        except Exception:
            pass

    def _click_submit(self) -> None:
        """Click submit buttons and submit forms."""
        if not self._page:
            return

        try:
            # Try form submit
            forms = self._page.query_selector_all("form")
            for form in forms:
                try:
                    form.evaluate("this.submit()")
                except Exception:
                    pass

            # Try input[type=submit]
            submits = self._page.query_selector_all("form input[type=submit]")
            for submit in submits:
                try:
                    submit.click()
                except Exception:
                    pass
        except Exception:
            pass

    def _click_all_button(self) -> None:
        """Click all buttons in forms."""
        if not self._page:
            return

        try:
            # Click form buttons
            buttons = self._page.query_selector_all("form button")
            for button in buttons:
                try:
                    button.click()
                except Exception:
                    pass

            # Use JS click for all buttons
            all_buttons = self._page.query_selector_all("button")
            for button in all_buttons:
                try:
                    self._evaluate_with_node(js.make_form_node_click("this"), button)
                except Exception:
                    pass
        except Exception:
            pass

    def _trigger_inline_events(self) -> None:
        """Trigger inline events (onclick, onchange, etc.)."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("triggerInlineEvents start")

        if self._page:
            script = js.make_trigger_inline_event(self.config.EventTriggerInterval * 1000)
            self._page.evaluate(script)

        logger.debug("triggerInlineEvents end")

    def _trigger_dom2_events(self) -> None:
        """Trigger DOM2 level events."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("triggerDom2Events start")

        if self._page:
            script = js.make_trigger_dom2_event(self.config.EventTriggerInterval * 1000)
            self._page.evaluate(script)

        logger.debug("triggerDom2Events end")

    def _trigger_javascript_protocol(self) -> None:
        """Trigger javascript: protocol links."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("clickATagJavascriptProtocol start")

        if self._page:
            script = js.make_trigger_javascript_protocol(self.config.EventTriggerInterval * 1000)
            self._page.evaluate(script)

        logger.debug("clickATagJavascriptProtocol end")

    def _remove_dom_listener(self) -> None:
        """Remove DOM node change listeners."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("RemoveDOMListener start")

        if self._page:
            self._page.evaluate(js.RemoveDOMListenerJS)

        logger.debug("RemoveDOMListener end")

    def _collect_links(self) -> None:
        """Collect links from various sources."""
        import logging
        logger = logging.getLogger(__name__)

        logger.debug("collectLinks start")

        threads = []
        for func in [self._collect_href_links, self._collect_object_links, self._collect_comment_links]:
            t = threading.Thread(target=func)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        logger.debug("collectLinks end")

    def _collect_href_links(self) -> None:
        """Collect links from src, href, data-url, data-href attributes."""
        if not self._page:
            return

        try:
            attr_names = ["src", "href", "data-url", "data-href"]
            for attr_name in attr_names:
                try:
                    elements = self._page.query_selector_all(f"[{attr_name}]")
                    for elem in elements:
                        value = elem.get_attribute(attr_name)
                        if value:
                            self.add_result_url(config.GET, value, config.FromDOM)
                except Exception:
                    pass
        except Exception:
            pass

    def _collect_object_links(self) -> None:
        """Collect links from object[data] elements."""
        if not self._page:
            return

        try:
            objects = self._page.query_selector_all("object[data]")
            for obj in objects:
                data = obj.get_attribute("data")
                if data:
                    self.add_result_url(config.GET, data, config.FromDOM)
        except Exception:
            pass

    def _collect_comment_links(self) -> None:
        """Collect URLs from HTML comments."""
        if not self._page:
            return

        try:
            # Get page content and find comments
            content = self._page.content()
            url_regex = re.compile(config.URLRegex)
            comments = re.findall(r'<!--(.*?)-->', content, re.DOTALL)

            for comment in comments:
                urls = url_regex.findall(comment)
                for url in urls:
                    if isinstance(url, tuple):
                        url = url[0] if url[0] else url[1] if len(url) > 1 else ""
                    if url:
                        self.add_result_url(config.GET, url, config.FromComment)
        except Exception:
            pass

    def _detect_charset(self) -> None:
        """Detect page charset from meta tags."""
        if not self._page:
            return

        try:
            meta = self._page.query_selector('meta[http-equiv="Content-Type"]')
            if meta:
                content = meta.get_attribute("content")
                if content and "charset=" in content:
                    charset = content.split("charset=")[-1].strip()
                    self.PageCharset = charset.upper()
        except Exception:
            pass

    def _encode_all_url_with_charset(self) -> None:
        """Encode all URLs with detected charset."""
        if not self.PageCharset or self.PageCharset == "UTF-8":
            return

        try:
            for req in self.ResultList:
                if hasattr(req.URL, 'RawQuery') and req.URL.RawQuery:
                    # Encode query with charset
                    encoded_query = req.URL.RawQuery.encode(self.PageCharset).decode('utf-8')
                    req.URL._parsed = req.URL._parsed._replace(query=encoded_query)
        except Exception:
            pass

    def add_result_url(self, method: str, _url: str, source: str) -> None:
        """
        Add URL to result list with proper handling.

        Args:
            method: HTTP method
            _url: URL string
            source: Request source type
        """
        nav_url = self.NavigateReq.URL
        url = GetUrl(_url, nav_url)
        if url is None:
            return

        option = Options(
            headers={},
            post_data=""
        )
        referer = nav_url.get_url()

        # Handle Host binding
        if "Host" in self.NavigateReq.Headers:
            host = self.NavigateReq.Headers["Host"]
            if nav_url.hostname != host and url.hostname == host:
                url_str = url.get_url().replace(f"://{url.hostname}", f"://{nav_url.hostname}", 1)
                url = GetUrl(url_str, nav_url)
                option.Headers["Host"] = host
                referer = nav_url.get_url().replace(nav_url.netloc, str(host), 1)

        # Add Cookie
        if "Cookie" in self.NavigateReq.Headers:
            option.Headers["Cookie"] = self.NavigateReq.Headers["Cookie"]

        # Fix Referer
        option.Headers["Referer"] = referer

        # Add extra headers
        for key, value in self.ExtraHeaders.items():
            option.Headers[key] = value

        req = GetRequest(method, url, option)
        req.Source = source

        with self.lock:
            self.ResultList.append(req)

    def add_result_request(self, req: Request) -> None:
        """
        Add request directly to result list.

        Args:
            req: Request object
        """
        # Add extra headers
        for key, value in self.ExtraHeaders.items():
            req.Headers[key] = value

        with self.lock:
            self.ResultList.append(req)

    def evaluate(self, expression: str) -> Any:
        """
        Execute JavaScript expression.

        Args:
            expression: JavaScript code to execute

        Returns:
            Result of evaluation
        """
        if not self._page:
            return None

        try:
            return self._page.evaluate(expression)
        except Exception:
            return None

    def get_node_ids(self, selector: str) -> List[Any]:
        """
        Get node IDs by CSS selector.

        Args:
            selector: CSS selector

        Returns:
            List of matching elements
        """
        if not self._page:
            return []

        try:
            return self._page.query_selector_all(selector)
        except Exception:
            return []

    def evaluate_with_node(self, expression: str, node: Any) -> Any:
        """
        Execute JavaScript with node context.

        Args:
            expression: JavaScript expression
            node: Node element

        Returns:
            Result of evaluation
        """
        if not self._page or not node:
            return None

        try:
            return node.evaluate(expression)
        except Exception:
            return None

    def dismiss_dialog(self) -> None:
        """Dismiss any open dialog."""
        if self._page:
            self._page.on("dialog", lambda dialog: dialog.dismiss())


class FillForm:
    """Form filling helper class."""

    def __init__(self, tab: Tab):
        """
        Initialize FillForm.

        Args:
            tab: Parent Tab object
        """
        self.tab = tab

    def fill_input(self) -> None:
        """Fill input elements with appropriate values."""
        if not self.tab._page:
            return

        try:
            inputs = self.tab._page.query_selector_all("input")
            for inp in inputs:
                try:
                    attr_type = inp.get_attribute("type") or "text"

                    if attr_type in ("text", "email", "password", "tel", ""):
                        name = (inp.get_attribute("id") or "") + (inp.get_attribute("class") or "") + (inp.get_attribute("name") or "")
                        value = self.get_match_input_text(name)
                        inp.fill(value)

                    elif attr_type in ("radio", "checkbox"):
                        inp.evaluate("this.checked = true")

                    elif attr_type in ("file", "image"):
                        # For file inputs, set a dummy path
                        inp.evaluate("this.required = false")
                        # Note: actual file upload not supported in headless mode
                except Exception:
                    pass
        except Exception:
            pass

    def fill_textarea(self) -> None:
        """Fill textarea elements."""
        if not self.tab._page:
            return

        try:
            textareas = self.tab._page.query_selector_all("textarea")
            value = self.get_match_input_text("other")
            for textarea in textareas:
                try:
                    textarea.fill(value)
                except Exception:
                    pass
        except Exception:
            pass

    def fill_multi_select(self) -> None:
        """Fill select elements by selecting first option."""
        if not self.tab._page:
            return

        try:
            selects = self.tab._page.query_selector_all("select")
            for select in selects:
                try:
                    options = select.query_selector_all("option")
                    if options:
                        options[0].evaluate("this.selected = true")
                except Exception:
                    pass
        except Exception:
            pass

    def get_match_input_text(self, name: str) -> str:
        """
        Get matching input text based on element name/id/class.

        Args:
            name: Combined attribute string

        Returns:
            Matched text value
        """
        # Check custom keyword values first
        for key, value in self.tab.config.CustomFormKeywordValues.items():
            if key.lower() in name.lower():
                return value

        name_lower = name.lower()

        # Check against input text map
        for key, item in config.InputTextMap.items():
            keywords = item.get("keyword", [])
            for keyword in keywords:
                if keyword.lower() in name_lower:
                    custom_value = self.tab.config.CustomFormValues.get(key)
                    if custom_value:
                        return custom_value
                    return item.get("value", "")

        # Return default
        return self.tab.config.CustomFormValues.get("default", config.DefaultInputText)


def is_ignored_by_keyword_match(req: Request, ignore_keywords: List[str]) -> bool:
    """
    Check if request should be ignored based on keywords.

    Args:
        req: Request object
        ignore_keywords: List of keywords to ignore

    Returns:
        True if should be ignored
    """
    import logging
    logger = logging.getLogger(__name__)

    url_str = req.URL.get_url()
    for keyword in ignore_keywords:
        if keyword in url_str:
            logger.info(f"ignore request: {req.simple_format()}")
            return True
    return False
