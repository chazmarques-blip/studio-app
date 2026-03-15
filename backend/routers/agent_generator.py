from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import time
import uuid

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper, EMERGENT_KEY, logger

router = APIRouter(prefix="/api", tags=["agent-generator"])


class AgentGenerateRequest(BaseModel):
    segment: str
    objective: str
    tone: str
    business_name: str
    business_description: str
    products_services: Optional[str] = ""
    hours: Optional[str] = ""
    differentials: Optional[str] = ""
    target_audience: Optional[str] = ""
    language: Optional[str] = "pt"


SEGMENT_CONTEXT = {
    "ecommerce": "e-commerce, online retail, product sales, cart recovery, order tracking",
    "restaurant": "restaurant, food service, menu, delivery, reservations, takeout",
    "health": "healthcare, medical clinic, appointments, patient care, exams, insurance",
    "beauty": "beauty salon, spa, aesthetic services, appointments, treatments",
    "real_estate": "real estate, property sales, rentals, viewings, buyer qualification",
    "automotive": "automotive dealership, vehicle sales, test drives, financing, service",
    "education": "educational institution, courses, enrollment, student support, tutoring",
    "finance": "financial services, investments, insurance, loans, financial planning",
    "travel": "travel agency, tourism, bookings, itineraries, hotels, flights",
    "fitness": "gym, fitness center, personal training, memberships, classes",
    "legal": "law firm, legal services, consultations, case management",
    "events": "event planning, weddings, corporate events, venues, catering",
    "saas": "SaaS platform, software service, onboarding, technical support, subscriptions",
    "logistics": "logistics, shipping, freight, delivery tracking, warehousing",
    "telecom": "telecommunications, internet, phone plans, billing, technical support",
    "general": "general business, customer service, sales, support",
}

OBJECTIVE_MAP = {
    "sales": "qualify leads, present products/services, close deals, upsell, cross-sell",
    "support": "resolve issues, troubleshoot problems, answer questions, provide guidance",
    "scheduling": "book appointments, manage calendar, send reminders, handle rescheduling",
    "sac": "handle complaints, process returns/refunds, ensure customer satisfaction",
    "onboarding": "welcome new customers, guide through setup, explain features, best practices",
}


@router.post("/agents/generate-preview")
async def generate_agent_preview(req: AgentGenerateRequest, user=Depends(get_current_user)):
    """Use AI to generate a complete agent configuration from questionnaire answers"""
    segment_ctx = SEGMENT_CONTEXT.get(req.segment, SEGMENT_CONTEXT["general"])
    objective_ctx = OBJECTIVE_MAP.get(req.objective, OBJECTIVE_MAP["support"])

    lang_map = {"pt": "Brazilian Portuguese", "en": "English", "es": "Spanish"}
    lang_name = lang_map.get(req.language, "Brazilian Portuguese")

    prompt = f"""You are an expert AI agent designer for a customer service automation platform.
Based on the following business information, generate a COMPLETE agent configuration.

BUSINESS INFORMATION:
- Segment: {req.segment} ({segment_ctx})
- Primary Objective: {req.objective} ({objective_ctx})
- Desired Tone: {req.tone}
- Business Name: {req.business_name}
- Business Description: {req.business_description}
- Products/Services: {req.products_services or 'Not specified'}
- Operating Hours: {req.hours or 'Not specified'}
- Differentials: {req.differentials or 'Not specified'}
- Target Audience: {req.target_audience or 'General public'}

RESPOND IN {lang_name}. Output ONLY valid JSON with this exact structure:
{{
  "agent_name": "A creative, human-like name appropriate for the business context",
  "description": "A concise 1-2 sentence description of what this agent does",
  "system_prompt": "A detailed, professional system prompt (300-500 words) that includes: agent identity, communication style, step-by-step conversation flow, specific knowledge about the business, escalation rules, and language handling. Make it specific to the business, not generic.",
  "personality": {{
    "tone_value": 0.0-1.0,
    "verbosity_value": 0.0-1.0,
    "emoji_value": 0.0-1.0,
    "proactivity": 0.0-1.0,
    "formality": 0.0-1.0
  }},
  "suggested_knowledge": [
    {{"type": "faq", "title": "...", "content": "..."}},
    {{"type": "product", "title": "...", "content": "..."}},
    {{"type": "hours", "title": "...", "content": "..."}}
  ],
  "escalation_keywords": ["keyword1", "keyword2", "keyword3"],
  "sample_conversation": [
    {{"role": "customer", "message": "..."}},
    {{"role": "agent", "message": "..."}},
    {{"role": "customer", "message": "..."}},
    {{"role": "agent", "message": "..."}}
  ]
}}"""

    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"agent-gen-{uuid.uuid4().hex[:8]}",
            system_message="You are a JSON generator. Output ONLY valid JSON, no markdown, no code blocks, no extra text."
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        start = time.time()
        response = await chat.send_message(UserMessage(text=prompt))
        elapsed = round((time.time() - start) * 1000)

        # Parse JSON from response
        import json
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        result = json.loads(cleaned)
        result["generation_time_ms"] = elapsed

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Agent generation JSON parse error: {e}\nResponse: {response[:500]}")
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Please try again.")
    except Exception as e:
        logger.error(f"Agent generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/deploy-generated")
