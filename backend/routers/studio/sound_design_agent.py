"""
Sound Design Agent - Intelligent Voice Assignment for Characters
Automatically assigns or creates optimal voices for each character
"""
from ._shared import *
import asyncio
from typing import Dict, List, Optional

# ══════════════════════════════════════════════════════════════════════════════
# SOUND DESIGN AGENT - Voice Assignment Expert
# ══════════════════════════════════════════════════════════════════════════════

SOUND_DESIGNER_SYSTEM_PROMPT = """You are a LEGENDARY SOUND DESIGNER and VOICE CASTING DIRECTOR for animation studios.

YOUR EXPERTISE:
- 30+ years casting voices for Pixar, Disney, DreamWorks, Studio Ghibli
- Deep understanding of how voice matches character personality, species, age
- Expert in voice characteristics: pitch, tone, timbre, tempo, accent
- Specialist in animal voices (birds, mammals, reptiles, aquatic creatures)

YOUR MISSION:
Assign the PERFECT voice to each character based on:
1. **Species/Type** (human, bird, lion, dolphin, etc.)
2. **Physical Traits** (size, build, features)
3. **Age** (child, young adult, elder)
4. **Personality** (energetic, wise, playful, serious)
5. **Role** (protagonist, villain, comic relief, narrator)

## VOICE MATCHING PRINCIPLES

### Species-Specific Guidelines

**BIRDS** (high-pitched, light, chirpy):
- Small birds (sparrow, hummingbird): Very high pitch, fast tempo, light tone
- Medium birds (crow, parrot): Medium-high pitch, articulate, intelligent sound
- Large birds (eagle, owl): Lower pitch for size, but still bright tone

**MAMMALS - Predators** (powerful, resonant):
- Lion: Deep, authoritative, rumbling bass
- Tiger: Similar to lion but slightly sharper
- Bear: Very deep, slow, gentle giant quality
- Wolf: Mid-low, sharp, intelligent

**MAMMALS - Herbivores** (gentle, warm):
- Deer: Soft, delicate, higher pitch
- Elephant: Very deep, slow, wise
- Rabbit: Medium-high, quick, nervous energy

**AQUATIC** (fluid, mysterious):
- Dolphin: Playful, intelligent, medium-high, friendly
- Whale: Ultra-deep, slow, ethereal
- Fish: Light, bubbly, quick

**REPTILES** (smooth, calculated):
- Snake: Sibilant, smooth, seductive or menacing
- Turtle: Slow, wise, deep, patient
- Lizard: Quick, sharp, alert

**INSECTS** (high, fast):
- Bee: Buzzy quality, busy, industrious
- Butterfly: Very light, delicate, ethereal

### Age Mapping
- **Child (0-12)**: High pitch, playful, innocent, energetic
- **Teen (13-17)**: Medium-high, enthusiastic, sometimes uncertain
- **Young Adult (18-35)**: Clear, confident, dynamic
- **Adult (36-60)**: Rich, authoritative, experienced
- **Elder (60+)**: Deep, wise, slower tempo, gravelly optional

### Personality → Voice Traits
- **Playful**: Fast tempo, varied pitch, light tone
- **Wise**: Slow tempo, deep pitch, calm tone
- **Energetic**: Fast tempo, bright tone, varied pitch
- **Serious**: Steady tempo, controlled pitch, strong tone
- **Comic**: Exaggerated, unexpected pitch changes, quirky
- **Heroic**: Strong, clear, mid-low pitch, confident
- **Villain**: Sharp or very deep, menacing, calculated

## ELEVENLABS VOICE LIBRARY ANALYSIS

When analyzing the voice library, consider:
1. **Gender Match**: Male voices for male characters, female for female (unless creative choice)
2. **Age Appropriate**: Young voices sound different from elder voices
3. **Accent Context**: Match accent to character's origin/culture if relevant
4. **Energy Level**: Active characters need expressive voices, calm characters need steady voices
5. **Distinctiveness**: Each character should sound UNIQUE - avoid assigning same voice to multiple characters

## OUTPUT FORMAT

Return ONLY valid JSON with detailed reasoning:

```json
{
  "voice_assignments": [
    {
      "character_name": "Pomba da Paz",
      "character_type": "bird - dove",
      "recommended_voice_id": "21m00Tcm4TlvDq8ikWAM",
      "recommended_voice_name": "Rachel",
      "confidence_score": 95,
      "reasoning": "Rachel's soft, gentle tone perfectly matches a dove's peaceful nature. Her medium-high pitch suits a small bird, and her calm delivery reflects the character's serene personality.",
      "voice_characteristics_needed": {
        "pitch": "medium-high",
        "tone": "soft, gentle, warm",
        "tempo": "calm, measured",
        "timbre": "light, airy"
      },
      "alternative_voice_id": "pNInz6obpgDQGcFmaJgB",
      "alternative_voice_name": "Adam"
    }
  ]
}
```

## CRITICAL RULES
1. NEVER assign the same voice to multiple characters unless they are intentionally identical (twins, clones)
2. ALWAYS match species to appropriate pitch range (birds high, elephants low)
3. CONSIDER age first, then personality
4. For animal characters, prioritize species-appropriate sound over human gender
5. Make each character's voice MEMORABLE and DISTINCT
"""


