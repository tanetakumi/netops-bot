#!/usr/bin/env python3
"""
一括更新管理コマンドCog
"""

import discord
from discord.ext import commands
from typing import Optional
from dns_manager import CloudflareDNSManager
from bot_config import Config
from utils import log

class BulkCommands(commands.Cog):
    """一括更新管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
        config = Config()
        self.dns_manager = CloudflareDNSManager(config)
    
    bulk_group = discord.SlashCommandGroup("bulk", "一括更新管理コマンド")
    
    @bulk_group.command(name="list", description="対象ドメインリスト表示")
    async def bulk_list(self, ctx):
        """一括更新対象のドメインリストを表示"""
        await ctx.defer()
        
        try:
            domains = self.dns_manager.domain_manager.get_domains()
            
            if domains:
                domain_list = "\n".join([f"• {domain}.{self.dns_manager.config.domain}" for domain in domains])
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
    async def bulk_execute(self, ctx):
        """一括更新を実行"""
        await ctx.defer()
        
        try:
            
            # 現在のIPアドレスを取得
            from utils import get_current_ip
            current_ip = get_current_ip(self.dns_manager.config.ip_services)
            
            success, successful_domains, failed_domains = await self.dns_manager.bulk_update_records()
            
            if success:
                embed = discord.Embed(
                    title="✅ 一括更新完了",
                    description=f"すべてのドメインの更新が完了しました\n**更新先IPアドレス:** `{current_ip}`",
                    color=0x00ff00
                )
                if successful_domains:
                    embed.add_field(
                        name="✅ 更新成功",
                        value=f"• " + f"\n• ".join([f"{d}.{self.dns_manager.config.domain}" for d in successful_domains]),
                        inline=False
                    )
            else:
                embed = discord.Embed(
                    title="⚠️ 一括更新完了（一部失敗）",
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
            
            await ctx.followup.send(embed=embed)
            
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

def setup(bot):
    """Cogをbotに追加"""
    bot.add_cog(BulkCommands(bot))