#!/usr/bin/env python3
"""
XMLファイルのパスを修正するユーティリティ
Premiere Proで読み込めるように、XMLファイル内のファイルパスを修正します
"""
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import urllib.parse


def fix_xml_paths(xml_path: str, media_folder: str = None) -> str:
    """
    XMLファイル内のメディアパスを修正
    
    Args:
        xml_path: 修正するXMLファイルのパス
        media_folder: メディアファイルがあるフォルダ（指定しない場合はXMLと同じフォルダ）
    
    Returns:
        修正されたXMLファイルのパス
    """
    # XMLファイルを読み込む
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # メディアフォルダを決定
    if media_folder is None:
        media_folder = os.path.dirname(xml_path)
    
    # すべてのpathurl要素を探して修正
    modified = False
    for pathurl in root.iter('pathurl'):
        if pathurl.text:
            # 現在のパスを解析
            current_path = pathurl.text
            
            # file://localhost/ を除去してファイル名を取得
            if current_path.startswith('file://localhost/'):
                file_path = current_path[17:]  # "file://localhost/" の長さ
            elif current_path.startswith('file://localhost'):
                file_path = current_path[16:]  # "file://localhost" の長さ
            else:
                continue
            
            # URLデコード
            file_path = urllib.parse.unquote(file_path)
            
            # ファイル名だけを取得
            filename = os.path.basename(file_path)
            
            # 新しいパスを構築
            new_path = os.path.join(media_folder, filename)
            
            # ファイルが存在するか確認
            if os.path.exists(new_path):
                # 新しいURLを作成
                abs_path = os.path.abspath(new_path)
                if os.name == 'nt':
                    # Windows
                    url_path = abs_path.replace('\\', '/')
                    new_url = f"file://localhost/{url_path}"
                else:
                    # macOS/Linux - 日本語パスをエンコードしない
                    new_url = f"file://localhost{abs_path}"
                
                pathurl.text = new_url
                modified = True
                print(f"パスを修正: {filename}")
            else:
                print(f"警告: ファイルが見つかりません: {new_path}")
    
    if modified:
        # 修正したXMLを保存
        output_path = xml_path.replace('.xml', '_fixed.xml')
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"\n修正されたXMLを保存しました: {output_path}")
        return output_path
    else:
        print("修正が必要なパスはありませんでした。")
        return xml_path


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法: python xml_path_fixer.py <XMLファイル> [メディアフォルダ]")
        print("例: python xml_path_fixer.py output/edited.xml /path/to/media")
        sys.exit(1)
    
    xml_path = sys.argv[1]
    media_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(xml_path):
        print(f"エラー: XMLファイルが見つかりません: {xml_path}")
        sys.exit(1)
    
    fix_xml_paths(xml_path, media_folder)


if __name__ == "__main__":
    main()