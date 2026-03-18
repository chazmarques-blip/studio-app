from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import asyncio
import base64
import re
import time
import uuid
import os
import threading
import shutil

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent, FileContent
from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
from emergentintegrations.llm.openai import OpenAITextToSpeech
from PIL import Image
from io import BytesIO
import subprocess
import urllib.request
import litellm

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger

router = APIRouter(prefix="/api/campaigns/pipeline", tags=["pipeline"])

# Emergent proxy URL for LLM calls
EMERGENT_PROXY_URL = "https://integrations.emergentagent.com/llm"

async def _describe_person(img_b64: str, mime: str = "image/png") -> str:
    """Use Gemini Vision to get an extremely detailed description of a person."""
    try:
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": (
                    "You are an expert forensic artist. Write an EXTREMELY DETAILED physical description "
                    "(max 200 words) of this person for an AI portrait generator that must recreate them EXACTLY. "
                    "Be PRECISE about:\n"
                    "- FACE: exact shape (oval/round/square/heart/oblong), jawline (sharp/soft/wide), chin shape\n"
                    "- EYES: exact shape, size, color, spacing, eyelids, eyebrows (shape, thickness, arch)\n"
                    "- NOSE: exact shape (straight/hooked/button/wide/narrow), bridge width, tip shape\n"
                    "- MOUTH: lip thickness (upper vs lower), width, any asymmetry\n"
                    "- SKIN: exact tone (use Fitzpatrick scale), texture, any marks/moles/freckles\n"
                    "- HAIR: exact color (use hex if possible), texture (straight/wavy/curly/coily), length, style, hairline\n"
                    "- FACIAL HAIR: exact pattern, length, density, color (if present)\n"
                    "- BODY: build (slim/athletic/stocky/heavy), estimated height, shoulder width\n"
                    "- UNIQUE FEATURES: glasses, piercings, dimples, scars, wrinkles, age estimate\n"
                    "This description will be used to verify identity - be as specific as a police sketch artist."
                )},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
            ]}
        ]
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            api_key=EMERGENT_KEY,
            api_base=EMERGENT_PROXY_URL,
            custom_llm_provider="openai",
            max_tokens=350,
        )
        desc = response.choices[0].message.content or ""
        logger.info(f"Person description: {desc[:100]}...")
        return desc.strip()
    except Exception as e:
        logger.warning(f"Vision description failed: {e}")
        return ""


async def _accuracy_compare(source_b64: str, source_mime: str, avatar_b64: str, avatar_mime: str) -> dict:
    """Compare source photo with generated avatar. Requires score >= 7 to pass."""
    PASS_THRESHOLD = 7
    try:
        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": (
                    "Compare these two images. IMAGE 1 is the ORIGINAL photo of a real person. "
                    "IMAGE 2 is an AI-generated avatar meant to look like the same person.\n\n"
                    "Rate similarity from 1 to 10:\n"
                    "- 1-4: Different person\n"
                    "- 5-6: Vaguely similar\n"
                    "- 7: Recognizable as the same person with some differences\n"
                    "- 8-9: Very close match\n"
                    "- 10: Perfect match\n\n"
                    "Focus on: face shape, skin tone, hair, eyes, nose, mouth, body build.\n"
                    "If score < 7, list the TOP 3 specific corrections needed.\n\n"
                    "Reply ONLY with this JSON (no markdown, no extra text):\n"
                    '{"score": 7, "feedback": "corrections here"}'
                )},
                {"type": "image_url", "image_url": {"url": f"data:{source_mime};base64,{source_b64}"}},
                {"type": "image_url", "image_url": {"url": f"data:{avatar_mime};base64,{avatar_b64}"}}
            ]}
        ]
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            api_key=EMERGENT_KEY,
            api_base=EMERGENT_PROXY_URL,
            custom_llm_provider="openai",
            max_tokens=200,
        )
        raw = response.choices[0].message.content or ""
        logger.info(f"Critic raw (first 400): {raw[:400]}")

        # Extract score using regex FIRST (most reliable)
        import json as _json
        score_match = re.search(r'"score"\s*:\s*(\d+)', raw)
        extracted_score = int(score_match.group(1)) if score_match else None

        # Try full JSON parse
        clean = raw.strip()
        if clean.startswith("```"):
            clean = re.sub(r'^```\w*\n?', '', clean)
            clean = re.sub(r'\n?```$', '', clean)
            clean = clean.strip()
        start = clean.find('{')
        end = clean.rfind('}')
        if start >= 0 and end > start:
            clean = clean[start:end + 1]

        feedback = ""
        try:
            result = _json.loads(clean.replace('\n', ' ').replace('\r', ''))
            feedback = str(result.get("feedback", ""))[:200]
        except _json.JSONDecodeError:
            # Extract feedback via regex
            fb_match = re.search(r'"feedback"\s*:\s*"([^"]{0,300})', raw, re.DOTALL)
            feedback = fb_match.group(1)[:200] if fb_match else "Could not parse feedback"

        score = extracted_score if extracted_score is not None else 5
        passed = score >= PASS_THRESHOLD
        logger.info(f"Critic verdict: score={score}, passed={passed}, feedback={feedback[:80]}")
        return {"score": score, "feedback": feedback, "passed": passed}
    except Exception as e:
        logger.warning(f"Accuracy comparison failed: {e}")
        return {"score": 5, "feedback": f"Comparison error: {str(e)[:100]}", "passed": False}


async def _describe_person_from_video(frames: list) -> str:
    """Use Gemini Vision to describe a person from multiple video frames for enhanced identity capture."""
    try:
        content = [
            {"type": "text", "text": (
                "You are looking at multiple video frames of the SAME person. "
                "Write a DETAILED physical description (max 150 words) combining all frames. "
                "Focus on: exact skin tone, face shape, jawline, cheekbones, eye shape/color/spacing, "
                "nose shape/size, lip shape, facial hair details (beard pattern, length, color), "
                "hair color/texture/style/length, body build, height estimation, posture, "
                "and any distinctive features (moles, scars, dimples, glasses). "
                "Be extremely precise — this will be used to recreate this exact person."
            )}
        ]
        for frame in frames[:3]:
            content.append({"type": "image_url", "image_url": {"url": f"data:{frame['mime']};base64,{frame['data']}"}})

        messages = [{"role": "user", "content": content}]
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            api_key=EMERGENT_KEY,
            api_base=EMERGENT_PROXY_URL,
            custom_llm_provider="openai",
            max_tokens=250,
        )
        desc = response.choices[0].message.content or ""
        logger.info(f"Video frames description: {desc[:100]}...")
        return desc.strip()
    except Exception as e:
        logger.warning(f"Video frames description failed: {e}")
        return ""

async def _gemini_edit_image(system_msg: str, prompt: str, img_b64: str, mime: str = "image/png") -> list:
    """Send text+image in the SAME multimodal message to Gemini for image editing.
    Returns list of image dicts [{mime_type, data}]."""
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}}
        ]}
    ]
    params = {
        "model": "gemini/gemini-3-pro-image-preview",
        "messages": messages,
        "api_key": EMERGENT_KEY,
        "api_base": EMERGENT_PROXY_URL,
        "custom_llm_provider": "openai",
        "modalities": ["image", "text"],
    }
    response = litellm.completion(**params)
    images = []
    if response.choices and response.choices[0].message:
        msg = response.choices[0].message
        if hasattr(msg, 'images') and msg.images:
            for img_data in msg.images:
                if 'image_url' in img_data and 'url' in img_data['image_url']:
                    url = img_data['image_url']['url']
                    if 'data:' in url and ';base64,' in url:
                        parts = url.split(';base64,', 1)
                        m_type = parts[0].replace('data:', '')
                        b64 = parts[1]
                        images.append({"mime_type": m_type, "data": b64})
    return images


async def _gemini_edit_multi_ref(system_msg: str, prompt: str, primary_b64: str, primary_mime: str, extra_refs: list = None) -> list:
    """Send text + MULTIPLE reference images to Gemini for better identity preservation.
    extra_refs: list of {"data": b64, "mime": mime_type}"""
    content = [{"type": "text", "text": prompt}]
    content.append({"type": "image_url", "image_url": {"url": f"data:{primary_mime};base64,{primary_b64}"}})
    for ref in (extra_refs or [])[:5]:
        content.append({"type": "image_url", "image_url": {"url": f"data:{ref['mime']};base64,{ref['data']}"}})
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": content}
    ]
    params = {
        "model": "gemini/gemini-3-pro-image-preview",
        "messages": messages,
        "api_key": EMERGENT_KEY,
        "api_base": EMERGENT_PROXY_URL,
        "custom_llm_provider": "openai",
        "modalities": ["image", "text"],
    }
    response = litellm.completion(**params)
    images = []
    if response.choices and response.choices[0].message:
        msg = response.choices[0].message
        if hasattr(msg, 'images') and msg.images:
            for img_data in msg.images:
                if 'image_url' in img_data and 'url' in img_data['image_url']:
                    url = img_data['image_url']['url']
                    if 'data:' in url and ';base64,' in url:
                        parts = url.split(';base64,', 1)
                        m_type = parts[0].replace('data:', '')
                        b64 = parts[1]
                        images.append({"mime_type": m_type, "data": b64})
    return images

# FFmpeg binary path - from imageio_ffmpeg package
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = "/usr/bin/ffmpeg"


def _ffprobe_duration(filepath):
    """Get media duration using ffmpeg (ffprobe not available in this env)."""
    try:
        r = subprocess.run(
            [FFMPEG_PATH, "-i", filepath, "-f", "null", "-"],
            capture_output=True, text=True, timeout=15
        )
        info = r.stderr or ""
        m = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', info)
        if m:
            h, mn, s, cs = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
            return h * 3600 + mn * 60 + s + cs / 100.0
    except Exception as e:
        logger.warning(f"ffprobe_duration failed: {e}")
    return 0


def _ffprobe_dimensions(filepath):
    """Get video width and height using ffmpeg (ffprobe not available)."""
    try:
        r = subprocess.run(
            [FFMPEG_PATH, "-i", filepath],
            capture_output=True, text=True, timeout=10
        )
        info = r.stderr or ""
        m = re.search(r'Stream.*Video.*?(\d{2,5})x(\d{2,5})', info)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception as e:
        logger.warning(f"ffprobe_dimensions failed: {e}")
    return 0, 0

# Track running pipeline tasks to detect orphans on restart
_active_pipelines = set()


