#!/usr/bin/env python3
"""
Cloudflare DNS Manager Core Class
"""

from typing import Dict, List, Optional, Tuple
from config import Config
from utils import log, get_current_ip, validate_ipv4, make_request, format_record_table
from domain_list_manager import DomainListManager

class CloudflareDNSManager:
    """Cloudflare DNS管理のメインクラス"""
    
    def __init__(self, config: Config):
        self.config = config
        self.domain_manager = DomainListManager(config)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """Cloudflare APIへのリクエスト実行"""
        url = f"{self.config.base_url}{endpoint}"
        return make_request(method, url, self.config.get_headers(), data, self.config.request_timeout)
    
    def list_records(self, record_type: Optional[str] = None, name_filter: Optional[str] = None) -> bool:
        """DNSレコードの一覧表示"""
        log("DNSレコードを取得中...")
        
        endpoint = f"/zones/{self.config.zone_id}/dns_records"
        params = []
        
        if record_type:
            params.append(f"type={record_type}")
        
        if params:
            endpoint += "?" + "&".join(params)
        
        success, response = self._make_request("GET", endpoint)
        
        if not success:
            log(f"DNSレコード取得に失敗: {response.get('error', 'Unknown error')}", "ERROR")
            return False
        
        records = response.get('result', [])
        
        # 名前でフィルタリング
        if name_filter:
            records = [r for r in records if name_filter.lower() in r.get('name', '').lower()]
        
        print(f"\n=== DNS Records for {self.config.domain} ===")
        print(f"Total: {len(records)} records")
        if record_type:
            print(f"Type filter: {record_type}")
        if name_filter:
            print(f"Name filter: {name_filter}")
        print()
        
        print(format_record_table(records))
        return True
    
    def create_record(self, name: str, content: Optional[str] = None, record_type: str = "A", 
                     ttl: int = 60, proxied: bool = False) -> bool:
        """新しいDNSレコードを作成"""
        # 完全なレコード名を構築
        if not name.endswith(self.config.domain):
            full_name = f"{name}.{self.config.domain}" if name != "@" else self.config.domain
        else:
            full_name = name
        
        # コンテンツの処理
        if content is None:
            if record_type == "A":
                log("IPアドレスが指定されていないため、現在のIPを取得します")
                content = get_current_ip(self.config.ip_services)
                if content is None:
                    log("現在のIPアドレスを取得できませんでした", "ERROR")
                    return False
                log(f"取得したIPアドレス: {content}")
            else:
                log(f"{record_type}レコードにはcontentの指定が必要です", "ERROR")
                return False
        
        # IPv4アドレスの検証
        if record_type == "A" and not validate_ipv4(content):
            log(f"無効なIPv4アドレス: {content}", "ERROR")
            return False
        
        # 既存レコードのチェック
        log(f"既存レコードをチェック: {full_name}")
        success, response = self._make_request("GET", f"/zones/{self.config.zone_id}/dns_records?name={full_name}")
        
        if success and response.get('result'):
            print(f"\n警告: レコード '{full_name}' は既に存在します:")
            for record in response['result']:
                print(f"  {record['type']} {record['name']} {record['content']}")
            
            confirm = input("\n続行しますか？ (y/N): ").strip().lower()
            if confirm != 'y':
                log("作成をキャンセルしました")
                return False
        
        # レコード作成
        data = {
            "type": record_type,
            "name": full_name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied
        }
        
        log(f"DNSレコードを作成中: {record_type} {full_name} {content}")
        success, response = self._make_request("POST", f"/zones/{self.config.zone_id}/dns_records", data)
        
        if success:
            record_id = response['result']['id']
            log(f"✅ DNSレコードの作成が完了しました")
            print(f"\n=== 作成されたレコード ===")
            print(f"Record ID: {record_id}")
            print(f"Type: {record_type}")
            print(f"Name: {full_name}")
            print(f"Content: {content}")
            print(f"TTL: {ttl}")
            print(f"Proxied: {proxied}")
            return True
        else:
            log(f"DNSレコード作成に失敗: {response}", "ERROR")
            return False
    
    def delete_record(self, name: str, record_type: Optional[str] = None) -> bool:
        """DNSレコードを削除"""
        # 完全なレコード名を構築
        if not name.endswith(self.config.domain):
            full_name = f"{name}.{self.config.domain}" if name != "@" else self.config.domain
        else:
            full_name = name
        
        # 対象レコードを検索
        log(f"削除対象レコードを検索: {full_name}")
        endpoint = f"/zones/{self.config.zone_id}/dns_records?name={full_name}"
        if record_type:
            endpoint += f"&type={record_type}"
        
        success, response = self._make_request("GET", endpoint)
        
        if not success:
            log(f"レコード検索に失敗: {response}", "ERROR")
            return False
        
        records = response.get('result', [])
        
        if not records:
            log(f"レコードが見つかりません: {full_name}", "ERROR")
            return False
        
        if len(records) > 1:
            print(f"\n複数のレコードが見つかりました:")
            for i, record in enumerate(records):
                print(f"  {i+1}. {record['type']} {record['name']} {record['content']}")
            
            try:
                choice = int(input("\n削除するレコードの番号を選択 (1-{}): ".format(len(records))))
                if 1 <= choice <= len(records):
                    target_record = records[choice - 1]
                else:
                    log("無効な選択です", "ERROR")
                    return False
            except ValueError:
                log("無効な入力です", "ERROR")
                return False
        else:
            target_record = records[0]
        
        # 削除確認
        print(f"\n削除対象レコード:")
        print(f"  Type: {target_record['type']}")
        print(f"  Name: {target_record['name']}")
        print(f"  Content: {target_record['content']}")
        
        confirm = input("\nこのレコードを削除しますか？ (y/N): ").strip().lower()
        if confirm != 'y':
            log("削除をキャンセルしました")
            return False
        
        # レコード削除
        record_id = target_record['id']
        log(f"DNSレコードを削除中: {record_id}")
        success, response = self._make_request("DELETE", f"/zones/{self.config.zone_id}/dns_records/{record_id}")
        
        if success:
            log("✅ DNSレコードの削除が完了しました")
            return True
        else:
            log(f"DNSレコード削除に失敗: {response}", "ERROR")
            return False
    
    def update_record(self, name: str, content: str, record_type: Optional[str] = None) -> bool:
        """既存のDNSレコードのIPアドレスを更新"""
        # 完全なレコード名を構築
        if not name.endswith(self.config.domain):
            full_name = f"{name}.{self.config.domain}" if name != "@" else self.config.domain
        else:
            full_name = name
        
        # デフォルトのレコードタイプをAに設定
        if record_type is None:
            record_type = "A"
        
        # 対象レコードを検索
        log(f"更新対象レコードを検索: {full_name}")
        endpoint = f"/zones/{self.config.zone_id}/dns_records?name={full_name}&type={record_type}"
        
        success, response = self._make_request("GET", endpoint)
        
        if not success:
            log(f"レコード検索に失敗: {response}", "ERROR")
            return False
        
        records = response.get('result', [])
        
        if not records:
            log(f"レコードが見つかりません: {full_name}", "ERROR")
            return False
        
        if len(records) > 1:
            log(f"複数のレコードが見つかりました。最初のレコードを更新します", "WARNING")
            target_record = records[0]
        else:
            target_record = records[0]
        
        # IPv4アドレスの検証
        if record_type == "A" and not validate_ipv4(content):
            log(f"無効なIPv4アドレス: {content}", "ERROR")
            return False
        
        # 現在の設定を表示
        print(f"\n現在の設定:")
        print(f"  Type: {target_record['type']}")
        print(f"  Name: {target_record['name']}")
        print(f"  Content: {target_record['content']}")
        
        # 新しい値の準備（IPアドレスのみ更新）
        new_data = {
            "type": target_record['type'],
            "name": target_record['name'],
            "content": content,
            "ttl": target_record['ttl'],
            "proxied": target_record['proxied']
        }
        
        # 変更点を表示
        print(f"\n変更後の設定:")
        print(f"  Type: {new_data['type']}")
        print(f"  Name: {new_data['name']}")
        print(f"  Content: {new_data['content']} (変更)")
        
        confirm = input("\nこの内容で更新しますか？ (y/N): ").strip().lower()
        if confirm != 'y':
            log("更新をキャンセルしました")
            return False
        
        # レコード更新
        record_id = target_record['id']
        log(f"DNSレコードのIPアドレスを更新中: {record_id}")
        success, response = self._make_request("PUT", f"/zones/{self.config.zone_id}/dns_records/{record_id}", new_data)
        
        if success:
            log(f"✅ DNSレコードのIPアドレス更新が完了しました: {target_record['content']} -> {content}")
            return True
        else:
            log(f"DNSレコード更新に失敗: {response}", "ERROR")
            return False
    
    def bulk_update_records(self, custom_domains: Optional[List[str]] = None) -> bool:
        """リストに含まれるドメインのIPアドレスを現在のIPアドレスで一括更新"""
        # 使用するドメインリストを決定
        domains_to_update = custom_domains if custom_domains is not None else self.domain_manager.get_domains()
        
        if not domains_to_update:
            log("更新対象のドメインが指定されていません", "ERROR")
            return False
        
        # 現在のIPアドレスを取得
        log("現在のIPアドレスを取得中...")
        current_ip = get_current_ip(self.config.ip_services)
        if current_ip is None:
            log("現在のIPアドレスを取得できませんでした", "ERROR")
            return False
        
        log(f"取得したIPアドレス: {current_ip}")
        
        # 各ドメインを更新
        success_count = 0
        failed_domains = []
        
        print(f"\n=== 一括更新開始 ===")
        print(f"対象ドメイン: {domains_to_update}")
        print(f"更新先IPアドレス: {current_ip}")
        print()
        
        for domain in domains_to_update:
            log(f"ドメイン '{domain}' を更新中...")
            
            try:
                success = self.update_record(domain, current_ip, "A")
                if success:
                    success_count += 1
                    log(f"✅ '{domain}' の更新が完了しました")
                else:
                    failed_domains.append(domain)
                    log(f"❌ '{domain}' の更新に失敗しました", "ERROR")
            except Exception as e:
                failed_domains.append(domain)
                log(f"❌ '{domain}' の更新中にエラーが発生: {e}", "ERROR")
        
        # 結果のサマリー
        print(f"\n=== 一括更新結果 ===")
        print(f"総ドメイン数: {len(domains_to_update)}")
        print(f"成功: {success_count}")
        print(f"失敗: {len(failed_domains)}")
        
        if failed_domains:
            print(f"失敗したドメイン: {failed_domains}")
        
        if success_count == len(domains_to_update):
            log("✅ 全てのドメインの更新が完了しました")
            return True
        else:
            log(f"⚠️  {len(failed_domains)}個のドメインの更新に失敗しました", "WARNING")
            return False