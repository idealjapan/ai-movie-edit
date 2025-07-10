#!/usr/bin/env python3
"""
1秒無音でカット - 動画編集者向けの効率的なEDL生成
"""

import json
from utils.silence_detector import SilenceDetector
from utils.edl_generator_fixed import generate_fixed_edl

def main():
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    print("動画編集者向け - 1秒無音カットEDL生成")
    print("="*50)
    print("設定:")
    print("  min_silence_len: 1000ms (1秒)")
    print("  silence_thresh: -40dB (標準)")
    print("  keep_silence: 200ms (自然な余白)")
    
    detector = SilenceDetector(
        min_silence_len=1000,  # 1秒の無音でカット
        silence_thresh=-40,    # 標準的な無音判定
        keep_silence=200       # 前後200ms残して自然に
    )
    
    # 無音検出を実行
    print("\n無音区間を検出中...")
    segments = detector.analyze_video(video_path, save_segments=False)
    
    # 短すぎるセグメント（0.5秒未満）を除外
    filtered_segments = []
    for start, end in segments:
        duration = end - start
        if duration >= 0.5:  # 0.5秒以上のセグメントのみ使用
            filtered_segments.append((start, end))
    
    # セグメント情報を整理
    segments_data = []
    for i, (start, end) in enumerate(filtered_segments):
        segments_data.append({
            "index": i,
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(end - start, 2)
        })
    
    # 結果を表示
    print(f"\n検出されたセグメント数: {len(segments_data)}")
    print(f"（元: {len(segments)}個 → フィルタ後: {len(segments_data)}個）")
    
    print("\nセグメント一覧:")
    total_duration = 0
    for i, seg in enumerate(segments_data):
        print(f"  {i+1:3d}. {seg['start']:7.2f}s - {seg['end']:7.2f}s ({seg['duration']:6.2f}s)")
        total_duration += seg['duration']
        
        # 30個ごとに区切り
        if (i + 1) % 30 == 0 and i < len(segments_data) - 1:
            print("  " + "-"*40)
    
    print(f"\n合計時間: {total_duration:.2f}秒 / 元動画: 746.68秒")
    print(f"カット率: {(1 - total_duration/746.68)*100:.1f}%削減")
    
    # セグメント情報を保存
    with open('editor_segments.json', 'w') as f:
        json.dump(segments_data, f, indent=2)
    
    # EDL生成
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_1sec_cut.edl'
    metadata = {
        'fps': 29.97,
        'width': 1920,
        'height': 1080
    }
    
    print("\nEDL生成中...")
    edl_path = generate_fixed_edl(video_path, segments_data, output_path, metadata)
    
    print(f"\n✅ 完了！")
    print(f"EDL: {output_path}")
    print(f"セグメント情報: editor_segments.json")
    print(f"\nPremiere Proでインポートして、{len(segments_data)}個のクリップとして編集できます！")

if __name__ == "__main__":
    main()