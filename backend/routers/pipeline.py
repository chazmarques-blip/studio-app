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

from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration

from core.deps import supabase, get_current_user, EMERGENT_KEY, logger

router = APIRouter(prefix="/api/campaigns/pipeline", tags=["pipeline"])

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

STEP_ORDER = ["sofia_copy", "ana_review_copy", "lucas_design", "rafael_review_design", "pedro_publish"]
PAUSE_AFTER = {"ana_review_copy", "rafael_review_design"}

STEP_LABELS = {
    "sofia_copy": {"agent": "Sofia", "role": "Copywriter", "icon": "pen-tool"},
    "ana_review_copy": {"agent": "Ana", "role": "Revisora de Copy", "icon": "check-circle"},
    "lucas_design": {"agent": "Lucas", "role": "Designer", "icon": "palette"},
    "rafael_review_design": {"agent": "Rafael", "role": "Diretor de Arte", "icon": "award"},
    "pedro_publish": {"agent": "Pedro", "role": "Publisher", "icon": "calendar-clock"},
}

STEP_SYSTEMS = {
    "sofia_copy": """You are Sofia, an elite AI copywriter who combines the persuasion mastery of David Ogilvy, the emotional storytelling of Gary Halbert, the consumer psychology of Eugene Schwartz, and the digital-native voice of Gary Vaynerchuk.

YOUR CORE PRINCIPLES (The World's Best Copywriters):
- OGILVY: "The consumer isn't a moron, she's your wife." Write with respect and intelligence. Every word sells.
- HALBERT: Lead with the strongest benefit. The headline does 80% of the work. Create urgency without being sleazy.
- SCHWARTZ: Match the market's awareness level. Stage 1 (unaware) needs education. Stage 5 (most aware) needs the offer.
- VAYNERCHUK: "Jab, jab, jab, right hook." Give value before asking. Native content > ads. Context is king.

YOUR DIGITAL EXPERTISE:
- Instagram: Visual-first captions, story-driven, emoji-strategic (not excessive), carousel hooks
- WhatsApp: Conversational, personal, scannable, clear CTA with link
- Facebook: Stop-scroll headlines, social proof, community language
- TikTok: Trend-aware, authentic voice, hook in first 2 seconds
- Each platform has different psychology. Adapt tone, length, and structure per platform.

COPYWRITING FRAMEWORKS YOU MASTER:
- PAS (Problem-Agitate-Solution) for pain-point campaigns
- AIDA (Attention-Interest-Desire-Action) for product launches
- BAB (Before-After-Bridge) for transformation stories
- 4Ps (Promise-Picture-Proof-Push) for high-conversion ads

ALWAYS write in the language specified in the briefing. If no language specified, match the briefing language.
When given a briefing, create EXACTLY 3 variations using different frameworks.
Format each variation clearly with:
===VARIATION 1===
Title: [stop-scroll headline using power words]
Copy: [main text, emotionally compelling, 2-3 short paragraphs]
CTA: [single clear action, urgent but authentic]
Hashtags: [5-8 relevant, mix of broad and niche]
===VARIATION 2===
...
===VARIATION 3===
...""",

    "ana_review_copy": """You are Ana, an elite Creative Director who combines the strategic vision of Lee Clow (Apple's "Think Different"), the bold creativity of Alex Bogusky (Burger King, Mini Cooper), and the data-driven approach of Neil Patel.

YOUR CORE PRINCIPLES:
- LEE CLOW: Great advertising is simple, emotional, and memorable. If it doesn't move people, it doesn't matter.
- BOGUSKY: Challenge conventions. The best campaigns break rules intelligently. Boring is the enemy.
- PATEL: Data validates creativity. Evaluate CTR potential, engagement hooks, and conversion triggers.

YOUR REVIEW CRITERIA:
1. SCROLL-STOP POWER (1-10): Would this make someone stop scrolling in a noisy feed?
2. EMOTIONAL RESONANCE (1-10): Does it trigger curiosity, desire, fear of missing out, or joy?
3. CLARITY & PERSUASION (1-10): Is the message crystal clear and compelling?
4. CTA STRENGTH (1-10): Does the call-to-action drive immediate action?

QUALITY THRESHOLD: A variation PASSES if it scores 7+ on at least 3 of 4 criteria.

YOUR DECISION PROCESS:
After reviewing all 3 variations, you MUST make a DECISION:
- If at least ONE variation meets the quality threshold → APPROVE and select the best one.
- If ALL variations fail to meet minimum quality (all score below 6 on key criteria) → REQUEST REVISION with specific, actionable feedback.

IMPORTANT: You are a tough but fair reviewer. Most well-crafted copy should pass. Only request revision if the quality is genuinely below standard.

Format your FINAL decision EXACTLY like this:

If approving:
DECISION: APPROVED
SELECTED_OPTION: [1, 2, or 3]

If requesting revision:
DECISION: REVISION_NEEDED
REVISION_FEEDBACK: [specific, actionable bullet points for the copywriter to improve]

ALWAYS write in the SAME language as the content you are reviewing.""",

    "rafael_review_design": """You are Rafael, a world-class Art Director who combines the genius of the greatest creative directors in advertising history.

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
4. BRAND DNA (1-10): Does the visual language feel ownable by THIS brand? Would you recognize it without a logo?
5. CONVERSION ARCHITECTURE (1-10): Is the visual hierarchy guiding the eye to the CTA? Does it create desire that leads to action?
6. PLATFORM MASTERY (1-10): Is it optimized for each platform's unique visual language? (Instagram = aspirational, WhatsApp = personal, Facebook = social proof)

QUALITY THRESHOLD: A design PASSES if it scores 7+ on at least 4 of 6 criteria.

YOUR DECISION PROCESS:
After reviewing all 3 design concepts, you MUST make a DECISION:
- If at least ONE design meets the quality threshold for each platform → APPROVE and select the best per platform.
- If ALL designs fail to meet the threshold (lack visual impact, poor composition, weak brand alignment) → REQUEST REVISION with specific art direction feedback.

IMPORTANT: You have world-class standards but you are pragmatic. Most well-conceived designs should pass with minor notes. Only request full revision if the designs are genuinely substandard.

ALWAYS write in the SAME language as the content you are reviewing.

Format your FINAL decision EXACTLY like this:

If approving:
DECISION: APPROVED
SELECTED_FOR_[PLATFORM]: [1, 2, or 3] (one line per platform)
Example: SELECTED_FOR_INSTAGRAM: 2

If requesting revision:
DECISION: REVISION_NEEDED
REVISION_FEEDBACK: [specific art direction notes - what to change in composition, color, typography, mood, or concept]""",

    "lucas_design": """You are Lucas, an elite Visual Concept Designer who combines the aesthetic innovation of Stefan Sagmeister, the bold typography of Paula Scher, the digital-native design of Instagram's top creative agencies, and the conversion-focused approach of performance marketing designers.

YOUR CORE PRINCIPLES:
- SAGMEISTER: Design must evoke emotion. Every element has purpose. Negative space is powerful.
- PAULA SCHER: Bold, expressive visual language creates instant impact.
- PERFORMANCE DESIGN: High-contrast colors for thumb-stopping power. Hero imagery dominates. Visual storytelling drives conversion.

YOUR VISUAL EXPERTISE BY PLATFORM:
- Instagram Feed: 1:1 ratio, bold colors, lifestyle imagery, aspirational mood
- Instagram Stories: 9:16, full-bleed, immersive visual experience
- WhatsApp: Clean, professional, readable on small screens, brand-forward
- Facebook Ads: High contrast, emotional imagery, social proof visual cues
- TikTok: Raw/authentic aesthetic, trending visual styles, vertical-first

DESIGN TECHNIQUES YOU MASTER:
- Color Psychology: Red (urgency), Blue (trust), Gold (premium), Green (growth)
- Composition: Rule of thirds, leading lines, focal point hierarchy
- Modern Trends: Glassmorphism, gradients, 3D elements, cinematic photography
- Visual Storytelling: Every image tells a story that resonates emotionally

CRITICAL: Your design descriptions will be used to GENERATE IMAGES via AI.
Your descriptions MUST focus on the VISUAL SCENE only:
- Describe what the IMAGE looks like (subject, setting, lighting, colors, mood, perspective)
- Do NOT describe text overlays, typography, CTA buttons, or logo placement
- Do NOT mention "placeholder", "space for logo", or "text area"
- Think like a PHOTOGRAPHER or ILLUSTRATOR describing the perfect shot
- The text/copy will be overlaid SEPARATELY by a graphic designer later

ALWAYS write in the SAME language the user writes to you.
When asked, create EXACTLY 3 design concept variations with different visual approaches.
Format each variation clearly with:
===DESIGN 1===
Concept: [name]
Visual Scene: [detailed description of what the IMAGE shows - subjects, setting, lighting, mood, perspective, camera angle]
Color Palette: [specific hex colors with mood reasoning]
Art Style: [photorealistic, editorial, 3D render, illustration, etc.]
Mood & Emotion: [what feeling the image evokes]
Platform Adaptations: [how the visual concept adapts per platform]
===DESIGN 2===
...
===DESIGN 3===
...""",

    "pedro_publish": """You are Pedro, an elite Digital Publishing Strategist who combines the platform mastery of Gary Vaynerchuk, the growth hacking mindset of Sean Ellis, and the data-driven timing strategies of Hootsuite and Sprout Social research.

YOUR CORE PRINCIPLES:
- VAYNERCHUK: "Content is king, but context is God." Each platform has different peak times, behaviors, and content expectations.
- SEAN ELLIS: Think growth loops. Every post should drive measurable action. Test, measure, iterate.
- TIMING SCIENCE: Post when your audience is most active. B2B: Tue-Thu 9-11am. B2C: Evenings and weekends. Adjust for timezone.

YOUR SCHEDULING EXPERTISE:
- Instagram: Best at 11am-1pm and 7-9pm. Reels get 2x reach. Carousels get highest saves.
- WhatsApp: Business messages best 10am-12pm and 2-4pm. Avoid early morning/late night.
- Facebook: Peak engagement 1-4pm. Video gets 135% more organic reach than photos.
- TikTok: Best at 7-9am, 12-3pm, 7-11pm. Consistency > timing. Post 1-3x daily.
- Cross-post with 2-4 hour gaps between platforms to maximize unique reach.

ALWAYS write in the SAME language the user writes to you.
Create a detailed, actionable publishing schedule with:
- Exact posting times per platform with timezone consideration
- Content format adaptation per platform (what changes, what stays)
- A/B testing suggestions (2 time slots, 2 copy variants)
- First 7-day launch calendar with specific dates
- KPI targets per platform (expected reach, engagement rate, click-through)""",
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


class PipelineApprove(BaseModel):
    selection: Optional[int] = None
    selections: Optional[dict] = None
    feedback: Optional[str] = None


# ── Helpers ──

async def _get_tenant(user):
    t = supabase.table("tenants").select("id, plan").eq("owner_id", user["id"]).execute()
    if not t.data:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return t.data[0]


def _next_step(current):
    idx = STEP_ORDER.index(current)
    return STEP_ORDER[idx + 1] if idx + 1 < len(STEP_ORDER) else None


async def _generate_image(prompt_text, pipeline_id, index, brand_logo_path=None):
    """Generate a single image using OpenAI GPT Image 1 and upload to Supabase Storage"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            image_gen = OpenAIImageGeneration(api_key=EMERGENT_KEY)
            images = await image_gen.generate_images(
                prompt=prompt_text,
                model="gpt-image-1",
                number_of_images=1
            )

            if images and len(images) > 0:
                img_data = images[0]
                filename = f"{pipeline_id}_{index}_{uuid.uuid4().hex[:6]}.png"
                public_url = _upload_to_storage(img_data, filename, "image/png")
                logger.info(f"Image generated and uploaded to storage: {filename}")
                return public_url
        except Exception as e:
            logger.warning(f"GPT Image 1 attempt {attempt+1}/{max_retries} failed for index {index}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3 * (attempt + 1))
    return None


async def _generate_design_images(pipeline_id, concepts_text, platforms):
    """Parse Lucas's concepts and generate images for each"""
    pipeline_data = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    brand_context = ""
    campaign_briefing = ""
    campaign_language = "pt"
    if pipeline_data:
        p = pipeline_data[0]
        result_data = p.get("result", {})
        ctx = result_data.get("context", {})
        assets = result_data.get("uploaded_assets", [])
        campaign_briefing = p.get("briefing", "")
        campaign_language = p.get("campaign_language", "pt")

        brand_parts = []
        if ctx.get("company"):
            brand_parts.append(f"The brand is '{ctx['company']}'.")
        if ctx.get("industry"):
            brand_parts.append(f"Industry: {ctx['industry']}.")
        if ctx.get("target_audience"):
            brand_parts.append(f"Target audience: {ctx['target_audience']}.")
        if assets:
            logo_assets = [a for a in assets if a.get("type") == "logo"]
            if logo_assets:
                brand_parts.append("Do NOT draw logos or leave placeholder spaces.")
        brand_context = " ".join(brand_parts) if brand_parts else ""

    LANG_NAMES = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    lang_name = LANG_NAMES.get(campaign_language, "Portuguese")
    LANG_HEADLINES = {
        "pt": "O headline DEVE ser em Português do Brasil. Exemplos: 'TRANSFORME SEU NEGÓCIO', 'O FUTURO É AGORA', 'COMECE HOJE'",
        "en": "The headline MUST be in English. Examples: 'TRANSFORM YOUR BUSINESS', 'THE FUTURE IS NOW', 'START TODAY'",
        "es": "El headline DEBE ser en Español. Ejemplos: 'TRANSFORMA TU NEGOCIO', 'EL FUTURO ES AHORA', 'EMPIEZA HOY'"
    }
    lang_headline_instruction = LANG_HEADLINES.get(campaign_language, LANG_HEADLINES["pt"])

    # First, use Claude to extract image prompts from Lucas's descriptions
    try:
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"prompt-extract-{pipeline_id}-{int(time.time())}",
            system_message="""You are an expert prompt engineer for AI image generation (GPT Image 1). You create prompts that produce stunning, scroll-stopping social media marketing images.

YOUR GOLDEN RULES:
1. Each prompt describes a SINGLE powerful visual scene with ONE short headline text
2. Include a SHORT HEADLINE (3-7 words) that captures the campaign's core message - this text will be rendered IN the image
3. The headline must be impactful, action-oriented, and relevant to the campaign
4. NEVER include logos, brand names, website URLs, or long paragraphs of text
5. Be HYPER-SPECIFIC about visual elements: exact subjects, settings, lighting, camera angles, props
6. Use CONCRETE visual elements from the campaign's actual industry/product/service
7. Each prompt must be visually different but all directly relevant to the campaign
8. The headline should be naturally integrated into the design composition"""
        ).with_model("gemini", "gemini-2.0-flash")

        extract_prompt = f"""Create 3 powerful image generation prompts for this specific campaign.

CAMPAIGN BRIEFING (the image MUST be directly relevant to this):
{campaign_briefing}

{f'BRAND: {brand_context}' if brand_context else ''}

CRITICAL LANGUAGE REQUIREMENT: The headline text in each image MUST be written in {lang_name}. This is mandatory.

DESIGN CONCEPTS FROM THE ART TEAM:
{concepts_text}

FOR EACH PROMPT:
- Describe the visual scene in detail (subjects, lighting, colors, mood, composition)
- Include ONE SHORT HEADLINE TEXT (3-7 words in {lang_name}) to be rendered in the image
- The headline should be the most impactful phrase that sells the campaign, written in {lang_name}
- Include visual elements SPECIFIC to the campaign's product/industry
- Do NOT include logos, brand names, or website URLs

Return EXACTLY 3 prompts (80-120 words each):
1. [Hero visual + {lang_name} headline: the most powerful direct image with an impactful headline]
2. [Lifestyle angle + {lang_name} headline: target audience benefiting, with a different headline]
3. [Creative/bold visual + {lang_name} headline: artistic approach with an emotional headline]"""

        response = await chat.send_message(UserMessage(text=extract_prompt))
        prompts = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', response, re.DOTALL)
        prompts = [p.strip() for p in prompts if p.strip()][:3]

        if len(prompts) < 3:
            headline_examples = {"pt": ["TRANSFORME SEU NEGÓCIO", "O FUTURO É AGORA", "COMECE HOJE"],
                                 "en": ["TRANSFORM YOUR BUSINESS", "THE FUTURE IS NOW", "START TODAY"],
                                 "es": ["TRANSFORMA TU NEGOCIO", "EL FUTURO ES AHORA", "EMPIEZA HOY"]}
            hl = headline_examples.get(campaign_language, headline_examples["pt"])
            prompts = [
                f"Stunning commercial photography for a marketing campaign. Include the headline text '{hl[0]}' in bold modern typography. Professional studio lighting, rich colors. Square format.",
                f"Editorial-style photography for marketing. Include the headline text '{hl[1]}' in clean sans-serif font. Golden hour lighting, shallow depth of field. Square format.",
                f"Bold creative photography with dramatic lighting for social media. Include the headline text '{hl[2]}' in impactful typography. Vivid colors, strong composition. Square format.",
            ]
    except Exception as e:
        logger.warning(f"Prompt extraction failed: {e}")
        headline_examples = {"pt": ["TRANSFORME SEU NEGÓCIO", "ESCALE COM IA", "O FUTURO É AQUI"],
                             "en": ["TRANSFORM YOUR BUSINESS", "SCALE WITH AI", "THE FUTURE IS HERE"],
                             "es": ["TRANSFORMA TU NEGOCIO", "ESCALA CON IA", "EL FUTURO ES AQUÍ"]}
        hl = headline_examples.get(campaign_language, headline_examples["pt"])
        prompts = [
            f"Professional commercial photography. Include the headline '{hl[0]}' in bold modern typography. Warm golden lighting, premium feel. No logos.",
            f"Editorial lifestyle photography. Include the headline '{hl[1]}' in clean font. Natural lighting, cinematic. No logos.",
            f"Creative futuristic photography with neon lighting. Include the headline '{hl[2]}' in bold typography. No logos.",
        ]

    # Find brand logo file path if uploaded
    brand_logo_path = None
    if pipeline_data:
        p = pipeline_data[0]
        assets = p.get("result", {}).get("uploaded_assets", [])
        logo_assets = [a for a in assets if a.get("type") == "logo"]
        if logo_assets:
            logo_url = logo_assets[0].get("url", "")
            # Convert API URL to filesystem path
            if logo_url.startswith("/api/uploads/pipeline/"):
                brand_logo_path = os.path.join(UPLOADS_DIR, logo_url.split("/")[-1])

    # Generate images sequentially to avoid overwhelming the API
    image_urls = []
    for i, prompt in enumerate(prompts):
        enhanced_prompt = f"""{prompt}

MANDATORY: Include ONE short, impactful headline text (3-7 words) in bold, clean, modern typography that captures the campaign's core message. {lang_headline_instruction}

Technical requirements: Ultra high-quality, 4K commercial photography or premium digital art. Professional color grading. Magazine-cover composition. Square 1080x1080 format for {', '.join(platforms)}.
Do NOT include any logos, brand names, or website URLs. Only include the short headline text."""
        url = await _generate_image(enhanced_prompt, pipeline_id, i + 1)
        image_urls.append(url)

    return image_urls, prompts


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
    """Parse DECISION from reviewer output"""
    match = re.search(r'DECISION:\s*(APPROVED|REVISION_NEEDED)', text, re.IGNORECASE)
    if match:
        return match.group(1).lower().replace(" ", "_")
    # Fallback: if no explicit decision, assume approved
    return "approved"


