# AgentZZ - PRD

## Original Problem Statement
Mobile-first, no-code SaaS platform for deploying pre-built AI agents on social media channels (WhatsApp, Instagram, Facebook, Telegram, SMS). Includes AI Marketing Studio for multimodal campaign generation.

## Core Architecture
- Frontend: React + Tailwind + shadcn-ui + Framer Motion + recharts
- Backend: FastAPI (Python)
- Database: Supabase (PostgreSQL) — ALL data stored in Supabase (no MongoDB)
- AI: Claude Sonnet 4.5, Gemini Flash, Gemini Nano Banana (images), Sora 2 (video), ElevenLabs (voice/music)
- Auth: Supabase Auth
- Pipeline: Multi-agent AI directors (Sofia, Lee, Ana, Lucas, Rafael, George, Stefan, Dylan, Roger, Marcos, Pedro)

## Implemented Features (Completed)
- Dashboard with recharts analytics
- Agent Management + Marketplace
- Agent Configuration with Google Calendar/Sheets integration
- AI Marketing Studio with full pipeline
- Campaign Gallery with Art Style Generator (14 styles)
- Avatar 3D Creator with 360-degree views
- Video generation pipeline (Sora 2 + FFmpeg)
- Audio Pre-Approval (pipeline pauses before video)
- FFmpeg quality: CRF 16, scale+crop, 256k/320k audio
- Landing Page V2
- Multi-language support (PT/EN/ES)

## Completed This Session (2026-03-21)

### Bug Fix: Art Gallery Images Disappearing + Mockup Mismatch
**Two root causes found and fixed:**
1. **Campo `images` vs `image_urls`**: engine.py salvava como `image_urls`, mas regenerate-single-image/edit-image-text liam de `images` (vazio). Corrigido com logica de merge com deduplicacao em todos os endpoints.
2. **Mockup mostrando imagem errada**: `platform_variants` tinha indices desincronizados com `images`. Mockup agora usa `images[safeIdx]` diretamente.

**Correcoes aplicadas:**
- `pipeline/engine.py`: Merge images/image_urls antes de publicar campanha
- `pipeline/routes.py`: 4 endpoints corrigidos + endpoint de migracao
- `Marketing.jsx`: Mockup usa images diretamente, ArtGalleryModal refresh ao abrir/fechar
- **Migracao executada**: 64 pipelines + 54 campanhas corrigidas
- **Testes**: 11/11 backend + 8/8 frontend (iteration_83)

### Smart Text Detection & Targeted Editing (2026-03-21)
- Novo endpoint `detect-image-text`: usa Gemini Vision para detectar todos os textos na imagem
- Frontend: modal separado com fluxo de 3 passos (detectando → selecione texto → digite novo texto)
- `_edit_text_in_image` aceita `original_text` para substituicao direcionada
- Fix: parser agora lida com respostas truncadas e markdown code blocks da Gemini
- Fix: deteccao de mime type usa magic bytes do conteudo (nao extensao da URL)
- Fix: fallback URL → base64 para imagens que falham na deteccao via URL
- Testes: 11/11 backend + frontend (iteration_84) + curl confirmado em 3 imagens

### Edit Image Text — AI In-Place Editing (2026-03-21)
- **Antes**: O "Edit Image Text" gerava uma imagem COMPLETAMENTE nova (perdia o visual original)
- **Agora**: Usa Gemini image editing para alterar APENAS o texto, preservando background/composicao/cores
- Nova funcao `_edit_text_in_image` em `media.py` com prompts especializados em preservacao visual
- Endpoint `edit-image-text` reescrito para usar edicao in-place em vez de geracao do zero
- Testado com campanha Hercules: texto mudou de "Banheiro dos Sonhos AGORA" → "Banheiro de Luxo Premium" mantendo imagem identica
- Files: `pipeline/media.py`, `pipeline/routes.py`, `Marketing.jsx`

