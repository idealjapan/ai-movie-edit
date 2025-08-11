# 会社のAPIを使用する設定方法

このドキュメントでは、AI動画編集ツールで会社のAPIを使用する方法を説明します。

## 設定方法

### 1. 環境変数ファイルの作成

プロジェクトのルートディレクトリに `.env` ファイルを作成し、以下の内容を設定します：

```bash
# カスタムAPI設定（会社のAPIを使用）
CUSTOM_WHISPER_ENDPOINT=https://your-company-api.com/v1/audio/transcriptions
CUSTOM_GPT_ENDPOINT=https://your-company-api.com/v1/chat/completions
CUSTOM_API_KEY=your-company-api-key-here

# モデル設定（必要に応じて変更）
WHISPER_MODEL=whisper-1
GPT_MODEL=gpt-4o
```

### 2. Streamlit Cloudでの設定

Streamlit Cloudで使用する場合：

1. Streamlit Cloudの管理画面を開く
2. アプリの設定（Settings）に移動
3. "Secrets"セクションで環境変数を追加：

```toml
CUSTOM_WHISPER_ENDPOINT = "https://your-company-api.com/v1/audio/transcriptions"
CUSTOM_GPT_ENDPOINT = "https://your-company-api.com/v1/chat/completions"
CUSTOM_API_KEY = "your-company-api-key-here"
WHISPER_MODEL = "whisper-1"
GPT_MODEL = "gpt-4o"
```

### 3. 動作確認

設定が正しく行われている場合：
- サイドバーに「🏢 会社のAPIを使用しています」と表示されます
- APIキーの入力欄が非表示になります

## API要件

会社のAPIは以下の仕様に準拠している必要があります：

### Whisper API（音声認識）
- エンドポイント: `/v1/audio/transcriptions`
- メソッド: POST
- リクエスト形式: multipart/form-data
- パラメータ:
  - `file`: 音声ファイル
  - `model`: モデル名
  - `response_format`: "verbose_json"
  - `timestamp_granularities[]`: "word"
  - `language`: "ja"

### GPT API（テキスト生成）
- エンドポイント: `/v1/chat/completions`
- メソッド: POST
- リクエスト形式: application/json
- パラメータ:
  - `model`: モデル名
  - `messages`: チャット履歴
  - `temperature`: 0.7
  - `max_tokens`: 4000

## トラブルシューティング

### APIが切り替わらない場合
1. 環境変数が正しく設定されているか確認
2. すべての必要な変数（ENDPOINT、API_KEY）が設定されているか確認
3. Streamlit Cloudの場合は、アプリを再起動

### エラーが発生する場合
1. APIエンドポイントのURLが正しいか確認
2. APIキーが有効か確認
3. APIの仕様がOpenAI互換か確認