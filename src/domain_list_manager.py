#!/usr/bin/env python3
"""
Domain list management for Cloudflare DNS Manager
"""

import json
from typing import List
from config import Config
from utils import log

class DomainListManager:
    """ドメインリスト管理クラス"""
    
    def __init__(self, config: Config):
        self.config = config
        self.domains_file = config.domains_file
        self.target_domains = self._load_target_domains()
    
    def _load_target_domains(self) -> List[str]:
        """ドメインリストをファイルから読み込み"""
        try:
            with open(self.domains_file, 'r', encoding='utf-8') as f:
                domains = json.load(f)
                log(f"ドメインリストを読み込みました: {domains}")
                return domains
        except FileNotFoundError:
            # ファイルが存在しない場合はデフォルトリストを作成
            default_domains = self.config.default_domains.copy()
            self._save_target_domains(default_domains)
            log(f"デフォルトドメインリストを作成しました: {default_domains}")
            return default_domains
        except json.JSONDecodeError:
            log("ドメインリストファイルの形式が無効です。デフォルトリストを使用します", "ERROR")
            return self.config.default_domains.copy()
        except Exception as e:
            log(f"ドメインリスト読み込み中にエラー: {e}", "ERROR")
            return self.config.default_domains.copy()
    
    def _save_target_domains(self, domains: List[str] = None) -> bool:
        """ドメインリストをファイルに保存"""
        if domains is None:
            domains = self.target_domains
        
        try:
            with open(self.domains_file, 'w', encoding='utf-8') as f:
                json.dump(domains, f, ensure_ascii=False, indent=2)
            log(f"ドメインリストを保存しました: {domains}")
            return True
        except Exception as e:
            log(f"ドメインリスト保存中にエラー: {e}", "ERROR")
            return False
    
    def list_domains(self) -> bool:
        """一括更新対象のドメインリストを表示"""
        print(f"\n=== 一括更新対象ドメインリスト ===")
        print(f"保存ファイル: {self.domains_file}")
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