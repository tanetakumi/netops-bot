#!/usr/bin/env python3
"""
ルーター管理コマンドCog
"""

import discord
from discord.ext import commands, tasks
import subprocess
import os
import datetime
import asyncio
from bot_config import BotConfig, Config
from croniter import croniter
from utils import log
from dns_manager import CloudflareDNSManager

class RouterCommands(commands.Cog):
    """ルーター管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
        self.bot_config = BotConfig()
        self.last_execution_time = None
        # Initialize DNS manager for bulk updates
        config = Config()
        self.dns_manager = CloudflareDNSManager(config)
        log("Starting scheduler task...", "INFO")
        self.scheduler_task.start()
    
    def cog_unload(self):
        log("Stopping scheduler task...", "INFO")
        self.scheduler_task.cancel()
    
    router_group = discord.SlashCommandGroup("router", "ルーター管理コマンド")
    
    @router_group.command(name="schedule-update", description="ルーター更新スケジュール設定")
    async def router_schedule_update(self, ctx, cron_expression: str):
        """ルーター更新のスケジュールを設定"""
        await ctx.defer()
        
        try:
            if not croniter.is_valid(cron_expression):
                await ctx.followup.send("❌ 無効なcron式です。例: `0 9 * * *` (毎日9時)", ephemeral=True)
                return
            
            cron = croniter(cron_expression, datetime.datetime.now())
            next_run = cron.get_next(datetime.datetime)
            
            success = self.bot_config.update_router_schedule(cron_expression, ctx.channel.id)
            
            if not success:
                await ctx.followup.send("❌ スケジュール設定の更新に失敗しました", ephemeral=True)
                return
            
            self.bot_config.reload()
            
            # スケジュールタスクを再起動
            log("Restarting scheduler task with new schedule...", "INFO")
            if self.scheduler_task.is_running():
                self.scheduler_task.cancel()
                log("Cancelled existing scheduler task", "INFO")
            
            # 少し待ってから再起動
            await asyncio.sleep(1)
            self.scheduler_task.start()
            log(f"Restarted scheduler task with new cron: {cron_expression}", "INFO")
            
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
            schedule_config = self.bot_config.get_router_schedule_config()
            
            if not schedule_config or not schedule_config.get("cron"):
                embed = discord.Embed(
                    title="📋 スケジュール表示",
                    description="設定されたスケジュールがありません",
                    color=0xffaa00
                )
                await ctx.followup.send(embed=embed)
                return
            
            cron_expr = schedule_config["cron"]
            cron = croniter(cron_expr, datetime.datetime.now())
            next_run = cron.get_next(datetime.datetime)
            
            embed = discord.Embed(
                title="📋 ルーター更新スケジュール",
                color=0x0099ff
            )
            
            embed.add_field(name="Cron式", value=f"`{cron_expr}`", inline=False)
            
            channel_id = schedule_config.get("channel_id")
            if channel_id:
                embed.add_field(name="ログ送信チャンネル", value=f"<#{channel_id}>", inline=False)
            
            embed.add_field(name="次回実行", value=next_run.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            
            embed.add_field(
                name="📝 Cron式の形式",
                value="```\n分 時 日 月 曜日\n*  *  *  *  *\n```",
                inline=False
            )
            embed.add_field(
                name="📋 例",
                value="`0 9 * * *` → 毎日 9:00\n`0 0 * * 0` → 毎週日曜日 0:00\n`0 12 1 * *` → 毎月1日 12:00\n`30 14 * * 1-5` → 平日 14:30",
                inline=False
            )
            
            await ctx.followup.send(embed=embed)
            
        except Exception as e:
            await ctx.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)
            log(f"Router schedule show error: {e}", "ERROR")
    
    @tasks.loop(minutes=1)
    async def scheduler_task(self):
        """スケジュールされたタスクを実行"""
        try:
            log("Scheduler task running...", "INFO")
            schedule_config = self.bot_config.get_router_schedule_config()
            log(f"Schedule config: {schedule_config}", "INFO")
            
            if not schedule_config or not schedule_config.get("cron"):
                log("No schedule config or cron expression found", "INFO")
                return
            
            cron_expr = schedule_config["cron"]
            channel_id = schedule_config.get("channel_id")
            log(f"Cron expression: {cron_expr}, Channel ID: {channel_id}", "INFO")
            
            if not channel_id or not croniter.is_valid(cron_expr):
                log("Invalid channel ID or cron expression", "ERROR")
                return
            
            current_time = datetime.datetime.now()
            normalized_time = current_time.replace(second=0, microsecond=0)
            
            # croniterで次の実行時刻を取得
            cron = croniter(cron_expr, normalized_time - datetime.timedelta(minutes=1))
            next_run = cron.get_next(datetime.datetime)
            
            log(f"Current time: {current_time}, Normalized: {normalized_time}", "INFO")
            log(f"Next scheduled run: {next_run}", "INFO")
            
            if next_run == normalized_time:
                log("Cron time matches! Checking execution conditions...", "INFO")
                if (self.last_execution_time is None or 
                    (current_time - self.last_execution_time).total_seconds() >= 60):
                    
                    log("Executing scheduled router update...", "INFO")
                    self.last_execution_time = current_time
                    await self.execute_scheduled_router_update(channel_id, schedule_config)
                else:
                    log("Skipping execution - too soon after last execution", "INFO")
            else:
                log("Cron time does not match current time", "INFO")
                    
        except Exception as e:
            log(f"Scheduler task error: {e}", "ERROR")
    
    @scheduler_task.before_loop
    async def before_scheduler_task(self):
        await self.bot.wait_until_ready()
        log("Scheduler task is ready to start", "INFO")
    
    @scheduler_task.error
    async def scheduler_task_error(self, error):
        log(f"Scheduler task loop error: {error}", "ERROR")
    
    async def execute_scheduled_router_update(self, channel_id, schedule_config):
        """スケジュールされたルーター更新を実行"""
        try:
            log(f"Executing scheduled router update - Channel: {channel_id}", "INFO")
            
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                log(f"Channel {channel_id} not found", "ERROR")
                return
            
            embed = discord.Embed(
                title="🔄 スケジュールされたルーター更新を開始しました",
                description="コミュファ光の接続設定を更新中です",
                color=0xffaa00
            )
            embed.add_field(name="Cron式", value=f"`{schedule_config['cron']}`", inline=False)
            embed.add_field(name="実行時刻", value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), inline=False)
            
            status_message = await channel.send(embed=embed)
            
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "router_automation.py")
            
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                embed = discord.Embed(
                    title="✅ スケジュールされたルーター更新完了",
                    description="コミュファ光の接続設定更新が完了しました",
                    color=0x00ff00
                )
                if result.stdout:
                    output = result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout
                    embed.add_field(name="実行結果", value=f"```\n{output}\n```", inline=False)
                
                log(f"Scheduled router update completed successfully - Channel: {channel_id}", "INFO")
                
                # Automatically trigger bulk domain update after successful router update
                await self.execute_bulk_domain_update(channel)
            else:
                embed = discord.Embed(
                    title="❌ スケジュールされたルーター更新失敗",
                    description="ルーター設定更新中にエラーが発生しました",
                    color=0xff0000
                )
                if result.stderr:
                    error_output = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
                    embed.add_field(name="エラー詳細", value=f"```\n{error_output}\n```", inline=False)
                
                log(f"Scheduled router update failed - Channel: {channel_id}, Error: {result.stderr}", "ERROR")
            
            await channel.send(embed=embed)
            
        except subprocess.TimeoutExpired:
            embed = discord.Embed(
                title="⏰ スケジュールされたルーター更新タイムアウト",
                description="ルーター設定更新がタイムアウトしました（5分）",
                color=0xffaa00
            )
            if channel:
                await channel.send(embed=embed)
            log(f"Scheduled router update timeout - Channel: {channel_id}", "ERROR")
            
        except Exception as e:
            log(f"Scheduled router update error - Channel: {channel_id}: {e}", "ERROR")
            if channel:
                embed = discord.Embed(
                    title="❌ スケジュールされたルーター更新エラー",
                    description=f"エラーが発生しました: {str(e)}",
                    color=0xff0000
                )
                await channel.send(embed=embed)
    
    async def execute_bulk_domain_update(self, channel):
        """ルーター更新後の自動ドメイン一括更新を実行"""
        try:
            log("Executing automatic bulk domain update after router update", "INFO")
            
            # 現在のIPアドレスを取得
            from utils import get_current_ip
            current_ip = get_current_ip(self.dns_manager.config.ip_services)
            
            # 一括更新を実行
            success, successful_domains, failed_domains = await self.dns_manager.bulk_update_records()
            
            if success:
                embed = discord.Embed(
                    title="✅ ドメイン一括更新完了",
                    description=f"すべてのドメインが新しいIPアドレスで更新されました\n**更新先IPアドレス:** `{current_ip}`",
                    color=0x00ff00
                )
                if successful_domains:
                    embed.add_field(
                        name="✅ 更新成功",
                        value=f"• " + f"\n• ".join([f"{d}.{self.dns_manager.config.domain}" for d in successful_domains]),
                        inline=False
                    )
                log("Automatic bulk domain update completed successfully", "INFO")
            else:
                embed = discord.Embed(
                    title="⚠️ ドメイン一括更新完了（一部失敗）",
                    description=f"一部のドメインの更新に失敗しました\n**更新先IPアドレス:** `{current_ip}`",
                    color=0xffaa00
                )
                if successful_domains:
                    embed.add_field(
                        name="✅ 更新成功",
                        value=f"• " + f"\n• ".join([f"{d}.{self.dns_manager.config.domain}" for d in successful_domains]),
                        inline=False
                    )
                if failed_domains:
                    embed.add_field(
                        name="❌ 更新失敗",
                        value=f"• " + f"\n• ".join([f"{d}.{self.dns_manager.config.domain}" for d in failed_domains]),
                        inline=False
                    )
                log("Automatic bulk domain update completed with some failures", "WARNING")
            
            await channel.send(embed=embed)
            
        except Exception as e:
            log(f"Automatic bulk domain update error: {e}", "ERROR")
            embed = discord.Embed(
                title="❌ ドメイン一括更新エラー",
                description=f"自動ドメイン更新中にエラーが発生しました: {str(e)}",
                color=0xff0000
            )
            await channel.send(embed=embed)
    
    @scheduler_task.before_loop
    async def before_scheduler_task(self):
        """スケジューラー開始前にBotの準備を待つ"""
        await self.bot.wait_until_ready()

def setup(bot):
    """Cogをbotに追加"""
    bot.add_cog(RouterCommands(bot))