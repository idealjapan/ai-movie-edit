"""
高度な無音区間検出モジュール
より精度の高い無音検出アルゴリズムを実装
"""

import numpy as np
import librosa
from scipy import signal
from pydub import AudioSegment
import json
from pathlib import Path

class AdvancedSilenceDetector:
    """高度な無音区間検出クラス"""
    
    def __init__(self, 
                 min_silence_len=500,
                 silence_thresh=-40,
                 energy_threshold=0.02,
                 zero_crossing_threshold=0.1,
                 use_adaptive_threshold=True):
        """
        Args:
            min_silence_len: 最小無音長さ（ミリ秒）
            silence_thresh: 音量しきい値（dB）
            energy_threshold: エネルギーしきい値
            zero_crossing_threshold: ゼロ交差率しきい値
            use_adaptive_threshold: 適応的しきい値を使用するか
        """
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.energy_threshold = energy_threshold
        self.zero_crossing_threshold = zero_crossing_threshold
        self.use_adaptive_threshold = use_adaptive_threshold
    
    def detect_silence_multimethod(self, audio_path):
        """複数の手法を組み合わせた無音検出"""
        
        # 音声を読み込む
        y, sr = librosa.load(audio_path, sr=None)
        
        # 1. エネルギーベースの検出
        energy_silence = self._detect_by_energy(y, sr)
        
        # 2. スペクトラルセントロイドベースの検出
        spectral_silence = self._detect_by_spectral_centroid(y, sr)
        
        # 3. ゼロ交差率ベースの検出
        zcr_silence = self._detect_by_zero_crossing(y, sr)
        
        # 4. 複合的な判定（投票方式）
        combined_silence = self._combine_detections(
            energy_silence, spectral_silence, zcr_silence, len(y), sr
        )
        
        return combined_silence
    
    def _detect_by_energy(self, y, sr):
        """エネルギーベースの無音検出"""
        # フレームごとのRMSエネルギーを計算
        hop_length = int(sr * 0.01)  # 10ms
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # 適応的しきい値
        if self.use_adaptive_threshold:
            # 移動平均でベースラインを計算
            window_size = int(sr / hop_length)  # 1秒のウィンドウ
            baseline = signal.medfilt(rms, kernel_size=min(window_size, len(rms)))
            threshold = baseline * 2  # ベースラインの2倍をしきい値に
            threshold = np.maximum(threshold, self.energy_threshold)
        else:
            threshold = self.energy_threshold
        
        # 無音フレームを検出
        is_silent = rms < threshold
        
        return self._frames_to_segments(is_silent, sr, hop_length)
    
    def _detect_by_spectral_centroid(self, y, sr):
        """スペクトラルセントロイドベースの無音検出"""
        hop_length = int(sr * 0.01)
        
        # スペクトラルセントロイドを計算
        cent = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
        
        # 正規化
        if len(cent) > 0 and np.max(cent) > 0:
            cent_norm = cent / np.max(cent)
        else:
            cent_norm = cent
        
        # 低いセントロイド = 無音の可能性が高い
        is_silent = cent_norm < 0.1
        
        return self._frames_to_segments(is_silent, sr, hop_length)
    
    def _detect_by_zero_crossing(self, y, sr):
        """ゼロ交差率ベースの無音検出"""
        hop_length = int(sr * 0.01)
        
        # ゼロ交差率を計算
        zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]
        
        # 高いゼロ交差率 = ノイズの可能性
        # 低いゼロ交差率 = 無音または持続音
        is_silent = zcr < self.zero_crossing_threshold
        
        return self._frames_to_segments(is_silent, sr, hop_length)
    
    def _frames_to_segments(self, is_silent, sr, hop_length):
        """フレーム単位の無音判定をセグメントに変換"""
        segments = []
        silent_start = None
        min_frames = int(self.min_silence_len * sr / (1000 * hop_length))
        
        for i, silent in enumerate(is_silent):
            time = i * hop_length / sr
            
            if silent and silent_start is None:
                silent_start = time
            elif not silent and silent_start is not None:
                duration = time - silent_start
                if duration * 1000 >= self.min_silence_len:
                    segments.append((silent_start, time))
                silent_start = None
        
        # 最後が無音の場合
        if silent_start is not None:
            end_time = len(is_silent) * hop_length / sr
            duration = end_time - silent_start
            if duration * 1000 >= self.min_silence_len:
                segments.append((silent_start, end_time))
        
        return segments
    
    def _combine_detections(self, energy_seg, spectral_seg, zcr_seg, total_samples, sr):
        """複数の検出結果を組み合わせる"""
        duration = total_samples / sr
        resolution = 0.01  # 10ms resolution
        
        # タイムラインを作成
        timeline_points = int(duration / resolution)
        timeline = np.zeros((3, timeline_points))  # 3つの手法
        
        # 各手法の結果をタイムラインにマッピング
        for seg in energy_seg:
            start_idx = int(seg[0] / resolution)
            end_idx = int(seg[1] / resolution)
            timeline[0, start_idx:end_idx] = 1
        
        for seg in spectral_seg:
            start_idx = int(seg[0] / resolution)
            end_idx = int(seg[1] / resolution)
            timeline[1, start_idx:end_idx] = 1
        
        for seg in zcr_seg:
            start_idx = int(seg[0] / resolution)
            end_idx = int(seg[1] / resolution)
            timeline[2, start_idx:end_idx] = 1
        
        # 投票（2つ以上の手法が無音と判定）
        combined = np.sum(timeline, axis=0) >= 2
        
        # セグメントに変換
        segments = []
        silent_start = None
        
        for i, is_silent in enumerate(combined):
            time = i * resolution
            
            if is_silent and silent_start is None:
                silent_start = time
            elif not is_silent and silent_start is not None:
                if (time - silent_start) * 1000 >= self.min_silence_len:
                    segments.append((silent_start, time))
                silent_start = None
        
        if silent_start is not None:
            if (duration - silent_start) * 1000 >= self.min_silence_len:
                segments.append((silent_start, duration))
        
        return segments
    
    def analyze_and_optimize(self, audio_path):
        """音声を分析して最適なパラメータを提案"""
        y, sr = librosa.load(audio_path, sr=None)
        
        # 音声の統計情報を計算
        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # 統計値
        rms_mean = np.mean(rms)
        rms_std = np.std(rms)
        zcr_mean = np.mean(zcr)
        
        # パラメータの推奨値
        recommendations = {
            "energy_threshold": float(rms_mean - 2 * rms_std),
            "zero_crossing_threshold": float(zcr_mean),
            "suggested_silence_thresh": int(20 * np.log10(rms_mean) - 10),
            "audio_characteristics": {
                "average_energy": float(rms_mean),
                "energy_variance": float(rms_std),
                "average_zcr": float(zcr_mean),
                "is_noisy": zcr_mean > 0.1,
                "dynamic_range": float(np.max(rms) - np.min(rms))
            }
        }
        
        return recommendations