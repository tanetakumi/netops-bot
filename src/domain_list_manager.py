#!/usr/bin/env python3
"""
Domain list management for Cloudflare DNS Manager
"""

import json
from typing import List
from bot_config import Config
from utils import log

class DomainListManager:
    """ドメインリスト管理クラス"""
    
    def __init__(self, config: Config):
        self.config = config
        self.target_domains = self._load_target_domains()
    
    def _load_target_domains(self) -> List[str]:
        """ドメインリストを統合設定から読み込み"""
        domains = self.config.get_target_domains()
        log(f"ドメインリストを読み込みました: {domains}")
        return domains
    
    def _save_target_domains(self, domains: List[str] = None) -> bool:
        """ドメインリストを保存（統合設定では手動でbot_config.jsonを編集）"""
        if domains is None:
            domains = self.target_domains
        
        log(f"統合設定では手動でbot_config.jsonを編集してください: {domains}", "WARNING")
        log("現在の設定ファイルでは自動保存をサポートしていません", "WARNING")
        return False
    
    def list_domains(self) -> bool:
        """一括更新対象のドメインリストを表示"""
        print(f"\n=== 一括更新対象ドメインリスト ===")
        print(f"設定ファイル: bot_config.json")
        print(f"ドメイン数: {len(self.target_domains)}")
        print()
        
        if not self.target_domains:
            print("登録されているドメインがありません。")
        else:
            for i, domain in enumerate(self.target_domains, 1):
                print(f"  {i}. {domain}.{self.config.domain}")
        
        return True
    
    def add_domain(self, domain: str) -> bool:
        """一括更新対象のドメインリストに追加"""
        if domain in self.target_domains:
            log(f"ドメイン '{domain}' は既にリストに登録されています", "WARNING")
            return False
        
        self.target_domains.append(domain)
        
        if self._save_target_domains():
            log(f"✅ ドメイン '{domain}' をリストに追加しました")
            return True
        else:
            # 保存に失敗した場合は元に戻す
            self.target_domains.remove(domain)
            return False
    
    def remove_domain(self, domain: str) -> bool:
        """一括更新対象のドメインリストから削除"""
        if domain not in self.target_domains:
            log(f"ドメイン '{domain}' はリストに登録されていません", "ERROR")
            return False
        
        self.target_domains.remove(domain)
        
        if self._save_target_domains():
            log(f"✅ ドメイン '{domain}' をリストから削除しました")
            return True
        else:
            # 保存に失敗した場合は元に戻す
            self.target_domains.append(domain)
            return False
    
    def get_domains(self) -> List[str]:
        """現在のドメインリストを取得"""
        return self.target_domains.copy()