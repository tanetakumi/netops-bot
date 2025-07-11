#!/usr/bin/env python3
"""
Discord Bot for Cloudflare DNS Manager and Router Automation
"""

import discord
from discord.ext import commands, tasks
import asyncio
import traceback
import subprocess
import os
import json
import datetime
from typing import Optional, List
from dotenv import load_dotenv
from bot_config import Config, BotConfig
from croniter import croniter

# .envファイルを読み込む
load_dotenv()
from dns_manager import CloudflareDNSManager
from utils import log

# Bot設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# DNS Managerの初期化
config = Config()
bot_config = BotConfig()
if not config.validate():
    print("エラー: ZONE_ID と API_TOKEN を設定してください")
    exit(1)

dns_manager = CloudflareDNSManager(config)

class DNSCommands(commands.Cog):
    """DNS管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.dns_manager = dns_manager
    
    dns_group = discord.SlashCommandGroup("dns", "DNS管理コマンド")
    
    @dns_group.command(name="list", description="DNSレコード一覧表示")
    async def dns_list(
        self, 
        ctx,
        record_type: Optional[str] = None,
        name_filter: Optional[str] = None
    ):
        """DNSレコード一覧を表示"""
        await ctx.defer()
        
        try:
            success, records = self.dns_manager.list_records(record_type, name_filter)
            
            if not success:
                await ctx.followup.send("❌ DNSレコードの取得に失敗しました", ephemeral=True)
                return
            
            if not records:
                embed = discord.Embed(
                    title="📋 DNS Records",
                    description="指定した条件に一致するDNSレコードが見つかりませんでした",
                    color=0xffaa00
                )
                await ctx.followup.send(embed=embed)
                return
            
            # メインEmbedを作成
            main_embed = discord.Embed(
                title="📋 DNS Records",
                description=f"ドメイン: **{self.dns_manager.config.domain}**",
                color=0x0099ff
            )
            
            # フィルタ情報を表示
            filter_info = []
            if record_type:
                filter_info.append(f"タイプ: {record_type}")
            if name_filter:
                filter_info.append(f"名前: {name_filter}")
            
            if filter_info:
                main_embed.add_field(name="🔍 フィルタ", value=" | ".join(filter_info), inline=False)
            
            main_embed.add_field(name="📊 合計", value=f"{len(records)} 件", inline=True)
            
            # レコードを5件ずつ表示
            records_per_page = 5
            total_pages = (len(records) + records_per_page - 1) // records_per_page
            
            for page in range(total_pages):
                start_idx = page * records_per_page
                end_idx = min(start_idx + records_per_page, len(records))
                page_records = records[start_idx:end_idx]
                
                if page == 0:
                    embed = main_embed
                else:
                    embed = discord.Embed(
                        title=f"📋 DNS Records - Page {page + 1}/{total_pages}",
                        color=0x0099ff
                    )
                
                for record in page_records:
                    name = record.get('name', 'N/A')
                    record_type = record.get('type', 'N/A')
                    content = record.get('content', 'N/A')
                    ttl = record.get('ttl', 'N/A')
                    proxied = record.get('proxied', False)
                    
                    # レコード名を短縮表示
                    domain = self.dns_manager.config.domain
                    if name.endswith(f".{domain}"):
                        short_name = name[:-len(f".{domain}")]
                    elif name == domain:
                        short_name = "@"
                    else:
                        short_name = name
                    
                    # プロキシ状態のアイコン
                    proxy_icon = "🟠" if proxied else "⚪"
                    
                    # フィールドの値を構築
                    field_value = f"**Content:** `{content}`\n**TTL:** {ttl}\n**Proxied:** {proxy_icon} {'Yes' if proxied else 'No'}"
                    
                    # レコードタイプのアイコン
                    type_icons = {
                        'A': '🔵',
                        'AAAA': '🟣',
                        'CNAME': '🔶',
                        'MX': '📧',
                        'TXT': '📝',
                        'NS': '🌐',
                        'PTR': '🔄'
                    }
                    type_icon = type_icons.get(record_type, '🔸')
                    
                    embed.add_field(
                        name=f"{type_icon} {short_name} ({record_type})",
                        value=field_value,
                        inline=False
                    )
                
                if page < total_pages - 1:
                    embed.set_footer(text=f"Page {page + 1}/{total_pages} - 続きがあります")
                else:
                    embed.set_footer(text=f"Page {page + 1}/{total_pages} - 最後のページ")
                
                await ctx.followup.send(embed=embed)
                
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"DNS list error: {e}", "ERROR")
    
    @dns_group.command(name="create", description="新規DNSレコード作成")
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
    
    @dns_group.command(name="update", description="DNSレコード更新")
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
    
    @dns_group.command(name="delete", description="DNSレコード削除")
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
    
    bulk_group = discord.SlashCommandGroup("bulk", "一括更新管理コマンド")
    
    @bulk_group.command(name="list", description="対象ドメインリスト表示")
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
    
    @bulk_group.command(name="execute", description="一括更新実行")
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
    
    @bulk_group.command(name="add", description="ドメインをリストに追加")
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
    
    @bulk_group.command(name="remove", description="ドメインをリストから削除")
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
        self.schedule_file = os.path.join(os.path.dirname(__file__), "router_schedule.json")
        self.init_default_schedule()
        self.scheduler_task.start()
    
    def cog_unload(self):
        self.scheduler_task.cancel()
    
    router_group = discord.SlashCommandGroup("router", "ルーター管理コマンド")
    
    
    @router_group.command(name="schedule-update", description="ルーター更新スケジュール設定")
    async def router_schedule_update(self, ctx, cron_expression: str):
        """ルーター更新のスケジュールを設定"""
        await ctx.defer()
        
        try:
            # cron式の妥当性確認
            if not croniter.is_valid(cron_expression):
                await ctx.followup.send("❌ 無効なcron式です。例: `0 9 * * *` (毎日9時)", ephemeral=True)
                return
            
            # 次回実行時刻を計算
            cron = croniter(cron_expression, datetime.datetime.now())
            next_run = cron.get_next(datetime.datetime)
            
            # スケジュールデータを読み込み
            schedules = self.load_schedules()
            
            # 既存のスケジュールをすべて削除して新しいものを設定
            schedules = {
                "1": {
                    "cron": cron_expression,
                    "channel_id": ctx.channel.id,
                    "created_at": datetime.datetime.now().isoformat(),
                    "next_run": next_run.isoformat(),
                    "is_default": False
                }
            }
            
            # ファイルに保存
            self.save_schedules(schedules)
            
            embed = discord.Embed(
                title="✅ スケジュール設定完了",
                description=f"ルーター更新スケジュールを設定しました",
                color=0x00ff00
            )
            embed.add_field(name="Cron式", value=f"`{cron_expression}`", inline=False)
            embed.add_field(name="ログ送信チャンネル", value=f"<#{ctx.channel.id}>", inline=False)
            embed.add_field(name="次回実行", value=next_run.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Router schedule update error: {e}", "ERROR")
    
    @router_group.command(name="schedule-show", description="スケジュール表示")
    async def router_schedule_show(self, ctx):
        """設定されたスケジュールを表示"""
        await ctx.defer()
        
        try:
            schedules = self.load_schedules()
            
            if not schedules:
                # デフォルトスケジュールを初期化して再試行
                self.init_default_schedule()
                schedules = self.load_schedules()
                
                if not schedules:
                    embed = discord.Embed(
                        title="📋 スケジュール表示",
                        description="設定されたスケジュールがありません",
                        color=0xffaa00
                    )
                    await ctx.followup.send(embed=embed)
                    return
            
            # 最初のスケジュールを取得（1つのスケジュールのみ想定）
            schedule = list(schedules.values())[0]
            next_run = datetime.datetime.fromisoformat(schedule["next_run"])
            
            embed = discord.Embed(
                title="📋 ルーター更新スケジュール",
                color=0x0099ff
            )
            
            embed.add_field(name="Cron式", value=f"`{schedule['cron']}`", inline=False)
            embed.add_field(name="ログ送信チャンネル", value=f"<#{schedule['channel_id']}>", inline=False)
            embed.add_field(name="次回実行", value=next_run.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Router schedule show error: {e}", "ERROR")
    
    
    def load_schedules(self):
        """スケジュールファイルを読み込み"""
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log(f"Schedule load error: {e}", "ERROR")
        return {}
    
    def save_schedules(self, schedules):
        """スケジュールファイルに保存"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"Schedule save error: {e}", "ERROR")
    
    def init_default_schedule(self):
        """デフォルトスケジュールを初期化"""
        try:
            # 既存のスケジュールがある場合は何もしない
            if os.path.exists(self.schedule_file):
                schedules = self.load_schedules()
                if schedules:
                    log("Default schedule already exists, skipping initialization", "INFO")
                    return
            
            # 統合設定からデフォルトスケジュールを読み込み
            schedule_config = bot_config.get_router_schedule_config()
            log(f"Loading default schedule config: {schedule_config}", "INFO")
            
            if schedule_config and schedule_config.get("cron"):
                # 次回実行時刻を計算
                cron_expr = schedule_config["cron"]
                channel_id = schedule_config.get("channel_id")
                
                # チャンネルIDの検証
                if not channel_id:
                    log("Default schedule init error: channel_id is missing", "ERROR")
                    return
                
                if croniter.is_valid(cron_expr):
                    cron = croniter(cron_expr, datetime.datetime.now())
                    next_run = cron.get_next(datetime.datetime)
                    
                    # デフォルトスケジュールを作成
                    schedules = {
                        "1": {
                            "cron": cron_expr,
                            "channel_id": channel_id,
                            "created_at": datetime.datetime.now().isoformat(),
                            "next_run": next_run.isoformat(),
                            "is_default": True
                        }
                    }
                    
                    self.save_schedules(schedules)
                    log(f"Default schedule initialized: {cron_expr} -> channel {channel_id}", "INFO")
                else:
                    log(f"Invalid cron expression: {cron_expr}", "ERROR")
            else:
                log("Default schedule config is missing or invalid", "ERROR")
                    
        except Exception as e:
            log(f"Default schedule init error: {e}", "ERROR")
    
    @tasks.loop(minutes=1)
    async def scheduler_task(self):
        """スケジュールされたタスクを実行"""
        try:
            schedules = self.load_schedules()
            current_time = datetime.datetime.now()
            
            for schedule_id, schedule in schedules.items():
                next_run = datetime.datetime.fromisoformat(schedule["next_run"])
                
                if current_time >= next_run:
                    # スケジュールされたタスクを実行
                    await self.execute_scheduled_router_update(schedule_id, schedule)
                    
                    # 次回実行時刻を更新
                    cron = croniter(schedule["cron"], current_time)
                    next_run = cron.get_next(datetime.datetime)
                    schedule["next_run"] = next_run.isoformat()
                    
                    # 更新されたスケジュールを保存
                    self.save_schedules(schedules)
                    
        except Exception as e:
            log(f"Scheduler task error: {e}", "ERROR")
    
    async def execute_scheduled_router_update(self, schedule_id, schedule):
        """スケジュールされたルーター更新を実行"""
        try:
            log(f"Executing scheduled router update - ID: {schedule_id}", "INFO")
            
            # チャンネルを取得
            channel_id = schedule.get("channel_id")
            if not channel_id:
                log(f"No channel_id found for schedule {schedule_id}", "ERROR")
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                log(f"Channel {channel_id} not found for schedule {schedule_id}", "ERROR")
                return
            
            # 実行開始メッセージを送信
            embed = discord.Embed(
                title="🔄 スケジュールされたルーター更新を開始しました",
                description="コミュファ光の接続設定を更新中です",
                color=0xffaa00
            )
            embed.add_field(name="Cron式", value=f"`{schedule['cron']}`", inline=False)
            embed.add_field(name="実行時刻", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            
            status_message = await channel.send(embed=embed)
            
            # router_automation.pyを実行
            script_path = os.path.join(os.path.dirname(__file__), "router_automation.py")
            
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # 実行結果をチャンネルに送信
            if result.returncode == 0:
                embed = discord.Embed(
                    title="✅ スケジュールされたルーター更新完了",
                    description="コミュファ光の接続設定更新が完了しました",
                    color=0x00ff00
                )
                if result.stdout:
                    # 出力が長い場合は最後の部分のみ表示
                    output = result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout
                    embed.add_field(name="実行結果", value=f"```\n{output}\n```", inline=False)
                
                log(f"Scheduled router update completed successfully - ID: {schedule_id}", "INFO")
            else:
                embed = discord.Embed(
                    title="❌ スケジュールされたルーター更新失敗",
                    description="ルーター設定更新中にエラーが発生しました",
                    color=0xff0000
                )
                if result.stderr:
                    error_output = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
                    embed.add_field(name="エラー詳細", value=f"```\n{error_output}\n```", inline=False)
                
                log(f"Scheduled router update failed - ID: {schedule_id}, Error: {result.stderr}", "ERROR")
            
            await channel.send(embed=embed)
            
        except subprocess.TimeoutExpired:
            # タイムアウトの場合のメッセージ
            embed = discord.Embed(
                title="⏰ スケジュールされたルーター更新タイムアウト",
                description="ルーター設定更新がタイムアウトしました（5分）",
                color=0xffaa00
            )
            if channel:
                await channel.send(embed=embed)
            log(f"Scheduled router update timeout - ID: {schedule_id}", "ERROR")
            
        except Exception as e:
            log(f"Scheduled router update error - ID: {schedule_id}: {e}", "ERROR")
            if channel:
                embed = discord.Embed(
                    title="❌ スケジュールされたルーター更新エラー",
                    description=f"エラーが発生しました: {str(e)}",
                    color=0xff0000
                )
                await channel.send(embed=embed)
    
    @scheduler_task.before_loop
    async def before_scheduler_task(self):
        """スケジューラー開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

@bot.event
async def on_ready():
    """Bot起動時の処理"""
    print(f'{bot.user} がログインしました!')
    print(f'サーバー数: {len(bot.guilds)}')
    
    # コマンドを同期
    try:
        await bot.sync_commands()
        print('スラッシュコマンドを同期しました')
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