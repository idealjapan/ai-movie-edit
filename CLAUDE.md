# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered video editing tool (AI動画カット＆テロップツール) that automatically detects silence periods in videos and generates captions/subtitles. It's designed for Japanese content creators using Adobe Premiere Pro, reducing editing time by approximately 70%.

## Quick Start - Common Workflows

```bash
# Standard workflow - silence removal + captions for Premiere Pro
python main.py video.mp4 --format pure-fcp7

# Quick processing with default settings
python process_video.py video.mp4

# Export subtitles only (requires caption file)
python main.py video.mp4 --format srt --captions captions.json

# Maximum compatibility export (EDL)
python main.py video.mp4 --format edl

# NEW: Generate SRT from edited video (after EDL cuts)
python generate_srt.py edited_video.mp4 -o output/subtitles.srt
```

### Recommended Workflow for Professional Editing

1. **Step 1: Generate EDL for cuts**
   ```bash
   python main.py raw_video.mp4 --format edl
   ```

2. **Step 2: Import EDL into Premiere/DaVinci**
   - Fine-tune cuts manually
   - Export the edited video

3. **Step 3: Generate SRT from edited video**
   ```bash
   python generate_srt.py edited_video.mp4 --max-chars-per-line 20
   ```

4. **Step 4: Import SRT into your editor**
   - Further customize caption styling
   - Adjust timing if needed

## Common Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up OpenAI API key - copy example file first
cp .env.example .env
# Then edit .env to add your actual API key
```

### Running the Application

The project has two different CLI entry points with different purposes:

**main.py - Primary CLI for flexible processing**
```bash
# Basic usage
python main.py <video_path> [options]

# With custom silence detection parameters
python main.py video.mp4 --min-silence 1000 --silence-thresh -40 --keep-silence 200

# With caption file
python main.py video.mp4 --captions captions.json

# Using pre-computed segments (skips silence detection)
python main.py video.mp4 --segments segments.json

# Export to different formats
python main.py video.mp4 --format pure-fcp7  # Pure FCP7 XML (Premiere-compatible)
python main.py video.mp4 --format edl       # EDL format (universal compatibility)
python main.py video.mp4 --format srt --captions captions.json  # SRT subtitles only
```

**main.py Options**:
- `--output, -o`: Output XML file path (default: `output/{video_name}_edited.xml`)
- `--min-silence`: Minimum silence duration in ms (default: 1000)
- `--silence-thresh`: Silence threshold in dB (default: -35)
- `--keep-silence`: Silence margin to keep in ms (default: 200)
- `--temp-dir`: Temporary file directory (default: `temp`)
- `--captions`: Path to caption JSON file
- `--segments`: Path to segment JSON file
- `--format`: Export format - xml, pure-fcp7, edl, or srt (default: xml)

**process_video.py - Alternative CLI with integrated pipeline**
```bash
# Basic usage - runs full pipeline (silence detection + transcription + caption generation)
python process_video.py video.mp4

# With custom parameters
python process_video.py video.mp4 --silence-threshold 0.01 --margin 0.5 --max-chars-per-line 20
```

**process_video.py Options**:
- `--silence-threshold`: Amplitude threshold for silence (default: 0.01)
- `--margin`: Time margin around speech in seconds (default: 0.5)
- `--max-chars-per-line`: Maximum characters per caption line (default: 20)
- `--api-key`: OpenAI API key (overrides .env file)

**GUI Mode**
```bash
python app.py
```

**generate_srt.py - SRT subtitle generation from edited video**
```bash
# Basic usage - generate SRT from edited video
python generate_srt.py edited_video.mp4

# With custom output path
python generate_srt.py edited_video.mp4 -o custom_subtitles.srt

# With custom formatting
python generate_srt.py edited_video.mp4 --max-chars-per-line 25

# With custom API key
python generate_srt.py edited_video.mp4 --api-key sk-...
```

**generate_srt.py Options**:
- `--output, -o`: Output SRT file path (default: `output/{video_name}_subtitles.srt`)
- `--max-chars-per-line`: Maximum characters per caption line (default: 20)
- `--temp-dir`: Temporary file directory (default: `temp`)
- `--api-key`: OpenAI API key (overrides .env file)

### Testing
```bash
# Test FFmpeg functionality (requires video file)
python tests/test_ffmpeg.py sample_data/test_video.mp4

# Test Whisper API integration
python tests/test_whisper.py

# Test XML generation
python tests/test_xml_gen.py

# Test ultimate XML generator
python tests/test_ultimate_xml.py

# Test new format generators (pure-fcp7, edl)
python tests/test_new_generators.py

# Run all tests sequentially
python tests/test_ffmpeg.py sample_data/test_video.mp4 && python tests/test_whisper.py && python tests/test_xml_gen.py

# Test specific functionality with custom files
python tests/test_silence_detection.py path/to/your/video.mp4
python tests/test_edl_samples.py  # Tests EDL generation with various formats

