"""
Dialogue Timeline Agent
Converts raw dialogue text into precise timestamped timeline for scene synchronization.

This agent ensures that storyboards, shot briefs, and Sora 2 video generation
are perfectly synchronized with the dialogue timing.
"""
import os
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


def generate_dialogue_timeline(
    scene_dialogue: str,
    scene_duration: float = 12.0,
    language: str = "pt",
    scene_emotion: str = "neutral",
    audio_mode: str = "narrated",
    project_id: str = ""
) -> List[Dict]:
    """
    Converts raw dialogue text into timestamped timeline.
    
    Args:
        scene_dialogue: Raw dialogue text (can be narrated or dubbed format)
        scene_duration: Total scene duration in seconds (default 12s)
        language: Language code (pt, en, es)
        scene_emotion: Scene emotion/mood (affects pacing)
        audio_mode: "narrated" or "dubbed"
        project_id: Project ID for logging
    
    Returns:
        List of dialogue beats with precise timing:
        [
            {
                "beat": 1,
                "speaker": "Narrator",
                "text": "Jonas vivia em Jerusalém.",
                "start_time": 0.0,
                "end_time": 2.2,
                "duration": 2.2,
                "tone": "calm storytelling",
                "word_count": 4,
                "speech_rate": 1.8,
                "action_note": "Establishing shot"
            },
            ...
        ]
    """
    if not scene_dialogue or not scene_dialogue.strip():
        logger.warning(f"DialogueTimeline [{project_id}]: Empty dialogue, returning empty timeline")
        return []
    
    # Language-specific speech rates (words per second)
    SPEECH_RATES = {
        "pt": {"narrator": 2.0, "character": 2.5, "excited": 3.0, "calm": 1.5},
        "en": {"narrator": 2.2, "character": 2.7, "excited": 3.2, "calm": 1.7},
        "es": {"narrator": 2.3, "character": 2.8, "excited": 3.3, "calm": 1.8},
    }
    
    rates = SPEECH_RATES.get(language, SPEECH_RATES["pt"])
    
    LANG_NAMES = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    lang_name = LANG_NAMES.get(language, "Portuguese")
    
    system_prompt = f"""You are a DIALOGUE TIMING EXPERT for animated film production.

Your job: Convert raw dialogue text into a PRECISE TIMELINE with start/end times for a {scene_duration}-second scene.

TIMING RULES:
1. SPEECH RATES (words per second):
   - Narrator: {rates['narrator']} w/s (storytelling, calm)
   - Character (normal): {rates['character']} w/s (conversational)
   - Excited/urgent: {rates['excited']} w/s (fast-paced)
   - Calm/contemplative: {rates['calm']} w/s (slow, emotional)

2. PAUSES & TIMING:
   - Add 0.3s pause between different speakers
   - Add 0.5-1.0s pause for dramatic moments ("...", silence)
   - Add 0.2s pause at end of each sentence
   - First line can start at 0.0s OR delay 0.5s if scene needs establishing

3. EMOTIONAL PACING:
   Scene emotion: {scene_emotion}
   - If sad/melancholic: slow down all speech by 20%
   - If exciting/action: speed up by 15%
   - If tense/dramatic: add longer pauses (0.5s extra)

4. CRITICAL CONSTRAINT:
   - Total dialogue MUST fit within {scene_duration} seconds
   - If text is too long, increase speech rate OR note "dialogue_too_long"
   - Leave 0.5-2s of silence at end for scene breathing room

5. ACTION NOTES:
   - For narrator: note if off-screen or on-screen visuals
   - For characters: note "speaking on camera, mouth moving" or "reacting, listening"
   - For off-screen voices: note "voice only, character not visible"

OUTPUT FORMAT:
Return ONLY valid JSON array. No markdown, no explanation.

[
  {{
    "beat": 1,
    "speaker": "Narrator" or "CharacterName" or "God (voice)",
    "text": "exact dialogue line",
    "start_time": 0.0,
    "end_time": 2.2,
    "duration": 2.2,
    "tone": "calm storytelling" or "excited" or "questioning",
    "word_count": 4,
    "speech_rate": 1.8,
    "action_note": "Establishing shot, no character visible" or "Jonas speaking on camera"
  }}
]

LANGUAGE: {lang_name}
AUDIO MODE: {audio_mode}"""

    user_prompt = f"""Scene Duration: {scene_duration} seconds
Scene Emotion/Mood: {scene_emotion}
Audio Mode: {audio_mode}

RAW DIALOGUE TEXT:
{scene_dialogue}

---

Break this dialogue into a precise timeline. Calculate start_time and end_time for each line based on:
1. Word count and speech rate
2. Natural pauses between speakers
3. Emotional pacing
4. Total scene duration constraint

Return ONLY the JSON array."""

    try:
        import litellm
        
        response = litellm.completion(
            model="anthropic/claude-sonnet-4-5-20250929",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            api_key=ANTHROPIC_API_KEY,
            max_tokens=3000,
            timeout=120
        )
        
        result = response.choices[0].message.content
        
        # Parse JSON from response
        try:
            timeline = json.loads(result)
        except json.JSONDecodeError:
            # Try extracting JSON array from markdown
            import re
            match = re.search(r'\[[\s\S]*\]', result)
            if match:
                timeline = json.loads(match.group())
            else:
                logger.error(f"DialogueTimeline [{project_id}]: Failed to parse JSON from Claude response")
                return _fallback_timeline(scene_dialogue, scene_duration, language)
        
        if not isinstance(timeline, list):
            logger.error(f"DialogueTimeline [{project_id}]: Response is not a list")
            return _fallback_timeline(scene_dialogue, scene_duration, language)
        
        # Validate and adjust timeline
        timeline = _validate_and_adjust_timeline(timeline, scene_duration, project_id)
        
        total_duration = max([beat.get("end_time", 0) for beat in timeline]) if timeline else 0
        logger.info(f"DialogueTimeline [{project_id}]: Generated {len(timeline)} beats, total {total_duration:.1f}s / {scene_duration}s")
        
        return timeline
        
    except Exception as e:
        logger.error(f"DialogueTimeline [{project_id}]: Generation failed: {e}")
        return _fallback_timeline(scene_dialogue, scene_duration, language)


