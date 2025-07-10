"""
設定ファイル：APIキーや重要なパラメータを管理
"""
import os
from dotenv import load_dotenv

# .envファイルから環境変数をロード
load_dotenv()

# OpenAI APIキー
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-api-key-here')

# デフォルト設定値
DEFAULT_SETTINGS = {
    # 無音検出のパラメータ
    'silence_threshold': 1.0,  # 秒単位
    'margin': 0.2,  # 秒単位
    
    # 音声抽出の設定
    'audio_format': 'wav',
    'audio_codec': 'pcm_s16le',
    'audio_sample_rate': 16000,
    'audio_channels': 1,
    
    # テロップの設定
    'max_chars_per_line': 15,  # 1行の最大文字数
    
    # ファイル出力設定
    'output_dir': 'output',
    'temp_dir': 'temp'
}

# OpenAI APIのエンドポイント
WHISPER_API_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
GPT_API_ENDPOINT = "https://api.openai.com/v1/chat/completions"

# GPT-4oモデル名
GPT_MODEL = "gpt-4o"

# Whisperモデル名
WHISPER_MODEL = "whisper-1"
