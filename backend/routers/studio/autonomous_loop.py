"""
StudioX Autonomous Loop Engine
Orchestrates multi-agent collaboration until quality score >= 90%
"""
from ._shared import *
import json
import asyncio
from typing import Dict, List

# ── Load Agent Specifications ──

def load_agent_spec(agent_id: str) -> Dict:
    """Load agent specification from /app/memory/agents/"""
    import os
    agent_path = f"/app/memory/agents/{agent_id}.json"
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"Agent spec not found: {agent_id}")
    
    with open(agent_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── Multi-Agent Consensus Room ──

async def multi_agent_consensus(project_id: str, tenant_id: str, user_prompt: str) -> Dict:
    """
    FASE 2: Sala de Reunião (Consensus Room)
    Orchestrates collaboration between specialized agents to create unified Project Bible
    """
    logger.info(f"ConsensusRoom [{project_id}]: Starting multi-agent consensus")
    
    # Load agent specs
    orchestrator_spec = load_agent_spec("orchestrator_agent")
    
    # Get project and bible
    settings, projects, project = _get_project(tenant_id, project_id)
    bible = project.get("project_bible", {})
    characters = bible.get("characters", [])
    
    # Build context for orchestrator
    context = f"""
USER PROMPT: {user_prompt}

APPROVED CHARACTERS:
{json.dumps(characters, indent=2)}

PROJECT METADATA:
- Visual Style: {bible.get('visual_style', {}).get('art_style', 'pixar_3d')}
- Language: {project.get('language', 'pt')}

YOUR TASK:
Create a comprehensive Project Bible that will serve as the foundation for all production work.
Define:
1. Visual style details (color palette, lighting, camera style)
2. Narrative elements (tone, period, themes)
3. Production scope (target duration, estimated scenes)

Return ONLY valid JSON in this format:
{{
  "visual_style": {{
    "art_style": "pixar_3d",
    "color_palette": ["#hex1", "#hex2"],
    "lighting": "description",
    "camera_style": "description"
  }},
  "narrative_elements": {{
    "tone": "description",
    "period": "historical period",
    "target_duration": "X minutes",
    "key_themes": ["theme1", "theme2"]
  }},
  "production_metadata": {{
    "total_scenes_planned": 15,
    "estimated_cost_usd": 45.0,
    "estimated_duration_seconds": 180
  }},
  "consensus_log": ["decision 1", "decision 2"],
  "quality_score": 95
}}
"""
    
    # Call Claude with orchestrator prompt
    messages = [{"role": "user", "content": context}]
    
    try:
        response = client_anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4000,
            system=orchestrator_spec["system_prompt"],
            messages=messages,
            temperature=0.7
        )
        
        raw_text = response.content[0].text.strip()
        
        # Parse JSON response
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        consensus_result = json.loads(raw_text)
        
        logger.info(f"ConsensusRoom [{project_id}]: Consensus achieved with score {consensus_result.get('quality_score', 0)}")
        
        return consensus_result
        
    except Exception as e:
        logger.error(f"ConsensusRoom [{project_id}]: Error - {e}")
        raise HTTPException(status_code=500, detail=f"Consensus failed: {str(e)}")


# ── Quality Validation ──

# ── Dialogue Generation ──

async def generate_dialogues(project_id: str, tenant_id: str, bible: Dict, screenplay: Dict) -> List[Dict]:
    """
    FASE 3.2: Generate high-quality cinematic dialogues
    """
    logger.info(f"DialogueWriter [{project_id}]: Generating dialogues")
    
    dialogue_spec = load_agent_spec("dialogue_writer_agent")
    
    scenes = screenplay.get("scenes", [])
    all_dialogues = []
    
    for scene in scenes[:3]:  # Process first 3 scenes for now (can be parallelized)
        context = f"""
PROJECT BIBLE:
{json.dumps(bible.get('characters', []), indent=2)}

SCENE:
- Number: {scene.get('scene_number', '?')}
- Title: {scene.get('title', '')}
- Location: {scene.get('location', '')}
- Characters: {', '.join(scene.get('characters_in_scene', []))}
- Emotion: {scene.get('emotion', '')}
- Description: {scene.get('description', '')}

Write cinematic dialogues for this scene following the quality criteria.
Return ONLY valid JSON:
{{
  "scene_{scene.get('scene_number', 1)}": {{
    "dialogues": [
      {{
        "character": "name",
        "line": "dialogue text",
        "emotion": "emotion",
        "timing": "2.5s",
        "action_note": "what character is doing"
      }}
    ],
    "subtext": "underlying meaning",
    "quality_score": 92
  }}
}}
"""
        
        try:
            response = client_anthropic.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=2000,
                system=dialogue_spec["system_prompt"],
                messages=[{"role": "user", "content": context}],
                temperature=0.8
            )
            
            raw_text = response.content[0].text.strip()
            
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            
            scene_dialogues = json.loads(raw_text)
            all_dialogues.append({
                "scene_number": scene.get('scene_number'),
                **list(scene_dialogues.values())[0]
            })
            
        except Exception as e:
            logger.error(f"DialogueWriter [{project_id}]: Error in scene {scene.get('scene_number')} - {e}")
            continue
    
    logger.info(f"DialogueWriter [{project_id}]: Generated dialogues for {len(all_dialogues)} scenes")
    return all_dialogues


