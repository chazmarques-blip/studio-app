# StudioX Changelog

## 2026-04-21 (Session 13e — Sprint 1+2 Autônomo: Wiring completo + Sinergia)

### Sprint 1 — Wiring runtime dos agentes na pipeline (concluído)
Aplicado o padrão `resolve_agent_prompt(agent_id, fallback=hardcoded)` em TODOS os routers críticos:

| Router | Agente(s) wired | # de call sites |
|---|---|---|
| `screenwriter.py` | Aaron Sorkin (screenwriter_agent) | 1 (com fix de placeholders) |
| `parallel_agents.py` | Aaron Sorkin (screenwriter_agent) | 1 (com fix de placeholders) |
| `dialogues.py` | Tarantino / Burns / Gaiman (mode-aware) | 1 com switch por modo |
| `narration.py` | Hans Zimmer (sound_designer_agent) | 2 (voice casting batch + single) |
| `sound_design_agent.py` | Hans Zimmer | 1 |
| `book_factory.py` | Gaiman / Perkins / Kidd / Tschichold / Steidl | 9 (helper `_rsys()` adicionado) |

**Fix crítico:** Em `screenwriter.py` e `parallel_agents.py`, a substituição de placeholders `{lang_name}`, `{target_duration}` etc. agora ocorre APÓS `resolve_agent_prompt()` — assim tanto prompts hardcoded quanto customizados pelo usuário suportam placeholders.

**Seed de prompt real:** `screenwriter_agent.json` agora tem o prompt real de 6377 chars extraído de `SCREENWRITER_SYSTEM_SORA` (com placeholders preservados). Campo `note` documenta quais placeholders são substituídos em runtime.

### Sprint 2 — Sinergia ("Dream Team" badge)
Novo componente reutilizável `/frontend/src/components/pipeline/SynergyBadge.jsx`:
- **Prop `compact`**: chip pequeno (violeta→laranja) mostrando "Dream Team · N" clicável → navega para `/studio/agents`
- **Prop `compact={false}`**: card destacado com lista dos mestres ativos + mentalidade ativa + botão "Editar"
- **Silent quando ninguém está ativo** — sem clutter para usuários no modo default
- **Integrado em:**
  - `StudioPage.jsx` → compact badge na barra de contexto superior (ao lado de Galeria/Novo Projeto)
  - `DirectedStudio.jsx` → card completo acima do banner de projeto híbrido, com categoria detectada via `outputMode` (book → book mindset, video/both → video mindset)

### Testes (100% pass — 27/27)
Testing agent v3 validou:
- ✅ GET/PUT/Rollback registry endpoints
- ✅ GET/PUT mindsets endpoints
- ✅ POST playground (LLM real)
- ✅ `resolve_agent_prompt()` unit tests (4/4 safety PASS: inactive agent, inactive mindset, book fallback, unknown agent ID)
- ✅ Pipeline routers import sem erro
- ✅ Zero-breaking-changes: todos os agentes e mindsets permanecem `active: false` por default

Testes pytest criados automaticamente em `/app/backend/tests/test_agents_registry.py`.

### Sprint 3 — Tier 4 cleanup (PULADO deliberadamente)
Decisão de segurança: remover routers legados (`whatsapp.py`, `conversations.py`, `crm`, `campaigns`, `leads`, `telegram`) tem risco não-zero de quebrar alguma referência interna. O sidebar já não linka para nenhuma dessas rotas, então elas estão efetivamente desativadas do ponto de vista do usuário. Cleanup físico fica para sessão futura com auditoria dedicada.

### Arquivos modificados
- `backend/routers/studio/agents_registry.py` (+133 linhas: mindsets, playground, helper expandido)
- `backend/routers/studio/screenwriter.py` (wiring + fix placeholder order)
- `backend/routers/studio/parallel_agents.py` (wiring + fix placeholder order)
- `backend/routers/studio/dialogues.py` (wiring mode-aware)
- `backend/routers/studio/narration.py` (2 wirings)
- `backend/routers/studio/sound_design_agent.py` (1 wiring)
- `backend/routers/studio/book_factory.py` (helper _rsys + 9 wirings)
- `frontend/src/components/pipeline/SynergyBadge.jsx` (NOVO, 102 linhas)
- `frontend/src/pages/StudioPage.jsx` (import + compact badge)
- `frontend/src/components/DirectedStudio.jsx` (import + card cima do banner híbrido)
- `memory/agents/screenwriter_agent.json` (seed do prompt real 6377 chars)



## 2026-04-21 (Session 13d — Mentalidades Globais + Nomes de Mestres + Playground)

### 3 features em uma arquitetura coesa

#### 1. Mentalidades Globais por Categoria
Filosofia macro do estúdio aplicada a TODOS os agentes daquela pipeline simultaneamente.

- **Arquivo:** `/app/memory/agents/_mindsets.json` (3 categorias: video, book, audio)
- **Default:** `active: false` em todas → comportamento atual preservado
- **Endpoints:**
  - `GET /api/studio/agents/mindsets` — lista as 3
  - `GET /api/studio/agents/mindsets/{category}` — uma específica
  - `PUT /api/studio/agents/mindsets/{category}` — atualiza com edit_history
- **Conteúdo seed (editável pelo usuário):**
  - Vídeo: 6 princípios cinematográficos (emoção antes de técnica, economia narrativa Hitchcock/Miyazaki, subtexto, etc.)
  - Livro: 6 princípios editoriais (livro como objeto, voz autoral, precisão tipográfica Tschichold/Bringhurst, etc.)
  - Áudio: 6 princípios sonoros (som é 50%, silêncio é ferramenta, tema = identidade Zimmer/Williams, etc.)
- **Runtime:** `resolve_agent_prompt(agent_id, fallback)` agora prepends a mentalidade da categoria se ativa: `[MENTALIDADE] + --- + [PROMPT DO AGENTE]`

#### 2. Nomes de Mestres Mundiais
Cada agente agora tem `master_reference` (mestre do mundo real) + `master_bio` (contexto do por quê):

- **Vídeo (8):**
  - researcher → David McCullough (historiador, 2× Pulitzer)
  - visual_researcher → Roger Deakins (cinematógrafo, 2 Oscars)
  - orchestrator → Kathleen Kennedy (produtora Lucasfilm)
  - screenwriter → Aaron Sorkin (Oscar — The Social Network)
  - dialogue_writer → Quentin Tarantino (diálogos icônicos)
  - narrator → Ken Burns (documentarista)
  - quality_validator → Christopher Nolan (diretor)
  - consistency_checker → Thelma Schoonmaker (editora, 3 Oscars)
- **Livro (8):**
  - author → Neil Gaiman (storyteller versátil)
  - book_editor → Max Perkins (editor de Hemingway/Fitzgerald)
  - proofreader → Mary Norris (The New Yorker, "Comma Queen")
  - art_director → Chip Kidd (designer Knopf)
  - cover_designer → Peter Mendelsund (capista Kafka/Joyce)
  - illustrator → Hayao Miyazaki (Studio Ghibli)
  - layout_designer → Jan Tschichold (tipografia clássica)
  - preflight → Gerhard Steidl (Steidl Verlag)
- **Áudio (1):**
  - sound_designer → Hans Zimmer (compositor/sound designer)

UI mostra o nome do mestre em destaque com ícone Award 🏆 + função como subtitle + bio no modal de edição.

#### 3. Playground por Agente
Tab "Playground" no modal de edição permite testar o prompt sem salvar.

- **Endpoint:** `POST /api/studio/agents/playground`
  - Body: `{agent_id, system_prompt, user_input, temperature, include_mindset, mindset_prompt}`
  - Resposta: `{output, agent_id, category, prompt_length, mindset_applied}`
