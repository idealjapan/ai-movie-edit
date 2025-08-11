#!/usr/bin/env python3
"""
1秒無音でカット - マージン調整版
"""

import json
from utils.silence_detector import SilenceDetector
from utils.edl_generator_fixed import generate_fixed_edl

def main():
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    print("動画編集者向け - 1秒無音カットEDL生成（マージン調整版）")
    print("="*50)
    print("設定:")
    print("  min_silence_len: 1000ms (1秒)")
    print("  silence_thresh: -40dB (標準)")
    print("  keep_silence: 500ms (前後0.5秒の余裕)")
    
    detector = SilenceDetector(
        min_silence_len=1000,  # 1秒の無音でカット
        silence_thresh=-40,    # 標準的な無音判定
        keep_silence=500       # 前後500ms残して余裕を持たせる
    )
    
    # 無音検出を実行
    print("\n無音区間を検出中...")
    segments = detector.analyze_video(video_path, save_segments=False)
    
    # セグメントの前後にマージンを追加
    adjusted_segments = []
    margin = 0.3  # 追加のマージン（秒）
    
    for i, (start, end) in enumerate(segments):
        # 開始位置を早める（最小0）
        adj_start = max(0, start - margin)
        
        # 終了位置を遅らせる（次のセグメントと重ならないように）
        if i < len(segments) - 1:
            next_start = segments[i + 1][0]
            adj_end = min(end + margin, next_start - 0.1)
        else:
            adj_end = end + margin
        
        duration = adj_end - adj_start
        
        # 0.5秒以上のセグメントのみ使用
        if duration >= 0.5:
            adjusted_segments.append((adj_start, adj_end))
    
    # セグメント情報を整理
    segments_data = []
    for i, (start, end) in enumerate(adjusted_segments):
        segments_data.append({
            "index": i,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(end - start, 2)
        })
    
    # 結果を表示
    print(f"\n検出されたセグメント数: {len(segments_data)}")
    print(f"（元: {len(segments)}個 → 調整後: {len(segments_data)}個）")
    
    print("\nセグメント一覧（最初の10個）:")
    total_duration = 0
    for i, seg in enumerate(segments_data[:10]):
        print(f"  {i+1:3d}. {seg['start']:7.2f}s - {seg['end']:7.2f}s ({seg['duration']:6.2f}s)")
        total_duration += seg['duration']
    
    if len(segments_data) > 10:
        print(f"  ... 他 {len(segments_data)-10} セグメント")
        for seg in segments_data[10:]:
            total_duration += seg['duration']
    
    print(f"\n合計時間: {total_duration:.2f}秒")
    
    # セグメント情報を保存
    with open('editor_segments_margin.json', 'w') as f:
        json.dump(segments_data, f, indent=2)
    
    # EDL生成
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_margin.edl'
    metadata = {
        'fps': 29.97,
        'width': 1920,
        'height': 1080
    }
    
    print("\nEDL生成中...")
    edl_path = generate_fixed_edl(video_path, segments_data, output_path, metadata)
    
    print(f"\n✅ 完了！")
    print(f"EDL: {output_path}")
    print(f"セグメント情報: editor_segments_margin.json")
    print(f"\nマージン設定:")
    print(f"  - 無音検出時のマージン: 500ms")
    print(f"  - 追加のマージン: 300ms")
    print(f"  - 合計: 前後約800ms（0.8秒）の余裕")

if __name__ == "__main__":
    main()