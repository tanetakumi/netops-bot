#!/bin/bash

# Docker用の起動スクリプト

echo "=== Cloudflare Discord Bot Starting ==="
echo "Environment check:"
echo "- DISCORD_BOT_TOKEN: ${DISCORD_BOT_TOKEN:0:10}..."
echo "- CLOUDFLARE_ZONE_ID: ${CLOUDFLARE_ZONE_ID:0:10}..."
echo "- CLOUDFLARE_DOMAIN: $CLOUDFLARE_DOMAIN"
echo "- ROUTER_IP: $ROUTER_IP"

# ヘルスチェック用のシンプルなHTTPサーバーをバックグラウンドで起動
python3 -m http.server 8080 &

# Discord botを起動
exec python3 src/discord_bot.py