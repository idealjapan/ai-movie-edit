# ローカルデプロイメントガイド（ファイルサイズ制限なし）

## 🚀 クイックスタート

### 1. 前提条件
- Docker Desktop のインストール
- APIキーの設定（.envファイル）

### 2. セットアップ
```bash
# リポジトリをクローン
git clone https://github.com/idealjapan/ai-movie-edit.git
cd ai-movie-edit

# 環境変数ファイルを作成
cp .env.example .env
# .envファイルを編集してAPIキーを設定

# デプロイスクリプトを実行
./deploy_local.sh
```

### 3. アクセス
ブラウザで http://localhost:8501 を開く

## 🎯 メリット
- **ファイルサイズ制限なし**（10GB以上も可能）
- **高速処理**（ローカルリソース使用）
- **プライバシー保護**（データが外部に出ない）
- **カスタマイズ可能**

## 🏢 チーム向け設定

### 社内ネットワークで共有
```bash
# 他のPCからアクセス可能にする
streamlit run streamlit_app.py --server.address 0.0.0.0
```

チームメンバーは `http://<あなたのIPアドレス>:8501` でアクセス

### 社内サーバーにデプロイ
1. サーバーにDockerをインストール
2. このリポジトリをクローン
3. `docker-compose up -d` で起動
4. Nginxでリバースプロキシ設定（オプション）

## 📝 設定のカスタマイズ

### ファイルサイズ上限の変更
`streamlit_app.py` で以下を追加：
```python
# 10GBまで対応
st.set_option('server.maxUploadSize', 10000)
```

### メモリ制限の調整
`docker-compose.yml` で：
```yaml
services:
  streamlit-app:
    mem_limit: 8g  # 8GBまで使用可能
```

## 🔧 トラブルシューティング

### ポート8501が使用中
```bash
# 別のポートを使用
docker-compose down
# docker-compose.ymlのポートを変更（例: 8502:8501）
docker-compose up -d
```

### メモリ不足エラー
Docker Desktopの設定でメモリ割り当てを増やす

## 📊 パフォーマンス最適化

### 1. SSDを使用
一時ファイルの保存先をSSDに：
```yaml
volumes:
  - /path/to/ssd/temp:/app/temp
```

### 2. 並列処理
複数の動画を同時処理する場合はワーカー数を調整

### 3. GPU活用（将来的な拡張）
CUDAサポートでさらなる高速化が可能