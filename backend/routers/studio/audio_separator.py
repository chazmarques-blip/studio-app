"""
Audio Separation Module for StudioX
Separates audio from generated videos into individual stems (dialogue, music, effects)
Uses Demucs AI for high-quality stem separation
"""

import os
import subprocess
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("studiox")


def extract_audio_from_video(video_path: str, output_audio_path: str) -> bool:
    """
    Extract audio track from video file using FFmpeg
    
    Args:
        video_path: Path to input video file
        output_audio_path: Path to save extracted audio (WAV format)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "44100",  # 44.1kHz sample rate
            "-ac", "2",  # Stereo
            output_audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(output_audio_path):
            audio_size = os.path.getsize(output_audio_path) // 1024
            logger.info(f"Audio extracted: {output_audio_path} ({audio_size}KB)")
            return True
        else:
            logger.error(f"FFmpeg audio extraction failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to extract audio: {e}")
        return False


def separate_audio_stems(audio_path: str, output_dir: str, model: str = "htdemucs") -> Optional[Dict[str, str]]:
    """
    Separate audio into stems using Demucs AI
    
    Args:
        audio_path: Path to input audio file
        output_dir: Directory to save separated stems
        model: Demucs model to use (htdemucs, htdemucs_6s, htdemucs_ft)
            - htdemucs: 4 stems (vocals, drums, bass, other) - DEFAULT, fastest
            - htdemucs_6s: 6 stems (vocals, drums, bass, guitar, piano, other) - slower
            
    Returns:
        Dict mapping stem names to file paths, or None if failed
    """
    try:
        # Create temp directory for Demucs output
        demucs_output = os.path.join(output_dir, "demucs_temp")
        os.makedirs(demucs_output, exist_ok=True)
        
        # Run Demucs separation
        logger.info(f"Demucs: Starting stem separation with model '{model}'...")
        cmd = [
            "demucs",
            "--two-stems=vocals",  # Separate vocals from everything else first
            "--out", demucs_output,
            "--mp3",  # Output as MP3 for smaller file size
            "--mp3-bitrate", "192",
            audio_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode != 0:
            logger.error(f"Demucs separation failed: {result.stderr}")
            return None
        
        # Find generated stems (Demucs creates: htdemucs/<filename>/vocals.mp3, no_vocals.mp3)
        audio_filename = Path(audio_path).stem
        stems_dir = os.path.join(demucs_output, "htdemucs", audio_filename)
        
        if not os.path.exists(stems_dir):
            logger.error(f"Demucs output directory not found: {stems_dir}")
            return None
        
        # Map Demucs stems to our naming convention
        stems = {}
        
        # Vocals = Dialogue
        vocals_path = os.path.join(stems_dir, "vocals.mp3")
        if os.path.exists(vocals_path):
            dialogue_path = os.path.join(output_dir, "camada_dialogos.mp3")
            os.rename(vocals_path, dialogue_path)
            stems["dialogue"] = dialogue_path
            logger.info(f"Stem separated: Dialogue ({os.path.getsize(dialogue_path)//1024}KB)")
        
        # No_vocals = Music + SFX combined
        # We'll do a second pass to separate music from effects
        no_vocals_path = os.path.join(stems_dir, "no_vocals.mp3")
        if os.path.exists(no_vocals_path):
            # Run second Demucs pass to separate drums/bass/other from no_vocals
            logger.info("Demucs: Second pass - separating music and effects...")
            cmd2 = [
                "demucs",
                "--out", demucs_output,
                "--mp3",
                "--mp3-bitrate", "192",
                no_vocals_path
            ]
            
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=600)
            
            if result2.returncode == 0:
                no_vocals_stems_dir = os.path.join(demucs_output, "htdemucs", "no_vocals")
                
                # Drums + Bass = Sound Effects (percussive elements)
                drums_path = os.path.join(no_vocals_stems_dir, "drums.mp3")
                bass_path = os.path.join(no_vocals_stems_dir, "bass.mp3")
                
                if os.path.exists(drums_path) and os.path.exists(bass_path):
                    # Merge drums + bass as effects
                    effects_path = os.path.join(output_dir, "camada_efeitos.mp3")
                    merge_cmd = [
                        "ffmpeg", "-y",
                        "-i", drums_path,
                        "-i", bass_path,
                        "-filter_complex", "amix=inputs=2:duration=longest",
                        effects_path
                    ]
                    subprocess.run(merge_cmd, capture_output=True, timeout=60)
                    stems["effects"] = effects_path
                    logger.info(f"Stem separated: Effects ({os.path.getsize(effects_path)//1024}KB)")
                
                # Other = Music (melodic/harmonic content)
                other_path = os.path.join(no_vocals_stems_dir, "other.mp3")
                if os.path.exists(other_path):
                    music_path = os.path.join(output_dir, "camada_musica.mp3")
                    os.rename(other_path, music_path)
                    stems["music"] = music_path
                    logger.info(f"Stem separated: Music ({os.path.getsize(music_path)//1024}KB)")
            else:
                # Fallback: if second pass fails, treat no_vocals as music
                music_path = os.path.join(output_dir, "camada_musica.mp3")
                os.rename(no_vocals_path, music_path)
                stems["music"] = music_path
                logger.warning("Demucs second pass failed, using no_vocals as music only")
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(demucs_output, ignore_errors=True)
        
        logger.info(f"Demucs: Separation complete! Generated {len(stems)} stems")
        return stems
        
    except Exception as e:
        logger.error(f"Demucs stem separation error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def create_silent_video(video_path: str, output_path: str) -> bool:
    """
    Remove audio from video, creating a silent video base
    
    Args:
        video_path: Path to input video
        output_path: Path to save silent video
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-an",  # Remove audio
            "-c:v", "copy",  # Copy video stream (no re-encoding)
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(output_path):
            video_size = os.path.getsize(output_path) // 1024
            logger.info(f"Silent video created: {output_path} ({video_size}KB)")
            return True
        else:
            logger.error(f"FFmpeg silent video creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create silent video: {e}")
        return False


