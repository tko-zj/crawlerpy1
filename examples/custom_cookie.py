"""
crawlergo 自定义 Cookie 示例

展示如何:
- 设置自定义 Cookie
- 添加自定义请求头
- 模拟登录状态爬取
"""

from crawlergo.task import TaskConfig, CrawlerTask, GetRequest, GetUrl
from crawlergo.model import Options


def crawl_with_custom_cookie():
    """自定义 Cookie 爬取示例"""

    target_url = "https://example.com"

    # 1. 自定义 Cookie
    custom_cookie = "session_id=abc123; user_id=1001; is_login=true"

    # 2. 自定义请求头 (可选)
    custom_headers = {
        "Cookie": custom_cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://example.com/login",
    }

    # 3. 解析 URL
    url = GetUrl(target_url)
    if not url:
        print("URL 解析失败")
        return

    # 4. 使用 Options 设置请求头
    options = Options(
        headers=custom_headers,
        post_data=""
    )
    request = GetRequest("GET", url, options)

    # 5. 配置任务
    config = TaskConfig(
        max_crawl_count=100,
        filter_mode="smart",
        extra_headers=custom_headers,    # 通过 extra_headers 也可以设置
        # 或者使用字符串形式
        # extra_headers_string='{"Cookie": "session_id=abc123"}',
    )

    # 6. 创建并执行爬虫
    crawler = CrawlerTask.new_crawler_task(
        targets=[request],
        task_config=config
    )

    print(f"使用自定义 Cookie 爬取: {target_url}")
    print(f"Cookie: {custom_cookie}")
    crawler.run()

    # 7. 处理结果
    result = crawler.Result
    print(f"\n爬取完成! 共获取 {len(result.ReqList)} 个URL")

    return result


def crawl_with_post_data():
    """POST 请求示例 (发送表单数据)"""

    target_url = "https://example.com/login"

    # 自定义表单数据
    post_data = "username=admin&password=admin123&captcha=1234"

    # 自定义请求头
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "csrf_token=xxx",
    }

    url = GetUrl(target_url)
    if not url:
        print("URL 解析失败")
        return

    # 使用 Options 设置 POST 数据
    options = Options(
        headers=headers,
        post_data=post_data
    )
    request = GetRequest("POST", url, options)

    config = TaskConfig(
        max_crawl_count=50,
        filter_mode="smart",
    )

    crawler = CrawlerTask.new_crawler_task(
        targets=[request],
        task_config=config
    )

    print(f"发送 POST 请求到: {target_url}")
    print(f"POST 数据: {post_data}")
    crawler.run()

    result = crawler.Result
    print(f"\n爬取完成! 共获取 {len(result.ReqList)} 个URL")

    return result


if __name__ == "__main__":
    print("=== 自定义 Cookie 示例 ===")
    crawl_with_custom_cookie()

    print("\n" + "="*50 + "\n")

    print("=== POST 请求示例 ===")
    crawl_with_post_data()
