# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Physiologically-Optimized Short-Form Video Generator** that creates MP4 videos based on physiological state labels rather than sensor data. The system generates personalized content (script, images, voice, editing) based on the user's declared state (calm, focus, energized, pre_sleep, stressed, neutral).

## Development Commands

### Setup Virtual Environment (Python 3.13)
```bash
# Create virtual environment
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Set Required API Key
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Generate Single Video

**Original Pipeline (Static Images):**
```bash
# Activate virtual environment first
source venv/bin/activate

# Basic usage with gradient/static images
python pipeline.py --topic "morning forest walk" --state calm
python pipeline.py --topic "deep work session" --state focus
python pipeline.py --topic "gym training montage" --state energized
```

**Enhanced Pipeline (Real Video Footage):**
```bash
# Enhanced version with real video clips
python pipeline_enhanced.py --topic "ocean waves at sunset" --state calm
python pipeline_enhanced.py --topic "coffee shop ambiance" --state focus
python pipeline_enhanced.py --topic "mountain hiking trail" --state energized

# With options
python pipeline_enhanced.py --topic "gentle rain forest" --state pre_sleep --no-cleanup
```

### Generate Batch Videos
```bash
# Create batch.json with format: [{"topic": "...", "state": "..."}, ...]
python pipeline.py --topic ignored --state calm --batch batch.json
python pipeline_enhanced.py --topic ignored --state calm --batch batch.json
```

### Video API Setup (Optional - For Real Footage)
```bash
# Get free API keys from:
# Pexels: https://www.pexels.com/api/
# Pixabay: https://pixabay.com/api/docs/

export PEXELS_API_KEY="your-pexels-api-key"
export PIXABAY_API_KEY="your-pixabay-api-key"

# Enhanced pipeline will automatically use these for real video clips
python pipeline_enhanced.py --topic "ocean waves" --state calm
```

### Python API Usage
```python
# Original pipeline (static images)
from pipeline import VideoGenerationPipeline
from models import PhysioState

pipeline = VideoGenerationPipeline()
result = pipeline.run(topic="rainy day coffee shop", state=PhysioState.FOCUS)
print(result["output_path"])  # ./output_ppv/abc12345_Rainy_Day....mp4

# Enhanced pipeline (real video footage)
from pipeline_enhanced import EnhancedVideoGenerationPipeline

