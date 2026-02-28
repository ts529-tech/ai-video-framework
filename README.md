# 🎬 Physiologically-Optimized Video Generation Framework

**AI-powered video creation system that generates personalized short-form content based on physiological states** — no wearable hardware required. Uses advanced AI and real video footage to create wellness-optimized videos tailored to your mental state.

## ✨ Key Features

🧠 **AI-Driven Content**: Claude API generates contextual scripts based on physiological state labels
🎥 **Real Video Footage**: Integrates professional video clips from Pexels and Pixabay APIs  
🎨 **Dynamic Visual Effects**: State-specific Ken Burns patterns and cinematic transitions
🎙️ **Adaptive Narration**: TTS voices adjusted for each physiological state (calm, focus, energized, etc.)
⚡ **Smart Fallback**: Graceful degradation from real footage → enhanced images → gradients
🎯 **Physiologically Optimized**: Every element calibrated for specific mental states and arousal levels

**Two Pipeline Options:**
- **Original Pipeline**: Fast generation with enhanced static visuals and Ken Burns effects
- **Enhanced Pipeline**: Professional video footage with advanced cinematic effects


---

## 🏗️ Architecture Overview

### **Enhanced Pipeline Flow**
1. **Script Generation** → AI creates state-optimized scenes with narration
2. **Real Video Fetching** → Professional footage from Pexels/Pixabay APIs
3. **Voice Synthesis** → State-appropriate TTS with accent/speed variations  
4. **Advanced Assembly** → Cinematic effects, dynamic movements, professional rendering

### **Core Components**

```
📁 Core Pipelines
├── pipeline.py                  ← Original: Static visuals + Ken Burns
├── pipeline_enhanced.py         ← Enhanced: Real footage + advanced effects

📁 Content Generation  
├── script_generator.py          ← Claude API → structured scene scripts
├── models.py                    ← PhysioState system + data structures

📁 Media Sources
├── image_fetcher.py             ← Static images + gradient fallbacks
├── video_fetcher.py             ← Real video clips (Pexels/Pixabay APIs)
├── voice_generator.py           ← TTS narration (gTTS + ElevenLabs)

📁 Video Assembly
├── video_assembler.py           ← Original: Basic Ken Burns effects
├── video_assembler_enhanced.py  ← Enhanced: Professional video processing

📁 Configuration
├── setup_api_keys.sh            ← API key setup helper
├── requirements.txt             ← Python dependencies  
└── CLAUDE.md                    ← Development guide
```

---

## 🚀 Quick Start

### **Option A: Enhanced Pipeline (Recommended)**
Real video footage with cinematic effects:

```bash
# 1. Setup virtual environment (Python 3.13)
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Set API keys
export ANTHROPIC_API_KEY="sk-ant-..."
export PEXELS_API_KEY="your-pexels-key"     # Free from pexels.com/api

# 3. Generate professional videos with real footage
python pipeline_enhanced.py --topic "ocean waves at sunset" --state calm
python pipeline_enhanced.py --topic "coffee shop ambiance" --state focus  
python pipeline_enhanced.py --topic "mountain hiking trail" --state energized
```

### **Option B: Original Pipeline**
Fast generation with enhanced static visuals:

```bash
# Same setup as above, but use original pipeline
python pipeline.py --topic "morning forest walk" --state calm
python pipeline.py --topic "deep work session" --state focus
python pipeline.py --topic "gym training montage" --state energized

# Pre-sleep wind-down
python pipeline.py --topic "bedtime breathing guide" --state pre_sleep

```

---

## 🧠 Physiological State System

The framework uses **6 physiological states** that drive all content decisions:

| State | Target Outcome | Duration | Arousal | Visual Style | Content |
|-------|----------------|----------|---------|--------------|---------|
| **🌊 CALM** | Maintain calm, deepen relaxation | 30-60s | Very Low | Cool, soft, slow motion | Nature, ASMR, mindfulness |
| **🎯 FOCUS** | Maintain focus, reduce distractions | 30-55s | Low-Med | Clean, minimal, steady | Lo-fi, explainers, productivity |
| **⚡ ENERGIZED** | Sustain energy, boost motivation | 15-45s | High | Warm, vibrant, fast cuts | Fitness, motivational, upbeat |
| **😴 PRE_SLEEP** | Reduce arousal, prepare for sleep | 45-60s | Very Low | Dark amber, ultra-slow | Sleep stories, breathing guides |
| **😤 STRESSED** | Reduce stress, lower arousal | 30-60s | Low | Warm greens/blues, gentle | Calming, humor, grounding |
| **⚪ NEUTRAL** | Light engagement, baseline | 20-50s | Medium | Balanced, moderate | News, trivia, mixed content |

