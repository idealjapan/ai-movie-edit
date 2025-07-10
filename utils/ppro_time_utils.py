"""
Premiere Pro時間計算ユーティリティ
pproTicksやタイムコードの計算を行う
"""
from typing import Tuple, Dict
import math


class PproTimeCalculator:
    """Premiere Pro固有の時間計算を行うクラス"""
    
    # Premiere Proの定数
    PPRO_TICKS_PER_SECOND = 282_432_000  # 1秒あたりのticks数
    
    def __init__(self, fps: float, is_ntsc: bool = False):
        """
        初期化
        
        Args:
            fps: フレームレート
            is_ntsc: NTSCフレームレートかどうか
        """
        self.fps = fps
        self.is_ntsc = is_ntsc
        self.timebase = self._get_timebase()
        self.ticks_per_frame = self.PPRO_TICKS_PER_SECOND / self.fps
        
    def _get_timebase(self) -> int:
        """タイムベースを取得"""
        if self.is_ntsc:
            # NTSC の場合、実際のfpsより1大きい整数値を使用
            if abs(self.fps - 23.976) < 0.01:
                return 24
            elif abs(self.fps - 29.97) < 0.01:
                return 30
            elif abs(self.fps - 59.94) < 0.01:
                return 60
            elif abs(self.fps - 119.88) < 0.01:
                return 120
        
        # 非NTSCまたは標準的でないフレームレート
        return round(self.fps)
    
    def seconds_to_ticks(self, seconds: float) -> int:
        """
        秒をpproTicksに変換
        
        Args:
            seconds: 秒数
            
        Returns:
            pproTicks値
        """
        return int(seconds * self.PPRO_TICKS_PER_SECOND)
    
    def ticks_to_seconds(self, ticks: int) -> float:
        """
        pproTicksを秒に変換
        
        Args:
            ticks: pproTicks値
            
        Returns:
            秒数
        """
        return ticks / self.PPRO_TICKS_PER_SECOND
    
    def frames_to_ticks(self, frames: int) -> int:
        """
        フレーム数をpproTicksに変換
        
        Args:
            frames: フレーム数
            
        Returns:
            pproTicks値
        """
        return int(frames * self.ticks_per_frame)
    
    def seconds_to_frames(self, seconds: float) -> int:
        """
        秒をフレーム数に変換
        
        Args:
            seconds: 秒数
            
        Returns:
            フレーム数
        """
        return int(seconds * self.fps)
    
    def frames_to_seconds(self, frames: int) -> float:
        """
        フレーム数を秒に変換
        
        Args:
            frames: フレーム数
            
        Returns:
            秒数
        """
        return frames / self.fps
    
    def seconds_to_timecode(self, seconds: float, drop_frame: bool = False) -> str:
        """
        秒をタイムコードに変換
        
        Args:
            seconds: 秒数
            drop_frame: ドロップフレームタイムコードを使用するか
            
        Returns:
            タイムコード文字列 (HH:MM:SS:FF)
        """
        total_frames = int(seconds * self.fps)
        
        if drop_frame and self.is_ntsc and abs(self.fps - 29.97) < 0.01:
            # 29.97fpsのドロップフレーム計算
            return self._calculate_drop_frame_timecode(total_frames)
        else:
            # 通常のタイムコード計算
            return self._calculate_non_drop_frame_timecode(total_frames)
    
    def _calculate_non_drop_frame_timecode(self, total_frames: int) -> str:
        """
        非ドロップフレームタイムコードを計算
        
        Args:
            total_frames: 総フレーム数
            
        Returns:
            タイムコード文字列
        """
        frames_per_second = self.timebase
        
        frames = total_frames % frames_per_second
        seconds = (total_frames // frames_per_second) % 60
        minutes = (total_frames // (frames_per_second * 60)) % 60
        hours = total_frames // (frames_per_second * 60 * 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    
    def _calculate_drop_frame_timecode(self, total_frames: int) -> str:
        """
        ドロップフレームタイムコードを計算（29.97fps用）
        
        Args:
            total_frames: 総フレーム数
            
        Returns:
            タイムコード文字列
        """
        # ドロップフレームの計算は複雑なので、簡略化
        # 実際の実装では、10分ごとに18フレーム、1分ごとに2フレームをドロップ
        drop_frames = 2  # 1分あたりのドロップフレーム数
        frames_per_10_minutes = 17982  # 10分あたりのフレーム数
        frames_per_minute = 1798  # 1分あたりのフレーム数（ドロップ後）
        
        # 10分単位の計算
        ten_minutes = total_frames // frames_per_10_minutes
        remaining = total_frames % frames_per_10_minutes
        
        # 1分単位の計算
        if remaining >= 1800:
            minutes = (remaining - 1800) // frames_per_minute + 1
            remaining = (remaining - 1800) % frames_per_minute
            if minutes > 0:
                remaining += 2  # ドロップしたフレームを追加
        else:
            minutes = 0
        
        # 最終的な時分秒フレームの計算
        total_minutes = ten_minutes * 10 + minutes
        hours = total_minutes // 60
        minutes = total_minutes % 60
        seconds = remaining // 30
        frames = remaining % 30
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d};{frames:02d}"  # セミコロンでドロップフレーム表示
    
    def get_sequence_settings(self) -> Dict:
        """
        シーケンス設定用の情報を取得
        
        Returns:
            シーケンス設定の辞書
        """
        return {
            'timebase': self.timebase,
            'ntsc': str(self.is_ntsc).upper(),
            'fps': self.fps,
            'ppro_ticks_per_frame': int(self.ticks_per_frame),
            'ppro_ticks_per_second': self.PPRO_TICKS_PER_SECOND
        }


# ユーティリティ関数
def create_calculator_from_metadata(metadata: Dict) -> PproTimeCalculator:
    """
    メタデータからCalculatorインスタンスを作成
    
    Args:
        metadata: VideoMetadataExtractorの出力
        
    Returns:
        PproTimeCalculatorインスタンス
    """
    return PproTimeCalculator(
        fps=metadata['fps'],
        is_ntsc=metadata['is_ntsc']
    )