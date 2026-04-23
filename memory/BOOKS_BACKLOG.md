# 📚 StudioX Books — Backlog de Ajustes e Melhorias

> **Status**: `PAUSED` — foco atual do projeto está em **Criação de Vídeos Perfeitos**.
> Este arquivo registra tudo que foi identificado como necessário de ajustar no pipeline de livros quando formos voltar a focar nessa trilha.
>
> **Última análise em tempo real**: 23/04/2026 (Manual do Pulmeranea, 33 spreads, score 85/90).

---

## 🔴 P0 — Bugs / Quebras que impedem uso profissional

### 1. CMYK conversion fica como "pending warning" em vez de automático
- **Arquivo**: pipeline de render do PDF (provavelmente em `book_factory.py` render step)
- **Sintoma**: Todos os PDFs terminam em RGB + preflight_report emite `"CMYK conversion pending — use ghostscript post-processing before printing"`
- **Expectativa**: pipeline já deveria gerar PDF CMYK 300dpi pronto para KDP/Lulu sem intervenção manual
- **Solução sugerida**: adicionar step `ghostscript` no final do render com parâmetros:
  ```bash
  gs -o final_cmyk.pdf -sDEVICE=pdfwrite -sProcessColorModel=DeviceCMYK \
     -sColorConversionStrategy=CMYK -dPDFSETTINGS=/prepress final.pdf
  ```
- **Impacto**: bloqueia impressão profissional. Usuário precisa converter manualmente depois.

### 2. Glen Keane Visual Continuity Auditor NÃO é chamado automaticamente
- **Arquivo**: `/app/backend/routers/studio/book_factory.py` (fim do pipeline, após render)
- **Sintoma**: `book_state.visual_audit` retorna `{score: None, verdict: None, issues: []}` mesmo depois do pipeline completar com sucesso
- **Expectativa**: Glen Keane deveria rodar automaticamente após render, popular `visual_audit` e travar PDF se score < threshold
- **Nota**: Existe endpoint `POST /api/studio/book/projects/{id}/visual-continuity-audit` criado na sessão de Continuity Audits — só falta **integrar ao pipeline automático** ou expor um botão "Re-auditar" visível no BookStudio após PDF pronto
- **Impacto**: Quality Gate está funcional mas usa score de outro auditor. Glen Keane está disponível mas desconectado.

### 3. Thumbnails não são populados
- **Arquivo**: `/app/backend/routers/studio/book_factory.py` (step que gera `illustration_plan[i].image_url`)
- **Sintoma**: `book_state.thumbnails = []` mesmo com 33 spreads gerados com imagens
- **Impacto visual**: listagem de projetos mostra "0 spreads" / "0 personagens" ao lado do livro pronto, o que desorienta o usuário
- **Solução**: na fase final do pipeline, popular `thumbnails = [sp.image_url for sp in illustration_plan if sp.image_url]`

---

## 🟡 P1 — UX / Qualidade de Feature

### 4. Quality Gate (≥90) muito rigoroso + não configurável
- **Arquivo**: `/app/backend/routers/studio/book_editable.py` linha ~25 (`@router.get(".../quality-gate")`)
- **Sintoma**: Manual do Pulmeranea score 85 ficou bloqueado. Livro é visualmente bom, só perdeu 5 pontos.
- **Solução sugerida**:
  - Tornar `min_required` configurável por projeto (`brief.quality_gate_threshold: 80 | 90 | 95`)
  - Adicionar botão "**Forçar aprovação**" (admin override) no BookStudio quando score está no intervalo 70-89
  - Mostrar visualmente QUAIS spreads falharam com thumbnails + razão, não apenas score global

### 5. Pipeline de livro não usa o `ActiveAgentIndicator` live
- **Arquivo**: `/app/frontend/src/pages/BookStudio.jsx` (já tem `<ActiveAgentIndicator>` wired mas pipeline não chama `set_active_agent`)
- **Sintoma**: durante ~6 min de geração do livro, o usuário só vê o "pipeline_running=true" mas **não sabe qual agente/master está ativo**
- **Agentes que deveriam aparecer em sequência**:
  1. `outline_writer_agent` — "Criando estrutura narrativa…"
  2. `chapter_writer_agent` — "Escrevendo capítulo X de Y…"
  3. `picturebook_designer_agent` (Mary Blair) — "Planejando ilustrações…" (JÁ INSTRUMENTADO ✅)
  4. `illustration_generator` — "Ilustração p.X de Y sendo gerada…"
  5. `cover_designer_agent` — "Gerando capa…"
  6. `layout_diagramador_agent` — "Diagramando PDF final…"
  7. `visual_continuity_checker_book_agent` (Glen Keane) — "Auditando continuidade visual…" (já existe endpoint, falta hook no fim do pipeline)
- **Solução**: adicionar `set_active_agent(...)` + `clear_active_agent()` em cada step do `book_factory.py`
- **Impacto**: UX MUITO melhor — usuário vê "Mary Blair está planejando sua aquarela…" em tempo real

### 6. Retry por spread (regerar UMA ilustração sem refazer livro todo)
- **Arquivo**: precisa de novo endpoint `POST /api/studio/book/projects/{id}/regenerate-spread/{spread_id}`
- **Sintoma atual**: se `p.5` ficou feia, usuário é obrigado a rodar o pipeline completo de novo (6 min + custo LLM total)
- **Solução**: já existe `book_editable.py` com `regenerate-image` endpoint — expor no UI do `BookEditorPage` com botão "🔄 Regerar" por spread
- **Custo**: ~10s por spread em vez de 6 min

