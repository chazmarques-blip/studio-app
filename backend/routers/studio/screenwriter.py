"""Auto-generated module from studio.py split."""
from ._shared import *

# ── STEP 1: Screenwriter Chat ──

# ── System Prompts for Sora (12s scenes) and Kling (5min scenes) ──

SCREENWRITER_SYSTEM_SORA = """⚠️ CRITICAL LANGUAGE RULE - READ THIS FIRST:
YOU MUST write ALL content (titles, scene descriptions, dialogue, narration, research_notes) in {lang_name} ({lang}).
DO NOT write in English unless the language IS English. DO NOT mix languages.
This rule applies to EVERY scene, EVERY response, EVERY continuation.
MANDATORY and NON-NEGOTIABLE.

===============================================================================
NARRATIVE STRUCTURE - 3-PART STORY ARC (MANDATORY)
===============================================================================

EVERY story MUST follow this 3-part structure:

1. INTRODUÇÃO (Introduction) - First 1-2 scenes
   - Apresenta os personagens principais
   - Estabelece o contexto e cenário
   - Cria o gancho inicial (hook)
   - Tom: Convidativo, estabelece expectativa

2. DESENVOLVIMENTO (Development) - Middle scenes
   - A história principal se desenrola
   - Conflitos, desafios, aventuras
   - Crescimento dos personagens
   - Emoções e reviravoltas

3. ENCERRAMENTO (Closing) - Last 1-2 scenes
   - Resolução da história
   - Moral ou aprendizado (se apropriado para a idade)
   - Fechamento emocional satisfatório
   - CRÍTICO: Convite para a próxima história
   - Exemplo: "E assim... Até a próxima aventura!"
   - Tom: Caloroso, deixa porta aberta para continuação

===============================================================================
CRITICAL CHARACTER LIBRARY RULE - READ THIS SECOND
===============================================================================

IF a CHARACTER LIBRARY is provided in the user prompt below, YOU ARE REQUIRED TO:

1. **USE EXACT NAMES** from the library
   ❌ WRONG: "Abraão"
   ✅ CORRECT: "Abraão Biblizoo Baby"

2. **INCLUDE THE ID** in your JSON response
   ✅ {{"id": "abc123", "name": "Abraão Biblizoo Baby", "description": "..."}}

3. **USE THE ORIGINAL DESCRIPTION** from the library (copy first 150 chars)
   ❌ DO NOT create new descriptions for existing characters
   ✅ Copy the description exactly as provided

4. **ONLY CREATE NEW CHARACTERS** if they absolutely don't exist in the library
   - For new characters, do NOT include "id" field
   - Mark clearly: "name": "NOVO: [Name]"

This is MANDATORY for visual continuity. Characters with IDs will use existing avatars.
Characters without IDs will generate new avatars breaking visual consistency.

===============================================================================

You are a MASTER SCREENWRITER and WORLD-BUILDER. You create RICH, DETAILED screenplays that honor the source material.

**ENGINE: Sora 2** - Cenas curtas de 12 segundos (vídeo fragmentado)

TASK: Create a screenplay structure. Return ONLY valid JSON:
{{
  "title": "Story Title",
  "total_scenes": N,
  "characters": [CHARACTERS],
  "scenes": [SCENES],
  "research_notes": "Sources used",
  "narration": "Brief context"
}}

Each scene:
{{"scene_number": N, "time_start": "M:SS", "time_end": "M:SS", "title": "Title", "description": "RICH visual", "dialogue": "Text", "characters_in_scene": ["Name"], "emotion": "mood", "camera": "shot", "transition": "fade/cut", "transition_from": "How this scene CONNECTS from the previous (visual bridge)", "transition_to": "How this scene ENDS leading into the next", "music_mood": "Music mood for this scene (e.g. alegre, tenso, calmo, épico)", "sfx_notes": "Key sound effects (e.g. sons de natureza, passos na grama, vento)"}}

===============================================================================
SCENE CONTINUITY RULES (CRITICAL FOR CINEMA QUALITY)
===============================================================================

1. VISUAL BRIDGE: Each scene MUST start by connecting to the previous scene's ending.
   - Scene 1 ends with Brenda kneeling in the garden → Scene 2 MUST start in the same garden
   - NEVER teleport characters to new locations without transition
   - Use "transition_from" to describe the visual bridge

2. DIALOGUE FLOW: The last line of dialogue in scene N should naturally lead to scene N+1.
   - End scene: "E agora vamos ver o habitat deles!" → Next scene starts at the habitat
   - Characters should reference what just happened

3. AUDIO CONTINUITY: Use "music_mood" and "sfx_notes" to create sonic flow.
   - Music mood should evolve gradually (not jump from "alegre" to "tenso" without reason)
   - Environmental sounds should match the location
   - If scenes share the same location, share similar sfx_notes

4. CAMERA CONTINUITY: End one scene and start the next with compatible camera angles.
   - End with wide shot → Start next with wide shot of same space
   - End with close-up on character → Start next from same character's perspective

===============================================================================

RULES FOR SORA:
- Each scene = EXACTLY 12 seconds
- Generate 20-30 scenes for a 5-minute story
- Each narrative beat = separate scene
- Detailed visual descriptions for each 12s moment
- **LANGUAGE RULE**: ALL content in {lang_name} ({lang})

DIALOGUE TIMING RULE (CRITICAL FOR LIP SYNC):
- Each scene has ONLY 12 seconds of video
- Dialogue MUST fill 9-10 seconds of speech (leaving only 1-2s for visual transition)
- TARGET: 35-40 words of dialogue per scene (Portuguese ~2.5 words/sec = ~14-16s reading, but spoken faster ~4 words/sec)
- ALL 3 characters should speak in EVERY scene — dynamic back-and-forth conversation
- Short punchy exchanges: Character A says something → Character B reacts → Character C comments
- The LAST line of dialogue must LEAD INTO the next scene's topic naturally
- Example flow: "Snow: 'E agora?' → Ash: 'Agora vamos falar sobre...' → Brenda: 'Vem, meninos!'"
- NEVER leave more than 1 second of silence in a scene

RICHNESS GUIDELINES:
- Simple story → 15-20 scenes
- Medium story → 20-25 scenes  
- Epic story → 25-35+ scenes"""

