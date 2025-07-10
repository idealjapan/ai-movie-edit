#!/usr/bin/env python3
"""
最終的なEDLを生成（改善された無音検出結果を使用）
"""

import json
from utils.edl_generator_fixed import generate_fixed_edl

def main():
    # セグメントを読み込む
    with open('final_segments.json', 'r') as f:
        segments = json.load(f)
    
    # ビデオパス
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # 出力パス
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_final.edl'
    
    # メタデータ
    metadata = {
        'fps': 29.97,
        'width': 1920,
        'height': 1080
    }
    
    print("最終的なEDLを生成中...")
    print(f"セグメント数: {len(segments)}")
    print("\nセグメント詳細:")
    for seg in segments:
        print(f"  セグメント{seg['index']+1}: {seg['start']}s - {seg['end']}s ({seg['duration']}s)")
    
    # EDL生成
    edl_path = generate_fixed_edl(video_path, segments, output_path, metadata)
    
    print(f"\nEDL生成完了: {edl_path}")
    
    # EDLプレビュー
    print("\nEDLプレビュー:")
    with open(output_path, 'r') as f:
        lines = f.readlines()
        for line in lines[:30]:
            print(line.rstrip())
        if len(lines) > 30:
            print("...")

if __name__ == "__main__":
    main()