async def analyze_character_voice_needs(
    character: Dict,
    all_characters: List[Dict],
    available_voices: List[Dict],
    lang: str = "pt"
) -> Dict:
    """
    Deep analysis of a single character to determine optimal voice
    
    Args:
        character: Character dict with name, description, age, role
        all_characters: All project characters (for distinctiveness check)
        available_voices: ElevenLabs voice library
        lang: Project language
    
    Returns:
        Voice recommendation with reasoning
    """
    
    # Build voice catalog for agent
    voices_catalog = "\n".join([
        f"- ID: {v['id']} | Name: {v['name']} | Gender: {v['gender']} | "
        f"Accent: {v.get('accent', 'neutral')} | Style: {v.get('style', 'versatile')} | "
        f"Description: {v.get('description', 'N/A')}"
        for v in available_voices
    ])
    
    # Extract character details
    char_name = character.get("name", "Unknown")
    char_desc = character.get("description", "")
    char_age = character.get("age", "adult")
    char_role = character.get("role", "supporting")
    
    # Build context of other characters (to ensure distinctiveness)
    other_chars = [c.get("name", "") for c in all_characters if c.get("name") != char_name]
    other_chars_text = ", ".join(other_chars[:10]) if other_chars else "None"
    
    user_prompt = f"""Analyze this character and recommend the PERFECT voice:

CHARACTER TO CAST:
- Name: {char_name}
- Description: {char_desc}
- Age: {char_age}
- Role: {char_role}

OTHER CHARACTERS IN PROJECT:
{other_chars_text}

AVAILABLE VOICES:
{voices_catalog}

TASK:
1. Identify the character's species/type (human, animal type, creature)
2. Determine optimal voice characteristics (pitch, tone, tempo, timbre)
3. Select the BEST MATCHING voice from the library
4. Provide detailed reasoning
5. Suggest an alternative voice as backup

Language: {lang}

Return JSON with your expert voice recommendation."""
    
    try:
        result = await _call_claude_async(
            SOUND_DESIGNER_SYSTEM_PROMPT,
            user_prompt,
            max_tokens=1500,
            timeout=90
        )
        
        parsed = _parse_json(result)
        
        if not parsed or "voice_assignments" not in parsed:
            # Try to extract JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                parsed = _parse_json(json_match.group(0))
        
        if parsed and "voice_assignments" in parsed:
            return parsed["voice_assignments"][0] if len(parsed["voice_assignments"]) > 0 else None
        
        return None
        
    except Exception as e:
        logger.error(f"SoundDesigner analysis error for '{char_name}': {e}")
        return None


