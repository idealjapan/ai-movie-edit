# SRTタイミング精度向上ガイド

## 問題点と解決策

### 従来の問題
- Whisperのセグメント（発話単位）とGPT整形後の行（改行単位）を単純にマッピング
- GPTが改行を入れると、実際の発話タイミングとずれが発生

### 改良版の解決策
OpenAI Whisper APIの**単語レベルタイムスタンプ**機能を活用：
- `timestamp_granularities=["word"]`パラメータで単語ごとのタイミングを取得
- GPT整形後のテキストと単語を照合して正確なタイミングを計算

## 使い方

### 改良版スクリプトの実行
```bash
# 基本的な使い方
python generate_srt_improved.py edited_video.mp4

# オプション指定
python generate_srt_improved.py edited_video.mp4 \
  --max-chars-per-line 25 \
  --output custom_subtitles.srt
```

### 従来版との比較
```bash
# 従来版（セグメントベース）
python generate_srt.py video.mp4

# 改良版（単語レベル）
python generate_srt_improved.py video.mp4
```

## 技術的な詳細

### 1. Whisper APIの変更点
```python
# 従来
data = {
    "model": self.model,
    "response_format": "verbose_json",
    "language": "ja"
}

# 改良版
data = {
    "model": self.model,
    "response_format": "verbose_json",
    "timestamp_granularities[]": "word",  # 追加
    "language": "ja"
}
```

### 2. タイミング照合アルゴリズム
1. GPT整形後の各行から実際の文字を抽出（記号除去）
2. 単語タイムスタンプと順番に照合
3. 各行の最初の単語の開始時刻と最後の単語の終了時刻を記録
4. 80%以上マッチしたら次の行へ

### 3. フォールバック機能
単語タイムスタンプが利用できない場合は、従来のセグメントベース処理に自動的にフォールバック

## 期待される改善効果

- **タイミング精度**: セグメント単位（数秒）→ 単語単位（0.1秒以下）
- **改行の自由度**: GPTがどのように改行しても正確なタイミングを維持
- **編集効率**: Premiere Proでの手動調整が大幅に削減

## 注意事項

- 単語レベルタイムスタンプの生成には若干の追加処理時間がかかります
- Whisper APIの最新バージョンが必要です（2024年以降）
- 日本語の場合、単語の区切りは形態素解析に基づきます

## トラブルシューティング

### エラー：`timestamp_granularities`が認識されない
→ OpenAI APIクライアントを最新版に更新してください

### 単語タイムスタンプが取得できない
→ APIレスポンスの`words`フィールドを確認し、フォールバック処理が動作しているか確認

### タイミングがまだずれる
→ `--max-chars-per-line`を調整して、1行の文字数を最適化してください