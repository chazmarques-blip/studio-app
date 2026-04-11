"""
Kling AI Video Generation Client
Supports both text-to-video (T2V) and image-to-video (I2V) generation
API Documentation: https://app.klingai.com/global/dev/document-api
"""

import os
import time
import base64
import requests
import logging
import jwt
from typing import Optional, Dict, Any

logger = logging.getLogger("studiox")

class KlingClient:
    """Client for Kling AI video generation API"""
    
    def __init__(self, access_key: Optional[str] = None, secret_key: Optional[str] = None):
        self.access_key = access_key or os.environ.get("KLING_ACCESS_KEY")
        self.secret_key = secret_key or os.environ.get("KLING_SECRET_KEY")
        
        if not self.access_key or not self.secret_key:
            logger.warning("Kling AI credentials not found - video generation will fail")
        
        self.api_base = "https://api.klingai.com"
        self.api_version = "v1"
    
    def _get_auth_token(self) -> str:
        """Generate JWT token locally using PyJWT (HS256)"""
        if not self.access_key or not self.secret_key:
            raise Exception("Kling AI credentials (KLING_ACCESS_KEY / KLING_SECRET_KEY) not configured")
        
        headers = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "iss": self.access_key,
            "exp": int(time.time()) + 1800,  # 30 min expiry
            "nbf": int(time.time()) - 5
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm="HS256", headers=headers)
        logger.info("Kling AI: JWT token generated successfully")
        return token
    
    def text_to_video(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        duration: float = 5.0,
        resolution: str = "1280x720",
        model: str = "kling-v2-master",
        cfg_scale: float = 0.5,
        seed: Optional[int] = None,
        generate_audio: bool = True,
        max_wait: int = 600
    ) -> bytes:
        """Generate video using Kling AI (T2V or I2V)"""
        try:
            token = self._get_auth_token()
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Determine mode and endpoint
            is_i2v = image_path and os.path.exists(image_path)
            
            if is_i2v:
                # Image-to-video
                url = f"{self.api_base}/{self.api_version}/videos/image2video"
                with open(image_path, 'rb') as f:
                    img_b64 = base64.b64encode(f.read()).decode()
                
                payload = {
                    "model_name": model,
                    "prompt": prompt[:2500],
                    "image": img_b64,
                    "duration": str(duration),
                    "aspect_ratio": self._resolution_to_aspect(resolution),
                    "cfg_scale": cfg_scale
                }
            else:
                # Text-to-video
                url = f"{self.api_base}/{self.api_version}/videos/text2video"
                payload = {
                    "model_name": model,
                    "prompt": prompt[:2500],
                    "duration": str(duration),
                    "aspect_ratio": self._resolution_to_aspect(resolution),
                    "cfg_scale": cfg_scale
                }
            
            if seed is not None:
                payload["seed"] = seed
            
            mode_str = "I2V" if is_i2v else "T2V"
            logger.info(f"Kling AI: Submitting {mode_str} request (dur={duration}s, model={model})")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"Kling AI submit error: {response.status_code} - {response.text[:500]}")
                response.raise_for_status()
            
            data = response.json()
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                logger.error(f"Kling AI: No task_id returned - {data}")
                return b""
            
            logger.info(f"Kling AI: Task {task_id} submitted, polling...")
            
            # Poll for completion
            start_time = time.time()
            poll_url = f"{self.api_base}/{self.api_version}/videos/text2video/{task_id}"
            if is_i2v:
                poll_url = f"{self.api_base}/{self.api_version}/videos/image2video/{task_id}"
            
            while time.time() - start_time < max_wait:
                time.sleep(10)
                
                poll_response = requests.get(poll_url, headers=headers, timeout=30)
                poll_data = poll_response.json()
                
                task_data = poll_data.get("data", {})
                status = task_data.get("task_status", task_data.get("status", ""))
                
                if status in ("succeed", "completed"):
                    # Get video URL from works array
                    works = task_data.get("task_result", {}).get("videos", [])
                    if not works:
                        works = task_data.get("works", [])
                    
                    video_url = None
                    for w in works:
                        video_url = w.get("resource", {}).get("resource", w.get("video_url", w.get("url")))
                        if video_url:
                            break
                    
                    if not video_url:
                        video_url = task_data.get("video_url")
                    
                    if video_url:
                        video_response = requests.get(video_url, timeout=120)
                        video_response.raise_for_status()
                        elapsed = time.time() - start_time
                        logger.info(f"Kling AI: Task {task_id} DONE in {elapsed:.0f}s ({len(video_response.content)//1024}KB)")
                        return video_response.content
                    else:
                        logger.error(f"Kling AI: Completed but no video URL found in: {task_data.keys()}")
                        return b""
                
                elif status in ("failed", "error"):
                    error_msg = task_data.get("task_status_msg", task_data.get("error_message", "Unknown"))
                    logger.error(f"Kling AI: Task {task_id} FAILED - {error_msg}")
                    return b""
                
                elif status in ("submitted", "processing", "pending"):
                    elapsed = time.time() - start_time
                    logger.info(f"Kling AI: Task {task_id} {status}... ({elapsed:.0f}s)")
                else:
                    logger.warning(f"Kling AI: Task {task_id} unknown status: {status}")
            
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
