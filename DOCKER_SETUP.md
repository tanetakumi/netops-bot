# Docker Setup Guide

CloudflareディスコードBot をDockerコンテナで実行するためのセットアップガイドです。

## 📁 ファイル構成

```
cloudflare/
├── docker-compose.yml     # Docker Compose設定
├── Dockerfile            # Docker設定
├── .env.example          # 環境変数テンプレート
├── .env                  # 環境変数設定（作成が必要）
├── docker-start.sh       # Docker起動スクリプト
├── requirements.txt      # Python依存関係
├── run_bot.py            # Discord botローカル実行
├── src/                  # Pythonソースコード
│   ├── discord_bot.py    # Discord botメインファイル
│   ├── dns_manager.py    # DNS管理
│   ├── router_automation.py # ルーター自動化
│   └── ... (その他のPythonファイル)
└── target_domains.json   # ドメインリストデータ
```

## 🚀 セットアップ手順

### 1. 環境変数ファイルの作成
```bash
# テンプレートをコピー
cp .env.example .env

# .envファイルを編集
nano .env
```

### 2. .envファイルの設定
```env
# Discord Bot設定
DISCORD_BOT_TOKEN=your_discord_bot_token_here

# Cloudflare設定
CLOUDFLARE_ZONE_ID=your_zone_id_here
CLOUDFLARE_API_TOKEN=your_api_token_here
CLOUDFLARE_DOMAIN=craftershub.jp

# ルーター設定
ROUTER_IP=192.168.0.1
ROUTER_USER=admin
ROUTER_PASS=your_router_password_here

# Selenium設定
DISPLAY=:99
```

### 3. Docker Compose でビルド＆起動
```bash
# Discord bot を起動
docker-compose up -d

# ログを確認
docker-compose logs -f cloudflare-discord-bot
```

## 🔧 運用コマンド

### 基本操作
```bash
# 起動
docker-compose up -d

# 停止
docker-compose down

# 再起動
docker-compose restart

# ログ確認
docker-compose logs -f cloudflare-discord-bot

# コンテナに入る
docker-compose exec cloudflare-discord-bot bash
```

### ローカル実行（Docker不使用）
```bash
# Discord bot起動（すべての機能を含む）
python run_bot.py
```

### イメージの更新
```bash
# イメージを再ビルド
docker-compose build --no-cache

# 起動
docker-compose up -d
```

## 📋 サービス構成

### cloudflare-discord-bot
- **役割**: 統合Discord bot（DNS管理 + ルーター自動化）
- **ポート**: なし（Discord WebSocketを使用）
- **ボリューム**: 
  - `./output:/app/output` - ルーター自動化の出力
  - `./target_domains.json:/app/target_domains.json` - ドメインリスト
- **再起動**: `unless-stopped`
- **機能**:
  - DNS管理 (`/dns` コマンド)
  - 一括更新 (`/bulk` コマンド)
  - ルーター自動化 (`/router update` コマンド)

## 🔍 トラブルシューティング

### よくある問題と解決方法

#### 1. Bot起動エラー
```bash
# ログを確認
docker-compose logs cloudflare-discord-bot

# 環境変数の確認
docker-compose exec cloudflare-discord-bot env | grep -E "(DISCORD|CLOUDFLARE)"
```

#### 2. ルーター自動化エラー
```bash
# Selenium ChromeDriverの確認
docker-compose exec cloudflare-discord-bot /usr/bin/chromedriver --version

# ディスプレイ設定の確認
docker-compose exec cloudflare-discord-bot echo $DISPLAY
```

#### 3. 権限エラー
```bash
# output ディレクトリの権限確認
ls -la output/

# 権限修正
sudo chown -R $USER:$USER output/
```

#### 4. ネットワーク接続エラー
```bash
# コンテナからの外部接続テスト
docker-compose exec cloudflare-discord-bot curl -I https://api.cloudflare.com

# DNS確認
docker-compose exec cloudflare-discord-bot nslookup discord.com
```

#### 5. ボリュームマウントエラー
```bash
# ボリュームの状態確認
docker volume ls

# ボリュームを削除して再作成
docker-compose down -v
docker-compose up -d
```

## 📊 監視とログ

### ヘルスチェック
コンテナには自動ヘルスチェックが設定されています：
```bash
# ヘルスチェック状況確認
docker-compose ps
```

### ログローテーション
本番環境では以下の設定を追加することを推奨：
```yaml
services:
  cloudflare-discord-bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔒 セキュリティ考慮事項

1. **環境変数の保護**
   - `.env`ファイルを`.gitignore`に追加
   - ファイルの権限を適切に設定: `chmod 600 .env`

2. **ネットワークセキュリティ**
   - 必要最小限のポートのみ開放
   - ファイアウォール設定の確認

3. **定期更新**
   - ベースイメージの定期更新
   - 依存関係の脆弱性チェック

## 🚀 本番環境向け設定

### docker-compose.prod.yml (例)
```yaml
version: '3.8'

services:
  cloudflare-discord-bot:
    build: .
    restart: always
    volumes:
      - ./output:/app/output
      - ./target_domains.json:/app/target_domains.json
      - ./logs:/app/logs
    env_file:
      - .env
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:4444/wd/hub/status', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

使用方法:
```bash
docker-compose -f docker-compose.prod.yml up -d
```