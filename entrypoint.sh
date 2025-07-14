#!/bin/bash

# データディレクトリを作成
mkdir -p /app/data/output

# bot_config.jsonをテンプレートから生成
if [ ! -f "/app/data/bot_config.json" ]; then
    echo "Generating bot_config.json from template..."
    envsubst < /app/bot_config.json.template > /app/data/bot_config.json
    echo "bot_config.json generated successfully"
else
    echo "bot_config.json already exists, skipping generation"
fi

# 元のコマンドを実行
exec "$@"