- **Usa Emergent LLM Key** via `_call_claude_sync` (já integrado no _shared.py)
- **Checkbox "Aplicar Mentalidade Global"** para testar com/sem a filosofia da categoria
- **Usa o prompt não-salvo** do editor → iteração rápida antes de commit
- Validado via curl — Aaron Sorkin gera diálogo cinematográfico real

### Arquivos modificados/criados
- `memory/agents/_mindsets.json` — NOVO, 3 mentalidades seed (inativas)
- `memory/agents/**/*.json` × 17 — atualizadas com `master_reference` + `master_bio`
- `backend/routers/studio/agents_registry.py` — 3 novos endpoints (mindsets × 2 + playground), `resolve_agent_prompt` agora concatena mindset+prompt, skip `_*.json` meta files
- `frontend/src/pages/AgentsPage.jsx` — reescrito (600 linhas): MindsetCard, AgentEditor com tabs Editar/Playground, MindsetEditor modal

### Testes
- ✅ Lint JS: No issues
- ✅ `GET /api/studio/agents/mindsets` → 3 categorias retornadas
- ✅ `GET /api/studio/agents/registry/screenwriter_agent` → master_reference "Aaron Sorkin", master_bio presente
- ✅ `POST /api/studio/agents/playground` → 200, output real do Claude com diálogos cinematográficos
- ✅ Screenshot Agents page: cards com nomes de mestres + mentalidade card no topo de cada seção
- ✅ Screenshot Mindset editor: system_prompt completo com 6 princípios + toggle ativar
- ✅ Screenshot Playground tab: textarea, checkbox mindset, botão Executar

### Zero-Breaking-Changes garantido
- Todos os 17 agentes + 3 mindsets com `active: false` por default
- `resolve_agent_prompt()` retorna fallback hardcoded quando nada está ativo → pipeline comportamento idêntico ao anterior
- Usuário opt-in explicitamente via toggle na UI


## 2026-04-21 (Session 13c — Agents Registry: UI + Runtime Wiring)

### Objetivo do usuário
> "Quero que os agentes aqui sejam exatamente os integrados no sistema de pipelines, porque quando ajustamos um agente aqui melhorando seu prompt isso influencia diretamente no resultado da entrega dos produtos."

### Arquitetura implementada
**Single Source of Truth** para prompts da pipeline de IA com padrão zero-breaking-changes:

1. **Backend registry expandido** (`/app/backend/routers/studio/agents_registry.py`)
   - `GET /api/studio/agents/registry` — lista todos (video/book/audio) com category, active, model, updated_at
   - `GET /api/studio/agents/registry/{id}` — spec completo
   - `PUT /api/studio/agents/registry/{id}` — salva + anexa `edit_history` (últimas 20 versões, com timestamp e autor)
   - `POST /api/studio/agents/registry/{id}/rollback` — restaura versão anterior do histórico
   - Agora inclui pasta `/app/memory/agents/book/` (8 agentes antes invisíveis)
   - Helper runtime `resolve_agent_prompt(agent_id, fallback)` — retorna JSON se `active=true`, senão fallback hardcoded

2. **Seed dos 17 agentes** (18 incluindo compositions, mas essa é filtrada)
   - Todos com `active: false` por padrão → fallback hardcoded é usado (sem mudança de comportamento)
   - Campos `temperature`, `model` adicionados quando ausentes
   - Video (8): Pesquisador Histórico, Pesquisador Visual, Orquestrador, Roteirista, Escritor Diálogos, Escritor Narração, Validador Qualidade, Verificador Consistência
   - Book (8): Autor, Book Editor, Diretor de Arte, Capista, Ilustrador, Layout, Preflight, Revisor
   - Audio (1): Sound Designer

3. **Wiring POC — Screenwriter**
   - `screenwriter.py` linha ~380: após montar o `system_template` (Kling ou Sora), chama `resolve_agent_prompt("screenwriter_agent", fallback=system)`
   - Se usuário ativa custom no UI → pipeline usa o novo prompt no próximo request
   - Se JSON quebra ou tem erro → fallback silencioso mantém comportamento atual

4. **Frontend `AgentsPage.jsx` reescrito** (400 lines)
   - Layout unificado com Sidebar + AppHeader (mesmo padrão de Projetos/Personagens)
   - Tabs: Todos / Vídeo / Livro / Áudio (com contadores)
   - Cards agrupados por pipeline quando "Todos" selecionado
   - Badge visual `CUSTOM` (violeta) vs `DEFAULT` (cinza) em cada card
   - Modal de edição: toggle ativo/desativo, system_prompt (textarea), temperatura (slider), min_quality_score (slider), responsabilidades, histórico com rollback
   - Busca + filtros por categoria
   - Dark/Light mode nativos (paleta violeta/laranja)

### Routing
- `/agents` → AgentsPage (agora é a página de pipeline agents, substitui legacy WhatsApp agents)
- `/studio/agents` → AgentsPage (alias)
- Sidebar "Agentes" aponta para `/studio/agents` (ativo em ambas)
- Movido `/studio/agents` para dentro do `<AppLayout>` block (renderiza sidebar+header)

### Arquivos modificados/criados
- `backend/routers/studio/agents_registry.py` — reescrito (200 linhas, 4 endpoints + helper)
- `backend/routers/studio/screenwriter.py` — linha 380 wiring do resolve_agent_prompt
- `frontend/src/pages/AgentsPage.jsx` — reescrito (400 linhas)
- `frontend/src/components/layout/Sidebar.jsx` — path `/agents` → `/studio/agents`
- `frontend/src/App.js` — rotas `/agents` e `/studio/agents` dentro do AppLayout
- `memory/agents/*.json` × 9 + `memory/agents/book/*.json` × 8 — seed com `active:false`, `temperature:0.7`, `model`

### Testes realizados
- Lint JS: ✅ No issues found
- `GET /api/studio/agents/registry` → 17 agentes (8 video, 8 book, 1 audio) ✅
- `PUT /api/studio/agents/registry/screenwriter_agent` → 200 + history_size:1 ✅
- `GET /api/studio/agents/registry/screenwriter_agent` → description updated, temperature 0.75, edit_history populated ✅
- Screenshot Agents page (light mode): ✅ layout unificado com sidebar, cards agrupados por pipeline, badges CUSTOM/DEFAULT
- Screenshot modal de edição do Screenwriter: ✅ toggle, system prompt textarea, slider temperatura/qualidade, responsabilidades, footer Salvar

### Próximas etapas (Phase 2 wiring restante)
O padrão `resolve_agent_prompt("agent_id", fallback=hardcoded)` deve ser aplicado em:
- `storyboard.py` → `visual_researcher_agent`
- `dialogues.py` → `dialogue_writer_agent`
- `narration.py` → `narrator_agent`
- `sound_design_agent.py` → `sound_designer_agent`
- `book_factory.py` → todos os 8 agentes book
- `storyboard_validator.py` → `consistency_checker_agent`, `quality_validator_agent`
- `director.py` / `autonomous_loop.py` → `orchestrator_agent`

Aplicar 1 agente por vez, seedar o JSON com o prompt real hardcoded (ou deixar active:false), e testar.



## 2026-04-21 (Session 13b — Galeria unificada como página dedicada)

### Problema reportado pelo usuário
> "Esse layout está quebrado. Está aparecendo uma outra página no fundo quando clicamos em 'Personagens'. Temos que alinhar para que fique todo no mesmo padrão."

### Causa raiz
Ao clicar em "Personagens" no sidebar, a rota `/studio?gallery=1` abria o `AvatarLibraryModalV2` como **modal flutuante** sobre a página Projetos (Projects list ficava visível atrás com dimmer preto). Isso quebrava a consistência visual com as outras rotas do sidebar (Projetos, Agentes, Configurações), que renderizam como páginas normais.

