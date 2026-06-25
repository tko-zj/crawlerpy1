"""
crawlergo 使用代理示例

展示如何:
- 配置 HTTP/SOCKS 代理
- 通过代理执行爬虫
- 处理代理认证
"""

from crawlergo.task import TaskConfig, CrawlerTask, GetRequest, GetUrl


def crawl_with_proxy():
    """使用代理爬取示例"""

    # 1. 目标 URL
    target_url = "https://example.com"

    # 2. 配置代理
    # 支持 HTTP、HTTPS、SOCKS4、SOCKS5 代理
    proxy = "http://127.0.0.1:8080"      # HTTP 代理
    # proxy = "socks5://user:pass@127.0.0.1:1080"  # 带认证的 SOCKS5 代理

    # 3. 解析 URL 并创建请求
    url = GetUrl(target_url)
    if not url:
        print("URL 解析失败")
        return

    request = GetRequest("GET", url)

    # 4. 配置任务 (代理设置在 TaskConfig 中)
    config = TaskConfig(
        max_crawl_count=100,
        filter_mode="smart",
        proxy=proxy,                  # 设置代理
        dom_content_loaded_timeout=None,
    )

    # 5. 创建并执行爬虫
    crawler = CrawlerTask.new_crawler_task(
        targets=[request],
        task_config=config
    )

    print(f"使用代理 {proxy} 爬取: {target_url}")
    crawler.run()

    # 6. 处理结果
    result = crawler.Result
    print(f"\n爬取完成! 共获取 {len(result.ReqList)} 个URL")

    return result


if __name__ == "__main__":
    crawl_with_proxy()
