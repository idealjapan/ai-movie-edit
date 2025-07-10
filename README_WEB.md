# AI字幕生成ツール - Web版

## 概要
動画ファイルから高精度な字幕（SRT）を自動生成するWebアプリケーションです。
日本語に特化した文字レベルのタイムスタンプで、Premiere Proでの調整作業を大幅に削減できます。

## 特徴
- 🎯 **高精度**: 文字レベルのタイムスタンプ
- 🇯🇵 **日本語特化**: 日本語の文字認識に最適化
- 🚀 **簡単操作**: ドラッグ&ドロップで動画をアップロード
- 👥 **チーム共有**: URLを共有するだけで利用可能

## 使い方

### 1. アクセス
Streamlit CloudにデプロイされたURLにアクセスします。

### 2. APIキーの入力
サイドバーにOpenAI APIキーを入力します。
- APIキーは`sk-`で始まる文字列です
- [OpenAI Platform](https://platform.openai.com/api-keys)で取得できます

### 3. 動画のアップロード
- 対応形式: MP4, MOV, AVI, MKV, M4V
- 最大サイズ: 500MB
- ドラッグ&ドロップまたはクリックで選択

### 4. 字幕生成
「🚀 字幕を生成」ボタンをクリックして処理を開始します。
- 処理時間: 5分の動画で約2-3分
- プログレスバーで進捗を確認

### 5. ダウンロード
生成されたSRTファイルをダウンロードします。

## デプロイ方法

### Streamlit Cloudでのデプロイ

1. **GitHubリポジトリの準備**
   ```bash
   git add .
   git commit -m "Add Streamlit web app"
   git push origin main
   ```

2. **Streamlit Cloudにサインイン**
   - https://streamlit.io/cloud
   - GitHubアカウントでログイン

3. **新規アプリを作成**
   - "New app"をクリック
   - リポジトリを選択
   - Branch: `main`
   - Main file path: `streamlit_app.py`

4. **デプロイ**
   - "Deploy"をクリック
   - 数分で自動的にビルド・デプロイされます

### ローカルでのテスト

```bash
# 依存関係のインストール
pip install -r requirements_web.txt

# アプリの起動
streamlit run streamlit_app.py
```

## 必要な環境変数
特になし（APIキーはユーザーが入力）

## 制限事項
- 同時利用は1-2人程度を想定
- ファイルサイズは500MBまで
- 処理時間が長い場合はタイムアウトする可能性があります

## トラブルシューティング

### エラー: "FFmpeg not found"
→ Streamlit Cloudの場合、`packages.txt`にffmpegが記載されているか確認

### エラー: "API key invalid"
→ OpenAI APIキーが正しく入力されているか確認

### 処理が途中で止まる
→ ファイルサイズが大きすぎる可能性。より小さいファイルで試してください

## セキュリティ
- APIキーはサーバーに保存されません
- アップロードファイルは処理後自動的に削除されます
- HTTPSで暗号化された通信

## サポート
問題が発生した場合は、GitHubのIssuesで報告してください。