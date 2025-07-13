#!/usr/bin/env python3
"""
統合Bot設定管理
"""

import os
import json
import re
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

class BotConfig:
    """統合Bot設定管理クラス"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        # 設定ファイルはルートディレクトリ（Dockerコンテナ内では /app/）に配置
        if os.path.exists(f"/app/{config_file}"):
            self.config_path = f"/app/{config_file}"
        else:
            # 開発環境用（ルートディレクトリの一つ上）
            self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込み、環境変数を置換"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_str = f.read()
                
            # 環境変数を置換
            config_str = self._replace_env_vars(config_str)
            
            return json.loads(config_str)
        except FileNotFoundError:
            print(f"設定ファイルが見つかりません: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"設定ファイルの解析に失敗しました: {e}")
            return {}
        except Exception as e:
            print(f"設定ファイルの読み込みに失敗しました: {e}")
            return {}
    
    def _replace_env_vars(self, config_str: str) -> str:
        """設定文字列内の環境変数を置換"""
        pattern = r'\$\{([^}]+)\}'
        
        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is None:
                print(f"環境変数が設定されていません: {var_name}")
                return match.group(0)  # 置換しない
            return env_value
        
        return re.sub(pattern, replace_var, config_str)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット記法でネストした設定値を取得"""
        keys = key_path.split('.')
        current = self._config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def get_cloudflare_config(self) -> Dict[str, Any]:
        """Cloudflare設定を取得"""
        return self.get('cloudflare', {})
    
    def get_dns_config(self) -> Dict[str, Any]:
        """DNS設定を取得"""
        return self.get('dns', {})
    
    def get_router_config(self) -> Dict[str, Any]:
        """Router設定を取得"""
        return self.get('router', {})
    
    def get_discord_config(self) -> Dict[str, Any]:
        """Discord設定を取得"""
        return self.get('discord', {})
    
    def get_target_domains(self) -> List[str]:
        """対象ドメインリストを取得"""
        return self.get('dns.target_domains', [])
    
    def get_default_domains(self) -> List[str]:
        """デフォルトドメインリストを取得"""
        return self.get('dns.default_domains', [])
    
    def get_router_schedule_config(self) -> Dict[str, Any]:
        """Routerスケジュール設定を取得"""
        return self.get('router.schedule', {})
    
    def get_router_selenium_config(self) -> Dict[str, Any]:
        """Router Selenium設定を取得"""
        return self.get('router.selenium', {})
    
    def get_router_connection_config(self) -> Dict[str, Any]:
        """Router接続設定を取得"""
        return self.get('router.connection', {})
    
    def validate(self) -> bool:
        """設定値の検証"""
        # 必須環境変数のチェック
        required_cloudflare = ['zone_id', 'api_token']
        cf_config = self.get_cloudflare_config()
        
        for key in required_cloudflare:
            if not cf_config.get(key):
                print(f"必須のCloudflare設定が不足しています: {key}")
                return False
        
        # Router設定のチェック
        router_conn = self.get_router_connection_config()
        if not router_conn.get('ip') or not router_conn.get('password'):
            print("Router接続設定が不足しています")
            return False
        
        return True
    
    def reload(self):
        """設定を再読み込み"""
        self._config = self._load_config()
    
    def update_router_schedule(self, cron_expression: str, channel_id: int) -> bool:
        """Routerスケジュール設定を更新"""
        try:
            # 現在の設定を読み込み
            if not self._config:
                self._config = {}
            
            # router.schedule セクションを更新
            if 'router' not in self._config:
                self._config['router'] = {}
            if 'schedule' not in self._config['router']:
                self._config['router']['schedule'] = {}
            
            self._config['router']['schedule']['cron'] = cron_expression
            self._config['router']['schedule']['channel_id'] = str(channel_id)
            
            # ファイルに書き込み
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Router schedule update error: {e}")
            return False
    
    # Config クラス互換のプロパティとメソッド
    @property
    def zone_id(self) -> str:
        """Cloudflare Zone ID"""
        return self.get('cloudflare.zone_id')
    
    @property
    def api_token(self) -> str:
        """Cloudflare API Token"""
        return self.get('cloudflare.api_token')
    
    @property
    def domain(self) -> str:
        """Cloudflare Domain"""
        return self.get('cloudflare.domain', "example.com")
    
    @property
    def base_url(self) -> str:
        """Cloudflare API Base URL"""
        return self.get('cloudflare.base_url', "https://api.cloudflare.com/client/v4")
    
    @property
    def request_timeout(self) -> int:
        """Request Timeout"""
        return self.get('cloudflare.request_timeout', 30)
    
    @property
    def ip_services(self) -> List[str]:
        """IP Services"""
        return self.get('cloudflare.ip_services', [
            "https://ipv4.icanhazip.com",
            "https://api.ipify.org",
            "https://checkip.amazonaws.com"
        ])
    
    @property
    def default_domains(self) -> List[str]:
        """Default Domains (fallback for target_domains)"""
        return self.get_target_domains()
    
    def get_headers(self) -> Dict[str, str]:
        """APIリクエスト用のヘッダーを取得"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

# グローバル設定インスタンス
bot_config = BotConfig()

# Config クラスのエイリアス（後方互換性のため）
Config = BotConfig