# ── Narration Generation ──

async def generate_narration(project_id: str, tenant_id: str, bible: Dict, screenplay: Dict, dialogues: List[Dict]) -> List[Dict]:
    """
    FASE 3.3: Generate high-quality cinematic narration
    """
    logger.info(f"Narrator [{project_id}]: Generating narration")
    
    narrator_spec = load_agent_spec("narrator_agent")
    
    context = f"""
PROJECT BIBLE:
{json.dumps(bible.get('narrative_elements', {}), indent=2)}

SCREENPLAY:
{json.dumps(screenplay.get('scenes', [])[:3], indent=2)}

DIALOGUES ALREADY WRITTEN:
{json.dumps(dialogues, indent=2)}

Write cinematic narration that COMPLEMENTS (not duplicates) the visuals and dialogues.
Focus on emotional context, transitions, and poetic atmosphere.

Return ONLY valid JSON:
{{
  "narration": [
    {{
      "scene_range": [1, 3],
      "text": "narration text",
      "timing": "12.5s",
      "tone": "epic/intimate/reflective",
      "voice_instruction": "pause instructions"
    }}
  ],
  "quality_score": 95
}}
"""
    
    try:
        response = client_anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=narrator_spec["system_prompt"],
            messages=[{"role": "user", "content": context}],
            temperature=0.8
        )
        
        raw_text = response.content[0].text.strip()
        
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        narration_result = json.loads(raw_text)
        narration = narration_result.get("narration", [])
        
        logger.info(f"Narrator [{project_id}]: Generated {len(narration)} narration blocks")
        return narration
        
    except Exception as e:
        logger.error(f"Narrator [{project_id}]: Error - {e}")
        return []


# ── Quality Validation ──

async def validate_quality(project_id: str, tenant_id: str, bible: Dict) -> Dict:
    """
    FASE 4: Quality Validation
    Validates all components and calculates quality score
    """
    logger.info(f"QualityCheck [{project_id}]: Validating quality")
    
    validator_spec = load_agent_spec("quality_validator_agent")
    
    # Build validation context
    context = f"""
PROJECT BIBLE:
{json.dumps(bible, indent=2)}

Evaluate the quality of this Project Bible across all criteria.
Return ONLY valid JSON:
{{
  "quality_score": 95,
  "breakdown": {{
    "visual_consistency": 92,
    "narrative_coherence": 95,
    "character_development": 90,
    "production_feasibility": 98
  }},
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2"],
  "ready_for_user": true
}}
"""
    
    try:
        response = client_anthropic.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=validator_spec.get("system_prompt", "You are a quality validator."),
            messages=[{"role": "user", "content": context}],
            temperature=0.3
        )
        
        raw_text = response.content[0].text.strip()
        
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()
        
        validation_result = json.loads(raw_text)
        
        logger.info(f"QualityCheck [{project_id}]: Score = {validation_result.get('quality_score', 0)}")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"QualityCheck [{project_id}]: Error - {e}")
        return {
            "quality_score": 0,
            "breakdown": {},
            "issues": [str(e)],
            "recommendations": [],
            "ready_for_user": False
        }


# ── Autonomous Loop Engine ──

class AutonomousLoopRequest(BaseModel):
    project_id: str
    user_prompt: str