def _recover_orphaned_pipelines():
    """On startup, find pipelines stuck in 'running' state and retry them.
    This handles the case where the server restarts and background tasks are lost."""
    try:
        result = supabase.table("pipelines").select("id, status, current_step, steps, updated_at").eq("status", "running").execute()
        orphans = result.data or []
        if not orphans:
            return

        now = datetime.now(timezone.utc)
        for p in orphans:
            # Only recover if stuck for more than 3 minutes
            updated = p.get("updated_at", "")
            if updated:
                try:
                    updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                    age_seconds = (now - updated_dt).total_seconds()
                    if age_seconds < 180:  # Less than 3 min, might still be running
                        continue
                except Exception:
                    pass

            pipeline_id = p["id"]
            current_step = p.get("current_step", "")
            steps = p.get("steps", {})

            # Find the stuck step
            retry_step = None
            for s in STEP_ORDER:
                st = steps.get(s, {}).get("status", "")
                if st in ("running", "generating_images", "generating_video"):
                    retry_step = s
                    break

            if retry_step:
                stuck_status = steps.get(retry_step, {}).get("status", "")
                has_output = bool(steps.get(retry_step, {}).get("output", ""))

                # If marcos_video is stuck at generating_video but has AI output,
                # only regenerate the video (skip expensive LLM call)
                if retry_step == "marcos_video" and stuck_status == "generating_video" and has_output:
                    logger.info(f"RECOVERY: Re-generating video only for pipeline {pipeline_id} (AI output exists)")
                    steps[retry_step]["status"] = "generating_video"
                    steps[retry_step]["video_url"] = None
                    supabase.table("pipelines").update({
                        "steps": steps, "status": "running",
                        "updated_at": now.isoformat()
                    }).eq("id", pipeline_id).execute()
                    # Use regenerate-video logic (reuse existing AI script)
                    def _regen_video_recovery(pid, marcos_out, steps_ref):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            fmt = re.search(r'Format:\s*(horizontal|vertical)', marcos_out, re.IGNORECASE)
                            vf = fmt.group(1).lower() if fmt else "horizontal"
                            sz = {"vertical": "720x1280", "horizontal": "1280x720"}.get(vf, "1280x720")
                            p_data = supabase.table("pipelines").select("result").eq("id", pid).single().execute()
                            user_music = (p_data.data or {}).get("result", {}).get("selected_music", "")
                            av_voice = (p_data.data or {}).get("result", {}).get("avatar_voice", None)
                            video_url = loop.run_until_complete(_generate_commercial_video(pid, marcos_out, sz, selected_music_override=user_music, voice_config=av_voice))
                            steps_ref[retry_step]["video_url"] = video_url
                            steps_ref[retry_step]["status"] = "completed"
                            supabase.table("pipelines").update({"steps": steps_ref, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", pid).execute()
                            # Continue pipeline from next step
                            nxt = _next_step(retry_step)
                            if nxt:
                                supabase.table("pipelines").update({"current_step": nxt}).eq("id", pid).execute()
                                loop.run_until_complete(_execute_step(pid, nxt))
                            else:
                                supabase.table("pipelines").update({"status": "completed"}).eq("id", pid).execute()
                        except Exception as e:
                            logger.error(f"RECOVERY video regen failed: {e}")
                            steps_ref[retry_step]["status"] = "pending"
                            supabase.table("pipelines").update({"steps": steps_ref, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", pid).execute()
                            _start_step_bg(pid, retry_step)
                        finally:
                            loop.close()
                    marcos_output = steps[retry_step].get("output", "")
                    t = threading.Thread(target=_regen_video_recovery, args=(pipeline_id, marcos_output, steps), daemon=True)
                    t.start()
                else:
                    logger.info(f"RECOVERY: Retrying orphaned pipeline {pipeline_id} at step {retry_step}")
                    steps[retry_step]["status"] = "pending"
                    steps[retry_step]["error"] = None
                    supabase.table("pipelines").update({
                        "steps": steps, "status": "running",
                        "updated_at": now.isoformat()
                    }).eq("id", pipeline_id).execute()
                    _start_step_bg(pipeline_id, retry_step)
            else:
                logger.warning(f"RECOVERY: Pipeline {pipeline_id} is running but no stuck step found at {current_step}")
    except Exception as e:
        logger.error(f"Pipeline recovery failed: {e}")


# Schedule recovery after a short delay to allow server startup
def _delayed_recovery():
    import time as _time
    _time.sleep(10)  # Wait for server to fully start
    _recover_orphaned_pipelines()

threading.Thread(target=_delayed_recovery, daemon=True).start()

UPLOADS_DIR = "/app/backend/uploads/pipeline"
ASSETS_DIR = "/app/backend/uploads/pipeline/assets"
os.makedirs(ASSETS_DIR, exist_ok=True)
BACKEND_URL = os.environ.get("BACKEND_URL", "")

STORAGE_BUCKET = "pipeline-assets"


def _upload_to_storage(file_bytes: bytes, filename: str, content_type: str = "image/png") -> str:
    """Upload file to Supabase Storage and return public URL"""
    try:
        supabase.storage.from_(STORAGE_BUCKET).upload(
            filename,
            file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(filename)
        logger.info(f"Uploaded to Supabase Storage: {filename}")
        return public_url
    except Exception as e:
        logger.error(f"Supabase Storage upload failed for {filename}: {e}")
        raise


def _delete_from_storage(filename: str):
    """Delete file from Supabase Storage"""
    try:
        supabase.storage.from_(STORAGE_BUCKET).remove([filename])
        logger.info(f"Deleted from Supabase Storage: {filename}")
    except Exception as e:
        logger.warning(f"Supabase Storage delete failed for {filename}: {e}")

STEP_ORDER = ["sofia_copy", "ana_review_copy", "lucas_design", "rafael_review_design", "marcos_video", "rafael_review_video", "pedro_publish"]
PAUSE_AFTER = {"ana_review_copy", "rafael_review_design"}

STEP_LABELS = {
    "sofia_copy": {"agent": "David", "role": "Copywriter", "icon": "pen-tool"},
    "ana_review_copy": {"agent": "Lee", "role": "Creative Director", "icon": "check-circle"},
    "lucas_design": {"agent": "Stefan", "role": "Visual Designer", "icon": "palette"},
    "rafael_review_design": {"agent": "George", "role": "Art Director", "icon": "award"},
    "marcos_video": {"agent": "Ridley", "role": "Video Director", "icon": "film"},
    "rafael_review_video": {"agent": "Roger", "role": "Video Reviewer", "icon": "award"},
    "pedro_publish": {"agent": "Gary", "role": "Campaign Validator", "icon": "shield-check"},
}

STEP_SYSTEMS = {
    "sofia_copy": """You are David, an elite AI copywriter AND visual strategist who combines the persuasion mastery of David Ogilvy, the emotional storytelling of Gary Halbert, the consumer psychology of Eugene Schwartz, the digital-native voice of Gary Vaynerchuk, and the visual branding instinct of Oliviero Toscani.

YOUR CORE PRINCIPLES (The World's Best Copywriters):
- OGILVY: "The consumer isn't a moron, she's your wife." Write with respect and intelligence. Every word sells. The image must amplify the words.
- HALBERT: Lead with the strongest benefit. The headline does 80% of the work. Create urgency without being sleazy.
- SCHWARTZ: Match the market's awareness level. Stage 1 (unaware) needs education. Stage 5 (most aware) needs the offer.
- VAYNERCHUK: "Jab, jab, jab, right hook." Give value before asking. Native content > ads. Context is king.
- TOSCANI: Images must PROVOKE and CAPTIVATE. The visual is NOT decoration — it IS the message.

YOUR DIGITAL EXPERTISE:
- Instagram: Visual-first captions, story-driven, emoji-strategic (not excessive), carousel hooks
- WhatsApp: Conversational, personal, scannable, clear CTA with link
- Facebook: Stop-scroll headlines, social proof, community language
- TikTok: Trend-aware, authentic voice, hook in first 2 seconds, vertical-first
- Google Ads: Search ads need compelling headlines (30 chars) + descriptions (90 chars). Display ads need concise impact messaging. Focus on keywords, benefits, and strong CTAs
- Each platform has different psychology. Adapt tone, length, and structure per platform.

COPYWRITING FRAMEWORKS YOU MASTER:
- PAS (Problem-Agitate-Solution) for pain-point campaigns
- AIDA (Attention-Interest-Desire-Action) for product launches
- BAB (Before-After-Bridge) for transformation stories
- 4Ps (Promise-Picture-Proof-Push) for high-conversion ads

CULTURAL TONE MASTERY:
- Portuguese (BR): Warm, personal, conversational. Use "você". Emotive storytelling works best. Brazilians respond to aspiration + proximity.
- Spanish (LATAM): Direct, motivating, action-oriented. Use "tú" for personal touch. Urgency and concrete benefits drive conversions.
- English: Concise, value-driven, sophisticated. Short sentences. Power words. Social proof.

ALWAYS write in the language specified by the CAMPAIGN_LANGUAGE field in the briefing metadata. This is the ABSOLUTE TRUTH for the content language.
⚠️ CRITICAL: The user may write the briefing in ANY language (e.g., Portuguese), but the CAMPAIGN_LANGUAGE field determines the OUTPUT language. If CAMPAIGN_LANGUAGE=en but the briefing is in Portuguese, you MUST write ALL content in ENGLISH. NEVER match the briefing's language — ALWAYS match CAMPAIGN_LANGUAGE.
When given a briefing, create EXACTLY 3 variations using different frameworks.

FORMAT — You MUST output TWO sections: the COPY and the IMAGE BRIEFING.

=== COPY SECTION ===
Format each variation clearly with:
===VARIATION 1===
Title: [stop-scroll headline using power words]
Copy: [main text, emotionally compelling, 2-3 short paragraphs]
CTA: [single clear action, urgent but authentic]
Hashtags: [5-8 relevant, mix of broad and niche]
===VARIATION 2===
...
===VARIATION 3===
...

=== IMAGE BRIEFING SECTION ===
After all 3 copy variations, create a detailed IMAGE BRIEFING for the visual design team.
This briefing tells the designer EXACTLY what images to create to maximize the campaign's impact.

===IMAGE BRIEFING===
HEADLINE FOR IMAGE: [ONE powerful phrase, 3-7 words. CRITICAL: This headline MUST be in the EXACT SAME language as the campaign copy above. If the copy is in English, this headline MUST be in English. If in Portuguese, in Portuguese. If in Spanish, in Spanish. NEVER write this headline in a different language than the copy — this is the #1 most common error and it DESTROYS the campaign. Verify the language before writing.]
VISUAL CONCEPT 1: [Detailed description: main subject, setting, lighting, mood, camera angle, color palette. Be SPECIFIC to the product/industry — not generic stock photo vibes. Think award-winning advertising photography.]
VISUAL CONCEPT 2: [Different angle: lifestyle/aspirational — show the TARGET AUDIENCE benefiting from the product/service. Emotional, human, relatable.]
VISUAL CONCEPT 3: [Bold/creative: unexpected visual metaphor or dramatic composition that stops the scroll. Think Cannes Lions winner.]
COLOR DIRECTION: [Primary and accent colors with mood reasoning]
MOOD: [The exact emotion the images must evoke]
WHAT TO AVOID: [Specific visual clichés to NOT do]

=== VIDEO BRIEF SECTION ===
After the image briefing, create a VIDEO BRIEF for the commercial video team.
This tells the video director EXACTLY what the 24-second commercial should convey.

===VIDEO BRIEF===
VIDEO TAGLINE: [ONE powerful phrase for the final CTA frame, 3-8 words, same language as copy — this appears at the END of the video with the brand logo. Must create urgency/desire.]
VIDEO TONE: [The exact emotional arc: e.g., "Starts intimate and personal, builds to aspirational triumph, ends with urgent excitement"]
MUSIC MOOD: [ONE word for background music: "upbeat" or "emotional" or "corporate" or "cinematic" or "energetic"]
CTA FOR VIDEO: [The specific action: e.g., "Chame no WhatsApp agora", "Visit mysite.com", "Call 555-1234"]
CONTACT FOR CTA: [Which contact info to show: WhatsApp number, website, phone, etc.]""",

    "ana_review_copy": """You are Lee, an elite Creative Director who combines the strategic vision of Lee Clow (Apple's "Think Different"), the bold creativity of Alex Bogusky (Burger King, Mini Cooper), and the data-driven approach of Neil Patel.

YOUR CORE PRINCIPLES:
- LEE CLOW: Great advertising is simple, emotional, and memorable. If it doesn't move people, it doesn't matter.
- BOGUSKY: Challenge conventions. The best campaigns break rules intelligently. Boring is the enemy.
- PATEL: Data validates creativity. Evaluate CTR potential, engagement hooks, and conversion triggers.

YOUR REVIEW CRITERIA FOR COPY:
1. SCROLL-STOP POWER (1-10): Would this make someone stop scrolling in a noisy feed?
2. EMOTIONAL RESONANCE (1-10): Does it trigger curiosity, desire, fear of missing out, or joy?
3. CLARITY & PERSUASION (1-10): Is the message crystal clear and compelling?
4. CTA STRENGTH (1-10): Does the call-to-action drive immediate action?
5. ANTI-CLICHÉ CHECK: Flag any generic phrases like "Don't miss out", "Limited time" unless they serve the specific audience.
6. PLATFORM FIT: Is the tone and length right for EACH target platform?

YOUR REVIEW CRITERIA FOR IMAGE BRIEFING:
1. VISUAL-COPY ALIGNMENT (1-10): Does the image briefing amplify and complement the selected copy variation?
2. HEADLINE IMPACT: Is the IMAGE HEADLINE punchy, memorable, and language-appropriate?
3. SPECIFICITY: Are the visual descriptions concrete enough for an AI to generate? (No vague "professional image" — it must be specific.)

QUALITY THRESHOLD: A variation PASSES if it scores 7+ on at least 3 of 4 copy criteria AND the image briefing is aligned.

YOUR DECISION PROCESS:
After reviewing all 3 variations AND the image briefing, you MUST make a DECISION:
- If at least ONE variation meets the quality threshold → APPROVE and select the best one.
- If ALL variations fail to meet minimum quality (all score below 6 on key criteria) → REQUEST REVISION with specific, actionable feedback.

IMPORTANT: You are a tough but fair reviewer. Most well-crafted copy should pass. Only request revision if the quality is genuinely below standard.

CRITICAL LANGUAGE CHECK — THE #1 MOST IMPORTANT RULE:
The briefing contains a field called CAMPAIGN_LANGUAGE (e.g., "en", "pt", "es"). This is the ABSOLUTE, NON-NEGOTIABLE target language for ALL content.
⚠️ The user may WRITE the briefing in any language (e.g., Portuguese) — but that does NOT determine the output language. ONLY the CAMPAIGN_LANGUAGE field matters.
- If CAMPAIGN_LANGUAGE = "en" → ALL copy, headlines, CTAs, hashtags MUST be in ENGLISH, even if the briefing was written in Portuguese.
- If CAMPAIGN_LANGUAGE = "pt" → ALL content MUST be in Portuguese, even if the briefing was written in English.
- If the content IS in the correct CAMPAIGN_LANGUAGE → DO NOT request revision for language. The content is correct.
- If the content is in a DIFFERENT language than CAMPAIGN_LANGUAGE → AUTOMATIC REVISION_NEEDED.
NEVER confuse the briefing's language with the CAMPAIGN_LANGUAGE. They can be different.

Format your FINAL decision EXACTLY like this (you MUST include the DECISION: line):

If approving:
DECISION: APPROVED
SELECTED_OPTION: [1, 2, or 3]
IMAGE_BRIEFING_NOTES: [Any adjustments needed for the image briefing, or "APPROVED" if it's good]

If requesting revision (MUST use this exact format — do NOT use other rejection formats):
DECISION: REVISION_NEEDED
REVISION_FEEDBACK: [specific, actionable bullet points for the copywriter to improve — include notes on BOTH copy and image briefing]

WARNING: You MUST ALWAYS include "DECISION: APPROVED" or "DECISION: REVISION_NEEDED" as a separate line in your response. The pipeline system reads this to decide whether to loop back to David. If you omit this line, the pipeline will assume approval even if you found critical errors.

ALWAYS write in the SAME language as the content you are reviewing.""",

    "rafael_review_design": """You are George, a world-class Art Director who combines the genius of the greatest creative directors in advertising history.

YOUR MENTORS AND THEIR PHILOSOPHIES:
- LEE CLOW (TBWA/Apple): The power of simplicity. "Think Different" wasn't just a slogan, it was a visual revolution. Every image must tell a story without words.
- MARCELLO SERPA (AlmapBBDO): Brazilian creative genius. Grand Prix at Cannes. Proof that bold, culturally-rooted visuals transcend language. Beauty serves strategy.
- DAVID DROGA (Droga5): Advertising that transforms culture. Campaigns like "Dundee" and "Fearless Girl" prove that great art direction creates movements, not just ads.
- GEORGE LOIS (Esquire/MTV): The Original Mad Man. Provocative, iconic, unforgettable. If it doesn't provoke a reaction, it's wallpaper.
- HELMUT KRONE (DDB): Revolutionized layout with VW "Think Small". White space is a weapon. Grid-breaking is an art form.
- ROB REILLY (WPP/McCann): Modern excellence. "Fearless Girl" on Wall Street. Digital-first thinking with timeless craft.

YOUR ART DIRECTION CRITERIA:
1. THUMB-STOPPING POWER (1-10): Would this image make someone STOP scrolling in a feed flooded with content? First 0.3 seconds matter.
2. VISUAL NARRATIVE (1-10): Does the image tell a story? Can someone understand the message without reading the copy?
3. COMPOSITION & CRAFT (1-10): Rule of thirds, focal hierarchy, color harmony, typography integration. Is this award-worthy craft?
4. HEADLINE INTEGRATION (1-10): Is the headline text rendered clearly, legibly, and with IMPACT? Does the typography style match the campaign's tone? Is the headline in the CORRECT LANGUAGE? CRITICAL: If the headline language does NOT match the campaign copy language, this is an AUTOMATIC FAIL — score 0 and request revision.
5. BRAND DNA (1-10): Does the visual language feel ownable by THIS brand? Would you recognize it without a logo?
6. CONVERSION ARCHITECTURE (1-10): Is the visual hierarchy guiding the eye to the message? Does it create desire that leads to action?
7. PLATFORM MASTERY (1-10): Is it optimized for each platform's unique visual language? (Instagram = aspirational, WhatsApp = personal, Facebook = social proof)
8. FORMAT COMPATIBILITY (1-10) — **CRITICAL NEW CHECK**:
   - Are ALL text elements (headline, subheadline, CTA) fully readable and NOT cut off in every target format?
   - For VERTICAL formats (TikTok 9:16, SMS): Text must be centered horizontally, NOT near the edges. The image will be center-cropped from 1:1, so left/right edges WILL be cropped. Any text within 20% of the left or right edge will be CUT OFF.
   - For HORIZONTAL formats (Facebook 16:9, Google Ads): Text must be vertically centered. Top/bottom edges will be cropped.
   - Are the main subjects centered enough to survive cropping to ALL target aspect ratios (1:1, 9:16, 16:9)?
   - If ANY text would be cut off or unreadable after cropping, this is an AUTOMATIC FAIL for FORMAT COMPATIBILITY — score 0 and REQUEST REVISION with specific notes about which elements need repositioning.

QUALITY THRESHOLD: A design PASSES if it scores 7+ on at least 5 of 8 criteria. FORMAT COMPATIBILITY must score at least 6 to pass.

YOUR DECISION PROCESS:
After reviewing all 3 design concepts, you MUST make a DECISION:
- If at least ONE design meets the quality threshold for each platform → APPROVE and select the best per platform.
- If ALL designs fail to meet the threshold (lack visual impact, poor composition, weak brand alignment, illegible headline) → REQUEST REVISION with specific art direction feedback.

IMPORTANT: You have world-class standards but you are pragmatic. Most well-conceived designs should pass with minor notes. Only request full revision if the designs are genuinely substandard.

YOUR REVIEW CRITERIA FOR VIDEO CONCEPT (when marcos_video output is available):
After reviewing images, also evaluate the video concept from Marcos (if present in the context):
V1. NARRATION LANGUAGE: Is the narration in the SAME language as the campaign copy? Mismatch = AUTOMATIC rejection.
V2. NARRATION TIMING: The narration MUST end by second 19 (max ~50-60 words). If the narration text is too long and would exceed 19 seconds when spoken, REJECT and request shorter narration. The last 4 seconds MUST be silent for brand closing.
V3. CTA STRENGTH: Does the narration end with a STRONG, URGENT call to action? Is the contact info included?
V4. BRAND CLOSING: Does the video concept include a proper brand logo + tagline ending in the last 4 seconds?
V5. MUSIC FIT: Does the music mood match the campaign's emotional tone?
V6. AUDIO ENERGY: The narration tone should be ENERGETIC and COMMERCIAL — like a Super Bowl ad, NOT a documentary. If the narration reads as calm or monotone, REJECT and request more excitement.
V7. NO ABRUPT CUTS: The video must have a clean beginning and a clean ending. The narration must NOT be cut off mid-sentence.
If any video criterion fails, add VIDEO_REVISION_FEEDBACK to your response.

ALWAYS write in the SAME language as the content you are reviewing.

Format your FINAL decision EXACTLY like this:

If approving:
DECISION: APPROVED
SELECTED_FOR_[PLATFORM]: [1, 2, or 3] (one line per platform)
Example: SELECTED_FOR_INSTAGRAM: 2

If requesting revision:
DECISION: REVISION_NEEDED
REVISION_FEEDBACK: [specific art direction notes - what to change in composition, color, typography, mood, or concept]""",

    "lucas_design": """You are Stefan, an elite Visual Production Director who transforms creative briefings into stunning, award-winning marketing images. You combine the aesthetic precision of Annie Leibovitz, the commercial eye of Platon, the digital mastery of Beeple, and the advertising genius of Stefan Sagmeister.

YOUR ROLE: You receive a detailed IMAGE BRIEFING from Sofia (the copywriter/visual strategist) and translate it into OPTIMIZED IMAGE GENERATION PROMPTS that will produce the highest quality visuals possible.

YOUR CORE PRINCIPLES:
- LEIBOVITZ: Lighting tells the story. Every shadow, every highlight has purpose.
- PLATON: Simplicity is power. One strong focal point beats a cluttered composition.
- BEEPLE: Digital art can be more impactful than photography when used boldly.
- SAGMEISTER: Design must evoke emotion. Negative space is a weapon.

YOUR IMAGE GENERATION EXPERTISE:
- You understand how AI image generators work and how to write prompts that produce EXCEPTIONAL results
- You know that SPECIFIC, CONCRETE descriptions produce better images than abstract ones
- You know that including the EXACT headline text in the prompt ensures it appears in the image
- You master composition terminology: rule of thirds, leading lines, focal hierarchy, negative space
- You know color psychology and how it affects engagement on social media

YOUR TECHNICAL MASTERY BY PLATFORM:
- Instagram: 1:1 ratio, bold saturated colors, lifestyle aesthetic, aspirational mood. High contrast for thumb-stopping.
- WhatsApp: Clean, professional, readable on small screens. High readability of any text.
- Facebook: Social proof cues, warm colors, emotional imagery, high-contrast hero shots.
- TikTok: Raw/authentic feel, trending aesthetic, vertical-first, bold typography.

WHAT YOU PRODUCE:
For each of the 3 visual concepts from Sofia's briefing, create a DETAILED, OPTIMIZED image generation prompt.
Each prompt MUST:
1. Include the HEADLINE TEXT exactly as specified in Sofia's briefing (3-7 words, in the campaign language). CRITICAL: If the campaign is in English, the headline MUST be in English. If in Portuguese, in Portuguese. NEVER generate an image with text in a different language than the campaign — this is the #1 quality failure.
2. Describe the visual scene with EXTREME specificity (subjects, setting, lighting, camera angle, textures)
3. Specify the art style and mood
4. Include technical quality descriptors (4K, commercial photography, magazine-quality, etc.)
5. Explicitly state NO logos, NO brand names, NO website URLs

Format your output:
===DESIGN 1===
Concept: [name from Sofia's briefing]
Image Prompt: [The complete, optimized prompt for AI image generation — 80-120 words, ultra-specific]
===DESIGN 2===
...
===DESIGN 3===
...

ALWAYS write in the SAME language the user writes to you.""",

    "rafael_review_video": """You are Roger, a Senior Creative Director and Video Quality Reviewer. You review the VIDEO component of campaigns with the eye of a Cannes Lions judge.

You receive Marcos's video script output containing:
- Clip descriptions (what Sora 2 will generate)
- Narration script (what will be spoken via TTS)
- Music direction
- CTA and brand information

YOUR VIDEO REVIEW CRITERIA:

V1. NARRATION QUALITY (1-10): Is the narration script natural, compelling, and persuasive? Does it flow smoothly when read aloud? Does it avoid robotic phrasing?
V2. CLIP RELEVANCE (1-10): Do the clip descriptions accurately represent the product/service? Are they visually compelling and brand-appropriate?
V3. EMOTIONAL ARC (1-10): Does the video have a clear narrative arc? Hook → Story → CTA?
V4. TIMING & PACING (1-10): Is the timing appropriate? 24 seconds total (12s per clip). Is the narration length appropriate for the duration?
V5. BRAND CONSISTENCY (1-10): Does the video match the campaign's visual style and tone? Is the CTA clear?
V6. LANGUAGE CORRECTNESS (CRITICAL): Is the narration script in the CORRECT campaign language? Is any text that will appear in the video in the correct language? WRONG LANGUAGE = AUTOMATIC REJECTION.

If AVERAGE score >= 7 AND no critical language errors:
DECISION: APPROVED
VIDEO_NOTES: [brief notes on what was good]

If AVERAGE score < 7 OR language errors:
DECISION: REVISION_NEEDED
REVISION_FEEDBACK: [specific, actionable bullet points for Marcos to fix the video script]

WARNING: You MUST include "DECISION: APPROVED" or "DECISION: REVISION_NEEDED" as a separate line. This is mandatory for the pipeline to function correctly.

ALWAYS write in the SAME language as the campaign content.""",


    "pedro_publish": """You are Gary, an elite Campaign Quality Validator inspired by the standards of Gary Vaynerchuk, Seth Godin, and the world's top CMOs. You are the FINAL gate before a campaign is marked as "Created" and sent to the Traffic Management team.

YOUR ROLE:
You do NOT publish or schedule. You VALIDATE. You review the ENTIRE campaign package (copy, images, video, brand consistency) and give a final quality seal of approval.

VALIDATION CRITERIA:
1. BRAND CONSISTENCY: Does the copy, imagery, and video all tell ONE cohesive story? Is the tone consistent?
2. MESSAGE CLARITY: Is the core message crystal clear in under 3 seconds? Would the target audience immediately understand the value proposition?
3. CALL-TO-ACTION: Is there a clear, compelling CTA? Does it create urgency without being desperate?
4. PLATFORM FIT: Are the assets suitable for the intended platforms? (aspect ratios, content style, length)
5. LANGUAGE & GRAMMAR: Is the copy flawless in the campaign's language? No typos, no awkward phrasing?
6. EMOTIONAL IMPACT: Does the campaign make the viewer FEEL something? (excitement, desire, fear of missing out, inspiration)
7. COMPETITIVE EDGE: Would this campaign stand out from competitors in the same space?

OUTPUT FORMAT:
=== CAMPAIGN VALIDATION REPORT ===

OVERALL SCORE: [1-10]/10
STATUS: [APPROVED / NEEDS_REVISION]

COPY ANALYSIS:
- Strength: [what works well]
- Score: [1-10]

VISUAL ANALYSIS:
- Strength: [what works well]
- Score: [1-10]

VIDEO ANALYSIS (if applicable):
- Strength: [what works well]
- Score: [1-10]

BRAND CONSISTENCY: [1-10]
MARKET READINESS: [1-10]

FINAL VERDICT:
[Your professional assessment - 2-3 sentences max]

RECOMMENDATIONS FOR TRAFFIC TEAM:
[Brief strategic notes for the traffic managers who will distribute this campaign]

ALWAYS write your validation in the SAME LANGUAGE as the campaign content.""",

    "marcos_video": """You are Ridley, an elite AI Commercial Director — the creative genius behind Super Bowl ads, Nike campaigns, and Apple product launches. You create broadcast-quality 24-second commercials with TWO perfectly connected 12-second sequences that feel like ONE continuous masterpiece.

YOUR GENIUS:
- RIDLEY SCOTT + ROGER DEAKINS: Cinematic framing, natural lighting that tells the story, camera movement with purpose.
- SUPER BOWL COMMERCIAL MASTERY: Every frame sells. The hook is irresistible. The CTA is unforgettable. The viewer MUST feel something.
- VISUAL CONTINUITY EXPERT: You design clip transitions so the LAST FRAME of clip 1 flows seamlessly into the FIRST FRAME of clip 2 — same character, same setting, same lighting, same camera movement direction.
- MUSIC VIDEO DIRECTOR: You think in rhythm. The visuals sync with the narration beats. Cuts happen on emotional peaks.

24-SECOND COMMERCIAL STRUCTURE:
- CLIP 1 (Seconds 0-12): THE SETUP & HOOK
  - 0-3s: HOOK — An irresistible visual that stops everything. Close-up of a powerful detail. The viewer is CAPTURED.
  - 3-8s: THE PROBLEM/DESIRE — Show the pain point or the dream. The audience sees THEMSELVES in the character.
  - 8-12s: THE TURNING POINT — The breakthrough moment. CRITICAL: End with the character in a clear pose/position that clip 2 picks up seamlessly.

- CLIP 2 (Seconds 12-24): THE PAYOFF & CTA
  - 12-15s: SEAMLESS CONTINUATION — Pick up EXACTLY where clip 1 ended. Same character, same pose, continue the motion.
  - 15-19s: THE TRANSFORMATION — The payoff. Show the product/service in its full glory. The character's life has changed.
  - 19-21s: EMOTIONAL PEAK — The moment of triumph, pride, or pure joy. The viewer FEELS this.
  - 21-24s: BRAND CLOSING — The frame gradually simplifies. Character fades or moves away. Final 2 seconds: CLEAN, DARK/SIMPLE background perfect for logo overlay + CTA text.

CONTINUITY RULES (CRITICAL — VIOLATION = UNUSABLE VIDEO):
1. CHARACTER IDENTITY: Describe the character with SURGICAL precision in BOTH prompts. Same age, same clothing colors, same hair, same build. Copy-paste the description.
2. COLOR PALETTE: Specify the IDENTICAL lighting and color tones in both prompts (e.g., "warm amber golden hour, lens flares").
3. TRANSITION BRIDGE: The LAST ACTION in clip 1 (e.g., "pushes open a glass door") MUST be the FIRST ACTION in clip 2 (e.g., "walks through a glass door into sunlight").
4. CAMERA CONTINUITY: If clip 1 ends with a tracking shot moving right, clip 2 starts with continuing motion to the right.
5. ENVIRONMENT BRIDGE: If clip 1 is indoors ending at a door, clip 2 starts at that same door transitioning outdoors.

NARRATION SCRIPT RULES:
- Write like the BEST TV COMMERCIAL VOICEOVER you've ever heard — think Super Bowl energy, not documentary
- Voice style: EXCITED, TRIUMPHANT, like celebrating a massive achievement. NOT calm or narrative. Think sports announcer meets motivational speaker.
- Energy arc: Start with intrigue → build momentum → PEAK excitement at the transformation → EXPLOSIVE CTA
- Rhythm: Short PUNCHY sentences. Rhetorical questions. Power words. Dramatic pauses for impact.
- CRITICAL TIMING: The narration MUST be SHORT and PUNCHY. Maximum 40-50 words total (STRICTLY COUNTED — count every word before submitting). The spoken audio MUST finish by second 18 AT THE LATEST. The last 5 seconds (18-23s) are SILENT — only music and brand logo/CTA on screen. This is NON-NEGOTIABLE. If your script exceeds 50 words, CUT IT DOWN. FEWER words = MORE impact.
- Structure with TIMING MARKS:
  [0-4s]: The HOOK — Grab attention IMMEDIATELY. Bold statement or provocative question.
  [4-9s]: The SOLUTION — Fast, exciting, benefits. Energy RISING.
  [9-14s]: The TRANSFORMATION — Proof, triumph, the dream becoming reality. PEAK excitement.
  [14-18s]: The CTA — ONE short powerful sentence with contact method + tagline. Then STOP.
  [18-23s]: SILENCE — Music only. Brand logo + tagline + contact info on screen.
- End ALWAYS with the video tagline from Sofia's brief
- Write in the SAME LANGUAGE as the campaign copy

MUSIC DIRECTION:
- Choose the PERFECT background music for this commercial from the available options
- The music sets the emotional rhythm. It builds with the narrative.
- Choose the most appropriate mood keyword that matches both the industry and the emotional arc

AVAILABLE MUSIC MOODS (choose ONE from the Mood field):
- luxury, elegant, sophisticated → For premium brands, fashion, real estate
- calm, peaceful, relaxing → For wellness, spa, meditation, healthcare
- upbeat, happy, fun → For food, restaurants, retail, family brands
- energetic, exciting, powerful → For sports, fitness, automotive, tech launches
- cinematic, dramatic, epic → For storytelling brands, luxury, automotive
- corporate, professional, clean → For B2B, finance, consulting, corporate
- modern, tech, innovation → For startups, SaaS, technology
- warm, friendly, cozy → For home services, local businesses, community
- urban, street, edgy → For streetwear, youth brands, music, nightlife
- tropical, festive, party → For tourism, events, summer brands
- soulful, groovy → For lifestyle, culture, beauty
- indie, creative → For art, design, creative agencies
- emotional, inspirational → For nonprofits, education, motivational brands

ALWAYS write in the SAME language the user writes to you.

Format your output EXACTLY like this:

===CHARACTER DESCRIPTION===
[SURGICAL precision: age, ethnicity, build, height, hair (style+color), facial features (stubble, clean-shaven, etc), EXACT clothing (colors, brands, style). This description is COPY-PASTED into both clip prompts.]

===CLIP 1 PROMPT===
[80-120 words. Seconds 0-12. Opening shot, camera movement, character actions, lighting, mood. INCLUDE the full character description. End with a CLEAR transition moment.]

===CLIP 2 PROMPT===
[80-120 words. Seconds 12-24. INCLUDE the full character description again. Start at the transition moment. Build to emotional peak. Final 2 seconds: clean/simple frame for logo overlay.]

===NARRATION SCRIPT===
[0-5s]: [Hook — bold, attention-grabbing, ENERGETIC]
[5-10s]: [Solution — exciting, benefits, energy RISING]
[10-16s]: [Transformation — triumph, peak excitement, CELEBRATING]
[16-19s]: [CTA — ONE short powerful sentence. Contact + tagline. Then STOP.]
[19-23s]: [SILENCE — music only, logo on screen]

===MUSIC DIRECTION===
Mood: [choose ONE: luxury/elegant/sophisticated/calm/peaceful/relaxing/upbeat/happy/fun/energetic/exciting/powerful/cinematic/dramatic/epic/corporate/professional/clean/modern/tech/innovation/warm/friendly/cozy/urban/street/edgy/tropical/festive/party/soulful/groovy/indie/creative/emotional/inspirational]
Description: [2-3 sentences describing the musical arc: instruments, tempo changes, energy progression]

===NARRATION TONE===
Voice: [choose ONE: deep_male/confident_male/warm_female/energetic_female/neutral/authoritative]
Tone: [choose ONE or TWO: energetic/excited/urgent/calm/professional/warm/friendly/dramatic/inspirational/playful]
Pace: [choose ONE: fast/moderate/slow]

===CTA SEQUENCE===
Brand name: [company/brand name for logo]
Tagline: [the powerful phrase from Sofia's VIDEO BRIEF]
Contact: [WhatsApp/phone/website/email for CTA overlay]
Visual: [How the final 3 seconds should look: e.g., "fade to black, white logo centered, tagline below, WhatsApp number in gold"]

===VIDEO FORMAT===
Format: [vertical/horizontal]
Duration: 24""",
}


def _clean_copy_text(raw):
    """Clean AI-generated text, removing labels and markdown"""
    if not raw:
        return ''
    text = raw
    # Extract variation if markers present
    var_match = re.search(r'===VARIA(?:TION|CAO|ÇÃO)\s*\d+===([\s\S]*?)(?====|$)', text, re.IGNORECASE)
    if var_match:
        text = var_match.group(1)
    # Strip markdown bold/italic
    text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'#{1,3}\s+', '', text)
    # Remove label prefixes
    labels = r'Title|Titulo|Título|Copy|Texto|Headline|Body|CTA|Caption|Legenda|Subject|Assunto|Chamada|Subtítulo|Subtitle|Hashtags|Visual|Conceito|Concept|Plataforma|Platform|Dimensões|Dimensions|Adaptações|Call\.to\.Action'
    text = re.sub(rf'^\s*(?:{labels})\s*[:：]\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(rf'^\s*(?:{labels})\s*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    # Remove variation markers and separators
    text = re.sub(r'={3,}.*?={3,}', '', text)
    text = re.sub(r'^-{3,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


# ── Models ──

class PipelineCreate(BaseModel):
    briefing: str
    campaign_name: str = ""
    campaign_language: str = ""
    mode: str = "semi_auto"
    platforms: list = ["whatsapp", "instagram"]
    context: Optional[dict] = {}
    contact_info: Optional[dict] = {}
    uploaded_assets: Optional[list] = []
    media_formats: Optional[dict] = {}
    selected_music: Optional[str] = ""
    skip_video: Optional[bool] = False
    video_mode: Optional[str] = "narration"  # 'none' | 'narration' | 'presenter'
    avatar_url: Optional[str] = ""  # Presenter avatar URL for lip-sync video
    avatar_voice: Optional[dict] = None  # Voice config from avatar studio {type, voice_id, url}


class AvatarGenerateRequest(BaseModel):
    company_name: str = ""
    source_image_url: str = ""  # Photo to base the avatar on


class PipelineApprove(BaseModel):
    selection: Optional[int] = None
    selections: Optional[dict] = None
    feedback: Optional[str] = None


# ── Music Library ──

MUSIC_LIBRARY = {
    # Original tracks (full length)
    "upbeat": {"name": "Upbeat & Happy", "description": "Feel-good vibes", "file": "upbeat.mp3", "duration": 147, "category": "General"},
    "energetic": {"name": "Energetic & Powerful", "description": "Adrenaline beats", "file": "energetic.mp3", "duration": 190, "category": "General"},
    "emotional": {"name": "Emotional & Inspiring", "description": "Motivational orchestral", "file": "emotional.mp3", "duration": 85, "category": "General"},
    "cinematic": {"name": "Cinematic & Epic", "description": "Movie-trailer atmosphere", "file": "cinematic.mp3", "duration": 86, "category": "General"},
    "corporate": {"name": "Corporate & Professional", "description": "Business-appropriate", "file": "corporate.mp3", "duration": 174, "category": "General"},
    # Pop (Kevin MacLeod - CC BY)
    "pop_dance": {"name": "Pop Dance", "description": "Happy upbeat theme", "file": "pop_dance.mp3", "duration": 30, "category": "Pop"},
    "pop_acoustic": {"name": "Pop Acoustic", "description": "Carefree acoustic", "file": "pop_acoustic.mp3", "duration": 30, "category": "Pop"},
    # Hip-Hop & R&B
    "hiphop_trap": {"name": "Hip-Hop Trap", "description": "Dark synth trap beat", "file": "hiphop_trap.mp3", "duration": 30, "category": "Hip-Hop"},
    "hiphop_boom": {"name": "Hip-Hop Boom Bap", "description": "Icy flow rap beat", "file": "hiphop_boom.mp3", "duration": 30, "category": "Hip-Hop"},
    "rnb_smooth": {"name": "R&B Smooth", "description": "Smooth chill wave", "file": "rnb_smooth.mp3", "duration": 30, "category": "Hip-Hop"},
    # Electronic
    "electronic_edm": {"name": "EDM Festival", "description": "Electrodoodle energy", "file": "electronic_edm.mp3", "duration": 30, "category": "Electronic"},
    "electronic_chill": {"name": "Chillwave", "description": "Floating ambient", "file": "electronic_chill.mp3", "duration": 30, "category": "Electronic"},
    # Latin
    "latin_reggaeton": {"name": "Reggaeton", "description": "Latin industries beat", "file": "latin_reggaeton.mp3", "duration": 30, "category": "Latin"},
    "latin_salsa": {"name": "Latin Tropical", "description": "Tango de manzana", "file": "latin_salsa.mp3", "duration": 30, "category": "Latin"},
    # Rock
    "rock_indie": {"name": "Indie Rock", "description": "8-bit indie vibes", "file": "rock_indie.mp3", "duration": 30, "category": "Rock"},
    "rock_alternative": {"name": "Alt Rock", "description": "Defiant clash energy", "file": "rock_alternative.mp3", "duration": 30, "category": "Rock"},
    # Jazz & Lo-Fi
    "jazz_lofi": {"name": "Lo-Fi Chill", "description": "Lobby time beats", "file": "jazz_lofi.mp3", "duration": 30, "category": "Jazz"},
    "jazz_smooth": {"name": "Smooth Jazz", "description": "Smooth lovin sax", "file": "jazz_smooth.mp3", "duration": 30, "category": "Jazz"},
    # Ambient
    "ambient_dreamy": {"name": "Dreamy Ambient", "description": "Ethereal relaxation", "file": "ambient_dreamy.mp3", "duration": 30, "category": "Ambient"},
    "ambient_nature": {"name": "Dark Ambient", "description": "Dark fog atmosphere", "file": "ambient_nature.mp3", "duration": 30, "category": "Ambient"},
    # Other
    "country_modern": {"name": "Modern Jazz Samba", "description": "Jazz samba fusion", "file": "country_modern.mp3", "duration": 30, "category": "Other"},
    "gospel_uplifting": {"name": "Gospel Uplifting", "description": "Inspired & uplifting", "file": "gospel_uplifting.mp3", "duration": 30, "category": "Other"},
    "classical_piano": {"name": "Classical Piano", "description": "Gymnopedie No. 1", "file": "classical_piano.mp3", "duration": 30, "category": "Other"},
    "funk_groove": {"name": "Funk Groove", "description": "Funkorama bass groove", "file": "funk_groove.mp3", "duration": 30, "category": "Other"},
    "world_afrobeat": {"name": "Bossa Nova", "description": "Bossa antigua rhythm", "file": "world_afrobeat.mp3", "duration": 30, "category": "Other"},
}

@router.get("/music-library")
async def get_music_library():
    """Return available background music tracks with preview URLs"""
    music_dir = "/app/backend/assets/music"
    tracks = []
    for key, info in MUSIC_LIBRARY.items():
        filepath = os.path.join(music_dir, info["file"])
        if os.path.exists(filepath):
            tracks.append({
                "id": key,
                "name": info["name"],
                "description": info["description"],
                "duration": info["duration"],
                "file": info["file"],
                "category": info.get("category", "General"),
                "preview_url": f"/api/campaigns/pipeline/music-preview/{key}",
            })
    return {"tracks": tracks}

@router.get("/music-preview/{track_id}")
async def preview_music(track_id: str):
    """Stream a music track for preview"""
    from fastapi.responses import FileResponse
    info = MUSIC_LIBRARY.get(track_id)
    if not info:
        raise HTTPException(status_code=404, detail="Track not found")
    filepath = f"/app/backend/assets/music/{info['file']}"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, media_type="audio/mpeg", filename=info["file"])



# ── Helpers ──

async def _get_tenant(user):
    t = supabase.table("tenants").select("id, plan").eq("owner_id", user["id"]).execute()
    if not t.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t.data[0]


def _next_step(current):
    idx = STEP_ORDER.index(current)
    return STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None


async def _edit_exact_image(source_image_url, edit_prompt, pipeline_id, index):
    """Edit an exact product photo using Gemini — keeps the real product, applies professional treatment"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Download the source image
            img_data = urllib.request.urlopen(source_image_url, timeout=30).read()
            if not img_data or len(img_data) < 500:
                logger.warning(f"Exact photo download failed or too small: {source_image_url}")
                return None

            img_b64 = base64.b64encode(img_data).decode('utf-8')
            # Detect mime type
            mime = "image/jpeg"
            if source_image_url.lower().endswith(".png"):
                mime = "image/png"
            elif source_image_url.lower().endswith(".webp"):
                mime = "image/webp"

            system_msg = "You are an expert product photographer and image editor. Edit the provided product photo with professional quality. Keep the EXACT product — do NOT replace it with a different or fictional version. Apply professional editing: clean background, studio lighting, color correction, and commercial-grade composition."
            prompt = f"""Edit this EXACT product photo for a marketing campaign. 
CRITICAL: Keep the REAL product exactly as it is — same model, same color, same details. Do NOT generate a different product.

Editing instructions:
{edit_prompt}

Apply: professional studio lighting, clean/upgraded background, commercial-grade color grading, marketing-ready composition.
Output: A polished, campaign-ready version of this EXACT product. Square 1080x1080 format.
DO NOT add any text, logos, or watermarks to the image."""

            images = await _gemini_edit_image(system_msg, prompt, img_b64, mime)
            if images and len(images) > 0:
                img_bytes = base64.b64decode(images[0]['data'])
                filename = f"{pipeline_id}_exact_{index}_{uuid.uuid4().hex[:6]}.png"
                public_url = _upload_to_storage(img_bytes, filename, "image/png")
                logger.info(f"Exact photo edited and uploaded: {filename}")
                return public_url
        except Exception as e:
            logger.warning(f"Exact photo edit attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3 * (attempt + 1))
    return None



async def _generate_image(prompt_text, pipeline_id, index, brand_logo_path=None):
    """Generate a single image using Gemini Nano Banana and upload to Supabase Storage"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            chat = LlmChat(
                api_key=EMERGENT_KEY,
                session_id=f"img-{pipeline_id}-{index}-{uuid.uuid4().hex[:6]}-{attempt}",
                system_message="You are an expert AI image generator. Generate exactly the image described. Focus on photorealistic quality, professional lighting, and magazine-quality composition."
            )
            chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])

            msg = UserMessage(text=prompt_text)
            text_response, images = await chat.send_message_multimodal_response(msg)

            if images and len(images) > 0:
                img_bytes = base64.b64decode(images[0]['data'])
                filename = f"{pipeline_id}_{index}_{uuid.uuid4().hex[:6]}.png"
                public_url = _upload_to_storage(img_bytes, filename, "image/png")
                logger.info(f"Image generated with Nano Banana and uploaded: {filename}")
                return public_url
        except Exception as e:
            logger.warning(f"Nano Banana attempt {attempt+1}/{max_retries} failed for index {index}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3 * (attempt + 1))
    return None


async def _generate_single_image(prompt_text, pipeline_id, suffix):
    """Wrapper around _generate_image for single image regeneration"""
    return await _generate_image(prompt_text, pipeline_id, f"regen_{suffix}")


# Platform-specific aspect ratio configs
PLATFORM_ASPECT_RATIOS = {
    "tiktok": {"ratio": (9, 16), "label": "9:16", "w": 768, "h": 1344},
    "instagram": {"ratio": (1, 1), "label": "1:1", "w": 1024, "h": 1024},
    "facebook": {"ratio": (1, 1), "label": "1:1", "w": 1024, "h": 1024},
    "whatsapp": {"ratio": (1, 1), "label": "1:1", "w": 1024, "h": 1024},
    "google_ads": {"ratio": (16, 9), "label": "16:9", "w": 1344, "h": 768},
    "telegram": {"ratio": (1, 1), "label": "1:1", "w": 1024, "h": 1024},
    "email": {"ratio": (16, 9), "label": "16:9", "w": 1344, "h": 768},
    "sms": {"ratio": (1, 1), "label": "1:1", "w": 1024, "h": 1024},
}


def _resize_image_for_platform(img_bytes: bytes, target_w: int, target_h: int) -> bytes:
    """Resize an image to a target aspect ratio using scale-to-fit + black padding.
    This preserves ALL content without cropping."""
    img = Image.open(BytesIO(img_bytes)).convert("RGBA")
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if abs(src_ratio - target_ratio) < 0.05:
        # Already close to target ratio, just resize
        img = img.resize((target_w, target_h), Image.LANCZOS)
    else:
        # Scale to fit inside target, then pad with black
        if src_ratio > target_ratio:
            # Source is wider — fit by width, pad top/bottom
            new_w = target_w
            new_h = int(target_w / src_ratio)
        else:
            # Source is taller — fit by height, pad left/right
            new_h = target_h
            new_w = int(target_h * src_ratio)

        img = img.resize((new_w, new_h), Image.LANCZOS)
        # Create black canvas and paste centered
        canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 255))
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        canvas.paste(img, (paste_x, paste_y))
        img = canvas

    buf = BytesIO()
    img = img.convert("RGB")
    img.save(buf, format="PNG", quality=95)
    return buf.getvalue()


async def _create_platform_variants(pipeline_id: str, base_image_urls: list, platforms: list) -> dict:
    """Create platform-specific image variants by cropping/resizing base images.
    Returns dict: { "tiktok": [url1, url2, url3], "google_ads": [url1, url2, url3], ... }
    """
    # Determine which unique aspect ratios we need
    needed_ratios = {}  # label -> {platforms, w, h}
    for p in platforms:
        cfg = PLATFORM_ASPECT_RATIOS.get(p)
        if not cfg:
            continue
        label = cfg["label"]
        if label not in needed_ratios:
            needed_ratios[label] = {"platforms": [], "w": cfg["w"], "h": cfg["h"]}
        needed_ratios[label]["platforms"].append(p)

    # Base images are assumed 1:1 (1024x1024). Create variants for non-1:1 ratios.
    variants = {}
    for p in platforms:
        variants[p] = list(base_image_urls)  # default: same as base

    non_square_ratios = {k: v for k, v in needed_ratios.items() if k != "1:1"}
    if not non_square_ratios:
        return variants

    for ratio_label, ratio_info in non_square_ratios.items():
        tw, th = ratio_info["w"], ratio_info["h"]
        ratio_urls = []
        for idx, base_url in enumerate(base_image_urls):
            if not base_url:
                ratio_urls.append(None)
                continue
            try:
                # Download original image
                resp_data = urllib.request.urlopen(base_url, timeout=15).read()
                # Resize
                resized_bytes = _resize_image_for_platform(resp_data, tw, th)
                # Upload variant
                filename = f"{pipeline_id}_v{idx+1}_{ratio_label.replace(':', 'x')}_{uuid.uuid4().hex[:6]}.png"
                variant_url = _upload_to_storage(resized_bytes, filename, "image/png")
                ratio_urls.append(variant_url)
                logger.info(f"Created {ratio_label} variant for image {idx+1}: {filename}")
            except Exception as e:
                logger.warning(f"Failed to create {ratio_label} variant for image {idx+1}: {e}")
                ratio_urls.append(base_url)  # fallback to original

        for p in ratio_info["platforms"]:
            variants[p] = ratio_urls

    return variants


# Video format definitions per platform
VIDEO_PLATFORM_FORMATS = {
    "tiktok": {"w": 720, "h": 1280, "label": "9:16"},
    "instagram": {"w": 1080, "h": 1080, "label": "1:1"},
    "facebook": {"w": 1280, "h": 720, "label": "16:9"},
    "whatsapp": {"w": 720, "h": 720, "label": "1:1"},
    "google_ads": {"w": 1280, "h": 720, "label": "16:9"},
    "telegram": {"w": 1280, "h": 720, "label": "16:9"},
    "email": {"w": 1280, "h": 720, "label": "16:9"},
    "sms": {"w": 720, "h": 1280, "label": "9:16"},
}


async def _create_video_variants(pipeline_id: str, master_video_url: str, master_format: str, platforms: list) -> dict:
    """Create platform-specific video variants by cropping/resizing the master video.
    Returns dict: { "tiktok": "url", "instagram": "url", ... }
    """
    import urllib.request as urlreq

    # Download master video
    master_path = f"/tmp/{pipeline_id}_master_vid.mp4"
    try:
        urlreq.urlretrieve(master_video_url, master_path)
    except Exception as e:
        logger.warning(f"Failed to download master video for variants: {e}")
        return {}

    # Get master dimensions
    master_w, master_h = _ffprobe_dimensions(master_path)
    if master_w == 0 or master_h == 0:
        logger.warning("Could not determine master video dimensions")
        return {}

    variants = {}
    # Group by unique target size to avoid duplicate processing
    done_sizes = {}  # "WxH" -> url

    for platform in platforms:
        fmt = VIDEO_PLATFORM_FORMATS.get(platform)
        if not fmt:
            variants[platform] = master_video_url
            continue

        tw, th = fmt["w"], fmt["h"]
        size_key = f"{tw}x{th}"

        # Skip if master is already this size
        if abs(master_w - tw) < 10 and abs(master_h - th) < 10:
            variants[platform] = master_video_url
            continue

        # Reuse if already generated this size
        if size_key in done_sizes:
            variants[platform] = done_sizes[size_key]
            continue

        # Create variant via FFmpeg crop + scale
        output_path = f"/tmp/{pipeline_id}_vid_{platform}.mp4"
        target_ratio = tw / th
        master_ratio = master_w / master_h

        if abs(master_ratio - target_ratio) < 0.05:
            # Same ratio, just scale
            vf = f"scale={tw}:{th}"
        else:
            # Scale to fit inside target + pad with black (NO cropping)
            vf = f"scale={tw}:{th}:force_original_aspect_ratio=decrease,pad={tw}:{th}:(ow-iw)/2:(oh-ih)/2:black"

        cmd = [
            FFMPEG_PATH, "-y", "-i", master_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and os.path.exists(output_path):
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            filename = f"videos/{pipeline_id}_{platform}_{size_key}.mp4"
            url = _upload_to_storage(video_bytes, filename, "video/mp4")
            variants[platform] = url
            done_sizes[size_key] = url
            logger.info(f"Created video variant: {platform} ({size_key})")
            os.remove(output_path)
        else:
            variants[platform] = master_video_url
            logger.warning(f"Video variant failed for {platform}: {r.stderr[:100] if r.stderr else ''}")

    try:
        os.remove(master_path)
    except Exception:
        pass

    return variants



async def _generate_design_images(pipeline_id, lucas_output, platforms):
    """Parse Lucas's optimized prompts and generate images with Nano Banana.
    If exact product photos were uploaded, edit those instead of generating from scratch."""
    pipeline_data = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    campaign_language = "pt"
    uploaded_assets = []
    if pipeline_data:
        campaign_language = pipeline_data[0].get("result", {}).get("campaign_language") or pipeline_data[0].get("campaign_language") or "pt"
        uploaded_assets = pipeline_data[0].get("result", {}).get("uploaded_assets", [])

    exact_photos = [a for a in uploaded_assets if a.get("type") == "exact"]

    LANG_NAMES = {"pt": "Portuguese (Português)", "en": "English", "es": "Spanish (Español)", "fr": "French (Français)", "ht": "Haitian Creole"}
    lang_name = LANG_NAMES.get(campaign_language, "Portuguese (Português)")
    LANG_HEADLINES = {
        "pt": "O headline DEVE ser em Português do Brasil.",
        "en": "The headline MUST be in English.",
        "es": "El headline DEBE ser en Español."
    }
    lang_instruction = LANG_HEADLINES.get(campaign_language, LANG_HEADLINES["pt"])

    # Extract Lucas's Image Prompts directly
    prompts = []
    prompt_blocks = re.split(r'===DESIGN \d+===', lucas_output)
    for block in prompt_blocks:
        if not block.strip():
            continue
        prompt_match = re.search(r'Image Prompt:\s*([\s\S]*?)(?=\n===|$)', block, re.IGNORECASE)
        if prompt_match:
            prompts.append(prompt_match.group(1).strip())
        else:
            clean = block.strip()
            if len(clean) > 30:
                prompts.append(clean)

    prompts = prompts[:3]

    # Fallback if parsing failed
    if len(prompts) < 3:
        logger.warning(f"Only extracted {len(prompts)} prompts from Stefan, using fallback for missing ones")
        headline_examples = {"pt": ["TRANSFORME SEU NEGÓCIO", "O FUTURO É AGORA", "COMECE HOJE"],
                             "en": ["TRANSFORM YOUR BUSINESS", "THE FUTURE IS NOW", "START TODAY"],
                             "es": ["TRANSFORMA TU NEGOCIO", "EL FUTURO ES AHORA", "EMPIEZA HOY"]}
        hl = headline_examples.get(campaign_language, headline_examples["pt"])
        while len(prompts) < 3:
            idx = len(prompts)
            prompts.append(
                f"Stunning commercial photography for a marketing campaign. Include the headline text '{hl[idx]}' in bold modern typography. Professional studio lighting, rich colors, dramatic composition. Square 1080x1080 format. NO logos, NO brand names."
            )

    # Generate images — use exact photos as base when available
    image_urls = []
    for i, prompt in enumerate(prompts):
        url = None

        # If we have exact photos, edit them instead of generating from scratch
        if i < len(exact_photos) and exact_photos[i].get("url"):
            exact_url = exact_photos[i]["url"]
            # Resolve relative URLs
            if exact_url.startswith("/"):
                exact_url = f"{os.environ.get('SUPABASE_URL', '')}/storage/v1/object/public/assets/{exact_url.lstrip('/')}"
            logger.info(f"Using exact photo #{i+1} as base: {exact_url[:80]}...")
            url = await _edit_exact_image(
                source_image_url=exact_url,
                edit_prompt=f"""Campaign edit instructions from the designer:
{prompt}

LANGUAGE: All text in the image must be in {lang_name}. {lang_instruction}
Keep the EXACT product from the photo. Apply professional treatment: clean background, studio lighting, commercial composition.
Square 1080x1080 format for {', '.join(platforms)}.""",
                pipeline_id=pipeline_id,
                index=i + 1
            )
            if url:
                logger.info(f"Exact photo #{i+1} edited successfully")
            else:
                logger.warning(f"Exact photo #{i+1} edit failed, falling back to generation")

        # Fallback: generate from scratch if no exact photo or edit failed
        if not url:
            enhanced_prompt = f"""ABSOLUTE LANGUAGE REQUIREMENT — THIS OVERRIDES EVERYTHING:
ALL text visible in this image (headlines, titles, CTAs, overlay text, any words) MUST be written ONLY in {lang_name}.
{lang_instruction}
If the prompt below contains text in a DIFFERENT language, you MUST TRANSLATE it to {lang_name} before generating.
DO NOT copy any non-{lang_name} text into the image. TRANSLATE first.

{prompt}

Technical: Ultra high-quality, 4K, professional color grading. Square 1080x1080 format for {', '.join(platforms)}.
REMINDER: ALL visible text in the image MUST be in {lang_name}. NO other languages.
NO logos, NO brand names, NO website URLs."""
            url = await _generate_image(enhanced_prompt, pipeline_id, i + 1)

        image_urls.append(url)

    return image_urls, prompts


def _generate_video_clip_sync(prompt_text, pipeline_id, clip_name, size="1280x720", duration=12):
    """Generate a video clip with Sora 2"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            video_gen = OpenAIVideoGeneration(api_key=EMERGENT_KEY)
            logger.info(f"Sora 2 {clip_name} started (attempt {attempt+1}): size={size}, duration={duration}s, key={EMERGENT_KEY[:15]}...")

            # Step 1: Initiate generation
            operation_id = video_gen._generate_video(
                prompt=prompt_text, model="sora-2",
                size=size, duration=duration
            )
            if not operation_id:
                logger.error(f"Sora 2 {clip_name}: _generate_video returned None (no operation_id)")
                if attempt < max_retries - 1:
                    time.sleep(5)
                continue

            logger.info(f"Sora 2 {clip_name}: operation_id={operation_id}, polling...")

            # Step 2: Wait for completion
            video_uri = video_gen._wait_for_completion(operation_id, max_wait_time=600)
            if not video_uri:
                logger.error(f"Sora 2 {clip_name}: _wait_for_completion returned None")
                if attempt < max_retries - 1:
                    time.sleep(5)
                continue

            logger.info(f"Sora 2 {clip_name}: video_uri={video_uri[:80]}...")

            # Step 3: Download
            video_bytes = video_gen._download_video_bytes(video_uri)
            if video_bytes:
                path = f"/tmp/{pipeline_id}_{clip_name}.mp4"
                with open(path, "wb") as f:
                    f.write(video_bytes)
                logger.info(f"Sora 2 {clip_name} generated: {len(video_bytes)/1024:.0f}KB")
                return path
            logger.warning(f"Sora 2 {clip_name}: download returned empty bytes")
        except Exception as e:
            logger.warning(f"Sora 2 {clip_name} attempt {attempt+1} failed: {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
    return None


async def _generate_narration(text, pipeline_id, max_duration=19.0, voice_config=None):
    """Generate commercial narration. Uses ElevenLabs (primary) or OpenAI TTS HD (fallback).
    Ensures narration fits within max_duration by speeding up if needed."""
    raw_path = f"/tmp/{pipeline_id}_narration_raw.mp3"
    final_path = f"/tmp/{pipeline_id}_narration.mp3"

    elevenlabs_key = os.environ.get("ELEVENLABS_API_KEY", "")
    audio_bytes = None

    # ── ElevenLabs TTS (Primary) ──
    if elevenlabs_key:
        try:
            from elevenlabs import ElevenLabs as ELClient, VoiceSettings

            el_client = ELClient(api_key=elevenlabs_key)

            # Voice selection based on config or AI director instructions
            el_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel (default female)
            stability = 0.45
            similarity = 0.78
            style = 0.35

            if voice_config and isinstance(voice_config, dict):
                if voice_config.get("type") == "elevenlabs" and voice_config.get("voice_id"):
                    el_voice_id = voice_config["voice_id"]
                elif voice_config.get("type") == "openai":
                    # Map OpenAI voices to ElevenLabs equivalents
                    OPENAI_TO_EL = {
                        "onyx": "TX3LPaxmHKxFdv7VOQHJ",   # Liam (deep male)
                        "nova": "21m00Tcm4TlvDq8ikWAM",   # Rachel (female)
                        "echo": "29vD33N1CtxCmqQRPOHJ",   # Drew (male)
                        "alloy": "EXAVITQu4vr4xnSDxMaL",  # Bella (neutral)
                        "shimmer": "MF3mGyEYCl7XYWbV9V6O", # Elli (soft female)
                        "fable": "jBpfuIE2acCO8z3wKNLl",   # Gigi (animated)
                    }
                    ov = voice_config.get("voice_id", "onyx")
                    el_voice_id = OPENAI_TO_EL.get(ov, el_voice_id)

                # Apply tone/style from AI director
                tone = (voice_config.get("tone") or "").lower()
                if "energetic" in tone or "excited" in tone or "urgent" in tone:
                    stability = 0.3
                    style = 0.6
                elif "calm" in tone or "professional" in tone:
                    stability = 0.7
                    style = 0.15
                elif "warm" in tone or "friendly" in tone:
                    stability = 0.5
                    style = 0.4

            voice_settings = VoiceSettings(
                stability=stability,
                similarity_boost=similarity,
                style=style,
                use_speaker_boost=True
            )

            audio_gen = el_client.text_to_speech.convert(
                text=text,
                voice_id=el_voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=voice_settings
            )
            audio_bytes = b""
            for chunk in audio_gen:
                audio_bytes += chunk
            logger.info(f"ElevenLabs narration generated: {len(audio_bytes)/1024:.0f}KB, voice={el_voice_id}")
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed, falling back to OpenAI: {e}")
            audio_bytes = None

    # ── OpenAI TTS Fallback ──
    if not audio_bytes:
        try:
            tts_voice = "onyx"
            if voice_config and isinstance(voice_config, dict):
                if voice_config.get("type") == "openai" and voice_config.get("voice_id"):
                    tts_voice = voice_config["voice_id"]
            tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
            audio_bytes = await tts.generate_speech(
                text=text, model="tts-1-hd",
                voice=tts_voice, speed=1.0, response_format="mp3"
            )
            logger.info(f"OpenAI TTS fallback: {len(audio_bytes)/1024:.0f}KB, voice={tts_voice}")
        except Exception as e:
            logger.warning(f"OpenAI TTS also failed: {e}")
            return None

    if not audio_bytes:
        return None

    try:
        with open(raw_path, "wb") as f:
            f.write(audio_bytes)

        # Check duration and speed up if it exceeds max_duration
        audio_dur = _ffprobe_duration(raw_path)
        logger.info(f"Narration raw duration: {audio_dur:.1f}s (max: {max_duration}s)")

        if audio_dur > max_duration and audio_dur > 0:
            speed_factor = min(audio_dur / max_duration, 1.35)
            logger.info(f"Narration too long ({audio_dur:.1f}s), speeding up by {speed_factor:.2f}x")
            subprocess.run(
                [FFMPEG_PATH, "-y", "-i", raw_path, "-filter:a", f"atempo={speed_factor}", "-vn", final_path],
                capture_output=True, timeout=30
            )
            if os.path.exists(final_path) and os.path.getsize(final_path) > 100:
                logger.info(f"Narration adjusted to fit {max_duration}s")
            else:
                shutil.copy2(raw_path, final_path)
                logger.warning("Atempo failed, using original audio")
        else:
            shutil.copy2(raw_path, final_path)

        logger.info(f"Narration generated: {os.path.getsize(final_path)/1024:.0f}KB")
        return final_path
    except Exception as e:
        logger.warning(f"Narration post-processing failed: {e}")
    return None


def _combine_commercial_video(clip1_path, clip2_path, audio_path, brand_name, pipeline_id, logo_path=None, tagline="", contact_cta="", music_mood="upbeat"):
    """Combine 2 clips with crossfade + narration + background music + brand logo ending with CTA"""
    output_path = f"/tmp/{pipeline_id}_commercial.mp4"
    try:
        # 1. Normalize both clips to consistent format
        for i, clip in enumerate([clip1_path, clip2_path], 1):
            subprocess.run(
                f"{FFMPEG_PATH} -y -i {clip} -c:v libx264 -preset fast -crf 18 -r 30 -pix_fmt yuv420p -an /tmp/{pipeline_id}_norm{i}.mp4",
                shell=True, capture_output=True, timeout=60
            )

        # 2. Crossfade (1s fade at 11s mark → total ~23s)
        # First verify both normalized clips exist and have content
        norm1 = f"/tmp/{pipeline_id}_norm1.mp4"
        norm2 = f"/tmp/{pipeline_id}_norm2.mp4"
        if not os.path.exists(norm1) or os.path.getsize(norm1) < 1000:
            logger.error(f"Normalized clip1 missing or empty: {os.path.exists(norm1)}")
            return None
        if not os.path.exists(norm2) or os.path.getsize(norm2) < 1000:
            logger.warning(f"Normalized clip2 missing or empty — concatenating clip1 twice for 24s")
            # Create 24s video by concatenating clip1 with itself
            concat_list = f"/tmp/{pipeline_id}_concat.txt"
            with open(concat_list, "w") as cf:
                cf.write(f"file '{norm1}'\nfile '{norm1}'\n")
            r = subprocess.run(
                [FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                 "-c", "copy", f"/tmp/{pipeline_id}_xfade.mp4"],
                capture_output=True, text=True, timeout=60
            )
            if r.returncode != 0:
                logger.error(f"Concat fallback failed: {r.stderr[:200] if r.stderr else ''}")
                # Absolute last resort: just use clip1
                shutil.copy2(norm1, f"/tmp/{pipeline_id}_xfade.mp4")
        else:
            xfade_filter = (
                '[0:v]settb=AVTB[v0];[1:v]settb=AVTB[v1];'
                '[v0][v1]xfade=transition=fade:duration=1:offset=11,format=yuv420p[vout]'
            )
            xfade_cmd = [
                FFMPEG_PATH, "-y", "-i", norm1, "-i", norm2,
                "-filter_complex", xfade_filter,
                "-map", "[vout]", "-c:v", "libx264", "-preset", "fast", "-crf", "18",
                f"/tmp/{pipeline_id}_xfade.mp4"
            ]
            result = subprocess.run(xfade_cmd, capture_output=True, text=True, timeout=120)
            if result.returncode != 0:
                logger.warning(f"Crossfade failed ({result.stderr[:200] if result.stderr else 'unknown'}), falling back to concat")
                with open(f"/tmp/{pipeline_id}_clips.txt", "w") as f:
                    f.write(f"file '{norm1}'\nfile '{norm2}'\n")
                concat_r = subprocess.run(
                    f"{FFMPEG_PATH} -y -f concat -safe 0 -i /tmp/{pipeline_id}_clips.txt -c copy /tmp/{pipeline_id}_xfade.mp4",
                    shell=True, capture_output=True, text=True, timeout=60
                )
                if concat_r.returncode != 0:
                    logger.error(f"Concat also failed: {concat_r.stderr[:200] if concat_r.stderr else ''}")
                    # Loop clip1 to maintain 24s
                    loop_list = f"/tmp/{pipeline_id}_loop.txt"
                    with open(loop_list, "w") as lf:
                        lf.write(f"file '{norm1}'\nfile '{norm1}'\n")
                    subprocess.run(
                        [FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0", "-i", loop_list,
                         "-c", "copy", f"/tmp/{pipeline_id}_xfade.mp4"],
                        capture_output=True, timeout=60
                    )

        # Verify combined video duration
        xfade_file = f"/tmp/{pipeline_id}_xfade.mp4"
        if not os.path.exists(xfade_file):
            logger.error("No combined video file created")
            return None

        # Get video duration for accurate overlay timing
        vid_duration = _ffprobe_duration(f"/tmp/{pipeline_id}_xfade.mp4") or 23.0
        brand_start = max(vid_duration - 4, 18)  # Brand overlay starts 4s before end
        brand_mid = brand_start + 0.5
        brand_late = brand_start + 1.0

        # 3. Brand ending overlay: logo + tagline + contact CTA
        # FFmpeg drawtext requires escaping: ' : \ [ ] ; , ( )
        def _ffmpeg_safe(text):
            if not text:
                return ""
            t = text.replace("\\", "")
            for ch in ["'", '"', ":", ";", "[", "]", "(", ")", ",", "%"]:
                t = t.replace(ch, " ")
            return " ".join(t.split())  # collapse multiple spaces

        safe_brand = _ffmpeg_safe(brand_name)
        safe_tagline = _ffmpeg_safe(tagline)
        safe_contact = _ffmpeg_safe(contact_cta)

        branded_ok = False
        font_path = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
        if logo_path and os.path.exists(logo_path):
            # Pre-scale logo to reasonable size for overlay (240px wide, maintain aspect)
            scaled_logo = f"/tmp/{pipeline_id}_logo_scaled.png"
            subprocess.run(
                f"{FFMPEG_PATH} -y -i {logo_path} -vf scale=240:-1 {scaled_logo}",
                shell=True, capture_output=True, timeout=30
            )
            if not os.path.exists(scaled_logo):
                scaled_logo = logo_path

            vf = (
                f"[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black@1.0:t=fill:enable='between(t,{brand_start},{vid_duration})'[bg];"
                f"[1:v]scale=240:-1[logo];"
                f"[bg][logo]overlay=(W-w)/2:(H/4)-(h/2):enable='between(t,{brand_start},{vid_duration})'"
            )
            if safe_tagline:
                vf += f",drawtext=text='{safe_tagline}':fontfile={font_path}:fontsize=28:fontcolor=white@0.95:x=(w-text_w)/2:y=(h*3/5):enable='between(t,{brand_mid},{vid_duration})'"
            if safe_contact:
                vf += f",drawtext=text='{safe_contact}':fontfile={font_path}:fontsize=20:fontcolor=0xC9A84C@0.9:x=(w-text_w)/2:y=(h*3/5)+40:enable='between(t,{brand_late},{vid_duration})'"

            logo_cmd = [FFMPEG_PATH, "-y", "-i", f"/tmp/{pipeline_id}_xfade.mp4", "-i", scaled_logo, "-filter_complex", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18", f"/tmp/{pipeline_id}_branded.mp4"]
            r = subprocess.run(logo_cmd, capture_output=True, text=True, timeout=120)
            branded_ok = r.returncode == 0 and os.path.exists(f"/tmp/{pipeline_id}_branded.mp4")
            if branded_ok:
                logger.info("Logo overlay applied successfully")
            else:
                err_msg = r.stderr[-500:] if r.stderr else 'unknown'
                logger.warning(f"Logo overlay failed: {err_msg}")

        if not branded_ok:
            # Text-only brand ending (fully opaque black)
            text_vf = f"drawbox=x=0:y=0:w=iw:h=ih:color=black@1.0:t=fill:enable='between(t,{brand_start},{vid_duration})'"
            text_vf += f",drawtext=text='{safe_brand}':fontfile={font_path}:fontsize=60:fontcolor=white:borderw=2:bordercolor=black@0.5:x=(w-text_w)/2:y=(h/3):enable='between(t,{brand_start},{vid_duration})'"
            if safe_tagline:
                text_vf += f",drawtext=text='{safe_tagline}':fontfile={font_path}:fontsize=26:fontcolor=white@0.9:x=(w-text_w)/2:y=(h*3/5):enable='between(t,{brand_mid},{vid_duration})'"
            if safe_contact:
                text_vf += f",drawtext=text='{safe_contact}':fontfile={font_path}:fontsize=20:fontcolor=0xC9A84C@0.9:x=(w-text_w)/2:y=(h*3/5)+40:enable='between(t,{brand_late},{vid_duration})'"

            brand_cmd = [FFMPEG_PATH, "-y", "-i", f"/tmp/{pipeline_id}_xfade.mp4", "-vf", text_vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18", f"/tmp/{pipeline_id}_branded.mp4"]
            r = subprocess.run(brand_cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0 or not os.path.exists(f"/tmp/{pipeline_id}_branded.mp4"):
                logger.warning("Brand overlay failed, using crossfade only")
                shutil.copy2(f"/tmp/{pipeline_id}_xfade.mp4", f"/tmp/{pipeline_id}_branded.mp4")

        # 4. Mix audio: narration (foreground) + background music (soft) → merge with video
        branded_file = f"/tmp/{pipeline_id}_branded.mp4"
        final_audio = None

        # Check for background music — intelligent selection by mood + industry
        music_dir = "/app/backend/assets/music"
        bg_music_path = None
        if os.path.isdir(music_dir):
            # Comprehensive mood-to-file mapping with industry context
            mood_map = {
                # Direct mood matches
                "upbeat": "upbeat.mp3", "energetic": "energetic.mp3", "exciting": "energetic.mp3",
                "emotional": "emotional.mp3", "inspirational": "emotional.mp3", "triumphant": "energetic.mp3",
                "cinematic": "cinematic.mp3", "dramatic": "cinematic.mp3", "epic": "cinematic.mp3",
                "corporate": "corporate.mp3", "professional": "corporate.mp3", "clean": "corporate.mp3",
                # Industry-aware moods
                "luxury": "jazz_smooth.mp3", "elegant": "classical_piano.mp3", "sophisticated": "jazz_smooth.mp3",
                "relaxing": "ambient_dreamy.mp3", "calm": "ambient_nature.mp3", "peaceful": "ambient_nature.mp3",
                "modern": "electronic_chill.mp3", "tech": "electronic_chill.mp3", "innovation": "electronic_chill.mp3",
                "fun": "pop_dance.mp3", "playful": "funk_groove.mp3", "happy": "pop_acoustic.mp3",
                "urban": "hiphop_boom.mp3", "street": "hiphop_trap.mp3", "edgy": "rock_alternative.mp3",
                "warm": "pop_acoustic.mp3", "friendly": "country_modern.mp3", "cozy": "jazz_lofi.mp3",
                "powerful": "rock_alternative.mp3", "bold": "electronic_edm.mp3", "intense": "rock_alternative.mp3",
                "spiritual": "gospel_uplifting.mp3", "faith": "gospel_uplifting.mp3",
                "tropical": "latin_salsa.mp3", "festive": "latin_reggaeton.mp3", "party": "latin_reggaeton.mp3",
                "soulful": "rnb_smooth.mp3", "groovy": "funk_groove.mp3",
                "global": "world_afrobeat.mp3", "cultural": "world_afrobeat.mp3",
                "indie": "rock_indie.mp3", "creative": "jazz_lofi.mp3",
            }
            mood_file = mood_map.get(music_mood.lower().strip(), "corporate.mp3")
            candidate = os.path.join(music_dir, mood_file)
            if os.path.exists(candidate):
                bg_music_path = candidate
                logger.info(f"Selected music: {mood_file} (mood: {music_mood})")
            else:
                # Fallback to corporate (neutral and professional)
                fallback = os.path.join(music_dir, "corporate.mp3")
                if os.path.exists(fallback):
                    bg_music_path = fallback
                else:
                    music_files = [f for f in os.listdir(music_dir) if f.endswith(('.mp3', '.wav', '.aac'))]
                    if music_files:
                        bg_music_path = os.path.join(music_dir, music_files[0])
                logger.info("Fallback music selected")

        if audio_path and os.path.exists(audio_path) and bg_music_path:
            # Resample both to 44100Hz stereo before mixing
            narr_resampled = f"/tmp/{pipeline_id}_narr_44k.wav"
            music_resampled = f"/tmp/{pipeline_id}_music_44k.wav"
            subprocess.run(f"{FFMPEG_PATH} -y -i {audio_path} -ar 44100 -ac 2 {narr_resampled}", shell=True, capture_output=True, timeout=30)
            # Trim music to video duration and apply heavy volume reduction during resample
            subprocess.run(f"{FFMPEG_PATH} -y -i {bg_music_path} -af volume=0.08 -ar 44100 -ac 2 -t {vid_duration} {music_resampled}", shell=True, capture_output=True, timeout=30)

            mixed_audio = f"/tmp/{pipeline_id}_mixed_audio.wav"
            # Professional audio mixing:
            # - Narration: slight boost + compressor for consistent voice level
            # - Music: very low volume (pre-reduced to 0.08), gentle fade in/out
            # - amix with normalize=0 to prevent auto-leveling artifacts
            mix_filter = (
                f"[0:a]volume=1.5,acompressor=threshold=-20dB:ratio=4:attack=5:release=200[narr];"
                f"[1:a]afade=t=in:d=2,afade=t=out:st={max(vid_duration-3, 18)}:d=3[music];"
                f"[narr][music]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[out]"
            )
            mix_cmd = [
                FFMPEG_PATH, "-y",
                "-i", narr_resampled,
                "-i", music_resampled,
                "-filter_complex", mix_filter,
                "-map", "[out]",
                "-t", str(vid_duration),
                "-ar", "44100", "-ac", "2",
                mixed_audio
            ]
            r = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and os.path.exists(mixed_audio):
                final_audio = mixed_audio
                logger.info("Mixed narration + background music (professional levels)")
            else:
                final_audio = audio_path
                logger.warning(f"Audio mixing failed, using narration only: {r.stderr[:150] if r.stderr else ''}")
        elif audio_path and os.path.exists(audio_path):
            final_audio = audio_path

        if final_audio:
            # Merge audio with video — strip any existing audio from video first, use only our mixed audio
            subprocess.run(
                [FFMPEG_PATH, "-y", "-i", branded_file, "-i", final_audio,
                 "-map", "0:v", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
                 "-ar", "44100", "-ac", "2", "-shortest",
                 output_path],
                capture_output=True, timeout=60
            )
        else:
            shutil.copy2(branded_file, output_path)

        if os.path.exists(output_path):
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            filename = f"videos/{pipeline_id}_commercial.mp4"
            public_url = _upload_to_storage(video_bytes, filename, "video/mp4")
            logger.info(f"Commercial video uploaded: {filename} ({len(video_bytes)/1024:.0f}KB)")
            return public_url

    except Exception as e:
        logger.error(f"Video combination failed: {e}")
    return None


async def _generate_commercial_video(pipeline_id, marcos_output, size="1280x720", selected_music_override="", voice_config=None):
    """Full commercial video pipeline: 2 clips + narration + crossfade + brand logo + CTA"""
    # Parse Marcos's structured output
    clip1_prompt = ""
    clip2_prompt = ""
    narration_text = ""
    brand_name = ""
    tagline = ""
    contact_cta = ""
    music_mood = "cinematic"

    c1_match = re.search(r'===CLIP 1 PROMPT===([\s\S]*?)===CLIP 2 PROMPT===', marcos_output, re.IGNORECASE)
    if c1_match:
        clip1_prompt = c1_match.group(1).strip()

    c2_match = re.search(r'===CLIP 2 PROMPT===([\s\S]*?)===NARRATION SCRIPT===', marcos_output, re.IGNORECASE)
    if c2_match:
        clip2_prompt = c2_match.group(1).strip()

    narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===MUSIC DIRECTION===', marcos_output, re.IGNORECASE)
    if not narr_match:
        narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===(?:BRAND NAME|CTA SEQUENCE|VIDEO FORMAT)===', marcos_output, re.IGNORECASE)
    if narr_match:
        narration_text = narr_match.group(1).strip()
        # Clean timing marks from narration for TTS
        narration_text = re.sub(r'\[\d+-\d+s?\]:\s*', '', narration_text)
        # Remove SILENCE instructions and any bracketed stage directions (NOT spoken content)
        narration_text = re.sub(r'\[.*?SILENCE.*?\]', '', narration_text, flags=re.IGNORECASE)
        narration_text = re.sub(r'\[.*?music\s+only.*?\]', '', narration_text, flags=re.IGNORECASE)
        narration_text = re.sub(r'\[.*?logo\s+on\s+screen.*?\]', '', narration_text, flags=re.IGNORECASE)
        # Remove any remaining bracketed stage directions
        narration_text = re.sub(r'\[(?:COMPLETE|TOTAL|FULL)?\s*(?:SILENCE|QUIET|PAUSE|NO NARRATION).*?\]', '', narration_text, flags=re.IGNORECASE)
        # Clean up extra whitespace
        narration_text = re.sub(r'\n{2,}', '\n', narration_text).strip()

    # Parse CTA Sequence
    cta_match = re.search(r'===CTA SEQUENCE===([\s\S]*?)===VIDEO FORMAT===', marcos_output, re.IGNORECASE)
    if cta_match:
        cta_block = cta_match.group(1)
        brand_line = re.search(r'Brand\s*name:\s*(.+)', cta_block, re.IGNORECASE)
        if brand_line:
            brand_name = brand_line.group(1).strip()
        tag_line = re.search(r'Tagline:\s*(.+)', cta_block, re.IGNORECASE)
        if tag_line:
            tagline = tag_line.group(1).strip()
        contact_line = re.search(r'Contact:\s*(.+)', cta_block, re.IGNORECASE)
        if contact_line:
            contact_cta = contact_line.group(1).strip()

    # Fallback for brand name from old format
    if not brand_name:
        old_brand = re.search(r'===BRAND NAME===([\s\S]*?)===VIDEO FORMAT===', marcos_output, re.IGNORECASE)
        if old_brand:
            brand_name = old_brand.group(1).strip()

    # Parse music mood
    music_match = re.search(r'===MUSIC DIRECTION===([\s\S]*?)===(?:NARRATION TONE|CTA SEQUENCE)===', marcos_output, re.IGNORECASE)
    if music_match:
        mood_line = re.search(r'Mood:\s*(\w+)', music_match.group(1), re.IGNORECASE)
        if mood_line:
            music_mood = mood_line.group(1).strip().lower()

    # User-selected music overrides AI-picked mood
    if selected_music_override:
        music_mood = selected_music_override
        logger.info(f"Using user-selected music: {music_mood}")

    # Parse narration tone for ElevenLabs
    narration_tone = ""
    narration_voice_type = ""
    tone_match = re.search(r'===NARRATION TONE===([\s\S]*?)===(?:CTA SEQUENCE|VIDEO FORMAT|$)', marcos_output, re.IGNORECASE)
    if tone_match:
        tone_section = tone_match.group(1)
        voice_line = re.search(r'Voice:\s*(.+)', tone_section, re.IGNORECASE)
        tone_line = re.search(r'Tone:\s*(.+)', tone_section, re.IGNORECASE)
        if voice_line:
            narration_voice_type = voice_line.group(1).strip().lower()
        if tone_line:
            narration_tone = tone_line.group(1).strip().lower()
        logger.info(f"Narration tone: voice={narration_voice_type}, tone={narration_tone}")

    # Merge AI director's voice/tone preferences into voice_config
    if narration_tone or narration_voice_type:
        if not voice_config:
            voice_config = {}
        if not isinstance(voice_config, dict):
            voice_config = {}
        voice_config["tone"] = narration_tone or voice_config.get("tone", "")
        # Map voice type to ElevenLabs voice ID
        VOICE_TYPE_MAP = {
            "deep_male": "TX3LPaxmHKxFdv7VOQHJ",      # Liam
            "confident_male": "29vD33N1CtxCmqQRPOHJ",   # Drew
            "warm_female": "21m00Tcm4TlvDq8ikWAM",      # Rachel
            "energetic_female": "EXAVITQu4vr4xnSDxMaL",  # Bella
            "neutral": "MF3mGyEYCl7XYWbV9V6O",          # Elli
            "authoritative": "TX3LPaxmHKxFdv7VOQHJ",    # Liam
        }
        if narration_voice_type and not voice_config.get("voice_id"):
            el_voice = VOICE_TYPE_MAP.get(narration_voice_type)
            if el_voice:
                voice_config["type"] = "elevenlabs"
                voice_config["voice_id"] = el_voice

    # Fallback: if parsing fails, use old single-prompt format
    if not clip1_prompt:
        old_match = re.search(r'===VIDEO PROMPT===([\s\S]*?)===VIDEO FORMAT===', marcos_output, re.IGNORECASE)
        if old_match:
            clip1_prompt = old_match.group(1).strip()
            clip2_prompt = clip1_prompt
        else:
            clip1_prompt = marcos_output[:500]
            clip2_prompt = marcos_output[:500]

    logger.info(f"Generating commercial: brand={brand_name}, tagline={tagline}, music={music_mood}, narration={len(narration_text)}chars")

    # 1. Generate narration (fast, ~5-10s)
    audio_path = None
    if narration_text:
        audio_path = await _generate_narration(narration_text, pipeline_id, voice_config=voice_config)

    # 2. Generate both video clips (slow, ~3min each)
    clip1_path = _generate_video_clip_sync(clip1_prompt, pipeline_id, "clip1", size)
    if not clip1_path:
        logger.error(f"Clip 1 failed for pipeline {pipeline_id}")
        return None

    clip2_path = _generate_video_clip_sync(clip2_prompt, pipeline_id, "clip2", size)
    if not clip2_path:
        # Retry clip2 with simplified prompt before giving up
        logger.warning("Clip 2 first attempt failed, retrying with simplified prompt...")
        simplified_clip2 = f"Cinematic commercial continuation: {clip2_prompt[:200]}. Professional lighting, smooth camera movement."
        clip2_path = _generate_video_clip_sync(simplified_clip2, pipeline_id, "clip2", size)

    if not clip2_path:
        # Last resort: duplicate clip1 to maintain 24-second duration
        logger.warning("Clip 2 failed completely. Duplicating clip1 to maintain 24s duration.")
        clip2_path = f"/tmp/{pipeline_id}_clip2.mp4"
        # Create a reversed version of clip1 for visual variation
        r = subprocess.run(
            [FFMPEG_PATH, "-y", "-i", clip1_path, "-vf", "reverse", "-af", "areverse", "-c:v", "libx264", "-preset", "fast", clip2_path],
            capture_output=True, timeout=60
        )
        if r.returncode != 0 or not os.path.exists(clip2_path):
            # If reverse fails, just copy clip1
            import shutil
            shutil.copy2(clip1_path, clip2_path)
            logger.warning("Reverse failed, using clip1 copy as clip2")

    # 3. Check for uploaded logo image
    logo_path = None
    try:
        pipeline = supabase.table("pipelines").select("result").eq("id", pipeline_id).single().execute()
        assets = pipeline.data.get("result", {}).get("uploaded_assets", []) if pipeline.data else []
        backend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        for asset in assets:
            url = asset.get("url", "") if isinstance(asset, dict) else str(asset)
            if url and any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                # Convert relative URL to absolute
                if url.startswith('/'):
                    url = f"{backend_url}{url}"
                logo_path = f"/tmp/{pipeline_id}_logo.png"
                urllib.request.urlretrieve(url, logo_path)
                logger.info(f"Downloaded logo for video: {url}")
                break
    except Exception as e:
        logger.warning(f"Could not fetch logo from pipeline: {e}")

    # Fallback: use default brand logo if no pipeline logo found
    if not logo_path or not os.path.exists(logo_path or ""):
        default_logo = "/app/backend/assets/brand_logo.png"
        if os.path.exists(default_logo):
            logo_path = default_logo
            logger.info("Using default brand logo from assets")

    # 4. Combine: crossfade + brand ending (logo/text + tagline + contact) + narration + music
    return _combine_commercial_video(clip1_path, clip2_path, audio_path, brand_name or "Brand", pipeline_id, logo_path, tagline, contact_cta, music_mood)


async def _generate_presenter_video(pipeline_id, marcos_output, avatar_url, size="1280x720", selected_music_override="", voice_config=None):
    """Generate a commercial with the avatar as a character IN the scene.
    1. Parse narration and clip prompts from marcos_output
    2. Enhance Sora prompts to include the avatar as an active character in each scene
    3. Generate 2 Sora clips with the avatar naturally in the campaign context
    4. Generate natural voiceover narration
    5. Combine clips + narration + music + brand ending
    """
    try:
        # Parse everything from Marcos's structured output
        narration_text = ""
        clip1_prompt = ""
        clip2_prompt = ""
        brand_name = ""
        tagline = ""
        contact_cta = ""
        music_mood = "corporate"

        narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===MUSIC DIRECTION===', marcos_output, re.IGNORECASE)
        if not narr_match:
            narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===(?:BRAND NAME|CTA SEQUENCE|VIDEO FORMAT)===', marcos_output, re.IGNORECASE)
        if narr_match:
            narration_text = narr_match.group(1).strip()
            narration_text = re.sub(r'\[\d+-\d+s?\]:\s*', '', narration_text)
            narration_text = re.sub(r'\[.*?SILENCE.*?\]', '', narration_text, flags=re.IGNORECASE)
            narration_text = re.sub(r'\[.*?music\s+only.*?\]', '', narration_text, flags=re.IGNORECASE)
            narration_text = re.sub(r'\[.*?logo\s+on\s+screen.*?\]', '', narration_text, flags=re.IGNORECASE)
            narration_text = re.sub(r'\[(?:COMPLETE|TOTAL|FULL)?\s*(?:SILENCE|QUIET|PAUSE|NO NARRATION).*?\]', '', narration_text, flags=re.IGNORECASE)
            narration_text = re.sub(r'\n{2,}', '\n', narration_text).strip()

        # Parse clip prompts
        c1_match = re.search(r'===CLIP 1.*?===([\s\S]*?)===CLIP 2', marcos_output, re.IGNORECASE)
        c2_match = re.search(r'===CLIP 2.*?===([\s\S]*?)===(?:NARRATION|MUSIC|CTA)', marcos_output, re.IGNORECASE)
        if c1_match:
            clip1_prompt = c1_match.group(1).strip()
        if c2_match:
            clip2_prompt = c2_match.group(1).strip()

        # Fallback: old format
        if not clip1_prompt:
            old_match = re.search(r'===VIDEO PROMPT===([\s\S]*?)===VIDEO FORMAT===', marcos_output, re.IGNORECASE)
            if old_match:
                clip1_prompt = old_match.group(1).strip()
                clip2_prompt = clip1_prompt
            else:
                clip1_prompt = marcos_output[:500]
                clip2_prompt = marcos_output[:500]

        cta_match = re.search(r'===CTA SEQUENCE===([\s\S]*?)===VIDEO FORMAT===', marcos_output, re.IGNORECASE)
        if cta_match:
            cta_block = cta_match.group(1)
            bl = re.search(r'Brand\s*name:\s*(.+)', cta_block, re.IGNORECASE)
            if bl: brand_name = bl.group(1).strip()
            tl = re.search(r'Tagline:\s*(.+)', cta_block, re.IGNORECASE)
            if tl: tagline = tl.group(1).strip()
            cl = re.search(r'Contact:\s*(.+)', cta_block, re.IGNORECASE)
            if cl: contact_cta = cl.group(1).strip()

        music_match = re.search(r'===MUSIC DIRECTION===([\s\S]*?)===(?:NARRATION TONE|CTA SEQUENCE)===', marcos_output, re.IGNORECASE)
        if music_match:
            ml = re.search(r'Mood:\s*(\w+)', music_match.group(1), re.IGNORECASE)
            if ml: music_mood = ml.group(1).strip().lower()

        if selected_music_override:
            music_mood = selected_music_override

        if not narration_text:
            logger.warning(f"No narration text found for presenter video {pipeline_id}")
            return None

        logger.info(f"Presenter video (scene mode): brand={brand_name}, music={music_mood}, avatar={avatar_url[:60]}...")

        # --- AVATAR IN SCENE: Enhance Sora prompts to include the avatar as a natural character ---
        avatar_scene_instruction = (
            "IMPORTANT: The main character in this scene is a real person (the brand presenter/ambassador). "
            "This person must appear naturally integrated into the scene — walking, gesturing, interacting with "
            "products and customers. Show them as confident, approachable, and professional. "
            "The person should be the FOCAL POINT of the scene, not just a bystander. "
            "Cinematic quality, natural movements, warm lighting, documentary-style camera work. "
            "The scene must feel REAL and NATURAL, not staged or robotic."
        )

        enhanced_clip1 = f"""{avatar_scene_instruction}

Scene description: {clip1_prompt}

Style: Cinematic commercial, smooth camera movements, natural lighting, 
professional color grading. The presenter moves naturally through the scene, 
engaging with the environment. Documentary-style, authentic feel."""

        enhanced_clip2 = f"""{avatar_scene_instruction}

Scene description: {clip2_prompt}

Style: Continuation of the same commercial. The presenter continues interacting 
naturally — demonstrating products, connecting with people, showcasing the brand. 
Smooth transition feel, same cinematic quality. Warm, inviting atmosphere."""

        # 1. Generate narration with natural tone (slightly slower for warmth)
        audio_path = await _generate_narration(narration_text, pipeline_id, max_duration=19.0, voice_config=voice_config)

        # 2. Generate Sora clips with avatar in scene
        logger.info(f"Generating Sora clip 1 with avatar in scene...")
        clip1_path = _generate_video_clip_sync(enhanced_clip1, pipeline_id, "clip1", size)
        if not clip1_path:
            logger.error(f"Presenter clip 1 failed for pipeline {pipeline_id}")
            return None

        logger.info(f"Generating Sora clip 2 with avatar in scene...")
        clip2_path = _generate_video_clip_sync(enhanced_clip2, pipeline_id, "clip2", size)
        if not clip2_path:
            logger.warning("Presenter clip 2 failed, retrying with simplified prompt...")
            simplified = f"Cinematic commercial continuation: professional presenter naturally interacting in {clip2_prompt[:200]}. Warm natural lighting, smooth camera."
            clip2_path = _generate_video_clip_sync(simplified, pipeline_id, "clip2", size)
            if not clip2_path:
                shutil.copy2(clip1_path, f"/tmp/{pipeline_id}_clip2.mp4")
                clip2_path = f"/tmp/{pipeline_id}_clip2.mp4"

        # 3. Compose final video: clip1 + clip2 + narration + music + brand ending
        # (Reuse the same composition logic as commercial video)
        output_path = f"/tmp/{pipeline_id}_commercial.mp4"
        FFMPEG = FFMPEG_PATH

        # Get clip durations
        clip1_dur = _ffprobe_duration(clip1_path) or 12.0
        clip2_dur = _ffprobe_duration(clip2_path) or 12.0
        total_clip_dur = clip1_dur + clip2_dur

        # Concatenate clips
        concat_path = f"/tmp/{pipeline_id}_concat.mp4"
        concat_list = f"/tmp/{pipeline_id}_concat.txt"
        with open(concat_list, "w") as f:
            f.write(f"file '{clip1_path}'\nfile '{clip2_path}'\n")
        subprocess.run(
            [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
             "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-an", concat_path],
            capture_output=True, timeout=120
        )
        if not os.path.exists(concat_path) or os.path.getsize(concat_path) < 1000:
            logger.error("Clip concatenation failed")
            return None

        # Add narration + background music
        music_dir = "/app/backend/assets/music"
        bg_music_path = None
        if os.path.isdir(music_dir):
            mood_map = {
                "upbeat": "upbeat.mp3", "energetic": "energetic.mp3", "emotional": "emotional.mp3",
                "cinematic": "cinematic.mp3", "corporate": "corporate.mp3", "luxury": "jazz_smooth.mp3",
                "modern": "electronic_chill.mp3", "fun": "pop_dance.mp3",
            }
            mood_file = mood_map.get(music_mood, "corporate.mp3")
            candidate = os.path.join(music_dir, mood_file)
            bg_music_path = candidate if os.path.exists(candidate) else os.path.join(music_dir, "corporate.mp3")
            if not os.path.exists(bg_music_path):
                bg_music_path = None

        inputs = ["-i", concat_path]
        filter_parts = []
        audio_streams = []

        if audio_path and os.path.exists(audio_path):
            inputs.extend(["-i", audio_path])
            audio_idx = 1
            filter_parts.append(f"[{audio_idx}:a]volume=1.2,apad=pad_dur={total_clip_dur}[voice]")
            audio_streams.append("[voice]")

            if bg_music_path:
                inputs.extend(["-i", bg_music_path])
                music_idx = audio_idx + 1
                fade_out_start = max(total_clip_dur - 3, 10)
                filter_parts.append(f"[{music_idx}:a]volume=0.08,afade=t=in:d=2,afade=t=out:st={fade_out_start}:d=3,atrim=0:{total_clip_dur}[music]")
                audio_streams.append("[music]")
                filter_parts.append(f"{''.join(audio_streams)}amix=inputs=2:duration=first:normalize=0[mixed]")
                final_audio = "[mixed]"
            else:
                final_audio = "[voice]"
        elif bg_music_path:
            inputs.extend(["-i", bg_music_path])
            fade_out_start = max(total_clip_dur - 3, 10)
            filter_parts.append(f"[1:a]volume=0.15,afade=t=in:d=2,afade=t=out:st={fade_out_start}:d=3,atrim=0:{total_clip_dur}[music]")
            final_audio = "[music]"
        else:
            final_audio = None

        if filter_parts and final_audio:
            filter_complex = ";".join(filter_parts)
            cmd = [FFMPEG, "-y"] + inputs + [
                "-filter_complex", filter_complex,
                "-map", "0:v", "-map", final_audio,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "256k",
                "-shortest", output_path
            ]
        else:
            cmd = [FFMPEG, "-y", "-i", concat_path, "-c", "copy", output_path]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            logger.warning(f"Final mix failed: {r.stderr[:300] if r.stderr else ''}")
            shutil.copy2(concat_path, output_path)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            with open(output_path, "rb") as f:
                video_bytes = f.read()
            filename = f"videos/{pipeline_id}_presenter.mp4"
            public_url = _upload_to_storage(video_bytes, filename, "video/mp4")
            logger.info(f"Presenter video (scene mode) uploaded: {filename} ({len(video_bytes)/1024:.0f}KB)")
            return public_url

    except Exception as e:
        logger.error(f"Presenter video (scene mode) failed: {e}")
        try:
            return await _generate_commercial_video(pipeline_id, marcos_output, size, selected_music_override, voice_config=voice_config)
        except Exception:
            pass
    return None


def _parse_ana_copy_selection(text):
    match = re.search(r'SELECTED_OPTION:\s*(\d)', text)
    return int(match.group(1)) if match else 1


def _parse_rafael_design_selections(text, platforms):
    selections = {}
    for p in platforms:
        match = re.search(rf'SELECTED_FOR_{p.upper()}:\s*(\d)', text)
        selections[p] = int(match.group(1)) if match else 1
    return selections


def _parse_review_decision(text):
    """Parse DECISION from reviewer output - robust detection"""
    # 1. Check explicit DECISION tag
    match = re.search(r'DECISION:\s*(APPROVED|REVISION_NEEDED|REJECTED)', text, re.IGNORECASE)
    if match:
        val = match.group(1).lower().replace(" ", "_")
        return "revision_needed" if val in ("revision_needed", "rejected") else "approved"

    # 2. Detect implicit rejection signals (critical errors found by reviewer)
    rejection_signals = [
        r'PROBLEMA\s+CR[ÍI]TICO',
        r'CRITICAL\s+PROBLEM',
        r'IDIOMA\s+INCORRECTO|IDIOMA\s+INCORRETO|WRONG\s+LANGUAGE',
        r'REJECTED|REJEITADO|RECHAZADO',
        r'REVISION\s*NEEDED|REVIS[AÃ]O\s+NECESS[AÁ]RIA',
        r'LANGUAGE\s+MISMATCH|LANGUAGE\s+ERROR',
        r'FUNDAMENTAL\s+ERROR|ERRO\s+FUNDAMENTAL',
        r'INVALIDATES?\s+(THE\s+)?CAMPAIGN|INVALIDA\s+(A\s+)?CAMPANHA',
        r'MUST\s+BE\s+REDONE|DEVE\s+SER\s+REFEITO',
        r'SCORE.*?[0-4]/10',  # Very low score
    ]
    text_upper = text.upper()
    for pattern in rejection_signals:
        if re.search(pattern, text_upper, re.IGNORECASE):
            return "revision_needed"

    # 3. Fallback: assume approved if no rejection signals
    return "approved"


def _extract_revision_feedback(text):
    """Extract revision feedback from reviewer output"""
    # Try explicit tag first
    match = re.search(r'REVISION_FEEDBACK:\s*([\s\S]*?)(?=\n\n(?:DECISION|SELECTED)|$)', text, re.IGNORECASE)
    if match and match.group(1).strip():
        return match.group(1).strip()

    # Try to extract the critical problem description
    problem_match = re.search(r'(?:PROBLEMA\s+CR[ÍI]TICO|CRITICAL\s+PROBLEM)[:\s]*([\s\S]*?)(?=\n\n|\n[A-Z]{3,}|\Z)', text, re.IGNORECASE)
    if problem_match and problem_match.group(1).strip():
        return problem_match.group(1).strip()

    # Extract any section mentioning errors or issues
    error_match = re.search(r'(?:ERRORS?|ISSUES?|PROBLEMAS?)[:\s]*([\s\S]*?)(?=\n\n[A-Z]|\Z)', text, re.IGNORECASE)
    if error_match and error_match.group(1).strip():
        return error_match.group(1).strip()

    return "Quality issues detected. Please improve the copy/design quality, ensure correct language, and fix all identified problems."


def _build_prompt(step, pipeline):
    briefing = pipeline["briefing"]
    platforms = pipeline.get("platforms") or []
    platforms_str = ", ".join(platforms)
    steps = pipeline.get("steps") or {}
    ctx = pipeline.get("result", {}).get("context", {})
    contact = pipeline.get("result", {}).get("contact_info", {})
    assets = pipeline.get("result", {}).get("uploaded_assets", [])
    campaign_lang = pipeline.get("result", {}).get("campaign_language", "")

    LANG_NAMES = {"pt": "Portuguese (Brazilian)", "en": "English", "es": "Spanish", "fr": "French", "ht": "Haitian Creole"}
    lang_instruction = ""
    if campaign_lang:
        lang_name = LANG_NAMES.get(campaign_lang, campaign_lang)
        lang_instruction = f"""

=== MANDATORY LANGUAGE RULE (NON-NEGOTIABLE) ===
The campaign language is: **{lang_name}** (code: {campaign_lang})
EVERY piece of text you produce MUST be in {lang_name}:
- ALL headlines, titles, CTAs, taglines, hashtags → {lang_name}
- ALL image headline text that will appear ON the image → {lang_name}
- ALL narration scripts → {lang_name}
- ALL copy variations → {lang_name}
This overrides your default language. Even if the briefing is written in another language, your OUTPUT must be in {lang_name}.
VIOLATION = AUTOMATIC REJECTION. No exceptions.
=== END LANGUAGE RULE ==="""

    ctx_str = ""
    if ctx:
        parts = []
        if ctx.get("company"): parts.append(f"Company: {ctx['company']}")
        if ctx.get("industry"): parts.append(f"Industry: {ctx['industry']}")
        if ctx.get("audience"): parts.append(f"Target audience: {ctx['audience']}")
        if ctx.get("brand_voice"): parts.append(f"Brand voice: {ctx['brand_voice']}")
        if ctx.get("website_url"): parts.append(f"Company website (use as reference): {ctx['website_url']}")
        ctx_str = "\n".join(parts)

    contact_str = ""
    if contact:
        cparts = []
        if contact.get("phone"):
            phone_str = f"Phone: {contact['phone']}"
            if contact.get("is_whatsapp"): phone_str += " (also WhatsApp)"
            cparts.append(phone_str)
        if contact.get("website"): cparts.append(f"Website: {contact['website']}")
        if contact.get("email"): cparts.append(f"Email: {contact['email']}")
        if contact.get("address"): cparts.append(f"Address: {contact['address']}")
        if cparts:
            contact_str = "\nContact information to include in the campaign:\n" + "\n".join(cparts)

    # Build media format instructions from selected platforms
    media_formats = pipeline.get("result", {}).get("media_formats", {})
    format_str = ""
    if media_formats:
        # Find the primary image and video sizes
        img_sizes = set()
        vid_sizes = set()
        for pid_fmt, fmt in media_formats.items():
            if fmt.get("imgSize"): img_sizes.add(fmt["imgSize"])
            if fmt.get("vidSize"): vid_sizes.add(fmt["vidSize"])
        if img_sizes:
            format_str += f"\nIMAGE FORMAT REQUIREMENTS: Generate images for these sizes: {', '.join(img_sizes)}. Primary size: {list(img_sizes)[0]}."
        if vid_sizes:
            format_str += f"\nVIDEO FORMAT REQUIREMENTS: The commercial video should target: {', '.join(vid_sizes)}."

    assets_str = ""
    if assets:
        exact_assets = [a for a in assets if a.get("type") == "exact"]
        ref_assets = [a for a in assets if a.get("type") == "reference"]
        aparts = []
        if exact_assets:
            exact_urls = [a.get("url", "") for a in exact_assets]
            aparts.append(f"EXACT PRODUCT PHOTOS ({len(exact_assets)} file(s)): {', '.join(exact_urls)}\n"
                          f"CRITICAL: These are REAL product photos. The campaign images MUST feature these EXACT products — "
                          f"do NOT create generic/fictional versions. You may describe professional editing (background removal, "
                          f"studio lighting, color correction) but the product itself must be the one from the photos.")
        if ref_assets:
            aparts.append(f"Reference images have been uploaded ({len(ref_assets)} file(s)). Use these as visual inspiration and style reference for the campaign designs.")
        if aparts:
            assets_str = "\nUploaded assets:\n" + "\n".join(aparts)

    if step == "sofia_copy":
        revision_info = ""
        revision_fb = steps.get("sofia_copy", {}).get("revision_feedback")
        prev_output = steps.get("sofia_copy", {}).get("previous_output")
        if revision_fb and prev_output:
            round_num = steps.get("sofia_copy", {}).get("revision_round", 1)
            revision_info = f"""

--- REVISION REQUEST (Round {round_num}/2) ---
The Creative Director reviewed your work and requested changes.

YOUR PREVIOUS OUTPUT:
{prev_output}

REVIEWER'S FEEDBACK:
{revision_fb}

IMPORTANT: Revise ALL 3 variations addressing EVERY point in the reviewer's feedback. Maintain the same format (===VARIATION 1===, etc.). Make each variation significantly better."""

        return f"""{lang_instruction}

Create 3 campaign copy variations for the following briefing.
Target platforms: {platforms_str}

Briefing: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}
{format_str}
{assets_str}
{revision_info}

{lang_instruction}

FINAL REMINDER: The briefing above may be written in ANY language. That does NOT matter. Your OUTPUT must be ENTIRELY in the language specified at the top of this prompt. Every word, headline, CTA, hashtag — ALL in that language. Zero exceptions.

Remember: Create EXACTLY 3 variations formatted with ===VARIATION 1===, ===VARIATION 2===, ===VARIATION 3==="""

    elif step == "ana_review_copy":
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        revision_count = steps.get("ana_review_copy", {}).get("revision_count", 0)
        revision_context = ""
        if revision_count > 0:
            revision_context = f"\n\nNOTE: This is REVISION ROUND {revision_count}. The copywriter has revised their work based on your previous feedback. Review the revised versions with the same critical eye, but acknowledge improvements."

        return f"""Review these 3 copy variations created by David for the following campaign:

Briefing: {briefing}
Platforms: {platforms_str}
{lang_instruction}

David's variations:
{sofia_output}
{revision_context}

CRITICAL: The CAMPAIGN_LANGUAGE is specified above. Verify that ALL content matches this language. If the briefing was written in a different language, that's OK — what matters is that David's OUTPUT is in the correct CAMPAIGN_LANGUAGE.

Analyze each variation on the criteria in your instructions.
Then make your DECISION: APPROVED (with SELECTED_OPTION) or REVISION_NEEDED (with REVISION_FEEDBACK)."""

    elif step == "lucas_design":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        if not approved_copy:
            approved_copy = steps.get("ana_review_copy", {}).get("output", "")

        # Extract Sofia's image briefing from her output
        sofia_full_output = steps.get("sofia_copy", {}).get("output", "")
        image_briefing = ""
        briefing_match = re.search(r'===IMAGE BRIEFING===([\s\S]*?)$', sofia_full_output, re.IGNORECASE)
        if briefing_match:
            image_briefing = briefing_match.group(1).strip()

        # Check if Ana had notes on the image briefing
        ana_image_notes = ""
        ana_output = steps.get("ana_review_copy", {}).get("output", "")
        notes_match = re.search(r'IMAGE_BRIEFING_NOTES:\s*([\s\S]*?)(?=\n\n|$)', ana_output, re.IGNORECASE)
        if notes_match and "approved" not in notes_match.group(1).lower():
            ana_image_notes = f"\n\nAna's notes on the image briefing:\n{notes_match.group(1).strip()}"

        revision_info = ""
        revision_fb = steps.get("lucas_design", {}).get("revision_feedback")
        prev_output = steps.get("lucas_design", {}).get("previous_output")
        if revision_fb and prev_output:
            round_num = steps.get("lucas_design", {}).get("revision_round", 1)
            revision_info = f"""

--- REVISION REQUEST (Round {round_num}/2) ---
The Art Director reviewed your designs and requested changes.

YOUR PREVIOUS PROMPTS:
{prev_output}

ART DIRECTOR'S FEEDBACK:
{revision_fb}

IMPORTANT: Revise ALL 3 image prompts addressing EVERY point in the art director's feedback. Make each prompt significantly more impactful."""

        # Get exact photos info for Stefan
        exact_assets = [a for a in assets if a.get("type") == "exact"]
        exact_photo_instruction = ""
        if exact_assets:
            exact_photo_instruction = f"""
EXACT PRODUCT PHOTOS PROVIDED: {len(exact_assets)} photo(s)
CRITICAL RULE: The client uploaded REAL product photos. Your prompts for designs #{', #'.join([str(i+1) for i in range(min(len(exact_assets), 3))])} MUST describe how to EDIT the real product photo — NOT generate a new product from scratch.
For these designs, write EDITING INSTRUCTIONS: describe the background, lighting, composition, and styling to apply to the EXISTING product photo.
Example: "The existing [product] photographed in a premium studio setting with soft gradient backdrop, dramatic rim lighting, golden hour tones..."
For any remaining designs beyond the exact photos count, you may create fully new concepts."""

        return f"""Transform David's IMAGE BRIEFING into 3 optimized AI image generation prompts.
Target platforms: {platforms_str}

DAVID'S IMAGE BRIEFING:
{image_briefing if image_briefing else "(No explicit briefing found. Use the approved copy and original briefing to create visual concepts.)"}
{ana_image_notes}

APPROVED CAMPAIGN COPY (for context):
{approved_copy}

ORIGINAL BRIEFING: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}
{format_str}
{assets_str}
{exact_photo_instruction}
{revision_info}

YOUR TASK: Create 3 IMAGE GENERATION PROMPTS based on David's visual concepts.
Each prompt MUST:
1. Include the HEADLINE TEXT from David's briefing exactly as written (3-7 words, in the campaign language)
2. Be 80-120 words of HYPER-SPECIFIC visual description
3. Include: subject, setting, lighting, camera angle, color palette, mood, art style
4. End with: "Ultra high-quality, 4K commercial photography. NO logos, NO brand names, NO website URLs."
5. If IMAGE FORMAT REQUIREMENTS were provided above, adapt each prompt's aspect ratio description accordingly (e.g., "vertical portrait composition" for 9:16, "landscape panoramic" for 16:9, "square centered" for 1:1).
6. If EXACT PRODUCT PHOTOS are provided, the first {len(exact_assets)} design(s) MUST be EDITING INSTRUCTIONS for the real photos — describe the treatment, background, and styling, NOT a new product.

CRITICAL LANGUAGE RULE: ALL text that appears in the image (headlines, overlays, CTAs) MUST be in the SAME language as the approved campaign copy. If the copy is in English, the image headline MUST be in English. If in Portuguese, in Portuguese. NEVER mix languages between copy and image text — this destroys campaign coherence.
{lang_instruction}

Format:
===DESIGN 1===
Concept: [name]
Image Prompt: [complete optimized prompt]
===DESIGN 2===
...
===DESIGN 3===
..."""

    elif step == "rafael_review_design":
        lucas_output = steps.get("lucas_design", {}).get("output", "")
        revision_count = steps.get("rafael_review_design", {}).get("revision_count", 0)
        revision_context = ""
        if revision_count > 0:
            revision_context = f"\n\nNOTE: This is REVISION ROUND {revision_count}. The designer has revised their concepts based on your previous art direction feedback. Review with the same world-class standards, but acknowledge improvements."

        return f"""Review these 3 design concepts created by Stefan.
Target platforms: {platforms_str}

Design concepts:
{lucas_output}
{revision_context}

CRITICAL LANGUAGE CHECK: Verify that ALL text/headlines in the image prompts are in the SAME language as the campaign copy. The CAMPAIGN_LANGUAGE specified below is the ABSOLUTE truth. If the campaign copy is in English, ALL image text must be in English. If in Portuguese, ALL in Portuguese. Language mismatch is an AUTOMATIC REJECTION.
{lang_instruction}

Evaluate each concept using your art direction criteria.
Then make your DECISION: APPROVED (with SELECTED_FOR_[PLATFORM] lines) or REVISION_NEEDED (with REVISION_FEEDBACK).

If approving, end with:
{chr(10).join(f'SELECTED_FOR_{p.upper()}: [1, 2, or 3]' for p in platforms)}"""

    elif step == "marcos_video":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        image_briefing = ""
        video_brief = ""
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        briefing_match = re.search(r'===IMAGE BRIEFING===([\s\S]*?)===VIDEO BRIEF===', sofia_output, re.IGNORECASE)
        if briefing_match:
            image_briefing = briefing_match.group(1).strip()
        else:
            briefing_match = re.search(r'===IMAGE BRIEFING===([\s\S]*?)$', sofia_output, re.IGNORECASE)
            if briefing_match:
                image_briefing = briefing_match.group(1).strip()
        video_brief_match = re.search(r'===VIDEO BRIEF===([\s\S]*?)$', sofia_output, re.IGNORECASE)
        if video_brief_match:
            video_brief = video_brief_match.group(1).strip()
        campaign_name = pipeline.get("result", {}).get("campaign_name", "Brand")
        contact_info = pipeline.get("result", {}).get("contact_info", {})
        contact_details = ""
        if contact_info:
            parts = []
            if contact_info.get("whatsapp"): parts.append(f"WhatsApp: {contact_info['whatsapp']}")
            if contact_info.get("phone"): parts.append(f"Phone: {contact_info['phone']}")
            if contact_info.get("website"): parts.append(f"Website: {contact_info['website']}")
            if contact_info.get("email"): parts.append(f"Email: {contact_info['email']}")
            if contact_info.get("address"): parts.append(f"Address: {contact_info['address']}")
            contact_details = " | ".join(parts)

        # Get video format from media_formats — choose based on majority of target platforms
        vid_format_note = ""
        mf = pipeline.get("result", {}).get("media_formats", {})
        if mf:
            vertical_count = 0
            horizontal_count = 0
            all_vid_sizes = {}
            for plat, p_fmt in mf.items():
                vs = p_fmt.get("vidSize", "")
                if vs:
                    all_vid_sizes[plat] = vs
                    ratio = p_fmt.get("vidRatio", "")
                    if ratio == "9:16":
                        vertical_count += 1
                    else:
                        horizontal_count += 1
            # Choose primary format based on majority
            if vertical_count > horizontal_count:
                primary_format = "vertical"
                primary_size = "720x1280"
            else:
                primary_format = "horizontal"
                primary_size = "1280x720"
            vid_format_note = f"""
VIDEO FORMAT REQUIREMENT:
- Primary format: {primary_format.upper()} ({primary_size})
- Target platforms requiring vertical (9:16): {', '.join([p for p,f in mf.items() if f.get('vidRatio') == '9:16'])}
- Target platforms requiring horizontal (16:9): {', '.join([p for p,f in mf.items() if f.get('vidRatio') == '16:9'])}
- Your video will be generated at {primary_size}. Choose your format accordingly: set Format to '{primary_format}' in your output.
- Compose your shots to work well in {primary_format} format. Keep subjects centered for easy cropping to other formats."""

        # Check for revision feedback from rafael_review_video
        revision_info = ""
        revision_fb = steps.get("marcos_video", {}).get("revision_feedback")
        prev_output = steps.get("marcos_video", {}).get("previous_output")
        if revision_fb and prev_output:
            round_num = steps.get("marcos_video", {}).get("revision_round", 1)
            revision_info = f"""

--- VIDEO REVISION REQUEST (Round {round_num}) ---
The Video Director reviewed your script and requested changes.

YOUR PREVIOUS OUTPUT:
{prev_output}

DIRECTOR'S FEEDBACK:
{revision_fb}

IMPORTANT: Address EVERY point in the director's feedback. Maintain the same output format."""

        # Get avatar and brand info for video scene composition
        avatar_url = pipeline.get("result", {}).get("avatar_url", "")
        video_mode = pipeline.get("result", {}).get("video_mode", "narration")
        brand_data = pipeline.get("result", {}).get("brand_data", None)
        apply_brand = pipeline.get("result", {}).get("apply_brand", False)
        uploaded_assets = pipeline.get("result", {}).get("uploaded_assets", [])
        exact_photos = [a for a in uploaded_assets if a.get("type") == "exact"]

        avatar_instruction = ""
        if avatar_url:
            avatar_instruction = f"""
AVATAR/PRESENTER INSTRUCTION:
- An avatar/presenter has been created for this campaign. Image: {avatar_url}
- The video MUST feature this person as the main character/presenter in the scenes
- Show the avatar ACTIVELY INTERACTING: demonstrating the product, talking to customers, presenting services
- The avatar should be IN the scene (not just standing still) — walking, gesturing, showcasing
- Make the scenes dynamic: the avatar engages with the environment and products naturally"""

        exact_photos_instruction = ""
        if exact_photos:
            photo_urls = [a.get("url", "") for a in exact_photos[:3]]
            exact_photos_instruction = f"""
EXACT PRODUCT PHOTOS:
- The client provided exact product photos that MUST appear in the video scenes: {', '.join(photo_urls)}
- These are real products — the video must showcase EXACTLY these items (not generic versions)
- Show the products being used, demonstrated, or displayed prominently in the commercial scenes"""

        brand_overlay_instruction = ""
        if apply_brand and brand_data:
            brand_overlay_instruction = f"""
BRAND OVERLAY:
- Company: {brand_data.get('company_name', '')}
- Logo URL: {brand_data.get('logo_url', '')}
- Phone: {brand_data.get('phone', '')} {'(WhatsApp)' if brand_data.get('is_whatsapp') else ''}
- Website: {brand_data.get('website_url', '')}
- Use this brand info in the CTA ending sequence"""

        return f"""Create a 24-second commercial video (TWO 12-second clips with perfect continuity) for this campaign.

Brand/Company: {campaign_name}
Platforms: {platforms_str}
Approved campaign copy: {approved_copy}
Visual direction: {image_briefing}
Video brief from David: {video_brief}
Contact info for CTA: {contact_details or contact_str}
Original briefing: {briefing}
{vid_format_note}
{lang_instruction}
{avatar_instruction}
{exact_photos_instruction}
{brand_overlay_instruction}
{revision_info}

REQUIREMENTS:
1. Design TWO clips that feel like ONE continuous shot — same character, same visual style, seamless transition
2. Write a DYNAMIC commercial narration script for the full 24 seconds with timing marks — urgent, exciting, creates FOMO
3. The final 3 seconds: clean dark background for brand logo "{campaign_name}" + tagline + contact CTA
4. Choose the right MUSIC MOOD that amplifies the commercial's emotional arc
5. The narration and all text must be in the SAME LANGUAGE as the campaign copy above
6. Include the contact info in the CTA SEQUENCE for the video ending overlay
7. If an avatar/presenter is provided, they MUST be the main character in every scene — actively interacting, not just standing

Output EXACTLY in the format specified in your instructions."""

    elif step == "rafael_review_video":
        marcos_output = steps.get("marcos_video", {}).get("output", "")
        video_url = steps.get("marcos_video", {}).get("video_url", "")
        briefing_summary = steps.get("sofia_copy", {}).get("output", "")[:500]
        return f"""Review the video commercial created by Ridley for this campaign.

Campaign briefing summary: {briefing_summary}

Ridley's video script and concept:
{marcos_output}

Video generated: {"YES - " + video_url if video_url else "NO - Video generation failed or pending"}

Platforms: {platforms_str}
{lang_instruction}

Review EVERY aspect:
1. Is the narration script in the CORRECT campaign language?
2. Are the clip descriptions compelling and on-brand?
3. Is the emotional arc effective (Hook → Story → CTA)?
4. Is the timing appropriate for a 24-second commercial?
5. Does the CTA have the correct contact information?
6. Is the music direction appropriate for the target audience?
7. AUDIO QUALITY CHECK: Is the music mood compatible with the campaign industry? A mismatch (e.g., energetic music for a spa brand) creates an unprofessional result. Flag any mood/industry mismatch.
8. NARRATION LENGTH CHECK: The narration MUST end by second 19. Count the words — if the narration exceeds 60 words, it's TOO LONG and will overlap with the brand ending. Flag and request trimming.
9. Is the contact CTA text clean and without placeholder text like "(display number)" or "[insert here]"? Real contact info must be present.

Provide your detailed score (V1-V6) and DECISION."""

    elif step == "pedro_publish":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        design_approvals = steps.get("rafael_review_design", {}).get("selections", {})
        rafael_design_output = steps.get("rafael_review_design", {}).get("output", "")
        video_info = steps.get("marcos_video", {}).get("output", "")
        has_video = bool(steps.get("marcos_video", {}).get("video_url"))
        video_note = "\nA commercial video has been generated for this campaign." if has_video else "\nNo video was generated for this campaign."
        return f"""Validate this complete campaign package before marking it as CREATED.

Platforms: {platforms_str}

APPROVED COPY:
{approved_copy}

DESIGN REVIEW & APPROVALS:
{rafael_design_output}
Platform selections: {design_approvals}

VIDEO CONCEPT:
{video_info}{video_note}

ORIGINAL BRIEFING:
{briefing}
{contact_str}
{lang_instruction}

Perform your validation following the criteria in your system prompt.
Output your CAMPAIGN VALIDATION REPORT with scores and FINAL VERDICT.
Include RECOMMENDATIONS FOR TRAFFIC TEAM at the end — strategic notes for James (Chief Traffic Manager) and the channel specialists (Emily for Meta, Ryan for TikTok, Sarah for Messaging, Mike for Google Ads)."""

    return briefing


async def _execute_step(pipeline_id, step):
    """Execute a single pipeline step using AI"""
    pipeline = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    if not pipeline:
        return
    pipeline = pipeline[0]
    steps = pipeline.get("steps") or {}

    # Enterprise check only for the publish step
    if step == "pedro_publish":
        tenant = supabase.table("tenants").select("plan").eq("id", pipeline["tenant_id"]).execute()
        if tenant.data and tenant.data[0].get("plan") != "enterprise":
            steps[step] = steps.get(step, {})
            steps[step]["status"] = "requires_upgrade"
            steps[step]["error"] = "O plano Enterprise e necessario para publicar campanhas. Faca upgrade para desbloquear."
            supabase.table("pipelines").update({
                "steps": steps, "status": "requires_upgrade", "current_step": step,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
            return

    # Mark step as running
    steps[step] = steps.get(step, {})
    steps[step]["status"] = "running"
    steps[step]["started_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("pipelines").update({
        "steps": steps, "current_step": step, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    try:
        prompt = _build_prompt(step, pipeline)
        system = STEP_SYSTEMS.get(step, "")

        # Creative agents use Claude Sonnet 4.5 for quality
        # Review agents use Gemini Flash for SPEED (reviews don't need creative generation)
        # This cuts review time from ~60s to ~10s each
        STEP_MODELS = {
            "sofia_copy": ("anthropic", "claude-sonnet-4-5-20250929"),
            "ana_review_copy": ("gemini", "gemini-2.0-flash"),
            "lucas_design": ("anthropic", "claude-sonnet-4-5-20250929"),
            "rafael_review_design": ("gemini", "gemini-2.0-flash"),
            "marcos_video": ("anthropic", "claude-sonnet-4-5-20250929"),
            "rafael_review_video": ("gemini", "gemini-2.0-flash"),
            "pedro_publish": ("gemini", "gemini-2.0-flash"),
        }
        provider, model = STEP_MODELS.get(step, ("anthropic", "claude-sonnet-4-5-20250929"))

        # Execute with strict timeout per attempt
        response = None
        last_error = None
        # Review steps (Gemini Flash) are fast — use shorter timeout and fewer retries
        is_review = step in ("ana_review_copy", "rafael_review_design", "rafael_review_video", "pedro_publish")
        timeout_per_attempt = 30 if is_review else 75
        # Only 1 attempt for primary model before fallback (avoids long waits on 502 errors)
        max_attempts = 1

        for attempt in range(max_attempts):
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-{int(time.time())}-{attempt}",
                    system_message=system
                ).with_model(provider, model)

                start = time.time()
                response = await asyncio.wait_for(
                    chat.send_message(UserMessage(text=prompt)),
                    timeout=timeout_per_attempt
                )
                elapsed = round((time.time() - start) * 1000)
                break
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Step {step} timed out after {timeout_per_attempt}s on attempt {attempt+1}")
                logger.warning(f"Pipeline step {step} attempt {attempt+1} timed out after {timeout_per_attempt}s")
            except Exception as retry_err:
                last_error = retry_err
                logger.warning(f"Pipeline step {step} attempt {attempt+1} failed: {retry_err}")

            if attempt < max_attempts - 1:
                await asyncio.sleep(2)

        # Fallback to Gemini Flash if Claude failed (for creative steps)
        if response is None and provider == "anthropic":
            logger.info(f"Claude failed for {step}, falling back to gemini-2.0-flash")
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-fallback-{int(time.time())}",
                    system_message=system
                ).with_model("gemini", "gemini-2.0-flash")
                start = time.time()
                response = await asyncio.wait_for(
                    chat.send_message(UserMessage(text=prompt)),
                    timeout=timeout_per_attempt
                )
                elapsed = round((time.time() - start) * 1000)
            except Exception as fb_err:
                logger.error(f"Fallback also failed for {step}: {fb_err}")

        if response is None:
            raise last_error

        steps[step]["output"] = response
        steps[step]["status"] = "completed"
        steps[step]["completed_at"] = datetime.now(timezone.utc).isoformat()
        steps[step]["elapsed_ms"] = elapsed

        # For reviewer steps: parse decision and handle revision loop
        # MAX_REVISIONS = 1: Only 1 revision allowed per review step for speed.
        # The initial prompt is strong enough that 1 revision should fix most issues.
        MAX_REVISIONS = 1

        if step == "ana_review_copy":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < MAX_REVISIONS:
                # Revision loop - send back to David
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"Lee requested revision {revision_count + 1}/{MAX_REVISIONS} for pipeline {pipeline_id}")

                # Prepare Sofia for re-run
                prev_sofia_output = steps.get("sofia_copy", {}).get("output", "")
                steps["sofia_copy"]["previous_output"] = prev_sofia_output
                steps["sofia_copy"]["revision_feedback"] = revision_feedback
                steps["sofia_copy"]["revision_round"] = revision_count + 1
                steps["sofia_copy"]["status"] = "pending"

                supabase.table("pipelines").update({
                    "steps": steps, "status": "running", "current_step": "sofia_copy",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                await _execute_step(pipeline_id, "sofia_copy")
                return  # Skip normal next-step flow

            # Approved (or max revisions reached) - parse selection
            if decision == "revision_needed" and revision_count >= MAX_REVISIONS:
                logger.warning(f"Max revisions ({MAX_REVISIONS}) reached for ana_review_copy, auto-approving pipeline {pipeline_id}")
            steps[step]["decision"] = "approved"
            selected = _parse_ana_copy_selection(response)
            steps[step]["auto_selection"] = selected
            sofia_output = steps.get("sofia_copy", {}).get("output", "")

            # Strip IMAGE BRIEFING section from Sofia's output before parsing variations
            copy_only = re.split(r'===\s*IMAGE BRIEFING\s*===', sofia_output, flags=re.IGNORECASE)[0]

            variations = re.split(r'===\s*VARIATION \d+\s*===', copy_only)
            variations = [v.strip() for v in variations[1:] if v.strip()]

            if variations and 0 < selected <= len(variations):
                steps[step]["approved_content"] = variations[selected - 1]
            elif variations:
                steps[step]["approved_content"] = variations[0]
            else:
                steps[step]["approved_content"] = copy_only.strip()

        elif step == "rafael_review_design":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < MAX_REVISIONS:
                # Revision loop - send back to Lucas
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"George requested design revision {revision_count + 1}/{MAX_REVISIONS} for pipeline {pipeline_id}")

                prev_lucas_output = steps.get("lucas_design", {}).get("output", "")
                steps["lucas_design"]["previous_output"] = prev_lucas_output
                steps["lucas_design"]["revision_feedback"] = revision_feedback
                steps["lucas_design"]["revision_round"] = revision_count + 1
                steps["lucas_design"]["status"] = "pending"

                supabase.table("pipelines").update({
                    "steps": steps, "status": "running", "current_step": "lucas_design",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                await _execute_step(pipeline_id, "lucas_design")
                return

            if decision == "revision_needed" and revision_count >= MAX_REVISIONS:
                logger.warning(f"Max revisions ({MAX_REVISIONS}) reached for rafael_review_design, auto-approving pipeline {pipeline_id}")
            steps[step]["decision"] = "approved"
            platforms = pipeline.get("platforms") or []
            selections = _parse_rafael_design_selections(response, platforms)
            steps[step]["auto_selections"] = selections
            steps[step]["selections"] = selections

        elif step == "rafael_review_video":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < MAX_REVISIONS:
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"Roger requested video revision {revision_count + 1}/{MAX_REVISIONS} for pipeline {pipeline_id}")

                prev_marcos_output = steps.get("marcos_video", {}).get("output", "")
                steps["marcos_video"]["previous_output"] = prev_marcos_output
                steps["marcos_video"]["revision_feedback"] = revision_feedback
                steps["marcos_video"]["revision_round"] = revision_count + 1
                steps["marcos_video"]["status"] = "pending"

                supabase.table("pipelines").update({
                    "steps": steps, "status": "running", "current_step": "marcos_video",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                await _execute_step(pipeline_id, "marcos_video")
                return

            if decision == "revision_needed" and revision_count >= MAX_REVISIONS:
                logger.warning(f"Max revisions ({MAX_REVISIONS}) reached for rafael_review_video, auto-approving pipeline {pipeline_id}")
            steps[step]["decision"] = "approved"

        # Generate actual images for Lucas's design step
        elif step == "lucas_design":
            platforms = pipeline.get("platforms") or []
            # Update DB to show we're generating images now
            steps[step]["output"] = response
            steps[step]["status"] = "generating_images"
            supabase.table("pipelines").update({
                "steps": steps,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()

            image_urls, image_prompts = await _generate_design_images(
                pipeline_id, response, platforms
            )
            steps[step]["image_urls"] = image_urls
            steps[step]["image_prompts"] = image_prompts

            # Create platform-specific variants (TikTok 9:16, Google Ads 16:9, etc.)
            try:
                platform_variants = await _create_platform_variants(pipeline_id, image_urls, platforms)
                steps[step]["platform_variants"] = platform_variants
                logger.info(f"Created platform variants for {len(platform_variants)} platforms")
            except Exception as pv_err:
                logger.warning(f"Platform variant creation failed: {pv_err}")
                steps[step]["platform_variants"] = {}

            steps[step]["status"] = "completed"

        # Generate video for Marcos's video step
        elif step == "marcos_video":
            # Check skip_video flag
            skip_video = pipeline.get("result", {}).get("skip_video", False)
            if skip_video:
                logger.info(f"Skipping video generation for pipeline {pipeline_id} (skip_video=True)")
                steps[step]["output"] = response
                steps[step]["status"] = "completed"
                steps[step]["video_url"] = None
                steps[step]["video_format"] = "horizontal"
                steps[step]["video_duration"] = 0
                steps[step]["skipped"] = True
            else:
                # Validate narration script language before generating
                camp_lang = pipeline.get("result", {}).get("campaign_language", "")
                if camp_lang:
                    narr_match = re.search(r'===NARRATION SCRIPT===([\s\S]*?)===', response, re.IGNORECASE)
                    if not narr_match:
                        narr_match = re.search(r'NARRATION SCRIPT[:\s]*([\s\S]*?)(?:===|MUSIC DIRECTION)', response, re.IGNORECASE)
                    if narr_match:
                        narr_text = narr_match.group(1).strip()
                        LANG_NAMES_V = {"pt": "Portuguese", "en": "English", "es": "Spanish", "fr": "French"}
                        expected_lang = LANG_NAMES_V.get(camp_lang, camp_lang)
                        logger.info(f"Video narration language validation: expected={expected_lang}, checking script ({len(narr_text)} chars)")

                # Parse video format from output
                video_format = "horizontal"
                format_match = re.search(r'Format:\s*(vertical|horizontal)', response, re.IGNORECASE)
                if format_match:
                    video_format = format_match.group(1).lower()

                platforms = pipeline.get("platforms") or []
                # Sora 2 valid sizes: 720x1280, 1280x720
                FORMAT_MAP = {"vertical": "720x1280", "horizontal": "1280x720"}
                if not format_match:
                    if any(p in platforms for p in ["tiktok", "instagram", "whatsapp"]):
                        video_format = "vertical"
                    elif any(p in platforms for p in ["google_ads", "facebook"]):
                        video_format = "horizontal"
                size = FORMAT_MAP.get(video_format, "1280x720")

                # Update status to generating_video
                steps[step]["output"] = response
                steps[step]["status"] = "generating_video"
                supabase.table("pipelines").update({
                    "steps": steps,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", pipeline_id).execute()

                # Generate the full commercial
                user_music = pipeline.get("result", {}).get("selected_music", "")
                video_mode = pipeline.get("result", {}).get("video_mode", "narration")
                avatar_url = pipeline.get("result", {}).get("avatar_url", "")
                avatar_voice = pipeline.get("result", {}).get("avatar_voice", None)

                if video_mode == "presenter" and avatar_url:
                    # Presenter mode: talking head with lip-sync via fal.ai
                    video_url = await _generate_presenter_video(pipeline_id, response, avatar_url, size, user_music, voice_config=avatar_voice)
                else:
                    # Narration mode: 2 Sora clips + TTS narration (original behavior)
                    video_url = await _generate_commercial_video(pipeline_id, response, size, selected_music_override=user_music, voice_config=avatar_voice)
                steps[step]["video_url"] = video_url
                steps[step]["video_format"] = video_format
                steps[step]["video_duration"] = 24
                steps[step]["video_size"] = size

                # Generate per-channel video variants (crop/resize from master)
                if video_url:
                    try:
                        video_variants = await _create_video_variants(pipeline_id, video_url, video_format, pipeline.get("platforms", []))
                        steps[step]["video_variants"] = video_variants
                        logger.info(f"Created video variants for {len(video_variants)} platforms")
                    except Exception as vv_err:
                        logger.warning(f"Failed to create video variants: {vv_err}")

                if not video_url:
                    logger.warning(f"Commercial video generation failed for pipeline {pipeline_id}, continuing pipeline")
                steps[step]["status"] = "completed"

        # Determine next pipeline status
        nxt = _next_step(step)
        mode = pipeline.get("mode", "semi_auto")

        if not nxt:
            new_status = "completed"
            # Save as campaign in campaigns table
            try:
                approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
                clean_copy = _clean_copy_text(approved_copy)
                image_urls = steps.get("lucas_design", {}).get("image_urls", [])
                platform_variants = steps.get("lucas_design", {}).get("platform_variants", {})
                video_url = steps.get("marcos_video", {}).get("video_url", "")
                schedule_text = steps.get("pedro_publish", {}).get("output", "")
                ctx = pipeline.get("result", {}).get("context", {})
                user_campaign_name = pipeline.get("result", {}).get("campaign_name", "")
                campaign_name = user_campaign_name or ctx.get("company", "") or pipeline.get("briefing", "")[:50]
                supabase.table("campaigns").insert({
                    "tenant_id": pipeline["tenant_id"],
                    "name": campaign_name,
                    "status": "draft",
                    "goal": "ai_pipeline",
                    "metrics": {
                        "type": "ai_pipeline",
                        "target_segment": {"platforms": pipeline.get("platforms", [])},
                        "messages": [{"step": 1, "channel": "multi", "content": clean_copy, "delay_hours": 0}],
                        "schedule": {"pipeline_id": pipeline_id, "schedule_text": schedule_text},
                        "stats": {
                            "sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0,
                            "images": [u for u in image_urls if u],
                            "platform_variants": platform_variants,
                            "video_url": video_url,
                            "video_variants": steps.get("marcos_video", {}).get("video_variants", {}),
                            "pipeline_id": pipeline_id,
                        },
                        "created_by": pipeline.get("tenant_id"),
                    },
                }).execute()
                logger.info(f"Campaign created from pipeline {pipeline_id}")
            except Exception as camp_err:
                logger.warning(f"Failed to create campaign from pipeline: {camp_err}")
        elif mode == "auto":
            new_status = "running"
        elif step in PAUSE_AFTER:
            new_status = "waiting_approval"
        else:
            new_status = "running"

        supabase.table("pipelines").update({
            "steps": steps, "status": new_status,
            "current_step": nxt or step,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", pipeline_id).execute()

        # In auto mode, run next step
        if mode == "auto" and nxt:
            await _execute_step(pipeline_id, nxt)

        # In semi-auto, if not a pause point, auto-continue to next
        if mode == "semi_auto" and nxt and step not in PAUSE_AFTER:
            await _execute_step(pipeline_id, nxt)

    except Exception as e:
        logger.error(f"Pipeline step {step} failed: {e}")
        steps[step]["status"] = "failed"
        steps[step]["error"] = str(e)
        steps[step]["completed_at"] = datetime.now(timezone.utc).isoformat()
        supabase.table("pipelines").update({
            "steps": steps, "status": "failed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", pipeline_id).execute()


# ── Endpoints ──

def _run_step_in_thread(pipeline_id, step):
    """Run pipeline step in a separate thread with its own event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_execute_step(pipeline_id, step))
    except Exception as e:
        logger.error(f"Thread pipeline step {step} error: {e}")
    finally:
        loop.close()


def _start_step_bg(pipeline_id, step):
    """Start a pipeline step in a background thread"""
    t = threading.Thread(target=_run_step_in_thread, args=(pipeline_id, step), daemon=True)
    t.start()

@router.post("/upload")
async def upload_pipeline_asset(
    file: UploadFile = File(...),
    asset_type: str = Form("reference"),
    user=Depends(get_current_user)
):
    """Upload a brand logo or reference image to Supabase Storage"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted")

    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = os.path.splitext(file.filename or "upload.png")[1] or ".png"
    filename = f"assets/{asset_type}_{uuid.uuid4().hex[:8]}{ext}"
    content_type = file.content_type or "image/png"
    public_url = _upload_to_storage(content, filename, content_type)
    return {"url": public_url, "filename": filename, "type": asset_type, "size": len(content)}


@router.post("/generate-avatar")
async def generate_avatar(req: AvatarGenerateRequest, user=Depends(get_current_user)):
    """Generate a full-body professional avatar from an uploaded photo using AI."""
    try:
        system_msg = (
            "You are an expert portrait photographer. You create stunning full-body professional photos. "
            "CRITICAL: Always output VERTICAL portrait format (taller than wide, approximately 3:5 ratio). "
            "When given a reference photo, preserve the person's EXACT identity — same face, features, skin tone, hair."
        )

        if req.source_image_url:
            img_b64 = None
            mime = "image/png"
            try:
                img_req = urllib.request.Request(req.source_image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=15) as resp:
                    img_data = resp.read()
                    img_b64 = base64.b64encode(img_data).decode("utf-8")
                    content_type = resp.headers.get("Content-Type", "image/png")
                    mime = content_type if content_type.startswith("image/") else "image/png"
            except Exception as dl_err:
                logger.warning(f"Failed to download source image: {dl_err}")

            prompt = (
                "EDIT this photo to create a FULL-BODY professional portrait of this EXACT SAME person. "
                "Do NOT generate a different person. Preserve their EXACT face, features, skin tone, and hair. "
                "Show them standing confidently in a modern studio with soft lighting. "
                "Professional business attire. Full body visible from head to feet. "
                "Clean minimal background. Photorealistic, 4K detail. "
                "OUTPUT FORMAT: VERTICAL portrait (taller than wide, 3:5 ratio)."
            )

            if img_b64:
                # Step 1: Get vision description of the person
                person_desc = await _describe_person(img_b64, mime)

                prompt = (
                    "FOCUS ONLY ON THE PERSON in this photo. IGNORE the background, other people, and scenery completely. "
                    "Create a FULL-BODY professional portrait of this EXACT SAME person. "
                    "Do NOT generate a different person. Preserve their EXACT face, features, skin tone, facial hair, and hair. "
                    "Show them standing confidently in a modern studio with soft lighting. "
                    "Professional business attire. Full body visible from head to feet. "
                    "REPLACE the background with a clean, minimal studio background. "
                    "Photorealistic, 4K detail. "
                    "OUTPUT FORMAT: VERTICAL portrait (taller than wide, 3:5 ratio)."
                )
                if person_desc:
                    prompt = f"PERSON TO FOCUS ON (ignore background and other people): {person_desc}\n\n{prompt}"

                # Step 2: Use direct multimodal call with text+image in SAME message
                images = await _gemini_edit_image(system_msg, prompt, img_b64, mime)
                if images:
                    img_bytes = base64.b64decode(images[0]['data'])
                    filename = f"avatars/avatar_{uuid.uuid4().hex[:8]}.png"
                    public_url = _upload_to_storage(img_bytes, filename, "image/png")
                    return {"avatar_url": public_url}

        # Fallback: no source image or image download failed
        prompt = (
            f"Professional full-body portrait of a confident business presenter"
            f"{' for ' + req.company_name if req.company_name else ''}. "
            "Standing in a modern studio, professional attire, warm smile, looking at camera. "
            "Full body visible from head to feet. Clean minimal background. "
            "Photorealistic, 4K detail. "
            "OUTPUT FORMAT: VERTICAL portrait (taller than wide, 3:5 ratio)."
        )
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"avatar-{uuid.uuid4().hex[:8]}",
            system_message=system_msg
        )
        msg = UserMessage(text=prompt)
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        text_response, images = await chat.send_message_multimodal_response(msg)

        if images and len(images) > 0:
            img_bytes = base64.b64decode(images[0]['data'])
            filename = f"avatars/avatar_{uuid.uuid4().hex[:8]}.png"
            public_url = _upload_to_storage(img_bytes, filename, "image/png")
            return {"avatar_url": public_url}
        raise HTTPException(status_code=500, detail="AI não gerou a imagem. Tente novamente.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AvatarAccuracyRequest(BaseModel):
    source_image_url: str
    video_frame_urls: list = []  # Additional frames from video for richer reference
    company_name: str = ""
    logo_url: str = ""  # Company logo URL to composite onto the polo shirt
    max_iterations: int = 3

# In-memory store for accuracy generation jobs
_accuracy_jobs = {}


def _composite_logo_on_avatar(avatar_bytes: bytes, logo_bytes: bytes) -> bytes:
    """Composite company logo onto the left chest area of the avatar's white polo shirt.
    Automatically removes black/dark backgrounds from the logo."""
    try:
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        logo_img = Image.open(BytesIO(logo_bytes)).convert("RGBA")

        # Remove black/dark background from logo
        import numpy as np
        logo_arr = np.array(logo_img)
        # Detect dark pixels (R<50, G<50, B<50) and make them transparent
        dark_mask = (logo_arr[:, :, 0] < 50) & (logo_arr[:, :, 1] < 50) & (logo_arr[:, :, 2] < 50)
        logo_arr[dark_mask, 3] = 0  # Set alpha to 0 for dark pixels
        logo_img = Image.fromarray(logo_arr, "RGBA")

        # Crop to non-transparent bounding box to remove excess space
        bbox = logo_img.getbbox()
        if bbox:
            logo_img = logo_img.crop(bbox)

        aw, ah = avatar_img.size
        # Logo on left chest: ~10% of avatar width, positioned at ~38% from left, ~22% from top
        logo_target_w = max(int(aw * 0.10), 40)
        logo_ratio = logo_img.height / logo_img.width
        logo_target_h = int(logo_target_w * logo_ratio)
        logo_resized = logo_img.resize((logo_target_w, logo_target_h), Image.LANCZOS)

        # Position: left chest area
        paste_x = int(aw * 0.38)
        paste_y = int(ah * 0.22)

        # Paste with alpha mask for transparency
        avatar_img.paste(logo_resized, (paste_x, paste_y), logo_resized)

        # Convert back to RGB PNG
        output = avatar_img.convert("RGB")
        buf = BytesIO()
        output.save(buf, format="PNG", quality=95)
        logger.info(f"Logo composited: {logo_target_w}x{logo_target_h} at ({paste_x},{paste_y})")
        return buf.getvalue()
    except Exception as e:
        logger.warning(f"Logo compositing failed: {e}")
        return avatar_bytes  # Return original if compositing fails


def _run_accuracy_generation(job_id: str, source_image_url: str, video_frame_urls: list, company_name: str, logo_url: str, max_iterations: int):
    """Background thread: generate avatar with accuracy agent feedback loop."""
    import asyncio
    import json
    loop = asyncio.new_event_loop()
    try:
        # Download source image (primary reference)
        img_b64 = None
        mime = "image/png"
        try:
            img_req = urllib.request.Request(source_image_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(img_req, timeout=15) as resp:
                img_data = resp.read()
                img_b64 = base64.b64encode(img_data).decode("utf-8")
                content_type = resp.headers.get("Content-Type", "image/png")
                mime = content_type if content_type.startswith("image/") else "image/png"
        except Exception as dl_err:
            logger.warning(f"Failed to download source image: {dl_err}")
            _accuracy_jobs[job_id] = {"status": "failed", "error": f"Failed to download source: {dl_err}"}
            return

        if not img_b64:
            _accuracy_jobs[job_id] = {"status": "failed", "error": "Could not read source image"}
            return

        # Download video frames for additional reference
        extra_frames_b64 = []
        for frame_url in (video_frame_urls or [])[:3]:
            try:
                freq = urllib.request.Request(frame_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(freq, timeout=10) as fresp:
                    fdata = fresp.read()
                    fb64 = base64.b64encode(fdata).decode("utf-8")
                    fct = fresp.headers.get("Content-Type", "image/png")
                    fmime = fct if fct.startswith("image/") else "image/png"
                    extra_frames_b64.append({"data": fb64, "mime": fmime})
            except Exception as fe:
                logger.warning(f"Failed to download video frame: {fe}")

        # Step 1: Get vision description — use photo as primary
        AGENTS = [
            {"name": "Scanner", "role": "Analyzing reference"},
            {"name": "Artist", "role": "Generating avatar"},
            {"name": "Critic", "role": "Evaluating accuracy"},
        ]
        _accuracy_jobs[job_id] = {"status": "processing", "progress": "Analyzing reference photo...", "iteration": 0, "iterations": [], "agents": AGENTS, "active_agent": "Scanner"}
        person_desc = loop.run_until_complete(_describe_person(img_b64, mime))

        # Enhance description with video frames if available
        if extra_frames_b64:
            _accuracy_jobs[job_id]["progress"] = "Analyzing video frames for enhanced identity..."
            video_desc = loop.run_until_complete(_describe_person_from_video(extra_frames_b64))
            if video_desc:
                person_desc = f"{person_desc}\nADDITIONAL DETAILS FROM VIDEO: {video_desc}"
                logger.info(f"Enhanced desc with video: {video_desc[:100]}...")

        system_msg = (
            "You are a professional photo editor. You edit existing photos of real people. "
            "ABSOLUTE RULE: The person in the output MUST be IDENTICAL to the person in the input photo. "
            "You only change clothing, background, and pose. The face, body, skin, and hair stay EXACTLY the same. "
            "Output VERTICAL format (taller than wide, 3:5 ratio)."
        )

        iterations = []
        extra_feedback = ""

        for attempt in range(max_iterations):
            _accuracy_jobs[job_id] = {
                "status": "processing",
                "progress": f"Generating avatar (attempt {attempt + 1}/{max_iterations})...",
                "iteration": attempt + 1,
                "iterations": iterations,
                "agents": AGENTS,
                "active_agent": "Artist",
            }

            prompt = (
                "EDIT this photo of this person. Do NOT create a new person. Keep THIS EXACT person.\n\n"
                "CHANGES TO MAKE:\n"
                "1. CLOTHING: Change to a clean plain white polo shirt (completely blank, no logos), "
                "black dress pants, white sneakers\n"
                "2. BACKGROUND: Change to a clean professional photo studio with soft lighting\n"
                "3. POSE: Standing full body, slight smile, arms relaxed\n"
                "4. FRAMING: Full body head to feet, VERTICAL portrait format\n\n"
                "DO NOT CHANGE:\n"
                "- The person's face (every detail must stay identical)\n"
                "- Skin tone and complexion\n"
                "- Hair color, style, and length\n"
                "- Facial hair pattern\n"
                "- Body build and proportions\n"
                "- Remove sunglasses if worn, showing the person's natural eyes"
            )
            if person_desc and attempt == 0:
                # Include key identity features in the prompt
                prompt += f"\n\nIMPORTANT - Person identity details to preserve: {person_desc[:400]}"
            elif person_desc:
                # On retry, include a shorter reminder
                prompt += f"\n\nPerson: {person_desc[:200]}"
            if extra_feedback:
                prompt += f"\n\nFIX THESE ISSUES: {extra_feedback}"

            # Use primary photo as the ONLY visual reference (video frames enhance text description only)
            images = loop.run_until_complete(_gemini_edit_image(system_msg, prompt, img_b64, mime))
            if not images:
                iterations.append({"attempt": attempt + 1, "url": None, "score": 0, "feedback": "Generation failed", "passed": False})
                continue

            # Upload generated avatar (with logo composited if available)
            gen_bytes = base64.b64decode(images[0]['data'])
            gen_b64 = images[0]['data']
            gen_mime = images[0].get('mime_type', 'image/png')

            # Composite company logo onto the shirt if logo_url is provided
            if logo_url:
                try:
                    logo_req = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(logo_req, timeout=10) as logo_resp:
                        logo_bytes = logo_resp.read()
                    gen_bytes = _composite_logo_on_avatar(gen_bytes, logo_bytes)
                    gen_b64 = base64.b64encode(gen_bytes).decode("utf-8")
                    logger.info("Logo composited onto avatar successfully")
                except Exception as logo_err:
                    logger.warning(f"Logo download/composite failed: {logo_err}")

            filename = f"avatars/avatar_acc_{uuid.uuid4().hex[:8]}.png"
            avatar_url = _upload_to_storage(gen_bytes, filename, "image/png")

            # Accuracy comparison
            _accuracy_jobs[job_id]["progress"] = f"Evaluating accuracy (attempt {attempt + 1})..."
            _accuracy_jobs[job_id]["active_agent"] = "Critic"
            comparison = loop.run_until_complete(_accuracy_compare(img_b64, mime, gen_b64, gen_mime))

            iteration_result = {
                "attempt": attempt + 1,
                "url": avatar_url,
                "score": comparison["score"],
                "feedback": comparison["feedback"],
                "passed": comparison["passed"],
            }
            iterations.append(iteration_result)

            _accuracy_jobs[job_id]["iterations"] = iterations

            if comparison["passed"]:
                logger.info(f"Accuracy agent APPROVED avatar on attempt {attempt + 1} (score: {comparison['score']}/10)")
                _accuracy_jobs[job_id] = {
                    "status": "completed",
                    "avatar_url": avatar_url,
                    "iterations": iterations,
                    "final_score": comparison["score"],
                    "agents": AGENTS,
                    "active_agent": None,
                }
                return

            # Not passed - prepare feedback for next iteration
            extra_feedback = comparison["feedback"]
            logger.info(f"Accuracy agent REJECTED attempt {attempt + 1} (score: {comparison['score']}/10): {extra_feedback}")

        # All iterations exhausted - return best one
        best = max(iterations, key=lambda x: x.get("score", 0)) if iterations else None
        if best and best.get("url"):
            _accuracy_jobs[job_id] = {
                "status": "completed",
                "avatar_url": best["url"],
                "iterations": iterations,
                "final_score": best["score"],
                "note": "best_of_attempts",
            }
        else:
            _accuracy_jobs[job_id] = {"status": "failed", "error": "All generation attempts failed", "iterations": iterations}

    except Exception as e:
        logger.error(f"Accuracy avatar generation failed: {e}")
        _accuracy_jobs[job_id] = {"status": "failed", "error": str(e), "iterations": _accuracy_jobs.get(job_id, {}).get("iterations", [])}
    finally:
        loop.close()


@router.post("/generate-avatar-with-accuracy")
async def generate_avatar_with_accuracy(req: AvatarAccuracyRequest, user=Depends(get_current_user)):
    """Start avatar generation with accuracy agent feedback loop. Returns job_id for polling."""
    job_id = uuid.uuid4().hex[:10]
    _accuracy_jobs[job_id] = {"status": "processing", "progress": "Starting...", "iteration": 0, "iterations": []}
    thread = threading.Thread(
        target=_run_accuracy_generation,
        args=(job_id, req.source_image_url, req.video_frame_urls, req.company_name, req.logo_url, min(req.max_iterations, 3)),
        daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "processing"}


@router.get("/generate-avatar-with-accuracy/{job_id}")
async def get_avatar_accuracy_status(job_id: str, user=Depends(get_current_user)):
    """Poll for avatar accuracy generation status."""
    job = _accuracy_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Accuracy job not found")
    return job


@router.post("/extract-from-video")
async def extract_from_video(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Extract best frame (image) and audio from an uploaded video for avatar creation.
    Returns: { frame_url, audio_url, duration }"""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    try:
        video_bytes = await file.read()
        if len(video_bytes) > 50 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Video exceeds 50MB limit")

        uid = uuid.uuid4().hex[:8]
        video_path = f"/tmp/avatar_video_{uid}.mp4"
        with open(video_path, "wb") as f:
            f.write(video_bytes)

        # Get video duration
        duration = _ffprobe_duration(video_path) or 10.0

        # Extract best frame at 1/3 of video (person usually well-positioned)
        frame_time = min(duration / 3, 5.0)
        frame_path = f"/tmp/avatar_frame_{uid}.jpg"
        r = subprocess.run(
            [FFMPEG_PATH, "-y", "-ss", str(frame_time), "-i", video_path,
             "-vframes", "1", "-q:v", "2", frame_path],
            capture_output=True, timeout=30
        )
        if r.returncode != 0 or not os.path.exists(frame_path):
            # Fallback: try frame at 0s
            subprocess.run(
                [FFMPEG_PATH, "-y", "-i", video_path, "-vframes", "1", "-q:v", "2", frame_path],
                capture_output=True, timeout=30
            )

        # Extract additional frames at different times for enhanced identity
        extra_frame_urls = []
        frame_times = [max(0.5, duration * 0.15), max(1.0, duration * 0.5), max(1.5, duration * 0.75)]
        for i, ft in enumerate(frame_times):
            if ft >= duration:
                continue
            ef_path = f"/tmp/avatar_frame_{uid}_extra_{i}.jpg"
            ef_r = subprocess.run(
                [FFMPEG_PATH, "-y", "-ss", str(ft), "-i", video_path,
                 "-vframes", "1", "-q:v", "2", ef_path],
                capture_output=True, timeout=15
            )
            if ef_r.returncode == 0 and os.path.exists(ef_path) and os.path.getsize(ef_path) > 500:
                with open(ef_path, "rb") as ef:
                    ef_bytes = ef.read()
                ef_filename = f"avatars/video_frame_{uid}_extra_{i}.jpg"
                ef_url = _upload_to_storage(ef_bytes, ef_filename, "image/jpeg")
                extra_frame_urls.append(ef_url)
            if os.path.exists(ef_path):
                try:
                    os.remove(ef_path)
                except Exception:
                    pass

        # Extract audio
        audio_path = f"/tmp/avatar_audio_{uid}.mp3"
        r2 = subprocess.run(
            [FFMPEG_PATH, "-y", "-i", video_path, "-vn",
             "-acodec", "libmp3lame", "-ab", "192k", "-ar", "44100", audio_path],
            capture_output=True, timeout=60
        )
        audio_url = None
        if r2.returncode == 0 and os.path.exists(audio_path) and os.path.getsize(audio_path) > 500:
            with open(audio_path, "rb") as af:
                audio_bytes_data = af.read()
            audio_filename = f"voice_recordings/video_voice_{uid}.mp3"
            audio_url = _upload_to_storage(audio_bytes_data, audio_filename, "audio/mpeg")
            logger.info(f"Extracted audio from video: {audio_filename} ({len(audio_bytes_data)/1024:.0f}KB)")

        # Upload frame
        frame_url = None
        if os.path.exists(frame_path) and os.path.getsize(frame_path) > 500:
            with open(frame_path, "rb") as ff:
                frame_bytes = ff.read()
            frame_filename = f"avatars/video_frame_{uid}.jpg"
            frame_url = _upload_to_storage(frame_bytes, frame_filename, "image/jpeg")
            logger.info(f"Extracted frame from video: {frame_filename}")

        # Cleanup
        for p in [video_path, frame_path, audio_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

        if not frame_url:
            raise HTTPException(status_code=500, detail="Could not extract frame from video")

        return {
            "frame_url": frame_url,
            "audio_url": audio_url,
            "duration": round(duration, 1),
            "extra_frame_urls": extra_frame_urls,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



class VoicePreviewRequest(BaseModel):
    voice_id: str = "alloy"
    text: str = "Hello! This is a preview of my voice. I can be the presenter for your marketing campaigns."

@router.post("/voice-preview")
async def voice_preview(req: VoicePreviewRequest, user=Depends(get_current_user)):
    """Generate a short voice preview using OpenAI TTS."""
    valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    if req.voice_id not in valid_voices:
        raise HTTPException(status_code=400, detail=f"Invalid voice. Choose from: {', '.join(valid_voices)}")
    try:
        tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
        audio_bytes = await tts.generate_speech(
            text=req.text[:200], model="tts-1-hd",
            voice=req.voice_id, speed=1.0, response_format="mp3"
        )
        filename = f"voice_previews/preview_{req.voice_id}_{uuid.uuid4().hex[:6]}.mp3"
        public_url = _upload_to_storage(audio_bytes, filename, "audio/mpeg")
        return {"audio_url": public_url, "voice_id": req.voice_id}
    except Exception as e:
        logger.error(f"Voice preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-voice-recording")
async def upload_voice_recording(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Upload a custom voice recording."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) > 20 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File exceeds 20MB limit")
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "webm"
        filename = f"voice_recordings/recording_{uuid.uuid4().hex[:8]}.{ext}"
        content_type = file.content_type or "audio/webm"
        public_url = _upload_to_storage(audio_bytes, filename, content_type)
        return {"audio_url": public_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MasterVoiceRequest(BaseModel):
    audio_url: str

@router.post("/master-voice")
async def master_voice(req: MasterVoiceRequest, user=Depends(get_current_user)):
    """Masterize voice: noise reduction, EQ, compression, normalization — keeps original character."""
    try:
        # Download original audio
        audio_data = urllib.request.urlopen(req.audio_url, timeout=30).read()
        if not audio_data or len(audio_data) < 500:
            raise HTTPException(status_code=400, detail="Could not download audio")

        uid = uuid.uuid4().hex[:8]
        input_path = f"/tmp/voice_raw_{uid}.mp3"
        output_path = f"/tmp/voice_master_{uid}.mp3"
        with open(input_path, "wb") as f:
            f.write(audio_data)

        # FFmpeg mastering chain:
        # 1. highpass=80 — remove low rumble/hum
        # 2. lowpass=12000 — remove high freq hiss
        # 3. afftdn — adaptive noise reduction
        # 4. acompressor — gentle compression for consistent volume
        # 5. equalizer — boost presence (2-4kHz) for clarity
        # 6. loudnorm — normalize loudness to broadcast standard
        filter_chain = (
            "highpass=f=80,"
            "lowpass=f=12000,"
            "afftdn=nf=-25:nr=10:nt=w,"
            "acompressor=threshold=-20dB:ratio=3:attack=5:release=50:makeup=2,"
            "equalizer=f=3000:t=q:w=1.5:g=3,"
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        )
        r = subprocess.run(
            [FFMPEG_PATH, "-y", "-i", input_path, "-af", filter_chain,
             "-acodec", "libmp3lame", "-ab", "192k", "-ar", "44100", output_path],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode != 0 or not os.path.exists(output_path):
            logger.warning(f"Voice mastering failed: {r.stderr[:300] if r.stderr else ''}")
            raise HTTPException(status_code=500, detail="Mastering failed")

        with open(output_path, "rb") as f:
            mastered_bytes = f.read()
        filename = f"voice_recordings/mastered_{uid}.mp3"
        public_url = _upload_to_storage(mastered_bytes, filename, "audio/mpeg")
        logger.info(f"Voice mastered: {len(audio_data)/1024:.0f}KB → {len(mastered_bytes)/1024:.0f}KB")

        # Cleanup
        for p in [input_path, output_path]:
            try: os.remove(p)
            except: pass

        return {"audio_url": public_url, "original_size": len(audio_data), "mastered_size": len(mastered_bytes)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice mastering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AvatarVideoPreviewRequest(BaseModel):
    avatar_url: str
    voice_url: str = ""  # Custom voice URL (recorded/extracted)
    voice_id: str = ""   # TTS voice ID (alloy, onyx, etc.)
    language: str = "pt"  # Language for test text

# In-memory store for preview generation jobs
_preview_jobs = {}

PREVIEW_TEXTS = {
    "pt": "Olá! Sou seu apresentador virtual, pronto para representar sua marca!",
    "en": "Hello! I'm your virtual presenter, ready to represent your brand!",
    "es": "Hola! Soy tu presentador virtual, listo para representar tu marca!",
}

def _run_preview_generation(job_id: str, avatar_url: str, voice_url: str, voice_id: str, language: str):
    """Background thread: generate TTS audio (if needed) then lip-sync video with Kling Avatar."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        text = PREVIEW_TEXTS.get(language, PREVIEW_TEXTS["pt"])
        audio_url = voice_url  # Use custom voice if available

        # If no custom voice, generate TTS audio
        if not audio_url:
            tts_voice = voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "onyx"
            tts = OpenAITextToSpeech(api_key=EMERGENT_KEY)
            audio_bytes = loop.run_until_complete(tts.generate_speech(
                text=text, model="tts-1-hd",
                voice=tts_voice, speed=1.0, response_format="mp3"
            ))
            audio_filename = f"voice_previews/preview_tts_{uuid.uuid4().hex[:6]}.mp3"
            audio_url = _upload_to_storage(audio_bytes, audio_filename, "audio/mpeg")
            logger.info(f"Preview TTS audio generated: {audio_filename}")

        _preview_jobs[job_id] = {"status": "generating_video", "progress": "Lip-sync..."}

        # Generate lip-sync video with Kling Avatar v2
        fal_key = os.environ.get("FAL_KEY")
        if not fal_key:
            _preview_jobs[job_id] = {"status": "failed", "error": "FAL_KEY not configured"}
            return

        import fal_client
        os.environ["FAL_KEY"] = fal_key
        handler = loop.run_until_complete(fal_client.submit_async(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": avatar_url,
                "audio_url": audio_url,
            }
        ))
        result = loop.run_until_complete(handler.get())
        video_url = result.get("video", {}).get("url") if result else None

        if video_url:
            _preview_jobs[job_id] = {"status": "completed", "video_url": video_url}
            logger.info(f"Preview lip-sync video generated: {video_url}")
        else:
            _preview_jobs[job_id] = {"status": "failed", "error": "Kling returned no video"}
    except Exception as e:
        logger.error(f"Avatar video preview failed: {e}")
        _preview_jobs[job_id] = {"status": "failed", "error": str(e)}
    finally:
        loop.close()

@router.post("/avatar-video-preview")
async def avatar_video_preview(req: AvatarVideoPreviewRequest, user=Depends(get_current_user)):
    """Start avatar video preview generation with lip-sync. Returns job_id for polling."""
    job_id = uuid.uuid4().hex[:10]
    _preview_jobs[job_id] = {"status": "processing", "progress": "Starting..."}
    thread = threading.Thread(
        target=_run_preview_generation,
        args=(job_id, req.avatar_url, req.voice_url, req.voice_id, req.language),
        daemon=True
    )
    thread.start()
    return {"job_id": job_id, "status": "processing"}

@router.get("/avatar-video-preview/{job_id}")
async def get_avatar_video_preview(job_id: str, user=Depends(get_current_user)):
    """Poll for avatar video preview generation status."""
    job = _preview_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Preview job not found")
    return job


class AvatarVariantRequest(BaseModel):
    source_image_url: str = ""
    clothing: str = "company_uniform"
    angle: str = "front"
    company_name: str = ""
    logo_url: str = ""

@router.post("/generate-avatar-variant")
async def generate_avatar_variant(req: AvatarVariantRequest, user=Depends(get_current_user)):
    """Generate an avatar variant with different clothing or angle."""
    CLOTHING_MAP = {
        "company_uniform": "wearing a crisp plain white polo shirt (no logos, no text, completely blank), fitted black dress pants, and clean white sneakers (sapatênis style)",
        "business_formal": "wearing a tailored dark navy business suit, white dress shirt, elegant tie",
        "casual": "wearing a casual smart outfit, clean jeans, stylish blazer over a t-shirt",
        "streetwear": "wearing trendy streetwear, designer hoodie, sneakers, modern urban style",
        "creative": "wearing an artistic creative outfit, colorful patterns, unique accessories",
    }
    ANGLE_MAP = {
        "front": "facing directly towards the camera, front view, looking straight at the viewer",
        "left_profile": "body and face turned to THEIR LEFT, showing the LEFT side of the face and body in profile view, camera positioned to their right capturing the left cheek",
        "right_profile": "body and face turned to THEIR RIGHT, showing the RIGHT side of the face and body in profile view, camera positioned to their left capturing the right cheek",
        "back": "turned completely away from camera showing their back, we see the back of their head and body, looking slightly over their right shoulder",
    }
    clothing_desc = CLOTHING_MAP.get(req.clothing, CLOTHING_MAP["company_uniform"])
    angle_desc = ANGLE_MAP.get(req.angle, ANGLE_MAP["front"])
    try:
        system_msg = (
            "You are an expert at editing portrait photographs while preserving the person's EXACT identity. "
            "CRITICAL RULE: The person in the output MUST be the EXACT SAME individual as in the input photo — "
            "same face shape, same eyes, same nose, same mouth, same skin tone, same hair color and style, "
            "same body build. Do NOT generate a different person. Do NOT change their appearance. "
            "Only change their clothing and camera angle as instructed. "
            "The output must be VERTICAL portrait format (taller than wide, approximately 3:5 ratio)."
        )
        prompt = (
            f"EDIT this photo of this EXACT person. Do NOT replace them with a different person.\n\n"
            f"CHANGE ONLY:\n"
            f"1. CLOTHING: Dress them in: {clothing_desc}\n"
            f"2. POSE/ANGLE: Reposition them so they are {angle_desc}\n\n"
            f"KEEP EXACTLY THE SAME:\n"
            f"- Their face (every detail — eyes, nose, mouth, jawline, eyebrows)\n"
            f"- Their skin tone and complexion\n"
            f"- Their hair color, style, and length\n"
            f"- Their body build and proportions\n\n"
            f"OUTPUT: Full-body portrait, VERTICAL format (taller than wide, 3:5 ratio), "
            f"head to feet visible, modern photo studio, soft professional lighting, clean minimal background. "
            f"Photorealistic, 4K detail."
        )

        if req.source_image_url:
            img_b64 = None
            mime = "image/png"
            try:
                img_req = urllib.request.Request(req.source_image_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(img_req, timeout=15) as resp:
                    img_data = resp.read()
                    img_b64 = base64.b64encode(img_data).decode("utf-8")
                    content_type = resp.headers.get("Content-Type", "image/png")
                    mime = content_type if content_type.startswith("image/") else "image/png"
            except Exception as dl_err:
                logger.warning(f"Failed to download source image: {dl_err}")

            if img_b64:
                # Step 1: Get vision description for identity preservation
                person_desc = await _describe_person(img_b64, mime)
                if person_desc:
                    prompt = f"PERSON IDENTITY (must match EXACTLY): {person_desc}\n\n{prompt}"

                images = await _gemini_edit_image(system_msg, prompt, img_b64, mime)
                if images:
                    img_bytes = base64.b64decode(images[0]['data'])
                    # Composite logo if it's company_uniform and logo_url provided
                    if req.clothing == "company_uniform" and req.logo_url:
                        try:
                            logo_req_dl = urllib.request.Request(req.logo_url, headers={"User-Agent": "Mozilla/5.0"})
                            with urllib.request.urlopen(logo_req_dl, timeout=10) as logo_resp:
                                logo_bytes = logo_resp.read()
                            img_bytes = _composite_logo_on_avatar(img_bytes, logo_bytes)
                        except Exception as le:
                            logger.warning(f"Variant logo composite failed: {le}")
                    filename = f"avatars/avatar_var_{uuid.uuid4().hex[:8]}.png"
                    public_url = _upload_to_storage(img_bytes, filename, "image/png")
                    return {"avatar_url": public_url, "clothing": req.clothing, "angle": req.angle}

        # Fallback without image reference
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"avatar-var-{uuid.uuid4().hex[:8]}",
            system_message=system_msg
        )
        msg = UserMessage(text=prompt)
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        text_response, images = await chat.send_message_multimodal_response(msg)
        if images and len(images) > 0:
            img_bytes = base64.b64decode(images[0]['data'])
            filename = f"avatars/avatar_var_{uuid.uuid4().hex[:8]}.png"
            public_url = _upload_to_storage(img_bytes, filename, "image/png")
            return {"avatar_url": public_url, "clothing": req.clothing, "angle": req.angle}
        raise HTTPException(status_code=500, detail="AI failed to generate image. Try again.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar variant generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class AvatarBatch360Request(BaseModel):
    source_image_url: str = ""
    clothing: str = "company_uniform"
    logo_url: str = ""

# In-memory store for batch 360 jobs
_batch360_jobs = {}

def _run_batch_360(job_id: str, source_url: str, clothing: str, logo_url: str = ""):
    """Background thread to generate all 4 angles for an avatar."""
    import asyncio
    CLOTHING_MAP = {
        "company_uniform": "wearing a crisp plain white polo shirt (no logos, no text, completely blank), fitted black dress pants, and clean white sneakers (sapatênis style)",
        "business_formal": "wearing a tailored dark navy business suit, white dress shirt, elegant tie",
        "casual": "wearing a casual smart outfit, clean jeans, stylish blazer over a t-shirt",
        "streetwear": "wearing trendy streetwear, designer hoodie, sneakers, modern urban style",
        "creative": "wearing an artistic creative outfit, colorful patterns, unique accessories",
    }
    ANGLE_MAP = {
        "front": "facing directly towards the camera, front view, looking straight at the viewer",
        "left_profile": "body and face turned to THEIR LEFT, showing the LEFT side profile view",
        "right_profile": "body and face turned to THEIR RIGHT, showing the RIGHT side profile view",
        "back": "turned completely away from camera showing their back, looking slightly over shoulder",
    }
    clothing_desc = CLOTHING_MAP.get(clothing, CLOTHING_MAP["company_uniform"])
    system_msg = (
        "You are an expert at editing portrait photographs while preserving the person's EXACT identity. "
        "CRITICAL RULE: The person in the output MUST be the EXACT SAME individual as in the input photo — "
        "same face shape, same eyes, same nose, same mouth, same skin tone, same hair color and style, "
        "same body build. Do NOT generate a different person. Do NOT change their appearance. "
        "Only change their clothing and camera angle as instructed. "
        "The output must be VERTICAL portrait format (taller than wide, approximately 3:5 ratio)."
    )

    # Download source image once
    img_b64 = None
    mime = "image/png"
    try:
        img_req = urllib.request.Request(source_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(img_req, timeout=15) as resp:
            img_data = resp.read()
            img_b64 = base64.b64encode(img_data).decode("utf-8")
            ct = resp.headers.get("Content-Type", "image/png")
            mime = ct if ct.startswith("image/") else "image/png"
    except Exception as e:
        logger.error(f"Batch 360: Failed to download source: {e}")
        _batch360_jobs[job_id] = {"status": "failed", "error": str(e)}
        return

    loop = asyncio.new_event_loop()

    # Step 1: Get vision description for identity preservation
    person_desc = loop.run_until_complete(_describe_person(img_b64, mime))

    results = {}
    for angle_key, angle_desc in ANGLE_MAP.items():
        try:
            prompt = (
                f"EDIT this photo of this EXACT person. Do NOT replace them with a different person.\n\n"
                f"CHANGE ONLY:\n"
                f"1. CLOTHING: Dress them in: {clothing_desc}\n"
                f"2. POSE/ANGLE: Reposition them so they are {angle_desc}\n\n"
                f"KEEP EXACTLY THE SAME:\n"
                f"- Their face (every detail — eyes, nose, mouth, jawline, eyebrows)\n"
                f"- Their skin tone and complexion\n"
                f"- Their hair color, style, and length\n"
                f"- Their body build and proportions\n\n"
                f"OUTPUT: Full-body portrait, VERTICAL format (taller than wide, 3:5 ratio), "
                f"head to feet visible, modern photo studio, soft professional lighting, clean minimal background. "
                f"Photorealistic, 4K detail."
            )
            if person_desc:
                prompt = f"PERSON IDENTITY (must match EXACTLY): {person_desc}\n\n{prompt}"

            images = loop.run_until_complete(_gemini_edit_image(system_msg, prompt, img_b64, mime))
            if images:
                img_bytes = base64.b64decode(images[0]['data'])
                # Composite logo for company_uniform (front/left/right only, not back)
                if clothing == "company_uniform" and logo_url and angle_key != "back":
                    try:
                        logo_req_dl = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(logo_req_dl, timeout=10) as logo_resp:
                            logo_bytes_data = logo_resp.read()
                        img_bytes = _composite_logo_on_avatar(img_bytes, logo_bytes_data)
                    except Exception as le:
                        logger.warning(f"360 logo composite failed for {angle_key}: {le}")
                filename = f"avatars/avatar_360_{angle_key}_{uuid.uuid4().hex[:6]}.png"
                public_url = _upload_to_storage(img_bytes, filename, "image/png")
                results[angle_key] = public_url
                logger.info(f"Batch 360: {angle_key} done")
            else:
                results[angle_key] = None
                logger.warning(f"Batch 360: {angle_key} returned no images")
        except Exception as e:
            logger.error(f"Batch 360: {angle_key} failed: {e}")
            results[angle_key] = None
        # Update progress
        _batch360_jobs[job_id] = {"status": "processing", "results": results, "completed": len([v for v in results.values() if v])}

    loop.close()
    _batch360_jobs[job_id] = {"status": "completed", "results": results}

@router.post("/generate-avatar-360")
async def generate_avatar_360(req: AvatarBatch360Request, user=Depends(get_current_user)):
    """Start batch generation of all 4 angles for an avatar (background job with polling)."""
    job_id = uuid.uuid4().hex[:10]
    _batch360_jobs[job_id] = {"status": "processing", "results": {}, "completed": 0}
    thread = threading.Thread(target=_run_batch_360, args=(job_id, req.source_image_url, req.clothing, req.logo_url), daemon=True)
    thread.start()
    return {"job_id": job_id, "status": "processing"}

@router.get("/generate-avatar-360/{job_id}")
async def get_avatar_360_status(job_id: str, user=Depends(get_current_user)):
    """Poll for batch 360 generation status."""
    job = _batch360_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job




@router.post("/generate-presenter-video")
async def generate_presenter_video_endpoint(
    pipeline_id: str = Form(""),
    avatar_url: str = Form(""),
    audio_url: str = Form(""),
    user=Depends(get_current_user)
):
    """Generate a talking-head presenter video using fal.ai Kling Avatar v2.
    Requires FAL_KEY in environment."""
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise HTTPException(status_code=503, detail="Presenter video requires FAL_KEY configuration. Contact admin.")
    try:
        import fal_client
        os.environ["FAL_KEY"] = fal_key
        handler = await fal_client.submit_async(
            "fal-ai/kling-video/ai-avatar/v2/standard",
            arguments={
                "image_url": avatar_url,
                "audio_url": audio_url,
            }
        )
        result = await handler.get()
        video_url = result.get("video", {}).get("url") if result else None
        if video_url:
            return {"video_url": video_url}
        raise HTTPException(status_code=500, detail="Presenter video generation returned no video")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Presenter video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_pipelines(user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(20).execute()
    return {"pipelines": result.data or []}


@router.post("")
async def create_pipeline(data: PipelineCreate, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)

    init_steps = {}
    for s in STEP_ORDER:
        init_steps[s] = {"status": "pending", "output": None, "started_at": None, "completed_at": None}

    pipeline = {
        "tenant_id": tenant["id"],
        "briefing": data.briefing,
        "mode": data.mode,
        "platforms": data.platforms,
        "status": "running",
        "current_step": "sofia_copy",
        "steps": init_steps,
        "result": {
            "context": data.context or {},
            "contact_info": data.contact_info or {},
            "uploaded_assets": data.uploaded_assets or [],
            "campaign_name": data.campaign_name or "",
            "campaign_language": data.campaign_language or "",
            "media_formats": data.media_formats or {},
            "selected_music": data.selected_music or "",
            "skip_video": data.skip_video or False,
            "video_mode": data.video_mode or "narration",
            "avatar_url": data.avatar_url or "",
            "avatar_voice": data.avatar_voice or None,
        },
    }

    result = supabase.table("pipelines").insert(pipeline).execute()
    pid = result.data[0]["id"]

    _start_step_bg(pid, "sofia_copy")
    return result.data[0]



@router.get("/saved/history")
async def get_saved_history_v2(user=Depends(get_current_user)):
    """Get saved logos and recent briefings from previous pipelines"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("briefing, result, platforms, created_at").eq("tenant_id", tenant["id"]).order("created_at", desc=True).limit(20).execute()
    pipelines = result.data or []

    logos = []
    seen_urls = set()
    briefings = []
    seen_briefings = set()

    for p in pipelines:
        assets = (p.get("result") or {}).get("uploaded_assets") or []
        for a in assets:
            if a.get("type") == "logo" and a.get("url") and a["url"] not in seen_urls:
                seen_urls.add(a["url"])
                logos.append({"url": a["url"], "filename": a.get("filename", "logo")})
        b = p.get("briefing", "").strip()
        camp_name = (p.get("result") or {}).get("campaign_name", "")
        camp_lang = (p.get("result") or {}).get("campaign_language", "")
        if b and b not in seen_briefings:
            seen_briefings.add(b)
            briefings.append({
                "briefing": b, "campaign_name": camp_name,
                "campaign_language": camp_lang,
                "platforms": p.get("platforms", []),
                "created_at": p.get("created_at", ""),
            })

    return {"logos": logos[:10], "briefings": briefings[:10]}


@router.delete("/saved/logo")
async def delete_saved_logo_v2(url: str, user=Depends(get_current_user)):
    """Delete a saved logo file from Supabase Storage or local disk"""
    await _get_tenant(user)
    if url.startswith("http"):
        # Supabase Storage URL — extract filename from URL
        # URL format: https://xxx.supabase.co/storage/v1/object/public/pipeline-assets/assets/logo_xxx.png
        parts = url.split(f"/{STORAGE_BUCKET}/")
        if len(parts) == 2:
            _delete_from_storage(parts[1])
        return {"status": "deleted", "url": url}
    elif url.startswith("/api/uploads/pipeline/"):
        # Legacy local file
        filename = url.split("/")[-1]
        filepath = os.path.join(UPLOADS_DIR, "assets", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        return {"status": "deleted", "url": url}
    else:
        raise HTTPException(status_code=400, detail="Invalid logo URL")


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return result.data[0]


@router.post("/{pipeline_id}/approve")
async def approve_step(pipeline_id: str, data: PipelineApprove, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    if pipeline["status"] != "waiting_approval":
        raise HTTPException(status_code=400, detail="Pipeline is not waiting for approval")

    steps = pipeline.get("steps") or {}

    # Find the step that just completed and needs approval
    # First, try using current_step - the pending step IS what needs to run next
    current = pipeline.get("current_step", "")
    approval_step = None

    if current and steps.get(current, {}).get("status") == "pending":
        # The current step is pending — find the previous completed step
        idx = STEP_ORDER.index(current) if current in STEP_ORDER else -1
        if idx > 0:
            approval_step = STEP_ORDER[idx - 1]

    # Fallback: search in reverse for any completed step at a pause point
    if not approval_step:
        for s in reversed(STEP_ORDER):
            if steps.get(s, {}).get("status") == "completed" and s in PAUSE_AFTER:
                approval_step = s
                break

    # Final fallback: find last completed step before first pending step
    if not approval_step:
        for i, s in enumerate(STEP_ORDER):
            if steps.get(s, {}).get("status") == "pending" and i > 0:
                approval_step = STEP_ORDER[i - 1]
                break

    if not approval_step:
        raise HTTPException(status_code=400, detail="No step awaiting approval")

    # Apply user's selection
    if approval_step == "ana_review_copy" and data.selection is not None:
        steps[approval_step]["user_selection"] = data.selection
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        copy_only = re.split(r'===\s*IMAGE BRIEFING\s*===', sofia_output, flags=re.IGNORECASE)[0]
        variations = re.split(r'===\s*VARIATION \d+\s*===', copy_only)
        variations = [v.strip() for v in variations[1:] if v.strip()]
        sel = data.selection
        if 0 < sel <= len(variations):
            steps[approval_step]["approved_content"] = variations[sel - 1]

    elif approval_step == "rafael_review_design" and data.selections:
        steps[approval_step]["user_selections"] = data.selections
        steps[approval_step]["selections"] = data.selections

    if data.feedback:
        steps[approval_step]["user_feedback"] = data.feedback

    supabase.table("pipelines").update({
        "steps": steps,
        "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    # Run next step
    nxt = _next_step(approval_step)
    if nxt:
        _start_step_bg(pipeline_id, nxt)
        return {"status": "approved", "next_step": nxt}
    else:
        supabase.table("pipelines").update({"status": "completed"}).eq("id", pipeline_id).execute()
        return {"status": "completed"}


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").delete().eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"status": "deleted"}


@router.post("/{pipeline_id}/retry")
async def retry_failed_step(pipeline_id: str, user=Depends(get_current_user)):
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    if pipeline["status"] not in ("failed", "running"):
        raise HTTPException(status_code=400, detail="Pipeline is not in a retryable state")

    steps = pipeline.get("steps") or {}
    retry_step = None
    for s in STEP_ORDER:
        st = steps.get(s, {}).get("status")
        if st in ("failed", "running", "generating_images", "generating_video"):
            retry_step = s
            break

    if not retry_step:
        raise HTTPException(status_code=400, detail="No retryable step found")

    steps[retry_step]["status"] = "pending"
    steps[retry_step]["error"] = None
    supabase.table("pipelines").update({
        "steps": steps, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    _start_step_bg(pipeline_id, retry_step)
    return {"status": "retrying", "step": retry_step}


class RegenerateDesignRequest(BaseModel):
    design_index: int = 0
    feedback: str = ""


@router.post("/{pipeline_id}/regenerate-design")
async def regenerate_design(pipeline_id: str, data: RegenerateDesignRequest, user=Depends(get_current_user)):
    """Regenerate a specific design image with user feedback"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    lucas = steps.get("lucas_design", {})

    if lucas.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Design step not completed")

    old_prompts = lucas.get("image_prompts", [])
    old_urls = lucas.get("image_urls", [])
    idx = data.design_index

    if idx < 0 or idx >= len(old_prompts):
        raise HTTPException(status_code=400, detail="Invalid design index")

    # Build enhanced prompt with feedback
    original_prompt = old_prompts[idx]
    enhanced_prompt = f"{original_prompt}. ADJUSTMENTS: {data.feedback}. ABSOLUTE RULE: ZERO text, words, logos, or placeholder shapes in the image. Pure visual only." if data.feedback else original_prompt

    # Mark as regenerating
    lucas["status"] = "generating_images"
    steps["lucas_design"] = lucas
    supabase.table("pipelines").update({
        "steps": steps, "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", pipeline_id).execute()

    # Regenerate in background thread
    def _regen():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            new_url = loop.run_until_complete(_generate_image(enhanced_prompt, pipeline_id, idx + 10))
            fresh = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data[0]
            s = fresh.get("steps", {})
            urls = s.get("lucas_design", {}).get("image_urls", list(old_urls))
            prompts = s.get("lucas_design", {}).get("image_prompts", list(old_prompts))
            if new_url:
                urls[idx] = new_url
                prompts[idx] = enhanced_prompt
            s["lucas_design"]["image_urls"] = urls
            s["lucas_design"]["image_prompts"] = prompts
            s["lucas_design"]["status"] = "completed"
            prev_status = fresh.get("status")
            new_status = "waiting_approval" if prev_status == "running" else prev_status
            if fresh.get("current_step") in ("rafael_review_design", "lucas_design"):
                new_status = "waiting_approval"
            supabase.table("pipelines").update({
                "steps": s, "status": new_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
        except Exception as e:
            logger.error(f"Regenerate design failed: {e}")
            fresh = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data[0]
            s = fresh.get("steps", {})
            s["lucas_design"]["status"] = "completed"
            supabase.table("pipelines").update({
                "steps": s, "status": "waiting_approval",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
        finally:
            loop.close()

    t = threading.Thread(target=_regen, daemon=True)
    t.start()
    return {"status": "regenerating", "design_index": idx}


@router.get("/{pipeline_id}/labels")
async def get_step_labels(pipeline_id: str, user=Depends(get_current_user)):
    return {"labels": STEP_LABELS, "order": STEP_ORDER}


@router.post("/{pipeline_id}/regenerate-video-variants")
async def regenerate_video_variants(pipeline_id: str, user=Depends(get_current_user)):
    """Regenerate per-platform video variants from the master video."""
    tenant = await _get_tenant(user)
    pipeline = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute().data
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    p = pipeline[0]
    marcos = p.get("steps", {}).get("marcos_video", {})
    video_url = marcos.get("video_url")
    video_format = marcos.get("video_format", "horizontal")
    platforms = p.get("platforms", [])
    if not video_url:
        raise HTTPException(status_code=400, detail="No master video to create variants from")

    try:
        variants = await _create_video_variants(pipeline_id, video_url, video_format, platforms)
        if variants:
            steps = p.get("steps", {})
            steps["marcos_video"]["video_variants"] = variants
            supabase.table("pipelines").update({
                "steps": steps,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()
            # Also update campaign stats
            campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
            for c in campaigns:
                m = c.get("metrics") or {}
                s = m.get("stats") or {}
                if s.get("pipeline_id") == pipeline_id:
                    s["video_variants"] = variants
                    m["stats"] = s
                    supabase.table("campaigns").update({"metrics": m}).eq("id", c["id"]).execute()
                    logger.info(f"Updated campaign {c['id']} with {len(variants)} video variants")
                    break
            return {"status": "success", "variants": variants, "count": len(variants)}
        return {"status": "no_variants_generated"}
    except Exception as e:
        logger.error(f"Regenerate video variants failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{pipeline_id}/remix-audio")
async def remix_audio(pipeline_id: str, user=Depends(get_current_user)):
    """Re-mix audio for an existing video with corrected volume levels"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    marcos = steps.get("marcos_video", {})
    video_url = marcos.get("video_url", "")
    marcos_output = marcos.get("output", "")
    if not video_url:
        raise HTTPException(status_code=400, detail="No video found to remix")

    # Parse music mood from marcos output
    music_mood = "corporate"
    music_match = re.search(r'===MUSIC DIRECTION===([\s\S]*?)===(?:NARRATION TONE|CTA SEQUENCE)===', marcos_output, re.IGNORECASE)
    if music_match:
        mood_line = re.search(r'Mood:\s*(\w+)', music_match.group(1), re.IGNORECASE)
        if mood_line:
            music_mood = mood_line.group(1).strip().lower()

    # User-selected music override
    user_music = pipeline.get("result", {}).get("selected_music", "")
    if user_music:
        music_mood = user_music

    def _remix_bg(pid, vid_url, mood):
        import urllib.request as urlreq
        try:
            # Download existing video
            vid_path = f"/tmp/{pid}_remix_src.mp4"
            urlreq.urlretrieve(vid_url, vid_path)

            # Extract video (no audio) and existing narration
            vid_only = f"/tmp/{pid}_remix_vid.mp4"
            subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -an -c:v copy {vid_only}", shell=True, capture_output=True, timeout=60)

            # Extract existing audio to analyze
            old_audio = f"/tmp/{pid}_remix_old_audio.wav"
            subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -vn -acodec pcm_s16le -ar 44100 -ac 2 {old_audio}", shell=True, capture_output=True, timeout=30)

            # Get video duration
            vid_duration = _ffprobe_duration(vid_only) or 23.0

            # Select music
            music_dir = "/app/backend/assets/music"
            mood_map = {
                "upbeat": "upbeat.mp3", "energetic": "energetic.mp3", "exciting": "energetic.mp3",
                "emotional": "emotional.mp3", "inspirational": "emotional.mp3",
                "cinematic": "cinematic.mp3", "dramatic": "cinematic.mp3", "epic": "cinematic.mp3",
                "corporate": "corporate.mp3", "professional": "corporate.mp3", "clean": "corporate.mp3",
                "luxury": "jazz_smooth.mp3", "elegant": "classical_piano.mp3", "sophisticated": "jazz_smooth.mp3",
                "relaxing": "ambient_dreamy.mp3", "calm": "ambient_nature.mp3", "peaceful": "ambient_nature.mp3",
                "modern": "electronic_chill.mp3", "tech": "electronic_chill.mp3",
                "warm": "pop_acoustic.mp3", "friendly": "country_modern.mp3",
                "fun": "pop_dance.mp3", "happy": "pop_acoustic.mp3",
            }
            mood_file = mood_map.get(mood, "corporate.mp3")
            bg_music = os.path.join(music_dir, mood_file)
            if not os.path.exists(bg_music):
                bg_music = os.path.join(music_dir, "corporate.mp3")

            # Resample with pre-reduced music volume
            narr_rs = f"/tmp/{pid}_remix_narr.wav"
            music_rs = f"/tmp/{pid}_remix_music.wav"
            # Use old audio as narration source (it already has the mixed audio, so we try to use original narration if available)
            narr_src = f"/tmp/{pid}_narration.mp3"
            if not os.path.exists(narr_src):
                narr_src = old_audio  # fallback to extracted audio
            subprocess.run(f"{FFMPEG_PATH} -y -i {narr_src} -ar 44100 -ac 2 {narr_rs}", shell=True, capture_output=True, timeout=30)
            subprocess.run(f"{FFMPEG_PATH} -y -i {bg_music} -af volume=0.08 -ar 44100 -ac 2 -t {vid_duration} {music_rs}", shell=True, capture_output=True, timeout=30)

            # Professional mix
            mixed = f"/tmp/{pid}_remix_mixed.wav"
            mix_filter = (
                f"[0:a]volume=1.5,acompressor=threshold=-20dB:ratio=4:attack=5:release=200[narr];"
                f"[1:a]afade=t=in:d=2,afade=t=out:st={max(vid_duration-3, 18)}:d=3[music];"
                f"[narr][music]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[out]"
            )
            r = subprocess.run([FFMPEG_PATH, "-y", "-i", narr_rs, "-i", music_rs, "-filter_complex", mix_filter, "-map", "[out]", "-t", str(vid_duration), "-ar", "44100", "-ac", "2", mixed], capture_output=True, text=True, timeout=60)

            if r.returncode != 0:
                logger.error(f"Remix audio mix failed: {r.stderr[:200]}")
                return

            # Merge new audio with video
            output = f"/tmp/{pid}_remixed.mp4"
            subprocess.run([FFMPEG_PATH, "-y", "-i", vid_only, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output], capture_output=True, timeout=60)

            if os.path.exists(output):
                with open(output, "rb") as f:
                    video_bytes = f.read()
                filename = f"videos/{pid}_commercial.mp4"
                new_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                # Update pipeline
                steps["marcos_video"]["video_url"] = new_url
                supabase.table("pipelines").update({"steps": steps}).eq("id", pid).execute()
                # Also update campaign if exists (search by pipeline_id in metrics JSONB)
                try:
                    camps = supabase.table("campaigns").select("id, metrics").eq("tenant_id", supabase.table("pipelines").select("tenant_id").eq("id", pid).single().execute().data["tenant_id"]).execute()
                    for c in (camps.data or []):
                        metrics = c.get("metrics") or {}
                        if metrics.get("stats", {}).get("pipeline_id") == pid:
                            stats = metrics.get("stats", {})
                            stats["video_url"] = new_url
                            metrics["stats"] = stats
                            supabase.table("campaigns").update({"metrics": metrics}).eq("id", c["id"]).execute()
                            logger.info(f"Updated campaign {c['id']} with new video URL")
                            break
                except Exception as ce:
                    logger.warning(f"Campaign update skipped: {ce}")
                logger.info(f"Audio remixed successfully for pipeline {pid}")
        except Exception as e:
            logger.error(f"Remix failed for {pid}: {e}")

    t = threading.Thread(target=_remix_bg, args=(pipeline_id, video_url, music_mood), daemon=True)
    t.start()
    return {"status": "remixing", "message": "Audio is being remixed with corrected levels"}


@router.post("/remix-all-videos")
async def remix_all_videos(user=Depends(get_current_user)):
    """Batch remix audio for ALL existing videos with corrected volume levels"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("id, steps, result").eq("tenant_id", tenant["id"]).execute()
    pipelines_with_video = []
    for p in (result.data or []):
        vid_url = (p.get("steps") or {}).get("marcos_video", {}).get("video_url", "")
        if vid_url:
            pipelines_with_video.append(p["id"])

    # Process all remixes in a single background thread, sequentially
    def _batch_remix_all(pipeline_ids, tenant_id):
        import urllib.request as urlreq
        for pid in pipeline_ids:
            try:
                p_data = supabase.table("pipelines").select("*").eq("id", pid).single().execute()
                if not p_data.data:
                    continue
                steps = p_data.data.get("steps", {})
                marcos = steps.get("marcos_video", {})
                video_url = marcos.get("video_url", "")
                marcos_output = marcos.get("output", "")
                if not video_url:
                    continue
                music_mood = "corporate"
                music_match = re.search(r'Mood:\s*(\w+)', marcos_output, re.IGNORECASE)
                if music_match:
                    music_mood = music_match.group(1).strip().lower()
                user_music = p_data.data.get("result", {}).get("selected_music", "")
                if user_music:
                    music_mood = user_music

                vid_path = f"/tmp/{pid}_remix_src.mp4"
                urlreq.urlretrieve(video_url, vid_path)
                vid_only = f"/tmp/{pid}_remix_vid.mp4"
                subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -an -c:v copy {vid_only}", shell=True, capture_output=True, timeout=60)
                vid_duration = _ffprobe_duration(vid_only) or 23.0
                music_dir = "/app/backend/assets/music"
                mood_map = {
                    "upbeat": "upbeat.mp3", "energetic": "energetic.mp3", "cinematic": "cinematic.mp3",
                    "corporate": "corporate.mp3", "emotional": "emotional.mp3", "luxury": "jazz_smooth.mp3",
                    "calm": "ambient_nature.mp3", "modern": "electronic_chill.mp3", "warm": "pop_acoustic.mp3",
                    "fun": "pop_dance.mp3", "elegant": "classical_piano.mp3",
                }
                bg_music = os.path.join(music_dir, mood_map.get(music_mood, "corporate.mp3"))
                if not os.path.exists(bg_music):
                    bg_music = os.path.join(music_dir, "corporate.mp3")
                narr_src = f"/tmp/{pid}_narration.mp3"
                if not os.path.exists(narr_src):
                    old_audio = f"/tmp/{pid}_remix_old.wav"
                    subprocess.run(f"{FFMPEG_PATH} -y -i {vid_path} -vn -acodec pcm_s16le -ar 44100 -ac 2 {old_audio}", shell=True, capture_output=True, timeout=30)
                    narr_src = old_audio
                narr_rs = f"/tmp/{pid}_remix_narr.wav"
                music_rs = f"/tmp/{pid}_remix_music.wav"
                subprocess.run(f"{FFMPEG_PATH} -y -i {narr_src} -ar 44100 -ac 2 {narr_rs}", shell=True, capture_output=True, timeout=30)
                subprocess.run(f"{FFMPEG_PATH} -y -i {bg_music} -af volume=0.08 -ar 44100 -ac 2 -t {vid_duration} {music_rs}", shell=True, capture_output=True, timeout=30)
                mixed = f"/tmp/{pid}_remix_mixed.wav"
                mix_filter = f"[0:a]volume=1.5,acompressor=threshold=-20dB:ratio=4:attack=5:release=200[narr];[1:a]afade=t=in:d=2,afade=t=out:st={max(vid_duration-3,18)}:d=3[music];[narr][music]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[out]"
                subprocess.run([FFMPEG_PATH, "-y", "-i", narr_rs, "-i", music_rs, "-filter_complex", mix_filter, "-map", "[out]", "-t", str(vid_duration), "-ar", "44100", "-ac", "2", mixed], capture_output=True, timeout=60)
                output = f"/tmp/{pid}_remixed.mp4"
                subprocess.run([FFMPEG_PATH, "-y", "-i", vid_only, "-i", mixed, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", output], capture_output=True, timeout=60)
                if os.path.exists(output):
                    with open(output, "rb") as f:
                        vb = f.read()
                    fn = f"videos/{pid}_commercial.mp4"
                    new_url = _upload_to_storage(vb, fn, "video/mp4")
                    steps["marcos_video"]["video_url"] = new_url
                    supabase.table("pipelines").update({"steps": steps}).eq("id", pid).execute()
                    # Update linked campaign
                    try:
                        camps = supabase.table("campaigns").select("id, metrics").eq("tenant_id", tenant_id).execute()
                        for c in (camps.data or []):
                            if (c.get("metrics") or {}).get("stats", {}).get("pipeline_id") == pid:
                                m = c.get("metrics") or {}
                                m.setdefault("stats", {})["video_url"] = new_url
                                supabase.table("campaigns").update({"metrics": m}).eq("id", c["id"]).execute()
                                break
                    except Exception:
                        pass
                    logger.info(f"Batch remix done: {pid}")
                # Clean up temp files
                for f in [vid_path, vid_only, narr_rs, music_rs, mixed, output]:
                    try:
                        os.remove(f)
                    except Exception:
                        pass
                time.sleep(3)  # Delay between uploads to avoid overwhelming Supabase
            except Exception as e:
                logger.error(f"Batch remix failed for {pid}: {e}")
        logger.info(f"Batch remix complete: processed {len(pipeline_ids)} pipelines")

    t = threading.Thread(target=_batch_remix_all, args=(pipelines_with_video, tenant["id"]), daemon=True)
    t.start()
    return {"status": "remixing", "count": len(pipelines_with_video), "pipelines": pipelines_with_video}







class RegenerateStyleRequest(BaseModel):
    style: str = "professional"
    prompt_override: str = ""
    campaign_name: str = ""
    campaign_copy: str = ""
    product_description: str = ""
    language: str = "pt"

@router.post("/regenerate-single-image")
async def regenerate_single_image(body: RegenerateStyleRequest, user=Depends(get_current_user)):
    """Generate a single image with a specific visual style, without needing a full pipeline"""
    await _get_tenant(user)

    STYLE_PROMPTS = {
        "minimalist": "Ultra minimalist composition. Single powerful focal element against vast negative space. Muted, desaturated palette with one accent color. Zen-like simplicity. Think Apple product photography.",
        "vibrant": "Explosion of saturated colors and dynamic energy. Bold complementary color clashes, motion blur effects, dramatic perspective. Youthful, electric atmosphere.",
        "luxury": "Premium luxury photography. Rich dark backgrounds, dramatic studio lighting with gold/warm highlights, silk textures, shallow depth of field. Ultra-sophisticated mood.",
        "corporate": "Editorial business photography. Clean natural lighting, professional environment, confident subjects or pristine product shots. Trustworthy blue-gray color grading.",
        "playful": "Joyful, whimsical visual storytelling. Bright candy colors, unexpected perspectives, playful subjects in dynamic poses. Warm, inviting, fun.",
        "bold": "High-impact, stop-the-scroll photography. Extreme contrast, dramatic shadows, close-up details, powerful visual tension. Fearless composition.",
        "organic": "Warm, natural, earthy photography. Golden hour lighting, natural textures (wood, linen, stone), warm earth tones, authentic lifestyle moments.",
        "tech": "Futuristic, sleek technology aesthetic. Dark environment with neon accent lighting, reflective surfaces, geometric precision, blue-purple color palette.",
        "professional": "High-end commercial photography. Studio-quality lighting, professional color grading, clean background, sharp focus on subject with natural bokeh."
    }

    LANG_MAP = {"pt": "Portuguese (Português)", "es": "Spanish (Español)", "en": "English"}
    lang_name = LANG_MAP.get(body.language, "Portuguese (Português)")
    lang_code = body.language or "pt"

    style_desc = STYLE_PROMPTS.get(body.style, STYLE_PROMPTS["professional"])

    # Build prompt with LANGUAGE as the FIRST and DOMINANT instruction
    lang_header = f"""⚠️ ABSOLUTE MANDATORY LANGUAGE RULE — OVERRIDES EVERYTHING BELOW:
ALL text, headlines, words, phrases visible in this image MUST be written EXCLUSIVELY in {lang_name}.
DO NOT use English or any other language. If any text would naturally be in English, TRANSLATE it to {lang_name}.
This is NON-NEGOTIABLE. Any text not in {lang_name} makes the image UNUSABLE.
"""

    if body.prompt_override.strip():
        content_prompt = body.prompt_override.strip()
    else:
        context = body.product_description or body.campaign_name or "brand"
        copy_hint = body.campaign_copy[:200] if body.campaign_copy else ""
        content_prompt = f"Create a stunning marketing visual for: {context}."
        if copy_hint:
            content_prompt += f" The campaign message (use this as reference for the headline language and tone): {copy_hint}"

    prompt = lang_header
    prompt += f"\n{content_prompt}"
    prompt += f"\n\nVISUAL STYLE: {style_desc}"
    prompt += f"\n\nINCLUDE one short impactful headline text (3-7 words) written in {lang_name}, in bold clean typography. No logos or brand names. 1080x1080 square format."
    prompt += f"\n\n🚨 FINAL CHECK: Every single word visible in the generated image MUST be in {lang_name}. Zero exceptions."

    pid = f"single-{uuid.uuid4().hex[:8]}"
    url = await _generate_image(prompt, pid, 1)
    if not url:
        raise HTTPException(status_code=500, detail="Image generation failed after retries")
    return {"status": "generated", "image_url": url, "style": body.style}





@router.post("/{pipeline_id}/archive")
async def archive_pipeline(pipeline_id: str, user=Depends(get_current_user)):
    """Archive/dismiss a pipeline so the user can create a new one"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("id, tenant_id, status").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    supabase.table("pipelines").update({"status": "archived"}).eq("id", pipeline_id).execute()
    return {"status": "archived", "pipeline_id": pipeline_id}



class PublishRequest(BaseModel):
    edited_copy: Optional[str] = None

@router.post("/{pipeline_id}/publish")
async def publish_pipeline_campaign(pipeline_id: str, body: PublishRequest = PublishRequest(), user=Depends(get_current_user)):
    """Publish a campaign created from a completed pipeline"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    if pipeline.get("status") not in ("completed", "waiting_approval"):
        raise HTTPException(status_code=400, detail="Pipeline is not ready")

    steps = pipeline.get("steps") or {}
    approved_copy = body.edited_copy or steps.get("ana_review_copy", {}).get("approved_content", "")
    clean_copy = _clean_copy_text(approved_copy)
    image_urls = steps.get("lucas_design", {}).get("image_urls", [])
    platform_variants = steps.get("lucas_design", {}).get("platform_variants", {})
    video_url = steps.get("marcos_video", {}).get("video_url", "")
    schedule_text = steps.get("pedro_publish", {}).get("output", "")
    user_campaign_name = pipeline.get("result", {}).get("campaign_name", "")
    ctx = pipeline.get("result", {}).get("context", {})
    campaign_name = user_campaign_name or ctx.get("company", "") or pipeline.get("briefing", "")[:50]

    # Find existing campaign from this pipeline
    campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
    campaign_id = None
    for c in campaigns:
        m = c.get("metrics") or {}
        s = m.get("stats") or {}
        if s.get("pipeline_id") == pipeline_id:
            campaign_id = c["id"]
            break

    campaign_data = {
        "name": campaign_name,
        "status": "created",
        "goal": "ai_pipeline",
        "metrics": {
            "type": "ai_pipeline",
            "target_segment": {"platforms": pipeline.get("platforms", [])},
            "messages": [{"step": 1, "channel": "multi", "content": clean_copy, "delay_hours": 0}],
            "schedule": {"pipeline_id": pipeline_id, "schedule_text": schedule_text},
            "stats": {
                "sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0,
                "images": [u for u in image_urls if u],
                "platform_variants": platform_variants,
                "video_url": video_url,
                "pipeline_id": pipeline_id,
            },
        },
    }

    if campaign_id:
        supabase.table("campaigns").update({**campaign_data, "updated_at": datetime.now(timezone.utc).isoformat()}).eq("id", campaign_id).execute()
    else:
        campaign_data["tenant_id"] = tenant["id"]
        insert_result = supabase.table("campaigns").insert(campaign_data).execute()
        campaign_id = insert_result.data[0]["id"]

    # Mark pipeline as completed/published
    supabase.table("pipelines").update({"status": "completed"}).eq("id", pipeline_id).execute()

    return {"status": "published", "campaign_id": campaign_id}



@router.post("/{pipeline_id}/regenerate-video")
async def regenerate_video(pipeline_id: str, user=Depends(get_current_user)):
    """Regenerate the commercial video for a completed pipeline and update its campaign"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    marcos = steps.get("marcos_video", {})
    marcos_output = marcos.get("output", "")
    if not marcos_output:
        raise HTTPException(status_code=400, detail="No video script found in pipeline")

    # Determine video format
    format_match = re.search(r'Format:\s*(horizontal|vertical)', marcos_output, re.IGNORECASE)
    video_format = format_match.group(1).lower() if format_match else "horizontal"
    FORMAT_MAP = {"vertical": "720x1280", "horizontal": "1280x720"}
    size = FORMAT_MAP.get(video_format, "1280x720")
    user_music = pipeline.get("result", {}).get("selected_music", "")

    # Mark as generating
    steps["marcos_video"]["status"] = "generating_video"
    steps["marcos_video"]["video_url"] = None
    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

    # Generate in background
    async def _regen():
        try:
            avatar_voice_regen = pipeline.get("result", {}).get("avatar_voice", None)
            video_mode = pipeline.get("result", {}).get("video_mode", "narration")
            avatar_url = pipeline.get("result", {}).get("avatar_url", "")

            if video_mode == "presenter" and avatar_url:
                video_url = await _generate_presenter_video(pipeline_id, marcos_output, avatar_url, size, user_music, voice_config=avatar_voice_regen)
            else:
                video_url = await _generate_commercial_video(pipeline_id, marcos_output, size, selected_music_override=user_music, voice_config=avatar_voice_regen)
            steps["marcos_video"]["video_url"] = video_url
            steps["marcos_video"]["status"] = "completed"
            supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

            # Auto-update associated campaign
            if video_url:
                # Create video variants for each platform
                video_variants = {}
                try:
                    platforms = pipeline.get("platforms", [])
                    video_variants = await _create_video_variants(pipeline_id, video_url, video_format, platforms)
                    steps["marcos_video"]["video_variants"] = video_variants
                    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()
                    logger.info(f"Regenerated video variants for {len(video_variants)} platforms")
                except Exception as vv_err:
                    logger.warning(f"Failed to create video variants during regen: {vv_err}")

                campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
                for c in campaigns:
                    m = c.get("metrics") or {}
                    s = m.get("stats") or {}
                    if s.get("pipeline_id") == pipeline_id:
                        s["video_url"] = video_url
                        s["video_variants"] = video_variants
                        m["stats"] = s
                        supabase.table("campaigns").update({"metrics": m}).eq("id", c["id"]).execute()
                        logger.info(f"Auto-updated campaign {c['id']} with video + {len(video_variants)} variants")
                        break
        except Exception as e:
            logger.error(f"Video regeneration failed: {e}")
            steps["marcos_video"]["status"] = "completed"
            supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

    asyncio.create_task(_regen())
    return {"status": "generating", "pipeline_id": pipeline_id, "message": "Video regeneration started"}



# ── Campaign Editing Endpoints ──

class UpdateCopyRequest(BaseModel):
    copy_text: str

class RegenerateImageRequest(BaseModel):
    image_index: int = 0
    feedback: str = ""

class CloneLanguageRequest(BaseModel):
    target_language: str = "pt"

@router.put("/{pipeline_id}/update-copy")
async def update_pipeline_copy(pipeline_id: str, data: UpdateCopyRequest, user=Depends(get_current_user)):
    """Update the copy text in a completed pipeline and sync to campaign"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    sofia = steps.get("sofia_copy", {})
    sofia["output"] = data.copy_text
    steps["sofia_copy"] = sofia
    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

    # Sync updated copy to the campaign messages
    campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
    for c in campaigns:
        m = c.get("metrics") or {}
        s = m.get("stats") or {}
        if s.get("pipeline_id") == pipeline_id:
            # Parse variations and rebuild messages
            variations = re.split(r'===\s*VARIATION\s*\d+\s*===', data.copy_text, flags=re.IGNORECASE)
            variations = [v.strip() for v in variations if v.strip()]
            platforms = pipeline.get("platforms") or []
            new_messages = []
            for i, plat in enumerate(platforms):
                var_idx = i % max(len(variations), 1)
                text = _clean_copy_text(variations[var_idx] if variations else data.copy_text)
                new_messages.append({"channel": plat, "content": text, "delay_hours": 0})
            m["messages"] = new_messages
            supabase.table("campaigns").update({"metrics": m}).eq("id", c["id"]).execute()
            logger.info(f"Updated campaign {c['id']} copy from pipeline {pipeline_id}")
            break

    return {"status": "updated", "pipeline_id": pipeline_id}


@router.post("/{pipeline_id}/regenerate-image")
async def regenerate_pipeline_image(pipeline_id: str, data: RegenerateImageRequest, user=Depends(get_current_user)):
    """Regenerate a specific image in the pipeline with optional feedback"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = result.data[0]
    steps = pipeline.get("steps") or {}
    lucas = steps.get("lucas_design", {})
    image_urls = lucas.get("image_urls", [])

    if data.image_index < 0 or data.image_index >= len(image_urls):
        raise HTTPException(status_code=400, detail=f"Invalid image index {data.image_index}. Available: 0-{len(image_urls)-1}")

    # Get pipeline context for image generation
    pipeline_result = pipeline.get("result") or {}
    campaign_language = pipeline_result.get("campaign_language", "en")
    lang_name = {"en": "English", "pt": "Portuguese (Português)", "es": "Spanish (Español)", "fr": "French (Français)", "de": "German", "it": "Italian", "ht": "Haitian Creole"}.get(campaign_language, "English")
    platforms = pipeline.get("platforms") or ["instagram"]

    # Build enhanced prompt with feedback
    sofia_output = steps.get("sofia_copy", {}).get("output", "")
    briefing = pipeline.get("briefing", "")

    lang_header = f"""⚠️ ABSOLUTE MANDATORY LANGUAGE RULE — OVERRIDES EVERYTHING BELOW:
ALL text, headlines, words, phrases visible in this image MUST be written EXCLUSIVELY in {lang_name}.
DO NOT use English or any other language. If any text would naturally be in English, TRANSLATE it to {lang_name}.
This is NON-NEGOTIABLE. Any text not in {lang_name} makes the image UNUSABLE.
"""

    base_prompt = f"""Create a professional marketing image for: {briefing[:300]}
Campaign copy context (use as reference for tone and language): {sofia_output[:200]}
Target platforms: {', '.join(platforms)}"""

    if data.feedback:
        base_prompt = f"""REGENERATION REQUEST — The previous image was NOT satisfactory.
USER FEEDBACK: {data.feedback}

Based on this feedback, create a NEW and IMPROVED image.
Original context: {briefing[:300]}
Campaign copy context (use as reference for tone and language): {sofia_output[:200]}
Target platforms: {', '.join(platforms)}"""

    enhanced_prompt = f"""{lang_header}
{base_prompt}

Technical: Ultra high-quality, 4K, professional color grading. Square 1080x1080.
NO logos, NO brand names, NO website URLs.
🚨 FINAL CHECK: Every single word visible in the generated image MUST be in {lang_name}. Zero exceptions."""

    async def _regen_image():
        try:
            logger.info(f"Regenerating image {data.image_index} for pipeline {pipeline_id}")
            new_url = await _generate_single_image(enhanced_prompt, pipeline_id, f"regen_{data.image_index}")
            if new_url:
                # Update main image
                image_urls[data.image_index] = new_url
                lucas["image_urls"] = image_urls
                steps["lucas_design"] = lucas
                supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()

                # Regenerate ALL platform variants using the updated image list
                try:
                    new_variants = await _create_platform_variants(pipeline_id, image_urls, platforms)
                    lucas["platform_variants"] = new_variants
                    steps["lucas_design"] = lucas
                    supabase.table("pipelines").update({"steps": steps}).eq("id", pipeline_id).execute()
                    logger.info(f"Platform variants regenerated for pipeline {pipeline_id}")
                except Exception as ve:
                    logger.warning(f"Platform variant regeneration failed (non-critical): {ve}")

                # Sync to campaign
                campaigns = supabase.table("campaigns").select("*").eq("tenant_id", tenant["id"]).execute().data or []
                for c in campaigns:
                    m = c.get("metrics") or {}
                    s = m.get("stats") or {}
                    if s.get("pipeline_id") == pipeline_id:
                        s["image_urls"] = image_urls
                        s["platform_variants"] = lucas.get("platform_variants", {})
                        m["stats"] = s
                        supabase.table("campaigns").update({"metrics": m}).eq("id", c["id"]).execute()
                        logger.info(f"Updated campaign images for pipeline {pipeline_id}")
                        break

                logger.info(f"Image {data.image_index} regenerated successfully: {new_url}")
            else:
                logger.error(f"Image regeneration returned None for pipeline {pipeline_id}")
        except Exception as e:
            logger.error(f"Image regeneration failed: {e}")

    asyncio.create_task(_regen_image())
    return {"status": "regenerating", "pipeline_id": pipeline_id, "image_index": data.image_index}


@router.post("/{pipeline_id}/clone-language")
async def clone_pipeline_language(pipeline_id: str, data: CloneLanguageRequest, user=Depends(get_current_user)):
    """Clone a completed pipeline into a different language, creating a new campaign"""
    tenant = await _get_tenant(user)
    result = supabase.table("pipelines").select("*").eq("id", pipeline_id).eq("tenant_id", tenant["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    original = result.data[0]
    orig_result = original.get("result") or {}
    orig_name = orig_result.get("campaign_name", "Campaign")
    orig_lang = orig_result.get("campaign_language", "en")

    lang_labels = {"en": "English", "pt": "Portuguese", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "ja": "Japanese", "zh": "Chinese"}
    target_label = lang_labels.get(data.target_language, data.target_language.upper())

    if orig_lang == data.target_language:
        raise HTTPException(status_code=400, detail=f"Campaign is already in {target_label}")

    # Create new pipeline with same config but different language
    init_steps = {}
    for s in STEP_ORDER:
        init_steps[s] = {"status": "pending", "output": None, "started_at": None, "completed_at": None}

    new_name = f"{orig_name} ({target_label})"
    new_pipeline = {
        "tenant_id": tenant["id"],
        "briefing": original.get("briefing", ""),
        "mode": "auto",
        "platforms": original.get("platforms", []),
        "status": "running",
        "current_step": "sofia_copy",
        "steps": init_steps,
        "result": {
            "context": orig_result.get("context", {}),
            "contact_info": orig_result.get("contact_info", {}),
            "uploaded_assets": orig_result.get("uploaded_assets", []),
            "campaign_name": new_name,
            "campaign_language": data.target_language,
            "media_formats": orig_result.get("media_formats", {}),
            "selected_music": orig_result.get("selected_music", ""),
            "skip_video": orig_result.get("skip_video", False),
            "video_mode": orig_result.get("video_mode", "narration"),
            "avatar_url": orig_result.get("avatar_url", ""),
            "avatar_voice": orig_result.get("avatar_voice", None),
            "apply_brand": orig_result.get("apply_brand", False),
            "brand_data": orig_result.get("brand_data", None),
            "cloned_from": pipeline_id,
        },
    }

    new_result = supabase.table("pipelines").insert(new_pipeline).execute()
    new_pid = new_result.data[0]["id"]

    _start_step_bg(new_pid, "sofia_copy")
    logger.info(f"Cloned pipeline {pipeline_id} ({orig_lang}) -> {new_pid} ({data.target_language}) as '{new_name}'")

    return {
        "status": "running",
        "pipeline_id": new_pid,
        "campaign_name": new_name,
        "target_language": data.target_language,
        "cloned_from": pipeline_id,
    }
