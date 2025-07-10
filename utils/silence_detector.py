"""
無音区間検出モジュール：動画・音声ファイルから無音区間を特定し、音声がある区間のリストを作成
"""
import os
import numpy as np
import json
from pathlib import Path
import subprocess
import tempfile
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import detect_silence

class SilenceDetector:
    """無音区間検出クラス"""
    
    def __init__(self, min_silence_len=500, silence_thresh=-40, keep_silence=100):
        """
        Args:
            min_silence_len (int): 無音と判定する最小の長さ（ミリ秒）
            silence_thresh (int): 無音と判定する音量のしきい値（dB）
            keep_silence (int): 無音区間の前後に残す無音の長さ（ミリ秒）
        """
        self.min_silence_len = min_silence_len
        self.silence_thresh = silence_thresh
        self.keep_silence = keep_silence
    
    def extract_audio_from_video(self, video_path):
        """動画ファイルから音声を抽出"""
        # 音声ファイルの場合はそのまま使用
        if video_path.lower().endswith(('.wav', '.mp3', '.aac', '.m4a')):
            print(f"音声ファイルを直接使用します: {video_path}")
            # MP3の場合はwavに変換
            if video_path.lower().endswith('.mp3'):
                try:
                    wav_path = os.path.splitext(video_path)[0] + ".wav"
                    if os.path.exists(wav_path):
                        print(f"既存のWAVファイルを使用します: {wav_path}")
                        return wav_path
                    
                    print(f"MP3ファイルをWAVに変換中: {video_path}")
                    # ffmpegを使用して直接変換
                    cmd = [
                        "ffmpeg", "-i", video_path, 
                        "-acodec", "pcm_s16le", 
                        "-ar", "44100", "-ac", "2", 
                        wav_path, "-y"
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    print(f"変換完了: {wav_path}")
                    return wav_path
                except Exception as e:
                    print(f"MP3変換エラー: {e}")
                    print("librosaを使用して直接処理します")
                    return video_path
            return video_path
        
        # 動画ファイルの場合は音声を抽出
        audio_path = os.path.splitext(video_path)[0] + ".wav"
        
        # すでに音声ファイルが存在する場合はスキップ
        if os.path.exists(audio_path):
            print(f"音声ファイルが既に存在します: {audio_path}")
            return audio_path
        
        # FFmpegで音声抽出
        try:
            print(f"動画から音声を抽出中: {video_path}")
            
            # 一時ディレクトリを確保
            temp_dir = os.path.dirname(audio_path)
            if not os.path.exists(temp_dir) and temp_dir:
                os.makedirs(temp_dir, exist_ok=True)
            
            # ffmpegを使用して音声抽出（オプションを変更）
            cmd = [
                "ffmpeg", "-i", video_path, 
                "-vn", "-acodec", "pcm_s16le", 
                "-ar", "44100", "-ac", "2", 
                "-f", "wav",  # 明示的にフォーマット指定
                audio_path, "-y"
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # エラーが発生したかチェック
            if result.returncode != 0:
                print(f"FFmpeg警告: {result.stderr}")
                # エラーが発生しても続行する場合があるため、ファイルの存在をチェック
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    print(f"エラーが発生しましたが、音声ファイルは生成されています: {audio_path}")
                    return audio_path
                
                # ffmpeg-pythonを使用した代替方法を試みる
                print("代替方法を試みます...")
                import ffmpeg
                try:
                    # ffmpeg-pythonを使用した音声抽出
                    stream = ffmpeg.input(video_path)
                    stream = ffmpeg.output(stream.audio, audio_path, acodec='pcm_s16le', ar=44100, ac=2)
                    ffmpeg.run(stream, overwrite_output=True)
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        print(f"代替方法で音声抽出に成功しました: {audio_path}")
                        return audio_path
                except Exception as e:
                    print(f"代替方法でもエラー: {e}")
                    
                    # 直接librosaで処理するために元のファイルを返す
                    print("librosaを使用して元の動画ファイルを直接処理します")
                    return video_path
            
            print(f"音声抽出完了: {audio_path}")
            return audio_path
            
        except Exception as e:
            print(f"音声抽出エラー: {e}")
            
            # エラーが発生した場合、元のファイルを返す
            print("エラーが発生したため、元のファイルを直接処理します")
            return video_path
    
    def detect_silent_segments(self, audio_path):
        """音声ファイルから無音区間を検出"""
        print(f"無音区間を検出中: {audio_path}")
        
        # 音声ファイルを読み込み
        try:
            audio = AudioSegment.from_file(audio_path)
            
            # ノーマライズを実行して小さい音も検出しやすくする
            audio = audio.normalize()
            
            print(f"音声ファイル情報: 長さ={len(audio)/1000:.2f}秒, チャンネル数={audio.channels}, サンプルレート={audio.frame_rate}Hz")
            print(f"検出パラメータ: min_silence_len={self.min_silence_len}ms, silence_thresh={self.silence_thresh}dB")
            
            # 無音区間の検出（戻り値は [start, end] のミリ秒単位のリスト）
            silent_segments = detect_silence(
                audio, 
                min_silence_len=self.min_silence_len, 
                silence_thresh=self.silence_thresh,
                seek_step=1
            )
            
            # ミリ秒から秒に変換
            silent_segments_sec = [(start/1000, end/1000) for start, end in silent_segments]
            
            print(f"検出された無音区間: {len(silent_segments_sec)}個")
            # 詳細な情報を表示
            if silent_segments_sec:
                for i, (start, end) in enumerate(silent_segments_sec[:5]):  # 最初の5つだけ表示
                    print(f"  無音区間 {i+1}: {start:.2f}秒 - {end:.2f}秒 (長さ: {end-start:.2f}秒)")
                if len(silent_segments_sec) > 5:
                    print(f"  ... 他 {len(silent_segments_sec)-5} 個の無音区間")
            
            return silent_segments_sec
            
        except Exception as e:
            print(f"pydubでの無音区間検出中にエラーが発生しました: {e}")
            print("代替処理を試みます...")
            
            # 代替処理：ffmpeg-pythonを使用したり、librosaで読み込んでsilent_segmentsを取得
            try:
                # librosaを使用して音声を読み込む
                y, sr = librosa.load(audio_path, sr=None)
                
                # 音量の計算（dB単位）
                db = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
                
                # 各フレームの平均音量を計算
                mean_db = np.mean(db, axis=0)
                
                # 無音区間の判定（self.silence_threshより小さい音量の区間）
                is_silent = mean_db < self.silence_thresh
                
                # 無音区間を連続フレームとしてグループ化
                silent_segments_sec = []
                silent_start = None
                
                for i, silent in enumerate(is_silent):
                    frame_time = librosa.frames_to_time(i, sr=sr)
                    
                    if silent and silent_start is None:
                        silent_start = frame_time
                    elif not silent and silent_start is not None:
                        if (frame_time - silent_start) * 1000 >= self.min_silence_len:
                            silent_segments_sec.append((silent_start, frame_time))
                        silent_start = None
                
                # 最後が無音で終わる場合
                if silent_start is not None:
                    end_time = librosa.frames_to_time(len(is_silent), sr=sr)
                    if (end_time - silent_start) * 1000 >= self.min_silence_len:
                        silent_segments_sec.append((silent_start, end_time))
                
                print(f"librosaによる検出: {len(silent_segments_sec)}個の無音区間")
                return silent_segments_sec
                
            except Exception as e2:
                print(f"代替処理でもエラーが発生しました: {e2}")
                print("動画全体を1つの区間として処理します。")
                # エラーが発生した場合は空のリストを返す
                return []
    
    def get_non_silent_segments(self, audio_path, total_duration=None):
        """無音でない区間（音声がある区間）を取得"""
        # 無音区間を検出
        silent_segments = self.detect_silent_segments(audio_path)
        
        # 総再生時間が指定されていない場合は音声ファイルから取得
        if total_duration is None:
            audio = AudioSegment.from_file(audio_path)
            total_duration = len(audio) / 1000  # ミリ秒から秒に変換
        
        # 音声がある区間を計算
        non_silent_segments = []
        if not silent_segments:
            # 無音区間がない場合や全体が無音の場合
            if total_duration > 0:
                print("無音区間が検出されませんでした。全体を1つの区間として処理します。")
                non_silent_segments = [(0, total_duration)]
            else:
                print("有効な音声区間が見つかりませんでした。")
        else:
            # 無音区間が全体をカバーしているかチェック
            if len(silent_segments) == 1 and silent_segments[0][0] <= 0.1 and silent_segments[0][1] >= total_duration - 0.1:
                print("動画全体が無音として検出されました。全体を1つの区間として処理します。")
                non_silent_segments = [(0, total_duration)]
            else:
                # 無音区間の間の音声区間を抽出
                last_end = 0
                
                for start, end in silent_segments:
                    # 無音区間の前に音声区間がある場合
                    if start > last_end:
                        non_silent_segments.append((last_end, start))
                    last_end = end
                
                # 最後の無音区間の後に音声区間がある場合
                if last_end < total_duration:
                    non_silent_segments.append((last_end, total_duration))
        
        # 結果が空の場合は全体を使用
        if not non_silent_segments:
            print("有効な音声区間が見つからなかったため、全体を1つの区間として使用します。")
            non_silent_segments = [(0, total_duration)]
            
        print(f"抽出された音声区間: {len(non_silent_segments)}個")
        return non_silent_segments
    
    def analyze_video(self, video_path, output_dir="temp", save_segments=True):
        """動画ファイルの無音区間を分析し、音声がある区間を返す"""
        # 出力ディレクトリの作成
        os.makedirs(output_dir, exist_ok=True)
        
        # 動画から音声を抽出
        audio_path = self.extract_audio_from_video(video_path)
        
        # 総再生時間を取得
        total_duration = None
        # 音声ファイルからの読み込み試行
        try:
            try:
                audio = AudioSegment.from_file(audio_path)
                total_duration = len(audio) / 1000  # ミリ秒から秒に変換
                print(f"総再生時間: {total_duration:.2f}秒")
            except Exception as e:
                print(f"AudioSegmentでの読み込みに失敗: {e}")
                
                # librasaを使った代替法
                try:
                    y, sr = librosa.load(audio_path, sr=None)
                    total_duration = librosa.get_duration(y=y, sr=sr)
                    print(f"librosaによる総再生時間: {total_duration:.2f}秒")
                except Exception as e:
                    print(f"librosaでの読み込みにも失敗: {e}")
                    
                    # ffprobeを使用した代替法
                    try:
                        import ffmpeg
                        probe = ffmpeg.probe(video_path)
                        # 動画または音声ストリームの長さを取得
                        audio_stream = next((stream for stream in probe['streams'] 
                                            if stream['codec_type'] == 'audio'), None)
                        if audio_stream and 'duration' in audio_stream:
                            total_duration = float(audio_stream['duration'])
                        else:
                            # 動画の長さを使用
                            video_stream = next((stream for stream in probe['streams'] 
                                                if stream['codec_type'] == 'video'), None)
                            if video_stream and 'duration' in video_stream:
                                total_duration = float(video_stream['duration'])
                            else:
                                # 全体の長さを使用
                                total_duration = float(probe.get('format', {}).get('duration', 0))
                        
                        print(f"ffprobeによる総再生時間: {total_duration:.2f}秒")
                    except Exception as e:
                        print(f"ffprobeでの取得にも失敗: {e}")
                        # 何も情報が得られない場合は適当な値を設定（後で検出）
                        total_duration = 0
        except Exception as e:
            print(f"総再生時間の取得中に予期しないエラーが発生しました: {e}")
            total_duration = 0
        
        # 音声から無音でない区間（音声がある区間）を取得
        non_silent_segments = self.get_non_silent_segments(audio_path, total_duration)
        
        # 結果がない場合の処理
        if not non_silent_segments and total_duration > 0:
            print("有効なセグメントが検出されなかったため、全体を1つのセグメントとして使用します")
            non_silent_segments = [(0, total_duration)]
        
        # セグメント情報をJSON形式で保存
        if save_segments:
            filename = Path(video_path).stem
            segments_json = []
            
            for i, (start, end) in enumerate(non_silent_segments):
                segments_json.append({
                    "index": i,
                    "start": start,
                    "end": end,
                    "duration": end - start
                })
            
            segments_path = os.path.join(output_dir, f"{filename}_segments.json")
            with open(segments_path, "w") as f:
                json.dump(segments_json, f, indent=2)
            
            print(f"セグメント情報を保存しました: {segments_path}")
        
        # 音声がある区間のリストを返す
        return non_silent_segments
    
    def adjust_silence_detection(self, min_silence_len=None, silence_thresh=None, keep_silence=None):
        """無音検出のパラメータを調整"""
        if min_silence_len is not None:
            self.min_silence_len = min_silence_len
        if silence_thresh is not None:
            self.silence_thresh = silence_thresh
        if keep_silence is not None:
            self.keep_silence = keep_silence
        
        print(f"無音検出パラメータを調整しました: min_silence_len={self.min_silence_len}ms, silence_thresh={self.silence_thresh}dB, keep_silence={self.keep_silence}ms")

# テスト用コード
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python silence_detector.py <動画ファイルパス> [min_silence_len] [silence_thresh]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # コマンドライン引数からパラメータを設定（オプション）
    min_silence_len = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    silence_thresh = int(sys.argv[3]) if len(sys.argv) > 3 else -40
    
    # 無音検出器の初期化とパラメータ設定
    detector = SilenceDetector(min_silence_len=min_silence_len, silence_thresh=silence_thresh)
    
    # 動画を分析し、音声がある区間を取得
    non_silent_segments = detector.analyze_video(video_path)
    
    # 結果を表示
    print("音声がある区間:")
    for i, (start, end) in enumerate(non_silent_segments):
        print(f"  区間 {i+1}: {start:.2f}秒 - {end:.2f}秒 (長さ: {end-start:.2f}秒)") 