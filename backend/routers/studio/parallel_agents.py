"""
Parallel Agent System for StudioX
Implements parallel screenplay and dialogue generation with continuity preservation
"""
from ._shared import *
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
import threading

# Thread-safe lock for merging results
merge_lock = threading.Lock()

def _parse_time(time_str: str) -> int:
    """Parse time string '0:12' or '5:30' to seconds"""
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return int(parts[0])
    except:
        return 12  # default 12s


# ══════════════════════════════════════════════════════════════════════════════
# PARALLEL SCREENPLAY GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_screenplay_parallel(
    tenant_id: str,
    project_id: str,
    user_prompt: str,
    lang: str,
    audio_mode: str,
    max_scenes: int = 50,
    batch_size: int = 10,
    max_workers: int = 3,
    character_folder_id: str = None,  # NEW: Folder ID for character library
    target_audience: str = "all",  # NEW: Target audience age range
    video_engine: str = "sora",  # NEW: Video engine (sora/kling)
    target_duration_minutes: int = 5  # FIXED: Target duration in minutes
) -> Dict:
    """
    Generate screenplay using parallel agents
    
    Strategy:
    1. Phase 1: Single agent creates story structure + first batch (10 scenes)
    2. Phase 2: Multiple agents (3-5) generate remaining scenes in parallel batches
    3. Each agent receives context from previous scenes to maintain continuity
    
    Args:
        tenant_id: Tenant ID
        project_id: Project ID
        user_prompt: User's story request
        lang: Language code (pt, en, etc.)
        audio_mode: narrated or dubbed
        max_scenes: Maximum scenes to generate (default 50)
        batch_size: Scenes per batch (default 10)
        max_workers: Number of parallel agents (default 3)
    
    Returns:
        Dict with scenes, characters, metadata
    """
    logger.info(f"ParallelScreenplay [{project_id}]: Starting parallel generation (max_scenes={max_scenes}, workers={max_workers}, engine={video_engine}, target_duration={target_duration_minutes}min)")
    
    from .screenwriter import SCREENWRITER_SYSTEM_SORA, SCREENWRITER_SYSTEM_KLING, LANG_FULL_NAMES
    
    # ── Calculate number of scenes based on video engine ──
    if video_engine == "kling":
        # Kling: 5 minutes per scene
        num_scenes_needed = target_duration_minutes // 5
        if num_scenes_needed < 1:
            num_scenes_needed = 1
        system_template = SCREENWRITER_SYSTEM_KLING
        scene_duration = "5 minutos"
        logger.info(f"ParallelScreenplay [{project_id}]: KLING mode - {num_scenes_needed} scene(s) × 5min = {target_duration_minutes}min")
    else:
        # Sora: 12 seconds per scene
        num_scenes_needed = (target_duration_minutes * 60) // 12
        system_template = SCREENWRITER_SYSTEM_SORA
        scene_duration = "12 segundos"
        logger.info(f"ParallelScreenplay [{project_id}]: SORA mode - {num_scenes_needed} scenes × 12s = {target_duration_minutes}min")
    
    # ── NEW: Get character library from folder ──
    folder_characters = []
    character_library_text = ""
    
    if character_folder_id:
        folder_characters = _get_folder_characters(tenant_id, character_folder_id)
        if folder_characters:
            logger.info(f"ParallelScreenplay [{project_id}]: Using {len(folder_characters)} characters from folder {character_folder_id}")
            character_library_text = "\n\n" + "="*80 + "\n"
            character_library_text += f"📚 CHARACTER LIBRARY - {len(folder_characters)} PERSONAGENS DISPONÍVEIS\n"
            character_library_text += "="*80 + "\n"
            character_library_text += "Você DEVE usar SOMENTE personagens desta lista:\n\n"
            
            for char in folder_characters:
                character_library_text += f"- ID: {char['id']}\n"
                character_library_text += f"  Nome: {char['name']}\n"
                character_library_text += f"  Descrição: {char['description']}\n"
                character_library_text += f"  Idade: {char.get('age', 'adulto')}\n\n"
            
            character_library_text += "\n⚠️ REGRA CRÍTICA:\n"
            character_library_text += "- Use o NOME COMPLETO exatamente como fornecido\n"
            character_library_text += "- Inclua o ID do personagem na sua resposta JSON\n"
            character_library_text += "- Se precisar de personagens extras (figurantes, multidão), marque como 'NOVO:'\n"
            character_library_text += "="*80 + "\n"
    
    # ── NEW: Get audience guidelines ──
    audience_guideline = _get_audience_guideline(target_audience, lang)
    
    # ── Phase 1: Foundation Agent (First Batch) ──
    logger.info(f"ParallelScreenplay [{project_id}]: Phase 1 - Foundation agent generating structure")
    
    # Replace all template placeholders
    system = system_template.replace("{lang}", lang).replace("{lang_name}", LANG_FULL_NAMES.get(lang, lang)).replace("{target_duration}", str(target_duration_minutes)).replace("{num_scenes}", str(num_scenes_needed))
    
    # Add character library and audience guidelines to system prompt
    if character_library_text:
        system += character_library_text
    
    if audience_guideline:
        system += f"\n\n🎯 TARGET AUDIENCE: {target_audience}\n{audience_guideline}\n"
    
    audio_instruction = _build_audio_instruction(lang, audio_mode, LANG_FULL_NAMES)
    
    # Adapt batch_size for video engine
    if video_engine == "kling":
        # For Kling, generate fewer scenes per batch (1-2 scenes, as each is 5min)
        effective_batch_size = min(2, num_scenes_needed)
    else:
        # For Sora, keep original batch size
        effective_batch_size = min(batch_size, num_scenes_needed)
    
    initial_prompt = f"""
Story: {user_prompt}
{audio_instruction}

ENGINE: {video_engine.upper()} ({scene_duration} por cena)
TARGET: {target_duration_minutes} minutos = {num_scenes_needed} cena(s)

Create the screenplay structure with the first {effective_batch_size} scene(s). Set "total_scenes" to {num_scenes_needed}. Return ONLY valid JSON with:
- title
- total_scenes (exactly {num_scenes_needed})
- characters (all main characters)
- scenes (first {effective_batch_size} scene(s) only)
- research_notes
"""
    
    try:
        result = _call_claude_sync(system, initial_prompt, max_tokens=8000, timeout_per_attempt=360)
        foundation = _parse_json(result)
        
        if not foundation:
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result)
            if json_match:
                foundation = _parse_json(json_match.group(1))
        
        if not foundation:
            raise Exception("Foundation agent failed to return valid JSON")
        
        all_scenes = foundation.get("scenes", [])
        all_characters = foundation.get("characters", [])
        # Cap total_scenes to what was calculated based on target_duration and engine
        total_needed = min(foundation.get("total_scenes", len(all_scenes)), num_scenes_needed)
        title = foundation.get("title", "Untitled")
        
        logger.info(f"ParallelScreenplay [{project_id}]: Foundation complete - {len(all_scenes)}/{total_needed} scenes, {len(all_characters)} characters")
        
        if len(all_scenes) >= total_needed:
            return {
                "title": title,
                "scenes": all_scenes,
                "characters": all_characters,
                "total_scenes": len(all_scenes),
                "metadata": {"generation_mode": "foundation_only"}
            }
        
    except Exception as e:
        logger.error(f"ParallelScreenplay [{project_id}]: Foundation agent failed - {e}")
        raise
    
    # ── Phase 2: Parallel Agents (Remaining Batches) ──
    remaining_scenes_needed = total_needed - len(all_scenes)
    
    if remaining_scenes_needed <= 0:
        return {
            "title": title,
            "scenes": all_scenes,
            "characters": all_characters,
            "total_scenes": len(all_scenes),
            "metadata": {"generation_mode": "foundation_only"}
        }
    
    logger.info(f"ParallelScreenplay [{project_id}]: Phase 2 - Launching {max_workers} parallel agents for {remaining_scenes_needed} remaining scenes")
    
    # Calculate batches
    batches = []
    current_scene_num = len(all_scenes) + 1
    
    while current_scene_num <= total_needed:
        batch_end = min(current_scene_num + batch_size - 1, total_needed)
        batches.append((current_scene_num, batch_end))
        current_scene_num = batch_end + 1
    
    logger.info(f"ParallelScreenplay [{project_id}]: Created {len(batches)} batches: {batches}")
    
    # Thread-safe result collector
    batch_results = {}
    batch_lock = threading.Lock()
    
    def _generate_batch(batch_info: Tuple[int, int]) -> Dict:
        """Single agent generates one batch of scenes"""
        start_num, end_num = batch_info
        batch_id = f"{start_num}-{end_num}"
        
        try:
            logger.info(f"ParallelScreenplay [{project_id}]: Agent starting batch {batch_id}")
            
            # Build context from existing scenes (for continuity)
            with batch_lock:
                context_scenes = all_scenes[-3:] if len(all_scenes) >= 3 else all_scenes
                context_summary = "\n".join([
                    f"Scene {s.get('scene_number')}: {s.get('title')} - {s.get('description', '')[:100]}"
                    for s in context_scenes
                ])
                char_names = ', '.join([c.get('name', '') for c in all_characters])
                last_time = all_scenes[-1].get('time_end', '0:00') if all_scenes else '0:00'
            
            # Adapt prompt based on video engine
            if video_engine == "kling":
                scene_duration_text = "Each scene = 5 minutes (300 seconds)"
                timing_instruction = f"- Start time from {last_time}\n- Each scene is EXACTLY 5 minutes long\n- Scene transitions happen at 5-minute intervals"
            else:
                scene_duration_text = "Each scene = 12 seconds"
                timing_instruction = f"- Start time from {last_time}\n- Each scene is EXACTLY 12 seconds long"
            
            batch_prompt = f"""⚠️ CRITICAL: ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}. DO NOT use English.

Continue the screenplay "{title}".

STORY CONTEXT: {user_prompt}

CHARACTERS SO FAR: {char_names}

RECENT SCENES (for continuity):
{context_summary}

Generate scenes {start_num} to {end_num}. {scene_duration_text}
{timing_instruction}
- Maintain visual consistency with existing scenes
- Keep same characters, tone, and narrative flow
- Introduce NEW characters only if story needs them
- ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}
{audio_instruction}

Return ONLY JSON:
{{
  "scenes": [array of {end_num - start_num + 1} scenes],
  "characters": [any NEW characters introduced, or empty array]
}}
"""
            
            result_text = _call_claude_sync(system, batch_prompt, max_tokens=8000, timeout_per_attempt=360)
            batch_data = _parse_json(result_text)
            
            if not batch_data:
                import re
                json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result_text)
                if json_match:
                    batch_data = _parse_json(json_match.group(1))
            
            if not batch_data or not batch_data.get("scenes"):
                raise Exception(f"Batch {batch_id} returned invalid JSON")
            
            logger.info(f"ParallelScreenplay [{project_id}]: Agent completed batch {batch_id} - {len(batch_data['scenes'])} scenes")
            
            return {
                "batch_id": batch_id,
                "start_num": start_num,
                "scenes": batch_data["scenes"],
                "characters": batch_data.get("characters", [])
            }
            
        except Exception as e:
            logger.error(f"ParallelScreenplay [{project_id}]: Batch {batch_id} failed - {e}")
            return {"batch_id": batch_id, "start_num": start_num, "scenes": [], "characters": [], "error": str(e)}
    
    # Launch parallel agents
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_batch = {executor.submit(_generate_batch, batch): batch for batch in batches}
        
        for future in as_completed(future_to_batch):
            batch_result = future.result()
            
            if batch_result.get("error"):
                logger.warning(f"ParallelScreenplay [{project_id}]: Batch {batch_result['batch_id']} failed, skipping")
                continue
            
            # Merge results in order
            with batch_lock:
                batch_results[batch_result["start_num"]] = batch_result
                
                # Add new characters (avoid duplicates)
                existing_names = {c["name"] for c in all_characters}
                for new_char in batch_result.get("characters", []):
                    if new_char.get("name") not in existing_names:
                        all_characters.append(new_char)
                        existing_names.add(new_char["name"])
    
    # Merge all batch scenes in order
    sorted_batch_keys = sorted(batch_results.keys())
    for start_num in sorted_batch_keys:
        batch = batch_results[start_num]
        all_scenes.extend(batch["scenes"])
    
    logger.info(f"ParallelScreenplay [{project_id}]: COMPLETE - {len(all_scenes)} scenes, {len(all_characters)} characters")
    
    return {
        "title": title,
        "scenes": all_scenes,
        "characters": all_characters,
        "total_scenes": len(all_scenes),
        "metadata": {
            "generation_mode": "parallel",
            "batches_processed": len(batch_results),
            "workers_used": max_workers
        }
    }


