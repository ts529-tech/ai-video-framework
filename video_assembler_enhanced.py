"""
video_assembler_enhanced.py — Enhanced video assembler that handles both video clips and images.

Supports:
  - Video clips from APIs (Pexels, Pixabay)
  - Enhanced Ken Burns effect for images
  - More dynamic movement and transitions
  - Better visual effects per physiological state
"""

import os
import textwrap
import random
from pathlib import Path
from typing import Optional

import numpy as np
from moviepy import (
    ImageClip, AudioFileClip, VideoFileClip,
    CompositeVideoClip, ColorClip,
    concatenate_videoclips, vfx
)
from PIL import Image, ImageDraw, ImageFont

from models import Scene, VideoScript, VideoConfig, PhysioState, STATE_PROFILES
from video_assembler import make_text_clip, STATE_VISUAL  # Import from original


class EnhancedVideoAssembler:
    """Enhanced assembler that creates more dynamic videos with real footage."""

    def __init__(self, config: VideoConfig):
        self.cfg = config
        self.W = config.width
        self.H = config.height

    def assemble(
        self,
        script: VideoScript,
        media_paths: list[str],  # Can be .jpg or .mp4 files
        audio_paths: list[Optional[str]],
        output_path: str,
    ) -> str:
        self.script_state = script.state  # Store state for scene processing
        vis = STATE_VISUAL.get(script.state, STATE_VISUAL[PhysioState.NEUTRAL])

        print(f"\n🎞  Enhanced assembling '{script.title}'")

        # Title card
        title_img = self._make_title_card(script)
        title_clip = ImageClip(title_img).with_duration(3).with_effects([vfx.FadeIn(0.4), vfx.FadeOut(0.6)])

        # Scene clips (enhanced with video support)
        scene_clips = []
        for scene, media_path, audio_path in zip(script.scenes, media_paths, audio_paths):
            clip = self._make_enhanced_scene_clip(scene, media_path, audio_path, vis)
            scene_clips.append(clip)

        # Outro card
        outro_img = self._make_outro_card(script)
        outro_clip = ImageClip(outro_img).with_duration(3).with_effects([vfx.FadeIn(0.6)])

        all_clips = [title_clip] + scene_clips + [outro_clip]
        final = concatenate_videoclips(all_clips, method="compose", padding=-0.4)

        print(f"   Total duration : {final.duration:.1f}s")
        print(f"   Writing MP4    : {output_path}")

        final.write_videofile(
            output_path,
            fps=self.cfg.fps,
            codec="libx264",
            audio_codec="aac",
            bitrate="2500k",
            audio_bitrate="128k",
            threads=4,
            logger=None,
            preset="medium",
            ffmpeg_params=["-pix_fmt", "yuv420p", "-movflags", "+faststart"]
        )
        print(f"   ✅ Done: {output_path}")
        return output_path

    def _make_enhanced_scene_clip(
        self,
        scene: Scene,
        media_path: str,
        audio_path: Optional[str],
        vis: dict,
    ) -> CompositeVideoClip:
        """Create scene clip with enhanced effects for both videos and images."""
        duration = scene.duration_s

        # Check if we have a video file or image
        is_video = media_path.lower().endswith(('.mp4', '.mov', '.avi'))

        if is_video:
            base_clip = self._create_video_clip(media_path, duration, vis, self.script_state)
        else:
            base_clip = self._create_enhanced_image_clip(media_path, duration, vis, self.script_state)

        # Dim overlay (state-dependent)
        overlay = (
            ColorClip(size=(self.W, self.H), color=[0, 0, 0])
            .with_duration(duration)
            .with_opacity(vis["overlay"])
        )

        # Scene title with enhanced animations
        title_dur = min(2.5, duration * 0.4)
        title_clip = self._create_animated_title(scene.title, title_dur, vis, self.script_state)

        # Enhanced subtitles
        sub_clip = self._create_enhanced_subtitles(scene.narration, duration, vis, self.script_state)

        layers = [base_clip, overlay, title_clip, sub_clip]
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
                    audio = audio.subclipped(0, duration)
                composite = composite.with_audio(audio)
            except Exception as e:
                print(f"      ⚠  Audio error scene {scene.scene_id}: {e}")

        return composite

    def _create_video_clip(self, video_path: str, duration: float, vis: dict, state: PhysioState) -> VideoFileClip:
        """Create enhanced video clip with state-appropriate effects."""
        try:
            video = VideoFileClip(video_path)
            
            # Trim video to scene duration
            if video.duration > duration:
                # Start from random point if video is longer
                start_time = random.uniform(0, max(0, video.duration - duration))
                video = video.subclipped(start_time, start_time + duration)
            else:
                # Loop if video is shorter
                video = video.with_duration(duration)
            
            # Resize to fit canvas
            video = video.resized((self.W, self.H))
            
            # Apply state-specific effects
            if state == PhysioState.CALM:
                # Slower motion for calm
                video = video.with_effects([vfx.MultiplySpeed(0.8)])
            elif state == PhysioState.ENERGIZED:
                # Faster motion for energy
                video = video.with_effects([vfx.MultiplySpeed(1.2)])
            elif state == PhysioState.PRE_SLEEP:
                # Very slow for sleep
                video = video.with_effects([vfx.MultiplySpeed(0.6)])
            
            video = video.with_fps(self.cfg.fps)
            print(f"      🎬 Video clip processed: {duration:.1f}s")
            return video
            
        except Exception as e:
            print(f"      ⚠  Video processing failed: {e}")
            # Fallback to image processing
            return self._create_enhanced_image_clip(video_path, duration, vis, state)

    def _create_enhanced_image_clip(self, img_path: str, duration: float, vis: dict, state: PhysioState) -> ImageClip:
        """Create enhanced image clip with more dynamic Ken Burns effect."""
        zoom_intensity = vis["zoom"]
        
        # Enhanced zoom patterns based on state
        zoom_patterns = {
            PhysioState.CALM: "gentle_drift",
            PhysioState.FOCUS: "steady_zoom",
            PhysioState.ENERGIZED: "dynamic_movement",
            PhysioState.PRE_SLEEP: "slow_fade",
            PhysioState.STRESSED: "calming_sway",
            PhysioState.NEUTRAL: "classic_ken_burns"
        }
        
        pattern = zoom_patterns.get(state, "classic_ken_burns")
        
        img_clip = ImageClip(img_path).with_duration(duration)
        
        if pattern == "gentle_drift":
            # Gentle drift with slight rotation
            img_clip = img_clip.resized(lambda t: 1 + zoom_intensity * (t / duration))
            img_clip = img_clip.rotated(lambda t: 2 * np.sin(t * 0.1))  # Gentle sway
        
        elif pattern == "dynamic_movement":
            # More aggressive movement for energized state
            zoom_in = random.choice([True, False])
            direction = random.choice([(1, 1), (-1, 1), (1, -1), (-1, -1)])
            
            def move_func(t):
                progress = t / duration
                zoom = 1 + zoom_intensity * 2 * progress if zoom_in else (1 + zoom_intensity * 2) - zoom_intensity * 2 * progress
                return zoom
            
            img_clip = img_clip.resized(move_func)
            img_clip = img_clip.with_position(lambda t: (
                self.W * 0.1 * direction[0] * (t / duration),
                self.H * 0.1 * direction[1] * (t / duration)
            ))
        
        elif pattern == "slow_fade":
            # Very subtle movement for sleep
            img_clip = img_clip.resized(lambda t: 1 + zoom_intensity * 0.5 * (t / duration))
            
        else:  # classic_ken_burns and others
            zoom_in = random.choice([True, False])
            img_clip = img_clip.resized(lambda t: 
                1 + zoom_intensity * (t / duration) if zoom_in
                else (1 + zoom_intensity) - zoom_intensity * (t / duration))
        
        img_clip = img_clip.with_position("center").with_fps(self.cfg.fps)
        return img_clip

    def _create_animated_title(self, title: str, duration: float, vis: dict, state: PhysioState) -> ImageClip:
        """Create animated title with state-appropriate effects."""
        # Base title
        title_clip = make_text_clip(
            text=title.upper(),
            fontsize=32,
            color=vis["font_color"],
            duration=duration,
            canvas_w=self.W,
            canvas_h=self.H,
            position=(60, 50),
        )
        
        # Add state-appropriate animations
        if state == PhysioState.ENERGIZED:
            # Slight bounce effect
            title_clip = title_clip.with_position(lambda t: (60, 50 + 5 * np.sin(t * 2)))
        elif state == PhysioState.CALM:
            # Gentle float
            title_clip = title_clip.with_position(lambda t: (60, 50 + 2 * np.sin(t * 0.5)))
        
        title_clip = title_clip.with_effects([vfx.FadeIn(0.3), vfx.FadeOut(0.4)])
        return title_clip

    def _create_enhanced_subtitles(self, text: str, duration: float, vis: dict, state: PhysioState) -> ImageClip:
        """Create enhanced subtitles with better typography."""
        # Larger font for better readability
        fontsize = 26 if state == PhysioState.PRE_SLEEP else 28
        
        # Enhanced background for better contrast
        bg_alpha = 180 if state == PhysioState.PRE_SLEEP else 160
        enhanced_bg = (*vis["sub_bg"][:3], bg_alpha)
        
        sub_clip = make_text_clip(
            text=text,
            fontsize=fontsize,
            color=vis["font_color"],
            duration=duration,
            canvas_w=self.W,
            canvas_h=self.H,
            position=("center", self.H - 140),
            bg=enhanced_bg,
            wrap_w=self.W - 100,
        )
        
        sub_clip = sub_clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
        return sub_clip

    def _make_title_card(self, script: VideoScript) -> str:
        """Create title card (reuse from original assembler)."""
        from video_assembler import VideoAssembler
        temp_assembler = VideoAssembler(self.cfg)
        return temp_assembler._make_title_card(script)

    def _make_outro_card(self, script: VideoScript) -> str:
        """Create outro card (reuse from original assembler)."""
        from video_assembler import VideoAssembler
        temp_assembler = VideoAssembler(self.cfg)
        return temp_assembler._make_outro_card(script)