SCREENWRITER_SYSTEM_KLING = """⚠️ CRITICAL LANGUAGE RULE - READ THIS FIRST:
YOU MUST write ALL content (titles, scene descriptions, dialogue, narration, research_notes) in {lang_name} ({lang}).
DO NOT write in English unless the language IS English. DO NOT mix languages.
This rule applies to EVERY scene, EVERY response, EVERY continuation.
MANDATORY and NON-NEGOTIABLE.

===============================================================================
NARRATIVE STRUCTURE — MANDATORY FOR ALL VIDEOS
===============================================================================

EVERY video script MUST follow this narrative structure regardless of content type:

1. ABERTURA / INTRODUÇÃO (Primeiros 30-60 segundos da primeira cena)
   - Os personagens SE APRESENTAM ao público (quem são, o que fazem)
   - Estabelecem o CONTEXTO: "Hoje vamos falar sobre...", "Você sabia que..."
   - Criam um GANCHO emocional ou de curiosidade
   - Explicam POR QUE estão ali e o que o espectador vai ganhar assistindo
   - Tom: Caloroso, convidativo, como se falasse diretamente com a criança
   - NUNCA pule direto para o conteúdo sem esta introdução

2. DESENVOLVIMENTO / CONTEÚDO (Meio do vídeo — 70-80% do tempo)
   - O conteúdo principal: dicas, história, aventura, aprendizado
   - Cada ponto/dica com transição natural ("E agora...", "Outra coisa importante...")
   - Interação com o público: perguntas retóricas, pausas para resposta
   - Variedade emocional: momentos engraçados, surpresas, carinho
   - Progressão lógica: do mais simples ao mais importante

3. ENCERRAMENTO / DESPEDIDA (Últimos 30-60 segundos da última cena)
   - Recapitulação rápida do que aprenderam/viveram
   - Mensagem emocional de fechamento
   - OBRIGATÓRIO: Convite para o próximo vídeo ("Na próxima aventura...")
   - OBRIGATÓRIO: Pedido de engajamento ("Se gostou, conta pra gente!")
   - Tom: Caloroso, satisfatório, deixa saudade

⚠️ REGRA DE OURO: Se o pedido é "dicas sobre X", NÃO comece direto com "Dica 1".
   Comece com: "Olá! Eu sou [nome]... Hoje vamos descobrir [X]... Preparados?"

⚠️ EXEMPLO DE ABERTURA CORRETA:
   ERRADO: "Dica número 1: prepare-se para fofura..."
   CORRETO: "Ash: 'Olá pessoal! Eu sou o Ash, e essa aqui é minha irmã Snow!'
            Snow: 'Oi gente! Hoje a gente vai contar uns segredos sobre nós, os Pomerâneas!'
            Ash: 'A Brenda, nossa mamãe, pediu pra gente dar umas dicas. Bora lá?'"
   
   Somente DEPOIS desta apresentação é que o conteúdo principal (dicas, história, etc.) deve começar.

===============================================================================

===============================================================================
NARRATIVE STRUCTURE - 3-PART STORY ARC (MANDATORY)
===============================================================================

EVERY story MUST follow this 3-part structure:

1. INTRODUÇÃO (Introduction) - First scene(s)
   - Apresenta os personagens principais
   - Estabelece o contexto e cenário
   - Cria o gancho inicial

2. DESENVOLVIMENTO (Development) - Middle scenes
   - A história principal
   - Conflitos, desafios, aventuras

3. ENCERRAMENTO (Closing) - Last scene(s)
   - Resolução da história
   - CRÍTICO: Convite para a próxima história

===============================================================================
CRITICAL CHARACTER LIBRARY RULE - READ THIS SECOND
===============================================================================

IF a CHARACTER LIBRARY is provided in the user prompt below, YOU ARE REQUIRED TO:

1. **USE EXACT NAMES** from the library
   ❌ WRONG: "Abraão"
   ✅ CORRECT: "Abraão Biblizoo Baby"

2. **INCLUDE THE ID** in your JSON response
   ✅ {{"id": "abc123", "name": "Abraão Biblizoo Baby", "description": "..."}}

3. **USE THE ORIGINAL DESCRIPTION** from the library (copy first 150 chars)
   ❌ DO NOT create new descriptions for existing characters
   ✅ Copy the description exactly as provided

4. **ONLY CREATE NEW CHARACTERS** if they absolutely don't exist in the library
   - For new characters, do NOT include "id" field
   - Mark clearly: "name": "NOVO: [Name]"

This is MANDATORY for visual continuity. Characters with IDs will use existing avatars.
Characters without IDs will generate new avatars breaking visual consistency.

===============================================================================

You are a MASTER SCREENWRITER and WORLD-BUILDER. You create RICH, DETAILED screenplays that honor the source material.

**ENGINE: Kling AI** - Cenas longas de 5 MINUTOS (vídeo contínuo)

TARGET DURATION: {target_duration} minutes total

TASK: Create a screenplay structure. Return ONLY valid JSON:
{{
  "title": "Story Title",
  "total_scenes": {num_scenes},
  "characters": [CHARACTERS],
  "scenes": [SCENES],
  "research_notes": "Sources used",
  "narration": "Brief context"
}}

Each scene (5 MINUTES = 300 SECONDS):
{{"scene_number": N, "time_start": "M:SS", "time_end": "M:SS", "title": "Title", "description": "EXTREMELY DETAILED progression: Opening (0-1min), Rising action (1-2min), Climax (2-3min), Falling action (3-4min), Resolution (4-5min). Include ALL character movements, camera movements, lighting changes, emotional beats", "dialogue": "Complete dialogue with timing markers", "characters_in_scene": ["Names"], "emotion": "mood", "camera": "complex camera choreography", "transition": "seamless/fade"}}

RULES FOR KLING:
- Each scene = EXACTLY 5 MINUTES (300 seconds)
- Total duration: {target_duration} minutes = {num_scenes} scenes
- EACH scene must be SELF-CONTAINED with complete narrative arc
- Description must detail EVERY 10 seconds of the 5-minute scene
- Include precise timing for dialogue, actions, camera moves
- Think CINEMATICALLY - one continuous shot narrative
- Transitions between scenes must be seamless
- **LANGUAGE RULE**: ALL content in {lang_name} ({lang})

SCENE STRUCTURE (5 minutes each):
- Opening (0:00-1:00): Establish setting, characters, mood
- Rising (1:00-2:00): Action develops, tension builds
- Climax (2:00-3:00): Peak emotional/narrative moment
- Falling (3:00-4:00): Consequences, reactions
- Resolution (4:00-5:00): Scene concludes, transition setup

RICHNESS FOR KLING:
- 5min story = 1 scene (one complete act)
- 10min story = 2 scenes (two-act structure)
- 15min story = 3 scenes (three-act structure)
- 20min story = 4 scenes
- 25min story = 5 scenes

Each 5-minute scene should feel like a SHORT FILM with full emotional journey.

===============================================================================
CRITICAL CHARACTER LIBRARY RULE - READ THIS CAREFULLY
===============================================================================

IF a CHARACTER LIBRARY is provided in the user prompt below, YOU ARE REQUIRED TO:

1. **USE EXACT NAMES** from the library
   [X] WRONG: "Abraão"
   [OK] CORRECT: "Abraão Biblizoo Baby"

2. **INCLUDE THE ID** in your JSON response
   [OK] {{"id": "abc123", "name": "Abraão Biblizoo Baby", "description": "..."}}

3. **USE THE ORIGINAL DESCRIPTION** from the library (copy first 150 chars)
   [X] DO NOT create new descriptions for existing characters
   [OK] Copy the description exactly as provided

4. **ONLY CREATE NEW CHARACTERS** if they absolutely don't exist in the library
   - For new characters, do NOT include "id" field
   - Mark clearly: "name": "NOVO: [Name]"

This is MANDATORY for visual continuity. Characters with IDs will use existing avatars.
Characters without IDs will generate new avatars breaking visual consistency.

===============================================================================

You are a MASTER SCREENWRITER and WORLD-BUILDER. You create RICH, DETAILED screenplays that honor the source material."""

