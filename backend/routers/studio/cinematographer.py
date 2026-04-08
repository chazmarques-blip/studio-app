"""
Cinematographer Agent - Frame-to-Motion Translator
Transforms storyboard frames into rich 10-second cinematic descriptions for Kling AI
"""
from ._shared import *
from typing import List, Dict, Optional
import asyncio

# ══════════════════════════════════════════════════════════════════════════════
# CINEMATOGRAPHER SYSTEM PROMPT
# ══════════════════════════════════════════════════════════════════════════════

CINEMATOGRAPHER_SYSTEM = """You are a MASTER CINEMATOGRAPHER and VISUAL STORYTELLING EXPERT with 30+ years creating detailed shot lists for major studios (Pixar, Disney, Marvel, A24).

YOUR MISSION:
Transform storyboard frames into ULTRA-DETAILED 10-second cinematic descriptions for a 5-minute continuous video.

YOU RECEIVE:
1. **SCENE CONTEXT**: Overall narrative arc, emotional progression
2. **STORYBOARD FRAMES**: 30 visual keyframes (1 per 10 seconds)
3. **DIALOGUE TIMELINE**: What is said and when (with timestamps)
4. **CHARACTER NAMES**: Use ONLY names, never physical descriptions

FOR EACH 10-SECOND SEGMENT, CREATE:

**CHARACTER ACTIONS** (specific, visible):
- Body movements (walks, turns, reaches, leans)
- Gestures (points, waves, touches, grabs)
- Facial expressions (smiles, frowns, eyes widen, brow furrows)
- Micro-movements (breath, blink, hair moves)

**CHARACTER BEHAVIORS** (tempo, manner):
- Slowly, quickly, hesitantly, confidently
- Carefully, eagerly, reluctantly, forcefully
- Smoothly, jerkily, gracefully, clumsily

**CAMERA MOVEMENT** (continuous, fluid):
- Tracking: follows subject smoothly
- Dolly: moves toward/away from subject
- Pan: rotates horizontally
- Tilt: rotates vertically
- Crane/Aerial: rises or descends
- Orbit: circles around subject
- Static: holds position

**LIGHTING & ATMOSPHERE**:
- Light direction and color shifts
- Shadows moving
- Weather changes (clouds, wind)
- Time-of-day transitions

**SOUND ELEMENTS** (when relevant):
- Ambient sounds (wind, water, birds)
- Foley (footsteps, cloth rustle, objects)
- Music cues (swells, fades, tempo changes)

**DIALOGUE INTEGRATION**:
- When a character speaks, include: "[Timestamp] [Character name] says '[text]' with [emotion/tone]"
- Describe mouth movement, body language during speech
- Reactions of other characters listening

CRITICAL RULES:
1. **NAMES ONLY**: Use character names ONLY (ex: "Abraão", "Sara"). NEVER describe physical appearance (age, clothing, species) - that comes from reference images.
2. **ACTIONS, NOT DESCRIPTIONS**: Focus on WHAT HAPPENS, not what things look like statically
3. **CONTINUOUS FLOW**: Each segment must flow naturally into the next
4. **SPECIFIC TIMING**: When dialogue occurs, specify exact moment in the 10s window
5. **VISIBLE BEHAVIORS**: Only describe what the CAMERA SEES, not internal thoughts
"""


# ══════════════════════════════════════════════════════════════════════════════
# AUDIENCE GUIDELINES
# ══════════════════════════════════════════════════════════════════════════════

