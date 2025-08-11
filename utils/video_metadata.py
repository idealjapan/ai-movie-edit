"""
動画メタデータ取得モジュール
FFmpegを使用して動画の詳細情報を取得
"""
import json
import subprocess
import os
from typing import Dict, Tuple, Optional
import re


class VideoMetadataExtractor:
    """動画のメタデータを取得するクラス"""
    
    def __init__(self):
        self.ffprobe_path = "ffprobe"  # ffprobeのパス
        
    def extract_metadata(self, video_path: str) -> Dict:
        """
        動画ファイルからメタデータを抽出
        
        Args:
            video_path: 動画ファイルのパス
            
        Returns:
            メタデータの辞書
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"動画ファイルが見つかりません: {video_path}")
            
        try:
            # ffprobeコマンドを実行
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            metadata = json.loads(result.stdout)
            
            # 解析したメタデータを整形
            return self._parse_metadata(metadata)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffprobeの実行に失敗しました: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"メタデータの解析に失敗しました: {e}")
    
    def _parse_metadata(self, raw_metadata: Dict) -> Dict:
        """
        生のメタデータを解析して必要な情報を抽出
        
        Args:
            raw_metadata: ffprobeの出力
            
        Returns:
            整形されたメタデータ
        """
        video_stream = None
        audio_stream = None
        
        # ビデオとオーディオストリームを探す
        for stream in raw_metadata.get('streams', []):
            if stream['codec_type'] == 'video' and video_stream is None:
                video_stream = stream
            elif stream['codec_type'] == 'audio' and audio_stream is None:
                audio_stream = stream
                
        if not video_stream:
            raise ValueError("ビデオストリームが見つかりません")
            
        # フレームレート情報を取得
        # avg_frame_rateを優先的に使用（より正確なため）
        avg_fps = video_stream.get('avg_frame_rate', video_stream.get('r_frame_rate', '30/1'))
        fps_info = self._parse_frame_rate(avg_fps)
        
        # 継続時間を取得
        duration = float(raw_metadata.get('format', {}).get('duration', 0))
        
        # NTSCフラグを判定
        is_ntsc = self._is_ntsc_frame_rate(fps_info['fps'])
        
        return {
            'duration': duration,
            'width': int(video_stream.get('width', 1920)),
            'height': int(video_stream.get('height', 1080)),
            'fps': fps_info['fps'],
            'fps_numerator': fps_info['numerator'],
            'fps_denominator': fps_info['denominator'],
            'timebase': fps_info['timebase'],
            'is_ntsc': is_ntsc,
            'codec': video_stream.get('codec_name', 'unknown'),
            'format': raw_metadata.get('format', {}).get('format_name', 'unknown'),
            'audio_sample_rate': int(audio_stream.get('sample_rate', 48000)) if audio_stream else 48000,
            'audio_channels': int(audio_stream.get('channels', 2)) if audio_stream else 2,
            'file_path': raw_metadata.get('format', {}).get('filename', ''),
            'file_size': int(raw_metadata.get('format', {}).get('size', 0))
        }
    
    def _parse_frame_rate(self, fps_string: str) -> Dict:
        """
        フレームレート文字列を解析
        
        Args:
            fps_string: "30000/1001" のような形式の文字列
            
        Returns:
            フレームレート情報の辞書
        """
        try:
            if '/' in fps_string:
                num, den = map(int, fps_string.split('/'))
                fps = num / den
            else:
                fps = float(fps_string)
                num, den = fps, 1
                
            # タイムベースを決定
            timebase = round(fps)
            
            return {
                'fps': fps,
                'numerator': num,
                'denominator': den,
                'timebase': timebase
            }
        except:
            # デフォルト値
            return {
                'fps': 30.0,
                'numerator': 30,
                'denominator': 1,
                'timebase': 30
            }
    
    def _is_ntsc_frame_rate(self, fps: float) -> bool:
        """
        NTSCフレームレートかどうかを判定
        
        Args:
            fps: フレームレート
            
        Returns:
            NTSCの場合True
        """
        ntsc_rates = [
            23.976,  # 24000/1001
            29.97,   # 30000/1001
            59.94,   # 60000/1001
            119.88   # 120000/1001
        ]
        
        # 0.1の誤差を許容（30.004fpsのような値にも対応）
        for rate in ntsc_rates:
            if abs(fps - rate) < 0.1:
                return True
                
        # 30.0fpsに近い値も29.97fpsとして扱う
        if 29.9 < fps < 30.1 and fps != 30.0:
            return True
            
        return False
    
    def get_frame_count(self, video_path: str) -> int:
        """
        動画の総フレーム数を取得
        
        Args:
            video_path: 動画ファイルのパス
            
        Returns:
            総フレーム数
        """
        metadata = self.extract_metadata(video_path)
        return int(metadata['duration'] * metadata['fps'])


# テスト用
if __name__ == "__main__":
    extractor = VideoMetadataExtractor()
    # テスト実行用のコード