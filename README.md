# netops-bot

Network Operations Discord Bot - Cloudflare DNS管理とルーター自動化機能を統合したDiscord botです。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## 機能

### 🌐 DNS管理コマンド (`/dns`)
- `/dns list [type] [filter]` - DNSレコード一覧表示
- `/dns create <name> [ip] [type] [ttl] [proxy]` - 新規レコード作成
- `/dns update <name> <ip> [type]` - レコード更新
- `/dns delete <name> [type]` - レコード削除

### 📦 一括更新管理 (`/bulk`)
- `/bulk list` - 対象ドメインリスト表示
- `/bulk execute [domains]` - 一括更新実行
- `/bulk add <name>` - ドメイン追加
- `/bulk remove <name>` - ドメイン削除

### 🔧 ルーター管理 (`/router`)
- `/router update` - ルーター接続設定更新（コミュファ光自動化）

## セットアップ

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数の設定
以下の環境変数を設定してください：

```bash
# Discord Bot Token
export DISCORD_BOT_TOKEN="your_discord_bot_token_here"

# Cloudflare設定
export CLOUDFLARE_ZONE_ID="your_zone_id_here"
export CLOUDFLARE_API_TOKEN="your_api_token_here"
export CLOUDFLARE_DOMAIN="your_domain.com"

# ルーター設定（オプション）
export ROUTER_IP="192.168.0.1"
export ROUTER_USER="admin"
export ROUTER_PASS="your_router_password"
```

### 3. Discord Botの作成
1. [Discord Developer Portal](https://discord.com/developers/applications)でアプリケーションを作成
2. Botセクションでbotを作成してトークンを取得
3. OAuth2 > URL Generatorで以下のスコープを選択：
   - `bot`
   - `applications.commands`
4. Bot Permissionsで必要な権限を選択：
   - Send Messages
   - Use Slash Commands
5. 生成されたURLでbotをサーバーに招待

### 4. Botの起動
```bash
python discord_bot.py
```

## 使用例

### DNS管理
```
/dns list                          # 全DNSレコード表示
/dns list type:A                   # Aレコードのみ表示
/dns create name:api ip:192.168.1.100  # APIサブドメイン作成
/dns update name:api ip:10.0.0.1   # APIサブドメインのIP更新
/dns delete name:test              # testサブドメイン削除
```

### 一括更新
```
/bulk list                         # 対象ドメインリスト表示
/bulk add name:staging             # stagingドメインを追加
/bulk execute                      # 現在のIPで一括更新
/bulk execute domains:api,staging  # 特定のドメインのみ更新
/bulk remove name:old-domain       # 不要なドメインを削除
```

### ルーター管理
```
/router update                     # コミュファ光ルーターの接続設定更新
```

## ファイル構成

```
cloudflare/
├── run_bot.py               # ローカル実行エントリーポイント
├── Dockerfile              # Docker設定
├── docker-compose.yml      # Docker Compose設定
├── requirements.txt        # 依存関係
├── target_domains.json     # ドメインリストデータ
├── src/                    # Pythonソースコード
│   ├── discord_bot.py      # Discord botメインファイル
│   ├── dns_manager.py      # Cloudflare DNS管理クラス
│   ├── domain_list_manager.py # ドメインリスト管理
│   ├── router_automation.py # ルーター自動化スクリプト
│   ├── config.py           # 設定管理
│   └── utils.py            # ユーティリティ関数
└── README.md               # このファイル
```

## セキュリティ注意事項

1. **環境変数の必須設定**: 
   - すべての機密情報は`.env`ファイルで管理
   - コードに直接機密情報を書き込まない
   - `.env`ファイルは**絶対にGitHubにコミットしない**

2. **必須環境変数**:
   ```bash
   DISCORD_BOT_TOKEN=your_actual_token
   CLOUDFLARE_ZONE_ID=your_actual_zone_id
   CLOUDFLARE_API_TOKEN=your_actual_api_token
   ROUTER_PASS=your_actual_password
   ```

3. **権限制限**: Discord botには最小限の権限のみ付与してください

4. **アクセス制御**: 本番環境では特定のユーザーやロールのみがコマンドを実行できるよう制限することを推奨します

## トラブルシューティング

### よくある問題

1. **"attempted relative import with no known parent package"エラー**
   - 直接`python discord_bot.py`で実行してください

2. **Cloudflare API エラー**
   - ZONE_IDとAPI_TOKENが正しく設定されているか確認してください

3. **ルーター自動化の失敗**
   - ChromeDriverが正しくインストールされているか確認してください
   - ルーターのIP、ユーザー名、パスワードが正しいか確認してください

4. **Discord スラッシュコマンドが表示されない**
   - Bot起動時のコマンド同期メッセージを確認してください
   - 必要に応じてDiscordクライアントを再起動してください

## 貢献

バグ報告や機能提案は、GitHubのIssuesで受け付けています。

## ライセンス

MIT License