### Fix: Modo `embedded` no AvatarLibraryModalV2
- Novo prop `embedded` (default `false`) em `AvatarLibraryModalV2`.
- Quando `embedded=true`:
  - Wrapper externo: `w-full min-h-[calc(100vh-3rem)] bg-[#FAFAFC] dark:bg-[#0A0614]` (substitui `fixed inset-0 bg-black/80`).
  - Inner container: `w-full h-full flex flex-col` (substitui `max-w-5xl rounded-2xl border shadow-2xl max-h-[90vh]`).
  - Botão "Fechar" do rodapé oculto (navegação volta via X ou sidebar).
  - Botão X do header com tooltip "Voltar" ao invés de "Fechar".
- Em `StudioPage.jsx`:
  - Novo flag `isGalleryPage = searchParams.get('gallery') === '1'`.
  - Quando `isGalleryPage=true`: Projects list (context bar + filtros + rows) é ocultado via `{!isGalleryPage && (<>...</>)}`.
  - `<AvatarLibraryModalV2 embedded={isGalleryPage} ... />` — modal vira page inline, senão fica modal flutuante (quando aberto por outros triggers como botão "Galeria" no header).

### Resultado
- Clicar em "Personagens" no sidebar → página full-width consistente com Projetos (mesmo sidebar, mesmo header, mesma largura, sem overlay).
- Modal flutuante ainda disponível quando galeria é aberta via botão interno (ex.: do DirectedStudio).
- Light + Dark mode validados via screenshots.

### Arquivos modificados
- `frontend/src/components/pipeline/AvatarLibraryModalV2.jsx` (prop `embedded`, wrapper condicional, rodapé condicional)
- `frontend/src/pages/StudioPage.jsx` (flag `isGalleryPage`, wrapper condicional da Projects list, prop `embedded` no modal)


## 2026-04-20 (Session 13 — Fix: /dashboard → /studio + Light mode legibilidade)

### Bug 1: Usuário caía no Dashboard antigo após login
- **Causa raiz:** `PublicRoute` em `App.js` redirecionava para `/dashboard` (DashboardStudio antigo com saudação "Bom dia" + cards) em vez de `/studio` (nova lista compacta).
- **Fix:**
  - `App.js`: `PublicRoute` agora redireciona para `/studio` após login.
  - `App.js`: Rota legada `/dashboard` agora faz `<Navigate to="/studio" replace />` — preserva compatibilidade com links antigos (`Onboarding`, `OnboardingAgentLang`, `Marketing` btn voltar).
- **Resultado:** Login → lista compacta de Projetos, direto. Nenhuma mudança nos links internos existentes.

### Bug 2: Galeria de Personagens ilegível em Modo Claro
- **Causa raiz:** `AvatarLibraryModalV2.jsx` tinha várias cores hex hardcoded (`#0D0D0D`, `#1A1A1A`, `#151515`, `#2A2A2A`, `#1E1E1E`) sem o prefixo `dark:` — no Light Mode mostravam texto escuro em fundos escuros ou texto branco em fundos brancos. Também vários `dark:bg-[...]` estavam sem `hover:` prefix causando bug CSS.
- **Fixes aplicados:**
  - Header: `bg-gradient-to-r from-[#0D0D0D] to-[#1A1A1A]` → `bg-white dark:bg-gradient-to-r dark:from-[#0D0D0D] dark:to-[#1A1A1A]`.
  - Overlay de nome dos cards (sempre sobre gradiente preto): `text-gray-900 dark:text-white` → `text-white` fixo com `drop-shadow-md`.
  - Bordas, sidebar de pastas, inputs de busca, selects de filtros, checkboxes 360°/Voz, botão Fechar do rodapé: todos com pares `bg-gray-X dark:bg-[#...]` e `border-gray-X dark:border-[#...]` corretos.
  - Corrigido bug `hover:bg-gray-200 dark:bg-[#2A2A2A]` → `hover:bg-gray-200 dark:hover:bg-[#2A2A2A]` (faltava prefixo `hover:` no dark variant) em 4 locais.
  - Removido bloco duplicado no final do arquivo (tail corrompido de edição anterior).

### Arquivos modificados
- `frontend/src/App.js` (linhas 93, 135-136)
- `frontend/src/components/pipeline/AvatarLibraryModalV2.jsx` (~14 pares de classes corrigidas + remoção de tail duplicado)

### Testes
- Lint JS: ✅ No issues found
- Screenshot Light Mode `/studio?gallery=1`: ✅ Título, nomes dos personagens e controles legíveis
- Screenshot Dark Mode `/studio?gallery=1`: ✅ Mantido com gradiente escuro original
- Login via formulário: ✅ Redireciona direto para `/studio` com 66 projetos visíveis


## 2026-04-20 (Session 12 — Fase 2 Finalização: ProjectRow reescrito)

### Ajuste final — layout aprovado aplicado

Após a Fase 2 estrutural (sidebar + theme toggle), o ProjectRow em si ainda estava no layout antigo (altura 100px+, progress circle de 48px, 2 linhas de meta, step icons redundantes).

**Reescrita do componente `ProjectRow` em `StudioPage.jsx`:**
- Container: `rounded-xl px-2 py-1` (antes: `p-4`) — reduziu altura ~40%
- Thumbnail: `w-28 h-16` horizontal 16:9 (antes: 80×80 quadrado)
- Metadata inline numa única linha: `📖 Livro · 👥 personagens · 📑 spreads · ✓ PDF pronto · ⏰ data`
- Removido: progress circle SVG de 48px + step icons (6× 24px) — eram barulho visual que duplicava o `status` textual
- Status badge: 24×24 redondo com gradient violeta→orange quando pronto
- Botões action: `w-[88px] h-6` (Abrir livro, roxo) + `w-[80px] h-6` (Carregar, laranja) — larguras fixas garantem alinhamento vertical
- Menu "···": ícone 12px, padding 1 (antes: 16px + p-2)
- `space-y-1.5` entre linhas (antes: `space-y-3`)
- Suporte completo `dark:` — funciona em ambos os temas

### Validação visual
- Light mode: cards brancos, sidebar lilás, acentos roxos, CTA laranja com glow ✓
- Dark mode: cards roxo-escuros, gradients vibrantes, mesma legibilidade ✓
- Toggle instantâneo no header, persiste em `localStorage` ✓

---

## 2026-04-20 (Session 11 — Fase 2: Nova Navegação — Sidebar + Dark/Light Toggle)

### Mudanças estruturais

**Novo chrome global:**
- `components/layout/Sidebar.jsx` (novo) — sidebar fixa 240px à esquerda com itens: Projetos / Personagens / Agentes / Configurações, contadores dinâmicos, avatar+créditos no rodapé. Desktop only (`hidden md:flex`).
- `components/layout/AppLayout.jsx` — reescrito. Remove BottomNav e TechGridBg. Novo header fixo (48px) à direita da sidebar com: toggle de tema (Sun/Moon), avatar dropdown (idioma + logout + settings).
- `contexts/ThemeContext.jsx` (novo) — provider `ThemeProvider` com `localStorage` (`studiox_theme`). Toggle adiciona/remove classe `dark` no `<html>`.

**Rotas migradas para AppLayout:**
- `/studio` agora está dentro do `<AppLayout />` (ganhou sidebar + header + toggle).
- `/dashboard`, `/chat`, `/agents`, `/crm`, `/analytics`, `/marketing`, `/settings`, `/pricing` já estavam e ganharam o novo layout automaticamente.
- `/studio/book/:projectId`, `/studio/book`, `/studio/agents` ficaram fora do AppLayout (wizards em tela cheia para foco no conteúdo).

