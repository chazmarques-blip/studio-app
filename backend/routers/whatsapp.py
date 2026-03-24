from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import os

from core.deps import supabase, get_current_user, get_tenant as get_tenant_helper, logger
from core.llm import DirectChat, DEFAULT_MODEL
from core.models import WhatsAppInstanceCreate, WhatsAppSendMessage
from core.utils import build_agent_system_prompt, check_escalation, evo_request

router = APIRouter(prefix="/api", tags=["whatsapp"])


# --- Webhook for incoming messages ---
@router.post("/webhook/whatsapp")
async def whatsapp_webhook(payload: dict):
    logger.info("WhatsApp webhook received")
    try:
        event = payload.get("event", "")
        instance = payload.get("instance", "")
        data = payload.get("data", {})

        if event == "messages.upsert":
            message_data = data.get("message", {})
            from_number = data.get("key", {}).get("remoteJid", "").replace("@s.whatsapp.net", "")
            content = message_data.get("conversation", "") or message_data.get("extendedTextMessage", {}).get("text", "")
            is_from_me = data.get("key", {}).get("fromMe", False)

            if is_from_me or not content:
                return {"status": "ignored"}

            channels = supabase.table("channels").select("*").eq("type", "whatsapp").eq("status", "connected").execute()
            channel = None
            for ch in channels.data:
                if ch.get("config", {}).get("instance_name") == instance:
                    channel = ch
                    break
            if not channel:
                return {"status": "no_channel"}

            tenant_id = channel["tenant_id"]

            existing = supabase.table("conversations").select("*").eq("tenant_id", tenant_id).eq("contact_phone", from_number).eq("status", "active").execute()
            if existing.data:
                convo = existing.data[0]
                convo_id = convo["id"]
            else:
                deployed = supabase.table("agents").select("id").eq("tenant_id", tenant_id).eq("is_deployed", True).eq("status", "active").limit(1).execute()
                agent_id = deployed.data[0]["id"] if deployed.data else None

                new_convo = {
                    "tenant_id": tenant_id,
                    "channel_id": channel["id"],
                    "agent_id": agent_id,
                    "contact_name": from_number,
                    "contact_phone": from_number,
                    "channel_type": "whatsapp",
                    "status": "active",
                    "last_message_at": datetime.now(timezone.utc).isoformat(),
                }
                convo_result = supabase.table("conversations").insert(new_convo).execute()
                convo = convo_result.data[0]
                convo_id = convo["id"]

            msg = {
                "conversation_id": convo_id,
                "sender": "customer",
                "content": content,
                "message_type": "text",
                "metadata": {"from": from_number},
            }
            supabase.table("messages").insert(msg).execute()
            supabase.table("conversations").update({"last_message_at": datetime.now(timezone.utc).isoformat()}).eq("id", convo_id).execute()

            if convo.get("agent_id") and not convo.get("is_handoff"):
                agent_result = supabase.table("agents").select("*").eq("id", convo["agent_id"]).execute()
                if agent_result.data:
                    agent = agent_result.data[0]

                    if check_escalation(content, agent):
                        supabase.table("conversations").update({"is_handoff": True}).eq("id", convo_id).execute()
                        escalation_msg = {
                            "conversation_id": convo_id,
                            "sender": "agent",
                            "content": "Entendo, vou transferir você para um atendente humano. Um momento, por favor.",
                            "message_type": "text",
                            "metadata": {"escalated": True, "agent_name": agent["name"]},
                        }
                        supabase.table("messages").insert(escalation_msg).execute()
                        return {"status": "escalated", "conversation_id": convo_id}

                    kb = supabase.table("agent_knowledge").select("*").eq("agent_id", agent["id"]).execute()
                    system_prompt = build_agent_system_prompt(agent, kb.data)

                    recent = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at", desc=False).limit(20).execute()

                    # Build message history and make ONE efficient API call
                    from core.llm import multi_turn_completion
                    history = []
                    for m in recent.data[:-1]:
                        role = "user" if m["sender"] == "customer" else "assistant"
                        history.append({"role": role, "content": m["content"]})
                    history.append({"role": "user", "content": content})

                    ai_response = await multi_turn_completion(
                        system_prompt=system_prompt,
                        messages_history=history,
                    )

                    ai_msg = {
                        "conversation_id": convo_id,
                        "sender": "agent",
                        "content": ai_response,
                        "message_type": "text",
                        "metadata": {"model": "claude-sonnet-4-5", "agent_name": agent["name"], "auto_reply": True},
                    }
                    supabase.table("messages").insert(ai_msg).execute()

                    try:
                        wa_config = channel.get("config", {})
                        api_url = wa_config.get("api_url")
                        api_key = wa_config.get("api_key")
                        instance_name = wa_config.get("instance_name")
                        if api_url and api_key and instance_name:
                            import httpx
                            async with httpx.AsyncClient(timeout=15.0) as http_client:
                                await http_client.post(
                                    f"{api_url.rstrip('/')}/message/sendText/{instance_name}",
                                    headers={"apikey": api_key, "Content-Type": "application/json"},
                                    json={"number": from_number, "text": ai_response},
                                )
                    except Exception as send_err:
                        logger.warning(f"Failed to send WhatsApp reply: {send_err}")

                    stats = agent.get("stats", {})
                    stats["total_messages"] = stats.get("total_messages", 0) + 1
                    supabase.table("agents").update({"stats": stats}).eq("id", agent["id"]).execute()

                    return {"status": "auto_replied", "conversation_id": convo_id, "response": ai_response}

            return {"status": "ok", "conversation_id": convo_id}

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

    return {"status": "ok"}


