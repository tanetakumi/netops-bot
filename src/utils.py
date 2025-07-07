#!/usr/bin/env python3
"""
Utility functions for Cloudflare DNS Manager
"""

import requests
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def log(message: str, level: str = "INFO"):
    """ログメッセージの出力"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def get_current_ip(ip_services: List[str]) -> Optional[str]:
    """現在のIPアドレスを取得"""
    for service in ip_services:
        try:
            response = requests.get(service, timeout=10)
            ip = response.text.strip()
            if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
                return ip
        except:
            continue
    return None

def validate_ipv4(ip: str) -> bool:
    """IPv4アドレスの形式を検証"""
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts)

def make_request(method: str, url: str, headers: dict, data: Optional[Dict] = None, timeout: int = 30) -> Tuple[bool, Dict]:
    """
    HTTPリクエストの実行
    
    Args:
        method: HTTPメソッド (GET, POST, PUT, DELETE)
        url: リクエストURL
        headers: HTTPヘッダー
        data: リクエストデータ
        timeout: タイムアウト値
        
    Returns:
        Tuple[成功フラグ, レスポンスデータ]
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return False, {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        result = response.json()
        
        if result.get("success", False):
            return True, result
        else:
            return False, result
            
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}
    except json.JSONDecodeError as e:
        return False, {"error": f"JSON decode error: {str(e)}"}

def format_record_table(records: List[Dict]) -> str:
    """DNSレコードをテーブル形式でフォーマット"""
    if not records:
        return "DNSレコードがありません。"
    
    # ヘッダー
    headers = ["ID", "Type", "Name", "Content", "TTL", "Proxy", "Created"]
    
    # 各カラムの最大幅を計算
    widths = [len(h) for h in headers]
    for record in records:
        values = [
            record.get('id', '')[:8] + '...',  # IDは短縮表示
            record.get('type', ''),
            record.get('name', ''),
            record.get('content', ''),
            str(record.get('ttl', '')),
            'ON' if record.get('proxied', False) else 'OFF',
            record.get('created_on', '')[:10]  # 日付のみ
        ]
        for i, value in enumerate(values):
            widths[i] = max(widths[i], len(str(value)))
    
    # テーブルの作成
    separator = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'
    header_row = '|' + '|'.join(f' {h:<{w}} ' for h, w in zip(headers, widths)) + '|'
    
    result = [separator, header_row, separator]
    
    for record in records:
        values = [
            record.get('id', '')[:8] + '...',
            record.get('type', ''),
            record.get('name', ''),
            record.get('content', ''),
            str(record.get('ttl', '')),
            'ON' if record.get('proxied', False) else 'OFF',
            record.get('created_on', '')[:10]
        ]
        row = '|' + '|'.join(f' {str(v):<{w}} ' for v, w in zip(values, widths)) + '|'
        result.append(row)
    
    result.append(separator)
    return '\n'.join(result)