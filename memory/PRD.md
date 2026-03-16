# AgentZZ - Product Requirements Document

## Problem Statement
No-code SaaS platform for SMB owners to deploy AI agents on social media with integrated AI marketing campaign generation.

## Architecture
- Frontend: React + Tailwind + shadcn-ui + Lucide Icons
- Backend: FastAPI (Python), Database: Supabase + MongoDB
- 3rd Party: Claude Sonnet 4.5, OpenAI TTS, Gemini Nano Banana, Sora 2, Google APIs, fal.ai (planned)

## Credentials
- Email: test@agentflow.com | Password: password123

## Current Status (March 16, 2026)

### Completed This Session
- [x] Agent Details Drawer (rich profiles, animated skill bars)
- [x] Company Management (primary/secondary, localStorage persist)
- [x] Default: Guided Questionnaire, Website URL as AI source
- [x] Video audio duplication fix (pause bg on lightbox)
- [x] Narration cutoff fix (atempo speedup if > 19s)
- [x] Video Mode Selector (Sem Video / Narracao / Apresentador)
- [x] Avatar System (upload photo or AI generate via Nano Banana)
- [x] Presenter Video infrastructure (fal.ai Kling Avatar v2)
- [x] CRITICAL: Replaced ALL ffprobe calls with ffmpeg-based helpers (_ffprobe_duration, _ffprobe_dimensions)
- [x] CRITICAL: 12s video fix — clip2 fallback now concatenates clip1 twice for 24s
- [x] CRITICAL: Video variants were EMPTY — now generated correctly for all 8 channels
- [x] Regenerated variants for all existing campaigns
- [x] Created regenerate-video-variants endpoint
- [x] Clone now preserves skip_video, video_mode, avatar_url
- [x] Compact uploads: Logo + Reference side by side in a single row
- [x] Fixed button-in-button HTML nesting
- [x] **Avatar Studio UI Refactor (P0 COMPLETE)**: Dedicated "Avatar do Apresentador" section created outside the company form. Features: photo upload, AI-powered full-body avatar generation (Gemini), large preview, regenerate/remove controls. Backend uses GPT Image 1 via Emergent LLM Key. Tested: iteration_44 (100% pass)
- [x] **Avatar Generation Bug Fix**: Fixed `UserMessage.__init__() got an unexpected keyword argument 'image_url'` - now downloads image and passes as `FileContent`. Tested: iteration_45 (100% pass)
- [x] **Company Edit Feature**: Added edit button (pencil icon) on company cards. Clicking opens form pre-filled with company data. "Atualizar Empresa" saves changes. Tested: iteration_45 (100% pass)
- [x] **i18n Refactor**: All hardcoded PT strings in PipelineView.jsx, Agents.jsx, AgentDetailsDrawer.jsx replaced with `t()` calls. Added 66 studio keys and 11 agent keys to en.json, pt.json, es.json. Tested: iteration_46 (100% pass)
- [x] **UI Reorganization**: Company/Avatar creation moved to modal dialogs triggered by "+" buttons in section headers. In the campaign flow, companies/avatars are selectable cards/thumbnails. Tested: iteration_46 (100% pass)
- [x] **Multiple Avatars**: Avatars stored as separate list in localStorage (agentzz_avatars). Users can create multiple avatars via "+" button and select one for campaigns. Tested: iteration_46 (100% pass)
- [x] **Company Logo Upload**: Logo upload integrated into company creation/edit modal. Company cards show uploaded logo on the left. Tested: iteration_47 (100% pass)
- [x] **Avatar Zoom Preview**: Hover-to-zoom on avatar thumbnails opens fullscreen overlay with close and download. Tested: iteration_47 (100% pass)
- [x] **Avatar Studio Advanced (P1 COMPLETE)**: Multi-step avatar creation modal with:
  - Stage 1: Photo upload + AI generation (Gemini)
  - Stage 2: 3 customization tabs (Clothing, 360° View, Voice)
  - **Clothing**: 4 styles (Business Formal, Casual, Streetwear, Creative) with AI regeneration
  - **360° View**: Generate 4 angles (front, left, right, back) for each avatar
  - **Voice**: OpenAI TTS bank (6 voices: alloy, echo, fable, onyx, nova, shimmer) + custom voice recording in browser
  - Each avatar saved with its selected voice. Gallery shows voice indicator
  - Backend: 3 new endpoints (/voice-preview, /upload-voice-recording, /generate-avatar-variant)
  - Tested: iteration_48 (100% pass - 11/11 tests)
