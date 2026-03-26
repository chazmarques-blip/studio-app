"""Storyboard Animated Preview — Generate slideshow MP4 with narration from storyboard panels.

Uses FFmpeg for video assembly, ElevenLabs for narration, and supports Ken Burns effect.
"""
import os
import subprocess
import tempfile
import logging
import urllib.request
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _download_file(url: str, dest: str, retries: int = 3):
    """Download file with retry logic."""
    supabase_url = os.environ.get('SUPABASE_URL', '')
    full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
    for attempt in range(retries):
        try:
            urllib.request.urlretrieve(full_url, dest)
            return True
        except Exception as e:
            logger.warning(f"Download attempt {attempt+1} failed for {full_url}: {e}")
            if attempt == retries - 1:
                return False
    return False


def _generate_panel_narration(text: str, voice_id: str, lang: str = "pt") -> bytes:
    """Generate narration audio for a panel using ElevenLabs."""
    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    if not elevenlabs_key:
        raise RuntimeError("ELEVENLABS_API_KEY not configured")

    from elevenlabs import ElevenLabs as ELClient, VoiceSettings

    client = ELClient(api_key=elevenlabs_key)
    voice_settings = VoiceSettings(
        stability=0.65,
        similarity_boost=0.75,
        style=0.3,
        use_speaker_boost=True,
    )

    LANG_HINTS = {"pt": "pt", "en": "en", "es": "es"}
    lang_hint = LANG_HINTS.get(lang, "")

    kwargs = {
        "text": text,
        "voice_id": voice_id,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": voice_settings,
    }
    if lang_hint:
        kwargs["language_code"] = lang_hint

    audio_gen = client.text_to_speech.convert(**kwargs)
    audio_bytes = b""
    for chunk in audio_gen:
        audio_bytes += chunk
    return audio_bytes


