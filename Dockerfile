# Selenium公式のStandaloneイメージを使用（Discord botとルーター自動化の両方に対応）
FROM selenium/standalone-chrome:4.15.0-20231129

# root権限に切り替え
USER root

# pipをインストール (Python3は既に含まれている)
RUN apt-get update && apt-get install -y \
    python3-distutils \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && wget https://bootstrap.pypa.io/get-pip.py \
    && python3 get-pip.py \
    && rm get-pip.py

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY src/ ./src/
COPY bot_config.json ./

# 出力ディレクトリを作成（ルーター自動化用）
RUN mkdir -p /app/output

# Pythonパスを設定
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Discord botを実行（デフォルト）
CMD ["python3", "-u", "src/discord_bot.py"]