#!/bin/bash
# 可変フレームレート動画を固定フレームレート30fpsに変換

echo "可変フレームレート動画を固定フレームレート30fpsに変換します..."

# 入力と出力ファイル
INPUT="/Users/takayakazuki/Desktop/IMG_2525.mov"
OUTPUT="/Users/takayakazuki/Desktop/IMG_2525_cfr30.mov"

# FFmpegで変換（30fps固定）
ffmpeg -i "$INPUT" \
  -r 30 \
  -c:v libx264 \
  -preset medium \
  -crf 18 \
  -c:a copy \
  -pix_fmt yuv420p \
  -movflags +faststart \
  "$OUTPUT"

echo "変換完了: $OUTPUT"
echo "この動画は固定30fpsなので、Premiere Proで問題なく読み込めるはずです。"