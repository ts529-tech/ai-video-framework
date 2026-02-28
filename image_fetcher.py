"""
image_fetcher.py — Fetches or generates scene images.

Priority order:
  1. Unsplash free source (no API key)
  2. PIL gradient fallback (always works offline)
"""

import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

from models import Scene, VideoConfig, PhysioState, STATE_PROFILES


# Mood → gradient color pairs
MOOD_GRADIENTS = {
    "serene":    [(135, 195, 215), (60,  110, 160)],
    "focused":   [(220, 220, 220), (80,  80,  100)],
    "energetic": [(255, 160,  50), (200,  50,  30)],
    "dreamy":    [(180, 140, 210), (80,   60, 130)],
    "grounding": [(120, 170,  90), (50,   90,  50)],
    "uplifting": [(255, 210,  80), (220, 130,  30)],
    "neutral":   [(160, 160, 160), (80,   80,  80)],
}


class ImageFetcher:

    def fetch(self, scene: Scene, state: PhysioState, config: VideoConfig, save_path: str) -> str:
        """Return path to a JPEG image for this scene."""
        query = self._build_query(scene, state)
        result = self._try_unsplash(query, config, save_path)
        if result:
            return result
        return self._gradient_fallback(scene, config, save_path)

    # ─── Unsplash ─────────────────────────────────────────────────────────────

    def _build_query(self, scene: Scene, state: PhysioState) -> str:
        profile  = STATE_PROFILES[state]
        category = profile["categories"][0]
        # Use the visual_prompt's first ~50 chars as the search query
        short = scene.visual_prompt[:60].split(",")[0].strip()
        return f"{short} {category}"

    def _try_unsplash(self, query: str, config: VideoConfig, save_path: str) -> str | None:
        encoded = requests.utils.quote(query)
        w, h    = config.width, config.height
        urls = [
            f"https://source.unsplash.com/featured/{w}x{h}/?{encoded}",
            f"https://source.unsplash.com/{w}x{h}/?{encoded}",
        ]
        for url in urls:
            try:
                r = requests.get(url, timeout=12, allow_redirects=True)
                if r.status_code == 200 and len(r.content) > 8000:
                    with open(save_path, "wb") as f:
                        f.write(r.content)
                    print(f"      📸 Unsplash OK: {Path(save_path).name}")
                    return save_path
            except Exception:
                continue
        return None

    # ─── Gradient fallback ────────────────────────────────────────────────────

    def _gradient_fallback(self, scene: Scene, config: VideoConfig, save_path: str) -> str:
        w, h   = config.width, config.height
        colors = MOOD_GRADIENTS.get(scene.mood, MOOD_GRADIENTS["neutral"])
        c1, c2 = colors

        img    = Image.new("RGB", (w, h))
        pixels = img.load()
        for y in range(h):
            r_ratio = y / h
            r = int(c1[0] * (1 - r_ratio) + c2[0] * r_ratio)
            g = int(c1[1] * (1 - r_ratio) + c2[1] * r_ratio)
            b = int(c1[2] * (1 - r_ratio) + c2[2] * r_ratio)
            for x in range(w):
                pixels[x, y] = (r, g, b)

        img = img.filter(ImageFilter.GaussianBlur(3))
        draw = ImageDraw.Draw(img)
        draw.text((w // 2, h // 2), scene.title, fill="white", anchor="mm")

        img.save(save_path, "JPEG", quality=88)
        print(f"      🎨 Gradient fallback: {Path(save_path).name}")
        return save_path