- [x] **Avatar Studio Bug Fixes**: 
  - Preview retangular (portrait) em vez de quadrado
  - Ângulos 360° Left/Right com prompts distintos no backend
  - Galeria interna de roupas (variações armazenadas, seleção instantânea do cache)
  - Microfone com detecção de MIME type e error handling detalhado
  - Tested: iteration_49 (100% pass - 17/17 backend + frontend verified)

- [x] **Avatar Edit & Clone (P0 COMPLETE)**:
  - Edit button (pen icon) on hover for each avatar in gallery
  - Opens customization modal pre-populated with avatar's data (image, clothing, voice, angles)
  - Modal title: "Edit Avatar" when editing vs "Customize Avatar" for new
  - Dual footer buttons: "Update" (saves over existing) + "Save as New" (clones)
  - 360° angles editable: regenerate button (refresh icon) on hover for each existing angle
  - i18n keys added for all 3 locales (en, pt, es)
  - Tested: iteration_50 (9/9), iteration_51 (6/6 angle regen) - 100% pass

- [x] **Brand Data Toggle & Exact Photos (P0 COMPLETE)**:
  - Removed logo upload from campaign form (logo comes from company data)
  - Removed Saved Logos section and Contact Data section (all from company now)
  - Added brand data toggle: checkbox with company logo, name, phone, website preview
  - Toggle ON by default: applies logo + company data to videos and campaign texts
  - Replaced "Brand & Reference Images" with "Product Images" (Exact Photos + Reference)
  - "Exact Photos" (green): AI uses exact product with professional editing/treatment
  - "Reference" (blue): Inspiration/reference images for AI
  - Pipeline payload now sends `apply_brand` flag and `brand_data` object
  - i18n: 8 new keys in all 3 locales
  - Tested: iteration_52 (100% pass - 11/11 features)

- [x] **Exact Photos Pipeline (COMPLETE)**:
  - `_edit_exact_image()`: New function that downloads the real product photo, sends it to Gemini as image input, and applies professional editing (background, lighting, composition) while keeping the EXACT product
  - `_generate_design_images()`: When exact photos exist, uses them as base images for editing (first N designs match N exact photos); remaining designs generated from scratch
  - `assets_str`: Differentiates between "exact" and "reference" photo types in prompt context
  - `lucas_design` prompt: Instructs Stefan to write EDITING instructions for exact photos (not new product descriptions)
  - Tested: Backend lint clean, upload endpoint verified

- [x] **Avatar from Video Upload (COMPLETE)**:
  - Photo/Video toggle in avatar creation modal (Camera/Film icons)
  - Backend: POST /api/campaigns/pipeline/extract-from-video extracts best frame + audio via FFmpeg
  - Auto-sets extracted voice as custom voice for the avatar
  - Green "Real voice extracted" badge when audio is found
  - Video hint: "Upload a 10-30s video of the person speaking naturally"
  - i18n: 12 new keys in all 3 locales
  - Tested: iteration_53 (100% pass - 15/15 features)

### Known Issues
- FFmpeg logo overlay sometimes fails (low priority)

---

## ROADMAP COMPLETO

### FASE 1 — Estabilização & Refatoração (Técnico)
| # | Tarefa | Detalhe | Depende de |
|---|--------|---------|-----------|
| 1.1 | **Refatoração pipeline.py** | Quebrar ~4000 linhas em módulos: `video.py`, `audio.py`, `avatar.py`, `ai_services.py`, `steps.py` | — |
| 1.2 | **Renomear agentes** | Permitir que o usuário renomeie os agentes do pipeline | — |
| 1.3 | **Redesign Landing/Login** | Página de entrada profissional, conversão de novos usuários | — |

### FASE 2 — CRM & Infraestrutura de Comunicação
| # | Tarefa | Detalhe | Depende de |
|---|--------|---------|-----------|
| 2.1 | **CRM / Base de Leads** | Importação de contatos (CSV, manual), tags, histórico de interação | — |
| 2.2 | **Kanban Visual** | Board visual de pipeline de vendas, colunas customizáveis, drag & drop | 2.1 |
| 2.3 | **Unified Inbox** | Inbox unificado para todos os canais (WhatsApp, Instagram, Telegram, SMS, Email) | 2.4 |
| 2.4 | **WhatsApp MVP** | Integração básica com Evolution API — enviar/receber mensagens | — |
| 2.5 | **Integrações Omnichannel** | Instagram DM, Facebook Messenger, Telegram, SMS (Twilio) | 2.4 |

