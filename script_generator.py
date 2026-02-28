"""
script_generator.py — Generates structured video scripts using Claude API.

Input:  topic (str) + PhysioState label
Output: VideoScript with N scenes, each with narration + visual prompt
"""

import json
import random
import anthropic

from models import PhysioState, STATE_PROFILES, Scene, VideoScript


class ScriptGenerator:
    """
    Calls Claude to produce a scene-by-scene short-form video script
    calibrated to the user's current physiological state label.
    """

    def __init__(self):
        self.client = anthropic.Anthropic()

    # ─── Public API ───────────────────────────────────────────────────────────

    def generate(self, topic: str, state: PhysioState) -> VideoScript:
        profile   = STATE_PROFILES[state]
        category  = random.choice(profile["categories"])
        min_s, max_s = profile["duration_s"]
        total_s   = random.randint(min_s, max_s)
        num_scenes = max(2, total_s // 15)
        scene_s    = total_s // num_scenes

        print(f"\n📝 Generating script")
        print(f"   Topic    : {topic}")
        print(f"   State    : {state.value}")
        print(f"   Category : {category}")
        print(f"   Duration : {total_s}s  ({num_scenes} scenes × ~{scene_s}s)")

        raw = self._call_claude(topic, state, profile, category, num_scenes, scene_s)
        script = self._parse(raw, topic, state, category, total_s)

        print(f"   ✅ Script ready: '{script.title}'")
        return script

    # ─── Claude call ──────────────────────────────────────────────────────────

    def _call_claude(
        self,
        topic: str,
        state: PhysioState,
        profile: dict,
        category: str,
        num_scenes: int,
        scene_s: int,
    ) -> str:

        system = (
            "You are an expert short-form video scriptwriter. "
            "Your scripts are calibrated to specific physiological target states. "
            "You always return valid JSON only — no markdown, no commentary."
        )

        prompt = f"""Write a short-form video script for the following brief:

TOPIC: {topic}
PHYSIOLOGICAL STATE: {state.value}
CONTENT CATEGORY: {category}
TARGET: {profile["target"]}
TONE: {profile["tone"]}
PACING: {profile["pace"]}
NARRATION STYLE: {profile["narration"]}
COLOR / VISUAL GRADE: {profile["color_grade"]}
NUMBER OF SCENES: {num_scenes}
SCENE DURATION: ~{scene_s} seconds each

Return ONLY this JSON structure (no markdown fences):
{{
  "title": "Short punchy video title",
  "description": "One sentence describing the video",
  "scenes": [
    {{
      "scene_id": 1,
      "title": "Scene title (3-5 words)",
      "narration": "Exactly 1-3 sentences of narration matching the tone and pacing above. Should feel natural when spoken aloud for {scene_s} seconds.",
      "visual_prompt": "Detailed image search / generation prompt: specific subject, lighting, composition, mood, style — all on one line",
      "duration_s": {scene_s},
      "mood": "one word: serene | focused | energetic | dreamy | grounding | uplifting | neutral",
      "transition": "fade"
    }}
  ]
}}

Guidelines:
- Narration must match the physiological target ({state.value}): {profile["target"]}
- Visual prompts must reflect: {profile["color_grade"]}
- Each scene should flow naturally into the next
- Keep total experience coherent as a short-form video unit
"""

        response = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    # ─── Parser ───────────────────────────────────────────────────────────────

    def _parse(
        self,
        raw: str,
        topic: str,
        state: PhysioState,
        category: str,
        total_s: int,
    ) -> VideoScript:

        # Strip accidental markdown fences
        text = raw
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        data = json.loads(text)

        scenes = [
            Scene(
                scene_id      = s["scene_id"],
                title         = s["title"],
                narration     = s["narration"],
                visual_prompt = s["visual_prompt"],
                duration_s    = s.get("duration_s", total_s // max(len(data["scenes"]), 1)),
                mood          = s.get("mood", "neutral"),
                transition    = s.get("transition", "fade"),
            )
            for s in data["scenes"]
        ]

        import uuid
        return VideoScript(
            video_id    = str(uuid.uuid4())[:8],
            topic       = topic,
            state       = state,
            category    = category,
            total_s     = total_s,
            scenes      = scenes,
            title       = data.get("title", topic),
            description = data.get("description", ""),
        )

    # ─── Fallback (no API key) ────────────────────────────────────────────────

    def fallback(self, topic: str, state: PhysioState) -> VideoScript:
        """Returns a hardcoded script so the pipeline can run without an API key."""
        import uuid
        profile  = STATE_PROFILES[state]
        category = profile["categories"][0]
        scenes = [
            Scene(1, "Opening",  f"Welcome to this {state.value} experience about {topic}.",
                  f"{topic} wide shot, soft lighting, {profile['color_grade']}", 15, "neutral"),
            Scene(2, "Journey",  f"Let yourself settle into the moment as we explore {topic}.",
                  f"{topic} close detail, ambient mood, {profile['color_grade']}", 15, "serene"),
            Scene(3, "Closing",  f"Carry this feeling with you as you return to your day.",
                  f"{topic} gentle fade, peaceful, {profile['color_grade']}", 15, "serene"),
        ]
        return VideoScript(
            video_id    = str(uuid.uuid4())[:8],
            topic       = topic,
            state       = state,
            category    = category,
            total_s     = 45,
            scenes      = scenes,
            title       = f"{topic} — {state.value.title()} Experience",
            description = f"A {state.value} short-form video about {topic}.",
        )
