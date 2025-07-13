#!/usr/bin/env python3
"""
Discord Bot for Cloudflare DNS Manager and Router Automation
"""

import discord
from discord.ext import commands
import os
import traceback
from dotenv import load_dotenv
from bot_config import Config

# .envファイルを読み込む
load_dotenv()

# Bot設定
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# 設定の検証
config = Config()
if not config.validate():
    print("エラー: ZONE_ID と API_TOKEN を設定してください")
    exit(1)

# Cogsの読み込み
def load_cogs():
    """Cogsを読み込み"""
    try:
        from cogs.dns_commands import DNSCommands
        from cogs.bulk_commands import BulkCommands
        from cogs.router_commands import RouterCommands
        
        bot.add_cog(DNSCommands(bot))
        bot.add_cog(BulkCommands(bot))
        bot.add_cog(RouterCommands(bot))
        
        print("Cogsを読み込みました")
    except Exception as e:
        print(f"Cogsの読み込みに失敗しました: {e}")
        raise

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

# Cogsを読み込み
load_cogs()

if __name__ == "__main__":
    # Discord botトークンを環境変数から取得
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("エラー: DISCORD_BOT_TOKEN環境変数を設定してください")
        exit(1)
    
    bot.run(token)