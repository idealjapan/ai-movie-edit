#!/usr/bin/env python3
"""
カット調整済み動画からSRT字幕ファイルを生成するスクリプト（改良版）
単語レベルのタイムスタンプを使用して、より正確なタイミングを実現

Usage:
    python generate_srt_improved.py <video_path> [options]
"""

import argparse
import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.audio_extractor import AudioExtractor
from utils.transcriber_improved import ImprovedTranscriber
from utils.caption_formatter_improved import ImprovedCaptionFormatter
from config import OPENAI_API_KEY, WHISPER_API_ENDPOINT, WHISPER_MODEL, GPT_API_ENDPOINT, GPT_MODEL


def generate_srt_from_captions(captions, output_path):
    """
    キャプションデータからSRTファイルを生成
    
    Args:
        captions: キャプションデータ（format_captionsの出力）
        output_path: 出力SRTファイルパス
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, caption in enumerate(captions['captions'], 1):
            # SRT形式のタイムコード
            start_time = format_srt_time(caption['start'])
            end_time = format_srt_time(caption['end'])
            
            # SRTフォーマットで書き込み
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{caption['text']}\n")
            f.write("\n")
    
    print(f"✅ SRTファイルを生成しました: {output_path}")


def format_srt_time(seconds):
    """
    秒数をSRTタイムコード形式に変換
    例: 1.5 -> "00:00:01,500"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main():
    parser = argparse.ArgumentParser(
        description='カット調整済み動画からSRT字幕ファイルを生成（改良版）'
    )
    parser.add_argument('video_path', help='入力動画ファイルのパス')
    parser.add_argument('--output', '-o', help='出力SRTファイルのパス')
    parser.add_argument('--max-chars-per-line', type=int, default=20,
                       help='1行あたりの最大文字数（デフォルト: 20）')
    parser.add_argument('--temp-dir', default='temp',
                       help='一時ファイル用ディレクトリ（デフォルト: temp）')
    parser.add_argument('--api-key', help='OpenAI APIキー（環境変数より優先）')
    
    args = parser.parse_args()
    
    # 入力ファイルの確認
    video_path = Path(args.video_path)
    if not video_path.exists():
        print(f"❌ エラー: 動画ファイルが見つかりません: {video_path}")
        sys.exit(1)
    
    # 出力ファイルパスの設定
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = Path('output')
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{video_path.stem}_subtitles_improved.srt"
    
    # APIキーの設定
    api_key = args.api_key or OPENAI_API_KEY
    if not api_key:
        print("❌ エラー: OpenAI APIキーが設定されていません")
        print("環境変数 OPENAI_API_KEY を設定するか、--api-key オプションを使用してください")
        sys.exit(1)
    
    # 一時ディレクトリの作成
    temp_dir = Path(args.temp_dir)
    temp_dir.mkdir(exist_ok=True)
    
    # 音声ファイルパスを初期化
    audio_path = temp_dir / f"{video_path.stem}_audio.wav"
    
    try:
        print(f"🎬 動画を処理中: {video_path}")
        print("🚀 改良版：単語レベルのタイムスタンプを使用")
        
        # 1. 音声を抽出
        print("🔊 音声を抽出中...")
        extractor = AudioExtractor()
        audio_path_str = extractor.extract_audio(str(video_path), str(temp_dir))
        audio_path = Path(audio_path_str)
        
        # 2. 音声を文字起こし（単語レベルのタイムスタンプ付き）
        print("📝 音声を文字起こし中（単語タイムスタンプ付き）...")
        transcriber = ImprovedTranscriber(api_key, WHISPER_API_ENDPOINT, WHISPER_MODEL)
        transcript = transcriber.transcribe(str(audio_path))
        
        if not transcript:
            print("❌ エラー: 文字起こしに失敗しました")
            sys.exit(1)
        
        # 単語タイムスタンプの確認
        if 'words' in transcript:
            print(f"✅ 単語タイムスタンプを取得しました（{len(transcript['words'])}単語）")
        else:
            print("⚠️ 警告: 単語タイムスタンプが利用できません")
        
        # 3. キャプションをフォーマット
        print("✂️ キャプションをフォーマット中...")
        formatter = ImprovedCaptionFormatter(
            api_key, 
            GPT_API_ENDPOINT, 
            GPT_MODEL,
            max_chars_per_line=args.max_chars_per_line
        )
        formatted_text = formatter.format_captions(transcript['text'])
        
        # 整形済みテロップデータを作成（単語タイムスタンプを活用）
        captions_path = temp_dir / f"{video_path.stem}_captions_improved.json"
        captions_data = formatter.save_formatted_captions(
            formatted_text, transcript, str(captions_path)
        )
        
        # 4. SRTファイルを生成
        print("📄 SRTファイルを生成中...")
        generate_srt_from_captions(captions_data, output_path)
        
        # 統計情報を表示
        total_captions = len(captions_data['captions'])
        total_duration = captions_data['captions'][-1]['end'] if captions_data['captions'] else 0
        
        print("\n📊 生成結果:")
        print(f"  - キャプション数: {total_captions}")
        print(f"  - 総時間: {format_srt_time(total_duration).replace(',', '.')}")
        print(f"  - 1行最大文字数: {args.max_chars_per_line}")
        print(f"  - 出力ファイル: {output_path}")
        print(f"  - タイミング精度: {'高（単語レベル）' if 'words' in transcript else '標準（セグメントレベル）'}")
        
        # 最初の数行をプレビュー
        print("\n📝 プレビュー（最初の3つ）:")
        for i, caption in enumerate(captions_data['captions'][:3], 1):
            print(f"{i}. [{format_srt_time(caption['start'])} - {format_srt_time(caption['end'])}]")
            print(f"   {caption['text']}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # 一時ファイルのクリーンアップ
        if audio_path.exists():
            audio_path.unlink()


if __name__ == "__main__":
    main()