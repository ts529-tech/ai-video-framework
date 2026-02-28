"""
video_assembler.py — Assembles scenes into a final MP4 video.

Per scene:
  - Ken Burns zoom effect (direction varies by state arousal)
  - Subtitle overlay (word-wrapped narration)
  - Scene title card (brief, fades out)
  - Narration audio

Final output:
  - Intro title card
  - Scene clips concatenated with transitions
  - Outro card
"""

import os
import textwrap
import random
from pathlib import Path
from typing import Optional

import numpy as np
from moviepy import (
    ImageClip, AudioFileClip,
    CompositeVideoClip, ColorClip,
    concatenate_videoclips, vfx
)
from PIL import Image, ImageDraw, ImageFont

from models import Scene, VideoScript, VideoConfig, PhysioState, STATE_PROFILES


# ─── PIL-based text clip (no ImageMagick dependency) ────────────────────────

def _hex_to_rgb(color: str) -> tuple:
    """Convert '#RRGGBB' or 'white'/'black' to (R,G,B)."""
    named = {"white": (255,255,255), "black": (0,0,0)}
    if color.lower() in named:
        return named[color.lower()]
    color = color.lstrip("#")
    return tuple(int(color[i:i+2], 16) for i in (0, 2, 4))

def make_text_clip(
    text:     str,
    fontsize: int,
    color:    str,
    duration: float,
    canvas_w: int,
    canvas_h: int,
    position: tuple,   # (x, y) in pixels from top-left, or ('center', y)
    bg:       tuple = (0, 0, 0, 0),   # RGBA background
    padding:  int = 12,
    wrap_w:   int = None,
) -> ImageClip:
    """
    Render text onto a transparent canvas using PIL, return as MoviePy ImageClip.
    Avoids any dependency on ImageMagick.
    """
    rgb = _hex_to_rgb(color)
    if wrap_w:
        text = textwrap.fill(text, width=max(10, wrap_w // (fontsize // 2)))

    # Measure text size
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fontsize)
    except Exception:
        font = ImageFont.load_default()

    # Compute bounding box
    tmp = Image.new("RGBA", (1, 1))
    td  = ImageDraw.Draw(tmp)
    bbox = td.multiline_textbbox((0, 0), text, font=font)
    tw   = bbox[2] - bbox[0] + padding * 2
    th   = bbox[3] - bbox[1] + padding * 2

    # Draw onto canvas
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    txt_img = Image.new("RGBA", (tw, th), bg)
    draw = ImageDraw.Draw(txt_img)

    # Shadow
    draw.multiline_text((padding + 1, padding + 1), text, font=font, fill=(0, 0, 0, 160), align="center")
    # Main text
    draw.multiline_text((padding, padding), text, font=font, fill=(*rgb, 255), align="center")

    # Paste onto canvas
    if position[0] == "center":
        px = (canvas_w - tw) // 2
    else:
        px = position[0]
    py = position[1] if position[1] >= 0 else canvas_h + position[1] - th

    canvas.paste(txt_img, (max(0, px), max(0, py)), txt_img)
    arr = np.array(canvas)

    clip = ImageClip(arr[:, :, :3], is_mask=False).with_duration(duration)
    # Use alpha channel as mask
    mask_arr = arr[:, :, 3] / 255.0
    from moviepy import ImageClip as IC
    mask = IC(mask_arr, is_mask=True).with_duration(duration)
    return clip.with_mask(mask)


# ─── Style presets per state ──────────────────────────────────────────────────

STATE_VISUAL = {
    PhysioState.CALM:      {"zoom": 0.018, "overlay": 0.30, "font_color": "#E8F4F8", "sub_bg": (20,  40,  60,  150)},
    PhysioState.FOCUS:     {"zoom": 0.010, "overlay": 0.20, "font_color": "#F0F0F0", "sub_bg": (30,  30,  30,  160)},
    PhysioState.ENERGIZED: {"zoom": 0.055, "overlay": 0.18, "font_color": "#FFFFFF", "sub_bg": (180, 60,  20,  170)},
    PhysioState.PRE_SLEEP: {"zoom": 0.008, "overlay": 0.50, "font_color": "#C8B8A2", "sub_bg": (10,  10,  25,  180)},
    PhysioState.STRESSED:  {"zoom": 0.015, "overlay": 0.28, "font_color": "#D8EED8", "sub_bg": (20,  50,  20,  150)},
    PhysioState.NEUTRAL:   {"zoom": 0.020, "overlay": 0.22, "font_color": "#F5F5F5", "sub_bg": (40,  40,  40,  150)},
}


class VideoAssembler:

    def __init__(self, config: VideoConfig):
        self.cfg    = config
        self.W      = config.width
        self.H      = config.height

    # ─── Public: assemble full video ─────────────────────────────────────────

    def assemble(
        self,
        script:      VideoScript,
        image_paths: list[str],
        audio_paths: list[Optional[str]],
        output_path: str,
    ) -> str:
        vis = STATE_VISUAL.get(script.state, STATE_VISUAL[PhysioState.NEUTRAL])

        print(f"\n🎞  Assembling '{script.title}'")

        # Title card
        title_img  = self._make_title_card(script)
        title_clip = ImageClip(title_img).with_duration(3).with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.6)])

        # Scene clips
        scene_clips = []
        for scene, img_path, audio_path in zip(script.scenes, image_paths, audio_paths):
            clip = self._make_scene_clip(scene, img_path, audio_path, vis)
            scene_clips.append(clip)

        # Outro card
        outro_img  = self._make_outro_card(script)
        outro_clip = ImageClip(outro_img).with_duration(3).with_effects([vfx.FadeIn(0.6)])

        all_clips  = [title_clip] + scene_clips + [outro_clip]
        final      = concatenate_videoclips(all_clips, method="compose", padding=-0.4)

        print(f"   Total duration : {final.duration:.1f}s")
        print(f"   Writing MP4    : {output_path}")

        final.write_videofile(
            output_path,
            fps         = self.cfg.fps,
            codec       = "libx264",
            audio_codec = "aac",
            bitrate     = "2000k",
            audio_bitrate = "128k",
            threads     = 4,
            logger      = None,
            preset      = "medium",
            ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        )
        print(f"   ✅ Done: {output_path}")
        return output_path

    # ─── Scene clip builder ───────────────────────────────────────────────────

    def _make_scene_clip(
        self,
        scene:      Scene,
        img_path:   str,
        audio_path: Optional[str],
        vis:        dict,
    ) -> CompositeVideoClip:

        duration = scene.duration_s
        zoom     = vis["zoom"]

        # Base image with Ken Burns zoom
        zoom_in  = random.choice([True, False])
        img_clip = (
            ImageClip(img_path)
            .with_duration(duration)
            .resized(lambda t: 1 + zoom * (t / duration) if zoom_in
                             else (1 + zoom) - zoom * (t / duration))
            .with_position("center")
            .with_fps(self.cfg.fps)
        )

        # Dim overlay
        overlay = (
            ColorClip(size=(self.W, self.H), color=[0, 0, 0])
            .with_duration(duration)
            .with_opacity(vis["overlay"])
        )

        # Scene title (top-left, fades after 2.5s)
        title_dur = min(2.5, duration * 0.4)
        title_clip = (
            make_text_clip(
                text     = scene.title.upper(),
                fontsize = 30,
                color    = vis["font_color"],
                duration = title_dur,
                canvas_w = self.W,
                canvas_h = self.H,
                position = (55, 45),
            )
            .with_effects([vfx.FadeIn(0.3), vfx.FadeOut(0.4)])
        )

        # Subtitle narration (bottom, full duration)
        sub_clip = (
            make_text_clip(
                text     = scene.narration,
                fontsize = 24,
                color    = vis["font_color"],
                duration = duration,
                canvas_w = self.W,
                canvas_h = self.H,
                position = ("center", self.H - 150),
                bg       = (*vis["sub_bg"][:3], vis["sub_bg"][3]),
                wrap_w   = self.W - 120,
            )
            .with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.4)])
        )

        layers = [img_clip, overlay, title_clip, sub_clip]
        composite = (
            CompositeVideoClip(layers, size=(self.W, self.H))
            .with_duration(duration)
            .with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.4)])
        )

        # Audio
        if audio_path and os.path.exists(audio_path):
            try:
                audio = AudioFileClip(audio_path)
                if audio.duration > duration:
                    audio = audio.subclip(0, duration)
                composite = composite.with_audio(audio)
            except Exception as e:
                print(f"      ⚠  Audio error scene {scene.scene_id}: {e}")

        return composite

    # ─── Title card ───────────────────────────────────────────────────────────

    def _make_title_card(self, script: VideoScript) -> str:
        vis   = STATE_VISUAL.get(script.state, STATE_VISUAL[PhysioState.NEUTRAL])
        path  = str(Path(self.cfg.temp_dir) / f"{script.video_id}_title.jpg")
        self._render_card(
            path        = path,
            line1       = script.title.upper(),
            line2       = script.state.value.replace("_", " ").title() + " Mode",
            line3       = script.description[:80] if script.description else "",
            bg_color    = (15, 15, 30),
            accent      = self._state_accent(script.state),
        )
        return path

    def _make_outro_card(self, script: VideoScript) -> str:
        path = str(Path(self.cfg.temp_dir) / f"{script.video_id}_outro.jpg")
        self._render_card(
            path     = path,
            line1    = "Thanks for watching",
            line2    = script.title.upper(),
            line3    = f"State: {script.state.value.replace('_',' ').title()}",
            bg_color = (10, 10, 20),
            accent   = self._state_accent(script.state),
        )
        return path

    def _render_card(
        self,
        path:     str,
        line1:    str,
        line2:    str,
        line3:    str,
        bg_color: tuple,
        accent:   tuple,
    ):
        img  = Image.new("RGB", (self.W, self.H), color=bg_color)
        draw = ImageDraw.Draw(img)
        cx   = self.W // 2
        cy   = self.H // 2

        # Accent lines
        draw.line([(cx - 260, cy - 70), (cx + 260, cy - 70)], fill=accent, width=2)
        draw.line([(cx - 260, cy + 80), (cx + 260, cy + 80)], fill=accent, width=2)

        # Text lines
        draw.text((cx, cy - 38), line1, fill="white",   anchor="mm")
        draw.text((cx, cy +  4), line2, fill=accent,    anchor="mm")
        draw.text((cx, cy + 56), line3, fill=(160,160,180), anchor="mm")

        img.save(path, "JPEG", quality=92)

    def _state_accent(self, state: PhysioState) -> tuple:
        accents = {
            PhysioState.CALM:      (100, 200, 230),
            PhysioState.FOCUS:     (180, 180, 220),
            PhysioState.ENERGIZED: (255, 140,  40),
            PhysioState.PRE_SLEEP: (180, 140,  80),
            PhysioState.STRESSED:  (100, 200, 120),
            PhysioState.NEUTRAL:   (180, 180, 180),
        }
        return accents.get(state, (180, 180, 180))
