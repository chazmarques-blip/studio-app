"""
Musical Video Generation Service
Generates music videos with background visuals (no lip-sync)
"""
import os
import logging
import tempfile
import subprocess
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class MusicalVideoService:
    """
    Service for generating music videos
    
    Creates videos with:
    - Characters in compatible actions (dancing, playing, happy scenes)
    - NO lip-sync (mouths closed or smiling)
    - Music playing as background audio
    - Optional subtitles with lyrics
    """
    
    def __init__(self):
        self.openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.openai_client = OpenAI(api_key=self.openai_api_key)
    
    def build_musical_scene_prompt(
        self,
        characters: List[str],
        scene_description: str,
        lyrics_excerpt: str,
        music_style: str,
        visual_style: str = "pixar_3d"
    ) -> str:
        """
        Build Sora 2 prompt for musical scene (WITHOUT lip-sync)
        
        Args:
            characters: List of character names
            scene_description: Base scene description
            lyrics_excerpt: Part of the lyrics for this scene
            music_style: Music style (upbeat, calm, etc.)
            visual_style: Animation style
        
        Returns:
            Optimized prompt for Sora 2
        """
        # Character actions based on music style
        if "upbeat" in music_style.lower() or "alegre" in music_style.lower():
            actions = "dancing joyfully, jumping, spinning, clapping hands"
        elif "calm" in music_style.lower() or "calmo" in music_style.lower():
            actions = "swaying gently, smiling peacefully, moving gracefully"
        else:
            actions = "moving rhythmically, expressing joy"
        
        # Visual style mapping
        style_hints = {
            "pixar_3d": "Pixar-style 3D animation, vibrant colors, soft lighting",
            "disney_2d": "Disney 2D animation, hand-drawn style, colorful",
            "claymation": "Claymation style, textured, warm lighting"
        }
        style_hint = style_hints.get(visual_style, style_hints["pixar_3d"])
        
        characters_str = ", ".join(characters) if characters else "characters"
        
        prompt = f"""{style_hint}. Music video scene featuring {characters_str}.

SCENE: {scene_description}

CHARACTERS' ACTIONS (NO SINGING, NO TALKING):
- {actions}
- Mouths CLOSED or smiling (not speaking/singing)
- Happy, expressive faces
- Natural body movements matching the rhythm
- Interacting playfully with each other

ATMOSPHERE:
- Colorful and vibrant environment
- Dynamic camera movements (slow pans, gentle zooms)
- Music video aesthetic for children
- Joyful and energetic mood

IMPORTANT: Characters are NOT singing or speaking. This is a music video with background music.
No lip movements. Just happy expressions and dance movements."""

        return prompt[:1000]  # Sora 2 limit
    
    async def generate_video_segment(
        self,
        prompt: str,
        duration: int = 12,
        size: str = "1280x720",
        reference_image: Optional[str] = None
    ) -> bytes:
        """
        Generate a single video segment using Sora 2
        
        Args:
            prompt: Sora 2 prompt
            duration: Video duration in seconds
            size: Video resolution
            reference_image: Optional character reference image
        
        Returns:
            Video bytes
        """
        try:
            import time
            
            gen_params = {
                "model": "sora-2",
                "prompt": prompt,
                "size": size,
                "seconds": duration
            }
            
            # Add reference image if provided
            if reference_image and os.path.exists(reference_image):
                from PIL import Image
                
                target_width, target_height = map(int, size.split('x'))
                img = Image.open(reference_image)
                
                if img.size != (target_width, target_height):
                    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                    resized_path = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                    img.save(resized_path, format="PNG")
                    reference_image = resized_path
                
                img_file = open(reference_image, "rb")
                gen_params["input_reference"] = img_file
            
            # Generate video
            logger.info(f"Generating musical video segment: {prompt[:100]}...")
            video = self.openai_client.videos.create(**gen_params)
            
            # Poll for completion
            video_id = video.id
            max_wait = 600  # 10 minutes
            start = time.time()
            
            while (time.time() - start) < max_wait:
                video_status = self.openai_client.videos.retrieve(video_id)
                
                if video_status.status == "completed":
                    content = self.openai_client.videos.download_content(video_id)
                    video_bytes = content.read()
                    logger.info(f"Musical video segment generated: {len(video_bytes)//1024}KB")
                    return video_bytes
                
                elif video_status.status == "failed":
                    error_msg = getattr(video_status, 'error', 'Unknown error')
                    raise Exception(f"Video generation failed: {error_msg}")
                
                time.sleep(10)
            
            raise TimeoutError("Video generation timeout")
            
        except Exception as e:
            logger.error(f"Error generating video segment: {e}")
            raise
    
    def merge_video_and_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        fade_in: bool = True,
        fade_out: bool = True
    ) -> str:
        """
        Merge video with music using FFmpeg
        
        Args:
            video_path: Path to video file
            music_path: Path to music MP3
            output_path: Path for output file
            fade_in: Apply fade-in effect
            fade_out: Apply fade-out effect
        
        Returns:
            Path to merged video
        """
        try:
            # Build FFmpeg command
            # Replace video's audio with music, keeping video stream
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,      # Video input
                "-i", music_path,      # Music input
                "-map", "0:v:0",       # Use video from first input
                "-map", "1:a:0",       # Use audio from second input (music)
                "-c:v", "copy",        # Copy video stream (no re-encoding)
                "-c:a", "aac",         # Encode audio as AAC
                "-b:a", "192k",        # Audio bitrate
                "-shortest",           # Cut to shortest stream
                output_path
            ]
            
            # Add fade effects if requested
            if fade_in or fade_out:
                # Get video duration first
                probe_cmd = [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    video_path
                ]
                result = subprocess.run(probe_cmd, capture_output=True, text=True)
                duration = float(result.stdout.strip())
                
                # Build audio filter
                audio_filter = []
                if fade_in:
                    audio_filter.append("afade=t=in:st=0:d=2")
                if fade_out:
                    audio_filter.append(f"afade=t=out:st={duration-2}:d=2")
                
                if audio_filter:
                    # Modify command to include audio filter
                    cmd = [
                        "ffmpeg", "-y",
                        "-i", video_path,
                        "-i", music_path,
                        "-map", "0:v:0",
                        "-map", "1:a:0",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-b:a", "192k",
                        "-af", ",".join(audio_filter),
                        "-shortest",
                        output_path
                    ]
            
            logger.info(f"Merging video and music: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg merge failed: {result.stderr.decode()[:300]}")
            
            logger.info(f"Video and music merged successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error merging video and music: {e}")
            raise
    
    def create_subtitle_file(
        self,
        lyrics: str,
        duration: int,
        output_path: str
    ) -> str:
        """
        Create SRT subtitle file from lyrics
        
        Args:
            lyrics: Full lyrics text
            duration: Total duration in seconds
            output_path: Path for SRT file
        
        Returns:
            Path to SRT file
        """
        try:
            # Split lyrics into lines
            lines = [line.strip() for line in lyrics.split('\n') if line.strip()]
            
            # Remove structure markers
            lines = [
                line for line in lines 
                if not line.startswith('[') and not line.endswith(']')
            ]
            
            if not lines:
                return None
            
            # Calculate time per line
            time_per_line = duration / len(lines)
            
            # Build SRT content
            srt_content = []
            for i, line in enumerate(lines, 1):
                start_time = (i - 1) * time_per_line
                end_time = i * time_per_line
                
                # Format timestamps
                start_str = self._format_srt_time(start_time)
                end_str = self._format_srt_time(end_time)
                
                srt_content.append(f"{i}")
                srt_content.append(f"{start_str} --> {end_str}")
                srt_content.append(line)
                srt_content.append("")  # Empty line
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_content))
            
            logger.info(f"Subtitle file created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating subtitle file: {e}")
            return None
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT timestamp (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# Global service instance
_musical_video_service: Optional[MusicalVideoService] = None

def get_musical_video_service() -> MusicalVideoService:
    """Get or create the global musical video service instance"""
    global _musical_video_service
    if _musical_video_service is None:
        _musical_video_service = MusicalVideoService()
    return _musical_video_service
