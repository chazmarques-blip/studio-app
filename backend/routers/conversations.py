from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional
from datetime import datetime, timezone
from pathlib import Path
import base64
import os
import tempfile

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper, logger
from core.llm import DirectChat, multi_turn_completion, speech_to_text as stt_direct, DEFAULT_MODEL
from core.models import ConversationCreate, MessageCreate
from core.utils import build_agent_system_prompt

router = APIRouter(prefix="/api", tags=["conversations"])


@router.get("/conversations")
async def list_conversations(channel_type: Optional[str] = None, status: Optional[str] = None, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    query = supabase.table("conversations").select("*").eq("tenant_id", tenant["id"]).order("last_message_at", desc=True)
    if channel_type and channel_type != "all":
        query = query.eq("channel_type", channel_type)
    if status:
        query = query.eq("status", status)
    result = query.limit(50).execute()
    return {"conversations": result.data}


@router.post("/conversations")
async def create_conversation(data: ConversationCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    convo = {
        "tenant_id": tenant["id"],
        "contact_name": data.contact_name,
        "contact_phone": data.contact_phone,
        "contact_email": data.contact_email,
        "channel_type": data.channel_type,
        "agent_id": data.agent_id,
        "status": "active",
        "is_handoff": False,
        "language": "",
        "metadata": {},
        "last_message_at": datetime.now(timezone.utc).isoformat(),
    }
    result = supabase.table("conversations").insert(convo).execute()
    return result.data[0]


@router.get("/conversations/{convo_id}")
async def get_conversation(convo_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    result = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result.data[0]


@router.get("/conversations/{convo_id}/messages")
async def get_messages(convo_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    convo = supabase.table("conversations").select("id").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    msgs = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).execute()
    return {"messages": msgs.data}


@router.post("/conversations/{convo_id}/messages")
async def send_message(convo_id: str, data: MessageCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg = {
        "conversation_id": convo_id,
        "sender": "operator",
        "content": data.content,
        "message_type": data.message_type,
        "metadata": data.metadata or {},
    }
    result = supabase.table("messages").insert(msg).execute()
    supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

    # Update tenant message usage
    usage = tenant.get("usage", {})
    usage["messages_sent_this_period"] = usage.get("messages_sent_this_period", 0) + 1
    supabase.table("tenants").update({"usage": usage}).eq("id", tenant["id"]).execute()

    # Send outbound message via WhatsApp if conversation is WhatsApp channel
    convo_data = convo.data[0]
    if convo_data.get("channel_type") == "whatsapp" and convo_data.get("contact_phone"):
        try:
            import httpx
            wa_channel = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").eq("status", "connected").execute()
            if wa_channel.data:
                wa_config = wa_channel.data[0].get("config", {})
                api_url = wa_config.get("api_url")
                api_key = wa_config.get("api_key")
                instance = wa_config.get("instance_name")
                if api_url and api_key and instance:
                    number = convo_data["contact_phone"].replace("+", "").replace(" ", "")
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        await client.post(
                            f"{api_url.rstrip('/')}/message/sendText/{instance}",
                            headers={"apikey": api_key, "Content-Type": "application/json"},
                            json={"number": number, "text": data.content},
                        )
        except Exception as e:
            logger.warning(f"WhatsApp outbound send failed: {e}")

    return result.data[0]


# --- Conversation with image/audio support ---
@router.post("/conversations/{convo_id}/messages/multimedia")
async def send_multimedia_message(
    convo_id: str,
    content: str = Form(""),
    message_type: str = Form("text"),
    image: UploadFile = File(None),
    audio: UploadFile = File(None),
    user=Depends(get_current_user)
):
    tenant = await get_tenant_helper(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    final_content = content
    metadata = {}

    if audio:
        audio_content = await audio.read()
        suffix = Path(audio.filename).suffix if audio.filename else '.mp3'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_content)
            tmp_path = tmp.name
        try:
            result = await stt_direct(file_path=tmp_path)
            final_content = result.text
            message_type = "audio"
            metadata["transcription"] = result.text
            metadata["original_type"] = "audio"
        finally:
            os.unlink(tmp_path)

    if image:
        img_content = await image.read()
        b64 = base64.b64encode(img_content).decode('utf-8')
        metadata["image_base64_preview"] = b64[:100]
        metadata["has_image"] = True
        message_type = "image"
        if not content:
            final_content = "[Image sent]"

    msg = {
        "conversation_id": convo_id,
        "sender": "customer",
        "content": final_content,
        "message_type": message_type,
        "metadata": metadata,
    }
    result = supabase.table("messages").insert(msg).execute()
    supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

    return result.data[0]


# --- AI Agent Auto-Reply ---
@router.post("/conversations/{convo_id}/ai-reply")
async def ai_agent_reply(convo_id: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    convo = supabase.table("conversations").select("*").eq("id", convo_id).eq("tenant_id", tenant["id"]).execute()
    if not convo.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    convo = convo.data[0]

    agent = None
    if convo.get("agent_id"):
        agent_result = supabase.table("agents").select("*").eq("id", convo["agent_id"]).execute()
        if agent_result.data:
            agent = agent_result.data[0]

    agent_name = agent["name"] if agent else "Assistant"
    agent_type = agent["type"] if agent else "support"
    system_prompt = agent.get("system_prompt", "") if agent else ""

    if not system_prompt:
        system_prompt = f"""You are {agent_name}, a professional {agent_type} assistant.
You are friendly, helpful and concise. Respond in the same language the customer writes.
Keep responses under 3 sentences unless more detail is needed."""

    msgs = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).limit(20).execute()

    # Build message history and make ONE efficient API call
    history = []
    for m in msgs.data[:-1]:
        role = "user" if m["sender"] == "customer" else "assistant"
        history.append({"role": role, "content": m["content"]})

    last_customer_msg = None
    for m in reversed(msgs.data):
        if m["sender"] == "customer":
            last_customer_msg = m["content"]
            break

    if not last_customer_msg:
        raise HTTPException(status_code=400, detail="No customer message to reply to")

    history.append({"role": "user", "content": last_customer_msg})

    response = await multi_turn_completion(
        system_prompt=system_prompt,
        messages_history=history,
    )

    ai_msg = {
        "conversation_id": convo_id,
        "sender": "agent",
        "content": response,
        "message_type": "text",
        "metadata": {"model": "claude-sonnet-4-5", "agent_name": agent_name},
    }
    result = supabase.table("messages").insert(ai_msg).execute()
    supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

    usage = tenant.get("usage", {})
    usage["messages_sent_this_period"] = usage.get("messages_sent_this_period", 0) + 1
    supabase.table("tenants").update({"usage": usage}).eq("id", tenant["id"]).execute()

    return {
        "message": result.data[0],
        "response": response,
    }