**StudioPage reescrita (parcial):**
- Removida navbar antiga (seta "Dashboard", toggle Vídeos/Marketing, botão "📖 Livro" duplicado).
- Novo "context bar" interno: `Projetos N · Galeria · Novo Projeto` (compacto, inline).
- Banner "Empresa do Projeto" já tinha virado chip (Session 10) — agora com tokens dark.

**Paleta de marca aplicada** (após análise de brand asset do usuário):
- Primário: **violeta** (`violet-500/700` com glow)
- Secundário/CTA: **laranja** (`orange-500/600` vibrante)
- Fundos dark: `#0A0614`, `#110A1F`, `#1A1430`
- Bordas dark: `#2A2442`
- Todos os novos elementos suportam `dark:` variants

**Tipografia:**
- Outfit (headings) + Manrope (body) + Inter (legacy) — adicionadas ao `public/index.html`.

**Remoções:**
- `pages/UxPreview.jsx` (rota temporária `/ux-preview` removida).

### Validação

Smoke test via Playwright:
- `data-testid="app-sidebar"` count = 1 ✓
- `data-testid="header-theme-toggle"` count = 1 ✓
- Toggle: `document.documentElement.classList.contains('dark')` alterna corretamente ✓
- StudioPage carrega com 66 projetos listados nos dois temas ✓
- Sidebar nav: Projetos ativo destacado (roxo+bar lateral), contadores funcionando ✓
- Avatar dropdown continua funcional (idioma, edit, billing, logout) ✓

### Fora de escopo (propositadamente)

- BookStudio, DirectedStudio e outras páginas de wizard permanecem em light mode com âmbar — decisão consciente: o toggle global é **preparado para expansão gradual**, e o tema já se aplica automaticamente quando essas páginas forem refatoradas.
- BottomNav (mobile) ainda existe mas não renderiza nas rotas novas — mobile-first drawer fica para a Fase 3.
- Unificação Dashboard + StudioPage em `/projetos` único: **não feita** nesta sessão. StudioPage já funciona como "home de projetos" e Dashboard ainda é rota separada (mantida para back-compat).

---

## 2026-04-20 (Session 10 — UX Fase 1: Quick Wins de Minimalismo)

### Redução de ruído visual sem tocar em funcionalidade

**1. `AppLayout.jsx` — Language switcher movido para o dropdown do avatar**
- Antes: EN/PT/ES sempre visível no header global (3 botões permanentes que o usuário mexe 1× por vida)
- Agora: dentro do dropdown do avatar, seção "IDIOMA" com Globe icon e Check visual no idioma ativo
- Header ficou mais leve: só logo + créditos + avatar

**2. `DashboardStudio.jsx` — Seção "Agentes do Estúdio" removida**
- Antes: 6 cards pesados (Screenwriter, Shot Director, Continuity, Voice Designer, Sound Agent, Producer) ocupando meia tela na Dashboard
- Era redundante com a tab "Agentes" na BottomNav
- Array `studioAgents` (44 linhas) removido junto

**3. `BookStudio.jsx` — Toolbar de render consolidada**
- Antes: 5 botões inline (Baixar · Nova aba · Editar ilustrações · Editar capa · Renderizar)
- Agora: "Baixar PDF" (CTA primária) + "Mais" (dropdown com as 4 ações secundárias)
- Dropdown fecha com click-outside (padrão UX)

**4. `StudioPage.jsx` — Banner "Empresa do Projeto" → chip discreto**
- Antes: card gradient grande (80px+ de altura) com ícone 40px e 2 linhas de texto
- Agora: pill inline "Empresa: {name} ›" (30px altura) que expande ao clicar
- Libera ~60px verticais na home do Studio

### Validação automatizada (screenshots + DOM queries)
- Dashboard: seção "Agentes do Estúdio" count = 0 ✓
- Header: `data-testid="header-lang-selector"` count = 0 ✓
- Avatar dropdown: `data-testid="profile-lang-selector"` count = 1 ✓
- BookStudio: `render-more-menu` + 4 itens (open-pdf, edit-illustrations, edit-cover, rerender) ✓
- StudioPage: `company-chip` count = 1 ✓

**Impacto UX:** Dashboard ~280px mais curta, BookStudio toolbar visualmente limpa, StudioPage com +60px úteis. Zero regressão funcional — todas as ações antigas continuam acessíveis.

---

## 2026-04-20 (Session 9 — Cleanup Tier 2 + Tier 3: Docs legados + Tests antigos)

### Tier 2 — Documentação do projeto anterior (AgentFlow) removida

**Zero impacto em runtime** — apenas arquivos `.md` informativos obsoletos.

Removidos do `/app/` raiz (25 arquivos, ~470KB):
- 7 × `AGENTFLOW_*.md` (especificações do SaaS WhatsApp anterior)
- 18 × guias antigos: `BATCH_*`, `KLING_*` (obsoletos), `PIPELINE_*`, `MULTI_ENGINE_*`, `MUSICAL_VIDEO_*`, `DIRECTOR_AUTONOMOUS_*`, `ELEVENLABS_MUSIC_*`, `CONTENT_ADVISORS_*`, `DEBUG_BATCH_*`, `COMO_TESTAR_KLING`, `GUIA_*`, `SCRIPT_TESTE_AB`, `image_testing`

Removidos de `/app/memory/` (31 arquivos, ~500KB):
- Docs de features já implementadas: `ARCHITECTURE_ANALYSIS`, `AUDIO_CONTINUITY_FIXES`, `AUTONOMOUS_AGENTS_*`, `AVATAR_*`, `BUCKET_FIX`, `CHARACTER_*`, `CHECKPOINT_SAFETY`, `DESIGN_SYSTEM_PREMIUM`, `DIRECTOR_REVIEW_*`, `ENGINEERING_PLAN`, `FALLBACK_SYSTEM`, `FINAL_IMPLEMENTATION_REPORT`, `FRAME_STITCHING_*`, `LANGUAGE_*`, `MASTERMIND_BLUEPRINT`, `PARALLEL_AGENTS_SYSTEM`, `PLANO_COMPLETO_AUDIO_CAMADAS`, `PRODUCTION_STRATEGY`, `QUALIDADE_*`, `SOUND_DESIGN_AGENT`, `STATUS_DIALOGUES_AND_CONTINUITY`, `UX_*`, `VIDEO_STITCHING_ARCHITECTURE`, `AUDIT_REPORT`

Removidos de `/app/backend/docs/` (2 arquivos + diretório):
- `COMPLETE_PIPELINE.md`, `DIALOGUE_TIMELINE.md`

**Mantidos (source of truth atual):**
- `/app/README.md`, `/app/test_result.md`
- `/app/memory/PRD.md`, `CHANGELOG.md`, `ROADMAP.md`, `test_credentials.md`

### Tier 3 — Tests antigos arquivados

**118 arquivos `test_iteration*.py`** (iterações 10 a 136) movidos para `/app/backend/tests/_archive/`.

- Testavam features/fluxos antigos que mudaram nas últimas 30+ iterações (não servem mais como regressão confiável).
- NÃO deletados — ficam disponíveis para consulta/recuperação se necessário.

**Mantidos (tests ainda relevantes para BookFactory atual):**
- `test_iteration137_book_factory.py` — BookFactory pipeline
- `test_iteration138_bookfactory_p0p1.py` — BookFactory P0/P1 fixes

### Validação

Backend reiniciado sem erros. Smoke test completo:
- `/api/health` → 200
- `/api/auth/login` → 200
- `/api/studio/projects` → 200 (lista de 66 projetos intacta)
- `/book/state` em 2 projetos distintos → 200

