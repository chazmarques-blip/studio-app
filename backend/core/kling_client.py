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
                    "duration": str(int(duration)),
                    "aspect_ratio": self._resolution_to_aspect(resolution),
                    "cfg_scale": cfg_scale
                }
            else:
                # Text-to-video
                url = f"{self.api_base}/{self.api_version}/videos/text2video"
                payload = {
                    "model_name": model,
                    "prompt": prompt[:2500],
                    "duration": str(int(duration)),
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


    def extend_video(
        self,
        video_id: str,
        prompt: str = "",
        max_wait: int = 600
    ) -> dict:
        """Extend an existing video by 4-5 seconds using Kling Video Extension API.
        
        Args:
            video_id: ID of the video to extend (from a previous generation)
            prompt: Optional text prompt to guide the extension direction
            max_wait: Maximum wait time in seconds
            
        Returns:
            dict with 'video_id', 'url', 'duration' or empty dict on failure
        """
        try:
            token = self._get_auth_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            url = f"{self.api_base}/{self.api_version}/videos/video-extend"
            payload = {
                "video_id": video_id,
                "prompt": prompt[:2500] if prompt else "",
            }
            
            logger.info(f"Kling AI: Extending video {video_id} (prompt={len(prompt)} chars)")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            
            if response.status_code != 200:
                logger.error(f"Kling AI extend error: {response.status_code} - {response.text[:300]}")
                return {}
            
            data = response.json()
            if data.get("code") != 0:
                logger.error(f"Kling AI extend API error: {data.get('message')}")
                return {}
            
            task_id = data.get("data", {}).get("task_id")
            if not task_id:
                logger.error(f"Kling AI: No task_id for extend - {data}")
                return {}
            
            logger.info(f"Kling AI: Extend task {task_id} submitted, polling...")
            
            # Poll for completion
            start_time = time.time()
            poll_url = f"{self.api_base}/{self.api_version}/videos/video-extend/{task_id}"
            
            while time.time() - start_time < max_wait:
                time.sleep(15)
                
                poll_response = requests.get(poll_url, headers=headers, timeout=30)
                poll_data = poll_response.json()
                
                task_data = poll_data.get("data", {})
                status = task_data.get("task_status", "")
                
                if status in ("succeed", "completed"):
                    videos = task_data.get("task_result", {}).get("videos", [])
                    if videos:
                        v = videos[0]
                        result = {
                            "video_id": v.get("id"),
                            "url": v.get("url"),
                            "duration": float(v.get("duration", 0)),
                        }
                        elapsed = time.time() - start_time
                        logger.info(f"Kling AI: Extend DONE in {elapsed:.0f}s — new duration: {result['duration']}s")
                        return result
                    else:
                        logger.error(f"Kling AI: Extend completed but no videos in result")
                        return {}
                
                elif status in ("failed", "error"):
                    error_msg = task_data.get("task_status_msg", "Unknown")
                    logger.error(f"Kling AI: Extend task {task_id} FAILED - {error_msg}")
                    return {}
                
                elif status in ("submitted", "processing"):
                    elapsed = time.time() - start_time
                    logger.info(f"Kling AI: Extend task {task_id} {status}... ({elapsed:.0f}s)")
            
            logger.error(f"Kling AI: Extend task {task_id} TIMEOUT after {max_wait}s")
            return {}
            
        except Exception as e:
            logger.error(f"Kling AI extend failed: {e}")
            return {}

    def generate_full_video(
        self,
        frames: list,
        initial_image_path: str = None,
        target_duration: float = 180.0,
        max_wait_per_step: int = 600
    ) -> bytes:
        """Generate a full-length video by creating initial clip + extending iteratively.
        
        Uses storyboard frames as context for each extension step.
        Each extension adds ~4-5 seconds. Max total: 180 seconds (3 minutes).
        
        Args:
            frames: List of storyboard frame dicts with 'kling_prompt', 'image_url', etc.
            initial_image_path: Path to first frame image for I2V
            target_duration: Target total duration in seconds (max 180)
            max_wait_per_step: Max wait per generation/extension step
            
        Returns:
            Video bytes of the final extended video, or empty bytes on failure
        """
        target_duration = min(target_duration, 180)  # API max is 3 minutes
        
        if not frames:
            logger.error("Kling AI: No frames provided for full video generation")
            return b""
        
        # Step 1: Generate initial 10s clip using first frame
        initial_prompt = frames[0].get("kling_prompt", "")
        logger.info(f"Kling AI: Generating full video ({target_duration}s target, {len(frames)} frames as context)")
        logger.info(f"Kling AI: Step 1 — Initial I2V clip (10s)")
        
        initial_video = self.text_to_video(
            prompt=initial_prompt,
            image_path=initial_image_path,
            duration=10.0,
            model="kling-v2-master",
            max_wait=max_wait_per_step
        )
        
        if not initial_video or len(initial_video) < 1000:
            logger.error("Kling AI: Initial clip generation failed")
            return b""
        
        # Get the video_id from the most recent task
        # We need to query the task list to find it
        current_video_id = self._get_last_video_id()
        if not current_video_id:
            logger.error("Kling AI: Could not retrieve video_id for initial clip")
            return initial_video  # Return what we have
        
        current_duration = 10.0
        current_video_bytes = initial_video
        step = 2
        
        # Step 2+: Extend iteratively until target duration
        # Each extension adds ~4-5 seconds
        frame_idx = 1  # Start from second frame for extension prompts
        
        while current_duration < target_duration:
            # Build prompt from upcoming frames
            if frame_idx < len(frames):
                ext_prompt = frames[frame_idx].get("kling_prompt", "")
                frame_idx += 1
            else:
                ext_prompt = frames[-1].get("kling_prompt", "Continue the scene naturally.")
            
            logger.info(f"Kling AI: Step {step} — Extending from {current_duration}s (target: {target_duration}s)")
            
            result = self.extend_video(
                video_id=current_video_id,
                prompt=ext_prompt,
                max_wait=max_wait_per_step
            )
            
            if not result or not result.get("video_id"):
                logger.warning(f"Kling AI: Extension failed at step {step} ({current_duration}s). Returning current video.")
                break
            
            # Download the extended video
            try:
                video_response = requests.get(result["url"], timeout=120)
                video_response.raise_for_status()
                current_video_bytes = video_response.content
                current_video_id = result["video_id"]
                current_duration = result.get("duration", current_duration + 4)
                logger.info(f"Kling AI: Step {step} DONE — video now {current_duration}s ({len(current_video_bytes)//1024}KB)")
            except Exception as e:
                logger.error(f"Kling AI: Failed to download extended video: {e}")
                break
            
            step += 1
        
        logger.info(f"Kling AI: Full video complete — {current_duration}s, {len(current_video_bytes)//1024}KB, {step-1} steps")
        return current_video_bytes
    
    def _get_last_video_id(self) -> str:
        """Get the video_id from the most recently completed text2video or image2video task."""
        try:
            token = self._get_auth_token()
            headers = {"Authorization": f"Bearer {token}"}
            
            # Check text2video tasks first
            for endpoint in ["text2video", "image2video"]:
                url = f"{self.api_base}/{self.api_version}/videos/{endpoint}?pageNum=1&pageSize=1"
                r = requests.get(url, headers=headers, timeout=15)
                data = r.json()
                
                tasks = data.get("data", [])
                if isinstance(tasks, list) and tasks:
                    task = tasks[0]
                    if task.get("task_status") in ("succeed", "completed"):
                        videos = task.get("task_result", {}).get("videos", [])
                        if videos:
                            vid = videos[0].get("id")
                            if vid:
                                logger.info(f"Kling AI: Found last video_id: {vid} from {endpoint}")
                                return vid
            
            return ""
        except Exception as e:
            logger.error(f"Kling AI: Error getting last video_id: {e}")
            return ""


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
