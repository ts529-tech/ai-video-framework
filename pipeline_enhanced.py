"""
pipeline_enhanced.py — Enhanced pipeline with video support.

Usage:
    python pipeline_enhanced.py --topic "ocean waves" --state calm
    
Features:
    - Real video clips from Pexels/Pixabay APIs
    - Enhanced Ken Burns effects for images
    - More dynamic movement and transitions
    - Falls back gracefully to static images
"""

import os
import sys
import time
import json
import shutil
import argparse
from pathlib import Path
from typing import Optional

from models import PhysioState, VideoConfig, VideoScript
from script_generator import ScriptGenerator
from video_fetcher import VideoFetcher  # New video fetcher
from voice_generator import VoiceGenerator
from video_assembler_enhanced import EnhancedVideoAssembler  # Enhanced assembler


class EnhancedVideoGenerationPipeline:
    """Enhanced pipeline supporting real video clips and dynamic effects."""

    def __init__(self, config: Optional[VideoConfig] = None):
        self.cfg = config or VideoConfig()
        Path(self.cfg.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)

        self.scripts = ScriptGenerator()
        self.videos = VideoFetcher()  # New video fetcher
        self.voices = VoiceGenerator()
        self.assembler = EnhancedVideoAssembler(self.cfg)  # Enhanced assembler

    def run(
        self,
        topic: str,
        state: PhysioState,
        cleanup: bool = True,
    ) -> dict:
        """Generate an enhanced video with real footage when possible."""
        print(f"\n{'═'*60}")
        print(f"  🎬 ENHANCED PHYSIOLOGICALLY-OPTIMIZED VIDEO GENERATOR")
        print(f"  Topic  : {topic}")
        print(f"  State  : {state.value}")
        print(f"  APIs   : Pexels={bool(os.getenv('PEXELS_API_KEY'))}, "
              f"Pixabay={bool(os.getenv('PIXABAY_API_KEY'))}")
        print(f"{'═'*60}")

        t0 = time.time()

        # Step 1: Generate script
        try:
            script = self.scripts.generate(topic, state)
        except Exception as e:
            print(f"   ⚠  Claude API failed ({e}), using fallback script")
            script = self.scripts.fallback(topic, state)

        self._save_script_json(script)

        # Step 2: Fetch videos/images per scene
        print(f"\n🎬 Fetching media ({len(script.scenes)} scenes)...")
        media_paths = []
        for scene in script.scenes:
            media_path = str(Path(self.cfg.temp_dir) / f"{script.video_id}_s{scene.scene_id}.jpg")
            result_path = self.videos.fetch_video(scene, state, self.cfg, media_path)
            media_paths.append(result_path)
            time.sleep(0.5)  # Be respectful to APIs

        # Step 3: Generate narration per scene
        print(f"\n🎙  Generating narration ({len(script.scenes)} scenes)...")
        audio_paths = []
        for scene in script.scenes:
            aud_path = str(Path(self.cfg.temp_dir) / f"{script.video_id}_s{scene.scene_id}.mp3")
            result = self.voices.generate(scene.narration, state, aud_path)
            audio_paths.append(result)

        # Step 4: Enhanced video assembly
        safe_title = script.title.replace(" ", "_").replace("/", "-")[:40]
        output_path = str(Path(self.cfg.output_dir) / f"{script.video_id}_{safe_title}_enhanced.mp4")

        self.assembler.assemble(script, media_paths, audio_paths, output_path)

        elapsed = time.time() - t0
        print(f"\n⏱  Total time: {elapsed:.1f}s")

        if cleanup:
            self._cleanup(script.video_id)

        return {
            "output_path": output_path,
            "script": script,
            "duration_s": script.total_s,
            "scenes": len(script.scenes),
            "elapsed_s": round(elapsed, 1),
        }

    def run_batch(self, jobs: list[dict], cleanup: bool = True) -> list[dict]:
        """Generate multiple enhanced videos."""
        results = []
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] Starting enhanced job: {job['topic']} / {job['state'].value}")
            try:
                r = self.run(job["topic"], job["state"], cleanup=cleanup)
                results.append({"status": "ok", **r})
            except Exception as e:
                print(f"   ❌ Job failed: {e}")
                results.append({"status": "error", "error": str(e), **job})
        return results

    def _save_script_json(self, script: VideoScript):
        """Save script JSON (same as original pipeline)."""
        path = Path(self.cfg.output_dir) / f"{script.video_id}_script.json"
        data = {
            "video_id": script.video_id,
            "title": script.title,
            "topic": script.topic,
            "state": script.state.value,
            "category": script.category,
            "total_s": script.total_s,
            "description": script.description,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "title": s.title,
                    "narration": s.narration,
                    "visual_prompt": s.visual_prompt,
                    "duration_s": s.duration_s,
                    "mood": s.mood,
                    "transition": s.transition,
                }
                for s in script.scenes
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"   📄 Script JSON saved: {path.name}")

    def _cleanup(self, video_id: str):
        """Clean up temp files."""
        temp = Path(self.cfg.temp_dir)
        removed = 0
        for f in temp.glob(f"{video_id}_*"):
            f.unlink()
            removed += 1
        if removed:
            print(f"🧹 Cleaned up {removed} temp files")


def main():
    parser = argparse.ArgumentParser(
        description="🎬 Enhanced Physiologically-Optimized Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Enhanced Features:
  - Real video clips from Pexels/Pixabay APIs
  - Dynamic Ken Burns effects
  - State-appropriate motion patterns
  - Enhanced visual effects

API Keys (optional, will fallback to images):
  export PEXELS_API_KEY="your-pexels-key"
  export PIXABAY_API_KEY="your-pixabay-key"

Examples:
  python pipeline_enhanced.py --topic "ocean waves at sunset" --state calm
  python pipeline_enhanced.py --topic "coffee shop ambiance" --state focus
  python pipeline_enhanced.py --topic "mountain hiking trail" --state energized
        """,
    )
    parser.add_argument("--topic", required=True, help="Video topic")
    parser.add_argument(
        "--state", required=True,
        choices=[s.value for s in PhysioState],
        help="Physiological state label",
    )
    parser.add_argument("--output-dir", default="./output_ppv", help="Output directory")
    parser.add_argument("--temp-dir", default="./temp_ppv", help="Temp assets directory")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--no-cleanup", action="store_true", help="Keep temp files")
    parser.add_argument("--batch", type=str, help="Batch JSON file")

    args = parser.parse_args()

    config = VideoConfig(
        width=args.width,
        height=args.height,
        temp_dir=args.temp_dir,
        output_dir=args.output_dir,
    )
    pipeline = EnhancedVideoGenerationPipeline(config)

    if args.batch:
        with open(args.batch) as f:
            jobs_raw = json.load(f)
        jobs = [{"topic": j["topic"], "state": PhysioState(j["state"])} for j in jobs_raw]
        results = pipeline.run_batch(jobs, cleanup=not args.no_cleanup)
        print(f"\n✅ Enhanced batch complete: {len(results)} videos")
        for r in results:
            status = r.get("status", "?")
            path = r.get("output_path", "—")
            print(f"   {status:6s}  {path}")
    else:
        state = PhysioState(args.state)
        result = pipeline.run(args.topic, state, cleanup=not args.no_cleanup)
        print(f"\n🎉 Enhanced video ready: {result['output_path']}")
        print(f"   Duration : {result['duration_s']}s")
        print(f"   Scenes   : {result['scenes']}")
        print(f"   Time     : {result['elapsed_s']}s")


if __name__ == "__main__":
    main()