### **State-Driven Adaptations**

Each state automatically adjusts:
- **Script Tone**: Meditation language for CALM, energetic language for ENERGIZED
- **Visual Movement**: Gentle drift for CALM, dynamic motion for ENERGIZED  
- **Voice Character**: Slow UK accent for CALM, confident pace for ENERGIZED
- **Color Grading**: Cool blues for CALM, warm oranges for ENERGIZED
- **Video Speed**: 0.8x for CALM, 1.2x for ENERGIZED, 0.6x for PRE_SLEEP

---

## 📱 Example Outputs

### **CALM State Video**
- **Real ocean waves** slowed to 80% speed
- **Gentle drift** Ken Burns movement  
- **Soft narration**: "Let the gentle waves wash away tension..."
- **Cool blue** color grading with low contrast
- **Duration**: 45-60 seconds with slow fades

### **ENERGIZED State Video**  
- **Mountain hiking footage** at 120% speed
- **Dynamic movement** with directional pans
- **Upbeat narration**: "Feel the power surge through your body..."  
- **Warm orange** color grading with high saturation
- **Duration**: 15-30 seconds with fast cuts

### **FOCUS State Video**
- **Coffee shop ambiance** at normal speed
- **Steady zoom** with minimal movement
- **Clear narration**: "Center your mind on the task ahead..."
- **Neutral tones** with high contrast text
- **Duration**: 30-45 seconds with moderate pacing

---

## 🔧 Advanced Usage

### **Batch Generation**
```bash
# Create batch.json:
# [
#   {"topic": "ocean waves at sunset", "state": "calm"},
#   {"topic": "morning coffee ritual", "state": "focus"},  
#   {"topic": "mountain peak climbing", "state": "energized"}
# ]

# Enhanced pipeline batch
python pipeline_enhanced.py --batch batch.json

# Original pipeline batch  
python pipeline.py --batch batch.json
```

### **Python API**
```python
# Enhanced Pipeline (Real Footage)
from pipeline_enhanced import EnhancedVideoGenerationPipeline
from models import PhysioState

pipeline = EnhancedVideoGenerationPipeline()
result = pipeline.run(
    topic = "forest stream flowing through trees",
    state = PhysioState.CALM
)

print(result["output_path"])   # ./output_ppv/abc12345_Forest_Stream_enhanced.mp4
print(result["duration_s"])    # e.g. 55
print(result["scenes"])        # e.g. 3

# Original Pipeline (Static Visuals)
from pipeline import VideoGenerationPipeline

pipeline = VideoGenerationPipeline()
result = pipeline.run(topic="study session", state=PhysioState.FOCUS)
```

### **API Key Setup Helper**
```bash
# Check current API key status
./setup_api_keys.sh

# Will show you which keys are set and provide setup instructions
```

---

## 💻 Technical Requirements

- **Python 3.12+ or 3.13** (recommended for best compatibility)
- **MoviePy 2.1.2+** for video processing  
- **macOS/Linux/Windows** support
- **4GB+ RAM** for video processing
- **Internet connection** for AI and video APIs

### **Required APIs**
- **Anthropic Claude API**: Script generation (required)
- **Pexels API**: Real video footage (free, optional but recommended)
- **Pixabay API**: Additional video source (free, optional)

### **Output Specifications**
- **Format**: MP4 (H.264, AAC audio)
- **Resolution**: 1280x720 (configurable)
- **Frame Rate**: 24fps (configurable)  
- **Compatibility**: QuickTime, VLC, web browsers
- **File Size**: 1-8MB depending on content and duration

---


---

## 🔮 Future Enhancements

- **Real Physiological Integration**: Connect with wearable devices (Apple Watch, Fitbit)
- **Custom Voice Cloning**: Personalized narration voices
- **AI Image Generation**: DALL-E 3 / Stable Diffusion integration
- **Multi-language Support**: Localized content and narration  
- **Advanced Analytics**: Physiological response tracking
- **Community Features**: Shared content libraries and templates
