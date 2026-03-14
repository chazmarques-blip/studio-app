# AgentZZ - Product Requirements Document

## Original Problem Statement
Build a comprehensive, mobile-first, no-code SaaS platform called "AgentZZ" that allows SMBs to deploy and configure pre-built AI agents on social media channels.

## Core Architecture
- **Frontend:** React, Tailwind CSS, shadcn-ui, i18next, Framer Motion, recharts
- **Backend:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL) + Supabase Storage (pipeline-assets bucket)
- **AI Models:**
  - Sofia, Ana, Lucas, Rafael, Marcos: Claude Sonnet 4.5 (with Gemini Flash fallback)
  - Pedro (scheduling): Gemini 2.0 Flash (primary)
  - Image Generation: Gemini Nano Banana
  - Video Generation: Sora 2 (2x 12s clips = 24s commercial)
  - Narration: OpenAI TTS HD (voice "Onyx")
  - Video Processing: ffmpeg (crossfade + brand overlay + audio merge)
  - All via emergentintegrations + Emergent LLM Key
- **Auth:** JWT-based custom auth

## AI Agent Pipeline (6 agents)
1. **Sofia** → Copy (3 variations) + IMAGE BRIEFING with explicit language enforcement
2. **Ana** → Reviews copy + briefing alignment + language consistency
3. **Lucas** → Image prompts + Nano Banana generation + CRITICAL LANGUAGE RULE
4. **Rafael** → Reviews images (7 criteria) + AUTOMATIC REJECTION on language mismatch
5. **Marcos** → 24s commercial: TWO 12s clip prompts with character continuity + narration script + brand ending → Sora 2 (2 clips) + TTS narration + ffmpeg crossfade + brand logo overlay
6. **Pedro** → Schedule + strategy (Gemini Flash)

## Video Commercial Pipeline (Marcos)
- Marcos outputs: CHARACTER DESCRIPTION + CLIP 1 PROMPT + CLIP 2 PROMPT + NARRATION SCRIPT + BRAND NAME
- Same character described identically in both clips for visual continuity
- Clip 1 ends at a transition point that Clip 2 naturally continues from
- Narration: Dynamic commercial voiceover, timed for 24s, urgent CTA at end
- ffmpeg: normalize clips → 1s crossfade → brand text overlay (last 3s) → merge narration audio
- Sizes: 1280x720 (landscape) or 720x1280 (portrait), auto-selected per platform

## Language Enforcement (Bug Fix)
- Sofia: Headlines "in the EXACT SAME language as the copy"
- Lucas: CRITICAL LANGUAGE RULE + lang_instruction injected
- Rafael: Criterion 4 = AUTOMATIC FAIL on language mismatch
- Marcos: Narration must match campaign copy language

## UI Redesign: Conteúdo Tab
- Channel icons REMOVED from campaign detail header
- Channel icons placed INSIDE "Conteúdo" tab as clickable selector header
- Click a channel → shows ONLY that channel's mockup (WhatsApp, Instagram, Facebook, TikTok, Google Ads, etc.)
- Video commercial section shown below the mockup

## Implemented Features
- AI Marketing Studio (6-agent pipeline, complete)
- Video Generation (24s commercial with narration + brand logo)
- Dashboard Quick Actions at top
- Persistent Supabase Storage
- 8 platforms: WhatsApp, Instagram, Facebook, TikTok, Google Ads, Telegram, Email, SMS
- Conteúdo tab with channel selector
- Dark luxury theme, Multi-language (PT/EN/ES)

## Backlog (Prioritized)
### P0
- Campos de contato no AI Studio (Website, Telefone, Endereço, Email) — múltiplos, selecionáveis
- Tamanhos por canal (imagens e vídeos adaptados a cada plataforma)

### P1
- Galeria de Criativos (imagens + vídeos)
- Programa de Referral/Embaixador AgentZZ
- **Avaliar e migrar geração de vídeo para Runway Gen-3 / Kling via fal.ai / Veo 3** (custo menor, vídeos mais longos sem corte)
- App Mobile (Capacitor iOS + Android)

### P2
- Integrações de canais ao vivo (publicação real)
- Refatorar pipeline.py em módulos

### P3
- Admin Management System
- Stripe
- Termos de Uso / Política de Privacidade

## Credentials
- Email: test@agentflow.com
- Password: password123
- Plan: Enterprise