def _validate_and_adjust_timeline(timeline: List[Dict], max_duration: float, project_id: str) -> List[Dict]:
    """
    Validates timeline and adjusts if it exceeds scene duration.
    """
    if not timeline:
        return timeline
    
    # Calculate total duration
    total_dur = max([beat.get("end_time", 0) for beat in timeline])
    
    if total_dur > max_duration:
        # Timeline exceeds scene duration - compress proportionally
        compression_factor = (max_duration - 0.5) / total_dur  # Leave 0.5s buffer
        logger.warning(f"DialogueTimeline [{project_id}]: Timeline {total_dur:.1f}s exceeds {max_duration}s, compressing by {compression_factor:.2f}x")
        
        for beat in timeline:
            beat["start_time"] = beat["start_time"] * compression_factor
            beat["end_time"] = beat["end_time"] * compression_factor
            beat["duration"] = beat["end_time"] - beat["start_time"]
            if "speech_rate" in beat:
                beat["speech_rate"] = beat["speech_rate"] / compression_factor
        
        # Recalculate
        total_dur = max([beat.get("end_time", 0) for beat in timeline])
        logger.info(f"DialogueTimeline [{project_id}]: Compressed to {total_dur:.1f}s")
    
    # Add silence info
    silence = max_duration - total_dur
    if silence > 0:
        logger.info(f"DialogueTimeline [{project_id}]: {silence:.1f}s silence at end for breathing room")
    
    return timeline


def _fallback_timeline(dialogue: str, duration: float, language: str) -> List[Dict]:
    """
    Simple fallback timeline when Claude fails.
    Splits dialogue by lines and distributes evenly.
    """
    lines = [line.strip() for line in dialogue.split('\n') if line.strip()]
    if not lines:
        return []
    
    # Simple even distribution
    time_per_line = duration / len(lines)
    timeline = []
    
    for i, line in enumerate(lines):
        # Try to detect speaker (simple heuristic)
        speaker = "Narrator"
        if ":" in line:
            speaker_part = line.split(":")[0].strip()
            if len(speaker_part) < 30:  # Likely a speaker name
                speaker = speaker_part
                line = line.split(":", 1)[1].strip()
        
        word_count = len(line.split())
        
        timeline.append({
            "beat": i + 1,
            "speaker": speaker,
            "text": line,
            "start_time": round(i * time_per_line, 1),
            "end_time": round((i + 1) * time_per_line, 1),
            "duration": round(time_per_line, 1),
            "tone": "neutral",
            "word_count": word_count,
            "speech_rate": round(word_count / time_per_line, 1) if time_per_line > 0 else 2.0,
            "action_note": "Auto-generated (fallback)"
        })
    
    return timeline


def enrich_scene_with_timeline(scene: Dict, project_id: str = "") -> Dict:
    """
    Enriches a scene dict with dialogue_timeline.
    
    Args:
        scene: Scene dict with at least 'dialogue' or 'dubbed_text' or 'narrated_text'
        project_id: Project ID for logging
    
    Returns:
        Scene dict with added 'dialogue_timeline' field
    """
    # Get dialogue from scene
    dialogue = scene.get("dubbed_text", "") or scene.get("dialogue", "") or scene.get("narrated_text", "")
    
    if not dialogue or not dialogue.strip():
        scene["dialogue_timeline"] = []
        return scene
    
    # Determine audio mode
    audio_mode = "dubbed" if scene.get("dubbed_text") else "narrated"
    
    # Get scene metadata
    duration = scene.get("duration", 12.0)
    emotion = scene.get("emotion", "neutral")
    language = scene.get("language", "pt")
    
    # Generate timeline
    timeline = generate_dialogue_timeline(
        scene_dialogue=dialogue,
        scene_duration=duration,
        language=language,
        scene_emotion=emotion,
        audio_mode=audio_mode,
        project_id=project_id
    )
    
    scene["dialogue_timeline"] = timeline
    
    return scene


def batch_enrich_scenes_with_timeline(scenes: List[Dict], project_id: str = "") -> List[Dict]:
    """
    Enriches all scenes with dialogue_timeline in batch.
    
    Args:
        scenes: List of scene dicts
        project_id: Project ID for logging
    
    Returns:
        List of enriched scenes
    """
    logger.info(f"DialogueTimeline [{project_id}]: Processing {len(scenes)} scenes")
    
    enriched_scenes = []
    for i, scene in enumerate(scenes):
        try:
            enriched = enrich_scene_with_timeline(scene, project_id=project_id)
            enriched_scenes.append(enriched)
        except Exception as e:
            logger.error(f"DialogueTimeline [{project_id}]: Scene {i+1} failed: {e}")
            scene["dialogue_timeline"] = []
            enriched_scenes.append(scene)
    
    return enriched_scenes
