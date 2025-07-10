#!/usr/bin/env python3
"""
主要なセグメントのみを検出（5秒以上の無音で区切る）
"""

import json
from utils.silence_detector import SilenceDetector

def main():
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # より大きな無音区間で区切る設定
    print("主要セグメント検出を実行中...")
    print("設定:")
    print("  min_silence_len: 5000ms (5秒)")
    print("  silence_thresh: -35dB")
    print("  keep_silence: 500ms")
    
    detector = SilenceDetector(
        min_silence_len=5000,  # 5秒以上の無音のみ検出
        silence_thresh=-35,    # 感度を高めに
        keep_silence=500       # 前後に500ms残す
    )
    
    # 無音検出を実行
    segments = detector.analyze_video(video_path, save_segments=False)
    
    # セグメント情報を整理
    segments_data = []
    for i, (start, end) in enumerate(segments):
        segments_data.append({
            "index": i,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(end - start, 2)
        })
    
    # 結果を表示
    print(f"\n検出された主要セグメント数: {len(segments_data)}")
    print("\nセグメント詳細:")
    total_duration = 0
    for seg in segments_data:
        print(f"  セグメント{seg['index']+1}: {seg['start']}s - {seg['end']}s ({seg['duration']}s)")
        total_duration += seg['duration']
    
    print(f"\n音声がある総時間: {total_duration:.2f}秒")
    
    # ファイルに保存
    output_file = 'major_segments.json'
    with open(output_file, 'w') as f:
        json.dump(segments_data, f, indent=2)
    
    print(f"\nセグメント情報を {output_file} に保存しました")
    
    return segments_data

if __name__ == "__main__":
    main()