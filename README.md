# AI動画編集ツール

自動的に無音区間を検出してカットし、Premiere Pro用のXMLを生成するツールです。

## 機能

- 動画の無音区間を自動検出
- 無音区間をカットしたPremiere Pro用XMLファイルの生成
- テロップ情報の追加（captions.jsonファイルから）

## 必要なもの

- Python 3.7以上
- 以下のPythonパッケージ:
  - librosa
  - soundfile
  - pydub
  - numpy
  - FFmpeg（システムにインストールが必要）

## インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/ai_video_editor.git
cd ai_video_editor

# 必要なパッケージをインストール
pip install -r requirements.txt
```

## 使い方

### 基本的な使い方

```bash
python main.py <動画ファイルパス> [オプション]
```

例:
```bash
python main.py sample_data/your_video.mp4 --min-silence 1000 --silence-thresh -40
```

### 利用可能なオプション

- `--output`, `-o`: 出力XMLファイルのパス（省略時は動画ファイル名_edited.xml）
- `--min-silence`: 無音と判定する最小の長さ（ミリ秒）（デフォルト: 1000）
- `--silence-thresh`: 無音と判定する音量のしきい値（dB）（デフォルト: -35）
- `--keep-silence`: 無音区間の前後に残す無音の長さ（ミリ秒）（デフォルト: 200）
- `--temp-dir`: 一時ファイルの保存ディレクトリ（デフォルト: temp）
- `--captions`: 使用するテロップデータのJSONファイルパス
- `--segments`: 使用するセグメントデータのJSONファイルパス（無音検出をスキップ）

### テロップデータの形式

テロップデータはJSON形式で、以下のような構造になっています:

```json
{
  "original_text": "元のテキスト全体",
  "formatted_text": "整形されたテキスト",
  "captions": [
    {
      "text": "テロップ1の内容",
      "start": 0.0,
      "end": 5.0
    },
    {
      "text": "テロップ2の内容",
      "start": 5.0,
      "end": 10.0
    }
  ]
}
```

### セグメントデータの形式

セグメントデータはJSON形式で、以下のような構造になっています:

```json
[
  {
    "index": 0,
    "start": 0,
    "end": 5,
    "duration": 5
  },
  {
    "index": 1,
    "start": 10,
    "end": 15,
    "duration": 5
  }
]
```

## 処理の流れ

1. 動画ファイルから音声を抽出
2. 音声から無音区間を検出
3. 音声がある区間のリストを作成
4. テロップデータがある場合は読み込み
5. Premiere Pro用のXMLファイルを生成

## GUIモード

このツールはコマンドラインだけでなく、GUIインターフェイスでも操作できます。
GUIモードを起動するには、以下のコマンドを実行します:

```bash
python app.py
```

## 注意事項

- 大きなファイルの処理には時間がかかる場合があります
- 出力されたXMLはAdobe Premiere Pro用に最適化されています