@router.get("/webhook/whatsapp")
async def whatsapp_webhook_verify():
    return {"status": "ok", "service": "agentzz-whatsapp-webhook"}


# --- Evolution API Endpoints ---
@router.post("/whatsapp/create-instance")
async def whatsapp_create_instance(data: WhatsAppInstanceCreate, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    try:
        resp = await evo_request("POST", data.api_url, data.api_key, "/instance/create", {
            "instanceName": data.instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
        })

        if resp.status_code >= 400:
            error_detail = resp.text
            try:
                error_detail = resp.json().get("message", resp.text)
            except Exception:
                pass
            raise HTTPException(status_code=resp.status_code, detail=f"Evolution API: {error_detail}")

        evo_data = resp.json()

        config = {
            "api_url": data.api_url,
            "api_key": data.api_key,
            "instance_name": data.instance_name,
        }

        existing = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").execute()
        if existing.data:
            channel_id = existing.data[0]["id"]
            supabase.table("channels").update({
                "config": config,
                "status": "waiting_qr",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", channel_id).execute()
        else:
            result = supabase.table("channels").insert({
                "tenant_id": tenant["id"],
                "type": "whatsapp",
                "status": "waiting_qr",
                "config": config,
            }).execute()
            channel_id = result.data[0]["id"]

        webhook_base = os.environ.get("WEBHOOK_BASE_URL", "")
        if webhook_base:
            await evo_request("POST", data.api_url, data.api_key, f"/webhook/set/{data.instance_name}", {
                "webhook": {
                    "enabled": True,
                    "url": f"{webhook_base}/api/webhook/whatsapp",
                    "webhookByEvents": False,
                    "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
                },
            })

        qr_code = None
        if isinstance(evo_data, dict):
            qr_code = evo_data.get("qrcode", {}).get("base64", None) if isinstance(evo_data.get("qrcode"), dict) else evo_data.get("qrcode")

        return {
            "status": "ok",
            "channel_id": channel_id,
            "instance_name": data.instance_name,
            "qr_code": qr_code,
            "evolution_response": evo_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp create instance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whatsapp/qr/{instance_name}")
async def whatsapp_get_qr(instance_name: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    channel = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").execute()
    if not channel.data:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    config = channel.data[0].get("config", {})
    api_url = config.get("api_url")
    api_key = config.get("api_key")

    if not api_url or not api_key:
        raise HTTPException(status_code=400, detail="Channel not configured")

    try:
        resp = await evo_request("GET", api_url, api_key, f"/instance/connect/{instance_name}")
        if resp.status_code >= 400:
            return {"qr_code": None, "status": "error", "detail": resp.text}
        data = resp.json()
        qr_code = None
        if isinstance(data, dict):
            qr_code = data.get("base64", None) or data.get("qrcode", None)
            if isinstance(qr_code, dict):
                qr_code = qr_code.get("base64", None)
        return {"qr_code": qr_code, "raw": data}
    except Exception as e:
        logger.error(f"QR fetch error: {e}")
        return {"qr_code": None, "status": "error", "detail": str(e)}


@router.get("/whatsapp/status/{instance_name}")
async def whatsapp_get_status(instance_name: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    channel = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").execute()
    if not channel.data:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    config = channel.data[0].get("config", {})
    api_url = config.get("api_url")
    api_key = config.get("api_key")

    if not api_url or not api_key:
        return {"connected": False, "state": "unconfigured"}

    try:
        resp = await evo_request("GET", api_url, api_key, f"/instance/connectionState/{instance_name}")
        if resp.status_code >= 400:
            return {"connected": False, "state": "error", "detail": resp.text}
        data = resp.json()
        state = data.get("state", data.get("instance", {}).get("state", "unknown"))
        is_connected = state in ("open", "connected")

        new_status = "connected" if is_connected else "waiting_qr"
        supabase.table("channels").update({
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", channel.data[0]["id"]).execute()

        return {"connected": is_connected, "state": state, "raw": data}
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {"connected": False, "state": "error", "detail": str(e)}


@router.post("/whatsapp/send")
async def whatsapp_send_message(data: WhatsAppSendMessage, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    channel = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").execute()
    if not channel.data:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    config = channel.data[0].get("config", {})
    api_url = config.get("api_url")
    api_key = config.get("api_key")
    instance = data.instance_name or config.get("instance_name")

    if not api_url or not api_key or not instance:
        raise HTTPException(status_code=400, detail="WhatsApp not configured")

    try:
        number = data.phone_number.replace("+", "").replace(" ", "").replace("-", "")

        resp = await evo_request("POST", api_url, api_key, f"/message/sendText/{instance}", {
            "number": number,
            "text": data.message,
        })

        if resp.status_code >= 400:
            raise HTTPException(status_code=resp.status_code, detail=f"Send failed: {resp.text}")

        return {"status": "sent", "response": resp.json()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whatsapp/set-webhook")
async def whatsapp_set_webhook(user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    channel = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").execute()
    if not channel.data:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    config = channel.data[0].get("config", {})
    api_url = config.get("api_url")
    api_key = config.get("api_key")
    instance = config.get("instance_name")
    webhook_base = os.environ.get("WEBHOOK_BASE_URL", "")

    if not webhook_base:
        raise HTTPException(status_code=400, detail="WEBHOOK_BASE_URL not configured")

    try:
        resp = await evo_request("POST", api_url, api_key, f"/webhook/set/{instance}", {
            "webhook": {
                "enabled": True,
                "url": f"{webhook_base}/api/webhook/whatsapp",
                "webhookByEvents": False,
                "events": ["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
            },
        })
        return {"status": "ok", "response": resp.json()}
    except Exception as e:
        logger.error(f"Webhook set error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/whatsapp/instance/{instance_name}")
async def whatsapp_delete_instance(instance_name: str, user=Depends(get_current_user)):
    tenant = await get_tenant_helper(user)
    channel = supabase.table("channels").select("*").eq("tenant_id", tenant["id"]).eq("type", "whatsapp").execute()
    if not channel.data:
        raise HTTPException(status_code=404, detail="WhatsApp channel not found")

    config = channel.data[0].get("config", {})
    api_url = config.get("api_url")
    api_key = config.get("api_key")

    try:
        await evo_request("DELETE", api_url, api_key, f"/instance/delete/{instance_name}")
    except Exception as e:
        logger.warning(f"Evolution API delete error (continuing): {e}")

    supabase.table("channels").delete().eq("id", channel.data[0]["id"]).execute()
    return {"status": "ok"}
