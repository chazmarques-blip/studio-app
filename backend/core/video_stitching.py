"""
Video Stitching Module - Frame Stitching with Audio Continuity

Splits long scenes (>12s) into multiple Sora 2 clips while maintaining:
- Visual continuity (frame stitching)
- Audio continuity (synchronized dialogue + music)
- Natural cut points (dialogue timeline analysis)
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Sora 2 API maximum reliable duration
SORA_MAX_DURATION = 12.0  # seconds

class VideoStitchingPlanner:
    """
    Plans how to split a long scene into multiple Sora 2 clips
    with natural cut points and audio continuity.
    """
    
    def __init__(self, scene: Dict, dialogue_timeline: List[Dict]):
        self.scene = scene
        self.dialogue_timeline = dialogue_timeline or []
        self.scene_duration = self._calculate_scene_duration()
        
    def _calculate_scene_duration(self) -> float:
        """Calculate total scene duration from dialogue timeline."""
        if not self.dialogue_timeline:
            # Fallback: estimate from dialogue length
            return 12.0  # Default to single clip
        
        # Get the end time of the last dialogue beat
        last_beat = max(self.dialogue_timeline, key=lambda b: b.get('end', 0))
        return last_beat.get('end', 12.0)
    
    def needs_splitting(self) -> bool:
        """Check if scene needs to be split into multiple clips."""
        return self.scene_duration > SORA_MAX_DURATION
    
    def find_natural_cut_points(self) -> List[float]:
        """
        Find natural cut points in the dialogue timeline.
        
        Prioritizes:
        1. Pauses/silences in dialogue
        2. End of complete sentences
        3. Scene transitions
        4. Character switches
        
        Returns:
            List of timestamps (in seconds) where cuts should happen
        """
        if not self.needs_splitting():
            return []
        
        cut_points = []
        current_time = 0.0
        
        for i, beat in enumerate(self.dialogue_timeline):
            beat_start = beat.get('start', 0)
            beat_end = beat.get('end', 0)
            character = beat.get('character')
            
            # Check if we're approaching the clip limit
            time_since_last_cut = beat_end - current_time
            
            if time_since_last_cut >= SORA_MAX_DURATION - 1.0:  # Leave 1s margin
                # Find the best cut point near this position
                
                # Option 1: Current beat is a pause/silence
                if character is None or beat.get('text', '').strip() in ['[pausa]', '[silêncio]', '[pausa dramática]']:
                    cut_point = beat_start
                    cut_points.append(cut_point)
                    current_time = cut_point
                    logger.info(f"Natural cut at {cut_point:.1f}s (pause/silence)")
                    continue
                
                # Option 2: Gap between current and next beat
                if i < len(self.dialogue_timeline) - 1:
                    next_beat = self.dialogue_timeline[i + 1]
                    gap = next_beat.get('start', 0) - beat_end
                    
                    if gap >= 0.5:  # At least 0.5s gap
                        cut_point = beat_end + (gap / 2)  # Cut in middle of gap
                        cut_points.append(cut_point)
                        current_time = cut_point
                        logger.info(f"Natural cut at {cut_point:.1f}s (gap between dialogue)")
                        continue
                
                # Option 3: End of current sentence
                cut_point = beat_end
                cut_points.append(cut_point)
                current_time = cut_point
                logger.info(f"Cut at {cut_point:.1f}s (end of sentence)")
        
        return cut_points
    
    def create_clip_plan(self) -> List[Dict]:
        """
        Create a complete plan for splitting the scene into clips.
        
        Returns:
            List of clip specifications with timing and metadata
        """
        if not self.needs_splitting():
            # Single clip - no splitting needed
            return [{
                'clip_index': 0,
                'start_time': 0.0,
                'end_time': self.scene_duration,
                'duration': self.scene_duration,
                'needs_frame_reference': False,
                'dialogue_beats': self.dialogue_timeline
            }]
        
        cut_points = self.find_natural_cut_points()
        
        # Add start and end points
        all_points = [0.0] + cut_points + [self.scene_duration]
        
        clips = []
        for i in range(len(all_points) - 1):
            start = all_points[i]
            end = all_points[i + 1]
            duration = end - start
            
            # Get dialogue beats for this clip
            clip_dialogue = [
                beat for beat in self.dialogue_timeline
                if beat.get('start', 0) >= start and beat.get('end', 0) <= end
            ]
            
            clips.append({
                'clip_index': i,
                'start_time': start,
                'end_time': end,
                'duration': duration,
                'needs_frame_reference': i > 0,  # All clips after first need reference frame
                'dialogue_beats': clip_dialogue,
                'description': self._generate_clip_description(start, end, clip_dialogue)
            })
        
        logger.info(f"Scene split plan: {len(clips)} clips - " + 
                   ", ".join([f"Clip {i}: {c['duration']:.1f}s" for i, c in enumerate(clips)]))
        
        return clips
    
    def _generate_clip_description(self, start: float, end: float, dialogue_beats: List[Dict]) -> str:
        """Generate a description for this clip segment."""
        if not dialogue_beats:
            return f"Visual sequence ({start:.1f}s-{end:.1f}s)"
        
        characters = list(set([b.get('character') for b in dialogue_beats if b.get('character')]))
        char_list = ", ".join(characters[:3])  # First 3 characters
        
        return f"{char_list} ({start:.1f}s-{end:.1f}s)"


class AudioSynchronizer:
    """
    Handles audio generation and synchronization for stitched video clips.
    """
    
    @staticmethod
    def generate_full_scene_audio(
        scene: Dict,
        dialogue_timeline: List[Dict],
        character_voices: Dict[str, Dict],
        background_music_path: Optional[str] = None
    ) -> Dict:
        """
        Generate complete audio for the entire scene before splitting.
        
        Args:
            scene: Scene data
            dialogue_timeline: Complete dialogue timeline
            character_voices: Voice assignments for characters
            background_music_path: Optional background music file
        
        Returns:
            Dictionary with audio file path and metadata
        """
        # TODO: Implement full audio generation
        # This will integrate with:
        # - ElevenLabs for dialogue
        # - Sound design agent for music/SFX
        # - FFmpeg for mixing
        
        logger.info("Generating full scene audio...")
        
        return {
            'audio_path': None,  # Path to generated audio file
            'duration': 0.0,
            'has_dialogue': len(dialogue_timeline) > 0,
            'has_music': background_music_path is not None
        }
    
    @staticmethod
    def extract_clip_audio(
        full_audio_path: str,
        start_time: float,
        end_time: float,
        output_path: str
    ) -> str:
        """
        Extract audio segment for a specific clip from the full audio.
        
        ⚠️ CRITICAL: Uses FFmpeg copy codec to preserve 100% quality.
        NO re-encoding = NO quality loss.
        
        Args:
            full_audio_path: Path to master audio file (high quality)
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds
            output_path: Output path for audio segment
            
        Returns:
            Path to extracted audio clip (LOSSLESS)
        """
        import subprocess
        
        duration = end_time - start_time
        
        # 🔒 LOSSLESS EXTRACTION:
        # -c:a copy = Copy audio stream without re-encoding
        # Result: 100% original quality preserved
        cmd = [
            'ffmpeg', '-y',
            '-i', full_audio_path,
            '-ss', str(start_time),  # Seek to start time
            '-t', str(duration),      # Duration to extract
            '-c:a', 'copy',          # ← CRITICAL: No re-encoding!
            '-avoid_negative_ts', 'make_zero',  # Fix timestamp issues
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"✅ Extracted audio clip LOSSLESS: {start_time:.1f}s - {end_time:.1f}s")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio clip: {e.stderr.decode()}")
            raise


class FrameStitcher:
    """
    Handles frame extraction and stitching for visual continuity.
    """
    
    @staticmethod
    def extract_last_frame(video_path: str, output_path: str) -> str:
        """
        Extract the last frame of a video to use as reference for next clip.
        
        Uses FFmpeg to extract the final frame as a high-quality image.
        """
        import subprocess
        
        cmd = [
            'ffmpeg', '-y',
            '-sseof', '-1',  # Seek to 1 second before end
            '-i', video_path,
            '-update', '1',
            '-q:v', '1',  # Highest quality
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Extracted last frame from {video_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract frame: {e.stderr.decode()}")
            raise
    
    @staticmethod
    def merge_clips_with_audio(
        video_clips: List[str],
        audio_clips: List[str],
        output_path: str
    ) -> str:
        """
        Merge multiple video clips with their corresponding audio clips.
        
        ⚠️ CRITICAL: Preserves 100% quality using copy codecs.
        - Video: NO re-encoding (Sora 2 quality preserved)
        - Audio: NO re-encoding (ElevenLabs quality preserved)
        - Only multiplexing (combining streams)
        
        Args:
            video_clips: List of video file paths (Sora 2 outputs)
            audio_clips: List of audio file paths (corresponding segments)
            output_path: Final output video path
            
        Returns:
            Path to merged video (LOSSLESS)
        """
        import subprocess
        import tempfile
        
        logger.info(f"🎬 Starting LOSSLESS merge of {len(video_clips)} clips...")
        
        # Step 1: Mux each video with its audio (NO re-encoding)
        intermediate_files = []
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for i, (video, audio) in enumerate(zip(video_clips, audio_clips)):
                intermediate = f"/tmp/clip_{i}_muxed.mp4"
                
                # 🔒 LOSSLESS MUX:
                # -c:v copy = Copy video without re-encoding (100% Sora 2 quality)
                # -c:a copy = Copy audio without re-encoding (100% ElevenLabs quality)
                mux_cmd = [
                    'ffmpeg', '-y',
                    '-i', video,
                    '-i', audio,
                    '-c:v', 'copy',  # ← CRITICAL: No video re-encoding!
                    '-c:a', 'copy',  # ← CRITICAL: No audio re-encoding!
                    '-shortest',     # Match shortest stream duration
                    '-map', '0:v:0', # Map video from first input
                    '-map', '1:a:0', # Map audio from second input
                    intermediate
                ]
                
                try:
                    subprocess.run(mux_cmd, check=True, capture_output=True)
                    logger.info(f"  ✅ Clip {i+1}: Muxed LOSSLESS")
                    intermediate_files.append(intermediate)
                    f.write(f"file '{intermediate}'\n")
                except subprocess.CalledProcessError as e:
                    logger.error(f"Failed to mux clip {i}: {e.stderr.decode()}")
                    raise
            
            concat_file = f.name
        
        # Step 2: Concatenate all muxed clips (NO re-encoding)
        # 🔒 LOSSLESS CONCAT:
        # -c copy = Copy all streams without re-encoding
        concat_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',  # ← CRITICAL: No re-encoding during concat!
            output_path
        ]
        
        try:
            subprocess.run(concat_cmd, check=True, capture_output=True)
            logger.info(f"✅ Merged {len(video_clips)} clips LOSSLESS → {output_path}")
            logger.info(f"📊 Quality preservation: Video 100% | Audio 100%")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to concatenate clips: {e.stderr.decode()}")
            raise


# ══════════════════════════════════════════════════════════════════════════════
# Example Usage
# ══════════════════════════════════════════════════════════════════════════════

def plan_scene_splitting_example():
    """Example of how to use the video stitching planner."""
    
    scene = {
        "scene_number": 5,
        "description": "Jonas conversa com o grande peixe pela primeira vez"
    }
    
    dialogue_timeline = [
        {"start": 0.0, "end": 5.5, "character": "Jonas", "text": "Olha o tamanho desse peixe!"},
        {"start": 6.0, "end": 10.0, "character": "Narrador", "text": "Jonas estava assustado"},
        {"start": 10.5, "end": 11.0, "character": None, "text": "[pausa dramática]"},
        {"start": 11.5, "end": 16.0, "character": "Peixe", "text": "Não tenha medo, pequeno"},
        {"start": 16.5, "end": 20.0, "character": "Jonas", "text": "Você... você fala?!"},
        {"start": 20.5, "end": 21.0, "character": None, "text": "[silêncio]"},
        {"start": 21.5, "end": 28.0, "character": "Peixe", "text": "Sim, e tenho uma missão para você"}
    ]
    
    planner = VideoStitchingPlanner(scene, dialogue_timeline)
    
    if planner.needs_splitting():
        print(f"Scene duration: {planner.scene_duration:.1f}s - Splitting required")
        clips = planner.create_clip_plan()
        
        for clip in clips:
            print(f"\nClip {clip['clip_index']}:")
            print(f"  Time: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s ({clip['duration']:.1f}s)")
            print(f"  Frame reference: {clip['needs_frame_reference']}")
            print(f"  Description: {clip['description']}")
            print(f"  Dialogue beats: {len(clip['dialogue_beats'])}")
    else:
        print(f"Scene duration: {planner.scene_duration:.1f}s - No splitting needed")


if __name__ == "__main__":
    plan_scene_splitting_example()