def generate_markers_json(
    project_data: Dict,
    output_path: str
) -> bool:
    """
    Generate markers.json file with scene timecodes for CapCut-style editing
    
    Args:
        project_data: Project dict containing screenplay and scene info
        output_path: Path to save markers.json
        
    Returns:
        True if successful, False otherwise
    """
    try:
        screenplay = project_data.get("screenplay", {}).get("scenes", [])
        
        markers = {
            "version": "1.0",
            "project_name": project_data.get("name", "StudioX Project"),
            "total_duration": 0,
            "scenes": []
        }
        
        current_time = 0.0
        
        for idx, scene in enumerate(screenplay, 1):
            duration = scene.get("duration", 10)  # Default 10s if not specified
            
            scene_marker = {
                "scene_number": idx,
                "start_time": current_time,
                "end_time": current_time + duration,
                "duration": duration,
                "description": scene.get("visual_frame", "")[:100],
                "dialogue": scene.get("dialogue", ""),
                "location": scene.get("location", ""),
                "characters": scene.get("characters", [])
            }
            
            markers["scenes"].append(scene_marker)
            current_time += duration
        
        markers["total_duration"] = current_time
        
        # Write JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(markers, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Markers JSON created: {output_path} ({len(markers['scenes'])} scenes)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate markers JSON: {e}")
        return False


def process_video_to_layers(
    video_path: str,
    project_data: Dict,
    output_dir: str
) -> Optional[Dict[str, str]]:
    """
    Main pipeline: Process generated video into separate layers
    
    Args:
        video_path: Path to the complete generated video (with audio)
        project_data: Project dict with screenplay info
        output_dir: Directory to save all output files
        
    Returns:
        Dict with paths to all generated files:
        {
            "video_completo": "path/to/video_completo.mp4",
            "video_base_silencioso": "path/to/video_base.mp4",
            "camada_dialogos": "path/to/dialogos.mp3",
            "camada_musica": "path/to/musica.mp3",
            "camada_efeitos": "path/to/efeitos.mp3",
            "markers": "path/to/markers.json"
        }
        Or None if processing failed
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info("=== Starting Layer Separation Pipeline ===")
        logger.info(f"Input video: {video_path} ({os.path.getsize(video_path)//1024}KB)")
        
        result = {}
        
        # Copy original video as "video_completo"
        video_completo_path = os.path.join(output_dir, "video_completo.mp4")
        import shutil
        shutil.copy2(video_path, video_completo_path)
        result["video_completo"] = video_completo_path
        logger.info("✅ Video completo saved")
        
        # Step 1: Extract audio
        audio_path = os.path.join(output_dir, "audio_extracted.wav")
        if not extract_audio_from_video(video_path, audio_path):
            logger.error("Audio extraction failed, aborting layer separation")
            return None
        logger.info("✅ Audio extracted")
        
        # Step 2: Separate audio into stems
        stems = separate_audio_stems(audio_path, output_dir)
        if stems:
            result.update(stems)
            logger.info(f"✅ Audio separated into {len(stems)} stems")
        else:
            logger.warning("⚠️ Stem separation failed, continuing without stems")
        
        # Step 3: Create silent video
        video_base_path = os.path.join(output_dir, "video_base_silencioso.mp4")
        if create_silent_video(video_path, video_base_path):
            result["video_base_silencioso"] = video_base_path
            logger.info("✅ Silent video created")
        
        # Step 4: Generate markers JSON
        markers_path = os.path.join(output_dir, "markers.json")
        if generate_markers_json(project_data, markers_path):
            result["markers"] = markers_path
            logger.info("✅ Markers JSON created")
        
        # Clean up temp audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
        
        logger.info("=== Layer Separation Complete! ===")
        logger.info(f"Generated {len(result)} files in {output_dir}")
        
        return result
        
    except Exception as e:
        logger.error(f"Layer separation pipeline error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