# Keep old variable for backwards compatibility
SCREENWRITER_SYSTEM_PHASE1 = """You are a MASTER SCREENWRITER and WORLD-BUILDER. You create RICH, DETAILED screenplays that honor the source material.

TASK: Create a screenplay structure. Return ONLY valid JSON:
{{
  "title": "Story Title",
  "total_scenes": N,
  "characters": [
    {{"id": "character_id_from_library_if_exists", "name": "Full Character Name From Library", "description": "Original description from library OR detailed physical if new", "age": "young/adult/old", "role": "protagonist/supporting"}}
  ],
  "scenes": [SCENES_HERE],
  "research_notes": "Sources used",
  "narration": "Brief context"
}}

Each scene:
{{"scene_number": N, "time_start": "M:SS", "time_end": "M:SS", "title": "Title", "description": "RICH visual: WHERE (landscape, nature), WHEN (time of day, weather), WHAT (action), ATMOSPHERE (light, colors)", "dialogue": "Text or narration", "characters_in_scene": ["Name"], "emotion": "mood", "camera": "shot type", "transition": "fade/cut"}}

RULES:
- Each scene = EXACTLY {scene_duration_label}
- There is NO LIMIT on the number of scenes or characters. Generate as many as the story NEEDS to be rich and faithful
- Generate up to 10 scenes per response. Set "total_scenes" to the FULL number the story needs. If more than 10, I will ask you to continue
- EVERY KEY NARRATIVE MOMENT deserves its OWN dedicated scene. NEVER compress multiple important events into a single scene
- Describe characters PHYSICALLY in detail with species-accurate features
- CRITICAL: If the story uses animals as characters, ALL descriptions MUST use animal features (fur, feathers, hooves, tails, snouts, paws). NEVER describe animal characters with human features (hands, fingers, human skin)
- Characters MUST maintain visually consistent appearance across ALL scenes — same colors, same clothing, same distinguishing marks
- Create as many UNIQUE characters as the story calls for — each with distinct visual identity. Secondary characters, crowds, and background characters ALL deserve proper names and descriptions
- Every scene description MUST include: specific location, time of day, atmosphere, background elements
- Be faithful to source material (bible, history, etc.). Cover the FULL arc of the story — beginning, development, climax, and resolution — with sufficient detail
- **LANGUAGE RULE (MANDATORY)**: ALL text content — title, scene titles, descriptions, dialogue, narration, research_notes — MUST be written ENTIRELY in {lang_name} ({lang}). Do NOT write in English unless the language IS English. This is NON-NEGOTIABLE.

⚠️ REMINDER: You are writing in {lang_name} ({lang}). Do NOT use English. Do NOT mix languages.

RICHNESS GUIDELINES:
- A simple story (1-2 key events) → 5-8 scenes
- A medium story (3-5 key events) → 8-15 scenes
- A rich/epic story (biblical, historical, mythological) → 15-30+ scenes
- Each emotional beat, each location change, each character introduction = a new scene
- If in doubt, MORE scenes is better than fewer. The user wants depth, not summaries."""

