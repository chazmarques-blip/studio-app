"""Pipeline utilities: storage, text parsing, AI wrappers."""
import base64
import re
import os
import urllib.request
import litellm
from io import BytesIO
from PIL import Image

from core.deps import supabase, logger
from core.llm import GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY
from pipeline.config import STORAGE_BUCKET, EMERGENT_PROXY_URL


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




from fastapi import HTTPException


async def _get_tenant(user):
    t = supabase.table("tenants").select("id, plan").eq("owner_id", user["id"]).execute()
    if not t.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t.data[0]



from pipeline.config import STEP_ORDER

def _next_step(current):
    idx = STEP_ORDER.index(current)
    return STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None




async def _detect_texts_in_image(img_b64_or_url: str, mime: str = "image/png", is_url: bool = False) -> list:
    """Use Gemini Vision to detect and extract all visible text/typography from an image.
    Returns a list of text strings found in the image."""
    try:
        if is_url:
            image_content = {"type": "image_url", "image_url": {"url": img_b64_or_url}}
        else:
            image_content = {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64_or_url}"}}

        messages = [
            {"role": "user", "content": [
                {"type": "text", "text": (
                    "Look at this image VERY carefully and list ALL text you can read.\n\n"
                    "Include:\n"
                    "- Headlines and titles (large bold text)\n"
                    "- Subtitles and subheadlines\n"
                    "- Body text and paragraphs\n"
                    "- Text inside banners, ribbons, badges, speech bubbles\n"
                    "- Stylized, artistic, or decorative text\n"
                    "- Text with effects (shadows, outlines, gradients)\n"
                    "- Small text, captions, labels, watermarks\n"
                    "- Text in ANY language (Portuguese, English, Spanish, etc.)\n\n"
                    "Return ONLY a JSON array of strings. Each string = one text element.\n"
                    "Order by size: largest text first.\n"
                    "DO NOT skip any text. Even partial or blurry text should be included.\n\n"
                    "Example: [\"BIG HEADLINE\", \"subtitle here\", \"small caption\"]\n"
                    "If truly no text exists: []"
                )},
                image_content,
            ]}
        ]
        response = litellm.completion(
            model="gemini/gemini-2.5-flash",
            messages=messages,
            api_key=GEMINI_API_KEY,
            max_tokens=800,
        )
        raw = response.choices[0].message.content or "[]"
        logger.info(f"Text detection raw ({len(raw)} chars): {raw.replace(chr(10), ' ')[:400]}")
        import json
        # Strip markdown code block markers
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split('\n')
            lines = [l for l in lines if not l.strip().startswith('```')]
            cleaned = '\n'.join(lines).strip()
        # Try to find complete JSON array
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            try:
                texts = json.loads(match.group())
                if isinstance(texts, list):
                    return [str(t).strip() for t in texts if str(t).strip()]
            except json.JSONDecodeError:
                pass
        # Handle truncated JSON: if starts with [ but no closing ]
        if '[' in cleaned and ']' not in cleaned:
            truncated = cleaned[cleaned.index('['):]
            # Remove trailing comma and whitespace, add closing ]
            truncated = truncated.rstrip().rstrip(',') + ']'
            try:
                texts = json.loads(truncated)
                if isinstance(texts, list):
                    logger.info(f"Text detection recovered from truncated JSON: {len(texts)} texts")
                    return [str(t).strip() for t in texts if str(t).strip()]
            except json.JSONDecodeError:
                pass
        logger.warning(f"Text detection: Could not parse response: {cleaned[:200]}")
        return []
    except Exception as e:
        logger.warning(f"Text detection failed: {e}")
        return []


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
            api_key=GEMINI_API_KEY,
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
            api_key=GEMINI_API_KEY,
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
            api_key=GEMINI_API_KEY,
            max_tokens=250,
        )
        desc = response.choices[0].message.content or ""
        logger.info(f"Video frames description: {desc[:100]}...")
        return desc.strip()
    except Exception as e:
        logger.warning(f"Video frames description failed: {e}")
        return ""



async def _gemini_edit_image(system_msg: str, prompt: str, img_b64: str, mime: str = "image/png") -> list:
    """Send text+image to Gemini for image editing using direct Google GenAI SDK.
    Returns list of image dicts [{mime_type, data}]."""
    from google import genai
    from google.genai import types
    import asyncio

    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = f"{system_msg}\n\n{prompt}"

    contents = [
        types.Part.from_bytes(data=base64.b64decode(img_b64), mime_type=mime),
        full_prompt,
    ]

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    images = []
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            img_b64_out = base64.b64encode(part.inline_data.data).decode()
            images.append({"mime_type": part.inline_data.mime_type or "image/png", "data": img_b64_out})
    return images




async def _gemini_edit_multi_ref(system_msg: str, prompt: str, primary_b64: str, primary_mime: str, extra_refs: list = None) -> list:
    """Send text + MULTIPLE reference images to Gemini using direct Google GenAI SDK.
    extra_refs: list of {"data": b64, "mime": mime_type}"""
    from google import genai
    from google.genai import types
    import asyncio

    client = genai.Client(api_key=GEMINI_API_KEY)
    full_prompt = f"{system_msg}\n\n{prompt}"

    contents = [
        types.Part.from_bytes(data=base64.b64decode(primary_b64), mime_type=primary_mime),
    ]
    for ref in (extra_refs or [])[:5]:
        contents.append(types.Part.from_bytes(data=base64.b64decode(ref["data"]), mime_type=ref.get("mime", "image/png")))
    contents.append(full_prompt)

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=contents,
        config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
    )

    images = []
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            img_b64_out = base64.b64encode(part.inline_data.data).decode()
            images.append({"mime_type": part.inline_data.mime_type or "image/png", "data": img_b64_out})
    return images

# FFmpeg binary path - from imageio_ffmpeg package
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = "/usr/bin/ffmpeg"




import subprocess

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
