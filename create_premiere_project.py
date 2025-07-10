#!/usr/bin/env python3
"""
Premiere Proプロジェクトファイルを直接生成
メディアパスの問題を完全に解決
"""
import os
import sys
import json
import subprocess
from pathlib import Path

def create_premiere_project_script(video_path, segments_path, output_dir):
    """
    Adobe ExtendScript (JSX) を生成してPremiere Proを制御
    """
    video_path = Path(video_path).resolve()
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # セグメントデータを読み込み
    with open(segments_path, 'r') as f:
        segments = json.load(f)
    
    # JSXスクリプトを生成
    jsx_content = f"""
// Premiere Pro自動化スクリプト
// 新規プロジェクトを作成
app.newProject("{output_dir / 'auto_edit.prproj'}");
var project = app.project;

// ビデオをインポート
var videoPath = "{video_path}";
project.importFiles([videoPath]);

// インポートされたアイテムを取得
var projectItem = project.rootItem.children[0];

// 新規シーケンスを作成
var sequence = project.createNewSequence("Edited_Sequence", projectItem);

// ビデオトラックとオーディオトラックを取得
var videoTrack = sequence.videoTracks[0];
var audioTrack = sequence.audioTracks[0];

// セグメントごとにクリップを配置
var segments = {json.dumps(segments)};
var currentTime = 0;

for (var i = 0; i < segments.length; i++) {{
    var segment = segments[i];
    var inPoint = segment.start;
    var outPoint = segment.end;
    var duration = outPoint - inPoint;
    
    // サブクリップを作成してタイムラインに配置
    projectItem.setInPoint(inPoint, 4); // 4 = seconds
    projectItem.setOutPoint(outPoint, 4);
    
    // ビデオトラックに挿入
    videoTrack.insertClip(projectItem, currentTime);
    
    // オーディオトラックに挿入
    audioTrack.insertClip(projectItem, currentTime);
    
    currentTime += duration;
}}

// プロジェクトを保存
project.save();

alert("プロジェクトの作成が完了しました！");
"""
    
    # JSXファイルを保存
    jsx_path = output_dir / "create_project.jsx"
    with open(jsx_path, 'w', encoding='utf-8') as f:
        f.write(jsx_content)
    
    print(f"✅ Premiere Pro制御スクリプトを生成しました: {jsx_path}")
    print("\n📋 実行方法:")
    print("1. Premiere Proを起動")
    print("2. ファイル → スクリプト → 参照...")
    print(f"3. {jsx_path} を選択して実行")
    
    return jsx_path

def create_simple_solution(video_path, edl_path):
    """
    シンプルな解決策：バッチファイルを生成
    """
    video_path = Path(video_path).resolve()
    edl_path = Path(edl_path).resolve()
    
    # バッチコマンドを生成
    if sys.platform == "win32":
        batch_content = f"""@echo off
echo Premiere Proメディアリンク修正バッチ
echo ================================
echo.
echo 1. Premiere Proで {edl_path.name} をインポート
echo 2. オフラインメディアが表示されたら、このウィンドウに戻る
echo 3. 任意のキーを押すと、自動的にメディアがリンクされます
echo.
pause

REM メディアファイルを一時的にEDLと同じ場所にリンク
mklink "{edl_path.parent / video_path.name}" "{video_path}"

echo.
echo ✅ メディアリンクを作成しました！
echo Premiere Proに戻って、プロジェクトパネルで右クリック
echo → メディアをリンク → {video_path.name} を選択
pause
"""
        batch_path = edl_path.parent / "fix_media_link.bat"
    else:
        # macOS/Linux
        batch_content = f"""#!/bin/bash
echo "Premiere Proメディアリンク修正スクリプト"
echo "======================================="
echo ""
echo "1. Premiere Proで {edl_path.name} をインポート"
echo "2. オフラインメディアが表示されたら、このターミナルに戻る"
echo "3. Enterキーを押すと、自動的にメディアがリンクされます"
echo ""
read -p "続行するにはEnterキーを押してください..."

# メディアファイルを一時的にEDLと同じ場所にリンク
ln -sf "{video_path}" "{edl_path.parent / video_path.name}"

echo ""
echo "✅ メディアリンクを作成しました！"
echo "Premiere Proに戻って、プロジェクトパネルで右クリック"
echo "→ メディアをリンク → {video_path.name} を選択"
read -p "終了するにはEnterキーを押してください..."
"""
        batch_path = edl_path.parent / "fix_media_link.sh"
        
    with open(batch_path, 'w') as f:
        f.write(batch_content)
    
    if sys.platform != "win32":
        os.chmod(batch_path, 0o755)
    
    print(f"\n✅ メディアリンク修正スクリプトを生成しました: {batch_path}")
    print("\n実行方法:")
    print(f"1. {batch_path} をダブルクリック")
    print("2. 指示に従って操作")
    
    return batch_path

if __name__ == "__main__":
    # テスト実行
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python create_premiere_project.py <動画ファイル> <セグメントJSON>")
        print("  python create_premiere_project.py --simple <動画ファイル> <EDLファイル>")
        sys.exit(1)
    
    if sys.argv[1] == "--simple":
        create_simple_solution(sys.argv[2], sys.argv[3])
    else:
        create_premiere_project_script(sys.argv[1], sys.argv[2], "premiere_auto_project")