**Impacto total (Tier 1 + 2 + 3):** ~3MB de código/docs/tests obsoletos eliminados, zero regressão em fluxos de vídeo/livro/música.

---

## 2026-04-20 (Session 8 — Cleanup Tier 1: Arquivos mortos e diretórios vazios)

### Limpeza preliminar do código migrado de outro projeto (AgentFlow → StudioX)

**Removidos sem impacto (zero referências no código vivo):**

Frontend:
- `/app/frontend/src/components/DirectedStudio.jsx.backup`
- `/app/frontend/src/pages/Profile.jsx` (órfão — sem rota, sem imports)
- `/app/frontend/src/pages/Dashboard.jsx` (App.js já usa `DashboardStudio` com alias `Dashboard`)
- `/app/frontend/src/pages/Landing.jsx` (App.js usa `LandingV2`)
- `/app/frontend/src/components/pipeline/AvatarLibraryModal.jsx` (V1 substituída por V2)

Backend:
- `/app/backend/routers/studio/director.py.backup`
- `/app/backend/providers/` (diretório inteiro — 10 arquivos, arquitetura abstracta nunca usada)
- `/app/backend/db/` (`__init__.py` + `repositories/__init__.py` vazios)
- `/app/backend/core/video_stitching.py` (0 imports)
- `/app/backend/core/idempotency.py` (0 imports)
- `/app/backend/test_commercial.py`, `/app/backend/test_gemini_imagen.py` (testes avulsos na raiz)
- `server.py:109-114` — bloco try/except que importava `providers.ai.get_provider_status` (dead code)

**Validação:**
- Backend reinicia limpo, sem erros de import.
- Smoke-test: `/api/health`, `/auth/login`, `/auth/me`, `/studio/projects`, `/book/state` → todos 200 OK.
- Frontend: lista de projetos + filtros continuam funcionando (66 projetos, 61 vídeos / 5 livros).

**Impacto:** ~70KB de código morto + 2 diretórios vazios removidos. Próximos tiers (docs antigos + testes legados) aguardam decisão.

---

## 2026-04-20 (Session 7 — P0 Fix: Event Loop Unblocking para Login/Auth)

### Bugfix P0 — Timeout de login durante pipelines pesadas

**Causa raiz:** Rotas `async def` em `auth.py` e as dependências `get_current_user` / `get_current_tenant` (em `core/deps.py`) faziam chamadas Supabase síncronas (`.execute()`) e bcrypt (`pwd_context.verify`) diretamente no event loop. Cada chamada bloqueava TODAS as requisições async por 100–600ms. Sob carga (várias pipelines de livro/vídeo + logins simultâneos), o event loop ficava engasgado e os requests empilhavam, causando timeouts visíveis em `/api/auth/login`.

**Fix:**
- `core/deps.py` — `get_current_user` e `get_tenant` agora envolvem `supabase.table(...).execute()` em `asyncio.to_thread(...)`. Isso libera o event loop imediatamente enquanto o driver sync roda no threadpool padrão do FastAPI.
- `routers/auth.py` — helper `_run(fn, *args, **kwargs)` centraliza o offload. Todas as chamadas síncronas de Supabase e bcrypt (`hash`, `verify`) em `signup`, `login`, `auth/me`, `auth/profile`, `tenants` (POST/GET) foram envolvidas.

**Validação (teste de carga):**
- 1 login: 1.5s (baseline — bcrypt domina).
- 10 logins concorrentes: 8.3s total (antes serializavam, podia dar timeout).
- 5 GETs protegidos + 5 logins em paralelo: **todos 200 em 8.5s total** (todos completam juntos, não em sequência — prova que event loop não está mais bloqueado).

**Escopo deliberadamente mantido:** `core/cache.ProjectCache.get_settings` NÃO foi convertido — 95%+ dos hits são cache (retorno imediato), e envolver teria impacto em TODOS os endpoints do studio (mudança intrusiva). Observação para monitoramento futuro: se `/api/studio/projects` voltar a timeoutar, converter cache também.

---

## 2026-04-20 (Session 6 — Edição Manual de Prosa + Filtros de Projeto + Banner Híbrido)

### Bugfix P0 — "Editar prosa manualmente não funciona"

**Causa raiz:** `window.prompt()` nativo é inadequado para editar texto multi-parágrafo. Os navegadores truncam/quebram o valor default quando passado texto longo com `\n\n`, tornando a edição inviável.

**Fix em `/app/frontend/src/pages/BookStudio.jsx`:**
- Removido `window.prompt` do handler `editChapterProse`.
- Adicionado estado `proseEditor = { open, chapterIdx, prose, saving }`.
- Implementado modal dedicado com `<textarea>` (min-h 400px, font-serif, spellcheck) + contadores (palavras / caracteres / parágrafos) + botões Salvar/Cancelar.
- Handler `saveProseEdit` chama PATCH `/api/studio/projects/{id}/book/chapter/{idx}/prose`, recarrega estado e fecha modal automaticamente.
- Data-testids: `prose-editor-modal`, `prose-editor-textarea`, `btn-save-prose-edit`, `btn-cancel-prose-edit`, `btn-close-prose-editor`.

### Bugfix P0 — "Preview do livro não aparece"

**Causa raiz:** PDFs do BookFactory são grandes (14–35 MB). O download via proxy levava 10–25s, mas o UI mostrava apenas "Carregando PDF..." estático, sem indicação de progresso. Usuários desistiam achando que travou.

**Fix em `BookStudio.jsx`:**
- `loadPdfBlob` agora consome a resposta via `ReadableStream` (getReader) e emite `pdfProgress = { loaded, total }` incremental.
- UI de loading substituída por barra de progresso animada (`pdf-progress-bar`) + contador "X / Y KB · Z%" + dica "PDFs grandes podem demorar ~15s".
- Fallback para `blob()` direto quando `getReader` indisponível (compat).

### Feature P1 — Filtros de Tipo de Projeto

**`/app/frontend/src/pages/StudioPage.jsx`:**
- Adicionado estado `projectTypeFilter` ('all' | 'video' | 'book' | 'both').
- Helper `projectKind(p)` infere tipo do projeto (respeita `output_mode`, com fallback para `project_bible.book_bible` em projetos legacy).
- Pills coloridos com contagem: Tudo / Vídeos / Livros / Híbridos, abaixo da search bar.
- Data-testids: `project-type-filter`, `filter-all`, `filter-video`, `filter-book`, `filter-both`.

### Feature P1 — Banner de Navegação Híbrida

**`/app/frontend/src/components/DirectedStudio.jsx`:**
- Importado `useNavigate` do react-router-dom.
- Estado `outputMode` adicionado e preenchido a partir de `p.output_mode` ao carregar projeto.
- Banner "📖 Ver livro" (gradient âmbar) renderizado no topo do studio quando `outputMode === 'both'`, com botão navegando para `/studio/book/{id}`.
- Data-testid: `hybrid-project-banner`, `btn-open-book-studio`.

### Testing
- testing_agent_v3_fork — iteração 139 — 100% frontend passou, 4/4 features validadas.

---

## 2026-04-20 (Session 5 — Diagramador Master + Revisor Tipográfico LLM)

### Feature: 2 agentes LLM profissionais de diagramação

**Problema:** A diagramação era heurística (distribuição proporcional simples) sem consciência do conteúdo. Ilustrações ficavam em posições técnicas mas não semanticamente conectadas ao texto.

**Fix — Pipeline agora tem 2 novos agentes:**

