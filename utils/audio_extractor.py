"""
音声抽出モジュール：FFmpegを使用して動画から音声を抽出
"""
import os
import subprocess
import sys
from pathlib import Path

class AudioExtractor:
    def __init__(self):
        # デフォルト設定
        self.default_format = 'wav'
        self.default_codec = 'pcm_s16le'
        self.default_sample_rate = 16000
        self.default_channels = 1
        
    def extract_audio(self, video_path, output_dir="temp", 
                     audio_format=None, audio_codec=None, 
                     audio_sample_rate=None, audio_channels=None):
        """
        動画ファイルから音声を抽出
        
        Args:
            video_path (str): 動画ファイルのパス
            output_dir (str, optional): 出力ディレクトリ
            audio_format (str, optional): 音声フォーマット
            audio_codec (str, optional): 音声コーデック
            audio_sample_rate (int, optional): サンプルレート
            audio_channels (int, optional): チャンネル数
            
        Returns:
            str: 抽出した音声ファイルのパス
        """
        # デフォルト値の設定
        if audio_format is None:
            audio_format = self.default_format
        if audio_codec is None:
            audio_codec = self.default_codec
        if audio_sample_rate is None:
            audio_sample_rate = self.default_sample_rate
        if audio_channels is None:
            audio_channels = self.default_channels
            
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 入力ファイル名から拡張子を除いた名前を取得
        video_filename = Path(video_path).stem
        audio_filename = f"{video_filename}.{audio_format}"
        audio_path = os.path.join(output_dir, audio_filename)
        
        # FFmpegコマンドを構築
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # 映像を除外
            '-acodec', audio_codec,
            '-ar', str(audio_sample_rate),
            '-ac', str(audio_channels),
            '-y',  # 既存ファイルを上書き
            audio_path
        ]
        
        try:
            # FFmpegを実行
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"音声を抽出しました: {audio_path}")
            return audio_path
        except subprocess.CalledProcessError as e:
            print(f"音声抽出エラー: {e}", file=sys.stderr)
            raise
        except FileNotFoundError:
            print("エラー: FFmpegがインストールされていません。", file=sys.stderr)
            raise