@router.post("/autonomous-loop/start")
async def start_autonomous_loop(
    req: AutonomousLoopRequest,
    tenant=Depends(get_current_tenant)
):
    """
    Start autonomous loop: agents work together until quality >= 90%
    
    PHASES:
    1. Multi-Agent Consensus (Sala de Reunião)
    2. Quality Validation
    3. If score < 90: refine and repeat
    4. If score >= 90: save final checkpoint
    """
    project_id = req.project_id
    user_prompt = req.user_prompt
    
    logger.info(f"AutonomousLoop [{project_id}]: Starting...")
    
    # Get project
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    bible = project.get("project_bible")
    if not bible:
        raise HTTPException(status_code=400, detail="Project Bible not initialized. Call /create-bible first.")
    
    iteration = 0
    max_iterations = 5
    quality_score = 0
    min_quality = 90
    
    consensus_log = []
    
    while quality_score < min_quality and iteration < max_iterations:
        iteration += 1
        logger.info(f"AutonomousLoop [{project_id}]: Iteration {iteration}/{max_iterations}")
        
        # FASE 2: Multi-Agent Consensus
        try:
            consensus_result = await multi_agent_consensus(project_id, tenant["id"], user_prompt)
            
            # Update bible with consensus
            bible["visual_style"] = consensus_result.get("visual_style", bible.get("visual_style", {}))
            bible["narrative_elements"] = consensus_result.get("narrative_elements", bible.get("narrative_elements", {}))
            bible["production_metadata"] = consensus_result.get("production_metadata", bible.get("production_metadata", {}))
            bible["iteration"] = iteration
            
            consensus_log.extend(consensus_result.get("consensus_log", []))
            
        except Exception as e:
            logger.error(f"AutonomousLoop [{project_id}]: Consensus failed - {e}")
            break
        
        # FASE 3.1: Generate Screenplay Structure (simplified for now)
        try:
            screenplay = {
                "scenes": [
                    {
                        "scene_number": 1,
                        "title": "Opening",
                        "location": "Laboratory",
                        "characters_in_scene": [c["name"] for c in bible.get("characters", [])[:2]],
                        "emotion": "Determined",
                        "description": "Scientist working late at night"
                    },
                    {
                        "scene_number": 2,
                        "title": "Discovery",
                        "location": "Laboratory",
                        "characters_in_scene": [c["name"] for c in bible.get("characters", [])[:2]],
                        "emotion": "Excited",
                        "description": "Breakthrough moment"
                    },
                    {
                        "scene_number": 3,
                        "title": "Recognition",
                        "location": "Academy",
                        "characters_in_scene": [c["name"] for c in bible.get("characters", [])[:1]],
                        "emotion": "Triumphant",
                        "description": "Receiving award"
                    }
                ]
            }
            bible["screenplay"] = screenplay
            logger.info(f"AutonomousLoop [{project_id}]: Screenplay created with {len(screenplay['scenes'])} scenes")
        except Exception as e:
            logger.error(f"AutonomousLoop [{project_id}]: Screenplay generation failed - {e}")
        
        # FASE 3.2: Generate Dialogues
        try:
            dialogues = await generate_dialogues(project_id, tenant["id"], bible, screenplay)
            bible["dialogues"] = dialogues
            logger.info(f"AutonomousLoop [{project_id}]: Dialogues generated for {len(dialogues)} scenes")
        except Exception as e:
            logger.error(f"AutonomousLoop [{project_id}]: Dialogue generation failed - {e}")
            bible["dialogues"] = []
        
        # FASE 3.3: Generate Narration
        try:
            narration = await generate_narration(project_id, tenant["id"], bible, screenplay, dialogues)
            bible["narration"] = narration
            logger.info(f"AutonomousLoop [{project_id}]: Narration generated ({len(narration)} blocks)")
        except Exception as e:
            logger.error(f"AutonomousLoop [{project_id}]: Narration generation failed - {e}")
            bible["narration"] = []
        
        # FASE 4: Quality Validation
        try:
            validation = await validate_quality(project_id, tenant["id"], bible)
            
            quality_score = validation.get("quality_score", 0)
            bible["quality_score"] = quality_score
            bible["quality_breakdown"] = validation.get("breakdown", {})
            bible["issues"] = validation.get("issues", [])
            bible["recommendations"] = validation.get("recommendations", [])
            
            logger.info(f"AutonomousLoop [{project_id}]: Iteration {iteration} - Quality Score = {quality_score}%")
            
            if quality_score >= min_quality:
                logger.info(f"AutonomousLoop [{project_id}]: ✅ Quality threshold reached!")
                break
            else:
                logger.info(f"AutonomousLoop [{project_id}]: ⚠️ Below threshold, refining...")
                
        except Exception as e:
            logger.error(f"AutonomousLoop [{project_id}]: Validation failed - {e}")
            break
    
    # Save final bible
    project["project_bible"] = bible
    project["consensus_log"] = consensus_log
    await _save_project(tenant["id"], project)
    
    status = "ready_for_approval" if quality_score >= min_quality else "max_iterations_reached"
    
    return {
        "status": status,
        "quality_score": quality_score,
        "iterations": iteration,
        "bible": bible
    }


@router.get("/autonomous-loop/status/{project_id}")
async def get_loop_status(
    project_id: str,
    tenant=Depends(get_current_tenant)
):
    """Get current status of autonomous loop"""
    settings, projects, project = _get_project(tenant["id"], project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    bible = project.get("project_bible", {})
    
    return {
        "project_id": project_id,
        "quality_score": bible.get("quality_score", 0),
        "iteration": bible.get("iteration", 0),
        "status": bible.get("status", "not_started"),
        "ready_for_approval": bible.get("quality_score", 0) >= 90
    }
