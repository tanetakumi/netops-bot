#!/usr/bin/env python3
"""
Discord Bot for Cloudflare DNS Manager and Router Automation
"""

import discord
from discord.ext import commands
import asyncio
import traceback
import subprocess
import os
from typing import Optional, List
from dotenv import load_dotenv
from config import Config

# .envファイルを読み込む
load_dotenv()
from dns_manager import CloudflareDNSManager
from utils import log

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# DNS Managerの初期化
config = Config()
if not config.validate():
    print("エラー: ZONE_ID と API_TOKEN を設定してください")
    exit(1)

dns_manager = CloudflareDNSManager(config)

class DNSCommands(commands.Cog):
    """DNS管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.dns_manager = dns_manager
    
    @commands.slash_command(name="dns", description="DNS管理コマンド")
    async def dns_group(self, ctx):
        """DNS管理のベースコマンド"""
        pass
    
    @dns_group.subcommand(name="list", description="DNSレコード一覧表示")
    async def dns_list(
        self, 
        ctx,
        record_type: Optional[str] = None,
        name_filter: Optional[str] = None
    ):
        """DNSレコード一覧を表示"""
        await ctx.defer()
        
        try:
            # DNS Manager のlist_recordsメソッドの出力をキャプチャする必要があるため
            # 一時的にファイルに出力してから読み取る方法を使用
            import io
            import sys
            
            # 標準出力をキャプチャ
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            success = self.dns_manager.list_records(record_type, name_filter)
            
            # 標準出力を元に戻す
            sys.stdout = old_stdout
            output = captured_output.getvalue()
            
            if success and output:
                # Discord の文字数制限（2000文字）を考慮して分割
                if len(output) > 1900:
                    chunks = [output[i:i+1900] for i in range(0, len(output), 1900)]
                    for i, chunk in enumerate(chunks):
                        embed = discord.Embed(
                            title=f"DNS Records ({i+1}/{len(chunks)})",
                            description=f"```\n{chunk}\n```",
                            color=0x00ff00
                        )
                        await ctx.followup.send(embed=embed)
                else:
                    embed = discord.Embed(
                        title="DNS Records",
                        description=f"```\n{output}\n```",
                        color=0x00ff00
                    )
                    await ctx.followup.send(embed=embed)
            else:
                await ctx.followup.send("❌ DNSレコードの取得に失敗しました", ephemeral=True)
                
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"DNS list error: {e}", "ERROR")
    
    @dns_group.subcommand(name="create", description="新規DNSレコード作成")
    async def dns_create(
        self,
        ctx,
        name: str,
        ip: Optional[str] = None,
        record_type: str = "A",
        ttl: int = 60,
        proxy: bool = False
    ):
        """新規DNSレコードを作成"""
        await ctx.defer()
        
        try:
            success = self.dns_manager.create_record(name, ip, record_type, ttl, proxy)
            
            if success:
                embed = discord.Embed(
                    title="✅ DNSレコード作成完了",
                    description=f"レコード `{name}` を作成しました",
                    color=0x00ff00
                )
                embed.add_field(name="Type", value=record_type, inline=True)
                embed.add_field(name="Content", value=ip or "自動取得", inline=True)
                embed.add_field(name="TTL", value=ttl, inline=True)
                await ctx.followup.send(embed=embed)
            else:
                await ctx.followup.send("❌ DNSレコードの作成に失敗しました", ephemeral=True)
                
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"DNS create error: {e}", "ERROR")
    
    @dns_group.subcommand(name="update", description="DNSレコード更新")
    async def dns_update(
        self,
        ctx,
        name: str,
        ip: str,
        record_type: str = "A"
    ):
        """DNSレコードを更新"""
        await ctx.defer()
        
        try:
            success = self.dns_manager.update_record(name, ip, record_type)
            
            if success:
                embed = discord.Embed(
                    title="✅ DNSレコード更新完了",
                    description=f"レコード `{name}` を更新しました",
                    color=0x00ff00
                )
                embed.add_field(name="New IP", value=ip, inline=True)
                embed.add_field(name="Type", value=record_type, inline=True)
                await ctx.followup.send(embed=embed)
            else:
                await ctx.followup.send("❌ DNSレコードの更新に失敗しました", ephemeral=True)
                
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"DNS update error: {e}", "ERROR")
    
    @dns_group.subcommand(name="delete", description="DNSレコード削除")
    async def dns_delete(
        self,
        ctx,
        name: str,
        record_type: Optional[str] = None
    ):
        """DNSレコードを削除"""
        await ctx.defer()
        
        try:
            success = self.dns_manager.delete_record(name, record_type)
            
            if success:
                embed = discord.Embed(
                    title="✅ DNSレコード削除完了",
                    description=f"レコード `{name}` を削除しました",
                    color=0x00ff00
                )
                await ctx.followup.send(embed=embed)
            else:
                await ctx.followup.send("❌ DNSレコードの削除に失敗しました", ephemeral=True)
                
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"DNS delete error: {e}", "ERROR")

class BulkCommands(commands.Cog):
    """一括更新管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.dns_manager = dns_manager
    
    @commands.slash_command(name="bulk", description="一括更新管理コマンド")
    async def bulk_group(self, ctx):
        """一括更新管理のベースコマンド"""
        pass
    
    @bulk_group.subcommand(name="list", description="対象ドメインリスト表示")
    async def bulk_list(self, ctx):
        """一括更新対象のドメインリストを表示"""
        await ctx.defer()
        
        try:
            domains = self.dns_manager.domain_manager.get_domains()
            
            if domains:
                domain_list = "\n".join([f"• {domain}.{config.domain}" for domain in domains])
                embed = discord.Embed(
                    title="📋 一括更新対象ドメインリスト",
                    description=domain_list,
                    color=0x0099ff
                )
                embed.add_field(name="ドメイン数", value=len(domains), inline=True)
            else:
                embed = discord.Embed(
                    title="📋 一括更新対象ドメインリスト",
                    description="登録されているドメインがありません",
                    color=0xffaa00
                )
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Bulk list error: {e}", "ERROR")
    
    @bulk_group.subcommand(name="execute", description="一括更新実行")
    async def bulk_execute(
        self,
        ctx,
        domains: Optional[str] = None
    ):
        """一括更新を実行"""
        await ctx.defer()
        
        try:
            custom_domains = domains.split(",") if domains else None
            
            embed = discord.Embed(
                title="🔄 一括更新を開始しています...",
                description="現在のIPアドレスで更新中です",
                color=0xffaa00
            )
            await ctx.followup.send(embed=embed)
            
            success = self.dns_manager.bulk_update_records(custom_domains)
            
            if success:
                embed = discord.Embed(
                    title="✅ 一括更新完了",
                    description="すべてのドメインの更新が完了しました",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="⚠️ 一括更新完了（一部失敗）",
                    description="一部のドメインの更新に失敗しました",
                    color=0xffaa00
                )
            
            await ctx.edit_original_response(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Bulk execute error: {e}", "ERROR")
    
    @bulk_group.subcommand(name="add", description="ドメインをリストに追加")
    async def bulk_add(self, ctx, name: str):
        """ドメインを一括更新リストに追加"""
        await ctx.defer()
        
        try:
            success = self.dns_manager.domain_manager.add_domain(name)
            
            if success:
                embed = discord.Embed(
                    title="✅ ドメイン追加完了",
                    description=f"`{name}` を一括更新リストに追加しました",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ ドメイン追加失敗",
                    description=f"`{name}` は既にリストに登録されています",
                    color=0xff0000
                )
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Bulk add error: {e}", "ERROR")
    
    @bulk_group.subcommand(name="remove", description="ドメインをリストから削除")
    async def bulk_remove(self, ctx, name: str):
        """ドメインを一括更新リストから削除"""
        await ctx.defer()
        
        try:
            success = self.dns_manager.domain_manager.remove_domain(name)
            
            if success:
                embed = discord.Embed(
                    title="✅ ドメイン削除完了",
                    description=f"`{name}` を一括更新リストから削除しました",
                    color=0x00ff00
                )
            else:
                embed = discord.Embed(
                    title="❌ ドメイン削除失敗",
                    description=f"`{name}` はリストに登録されていません",
                    color=0xff0000
                )
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Bulk remove error: {e}", "ERROR")

class RouterCommands(commands.Cog):
    """ルーター管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.slash_command(name="router", description="ルーター管理コマンド")
    async def router_group(self, ctx):
        """ルーター管理のベースコマンド"""
        pass
    
    @router_group.subcommand(name="update", description="ルーター接続設定更新")
    async def router_update(self, ctx):
        """ルーター自動化スクリプトを実行"""
        await ctx.defer()
        
        try:
            embed = discord.Embed(
                title="🔄 ルーター更新を開始しています...",
                description="コミュファ光の接続設定を更新中です",
                color=0xffaa00
            )
            await ctx.followup.send(embed=embed)
            
            # router_automation.pyを実行
            script_path = os.path.join(os.path.dirname(__file__), "router_automation.py")
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=300  # 5分でタイムアウト
            )
            
            if result.returncode == 0:
                embed = discord.Embed(
                    title="✅ ルーター更新完了",
                    description="コミュファ光の接続設定更新が完了しました",
                    color=0x00ff00
                )
                if result.stdout:
                    # 出力が長い場合は最後の部分のみ表示
                    output = result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout
                    embed.add_field(name="実行結果", value=f"```\n{output}\n```", inline=False)
            else:
                embed = discord.Embed(
                    title="❌ ルーター更新失敗",
                    description="ルーター設定更新中にエラーが発生しました",
                    color=0xff0000
                )
                if result.stderr:
                    error_output = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
                    embed.add_field(name="エラー詳細", value=f"```\n{error_output}\n```", inline=False)
            
            await ctx.edit_original_response(embed=embed)
            
        except subprocess.TimeoutExpired:
            embed = discord.Embed(
                title="⏰ ルーター更新タイムアウト",
                description="ルーター設定更新がタイムアウトしました（5分）",
                color=0xffaa00
            )
            await ctx.edit_original_response(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Router update error: {e}", "ERROR")

@bot.event
async def on_ready():
    """Bot起動時の処理"""
    print(f'{bot.user} がログインしました!')
    print(f'サーバー数: {len(bot.guilds)}')
    
    # コマンドを同期
    try:
        synced = await bot.tree.sync()
        print(f'スラッシュコマンドを同期しました: {len(synced)}個')
    except Exception as e:
        print(f'スラッシュコマンドの同期に失敗しました: {e}')

@bot.event
async def on_application_command_error(ctx, error):
    """コマンドエラーハンドリング"""
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f"このコマンドは {error.retry_after:.2f}秒後に使用できます。", ephemeral=True)
    else:
        await ctx.respond("コマンドの実行中にエラーが発生しました。", ephemeral=True)
        print(f"Command error: {error}")
        traceback.print_exception(type(error), error, error.__traceback__)

# Cogを追加
bot.add_cog(DNSCommands(bot))
bot.add_cog(BulkCommands(bot))
bot.add_cog(RouterCommands(bot))

if __name__ == "__main__":
    # Discord botトークンを環境変数から取得
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("エラー: DISCORD_BOT_TOKEN環境変数を設定してください")
        exit(1)
    
    bot.run(token)