### UI Readability Fix — AI Studio & Marketing (2026-03-21)
- Corrigido contraste de texto em 11 arquivos do ecossistema AI Studio (2 rodadas de ajuste)
- Mapeamento final: `#555→#999` (labels), `#444→#888` (terciario), `#333→#777` (sutil)
- Placeholders: `#333/#444` → `#666`
- Avatares: formato quadrado (h-16 w-16) → retangular portrait (h-24 w-16) para mostrar corpo inteiro
- ~200+ ajustes de cor + forma dos avatares, mantendo estetica "dark luxury"

### Download Fix — Botoes de Download (2026-03-21)
- Corrigido todos os botoes de download que abriam zoom/nova aba (target="_blank") → agora fazem download direto via blob fetch
- Adicionado spinner animado (RefreshCw) enquanto o download esta em progresso
- Locais corrigidos: imagens do campaign detail, avatar download, art gallery download, video lightbox download
- Sem sair da pagina ao clicar no download

### Historico de Edicoes de Avatar + Flag Base (2026-03-21)
- Painel de historico visual a esquerda do avatar com miniaturas de cada versao
- Badge "BASE" dourado na primeira versao (ancora de contexto)
- Numero de versao (v1, v2, v3...) e instrucao usada visivel no hover
- Click em qualquer versao anterior para reverter
- Backend: endpoint edit-avatar agora recebe base_url como parametro extra
- Quando base_url disponivel, envia AMBAS imagens (atual + base) via _gemini_edit_multi_ref
- Prompt instrui IA a preservar identidade do personagem base em TODAS as edicoes
- Historico inicializado automaticamente ao criar avatar OU abrir para edicao

### Correcao Global de Legibilidade de Texto (2026-03-22)
- **Mapeamento sistematico de cores** em ~20 arquivos JSX para leitura perfeita no tema dark luxury
- Texto principal: `#333-#555` → `#B0B0B0` (alto contraste)
- Texto secundario: `#666` → `#999` (legivel)
- Hover states: `#888` → `#E5E5E5` (evita hover mais escuro que default)
- Placeholders: `#333/#444` → `#666` (minimo aceitavel)
- Icones decorativos mantidos sutis (#444/#555) por design
- **Paginas corrigidas**: AgentConfig, AgentBuilder, Dashboard, TrafficHub, ChannelConnection, GoogleIntegration, CRM, Agents, AgentSandbox, LeadDetail, Pricing, Settings, Profile, UpsellScreen, Chat, Marketing, MarketingStudio, LandingV2, Landing, Login, AgentDetailsDrawer
- **Testes**: 15/15 paginas verificadas (iteration_86) - 100% PASS
- **Historico salvo no servidor**: edit_history agora persiste em Supabase (tenants.settings JSONB)
- **Auto-save**: Cada edicao AI automaticamente salva o historico no servidor
- **Carregamento**: Ao abrir avatar para edicao, historico salvo e carregado automaticamente
- **Download**: Botao de download em cada versao do historico (blob download direto)
- **Delete**: Botao de remover versao (exceto a BASE, que nao pode ser removida)
- **Editar**: Botao para abrir edicao AI a partir de qualquer versao do historico
- **Backend**: Novo campo `edit_history` no modelo AvatarIn + endpoint DELETE /api/data/avatars/{id}/history/{index}
- **Layout**: Imagens maiores (w-32), aspect 3/4, maxHeight 356px (mostra 2 completas), auto-scroll
- **Testes**: 11/11 backend + 100% frontend (iteration_85)

## Backlog
### P0 (In Progress)
- Presenter mode: lip-sync integration (avatar talks in video) — needs API like HeyGen/D-ID/Sync Labs
- Color grading via FFmpeg (contrast + saturation + warmth)
- Fade-in/out suaves, dissolve transitions

### P1
- Omnichannel integrations (WhatsApp, SMS, Instagram, Facebook, Telegram)
- CRM Kanban board

### P2
- Admin Management System
- Payment Gateway
- Terms of Use / Privacy Policy

### P3
- Refactor PipelineView.jsx (>2700 lines)
- Scalability hardening

## Known Issues
- `_extract_dylan_voice_settings` fails with UUID error for "_preview" suffixed pipeline IDs (non-critical)
- Live social channel integrations are mocked
- Legacy pipelines have mismatch between `images` and `image_urls` fields (handled by fallback)

## Test Credentials
- Email: test@agentflow.com
- Password: password123