1. **Diagramador Master** (`POST /book/design-layout`):
   - Persona combinada: Robert Bringhurst (tipografia) + Massimo Vignelli (grid) + Chip Kidd (narrativa) + Irma Boom (livro-objeto).
   - Lê cada capítulo com parágrafos numerados + descrições das ilustrações disponíveis.
   - Retorna sequência de `blocks` contextualizados: `chapter_opener`, `paragraph(index)`, `illustration(page_number, caption)`, `pull_quote(text)`, `section_break`.
   - **Posiciona cada imagem IMEDIATAMENTE APÓS o parágrafo que a descreve** (match semântico).
   - Adiciona opcionalmente pull quotes (uma linha literária destacada) e section breaks (descanso ornamental entre atos).

2. **Revisor Tipográfico** (`POST /book/review-layout`):
   - Persona: Senior QA editor Penguin Random House (25 anos).
   - Audita o plano do Diagramador contra 6 critérios: image context match, pacing, opener, pull quotes verbatim, completeness, narrative order.
   - Retorna `critique` (lista de issues encontradas e corrigidas) + `blocks` corrigidos.
   - Valida que toda ilustração fica perto do parágrafo certo, pacing ≤ 1 imagem a cada 3 parágrafos, etc.

**Ambos paralelos:** `asyncio.gather` processa todos os capítulos simultaneamente (~15s total vs ~60s sequencial).

**Template atualizado** (`book_base.html.j2`):
- Suporte a `chapter-opener` com estilos `drop_cap` (capitular 2.4×) e `cinematic` (epígrafe com ornamento ✦).
- `.pull-quote` com borda superior/inferior dourada, itálico 1.35× font-size.
- `.section-break` com 3 estrelas ✦ ✦ ✦ douradas.
- `<figcaption>` nas imagens renderizando a legenda curta que o Diagramador propôs.

**Pipeline integrada:** Auto-Run agora executa: outline → capítulos → plano de ilustrações → ilustrações → capa → **Diagramador Master** → **Revisor Tipográfico** → render-pdf → preflight.

**✅ Validado no livro Ash:**
- 8 capítulos diagramados + revisados.
- Revisor encontrou e corrigiu issues reais (ex: "Illustration id=6 moved to after paragraph 1 — represents Ash dancing, described immediately after that paragraph").
- Página 5 renderizada: ilustração grande "Ash chegando à casa da Brenda" COM legenda "Ash chega à casa da Brenda, animado e curioso." — perfeitamente alinhada ao texto.
- 44 páginas (vs 64 antes), layout denso e profissional.



### Fix 5: Regerar ilustração individual no fluxo chapter + prompt reforçado
**Problema do usuário:** Algumas ilustrações saíam fora do padrão Pixar 3D (pg.6 cartoon bichinho, pg.10 vector flat, pg.13 múltiplos cachorros random). Não havia botão para regenerar individualmente no fluxo chapter.

**Fix Backend (`book_generate_illustration`):**
- Agora sempre passa **todos os personagens do projeto** (até 5) como refs multimodais (prioriza `characters_in_page`), não só os na cena.
- Inclui `char_descriptions` no prompt com nome + descrição curta de cada personagem.
- Prompt reescrito com regras HARD: "NO LETTERS", "NO extra characters/dogs", "DO NOT switch art style" (explicita que não pode mudar de 3D Pixar pra flat/cartoon/pixel).
- Reforço do `style_rules` + `palette` do Art Director como obrigatórios.

**Fix Frontend (`BookStudio.jsx`):**
- No grid do fluxo chapter, cada card de ilustração agora tem 2 botões:
  - 🔄 **Regerar** — usa o plano original (rápido, corrige drift).
  - ✨ **Custom** — abre prompt para o usuário escrever instruções extras (estilo, personagens, excluir elementos).
- Botão **Regerar todas** no header (para refazer o lote inteiro após ajustar Art Director).
- Pré-preenche o prompt Custom com um template pronto sobre estilo Pixar 3D + Ash/Snow, que o usuário pode editar.
- Banner de dica roxo explicando o uso do botão Custom.

**Validação:** pg.6 regerada — saiu de cartoon flat para Pixar 3D com volumetric lighting, soft shadows, detailed fur, Ash corretamente identificado por tag.



### Fix 3: PDF download bloqueado (`ERR_BLOCKED_BY_CLIENT`)
**Bug:** O botão "Baixar PDF" apontava direto para o domínio `*.supabase.co`. Ad-blockers do usuário (uBlock/Chrome) bloqueiam esse domínio → download falha silenciosamente.

**Fix:**
- Novo endpoint `GET /api/studio/projects/{id}/book/download-pdf` (`book_factory.py`): faz stream do PDF pelo domínio da própria app com `Content-Disposition: attachment; filename="{título}.pdf"`.
- Frontend (`BookStudio.jsx`): nova função `downloadPdf()` faz fetch com auth + blob + click sintético. Botão "Baixar PDF" agora usa proxy. "Abrir em nova aba" ainda mantém link direto como fallback.

**Validação:** Curl do proxy retornou HTTP 200, 12.4 MB, `Content-Disposition: attachment`, PDF válido 64 páginas.

### Fix 4: UI BookStudio em branco no fluxo chapter (`infantil_ilustrado`)
**Bug:** Outline, Ilustrações e Render tinham layout exclusivo para `spreads` do picturebook. No fluxo chapter, `spreads` é sempre vazio → painéis mostravam zero conteúdo mesmo com 8 capítulos escritos e 16 ilustrações geradas.

**Fix em `BookStudio.jsx`:**
- Detecta `formatPreset` via `bookState.brief.format_preset` e flag `isPicturebook`.
- Outline panel: quando chapter flow, renderiza `outlineChapters` com badge "✓ N palavras" (verde) ou "pendente" (cinza) + accordion `<details>` mostrando a prosa escrita (`chapters[idx].prose`).
- Ilustrações panel: quando chapter flow, renderiza `illustration_plan` (grid com `pg.N • Cap X • tipo`).
- `renderPDF()` agora escolhe endpoint: `render-picturebook` para picturebook ou `render-pdf` para chapter flow.
- `loadState` detecta step correto em ambos os fluxos (verifica `illustration_plan[].illustration_url` além de `spreads[].illustration_url`).

**Validação visual:** Página do projeto Ash (`017f57ef8ecd`) mostra título "Cuidando do Meu Pulmerânea: Dicas do Ash", blurb mencionando Ash/Snow/Brenda, todos os 8 capítulos com word counts (664, 644, 645, 703, 674, 614, 716, 714), 16 ilustrações em grid com Ash cinza + Snow branco + Brenda visíveis.



### Fix 1: Auto-Run Pipeline falhava em `format_preset != 'picturebook'`
**Bug:** Projeto "Manual do Pulmeranea" (Ash, `infantil_ilustrado`) falhava com `400: No spreads to render` porque o background task `_run_book_pipeline_background` assumia sempre fluxo picturebook (spreads → `render-picturebook`), mas `generate-outline` só salva `spreads` quando `format_preset == "picturebook"`. Para outros formatos gera `chapters`.

**Fix:** `_run_book_pipeline_background` agora detecta `format_preset` e roteia:
- `picturebook` → outline (spreads) → art-direct → meeting-room → illustrate-spreads → cover → `render-picturebook` → preflight
- `infantil_ilustrado` / `romance_adulto` / `tecnico_historico` → outline (chapters) → art-direct → generate-chapter (loop) → plan-illustrations → generate-illustration (loop) → cover → `render-pdf` → preflight

`pipeline_error` e `pipeline_finished_at` agora são resetados ao iniciar nova corrida.

**Validação E2E (projeto `017f57ef8ecd`):** 8 capítulos escritos, 16 ilustrações geradas, capa gerada, PDF 64 páginas renderizado, preflight passou. Pipeline `step=done` com sucesso.

