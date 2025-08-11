#!/usr/bin/env python3
"""
AI動画編集ツール - メインスクリプト
無音区間を検出して自動カット、テロップ付きの編集XMLを生成
"""
import os
import sys
import json
import argparse
from pathlib import Path
from utils.silence_detector import SilenceDetector
from utils.premiere_xml_generator import PremiereXMLGenerator
from utils.pure_fcp7_xml_generator import PureFCP7XMLGenerator
from utils.edl_generator import EDLGenerator
from utils.ppro_time_utils import PproTimeCalculator
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
    
    print(f"SRTファイルも生成しました: {output_path}")


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
    
    print(f"EDLファイルも生成しました: {output_path}")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="AI動画編集ツール - 無音検出自動カット＆テロップ生成")
    parser.add_argument("video_path", help="処理する動画ファイルのパス")
    parser.add_argument("--output", "-o", help="出力XMLファイルのパス（省略時は動画ファイル名_edited.xml）")
    parser.add_argument("--min-silence", type=int, default=1000, help="無音と判定する最小の長さ（ミリ秒）")
    parser.add_argument("--silence-thresh", type=int, default=-35, help="無音と判定する音量のしきい値（dB）")
    parser.add_argument("--keep-silence", type=int, default=200, help="無音区間の前後に残す無音の長さ（ミリ秒）")
    parser.add_argument("--temp-dir", default="temp", help="一時ファイルの保存ディレクトリ")
    parser.add_argument("--captions", help="使用するテロップデータのJSONファイルパス")
    parser.add_argument("--segments", help="使用するセグメントデータのJSONファイルパス（無音検出をスキップ）")
    parser.add_argument("--format", choices=["xml", "pure-fcp7", "edl", "srt"], default="xml", help="出力フォーマット（デフォルト: xml）")
    
    args = parser.parse_args()
    
    # 入力ファイルの存在確認
    video_path = args.video_path
    if not os.path.exists(video_path):
        print(f"エラー: 指定された動画ファイルが見つかりません: {video_path}")
        return 1
    
    # 出力ファイルパスの設定
    if args.output:
        output_path = args.output
    else:
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        # フォーマットに応じて拡張子を決定
        if args.format == "edl":
            ext = ".edl"
        elif args.format == "srt":
            ext = ".srt"
        else:
            ext = ".xml"
        output_path = os.path.join(output_dir, f"{Path(video_path).stem}_edited{ext}")
    
    # 一時ディレクトリの作成
    os.makedirs(args.temp_dir, exist_ok=True)
    
    # テロップデータの読み込み
    caption_data = {}
    if args.captions:
        if os.path.exists(args.captions):
            with open(args.captions, 'r', encoding='utf-8') as f:
                caption_data = json.load(f)
            print(f"テロップデータを読み込みました: {args.captions}")
        else:
            print(f"警告: 指定されたテロップファイルが見つかりません: {args.captions}")
    
    # セグメントデータの取得
    if args.segments:
        # 既存のセグメントデータを使用
        if os.path.exists(args.segments):
            with open(args.segments, 'r', encoding='utf-8') as f:
                segments_data = json.load(f)
            
            # JSON形式からタプルのリストに変換
            keep_segments = [(segment["start"], segment["end"]) for segment in segments_data]
            print(f"セグメントデータを読み込みました: {args.segments}")
        else:
            print(f"エラー: 指定されたセグメントファイルが見つかりません: {args.segments}")
            return 1
    else:
        # 無音検出器を使用して音声があるセグメントを特定
        print("無音区間検出を開始します...")
        detector = SilenceDetector(
            min_silence_len=args.min_silence,
            silence_thresh=args.silence_thresh,
            keep_silence=args.keep_silence
        )
        
        keep_segments = detector.analyze_video(video_path, output_dir=args.temp_dir)
    
    # セグメント情報の表示
    print(f"\n音声がある区間（カットせずに保持する区間）: {len(keep_segments)}個")
    for i, (start, end) in enumerate(keep_segments):
        print(f"  区間 {i+1}: {start:.2f}秒 - {end:.2f}秒 (長さ: {end-start:.2f}秒)")
    
    # フォーマット処理
    if args.format == "srt":
        # SRTファイルのみ生成
        if caption_data and "captions" in caption_data:
            _generate_srt_file(caption_data["captions"], output_path)
            print(f"\n処理が完了しました。出力ファイル: {output_path}")
        else:
            print("エラー: SRTフォーマットにはキャプションデータが必要です")
            return 1
    else:
        # セグメントデータをDict形式に変換
        segment_dicts = [{"start": start, "end": end} for start, end in keep_segments]
        
        if args.format == "pure-fcp7":
            # Pure FCP7 XML生成
            print("\nPure FCP7 XML生成を開始します...")
            print("標準FCP7 XML形式でファイルを生成します（Premiere Pro互換）")
            
            # ビデオメタデータを取得
            metadata_extractor = VideoMetadataExtractor()
            metadata = metadata_extractor.extract_metadata(video_path)
            
            generator = PureFCP7XMLGenerator(
                video_path, 
                segment_dicts,
                captions=caption_data.get("captions", []) if caption_data else None,
                output_path=output_path
            )
            generator.analyze_video(metadata)
            output_file = generator.save()
            
        elif args.format == "edl":
            # EDL生成（新しいジェネレーターを使用）
            print("\nEDL生成を開始します...")
            print("CMX 3600 EDL形式でファイルを生成します")
            
            # ビデオメタデータを取得
            metadata_extractor = VideoMetadataExtractor()
            metadata = metadata_extractor.extract_metadata(video_path)
            
            generator = EDLGenerator(
                video_path,
                segment_dicts,
                output_path=output_path
            )
            generator.analyze_video(metadata)
            output_file = generator.save(
                include_titles=bool(caption_data),
                captions=caption_data.get("captions", []) if caption_data else None
            )
            
        else:
            # デフォルト: Premiere Pro XML形式
            print("\nXML生成を開始します...")
            print("Premiere Pro XML形式でファイルを生成します（フレームレート自動検出、pproTicks対応）")
            
            generator = PremiereXMLGenerator(video_path)
            output_file = generator.generate_xml(
                keep_segments, 
                output_path,
                captions=caption_data.get("captions", []) if caption_data else None
            )
            
            # 追加ファイルも生成（互換性のため）
            edl_output_path = os.path.splitext(output_path)[0] + ".edl"
            _generate_edl_file(keep_segments, video_path, edl_output_path, generator.time_calc)
            
            # SRTファイルも生成（字幕として使える）
            if caption_data and "captions" in caption_data:
                srt_output_path = os.path.splitext(output_path)[0] + ".srt"
                _generate_srt_file(caption_data["captions"], srt_output_path)
        
        print(f"\n処理が完了しました。出力ファイル: {output_path if args.format == 'xml' else output_file}")
    
    return 0

if __name__ == "__main__":
    # 使用例を表示
    if len(sys.argv) == 1:
        print("使用方法: python main.py <動画ファイルパス> [オプション]")
        print("\n例: python main.py IMG_7453.MP4 --min-silence 500 --silence-thresh -40")
        print("\n利用可能なオプションについては --help を参照してください。")
        sys.exit(1)
    
    sys.exit(main()) 