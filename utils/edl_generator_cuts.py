"""
EDL Generator with explicit cuts
Generates EDL that explicitly shows cuts between segments
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

class EDLGeneratorCuts:
    """Generate EDL files with explicit cut points"""
    
    def __init__(self, video_path: str, segments: List[Dict], 
                 output_path: Optional[str] = None):
        self.video_path = Path(video_path).resolve()
        self.segments = segments
        
        if output_path is None:
            self.output_path = Path("output") / f"{self.video_path.stem}_cuts.edl"
        else:
            self.output_path = Path(output_path)
        
        self.fps = 29.97
        self.drop_frame = False
        
    def analyze_video(self, metadata: Dict):
        """Analyze video metadata"""
        self.fps = metadata.get('fps', 29.97)
        self.drop_frame = abs(self.fps - 29.97) < 0.01
    
    def seconds_to_timecode(self, seconds: float) -> str:
        """Convert seconds to SMPTE timecode"""
        if seconds < 0:
            return "00:00:00:00"
        
        total_frames = int(seconds * self.fps)
        
        if self.drop_frame and self.fps > 29:
            frames_per_10min = int(10 * 60 * self.fps) - 18
            d = total_frames // frames_per_10min
            m = total_frames % frames_per_10min
            
            if m > 1:
                total_frames += 18 * d + 2 * ((m - 2) // (60 * int(self.fps) - 2))
            else:
                total_frames += 18 * d
        
        hours = int(total_frames // (3600 * self.fps))
        minutes = int((total_frames % (3600 * self.fps)) // (60 * self.fps))
        seconds_tc = int((total_frames % (60 * self.fps)) // self.fps)
        frames = int(total_frames % self.fps)
        
        separator = ';' if self.drop_frame else ':'
        return f"{hours:02d}:{minutes:02d}:{seconds_tc:02d}{separator}{frames:02d}"
    
    def generate_edl(self) -> str:
        """Generate EDL content with individual clips for each segment"""
        lines = []
        
        # EDL Header
        lines.append(f"TITLE: {self.video_path.stem}")
        lines.append("FCM: NON-DROP FRAME" if not self.drop_frame else "FCM: DROP FRAME")
        lines.append("")
        
        # Generate individual edits for each segment
        # Each segment is a separate edit from source
        timeline_pos = 0.0
        
        for i, segment in enumerate(self.segments, 1):
            edit_num = f"{i:03d}"
            reel = self.video_path.stem[:8].upper()
            
            # Source timecodes (from original video)
            src_in = self.seconds_to_timecode(segment['start'])
            src_out = self.seconds_to_timecode(segment['end'])
            
            # Record timecodes (on timeline)
            rec_in = self.seconds_to_timecode(timeline_pos)
            timeline_pos += segment['duration']
            rec_out = self.seconds_to_timecode(timeline_pos)
            
            # Create edit entry
            # Using V (video only) to see if it makes a difference
            lines.append(f"{edit_num}  {reel} V     C        {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
            lines.append(f"* COMMENT: SEGMENT {i} OF {len(self.segments)}")
            lines.append("")
            
        # Add audio tracks
        timeline_pos = 0.0
        for i, segment in enumerate(self.segments, 1):
            edit_num = f"{i + 100:03d}"  # Audio edits start at 101
            reel = self.video_path.stem[:8].upper()
            
            src_in = self.seconds_to_timecode(segment['start'])
            src_out = self.seconds_to_timecode(segment['end'])
            rec_in = self.seconds_to_timecode(timeline_pos)
            timeline_pos += segment['duration']
            rec_out = self.seconds_to_timecode(timeline_pos)
            
            # Audio tracks
            lines.append(f"{edit_num}  {reel} A     C        {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
            lines.append("")
            
        return "\n".join(lines)
    
    def save(self):
        """Save EDL to file"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        edl_content = self.generate_edl()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(edl_content)
        
        print(f"EDL saved to: {self.output_path}")
        return str(self.output_path)


def generate_edl_cuts(video_path: str, segments: List[Dict], 
                      output_path: Optional[str] = None,
                      metadata: Optional[Dict] = None) -> str:
    """Generate EDL file with explicit cuts"""
    generator = EDLGeneratorCuts(video_path, segments, output_path)
    
    if metadata:
        generator.analyze_video(metadata)
    
    return generator.save()