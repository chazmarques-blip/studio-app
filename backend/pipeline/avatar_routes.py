"""Pipeline avatar routes: generation, accuracy, 360, variants, video preview, voice."""
import asyncio
import base64
import os
import re
import uuid
import subprocess
import threading
import urllib.request
from datetime import datetime, timezone
from io import BytesIO

from fastapi import Depends, UploadFile, File, Form, HTTPException
from PIL import Image
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai import OpenAITextToSpeech

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger
from pipeline.router import router
from pipeline.config import (
    EMERGENT_PROXY_URL, STORAGE_BUCKET, PREVIEW_TEXTS,
    AvatarGenerateRequest, AvatarAccuracyRequest,
    AvatarVideoPreviewRequest, AvatarVariantRequest,
    AvatarBatch360Request, VoicePreviewRequest,
    MasterVoiceRequest,
)
from pipeline.utils import (
    _upload_to_storage, _describe_person,
    _accuracy_compare, _describe_person_from_video,
    _gemini_edit_image, _gemini_edit_multi_ref,
    _ffprobe_duration,
)
from pipeline.media import _composite_logo_on_avatar
from pipeline.engine import _accuracy_jobs, _preview_jobs, _batch360_jobs


@router.post("/generate-avatar")
async def generate_avatar(req: AvatarGenerateRequest, user=Depends(get_current_user)):
    """Generate a full-body professional avatar from an uploaded photo using AI."""
    try:
        system_msg = (
            "You are an expert portrait photographer. You create stunning full-body professional photos. "
            "CRITICAL: Always output VERTICAL portrait format (taller than wide, approximately 3:5 ratio). "
            "When given a reference photo, preserve the person's EXACT identity — same face, features, skin tone, hair."
        )

        if req.source_image_url:
            img_b64 = None
            mime = "image/png"
            try:
                img_req = urllib.request.Request(req.source_image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=15) as resp:
                    img_data = resp.read()
                    img_b64 = base64.b64encode(img_data).decode("utf-8")
                    content_type = resp.headers.get("Content-Type", "image/png")
                    mime = content_type if content_type.startswith("image/") else "image/png"
            except Exception as dl_err:
                logger.warning(f"Failed to download source image: {dl_err}")

            prompt = (
                "EDIT this photo to create a FULL-BODY professional portrait of this EXACT SAME person. "
                "Do NOT generate a different person. Preserve their EXACT face, features, skin tone, and hair. "
                "Show them standing confidently in a modern studio with soft lighting. "
                "Professional business attire. Full body visible from head to feet. "
                "Clean minimal background. Photorealistic, 4K detail. "
                "OUTPUT FORMAT: VERTICAL portrait (taller than wide, 3:5 ratio)."
            )

            if img_b64:
                # Step 1: Get vision description of the person
                person_desc = await _describe_person(img_b64, mime)

                prompt = (
                    "FOCUS ONLY ON THE PERSON in this photo. IGNORE the background, other people, and scenery completely. "
                    "Create a FULL-BODY professional portrait of this EXACT SAME person. "
                    "Do NOT generate a different person. Preserve their EXACT face, features, skin tone, facial hair, and hair. "
                    "Show them standing confidently in a modern studio with soft lighting. "
                    "Professional business attire. Full body visible from head to feet. "
                    "REPLACE the background with a clean, minimal studio background. "
                    "Photorealistic, 4K detail. "
                    "OUTPUT FORMAT: VERTICAL portrait (taller than wide, 3:5 ratio)."
                )
                if person_desc:
                    prompt = f"PERSON TO FOCUS ON (ignore background and other people): {person_desc}\n\n{prompt}"

                # Step 2: Use direct multimodal call with text+image in SAME message
                images = await _gemini_edit_image(system_msg, prompt, img_b64, mime)
                if images:
                    img_bytes = base64.b64decode(images[0]['data'])
                    filename = f"avatars/avatar_{uuid.uuid4().hex[:8]}.png"
                    public_url = _upload_to_storage(img_bytes, filename, "image/png")
                    return {"avatar_url": public_url}

        # Fallback: no source image or image download failed
        prompt = (
            f"Professional full-body portrait of a confident business presenter"
            f"{' for ' + req.company_name if req.company_name else ''}. "
            "Standing in a modern studio, professional attire, warm smile, looking at camera. "
            "Full body visible from head to feet. Clean minimal background. "
            "Photorealistic, 4K detail. "
            "OUTPUT FORMAT: VERTICAL portrait (taller than wide, 3:5 ratio)."
        )
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"avatar-{uuid.uuid4().hex[:8]}",
            system_message=system_msg
        )
        msg = UserMessage(text=prompt)
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        text_response, images = await chat.send_message_multimodal_response(msg)

        if images and len(images) > 0:
            img_bytes = base64.b64decode(images[0]['data'])
            filename = f"avatars/avatar_{uuid.uuid4().hex[:8]}.png"
            public_url = _upload_to_storage(img_bytes, filename, "image/png")
            return {"avatar_url": public_url}
        raise HTTPException(status_code=500, detail="AI não gerou a imagem. Tente novamente.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


_accuracy_jobs = {}




def _run_accuracy_generation(job_id: str, source_image_url: str, video_frame_urls: list, company_name: str, logo_url: str, max_iterations: int):
    """Background thread: generate avatar with accuracy agent feedback loop."""
    import asyncio
    import json
    loop = asyncio.new_event_loop()
    try:
        # Download source image (primary reference)
        img_b64 = None
        mime = "image/png"
        try:
            img_req = urllib.request.Request(source_image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, timeout=15) as resp:
                img_data = resp.read()
                img_b64 = base64.b64encode(img_data).decode("utf-8")
                content_type = resp.headers.get("Content-Type", "image/png")
                mime = content_type if content_type.startswith("image/") else "image/png"
        except Exception as dl_err:
            logger.warning(f"Failed to download source image: {dl_err}")
            _accuracy_jobs[job_id] = {"status": "failed", "error": f"Failed to download source: {dl_err}"}
            return

        if not img_b64:
            _accuracy_jobs[job_id] = {"status": "failed", "error": "Could not read source image"}
            return

        # Download video frames for additional reference
        extra_frames_b64 = []
        for frame_url in (video_frame_urls or [])[:3]:
            try:
                freq = urllib.request.Request(frame_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(freq, timeout=10) as fresp:
                    fdata = fresp.read()
                    fb64 = base64.b64encode(fdata).decode("utf-8")
                    fct = fresp.headers.get("Content-Type", "image/png")
                    fmime = fct if fct.startswith("image/") else "image/png"
                    extra_frames_b64.append({"data": fb64, "mime": fmime})
            except Exception as fe:
                logger.warning(f"Failed to download video frame: {fe}")

        # Step 1: Get vision description — use photo as primary
        AGENTS = [
            {"name": "Scanner", "role": "Analyzing reference"},
            {"name": "Artist", "role": "Generating avatar"},
            {"name": "Critic", "role": "Evaluating accuracy"},
        ]
        _accuracy_jobs[job_id] = {"status": "processing", "progress": "Analyzing reference photo...", "iteration": 0, "iterations": [], "agents": AGENTS, "active_agent": "Scanner"}
        person_desc = loop.run_until_complete(_describe_person(img_b64, mime))

        # Enhance description with video frames if available
        if extra_frames_b64:
            _accuracy_jobs[job_id]["progress"] = "Analyzing video frames for enhanced identity..."
            video_desc = loop.run_until_complete(_describe_person_from_video(extra_frames_b64))
            if video_desc:
                person_desc = f"{person_desc}\nADDITIONAL DETAILS FROM VIDEO: {video_desc}"
                logger.info(f"Enhanced desc with video: {video_desc[:100]}...")

        system_msg = (
            "You are a professional photo editor. You edit existing photos of real people. "
            "ABSOLUTE RULE: The person in the output MUST be IDENTICAL to the person in the input photo. "
            "You only change clothing, background, and pose. The face, body, skin, and hair stay EXACTLY the same. "
            "Output VERTICAL format (taller than wide, 3:5 ratio)."
        )

        iterations = []
        extra_feedback = ""

        for attempt in range(max_iterations):
            _accuracy_jobs[job_id] = {
                "status": "processing",
                "progress": f"Generating avatar (attempt {attempt + 1}/{max_iterations})...",
                "iteration": attempt + 1,
                "iterations": iterations,
                "agents": AGENTS,
                "active_agent": "Artist",
            }

            prompt = (
                "EDIT this photo of this person. Do NOT create a new person. Keep THIS EXACT person.\n\n"
                "CHANGES TO MAKE:\n"
                "1. CLOTHING: Change to a clean plain white polo shirt (completely blank, no logos), "
                "black dress pants, white sneakers\n"
                "2. BACKGROUND: Change to a clean professional photo studio with soft lighting\n"
                "3. POSE: Standing full body, slight smile, arms relaxed\n"
                "4. FRAMING: Full body head to feet, VERTICAL portrait format\n\n"
                "DO NOT CHANGE:\n"
                "- The person's face (every detail must stay identical)\n"
                "- Skin tone and complexion\n"
                "- Hair color, style, and length\n"
                "- Facial hair pattern\n"
                "- Body build and proportions\n"
                "- Remove sunglasses if worn, showing the person's natural eyes"
            )
            if person_desc and attempt == 0:
                # Include key identity features in the prompt
                prompt += f"\n\nIMPORTANT - Person identity details to preserve: {person_desc[:400]}"
            elif person_desc:
                # On retry, include a shorter reminder
                prompt += f"\n\nPerson: {person_desc[:200]}"
            if extra_feedback:
                prompt += f"\n\nFIX THESE ISSUES: {extra_feedback}"

            # Use primary photo as the ONLY visual reference (video frames enhance text description only)
            images = loop.run_until_complete(_gemini_edit_image(system_msg, prompt, img_b64, mime))
            if not images:
                iterations.append({"attempt": attempt + 1, "url": None, "score": 0, "feedback": "Generation failed", "passed": False})
                continue

            # Upload generated avatar (with logo composited if available)
            gen_bytes = base64.b64decode(images[0]['data'])
            gen_b64 = images[0]['data']
            gen_mime = images[0].get('mime_type', 'image/png')

            # Composite company logo onto the shirt if logo_url is provided
            if logo_url:
                try:
                    logo_req = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(logo_req, timeout=10) as logo_resp:
                        logo_bytes = logo_resp.read()
                    gen_bytes = _composite_logo_on_avatar(gen_bytes, logo_bytes)
                    gen_b64 = base64.b64encode(gen_bytes).decode("utf-8")
                    logger.info("Logo composited onto avatar successfully")
                except Exception as logo_err:
                    logger.warning(f"Logo download/composite failed: {logo_err}")

            filename = f"avatars/avatar_acc_{uuid.uuid4().hex[:8]}.png"
            avatar_url = _upload_to_storage(gen_bytes, filename, "image/png")

            # Accuracy comparison
            _accuracy_jobs[job_id]["progress"] = f"Evaluating accuracy (attempt {attempt + 1})..."
            _accuracy_jobs[job_id]["active_agent"] = "Critic"
            comparison = loop.run_until_complete(_accuracy_compare(img_b64, mime, gen_b64, gen_mime))

            iteration_result = {
                "attempt": attempt + 1,
                "url": avatar_url,
                "score": comparison["score"],
                "feedback": comparison["feedback"],
                "passed": comparison["passed"],
            }
            iterations.append(iteration_result)

            _accuracy_jobs[job_id]["iterations"] = iterations

            if comparison["passed"]:
                logger.info(f"Accuracy agent APPROVED avatar on attempt {attempt + 1} (score: {comparison['score']}/10)")
                _accuracy_jobs[job_id] = {
                    "status": "completed",
                    "avatar_url": avatar_url,
                    "iterations": iterations,
                    "final_score": comparison["score"],
                    "agents": AGENTS,
                    "active_agent": None,
                }
                return

            # Not passed - prepare feedback for next iteration
            extra_feedback = comparison["feedback"]
            logger.info(f"Accuracy agent REJECTED attempt {attempt + 1} (score: {comparison['score']}/10): {extra_feedback}")

        # All iterations exhausted - return best one
        best = max(iterations, key=lambda x: x.get("score", 0)) if iterations else None
        if best and best.get("url"):
            _accuracy_jobs[job_id] = {
                "status": "completed",
                "avatar_url": best["url"],
                "iterations": iterations,
                "final_score": best["score"],
                "note": "best_of_attempts",
            }
        else:
            _accuracy_jobs[job_id] = {"status": "failed", "error": "All generation attempts failed", "iterations": iterations}

    except Exception as e:
        logger.error(f"Accuracy avatar generation failed: {e}")
        _accuracy_jobs[job_id] = {"status": "failed", "error": str(e), "iterations": _accuracy_jobs.get(job_id, {}).get("iterations", [])}
    finally:
        loop.close()




@router.post("/generate-avatar-with-accuracy")
async def generate_avatar_with_accuracy(req: AvatarAccuracyRequest, user=Depends(get_current_user)):
    """Start avatar generation with accuracy agent feedback loop. Returns job_id for polling."""
    job_id = uuid.uuid4().hex[:10]
    _accuracy_jobs[job_id] = {"status": "processing", "progress": "Starting...", "iteration": 0, "iterations": []}
    thread = threading.Thread(
        target=_run_accuracy_generation,
        args=(job_id, req.source_image_url, req.video_frame_urls, req.company_name, req.logo_url, min(req.max_iterations, 3)),
        daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "processing"}


@router.get("/generate-avatar-with-accuracy/{job_id}")
async def get_avatar_accuracy_status(job_id: str, user=Depends(get_current_user)):
    """Poll for avatar accuracy generation status."""
    job = _accuracy_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Accuracy job not found")
    return job




@router.post("/extract-from-video")
async def extract_from_video(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Extract best frame (image) and audio from an uploaded video for avatar creation.
    Returns: { frame_url, audio_url, duration }"""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    try:
        video_bytes = await file.read()
        if len(video_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Video exceeds 50MB limit")

        uid = uuid.uuid4().hex[:8]
        video_path = f"/tmp/avatar_video_{uid}.mp4"
        with open(video_path, "wb") as f:
            f.write(video_bytes)

        # Get video duration
        duration = _ffprobe_duration(video_path) or 10.0

        # Extract best frame at 1/3 of video (person usually well-positioned)
        frame_time = min(duration / 3, 5.0)
        frame_path = f"/tmp/avatar_frame_{uid}.jpg"
        r = subprocess.run(
            [FFMPEG_PATH, "-y", "-ss", str(frame_time), "-i", video_path,
             "-vframes", "1", "-q:v", "2", frame_path],
            capture_output=True, timeout=30
        )
        if r.returncode != 0 or not os.path.exists(frame_path):
            # Fallback: try frame at 0s
            subprocess.run(
                [FFMPEG_PATH, "-y", "-i", video_path, "-vframes", "1", "-q:v", "2", frame_path],
                capture_output=True, timeout=30
            )

        # Extract additional frames at different times for enhanced identity
        extra_frame_urls = []
        frame_times = [max(0.5, duration * 0.15), max(1.0, duration * 0.5), max(1.5, duration * 0.75)]
        for i, ft in enumerate(frame_times):
            if ft >= duration:
                continue
            ef_path = f"/tmp/avatar_frame_{uid}_extra_{i}.jpg"
            ef_r = subprocess.run(
                [FFMPEG_PATH, "-y", "-ss", str(ft), "-i", video_path,
                 "-vframes", "1", "-q:v", "2", ef_path],
                capture_output=True, timeout=15
            )
            if ef_r.returncode == 0 and os.path.exists(ef_path) and os.path.getsize(ef_path) > 500:
                with open(ef_path, "rb") as ef:
                    ef_bytes = ef.read()
                ef_filename = f"avatars/video_frame_{uid}_extra_{i}.jpg"
                ef_url = _upload_to_storage(ef_bytes, ef_filename, "image/jpeg")
                extra_frame_urls.append(ef_url)
            if os.path.exists(ef_path):
                try:
                    os.remove(ef_path)
                except Exception:
                    pass

        # Extract audio
        audio_path = f"/tmp/avatar_audio_{uid}.mp3"
        r2 = subprocess.run(
            [FFMPEG_PATH, "-y", "-i", video_path, "-vn",
             "-acodec", "libmp3lame", "-ab", "192k", "-ar", "44100", audio_path],
            capture_output=True, timeout=60
        )
        audio_url = None
        if r2.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 500:
            with open(audio_path, "rb") as af:
                audio_bytes_data = af.read()
            audio_filename = f"voice_recordings/video_voice_{uid}.mp3"
            audio_url = _upload_to_storage(audio_bytes_data, audio_filename, "audio/mpeg")
            logger.info(f"Extracted audio from video: {audio_filename} ({len(audio_bytes_data)/1024:.0f}KB)")

        # Upload frame
        frame_url = None
        if os.path.exists(frame_path) and os.path.getsize(frame_path) > 500:
            with open(frame_path, "rb") as ff:
                frame_bytes = ff.read()
            frame_filename = f"avatars/video_frame_{uid}.jpg"
            frame_url = _upload_to_storage(frame_bytes, frame_filename, "image/jpeg")
            logger.info(f"Extracted frame from video: {frame_filename}")

        # Cleanup
        for p in [video_path, frame_path, audio_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        if not frame_url:
            raise HTTPException(status_code=500, detail="Could not extract frame from video")

        return {
            "frame_url": frame_url,
            "audio_url": audio_url,
            "duration": round(duration, 1),
            "extra_frame_urls": extra_frame_urls,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/voice-preview")
async def voice_preview(req: VoicePreviewRequest, user=Depends(get_current_user)):
    """Generate a short voice preview using OpenAI TTS."""
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if req.voice_id not in valid_voices:
        raise HTTPException(status_code=400, detail=f"Invalid voice. Choose from: {', '.join(valid_voices)}")
    try:
        tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
        audio_bytes = await tts.generate_speech(
            text=req.text[:200], model="tts-1-hd",
            voice=req.voice_id, speed=1.0, response_format="mp3"
        )
        filename = f"voice_previews/preview_{req.voice_id}_{uuid.uuid4().hex[:6]}.mp3"
        public_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
        return {"audio_url": public_url, "voice_id": req.voice_id}
    except Exception as e:
        logger.error(f"Voice preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/upload-voice-recording")
async def upload_voice_recording(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload a custom voice recording."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File exceeds 20MB limit")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "webm"
        filename = f"voice_recordings/recording_{uuid.uuid4().hex[:8]}.{ext}"
        content_type = file.content_type or "audio/webm"
        public_url = _upload_to_storage(audio_bytes, filename, content_type)
        return {"audio_url": public_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/master-voice")
async def master_voice(req: MasterVoiceRequest, user=Depends(get_current_user)):
    """Masterize voice: noise reduction, EQ, compression, normalization — keeps original character."""
    try:
        # Download original audio
        audio_data = urllib.request.urlopen(req.audio_url, timeout=30).read()
        if not audio_data or len(audio_data) < 500:
            raise HTTPException(status_code=400, detail="Could not download audio")

        uid = uuid.uuid4().hex[:8]
        input_path = f"/tmp/voice_raw_{uid}.mp3"
        output_path = f"/tmp/voice_master_{uid}.mp3"
        with open(input_path, "wb") as f:
            f.write(audio_data)

        # FFmpeg mastering chain:
        # 1. highpass=80 — remove low rumble/hum
        # 2. lowpass=12000 — remove high freq hiss
        # 3. afftdn — adaptive noise reduction
        # 4. acompressor — gentle compression for consistent volume
        # 5. equalizer — boost presence (2-4kHz) for clarity
        # 6. loudnorm — normalize loudness to broadcast standard
        filter_chain = (
            "highpass=f=80,"
            "lowpass=f=12000,"
            "afftdn=nf=-25:nr=10:nt=w,"
            "acompressor=threshold=-20dB:ratio=3:attack=5:release=50:makeup=2,"
            "equalizer=f=3000:t=q:w=1.5:g=3,"
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        )
        r = subprocess.run(
            [FFMPEG_PATH, "-y", "-i", input_path, "-af", filter_chain,
             "-acodec", "libmp3lame", "-ab", "192k", "-ar", "44100", output_path],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0 or not os.path.exists(output_path):
            logger.warning(f"Voice mastering failed: {r.stderr[:300] if r.stderr else ''}")
            raise HTTPException(status_code=500, detail="Mastering failed")

        with open(output_path, "rb") as f:
            mastered_bytes = f.read()
        filename = f"voice_recordings/mastered_{uid}.mp3"
        public_url = _upload_to_storage(mastered_bytes, filename, "audio/mpeg")
        logger.info(f"Voice mastered: {len(audio_data)/1024:.0f}KB → {len(mastered_bytes)/1024:.0f}KB")

        # Cleanup
        for p in [input_path, output_path]:
            try: os.remove(p)
            except: pass

        return {"audio_url": public_url, "original_size": len(audio_data), "mastered_size": len(mastered_bytes)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice mastering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


_preview_jobs = {}

PREVIEW_TEXTS = {
    "pt": "Olá! Sou seu apresentador virtual, pronto para representar sua marca!",
    "en": "Hello! I'm your virtual presenter, ready to represent your brand!",
    "es": "Hola! Soy tu presentador virtual, listo para representar tu marca!",
}



def _run_preview_generation(job_id: str, avatar_url: str, voice_url: str, voice_id: str, language: str):
    """Background thread: generate TTS audio (if needed) then lip-sync video with Kling Avatar."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        text = PREVIEW_TEXTS.get(language, PREVIEW_TEXTS["pt"])
        audio_url = voice_url  # Use custom voice if available

        # If no custom voice, generate TTS audio
        if not audio_url:
            tts_voice = voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "onyx"
            tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
            audio_bytes = loop.run_until_complete(tts.generate_speech(
                text=text, model="tts-1-hd",
                voice=tts_voice, speed=1.0, response_format="mp3"
            ))
            audio_filename = f"voice_previews/preview_tts_{uuid.uuid4().hex[:6]}.mp3"
            audio_url = _upload_to_storage(audio_bytes, audio_filename, "audio/mpeg")
            logger.info(f"Preview TTS audio generated: {audio_filename}")

        _preview_jobs[job_id] = {"status": "generating_video", "progress": "Lip-sync..."}

        # Generate lip-sync video with Kling Avatar v2
        fal_key = os.environ.get("FAL_KEY")
        if not fal_key:
            _preview_jobs[job_id] = {"status": "failed", "error": "FAL_KEY not configured"}
            return

        import fal_client
        os.environ["FAL_KEY"] = fal_key
        handler = loop.run_until_complete(fal_client.submit_async(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": avatar_url,
                "audio_url": audio_url,
            }
        ))
        result = loop.run_until_complete(handler.get())
        video_url = result.get("video", {}).get("url") if result else None

        if video_url:
            _preview_jobs[job_id] = {"status": "completed", "video_url": video_url}
            logger.info(f"Preview lip-sync video generated: {video_url}")
        else:
            _preview_jobs[job_id] = {"status": "failed", "error": "Kling returned no video"}
    except Exception as e:
        logger.error(f"Avatar video preview failed: {e}")
        _preview_jobs[job_id] = {"status": "failed", "error": str(e)}
    finally:
        loop.close()



@router.post("/avatar-video-preview")
async def avatar_video_preview(req: AvatarVideoPreviewRequest, user=Depends(get_current_user)):
    """Start avatar video preview generation with lip-sync. Returns job_id for polling."""
    job_id = uuid.uuid4().hex[:10]
    _preview_jobs[job_id] = {"status": "processing", "progress": "Starting..."}
    thread = threading.Thread(
        target=_run_preview_generation,
        args=(job_id, req.avatar_url, req.voice_url, req.voice_id, req.language),
        daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "processing"}

@router.get("/avatar-video-preview/{job_id}")
async def get_avatar_video_preview(job_id: str, user=Depends(get_current_user)):
    """Poll for avatar video preview generation status."""
    job = _preview_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Preview job not found")
    return job


@router.post("/generate-avatar-variant")
async def generate_avatar_variant(req: AvatarVariantRequest, user=Depends(get_current_user)):
    """Generate an avatar variant with different clothing or angle."""
    CLOTHING_MAP = {
        "company_uniform": "wearing a crisp plain white polo shirt (no logos, no text, completely blank), fitted black dress pants, and clean white sneakers (sapatênis style)",
        "business_formal": "wearing a tailored dark navy business suit, white dress shirt, elegant tie",
        "casual": "wearing a casual smart outfit, clean jeans, stylish blazer over a t-shirt",
        "streetwear": "wearing trendy streetwear, designer hoodie, sneakers, modern urban style",
        "creative": "wearing an artistic creative outfit, colorful patterns, unique accessories",
    }
    ANGLE_MAP = {
        "front": "facing directly towards the camera, front view, looking straight at the viewer",
        "left_profile": "body and face turned to THEIR LEFT, showing the LEFT side of the face and body in profile view, camera positioned to their right capturing the left cheek",
        "right_profile": "body and face turned to THEIR RIGHT, showing the RIGHT side of the face and body in profile view, camera positioned to their left capturing the right cheek",
        "back": "turned completely away from camera showing their back, we see the back of their head and body, looking slightly over their right shoulder",
    }
    clothing_desc = CLOTHING_MAP.get(req.clothing, CLOTHING_MAP["company_uniform"])
    angle_desc = ANGLE_MAP.get(req.angle, ANGLE_MAP["front"])
    try:
        system_msg = (
            "You are an expert at editing portrait photographs while preserving the person's EXACT identity. "
            "CRITICAL RULE: The person in the output MUST be the EXACT SAME individual as in the input photo — "
            "same face shape, same eyes, same nose, same mouth, same skin tone, same hair color and style, "
            "same body build. Do NOT generate a different person. Do NOT change their appearance. "
            "Only change their clothing and camera angle as instructed. "
            "The output must be VERTICAL portrait format (taller than wide, approximately 3:5 ratio)."
        )
        prompt = (
            f"EDIT this photo of this EXACT person. Do NOT replace them with a different person.\n\n"
            f"CHANGE ONLY:\n"
            f"1. CLOTHING: Dress them in: {clothing_desc}\n"
            f"2. POSE/ANGLE: Reposition them so they are {angle_desc}\n\n"
            f"KEEP EXACTLY THE SAME:\n"
            f"- Their face (every detail — eyes, nose, mouth, jawline, eyebrows)\n"
            f"- Their skin tone and complexion\n"
            f"- Their hair color, style, and length\n"
            f"- Their body build and proportions\n\n"
            f"OUTPUT: Full-body portrait, VERTICAL format (taller than wide, 3:5 ratio), "
            f"head to feet visible, modern photo studio, soft professional lighting, clean minimal background. "
            f"Photorealistic, 4K detail."
        )

        if req.source_image_url:
            img_b64 = None
            mime = "image/png"
            try:
                img_req = urllib.request.Request(req.source_image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=15) as resp:
                    img_data = resp.read()
                    img_b64 = base64.b64encode(img_data).decode("utf-8")
                    content_type = resp.headers.get("Content-Type", "image/png")
                    mime = content_type if content_type.startswith("image/") else "image/png"
            except Exception as dl_err:
                logger.warning(f"Failed to download source image: {dl_err}")

            if img_b64:
                # Step 1: Get vision description for identity preservation
                person_desc = await _describe_person(img_b64, mime)
                if person_desc:
                    prompt = f"PERSON IDENTITY (must match EXACTLY): {person_desc}\n\n{prompt}"

                images = await _gemini_edit_image(system_msg, prompt, img_b64, mime)
                if images:
                    img_bytes = base64.b64decode(images[0]['data'])
                    # Composite logo if it's company_uniform and logo_url provided
                    if req.clothing == "company_uniform" and req.logo_url:
                        try:
                            logo_req_dl = urllib.request.Request(req.logo_url, headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(logo_req_dl, timeout=10) as logo_resp:
                                logo_bytes = logo_resp.read()
                            img_bytes = _composite_logo_on_avatar(img_bytes, logo_bytes)
                        except Exception as le:
                            logger.warning(f"Variant logo composite failed: {le}")
                    filename = f"avatars/avatar_var_{uuid.uuid4().hex[:8]}.png"
                    public_url = _upload_to_storage(img_bytes, filename, "image/png")
                    return {"avatar_url": public_url, "clothing": req.clothing, "angle": req.angle}

        # Fallback without image reference
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"avatar-var-{uuid.uuid4().hex[:8]}",
            system_message=system_msg
        )
        msg = UserMessage(text=prompt)
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        text_response, images = await chat.send_message_multimodal_response(msg)
        if images and len(images) > 0:
            img_bytes = base64.b64decode(images[0]['data'])
            filename = f"avatars/avatar_var_{uuid.uuid4().hex[:8]}.png"
            public_url = _upload_to_storage(img_bytes, filename, "image/png")
            return {"avatar_url": public_url, "clothing": req.clothing, "angle": req.angle}
        raise HTTPException(status_code=500, detail="AI failed to generate image. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar variant generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


_batch360_jobs = {}



def _run_batch_360(job_id: str, source_url: str, clothing: str, logo_url: str = ""):
    """Background thread to generate all 4 angles for an avatar."""
    import asyncio
    CLOTHING_MAP = {
        "company_uniform": "wearing a crisp plain white polo shirt (no logos, no text, completely blank), fitted black dress pants, and clean white sneakers (sapatênis style)",
        "business_formal": "wearing a tailored dark navy business suit, white dress shirt, elegant tie",
        "casual": "wearing a casual smart outfit, clean jeans, stylish blazer over a t-shirt",
        "streetwear": "wearing trendy streetwear, designer hoodie, sneakers, modern urban style",
        "creative": "wearing an artistic creative outfit, colorful patterns, unique accessories",
    }
    ANGLE_MAP = {
        "front": "facing directly towards the camera, front view, looking straight at the viewer",
        "left_profile": "body and face turned to THEIR LEFT, showing the LEFT side profile view",
        "right_profile": "body and face turned to THEIR RIGHT, showing the RIGHT side profile view",
        "back": "turned completely away from camera showing their back, looking slightly over shoulder",
    }
    clothing_desc = CLOTHING_MAP.get(clothing, CLOTHING_MAP["company_uniform"])
    system_msg = (
        "You are an expert at editing portrait photographs while preserving the person's EXACT identity. "
        "CRITICAL RULE: The person in the output MUST be the EXACT SAME individual as in the input photo — "
        "same face shape, same eyes, same nose, same mouth, same skin tone, same hair color and style, "
        "same body build. Do NOT generate a different person. Do NOT change their appearance. "
        "Only change their clothing and camera angle as instructed. "
        "The output must be VERTICAL portrait format (taller than wide, approximately 3:5 ratio)."
    )

    # Download source image once
    img_b64 = None
    mime = "image/png"
    try:
        img_req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(img_req, timeout=15) as resp:
            img_data = resp.read()
            img_b64 = base64.b64encode(img_data).decode("utf-8")
            ct = resp.headers.get("Content-Type", "image/png")
            mime = ct if ct.startswith("image/") else "image/png"
    except Exception as e:
        logger.error(f"Batch 360: Failed to download source: {e}")
        _batch360_jobs[job_id] = {"status": "failed", "error": str(e)}
        return

    loop = asyncio.new_event_loop()

    # Step 1: Get vision description for identity preservation
    person_desc = loop.run_until_complete(_describe_person(img_b64, mime))

    results = {}
    for angle_key, angle_desc in ANGLE_MAP.items():
        try:
            prompt = (
                f"EDIT this photo of this EXACT person. Do NOT replace them with a different person.\n\n"
                f"CHANGE ONLY:\n"
                f"1. CLOTHING: Dress them in: {clothing_desc}\n"
                f"2. POSE/ANGLE: Reposition them so they are {angle_desc}\n\n"
                f"KEEP EXACTLY THE SAME:\n"
                f"- Their face (every detail — eyes, nose, mouth, jawline, eyebrows)\n"
                f"- Their skin tone and complexion\n"
                f"- Their hair color, style, and length\n"
                f"- Their body build and proportions\n\n"
                f"OUTPUT: Full-body portrait, VERTICAL format (taller than wide, 3:5 ratio), "
                f"head to feet visible, modern photo studio, soft professional lighting, clean minimal background. "
                f"Photorealistic, 4K detail."
            )
            if person_desc:
                prompt = f"PERSON IDENTITY (must match EXACTLY): {person_desc}\n\n{prompt}"

            images = loop.run_until_complete(_gemini_edit_image(system_msg, prompt, img_b64, mime))
            if images:
                img_bytes = base64.b64decode(images[0]['data'])
                # Composite logo for company_uniform (front/left/right only, not back)
                if clothing == "company_uniform" and logo_url and angle_key != "back":
                    try:
                        logo_req_dl = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(logo_req_dl, timeout=10) as logo_resp:
                            logo_bytes_data = logo_resp.read()
                        img_bytes = _composite_logo_on_avatar(img_bytes, logo_bytes_data)
                    except Exception as le:
                        logger.warning(f"360 logo composite failed for {angle_key}: {le}")
                filename = f"avatars/avatar_360_{angle_key}_{uuid.uuid4().hex[:6]}.png"
                public_url = _upload_to_storage(img_bytes, filename, "image/png")
                results[angle_key] = public_url
                logger.info(f"Batch 360: {angle_key} done")
            else:
                results[angle_key] = None
                logger.warning(f"Batch 360: {angle_key} returned no images")
        except Exception as e:
            logger.error(f"Batch 360: {angle_key} failed: {e}")
            results[angle_key] = None
        # Update progress
        _batch360_jobs[job_id] = {"status": "processing", "results": results, "completed": len([v for v in results.values() if v])}

    loop.close()
    _batch360_jobs[job_id] = {"status": "completed", "results": results}



@router.post("/generate-avatar-360")
async def generate_avatar_360(req: AvatarBatch360Request, user=Depends(get_current_user)):
    """Start batch generation of all 4 angles for an avatar (background job with polling)."""
    job_id = uuid.uuid4().hex[:10]
    _batch360_jobs[job_id] = {"status": "processing", "results": {}, "completed": 0}
    thread = threading.Thread(target=_run_batch_360, args=(job_id, req.source_image_url, req.clothing, req.logo_url), daemon=True)
    thread.start()
    return {"job_id": job_id, "status": "processing"}

@router.get("/generate-avatar-360/{job_id}")
async def get_avatar_360_status(job_id: str, user=Depends(get_current_user)):
    """Poll for batch 360 generation status."""
    job = _batch360_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job






@router.post("/generate-presenter-video")
async def generate_presenter_video_endpoint(
    pipeline_id: str = Form(""),
    avatar_url: str = Form(""),
    audio_url: str = Form(""),
    user=Depends(get_current_user)
):
    """Generate a talking-head presenter video using fal.ai Kling Avatar v2.
    Requires FAL_KEY in environment."""
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise HTTPException(status_code=503, detail="Presenter video requires FAL_KEY configuration. Contact admin.")
    try:
        import fal_client
        os.environ["FAL_KEY"] = fal_key
        handler = await fal_client.submit_async(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": avatar_url,
                "audio_url": audio_url,
            }
        )
        result = await handler.get()
        video_url = result.get("video", {}).get("url") if result else None
        if video_url:
            return {"video_url": video_url}
        raise HTTPException(status_code=500, detail="Presenter video generation returned no video")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Presenter video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))




