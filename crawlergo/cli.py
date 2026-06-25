#!/usr/bin/env python3
"""
crawlergo CLI - Python port of crawlergo
A powerful web crawler based on Chrome headless mode
"""

import click
import json
import sys
from . import CrawlerGo, Config


@click.command()
@click.option(
    '--chromium-path', '-c',
    required=True,
    help='Path to Chromium executable'
)
@click.option(
    '--chrome-ws-url', '-w',
    default='',
    help='Chrome WebSocket URL (if empty, will launch new Chrome)'
)
@click.option(
    '--custom-headers',
    default='',
    help='Custom request headers in JSON format'
)
@click.option(
    '--post-data', '-d',
    default='',
    help='POST data to send with requests'
)
@click.option(
    '--max-crawled-count', '-m',
    default=200,
    type=int,
    help='Maximum number of URLs to crawl (default: 200)'
)
@click.option(
    '--filter-mode', '-f',
    type=click.Choice(['simple', 'smart', 'strict'], case_sensitive=False),
    default='smart',
    help='Filter mode: simple/smart/strict (default: smart)'
)
@click.option(
    '--output-mode', '-o',
    type=click.Choice(['console', 'json', 'none'], case_sensitive=False),
    default='console',
    help='Output mode: console/json/none (default: console)'
)
@click.option(
    '--output-json',
    default='',
    help='Path to output JSON file (used with -o json)'
)
@click.option(
    '--max-tab-count', '-t',
    default=8,
    type=int,
    help='Maximum number of tabs (default: 8)'
)
@click.option(
    '--fuzz-path',
    is_flag=True,
    default=False,
    help='Enable path fuzzing'
)
@click.option(
    '--fuzz-path-dict',
    default='',
    help='Path to fuzz dictionary file'
)
@click.option(
    '--robots-path',
    is_flag=True,
    default=False,
    help='Parse robots.txt'
)
@click.option(
    '--request-proxy',
    default='',
    help='Proxy address for requests'
)
@click.option(
    '--encode-url',
    is_flag=True,
    default=False,
    help='Encode URL using detected charset'
)
@click.option(
    '--tab-run-timeout',
    default=20,
    type=int,
    help='Single tab run timeout in seconds (default: 20)'
)
@click.option(
    '--wait-dom-content-loaded-timeout',
    default=5,
    type=int,
    help='DOM content loaded timeout in seconds (default: 5)'
)
@click.option(
    '--event-trigger-mode',
    type=click.Choice(['async', 'sync'], case_sensitive=False),
    default='async',
    help='Event trigger mode: async/sync (default: async)'
)
@click.option(
    '--event-trigger-interval',
    default=100,
    type=int,
    help='Event trigger interval in milliseconds (default: 100)'
)
@click.option(
    '--before-exit-delay',
    default=1,
    type=int,
    help='Delay before exit in seconds (default: 1)'
)
@click.option(
    '--ignore-url-keywords', '-iuk',
    multiple=True,
    help='URL keywords to ignore (can specify multiple)'
)
@click.option(
    '--form-values', '-fv',
    default='',
    help='Form field values in JSON format'
)
@click.option(
    '--form-keyword-values', '-fkv',
    default='',
    help='Form keyword values in JSON format'
)
@click.option(
    '--push-to-proxy',
    default='',
    help='Push results to proxy address'
)
@click.option(
    '--push-pool-max',
    default=10,
    type=int,
    help='Maximum concurrent push workers (default: 10)'
)
@click.option(
    '--log-level',
    type=click.Choice(['debug', 'info', 'warn', 'error'], case_sensitive=False),
    default='info',
    help='Log level: debug/info/warn/error (default: info)'
)
@click.option(
    '--no-headless',
    is_flag=True,
    default=False,
    help='Disable headless mode'
)
@click.option(
    '--max-run-time',
    default=3600,
    type=int,
    help='Maximum run time in seconds (default: 3600)'
)
@click.argument('target_url', required=True)
def main(
    chromium_path,
    chrome_ws_url,
    custom_headers,
    post_data,
    max_crawled_count,
    filter_mode,
    output_mode,
    output_json,
    max_tab_count,
    fuzz_path,
    fuzz_path_dict,
    robots_path,
    request_proxy,
    encode_url,
    tab_run_timeout,
    wait_dom_content_loaded_timeout,
    event_trigger_mode,
    event_trigger_interval,
    before_exit_delay,
    ignore_url_keywords,
    form_values,
    form_keyword_values,
    push_to_proxy,
    push_pool_max,
    log_level,
    no_headless,
    max_run_time,
    target_url,
):
    """
    crawlergo - A powerful web crawler based on Chrome headless mode

    TARGET_URL: The target URL to crawl (required)
    """

    # Parse custom headers
    headers = None
    if custom_headers:
        try:
            headers = json.loads(custom_headers)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in --custom-headers: {e}", err=True)
            sys.exit(1)

    # Parse form values
    form_vals = None
    if form_values:
        try:
            form_vals = json.loads(form_values)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in --form-values: {e}", err=True)
            sys.exit(1)

    # Parse form keyword values
    form_kw_vals = None
    if form_keyword_values:
        try:
            form_kw_vals = json.loads(form_keyword_values)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON in --form-keyword-values: {e}", err=True)
            sys.exit(1)

    # Create configuration
    config = Config(
        chromium_path=chromium_path,
        chrome_ws_url=chrome_ws_url if chrome_ws_url else None,
        custom_headers=headers,
        post_data=post_data if post_data else None,
        max_crawled_count=max_crawled_count,
        filter_mode=filter_mode.lower(),
        output_mode=output_mode.lower(),
        output_json_path=output_json if output_json else None,
        max_tab_count=max_tab_count,
        fuzz_path=fuzz_path,
        fuzz_path_dict=fuzz_path_dict if fuzz_path_dict else None,
        robots_path=robots_path,
        request_proxy=request_proxy if request_proxy else None,
        encode_url=encode_url,
        tab_run_timeout=tab_run_timeout,
        wait_dom_content_loaded_timeout=wait_dom_content_loaded_timeout,
        event_trigger_mode=event_trigger_mode.lower(),
        event_trigger_interval=event_trigger_interval / 1000.0,  # Convert ms to seconds
        before_exit_delay=before_exit_delay,
        ignore_url_keywords=list(ignore_url_keywords) if ignore_url_keywords else None,
        form_values=form_vals,
        form_keyword_values=form_kw_vals,
        push_to_proxy=push_to_proxy if push_to_proxy else None,
        push_pool_max=push_pool_max,
        log_level=log_level.lower(),
        headless=not no_headless,
        max_run_time=max_run_time,
    )

    # Create crawler instance
    crawler = CrawlerGo(config)

    # Run crawler
    try:
        result = crawler.run(target_url)

        # Handle output
        if output_mode.lower() == 'console' or output_mode.lower() == 'none':
            if result:
                for url_info in result:
                    click.echo(url_info.get('url', ''))
        elif output_mode.lower() == 'json':
            if result:
                if output_json:
                    with open(output_json, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    click.echo(f"Results written to {output_json}")
                else:
                    click.echo(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    finally:
        crawler.close()


if __name__ == '__main__':
    main()