### FASE 3 — Agentes Inteligentes
| # | Tarefa | Detalhe | Depende de |
|---|--------|---------|-----------|
| 3.1 | **Agente Testador (Sandbox)** | Chat interno entre Agente Testador (simula cliente) e Agente Alvo. Split-screen: chat à esquerda, config à direita. Ajuste em tempo real. Cenários: "cliente irritado", "dúvida técnica", "pedido de preço". Score automático de coerência e assertividade | — |
| 3.2 | **Agente Gestor de Chats (Supervisor)** | Analisa todas as conversas dos agentes. Avalia coerência, tom, informações corretas, oportunidades perdidas. Relatório por agente com nota, pontos fortes e melhorias. Alertas automáticos. Sugestões de melhoria de prompt | 2.3 |
| 3.3 | **Agente Gestor de Kanban** | Move leads automaticamente entre colunas baseado no status do chat. Regras inteligentes ("pediu proposta → Negociação"). Cria tarefas de follow-up. Priorização por score de qualificação. Notificações ao dono | 2.2, 3.2 |

### FASE 4 — Campanhas & Nurturing
| # | Tarefa | Detalhe | Depende de |
|---|--------|---------|-----------|
| 4.1 | **Campanhas para Leads** | Segmentação por tags, status no Kanban, histórico. Criar campanha direcionada ("Re-engajar leads frios 30 dias"). Agendamento de disparo (WhatsApp, SMS, Email). Dashboard de performance por segmento | 2.1, 2.4 |
| 4.2 | **AutoFlow (Visual Workflow Builder)** | Builder drag & drop para fluxos de automação: triggers → condições → ações. Templates pré-prontos | 2.3 |
| 4.3 | **Social Publishing** | Publicação direta de campanhas nas redes sociais (Instagram, Facebook, etc.) | — |

### FASE 5 — Monetização & Escala
| # | Tarefa | Detalhe | Depende de |
|---|--------|---------|-----------|
| 5.1 | **Stripe / Pagamentos** | Gateway de pagamento, planos Freemium/Pro/Enterprise, cobrança recorrente | — |
| 5.2 | **Sistema Admin** | Dashboard administrativo: gestão de usuários, planos, métricas da plataforma, logs | 5.1 |
| 5.3 | **Analytics & Relatórios** | Relatórios de performance de campanhas, agentes, conversões, ROI por canal | 2.1, 3.2 |
| 5.4 | **Termos de Uso & LGPD** | Páginas legais, consentimento, gestão de dados pessoais | — |

---

## ORDEM DE EXECUÇÃO RECOMENDADA

```
IMEDIATO (próximas sessões):
  1.1 Refatoração pipeline.py
  1.2 Renomear agentes
  3.1 Agente Testador (Sandbox) ← não depende de nada externo

CURTO PRAZO:
  1.3 Redesign Landing/Login
  2.1 CRM / Base de Leads
  2.2 Kanban Visual
  2.4 WhatsApp MVP

MÉDIO PRAZO:
  2.3 Unified Inbox
  3.2 Agente Gestor de Chats
  3.3 Agente Gestor de Kanban
  4.1 Campanhas para Leads

LONGO PRAZO:
  2.5 Integrações Omnichannel
  4.2 AutoFlow
  4.3 Social Publishing
  5.1 Stripe
  5.2 Admin
  5.3 Analytics
  5.4 LGPD
```

### Future
- Marketplace de agentes pré-configurados por nicho
- API pública para integrações externas
- White-label para revendedores
- App mobile nativo

## Test Reports
- iteration_40: Agent Details Drawer
- iteration_41: Company management + defaults
- iteration_42: Avatar + Video Mode
- iteration_50: Avatar Edit & Clone (100% pass - 9/9 features)
- iteration_43: Video bug fixes (ffprobe, 12s, variants)
- iteration_44: Avatar Studio UI Refactor (100% pass)
- iteration_45: Avatar bug fix + Company edit (100% pass)
- iteration_46: i18n refactor + UI reorganization (100% pass - 13/13 features)
- iteration_47: Company logo upload + Avatar zoom preview (100% pass - 10/10 features)
- iteration_48: Avatar Studio Advanced - Clothing, 360°, Voice (100% pass - 11/11 tests)
- iteration_49: Avatar Studio Bug Fixes - Portrait preview, angles, gallery, mic (100% pass - 17/17)
- iteration_43: Video variants + clone fix (100% pass)
- iteration_52: Brand Data Toggle & Exact Photos (100% pass - 11/11 features)
