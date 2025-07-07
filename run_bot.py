#!/usr/bin/env python3
"""
Local execution entry point for Discord Bot
"""

import sys
import os

# srcディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Discord botを起動
from discord_bot import bot
import config

if __name__ == "__main__":
    # Discord botトークンを環境変数から取得
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("エラー: DISCORD_BOT_TOKEN環境変数を設定してください")
        exit(1)
    
    bot.run(token)