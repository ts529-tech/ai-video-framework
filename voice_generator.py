"""
voice_generator.py — Text-to-speech narration per scene.

Uses gTTS (free, no API key). Maps PhysioState to accent/speed.
ElevenLabs premium path included as optional upgrade.
"""

import requests
from pathlib import Path

from models import PhysioState

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False


# State → voice character
STATE_VOICE = {
    PhysioState.CALM:      {"lang": "en", "tld": "co.uk", "slow": True},
    PhysioState.FOCUS:     {"lang": "en", "tld": "com",   "slow": False},
    PhysioState.ENERGIZED: {"lang": "en", "tld": "com.au","slow": False},
    PhysioState.PRE_SLEEP: {"lang": "en", "tld": "co.uk", "slow": True},
    PhysioState.STRESSED:  {"lang": "en", "tld": "co.uk", "slow": True},
    PhysioState.NEUTRAL:   {"lang": "en", "tld": "com",   "slow": False},
}


class VoiceGenerator:

    def generate(self, text: str, state: PhysioState, save_path: str) -> str | None:
        """Generate narration audio. Returns path or None on failure."""
        if not HAS_GTTS:
            print("      ⚠  gtts not installed — no audio")
            return None
        voice = STATE_VOICE.get(state, STATE_VOICE[PhysioState.NEUTRAL])
        try:
            tts = gTTS(text=text, lang=voice["lang"], tld=voice["tld"], slow=voice["slow"])
            tts.save(save_path)
            print(f"      🎙  Voice OK: {Path(save_path).name}")
            return save_path
        except Exception as e:
            print(f"      ⚠  TTS failed: {e}")
            return None

    # ─── Optional: ElevenLabs ─────────────────────────────────────────────────

    def elevenlabs(
        self,
        text: str,
        save_path: str,
        api_key: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
    ) -> str | None:
        url     = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.75, "similarity_boost": 0.85},
        }
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
            return save_path
        print(f"      ⚠  ElevenLabs error {r.status_code}")
        return None
