#!/bin/bash

echo "=== FFmpegインストールガイド ==="
echo

# Homebrewがインストールされているか確認
if command -v brew &> /dev/null; then
    echo "Homebrewが見つかりました。"
    echo "FFmpegをインストールします..."
    echo
    echo "実行するコマンド："
    echo "brew install ffmpeg"
    echo
    echo "上記コマンドをTerminalで実行してください。"
else
    echo "Homebrewがインストールされていません。"
    echo
    echo "1. まずHomebrewをインストール："
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo
    echo "2. その後FFmpegをインストール："
    echo "brew install ffmpeg"
fi

echo
echo "インストール後、convert_vfr_to_cfr.sh を実行してください。"