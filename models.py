"""
models.py — Core data classes and hardcoded state labels.

State labels replace physiological sensor data entirely.
Each label maps to a content profile used throughout the pipeline.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ─── Physiological State Labels (replaces wearable sensor data) ──────────────

class PhysioState(str, Enum):
    """
    Hardcoded state labels. In a real deployment these would be derived
    from wearable HR/HRV measurements. Here they are selected by the user
    or set programmatically.
    """
    CALM       = "calm"        # Low HR, high HRV — rest / recovery
    FOCUS      = "focus"       # Stable HR, moderate HRV — cognitive work
    ENERGIZED  = "energized"   # Elevated HR, lower HRV — active / motivated
    PRE_SLEEP  = "pre_sleep"   # Very low HR, high HRV — wind-down
    STRESSED   = "stressed"    # Elevated HR, low HRV — needs relief
    NEUTRAL    = "neutral"     # Baseline / unknown state


# ─── State → Content Profile Mapping ─────────────────────────────────────────

STATE_PROFILES = {
    PhysioState.CALM: {
        "target":       "maintain calm, deepen relaxation",
        "categories":   ["nature", "asmr", "mindfulness", "ambient_music"],
        "tone":         "slow, soothing, meditative",
        "arousal":      "very_low",
        "duration_s":   (30, 60),
        "pace":         "slow cuts, lingering shots",
        "color_grade":  "cool, desaturated, soft",
        "narration":    "gentle, unhurried, soft voice",
        "pre_sleep_ok": True,
    },
    PhysioState.FOCUS: {
        "target":       "maintain focus, reduce distractions",
        "categories":   ["lofi_study", "productivity", "minimalist", "explainer"],
        "tone":         "clean, clear, purposeful",
        "arousal":      "low_medium",
        "duration_s":   (30, 55),
        "pace":         "steady rhythm, minimal motion",
        "color_grade":  "neutral, high contrast text, clean",
        "narration":    "clear, measured, informative",
        "pre_sleep_ok": True,
    },
    PhysioState.ENERGIZED: {
        "target":       "sustain energy, boost motivation",
        "categories":   ["motivational", "fitness", "upbeat_music", "highlights"],
        "tone":         "dynamic, punchy, inspiring",
        "arousal":      "high",
        "duration_s":   (15, 45),
        "pace":         "fast cuts, high motion",
        "color_grade":  "warm, saturated, vibrant",
        "narration":    "upbeat, confident, energetic",
        "pre_sleep_ok": False,
    },
    PhysioState.PRE_SLEEP: {
        "target":       "reduce arousal, prepare for sleep",
        "categories":   ["sleep_story", "breathing_guide", "gentle_nature", "white_noise"],
        "tone":         "whispered, dreamy, ultra-slow",
        "arousal":      "very_low",
        "duration_s":   (45, 60),
        "pace":         "very slow dissolves, static shots",
        "color_grade":  "very dark, warm amber, deep blue",
        "narration":    "whispered, minimal, sleep-cue language",
        "pre_sleep_ok": True,
    },
    PhysioState.STRESSED: {
        "target":       "reduce stress, lower arousal",
        "categories":   ["nature", "humor_light", "breathing_guide", "calming_music"],
        "tone":         "warm, reassuring, grounding",
        "arousal":      "low",
        "duration_s":   (30, 60),
        "pace":         "gentle, unhurried",
        "color_grade":  "warm greens and blues, soft",
        "narration":    "empathetic, grounding, calm",
        "pre_sleep_ok": True,
    },
    PhysioState.NEUTRAL: {
        "target":       "engage lightly without arousal shift",
        "categories":   ["news_explainer", "trivia", "lofi_study", "ambient_music"],
        "tone":         "neutral, informative",
        "arousal":      "medium",
        "duration_s":   (20, 50),
        "pace":         "moderate",
        "color_grade":  "balanced",
        "narration":    "clear, neutral",
        "pre_sleep_ok": True,
    },
}


# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class Scene:
    scene_id:      int
    title:         str
    narration:     str
    visual_prompt: str     # image generation / search prompt
    duration_s:    int
    mood:          str
    transition:    str = "fade"   # fade | crossfade | cut


@dataclass
class VideoScript:
    video_id:    str
    topic:       str
    state:       PhysioState
    category:    str
    total_s:     int
    scenes:      list[Scene] = field(default_factory=list)
    title:       str = ""
    description: str = ""


@dataclass
class VideoConfig:
    width:      int = 1280
    height:     int = 720
    fps:        int = 24
    temp_dir:   str = "./temp_ppv"
    output_dir: str = "./output_ppv"
