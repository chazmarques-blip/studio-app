"""
Studio Router: Regenerate Scene Audio Only
Regenerates narration/audio for a scene without regenerating the video.
Useful for fixing language issues or adjusting dialogue without expensive video regeneration.
"""

from fastapi import APIRouter, Body, HTTPException
from ._shared import *

router = APIRouter()


@router.post("/projects/{project_id}/scenes/{scene_num}/regenerate-audio")
async def regenerate_scene_audio_only(
    project_id: str,
    scene_num: int,
    payload: dict = Body(...)
):
    """
    Regenerate only the audio/narration for a specific scene.
    Keeps the existing video intact and replaces only the audio track.
    
    Payload:
        - narration: str - New narration text
        - language: str - Language code (pt, en, es, etc.)
    
    Returns updated scene output with new audio
    """
    try:
        logger.info(f"Studio [{project_id}]: Regenerating audio for scene {scene_num}")
        
        # Get project
        project = await _get_project(project_id)
        if not project:
            raise HTTPException(404, "Project not found")
        
        scenes = project.get("scenes", [])
        scene = next((s for s in scenes if s.get("scene_number") == scene_num), None)
        if not scene:
            raise HTTPException(404, f"Scene {scene_num} not found")
        
        # Get parameters
        narration_text = payload.get("narration", scene.get("dialogue", ""))
        language = payload.get("language", project.get("language", "pt"))
        
        logger.info(f"Studio [{project_id}]: Audio regen - Language: {language}, Text length: {len(narration_text)}")
        
        # Find existing video output
        outputs = project.get("outputs", [])
        video_output = next((o for o in outputs if o.get("scene_number") == scene_num and o.get("type") == "video"), None)
        
        if not video_output or not video_output.get("url"):
            raise HTTPException(400, f"Scene {scene_num} has no video to attach audio to")
        
        # Get character voices mapping
        characters = project.get("characters", [])
        voice_map = {ch.get("name"): ch.get("voice_id") for ch in characters if ch.get("voice_id")}
        
        # Extract character from narration (simple heuristic)
        # Format: "CharName: dialogue text" or "Narrador: text"
        narrator_char = None
        if ":" in narration_text:
            parts = narration_text.split(":", 1)
            possible_char = parts[0].strip()
            if possible_char in voice_map:
                narrator_char = possible_char
        
        # Generate audio with ElevenLabs
        elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY")
        if not elevenlabs_key:
            raise HTTPException(500, "ElevenLabs API key not configured")
        
        # Default voice if no character match
        voice_id = voice_map.get(narrator_char, "21m00Tcm4TlvDq8ikWAM")  # Default: Rachel
        
        logger.info(f"Studio [{project_id}]: Generating audio - Voice: {voice_id}, Character: {narrator_char or 'Default'}")
        
        # Call ElevenLabs TTS
        import requests
        from elevenlabs import ElevenLabs
        
        client = ElevenLabs(api_key=elevenlabs_key)
        
        # Map language code to ElevenLabs language model
        LANGUAGE_MODELS = {
            "pt": "eleven_turbo_v2_5",
            "en": "eleven_turbo_v2_5",
            "es": "eleven_turbo_v2_5",
            "fr": "eleven_turbo_v2_5",
            "de": "eleven_turbo_v2_5",
            "it": "eleven_turbo_v2_5",
            "ja": "eleven_turbo_v2_5",
            "zh": "eleven_turbo_v2_5",
        }
        model = LANGUAGE_MODELS.get(language, "eleven_turbo_v2_5")
        
        # Generate audio
        audio_response = client.text_to_speech.convert(
            voice_id=voice_id,
            text=narration_text,
            model_id=model,
            output_format="mp3_44100_128"
        )
        
        # Collect audio bytes
        audio_bytes = b"".join(audio_response)
        
        logger.info(f"Studio [{project_id}]: Audio generated - {len(audio_bytes)} bytes")
        
        # Download existing video
        import tempfile
        import subprocess
        
        video_url = video_output["url"]
        video_temp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        audio_temp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        output_temp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        
        try:
            # Download video
            video_resp = requests.get(video_url, timeout=60)
            video_temp.write(video_resp.content)
            video_temp.close()
            
            # Write audio
            audio_temp.write(audio_bytes)
            audio_temp.close()
            
            # Merge audio with video using FFmpeg
            # Replace audio track, keep video as-is
            cmd = [
                "ffmpeg", "-y",
                "-i", video_temp.name,  # Input video
                "-i", audio_temp.name,  # Input audio
                "-map", "0:v:0",        # Use video from first input
                "-map", "1:a:0",        # Use audio from second input
                "-c:v", "copy",         # Copy video codec (no re-encoding)
                "-c:a", "aac",          # Encode audio as AAC
                "-shortest",            # Match shortest duration
                output_temp.name
            ]
            
            logger.info(f"Studio [{project_id}]: FFmpeg merge: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise HTTPException(500, f"FFmpeg audio merge failed: {result.stderr}")
            
            # Read merged video
            with open(output_temp.name, "rb") as f:
                merged_video_bytes = f.read()
            
            logger.info(f"Studio [{project_id}]: Merged video - {len(merged_video_bytes)} bytes")
            
            # Upload to storage
            file_name = f"scene_{scene_num}_audio_regen_{uuid.uuid4().hex[:8]}.mp4"
            new_video_url = await _upload_to_storage(merged_video_bytes, file_name, "video/mp4")
            
            logger.info(f"Studio [{project_id}]: New video uploaded: {new_video_url}")
            
            # Update output in project
            for output in outputs:
                if output.get("scene_number") == scene_num and output.get("type") == "video":
                    output["url"] = new_video_url
                    output["audio_regenerated"] = True
                    output["audio_language"] = language
                    break
            
            # Update scene dialogue if changed
            for s in scenes:
                if s.get("scene_number") == scene_num:
                    s["dialogue"] = narration_text
                    break
            
            # Save project
            await _save_project(project, flush_now=True)
            
            logger.info(f"Studio [{project_id}]: Scene {scene_num} audio regenerated successfully")
            
            return {
                "success": True,
                "scene_number": scene_num,
                "new_video_url": new_video_url,
                "audio_language": language,
                "narration": narration_text
            }
            
        finally:
            # Cleanup temp files
            try:
                os.unlink(video_temp.name)
                os.unlink(audio_temp.name)
                os.unlink(output_temp.name)
            except:
                pass
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Studio [{project_id}]: Audio regen error for scene {scene_num}")
        raise HTTPException(500, f"Failed to regenerate audio: {str(e)}")
