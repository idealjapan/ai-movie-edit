#!/usr/bin/env python3
"""
Generate EDL with gaps between segments
"""

import json
from pathlib import Path
from utils.edl_generator_gaps import EDLGeneratorGaps

def main():
    # Load segments
    with open('correct_segments.json', 'r') as f:
        segments = json.load(f)
    
    # Video path
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # Output path
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_gaps.edl'
    
    # Generate EDL
    print(f"Generating EDL with gaps for {len(segments)} segments...")
    print("\nSegments and gaps:")
    for i, seg in enumerate(segments):
        print(f"  Segment {i+1}: {seg['start']:.2f}s - {seg['end']:.2f}s (duration: {seg['duration']:.2f}s)")
        if i < len(segments) - 1:
            gap = segments[i+1]['start'] - seg['end']
            if gap > 0:
                print(f"    GAP: {gap:.2f}s")
    
    generator = EDLGeneratorGaps(video_path, segments, output_path)
    edl_path = generator.save()
    print(f"\nEDL generated: {edl_path}")

if __name__ == "__main__":
    main()