LANG_FULL_NAMES = {"pt": "Português (Brazilian Portuguese)", "en": "English", "es": "Español", "fr": "Français", "de": "Deutsch", "it": "Italiano"}


def _run_screenwriter_background(tenant_id: str, project_id: str, message: str, lang: str):
    """Background thread: call Claude screenwriter and save result. Uses chunked approach for reliability."""
    try:
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return

        chat_history = project.get("chat_history", [])

        history_text = "\n".join([
            f"{'USER' if m['role']=='user' else 'SCREENWRITER'}: {m['text'][:500]}"
            for m in chat_history[-6:]
        ])

        audio_mode = project.get("audio_mode", "narrated")

        # Detect video engine and adapt system prompt
        video_engine = project.get("video_engine", "sora")
        
        # ✅ Calculate scene duration based on video engine
        scene_duration_seconds = 300 if video_engine == "kling" else 12
        scene_duration_label = "5 minutos" if video_engine == "kling" else "12 segundos"
        logger.info(f"Screenwriter [{project_id}]: Engine={video_engine}, scene_duration={scene_duration_seconds}s")
        
        target_duration = project.get("target_duration_minutes", 5)
        
        if video_engine == "kling":
            num_scenes = target_duration // 5
            system_template = SCREENWRITER_SYSTEM_KLING
            logger.info(f"Screenwriter [{project_id}]: Kling - {num_scenes} scenes × 5min")
        else:
            num_scenes = (target_duration * 60) // 12
            system_template = SCREENWRITER_SYSTEM_SORA
            logger.info(f"Screenwriter [{project_id}]: Sora - ~{num_scenes} scenes × 12s")
        
        system = system_template.replace("{lang}", lang).replace("{lang_name}", LANG_FULL_NAMES.get(lang, lang)).replace("{target_duration}", str(target_duration)).replace("{num_scenes}", str(num_scenes))

        # Auto-sync character library if not loaded yet
        character_library = project.get("character_library")
        logger.info(f"🔍 Project {project_id}: Checking character_library... Exists: {character_library is not None}")
        
        # ✅ Update pipeline progress: Library step
        _update_project_field(tenant_id, project_id, {
            "pipeline_phase": "library_sync"
        })
        
        if not character_library:
            logger.info(f"📚 Project {project_id}: No character library found, starting auto-sync...")
            try:
                from services.character_library_service import CharacterLibraryService
                avatar_folders = settings.get("avatar_folders", [])
                logger.info(f"📁 Found {len(avatar_folders)} avatar folders")
                
                # ✅ Use project's character_folder_id instead of hardcoded "biblizoo baby"
                target_folder_id = project.get("character_folder_id")
                target_folder = None
                
                if target_folder_id:
                    # Find the specific folder for this project
                    for folder in avatar_folders:
                        if folder.get("id") == target_folder_id:
                            target_folder = folder
                            break
                    if target_folder:
                        logger.info(f"📂 Using project folder: '{target_folder['name']}' (id={target_folder_id})")
                    else:
                        logger.warning(f"⚠️ Project folder_id {target_folder_id} not found in avatar_folders")
                
                if not target_folder:
                    # Fallback: try to find any matching folder
                    for folder in avatar_folders:
                        folder_name = folder.get("name", "").lower()
                        if "biblizoo" in folder_name and "baby" in folder_name:
                            target_folder = folder
                            break
                
                if target_folder:
                    folder_id = target_folder["id"]
                    all_avatars = settings.get("studio_avatars", [])
                    folder_avatars = [a for a in all_avatars if a.get("folder_id") == folder_id]
                    logger.info(f"📦 Found {len(folder_avatars)} avatars in folder '{target_folder['name']}'")
                    
                    if folder_avatars:
                        service = CharacterLibraryService()
                        character_library = service.build_character_library(
                            folder_id=folder_id,
                            folder_name=target_folder['name'],
                            avatars=folder_avatars
                        )
                        project["character_library"] = character_library
                        _save_project(tenant_id, settings, projects)
                        logger.info(f"✅ Auto-synced {character_library.get('total_characters', 0)} characters from {target_folder['name']}")
                    else:
                        logger.warning(f"⚠️ Folder '{target_folder['name']}' found but is empty!")
                else:
                    logger.warning(f"⚠️ No matching folder found! Available: {[f.get('name') for f in avatar_folders]}")
            except Exception as e:
                logger.error(f"❌ Auto-sync character library failed: {e}", exc_info=True)

        # Inject Character Library if available
        character_library_instructions = ""
        if character_library:
            from services.character_library_service import CharacterLibraryService
            character_library_instructions = CharacterLibraryService.format_for_llm_prompt(character_library)
            logger.info(f"Injecting character library: {character_library.get('total_characters', 0)} characters available")

        # Inject audio mode context into prompt
        audio_instruction = ""
        lang_name = LANG_FULL_NAMES.get(lang, lang)
        if audio_mode == "dubbed":
            audio_instruction = f"""

AUDIO MODE: DUBBED (character voices + occasional narrator). The "dialogue" field MUST contain character dialogue lines IN {lang_name}. A narrator may also appear when needed to bridge scenes, explain time passages, or add emotional context — but the MAJORITY of the text should be character dialogue.
Format EXACTLY like this:
"dialogue": "Narrador: 'Naquela noite, sob o manto de estrelas...' / Abraão: 'Meu filho, vamos subir o monte juntos.' / Isaac: 'Sim, pai! Mas onde está o cordeiro?' / Abraão: 'Deus proverá, meu filho.'"

RULES for DUBBED mode:
- Each speaker must be prefixed with their name (or "Narrador") followed by colon
- Separate different speakers with " / "
- Character dialogue should be the MAJORITY (70%+) of the text
- Use "Narrador:" sparingly — only to introduce a scene, mark time passing, or add emotional weight
- Every scene MUST have at least one character speaking
- Keep dialogue natural, emotional, and age-appropriate for each character
- ALL dialogue and narration MUST be in {lang_name}"""
        else:
            audio_instruction = f"""

AUDIO MODE: NARRATED (voice-over narrator). The "dialogue" field should contain narrator text IN {lang_name}.
Format: "dialogue": "Narrador: 'Descrição do que acontece nesta cena...'"
- Use a storytelling narrator voice
- Keep narration concise (2-3 sentences per scene)
- ALL narration MUST be in {lang_name}"""

        # Build character personality context
        characters_list = project.get("characters", [])
        personality_ctx = ""
        chars_with_personality = [c for c in characters_list if c.get("personality")]
        if chars_with_personality:
            personality_lines = []
            for c in chars_with_personality:
                personality_lines.append(f"- {c['name']}: {c['personality']}")
            personality_ctx = f"""

CHARACTER PERSONALITIES (MUST be reflected in dialogue and actions):
{chr(10).join(personality_lines)}

RULES FOR PERSONALITY:
- Each character's dialogue MUST match their personality
- Use their catchphrases/bordões naturally in dialogue
- Their humor style must be consistent across ALL scenes
- Body language in descriptions should match personality (e.g. hyper character = always moving)
"""

        # Detect if project already has scenes (continuation vs new screenplay)
        existing_scenes = project.get("scenes", [])
        is_continuation = len(existing_scenes) > 0

        if is_continuation:
            existing_summary = "\n".join([
                f"Scene {s.get('scene_number')}: {s.get('title')} ({s.get('time_start')}-{s.get('time_end')})"
                for s in existing_scenes
            ])
            last_scene_num = max(s.get("scene_number", 0) for s in existing_scenes)
            last_time_end = existing_scenes[-1].get("time_end", "0:00") if existing_scenes else "0:00"
            user_prompt = f"""Previous conversation:
{history_text}

EXISTING SCREENPLAY (already written — DO NOT rewrite these, only ADD new scenes):
{existing_summary}

{character_library_instructions}
{personality_ctx}
The user now says: {message}
{audio_instruction}

CONTINUATION RULES:
- Scene numbers MUST start from {last_scene_num + 1}
- Time starts from {last_time_end} (each scene = {scene_duration_label})
- Keep the same characters, visual style, and narrative tone
- There is NO limit on new scenes or characters — generate as many as needed to enrich the story
- If the user asks to expand a specific part, create MULTIPLE detailed scenes for it
- Return ONLY JSON with "scenes" array containing the NEW scenes (continuation only)
- Also return "characters" array with any NEW characters introduced (or empty array if none)
- Return "total_scenes" as the total number of NEW scenes in this batch
- ALL text MUST be in {LANG_FULL_NAMES.get(lang, lang)}"""
        else:
            user_prompt = f"""Previous conversation:
{history_text}

{character_library_instructions}
{personality_ctx}
Current request: {message}
{audio_instruction}

⚠️ REGRA OBRIGATÓRIA DE ESTRUTURA NARRATIVA:
A PRIMEIRA CENA deve começar com uma INTRODUÇÃO onde OS PRÓPRIOS PERSONAGENS (não o narrador) se apresentam:
- Cada personagem diz seu nome e quem é: "Ash: 'Oi gente! Eu sou o Ash!'"
- Explicam o que vão fazer no vídeo: "Snow: 'Hoje vamos dar umas dicas!'"
- O narrador pode complementar mas NÃO substitui a fala dos personagens
- Somente DEPOIS desta apresentação dos personagens o conteúdo principal começa
A ÚLTIMA CENA deve ter ENCERRAMENTO com despedida e convite ao próximo vídeo.
PROIBIDO: Começar com "Narrador: 'Hoje temos...'" sem os personagens falarem primeiro.

Create the screenplay. Generate as many scenes and characters as the story NEEDS to be rich and complete — there is NO limit. If the story needs more than 10 scenes, generate the first 10 and set "total_scenes" to the full amount. Return ONLY valid JSON."""

        # Phase 1: Get first batch of scenes (up to 10)
        # ✅ Update pipeline progress: Researcher + Screenwriter active
        _update_project_field(tenant_id, project_id, {
            "pipeline_phase": "researcher_screenwriter"
        })
        
        result = _call_claude_sync(system, user_prompt, max_tokens=8000)
        parsed = _parse_json(result)

        if not parsed:
            # Try to extract from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', result)
            if json_match:
                parsed = _parse_json(json_match.group(1))

        # Re-read project (may have changed)
        settings, projects, project = _get_project(tenant_id, project_id)
        if not project:
            return
        chat_history = project.get("chat_history", [])

        if parsed:
            all_scenes = parsed.get("scenes", [])
            all_characters = parsed.get("characters", [])
            total_needed = parsed.get("total_scenes", len(all_scenes))

            # Phase 2: Aggressive continuation loop — generate ALL remaining scenes
            max_continuation_rounds = 10  # Safety limit (10 rounds × 10 scenes = 100 scenes max)
            round_num = 0
            while total_needed > len(all_scenes) and round_num < max_continuation_rounds:
                round_num += 1
                remaining = total_needed - len(all_scenes)
                try:
                    scene_summary = '\n'.join(
                        f"Scene {s.get('scene_number')}: {s.get('title')}"
                        for s in all_scenes
                    )
                    char_names = ', '.join(c.get('name', '') for c in all_characters)

                    continuation_prompt = f"""Continue the screenplay. Generate scenes {len(all_scenes) + 1} to {total_needed}.

SCENES ALREADY WRITTEN ({len(all_scenes)} of {total_needed}):
{scene_summary}

Characters so far: {char_names}
Story: {message}

IMPORTANT:
- Generate up to 10 scenes in this batch
- Scene numbers start from {len(all_scenes) + 1}
- Time starts from {all_scenes[-1].get('time_end', '0:00')} (each scene = 12 seconds)
- Keep the same visual style, characters, and narrative tone
- Introduce NEW characters when the story calls for them — there is NO character limit
- If the story needs more key moments, add them. Be RICH and DETAILED
- ALL text (titles, descriptions, dialogue) MUST be in {LANG_FULL_NAMES.get(lang, lang)}
- Return ONLY JSON with "scenes" array and optionally "characters" array for NEW characters introduced"""

                    cont_result = _call_claude_sync(system, continuation_prompt, max_tokens=8000)
                    cont_parsed = _parse_json(cont_result)
                    if not cont_parsed:
                        import re
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', cont_result)
                        if json_match:
                            cont_parsed = _parse_json(json_match.group(1))

                    if cont_parsed and cont_parsed.get("scenes"):
                        new_scenes = cont_parsed["scenes"]
                        all_scenes.extend(new_scenes)
                        if cont_parsed.get("characters"):
                            existing_names = {c["name"] for c in all_characters}
                            for c in cont_parsed["characters"]:
                                if c.get("name") not in existing_names:
                                    all_characters.append(c)
                        # Update total_needed if Claude indicates more are needed
                        if cont_parsed.get("total_scenes") and cont_parsed["total_scenes"] > total_needed:
                            total_needed = cont_parsed["total_scenes"]
                        logger.info(f"Studio [{project_id}]: Continuation round {round_num} added {len(new_scenes)} scenes (total: {len(all_scenes)}/{total_needed})")
                    else:
                        logger.warning(f"Studio [{project_id}]: Continuation round {round_num} returned no scenes. Stopping.")
                        break
                except Exception as e2:
                    logger.warning(f"Studio [{project_id}]: Continuation round {round_num} failed: {e2}. Using {len(all_scenes)} scenes.")
                    break

            if round_num > 0:
                logger.info(f"Studio [{project_id}]: Screenplay complete — {len(all_scenes)} scenes, {len(all_characters)} characters after {round_num} continuation rounds")

            # Re-read existing scenes
            prev_scenes = project.get("scenes", [])

            # ALWAYS replace scenes when generating a fresh screenplay
            # The merge logic was causing duplication (35 old + 25 new = 60 scenes)
            project["scenes"] = all_scenes
            project["characters"] = all_characters
            logger.info(f"Studio [{project_id}]: Screenplay set to {len(all_scenes)} scenes (replaced {len(prev_scenes)} previous)")

            # Unify dialogue: dubbed_text is the canonical dialogue source
            for scene in all_scenes:
                if scene.get("dubbed_text"):
                    scene["dialogue"] = scene["dubbed_text"]

            final_scenes = project["scenes"]
            final_characters = project.get("characters", [])

            # ===============================================================
            # PHASE 2: CONTENT ADVISORS SYSTEM
            # Apply content advisors if enabled in project configuration
            # ===============================================================
            from services.advisor_chain import AdvisorChain, has_active_advisors
            import asyncio
            
            advisor_results = None
            if has_active_advisors(project):
                try:
                    logger.info(f"Studio [{project_id}]: Content advisors are enabled, processing screenplay")
                    
                    # Build complete screenplay text from all scenes
                    screenplay_text = f"{parsed.get('title', 'Untitled')}\n\n"
                    for scene in final_scenes:
                        screenplay_text += f"CENA {scene.get('scene_number')}: {scene.get('title', '')}\n"
                        screenplay_text += f"{scene.get('description', '')}\n"
                        if scene.get('dialogue'):
                            screenplay_text += f"{scene['dialogue']}\n"
                        screenplay_text += "\n"
                    
                    # Process through advisor chain (sync wrapper for async function)
                    chain = AdvisorChain()
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    advisor_results = loop.run_until_complete(chain.process(screenplay_text, project))
                    loop.close()
                    
                    # Save advisor results to project
                    project["agents_output"]["content_advisors"] = {
                        "applied": advisor_results["applied_advisors"],
                        "stages": {
                            advisor_name: stage[:500] + "..." if len(stage) > 500 else stage
                            for advisor_name, stage in advisor_results["stages"].items()
                            if isinstance(stage, str)
                        },
                        "final_length": len(advisor_results["final"])
                    }
                    
                    logger.info(f"Studio [{project_id}]: Content advisors applied: {advisor_results['applied_advisors']}")
                    
                except Exception as advisor_error:
                    logger.error(f"Studio [{project_id}]: Content advisors failed: {advisor_error}")
                    # Continue without advisors on error
                    project["agents_output"]["content_advisors"] = {
                        "error": str(advisor_error)[:300]
                    }

            project["agents_output"] = project.get("agents_output", {})
            project["agents_output"]["screenwriter"] = {
                "title": parsed.get("title", ""),
                "research_notes": parsed.get("research_notes", ""),
                "narration": parsed.get("narration", ""),
            }
            
            # Build assistant text
            assistant_text = f"**{parsed.get('title', 'Roteiro')}** — {len(all_scenes)} {'novas cenas' if prev_scenes and not prev_scene_nums.intersection(new_scene_nums) else 'cenas'} (total: {len(final_scenes)})\n\n"
            
            # Add advisor info if applied
            if advisor_results and advisor_results["applied_advisors"]:
                assistant_text += f"✨ **Content Advisors aplicados:** {', '.join(advisor_results['applied_advisors'])}\n\n"
            
            for s in all_scenes:
                assistant_text += f"**CENA {s.get('scene_number','')}** ({s.get('time_start','')}-{s.get('time_end','')}) — {s.get('title','')}\n"
                assistant_text += f"_{s.get('description','')}_\n"
                if s.get('dialogue'):
                    assistant_text += f'"{s["dialogue"]}"\n'
                assistant_text += f"Personagens: {', '.join(s.get('characters_in_scene',[]))}\n\n"
            assistant_text += f"\n**Personagens identificados:** {', '.join(c.get('name','') for c in final_characters)}"
            if parsed.get("research_notes"):
                assistant_text += f"\n\n**Pesquisa:** {parsed['research_notes'][:300]}"
        else:
            assistant_text = result

        chat_history.append({"role": "assistant", "text": assistant_text})
        project["chat_history"] = chat_history[-20:]
        project["status"] = "scripting"
        project["chat_status"] = "done"
        project["pipeline_phase"] = "screenwriter_done"
        project["updated_at"] = datetime.now(timezone.utc).isoformat()
        n_scenes = len(project.get('scenes', []))
        n_chars = len(project.get('characters', []))
        _add_milestone(project, "screenplay_created", f"Roteiro criado — {n_scenes} cenas, {n_chars} personagens")
        _save_project(tenant_id, settings, projects, flush_now=True)

        logger.info(f"Studio [{project_id}]: Screenwriter done — {n_scenes} scenes")

    except Exception as e:
        logger.error(f"Studio [{project_id}] screenwriter error: {e}")
        settings, projects, project = _get_project(tenant_id, project_id)
        if project:
            project["chat_status"] = "error"
            project["error"] = str(e)[:300]
            _save_project(tenant_id, settings, projects, flush_now=True)


