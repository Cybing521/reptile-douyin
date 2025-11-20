import re
import csv
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

def parse_douyin_time(time_str: str) -> datetime:
    """
    解析抖音的时间字符串，转换为 datetime 对象。
    支持格式: "刚刚", "x分钟前", "x小时前", "昨天", "x天前", "MM-DD", "YYYY-MM-DD"
    """
    now = datetime.now()
    time_str = time_str.strip()

    if "刚刚" in time_str:
        return now
    
    if "分钟前" in time_str:
        minutes = int(re.search(r'(\d+)', time_str).group(1))
        return now - timedelta(minutes=minutes)
    
    if "小时前" in time_str:
        hours = int(re.search(r'(\d+)', time_str).group(1))
        return now - timedelta(hours=hours)
    
    if "昨天" in time_str:
        return now - timedelta(days=1)
    
    if "天前" in time_str:
        days = int(re.search(r'(\d+)', time_str).group(1))
        return now - timedelta(days=days)
    
    # 处理日期格式
    try:
        if re.match(r'\d{4}-\d{2}-\d{2}', time_str):
            return datetime.strptime(time_str, "%Y-%m-%d")
        if re.match(r'\d{2}-\d{2}', time_str):
            # 默认为当年
            return datetime.strptime(f"{now.year}-{time_str}", "%Y-%m-%d")
    except ValueError:
        pass

    # 如果无法解析，返回当前时间（或抛出异常，视需求而定）
    # 这里为了稳健性，返回一个较旧的时间以避免错误包含
    print(f"Warning: Could not parse time string '{time_str}', defaulting to now.")
    return now

def is_target_comment(text: str, keywords: List[str]) -> str | None:
    """
    检查评论是否包含关键词。
    返回命中的第一个关键词，如果没有命中则返回 None。
    """
    if not text:
        return None
    
    for kw in keywords:
        if kw in text:
            return kw
    return None

def save_to_csv(data: List[Dict[str, Any]], filepath: str):
    """
    将数据保存到 CSV 文件。如果文件不存在则创建并写入表头，否则追加。
    """
    if not data:
        return

    file_exists = os.path.isfile(filepath)
    keys = data[0].keys()

    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)
    
    print(f"Saved {len(data)} records to {filepath}")

def save_to_json(data: List[Dict[str, Any]], filepath: str):
    """
    将数据保存到 JSON 文件。
    如果文件存在，读取原有数据，追加新数据后重写。
    """
    if not data:
        return

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    existing_data = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            pass
    
    # 转换 datetime 对象为字符串以支持 JSON 序列化
    # 注意：这里假设 data 中的 datetime 已经被处理过，或者我们需要在这里处理
    # 由于 parse_douyin_time 返回 datetime，我们需要确保传入 save_to_json 前转为 str
    # 或者在这里统一处理
    
    # 简单起见，假设传入的 data 已经是 dict，且值是可序列化的
    # 如果有 datetime，需要自定义 encoder，但为了保持简单，
    # 我们在 main.py 中确保传入的是字符串，或者在这里转换
    
    # 合并
    existing_data.extend(data)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4, default=str)
    
    print(f"Saved {len(data)} records to {filepath}")
