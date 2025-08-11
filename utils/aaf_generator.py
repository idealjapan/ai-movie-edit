"""
AAF (Advanced Authoring Format) Generator for Premiere Pro
完全なメディアパス情報を含む高度なフォーマット
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import uuid
from datetime import datetime

class AAFGenerator:
    """AAFファイルを生成するクラス（簡易版）"""
    
    def __init__(self, video_path: str, segments: List[Dict], 
                 output_path: Optional[str] = None):
        self.video_path = Path(video_path).resolve()
        self.segments = segments
        
        if output_path is None:
            self.output_path = Path("output") / f"{self.video_path.stem}.aaf"
        else:
            self.output_path = Path(output_path)
        
        # メタデータ
        self.fps = 29.97
        self.creation_time = datetime.now().isoformat()
        
    def generate_xml_interchange(self) -> str:
        """Premiere Pro XML Interchange形式を生成（AAFの代替）"""
        # これはPremiere Proが直接読めるXML形式
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="5">
    <project>
        <name>{self.video_path.stem}_project</name>
        <children>
            <bin>
                <name>Media</name>
                <children>
                    <clip id="{self.video_path.stem}_master">
                        <name>{self.video_path.name}</name>
                        <duration>{int(self.segments[-1]['end'] * self.fps)}</duration>
                        <rate>
                            <timebase>{int(self.fps)}</timebase>
                            <ntsc>TRUE</ntsc>
                        </rate>
                        <media>
                            <video>
                                <track>
                                    <clipitem>
                                        <name>{self.video_path.name}</name>
                                        <file id="file-1">
                                            <name>{self.video_path.name}</name>
                                            <pathurl>file://{self.video_path.as_posix()}</pathurl>
                                        </file>
                                    </clipitem>
                                </track>
                            </video>
                            <audio>
                                <track>
                                    <clipitem>
                                        <file id="file-1"/>
                                    </clipitem>
                                </track>
                            </audio>
                        </media>
                    </clip>
                </children>
            </bin>
            <sequence>
                <name>{self.video_path.stem}_edited</name>
                <duration>{int(sum(s['end'] - s['start'] for s in self.segments) * self.fps)}</duration>
                <rate>
                    <timebase>{int(self.fps)}</timebase>
                    <ntsc>TRUE</ntsc>
                </rate>
                <media>
                    <video>
                        <format>
                            <samplecharacteristics>
                                <width>1920</width>
                                <height>1080</height>
                            </samplecharacteristics>
                        </format>
                        <track>"""
        
        # 各セグメントを追加
        timeline_position = 0
        for i, segment in enumerate(self.segments):
            start_frame = int(segment['start'] * self.fps)
            end_frame = int(segment['end'] * self.fps)
            duration = end_frame - start_frame
            
            xml_content += f"""
                            <clipitem id="clipitem-{i+1}">
                                <masterclipid>{self.video_path.stem}_master</masterclipid>
                                <name>{self.video_path.stem}</name>
                                <start>{timeline_position}</start>
                                <end>{timeline_position + duration}</end>
                                <in>{start_frame}</in>
                                <out>{end_frame}</out>
                                <file id="file-1">
                                    <name>{self.video_path.name}</name>
                                    <pathurl>file://{self.video_path.as_posix()}</pathurl>
                                </file>
                            </clipitem>"""
            
            timeline_position += duration
        
        xml_content += """
                        </track>
                    </video>
                    <audio>
                        <track>"""
        
        # オーディオトラックも同様に追加
        timeline_position = 0
        for i, segment in enumerate(self.segments):
            start_frame = int(segment['start'] * self.fps)
            end_frame = int(segment['end'] * self.fps)
            duration = end_frame - start_frame
            
            xml_content += f"""
                            <clipitem id="clipitem-a{i+1}">
                                <masterclipid>{self.video_path.stem}_master</masterclipid>
                                <name>{self.video_path.stem}</name>
                                <start>{timeline_position}</start>
                                <end>{timeline_position + duration}</end>
                                <in>{start_frame}</in>
                                <out>{end_frame}</out>
                                <file id="file-1"/>
                            </clipitem>"""
            
            timeline_position += duration
        
        xml_content += """
                        </track>
                    </audio>
                </media>
            </sequence>
        </children>
    </project>
</xmeml>"""
        
        return xml_content
    
    def save(self):
        """XMLファイルとして保存"""
        os.makedirs(self.output_path.parent, exist_ok=True)
        
        # 拡張子を.xmlに変更
        xml_path = self.output_path.with_suffix('.xml')
        
        xml_content = self.generate_xml_interchange()
        
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"Premiere Pro XML saved to: {xml_path}")
        
        # メディアリンク情報を別ファイルに保存
        link_info = {
            "video_file": str(self.video_path),
            "xml_file": str(xml_path),
            "segments": len(self.segments),
            "total_duration": sum(s['end'] - s['start'] for s in self.segments),
            "created": self.creation_time
        }
        
        info_path = xml_path.with_suffix('.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(link_info, f, indent=2, ensure_ascii=False)
        
        return str(xml_path)