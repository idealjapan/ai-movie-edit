# 🚨 Premiere Pro インポートエラー解決ガイド

## あなたの問題を即座に解決！

### 🔥 今すぐ実行するコマンド

```bash
# XMLを修正
python3 fix_xml_immediate.py output/IMG_2525_edited.xml

# または動画ファイルを指定
python3 fix_xml_immediate.py output/IMG_2525_edited.xml /path/to/IMG_2525.mp4
```

## 📁 正しいフォルダ構成

### ✅ これが正解！
```
📁 デスクトップ/
└── 📁 動画編集/
    ├── 🎬 IMG_2525.mp4        （元動画）
    ├── 📄 IMG_2525_edited.xml  （同じフォルダ！）
    └── 📄 project.prproj       （Premiereプロジェクト）
```

### ❌ これはダメ！
```
📁 デスクトップ/
├── 📁 動画/
│   └── 🎬 IMG_2525.mp4        （動画はここ）
└── 📁 XML/
    └── 📄 IMG_2525_edited.xml  （XMLは別フォルダ）
```

## 🛠️ 3つの解決方法

### 方法1: 即効性重視（推奨）
1. **動画とXMLを同じフォルダに移動**
2. **fix_xml_immediate.py を実行**
3. **Premiere Proで読み込み**

### 方法2: 手動修正
1. XMLをテキストエディタで開く
2. `<pathurl>` タグを探す
3. パスを以下のように修正：
   ```xml
   <!-- 間違い -->
   <pathurl>file://localhost/%E3%83%A6%E3%83%BC%E3%82%B6/takayakazuki/...</pathurl>
   
   <!-- 正しい -->
   <pathurl>file://localhost/Users/takayakazuki/Desktop/IMG_2525.mp4</pathurl>
   ```

### 方法3: Premiere Pro内で解決
1. エラーが出たら「OK」をクリック
2. プロジェクトパネルでオフラインクリップを右クリック
3. 「メディアをリンク...」を選択
4. 「ファイル名で一致」にチェック
5. 動画ファイルを選択

## 🎯 エラーの原因

あなたのケースでは：
- `/ユーザ/` という文字化けしたパスが原因
- 正しくは `/Users/` であるべき
- 日本語環境でのURLエンコーディングの問題

## ⚡ クイックチェックリスト

インポート前に確認：
- [ ] 動画ファイルが存在する
- [ ] XMLと動画が同じフォルダにある
- [ ] ファイル名が一致している
- [ ] Premiere Proが最新版

## 🚀 今後のベストプラクティス

### 1. フォルダ名は英語で
```
❌ /デスクトップ/動画編集/
✅ /Desktop/video_edit/
```

### 2. ファイル名もシンプルに
```
❌ テスト動画 (1) - コピー.mp4
✅ test_video_01.mp4
```

### 3. プロジェクトテンプレート
```bash
# プロジェクトフォルダを作成
mkdir my_project
cd my_project

# 動画をコピー
cp ~/Desktop/video.mp4 .

# XMLを生成（同じフォルダに）
python3 ~/AI_動画カット＆テロップツール/main.py video.mp4

# Premiere Proで開く
# すべてが同じフォルダなので問題なし！
```

---

## 💡 それでも解決しない場合

1. **XMLの中身を確認**
   ```bash
   grep pathurl IMG_2525_edited.xml
   ```

2. **パスが正しいか確認**
   ```bash
   ls -la /Users/takayakazuki/Desktop/IMG_2525.mp4
   ```

3. **修正スクリプトのログを確認**
   ```bash
   python3 fix_xml_immediate.py -v output/IMG_2525_edited.xml
   ```

これで必ず解決します！🎉