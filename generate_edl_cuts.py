#!/usr/bin/env python3
"""
Generate EDL with explicit cuts
"""

import json
from pathlib import Path
from utils.edl_generator_cuts import generate_edl_cuts
from utils.video_metadata import VideoMetadataExtractor

def main():
    # Load segments
    with open('correct_segments.json', 'r') as f:
        segments = json.load(f)
    
    # Video path
    video_path = '/Users/takayakazuki/Desktop/IMG_2525.mov'
    
    # Get video metadata
    extractor = VideoMetadataExtractor()
    metadata = extractor.extract_metadata(video_path)
    
    # Output path
    output_path = '/Users/takayakazuki/Desktop/IMG_2525_cuts.edl'
    
    # Generate EDL
    print(f"Generating EDL with {len(segments)} segments...")
    print(f"Video FPS: {metadata.get('fps', 'unknown')}")
    print("\nSegments:")
    for i, seg in enumerate(segments):
        print(f"  Segment {i+1}: {seg['start']:.2f}s - {seg['end']:.2f}s (duration: {seg['duration']:.2f}s)")
    
    edl_path = generate_edl_cuts(video_path, segments, output_path, metadata)
    print(f"\nEDL generated: {edl_path}")

if __name__ == "__main__":
    main()