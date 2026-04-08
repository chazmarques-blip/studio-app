"""
Kling AI Video Generation Client
Supports both text-to-video (T2V) and image-to-video (I2V) generation
API Documentation: https://kling.ai/document-api/quickStart/userManual
"""

import os
import time
import base64
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("studiox")

class KlingClient:
    """Client for Kling AI video generation API"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Initialize Kling AI client with API credentials
        
        Args:
            access_key: Kling AI Access Key (defaults to KLING_ACCESS_KEY env var)
            secret_key: Kling AI Secret Key (defaults to KLING_SECRET_KEY env var)
        """
        self.access_key = access_key or os.environ.get("KLING_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("KLING_SECRET_KEY")
        
        if not self.access_key or not self.secret_key:
            logger.warning("Kling AI credentials not found - text_to_video will fail")
        
        self.api_base = "https://api.klingai.com"
        self.api_version = "v1"
    
    def _get_auth_token(self) -> str:
        """Generate JWT token for API authentication"""
        url = f"{self.api_base}/{self.api_version}/auth/token"
        payload = {
            "access_key": self.access_key,
            "secret_key": self.secret_key
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("token", "")
        except Exception as e:
            logger.error(f"Kling AI auth failed: {e}")
            raise
    
    def text_to_video(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        duration: float = 5.0,
        resolution: str = "1280x720",
        model: str = "kling-v3",
        cfg_scale: float = 0.5,
        seed: Optional[int] = None,
        generate_audio: bool = True,
        max_wait: int = 600
    ) -> bytes:
        """Generate video using Kling AI
        
        Args:
            prompt: Text description of the video (max 2500 chars recommended)
            image_path: Optional reference image for image-to-video (I2V) mode
            duration: Video duration in seconds (3-15 for v3, up to 300 for v2.6)
            resolution: Video resolution ("1280x720", "1920x1080", "720x1280" portrait)
            model: Kling model version ("kling-v3", "kling-2.6", "kling-2.5")
            cfg_scale: Prompt adherence (0.0-1.0, default 0.5)
            seed: Random seed for reproducibility (optional)
            generate_audio: Enable native audio generation (voice, music, SFX) - Kling 2.6+/v3 only
            max_wait: Maximum seconds to wait for generation
            
        Returns:
            Video bytes if successful, empty bytes if failed
        """
        try:
            # Get authentication token
            token = self._get_auth_token()
            
            # Prepare request payload
            payload: Dict[str, Any] = {
                "model_name": model,
                "prompt": prompt[:2500],  # Kling supports longer prompts than Sora
                "duration": duration,
                "aspect_ratio": self._resolution_to_aspect(resolution),
                "cfg_scale": cfg_scale
            }
            
            # Enable native audio generation (Kling 2.6+/v3 feature)
            if generate_audio:
                payload["generate_audio"] = True
                logger.info("Kling AI: Native audio generation ENABLED (voice+music+SFX)")
            
            if seed is not None:
                payload["seed"] = seed
            
            # Image-to-video mode if reference image provided
            if image_path and os.path.exists(image_path):
                with open(image_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                payload["image"] = img_b64
                payload["mode"] = "i2v"
            else:
                payload["mode"] = "t2v"
            
            # Submit generation request
            url = f"{self.api_base}/{self.api_version}/videos/generations"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            logger.info(f"Kling AI: Submitting {payload['mode'].upper()} request (dur={duration}s, model={model})")
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                logger.error(f"Kling AI: No task_id returned - {data}")
                return b""
            
            logger.info(f"Kling AI: Task {task_id} submitted, polling for completion...")
            
            # Poll for completion
            start_time = time.time()
            poll_url = f"{self.api_base}/{self.api_version}/videos/generations/{task_id}"
            
            while time.time() - start_time < max_wait:
                time.sleep(10)  # Poll every 10 seconds
                
                poll_response = requests.get(poll_url, headers=headers, timeout=30)
                poll_response.raise_for_status()
                poll_data = poll_response.json()
                
                status = poll_data.get("data", {}).get("status")
                
                if status == "completed":
                    video_url = poll_data.get("data", {}).get("video_url")
                    if video_url:
                        # Download video
                        video_response = requests.get(video_url, timeout=120)
                        video_response.raise_for_status()
                        elapsed = time.time() - start_time
                        logger.info(f"Kling AI: Task {task_id} DONE in {elapsed:.0f}s ({len(video_response.content)//1024}KB)")
                        return video_response.content
                    else:
                        logger.error(f"Kling AI: Task {task_id} completed but no video_url")
                        return b""
                
                elif status in ["failed", "error"]:
                    error_msg = poll_data.get("data", {}).get("error_message", "Unknown error")
                    logger.error(f"Kling AI: Task {task_id} FAILED - {error_msg}")
                    return b""
                
                elif status in ["pending", "processing"]:
                    elapsed = time.time() - start_time
                    logger.info(f"Kling AI: Task {task_id} still {status}... ({elapsed:.0f}s elapsed)")
                else:
                    logger.warning(f"Kling AI: Task {task_id} unknown status: {status}")
            
            # Timeout
            logger.error(f"Kling AI: Task {task_id} TIMEOUT after {max_wait}s")
            return b""
            
        except Exception as e:
            logger.error(f"Kling AI generation failed: {e}")
            return b""
    
    def _resolution_to_aspect(self, resolution: str) -> str:
        """Convert resolution string to Kling aspect ratio format
        
        Args:
            resolution: "1280x720", "1920x1080", etc.
            
        Returns:
            Aspect ratio string like "16:9", "9:16", "1:1"
        """
        aspect_map = {
            "1280x720": "16:9",
            "1920x1080": "16:9",
            "720x1280": "9:16",
            "1080x1920": "9:16",
            "1024x1024": "1:1",
            "1536x1024": "3:2",
            "1024x1536": "2:3"
        }
        return aspect_map.get(resolution, "16:9")
    
    def estimate_cost(self, duration: float, model: str = "kling-v3") -> float:
        """Estimate generation cost in USD
        
        Args:
            duration: Video duration in seconds
            model: Kling model version
            
        Returns:
            Estimated cost in USD
        """
        # Rough pricing estimates (as of 2025-2026)
        # Official API: ~$4200/month unlimited
        # Third-party APIs: ~$0.15-0.30 per generation
        
        cost_per_second = {
            "kling-v3": 0.05,  # ~$0.25 for 5s
            "kling-2.6": 0.03,  # ~$0.15 for 5s, cheaper for long videos
            "kling-2.5": 0.02,
            "kling-1.6": 0.01
        }
        
        rate = cost_per_second.get(model, 0.05)
        return duration * rate


# Test function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    client = KlingClient()
    
    test_prompt = """High-quality 3D Pixar animation with warm lighting. 
    An anthropomorphic orange-furred dromedary camel standing upright on two legs, 
    wearing a red robe, looking at the stars with wonder. Desert night scene with 
    twinkling stars."""
    
    video_bytes = client.text_to_video(
        prompt=test_prompt,
        duration=5.0,
        resolution="1280x720",
        model="kling-v3"
    )
    
    if video_bytes:
        with open("/tmp/kling_test.mp4", "wb") as f:
            f.write(video_bytes)
        print("✅ Video saved to /tmp/kling_test.mp4")
    else:
        print("❌ Video generation failed")
