"""
crawlergo 基础使用示例

展示如何:
- 导入 crawlergo 模块
- 配置爬虫任务
- 执行爬虫
- 处理结果
"""

from crawlergo.task import TaskConfig, CrawlerTask, GetRequest, GetUrl


def basic_crawl():
    """基础爬取示例"""
    # 1. 定义目标 URL
    target_url = "https://example.com"

    # 2. 解析 URL
    url = GetUrl(target_url)
    if not url:
        print("URL 解析失败")
        return

    # 3. 创建请求对象
    request = GetRequest("GET", url)

    # 4. 配置任务参数
    config = TaskConfig(
        max_crawl_count=100,        # 最大爬取数量
        filter_mode="smart",        # 过滤模式: simple/smart/strict
        tab_run_timeout=None,       # 使用默认超时 (20秒)
        dom_content_loaded_timeout=None,  # DOM加载超时 (5秒)
    )

    # 5. 创建爬虫任务
    crawler = CrawlerTask.new_crawler_task(
        targets=[request],
        task_config=config
    )

    # 6. 执行爬虫
    print(f"开始爬取: {target_url}")
    crawler.run()

    # 7. 处理结果
    result = crawler.Result

    print(f"\n爬取完成!")
    print(f"同域名结果数量: {len(result.ReqList)}")
    print(f"所有结果数量: {len(result.AllReqList)}")
    print(f"所有域名: {result.AllDomainList}")
    print(f"子域名: {result.SubDomainList}")

    # 8. 遍历请求结果
    print("\n--- 爬取到的 URL (前10个) ---")
    for i, req in enumerate(result.ReqList[:10]):
        print(f"{i+1}. [{req.Method}] {req.URL.get_url()}")

    return result


if __name__ == "__main__":
    basic_crawl()
