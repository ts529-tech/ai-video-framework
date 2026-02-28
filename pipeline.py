"""
pipeline.py — Main orchestrator.

Wires together:
  ScriptGenerator → ImageFetcher → VoiceGenerator → VideoAssembler

Usage (Python API):
    from pipeline import VideoGenerationPipeline
    from models import PhysioState

    pipeline = VideoGenerationPipeline()
    result   = pipeline.run(topic="morning forest walk", state=PhysioState.CALM)
    print(result["output_path"])

Usage (CLI):
    python pipeline.py --topic "rainy day coffee shop" --state focus
    python pipeline.py --topic "ocean sunset" --state pre_sleep
    python pipeline.py --topic "gym workout" --state energized
    python pipeline.py --topic "forest walk" --state calm --no-cleanup
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
from image_fetcher import ImageFetcher
from voice_generator import VoiceGenerator
from video_assembler import VideoAssembler


class VideoGenerationPipeline:
    """
    End-to-end pipeline: state label + topic → MP4 video.

    No physiological sensor data required. The state label is a
    hardcoded enum value (CALM, FOCUS, ENERGIZED, PRE_SLEEP, STRESSED, NEUTRAL)
    that drives every generation decision.
    """

    def __init__(self, config: Optional[VideoConfig] = None):
        self.cfg      = config or VideoConfig()
        Path(self.cfg.temp_dir).mkdir(parents=True, exist_ok=True)
        Path(self.cfg.output_dir).mkdir(parents=True, exist_ok=True)

        self.scripts  = ScriptGenerator()
        self.images   = ImageFetcher()
        self.voices   = VoiceGenerator()
        # Assembler instantiated per run (needs config)
        self.assembler = VideoAssembler(self.cfg)

    # ─── Public API ───────────────────────────────────────────────────────────

    def run(
        self,
        topic:     str,
        state:     PhysioState,
        cleanup:   bool = True,
    ) -> dict:
        """
        Generate a complete short-form video.

        Returns:
            {
                "output_path": str,
                "script":      VideoScript,
                "duration_s":  int,
                "scenes":      int,
            }
        """
        print(f"\n{'═'*58}")
        print(f"  📹 PHYSIOLOGICALLY-OPTIMIZED VIDEO GENERATOR")
        print(f"  Topic  : {topic}")
        print(f"  State  : {state.value}")
        print(f"{'═'*58}")

        t0 = time.time()

        # ── Step 1: Generate script via Claude ────────────────────────────────
        try:
            script = self.scripts.generate(topic, state)
        except Exception as e:
            print(f"   ⚠  Claude API failed ({e}), using fallback script")
            script = self.scripts.fallback(topic, state)

        self._save_script_json(script)

        # ── Step 2: Fetch images per scene ────────────────────────────────────
        print(f"\n🖼  Fetching images ({len(script.scenes)} scenes)...")
        image_paths = []
        for scene in script.scenes:
            img_path = str(Path(self.cfg.temp_dir) / f"{script.video_id}_s{scene.scene_id}.jpg")
            self.images.fetch(scene, state, self.cfg, img_path)
            image_paths.append(img_path)
            time.sleep(0.25)   # polite rate limit

        # ── Step 3: Generate narration per scene ──────────────────────────────
        print(f"\n🎙  Generating narration ({len(script.scenes)} scenes)...")
        audio_paths = []
        for scene in script.scenes:
            aud_path = str(Path(self.cfg.temp_dir) / f"{script.video_id}_s{scene.scene_id}.mp3")
            result   = self.voices.generate(scene.narration, state, aud_path)
            audio_paths.append(result)

        # ── Step 4: Assemble MP4 ──────────────────────────────────────────────
        safe_title  = script.title.replace(" ", "_").replace("/", "-")[:40]
        output_path = str(Path(self.cfg.output_dir) / f"{script.video_id}_{safe_title}.mp4")

        self.assembler.assemble(script, image_paths, audio_paths, output_path)

        elapsed = time.time() - t0
        print(f"\n⏱  Total time: {elapsed:.1f}s")

        if cleanup:
            self._cleanup(script.video_id)

        return {
            "output_path": output_path,
            "script":      script,
            "duration_s":  script.total_s,
            "scenes":      len(script.scenes),
            "elapsed_s":   round(elapsed, 1),
        }

    # ─── Batch generation ────────────────────────────────────────────────────

    def run_batch(self, jobs: list[dict], cleanup: bool = True) -> list[dict]:
        """
        Generate multiple videos.

        jobs = [
            {"topic": "ocean waves",   "state": PhysioState.CALM},
            {"topic": "morning coffee","state": PhysioState.FOCUS},
            {"topic": "sprint workout","state": PhysioState.ENERGIZED},
        ]
        """
        results = []
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] Starting job: {job['topic']} / {job['state'].value}")
            try:
                r = self.run(job["topic"], job["state"], cleanup=cleanup)
                results.append({"status": "ok", **r})
            except Exception as e:
                print(f"   ❌ Job failed: {e}")
                results.append({"status": "error", "error": str(e), **job})
        return results

    # ─── Helpers ─────────────────────────────────────────────────────────────

    def _save_script_json(self, script: VideoScript):
        """Persist the generated script as JSON for inspection."""
        path = Path(self.cfg.output_dir) / f"{script.video_id}_script.json"
        data = {
            "video_id":   script.video_id,
            "title":      script.title,
            "topic":      script.topic,
            "state":      script.state.value,
            "category":   script.category,
            "total_s":    script.total_s,
            "description":script.description,
            "scenes": [
                {
                    "scene_id":      s.scene_id,
                    "title":         s.title,
                    "narration":     s.narration,
                    "visual_prompt": s.visual_prompt,
                    "duration_s":    s.duration_s,
                    "mood":          s.mood,
                    "transition":    s.transition,
                }
                for s in script.scenes
            ],
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"   📄 Script JSON saved: {path.name}")

    def _cleanup(self, video_id: str):
        """Remove temp assets for this video_id."""
        temp = Path(self.cfg.temp_dir)
        removed = 0
        for f in temp.glob(f"{video_id}_*"):
            f.unlink()
            removed += 1
        if removed:
            print(f"🧹 Cleaned up {removed} temp files")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📹 Physiologically-Optimized Video Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
State labels (choose one):
  calm       — nature, ASMR, mindfulness (low arousal)
  focus      — lo-fi, explainer, minimalist (stable)
  energized  — motivational, fitness, upbeat (high arousal)
  pre_sleep  — sleep story, breathing guide (very low arousal)
  stressed   — calming, grounding, humor (stress relief)
  neutral    — mixed, safe, baseline

Examples:
  python pipeline.py --topic "morning forest walk" --state calm
  python pipeline.py --topic "deep work session"   --state focus
  python pipeline.py --topic "gym workout"         --state energized
  python pipeline.py --topic "bedtime wind-down"   --state pre_sleep
  python pipeline.py --topic "stressful day recap" --state stressed
        """,
    )
    parser.add_argument("--topic",      required=True, help="Video topic")
    parser.add_argument(
        "--state", required=True,
        choices=[s.value for s in PhysioState],
        help="Physiological state label",
    )
    parser.add_argument("--output-dir", default="./output_ppv", help="Output directory")
    parser.add_argument("--temp-dir",   default="./temp_ppv",   help="Temp assets directory")
    parser.add_argument("--width",      type=int, default=1280)
    parser.add_argument("--height",     type=int, default=720)
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Keep temp files after rendering")
    parser.add_argument("--batch",      type=str, default=None,
                        help="Path to JSON batch file (list of {topic, state} objects)")

    args = parser.parse_args()

    config = VideoConfig(
        width      = args.width,
        height     = args.height,
        temp_dir   = args.temp_dir,
        output_dir = args.output_dir,
    )
    pipeline = VideoGenerationPipeline(config)

    if args.batch:
        with open(args.batch) as f:
            jobs_raw = json.load(f)
        jobs = [{"topic": j["topic"], "state": PhysioState(j["state"])} for j in jobs_raw]
        results = pipeline.run_batch(jobs, cleanup=not args.no_cleanup)
        print(f"\n✅ Batch complete: {len(results)} videos")
        for r in results:
            status = r.get("status", "?")
            path   = r.get("output_path", "—")
            print(f"   {status:6s}  {path}")
    else:
        state  = PhysioState(args.state)
        result = pipeline.run(args.topic, state, cleanup=not args.no_cleanup)
        print(f"\n🎉 Video ready: {result['output_path']}")
        print(f"   Duration : {result['duration_s']}s")
        print(f"   Scenes   : {result['scenes']}")
        print(f"   Time     : {result['elapsed_s']}s")


if __name__ == "__main__":
    main()
