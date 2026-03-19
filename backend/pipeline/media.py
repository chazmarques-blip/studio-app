"""Pipeline media generation: images and videos."""
import asyncio
import base64
import os
import re
import time
import uuid
import shutil
import urllib.request
import subprocess
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
from emergentintegrations.llm.openai import OpenAITextToSpeech

from core.deps import supabase, EMERGENT_KEY, logger
from pipeline.config import (
    EMERGENT_PROXY_URL, UPLOADS_DIR, ASSETS_DIR, STORAGE_BUCKET,
    PLATFORM_ASPECT_RATIOS, VIDEO_PLATFORM_FORMATS, MUSIC_LIBRARY,
)
from pipeline.utils import (
    _upload_to_storage, _delete_from_storage,
    _gemini_edit_image, _gemini_edit_multi_ref,
    _ffprobe_duration, _ffprobe_dimensions,
    FFMPEG_PATH,
)


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
    Returns dict: { "tiktok": [url1, url2, url3], "instagram_reels": [url1, url2, url3], ... }
    """
    # Expand platforms to include sub-formats
    SUB_FORMATS = {
        "instagram": ["instagram", "instagram_reels"],
        "facebook": ["facebook", "facebook_stories"],
        "youtube": ["youtube", "youtube_shorts"],
    }
    expanded = []
    for p in platforms:
        if p in SUB_FORMATS:
            expanded.extend(SUB_FORMATS[p])
        else:
            expanded.append(p)
    seen = set()
    all_platforms = []
    for p in expanded:
        if p not in seen:
            seen.add(p)
            all_platforms.append(p)

    # Determine which unique aspect ratios we need
    needed_ratios = {}  # label -> {platforms, w, h}
    for p in all_platforms:
        cfg = PLATFORM_ASPECT_RATIOS.get(p)
        if not cfg:
            continue
        label = cfg["label"]
        if label not in needed_ratios:
            needed_ratios[label] = {"platforms": [], "w": cfg["w"], "h": cfg["h"]}
        needed_ratios[label]["platforms"].append(p)

    # Base images are assumed 1:1 (1024x1024). Create variants for non-1:1 ratios.
    variants = {}
    for p in all_platforms:
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



async def _ai_analyze_video_for_crops(pipeline_id: str, master_path: str, master_w: int, master_h: int, platforms: list) -> dict:
    """AI Image Director: analyze master video keyframes and suggest optimal crop regions per platform.
    Returns dict: { "tiktok": {"x": int, "y": int, "w": int, "h": int}, ... }
    """
    # Extract 3 keyframes at 25%, 50%, 75% of video duration
    duration = _ffprobe_duration(master_path)
    if duration <= 0:
        duration = 10
    timestamps = [duration * 0.25, duration * 0.5, duration * 0.75]
    keyframes = []
    for i, ts in enumerate(timestamps):
        frame_path = f"/tmp/{pipeline_id}_kf_{i}.jpg"
        cmd = [FFMPEG_PATH, "-y", "-ss", str(ts), "-i", master_path, "-vframes", "1", "-q:v", "3", frame_path]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and os.path.exists(frame_path):
            with open(frame_path, "rb") as f:
                keyframes.append(ImageContent(image_base64=base64.b64encode(f.read()).decode()))
            os.remove(frame_path)
    if not keyframes:
        logger.warning("AI Director: no keyframes extracted")
        return {}

    # Build platform info for the prompt
    platform_lines = []
    for p in platforms:
        fmt = VIDEO_PLATFORM_FORMATS.get(p)
        if fmt:
            platform_lines.append(f"- {p}: target {fmt['w']}x{fmt['h']} (aspect {fmt['w']/fmt['h']:.3f})")

    prompt = f"""You are an expert video editor and visual composition director.

Analyze these {len(keyframes)} keyframes from a marketing video.
Master video: {master_w}x{master_h} pixels.

