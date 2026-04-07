"""
Music Generation API Endpoints
Routes for generating and managing music
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging

from services.music_service import get_music_service
from core.deps import get_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/music", tags=["music"])


class MusicGenerationRequest(BaseModel):
    """Request to generate music"""
    prompt: str = Field(
        ...,
        description="Text description of the music style and content",
        example="Upbeat children's song about Abraham and Isaac, cheerful xylophone and drums, educational tone"
    )
    duration_seconds: int = Field(
        default=180,
        ge=3,
        le=300,
        description="Duration of the music in seconds (3-300)"
    )
    with_vocals: bool = Field(
        default=True,
        description="Include vocals (True) or instrumental only (False)"
    )
    lyrics: Optional[str] = Field(
        default=None,
        description="Optional lyrics for the song"
    )


class MusicGenerationResponse(BaseModel):
    """Response after starting music generation"""
    task_id: str
    status: Literal["processing", "completed", "failed"]
    message: str
    audio_url: Optional[str] = None


class MusicStatusResponse(BaseModel):
    """Response with music generation status"""
    task_id: str
    status: Literal["processing", "completed", "failed"]
    audio_url: Optional[str] = None
    duration: Optional[int] = None
    error: Optional[str] = None


@router.post("/generate", response_model=MusicGenerationResponse)
async def generate_music(
    request: MusicGenerationRequest,
    tenant = Depends(get_tenant)
):
    """
    Generate music using ElevenLabs Music API
    
    The music generation is asynchronous. This endpoint returns immediately
    with a task_id. Use the /music/status/{task_id} endpoint to check progress.
    """
    try:
        music_service = get_music_service()
        
        # Build enhanced prompt with lyrics if provided
        full_prompt = request.prompt
        if request.lyrics:
            full_prompt = f"{request.prompt}\n\nLyrics:\n{request.lyrics}"
        
        logger.info(f"Starting music generation for tenant {tenant.get('id')}")
        
        result = await music_service.generate_music(
            prompt=full_prompt,
            duration_seconds=request.duration_seconds,
            with_vocals=request.with_vocals
        )
        
        return MusicGenerationResponse(
            task_id=result["task_id"],
            status=result["status"],
            message="Music generation started. Check status using the task_id.",
            audio_url=result.get("audio_url")
        )
        
    except Exception as e:
        logger.error(f"Error generating music: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate music: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=MusicStatusResponse)
async def get_music_status(
    task_id: str,
    tenant = Depends(get_tenant)
):
    """
    Check the status of a music generation task
    
    Returns:
        - status: 'processing', 'completed', or 'failed'
        - audio_url: URL to download the MP3 (when completed)
        - duration: Actual duration in seconds (when completed)
    """
    try:
        music_service = get_music_service()
        
        status = await music_service.check_generation_status(task_id)
        
        return MusicStatusResponse(
            task_id=task_id,
            **status
        )
        
    except Exception as e:
        logger.error(f"Error checking music status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to check music status: {str(e)}"
        )


@router.post("/generate-and-wait", response_model=MusicStatusResponse)
async def generate_music_and_wait(
    request: MusicGenerationRequest,
    tenant = Depends(get_tenant)
):
    """
    Generate music and wait for completion (blocking)
    
    This endpoint will block until the music is generated (up to 5 minutes).
    Use this for synchronous workflows.
    
    WARNING: This may timeout on slow connections. Consider using the
    async /generate + /status polling approach instead.
    """
    try:
        music_service = get_music_service()
        
        # Build enhanced prompt with lyrics if provided
        full_prompt = request.prompt
        if request.lyrics:
            full_prompt = f"{request.prompt}\n\nLyrics:\n{request.lyrics}"
        
        logger.info(f"Starting synchronous music generation for tenant {tenant.get('id')}")
        
        # Start generation
        result = await music_service.generate_music(
            prompt=full_prompt,
            duration_seconds=request.duration_seconds,
            with_vocals=request.with_vocals
        )
        
        task_id = result["task_id"]
        
        # Wait for completion
        final_status = await music_service.wait_for_completion(
            task_id=task_id,
            max_wait_seconds=300,  # 5 minutes max
            poll_interval=10
        )
        
        return MusicStatusResponse(
            task_id=task_id,
            **final_status
        )
        
    except TimeoutError as e:
        logger.error(f"Music generation timeout: {str(e)}")
        raise HTTPException(
            status_code=408,
            detail="Music generation timed out. Use async generation instead."
        )
    except Exception as e:
        logger.error(f"Error in synchronous music generation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate music: {str(e)}"
        )
