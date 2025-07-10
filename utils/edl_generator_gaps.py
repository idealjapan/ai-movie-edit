"""
EDL Generator with gaps between segments
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

class EDLGeneratorGaps:
    """Generate EDL with explicit gaps between segments"""
    
    def __init__(self, video_path: str, segments: List[Dict], 
                 output_path: Optional[str] = None):
        self.video_path = Path(video_path).resolve()
        self.segments = segments
        
        if output_path is None:
            self.output_path = Path("output") / f"{self.video_path.stem}_gaps.edl"
        else:
            self.output_path = Path(output_path)
        
        self.fps = 29.97
        self.drop_frame = False
        
    def seconds_to_timecode(self, seconds: float) -> str:
        """Convert seconds to SMPTE timecode"""
        if seconds < 0:
            return "00:00:00:00"
        
        total_frames = int(seconds * self.fps)
        
        hours = int(total_frames // (3600 * self.fps))
        minutes = int((total_frames % (3600 * self.fps)) // (60 * self.fps))
        seconds_tc = int((total_frames % (60 * self.fps)) // self.fps)
        frames = int(total_frames % self.fps)
        
        return f"{hours:02d}:{minutes:02d}:{seconds_tc:02d}:{frames:02d}"
    
    def generate_edl(self) -> str:
        """Generate EDL with gaps"""
        lines = []
        
        # EDL Header
        lines.append(f"TITLE: {self.video_path.stem}")
        lines.append("FCM: NON-DROP FRAME")
        lines.append("")
        
        # Track actual timeline position
        timeline_pos = 0.0
        edit_num = 1
        
        # Create edits with gaps
        for i, segment in enumerate(self.segments):
            # If there's a gap before this segment, add black/gap
            expected_start = 0 if i == 0 else self.segments[i-1]['end']
            gap = segment['start'] - expected_start
            
            if gap > 0.1 and i > 0:  # If gap > 0.1 seconds
                # Add black/gap edit
                black_in = self.seconds_to_timecode(0)
                black_out = self.seconds_to_timecode(gap)
                rec_in = self.seconds_to_timecode(timeline_pos)
                timeline_pos += gap
                rec_out = self.seconds_to_timecode(timeline_pos)
                
                lines.append(f"{edit_num:03d}  BL      V     C        {black_in} {black_out} {rec_in} {rec_out}")
                lines.append(f"* BLACK")
                lines.append("")
                edit_num += 1
            
            # Add the actual segment
            reel = self.video_path.stem[:8].upper()
            src_in = self.seconds_to_timecode(segment['start'])
            src_out = self.seconds_to_timecode(segment['end'])
            rec_in = self.seconds_to_timecode(timeline_pos)
            timeline_pos += segment['duration']
            rec_out = self.seconds_to_timecode(timeline_pos)
            
            lines.append(f"{edit_num:03d}  {reel} V     C        {src_in} {src_out} {rec_in} {rec_out}")
            lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
            lines.append("")
            edit_num += 1
        
        return "\n".join(lines)
    
    def save(self):
        """Save EDL to file"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        edl_content = self.generate_edl()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(edl_content)
        
        print(f"EDL saved to: {self.output_path}")
        return str(self.output_path)