#!/bin/bash

echo "=== 可変フレームレート動画を固定フレームレートに変換 ==="
echo

INPUT="/Users/takayakazuki/Desktop/IMG_2525.mov"
OUTPUT="/Users/takayakazuki/Desktop/IMG_2525_cfr30.mov"

# ProRes形式で変換（Premiere Proとの互換性が高い）
echo "ProRes形式で変換中..."
ffmpeg -i "$INPUT" \
    -r 30 \
    -vsync cfr \
    -c:v prores_ks \
    -profile:v 2 \
    -c:a pcm_s16le \
    -ar 44100 \
    "$OUTPUT"

echo
echo "変換完了！"
echo "出力ファイル: $OUTPUT"
echo
echo "次の手順："
echo "1. Premiere Proで新規プロジェクトを作成（30fps）"
echo "2. 変換後の動画（IMG_2525_cfr30.mov）をインポート"
echo "3. AI動画カットツールで再度処理を実行"