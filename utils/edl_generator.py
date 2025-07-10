"""
EDL (Edit Decision List) Generator for Adobe Premiere Pro
Generates CMX 3600 EDL format for maximum compatibility
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

class EDLGenerator:
    """Generate EDL files compatible with Adobe Premiere Pro"""
    
    def __init__(self, video_path: str, segments: List[Dict], 
                 output_path: Optional[str] = None):
        self.video_path = Path(video_path).resolve()
        self.segments = segments
        
        # Default output path
        if output_path is None:
            self.output_path = Path("output") / f"{self.video_path.stem}.edl"
        else:
            self.output_path = Path(output_path)
        
        # Video metadata
        self.fps = 29.97
        self.drop_frame = False
        
    def analyze_video(self, metadata: Dict):
        """Analyze video metadata"""
        self.fps = metadata.get('fps', 29.97)
        
        # Determine if drop frame timecode should be used
        # Drop frame is typically used for 29.97 fps
        self.drop_frame = abs(self.fps - 29.97) < 0.01
    
    def seconds_to_timecode(self, seconds: float) -> str:
        """Convert seconds to SMPTE timecode"""
        # Handle negative values
        if seconds < 0:
            return "00:00:00:00"
        
        # Calculate frames
        total_frames = int(seconds * self.fps)
        
        if self.drop_frame and self.fps > 29:
            # Drop frame calculation for 29.97 fps
            # Drop 2 frames every minute except every 10th minute
            frames_per_10min = int(10 * 60 * self.fps) - 18  # 18 frames dropped
            
            d = total_frames // frames_per_10min
            m = total_frames % frames_per_10min
            
            if m > 1:
                total_frames += 18 * d + 2 * ((m - 2) // (60 * int(self.fps) - 2))
            else:
                total_frames += 18 * d
        
        # Calculate time components
        hours = int(total_frames // (3600 * self.fps))
        minutes = int((total_frames % (3600 * self.fps)) // (60 * self.fps))
        seconds_tc = int((total_frames % (60 * self.fps)) // self.fps)
        frames = int(total_frames % self.fps)
        
        # Format with appropriate separator
        separator = ';' if self.drop_frame else ':'
        return f"{hours:02d}:{minutes:02d}:{seconds_tc:02d}{separator}{frames:02d}"
    
    def generate_edl(self) -> str:
        """Generate EDL content"""
        lines = []
        
        # EDL Header with enhanced information
        lines.append("TITLE: " + self.video_path.stem)
        lines.append("FCM: NON-DROP FRAME" if not self.drop_frame else "FCM: DROP FRAME")
        lines.append("")
        # Add source file information at the beginning
        lines.append(f"* SOURCE FILE INFORMATION:")
        lines.append(f"* FILENAME: {self.video_path.name}")
        lines.append(f"* PATH: {self.video_path.parent}")
        lines.append(f"* FULL PATH: {self.video_path}")
        lines.append("")
        
        # Edit decisions
        timeline_tc = 0.0  # Current position on timeline
        
        for i, segment in enumerate(self.segments, 1):
            # Edit number (padded to 3 digits)
            edit_num = f"{i:03d}"
            
            # Reel name (use filename without extension)
            reel = self.video_path.stem[:8].upper()  # CMX 3600 limits reel to 8 chars
            
            # Track type (V for video, A for audio, B for both)
            track = "B"  # Both video and audio
            
            # Edit type (C for cut)
            edit_type = "C"
            
            # Source in/out timecodes
            src_in = self.seconds_to_timecode(segment['start'])
            src_out = self.seconds_to_timecode(segment['end'])
            
            # Record in/out timecodes (timeline position)
            rec_in = self.seconds_to_timecode(timeline_tc)
            duration = segment['end'] - segment['start']
            timeline_tc += duration
            rec_out = self.seconds_to_timecode(timeline_tc)
            
            # Format: EDIT# REEL TRACK EDITTYPE SRC_IN SRC_OUT REC_IN REC_OUT
            edl_line = f"{edit_num}  {reel:<8} {track}     {edit_type}        "
            edl_line += f"{src_in} {src_out} {rec_in} {rec_out}"
            lines.append(edl_line)
            
            # Add source file comment with full information
            lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
            lines.append(f"* SOURCE FILE: {self.video_path.name}")
            lines.append(f"* REEL: {reel}")
            # Add file path hint for Premiere Pro
            lines.append(f"* FILE: {self.video_path.name}")
            lines.append("")
        
        return "\n".join(lines)
    
    def generate_edl_with_titles(self, captions: List[Dict]) -> str:
        """Generate EDL with title/caption information"""
        lines = []
        
        # EDL Header
        lines.append("TITLE: " + self.video_path.stem + "_with_titles")
        lines.append("FCM: NON-DROP FRAME" if not self.drop_frame else "FCM: DROP FRAME")
        lines.append("")
        
        # Combine segments and captions into a single timeline
        events = []
        
        # Add video segments
        for i, segment in enumerate(self.segments):
            events.append({
                'type': 'video',
                'start': segment['start'],
                'end': segment['end'],
                'data': segment,
                'index': i
            })
        
        # Add captions
        for i, caption in enumerate(captions):
            events.append({
                'type': 'title',
                'start': caption['start'],
                'end': caption['end'],
                'data': caption,
                'index': i
            })
        
        # Sort by start time
        events.sort(key=lambda x: x['start'])
        
        # Generate EDL entries
        edit_num = 1
        
        for event in events:
            if event['type'] == 'video':
                # Video edit
                segment = event['data']
                
                edit_str = f"{edit_num:03d}"
                reel = self.video_path.stem[:8].upper()
                
                src_in = self.seconds_to_timecode(segment['start'])
                src_out = self.seconds_to_timecode(segment['end'])
                rec_in = self.seconds_to_timecode(segment['start'])
                rec_out = self.seconds_to_timecode(segment['end'])
                
                edl_line = f"{edit_str}  {reel:<8} B     C        "
                edl_line += f"{src_in} {src_out} {rec_in} {rec_out}"
                lines.append(edl_line)
                lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
                
            else:
                # Title/Caption
                caption = event['data']
                
                edit_str = f"{edit_num:03d}"
                reel = "BL"  # Black/Title
                
                duration = caption['end'] - caption['start']
                src_in = self.seconds_to_timecode(0)
                src_out = self.seconds_to_timecode(duration)
                rec_in = self.seconds_to_timecode(caption['start'])
                rec_out = self.seconds_to_timecode(caption['end'])
                
                edl_line = f"{edit_str}  {reel:<8} V     C        "
                edl_line += f"{src_in} {src_out} {rec_in} {rec_out}"
                lines.append(edl_line)
                lines.append(f"* EFFECT NAME: TITLE")
                lines.append(f"* TITLE: {caption['text']}")
            
            lines.append("")
            edit_num += 1
        
        return "\n".join(lines)
    
    def save(self, include_titles: bool = False, captions: Optional[List[Dict]] = None):
        """Save the EDL file"""
        os.makedirs(self.output_path.parent, exist_ok=True)
        
        if include_titles and captions:
            edl_content = self.generate_edl_with_titles(captions)
        else:
            edl_content = self.generate_edl()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(edl_content)
        
        print(f"EDL saved to: {self.output_path}")
        return str(self.output_path)
    
    def save_with_titles_as_comments(self, captions: List[Dict]):
        """Save EDL with titles as comments (for reference)"""
        lines = []
        
        # Generate basic EDL
        edl_content = self.generate_edl()
        lines.append(edl_content)
        lines.append("\n")
        lines.append("* CAPTION INFORMATION:")
        lines.append("* =====================")
        
        # Add caption information as comments
        for i, caption in enumerate(captions, 1):
            tc_in = self.seconds_to_timecode(caption['start'])
            tc_out = self.seconds_to_timecode(caption['end'])
            lines.append(f"* CAPTION {i}: {tc_in} - {tc_out}")
            lines.append(f"* TEXT: {caption['text']}")
            lines.append("*")
        
        # Save file
        os.makedirs(self.output_path.parent, exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"EDL with caption comments saved to: {self.output_path}")
        return str(self.output_path)