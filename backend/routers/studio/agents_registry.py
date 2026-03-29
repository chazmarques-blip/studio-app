"""
Studio Agents Registry
API for viewing and managing StudioX AI agent specifications
"""
from ._shared import *
import os
import json

AGENTS_DIR = "/app/memory/agents"


@router.get("/agents/registry")
async def list_studio_agents(user=Depends(get_current_user)):
    """List all StudioX AI agents"""
    agents = []
    
    if not os.path.exists(AGENTS_DIR):
        return {"agents": [], "total": 0}
    
    for filename in os.listdir(AGENTS_DIR):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(AGENTS_DIR, filename), 'r', encoding='utf-8') as f:
                    agent = json.load(f)
                    agents.append({
                        "id": agent.get("id"),
                        "name": agent.get("name"),
                        "phase": agent.get("phase"),
                        "version": agent.get("version"),
                        "description": agent.get("description")
                    })
            except Exception as e:
                logger.error(f"Failed to load agent {filename}: {e}")
                continue
    
    # Sort by phase order
    phase_order = {"research": 1, "consensus": 2, "production": 3, "validation": 4, "execution": 5}
    agents.sort(key=lambda x: (phase_order.get(x.get("phase", ""), 99), x.get("name", "")))
    
    return {"agents": agents, "total": len(agents)}


@router.get("/agents/registry/{agent_id}")
async def get_studio_agent(agent_id: str, user=Depends(get_current_user)):
    """Get full specification of a StudioX AI agent"""
    agent_path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
    
    if not os.path.exists(agent_path):
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    with open(agent_path, 'r', encoding='utf-8') as f:
        agent = json.load(f)
    
    return {"agent": agent}


@router.put("/agents/registry/{agent_id}")
async def update_studio_agent(
    agent_id: str, 
    agent_data: Dict, 
    user=Depends(get_current_user)
):
    """Update agent specification (for fine-tuning)"""
    agent_path = os.path.join(AGENTS_DIR, f"{agent_id}.json")
    
    if not os.path.exists(agent_path):
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
    
    # Update timestamp
    from datetime import datetime
    agent_data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%d")
    
    with open(agent_path, 'w', encoding='utf-8') as f:
        json.dump(agent_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"AgentRegistry: Updated {agent_id}")
    
    return {"status": "updated", "agent_id": agent_id}