# Test SRT generation from edited video
python tests/test_generate_srt.py path/to/edited/video.mp4
```

### Code Quality Checks
```bash
# Python linting (if using pylint)
pylint utils/*.py

# Type checking (if using mypy)
mypy utils/*.py

# Format checking (if using black)
black --check .

# Run flake8 for style guide enforcement
flake8 utils/ --max-line-length=120
```

## Architecture Overview

The codebase follows a modular pipeline architecture:

1. **Entry Points**:
   - `main.py`: CLI interface for batch processing with flexible options
   - `process_video.py`: Alternative CLI with integrated full pipeline (includes transcription)
   - `app.py`: PyQt6 GUI for interactive use

2. **Core Processing Pipeline**:
   - Video → Audio Extraction → Silence Detection → Transcription → Caption Formatting → Export
   - `main.py` allows skipping steps with pre-computed data (segments/captions)
   - `process_video.py` runs the complete pipeline automatically

3. **Utility Modules** (`utils/`):
   - `audio_extractor.py`: Extracts audio from video using ffmpeg
   - `silence_detector.py`: Detects silence using librosa (amplitude-based algorithm)
   - `transcriber.py`: Interfaces with OpenAI Whisper API for transcription
   - `caption_formatter.py`: Formats captions according to user preferences
   - `premiere_xml_generator.py`: Generates Premiere Pro XML format (XMEML v4)
   - `premiere_xml_generator_ultimate.py`: Ultimate version with complete caption support and enhanced structure
   - `pure_fcp7_xml_generator.py`: Pure FCP7 format for better Premiere Pro compatibility
   - `edl_generator.py`: EDL format for universal NLE compatibility
   - `video_metadata.py`: Extracts video metadata using FFprobe
   - `ppro_time_utils.py`: Handles pproTicks time calculations
   - `segment_analyzer.py`: Analyzes video segments for optimal cutting

4. **Configuration** (`config.py`):
   - Centralized settings management
   - API key handling
   - Default parameters for silence detection and caption formatting

## Key Technical Details

- **Time Calculation**: Uses pproTicks (1 second = 282,432,000 ticks) for precise Premiere Pro timing
- **Frame Rate Handling**: Automatic NTSC detection (23.976fps, 29.97fps, 59.94fps)
- **Audio Processing**: Uses librosa for silence detection with configurable dB thresholds
- **API Integration**: OpenAI Whisper for transcription, GPT-4 for caption optimization
- **Export Formats**: 
  - XMEML version 4 (Premiere Pro) with multiple clip approach (not marker-based)
  - Pure FCP7 XML format for better Premiere Pro compatibility
  - EDL format for broader compatibility across all NLEs
  - SRT format for subtitle-only export
- **Temporary Files**: Uses `temp/` directory for audio extraction and processing
- **Output Files**: Generated files are saved to `output/` directory

## Development Workflow

When modifying the video processing pipeline:
1. Changes to silence detection algorithm should be made in `utils/silence_detector.py`
2. Caption formatting rules are in `utils/caption_formatter.py`
3. XML generation logic is in `utils/premiere_xml_generator.py` or related generator files
4. Time calculations are handled in `utils/ppro_time_utils.py`

When working with the GUI:
- PyQt6 interface code is in `app.py`
- GUI connects to the same `process_video.py` backend as CLI

## Important Considerations

- The project heavily relies on ffmpeg and ffprobe being installed on the system
- OpenAI API key must be configured in `.env` file
- Python 3.12 or below is recommended (PyQt6 has compatibility issues with Python 3.13)
- Large video files are processed in chunks to manage memory usage
- Temporary audio files are created during processing and should be cleaned up

## Data Formats

**Caption JSON Format**:
```json
{
  "original_text": "元のテキスト全体",
  "formatted_text": "整形されたテキスト",
  "captions": [
    {
      "text": "テロップ内容",
      "start": 0.0,
      "end": 5.0
    }
  ]
}
```

**Segment JSON Format**:
```json
[
  {
    "index": 0,
    "start": 0,
    "end": 5,
    "duration": 5
  }
]
```

## Frame Rate Processing Logic

```python
# NTSC判定ロジック
23.976fps → timebase=24, NTSC=TRUE
29.97fps  → timebase=30, NTSC=TRUE
59.94fps  → timebase=60, NTSC=TRUE
その他    → timebase=round(fps), NTSC=FALSE
```

## File Path Handling

- macOS: `file://localhost/path/to/file`
- Windows: `file://localhost/C:/path/to/file`
- Spaces are encoded as `%20`

## Known Issues

1. **Silence Detection**: Current amplitude-based detection may have false positives with background noise
2. **Memory Usage**: Long videos (several hours) may cause performance issues
3. **Dependencies**: Some environments have difficulty installing audio processing libraries like `librosa`

## Directory Structure
```
.
├── main.py              # CLI entry point
├── app.py               # GUI entry point
├── process_video.py     # Core processing pipeline
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── utils/               # Core utility modules
│   ├── audio_extractor.py
│   ├── silence_detector.py
│   ├── transcriber.py
│   ├── caption_formatter.py
│   ├── premiere_xml_generator.py
│   ├── premiere_xml_generator_ultimate.py
│   ├── pure_fcp7_xml_generator.py
│   ├── edl_generator.py
│   ├── video_metadata.py
│   ├── ppro_time_utils.py
│   └── segment_analyzer.py
├── tests/               # Test scripts
├── temp/                # Temporary files (created at runtime)
├── output/              # Generated output files (created at runtime)
└── sample_data/         # Sample video files for testing
```

## Recent Improvements (2025)

### Ultimate XML Generator (`premiere_xml_generator_ultimate.py`)
A completely rewritten XML generator based on comprehensive research of FCP7 XML (xmeml) format:

**Key Features:**
- **Complete Caption Support**: Full implementation of title generators with extensive style customization
- **Enhanced Structure**: Cleaner, more readable XML with proper hierarchy and organization
- **Professional Styling**: Support for Japanese fonts, drop shadows, outlines, backgrounds, and positioning
- **Bin Organization**: Media is organized in bins for better project management
- **Complete Metadata**: Includes color info, logging info, and all professional metadata fields
- **Multi-track Support**: Proper V1 (main video) and V2 (captions) track structure
- **Accurate Time Calculations**: Precise pproTicks calculations with full frame rate support

**Caption Style Options:**
```python
caption_style = {
    'font': 'Hiragino Kaku Gothic ProN',
    'fontsize': 56,
    'bold': True,
    'shadow': True,
    'outline': True,
    'position': {'x': 0.0, 'y': -0.8},  # Bottom center
    'background': True,
    # ... and many more options
}
```

### Premiere Pro Import Solutions (January 2025)

**Problem**: Generated XML files were not readable by Premiere Pro due to hybrid format mixing FCP7 XML with Premiere-specific extensions.

**Solutions Implemented**:

1. **Pure FCP7 XML Generator** (`pure_fcp7_xml_generator.py`)
   - Generates standard FCP7 XML without Premiere-specific extensions
   - Directly importable by Premiere Pro
   - Supports cuts and simple titles

2. **EDL Generator** (`edl_generator.py`)
   - Industry-standard Edit Decision List format
   - Maximum compatibility across all NLEs
   - Supports CMX 3600 format with timecode accuracy

3. **New Format Options in CLI**
   ```bash
   # Pure FCP7 XML (Premiere-compatible)
   python main.py video.mp4 --format pure-fcp7
   
   # EDL format (universal compatibility)
   python main.py video.mp4 --format edl
   
   # SRT only (subtitles)
   python main.py video.mp4 --format srt --captions captions.json
   ```

**Testing**:
```bash
python tests/test_new_generators.py
```

## Debugging Tips

### Common Debug Commands
```bash
# Check video metadata
ffprobe -v quiet -print_format json -show_format -show_streams video.mp4

# Test silence detection with verbose output
python -c "from utils.silence_detector import detect_silence; print(detect_silence('temp/audio.wav', verbose=True))"

# Verify XML structure
xmllint --format output/video_edited.xml | head -50

# Check API connectivity
python -c "import os; from utils.transcriber import transcribe_audio; print('API Key:', 'Set' if os.getenv('OPENAI_API_KEY') else 'Missing')"
```

### Performance Optimization

For large video files:
1. **Memory Management**: Process in chunks by using pre-computed segments
   ```bash
   # First extract segments
   python main.py large_video.mp4 --segments-only
   
   # Then process with segments
   python main.py large_video.mp4 --segments segments.json
   ```

2. **Parallel Processing**: Use multiple formats in separate processes
   ```bash
   python main.py video.mp4 --format pure-fcp7 &
   python main.py video.mp4 --format edl &
   wait
   ```

3. **Optimize Silence Detection**: Adjust parameters for faster processing
   ```bash
   # Increase minimum silence duration to reduce segments
   python main.py video.mp4 --min-silence 2000 --silence-thresh -30
   ```

## Troubleshooting

### FFmpeg Not Found
- Ensure FFmpeg is installed: `brew install ffmpeg` (macOS) or appropriate command for your OS
- Verify installation: `ffmpeg -version`
- Check PATH: `which ffmpeg`

### API Key Issues
- Check `.env` file exists and contains valid OpenAI API key
- Format: `OPENAI_API_KEY=sk-...`
- Test API: `python tests/test_whisper.py`

### Import Issues in Premiere Pro
- Try using `--format pure-fcp7` for better compatibility
- Use `--format edl` for maximum compatibility across video editors
- Check file paths in generated XML match your system
- Verify XML syntax: `xmllint --noout output/video_edited.xml`

### Memory Issues with Large Files
- Reduce chunk size in `config.py`
- Process audio separately first
- Use `--temp-dir` to specify SSD location for faster I/O
- Monitor memory usage: `top` or `htop` during processing