enhanced_pipeline = EnhancedVideoGenerationPipeline()
result = enhanced_pipeline.run(topic="ocean waves at sunset", state=PhysioState.CALM)
print(result["output_path"])  # ./output_ppv/abc12345_Ocean_Waves_enhanced.mp4
```

## Architecture

### Pipeline Flow

**Original Pipeline:**
1. **Script Generation** (`script_generator.py`) → Claude API generates structured scenes
2. **Image Fetching** (`image_fetcher.py`) → Static images + gradient fallbacks
3. **Voice Generation** (`voice_generator.py`) → gTTS narration per scene
4. **Video Assembly** (`video_assembler.py`) → MoviePy combines all assets into MP4

**Enhanced Pipeline:**
1. **Script Generation** (`script_generator.py`) → Same Claude API script generation
2. **Video/Media Fetching** (`video_fetcher.py`) → Real video clips from Pexels/Pixabay APIs
3. **Voice Generation** (`voice_generator.py`) → Same gTTS narration
4. **Enhanced Assembly** (`video_assembler_enhanced.py`) → Advanced effects and real footage

### Core Components

#### State System (`models.py`)
- `PhysioState` enum defines 6 physiological states
- `STATE_PROFILES` maps each state to content parameters (tone, pacing, visual style, etc.)
- Each state has specific arousal levels, duration ranges, and content categories

#### Main Orchestrator (`pipeline.py`)
- `VideoGenerationPipeline` class coordinates all modules
- Supports both single video and batch generation
- Handles cleanup of temporary assets
- Saves script JSON alongside each video for inspection

#### Script Generator (`script_generator.py:26`)
- Uses Claude API to generate scene-by-scene scripts
- Maps physiological state to narrative tone and visual requirements
- Fallback script system when API unavailable (`script_generator.py:157`)

#### Image Fetcher (`image_fetcher.py:30`)
- Primary: Unsplash free API using visual prompts
- Fallback: PIL-generated mood-based gradients
- No API key required

#### Voice Generator (`voice_generator.py:33`)
- gTTS free text-to-speech with state-specific accents/speeds
- Optional ElevenLabs premium upgrade path (`voice_generator.py:50`)

#### Video Assembler (`video_assembler.py:125`)
- Ken Burns zoom effects (intensity varies by arousal level)
- State-specific visual styling (overlays, colors, fonts)  
- Subtitle overlays with word wrapping
- PIL-based text rendering (no ImageMagick dependency)

#### Enhanced Video Fetcher (`video_fetcher.py`)
- **Pexels Videos API** - High-quality stock video clips
- **Pixabay Videos API** - Additional video source with different content
- **Smart fallback** - Gracefully falls back to static images if APIs unavailable
- **State-aware queries** - Builds search queries optimized for physiological states
- **Duration filtering** - Selects appropriate video lengths for scenes

#### Enhanced Video Assembler (`video_assembler_enhanced.py`)  
- **Real video clip processing** - Handles MP4 files with trimming, looping, speed adjustment
- **Advanced Ken Burns** - Multiple movement patterns (gentle_drift, dynamic_movement, slow_fade)
- **State-specific effects** - Different motion patterns per physiological state
- **Enhanced typography** - Better subtitle rendering with improved contrast
- **Smart compositing** - Handles both video clips and images seamlessly

### State-Content Mapping
Each `PhysioState` maps to specific content profiles:
- **CALM**: nature, ASMR, slow pacing, cool colors (30-60s)
- **FOCUS**: lo-fi, minimalist, steady rhythm, high contrast (30-55s)  
- **ENERGIZED**: motivational, fast cuts, warm/saturated colors (15-45s)
- **PRE_SLEEP**: sleep stories, ultra-slow, dark/amber colors (45-60s)
- **STRESSED**: calming, gentle, warm greens/blues (30-60s)
- **NEUTRAL**: mixed content, moderate pacing (20-50s)

### File Structure
```
# Core files
pipeline.py                    # Original static image pipeline
pipeline_enhanced.py           # Enhanced pipeline with real video footage
models.py                      # State system and data classes
script_generator.py            # Claude API script generation

# Media fetching
image_fetcher.py               # Original static image fetcher (Unsplash/gradients)
video_fetcher.py               # Enhanced video fetcher (Pexels/Pixabay APIs)

# Video assembly
video_assembler.py             # Original assembler (static images + Ken Burns)
video_assembler_enhanced.py    # Enhanced assembler (real videos + advanced effects)

# Voice and utilities
voice_generator.py             # TTS narration (gTTS/ElevenLabs)
requirements.txt               # Python dependencies
README.md                      # User documentation

# Output directories
output_ppv/                    # Final MP4 videos + script JSON files
temp_ppv/                      # Temporary assets (auto-cleaned)
```

## Key Dependencies
- `anthropic` - Claude API for script generation
- `moviepy>=2.1.2` - Video editing and assembly (updated for Python 3.13 compatibility)
- `gtts` - Free text-to-speech
- `Pillow` - Image processing and text rendering
- `requests` - Unsplash image fetching

## Setup Notes
- **Python 3.13 Compatibility**: This codebase has been updated to work with MoviePy 2.1.2+ and Python 3.13
- **API Changes**: MoviePy 2.x uses different method names (`with_duration` vs `set_duration`, effects system for fades)
- **Pillow Compatibility**: Updated to handle newer Pillow versions (11.x) that removed deprecated constants

## Development Notes
- No test framework currently implemented
- State system is hardcoded but designed for future sensor integration
- Gradual fallback system: Claude API → fallback script, Unsplash → PIL gradients
- All text rendering uses PIL to avoid ImageMagick dependencies
- Each video gets unique 8-char ID for asset management