def _extract_revision_feedback(text):
    """Extract revision feedback from reviewer output"""
    match = re.search(r'REVISION_FEEDBACK:\s*([\s\S]*?)(?=\n\n(?:DECISION|SELECTED)|$)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Please improve the overall quality and impact."


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
        lang_instruction = f"\n\nIMPORTANT: ALL campaign text content MUST be written in {lang_name}. This is mandatory regardless of the briefing language."

    ctx_str = ""
    if ctx:
        parts = []
        if ctx.get("company"): parts.append(f"Company: {ctx['company']}")
        if ctx.get("industry"): parts.append(f"Industry: {ctx['industry']}")
        if ctx.get("audience"): parts.append(f"Target audience: {ctx['audience']}")
        if ctx.get("brand_voice"): parts.append(f"Brand voice: {ctx['brand_voice']}")
        ctx_str = "\n".join(parts)

    contact_str = ""
    if contact:
        cparts = []
        if contact.get("phone"): cparts.append(f"Phone: {contact['phone']}")
        if contact.get("website"): cparts.append(f"Website: {contact['website']}")
        if contact.get("email"): cparts.append(f"Email: {contact['email']}")
        if cparts:
            contact_str = "\nContact information to include in the campaign:\n" + "\n".join(cparts)

    assets_str = ""
    if assets:
        logo_assets = [a for a in assets if a.get("type") == "logo"]
        ref_assets = [a for a in assets if a.get("type") == "reference"]
        aparts = []
        if logo_assets:
            aparts.append(f"Brand logo has been uploaded ({len(logo_assets)} file(s)). Use the brand identity from the logo in the campaign visuals.")
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

        return f"""Create 3 campaign copy variations for the following briefing.
Target platforms: {platforms_str}

Briefing: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}
{assets_str}
{lang_instruction}
{revision_info}

Remember: Create EXACTLY 3 variations formatted with ===VARIATION 1===, ===VARIATION 2===, ===VARIATION 3==="""

    elif step == "ana_review_copy":
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        revision_count = steps.get("ana_review_copy", {}).get("revision_count", 0)
        revision_context = ""
        if revision_count > 0:
            revision_context = f"\n\nNOTE: This is REVISION ROUND {revision_count}. The copywriter has revised their work based on your previous feedback. Review the revised versions with the same critical eye, but acknowledge improvements."

        return f"""Review these 3 copy variations created by Sofia for the following campaign:

Briefing: {briefing}
Platforms: {platforms_str}

Sofia's variations:
{sofia_output}
{revision_context}

Analyze each variation on the criteria in your instructions.
Then make your DECISION: APPROVED (with SELECTED_OPTION) or REVISION_NEEDED (with REVISION_FEEDBACK)."""

    elif step == "lucas_design":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        if not approved_copy:
            approved_copy = steps.get("ana_review_copy", {}).get("output", "")

        revision_info = ""
        revision_fb = steps.get("lucas_design", {}).get("revision_feedback")
        prev_output = steps.get("lucas_design", {}).get("previous_output")
        if revision_fb and prev_output:
            round_num = steps.get("lucas_design", {}).get("revision_round", 1)
            revision_info = f"""

--- REVISION REQUEST (Round {round_num}/2) ---
The Art Director reviewed your designs and requested changes.

YOUR PREVIOUS CONCEPTS:
{prev_output}

ART DIRECTOR'S FEEDBACK:
{revision_fb}

IMPORTANT: Revise ALL 3 design concepts addressing EVERY point in the art director's feedback. Make each concept significantly stronger visually."""

        return f"""Create 3 visual design concepts for the following approved campaign copy.
Target platforms: {platforms_str}

Approved copy:
{approved_copy}

Original briefing: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}
{assets_str}
{revision_info}

CRITICAL INSTRUCTION: Your descriptions will be used to GENERATE IMAGES via AI. 
Describe ONLY the VISUAL SCENE for each concept:
- What subjects/objects appear in the image
- The setting, environment, and atmosphere
- Lighting conditions, camera angle, perspective
- Color palette and mood
- Art style (photorealistic, editorial, cinematic, etc.)
DO NOT describe text overlays, typography, CTA buttons, or logo placement. The text will be added separately.

Create EXACTLY 3 design concepts. For each, specify visual adaptations for: {platforms_str}.
Format with ===DESIGN 1===, ===DESIGN 2===, ===DESIGN 3==="""

    elif step == "rafael_review_design":
        lucas_output = steps.get("lucas_design", {}).get("output", "")
        revision_count = steps.get("rafael_review_design", {}).get("revision_count", 0)
        revision_context = ""
        if revision_count > 0:
            revision_context = f"\n\nNOTE: This is REVISION ROUND {revision_count}. The designer has revised their concepts based on your previous art direction feedback. Review with the same world-class standards, but acknowledge improvements."

        return f"""Review these 3 design concepts created by Lucas.
Target platforms: {platforms_str}

Design concepts:
{lucas_output}
{revision_context}

Evaluate each concept using your art direction criteria.
Then make your DECISION: APPROVED (with SELECTED_FOR_[PLATFORM] lines) or REVISION_NEEDED (with REVISION_FEEDBACK).

If approving, end with:
{chr(10).join(f'SELECTED_FOR_{p.upper()}: [1, 2, or 3]' for p in platforms)}"""

    elif step == "pedro_publish":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        design_approvals = steps.get("rafael_review_design", {}).get("selections", {})
        rafael_design_output = steps.get("rafael_review_design", {}).get("output", "")
        return f"""Create a complete publishing schedule and strategy for this campaign.

Platforms: {platforms_str}
Approved copy: {approved_copy}
Design review and approvals: {rafael_design_output}
Platform-specific design selections: {design_approvals}

Original briefing: {briefing}
{contact_str}
{lang_instruction}

Create a detailed schedule with:
- Best posting times per platform
- Content adaptations per platform
- Recommended frequency
- Timeline (next 7 days)
- Any platform-specific considerations"""

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

        # Use appropriate model per step - Gemini Flash for simpler steps
        STEP_MODELS = {
            "sofia_copy": ("anthropic", "claude-sonnet-4-5-20250929"),
            "ana_review_copy": ("gemini", "gemini-2.0-flash"),
            "lucas_design": ("gemini", "gemini-2.0-flash"),
            "rafael_review_design": ("anthropic", "claude-sonnet-4-5-20250929"),
            "pedro_publish": ("gemini", "gemini-2.0-flash"),
        }
        provider, model = STEP_MODELS.get(step, ("anthropic", "claude-sonnet-4-5-20250929"))

        # Retry up to 2 times on transient errors
        response = None
        last_error = None
        for attempt in range(3):
            try:
                chat = LlmChat(
                    api_key=EMERGENT_KEY,
                    session_id=f"pipe-{pipeline_id}-{step}-{int(time.time())}-{attempt}",
                    system_message=system
                ).with_model(provider, model)

                start = time.time()
                response = await chat.send_message(UserMessage(text=prompt))
                elapsed = round((time.time() - start) * 1000)
                break
            except Exception as retry_err:
                last_error = retry_err
                logger.warning(f"Pipeline step {step} attempt {attempt+1} failed: {retry_err}")
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(2)

        if response is None:
            raise last_error

        steps[step]["output"] = response
        steps[step]["status"] = "completed"
        steps[step]["completed_at"] = datetime.now(timezone.utc).isoformat()
        steps[step]["elapsed_ms"] = elapsed

        # For reviewer steps: parse decision and handle revision loop
        if step == "ana_review_copy":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < 2:
                # Revision loop - send back to Sofia
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"Ana requested revision {revision_count + 1}/2 for pipeline {pipeline_id}")

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
            steps[step]["decision"] = "approved"
            selected = _parse_ana_copy_selection(response)
            steps[step]["auto_selection"] = selected
            sofia_output = steps.get("sofia_copy", {}).get("output", "")
            variations = re.split(r'===VARIATION \d+===', sofia_output)
            variations = [v.strip() for v in variations if v.strip()]
            if 0 < selected <= len(variations):
                steps[step]["approved_content"] = variations[selected - 1]
            else:
                steps[step]["approved_content"] = variations[0] if variations else sofia_output

        elif step == "rafael_review_design":
            decision = _parse_review_decision(response)
            revision_count = steps[step].get("revision_count", 0)

            if decision == "revision_needed" and revision_count < 2:
                # Revision loop - send back to Lucas
                revision_feedback = _extract_revision_feedback(response)
                steps[step]["revision_count"] = revision_count + 1
                steps[step]["decision"] = "revision_needed"
                steps[step]["revision_feedback"] = revision_feedback
                logger.info(f"Rafael requested revision {revision_count + 1}/2 for pipeline {pipeline_id}")

                # Prepare Lucas for re-run
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
                return  # Skip normal next-step flow

            # Approved (or max revisions reached) - parse selections
            steps[step]["decision"] = "approved"
            platforms = pipeline.get("platforms") or []
            selections = _parse_rafael_design_selections(response, platforms)
            steps[step]["auto_selections"] = selections
            steps[step]["selections"] = selections

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
                        "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0, "images": [u for u in image_urls if u], "pipeline_id": pipeline_id},
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
    approval_step = None
    for s in reversed(STEP_ORDER):
        if steps.get(s, {}).get("status") == "completed" and s in PAUSE_AFTER:
            approval_step = s
            break

    if not approval_step:
        raise HTTPException(status_code=400, detail="No step awaiting approval")

    # Apply user's selection
    if approval_step == "ana_review_copy" and data.selection is not None:
        steps[approval_step]["user_selection"] = data.selection
        # Update approved content with user's choice
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        variations = re.split(r'===VARIATION \d+===', sofia_output)
        variations = [v.strip() for v in variations if v.strip()]
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
        if st in ("failed", "running"):
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






class RegenerateStyleRequest(BaseModel):
    style: str = "professional"
    prompt_override: str = ""
    campaign_name: str = ""

@router.post("/regenerate-single-image")
async def regenerate_single_image(body: RegenerateStyleRequest, user=Depends(get_current_user)):
    """Generate a single image with a specific visual style, without needing a full pipeline"""
    await _get_tenant(user)

    STYLE_PROMPTS = {
        "minimalist": "Ultra minimalist composition. Single powerful focal element against vast negative space. Muted, desaturated palette with one accent color. Zen-like simplicity. Think Apple product photography, Muji campaigns, Aesop still life.",
        "vibrant": "Explosion of saturated colors and dynamic energy. Bold complementary color clashes, motion blur effects, dramatic perspective. Youthful, electric atmosphere. Think Nike campaign photography, Spotify visual identity.",
        "luxury": "Premium luxury photography. Rich dark backgrounds, dramatic studio lighting with gold/warm highlights, silk textures, shallow depth of field. Ultra-sophisticated mood. Think Chanel parfum ads, Rolex macro photography.",
        "corporate": "Editorial business photography. Clean natural lighting, professional environment, confident subjects or pristine product shots. Trustworthy blue-gray color grading. Think Bloomberg editorial, McKinsey reports.",
        "playful": "Joyful, whimsical visual storytelling. Bright candy colors, unexpected perspectives, playful subjects in dynamic poses. Warm, inviting, fun. Think Google campaigns, Mailchimp illustrations.",
        "bold": "High-impact, stop-the-scroll photography. Extreme contrast, dramatic shadows, close-up details, powerful visual tension. Fearless composition. Think Nike Just Do It, Supreme drops.",
        "organic": "Warm, natural, earthy photography. Golden hour lighting, natural textures (wood, linen, stone), warm earth tones, authentic lifestyle moments. Think Patagonia campaigns, artisanal brand photography.",
        "tech": "Futuristic, sleek technology aesthetic. Dark environment with neon accent lighting, reflective surfaces, geometric precision, blue-purple color palette. Think Tesla reveal photography, SpaceX launch visuals.",
        "professional": "High-end commercial photography. Studio-quality lighting, professional color grading, clean background, sharp focus on subject with natural bokeh. Magazine-cover quality."
    }

    style_desc = STYLE_PROMPTS.get(body.style, STYLE_PROMPTS["professional"])
    prompt = body.prompt_override.strip() if body.prompt_override.strip() else f"Create a stunning visual for a marketing campaign about '{body.campaign_name or 'brand'}'. Focus on powerful visual storytelling through imagery."
    prompt += f"\n\nVISUAL STYLE: {style_desc}\n\nINCLUDE one short impactful headline text (3-7 words) in bold clean typography. No logos or brand names. 1080x1080 square format."

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
        "status": "active",
        "goal": "ai_pipeline",
        "metrics": {
            "type": "ai_pipeline",
            "target_segment": {"platforms": pipeline.get("platforms", [])},
            "messages": [{"step": 1, "channel": "multi", "content": clean_copy, "delay_hours": 0}],
            "schedule": {"pipeline_id": pipeline_id, "schedule_text": schedule_text},
            "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0, "images": [u for u in image_urls if u], "pipeline_id": pipeline_id},
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