def _get_audio_duration(audio_path: str) -> float:
    """Get duration of audio file using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0  # Default 5 seconds


def generate_preview_video(
    project_id: str,
    panels: list,
    voice_id: str,
    lang: str = "pt",
    music_path: str = None,
    upload_fn=None,
    update_fn=None,
    tenant_id: str = "",
) -> str:
    """Generate an animated preview video from storyboard panels.

    Pipeline:
    1. Download panel images
    2. Generate narration for each panel (ElevenLabs)
    3. Create individual panel videos with Ken Burns effect (FFmpeg)
    4. Concatenate all panel videos
    5. Mix with background music (optional)
    6. Upload final video

    Returns: URL of the final video.
    """
    work_dir = tempfile.mkdtemp(prefix="preview_")
    total = len(panels)
    panel_videos = []

    try:
        # Phase 1: Download images & generate narration
        if update_fn:
            update_fn(tenant_id, project_id, {
                "preview_status": {"phase": "preparing", "current": 0, "total": total}
            })

        narration_files = []
        image_files = []

        for i, panel in enumerate(panels):
            sn = panel.get("scene_number", i + 1)

            # Download image
            img_path = os.path.join(work_dir, f"panel_{sn}.png")
            if panel.get("image_url"):
                if not _download_file(panel["image_url"], img_path):
                    logger.warning(f"Preview [{project_id}]: Failed to download panel {sn} image")
                    continue
            else:
                continue

            image_files.append((sn, img_path))

            # Generate narration
            narration_text = panel.get("dialogue", "") or panel.get("description", "")
            if narration_text:
                if update_fn:
                    update_fn(tenant_id, project_id, {
                        "preview_status": {"phase": "narrating", "current": i + 1, "total": total}
                    })
                try:
                    audio_bytes = _generate_panel_narration(narration_text, voice_id, lang)
                    audio_path = os.path.join(work_dir, f"narration_{sn}.mp3")
                    with open(audio_path, "wb") as f:
                        f.write(audio_bytes)
                    narration_files.append((sn, audio_path))
                    logger.info(f"Preview [{project_id}]: Narration {sn} generated ({len(audio_bytes)//1024}KB)")
                except Exception as e:
                    logger.warning(f"Preview [{project_id}]: Narration {sn} failed: {e}")
                    narration_files.append((sn, None))
            else:
                narration_files.append((sn, None))

        if not image_files:
            raise RuntimeError("No panel images available")

        # Phase 2: Create individual panel videos with Ken Burns effect
        if update_fn:
            update_fn(tenant_id, project_id, {
                "preview_status": {"phase": "rendering", "current": 0, "total": len(image_files)}
            })

        for idx, (sn, img_path) in enumerate(image_files):
            # Find matching narration
            narr = next((n for n in narration_files if n[0] == sn), None)
            narr_path = narr[1] if narr else None

            # Determine duration: narration length + 1s padding, or default 5s
            if narr_path and os.path.exists(narr_path):
                duration = _get_audio_duration(narr_path) + 0.8
            else:
                duration = 5.0

            duration = max(duration, 3.0)  # Minimum 3 seconds
            fps = 30

            # Ken Burns: zoom from 1.0 to 1.15 with slight pan
            # Alternate between zoom-in and zoom-out for variety
            panel_video = os.path.join(work_dir, f"video_{sn}.mp4")

            if idx % 3 == 0:
                # Zoom in center
                zoom_filter = f"zoompan=z='min(zoom+0.0005,1.15)':d={int(duration*fps)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
            elif idx % 3 == 1:
                # Pan left to right
                zoom_filter = f"zoompan=z='1.12':d={int(duration*fps)}:x='if(eq(on,1),0,x+1)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"
            else:
                # Zoom out
                zoom_filter = f"zoompan=z='if(eq(on,1),1.15,max(zoom-0.0005,1.0))':d={int(duration*fps)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={fps}"

            if narr_path and os.path.exists(narr_path):
                cmd = [
                    "ffmpeg", "-y",
                    "-i", img_path,
                    "-i", narr_path,
                    "-filter_complex",
                    f"[0:v]{zoom_filter},fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5[v]",
                    "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-c:a", "aac", "-b:a", "128k",
                    "-t", str(duration),
                    "-pix_fmt", "yuv420p",
                    panel_video
                ]
            else:
                # No audio — silent
                cmd = [
                    "ffmpeg", "-y",
                    "-i", img_path,
                    "-filter_complex",
                    f"[0:v]{zoom_filter},fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5}:d=0.5[v]",
                    "-map", "[v]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-c:a", "aac", "-b:a", "128k",
                    "-t", str(duration),
                    "-shortest",
                    "-pix_fmt", "yuv420p",
                    panel_video
                ]

            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
                if os.path.exists(panel_video) and os.path.getsize(panel_video) > 1000:
                    panel_videos.append(panel_video)
                    logger.info(f"Preview [{project_id}]: Panel {sn} video ready ({duration:.1f}s)")
                else:
                    logger.warning(f"Preview [{project_id}]: Panel {sn} video failed")
            except Exception as e:
                logger.error(f"Preview [{project_id}]: FFmpeg error panel {sn}: {e}")

            if update_fn:
                update_fn(tenant_id, project_id, {
                    "preview_status": {"phase": "rendering", "current": idx + 1, "total": len(image_files)}
                })

        if not panel_videos:
            raise RuntimeError("No panel videos generated")

        # Phase 3: Concatenate all panel videos
        if update_fn:
            update_fn(tenant_id, project_id, {
                "preview_status": {"phase": "concatenating", "current": 0, "total": 1}
            })

        concat_list = os.path.join(work_dir, "concat.txt")
        with open(concat_list, "w") as f:
            for pv in panel_videos:
                f.write(f"file '{pv}'\n")

        concat_video = os.path.join(work_dir, "preview_concat.mp4")
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            concat_video
        ]
        subprocess.run(concat_cmd, capture_output=True, timeout=120)

        if not os.path.exists(concat_video):
            raise RuntimeError("Concatenation failed")

        # Phase 4: Mix with background music (optional)
        final_video = concat_video
        if music_path and os.path.exists(music_path):
            if update_fn:
                update_fn(tenant_id, project_id, {
                    "preview_status": {"phase": "mixing_music", "current": 0, "total": 1}
                })

            mixed_video = os.path.join(work_dir, "preview_final.mp4")
            video_duration = _get_audio_duration(concat_video)
            mix_cmd = [
                "ffmpeg", "-y",
                "-i", concat_video,
                "-i", music_path,
                "-filter_complex",
                f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first[out]",
                "-map", "0:v", "-map", "[out]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                mixed_video
            ]
            try:
                subprocess.run(mix_cmd, capture_output=True, timeout=120)
                if os.path.exists(mixed_video) and os.path.getsize(mixed_video) > 1000:
                    final_video = mixed_video
            except Exception as e:
                logger.warning(f"Preview [{project_id}]: Music mix failed: {e}")

        # Phase 5: Upload
        if update_fn:
            update_fn(tenant_id, project_id, {
                "preview_status": {"phase": "uploading", "current": 0, "total": 1}
            })

        with open(final_video, "rb") as f:
            video_bytes = f.read()

        filename = f"storyboard/{project_id}/preview_animado.mp4"
        video_url = upload_fn(video_bytes, filename, "video/mp4") if upload_fn else None

        logger.info(f"Preview [{project_id}]: Complete! Size: {len(video_bytes)//1024}KB, URL: {video_url}")
        return video_url

    except Exception as e:
        logger.error(f"Preview [{project_id}]: Generation failed: {e}")
        raise
    finally:
        # Cleanup temp files
        import shutil
        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
