"""Book Generator — PDF Storybook Export and Interactive Book data.

Creates:
1. Cover image (via Gemini) with characters and creative title
2. PDF storybook with cover + illustrated pages
3. Structured JSON data for the Interactive Book reader
"""
import os
import io
import base64
import asyncio
import logging
import tempfile
import urllib.request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")


def _download_image_bytes(url: str) -> bytes:
    """Download image from URL or Supabase storage path."""
    supabase_url = os.environ.get('SUPABASE_URL', '')
    full_url = url if not url.startswith("/") else f"{supabase_url}/storage/v1/object/public{url}"
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    try:
        urllib.request.urlretrieve(full_url, tmp.name)
        with open(tmp.name, "rb") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"BookGen: Failed to download {full_url}: {e}")
        return None
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


def generate_cover_image(
    project_name: str,
    characters: list,
    char_avatars: dict,
    production_design: dict,
    lang: str = "pt",
) -> bytes:
    """Generate a book cover image using Gemini with all main characters."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        return None

    character_bible = production_design.get("character_bible", {}) if production_design else {}
    char_desc = ""
    ref_images = []
    for c in characters:
        name = c if isinstance(c, str) else c.get("name", "")
        desc = character_bible.get(name, "")
        if desc:
            char_desc += f"\n- {name}: {desc}"
        url = char_avatars.get(name)
        if url:
            img_bytes = _download_image_bytes(url)
            if img_bytes:
                ref_images.append(ImageContent(base64.b64encode(img_bytes).decode('utf-8')))

    lang_name = {"pt": "Portugues", "en": "English", "es": "Espanol"}.get(lang, "Portugues")

    prompt = f"""Generate a BOOK COVER illustration for a children's animated storybook.

STORY TITLE: {project_name}

MAIN CHARACTERS:{char_desc if char_desc else ' Use the characters from the reference images'}

DESIGN INSTRUCTIONS:
- Create a beautiful, eye-catching book cover suitable for a children's storybook
- Show ALL main characters together in a dynamic, inviting composition
- The scene should capture the essence and emotion of the story
- Use warm, rich colors with volumetric lighting
- Style: Premium 3D CGI animation (Pixar/DreamWorks quality)
- DO NOT include any text, titles, or labels — just the illustration
- The image should work as a full book cover (portrait orientation feel)
- Characters MUST match the reference images EXACTLY
- Make it magical, inviting, and full of wonder
- Language context: {lang_name}"""

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=f"cover-{datetime.now(timezone.utc).timestamp()}",
            system_message="You are a professional children's book cover artist."
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        if ref_images:
            msg = UserMessage(text=f"{prompt}\n\nCharacter reference images:", file_contents=ref_images)
        else:
            msg = UserMessage(text=prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        if images and len(images) > 0:
            return base64.b64decode(images[0]['data'])
        return None

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(_gen())).result(timeout=90)
    else:
        return asyncio.run(_gen())


def generate_creative_title(project_name: str, scenes: list, lang: str = "pt") -> str:
    """Generate a creative book title using Claude."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    api_key = EMERGENT_LLM_KEY
    if not api_key:
        return project_name

    scene_summary = ""
    for s in scenes[:5]:
        scene_summary += f"\n- {s.get('title', '')}: {s.get('description', '')[:100]}"

    lang_name = {"pt": "Portugues", "en": "English", "es": "Espanol"}.get(lang, "Portugues")

    async def _gen():
        chat = LlmChat(
            api_key=api_key,
            session_id=f"title-{datetime.now(timezone.utc).timestamp()}",
            system_message=f"You are a creative children's book author writing in {lang_name}. Respond with ONLY the title, nothing else."
        )
        chat.with_model("anthropic", "claude-sonnet-4-20250514")
        msg = UserMessage(
            text=f"Create a SHORT, creative, poetic title for a children's storybook. The original working title is: '{project_name}'. Here are some scenes:{scene_summary}\n\nRespond with ONLY the title in {lang_name} (max 8 words, no quotes)."
        )
        resp = await chat.send_message(msg)
        title = resp.strip().strip('"').strip("'")
        return title if len(title) < 100 else project_name

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(lambda: asyncio.run(_gen())).result(timeout=30)
    else:
        return asyncio.run(_gen())


def generate_pdf_storybook(
    project_name: str,
    creative_title: str,
    panels: list,
    cover_url: str = None,
    lang: str = "pt",
) -> bytes:
    """Generate a PDF storybook from storyboard panels.

    Returns PDF bytes.
    """
    from fpdf import FPDF
    from PIL import Image as PILImage

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False)
    page_w, page_h = 297, 210

    # --- Cover Page ---
    pdf.add_page()
    if cover_url:
        cover_bytes = _download_image_bytes(cover_url)
        if cover_bytes:
            tmp_cover = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp_cover.write(cover_bytes)
            tmp_cover.close()
            try:
                pdf.image(tmp_cover.name, x=0, y=0, w=page_w, h=page_h)
            except Exception as e:
                logger.warning(f"BookGen PDF: Cover image failed: {e}")
            finally:
                os.unlink(tmp_cover.name)

    # Title overlay on cover
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(20, page_h - 60)
    pdf.cell(page_w - 40, 20, creative_title, align='C')
    pdf.set_font("Helvetica", "", 14)
    pdf.set_xy(20, page_h - 35)
    subtitle = {"pt": "Um livro ilustrado", "en": "An illustrated storybook", "es": "Un libro ilustrado"}.get(lang, "Um livro ilustrado")
    pdf.cell(page_w - 40, 10, subtitle, align='C')

    # --- Story Pages ---
    sorted_panels = sorted(panels, key=lambda p: p.get("scene_number", 0))

    for panel in sorted_panels:
        frames = panel.get("frames", [])
        images_to_use = sorted(frames, key=lambda f: f.get("frame_number", 0)) if frames else []

        if not images_to_use and panel.get("image_url"):
            images_to_use = [{"image_url": panel["image_url"], "label": panel.get("title", "")}]

        scene_title = panel.get("title", f"Cena {panel.get('scene_number', '')}")
        dialogue = panel.get("dialogue", "")
        description = panel.get("description", "")

        for fi, frame in enumerate(images_to_use):
            pdf.add_page()
            img_url = frame.get("image_url", "")
            if img_url:
                img_bytes = _download_image_bytes(img_url)
                if img_bytes:
                    tmp_img = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                    tmp_img.write(img_bytes)
                    tmp_img.close()
                    try:
                        pdf.image(tmp_img.name, x=0, y=0, w=page_w, h=page_h * 0.72)
                    except Exception as e:
                        logger.warning(f"BookGen PDF: Image failed for panel {panel.get('scene_number')}: {e}")
                    finally:
                        os.unlink(tmp_img.name)

            # Text area below image
            text_y = page_h * 0.74
            pdf.set_fill_color(15, 15, 15)
            pdf.rect(0, text_y - 2, page_w, page_h - text_y + 2, 'F')

            # Scene title
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(201, 168, 76)
            pdf.set_xy(15, text_y)
            page_label = frame.get("label", f"Pagina {fi + 1}")
            pdf.cell(page_w - 30, 6, f"{scene_title} - {page_label}", align='L')

            # Narrative text
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(200, 200, 200)
            narrative = dialogue if dialogue else description
            if narrative:
                pdf.set_xy(15, text_y + 8)
                pdf.multi_cell(page_w - 30, 5, narrative[:300])

            # Page number
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(page_w - 25, page_h - 8)
            total_page = pdf.page_no()
            pdf.cell(15, 5, str(total_page), align='R')

    return bytes(pdf.output())


def build_interactive_book_data(
    project_id: str,
    project_name: str,
    creative_title: str,
    panels: list,
    cover_url: str = None,
    lang: str = "pt",
) -> dict:
    """Build structured JSON data for the Interactive Book reader.

    Returns a dict with all pages, narration text, and image URLs.
    """
    pages = []

    # Cover page
    pages.append({
        "type": "cover",
        "title": creative_title,
        "subtitle": {"pt": "Um livro ilustrado", "en": "An illustrated storybook", "es": "Un libro ilustrado"}.get(lang, "Um livro ilustrado"),
        "image_url": cover_url,
        "narration": f"{creative_title}. {pages[0]['subtitle'] if pages else ''}",
    })
    pages[0]["narration"] = f"{creative_title}."

    sorted_panels = sorted(panels, key=lambda p: p.get("scene_number", 0))

    page_num = 1
    for panel in sorted_panels:
        frames = panel.get("frames", [])
        images_to_use = sorted(frames, key=lambda f: f.get("frame_number", 0)) if frames else []

        if not images_to_use and panel.get("image_url"):
            images_to_use = [{"image_url": panel["image_url"], "label": panel.get("title", "")}]

        scene_title = panel.get("title", f"Cena {panel.get('scene_number', '')}")
        dialogue = panel.get("dialogue", "")
        description = panel.get("description", "")

        for fi, frame in enumerate(images_to_use):
            narrative = dialogue if dialogue else description
            pages.append({
                "type": "story",
                "page_number": page_num,
                "scene_number": panel.get("scene_number", 0),
                "title": scene_title,
                "label": frame.get("label", f"Pagina {fi + 1}"),
                "image_url": frame.get("image_url", panel.get("image_url", "")),
                "narration": narrative or scene_title,
                "characters": panel.get("characters_in_scene", []),
            })
            page_num += 1

    # End page
    end_text = {"pt": "Fim", "en": "The End", "es": "Fin"}.get(lang, "Fim")
    pages.append({
        "type": "end",
        "title": end_text,
        "narration": end_text,
        "image_url": cover_url,
    })

    return {
        "project_id": project_id,
        "title": creative_title,
        "original_title": project_name,
        "lang": lang,
        "total_pages": len(pages),
        "pages": pages,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
