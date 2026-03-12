from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pathlib import Path
import base64
import os
import tempfile
import uuid
import time

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai import OpenAISpeechToText

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper, EMERGENT_KEY, logger
from core.constants import AGENT_TYPE_DESCRIPTIONS
from core.models import SandboxChatRequest
from core.utils import sandbox_sessions

router = APIRouter(prefix="/api", tags=["ai"])


# --- AI Sandbox ---
@router.post("/sandbox/chat")
async def sandbox_chat(req: SandboxChatRequest, user=Depends(get_current_user)):
    session_id = req.session_id or f"sandbox-{user['id']}-{uuid.uuid4().hex[:8]}"

    system = req.system_prompt or f"""You are {req.agent_name}, a professional {req.agent_type} assistant for a business.
You are friendly, helpful and concise. You respond in the same language the customer writes to you.
If the customer writes in Portuguese, respond in Portuguese. If in English, respond in English. If in Spanish, respond in Spanish.
Keep responses under 3 sentences unless more detail is needed."""

    if session_id not in sandbox_sessions:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=session_id,
            system_message=system
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")
        sandbox_sessions[session_id] = chat
    else:
        chat = sandbox_sessions[session_id]

    msg = UserMessage(text=req.content)
    start = time.time()
    response = await chat.send_message(msg)
    elapsed = round((time.time() - start) * 1000)

    detected_lang = "en"
    pt_words = {"olá", "oi", "obrigado", "não", "sim", "como", "está", "bem", "bom", "você"}
    es_words = {"hola", "gracias", "no", "sí", "cómo", "está", "bien", "bueno", "usted"}
    words = set(response.lower().split()[:20])
    if words & pt_words:
        detected_lang = "pt"
    elif words & es_words:
        detected_lang = "es"

    return {
        "response": response,
        "session_id": session_id,
        "debug": {
            "response_time_ms": elapsed,
            "model": "claude-sonnet-4-5",
            "language_detected": detected_lang,
            "tokens_estimate": len(response.split()),
        }
    }


@router.delete("/sandbox/{session_id}")
async def clear_sandbox(session_id: str, user=Depends(get_current_user)):
    sandbox_sessions.pop(session_id, None)
    return {"status": "ok"}


# --- Image Analysis (Claude Vision) ---
@router.post("/ai/analyze-image")
async def analyze_image(
    image: UploadFile = File(None),
    image_base64: str = Form(None),
    prompt: str = Form("Describe this image in detail. If it contains text, transcribe it. If it's a product, describe features and condition."),
    language: str = Form("auto"),
    user=Depends(get_current_user)
):
    try:
        if image:
            content = await image.read()
            b64 = base64.b64encode(content).decode('utf-8')
        elif image_base64:
            b64 = image_base64
        else:
            raise HTTPException(status_code=400, detail="Provide image file or image_base64")

        img_content = ImageContent(image_base64=b64)

        lang_instruction = ""
        if language and language != "auto":
            lang_map = {"pt": "Portuguese", "es": "Spanish", "en": "English"}
            lang_instruction = f" Respond in {lang_map.get(language, language)}."

        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"vision-{uuid.uuid4().hex[:8]}",
            system_message=f"You are an image analysis assistant.{lang_instruction}"
        ).with_model("anthropic", "claude-sonnet-4-5-20250929")

        msg = UserMessage(text=prompt, file_contents=[img_content])
        start = time.time()
        response = await chat.send_message(msg)
        elapsed = round((time.time() - start) * 1000)

        return {
            "analysis": response,
            "debug": {"response_time_ms": elapsed, "model": "claude-sonnet-4-5-vision"},
        }
    except Exception as e:
        logger.error(f"Vision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Audio Transcription (Whisper) ---
@router.post("/ai/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(None),
    audio_base64: str = Form(None),
    language: str = Form(None),
    user=Depends(get_current_user)
):
    try:
        stt = OpenAISpeechToText(api_key=EMERGENT_KEY)

        if audio:
            content = await audio.read()
            suffix = Path(audio.filename).suffix if audio.filename else '.mp3'
        elif audio_base64:
            content = base64.b64decode(audio_base64)
            suffix = '.mp3'
        else:
            raise HTTPException(status_code=400, detail="Provide audio file or audio_base64")

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            start = time.time()
            with open(tmp_path, "rb") as f:
                result = await stt.transcribe(
                    file=f,
                    model="whisper-1",
                    response_format="verbose_json",
                    language=language,
                )
            elapsed = round((time.time() - start) * 1000)

            return {
                "text": result.text,
                "language": getattr(result, 'language', language or 'unknown'),
                "duration": getattr(result, 'duration', None),
                "debug": {"response_time_ms": elapsed, "model": "whisper-1"},
            }
        finally:
            os.unlink(tmp_path)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Multi-Agent Orchestration ---
@router.post("/conversations/{convo_id}/route-agent")
async def route_to_best_agent(convo_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msgs = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).limit(10).execute()
    if not msgs.data:
        raise HTTPException(status_code=400, detail="No messages in conversation")

    agents = supabase.table("agents").select("*").eq("tenant_id", tenant["id"]).eq("is_deployed", True).execute()
    if not agents.data:
        raise HTTPException(status_code=400, detail="No deployed agents")

    if len(agents.data) == 1:
        return {"agent_id": agents.data[0]["id"], "agent_name": agents.data[0]["name"], "reason": "Only one agent deployed"}

    context = "\n".join([f"{m['sender']}: {m['content']}" for m in msgs.data[-5:]])

    agent_list = "\n".join([f"- {a['name']} ({a['type']}): {AGENT_TYPE_DESCRIPTIONS.get(a['type'], a['type'])}" for a in agents.data])

    chat = LlmChat(
        api_key=EMERGENT_KEY,
        session_id=f"router-{uuid.uuid4().hex[:8]}",
        system_message="You are a conversation router. Given a conversation context and available agents, respond with ONLY the agent name that best handles this conversation. No explanation."
    ).with_model("anthropic", "claude-sonnet-4-5-20250929")

    prompt = f"Available agents:\n{agent_list}\n\nConversation:\n{context}\n\nWhich agent name should handle this?"
    best_name = (await chat.send_message(UserMessage(text=prompt))).strip()

    selected = None
    for a in agents.data:
        if a["name"].lower() in best_name.lower():
            selected = a
            break
    if not selected:
        selected = agents.data[0]

    supabase.table("conversations").update({"agent_id": selected["id"]}).eq("id", convo_id).execute()

    return {"agent_id": selected["id"], "agent_name": selected["name"], "reason": "Routed based on conversation context"}
