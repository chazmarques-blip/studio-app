"""
ElevenLabs Music Generation Service
Generates complete songs with vocals and instrumentals
"""
import os
import logging
from typing import Optional, Dict, Any
import httpx
import asyncio

logger = logging.getLogger(__name__)

class ElevenLabsMusicService:
    """Service for generating music using ElevenLabs Music API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    async def generate_music(
        self,
        prompt: str,
        duration_seconds: int = 180,
        with_vocals: bool = True
    ) -> Dict[str, Any]:
        """
        Generate music from a text prompt
        
        Args:
            prompt: Text description of the music style and content
                   Example: "Upbeat children's song about animals, cheerful xylophone"
            duration_seconds: Length of the music (min 3s, max 300s)
            with_vocals: Include vocals (True) or instrumental only (False)
        
        Returns:
            Dict with:
                - task_id: ID for checking generation status
                - status: Initial status
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # ElevenLabs Music API endpoint (as per latest docs)
                url = f"{self.base_url}/text-to-music"
                
                payload = {
                    "text": prompt,
                    "duration_seconds": min(max(duration_seconds, 3), 300),
                    "prompt_influence": 0.8,
                    "with_vocals": with_vocals
                }
                
                logger.info(f"Generating music with prompt: {prompt[:100]}...")
                
                response = await client.post(
                    url,
                    json=payload,
                    headers=self.headers
                )
                
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Music generation started: {result}")
                
                return {
                    "task_id": result.get("generation_id") or result.get("id"),
                    "status": "processing",
                    "audio_url": None
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error generating music: {e.response.text}")
            raise Exception(f"ElevenLabs API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error generating music: {str(e)}")
            raise
    
    async def check_generation_status(self, task_id: str) -> Dict[str, Any]:
        """
        Check the status of a music generation task
        
        Args:
            task_id: The generation task ID
        
        Returns:
            Dict with:
                - status: 'processing', 'completed', or 'failed'
                - audio_url: URL to download the MP3 (if completed)
                - duration: Actual duration in seconds (if completed)
                - error: Error message (if failed)
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                url = f"{self.base_url}/text-to-music/{task_id}"
                
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()
                
                result = response.json()
                
                # Parse response based on ElevenLabs format
                status = result.get("status", "unknown")
                
                if status == "completed":
                    return {
                        "status": "completed",
                        "audio_url": result.get("audio_url") or result.get("audio"),
                        "duration": result.get("duration_seconds", 0)
                    }
                elif status == "failed":
                    return {
                        "status": "failed",
                        "error": result.get("error", "Generation failed")
                    }
                else:
                    return {
                        "status": "processing",
                        "audio_url": None
                    }
                    
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"status": "processing", "audio_url": None}
            logger.error(f"HTTP error checking status: {e.response.text}")
            raise Exception(f"ElevenLabs API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error checking generation status: {str(e)}")
            raise
    
    async def wait_for_completion(
        self,
        task_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """
        Wait for music generation to complete (blocking)
        
        Args:
            task_id: The generation task ID
            max_wait_seconds: Maximum time to wait
            poll_interval: Seconds between status checks
        
        Returns:
            Final status dict with audio_url when completed
        """
        elapsed = 0
        
        while elapsed < max_wait_seconds:
            status = await self.check_generation_status(task_id)
            
            if status["status"] in ["completed", "failed"]:
                return status
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
            
            logger.info(f"Music generation in progress... ({elapsed}s elapsed)")
        
        raise TimeoutError(f"Music generation timed out after {max_wait_seconds}s")


# Global service instance
_music_service: Optional[ElevenLabsMusicService] = None

def get_music_service() -> ElevenLabsMusicService:
    """Get or create the global music service instance"""
    global _music_service
    if _music_service is None:
        _music_service = ElevenLabsMusicService()
    return _music_service
