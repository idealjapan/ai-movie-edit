# チーム向けセットアップガイド

## 🚀 30秒でセットアップ

### 前提条件
- Docker Desktop のインストール（5分）
- GitHubアカウント

### セットアップ手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/idealjapan/ai-movie-edit.git
cd ai-movie-edit

# 2. 環境変数ファイルを作成
cp .env.example .env

# 3. .envファイルを編集してAPIキーを設定
# OPENAI_API_KEY=sk-xxxxx...

# 4. 起動！
docker-compose up
```

### アクセス
ブラウザで `http://localhost:8501` を開く

## 📝 日常の使い方

### 起動
```bash
cd ai-movie-edit
docker-compose up
```

### 停止
```bash
docker-compose down
```

### 更新（新機能が追加された時）
```bash
git pull
docker-compose down
docker-compose up --build
```

## 🎯 チーム管理者向け

### APIキーの共有方法

#### 方法1: 環境変数ファイルを配布
```bash
# .envファイルを作成してチームに配布
echo "OPENAI_API_KEY=sk-xxxxx..." > .env
```

#### 方法2: チーム共有サーバー
1台のPCで起動して、チーム全員がアクセス：
```bash
# docker-compose.ymlを編集
# ports: - "0.0.0.0:8501:8501"
docker-compose up
```

チームは `http://ホストPC-IP:8501` でアクセス

## ⚡ トラブルシューティング

### Docker Desktopが起動しない
→ PCを再起動

### ポート8501が使用中
→ 別のStreamlitが起動中。停止するか別ポート使用

### メモリ不足
→ Docker Desktop設定でメモリ割り当てを増加

## 🔥 プロ向けTips

### エイリアス設定
```bash
# ~/.bashrc or ~/.zshrc に追加
alias movie-edit='cd ~/ai-movie-edit && docker-compose up'
alias movie-stop='cd ~/ai-movie-edit && docker-compose down'
```

使い方：
```bash
movie-edit  # 起動
movie-stop  # 停止
```

### 自動起動設定
PC起動時に自動で立ち上げ：
```yaml
# docker-compose.yml
services:
  streamlit-app:
    restart: always  # 常に再起動
```

## 📊 パフォーマンス設定

大きなファイルを扱う場合：
```yaml
# docker-compose.yml
services:
  streamlit-app:
    environment:
      - STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000  # 10GB
    deploy:
      resources:
        limits:
          memory: 8G  # 8GBメモリ割り当て
```