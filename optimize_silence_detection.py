#!/usr/bin/env python3
"""
無音検出パラメータの最適化スクリプト
動画の特性を分析して最適なパラメータを見つける
"""

import sys
import json
from pathlib import Path
from utils.silence_detector import SilenceDetector
from utils.silence_detector_advanced import AdvancedSilenceDetector
from pydub import AudioSegment
import numpy as np

def analyze_audio_characteristics(audio_path):
    """音声ファイルの特性を分析"""
    print("音声特性を分析中...")
    
    try:
        # 音声を読み込む
        audio = AudioSegment.from_file(audio_path)
        
        # dBFSで音量レベルを取得
        loudness = audio.dBFS
        max_loudness = audio.max_dBFS
        
        # 音声のダイナミックレンジを計算
        samples = np.array(audio.get_array_of_samples())
        if audio.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        
        # 統計値
        rms = np.sqrt(np.mean(samples**2))
        peak = np.max(np.abs(samples))
        
        print(f"\n音声特性:")
        print(f"  平均音量: {loudness:.1f} dBFS")
        print(f"  最大音量: {max_loudness:.1f} dBFS") 
        print(f"  RMS: {rms:.4f}")
        print(f"  ピーク: {peak}")
        print(f"  長さ: {len(audio)/1000:.1f}秒")
        
        # 推奨パラメータ
        recommended_thresh = int(loudness - 15)  # 平均より15dB低い
        
        return {
            "loudness": loudness,
            "max_loudness": max_loudness,
            "recommended_threshold": recommended_thresh,
            "duration": len(audio) / 1000
        }
        
    except Exception as e:
        print(f"音声分析エラー: {e}")
        return None

def find_optimal_parameters(video_path):
    """最適なパラメータを見つける"""
    
    # まず音声を抽出
    detector = SilenceDetector()
    audio_path = detector.extract_audio_from_video(video_path)
    
    # 音声特性を分析
    audio_info = analyze_audio_characteristics(audio_path)
    
    if audio_info:
        base_threshold = audio_info["recommended_threshold"]
    else:
        base_threshold = -40
    
    # グリッドサーチでパラメータを探索
    print("\n最適なパラメータを探索中...")
    
    # テストパラメータ
    silence_lengths = [300, 500, 700, 1000]
    thresholds = [base_threshold + offset for offset in [-5, 0, 5, 10]]
    
    best_config = None
    best_score = -1
    
    for min_silence in silence_lengths:
        for thresh in thresholds:
            detector = SilenceDetector(
                min_silence_len=min_silence,
                silence_thresh=thresh,
                keep_silence=200
            )
            
            segments = detector.analyze_video(video_path, save_segments=False)
            
            # スコアを計算（セグメント数と総時間のバランス）
            if segments:
                total_duration = sum(end - start for start, end in segments)
                segment_count = len(segments)
                
                # 理想的なセグメント数は5-15
                if 5 <= segment_count <= 15:
                    count_score = 1.0
                elif segment_count < 5:
                    count_score = segment_count / 5.0
                else:
                    count_score = max(0, 1.0 - (segment_count - 15) / 20.0)
                
                # 総時間の割合（音声がある部分の割合）
                if audio_info:
                    duration_ratio = total_duration / audio_info["duration"]
                else:
                    duration_ratio = 0.7  # デフォルト
                
                # 総合スコア
                score = count_score * 0.6 + min(duration_ratio, 1.0) * 0.4
                
                if score > best_score:
                    best_score = score
                    best_config = {
                        "min_silence_len": min_silence,
                        "silence_thresh": thresh,
                        "segment_count": segment_count,
                        "total_duration": total_duration,
                        "score": score
                    }
    
    # 高度な検出も試す
    print("\n高度な検出アルゴリズムをテスト中...")
    advanced_detector = AdvancedSilenceDetector()
    recommendations = advanced_detector.analyze_and_optimize(audio_path)
    
    # 結果を表示
    print("\n" + "="*60)
    print("最適化結果")
    print("="*60)
    
    if best_config:
        print(f"\n推奨設定（標準アルゴリズム）:")
        print(f"  min_silence_len: {best_config['min_silence_len']}ms")
        print(f"  silence_thresh: {best_config['silence_thresh']}dB")
        print(f"  検出セグメント数: {best_config['segment_count']}")
        print(f"  音声総時間: {best_config['total_duration']:.1f}秒")
        print(f"  スコア: {best_config['score']:.2f}")
    
    print(f"\n高度なアルゴリズムの推奨値:")
    print(f"  エネルギーしきい値: {recommendations['energy_threshold']:.4f}")
    print(f"  ゼロ交差率しきい値: {recommendations['zero_crossing_threshold']:.4f}")
    print(f"  推奨silence_thresh: {recommendations['suggested_silence_thresh']}dB")
    
    if recommendations['audio_characteristics']['is_noisy']:
        print("  ⚠️ ノイズが多い音声です。しきい値を高めに設定することを推奨します。")
    
    # 結果を保存
    output_file = "optimized_silence_params.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "standard_algorithm": best_config,
            "advanced_algorithm": recommendations,
            "audio_info": audio_info
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n最適化結果を {output_file} に保存しました")
    
    return best_config

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python optimize_silence_detection.py <動画ファイルパス>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    find_optimal_parameters(video_path)