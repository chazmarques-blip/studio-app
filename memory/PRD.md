# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python), ffmpeg
- **Database:** Supabase (PostgreSQL) + Supabase Storage (pipeline-assets bucket)
- **AI Models:** All via emergentintegrations + Emergent LLM Key
  - Sofia, Ana, Lucas, Rafael, Marcos: Claude Sonnet 4.5
  - Pedro: Gemini 2.0 Flash
  - Images: Gemini Nano Banana
  - Video: Sora 2 (2x 12s = 24s commercial)
  - Narration: OpenAI TTS HD (voice "Onyx", speed 0.92)
  - Video Processing: ffmpeg (crossfade + brand overlay + CTA + audio merge)

## AI Agent Pipeline (6 agents) — Updated Mar 14, 2026

### 1. Sofia (Copywriter) — Claude
- 3 copy variations (BAB/PAS/AIDA frameworks)
- IMAGE BRIEFING with headline + visual concepts + language enforcement
- **NEW: VIDEO BRIEF** — Video tagline, emotional tone, music mood, CTA text, contact info for video ending

### 2. Ana (Revisora) — Claude
- Reviews copy quality + briefing alignment + language consistency

### 3. Lucas (Designer) — Claude + Nano Banana
- 3 image prompts from Sofia's briefing
- CRITICAL LANGUAGE RULE: All image text must match copy language
- Generates images with Nano Banana

### 4. Rafael (Diretor de Arte) — Claude
- Reviews images (7 visual criteria)
- AUTOMATIC REJECTION on language mismatch
- **NEW: VIDEO CONCEPT REVIEW** — V1: Narration language, V2: CTA strength, V3: Brand closing, V4: Music fit

### 5. Marcos (Videomaker) — Claude + Sora 2 + TTS + ffmpeg
- Creates 24s commercial with structured output:
  - CHARACTER DESCRIPTION (surgical precision, copy-pasted in both clips)
  - CLIP 1 PROMPT (0-12s: hook → problem → turning point)
  - CLIP 2 PROMPT (12-24s: continuation → transformation → brand closing)
  - NARRATION SCRIPT (with timing marks [0-6s], [6-12s], [12-18s], [18-24s])
  - MUSIC DIRECTION (mood + description of musical arc)
  - CTA SEQUENCE (brand name + tagline + contact + visual description of ending)
- Pipeline: 2x Sora 2 clips → TTS narration → ffmpeg crossfade → brand logo overlay (uploaded or text) → tagline + contact CTA → audio merge
- Supports uploaded logo image overlay (falls back to text if none)

### 6. Pedro (Publisher) — Gemini Flash
- Schedule + strategy including video posting on Reels/TikTok/YouTube Shorts

## Video Commercial Pipeline Technical Flow
1. Marcos (Claude) generates structured output
2. Parse: clip1_prompt, clip2_prompt, narration_text, brand_name, tagline, contact_cta, music_mood
3. Generate TTS narration (OpenAI TTS HD, ~5s)
4. Generate Clip 1 with Sora 2 (~3 min)
5. Generate Clip 2 with Sora 2 (~3 min)
6. Check for uploaded logo image in pipeline assets
7. ffmpeg: normalize → crossfade (1s fade) → brand ending (logo/text + tagline + contact in gold) → merge narration audio
8. Upload to Supabase Storage

## Implemented Features
- AI Marketing Studio (6-agent pipeline)
- 24s Commercial Videos with narration + brand ending + CTA
- Language enforcement across all agents
- Dashboard Quick Actions at top
- Conteúdo tab: channel selector with clickable icons
- 8 platforms: WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS
- Dark luxury theme, Multi-language (PT/EN/ES)

## Backlog
### P0
- Campos de contato no AI Studio (Website, Telefone, Endereço, Email)
- Tamanhos por canal (imagens e vídeos adaptados a cada plataforma)
- Música de fundo no vídeo (royalty-free library por mood)

### P1
- Galeria de Criativos, Programa de Referral AgentZZ
- Migrar vídeo para Runway Gen-3 / Kling via fal.ai / Veo 3
- App Mobile (Capacitor iOS + Android)

### P2
- Integrações de canais ao vivo, Refatorar pipeline.py

### P3
- Admin System, Stripe, Termos de Uso

## Credentials
- Email: test@agentflow.com / Password: password123 / Plan: Enterprise
