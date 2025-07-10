"""
Premiere Pro完全互換XML生成モジュール
複数クリップ方式で正確なフレームレートとpproTicksを使用
"""
import os
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from xml.etree import ElementTree as ET
from xml.dom import minidom
import urllib.parse

from .video_metadata import VideoMetadataExtractor
from .ppro_time_utils import PproTimeCalculator, create_calculator_from_metadata


class PremiereXMLGenerator:
    """Premiere Pro用のXMLを生成するクラス"""
    
    def __init__(self, video_path: str):
        """
        初期化
        
        Args:
            video_path: 動画ファイルのパス
        """
        self.video_path = video_path
        self.video_name = Path(video_path).stem
        
        # メタデータを取得
        self.metadata_extractor = VideoMetadataExtractor()
        self.metadata = self.metadata_extractor.extract_metadata(video_path)
        
        # 時間計算機を初期化
        self.time_calc = create_calculator_from_metadata(self.metadata)
        
        # プロジェクト設定
        self.sequence_id = str(uuid.uuid4())
        self.master_clip_id = str(uuid.uuid4())
        
    def generate_xml(self, segments: List[Tuple[float, float]], 
                    output_path: str,
                    captions: Optional[List[Dict]] = None) -> str:
        """
        複数クリップ方式でXMLを生成
        
        Args:
            segments: 保持するセグメントのリスト [(start_sec, end_sec), ...]
            output_path: 出力ファイルパス
            captions: キャプションデータ（オプション）
            
        Returns:
            生成したXMLファイルのパス
        """
        # XMLルート要素を作成
        xmeml = ET.Element('xmeml', version='4')
        
        # プロジェクト要素
        project = ET.SubElement(xmeml, 'project')
        project_name = ET.SubElement(project, 'name')
        project_name.text = self.video_name
        
        # UUID
        project_uuid = ET.SubElement(project, 'uuid')
        project_uuid.text = str(uuid.uuid4())
        
        # プロジェクトの子要素
        children = ET.SubElement(project, 'children')
        
        # マスタークリップを作成
        self._create_master_clip(children)
        
        # シーケンスを作成
        self._create_sequence(children, segments, captions)
        
        # XMLを整形して出力
        xml_string = self._prettify_xml(xmeml)
        
        # ファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE xmeml>\n')
            f.write(xml_string)
            
        print(f"Premiere Pro XMLファイルを生成しました: {output_path}")
        return output_path
    
    def _create_master_clip(self, parent: ET.Element):
        """マスタークリップを作成"""
        clip = ET.SubElement(parent, 'clip', id=self.master_clip_id)
        
        # UUID
        uuid_elem = ET.SubElement(clip, 'uuid')
        uuid_elem.text = self.master_clip_id
        
        # マスタークリップID
        masterclipid = ET.SubElement(clip, 'masterclipid')
        masterclipid.text = self.master_clip_id
        
        # 名前
        name = ET.SubElement(clip, 'name')
        name.text = Path(self.video_path).name
        
        # 継続時間（pproTicks）
        duration = ET.SubElement(clip, 'duration')
        duration.text = str(self.time_calc.seconds_to_ticks(self.metadata['duration']))
        
        # レート
        rate = ET.SubElement(clip, 'rate')
        timebase = ET.SubElement(rate, 'timebase')
        timebase.text = str(self.time_calc.timebase)
        ntsc = ET.SubElement(rate, 'ntsc')
        ntsc.text = str(self.metadata['is_ntsc']).upper()
        
        # メディア
        media = ET.SubElement(clip, 'media')
        
        # ビデオ
        video = ET.SubElement(media, 'video')
        video_format = ET.SubElement(video, 'format')
        video_sc = ET.SubElement(video_format, 'samplecharacteristics')
        
        # ビデオ特性
        width = ET.SubElement(video_sc, 'width')
        width.text = str(self.metadata['width'])
        height = ET.SubElement(video_sc, 'height')
        height.text = str(self.metadata['height'])
        pixelaspectratio = ET.SubElement(video_sc, 'pixelaspectratio')
        pixelaspectratio.text = 'square'
        fielddominance = ET.SubElement(video_sc, 'fielddominance')
        fielddominance.text = 'none'
        
        # レート（ビデオ）
        video_rate = ET.SubElement(video_sc, 'rate')
        video_timebase = ET.SubElement(video_rate, 'timebase')
        video_timebase.text = str(self.time_calc.timebase)
        video_ntsc = ET.SubElement(video_rate, 'ntsc')
        video_ntsc.text = str(self.metadata['is_ntsc']).upper()
        
        # オーディオ
        audio = ET.SubElement(media, 'audio')
        audio_format = ET.SubElement(audio, 'format')
        audio_sc = ET.SubElement(audio_format, 'samplecharacteristics')
        
        depth = ET.SubElement(audio_sc, 'depth')
        depth.text = '16'
        samplerate = ET.SubElement(audio_sc, 'samplerate')
        samplerate.text = str(self.metadata['audio_sample_rate'])
        channelcount = ET.SubElement(audio_sc, 'channelcount')
        channelcount.text = str(self.metadata['audio_channels'])
        
        # ファイル情報
        file_elem = ET.SubElement(clip, 'file')
        file_name = ET.SubElement(file_elem, 'name')
        file_name.text = Path(self.video_path).name
        
        # パスURL
        pathurl = ET.SubElement(file_elem, 'pathurl')
        pathurl.text = self._create_file_url(self.video_path)
        
        # ファイルレート
        file_rate = ET.SubElement(file_elem, 'rate')
        file_timebase = ET.SubElement(file_rate, 'timebase')
        file_timebase.text = str(self.time_calc.timebase)
        file_ntsc = ET.SubElement(file_rate, 'ntsc')
        file_ntsc.text = str(self.metadata['is_ntsc']).upper()
        
        # ファイル継続時間
        file_duration = ET.SubElement(file_elem, 'duration')
        file_duration.text = str(self.time_calc.seconds_to_ticks(self.metadata['duration']))
    
    def _create_sequence(self, parent: ET.Element, segments: List[Tuple[float, float]], 
                        captions: Optional[List[Dict]] = None):
        """シーケンスを作成"""
        sequence = ET.SubElement(parent, 'sequence', id='sequence-1')
        
        # UUID
        uuid_elem = ET.SubElement(sequence, 'uuid')
        uuid_elem.text = self.sequence_id
        
        # 名前
        name = ET.SubElement(sequence, 'name')
        name.text = f"{self.video_name}_edited"
        
        # 総継続時間を計算
        total_duration = sum(end - start for start, end in segments)
        
        # 継続時間（pproTicks）
        duration = ET.SubElement(sequence, 'duration')
        duration.text = str(self.time_calc.seconds_to_ticks(total_duration))
        
        # レート
        rate = ET.SubElement(sequence, 'rate')
        timebase = ET.SubElement(rate, 'timebase')
        timebase.text = str(self.time_calc.timebase)
        ntsc = ET.SubElement(rate, 'ntsc')
        ntsc.text = str(self.metadata['is_ntsc']).upper()
        
        # タイムコード
        timecode = ET.SubElement(sequence, 'timecode')
        tc_rate = ET.SubElement(timecode, 'rate')
        tc_timebase = ET.SubElement(tc_rate, 'timebase')
        tc_timebase.text = str(self.time_calc.timebase)
        tc_ntsc = ET.SubElement(tc_rate, 'ntsc')
        tc_ntsc.text = str(self.metadata['is_ntsc']).upper()
        
        tc_string = ET.SubElement(timecode, 'string')
        tc_string.text = '00:00:00:00'
        tc_frame = ET.SubElement(timecode, 'frame')
        tc_frame.text = '0'
        tc_display = ET.SubElement(timecode, 'displayformat')
        tc_display.text = 'NDF'  # Non-Drop Frame
        
        # メディア
        media = ET.SubElement(sequence, 'media')
        
        # ビデオトラック
        video = ET.SubElement(media, 'video')
        self._create_video_tracks(video, segments)
        
        # オーディオトラック
        audio = ET.SubElement(media, 'audio')
        self._create_audio_tracks(audio, segments)
    
    def _create_video_tracks(self, parent: ET.Element, segments: List[Tuple[float, float]]):
        """ビデオトラックを作成"""
        track = ET.SubElement(parent, 'track')
        
        # トラックを有効化
        enabled = ET.SubElement(track, 'enabled')
        enabled.text = 'TRUE'
        
        # トラックをロック解除
        locked = ET.SubElement(track, 'locked')
        locked.text = 'FALSE'
        
        timeline_position = 0  # タイムライン上の現在位置
        
        for i, (start_sec, end_sec) in enumerate(segments):
            clipitem = ET.SubElement(track, 'clipitem', id=f'clipitem-v{i+1}')
            
            # マスタークリップID
            masterclipid = ET.SubElement(clipitem, 'masterclipid')
            masterclipid.text = self.master_clip_id
            
            # 名前
            name = ET.SubElement(clipitem, 'name')
            name.text = f"{Path(self.video_path).name} - {i+1}"
            
            # 有効
            enabled = ET.SubElement(clipitem, 'enabled')
            enabled.text = 'TRUE'
            
            # 継続時間（pproTicks）
            clip_duration = end_sec - start_sec
            duration = ET.SubElement(clipitem, 'duration')
            duration.text = str(self.time_calc.seconds_to_ticks(clip_duration))
            
            # レート
            rate = ET.SubElement(clipitem, 'rate')
            timebase = ET.SubElement(rate, 'timebase')
            timebase.text = str(self.time_calc.timebase)
            ntsc = ET.SubElement(rate, 'ntsc')
            ntsc.text = str(self.metadata['is_ntsc']).upper()
            
            # タイムライン上の位置（pproTicks）
            start = ET.SubElement(clipitem, 'start')
            start.text = str(self.time_calc.seconds_to_ticks(timeline_position))
            
            end = ET.SubElement(clipitem, 'end')
            end.text = str(self.time_calc.seconds_to_ticks(timeline_position + clip_duration))
            
            # ソースファイル内の位置（pproTicks）
            in_point = ET.SubElement(clipitem, 'in')
            in_point.text = str(self.time_calc.seconds_to_ticks(start_sec))
            
            out_point = ET.SubElement(clipitem, 'out')
            out_point.text = str(self.time_calc.seconds_to_ticks(end_sec))
            
            # pproTicksフィールド（Premiere Pro固有）
            pproTicksIn = ET.SubElement(clipitem, 'pproTicksIn')
            pproTicksIn.text = str(self.time_calc.seconds_to_ticks(start_sec))
            
            pproTicksOut = ET.SubElement(clipitem, 'pproTicksOut')
            pproTicksOut.text = str(self.time_calc.seconds_to_ticks(end_sec))
            
            # ファイル参照
            file_elem = ET.SubElement(clipitem, 'file', id=self.master_clip_id)
            
            # リンク情報（オーディオとのリンク）
            link = ET.SubElement(clipitem, 'link')
            linkclipref = ET.SubElement(link, 'linkclipref')
            linkclipref.text = f'clipitem-a{i+1}'
            mediatype = ET.SubElement(link, 'mediatype')
            mediatype.text = 'audio'
            
            # タイムライン位置を更新
            timeline_position += clip_duration
    
    def _create_audio_tracks(self, parent: ET.Element, segments: List[Tuple[float, float]]):
        """オーディオトラックを作成"""
        # ステレオの場合、2つのトラックを作成
        for channel in range(self.metadata['audio_channels']):
            track = ET.SubElement(parent, 'track')
            
            # トラックを有効化
            enabled = ET.SubElement(track, 'enabled')
            enabled.text = 'TRUE'
            
            # トラックをロック解除
            locked = ET.SubElement(track, 'locked')
            locked.text = 'FALSE'
            
            timeline_position = 0
            
            for i, (start_sec, end_sec) in enumerate(segments):
                clipitem = ET.SubElement(track, 'clipitem', 
                                       id=f'clipitem-a{i+1}-ch{channel+1}')
                
                # マスタークリップID
                masterclipid = ET.SubElement(clipitem, 'masterclipid')
                masterclipid.text = self.master_clip_id
                
                # 名前
                name = ET.SubElement(clipitem, 'name')
                name.text = f"{Path(self.video_path).name} - Audio {channel+1}"
                
                # 有効
                enabled = ET.SubElement(clipitem, 'enabled')
                enabled.text = 'TRUE'
                
                # 継続時間（pproTicks）
                clip_duration = end_sec - start_sec
                duration = ET.SubElement(clipitem, 'duration')
                duration.text = str(self.time_calc.seconds_to_ticks(clip_duration))
                
                # レート
                rate = ET.SubElement(clipitem, 'rate')
                timebase = ET.SubElement(rate, 'timebase')
                timebase.text = str(self.time_calc.timebase)
                ntsc = ET.SubElement(rate, 'ntsc')
                ntsc.text = str(self.metadata['is_ntsc']).upper()
                
                # タイムライン上の位置（pproTicks）
                start = ET.SubElement(clipitem, 'start')
                start.text = str(self.time_calc.seconds_to_ticks(timeline_position))
                
                end = ET.SubElement(clipitem, 'end')
                end.text = str(self.time_calc.seconds_to_ticks(timeline_position + clip_duration))
                
                # ソースファイル内の位置（pproTicks）
                in_point = ET.SubElement(clipitem, 'in')
                in_point.text = str(self.time_calc.seconds_to_ticks(start_sec))
                
                out_point = ET.SubElement(clipitem, 'out')
                out_point.text = str(self.time_calc.seconds_to_ticks(end_sec))
                
                # ファイル参照
                file_elem = ET.SubElement(clipitem, 'file', id=self.master_clip_id)
                
                # ソーストラック
                sourcetrack = ET.SubElement(clipitem, 'sourcetrack')
                mediatype = ET.SubElement(sourcetrack, 'mediatype')
                mediatype.text = 'audio'
                trackindex = ET.SubElement(sourcetrack, 'trackindex')
                trackindex.text = str(channel + 1)
                
                # リンク情報（ビデオとのリンク）
                if channel == 0:  # 最初のチャンネルのみビデオとリンク
                    link = ET.SubElement(clipitem, 'link')
                    linkclipref = ET.SubElement(link, 'linkclipref')
                    linkclipref.text = f'clipitem-v{i+1}'
                    mediatype = ET.SubElement(link, 'mediatype')
                    mediatype.text = 'video'
                
                timeline_position += clip_duration
    
    def _create_file_url(self, file_path: str) -> str:
        """ファイルパスをPremiere Pro用のURLに変換"""
        abs_path = os.path.abspath(file_path)
        
        # Windowsの場合
        if os.name == 'nt':
            # C:\path\to\file → file://localhost/C:/path/to/file
            url_path = abs_path.replace('\\', '/')
            return f"file://localhost/{url_path}"
        else:
            # macOS/Linuxの場合
            # /path/to/file → file://localhost/path/to/file
            return f"file://localhost{urllib.parse.quote(abs_path)}"
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """XMLを整形"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # DOCTYPE宣言を除外してから整形
        pretty_xml = reparsed.toprettyxml(indent='  ', encoding=None)
        
        # 不要な空行を削除
        lines = pretty_xml.split('\n')
        lines = [line.rstrip() for line in lines if line.strip()]
        
        # XML宣言を除外（別途追加するため）
        if lines[0].startswith('<?xml'):
            lines = lines[1:]
            
        return '\n'.join(lines)