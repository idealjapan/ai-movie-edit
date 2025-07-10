#!/usr/bin/env python3
"""
AI自動カット編集＆テロップ生成システム - コマンドライン版
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path

# 設定をインポート
from config import OPENAI_API_KEY, DEFAULT_SETTINGS, WHISPER_API_ENDPOINT, GPT_API_ENDPOINT, GPT_MODEL, WHISPER_MODEL

# ユーティリティモジュールをインポート
from utils.audio_extractor import AudioExtractor
from utils.transcriber import Transcriber
from utils.segment_analyzer import SegmentAnalyzer
from utils.caption_formatter import CaptionFormatter
from utils.premiere_xml_generator import PremiereXMLGenerator
from utils.premiere_xml_generator_ultimate import PremiereXMLGeneratorUltimate
from utils.premiere_xml_generator_tested import PremiereXMLGeneratorTested
from utils.pure_fcp7_xml_generator import PureFCP7XMLGenerator
from utils.edl_generator import EDLGenerator
from utils.video_metadata import VideoMetadataExtractor


def _generate_srt_file(captions, output_path):
    """SRTファイルを生成"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, caption in enumerate(captions):
            start_time = _seconds_to_srt_time(caption.get("start", 0))
            end_time = _seconds_to_srt_time(caption.get("end", 0))
            text = caption.get("text", "")
            
            f.write(f"{i+1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")
    
    print(f"SRTファイルが生成されました: {output_path}")


