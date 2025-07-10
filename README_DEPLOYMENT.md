# AI動画編集ツール - デプロイメントガイド

## Streamlit Cloudの制限事項

### ファイルサイズ制限
- **アップロード上限: 500MB**
- 大きな動画ファイルには対応できません

### 推奨される使用方法

#### 1. 短い動画での利用
- 5-10分程度の短い動画
- 低解像度（720p以下）で圧縮された動画
- WebM形式で高圧縮率の動画

#### 2. 動画の事前圧縮
```bash
# FFmpegで動画を圧縮（例: 480pに変換）
ffmpeg -i input.mp4 -vf scale=854:480 -c:v libx264 -crf 28 -preset fast output_480p.mp4

# さらに圧縮（音声品質を下げる）
ffmpeg -i input.mp4 -vf scale=854:480 -c:v libx264 -crf 32 -c:a aac -b:a 96k output_compressed.mp4
```

#### 3. 動画の分割
長い動画は事前に分割してから処理：
```bash
# 最初の10分を切り出し
ffmpeg -i input.mp4 -t 00:10:00 -c copy part1.mp4

# 10分から20分を切り出し
ffmpeg -i input.mp4 -ss 00:10:00 -t 00:10:00 -c copy part2.mp4
```

## 代替デプロイメント方法

### 1. ローカル実行（推奨）
大きなファイルを扱う場合：
```bash
# ローカルでStreamlitを起動
streamlit run streamlit_app.py
```

### 2. Docker環境
```bash
# Dockerイメージをビルド
docker build -t ai-movie-edit .

# コンテナを起動
docker run -p 8501:8501 ai-movie-edit
```

### 3. 企業向けソリューション

#### a. AWS EC2 + Streamlit
- EC2インスタンスにデプロイ
- ファイルサイズ制限なし
- スケーラブル

#### b. Google Cloud Run
- コンテナベースのデプロイメント
- メモリとCPUの調整可能
- 自動スケーリング

#### c. Azure App Service
- Webアプリケーションのホスティング
- 大容量ファイル対応
- 企業向けセキュリティ

### 4. API化
バックエンドAPIとして実装し、別途フロントエンドを構築：
```python
# FastAPIでAPIサーバー化
from fastapi import FastAPI, UploadFile
app = FastAPI()

@app.post("/process")
async def process_video(file: UploadFile):
    # 処理ロジック
    pass
```

## ファイルサイズ対策の提案

1. **プログレッシブアップロード**
   - 動画を小さなチャンクに分割してアップロード
   - クライアント側でファイル分割

2. **外部ストレージ連携**
   - Google Drive / Dropbox からの直接読み込み
   - S3 URLからの動画取得

3. **音声のみ処理モード**
   - 動画から音声を抽出してアップロード
   - 音声ファイルは通常数十MB程度

## まとめ

Streamlit Cloudは手軽ですが、500MBの制限があるため：
- 短い動画や圧縮された動画での利用を推奨
- 本格的な利用には企業向けクラウドサービスやローカル環境を検討
- チーム利用なら社内サーバーでのホスティングが最適