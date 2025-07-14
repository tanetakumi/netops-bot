#!/usr/bin/env python3
"""
DNS管理コマンドCog
"""

import discord
from discord.ext import commands
from typing import Optional
from dns_manager import CloudflareDNSManager
from bot_config import Config
from utils import log

class DNSCommands(commands.Cog):
    """DNS管理コマンドグループ"""
    
    def __init__(self, bot):
        self.bot = bot
        config = Config()
        self.dns_manager = CloudflareDNSManager(config)
    
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
                    
                    # フィールドの値を構築
                    field_value = f"**Content:** `{content}`\n**TTL:** {ttl}\n**Proxied:** {'Yes' if proxied else 'No'}"
                    
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
        name: str
    ):
        """DNSレコードを削除"""
        await ctx.defer()
        
        try:
            success = self.dns_manager.delete_record(name)
            
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

def setup(bot):
    """Cogをbotに追加"""
    bot.add_cog(DNSCommands(bot))