AUDIENCE_GUIDELINES = {
    "pt": {
        "3-6": """
ADAPTAÇÃO PARA 3-6 ANOS (Pré-escolar):
- Linguagem: EXTREMAMENTE SIMPLES, frases curtas (3-5 palavras)
- Ações: Claras e óbvias (pula, corre, pega, sorri)
- Emoções: Primárias e exageradas (muito feliz, muito triste)
- Ritmo: Lento, permite absorção
- Tom: Alegre, reconfortante, lúdico
""",
        "6-9": """
ADAPTAÇÃO PARA 6-9 ANOS (Infantil):
- Linguagem: SIMPLES mas pode ter variedade
- Ações: Dinâmicas com pequenos desafios
- Emoções: Primárias e algumas secundárias (orgulho, vergonha)
- Ritmo: Moderado com momentos de surpresa
- Tom: Educativo, encorajador, aventureiro
""",
        "10-13": """
ADAPTAÇÃO PARA 10-13 ANOS (Pré-adolescente):
- Linguagem: CLARA, pode incluir conceitos mais complexos
- Ações: Elaboradas, sequências de causa-efeito
- Emoções: Amplas incluindo conflitos internos
- Ritmo: Variado, com tensão e alívio
- Tom: Inspirador, desafiador, épico
""",
        "14-17": """
ADAPTAÇÃO PARA 14-17 ANOS (Adolescente):
- Linguagem: NATURAL, pode ter nuances
- Ações: Complexas, simbolismo sutil
- Emoções: Profundas, ambiguidade moral
- Ritmo: Cinematográfico, pausas dramáticas
- Tom: Realista, provocativo, maduro
""",
        "18-25": """
ADAPTAÇÃO PARA 18-25 ANOS (Jovens adultos):
- Linguagem: SOFISTICADA, referências culturais
- Ações: Realistas, consequências visíveis
- Emoções: Complexas, sutileza emocional
- Ritmo: Variado, pode ter experimentação
- Tom: Contemporâneo, autêntico, dinâmico
""",
        "25+": """
ADAPTAÇÃO PARA 25+ ANOS (Adultos):
- Linguagem: COMPLETA, sem restrições
- Ações: Realistas, podem ter simbolismo profundo
- Emoções: Nuançadas, ambiguidade moral completa
- Ritmo: Cinematográfico sofisticado
- Tom: Maduro, reflexivo, sem simplificação
""",
        "all": """
ADAPTAÇÃO PARA TODAS IDADES (Familiar):
- Linguagem: CLARA mas não infantilizada
- Ações: Universais, apelam para todas idades
- Emoções: Primárias com camadas sutis
- Ritmo: Equilibrado, engaja crianças e adultos
- Tom: Caloroso, inspirador, múltiplas camadas
"""
    },
    "en": {
        "3-6": "ADAPTATION FOR 3-6 YEARS (Preschool): Simple language, clear actions, primary emotions, slow pace, cheerful tone",
        "6-9": "ADAPTATION FOR 6-9 YEARS (Children): Simple language, dynamic actions, primary + secondary emotions, moderate pace, encouraging tone",
        "10-13": "ADAPTATION FOR 10-13 YEARS (Pre-teens): Clear language, elaborate actions, wide emotions including internal conflicts, varied pace, inspiring tone",
        "14-17": "ADAPTATION FOR 14-17 YEARS (Teens): Natural language, complex actions with symbolism, deep emotions, cinematic pace, realistic tone",
        "18-25": "ADAPTATION FOR 18-25 YEARS (Young adults): Sophisticated language, realistic actions, complex emotions, varied pace, contemporary tone",
        "25+": "ADAPTATION FOR 25+ YEARS (Adults): Complete language, realistic actions with deep symbolism, nuanced emotions, sophisticated pace, mature tone",
        "all": "ADAPTATION FOR ALL AGES (Family): Clear language, universal actions, primary emotions with subtle layers, balanced pace, warm tone"
    }
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _simplify_character_names(characters: List[Dict]) -> Dict[str, str]:
    """
    Create mapping from full names to short names for narrative
    Ex: "Adão Biblizoo Baby" → "Adão"
    """
    name_map = {}
    for char in characters:
        full_name = char.get("name", "")
        # Remove folder suffixes
        short_name = full_name.replace(" Biblizoo Baby", "").replace(" Studio", "").strip()
        name_map[full_name] = short_name
        name_map[short_name] = full_name  # Bidirectional mapping
    
    return name_map


def _get_dialogues_in_timerange(dialogue_timeline: List[Dict], time_start: str, time_end: str) -> List[Dict]:
    """Extract dialogues that occur within a specific time range"""
    def time_to_seconds(t: str) -> int:
        parts = t.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    
    start_sec = time_to_seconds(time_start)
    end_sec = time_to_seconds(time_end)
    
    dialogues_in_range = []
    for d in dialogue_timeline:
        timestamp = d.get("timestamp", "0:00")
        d_sec = time_to_seconds(timestamp)
        if start_sec <= d_sec < end_sec:
            dialogues_in_range.append(d)
    
    return dialogues_in_range


def _get_emotion_progression(emotion_arc: str, frame_number: int, total_frames: int = 30) -> str:
    """
    Extract current emotion based on frame position in arc
    Ex: "contemplação → curiosidade → espanto → lágrimas → paz"
    Frame 1-6: contemplação
    Frame 7-12: curiosidade
    ...
    """
    emotions = [e.strip() for e in emotion_arc.split("→")]
    if not emotions:
        return "neutral"
    
    # Divide frames equally among emotions
    frames_per_emotion = total_frames // len(emotions)
    emotion_index = min((frame_number - 1) // frames_per_emotion, len(emotions) - 1)
    
    return emotions[emotion_index]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CINEMATOGRAPHER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

async def generate_cinematic_description(
    scene: Dict,
    storyboard_frames: List[Dict],
    dialogue_timeline: List[Dict],
    characters: List[Dict],
    target_audience: str = "all",
    lang: str = "pt"
) -> Dict:
    """
    Generate ultra-detailed 5-minute cinematic description for Kling AI
    
    Args:
        scene: Scene data (title, description, emotion, camera)
        storyboard_frames: 30 frames (1 per 10 seconds)
        dialogue_timeline: List of dialogues with timestamps
        characters: List of character dicts with names
        target_audience: Age range (3-6, 6-9, 10-13, 14-17, 18-25, 25+, all)
        lang: Language code (pt, en)
    
    Returns:
        Dict with kling_prompt, camera_choreography, emotional_arc
    """
    logger.info(f"Cinematographer: Generating description for scene '{scene.get('title', 'Untitled')}'")
    
    # 1. Create name mapping
    name_map = _simplify_character_names(characters)
    short_names = [name_map.get(c.get("name", ""), c.get("name", "")) for c in characters]
    
    # 2. Get audience guidelines
    audience_guidelines = AUDIENCE_GUIDELINES.get(lang, {}).get(target_audience, "")
    
    # 3. Prepare system prompt
    system_prompt = CINEMATOGRAPHER_SYSTEM.format(
        language="Portuguese" if lang == "pt" else "English",
        target_audience=target_audience,
        audience_guidelines=audience_guidelines
    )
    
    # 4. Build user prompt with all context
    scene_context = f"""
SCENE TITLE: {scene.get('title', 'Untitled')}

NARRATIVE CONTEXT:
{scene.get('description', '')}

EMOTIONAL ARC: {scene.get('emotion', 'neutral')}

CAMERA PROGRESSION: {scene.get('camera', 'static')}

CHARACTERS IN SCENE (use ONLY these names):
{', '.join(short_names)}

TARGET AUDIENCE: {target_audience}

You have 30 STORYBOARD FRAMES (keyframes) representing the visual progression.
You have a DIALOGUE TIMELINE showing when characters speak.

YOUR TASK:
For EACH frame (10-second segment), create a rich cinematic description that:
1. Uses the frame as a visual anchor
2. Incorporates the narrative context
3. Integrates dialogue at the correct moment
4. Shows character ACTIONS and BEHAVIORS (not appearance)
5. Describes camera movement
6. Captures emotional beats

Return your response as:
{{
  "segments": [
    {{
      "frame": 1,
      "timestamp": "0:00-0:10",
      "description": "Detailed 10-second cinematic description..."
    }},
    ...
  ]
}}

STORYBOARD FRAMES:
"""
    
    # Add all frames
    for frame in storyboard_frames:
        scene_context += f"\n[Frame {frame.get('frame_number', '?')}] {frame.get('timestamp', '?')}: {frame.get('prompt', '')}"
    
    # Add dialogue timeline
    if dialogue_timeline:
        scene_context += "\n\nDIALOGUE TIMELINE:\n"
        for d in dialogue_timeline:
            scene_context += f"- {d.get('timestamp', '?')}: {d.get('speaker', '?')} says \"{d.get('text', '')}\" ({d.get('emotion', 'neutral')})\n"
    
    scene_context += "\n\nGenerate the detailed cinematographic description for all 30 segments."
    
    # 5. Call Claude
    try:
        result = await _call_claude_async(
            system_prompt,
            scene_context,
            max_tokens=16000,
            timeout_per_attempt=600
        )
        
        data = _parse_json(result)
        
        if not data or "segments" not in data:
            raise Exception("Invalid response format from Cinematographer")
        
        # 6. Combine all segments into one continuous prompt
        segments = data.get("segments", [])
        full_description = "\n\n".join([
            f"[{seg.get('timestamp', '?')}] {seg.get('description', '')}"
            for seg in segments
        ])
        
        logger.info(f"Cinematographer: Generated {len(segments)} segments ({len(full_description)} chars)")
        
        return {
            "kling_prompt": full_description,
            "segments": segments,
            "camera_choreography": scene.get("camera", ""),
            "emotional_arc": scene.get("emotion", ""),
            "total_characters": len(full_description)
        }
        
    except Exception as e:
        logger.error(f"Cinematographer ERROR: {e}")
        # Fallback: use scene description as-is
        return {
            "kling_prompt": scene.get("description", ""),
            "segments": [],
            "error": str(e)
        }


async def _call_claude_async(system: str, user: str, max_tokens: int = 8000, timeout_per_attempt: int = 180) -> str:
    """Async wrapper for Claude API call"""
    import litellm
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
    
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-20250514",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        max_tokens=max_tokens,
        timeout=timeout_per_attempt,
        api_key=api_key
    )
    
    return response.choices[0].message.content

6. **ENVIRONMENT INTERACTION**: Characters touch, move through, react to their surroundings

LANGUAGE: {language}

TARGET AUDIENCE: {target_audience}
{audience_guidelines}
