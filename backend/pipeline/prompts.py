"""Pipeline prompt construction for each AI agent step."""
import re

from pipeline.config import STEP_ORDER


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

    elif step == "dylan_sound":
        approved_copy = steps.get("ana_review_copy", {}).get("approved_content", "")
        if not approved_copy:
            approved_copy = steps.get("ana_review_copy", {}).get("output", "")
        # Extract video brief from Sofia
        sofia_output = steps.get("sofia_copy", {}).get("output", "")
        video_brief = ""
        vb_match = re.search(r'===VIDEO BRIEF===([\s\S]*?)$', sofia_output, re.IGNORECASE)
        if vb_match:
            video_brief = vb_match.group(1).strip()
        campaign_name = pipeline.get("result", {}).get("campaign_name", "Brand")
        video_mode = pipeline.get("result", {}).get("video_mode", "narration")

        return f"""Analyze this campaign and create the complete AUDIO IDENTITY — voice, music, and narration delivery direction.

Brand/Company: {campaign_name}
Target Platforms: {platforms_str}
Video Mode: {video_mode}
{lang_instruction}

APPROVED CAMPAIGN COPY:
{approved_copy}

VIDEO BRIEF FROM DAVID:
{video_brief if video_brief else "(No video brief available)"}

ORIGINAL BRIEFING:
{briefing}

{f'Context:{chr(10)}{ctx_str}' if ctx_str else ''}
{contact_str}

YOUR TASK:
1. Analyze the brand personality, target audience, and campaign mood
2. Select the PERFECT voice from your ElevenLabs catalog that EMBODIES this brand
3. Configure the voice settings for maximum impact
4. Write detailed narration delivery directions (emotion, pace, emphasis per segment)
5. Select the ideal music track that amplifies the campaign's emotional arc
6. Define the music mix (volume levels, fades, energy progression)
7. Add platform-specific audio notes for the Video Director

CRITICAL: Your audio direction will be followed EXACTLY by Ridley (Video Director) and the TTS engine. Be precise and specific. Every choice must serve the campaign's strategic goal.

Output in the EXACT format specified in your instructions."""

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

        # Inject Dylan's audio DNA if available
        dylan_output = steps.get("dylan_sound", {}).get("output", "")
        audio_direction = ""
        if dylan_output:
            audio_direction = f"""

=== AUDIO DIRECTION FROM DYLAN REED (Sound Director) ===
Dylan has already analyzed the brand and selected the optimal voice, music, and narration delivery.
You MUST follow his audio direction precisely. Do NOT override his voice or music choices.
Your job is to create the visual script and narration TEXT — Dylan handles HOW it sounds.

{dylan_output}

=== END AUDIO DIRECTION ===
IMPORTANT: Use Dylan's voice selection and music selection in your ===NARRATION TONE=== and ===MUSIC DIRECTION=== sections.
Copy his Voice ID, tone recommendations, and music track key EXACTLY into your output."""

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
{audio_direction}
{revision_info}

REQUIREMENTS:
1. Design TWO clips that feel like ONE continuous shot — same character, same visual style, seamless transition
2. Write a DYNAMIC commercial narration script for the full 24 seconds with timing marks — urgent, exciting, creates FOMO
3. The final 3 seconds: clean dark background for brand logo "{campaign_name}" + tagline + contact CTA
4. Follow Dylan's MUSIC and VOICE direction EXACTLY — use the same track key and voice ID he specified
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