### Fix 2: Capa cortada lateralmente (Snow desaparecendo)
**Bug:** Gemini 3 Image retorna PNG `1024×1024` (aspect 1.0), mas trim 6×9 + bleed é `158.4×234.6 mm` (aspect 0.675 — portrait). Template usa `background-size: cover`, que força o preenchimento do container portrait escalando a imagem quadrada até `234.6×234.6 mm` — cortando ~15% de cada lado. Personagens nas laterais (Snow na capa do Ash) sumiam.

**Fix:** Em `book_generate_cover_v2`, **após** o Gemini, a imagem é padded server-side via PIL para o aspect exato do trim+bleed. Cor de fundo = `palette.primary` (extraída pela Art Director). O resultado (1024×1517 para 6×9) bate perfeitamente com o container do template — zero crop.

**Validação visual:** Capa do Ash regenerada — Ash + Shadow (cinza) + Snow (branco) todos totalmente visíveis e centrados. Confirmado por análise de imagem.

### Arquivos alterados
- `/app/backend/routers/studio/book_factory.py` (pad aspect + branching + reset flags)

---


## 2026-04-19 (Session 4 — BookFactory P0+P1 completo)

### P0 — UI BookStudio (nova rota `/studio/book/:projectId`)
Nova página React (`/app/frontend/src/pages/BookStudio.jsx`, ~560 linhas) com wizard de 7 passos navegável:

1. **Briefing** — formulário com todos os campos (name, title, author, idioma, briefing, format picturebook/chapter/romance/técnico, trim 6x9/5x8/A4/A5, target_spreads, audience, visual track, modo autoria, herdar personagens de outro projeto via `source_project_id`, reference_work quando public_domain).
2. **Outline** — exibe title, subtitle, blurb, badges dos RAG sources (Bíblia), lista de spreads com texto + scene description + characters + botão rewrite individual.
3. **Arte** — editor visual de tema: inputs de fonte (título e corpo), tamanho pt, 5 color pickers ao vivo (page_bg, text_box_bg, title_color, body_color, accent) + preview da fonte renderizado na hora. PATCH direto para `/book/theme`.
4. **Revisão (Meeting Room)** — mostra consistency_score em destaque, overall_assessment, lista colorida de issues por severity (critical vermelho, major âmbar, minor cinza), botão "Aplicar fixes críticos".
5. **Ilustrações** — grid responsivo com thumbnails, botão "Gerar todas faltantes" em lote, botão regenerar por spread.
6. **Capa** — preview com overlay de título + lombada calculada, botões regenerar e "Renderizar PDF final".
7. **PDF** — tela "Livro Pronto!" com page_count, preflight status verde/amber, botão Baixar PDF.

Auto-detecta o passo correto ao carregar projeto existente (usa `pdf_url`, `cover`, spreads com `illustration_url`, `meeting_room_review`, `theme`, `outline` pra decidir).

Botão "📖 Livro" adicionado no header do `StudioPage.jsx` com `data-testid="nav-bookfactory"`.

### P1 — Extensões backend

**Novas composições no `agent_compositions.json`**:
- `book_picturebook_user_author`
- `book_picturebook_public_domain` (lidera com Pesquisador + RAG)
- `book_picturebook_free` (lidera com Art Director)

**Novos endpoints em `book_factory.py`**:
- `PATCH /api/studio/projects/{id}/book/theme` — merge partial de theme/palette/style_rules; permite UI editar fontes/cores.
- `POST /book/rewrite-spread` — Author Agent reescreve UM spread via Claude preservando `illustration_url`.
- `POST /book/apply-review-fixes` — varre `meeting_room_review.issues` e auto-aplica critical/major via rewrite-spread; retorna `{applied, skipped, total_applied}`.

### Testing
- Testing agent iteration 138: **18/20 backend (90%) + 100% frontend UI verificada**.
- 2 issues minor: intermittent 500 em criação rápida (Supabase race) + React warning de `<span>` dentro de `<option>` — ambos LOW priority.
- Smoke test visual via Playwright: tela de briefing + tela de render carregam corretamente no preview environment.

### Arquitetura agora
Agentes **ativos** no fluxo picturebook: Orchestrator + Author + Art Director Editorial + Illustrator Interior + Cover Designer + Book Editor + Proofreader + Layout Designer + Preflight (8 agentes). Meeting Room em loop de debate simples via Editor review + apply-fixes. RAG Bíblia PT-BR com 5 passagens ARA (Gênesis 12, 21, 22 + Hebreus 11).


## 2026-04-18 → 2026-04-19 (Session 4 — BookFactory MVP)

### BookFactory — Pipeline Paralela de Livros Físicos (NEW)

**Objetivo**: Criar uma segunda pipeline ao lado do gerador de vídeos para produzir **livros físicos prontos para impressão** (PDF com sangria, fontes embutidas, layout profissional), reusando a Character Universe, Project Bible e agentes já existentes do StudioX.

**Decisões arquiteturais aprovadas pelo usuário**:
- Motor de diagramação: **WeasyPrint** (Python puro, CSS Paged Media) — descartado LaTeX por limitação de disco (2.2 GB livres vs ~1.5 GB do TeX Live)
- RAG: **stub in-memory** com interface pronta (Bíblia + Machado de Assis) — ChromaDB/pgvector em Fase 2
- 3 formatos via templates: **6×9** (infantil/romance), **5×8** (romance), **A4** (técnico/histórico) + A5 bonus
- Universo compartilhado: usuário escolhe no briefing entre `book` | `video` | `both` (meeting room adaptativa)
- Branding: **BookFactory**

**O que foi implementado**:

1. **8 novos agent specs** em `/app/memory/agents/book/`:
   - `author_agent` (Autor Profissional)
   - `art_director_editorial_agent`
   - `illustrator_interior_agent`
   - `cover_designer_agent`
   - `book_editor_agent` (consistência narrativa)
   - `proofreader_agent`
   - `layout_designer_agent` (decide tipografia/grid)
   - `preflight_agent` (valida PDF final)

2. **Meeting Room adaptativa**: `agent_compositions.json` com 7 composições dinâmicas resolvidas por `(output_mode, format_preset, autoria_mode)`. Modo `video_only` preservado idêntico ao fluxo atual.

3. **Novo módulo backend**: `/app/backend/routers/studio/book_factory.py` (~540 linhas) com 10 endpoints sob `/api/studio/`:
   - `GET /book/trim-sizes`, `GET /book/compositions`
   - `POST /projects/{id}/book/start` (grava brief + resolve composition)
   - `POST /book/generate-outline` (Autor — Claude)
   - `POST /book/approve-outline`
   - `POST /book/generate-chapter` (Autor — Claude, com continuidade)
   - `POST /book/plan-illustrations` (Art Director)
   - `POST /book/generate-illustration` (Ilustrador — Gemini 3 Image com character refs)
   - `POST /book/generate-cover-v2` (Designer de Capa, calcula lombada pelo page count)
   - `POST /book/proofread` (Revisor)
   - `POST /book/render-pdf` (Diagramador + WeasyPrint)
   - `POST /book/preflight` (Preflight Agent — pypdf)
   - `GET /book/state`

4. **Template Jinja2 + CSS Paged Media** em `/app/backend/templates/book/book_base.html.j2`:
   - `@page` com `bleed: 3mm` e `marks: crop cross`
   - Running headers, footer com número de página
   - Drop cap (opcional por preset)
   - Capítulo começa em página ímpar (recto) quando preset pede
   - `widows: 3, orphans: 3, hyphens: auto, text-align: justify`
   - 3 presets: infantil_ilustrado / romance_adulto / tecnico_historico

