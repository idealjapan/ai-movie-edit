#!/usr/bin/env python3
"""
Premiere Pro 2024で確実に動作するXMLを生成
"""
import os
import sys
import json
from pathlib import Path
from urllib.parse import quote

def generate_working_xml(video_path, segments=None):
    """動作確認済みのシンプルなXML構造を生成"""
    
    video_name = Path(video_path).stem
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # デフォルトセグメント（テスト用）
    if segments is None:
        segments = [
            {"start": 0, "end": 10.1},  # 0:00-0:10
            {"start": 280.7, "end": 746.6}  # 4:40-12:26
        ]
    
    # XMLコンテンツ（シンプルで確実な構造）
    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
  <sequence id="sequence-1">
    <name>{video_name}_edited</name>
    <duration>{int(sum(s['end'] - s['start'] for s in segments) * 30)}</duration>
    <rate>
      <timebase>30</timebase>
      <ntsc>FALSE</ntsc>
    </rate>
    <timecode>
      <rate>
        <timebase>30</timebase>
        <ntsc>FALSE</ntsc>
      </rate>
      <string>00:00:00:00</string>
      <frame>0</frame>
      <displayformat>NDF</displayformat>
    </timecode>
    <media>
      <video>
        <format>
          <samplecharacteristics>
            <width>1920</width>
            <height>1080</height>
            <pixelaspectratio>square</pixelaspectratio>
            <fielddominance>none</fielddominance>
          </samplecharacteristics>
        </format>
        <track>'''
    
    # クリップを追加
    timeline_position = 0
    for i, segment in enumerate(segments):
        duration_frames = int((segment['end'] - segment['start']) * 30)
        in_frames = int(segment['start'] * 30)
        out_frames = int(segment['end'] * 30)
        
        xml_content += f'''
          <clipitem id="clipitem-{i+1}">
            <name>{video_name} - {i+1}</name>
            <duration>{duration_frames}</duration>
            <rate>
              <timebase>30</timebase>
              <ntsc>FALSE</ntsc>
            </rate>
            <start>{timeline_position}</start>
            <end>{timeline_position + duration_frames}</end>
            <in>{in_frames}</in>
            <out>{out_frames}</out>
            <file>
              <name>{Path(video_path).name}</name>
              <pathurl>file://localhost{quote(video_path)}</pathurl>
            </file>
          </clipitem>'''
        
        timeline_position += duration_frames
    
    xml_content += '''
        </track>
      </video>
    </media>
  </sequence>
</xmeml>'''
    
    # ファイルに保存
    output_path = output_dir / f"{video_name}_simple.xml"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"XMLファイルを生成しました: {output_path}")
    
    # EDLも生成（バックアップ用）
    generate_edl(video_path, segments, output_dir / f"{video_name}.edl")
    
    return output_path

def generate_edl(video_path, segments, output_path):
    """EDLファイルも生成"""
    video_name = Path(video_path).stem
    
    edl_content = f"TITLE: {video_name}_edited\nFCM: NON-DROP FRAME\n\n"
    
    timeline_tc = 0
    for i, segment in enumerate(segments):
        start_tc = frames_to_timecode(int(segment['start'] * 30))
        end_tc = frames_to_timecode(int(segment['end'] * 30))
        timeline_start = frames_to_timecode(timeline_tc)
        timeline_end = frames_to_timecode(timeline_tc + int((segment['end'] - segment['start']) * 30))
        
        edl_content += f"{i+1:03d}  {video_name} V     C        {start_tc} {end_tc} {timeline_start} {timeline_end}\n"
        timeline_tc += int((segment['end'] - segment['start']) * 30)
    
    with open(output_path, 'w') as f:
        f.write(edl_content)
    
    print(f"EDLファイルも生成しました: {output_path}")

def frames_to_timecode(frames, fps=30):
    """フレーム数をタイムコードに変換"""
    hours = frames // (fps * 3600)
    minutes = (frames % (fps * 3600)) // (fps * 60)
    seconds = (frames % (fps * 60)) // fps
    frames = frames % fps
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

def main():
    if len(sys.argv) < 2:
        # テスト用のデフォルト動画
        video_paths = [
            "/Users/takayakazuki/Desktop/IMG_2525_cfr30.mov",
            "/Users/takayakazuki/Desktop/IMG_2525.mov",
            "/Users/takayakazuki/Downloads/IMG_3228.mp4",
            "/Users/takayakazuki/Downloads/IMG_3229.mp4"
        ]
        
        for video_path in video_paths:
            if os.path.exists(video_path):
                print(f"動画ファイルを発見: {video_path}")
                generate_working_xml(video_path)
                break
        else:
            print("使用方法: python3 generate_test_xml.py <動画ファイルパス>")
            sys.exit(1)
    else:
        video_path = sys.argv[1]
        if not os.path.exists(video_path):
            print(f"エラー: ファイルが見つかりません: {video_path}")
            sys.exit(1)
        
        generate_working_xml(video_path)

if __name__ == "__main__":
    main()