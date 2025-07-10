#!/usr/bin/env python3
"""
短い無音も検出してEDLを生成（YouTubeショート向け）
"""

import json
from utils.silence_detector import SilenceDetector
from utils.edl_generator_fixed import generate_fixed_edl

def main():
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # 短い無音も検出する設定
    print("短い無音検出モードでEDLを生成中...")
    print("設定:")
    print("  min_silence_len: 1000ms (1秒)")
    print("  silence_thresh: -35dB")
    print("  keep_silence: 100ms")
    
    detector = SilenceDetector(
        min_silence_len=1000,  # 1秒以上の無音を検出
        silence_thresh=-35,    # 標準的なしきい値
        keep_silence=100       # 前後100ms残す（タイトに）
    )
    
    # 既存の音声ファイルを使用
    audio_path = '/Users/takayakazuki/Desktop/IMG_2525.wav'
    
    # 無音でない区間を取得
    segments = detector.get_non_silent_segments(audio_path, total_duration=746.68)
    
    # 最初の20セグメントのみ使用（多すぎる場合）
    if len(segments) > 20:
        print(f"\nセグメント数が多い（{len(segments)}個）ため、最初の20個を使用します")
        segments = segments[:20]
    
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
    print(f"\n検出されたセグメント数: {len(segments_data)}")
    print("\nセグメント詳細:")
    total_duration = 0
    for seg in segments_data[:10]:  # 最初の10個を表示
        print(f"  セグメント{seg['index']+1}: {seg['start']}s - {seg['end']}s ({seg['duration']}s)")
        total_duration += seg['duration']
    
    if len(segments_data) > 10:
        print(f"  ... 他 {len(segments_data)-10} セグメント")
        for seg in segments_data[10:]:
            total_duration += seg['duration']
    
    print(f"\n音声がある総時間: {total_duration:.2f}秒")
    
    # EDL生成
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_short_silence.edl'
    metadata = {
        'fps': 29.97,
        'width': 1920,
        'height': 1080
    }
    
    edl_path = generate_fixed_edl(video_path, segments_data, output_path, metadata)
    print(f"\nEDL生成完了: {edl_path}")

if __name__ == "__main__":
    main()