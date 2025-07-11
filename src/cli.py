#!/usr/bin/env python3
"""
Command Line Interface for Cloudflare DNS Manager
"""

import argparse
import sys
from bot_config import Config
from dns_manager import CloudflareDNSManager
from utils import log

class CLI:
    """コマンドラインインターフェースクラス"""
    
    def __init__(self):
        self.config = Config()
        if not self.config.validate():
            print("エラー: ZONE_ID と API_TOKEN を設定してください")
            sys.exit(1)
        
        self.dns_manager = CloudflareDNSManager(self.config)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """コマンドライン引数パーサーを作成"""
        parser = argparse.ArgumentParser(description="Cloudflare DNS Manager")
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # list コマンド
        list_parser = subparsers.add_parser("list", help="List DNS records")
        list_parser.add_argument("-t", "--type", help="Filter by record type")
        list_parser.add_argument("-f", "--filter", help="Filter by name (partial match)")
        
        # create コマンド
        create_parser = subparsers.add_parser("create", help="Create DNS record")
        create_parser.add_argument("-n", "--name", required=True, help="Record name (subdomain)")
        create_parser.add_argument("-i", "--ip", help="IP address or content")
        create_parser.add_argument("-t", "--type", default="A", help="Record type (default: A)")
        create_parser.add_argument("-l", "--ttl", type=int, default=60, help="TTL in seconds (default: 60)")
        create_parser.add_argument("-p", "--proxy", action="store_true", help="Enable proxy")
        
        # delete コマンド
        delete_parser = subparsers.add_parser("delete", help="Delete DNS record")
        delete_parser.add_argument("-n", "--name", required=True, help="Record name")
        delete_parser.add_argument("-t", "--type", help="Record type for safer deletion")
        
        # update コマンド
        update_parser = subparsers.add_parser("update", help="Update DNS record IP address")
        update_parser.add_argument("-n", "--name", required=True, help="Record name")
        update_parser.add_argument("-i", "--ip", required=True, help="New IP address")
        update_parser.add_argument("-t", "--type", help="Filter by record type (default: A)")
        
        # bulk-update コマンド
        bulk_update_parser = subparsers.add_parser("bulk-update", help="Bulk update predefined domains with current IP")
        bulk_update_parser.add_argument("-d", "--domains", nargs="+", help="Custom domain list (default: saved list)")
        
        # list-domains コマンド
        list_domains_parser = subparsers.add_parser("list-domains", help="List target domains for bulk update")
        
        # add-domain コマンド
        add_domain_parser = subparsers.add_parser("add-domain", help="Add domain to bulk update list")
        add_domain_parser.add_argument("-n", "--name", required=True, help="Domain name to add")
        
        # remove-domain コマンド
        remove_domain_parser = subparsers.add_parser("remove-domain", help="Remove domain from bulk update list")
        remove_domain_parser.add_argument("-n", "--name", required=True, help="Domain name to remove")
        
        return parser
    
    def run(self, args=None):
        """CLIを実行"""
        parser = self.create_parser()
        args = parser.parse_args(args)
        
        if not args.command:
            parser.print_help()
            sys.exit(1)
        
        # コマンドの実行
        try:
            if args.command == "list":
                success = self.dns_manager.list_records(args.type, args.filter)
            elif args.command == "create":
                success = self.dns_manager.create_record(
                    args.name, args.ip, args.type, args.ttl, args.proxy
                )
            elif args.command == "delete":
                success = self.dns_manager.delete_record(args.name, args.type)
            elif args.command == "update":
                success = self.dns_manager.update_record(
                    args.name, args.ip, args.type
                )
            elif args.command == "bulk-update":
                success = self.dns_manager.bulk_update_records(args.domains)
            elif args.command == "list-domains":
                success = self.dns_manager.domain_manager.list_domains()
            elif args.command == "add-domain":
                success = self.dns_manager.domain_manager.add_domain(args.name)
            elif args.command == "remove-domain":
                success = self.dns_manager.domain_manager.remove_domain(args.name)
            else:
                parser.print_help()
                sys.exit(1)
            
            sys.exit(0 if success else 1)
            
        except KeyboardInterrupt:
            print("\n処理を中断しました")
            sys.exit(1)
        except Exception as e:
            print(f"予期しないエラーが発生しました: {e}")
            sys.exit(1)