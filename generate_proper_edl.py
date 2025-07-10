#!/usr/bin/env python3
"""
Generate a proper EDL file with V and A tracks
"""

import json
from pathlib import Path
from utils.edl_generator_v2 import generate_edl_from_segments

def main():
    # Load segments
    with open('temp/IMG_2525_segments.json', 'r') as f:
        segments = json.load(f)
    
    # Video path
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # Output path
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_v2.edl'
    
    # Generate EDL
    print(f"Generating EDL with {len(segments)} segments...")
    for i, seg in enumerate(segments):
        print(f"  Segment {i+1}: {seg['start']:.2f}s - {seg['end']:.2f}s (duration: {seg['duration']:.2f}s)")
    
    edl_path = generate_edl_from_segments(video_path, segments, output_path)
    print(f"\nEDL generated: {edl_path}")

if __name__ == "__main__":
    main()