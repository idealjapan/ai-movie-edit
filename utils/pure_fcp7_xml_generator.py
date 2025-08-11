"""
Pure FCP7 XML Generator for Adobe Premiere Pro
Generates standard FCP7 XML without Premiere-specific extensions
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from fractions import Fraction

class PureFCP7XMLGenerator:
    """Generate pure FCP7 XML compatible with Adobe Premiere Pro"""
    
    def __init__(self, video_path: str, segments: List[Dict], 
                 captions: Optional[List[Dict]] = None,
                 output_path: Optional[str] = None):
        self.video_path = Path(video_path).resolve()
        self.segments = segments
        self.captions = captions or []
        
        # Default output path
        if output_path is None:
            self.output_path = Path("output") / f"{self.video_path.stem}_pure_fcp7.xml"
        else:
            self.output_path = Path(output_path)
        
        # Video metadata (will be filled by analyze_video)
        self.width = 1920
        self.height = 1080
        self.fps = 29.97
        self.duration_seconds = 0
        self.timebase = 30
        self.ntsc = True
        
    def analyze_video(self, metadata: Dict):
        """Analyze video metadata"""
        self.width = metadata.get('width', 1920)
        self.height = metadata.get('height', 1080)
        self.fps = metadata.get('fps', 29.97)
        self.duration_seconds = metadata.get('duration', 0)
        
        # Determine timebase and NTSC flag
        if abs(self.fps - 23.976) < 0.01:
            self.timebase = 24
            self.ntsc = True
        elif abs(self.fps - 29.97) < 0.01:
            self.timebase = 30
            self.ntsc = True
        elif abs(self.fps - 59.94) < 0.01:
            self.timebase = 60
            self.ntsc = True
        else:
            self.timebase = round(self.fps)
            self.ntsc = False
    
    def seconds_to_frames(self, seconds: float) -> int:
        """Convert seconds to frame count"""
        return int(round(seconds * self.fps))
    
    def generate_file_url(self, file_path: Path) -> str:
        """Generate file URL for FCP7 XML"""
        # Use proper URL format for Premiere Pro compatibility
        abs_path = str(file_path).replace('\\', '/')
        # Premiere Pro prefers file:/// format (three slashes)
        return f"file:///{abs_path}"
    
    def create_rate_element(self, parent: ET.Element):
        """Create rate element with timebase and NTSC"""
        rate = ET.SubElement(parent, 'rate')
        ET.SubElement(rate, 'timebase').text = str(self.timebase)
        ET.SubElement(rate, 'ntsc').text = 'TRUE' if self.ntsc else 'FALSE'
    
    def create_timecode_element(self, parent: ET.Element):
        """Create timecode element"""
        timecode = ET.SubElement(parent, 'timecode')
        self.create_rate_element(timecode)
        ET.SubElement(timecode, 'string').text = '00:00:00:00'
        ET.SubElement(timecode, 'frame').text = '0'
        ET.SubElement(timecode, 'displayformat').text = 'NDF'
        ET.SubElement(timecode, 'source').text = 'source'
    
    def create_format_element(self, parent: ET.Element):
        """Create format element for video characteristics"""
        format_elem = ET.SubElement(parent, 'format')
        samplechar = ET.SubElement(format_elem, 'samplecharacteristics')
        
        ET.SubElement(samplechar, 'width').text = str(self.width)
        ET.SubElement(samplechar, 'height').text = str(self.height)
        ET.SubElement(samplechar, 'pixelaspectratio').text = 'square'
        ET.SubElement(samplechar, 'fielddominance').text = 'none'
        
        self.create_rate_element(samplechar)
        
        ET.SubElement(samplechar, 'colordepth').text = '24'
        
        codec = ET.SubElement(samplechar, 'codec')
        ET.SubElement(codec, 'name').text = 'Apple ProRes 422'
    
    def create_master_clip(self, bin_elem: ET.Element) -> str:
        """Create master clip in bin"""
        clip_id = "masterclip-1"
        
        clip = ET.SubElement(bin_elem, 'clip', id=clip_id)
        ET.SubElement(clip, 'name').text = self.video_path.name
        
        # Duration in frames
        duration_frames = self.seconds_to_frames(self.duration_seconds)
        ET.SubElement(clip, 'duration').text = str(duration_frames)
        
        self.create_rate_element(clip)
        
        ET.SubElement(clip, 'in').text = '0'
        ET.SubElement(clip, 'out').text = str(duration_frames)
        
        # Media section
        media = ET.SubElement(clip, 'media')
        
        # Video track
        video = ET.SubElement(media, 'video')
        ET.SubElement(video, 'track')
        self.create_format_element(video)
        
        # Audio track
        audio = ET.SubElement(media, 'audio')
        ET.SubElement(audio, 'track')
        
        # File reference
        file_elem = ET.SubElement(clip, 'file', id=clip_id)
        ET.SubElement(file_elem, 'name').text = self.video_path.name
        ET.SubElement(file_elem, 'pathurl').text = self.generate_file_url(self.video_path)
        
        return clip_id
    
    def create_clip_item(self, track: ET.Element, segment: Dict, 
                        master_clip_id: str, index: int):
        """Create a clip item on the timeline"""
        clipitem = ET.SubElement(track, 'clipitem', id=f'clipitem-{index}')
        
        ET.SubElement(clipitem, 'masterclipid').text = master_clip_id
        ET.SubElement(clipitem, 'name').text = f"{self.video_path.stem} - {index}"
        ET.SubElement(clipitem, 'enabled').text = 'TRUE'
        
        # Calculate frames
        start_frame = self.seconds_to_frames(segment['start'])
        end_frame = self.seconds_to_frames(segment['end'])
        duration_frames = end_frame - start_frame
        
        ET.SubElement(clipitem, 'duration').text = str(duration_frames)
        
        self.create_rate_element(clipitem)
        
        # Timeline position (calculated from previous segments)
        timeline_start = 0
        for i in range(index):
            prev_seg = self.segments[i]
            timeline_start += self.seconds_to_frames(prev_seg['end'] - prev_seg['start'])
        
        ET.SubElement(clipitem, 'start').text = str(timeline_start)
        ET.SubElement(clipitem, 'end').text = str(timeline_start + duration_frames)
        
        # Source in/out points
        ET.SubElement(clipitem, 'in').text = str(start_frame)
        ET.SubElement(clipitem, 'out').text = str(end_frame)
        
        # File reference
        ET.SubElement(clipitem, 'file', id=master_clip_id)
        
        # Source track
        sourcetrack = ET.SubElement(clipitem, 'sourcetrack')
        ET.SubElement(sourcetrack, 'mediatype').text = 'video'
        ET.SubElement(sourcetrack, 'trackindex').text = '1'
    
    def create_title_clip(self, track: ET.Element, caption: Dict, index: int):
        """Create a simple title clip"""
        clipitem = ET.SubElement(track, 'clipitem', id=f'title-{index}')
        
        ET.SubElement(clipitem, 'name').text = f"Title {index}"
        ET.SubElement(clipitem, 'enabled').text = 'TRUE'
        
        # Calculate frames
        start_frame = self.seconds_to_frames(caption['start'])
        end_frame = self.seconds_to_frames(caption['end'])
        duration_frames = end_frame - start_frame
        
        ET.SubElement(clipitem, 'duration').text = str(duration_frames)
        
        self.create_rate_element(clipitem)
        
        ET.SubElement(clipitem, 'start').text = str(start_frame)
        ET.SubElement(clipitem, 'end').text = str(end_frame)
        
        # Create title effect
        effect = ET.SubElement(clipitem, 'effect')
        ET.SubElement(effect, 'name').text = 'Text'
        ET.SubElement(effect, 'effectid').text = 'text'
        ET.SubElement(effect, 'effecttype').text = 'generator'
        
        # Text parameter
        param = ET.SubElement(effect, 'parameter')
        ET.SubElement(param, 'parameterid').text = 'str'
        ET.SubElement(param, 'name').text = 'Text'
        ET.SubElement(param, 'value').text = caption['text']
    
    def generate_xml(self):
        """Generate pure FCP7 XML"""
        # Create root
        xmeml = ET.Element('xmeml', version='4')
        
        # Create project
        project = ET.SubElement(xmeml, 'project')
        ET.SubElement(project, 'name').text = f"{self.video_path.stem}_project"
        
        # Create bin
        children = ET.SubElement(project, 'children')
        bin_elem = ET.SubElement(children, 'bin')
        ET.SubElement(bin_elem, 'name').text = 'Media'
        
        # Create master clip
        bin_children = ET.SubElement(bin_elem, 'children')
        master_clip_id = self.create_master_clip(bin_children)
        
        # Create sequence
        sequence = ET.SubElement(children, 'sequence')
        ET.SubElement(sequence, 'name').text = f"{self.video_path.stem}_edited"
        
        # Calculate total duration
        total_frames = sum(
            self.seconds_to_frames(seg['end'] - seg['start']) 
            for seg in self.segments
        )
        ET.SubElement(sequence, 'duration').text = str(total_frames)
        
        self.create_rate_element(sequence)
        self.create_timecode_element(sequence)
        
        ET.SubElement(sequence, 'in').text = '-1'
        ET.SubElement(sequence, 'out').text = '-1'
        
        # Media section
        media = ET.SubElement(sequence, 'media')
        
        # Video section
        video = ET.SubElement(media, 'video')
        ET.SubElement(video, 'numOutputChannels').text = '1'
        self.create_format_element(video)
        
        # Video track 1 - Main clips
        track1 = ET.SubElement(video, 'track')
        ET.SubElement(track1, 'enabled').text = 'TRUE'
        ET.SubElement(track1, 'locked').text = 'FALSE'
        
        # Add clip items
        for i, segment in enumerate(self.segments):
            self.create_clip_item(track1, segment, master_clip_id, i)
        
        # Video track 2 - Titles (if captions exist)
        if self.captions:
            track2 = ET.SubElement(video, 'track')
            ET.SubElement(track2, 'enabled').text = 'TRUE'
            ET.SubElement(track2, 'locked').text = 'FALSE'
            
            for i, caption in enumerate(self.captions):
                self.create_title_clip(track2, caption, i)
        
        # Convert to string with proper formatting
        xml_str = ET.tostring(xmeml, encoding='unicode')
        
        # Pretty print
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ', encoding='UTF-8')
        
        # Add DOCTYPE declaration
        lines = pretty_xml.decode('utf-8').split('\n')
        lines.insert(1, '<!DOCTYPE xmeml>')
        
        # Remove empty lines
        final_xml = '\n'.join(line for line in lines if line.strip())
        
        return final_xml
    
    def save(self):
        """Save the XML file"""
        os.makedirs(self.output_path.parent, exist_ok=True)
        
        xml_content = self.generate_xml()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        print(f"Pure FCP7 XML saved to: {self.output_path}")
        return str(self.output_path)