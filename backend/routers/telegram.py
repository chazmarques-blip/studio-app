from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
import httpx
import os

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper, logger
from core.llm import DirectChat, DEFAULT_MODEL
from core.models import TelegramSetupRequest
from core.utils import build_agent_system_prompt

router = APIRouter(prefix="/api", tags=["telegram"])

# In-memory map of active telegram sessions: chat_id -> DirectChat
telegram_sessions: dict = {}


async def tg_request(bot_token: str, method: str, data: dict = None):
    """Make a request to Telegram Bot API"""
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        if data:
            resp = await client.post(url, json=data)
        else:
            resp = await client.get(url)
        return resp.json()


@router.post("/telegram/setup")
async def setup_telegram_bot(req: TelegramSetupRequest, user=Depends(get_current_user)):
    """Set up a Telegram bot for an agent"""
    tenant = await get_tenant_helper(user)

    # Verify bot token is valid
    try:
        me = await tg_request(req.bot_token, "getMe")
        if not me.get("ok"):
            raise HTTPException(status_code=400, detail="Invalid bot token")
        bot_username = me["result"]["username"]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot reach Telegram API: {e}")

    # Verify agent belongs to tenant
    agent = supabase.table("agents").select("id, name").eq("id", req.agent_id).eq("tenant_id", tenant["id"]).execute()
    if not agent.data:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Set webhook
    webhook_base = os.environ.get("REACT_APP_BACKEND_URL", os.environ.get("WEBHOOK_BASE_URL", ""))
    if not webhook_base:
        # Try to construct from request
        webhook_base = str(os.environ.get("WEBHOOK_BASE_URL", ""))

    if webhook_base:
        webhook_url = f"{webhook_base}/api/webhook/telegram/{req.agent_id}"
        try:
            result = await tg_request(req.bot_token, "setWebhook", {"url": webhook_url})
            if not result.get("ok"):
                logger.warning(f"Webhook set failed: {result}")
        except Exception as e:
            logger.warning(f"Webhook set error: {e}")

    # Store bot config in agent's ai_config.channels
    current_agent = supabase.table("agents").select("ai_config").eq("id", req.agent_id).execute()
    ai_config = current_agent.data[0].get("ai_config", {}) if current_agent.data else {}
    ai_config["channels"] = ai_config.get("channels", {})
    ai_config["channels"]["telegram"] = {"enabled": True, "bot_token": req.bot_token, "bot_username": bot_username, "connected": True}
    supabase.table("agents").update({
        "ai_config": ai_config,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", req.agent_id).execute()

    # Also store in channels table
    existing = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "telegram").execute()
    channel_data = {
        "tenant_id": tenant["id"],
        "type": "telegram",
        "status": "connected",
        "config": {"bot_token": req.bot_token, "bot_username": bot_username, "agent_id": req.agent_id},
    }
    if existing.data:
        supabase.table("channels").update({**channel_data, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", existing.data[0]["id"]).execute()
    else:
        supabase.table("channels").insert(channel_data).execute()

    return {"status": "ok", "bot_username": bot_username, "message": f"Bot @{bot_username} connected to {agent.data[0]['name']}!"}


@router.post("/webhook/telegram/{agent_id}")
async def telegram_webhook(agent_id: str, request: Request):
    """Handle incoming Telegram messages"""
    try:
        payload = await request.json()
        message = payload.get("message", {})
        if not message:
            return {"ok": True}

        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        from_user = message.get("from", {})
        user_name = from_user.get("first_name", "") + " " + from_user.get("last_name", "")
        user_name = user_name.strip() or "User"

        if not chat_id or not text:
            return {"ok": True}

        # Skip /start command
        if text == "/start":
            agent = supabase.table("agents").select("name, ai_config").eq("id", agent_id).execute()
            bot_token = agent.data[0].get("ai_config", {}).get("channels", {}).get("telegram", {}).get("bot_token") if agent.data else None
            if bot_token:
                welcome = f"Ola {user_name}! Sou {agent.data[0]['name']}, seu assistente de IA. Como posso te ajudar?"
                await tg_request(bot_token, "sendMessage", {"chat_id": chat_id, "text": welcome})
            return {"ok": True}

        # Get agent
        agent_result = supabase.table("agents").select("*").eq("id", agent_id).execute()
        if not agent_result.data:
            return {"ok": True, "error": "Agent not found"}
        agent = agent_result.data[0]

        bot_token = agent.get("ai_config", {}).get("channels", {}).get("telegram", {}).get("bot_token")
        if not bot_token:
            return {"ok": True, "error": "No bot token"}

        # Send typing indicator
        await tg_request(bot_token, "sendChatAction", {"chat_id": chat_id, "action": "typing"})

        # Build system prompt
        kb = supabase.table("agent_knowledge").select("*").eq("agent_id", agent_id).execute()
        system_prompt = build_agent_system_prompt(agent, kb.data)

        # Get or create conversation session
        session_key = f"tg-{agent_id}-{chat_id}"
        if session_key not in telegram_sessions:
            chat = DirectChat(system_message=system_prompt)
            telegram_sessions[session_key] = chat
        else:
            chat = telegram_sessions[session_key]

        # Get AI response
        response = await chat.send_message(text)

        # Send response back to Telegram
        await tg_request(bot_token, "sendMessage", {
            "chat_id": chat_id,
            "text": response,
            "parse_mode": "Markdown",
        })

        # Store in conversations & messages for tracking
        tenant_id = agent.get("tenant_id")
        if tenant_id:
            # Find or create conversation
            existing = supabase.table("conversations").select("id").eq("tenant_id", tenant_id).eq("contact_phone", str(chat_id)).eq("channel_type", "telegram").eq("status", "active").execute()
            if existing.data:
                convo_id = existing.data[0]["id"]
            else:
                convo = supabase.table("conversations").insert({
                    "tenant_id": tenant_id,
                    "agent_id": agent_id,
                    "contact_name": user_name,
                    "contact_phone": str(chat_id),
                    "channel_type": "telegram",
                    "status": "active",
                    "last_message_at": datetime.now(timezone.utc).isoformat(),
                }).execute()
                convo_id = convo.data[0]["id"]

            # Store messages
            supabase.table("messages").insert({"conversation_id": convo_id, "sender": "customer", "content": text, "message_type": "text", "metadata": {"from": user_name, "chat_id": chat_id}}).execute()
            supabase.table("messages").insert({"conversation_id": convo_id, "sender": "agent", "content": response, "message_type": "text", "metadata": {"model": "claude-sonnet-4-5", "agent_name": agent["name"]}}).execute()
            supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

            # Update agent stats
            stats = agent.get("stats", {})
            stats["total_messages"] = stats.get("total_messages", 0) + 1
            stats["total_conversations"] = stats.get("total_conversations", 0) + (0 if existing.data else 1)
            supabase.table("agents").update({"stats": stats}).eq("id", agent_id).execute()

        return {"ok": True}

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"ok": True, "error": str(e)}


@router.get("/webhook/telegram/{agent_id}")
async def telegram_webhook_verify(agent_id: str):
    return {"status": "ok", "service": "studiox-telegram-webhook", "agent_id": agent_id}