async def auto_assign_voices_with_sound_designer(
    project_id: str,
    tenant_id: str,
    available_voices: List[Dict]
) -> Dict:
    """
    Use Sound Designer Agent to assign optimal voices to ALL characters
    
    Strategy:
    - Analyzes each character independently
    - Considers species, age, personality
    - Ensures voice distinctiveness across all characters
    - Provides detailed reasoning for each assignment
    
    Returns:
        Dict with voice_map and detailed_assignments
    """
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        raise Exception("Project not found")
    
    characters = project.get("characters", [])
    if not characters:
        raise Exception("No characters in project")
    
    lang = project.get("language", "pt")
    
    logger.info(f"SoundDesigner [{project_id}]: Analyzing {len(characters)} characters")
    
    # Parallel analysis of all characters
    tasks = [
        analyze_character_voice_needs(char, characters, available_voices, lang)
        for char in characters
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Build voice map and detailed assignments
    voice_map = {}
    detailed_assignments = []
    used_voices = set()
    
    for char, result in zip(characters, results):
        char_name = char.get("name", "")
        
        if isinstance(result, Exception) or not result:
            # Fallback: Use Rachel (neutral, versatile)
            voice_map[char_name] = "21m00Tcm4TlvDq8ikWAM"
            detailed_assignments.append({
                "character_name": char_name,
                "voice_id": "21m00Tcm4TlvDq8ikWAM",
                "voice_name": "Rachel",
                "confidence": 50,
                "reasoning": "Fallback assignment due to analysis error",
                "status": "fallback"
            })
            continue
        
        recommended_id = result.get("recommended_voice_id")
        alternative_id = result.get("alternative_voice_id")
        
        # Check if recommended voice already used
        if recommended_id in used_voices and alternative_id:
            # Use alternative to ensure distinctiveness
            voice_map[char_name] = alternative_id
            used_voices.add(alternative_id)
            detailed_assignments.append({
                "character_name": char_name,
                "voice_id": alternative_id,
                "voice_name": result.get("alternative_voice_name", "Unknown"),
                "confidence": result.get("confidence_score", 80) - 10,
                "reasoning": f"{result.get('reasoning', '')} (Used alternative to ensure distinctiveness)",
                "status": "alternative"
            })
        else:
            voice_map[char_name] = recommended_id
            used_voices.add(recommended_id)
            detailed_assignments.append({
                "character_name": char_name,
                "voice_id": recommended_id,
                "voice_name": result.get("recommended_voice_name", "Unknown"),
                "confidence": result.get("confidence_score", 90),
                "reasoning": result.get("reasoning", ""),
                "voice_characteristics": result.get("voice_characteristics_needed", {}),
                "status": "recommended"
            })
    
    logger.info(f"SoundDesigner [{project_id}]: Assigned {len(voice_map)} voices, {len(used_voices)} unique")
    
    return {
        "voice_map": voice_map,
        "detailed_assignments": detailed_assignments,
        "stats": {
            "total_characters": len(characters),
            "unique_voices_used": len(used_voices),
            "fallbacks": sum(1 for a in detailed_assignments if a["status"] == "fallback"),
            "alternatives": sum(1 for a in detailed_assignments if a["status"] == "alternative")
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# ASYNC CLAUDE HELPER (if not already in _shared)
# ══════════════════════════════════════════════════════════════════════════════

async def _call_claude_async(system_prompt: str, user_prompt: str, max_tokens: int = 4000, timeout: int = 120) -> str:
    """Async wrapper for Claude calls"""
    import litellm
    
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("EMERGENT_LLM_KEY", "")
    
    response = await litellm.acompletion(
        model="anthropic/claude-sonnet-4-5-20250929",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        api_key=api_key,
        max_tokens=max_tokens,
        timeout=timeout,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()
