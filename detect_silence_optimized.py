#!/usr/bin/env python3
"""
最適化された無音検出
"""

import json
from utils.silence_detector import SilenceDetector

def main():
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # 最適化されたパラメータ（長い無音のみを検出）
    print("最適化されたパラメータで無音検出を実行中...")
    print("設定:")
    print("  min_silence_len: 2000ms (2秒)")
    print("  silence_thresh: -38dB")
    print("  keep_silence: 300ms")
    
    detector = SilenceDetector(
        min_silence_len=2000,  # 2秒以上の無音のみ検出
        silence_thresh=-38,    # バランス型のしきい値
        keep_silence=300       # 前後に300ms残す
    )
    
    # 無音検出を実行
    segments = detector.analyze_video(video_path, save_segments=False)
    
    # セグメント情報を整理
    segments_data = []
    for i, (start, end) in enumerate(segments):
        segments_data.append({
            "index": i,
            "start": start,
            "end": end,
            "duration": end - start
        })
    
    # 結果を表示
    print(f"\n検出されたセグメント数: {len(segments_data)}")
    print("\nセグメント詳細:")
    total_duration = 0
    for seg in segments_data:
        print(f"  セグメント{seg['index']+1}: {seg['start']:.2f}s - {seg['end']:.2f}s ({seg['duration']:.2f}s)")
        total_duration += seg['duration']
    
    print(f"\n音声がある総時間: {total_duration:.2f}秒")
    
    # ファイルに保存
    output_file = 'optimized_segments.json'
    with open(output_file, 'w') as f:
        json.dump(segments_data, f, indent=2)
    
    print(f"\nセグメント情報を {output_file} に保存しました")
    
    return segments_data

if __name__ == "__main__":
    main()