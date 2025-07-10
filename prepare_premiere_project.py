#!/usr/bin/env python3
"""
Premiere Pro用プロジェクト準備スクリプト
EDLと動画ファイルを同じフォルダにコピーして、インポート手順を表示
"""
import os
import shutil
import sys
from pathlib import Path

def prepare_premiere_project(video_path, edl_path, output_dir=None):
    """
    Premiere Proプロジェクト用にファイルを準備
    """
    video_path = Path(video_path)
    edl_path = Path(edl_path)
    
    # 出力ディレクトリの設定
    if output_dir is None:
        output_dir = video_path.parent / f"{video_path.stem}_premiere_project"
    else:
        output_dir = Path(output_dir)
    
    # ディレクトリ作成
    output_dir.mkdir(exist_ok=True)
    
    # ファイルをコピー
    print(f"プロジェクトフォルダを作成中: {output_dir}")
    
    # 動画ファイルをコピー
    video_dest = output_dir / video_path.name
    if not video_dest.exists():
        print(f"動画ファイルをコピー中: {video_path.name}")
        shutil.copy2(video_path, video_dest)
    
    # EDLファイルをコピー
    edl_dest = output_dir / edl_path.name
    print(f"EDLファイルをコピー中: {edl_path.name}")
    shutil.copy2(edl_path, edl_dest)
    
    # インストラクションファイルを作成
    instructions = f"""
Premiere Proインポート手順
========================

1. Premiere Proを起動
2. 新規プロジェクトを作成
3. プロジェクトファイル(.prproj)をこのフォルダに保存:
   {output_dir}

4. メディアのインポート:
   a) プロジェクトパネルに以下のファイルをドラッグ＆ドロップ:
      - {video_path.name}
   
   b) メディアがプロジェクトに表示されたことを確認

5. EDLのインポート:
   a) ファイル → 読み込み → EDL...
   b) {edl_path.name} を選択
   c) 以下の設定でインポート:
      - 新規シーケンス名: {video_path.stem}_edited
      - ビデオトラック: V1
      - オーディオトラック: A1-A2

6. メディアが自動的にリンクされます！

トラブルシューティング:
- それでもオフラインの場合は、プロジェクトパネルで
  右クリック → メディアをリンク → {video_path.name}を選択
"""
    
    instructions_path = output_dir / "README_PREMIERE.txt"
    with open(instructions_path, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"\n✅ プロジェクトフォルダの準備完了！")
    print(f"📁 場所: {output_dir}")
    print(f"\n📋 手順は以下のファイルを参照:")
    print(f"   {instructions_path}")
    
    # Finderで開く（macOS）
    if sys.platform == "darwin":
        os.system(f"open '{output_dir}'")
    
    return output_dir

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python prepare_premiere_project.py <動画ファイル> <EDLファイル> [出力フォルダ]")
        sys.exit(1)
    
    video_file = sys.argv[1]
    edl_file = sys.argv[2]
    output_folder = sys.argv[3] if len(sys.argv) > 3 else None
    
    prepare_premiere_project(video_file, edl_file, output_folder)