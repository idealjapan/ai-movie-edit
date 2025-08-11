"""
究極版 Premiere Pro XML生成モジュール
リサーチの知見をフル活用した完全なFCP7 XML (xmeml) 生成

主な特徴:
1. 完全な階層構造による読みやすいXML
2. テロップ/タイトルの完全サポート
3. 精密な時間計算（pproTicksとフレームレート対応）
4. メタデータの完全な記述
5. リンク情報による映像と音声の同期
"""
import os
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Union
from xml.etree import ElementTree as ET
from xml.dom import minidom
import urllib.parse
from fractions import Fraction
import math

from .video_metadata import VideoMetadataExtractor
from .ppro_time_utils import PproTimeCalculator, create_calculator_from_metadata


class PremiereXMLGeneratorUltimate:
    """究極版 Premiere Pro用XML生成クラス"""
    
    # Premiere Proで使用される標準的なビデオフォーマット
    VIDEO_FORMATS = {
        (1920, 1080, 29.97): "1080i_2997",
        (1920, 1080, 25): "1080i_25",
        (1920, 1080, 23.976): "1080p_2398",
        (1920, 1080, 24): "1080p_24",
        (1920, 1080, 30): "1080p_30",
        (1280, 720, 29.97): "720p_2997",
        (1280, 720, 25): "720p_25",
        (1280, 720, 23.976): "720p_2398",
        (1280, 720, 60): "720p_60",
        (1280, 720, 59.94): "720p_5994",
    }
    
    # テロップのデフォルトスタイル
    DEFAULT_CAPTION_STYLE = {
        'font': 'Arial',
        'fontsize': 48,
        'fontcolor': {'red': 255, 'green': 255, 'blue': 255, 'alpha': 255},  # 白
        'bold': True,
        'italic': False,
        'underline': False,
        'position': {'x': 0.0, 'y': -0.85},  # 下部中央
        'alignment': 'center',
        'shadow': True,
        'shadow_color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 200},
        'shadow_offset': {'x': 2, 'y': 2},
        'shadow_blur': 4,
        'outline': True,
        'outline_color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 255},
        'outline_width': 2,
        'background': True,
        'background_color': {'red': 0, 'green': 0, 'blue': 0, 'alpha': 128},
        'background_padding': 10
    }
    
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
        
        # ID管理
        self.id_counter = 0
        self.uuid_cache = {}
        
        # マスターリソース
        self.master_clip_id = self._generate_id("masterclip")
        self.sequence_id = self._generate_id("sequence")
        self.project_id = self._generate_id("project")
        
        # ビデオフォーマットを決定
        self.video_format = self._determine_video_format()
        
    def generate_xml(self, 
                    segments: List[Tuple[float, float]], 
                    output_path: str,
                    captions: Optional[List[Dict]] = None,
                    caption_style: Optional[Dict] = None) -> str:
        """
        究極のXMLを生成
        
        Args:
            segments: 保持するセグメントのリスト [(start_sec, end_sec), ...]
            output_path: 出力ファイルパス
            captions: キャプションデータ [{"text": str, "start": float, "end": float}, ...]
            caption_style: キャプションのスタイル設定（オプション）
            
        Returns:
            生成したXMLファイルのパス
        """
        # スタイルのマージ
        if caption_style:
            style = {**self.DEFAULT_CAPTION_STYLE, **caption_style}
        else:
            style = self.DEFAULT_CAPTION_STYLE
        
        # XMLドキュメントを構築
        xmeml = self._build_complete_xml(segments, captions, style)
        
        # XMLを整形して保存
        self._save_formatted_xml(xmeml, output_path)
        
        print(f"究極版 Premiere Pro XMLを生成しました: {output_path}")
        print(f"- セグメント数: {len(segments)}")
        print(f"- 総時間: {sum(end - start for start, end in segments):.2f}秒")
        if captions:
            print(f"- キャプション数: {len(captions)}")
        
        return output_path
    
    def _build_complete_xml(self, 
                           segments: List[Tuple[float, float]], 
                           captions: Optional[List[Dict]],
                           caption_style: Dict) -> ET.Element:
        """完全なXMLドキュメントを構築"""
        # ルート要素
        xmeml = ET.Element('xmeml')
        xmeml.set('version', '4')
        
        # プロジェクト
        project = ET.SubElement(xmeml, 'project')
        self._build_project_structure(project, segments, captions, caption_style)
        
        return xmeml
    
    def _build_project_structure(self, 
                               project: ET.Element, 
                               segments: List[Tuple[float, float]],
                               captions: Optional[List[Dict]],
                               caption_style: Dict):
        """プロジェクト構造を構築"""
        # プロジェクトメタデータ
        self._add_text_element(project, 'name', f"{self.video_name}_project")
        self._add_text_element(project, 'uuid', self.project_id)
        
        # 子要素コンテナ
        children = ET.SubElement(project, 'children')
        
        # ビン構造（整理のため）
        bin_elem = self._create_bin(children, "Media")
        
        # マスタークリップ
        self._create_complete_master_clip(bin_elem)
        
        # シーケンス
        self._create_complete_sequence(children, segments, captions, caption_style)
    
    def _create_bin(self, parent: ET.Element, name: str) -> ET.Element:
        """ビン（フォルダ）を作成"""
        bin_elem = ET.SubElement(parent, 'bin')
        self._add_text_element(bin_elem, 'name', name)
        self._add_text_element(bin_elem, 'uuid', self._generate_id(f"bin_{name}"))
        
        children = ET.SubElement(bin_elem, 'children')
        return children
    
    def _create_complete_master_clip(self, parent: ET.Element):
        """完全なマスタークリップを作成"""
        clip = ET.SubElement(parent, 'clip')
        clip.set('id', self.master_clip_id)
        clip.set('frameBlend', 'FALSE')
        
        # クリップメタデータ
        self._add_text_element(clip, 'uuid', self.master_clip_id)
        self._add_text_element(clip, 'masterclipid', self.master_clip_id)
        self._add_text_element(clip, 'ismasterclip', 'TRUE')
        self._add_text_element(clip, 'name', Path(self.video_path).name)
        
        # 継続時間
        duration_ticks = self.time_calc.seconds_to_ticks(self.metadata['duration'])
        self._add_text_element(clip, 'duration', str(duration_ticks))
        
        # レート情報
        self._add_rate_element(clip, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # イン・アウト点
        self._add_text_element(clip, 'in', '0')
        self._add_text_element(clip, 'out', str(duration_ticks))
        
        # メディア情報
        media = ET.SubElement(clip, 'media')
        self._create_video_media_info(media)
        self._create_audio_media_info(media)
        
        # ファイル情報
        self._create_file_info(clip)
        
        # カラー情報
        self._add_color_info(clip)
        
        # ログ情報
        logginginfo = ET.SubElement(clip, 'logginginfo')
        self._add_text_element(logginginfo, 'description', f"Source: {Path(self.video_path).name}")
        self._add_text_element(logginginfo, 'scene', '')
        self._add_text_element(logginginfo, 'shottake', '')
        self._add_text_element(logginginfo, 'lognote', '')
    
    def _create_complete_sequence(self, 
                                parent: ET.Element, 
                                segments: List[Tuple[float, float]],
                                captions: Optional[List[Dict]],
                                caption_style: Dict):
        """完全なシーケンスを作成"""
        sequence = ET.SubElement(parent, 'sequence')
        sequence.set('id', self.sequence_id)
        sequence.set('TL.SQVideoRenderCodec', 'H.264')
        sequence.set('TL.SQVideoRenderQuality', 'Max')
        sequence.set('TL.SQAudioRenderCodec', 'CODEC_ID_LPCM')
        
        # シーケンスメタデータ
        self._add_text_element(sequence, 'uuid', self.sequence_id)
        self._add_text_element(sequence, 'name', f"{self.video_name}_edited")
        
        # 総継続時間
        total_duration = sum(end - start for start, end in segments)
        duration_ticks = self.time_calc.seconds_to_ticks(total_duration)
        self._add_text_element(sequence, 'duration', str(duration_ticks))
        
        # レート情報
        self._add_rate_element(sequence, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # タイムコード情報
        self._add_timecode_info(sequence)
        
        # イン・アウト点
        self._add_text_element(sequence, 'in', '-1')
        self._add_text_element(sequence, 'out', '-1')
        
        # メディア
        media = ET.SubElement(sequence, 'media')
        
        # ビデオトラック
        video = ET.SubElement(media, 'video')
        self._add_text_element(video, 'numOutputChannels', '1')
        
        # フォーマット情報
        video_format = ET.SubElement(video, 'format')
        self._add_sequence_format_info(video_format)
        
        # トラック構造
        # V1: メインビデオ
        self._create_main_video_track(video, segments)
        
        # V2: キャプション（必要な場合）
        if captions:
            self._create_caption_track(video, captions, caption_style)
        
        # オーディオトラック
        audio = ET.SubElement(media, 'audio')
        self._add_text_element(audio, 'numOutputChannels', str(self.metadata['audio_channels']))
        
        # オーディオフォーマット
        audio_format = ET.SubElement(audio, 'format')
        self._add_audio_format_info(audio_format)
        
        # オーディオトラック
        self._create_audio_tracks(audio, segments)
    
    def _create_main_video_track(self, parent: ET.Element, segments: List[Tuple[float, float]]):
        """メインビデオトラック（V1）を作成"""
        track = ET.SubElement(parent, 'track')
        track.set('TL.SQTrackShy', '0')
        track.set('TL.SQTrackExpandedHeight', '25')
        track.set('TL.SQTrackExpanded', '0')
        track.set('MZ.TrackTargeted', '1')
        track.set('PannerCurrentValue', '0.5')
        track.set('PannerIsInverted', '0')
        track.set('PannerName', 'Balance')
        track.set('currentExplodedTrackIndex', '0')
        track.set('totalExplodedTrackCount', '1')
        track.set('premiereTrackType', 'DMX')
        
        # トラック属性
        self._add_text_element(track, 'enabled', 'TRUE')
        self._add_text_element(track, 'locked', 'FALSE')
        
        # クリップを配置
        timeline_position = 0
        
        for i, (start_sec, end_sec) in enumerate(segments):
            clip_duration = end_sec - start_sec
            
            # クリップアイテム
            clipitem = self._create_video_clipitem(
                track=track,
                index=i + 1,
                timeline_start=timeline_position,
                clip_duration=clip_duration,
                source_start=start_sec,
                source_end=end_sec
            )
            
            timeline_position += clip_duration
    
    def _create_video_clipitem(self, 
                             track: ET.Element,
                             index: int,
                             timeline_start: float,
                             clip_duration: float,
                             source_start: float,
                             source_end: float) -> ET.Element:
        """ビデオクリップアイテムを作成"""
        clipitem = ET.SubElement(track, 'clipitem')
        clipitem.set('id', self._generate_id(f"clipitem_v{index}"))
        clipitem.set('frameBlend', 'FALSE')
        
        # クリップ情報
        self._add_text_element(clipitem, 'masterclipid', self.master_clip_id)
        self._add_text_element(clipitem, 'name', f"{Path(self.video_path).name}")
        self._add_text_element(clipitem, 'enabled', 'TRUE')
        
        # 時間情報
        duration_ticks = self.time_calc.seconds_to_ticks(clip_duration)
        self._add_text_element(clipitem, 'duration', str(duration_ticks))
        
        # レート
        self._add_rate_element(clipitem, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # タイムライン上の位置
        start_ticks = self.time_calc.seconds_to_ticks(timeline_start)
        end_ticks = self.time_calc.seconds_to_ticks(timeline_start + clip_duration)
        self._add_text_element(clipitem, 'start', str(start_ticks))
        self._add_text_element(clipitem, 'end', str(end_ticks))
        
        # ソース内の位置
        in_ticks = self.time_calc.seconds_to_ticks(source_start)
        out_ticks = self.time_calc.seconds_to_ticks(source_end)
        self._add_text_element(clipitem, 'in', str(in_ticks))
        self._add_text_element(clipitem, 'out', str(out_ticks))
        
        # pproTicksフィールド
        self._add_text_element(clipitem, 'pproTicksIn', str(in_ticks))
        self._add_text_element(clipitem, 'pproTicksOut', str(out_ticks))
        
        # ファイル参照
        file_elem = ET.SubElement(clipitem, 'file')
        file_elem.set('id', self.master_clip_id)
        
        # ソーストラック
        sourcetrack = ET.SubElement(clipitem, 'sourcetrack')
        self._add_text_element(sourcetrack, 'mediatype', 'video')
        self._add_text_element(sourcetrack, 'trackindex', '1')
        
        # リンク情報（オーディオとのリンク）
        link = ET.SubElement(clipitem, 'link')
        self._add_text_element(link, 'linkclipref', self._generate_id(f"clipitem_a{index}"))
        self._add_text_element(link, 'mediatype', 'audio')
        self._add_text_element(link, 'trackindex', '1')
        self._add_text_element(link, 'clipindex', str(index))
        self._add_text_element(link, 'groupindex', '1')
        
        # フィルター（エフェクト）
        self._add_default_video_filters(clipitem)
        
        return clipitem
    
    def _create_caption_track(self, 
                            parent: ET.Element, 
                            captions: List[Dict],
                            caption_style: Dict):
        """キャプショントラック（V2）を作成"""
        track = ET.SubElement(parent, 'track')
        track.set('TL.SQTrackShy', '0')
        track.set('TL.SQTrackExpandedHeight', '25')
        track.set('TL.SQTrackExpanded', '0')
        track.set('MZ.TrackTargeted', '0')
        track.set('currentExplodedTrackIndex', '0')
        track.set('totalExplodedTrackCount', '1')
        track.set('premiereTrackType', 'DMX')
        
        # トラック属性
        self._add_text_element(track, 'enabled', 'TRUE')
        self._add_text_element(track, 'locked', 'FALSE')
        
        # 各キャプションをタイトルクリップとして配置
        for i, caption in enumerate(captions):
            self._create_title_clipitem(
                track=track,
                index=i + 1,
                text=caption['text'],
                start_time=caption['start'],
                end_time=caption['end'],
                style=caption_style
            )
    
    def _create_title_clipitem(self,
                             track: ET.Element,
                             index: int,
                             text: str,
                             start_time: float,
                             end_time: float,
                             style: Dict) -> ET.Element:
        """タイトルクリップアイテムを作成"""
        clipitem = ET.SubElement(track, 'clipitem')
        clipitem.set('id', self._generate_id(f"title_{index}"))
        clipitem.set('frameBlend', 'FALSE')
        
        # 基本情報
        self._add_text_element(clipitem, 'name', f'Caption {index}')
        self._add_text_element(clipitem, 'enabled', 'TRUE')
        
        # 時間情報
        duration = end_time - start_time
        duration_ticks = self.time_calc.seconds_to_ticks(duration)
        self._add_text_element(clipitem, 'duration', str(duration_ticks))
        
        # レート
        self._add_rate_element(clipitem, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # タイムライン上の位置
        start_ticks = self.time_calc.seconds_to_ticks(start_time)
        end_ticks = self.time_calc.seconds_to_ticks(end_time)
        self._add_text_element(clipitem, 'start', str(start_ticks))
        self._add_text_element(clipitem, 'end', str(end_ticks))
        
        # タイトルエフェクト
        effect = ET.SubElement(clipitem, 'effect')
        self._add_text_element(effect, 'name', 'Text')
        self._add_text_element(effect, 'effectid', 'Text')
        self._add_text_element(effect, 'effectcategory', 'Text')
        self._add_text_element(effect, 'effecttype', 'generator')
        self._add_text_element(effect, 'mediatype', 'video')
        
        # ワイプ設定
        wipecode = ET.SubElement(effect, 'wipecode')
        self._add_text_element(wipecode, 'value', '0')
        wipeaccuracy = ET.SubElement(effect, 'wipeaccuracy')
        self._add_text_element(wipeaccuracy, 'value', '100')
        aset = ET.SubElement(effect, 'aset')
        bset = ET.SubElement(effect, 'bset')
        
        # パラメータ
        self._add_title_parameters(effect, text, style)
        
        return clipitem
    
    def _add_title_parameters(self, effect: ET.Element, text: str, style: Dict):
        """タイトルエフェクトのパラメータを追加"""
        # テキスト内容
        param_text = self._create_parameter(effect, 'str', 'Text', 'string')
        self._add_text_element(param_text, 'value', text)
        
        # フォント
        param_font = self._create_parameter(effect, 'font', 'Font', 'font')
        self._add_text_element(param_font, 'value', style['font'])
        
        # フォントサイズ
        param_size = self._create_parameter(effect, 'fontsize', 'Font Size', 'int16')
        self._add_text_element(param_size, 'value', str(style['fontsize']))
        
        # フォントスタイル
        param_style = self._create_parameter(effect, 'fontstyle', 'Font Style', 'int16')
        style_value = 0
        if style['bold']:
            style_value += 1
        if style['italic']:
            style_value += 2
        if style['underline']:
            style_value += 4
        self._add_text_element(param_style, 'value', str(style_value))
        
        # フォントカラー
        param_color = self._create_parameter(effect, 'fontcolor', 'Font Color', 'color')
        self._add_color_value(param_color, style['fontcolor'])
        
        # 位置
        param_center = self._create_parameter(effect, 'center', 'Center', 'point')
        self._add_point_keyframe(param_center, 0, style['position']['x'], style['position']['y'])
        
        # 整列
        param_align = self._create_parameter(effect, 'justify', 'Justify', 'int16')
        align_values = {'left': 0, 'center': 1, 'right': 2}
        self._add_text_element(param_align, 'value', str(align_values.get(style['alignment'], 1)))
        
        # ドロップシャドウ
        if style.get('shadow', False):
            param_shadow = self._create_parameter(effect, 'dropshadow', 'Drop Shadow', 'bool')
            self._add_text_element(param_shadow, 'value', 'TRUE')
            
            # シャドウカラー
            param_shadow_color = self._create_parameter(effect, 'shadowcolor', 'Shadow Color', 'color')
            self._add_color_value(param_shadow_color, style['shadow_color'])
            
            # シャドウオフセット
            param_shadow_offset = self._create_parameter(effect, 'shadowoffset', 'Shadow Offset', 'point')
            self._add_point_keyframe(param_shadow_offset, 0, 
                                   style['shadow_offset']['x'], 
                                   style['shadow_offset']['y'])
            
            # シャドウソフトネス
            param_shadow_soft = self._create_parameter(effect, 'shadowsoftness', 'Shadow Softness', 'int16')
            self._add_text_element(param_shadow_soft, 'value', str(style['shadow_blur']))
        
        # アウトライン（ストローク）
        if style.get('outline', False):
            param_outline = self._create_parameter(effect, 'strokewidth', 'Stroke Width', 'int16')
            self._add_text_element(param_outline, 'value', str(style['outline_width']))
            
            param_outline_color = self._create_parameter(effect, 'strokecolor', 'Stroke Color', 'color')
            self._add_color_value(param_outline_color, style['outline_color'])
        
        # 背景
        if style.get('background', False):
            param_bg = self._create_parameter(effect, 'background', 'Background', 'bool')
            self._add_text_element(param_bg, 'value', 'TRUE')
            
            param_bg_color = self._create_parameter(effect, 'bgcolor', 'Background Color', 'color')
            self._add_color_value(param_bg_color, style['background_color'])
            
            param_bg_pad = self._create_parameter(effect, 'bgpadding', 'Background Padding', 'int16')
            self._add_text_element(param_bg_pad, 'value', str(style['background_padding']))
    
    def _create_audio_tracks(self, parent: ET.Element, segments: List[Tuple[float, float]]):
        """オーディオトラックを作成"""
        # ステレオの場合、2つのトラックを作成
        for channel in range(self.metadata['audio_channels']):
            track = ET.SubElement(parent, 'track')
            track.set('TL.SQTrackShy', '0')
            track.set('TL.SQTrackExpandedHeight', '25')
            track.set('TL.SQTrackExpanded', '0')
            track.set('MZ.TrackTargeted', '1' if channel == 0 else '0')
            track.set('PannerCurrentValue', '0.5')
            track.set('PannerIsInverted', '0')
            track.set('PannerName', 'Balance')
            track.set('currentExplodedTrackIndex', '0')
            track.set('totalExplodedTrackCount', '1')
            track.set('premiereTrackType', 'DMX')
            
            # トラック属性
            self._add_text_element(track, 'enabled', 'TRUE')
            self._add_text_element(track, 'locked', 'FALSE')
            self._add_text_element(track, 'outputchannelindex', str(channel))
            
            # クリップを配置
            timeline_position = 0
            
            for i, (start_sec, end_sec) in enumerate(segments):
                clip_duration = end_sec - start_sec
                
                # オーディオクリップアイテム
                clipitem = self._create_audio_clipitem(
                    track=track,
                    index=i + 1,
                    channel=channel + 1,
                    timeline_start=timeline_position,
                    clip_duration=clip_duration,
                    source_start=start_sec,
                    source_end=end_sec
                )
                
                timeline_position += clip_duration
    
    def _create_audio_clipitem(self,
                              track: ET.Element,
                              index: int,
                              channel: int,
                              timeline_start: float,
                              clip_duration: float,
                              source_start: float,
                              source_end: float) -> ET.Element:
        """オーディオクリップアイテムを作成"""
        clipitem = ET.SubElement(track, 'clipitem')
        clipitem.set('id', self._generate_id(f"clipitem_a{index}_ch{channel}"))
        clipitem.set('frameBlend', 'FALSE')
        
        # クリップ情報
        self._add_text_element(clipitem, 'masterclipid', self.master_clip_id)
        self._add_text_element(clipitem, 'name', f"{Path(self.video_path).name}")
        self._add_text_element(clipitem, 'enabled', 'TRUE')
        
        # 時間情報
        duration_ticks = self.time_calc.seconds_to_ticks(clip_duration)
        self._add_text_element(clipitem, 'duration', str(duration_ticks))
        
        # レート
        self._add_rate_element(clipitem, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # タイムライン上の位置
        start_ticks = self.time_calc.seconds_to_ticks(timeline_start)
        end_ticks = self.time_calc.seconds_to_ticks(timeline_start + clip_duration)
        self._add_text_element(clipitem, 'start', str(start_ticks))
        self._add_text_element(clipitem, 'end', str(end_ticks))
        
        # ソース内の位置
        in_ticks = self.time_calc.seconds_to_ticks(source_start)
        out_ticks = self.time_calc.seconds_to_ticks(source_end)
        self._add_text_element(clipitem, 'in', str(in_ticks))
        self._add_text_element(clipitem, 'out', str(out_ticks))
        
        # ファイル参照
        file_elem = ET.SubElement(clipitem, 'file')
        file_elem.set('id', self.master_clip_id)
        
        # ソーストラック
        sourcetrack = ET.SubElement(clipitem, 'sourcetrack')
        self._add_text_element(sourcetrack, 'mediatype', 'audio')
        self._add_text_element(sourcetrack, 'trackindex', str(channel))
        
        # リンク情報（ビデオとのリンク、チャンネル1のみ）
        if channel == 1:
            link = ET.SubElement(clipitem, 'link')
            self._add_text_element(link, 'linkclipref', self._generate_id(f"clipitem_v{index}"))
            self._add_text_element(link, 'mediatype', 'video')
            self._add_text_element(link, 'trackindex', '1')
            self._add_text_element(link, 'clipindex', str(index))
            self._add_text_element(link, 'groupindex', '1')
        
        # オーディオフィルター
        self._add_default_audio_filters(clipitem)
        
        return clipitem
    
    # ヘルパーメソッド群
    def _generate_id(self, prefix: str) -> str:
        """一意のIDを生成"""
        if prefix not in self.uuid_cache:
            self.uuid_cache[prefix] = str(uuid.uuid4())
        return self.uuid_cache[prefix]
    
    def _add_text_element(self, parent: ET.Element, tag: str, text: str) -> ET.Element:
        """テキスト要素を追加"""
        elem = ET.SubElement(parent, tag)
        elem.text = text
        return elem
    
    def _add_rate_element(self, parent: ET.Element, tag: str, timebase: int, is_ntsc: bool):
        """レート要素を追加"""
        rate = ET.SubElement(parent, tag)
        self._add_text_element(rate, 'timebase', str(timebase))
        self._add_text_element(rate, 'ntsc', str(is_ntsc).upper())
    
    def _add_timecode_info(self, parent: ET.Element):
        """タイムコード情報を追加"""
        timecode = ET.SubElement(parent, 'timecode')
        self._add_rate_element(timecode, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        self._add_text_element(timecode, 'string', '00:00:00:00')
        self._add_text_element(timecode, 'frame', '0')
        self._add_text_element(timecode, 'displayformat', 'NDF')
        self._add_text_element(timecode, 'source', 'source')
    
    def _create_video_media_info(self, media: ET.Element):
        """ビデオメディア情報を作成"""
        video = ET.SubElement(media, 'video')
        
        # ビデオトラック
        for i in range(1):  # 1トラックのみ
            track = ET.SubElement(video, 'track')
            
            # ビデオフォーマット
            format_elem = ET.SubElement(video, 'format')
            sc = ET.SubElement(format_elem, 'samplecharacteristics')
            
            # 解像度
            self._add_text_element(sc, 'width', str(self.metadata['width']))
            self._add_text_element(sc, 'height', str(self.metadata['height']))
            
            # コーデック
            codec = ET.SubElement(sc, 'codec')
            self._add_text_element(codec, 'name', self.metadata.get('codec_name', 'H.264'))
            appspecificdata = ET.SubElement(codec, 'appspecificdata')
            
            # ピクセルアスペクト比
            self._add_text_element(sc, 'pixelaspectratio', 'square')
            
            # フィールド
            self._add_text_element(sc, 'fielddominance', 'none')
            
            # フレームレート
            self._add_rate_element(sc, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
            
            # カラースペース
            self._add_text_element(sc, 'colordepth', '24')
    
    def _create_audio_media_info(self, media: ET.Element):
        """オーディオメディア情報を作成"""
        audio = ET.SubElement(media, 'audio')
        
        # オーディオトラック（チャンネル数分）
        for channel in range(self.metadata['audio_channels']):
            track = ET.SubElement(audio, 'track')
            
        # オーディオフォーマット
        format_elem = ET.SubElement(audio, 'format')
        sc = ET.SubElement(format_elem, 'samplecharacteristics')
        
        # オーディオ特性
        self._add_text_element(sc, 'depth', '16')
        self._add_text_element(sc, 'samplerate', str(self.metadata['audio_sample_rate']))
        self._add_text_element(sc, 'channelcount', str(self.metadata['audio_channels']))
    
    def _create_file_info(self, clip: ET.Element):
        """ファイル情報を作成"""
        file_elem = ET.SubElement(clip, 'file')
        file_elem.set('id', self.master_clip_id)
        
        # ファイル名
        self._add_text_element(file_elem, 'name', Path(self.video_path).name)
        
        # パスURL
        self._add_text_element(file_elem, 'pathurl', self._create_file_url(self.video_path))
        
        # レート
        self._add_rate_element(file_elem, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # メディア情報
        media = ET.SubElement(file_elem, 'media')
        self._create_video_media_info(media)
        self._create_audio_media_info(media)
    
    def _add_color_info(self, clip: ET.Element):
        """カラー情報を追加"""
        colorinfo = ET.SubElement(clip, 'colorinfo')
        
        # カラースペース
        colorspace = ET.SubElement(colorinfo, 'colorspace')
        
        # 輝度レベル
        lum = ET.SubElement(colorspace, 'lum')
        self._add_text_element(lum, 'min', '16')
        self._add_text_element(lum, 'max', '235')
        
        # クロマレベル
        chr = ET.SubElement(colorspace, 'chr')
        self._add_text_element(chr, 'min', '16')
        self._add_text_element(chr, 'max', '240')
    
    def _add_sequence_format_info(self, format_elem: ET.Element):
        """シーケンスのフォーマット情報を追加"""
        sc = ET.SubElement(format_elem, 'samplecharacteristics')
        
        # 解像度
        self._add_text_element(sc, 'width', str(self.metadata['width']))
        self._add_text_element(sc, 'height', str(self.metadata['height']))
        
        # ピクセルアスペクト比
        self._add_text_element(sc, 'pixelaspectratio', 'square')
        
        # フィールド
        self._add_text_element(sc, 'fielddominance', 'none')
        
        # フレームレート
        self._add_rate_element(sc, 'rate', self.time_calc.timebase, self.metadata['is_ntsc'])
        
        # カラー
        self._add_text_element(sc, 'colordepth', '24')
        
        # コーデック
        codec = ET.SubElement(sc, 'codec')
        self._add_text_element(codec, 'name', 'Apple ProRes 422')
        appspecificdata = ET.SubElement(codec, 'appspecificdata')
    
    def _add_audio_format_info(self, format_elem: ET.Element):
        """オーディオフォーマット情報を追加"""
        sc = ET.SubElement(format_elem, 'samplecharacteristics')
        
        # オーディオ特性
        self._add_text_element(sc, 'depth', '16')
        self._add_text_element(sc, 'samplerate', str(self.metadata['audio_sample_rate']))
    
    def _create_parameter(self, parent: ET.Element, param_id: str, name: str, value_type: str) -> ET.Element:
        """パラメータ要素を作成"""
        param = ET.SubElement(parent, 'parameter')
        self._add_text_element(param, 'parameterid', param_id)
        self._add_text_element(param, 'name', name)
        self._add_text_element(param, 'valuetype', value_type)
        return param
    
    def _add_color_value(self, param: ET.Element, color: Dict):
        """カラー値を追加"""
        value = ET.SubElement(param, 'value')
        self._add_text_element(value, 'red', str(color['red']))
        self._add_text_element(value, 'green', str(color['green']))
        self._add_text_element(value, 'blue', str(color['blue']))
        self._add_text_element(value, 'alpha', str(color['alpha']))
    
    def _add_point_keyframe(self, param: ET.Element, when: int, x: float, y: float):
        """ポイント（位置）のキーフレームを追加"""
        keyframe = ET.SubElement(param, 'keyframe')
        self._add_text_element(keyframe, 'when', str(when))
        value = ET.SubElement(keyframe, 'value')
        self._add_text_element(value, 'horiz', str(x))
        self._add_text_element(value, 'vert', str(y))
    
    def _add_default_video_filters(self, clipitem: ET.Element):
        """デフォルトのビデオフィルターを追加"""
        # 基本的なモーションフィルター
        filter_elem = ET.SubElement(clipitem, 'filter')
        effect = ET.SubElement(filter_elem, 'effect')
        self._add_text_element(effect, 'name', 'Basic Motion')
        self._add_text_element(effect, 'effectid', 'basic')
        self._add_text_element(effect, 'effectcategory', 'motion')
        self._add_text_element(effect, 'effecttype', 'motion')
        self._add_text_element(effect, 'mediatype', 'video')
        
        # スケール
        param_scale = self._create_parameter(effect, 'scale', 'Scale', 'int16')
        self._add_text_element(param_scale, 'value', '100')
        
        # 回転
        param_rotation = self._create_parameter(effect, 'rotation', 'Rotation', 'int16')
        self._add_text_element(param_rotation, 'value', '0')
        
        # 位置
        param_center = self._create_parameter(effect, 'center', 'Center', 'point')
        self._add_point_keyframe(param_center, 0, 0.0, 0.0)
    
    def _add_default_audio_filters(self, clipitem: ET.Element):
        """デフォルトのオーディオフィルターを追加"""
        # オーディオレベルフィルター
        filter_elem = ET.SubElement(clipitem, 'filter')
        effect = ET.SubElement(filter_elem, 'effect')
        self._add_text_element(effect, 'name', 'Audio Levels')
        self._add_text_element(effect, 'effectid', 'audiolevels')
        self._add_text_element(effect, 'effectcategory', 'audiolevels')
        self._add_text_element(effect, 'effecttype', 'audiolevels')
        self._add_text_element(effect, 'mediatype', 'audio')
        
        # レベル
        param_level = self._create_parameter(effect, 'level', 'Level', 'int16')
        self._add_text_element(param_level, 'value', '0')
    
    def _determine_video_format(self) -> str:
        """ビデオフォーマットを決定"""
        width = self.metadata['width']
        height = self.metadata['height']
        fps = self.metadata['fps']
        
        # 最も近いフォーマットを見つける
        key = (width, height, round(fps, 2))
        if key in self.VIDEO_FORMATS:
            return self.VIDEO_FORMATS[key]
        
        # デフォルト
        return f"{width}x{height}_{int(fps)}fps"
    
    def _create_file_url(self, file_path: str) -> str:
        """ファイルパスをPremiere Pro用のURLに変換"""
        abs_path = os.path.abspath(file_path)
        
        if os.name == 'nt':
            # Windows
            url_path = abs_path.replace('\\', '/')
            return f"file://localhost/{url_path}"
        else:
            # macOS/Linux - 日本語パスはエンコードしない
            # Premiere Proは生のパスを期待する
            return f"file://localhost{abs_path}"
    
    def _save_formatted_xml(self, elem: ET.Element, output_path: str):
        """整形されたXMLをファイルに保存"""
        # インデントを適用して読みやすく
        self._indent_xml(elem)
        
        # XMLを文字列に変換
        xml_string = ET.tostring(elem, encoding='unicode', method='xml')
        
        # minidomで再整形（さらに読みやすく）
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent='  ', encoding=None)
        
        # 余分な空行を削除
        lines = pretty_xml.split('\n')
        lines = [line.rstrip() for line in lines if line.strip()]
        
        # XML宣言を除外
        if lines[0].startswith('<?xml'):
            lines = lines[1:]
        
        # 最終的なXML
        final_xml = '\n'.join(lines)
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # ファイルに保存
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<!DOCTYPE xmeml>\n')
            f.write(final_xml)
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """XML要素にインデントを追加（再帰的）"""
        indent = "\n" + "  " * level
        
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent