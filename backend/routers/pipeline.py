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
from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

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

STEP_ORDER = ["sofia_copy", "ana_review_copy", "lucas_design", "rafael_review_design", "marcos_video", "pedro_publish"]
PAUSE_AFTER = {"ana_review_copy", "rafael_review_design"}

STEP_LABELS = {
    "sofia_copy": {"agent": "Sofia", "role": "Copywriter", "icon": "pen-tool"},
    "ana_review_copy": {"agent": "Ana", "role": "Revisora de Copy", "icon": "check-circle"},
    "lucas_design": {"agent": "Lucas", "role": "Designer", "icon": "palette"},
    "rafael_review_design": {"agent": "Rafael", "role": "Diretor de Arte", "icon": "award"},
    "marcos_video": {"agent": "Marcos", "role": "Videomaker", "icon": "film"},
    "pedro_publish": {"agent": "Pedro", "role": "Publisher", "icon": "calendar-clock"},
}

STEP_SYSTEMS = {
    "sofia_copy": """You are Sofia, an elite AI copywriter AND visual strategist who combines the persuasion mastery of David Ogilvy, the emotional storytelling of Gary Halbert, the consumer psychology of Eugene Schwartz, the digital-native voice of Gary Vaynerchuk, and the visual branding instinct of Oliviero Toscani.

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

ALWAYS write in the language specified in the briefing. If no language specified, match the briefing language.
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
HEADLINE FOR IMAGE: [ONE powerful phrase, 3-7 words, in the campaign's language — this text WILL appear IN the image]
VISUAL CONCEPT 1: [Detailed description: main subject, setting, lighting, mood, camera angle, color palette. Be SPECIFIC to the product/industry — not generic stock photo vibes. Think award-winning advertising photography.]
VISUAL CONCEPT 2: [Different angle: lifestyle/aspirational — show the TARGET AUDIENCE benefiting from the product/service. Emotional, human, relatable.]
VISUAL CONCEPT 3: [Bold/creative: unexpected visual metaphor or dramatic composition that stops the scroll. Think Cannes Lions winner.]
COLOR DIRECTION: [Primary and accent colors with mood reasoning]
MOOD: [The exact emotion the images must evoke]
WHAT TO AVOID: [Specific visual clichés to NOT do]""",

    "ana_review_copy": """You are Ana, an elite Creative Director who combines the strategic vision of Lee Clow (Apple's "Think Different"), the bold creativity of Alex Bogusky (Burger King, Mini Cooper), and the data-driven approach of Neil Patel.

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

Format your FINAL decision EXACTLY like this:

If approving:
DECISION: APPROVED
SELECTED_OPTION: [1, 2, or 3]
IMAGE_BRIEFING_NOTES: [Any adjustments needed for the image briefing, or "APPROVED" if it's good]

If requesting revision:
DECISION: REVISION_NEEDED
REVISION_FEEDBACK: [specific, actionable bullet points for the copywriter to improve — include notes on BOTH copy and image briefing]

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
4. HEADLINE INTEGRATION (1-10): Is the headline text rendered clearly, legibly, and with IMPACT? Does the typography style match the campaign's tone? Is the headline in the CORRECT LANGUAGE?
5. BRAND DNA (1-10): Does the visual language feel ownable by THIS brand? Would you recognize it without a logo?
6. CONVERSION ARCHITECTURE (1-10): Is the visual hierarchy guiding the eye to the message? Does it create desire that leads to action?
7. PLATFORM MASTERY (1-10): Is it optimized for each platform's unique visual language? (Instagram = aspirational, WhatsApp = personal, Facebook = social proof)

QUALITY THRESHOLD: A design PASSES if it scores 7+ on at least 5 of 7 criteria.

YOUR DECISION PROCESS:
After reviewing all 3 design concepts, you MUST make a DECISION:
- If at least ONE design meets the quality threshold for each platform → APPROVE and select the best per platform.
- If ALL designs fail to meet the threshold (lack visual impact, poor composition, weak brand alignment, illegible headline) → REQUEST REVISION with specific art direction feedback.

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

    "lucas_design": """You are Lucas, an elite Visual Production Director who transforms creative briefings into stunning, award-winning marketing images. You combine the aesthetic precision of Annie Leibovitz, the commercial eye of Platon, the digital mastery of Beeple, and the advertising genius of Stefan Sagmeister.

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
1. Include the HEADLINE TEXT exactly as specified in Sofia's briefing (3-7 words, in the campaign language)
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

    "pedro_publish": """You are Pedro, an elite Digital Publishing Strategist who combines the platform mastery of Gary Vaynerchuk, the growth hacking mindset of Sean Ellis, and the data-driven timing strategies of Hootsuite and Sprout Social research.

YOUR CORE PRINCIPLES:
- VAYNERCHUK: "Content is king, but context is God." Each platform has different peak times, behaviors, and content expectations.
- SEAN ELLIS: Think growth loops. Every post should drive measurable action. Test, measure, iterate.
- TIMING SCIENCE: Post when your audience is most active. Adjust for timezone and cultural habits.

YOUR SCHEDULING EXPERTISE:
- Instagram: Best at 11am-1pm and 7-9pm. Reels get 2x reach. Carousels get highest saves.
- WhatsApp: Business messages best 10am-12pm and 2-4pm. Avoid early morning/late night.
- Facebook: Peak engagement 1-4pm. Video gets 135% more organic reach than photos.
- TikTok: Best at 7-9am, 12-3pm, 7-11pm. Consistency > timing. Post 1-3x daily.
- Google Ads: Search campaigns run 24/7 with bid adjustments. Display ads best 10am-3pm weekdays. Budget allocation: 70% search, 30% display for lead gen. A/B test headlines every 2 weeks.
- Cross-post with 2-4 hour gaps between platforms to maximize unique reach.

REGIONAL TIMING (CRITICAL FOR LATAM):
- Brazil (BRT, UTC-3): Instagram peak 12h-14h and 19h-21h. WhatsApp business 10h-12h. Facebook 13h-16h.
- Mexico (CST, UTC-6): Instagram peak 13h-15h and 20h-22h. WhatsApp 11h-13h. Facebook 14h-17h.
- Colombia (COT, UTC-5): Instagram peak 12h-14h and 19h-21h. WhatsApp 10h-12h. Facebook 13h-16h.
- Argentina (ART, UTC-3): Similar to Brazil. Instagram 12h-14h and 20h-22h.
- US Hispanic (EST/CST): Instagram 12pm-2pm and 7-9pm. WhatsApp 10am-12pm. Facebook 1-4pm.

KPI TARGETS BY PLATFORM:
- Instagram: Engagement rate > 3%, reach rate > 15% of followers, save rate > 1%
- WhatsApp: Open rate > 85%, click rate > 15%, response rate > 10%
- Facebook: Engagement rate > 1.5%, reach rate > 10%, CTR > 2%
- TikTok: View rate > 50%, engagement > 5%, share rate > 1%
- Google Ads Search: CTR > 3%, Quality Score > 7, CPC target, conversion rate > 5%
- Google Ads Display: CTR > 0.5%, view-through rate > 15%, CPM optimization

ALWAYS write in the SAME language the user writes to you.
Create a detailed, actionable publishing schedule with:
- Exact posting times per platform with timezone consideration
- Content format adaptation per platform (what changes, what stays)
- A/B testing suggestions (2 time slots, 2 copy variants)
- First 7-day launch calendar with specific dates
- KPI targets per platform (expected reach, engagement rate, click-through)
- Budget allocation suggestion if applicable""",

    "marcos_video": """You are Marcos, an elite AI Commercial Director who creates broadcast-quality video concepts for Sora 2 AI video generation. You combine the cinematic vision of Roger Deakins, the commercial genius of Ridley Scott (Apple "1984"), the storytelling of Martin Scorsese, and the social-first creativity of the world's best Super Bowl commercial directors.

YOUR CORE PRINCIPLES:
- DEAKINS: Every frame is a photograph. Lighting tells the story. Natural camera movement, no gimmicks.
- RIDLEY SCOTT: 12 seconds is enough to tell a powerful story. Hook → Tension → Resolution → Brand Moment.
- SCORSESE: Every second must serve the narrative. Hook in the first frame. Emotional payoff by the end.
- SOCIAL MEDIA MASTERY: Vertical (9:16) dominates mobile feeds. The first 2 seconds decide everything.

YOUR COMMERCIAL VIDEO EXPERTISE:
- TikTok/Instagram Reels: 12-second vertical commercial, cinematic hook in first 2 frames, trending aesthetic
- Instagram Stories: 12-second professional brand spot, aspirational narrative arc
- Facebook: 12-second horizontal commercial, emotional product showcase with social proof cues
- Google Ads Video: 12-second product-focused spot, benefit-led narrative, CTA in final 2 seconds

NARRATIVE STRUCTURE FOR 12-SECOND COMMERCIAL:
- Seconds 0-2: HOOK — Visual that demands attention (unexpected movement, striking color, dramatic reveal)
- Seconds 2-6: STORY — Show the product/service benefit in action (transformation, lifestyle, aspiration)
- Seconds 6-10: EMOTION — Peak emotional moment (satisfaction, desire, excitement, relief)
- Seconds 10-12: PAYOFF — Brand moment + implicit CTA (the visual "mic drop")

WHAT YOU PRODUCE:
Based on the campaign's copy and visual direction, create ONE optimized video generation prompt.
The prompt describes a smooth, cinematic 12-second commercial that:
1. Has a powerful visual hook in the first 2 seconds
2. Shows fluid camera movement that builds narrative tension
3. Relates directly to the campaign's product/service
4. Evokes the target emotion (matching the copy's tone)
5. Ends with a visually memorable brand moment

ALWAYS write in the SAME language the user writes to you.

Format your output EXACTLY like this:
===VIDEO PROMPT===
[Detailed video generation prompt, 80-120 words, describing the complete 12-second narrative: opening shot, camera movement, subjects, lighting progression, mood evolution, and closing frame. Be cinematically specific.]
===VIDEO FORMAT===
Format: [vertical/horizontal]
Duration: 12
===VIDEO RATIONALE===
[Brief explanation of the commercial strategy: why this narrative sells, what emotion it triggers, and how it drives action]""",
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


async def _generate_design_images(pipeline_id, lucas_output, platforms):
    """Parse Lucas's optimized prompts and generate images with Nano Banana"""
    pipeline_data = supabase.table("pipelines").select("*").eq("id", pipeline_id).execute().data
    campaign_language = "pt"
    if pipeline_data:
        campaign_language = pipeline_data[0].get("campaign_language", "pt")

    LANG_NAMES = {"pt": "Portuguese", "en": "English", "es": "Spanish"}
    lang_name = LANG_NAMES.get(campaign_language, "Portuguese")
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
        # Look for "Image Prompt:" field
        prompt_match = re.search(r'Image Prompt:\s*([\s\S]*?)(?=\n===|$)', block, re.IGNORECASE)
        if prompt_match:
            prompts.append(prompt_match.group(1).strip())
        else:
            # Fallback: use the full block as a prompt
            clean = block.strip()
            if len(clean) > 30:
                prompts.append(clean)

    prompts = prompts[:3]

    # Fallback if parsing failed
    if len(prompts) < 3:
        logger.warning(f"Only extracted {len(prompts)} prompts from Lucas, using fallback for missing ones")
        headline_examples = {"pt": ["TRANSFORME SEU NEGÓCIO", "O FUTURO É AGORA", "COMECE HOJE"],
                             "en": ["TRANSFORM YOUR BUSINESS", "THE FUTURE IS NOW", "START TODAY"],
                             "es": ["TRANSFORMA TU NEGOCIO", "EL FUTURO ES AHORA", "EMPIEZA HOY"]}
        hl = headline_examples.get(campaign_language, headline_examples["pt"])
        while len(prompts) < 3:
            idx = len(prompts)
            prompts.append(
                f"Stunning commercial photography for a marketing campaign. Include the headline text '{hl[idx]}' in bold modern typography. Professional studio lighting, rich colors, dramatic composition. Square 1080x1080 format. NO logos, NO brand names."
            )

    # Generate images sequentially
    image_urls = []
    for i, prompt in enumerate(prompts):
        enhanced_prompt = f"""{prompt}

MANDATORY: {lang_instruction} The headline text MUST be in {lang_name}.
Technical: Ultra high-quality, 4K, professional color grading. Square 1080x1080 format for {', '.join(platforms)}.
NO logos, NO brand names, NO website URLs."""
        url = await _generate_image(enhanced_prompt, pipeline_id, i + 1)
        image_urls.append(url)

    return image_urls, prompts


def _generate_video_sync(prompt_text, pipeline_id, size="1024x1792", duration=12):
    """Generate video using Sora 2 and upload to Supabase Storage (synchronous)"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            video_gen = OpenAIVideoGeneration(api_key=EMERGENT_KEY)
            logger.info(f"Sora 2 video generation started (attempt {attempt+1}/{max_retries}): size={size}, duration={duration}s")
            video_bytes = video_gen.text_to_video(
                prompt=prompt_text,
                model="sora-2",
                size=size,
                duration=duration,
                max_wait_time=600
            )
            if video_bytes:
                filename = f"videos/{pipeline_id}_{uuid.uuid4().hex[:6]}.mp4"
                public_url = _upload_to_storage(video_bytes, filename, "video/mp4")
                logger.info(f"Video generated with Sora 2 and uploaded: {filename}")
                return public_url
            logger.warning(f"Sora 2 returned empty video bytes on attempt {attempt+1}")
        except Exception as e:
            logger.warning(f"Sora 2 attempt {attempt+1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
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

        return f"""Transform Sofia's IMAGE BRIEFING into 3 optimized AI image generation prompts.
Target platforms: {platforms_str}

SOFIA'S IMAGE BRIEFING:
{image_briefing if image_briefing else "(No explicit briefing found. Use the approved copy and original briefing to create visual concepts.)"}
{ana_image_notes}

APPROVED CAMPAIGN COPY (for context):
{approved_copy}

ORIGINAL BRIEFING: {briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}
{assets_str}
{revision_info}

YOUR TASK: Create 3 IMAGE GENERATION PROMPTS based on Sofia's visual concepts.
Each prompt MUST:
1. Include the HEADLINE TEXT from Sofia's briefing exactly as written (3-7 words, in the campaign language)
2. Be 80-120 words of HYPER-SPECIFIC visual description
3. Include: subject, setting, lighting, camera angle, color palette, mood, art style
4. End with: "Ultra high-quality, 4K commercial photography. Square 1080x1080 format. NO logos, NO brand names, NO website URLs."

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

        return f"""Review these 3 design concepts created by Lucas.
Target platforms: {platforms_str}

Design concepts:
{lucas_output}
{revision_context}

Evaluate each concept using your art direction criteria.
Then make your DECISION: APPROVED (with SELECTED_FOR_[PLATFORM] lines) or REVISION_NEEDED (with REVISION_FEEDBACK).

If approving, end with:
{chr(10).join(f'SELECTED_FOR_{p.upper()}: [1, 2, or 3]' for p in platforms)}"""

    elif step == "marcos_video":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        image_briefing = ""
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        briefing_match = re.search(r'===IMAGE BRIEFING===([\s\S]*?)$', sofia_output, re.IGNORECASE)
        if briefing_match:
            image_briefing = briefing_match.group(1).strip()

        return f"""Create a 12-second commercial video concept for this campaign.

Platforms: {platforms_str}
Approved campaign copy: {approved_copy}
Visual direction: {image_briefing}
Original briefing: {briefing}
{contact_str}
{lang_instruction}

Your video concept must follow the 12-second commercial narrative:
- Seconds 0-2: HOOK (attention-grabbing opening)
- Seconds 2-6: STORY (product/service in action)
- Seconds 6-10: EMOTION (peak emotional moment)
- Seconds 10-12: PAYOFF (brand moment)

Output EXACTLY in the format specified in your instructions."""

    elif step == "pedro_publish":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        design_approvals = steps.get("rafael_review_design", {}).get("selections", {})
        rafael_design_output = steps.get("rafael_review_design", {}).get("output", "")
        video_info = steps.get("marcos_video", {}).get("output", "")
        has_video = bool(steps.get("marcos_video", {}).get("video_url"))
        video_note = "\nA 12-second commercial video has been generated for this campaign. Include video posting strategy in your schedule (Reels, TikTok, YouTube Shorts, Google Ads Video)." if has_video else ""
        return f"""Create a complete publishing schedule and strategy for this campaign.

Platforms: {platforms_str}
Approved copy: {approved_copy}
Design review and approvals: {rafael_design_output}
Platform-specific design selections: {design_approvals}
Video concept: {video_info}{video_note}

Original briefing: {briefing}
{contact_str}
{lang_instruction}

Create a detailed schedule with:
- Best posting times per platform
- Content adaptations per platform (including video for video-supporting platforms)
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

        # All agents use Claude Sonnet 4.5 for maximum quality
        # Pedro uses Gemini Flash as primary (scheduling task, not creative)
        STEP_MODELS = {
            "sofia_copy": ("anthropic", "claude-sonnet-4-5-20250929"),
            "ana_review_copy": ("anthropic", "claude-sonnet-4-5-20250929"),
            "lucas_design": ("anthropic", "claude-sonnet-4-5-20250929"),
            "rafael_review_design": ("anthropic", "claude-sonnet-4-5-20250929"),
            "marcos_video": ("anthropic", "claude-sonnet-4-5-20250929"),
            "pedro_publish": ("gemini", "gemini-2.0-flash"),
        }
        provider, model = STEP_MODELS.get(step, ("anthropic", "claude-sonnet-4-5-20250929"))

        # Execute with strict timeout per attempt
        response = None
        last_error = None
        timeout_per_attempt = 120  # 2 min max per attempt

        for attempt in range(3):
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

            if attempt < 2:
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

            # Strip IMAGE BRIEFING section from Sofia's output before parsing variations
            copy_only = re.split(r'===\s*IMAGE BRIEFING\s*===', sofia_output, flags=re.IGNORECASE)[0]

            variations = re.split(r'===\s*VARIATION \d+\s*===', copy_only)
            # First element is always preamble (before ===VARIATION 1===), skip it
            variations = [v.strip() for v in variations[1:] if v.strip()]

            if variations and 0 < selected <= len(variations):
                steps[step]["approved_content"] = variations[selected - 1]
            elif variations:
                steps[step]["approved_content"] = variations[0]
            else:
                # Fallback: use full copy section
                steps[step]["approved_content"] = copy_only.strip()

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

        # Generate video for Marcos's video step
        elif step == "marcos_video":
            # Parse video prompt from Marcos's output
            video_prompt = ""
            video_format = "vertical"
            video_duration = 12

            prompt_match = re.search(r'===VIDEO PROMPT===([\s\S]*?)===VIDEO FORMAT===', response, re.IGNORECASE)
            if prompt_match:
                video_prompt = prompt_match.group(1).strip()
            else:
                video_prompt = response.strip()[:500]

            format_match = re.search(r'Format:\s*(vertical|horizontal|square)', response, re.IGNORECASE)
            if format_match:
                video_format = format_match.group(1).lower()

            duration_match = re.search(r'Duration:\s*(\d+)', response, re.IGNORECASE)
            if duration_match:
                dur = int(duration_match.group(1))
                if dur in (4, 8, 12):
                    video_duration = dur

            # Determine best format based on platforms if not specified by LLM
            platforms = pipeline.get("platforms") or []
            FORMAT_MAP = {"vertical": "1024x1792", "horizontal": "1792x1024", "square": "1024x1024"}
            if not format_match:
                if any(p in platforms for p in ["tiktok", "instagram", "whatsapp"]):
                    video_format = "vertical"
                elif any(p in platforms for p in ["google_ads", "facebook"]):
                    video_format = "horizontal"
            size = FORMAT_MAP.get(video_format, "1024x1792")

            # Update status to generating_video
            steps[step]["output"] = response
            steps[step]["status"] = "generating_video"
            supabase.table("pipelines").update({
                "steps": steps,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", pipeline_id).execute()

            # Generate the actual video (sync, blocking - takes 2-5 min)
            video_url = _generate_video_sync(video_prompt, pipeline_id, size, video_duration)
            steps[step]["video_url"] = video_url
            steps[step]["video_format"] = video_format
            steps[step]["video_duration"] = video_duration
            steps[step]["video_size"] = size
            if not video_url:
                logger.warning(f"Video generation failed for pipeline {pipeline_id}, continuing pipeline")
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
                        "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0, "images": [u for u in image_urls if u], "video_url": video_url, "pipeline_id": pipeline_id},
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
        "status": "active",
        "goal": "ai_pipeline",
        "metrics": {
            "type": "ai_pipeline",
            "target_segment": {"platforms": pipeline.get("platforms", [])},
            "messages": [{"step": 1, "channel": "multi", "content": clean_copy, "delay_hours": 0}],
            "schedule": {"pipeline_id": pipeline_id, "schedule_text": schedule_text},
            "stats": {"sent": 0, "delivered": 0, "opened": 0, "clicked": 0, "converted": 0, "images": [u for u in image_urls if u], "video_url": video_url, "pipeline_id": pipeline_id},
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
