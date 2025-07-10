"""
カスタムAPI設定モジュール
会社のAPIエンドポイントを使用するための設定
"""
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

def get_api_config():
    """
    API設定を取得（環境変数から優先的に読み込み）
    
    Returns:
        dict: API設定情報
    """
    # カスタムAPIが設定されているかチェック
    custom_whisper_endpoint = os.getenv('CUSTOM_WHISPER_ENDPOINT')
    custom_gpt_endpoint = os.getenv('CUSTOM_GPT_ENDPOINT')
    custom_api_key = os.getenv('CUSTOM_API_KEY')
    
    # カスタムAPIが完全に設定されている場合はそれを使用
    if custom_whisper_endpoint and custom_gpt_endpoint and custom_api_key:
        return {
            'whisper_endpoint': custom_whisper_endpoint,
            'gpt_endpoint': custom_gpt_endpoint,
            'api_key': custom_api_key,
            'whisper_model': os.getenv('WHISPER_MODEL', 'whisper-1'),
            'gpt_model': os.getenv('GPT_MODEL', 'gpt-4o'),
            'is_custom': True
        }
    
    # それ以外はOpenAI APIを使用
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("APIキーが設定されていません。.envファイルを確認してください。")
    
    return {
        'whisper_endpoint': 'https://api.openai.com/v1/audio/transcriptions',
        'gpt_endpoint': 'https://api.openai.com/v1/chat/completions',
        'api_key': openai_key,
        'whisper_model': os.getenv('WHISPER_MODEL', 'whisper-1'),
        'gpt_model': os.getenv('GPT_MODEL', 'gpt-4o'),
        'is_custom': False
    }