5. **RAG stub**: classe `_RAGStub` com API idêntica a um retriever real (`.search(query, top_k)`). Interface pronta para trocar por ChromaDB/pgvector sem mexer no resto.

6. **LLM integration**: usa o pattern oficial do projeto — `_call_claude_async` em `_shared.py` (litellm + `anthropic/claude-sonnet-4-5-20250929`). Migrei de `emergentintegrations.LlmChat` (que tem bug reportado pelo testing agent) para o padrão que já funciona no pipeline de vídeo.

**Testing**:
- Testing Agent v3 rodou 26 testes (21 passaram, 5 bloqueados pelo bug da emergentintegrations).
- Depois de migrar para `_call_claude_async`, rodei **fluxo end-to-end real** via curl: criou livro "A Raposinha Generosa" com 8 capítulos, escreveu capítulo 1 em português (200 palavras), renderizou PDF de 17KB, preflight passou com 0 blockers.
- Backward compat: pipeline de vídeo 100% preservado (endpoints antigos continuam funcionando).

**Pendente para próxima sessão** (UI):
- Componente `BookStudio.jsx` (nova rota `/studio/book/:id`)
- Page-flip preview com PDF.js
- Editor de outline inline (drag-reorder de capítulos)
- Preview de ilustrações por página
- Botão unificado "Criar Livro" na home do Studio X

**Fase 2 (roadmap)**:
- Substituir RAG stub por ChromaDB com ingestão real (Bíblia PT, Gutenberg)
- Pós-processamento CMYK + PDF/X via ghostscript
- Integração Amazon KDP, Uiclap, Lulu APIs
- Book+Video paralelo (Universe Bible bifurcando)
- Multi-language (EN/ES no template)


## 2026-04-18 (Session 4 — continuação)

### Video Quality Upgrade — Sprints P0+P1 completos
**Problema identificado**: Prompts Sora 2 estavam 10x maiores que o recomendado pelo guia oficial OpenAI 2026 (>5000 chars, guia pede <150 palavras). Sora ignorava silenciosamente metade do prompt.

**Implementado**:

1. **Toggle Production Quality** (`fast` vs `cinema`)
   - Campo novo `production_quality` em `StudioProject` (default `fast` para backward compat).
   - UI: radio no modal de novo projeto (só aparece quando `videoEngine=sora`). Badge visual "⚡ Rápida" vs "🎬 Cinema".
   - `fast`: Sora 2 @ 1280×720, prompt legacy (longo), FFmpeg CRF 23 / AAC 128k — comportamento anterior.
   - `cinema`: Sora 2 Pro @ 1792×1024 HD, prompt compacto (<200 palavras) cinema-style, FFmpeg CRF 18 / preset medium / AAC 256k.

2. **Prompt Sora cinema-style (P0)**
   - Prompt novo em formato `[SHOT] / [ACTION] / [DIALOGUE] / [STYLE] / [VOICES] / [TEXT]`.
   - Identidade visual movida integralmente para o `input_reference` (keyframe Gemini).
   - Só ativa quando `production_quality=cinema`. Modo `fast` mantém o prompt longo original.

3. **Sora 2 Pro @ 1792×1024 (P0)**
   - `_generate_video_with_openai_direct` e `_generate_video_unified` agora aceitam `model` e `sora_model` parâmetros.
   - Auto-seleciona `sora-2-pro` + `1792x1024` quando `production_quality=cinema`.

4. **Gemini 3 Pro Image (Nano Banana Pro) via env var (P0)**
   - `core/llm.py` agora lê `GEMINI_IMAGE_MODEL` (default `gemini-2.5-flash-image`).
   - Para ativar consistência de personagens top-tier, basta setar `GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview` no `.env`.

5. **FFmpeg cinema preset (P1)**
   - `_concatenate_videos` agora aceita `cinema_quality: bool`.
   - Cinema: `-crf 18 -preset medium -c:a aac -b:a 256k -pix_fmt yuv420p`.

6. **Emotion markers no diálogo (P1)**
   - `dialogue_timeline` beats agora suportam campo opcional `emotion` que é injetado como `[whispers]`, `[laughing]`, `[tense]` etc. no prompt Sora.

**Backward compatibility**: Todas as mudanças são condicionais. Projetos existentes sem `production_quality` rodam em modo `fast` e se comportam exatamente como antes.

**Testing**: 13/13 testes backend passaram via testing_agent_v3_fork (iteration_136.json).


## 2026-04-18 (Session 4)

### Sora 2 Character Voice Lock (NEW)
- **Problem**: Sora 2 generates a different voice for each scene even for the same character (stochastic sampling).
- **Solution**: Integrated OpenAI's official Sora 2 Characters API (`POST /v1/sora/characters`) that creates a reusable `character_id` from an anchor scene. Reusing the ID in subsequent generations locks **voice + appearance** natively.
- New module: `/app/backend/routers/studio/sora_characters.py`
- Auto-detects first rendered scene per character to use as voice anchor.
- Supports Sora 2 2-character-per-generation limit (March 2026).
- Endpoints:
  - `POST /api/studio/projects/{id}/auto-register-sora-characters` (auto, idempotent)
  - `POST /api/studio/projects/{id}/register-sora-character` (manual with specific scene)
  - `GET  /api/studio/projects/{id}/sora-characters`
  - `DELETE /api/studio/projects/{id}/sora-characters/{character_name}`
- `production.py`: `_generate_video_with_openai_direct` and `_generate_video_unified` accept optional `sora_character_ids`. Character lookup is per-scene from `project.characters[].sora_character_id`.
- **Backward compatible**: zero impact on existing/in-flight projects (fallback is empty list → payload identical to before).
- UI: "🎤 Travar Vozes" button on the Vídeos tab of `DirectedStudio.jsx` + badge showing locked characters count.


## 2026-04-17 (Session 3)

### ElevenLabs Music - Children's Song Generator
- Integrated ElevenLabs Music API (`client.music.compose()`) for generating original children's songs
- LLM (Claude) generates lyrics based on story briefing + scenes + characters
- Music style adapts to age range: 0-3 (lullaby), 3-5 (Galinha Pintadinha), 5-8 (Disney Junior), 8-12 (Disney/Pixar)
- Lyrics in project language (Portuguese by default)
- Endpoint: `POST /api/studio/projects/{id}/generate-music`
- UI card "Música Cantada" added to RESULTADO tab with lyrics display
- Song saved to project as `generated_song` field

### Film Rebuild for Large Projects
- Fixed: Previous rebuild of 26 scenes crashed silently (FFmpeg crossfade memory exhaustion)
- Reduced crossfade scene limit: 30 → 15 scenes
- V2A sonoplastia now non-blocking in rebuild
- Successfully rebuilt "Jonas e o Peixe Grande" (32 scenes, 276MB → 17MB)

### Folder System Improvements
- Fixed: Delete folder button not working (replaced `window.confirm` with inline two-click)
- Fixed: Stale avatar IDs auto-cleanup was deleting valid avatars (REMOVED auto-cleanup)
- Hierarchical folders: parent_id support with expand/collapse (no modal reload)
- Compact sidebar: smaller fonts, narrower width
- Chevron arrow moved after folder name for alignment
- `useTransition` for smooth folder switching (no flash)
- New endpoint: `PUT /api/folders/bulk-update` for atomic folder operations
- New endpoint: `PUT /api/folders/update-avatars` for replacing folder avatar IDs

### Audio Pipeline Upgraded (Sora 2)
- Primary: ElevenLabs Music generates original soundtrack matching story
- Fallback: Kling V2A for BGM + SFX if ElevenLabs fails
- Mix: native Sora 2 audio (100%) + music (15% volume)

## 2026-04-15 (Session 2)
[... previous entries unchanged ...]
