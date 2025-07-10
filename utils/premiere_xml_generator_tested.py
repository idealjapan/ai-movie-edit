"""
Premiere Pro 2024動作確認済みXML生成モジュール
実際にPremiere Proで読み込みテスト済みの形式を使用
"""
import os
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from xml.etree import ElementTree as ET
from xml.dom import minidom

from .video_metadata import VideoMetadataExtractor


class PremiereXMLGeneratorTested:
    """動作確認済みの形式でPremiere Pro XMLを生成"""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.video_name = Path(video_path).stem
        
        # メタデータを取得
        self.metadata_extractor = VideoMetadataExtractor()
        self.metadata = self.metadata_extractor.extract_metadata(video_path)
        
        # フレームレート関連
        self.fps = self.metadata['fps']
        self.is_ntsc = self._is_ntsc_framerate(self.fps)
        self.timebase = self._calculate_timebase()
        
    def _is_ntsc_framerate(self, fps: float) -> bool:
        """NTSCフレームレートかどうかを判定"""
        ntsc_rates = [23.976, 29.97, 59.94, 119.88]
        return any(abs(fps - rate) < 0.01 for rate in ntsc_rates)
    
    def _calculate_timebase(self) -> int:
        """タイムベースを計算"""
        if self.is_ntsc:
            if abs(self.fps - 23.976) < 0.01:
                return 24
            elif abs(self.fps - 29.97) < 0.01:
                return 30
            elif abs(self.fps - 59.94) < 0.01:
                return 60
        return int(round(self.fps))
    
    def generate_xml(self, segments: List[Tuple[float, float]], 
                    output_path: str,
                    captions: Optional[List[Dict]] = None) -> str:
        """
        動作確認済みのPremiere Pro XMLを生成
        """
        # ルート要素
        root = ET.Element('xmeml')
        root.set('version', '4')
        
        # シーケンス
        sequence = ET.SubElement(root, 'sequence')
        
        # シーケンスID（重要）
        sequence.set('id', 'sequence-1')
        
        # メタ情報
        uuid = ET.SubElement(sequence, 'uuid')
        uuid.text = 'sequence-uuid-1'
        
        name = ET.SubElement(sequence, 'name')
        name.text = f"{self.video_name}_edited"
        
        # 継続時間
        total_frames = sum(
            int((end - start) * self.fps) for start, end in segments
        )
        duration = ET.SubElement(sequence, 'duration')
        duration.text = str(total_frames)
        
        # レート
        rate = ET.SubElement(sequence, 'rate')
        timebase = ET.SubElement(rate, 'timebase')
        timebase.text = str(self.timebase)
        ntsc = ET.SubElement(rate, 'ntsc')
        ntsc.text = 'TRUE' if self.is_ntsc else 'FALSE'
        
        # タイムコード
        timecode = ET.SubElement(sequence, 'timecode')
        
        tc_rate = ET.SubElement(timecode, 'rate')
        tc_timebase = ET.SubElement(tc_rate, 'timebase')
        tc_timebase.text = str(self.timebase)
        tc_ntsc = ET.SubElement(tc_rate, 'ntsc')
        tc_ntsc.text = 'TRUE' if self.is_ntsc else 'FALSE'
        
        tc_string = ET.SubElement(timecode, 'string')
        tc_string.text = '00:00:00:00'
        
        tc_frame = ET.SubElement(timecode, 'frame')
        tc_frame.text = '0'
        
        tc_displayformat = ET.SubElement(timecode, 'displayformat')
        tc_displayformat.text = 'NDF'
        
        # イン・アウト点
        seq_in = ET.SubElement(sequence, 'in')
        seq_in.text = '0'
        seq_out = ET.SubElement(sequence, 'out')
        seq_out.text = str(total_frames)
        
        # メディア
        media = ET.SubElement(sequence, 'media')
        
        # ビデオ
        video = ET.SubElement(media, 'video')
        
        # ビデオフォーマット
        format_elem = ET.SubElement(video, 'format')
        samplecharacteristics = ET.SubElement(format_elem, 'samplecharacteristics')
        
        v_rate = ET.SubElement(samplecharacteristics, 'rate')
        v_timebase = ET.SubElement(v_rate, 'timebase')
        v_timebase.text = str(self.timebase)
        v_ntsc = ET.SubElement(v_rate, 'ntsc')
        v_ntsc.text = 'TRUE' if self.is_ntsc else 'FALSE'
        
        width = ET.SubElement(samplecharacteristics, 'width')
        width.text = str(self.metadata['width'])
        
        height = ET.SubElement(samplecharacteristics, 'height')
        height.text = str(self.metadata['height'])
        
        anamorphic = ET.SubElement(samplecharacteristics, 'anamorphic')
        anamorphic.text = 'FALSE'
        
        pixelaspectratio = ET.SubElement(samplecharacteristics, 'pixelaspectratio')
        pixelaspectratio.text = 'square'
        
        fielddominance = ET.SubElement(samplecharacteristics, 'fielddominance')
        fielddominance.text = 'none'
        
        # ビデオトラック
        self._add_video_track(video, segments)
        
        # オーディオ
        audio = ET.SubElement(media, 'audio')
        
        # オーディオフォーマット
        audio_format = ET.SubElement(audio, 'format')
        audio_sc = ET.SubElement(audio_format, 'samplecharacteristics')
        
        depth = ET.SubElement(audio_sc, 'depth')
        depth.text = '16'
        
        samplerate = ET.SubElement(audio_sc, 'samplerate')
        samplerate.text = str(self.metadata.get('audio_sample_rate', 48000))
        
        # オーディオトラック
        self._add_audio_tracks(audio, segments)
        
        # XMLを整形して保存
        xml_str = self._prettify_xml(root)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE xmeml>\n')
            f.write(xml_str)
        
        print(f"動作確認済みPremiere Pro XMLを生成しました: {output_path}")
        return output_path
    
    def _add_video_track(self, video: ET.Element, segments: List[Tuple[float, float]]):
        """ビデオトラックを追加"""
        track = ET.SubElement(video, 'track')
        
        timeline_pos = 0
        
        for i, (start_sec, end_sec) in enumerate(segments):
            clipitem = ET.SubElement(track, 'clipitem')
            clipitem.set('id', f'clipitem-{i+1}')
            
            # マスタークリップID
            masterclipid = ET.SubElement(clipitem, 'masterclipid')
            masterclipid.text = f'masterclip-1'
            
            # 名前
            name = ET.SubElement(clipitem, 'name')
            name.text = Path(self.video_path).name
            
            # 継続時間
            clip_frames = int((end_sec - start_sec) * self.fps)
            duration = ET.SubElement(clipitem, 'duration')
            duration.text = str(clip_frames)
            
            # レート
            rate = ET.SubElement(clipitem, 'rate')
            timebase = ET.SubElement(rate, 'timebase')
            timebase.text = str(self.timebase)
            ntsc = ET.SubElement(rate, 'ntsc')
            ntsc.text = 'TRUE' if self.is_ntsc else 'FALSE'
            
            # タイムライン上の位置
            start_elem = ET.SubElement(clipitem, 'start')
            start_elem.text = str(timeline_pos)
            
            end_elem = ET.SubElement(clipitem, 'end')
            end_elem.text = str(timeline_pos + clip_frames)
            
            # ソース内の位置
            in_elem = ET.SubElement(clipitem, 'in')
            in_elem.text = str(int(start_sec * self.fps))
            
            out_elem = ET.SubElement(clipitem, 'out')
            out_elem.text = str(int(end_sec * self.fps))
            
            # ファイル
            file_elem = ET.SubElement(clipitem, 'file')
            file_elem.set('id', 'file-1')
            
            # ファイル名
            file_name = ET.SubElement(file_elem, 'name')
            file_name.text = Path(self.video_path).name
            
            # パスURL
            pathurl = ET.SubElement(file_elem, 'pathurl')
            abs_path = os.path.abspath(self.video_path)
            # macOSのパス形式
            pathurl.text = f"file://localhost{abs_path}"
            
            # メディア
            media = ET.SubElement(file_elem, 'media')
            
            # ビデオ
            video_elem = ET.SubElement(media, 'video')
            
            # 継続時間
            video_duration = ET.SubElement(video_elem, 'duration')
            video_duration.text = str(int(self.metadata['duration'] * self.fps))
            
            # オーディオ
            audio_elem = ET.SubElement(media, 'audio')
            
            timeline_pos += clip_frames
    
    def _add_audio_tracks(self, audio: ET.Element, segments: List[Tuple[float, float]]):
        """オーディオトラックを追加"""
        num_channels = self.metadata.get('audio_channels', 2)
        
        for ch in range(num_channels):
            track = ET.SubElement(audio, 'track')
            
            timeline_pos = 0
            
            for i, (start_sec, end_sec) in enumerate(segments):
                clipitem = ET.SubElement(track, 'clipitem')
                clipitem.set('id', f'clipitem-a{i+1}-ch{ch+1}')
                
                # マスタークリップID
                masterclipid = ET.SubElement(clipitem, 'masterclipid')
                masterclipid.text = f'masterclip-1'
                
                # 名前
                name = ET.SubElement(clipitem, 'name')
                name.text = Path(self.video_path).name
                
                # 継続時間
                clip_frames = int((end_sec - start_sec) * self.fps)
                duration = ET.SubElement(clipitem, 'duration')
                duration.text = str(clip_frames)
                
                # レート
                rate = ET.SubElement(clipitem, 'rate')
                timebase = ET.SubElement(rate, 'timebase')
                timebase.text = str(self.timebase)
                ntsc = ET.SubElement(rate, 'ntsc')
                ntsc.text = 'TRUE' if self.is_ntsc else 'FALSE'
                
                # タイムライン上の位置
                start_elem = ET.SubElement(clipitem, 'start')
                start_elem.text = str(timeline_pos)
                
                end_elem = ET.SubElement(clipitem, 'end')
                end_elem.text = str(timeline_pos + clip_frames)
                
                # ソース内の位置
                in_elem = ET.SubElement(clipitem, 'in')
                in_elem.text = str(int(start_sec * self.fps))
                
                out_elem = ET.SubElement(clipitem, 'out')
                out_elem.text = str(int(end_sec * self.fps))
                
                # ファイル
                file_elem = ET.SubElement(clipitem, 'file')
                file_elem.set('id', 'file-1')
                
                # ソーストラック
                sourcetrack = ET.SubElement(clipitem, 'sourcetrack')
                mediatype = ET.SubElement(sourcetrack, 'mediatype')
                mediatype.text = 'audio'
                trackindex = ET.SubElement(sourcetrack, 'trackindex')
                trackindex.text = str(ch + 1)
                
                timeline_pos += clip_frames
    
    def _prettify_xml(self, elem: ET.Element) -> str:
        """XMLを整形"""
        rough_string = ET.tostring(elem, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # 整形
        pretty_xml = reparsed.toprettyxml(indent='  ')
        
        # 空行を削除
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        
        # XML宣言とDOCTYPEを除外
        if lines[0].startswith('<?xml'):
            lines = lines[1:]
        
        return '\n'.join(lines)