@router.post("/chat")
async def screenwriter_chat(req: ChatMessage, tenant=Depends(get_current_tenant)):
    """Start screenwriter in background (avoids K8s 60s proxy timeout)."""
    lang = req.language or "pt"

    if req.project_id:
        settings, projects, project = _get_project(tenant["id"], req.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        settings = _get_settings(tenant["id"])
        projects = settings.get("studio_projects", [])
        now = datetime.now(timezone.utc).isoformat()
        project = {
            "id": uuid.uuid4().hex[:12],
            "name": req.message[:50],
            "scene_type": "multi_scene",
            "briefing": req.message,
            "scenes": [],
            "characters": [],
            "chat_history": [],
            "agents_output": {},
            "agent_status": {},
            "outputs": [],
            "status": "scripting",
            "chat_status": "thinking",
            "error": None,
            "language": lang,
            "created_at": now,
            "updated_at": now,
        }
        projects.insert(0, project)

    # Save user message and set thinking status
    chat_history = project.get("chat_history", [])
    chat_history.append({"role": "user", "text": req.message})
    project["chat_history"] = chat_history[-20:]
    project["chat_status"] = "thinking"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)

    # Start background thread - USE PARALLEL GENERATION
    from .parallel_agents import generate_screenplay_parallel
    
    def _parallel_screenplay_wrapper():
        try:
            audio_mode = project.get("audio_mode", "narrated")
            character_folder_id = project.get("character_folder_id")  # NEW
            target_audience = project.get("target_audience", "all")  # NEW
            video_engine = project.get("video_engine", "sora")  # NEW: Get video engine
            target_duration = project.get("target_duration_minutes", 5)  # FIXED: Get target duration
            
            logger.info(f"Screenwriter [{project['id']}]: Using engine={video_engine}, target_duration={target_duration}min, target_audience={target_audience}")
            
            result = generate_screenplay_parallel(
                tenant_id=tenant["id"],
                project_id=project["id"],
                user_prompt=req.message,
                lang=lang,
                audio_mode=audio_mode,
                max_scenes=50,
                batch_size=10,
                max_workers=3,
                character_folder_id=character_folder_id,  # NEW
                target_audience=target_audience,  # NEW
                video_engine=video_engine,  # NEW: Pass video engine
                target_duration_minutes=target_duration  # FIXED: Pass target duration
            )
            _merge_screenplay_results(tenant["id"], project["id"], result)
        except Exception as e:
            logger.error(f"Parallel screenplay error: {e}, falling back")
            _run_screenwriter_background(tenant["id"], project["id"], req.message, lang)
    
    thread = threading.Thread(
        target=_parallel_screenplay_wrapper,
        daemon=True,
    )
    thread.start()

    return {
        "project_id": project["id"],
        "status": "thinking",
        "message": None,
        "scenes": project.get("scenes", []),
        "characters": project.get("characters", []),
    }


