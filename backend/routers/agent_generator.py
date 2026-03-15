from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import time
import uuid
import json
import asyncio

from emergentintegrations.llm.chat import LlmChat, UserMessage

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger

router = APIRouter(prefix="/api", tags=["agent-generator"])

# In-memory store for generation tasks
_generation_tasks = {}


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
    mindset: Optional[str] = ""
    response_length: Optional[str] = "medium"
    topic_scope: Optional[str] = ""
    forbidden_topics: Optional[str] = ""
    no_response_action: Optional[str] = "follow_up_24h"
    context_recovery: Optional[bool] = True
    integrations: Optional[List[str]] = []


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

RESPONSE_LENGTH_MAP = {
    "short": "Keep responses concise: 1-3 sentences max. Be direct and efficient.",
    "medium": "Use moderate-length responses: 2-5 sentences. Balance detail with brevity.",
    "detailed": "Provide comprehensive responses: 4-8 sentences. Include context and examples.",
}

NO_RESPONSE_MAP = {
    "follow_up_24h": "If the customer doesn't respond within 24 hours, send a gentle follow-up message asking if they still need help.",
    "follow_up_1h": "If the customer doesn't respond within 1 hour, send a quick check-in.",
    "wait": "Wait patiently for the customer to respond. Do not send follow-ups.",
    "close_48h": "If no response after 48 hours, send a closing message and archive the conversation.",
}

MINDSET_TEMPLATES = {
    "closer": {"name": "Closer", "desc": "Focused on closing deals", "traits": "assertive, solution-oriented, urgency-creating, objection-handling"},
    "consultant": {"name": "Consultant", "desc": "Asks deep questions first", "traits": "analytical, patient, inquisitive, thorough"},
    "concierge": {"name": "Concierge", "desc": "Premium service", "traits": "proactive, attentive, luxurious, detail-oriented"},
    "educator": {"name": "Educator", "desc": "Teaches and explains", "traits": "informative, patient, clear, encouraging"},
    "friend": {"name": "Friend", "desc": "Casual and warm", "traits": "relaxed, empathetic, approachable, genuine"},
    "resolver": {"name": "Resolver", "desc": "Problem-first approach", "traits": "decisive, pragmatic, focused, no-nonsense"},
    "nurturer": {"name": "Nurturer", "desc": "Long-term relationships", "traits": "caring, follow-up focused, relationship-builder, loyal"},
    "guardian": {"name": "Guardian", "desc": "Protective and careful", "traits": "cautious, transparent, ethical, advisory"},
}


@router.get("/agents/mindsets")
async def get_mindsets():
    return list(MINDSET_TEMPLATES.values())