async def deploy_generated_agent(data: dict, user=Depends(get_current_user)):
    """Deploy an AI-generated agent to the user's account"""
    tenant_result = supabase.table("tenants").select("*").eq("owner_id", user["id"]).execute()
    if not tenant_result.data:
        raise HTTPException(status_code=400, detail="Create a tenant first")
    tenant = tenant_result.data[0]

    agent_count = len(supabase.table("agents").select("id").eq("tenant_id", tenant["id"]).execute().data)
    if tenant["plan"] == "free" and agent_count >= 1:
        raise HTTPException(status_code=403, detail="Free plan allows only 1 agent. Upgrade to create more.")

    personality = data.get("personality", {})

    agent = {
        "tenant_id": tenant["id"],
        "name": data.get("agent_name", "Agent"),
        "type": data.get("objective", "support"),
        "description": data.get("description", ""),
        "system_prompt": data.get("system_prompt", ""),
        "status": "active",
        "language_mode": "auto_detect",
        "fixed_language": data.get("language", "pt"),
        "personality": {
            "tone": personality.get("tone_value", 0.6),
            "verbosity": personality.get("verbosity_value", 0.5),
            "emoji_usage": personality.get("emoji_value", 0.3),
        },
        "ai_config": {"model": "claude-sonnet", "temperature": 0.7, "max_tokens": 500},
        "stats": {"total_conversations": 0, "total_messages": 0, "resolution_rate": 0},
        "tone": data.get("tone", "friendly"),
        "emoji_level": personality.get("emoji_value", 0.3),
        "verbosity_level": personality.get("verbosity_value", 0.5),
        "escalation_rules": {
            "keywords": data.get("escalation_keywords", ["atendente", "humano", "gerente"]),
            "sentiment_threshold": 0.3,
        },
        "follow_up_config": {"enabled": False, "delay_hours": 24, "max_follow_ups": 3, "cool_down_days": 7},
        "knowledge_instructions": "",
        "is_deployed": True,
        "marketplace_template_id": None,
    }

    result = supabase.table("agents").insert(agent).execute()
    agent_data = result.data[0]

    # Add suggested knowledge items
    suggested_knowledge = data.get("suggested_knowledge", [])
    for item in suggested_knowledge:
        if item.get("title") and item.get("content"):
            supabase.table("agent_knowledge").insert({
                "agent_id": agent_data["id"],
                "type": item.get("type", "faq"),
                "title": item["title"],
                "content": item["content"],
            }).execute()

    # Update tenant usage
    current_usage = tenant.get("usage", {})
    current_usage["agents_created"] = current_usage.get("agents_created", 0) + 1
    supabase.table("tenants").update({"usage": current_usage}).eq("id", tenant["id"]).execute()

    return agent_data
