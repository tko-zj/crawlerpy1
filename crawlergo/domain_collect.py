"""
域名收集模块
提供子域名收集和全部域名收集功能
"""

from typing import List

from .model import Request


def sub_domain_collect(req_list: List[Request], host_limit: str) -> List[str]:
    """
    从请求列表中收集子域名（匹配host_limit后缀的域名）

    Args:
        req_list: 请求列表
        host_limit: 域名后缀限制，如 "example.com"

    Returns:
        子域名列表
    """
    unique_set = set()
    sub_domain_list = []

    for req in req_list:
        domain = req.URL.hostname
        if domain in unique_set:
            continue
        unique_set.add(domain)
        if domain.endswith("." + host_limit):
            sub_domain_list.append(domain)

    return sub_domain_list


def all_domain_collect(req_list: List[Request]) -> List[str]:
    """
    从请求列表中收集所有域名（去重）

    Args:
        req_list: 请求列表

    Returns:
        所有域名列表
    """
    unique_set = set()
    all_domain_list = []

    for req in req_list:
        domain = req.URL.hostname
        if domain in unique_set:
            continue
        unique_set.add(domain)
        all_domain_list.append(domain)

    return all_domain_list