def _build_prompt(req: AgentGenerateRequest) -> str:
    segment_ctx = SEGMENT_CONTEXT.get(req.segment, SEGMENT_CONTEXT["general"])
    objective_ctx = OBJECTIVE_MAP.get(req.objective, OBJECTIVE_MAP["support"])
    length_ctx = RESPONSE_LENGTH_MAP.get(req.response_length, RESPONSE_LENGTH_MAP["medium"])
    no_resp_ctx = NO_RESPONSE_MAP.get(req.no_response_action, NO_RESPONSE_MAP["follow_up_24h"])
    lang_map = {"pt": "Brazilian Portuguese", "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "auto": "the customer's language (auto-detect)"}
    lang_name = lang_map.get(req.language, "Brazilian Portuguese")

    extras = ""
    if req.mindset and req.mindset in MINDSET_TEMPLATES:
        m = MINDSET_TEMPLATES[req.mindset]
        extras += f"\nMINDSET: {m['name']} - {m['desc']}. Key traits: {m['traits']}."
    if req.topic_scope:
        extras += f"\nTOPIC SCOPE (agent ONLY talks about these subjects): {req.topic_scope}"
    if req.forbidden_topics:
        extras += f"\nFORBIDDEN TOPICS (agent must NEVER discuss): {req.forbidden_topics}. If asked about forbidden topics, politely redirect."
    if req.integrations:
        extras += f"\nINTEGRATIONS: {', '.join(req.integrations)}. Reference capabilities naturally."
    if req.context_recovery:
        extras += "\nCONTEXT RECOVERY: Remember previous conversations with the same customer."

    return f"""You are an expert AI agent designer. Generate a COMPLETE agent configuration.

BUSINESS:
- Segment: {req.segment} ({segment_ctx})
- Objective: {req.objective} ({objective_ctx})
- Tone: {req.tone}
- Name: {req.business_name}
- Description: {req.business_description}
- Products: {req.products_services or 'N/A'}
- Hours: {req.hours or 'N/A'}
- Differentials: {req.differentials or 'N/A'}
- Audience: {req.target_audience or 'General'}
{extras}
RESPONSE STYLE: {length_ctx}
NO-RESPONSE: {no_resp_ctx}

RESPOND IN {lang_name}. Output ONLY valid JSON:
{{
  "agent_name": "Creative human-like name",
  "description": "1-2 sentence description",
  "system_prompt": "Detailed 400-700 word system prompt with: identity, style, conversation flow, business knowledge, escalation rules, topic boundaries, no-response behavior, integration usage.",
  "personality": {{"tone_value": 0.0-1.0, "verbosity_value": 0.0-1.0, "emoji_value": 0.0-1.0, "proactivity": 0.0-1.0, "formality": 0.0-1.0}},
  "suggested_knowledge": [{{"type": "faq", "title": "...", "content": "..."}}, {{"type": "product", "title": "...", "content": "..."}}, {{"type": "policy", "title": "...", "content": "..."}}],
  "escalation_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "sample_conversation": [{{"role": "customer", "message": "..."}}, {{"role": "agent", "message": "..."}}, {{"role": "customer", "message": "..."}}, {{"role": "agent", "message": "..."}}, {{"role": "customer", "message": "..."}}, {{"role": "agent", "message": "..."}}],
  "topic_boundaries": {{"allowed": ["topics agent can discuss"], "forbidden": ["topics to avoid"]}}
}}"""


async def _run_generation(task_id: str, prompt: str):
    """Background task that generates the agent and stores result."""
    models = [
        ("gemini", "gemini-2.0-flash"),
        ("anthropic", "claude-sonnet-4-5-20250929"),
    ]

    for provider, model in models:
        try:
            logger.info(f"Agent gen [{task_id}]: trying {provider}/{model}")
            chat = LlmChat(
                api_key=EMERGENT_KEY,
                session_id=f"agent-gen-{task_id}",
                system_message="You are a JSON generator. Output ONLY valid JSON, no markdown, no code blocks."
            ).with_model(provider, model)

            start = time.time()
            response = await chat.send_message(UserMessage(text=prompt))
            elapsed = round((time.time() - start) * 1000)

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
            result["model_used"] = f"{provider}/{model}"

            _generation_tasks[task_id] = {"status": "completed", "result": result}
            logger.info(f"Agent gen [{task_id}]: OK with {provider}/{model} in {elapsed}ms")
            return

        except json.JSONDecodeError as e:
            logger.error(f"Agent gen [{task_id}] JSON error ({model}): {e}")
            continue
        except Exception as e:
            logger.error(f"Agent gen [{task_id}] error ({model}): {e}")
            continue

    _generation_tasks[task_id] = {"status": "failed", "error": "All AI models failed. Please try again."}


@router.post("/agents/generate-preview")
async def generate_agent_preview(req: AgentGenerateRequest, user=Depends(get_current_user)):
    """Start async agent generation, return task_id for polling."""
    task_id = uuid.uuid4().hex[:12]
    prompt = _build_prompt(req)

    _generation_tasks[task_id] = {"status": "generating"}

    # Fire and forget background task
    asyncio.create_task(_run_generation(task_id, prompt))

    return {"task_id": task_id, "status": "generating"}


@router.get("/agents/generate-status/{task_id}")
async def get_generation_status(task_id: str, user=Depends(get_current_user)):
    """Poll for generation result."""
    task = _generation_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task["status"] == "completed":
        # Clean up after delivery
        result = task["result"]
        del _generation_tasks[task_id]
        return {"status": "completed", "result": result}

    if task["status"] == "failed":
        error = task.get("error", "Unknown error")
        del _generation_tasks[task_id]
        return {"status": "failed", "error": error}

    return {"status": "generating"}


@router.post("/agents/deploy-generated")
async def deploy_generated_agent(data: dict, user=Depends(get_current_user)):
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
        "language_mode": data.get("language_mode", "auto_detect"),
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
        "follow_up_config": {
            "enabled": data.get("no_response_action", "follow_up_24h") != "wait",
            "delay_hours": 1 if data.get("no_response_action") == "follow_up_1h" else 24,
            "max_follow_ups": 3,
            "cool_down_days": 7,
        },
        "knowledge_instructions": "",
        "is_deployed": True,
        "marketplace_template_id": None,
        "agent_config": {
            "response_length": data.get("response_length", "medium"),
            "topic_scope": data.get("topic_boundaries", {}).get("allowed", []),
            "forbidden_topics": data.get("topic_boundaries", {}).get("forbidden", []),
            "context_recovery": data.get("context_recovery", True),
            "mindset": data.get("mindset", ""),
            "integrations": data.get("integrations", []),
            "no_response_action": data.get("no_response_action", "follow_up_24h"),
        },
    }

    result = supabase.table("agents").insert(agent).execute()
    agent_data = result.data[0]

    suggested_knowledge = data.get("suggested_knowledge", [])
    for item in suggested_knowledge:
        if item.get("title") and item.get("content"):
            supabase.table("agent_knowledge").insert({
                "agent_id": agent_data["id"],
                "type": item.get("type", "faq"),
                "title": item["title"],
                "content": item["content"],
            }).execute()

    current_usage = tenant.get("usage", {})
    current_usage["agents_created"] = current_usage.get("agents_created", 0) + 1
    supabase.table("tenants").update({"usage": current_usage}).eq("id", tenant["id"]).execute()

    return agent_data
