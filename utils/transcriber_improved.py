"""
文字起こしモジュール：OpenAI Whisper APIを使って音声からテキストとタイムスタンプを取得
改良版：単語レベルのタイムスタンプ対応
"""
import os
import json
import requests
from pathlib import Path
import sys

class ImprovedTranscriber:
    def __init__(self, api_key, api_endpoint, model):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        
    def transcribe(self, audio_path):
        """
        音声ファイルをWhisper APIで文字起こし（単語レベルのタイムスタンプ付き）
        
        Args:
            audio_path (str): 音声ファイルのパス
            
        Returns:
            dict: 文字起こし結果（テキスト、単語ごとのタイムスタンプなど）
        """
        print(f"文字起こしを開始します: {audio_path}")
        
        # 音声ファイルが存在するか確認
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_path}")
        
        # APIリクエストのヘッダー
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # APIリクエストのデータ（単語レベルのタイムスタンプを要求）
        data = {
            "model": self.model,
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word",  # 単語レベルのタイムスタンプを要求
            "language": "ja"
        }
        
        try:
            # 音声ファイルをオープン
            with open(audio_path, "rb") as audio_file:
                # マルチパートフォームデータを作成
                files = {
                    "file": (Path(audio_path).name, audio_file, "audio/wav")
                }
                
                # APIリクエストを送信
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    data=data,
                    files=files
                )
                
                # レスポンスを確認
                if response.status_code != 200:
                    print(f"API エラー ({response.status_code}): {response.text}", file=sys.stderr)
                    raise Exception(f"Whisper API エラー: {response.text}")
                
                # JSON形式の結果を取得
                result = response.json()
                
                # 結果を保存（デバッグ用）
                output_dir = "temp"
                os.makedirs(output_dir, exist_ok=True)
                transcript_path = os.path.join(output_dir, f"{Path(audio_path).stem}_transcript_with_words.json")
                with open(transcript_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"文字起こしが完了しました（単語タイムスタンプ付き）: {transcript_path}")
                return result
                
        except Exception as e:
            print(f"文字起こしエラー: {str(e)}", file=sys.stderr)
            raise