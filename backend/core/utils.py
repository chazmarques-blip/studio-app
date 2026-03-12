"""Shared utility functions for AgentZZ API"""
from core.constants import AGENT_TYPE_DESCRIPTIONS


# In-memory store for sandbox sessions (not persisted - sandbox is for testing only)
sandbox_sessions: dict = {}


def build_agent_system_prompt(agent: dict, knowledge_items: list = None) -> str:
    """Build a rich system prompt based on agent config, tone, and knowledge base"""
    name = agent.get("name", "Assistant")
    agent_type = agent.get("type", "support")
    tone = agent.get("tone", "professional")
    emoji_level = agent.get("emoji_level", 0.3)
    verbosity = agent.get("verbosity_level", 0.5)
    custom_prompt = agent.get("system_prompt", "")
    knowledge_text = agent.get("knowledge_instructions", "")
    escalation = agent.get("escalation_rules", {})

    tone_map = {
        "professional": "formal, respectful, and business-oriented",
        "friendly": "warm, approachable, and conversational",
        "empathetic": "understanding, caring, and emotionally supportive",
        "direct": "clear, concise, and straight to the point",
        "consultive": "advisory, asking questions to understand needs before suggesting solutions",
    }
    tone_desc = tone_map.get(tone, tone_map["professional"])

    emoji_desc = "Never use emojis." if emoji_level < 0.2 else "Use emojis sparingly." if emoji_level < 0.5 else "Use emojis frequently to be expressive."
    verbosity_desc = "Keep responses very short (1-2 sentences)." if verbosity < 0.3 else "Give moderate detail (2-3 sentences)." if verbosity < 0.7 else "Provide detailed, comprehensive responses."

    escalation_keywords = escalation.get("keywords", ["atendente", "humano", "gerente"])

    prompt = f"""You are {name}, a specialized {agent_type} assistant.

PERSONALITY & TONE:
- Your communication style is {tone_desc}
- {emoji_desc}
- {verbosity_desc}

LANGUAGE:
- ALWAYS respond in the same language the customer writes to you
- If Portuguese, respond in Portuguese. If English, respond in English. If Spanish, respond in Spanish.

ESCALATION RULES:
- If the customer mentions any of these words: {', '.join(escalation_keywords)}, or expresses strong frustration/anger, respond that you will transfer them to a human agent
- When escalating, be empathetic and assure them a human will help shortly
"""

    if custom_prompt:
        prompt += f"\nCUSTOM INSTRUCTIONS:\n{custom_prompt}\n"

    if knowledge_text:
        prompt += f"\nKNOWLEDGE BASE INSTRUCTIONS:\n{knowledge_text}\n"

    if knowledge_items:
        prompt += "\nKNOWLEDGE BASE (use this information to answer customer questions):\n"
        for item in knowledge_items:
            prompt += f"\n## {item.get('title', '')}\n{item.get('content', '')}\n"

    prompt += "\nIMPORTANT: Be natural and human-like. Never reveal you are an AI unless directly asked."
    return prompt


def check_escalation(content: str, agent: dict) -> bool:
    """Check if message should trigger escalation to human"""
    rules = agent.get("escalation_rules", {})
    keywords = rules.get("keywords", ["atendente", "humano", "gerente", "reclamação"])
    content_lower = content.lower()
    return any(kw.lower() in content_lower for kw in keywords)


async def evo_request(method: str, api_url: str, api_key: str, path: str, json_data: dict = None):
    """Make a request to Evolution API"""
    import httpx
    url = f"{api_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        elif method == "POST":
            resp = await client.post(url, headers=headers, json=json_data or {})
        elif method == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            resp = await client.get(url, headers=headers)
        return resp