def _build_audio_instruction(lang: str, audio_mode: str, lang_names: Dict) -> str:
    """Build audio mode instruction for screenplay"""
    lang_name = lang_names.get(lang, lang)
    
    if audio_mode == "dubbed":
        return f"""
AUDIO MODE: DUBBED (character voices + narrator). Format dialogue like:
"dialogue": "Narrador: 'Intro text...' / Character1: 'Line...' / Character2: 'Response...'"
- Use "Narrador:" sparingly (only for scene intros or emotional beats)
- Characters should speak 70%+ of the time
- ALL dialogue in {lang_name}"""
    else:
        return f"""
AUDIO MODE: NARRATED (voice-over). Format:
"dialogue": "Narrador: 'Scene description...'"
- Keep narration concise (2-3 sentences)
- ALL narration in {lang_name}"""


# ══════════════════════════════════════════════════════════════════════════════
# PARALLEL DIALOGUE GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_dialogues_parallel(
    tenant_id: str,
    project_id: str,
    scenes: List[Dict],
    characters: List[Dict],
    audio_mode: str,
    lang: str,
    max_workers: int = 5
) -> List[Dict]:
    """
    Generate dialogues for ALL scenes using parallel agents
    
    Strategy:
    - Each agent processes one scene independently
    - Agents receive character context and scene details
    - Results merged in scene order
    
    Args:
        tenant_id: Tenant ID
        project_id: Project ID
        scenes: List of screenplay scenes
        characters: List of characters
        audio_mode: narrated or dubbed  
        lang: Language code
        max_workers: Number of parallel agents (default 5)
    
    Returns:
        List of dialogue objects (one per scene)
    """
    logger.info(f"ParallelDialogue [{project_id}]: Generating dialogues for {len(scenes)} scenes (workers={max_workers})")
    
    all_dialogues = [None] * len(scenes)  # Pre-allocate to preserve order
    dialogue_lock = threading.Lock()
    
    # Character context
    char_context = "\n".join([
        f"- {c.get('name', 'Unknown')}: {c.get('description', '')} ({c.get('age', '')} {c.get('role', '')})"
        for c in characters
    ])
    
    # Build FULL SCRIPT CONTEXT (all scenes summary)
    full_script_context = "FULL STORY CONTEXT:\n"
    for idx, s in enumerate(scenes):
        scene_title = s.get("title", f"Scene {idx+1}")
        scene_desc = s.get("description", "")
        scene_start = s.get("time_start", "0:00")
        scene_end = s.get("time_end", "0:12")
        scene_chars = ", ".join(s.get("characters_in_scene", []))
        full_script_context += f"\nScene {idx+1}: {scene_title} ({scene_start} - {scene_end})\n"
        full_script_context += f"Characters: {scene_chars}\n"
        full_script_context += f"Description: {scene_desc}\n"
    
    # Mode-specific instructions
    LANG_NAMES = {"pt": "Português", "en": "English", "es": "Español", "fr": "Français"}
    lang_name = LANG_NAMES.get(lang, lang)
    
    if audio_mode == "dubbed":
        mode_instruction = f"""DUBBED MODE: Character voices + Narrator
Format: "Speaker: 'dialogue text...'"
Example: Narrador: 'Intro...' / Character1: 'Line...' / Character2: 'Response...'
- 70%+ character dialogue
- Use "Narrador:" sparingly (scene intro/emotional beats)
- ALL dialogue in {lang_name}"""
    elif audio_mode == "book":
        mode_instruction = f"""BOOK MODE: Literary narration
Write rich, descriptive text suitable for audiobook.
- Use vivid imagery and emotional language
- ALL text in {lang_name}"""
    else:
        mode_instruction = f"""NARRATED MODE: Voice-over storytelling
Format: "Narrador: 'Full narration...'"
- Concise (2-3 sentences per scene)
- ALL narration in {lang_name}"""
    
    def _generate_scene_dialogue(scene_idx: int, scene: Dict) -> Dict:
        """Single agent generates dialogue for one scene"""
        scene_num = scene.get("scene_number", scene_idx + 1)
        
        # Calculate scene duration
        start_time = scene.get("time_start", "0:00")
        end_time = scene.get("time_end", "0:12")
        start_secs = _parse_time(start_time)
        end_secs = _parse_time(end_time)
        duration_secs = end_secs - start_secs
        expected_words = int(duration_secs * 2.5)  # 150 words/min = 2.5 words/sec
        
        duration_display = f"{duration_secs//60}:{duration_secs%60:02d}"
        
        try:
            logger.info(f"ParallelDialogue [{project_id}]: Agent processing scene {scene_num} ({duration_secs}s, ~{expected_words} words)")
            
            # Determine max tokens based on duration
            if duration_secs > 60:
                max_tokens = 4096  # Long scenes need maximum output
            else:
                max_tokens = max(1500, int(expected_words * 1.5))
            
            system_prompt = f"""You are a MASTER DIALOGUE WRITER for {audio_mode} mode.

EXPERTISE:
- Academy Award-level dramatic writing
- Expert in character voice differentiation
- Emotional beats and story rhythm
- Age-appropriate language for all audiences

{full_script_context}

TASK: Write dialogue for Scene {scene_num} ({duration_secs} seconds = approximately {expected_words} words).

{mode_instruction}

CRITICAL: This scene is {duration_secs} seconds long. You MUST write approximately {expected_words} WORDS to fill this duration.
For a {duration_secs//60}-minute scene, write EXTENSIVE dialogue with 15-20 exchanges per character.
USE THE FULL STORY CONTEXT ABOVE to ensure dialogue flows naturally from previous scenes and sets up future scenes.

Return ONLY JSON:
{{
  "dialogue": "The complete dialogue text for this scene",
  "emotion_flow": "brief description of emotional progression"
}}"""
            
            user_prompt = f"""CHARACTERS:
{char_context}

CURRENT SCENE {scene_num}: {scene.get('title', '')}
- Time: {scene.get('time_start', '0:00')} - {scene.get('time_end', '0:12')}
- Characters present: {', '.join(scene.get('characters_in_scene', []))}
- Description: {scene.get('description', '')}
- Emotion: {scene.get('emotion', 'neutral')}
- Camera: {scene.get('camera', 'medium shot')}

Write emotionally powerful, natural dialogue for this scene in {lang_name}.
Remember: You know the FULL STORY from the context above. Use that knowledge to create dialogue that fits perfectly into the narrative arc."""
            
            result_text = _call_claude_sync(system_prompt, user_prompt, max_tokens=max_tokens, timeout_per_attempt=180)
            dialogue_data = _parse_json(result_text)
            
            if not dialogue_data:
                import re
                json_match = re.search(r'\{[\s\S]*\}', result_text)
                if json_match:
                    dialogue_data = _parse_json(json_match.group(0))
            
            if dialogue_data and "dialogue" in dialogue_data:
                logger.info(f"ParallelDialogue [{project_id}]: Scene {scene_num} complete")
                
                return {
                    "scene_number": scene_num,
                    "dialogue": dialogue_data["dialogue"],
                    "emotion_flow": dialogue_data.get("emotion_flow", "")
                }
            else:
                raise Exception("Invalid JSON response - missing dialogue field")
                
        except Exception as e:
            logger.error(f"ParallelDialogue [{project_id}]: Scene {scene_num} failed - {e}")
            # Return placeholder dialogue
            return {
                "scene_number": scene_num,
                "dialogue": f"Narrador: '{scene.get('description', 'Cena {scene_num}')}...'",
                "error": str(e)
            }
    
    # Launch parallel agents
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(_generate_scene_dialogue, idx, scene): idx 
            for idx, scene in enumerate(scenes)
        }
        
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            dialogue_result = future.result()
            
            with dialogue_lock:
                all_dialogues[idx] = dialogue_result
    
    # Filter out None values (failed scenes)
    valid_dialogues = [d for d in all_dialogues if d is not None]
    
    logger.info(f"ParallelDialogue [{project_id}]: COMPLETE - {len(valid_dialogues)}/{len(scenes)} dialogues generated")
    
    return valid_dialogues