For each target platform, determine the OPTIMAL CROP REGION from the master frame that:
1. Keeps the main subject (person/product/text) centered and fully visible
2. Maintains the target aspect ratio EXACTLY
3. Maximizes the usable area (largest possible crop)
4. Avoids cutting faces, important text, or key product details

Target platforms:
{chr(10).join(platform_lines)}

RESPOND in this EXACT format for each platform (one per line, no extra text):
PLATFORM:[name] CROP:[x],[y],[width],[height]

Rules:
- x + width <= {master_w}, y + height <= {master_h}
- width/height must equal the target aspect ratio
- If master aspect matches target, use: CROP:0,0,{master_w},{master_h}
- Prefer center-weighted crops when subjects are centered
- For vertical crops from horizontal video, focus on the center third"""

    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"ai-director-{pipeline_id}-{int(time.time())}",
            system_message="You are a professional video editor specializing in social media content optimization."
        ).with_model("gemini", "gemini-2.0-flash")

        msg = UserMessage(text=prompt, file_contents=keyframes)
        response = await asyncio.wait_for(chat.send_message(msg), timeout=30)

        # Parse response with multiple format patterns (Gemini can vary)
        crops = {}
        # Log raw response for debugging
        logger.info(f"AI Director raw response ({len(response)} chars): {response[:200]}...")

        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            try:
                # Pattern 1: "PLATFORM:name CROP:x,y,w,h"
                m = re.match(r'PLATFORM:\s*(\S+)\s*CROP:\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', line, re.IGNORECASE)
                if not m:
                    # Pattern 2: "**platform**: CROP: x, y, w, h" (markdown bold)
                    m = re.match(r'\*?\*?(\w[\w_]*)\*?\*?\s*:?\s*(?:CROP:?)?\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', line, re.IGNORECASE)
                if not m:
                    # Pattern 3: "- platform: x, y, w, h"
                    m = re.match(r'-\s*(\w[\w_]*)\s*:\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', line, re.IGNORECASE)
                if not m:
                    # Pattern 4: "platform CROP x,y,width,height"
                    m = re.match(r'(\w[\w_]*)\s+CROP\s*:?\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', line, re.IGNORECASE)
                if not m:
                    continue

                plat = m.group(1).strip().lower().rstrip(':').strip()
                x, y, w, h = int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
                # Validate: must fit inside master and have reasonable size
                x = max(0, min(x, master_w - 50))
                y = max(0, min(y, master_h - 50))
                w = min(w, master_w - x)
                h = min(h, master_h - y)
                if w >= 100 and h >= 100:
                    crops[plat] = {"x": x, "y": y, "w": w, "h": h}
            except (ValueError, IndexError):
                continue

        logger.info(f"AI Director: analyzed {len(keyframes)} frames -> crops for {list(crops.keys())}")
        return crops

    except Exception as e:
        logger.warning(f"AI Director analysis failed (will use generic): {e}")
        return {}


async def _create_video_variants(pipeline_id: str, master_video_url: str, master_format: str, platforms: list) -> dict:
    """Create platform-specific video variants using AI-directed crops when available.
    Returns dict: { "tiktok": "url", "instagram": "url", "instagram_reels": "url", ... }
    """
    import urllib.request as urlreq

    # Expand platforms to include sub-formats
    SUB_FORMATS = {
        "instagram": ["instagram", "instagram_reels"],
        "facebook": ["facebook", "facebook_stories"],
        "youtube": ["youtube", "youtube_shorts"],
    }
    expanded = []
    for p in platforms:
        if p in SUB_FORMATS:
            expanded.extend(SUB_FORMATS[p])
        else:
            expanded.append(p)
    seen = set()
    expanded_unique = []
    for p in expanded:
        if p not in seen:
            seen.add(p)
            expanded_unique.append(p)

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

    # ── AI Image Director: get smart crop suggestions ──
    ai_crops = {}
    try:
        ai_crops = await _ai_analyze_video_for_crops(pipeline_id, master_path, master_w, master_h, expanded_unique)
        if ai_crops:
            logger.info(f"AI Director provided smart crops for: {list(ai_crops.keys())}")
    except Exception as e:
        logger.warning(f"AI Director skipped, using generic: {e}")

    variants = {}
    done_sizes = {}  # "WxH" -> url (only for generic resizes, AI crops are unique)

    for platform in expanded_unique:
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

        # Check if AI Director provided a crop for this platform
        ai_crop = ai_crops.get(platform)

        # If no AI crop and we already have this size from generic resize, reuse
        if not ai_crop and size_key in done_sizes:
            variants[platform] = done_sizes[size_key]
            continue

        # Build FFmpeg video filter
        output_path = f"/tmp/{pipeline_id}_vid_{platform}.mp4"
        target_ratio = tw / th
        master_ratio = master_w / master_h

        if ai_crop:
            # AI-directed: smart crop then scale to target
            cx, cy, cw, ch = ai_crop["x"], ai_crop["y"], ai_crop["w"], ai_crop["h"]
            vf = f"crop={cw}:{ch}:{cx}:{cy},scale={tw}:{th}"
            logger.info(f"AI Director crop for {platform}: {cx},{cy},{cw}x{ch} -> {tw}x{th}")
        elif abs(master_ratio - target_ratio) < 0.05:
            vf = f"scale={tw}:{th}"
        else:
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
            suffix = "ai" if ai_crop else "gen"
            filename = f"videos/{pipeline_id}_{platform}_{size_key}_{suffix}.mp4"
            url = _upload_to_storage(video_bytes, filename, "video/mp4")
            variants[platform] = url
            if not ai_crop:
                done_sizes[size_key] = url
            logger.info(f"Video variant: {platform} ({size_key}) [{'AI-directed' if ai_crop else 'generic'}]")
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


async def _generate_narration(text, pipeline_id, max_duration=20.0, voice_config=None):
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
                    OPENAI_TO_EL = {
                        "onyx": "TX3LPaxmHKxFdv7VOQHJ",
                        "nova": "21m00Tcm4TlvDq8ikWAM",
                        "echo": "29vD33N1CtxCmqQRPOHJ",
                        "alloy": "EXAVITQu4vr4xnSDxMaL",
                        "shimmer": "MF3mGyEYCl7XYWbV9V6O",
                        "fable": "jBpfuIE2acCO8z3wKNLl",
                    }
                    ov = voice_config.get("voice_id", "onyx")
                    el_voice_id = OPENAI_TO_EL.get(ov, el_voice_id)

                # Dylan Reed's precise settings take priority over tone-based heuristics
                if voice_config.get("stability") is not None:
                    stability = voice_config["stability"]
                if voice_config.get("similarity") is not None:
                    similarity = voice_config["similarity"]
                if voice_config.get("style_val") is not None:
                    style = voice_config["style_val"]

                tone = (voice_config.get("tone") or "").lower()
                pace = (voice_config.get("pace") or "moderate").lower()

                # Tone-based adjustments only if Dylan didn't set precise values
                if "stability" not in voice_config:
                    if "energetic" in tone or "excited" in tone or "urgent" in tone:
                        stability = 0.3
                        style = 0.6
                    elif "calm" in tone or "professional" in tone:
                        stability = 0.7
                        style = 0.15
                    elif "warm" in tone or "friendly" in tone:
                        stability = 0.5
                        style = 0.4
                    elif "dramatic" in tone or "inspirational" in tone:
                        stability = 0.35
                        style = 0.55

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

        audio_dur = _ffprobe_duration(raw_path)
        logger.info(f"Narration raw duration: {audio_dur:.1f}s (max: {max_duration}s)")

        if audio_dur > max_duration and audio_dur > 0:
            speed_factor = min(audio_dur / max_duration, 1.15)  # Max 1.15x — barely noticeable
            if speed_factor > 1.05:
                logger.info(f"Narration slightly long ({audio_dur:.1f}s), gentle speed-up: {speed_factor:.2f}x")
                subprocess.run(
                    [FFMPEG_PATH, "-y", "-i", raw_path, "-filter:a", f"atempo={speed_factor}", "-vn", final_path],
                    capture_output=True, timeout=30
                )
                if os.path.exists(final_path) and os.path.getsize(final_path) > 100:
                    logger.info(f"Narration gently adjusted to fit {max_duration}s")
                else:
                    shutil.copy2(raw_path, final_path)
            else:
                shutil.copy2(raw_path, final_path)
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
            subprocess.run(f"{FFMPEG_PATH} -y -i {bg_music_path} -ar 44100 -ac 2 -t {vid_duration} {music_resampled}", shell=True, capture_output=True, timeout=30)

            mixed_audio = f"/tmp/{pipeline_id}_mixed_audio.wav"

            # ── Cinematic Audio Mixing (Murch/Zimmer method) ──
            # Narration: presence boost (3kHz), compressor (broadcast), cut mud (<80Hz)
            # Music: EQ carve (-8dB at 400Hz, -4dB at 2.5kHz), exponential fades
            # Mix: Sidechain compressor — music auto-ducks when narration plays
            fade_out_start = max(vid_duration - 3, 18)

            narr_chain = (
                "volume=1.3,"
                "highpass=f=80,"
                "equalizer=f=3000:t=h:w=1000:g=2.5,"
                "acompressor=threshold=-18dB:ratio=3:attack=10:release=100"
            )
            music_chain = (
                "equalizer=f=400:t=q:w=2:g=-8,"
                "equalizer=f=2500:t=q:w=1.5:g=-4,"
                f"afade=t=in:d=1.5:curve=exp,"
                f"afade=t=out:st={fade_out_start}:d=3:curve=exp"
            )
            # Sidechain: narration signal controls music compression
            # level_in=0.18 → music base level ~18% (cinematic bed)
            # threshold=0.025 → duck when voice > ~-32dB
            # ratio=8 → aggressive ducking
            # attack=15ms → fast response, release=250ms → smooth return
            sidechain = "sidechaincompress=threshold=0.025:ratio=8:attack=15:release=250:level_in=0.18:level_sc=1"

            mix_filter = (
                f"[0:a]{narr_chain}[narr];"
                f"[1:a]{music_chain}[music];"
                f"[narr][music]{sidechain}[out]"
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
                logger.info("Cinematic audio mix: sidechain ducking + EQ carving + outro swell")
            else:
                # Fallback to basic mix if cinematic filter fails
                logger.warning(f"Cinematic mix failed ({r.stderr[:100] if r.stderr else ''}), trying basic mix")
                basic_filter = (
                    f"[0:a]volume=1.5,acompressor=threshold=-20dB:ratio=4:attack=5:release=200[narr];"
                    f"[1:a]volume=0.08,afade=t=in:d=2,afade=t=out:st={max(vid_duration-3, 18)}:d=3[music];"
                    f"[narr][music]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[out]"
                )
                r2 = subprocess.run([
                    FFMPEG_PATH, "-y", "-i", narr_resampled, "-i", music_resampled,
                    "-filter_complex", basic_filter, "-map", "[out]",
                    "-t", str(vid_duration), "-ar", "44100", "-ac", "2", mixed_audio
                ], capture_output=True, text=True, timeout=60)
                if r2.returncode == 0 and os.path.exists(mixed_audio):
                    final_audio = mixed_audio
                    logger.info("Fallback basic mix succeeded")
                else:
                    final_audio = audio_path
                    logger.warning("All audio mixing failed, narration only")
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
        # Remove ALL bracketed stage directions (SILENCE, music only, logo, fade, etc.)
        narration_text = re.sub(r'\[.*?SILENCE.*?\]', '', narration_text, flags=re.IGNORECASE)
        narration_text = re.sub(r'\[.*?music\s+only.*?\]', '', narration_text, flags=re.IGNORECASE)
        narration_text = re.sub(r'\[.*?logo\s+on\s+screen.*?\]', '', narration_text, flags=re.IGNORECASE)
        narration_text = re.sub(r'\[(?:COMPLETE|TOTAL|FULL)?\s*(?:SILENCE|QUIET|PAUSE|NO NARRATION).*?\]', '', narration_text, flags=re.IGNORECASE)
        # Remove any remaining visual/stage directions (anything in brackets that isn't spoken)
        narration_text = re.sub(r'\[.*?(?:fade|black|screen|visual|music|logo|brand|overlay|transition|cut to).*?\]', '', narration_text, flags=re.IGNORECASE)
        # Remove standalone sentences that are clearly directions, not narration
        narration_text = re.sub(r'(?:^|\n).*?(?:sil[eê]ncio|apenas m[uú]sica|logo na tela|music only|fade to|no narration|no spoken|TOTAL WORD COUNT).*?(?:\n|$)', '\n', narration_text, flags=re.IGNORECASE)
        # Remove "WORD COUNT" lines
        narration_text = re.sub(r'\[?TOTAL WORD COUNT.*', '', narration_text, flags=re.IGNORECASE)
        # Clean up extra whitespace
        narration_text = re.sub(r'\n{2,}', '\n', narration_text).strip()
        # Final safety: if narration ends with stage direction-like text, strip it
        narration_text = re.sub(r'[.\s]*(sil[eê]ncio|apenas m[uú]sica|music only|logo|fade).*$', '.', narration_text, flags=re.IGNORECASE).strip()
        logger.info(f"Cleaned narration: {len(narration_text)} chars, ~{len(narration_text.split())} words")

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

    # 3. Check for logo image: first from company brand_data, then from uploaded_assets
    logo_path = None
    try:
        pipeline = supabase.table("pipelines").select("result").eq("id", pipeline_id).single().execute()
        result = pipeline.data.get("result", {}) if pipeline.data else {}
        
        # Try company logo from brand_data first
        brand_data = result.get("brand_data", {})
        logo_url = brand_data.get("logo_url", "") if brand_data else ""
        
        # Fallback to uploaded_assets
        if not logo_url:
            assets = result.get("uploaded_assets", [])
            backend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
            for asset in assets:
                url = asset.get("url", "") if isinstance(asset, dict) else str(asset)
                if url and any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                    if url.startswith('/'):
                        url = f"{backend_url}{url}"
                    logo_url = url
                    break
        
        if logo_url:
            logo_path = f"/tmp/{pipeline_id}_logo.png"
            urllib.request.urlretrieve(logo_url, logo_path)
            logger.info(f"Downloaded logo for video: {logo_url}")
        
        # Also enrich contact_cta from brand_data if not parsed from AI output
        if not contact_cta and brand_data:
            parts = []
            if brand_data.get("phone"):
                parts.append(brand_data["phone"])
            if brand_data.get("website_url"):
                parts.append(brand_data["website_url"])
            if parts:
                contact_cta = " | ".join(parts)
                logger.info(f"Using brand_data contact CTA: {contact_cta}")
        
        # Enrich brand_name from brand_data if not parsed
        if not brand_name and brand_data.get("company_name"):
            brand_name = brand_data["company_name"]
            
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

        # Add brand ending to presenter video (logo + contact info)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
            try:
                pipeline_rec = supabase.table("pipelines").select("result").eq("id", pipeline_id).single().execute()
                p_result = pipeline_rec.data.get("result", {}) if pipeline_rec.data else {}
                p_brand = p_result.get("brand_data", {})
                logo_url = p_brand.get("logo_url", "") if p_brand else ""
                p_contact = ""
                if p_brand:
                    parts = []
                    if p_brand.get("phone"): parts.append(p_brand["phone"])
                    if p_brand.get("website_url"): parts.append(p_brand["website_url"])
                    if parts: p_contact = " | ".join(parts)
                p_brand_name = brand_name or (p_brand.get("company_name", "") if p_brand else "")

                p_logo_path = None
                if logo_url:
                    p_logo_path = f"/tmp/{pipeline_id}_plogo.png"
                    import urllib.request as urlreq2
                    urlreq2.urlretrieve(logo_url, p_logo_path)

                # Apply branding overlay
                vid_dur = _ffprobe_duration(output_path) or 24.0
                b_start = max(vid_dur - 4, 18)
                b_mid = b_start + 0.5
                b_late = b_start + 1.0
                font = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
                def _safe(t):
                    if not t: return ""
                    for ch in ["'",'"',":",";",'[',']','(',')',',','%']:
                        t = t.replace(ch, " ")
                    return " ".join(t.split())

                branded_out = f"/tmp/{pipeline_id}_presenter_branded.mp4"
                branded_ok = False
                if p_logo_path and os.path.exists(p_logo_path):
                    scaled = f"/tmp/{pipeline_id}_plogo_s.png"
                    subprocess.run(f"{FFMPEG} -y -i {p_logo_path} -vf scale=240:-1 {scaled}", shell=True, capture_output=True, timeout=30)
                    if not os.path.exists(scaled): scaled = p_logo_path
                    vf = (f"[0:v]drawbox=x=0:y=0:w=iw:h=ih:color=black@1.0:t=fill:enable='between(t,{b_start},{vid_dur})'[bg];"
                          f"[1:v]scale=240:-1[logo];[bg][logo]overlay=(W-w)/2:(H/4)-(h/2):enable='between(t,{b_start},{vid_dur})'")
                    s_brand = _safe(p_brand_name)
                    if s_brand:
                        vf += f",drawtext=text='{s_brand}':fontfile={font}:fontsize=40:fontcolor=white:x=(w-text_w)/2:y=(h/2):enable='between(t,{b_mid},{vid_dur})'"
                    if p_contact:
                        vf += f",drawtext=text='{_safe(p_contact)}':fontfile={font}:fontsize=20:fontcolor=0xC9A84C@0.9:x=(w-text_w)/2:y=(h*3/5)+20:enable='between(t,{b_late},{vid_dur})'"
                    br = subprocess.run([FFMPEG, "-y", "-i", output_path, "-i", scaled, "-filter_complex", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", branded_out], capture_output=True, text=True, timeout=120)
                    branded_ok = br.returncode == 0 and os.path.exists(branded_out)
                
                if not branded_ok and p_brand_name:
                    tvf = f"drawbox=x=0:y=0:w=iw:h=ih:color=black@1.0:t=fill:enable='between(t,{b_start},{vid_dur})'"
                    tvf += f",drawtext=text='{_safe(p_brand_name)}':fontfile={font}:fontsize=60:fontcolor=white:x=(w-text_w)/2:y=(h/3):enable='between(t,{b_start},{vid_dur})'"
                    if p_contact:
                        tvf += f",drawtext=text='{_safe(p_contact)}':fontfile={font}:fontsize=20:fontcolor=0xC9A84C@0.9:x=(w-text_w)/2:y=(h*3/5)+20:enable='between(t,{b_late},{vid_dur})'"
                    br = subprocess.run([FFMPEG, "-y", "-i", output_path, "-vf", tvf, "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", branded_out], capture_output=True, text=True, timeout=120)
                    branded_ok = br.returncode == 0 and os.path.exists(branded_out)
                
                if branded_ok:
                    shutil.copy2(branded_out, output_path)
                    logger.info("Presenter video branding applied")
            except Exception as be:
                logger.warning(f"Presenter branding failed (non-fatal): {be}")

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
