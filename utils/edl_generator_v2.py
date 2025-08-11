"""
Enhanced EDL Generator for Adobe Premiere Pro
Generates CMX 3600 EDL format with better compatibility
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

class EDLGeneratorV2:
    """Generate EDL files with improved Premiere Pro compatibility"""
    
    def __init__(self, video_path: str, segments: List[Dict], 
                 output_path: Optional[str] = None):
        self.video_path = Path(video_path).resolve()
        self.segments = segments
        
        # Default output path
        if output_path is None:
            self.output_path = Path("output") / f"{self.video_path.stem}_v2.edl"
        else:
            self.output_path = Path(output_path)
        
        # Video metadata - default to 25fps for PAL
        self.fps = 25.0
        self.drop_frame = False
        
    def analyze_video(self, metadata: Dict):
        """Analyze video metadata"""
        self.fps = metadata.get('fps', 25.0)
        # For simplicity, use 25fps non-drop frame
        self.drop_frame = False
    
    def seconds_to_timecode(self, seconds: float) -> str:
        """Convert seconds to SMPTE timecode (25fps)"""
        if seconds < 0:
            return "00:00:00:00"
        
        # Calculate for 25fps
        total_frames = int(seconds * 25)
        
        hours = total_frames // (3600 * 25)
        minutes = (total_frames % (3600 * 25)) // (60 * 25)
        secs = (total_frames % (60 * 25)) // 25
        frames = total_frames % 25
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}:{frames:02d}"
    
    def generate_edl(self) -> str:
        """Generate EDL content with V and A tracks separated"""
        lines = []
        
        # EDL Header
        lines.append(f"TITLE: {self.video_path.stem}")
        lines.append("FCM: NON-DROP FRAME")
        lines.append("")
        
        # Generate both video and audio tracks
        timeline_tc = 0.0
        
        for i, segment in enumerate(self.segments, 1):
            edit_num = f"{i:03d}"
            reel = self.video_path.stem[:7].upper()
            
            # Calculate timecodes
            src_in_tc = self.seconds_to_timecode(segment['start'])
            src_out_tc = self.seconds_to_timecode(segment['end'])
            rec_in_tc = self.seconds_to_timecode(timeline_tc)
            rec_out_tc = self.seconds_to_timecode(timeline_tc + segment['duration'])
            
            # Video edit (V track)
            lines.append(f"{edit_num}  {reel} V     C        {src_in_tc} {src_out_tc} {rec_in_tc} {rec_out_tc}")
            lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
            lines.append("")
            
            # Audio edits (AA track for stereo)
            edit_num_audio = f"{i + 1000:03d}"  # Different edit numbers for audio
            lines.append(f"{edit_num_audio}  {reel} AA    C        {src_in_tc} {src_out_tc} {rec_in_tc} {rec_out_tc}")
            lines.append(f"* FROM CLIP NAME: {self.video_path.name}")
            lines.append("* AUDIO LEVEL AT 00:00:00:00 IS -0.00 DB  (REEL AX  A1)")
            lines.append("* AUDIO LEVEL AT 00:00:00:00 IS -0.00 DB  (REEL AX  A2)")
            lines.append("")
            
            timeline_tc += segment['duration']
        
        return "\n".join(lines)
    
    def save(self):
        """Save EDL to file"""
        # Create output directory
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate and save EDL
        edl_content = self.generate_edl()
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(edl_content)
        
        print(f"EDL saved to: {self.output_path}")
        return str(self.output_path)


def generate_edl_from_segments(video_path: str, segments: List[Dict], 
                               output_path: Optional[str] = None,
                               metadata: Optional[Dict] = None) -> str:
    """Generate EDL file from video segments"""
    generator = EDLGeneratorV2(video_path, segments, output_path)
    
    if metadata:
        generator.analyze_video(metadata)
    
    return generator.save()