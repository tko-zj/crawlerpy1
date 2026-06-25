"""
工具函数模块
提供MD5哈希、Header转换、文件读写、随机字符串生成等功能
"""

import hashlib
import random
import string
import time
from typing import List, Dict, Any


# 随机数相关常量
LETTER_BYTES = string.ascii_letters + string.digits
LETTER_BYTES_LOWER = string.ascii_lowercase + string.digits


def str_md5(s: str) -> str:
    """
    计算字符串的MD5哈希值
    
    Args:
        s: 输入字符串
        
    Returns:
        str: MD5哈希值的十六进制表示
    """
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def convert_headers(h: Dict[str, Any]) -> Dict[str, str]:
    """
    将map[string]interface{}类型的headers转换为map[string]string
    
    Args:
        h: 原始headers字典，值为任意类型
        
    Returns:
        Dict[str, str]: 转换后的headers字典
    """
    result = {}
    for key, value in h.items():
        result[key] = str(value)
    return result


def write_file(file_name: str, content: bytes) -> None:
    """
    写入内容到文件
    
    Args:
        file_name: 文件路径
        content: 要写入的字节内容
    """
    try:
        with open(file_name, 'wb') as f:
            f.write(content)
    except Exception as e:
        print(f"Error writing to file: {e}")


def read_file(file_path: str) -> List[str]:
    """
    读取文件内容，按行返回
    
    Args:
        file_path: 文件路径
        
    Returns:
        List[str]: 文件内容的行列表
    """
    lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                lines.append(line)
    except Exception as e:
        print(f"Error reading file: {e}")
    return lines


def string_slice_contain(data: List[str], item: str) -> bool:
    """
    检查字符串列表是否包含指定元素
    
    Args:
        data: 字符串列表
        item: 要查找的字符串
        
    Returns:
        bool: 是否包含
    """
    return item in data


def map_string_format(data: Dict[str, str]) -> str:
    """
    将字典格式化为key=value,key=value格式的字符串
    
    Args:
        data: 字典数据
        
    Returns:
        str: 格式化后的字符串
    """
    if not data:
        return ""
    parts = [f"{key}={value}" for key, value in data.items()]
    return ",".join(parts)


def rand_seq(n: int) -> str:
    """
    生成长度为n的随机序列，包含大小写字母和数字
    
    Args:
        n: 随机字符串长度
        
    Returns:
        str: 随机字符串
    """
    return ''.join(random.choice(LETTER_BYTES) for _ in range(n))


# 为了向后兼容，保留一些别名
MD5 = str_md5
Headers = convert_headers
FileWrite = write_file
FileRead = read_file
SliceContain = string_slice_contain
FormatMap = map_string_format
RandString = rand_seq