### 7. Editor Visual de Livros (`BookEditorPage.jsx`) nunca foi testado com livro real
- **Arquivo**: `/app/frontend/src/pages/BookEditorPage.jsx`
- **Status**: criado mas nunca validado com livro que tenha `illustration_plan` populado
- **Testes que faltam**:
  - Editar texto de um spread → salvar → reregerar PDF → validar mudança aparece
  - Trocar imagem de um spread (drag-drop / upload)
  - Aumentar/diminuir imagem no layout
  - Aplicar over-ride e forçar PDF mesmo com quality 85

---

## 🟢 P2 — Polimento / Melhorias

### 8. Ausência de "progress bar real" durante geração
- **Expectativa**: usuário vê "Gerando ilustração 7 de 16 (43%)"
- **Hoje**: pipeline_running boolean + log de eventos que o UI não consome
- **Solução**: adicionar `progress: {current: 7, total: 16, phase: 'illustrations'}` em `book_state` e exibir em `BookStudio.jsx`

### 9. Briefing não é validado antes de rodar pipeline
- **Sintoma**: 6 dos 7 livros estão em draft com briefing mas nunca geraram PDF
- **Possíveis causas**: briefing vazio / fora das regras / usuário não clicou "Gerar"
- **Solução**: validar briefing na UI antes de habilitar botão "Gerar Livro" + adicionar wizard de onboarding (ex: "3/5: Escolher formato")

### 10. Preflight warnings mistura crítico vs. cosmético
- **Exemplo real**: `"CMYK conversion pending"` aparece como warning amarelo — mas isso é BLOQUEADOR para impressão.
- **Solução**: categorizar `preflight_report.warnings` em `critical | warning | info` e destacar criticals em vermelho

### 11. Livros em draft aparecem junto com livros prontos na listagem
- **Expectativa**: separar "Livros em produção" de "Livros prontos (PDF)" visualmente
- **Solução**: adicionar badge de estado + filtro no StudioPage (já tem filtros para video/book/híbrido, falta filtro por fase)

### 12. Falta integração KDP / Lulu (print-on-demand direto)
- **Feature no backlog do PRD original**
- **Escopo**: upload automático do PDF CMYK para KDP (Amazon) e Lulu via API deles
- **Pré-requisito**: #1 (CMYK automático) + #4 (Quality Gate configurável)

---

## 🔵 P3 — Arquitetural (ao retomar a trilha de livros, reavaliar)

### 13. `book_factory.py` é monolítico (~2933 linhas)
- Mesmo problema que tivemos com `DirectedStudio.jsx`. Quebrar em:
  - `book/outline_generator.py` (outline + chapters)
  - `book/illustration_pipeline.py` (geração de spreads)
  - `book/cover_generator.py` (capa + spine)
  - `book/pdf_renderer.py` (layout + render WeasyPrint)
  - `book/preflight.py` (validação)

### 14. Pipeline síncrono (bloqueia worker)
- Hoje cada geração de ilustração é chamada em sequência com `await`. Para livro de 30 spreads demora 6min.
- **Solução**: paralelizar com `asyncio.gather()` em lotes de 4 (cuidar do rate limit da API de imagem). Tempo esperado: 6min → 2min.

### 15. Cache de "livro similar"
- Se o usuário gera 2 livros com briefings parecidos, o pipeline gera tudo do zero.
- **Ideia**: embedding do briefing + match semântico para reusar outline/illustration_plan como base (opt-in).

---

## 📂 Onde está o código hoje

| Componente | Arquivo | Linhas | Status |
|---|---|---:|---|
| Backend pipeline | `/app/backend/routers/studio/book_factory.py` | 2933 | ✅ Produção (monolítico) |
| Backend editor | `/app/backend/routers/studio/book_editable.py` | ~290 | ✅ Produção |
| Backend Continuity | `/app/backend/routers/studio/continuity_audit.py` | ~250 | ✅ Produção, não integrado ao book_factory |
| Frontend Book UI | `/app/frontend/src/pages/BookStudio.jsx` | 1545 | ✅ Produção |
| Frontend Editor | `/app/frontend/src/pages/BookEditorPage.jsx` | ? | ⚠️ Criado, nunca testado com livro real |
| Agent picturebook | `/app/memory/agents/book/picturebook_designer_agent.json` | - | ✅ Mary Blair seeded |
| Agent continuity book | `/app/memory/agents/book/visual_continuity_checker_book_agent.json` | - | ✅ Glen Keane seeded |

---

## 🎯 Quando retomar, ordem sugerida de ataque

1. **P0 #2** (integrar Glen Keane automaticamente) — 1h
2. **P0 #3** (popular thumbnails) — 30min
3. **P0 #1** (CMYK automático via ghostscript) — 2h + test print
4. **P1 #5** (live feedback com ActiveAgentIndicator) — 2h, super high-impact visual
5. **P1 #6** (retry por spread) — 2h
6. **P1 #7** (validar BookEditorPage end-to-end) — 1h
7. **P1 #4** (Quality Gate configurável + override) — 2h
8. Avaliar #8, #9, #10, #11
9. Integração KDP/Lulu #12 (épico dedicado)
10. Refactor arquitetural #13, #14, #15

**Esforço total estimado**: ~15-20h para deixar a trilha de livros "pronta para profissionalização".

---

## 📝 Notas de contexto

- Usuário decidiu focar 100% em **vídeos perfeitos** por enquanto
- Trilha de livros fica **em manutenção** (não vamos quebrar o que funciona, mas também não vamos evoluir)
- Todas as features core de livros continuam em produção: BookFactory, Quality Gate, BookEditorPage, BookStudio, agents Mary Blair + Glen Keane
- Ao retomar, começar por ler este arquivo + o último pipeline_log de um livro gerado (Manual do Pulmeranea é o caso de teste mais rico hoje)
