#!/bin/bash

# AI動画編集ツール - ローカルデプロイスクリプト

echo "🚀 AI動画編集ツールをローカルで起動します..."

# .envファイルの確認
if [ ! -f .env ]; then
    echo "⚠️  .envファイルが見つかりません"
    echo "📝 .env.exampleから.envを作成してください："
    echo "   cp .env.example .env"
    echo "   そして、APIキーを設定してください"
    exit 1
fi

# Dockerの確認
if ! command -v docker &> /dev/null; then
    echo "❌ Dockerがインストールされていません"
    echo "📦 https://www.docker.com/products/docker-desktop からインストールしてください"
    exit 1
fi

# Docker Composeで起動
echo "🐳 Dockerコンテナを起動中..."
docker-compose up -d

echo "✅ 起動完了！"
echo "🌐 ブラウザで http://localhost:8501 にアクセスしてください"
echo ""
echo "📌 停止するには: docker-compose down"
echo "📊 ログを見るには: docker-compose logs -f"