def _merge_screenplay_results(tenant_id: str, project_id: str, result: dict):
    """Merge parallel generation results"""
    settings, projects, project = _get_project(tenant_id, project_id)
    if not project:
        return
    
    existing_scenes = project.get("scenes", [])
    new_scenes = result.get("scenes", [])
    
    if existing_scenes:
        last_num = max(s.get("scene_number", 0) for s in existing_scenes)
        for ns in new_scenes:
            ns["scene_number"] = last_num + 1
            last_num += 1
        existing_scenes.extend(new_scenes)
    else:
        existing_scenes = new_scenes
    
    existing_chars = project.get("characters", [])
    existing_names = {c.get("name") for c in existing_chars}
    for new_char in result.get("characters", []):
        if new_char.get("name") not in existing_names:
            existing_chars.append(new_char)
    
    project["scenes"] = existing_scenes
    project["characters"] = existing_chars
    project["title"] = result.get("title", project.get("title", "Untitled"))
    
    chat_history = project.get("chat_history", [])
    chat_history.append({"role": "agent", "text": f"✅ {len(new_scenes)} cenas geradas!"})
    project["chat_history"] = chat_history[-20:]
    project["chat_status"] = "idle"
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    _save_project(tenant_id, settings, projects)



@router.post("/projects/{project_id}/reset-chat")
async def reset_chat(project_id: str, tenant=Depends(get_current_tenant)):
    """Reset a stuck chat_status back to 'idle' so user can retry."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project["chat_status"] = "idle"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)
    return {"status": "ok", "chat_status": "idle"}


@router.post("/projects/{project_id}/retry-chat")
async def retry_chat(project_id: str, tenant=Depends(get_current_tenant)):
    """Retry the last user message in the screenwriter chat."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chat_history = project.get("chat_history", [])
    last_user_msg = None
    for m in reversed(chat_history):
        if m["role"] == "user":
            last_user_msg = m["text"]
            break

    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message to retry")

    project["chat_status"] = "thinking"
    project["error"] = None
    _save_project(tenant["id"], settings, projects)

    lang = project.get("language", "pt")
    thread = threading.Thread(
        target=_run_screenwriter_background,
        args=(tenant["id"], project_id, last_user_msg, lang),
        daemon=True,
    )
    thread.start()

    return {"status": "thinking", "message": last_user_msg}





@router.patch("/projects/{project_id}/scenes/{scene_number}")
async def update_scene(project_id: str, scene_number: int, payload: dict = Body(...), tenant=Depends(get_current_tenant)):
    """Update individual scene fields (dialogue, description, title, etc.)."""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    scenes = project.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_number") == scene_number), None)
    if not scene:
        raise HTTPException(status_code=404, detail=f"Scene {scene_number} not found")
    
    # Update allowed fields
    allowed = {"dialogue", "dubbed_text", "description", "title", "emotion", "camera", 
               "transition", "transition_from", "transition_to", "music_mood", "sfx_notes"}
    updated = []
    for key, value in payload.items():
        if key in allowed:
            scene[key] = value
            updated.append(key)
    
    # Keep dialogue and dubbed_text in sync
    if "dialogue" in payload:
        scene["dubbed_text"] = payload["dialogue"]
    elif "dubbed_text" in payload:
        scene["dialogue"] = payload["dubbed_text"]
    
    _save_project(tenant["id"], settings, projects, flush_now=True)
    logger.info(f"Scene {scene_number} updated: {updated}")
    
    return {"status": "ok", "scene_number": scene_number, "updated": updated}
