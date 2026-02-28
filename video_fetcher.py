"""
video_fetcher.py — Fetches actual video clips from various sources.

Priority order:
  1. Pexels Videos API (free with API key)
  2. Pixabay Videos API (free with API key)  
  3. Static image fallback with enhanced Ken Burns
"""

import os
import requests
from pathlib import Path
from typing import Optional

from models import Scene, VideoConfig, PhysioState, STATE_PROFILES


class VideoFetcher:
    """Fetches short video clips based on scene prompts and physiological states."""
    
    def __init__(self):
        self.pexels_key = os.getenv('PEXELS_API_KEY')
        self.pixabay_key = os.getenv('PIXABAY_API_KEY')
    
    def fetch_video(self, scene: Scene, state: PhysioState, config: VideoConfig, save_path: str) -> str:
        """Fetch a video clip for this scene. Returns path to MP4 file."""
        query = self._build_query(scene, state)
        
        # Try video sources in order
        result = (
            self._try_pexels_video(query, config, save_path) or
            self._try_pixabay_video(query, config, save_path) or
            self._fallback_to_image_fetcher(scene, state, config, save_path)
        )
        
        return result
    
    def _build_query(self, scene: Scene, state: PhysioState) -> str:
        """Build search query from scene and state."""
        profile = STATE_PROFILES[state]
        category = profile["categories"][0]
        
        # Extract main subject from visual prompt
        main_subject = scene.visual_prompt.split(",")[0].strip()
        
        # Add movement keywords for video searches
        movement_words = {
            PhysioState.CALM: "slow motion gentle peaceful",
            PhysioState.FOCUS: "steady minimal clean",
            PhysioState.ENERGIZED: "dynamic motion active",
            PhysioState.PRE_SLEEP: "very slow dreamy soft",
            PhysioState.STRESSED: "calming soothing",
            PhysioState.NEUTRAL: "natural"
        }
        
        movement = movement_words.get(state, "natural")
        return f"{main_subject} {movement} {category}"
    
    def _try_pexels_video(self, query: str, config: VideoConfig, save_path: str) -> Optional[str]:
        """Fetch video from Pexels Videos API."""
        if not self.pexels_key:
            return None
            
        try:
            headers = {'Authorization': self.pexels_key}
            params = {
                'query': query,
                'per_page': 5,
                'size': 'medium',  # medium quality for faster downloads
                'orientation': 'landscape'
            }
            
            api_url = 'https://api.pexels.com/videos/search'
            r = requests.get(api_url, headers=headers, params=params, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                if data.get('videos'):
                    # Find a suitable video (prefer shorter ones)
                    for video in data['videos']:
                        if video.get('duration', 0) <= 30:  # Max 30 seconds
                            video_files = video.get('video_files', [])
                            # Find medium quality MP4
                            for vf in video_files:
                                if (vf.get('file_type') == 'video/mp4' and 
                                    vf.get('quality') in ['hd', 'sd']):
                                    
                                    # Download the video
                                    video_url = vf['link']
                                    vid_r = requests.get(video_url, timeout=30)
                                    if vid_r.status_code == 200:
                                        # Save as .mp4 instead of .jpg
                                        video_path = save_path.replace('.jpg', '.mp4')
                                        with open(video_path, 'wb') as f:
                                            f.write(vid_r.content)
                                        print(f"      🎬 Pexels video OK: {Path(video_path).name}")
                                        return video_path
                                    break
                            break
        except Exception as e:
            print(f"      ⚠  Pexels video failed: {e}")
        
        return None
    
    def _try_pixabay_video(self, query: str, config: VideoConfig, save_path: str) -> Optional[str]:
        """Fetch video from Pixabay Videos API."""
        if not self.pixabay_key:
            return None
            
        try:
            params = {
                'key': self.pixabay_key,
                'q': query,
                'video_type': 'film',
                'per_page': 5,
                'min_duration': 5,
                'max_duration': 30
            }
            
            api_url = 'https://pixabay.com/api/videos/'
            r = requests.get(api_url, params=params, timeout=15)
            
            if r.status_code == 200:
                data = r.json()
                if data.get('hits'):
                    video = data['hits'][0]  # Take first result
                    videos = video.get('videos', {})
                    
                    # Prefer medium quality
                    for quality in ['medium', 'small', 'tiny']:
                        if quality in videos:
                            video_url = videos[quality]['url']
                            vid_r = requests.get(video_url, timeout=30)
                            if vid_r.status_code == 200:
                                video_path = save_path.replace('.jpg', '.mp4')
                                with open(video_path, 'wb') as f:
                                    f.write(vid_r.content)
                                print(f"      🎬 Pixabay video OK: {Path(video_path).name}")
                                return video_path
                            break
        except Exception as e:
            print(f"      ⚠  Pixabay video failed: {e}")
        
        return None
    
    def _fallback_to_image_fetcher(self, scene: Scene, state: PhysioState, config: VideoConfig, save_path: str) -> str:
        """Fallback to original image fetcher with enhanced images."""
        from image_fetcher import ImageFetcher
        fetcher = ImageFetcher()
        
        # Try to get a real image first
        result = fetcher.fetch(scene, state, config, save_path)
        
        if result:
            print(f"      📸 Fallback to image: {Path(save_path).name}")
        
        return result