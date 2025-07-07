#!/usr/bin/env python3
"""
Configuration management for Cloudflare DNS Manager
"""

import os
from typing import Optional
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

class Config:
    """設定管理クラス"""
    
    def __init__(self):
        # Cloudflare設定（環境変数必須）
        self.zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
        self.api_token = os.getenv('CLOUDFLARE_API_TOKEN')
        self.domain = os.getenv('CLOUDFLARE_DOMAIN', "example.com")
        
        # ファイルパス設定
        self.domains_file = "target_domains.json"
        
        # API設定
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.request_timeout = 30
        
        # IP取得サービス
        self.ip_services = [
            "https://ipv4.icanhazip.com",
            "https://api.ipify.org",
            "https://checkip.amazonaws.com"
        ]
        
        # デフォルトドメインリスト
        self.default_domains = ["ama", "taichi"]
    
    def validate(self) -> bool:
        """設定値の検証"""
        if not self.zone_id or not self.api_token:
            return False
        return True
    
    def get_headers(self) -> dict:
        """APIリクエスト用のヘッダーを取得"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }