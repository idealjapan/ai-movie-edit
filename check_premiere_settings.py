#!/usr/bin/env python3
"""
Premiere Proの設定確認とトラブルシューティング
"""

def print_troubleshooting():
    """トラブルシューティングガイドを表示"""
    
    print("=== Premiere Pro XML読み込みトラブルシューティング ===\n")
    
    print("1. プロジェクト設定の確認:")
    print("   - ファイル > プロジェクト設定 > 一般")
    print("   - タイムベース: 30.00 fps")
    print("   - 表示形式: タイムコード")
    print()
    
    print("2. 可能性のある原因:")
    print("   a) 可変フレームレート（VFR）の動画")
    print("   b) プロジェクト設定とXMLの設定が不一致")
    print("   c) ファイルパスの問題")
    print("   d) XML構造の問題")
    print()
    
    print("3. 解決策:")
    print("   a) 新規プロジェクトを作成して再試行")
    print("   b) 動画を直接インポートしてから編集")
    print("   c) 動画を固定フレームレートに変換")
    print()
    
    print("4. 動画変換コマンド（Terminal）:")
    print("   ffmpeg -i /Users/takayakazuki/Desktop/IMG_2525.mov \\")
    print("          -r 30 -vsync cfr \\")
    print("          -c:v prores_ks -profile:v 2 \\")
    print("          -c:a copy \\")
    print("          /Users/takayakazuki/Desktop/IMG_2525_cfr30.mov")
    print()
    
    print("5. 代替案:")
    print("   - EDL形式で書き出す")
    print("   - マーカーを使用する方法")
    print("   - 手動でカット編集")

def create_edl_format():
    """EDL形式のファイルを生成（代替案）"""
    
    edl_content = """TITLE: IMG_2525_edited

001  IMG_2525 V     C        00:00:00:00 00:00:10:10 00:00:00:00 00:00:10:10
002  IMG_2525 V     C        00:04:40:20 00:12:26:23 00:00:10:10 00:08:06:13
"""
    
    output_path = "/Users/takayakazuki/Downloads/IMG_2525.edl"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(edl_content)
    
    print(f"\nEDL形式も作成しました: {output_path}")
    print("ファイル > 読み込み から EDLファイルを選択してください。")

def main():
    print_troubleshooting()
    create_edl_format()

if __name__ == "__main__":
    main()