def _seconds_to_srt_time(seconds):
    """秒からSRT形式のタイムコードに変換"""
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    minutes %= 60
    seconds %= 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def _generate_edl_file(segments, video_path, output_path, time_calc):
    """EDLファイルを生成"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("TITLE: AI SILENCE CUT SEQUENCE\n")
        f.write("FCM: NON-DROP FRAME\n\n")
        
        # 出力位置のタイムコード（タイムライン上の位置）
        record_in_sec = 0
        
        for i, (start_sec, end_sec) in enumerate(segments):
            clip_name = os.path.basename(video_path)
            
            # タイムコードを計算
            source_in_tc = time_calc.seconds_to_timecode(start_sec)
            source_out_tc = time_calc.seconds_to_timecode(end_sec)
            
            record_in_tc = time_calc.seconds_to_timecode(record_in_sec)
            record_out_sec = record_in_sec + (end_sec - start_sec)
            record_out_tc = time_calc.seconds_to_timecode(record_out_sec)
            
            # EDLエントリの作成
            f.write(f"{i+1:03d}  {clip_name} V     C        {source_in_tc} {source_out_tc} {record_in_tc} {record_out_tc}\n")
            f.write(f"{i+1:03d}  {clip_name} A     C        {source_in_tc} {source_out_tc} {record_in_tc} {record_out_tc}\n")
            f.write(f"{i+1:03d}  {clip_name} A2    C        {source_in_tc} {source_out_tc} {record_in_tc} {record_out_tc}\n")
            
            # 次のクリップの開始位置を更新
            record_in_sec = record_out_sec
    
    print(f"EDLファイルが生成されました: {output_path}")


def process_video(video_path, silence_threshold=1.0, margin=0.2, max_chars_per_line=15, use_tested_xml=True, output_format="xml", output_dir=None):
    """
    動画処理のメイン関数
    
    Args:
        video_path (str): 動画ファイルのパス
        silence_threshold (float): 無音閾値（秒）
        margin (float): マージン（秒）
        max_chars_per_line (int): テロップ1行の最大文字数
        use_tested_xml (bool): 動作確認済みXMLジェネレーターを使用するか
        output_format (str): 出力フォーマット ("xml", "pure-fcp7", "edl", "all")
        output_dir (str): 出力ディレクトリ（Noneの場合はデフォルトを使用）
    
    Returns:
        str: 生成されたファイルのパス
    """
    try:
        # 設定を更新
        config = DEFAULT_SETTINGS.copy()
        config['silence_threshold'] = silence_threshold
        config['margin'] = margin
        config['max_chars_per_line'] = max_chars_per_line
        
        # 出力ディレクトリを設定
        if output_dir:
            config['output_dir'] = output_dir
        
        # 1. 音声抽出
        print("1/5 動画から音声を抽出中...")
        input_is_audio = video_path.lower().endswith(('.wav', '.mp3', '.aac', '.m4a'))
        
        if input_is_audio:
            # 既に音声ファイルの場合は抽出をスキップ
            print("入力ファイルは既に音声ファイルのため、抽出をスキップします")
            audio_path = video_path
        else:
            # 動画から音声を抽出
            audio_extractor = AudioExtractor()
            audio_path = audio_extractor.extract_audio(video_path, output_dir=config['temp_dir'])
        
        # 2. 文字起こし
        print("2/5 音声から文字起こしとタイムスタンプを取得中...")
        transcriber = Transcriber(OPENAI_API_KEY, WHISPER_API_ENDPOINT, WHISPER_MODEL)
        transcript_data = transcriber.transcribe(audio_path)
        
        # 3. 無音区間検出
        print("3/5 発話区間と無音区間を解析中...")
        segment_analyzer = SegmentAnalyzer(
            silence_threshold=config['silence_threshold'],
            margin=config['margin']
        )
        keep_segments, full_transcript = segment_analyzer.analyze(transcript_data)
        
        # 発話区間データを保存
        segments_path = os.path.join(config['temp_dir'], f"{Path(video_path).stem}_segments.json")
        segment_analyzer.save_segments(keep_segments, segments_path)
        
        # 4. テロップ整形
        print("4/5 テロップを整形中...")
        caption_formatter = CaptionFormatter(
            OPENAI_API_KEY, 
            GPT_API_ENDPOINT, 
            GPT_MODEL,
            max_chars_per_line=config['max_chars_per_line']
        )
        formatted_text = caption_formatter.format_captions(full_transcript)
        
        # 整形済みテロップデータを保存
        captions_path = os.path.join(config['temp_dir'], f"{Path(video_path).stem}_captions.json")
        caption_data = caption_formatter.save_formatted_captions(
            formatted_text, transcript_data, captions_path
        )
        
        # 5. ファイル生成
        print("5/5 出力ファイルを生成中...")
        output_dir = config['output_dir']
        os.makedirs(output_dir, exist_ok=True)
        
        # セグメントデータをDict形式に変換
        segment_dicts = [{"start": start, "end": end} for start, end in keep_segments]
        
        # ビデオメタデータを取得（Pure FCP7/EDL用）
        metadata = None
        if output_format in ["pure-fcp7", "edl", "all"]:
            metadata_extractor = VideoMetadataExtractor()
            metadata = metadata_extractor.extract_metadata(video_path)
        
        generated_files = []
        
        # フォーマットに応じたファイル生成
        if output_format == "xml" or output_format == "all":
            # Premiere Pro XML生成
            xml_output_path = os.path.join(output_dir, f"{Path(video_path).stem}_edited.xml")
            
            # 究極版を使用
            print("究極版 Premiere Pro XML形式でファイルを生成します（完全なテロップ対応）")
            xml_generator = PremiereXMLGeneratorUltimate(video_path)
            
            xml_file_path = xml_generator.generate_xml(
                keep_segments, 
                xml_output_path,
                captions=caption_data.get("captions", []) if caption_data else None
            )
            generated_files.append(xml_file_path)
            print(f"XMLファイルが生成されました: {xml_file_path}")
            
            # SRTファイルも生成（字幕として使える）
            srt_output_path = os.path.join(output_dir, f"{Path(video_path).stem}_edited.srt")
            if caption_data and "captions" in caption_data:
                _generate_srt_file(caption_data["captions"], srt_output_path)
                generated_files.append(srt_output_path)
        
        if output_format == "pure-fcp7" or output_format == "all":
            # Pure FCP7 XML生成
            fcp7_output_path = os.path.join(output_dir, f"{Path(video_path).stem}_fcp7.xml")
            print("Pure FCP7 XML形式でファイルを生成します（標準FCP7 XML）")
            
            fcp7_generator = PureFCP7XMLGenerator(
                video_path, 
                segment_dicts,
                captions=caption_data.get("captions", []) if caption_data else None,
                output_path=fcp7_output_path
            )
            fcp7_generator.analyze_video(metadata)
            fcp7_file = fcp7_generator.save()
            generated_files.append(fcp7_file)
            print(f"FCP7 XMLファイルが生成されました: {fcp7_file}")
        
        if output_format == "edl" or output_format == "all":
            # EDL生成
            edl_output_path = os.path.join(output_dir, f"{Path(video_path).stem}_edited.edl")
            print("CMX 3600 EDL形式でファイルを生成します")
            
            edl_generator = EDLGenerator(
                video_path,
                segment_dicts,
                output_path=edl_output_path
            )
            edl_generator.analyze_video(metadata)
            edl_file = edl_generator.save(
                include_titles=bool(caption_data),
                captions=caption_data.get("captions", []) if caption_data else None
            )
            generated_files.append(edl_file)
            print(f"EDLファイルが生成されました: {edl_file}")
        
        # 処理完了
        print(f"\n処理が完了しました！")
        print(f"生成されたファイル数: {len(generated_files)}")
        for file in generated_files:
            print(f"  - {file}")
        
        # 最初のファイルパスを返す（GUIで表示用）
        return generated_files[0] if generated_files else None
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        raise

def main():
    """メイン関数"""
    # 引数パーサーの設定
    parser = argparse.ArgumentParser(description='AI自動カット編集＆テロップ生成システム')
    parser.add_argument('video_path', help='処理する動画ファイルのパス')
    parser.add_argument('--silence-threshold', type=float, default=1.0,
                        help='無音閾値（秒）。この長さ以上の無音区間をカットします。デフォルト: 1.0')
    parser.add_argument('--margin', type=float, default=0.2,
                        help='マージン（秒）。カット区間の前後に追加する余白です。デフォルト: 0.2')
    parser.add_argument('--max-chars-per-line', type=int, default=15,
                        help='テロップ1行の最大文字数。デフォルト: 15')
    parser.add_argument('--api-key', help='OpenAI APIキー。.envファイルまたは環境変数で設定していない場合に使用します。')
    
    # 引数のパース
    args = parser.parse_args()
    
    # APIキーの設定
    if args.api_key:
        global OPENAI_API_KEY
        OPENAI_API_KEY = args.api_key
    
    # 必要なディレクトリを作成
    os.makedirs(DEFAULT_SETTINGS['output_dir'], exist_ok=True)
    os.makedirs(DEFAULT_SETTINGS['temp_dir'], exist_ok=True)
    
    # 処理実行
    process_video(
        args.video_path,
        silence_threshold=args.silence_threshold,
        margin=args.margin,
        max_chars_per_line=args.max_chars_per_line
    )

if __name__ == "__main__":
    main()
