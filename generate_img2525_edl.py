#!/usr/bin/env python3
"""
IMG_2525.edlを生成
"""

import json
from utils.edl_generator_fixed import generate_fixed_edl

def main():
    # セグメントを読み込む
    with open('editor_segments.json', 'r') as f:
        segments = json.load(f)
    
    # ビデオパス
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # 出力パス - IMG_2525.edlとして保存
    output_path = '/Users/takayakazuki/Desktop/IMG_2525.edl'
    
    # メタデータ
    metadata = {
        'fps': 29.97,
        'width': 1920,
        'height': 1080
    }
    
    print("IMG_2525.edlを生成中...")
    print(f"セグメント数: {len(segments)}")
    
    # EDL生成
    edl_path = generate_fixed_edl(video_path, segments, output_path, metadata)
    
    print(f"\n✅ EDL生成完了: {edl_path}")
    print(f"Premiere Proでインポートして、{len(segments)}個のクリップとして編集できます！")

if __name__ == "__main__":
    main()