# ESTRATÉGIA DE PRODUÇÃO — AgentZZ
## Preparação para App Mobile + Alto Volume de Usuários
### Data: 27/03/2026

---

## DIAGNÓSTICO ATUAL — Por que o app não está pronto para produção

| Métrica | Atual | Meta Produção | Status |
|---------|-------|---------------|--------|
| Bundle frontend | ~15 MB | < 500 KB (gzip) | CRITICO |
| Assets estáticos (public/) | 91 MB (78MB só avatares) | 0 MB (CDN) | CRITICO |
| Tempo de 1st load (estimado) | 8-12s (3G) | < 3s | CRITICO |
| Compressão (gzip/brotli) | Nenhuma | Brotli | CRITICO |
| PWA / Service Worker | Não existe | Obrigatório para app | CRITICO |
| Code splitting | 0 | 100% das rotas | CRITICO |
| Lazy loading imagens | 0 | 100% | ALTO |
| Polling HTTP (requests repetidos) | 44 padrões | 0 (WebSocket/SSE) | ALTO |
| Debounce/throttle | 0 | Em todo input/scroll | ALTO |
| Cache headers HTTP | 0 | Em todos assets | ALTO |
| DB calls por page load (Dashboard) | 8 queries séries | 1-2 (agregado) | ALTO |
| Rate limiting | Nenhum | Todos endpoints AI | ALTO |
| Background job queue | Nenhum (threads inline) | Redis/Celery | ALTO |
| WebSocket/SSE | Nenhum | Para status em tempo real | MEDIO |
| CDN para mídia | Nenhum | CloudFront/Cloudflare | MEDIO |
| Docker/Container | Nenhum | Multi-stage build | MEDIO |
| API versioning | Nenhum | /api/v1/ | MEDIO |

---

## ESTRATÉGIA EM 4 PILARES

### PILAR 1: APP LEVE (Frontend Production-Ready)

**Problema atual:** O bundle tem ~15MB e carrega TUDO de uma vez. 78MB de avatares estão no diretório público sendo servidos pelo servidor web. Nenhuma imagem usa lazy loading. Zero code splitting. Para um app mobile isso é inviável — em 3G/4G, o usuário esperaria 8-12 segundos para a primeira tela.

**Ações:**

#### 1.1 Code Splitting por Rota (Impacto: -70% no bundle inicial)
Cada página é carregada APENAS quando o usuário navega até ela.
```javascript
// ANTES: Tudo carrega na primeira visita
import Marketing from './pages/Marketing';        // 2.422 linhas
import MarketingStudio from './pages/MarketingStudio';
import InteractiveBook from './pages/InteractiveBook';

// DEPOIS: Carrega sob demanda
const Marketing = React.lazy(() => import('./pages/Marketing'));
const MarketingStudio = React.lazy(() => import('./pages/MarketingStudio'));
const InteractiveBook = React.lazy(() => import('./pages/InteractiveBook'));
```
**Resultado:** Bundle inicial cai de ~15MB para ~2-3MB. Cada página extra carrega ~100-500KB quando acessada.

#### 1.2 Assets para CDN / Storage (Impacto: -91MB no servidor)
Os 78MB de avatares em `/public/avatars/` devem sair do bundle e ir para Supabase Storage ou CDN.
- Avatares já são salvos no Supabase Storage pela API
- Os que estão em `/public/` são cópias locais desnecessárias
- Remover esses arquivos reduz deploy de 91MB para ~13MB

#### 1.3 Lazy Loading Universal de Imagens (Impacto: -80% requests iniciais)
Adicionar `loading="lazy"` em TODA tag `<img>` dos componentes de mídia. O navegador só busca a imagem quando ela está próxima da viewport.

#### 1.4 Compressão GZip/Brotli (Impacto: -70% no tráfego)
Adicionar middleware de compressão no FastAPI. Um bundle de 2MB comprimido vira ~400KB.

#### 1.5 PWA (Progressive Web App) — Base para App Mobile
- Criar `manifest.json` (nome, ícones, tema, orientação)
- Criar `service-worker.js` (cache de assets estáticos)
- Registrar o SW no `index.js`
- **Resultado:** O app pode ser "instalado" no celular como um app nativo, funcionar offline para telas já visitadas, e ser publicado em stores via PWA wrapper (Capacitor/TWA)

#### 1.6 Storyboard com Expansão Sob Demanda
Painéis colapsados (thumbnail + título) expandem ao clicar. Reduz DOM nodes de ~500 para ~50 na página do storyboard.

#### 1.7 Virtualização de Listas Longas
Com 52+ projetos, usar `react-window` para renderizar apenas os visíveis na tela (~8-10 items), não todos os 52.

---

### PILAR 2: SERVIDOR RÁPIDO (Backend Production-Ready)

**Problema atual:** Funções síncronas bloqueiam o event loop. ThreadPools são criados e destruídos a cada request. Sem compressão. Sem cache headers. Dashboard faz 8 queries ao Supabase em série. Processos pesados (FFmpeg, AI) rodam inline.

**Ações:**

#### 2.1 Compressão de Respostas HTTP
```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)
```

#### 2.2 Cache Headers em Assets Estáticos
```python
# Imagens e vídeos do Supabase: cache 1 ano (imutáveis, URL muda)
# API responses dinâmicas: no-cache ou stale-while-revalidate
```

#### 2.3 Dashboard Query Otimizado
Consolidar as 8 queries do Dashboard em 1-2 queries com JOINs ou usar uma view materializada no Supabase.

#### 2.4 Global Thread Pool
Criar UM pool compartilhado no startup em vez de criar/destruir a cada chamada.

#### 2.5 Rate Limiting
Proteger endpoints de IA (Claude, Gemini, ElevenLabs, Sora) com limites por usuário:
- Geração de imagem: 20/hora
- Geração de vídeo: 5/hora
- Chat AI: 60/hora

#### 2.6 Background Job Queue (Futuro)
Processos pesados (FFmpeg, concatenação de vídeo, pós-produção) devem rodar em workers separados, não no processo principal da API. Opções: Celery + Redis, ou FastAPI BackgroundTasks para tarefas curtas.

---

### PILAR 3: SEGURANÇA (Obrigatório antes de publicar)

#### 3.1 Corrigir Auth em endpoints abertos
- `/cache/stats` e `/cache/flush` sem autenticação

#### 3.2 CORS restritivo
- Remover fallback `'*'`, listar domínios explícitos

#### 3.3 Content Security Policy
- Prevenir XSS com headers CSP

#### 3.4 Validação de uploads
- Limitar tamanho máximo (imagens: 10MB, áudio: 20MB, vídeo: 100MB)
- Validar MIME types

#### 3.5 Rate Limiting (mencionado acima)

---

### PILAR 4: ESTABILIDADE (Não quebrar em produção)

#### 4.1 Error Boundary Global
Capturar erros de componentes e mostrar tela amigável em vez de tela branca.

#### 4.2 AbortController em Requests
Cancelar chamadas API quando o componente desmonta. Previne memory leaks e erros de state update em componente desmontado.

#### 4.3 Fix de Build
O build de produção está falhando por import incorreto (`@/lib/i18n`). Precisa corrigir antes de qualquer deploy.

#### 4.4 Limpeza de Scripts Mortos
Remover 8 scripts não utilizados (45KB).

---

## PLANO DE EXECUÇÃO — Ordem Estratégica

A ordem importa. Cada fase constrói sobre a anterior.

### FASE 0: Fix Crítico (30 min)
**Pré-requisito para tudo — o build está quebrado**
- [ ] Corrigir import `@/lib/i18n` no build de produção
- **Teste:** `npm run build` deve completar sem erros

### FASE 1: Segurança Básica (1-2h)
**Sem isso, não pode ir para produção**
- [ ] Auth nos endpoints de cache
- [ ] CORS explícito (sem wildcard)
- [ ] Rate limiting nos endpoints de AI
- [ ] Validação de upload sizes
- **Teste:** Curl nos endpoints sem token deve retornar 401

### FASE 2: Performance Frontend — Quick Wins (2-3h)
**Maior impacto com menor esforço**
- [ ] `loading="lazy"` em todas as `<img>` (3 componentes)
- [ ] Code splitting com React.lazy (todas as rotas)
- [ ] Compressão GZip no backend
- [ ] Cache headers em assets estáticos
- **Teste:** Lighthouse score > 70. Bundle < 3MB

### FASE 3: UX Leve (3-4h)
**O que o usuário sente diretamente**
- [ ] Storyboard com painéis expandíveis (lazy expand)
- [ ] Error Boundary global
- [ ] AbortController em chamadas axios dos 3 componentes principais
- [ ] Debounce em inputs de busca/chat
- **Teste:** Storyboard com 20 cenas carrega em < 2s. Erros não crasham.

### FASE 4: PWA + App Ready (2-3h)
**Base para encapsulamento mobile**
- [ ] Criar manifest.json (nome, ícones, cores, orientation)
- [ ] Service Worker básico (cache de shell + assets)
- [ ] Registrar SW no index.js
- [ ] Splash screen e ícones do app
- **Teste:** Chrome DevTools > Application > Install disponível. Funciona offline (shell).

### FASE 5: Backend Optimization (2-3h)
**Servidor aguenta volume**
- [ ] Dashboard query consolidado (8 → 2 queries)
- [ ] Global ThreadPool compartilhado
- [ ] Remover avatares de /public/ (78MB)
- [ ] Limpar scripts mortos
- **Teste:** Dashboard carrega em < 1s. Memória do servidor estável.

---

## IMPACTO NO CENÁRIO DE APP MOBILE

| Cenário | Antes | Depois das 5 Fases |
|---------|-------|---------------------|
| Primeiro acesso (4G) | 8-12s | 2-3s |
| Navegação entre páginas | 1-2s (reload tudo) | 200-500ms (lazy) |
| Storyboard 20 cenas | Trava/lento | Fluido (expand on demand) |
| 100 usuários simultâneos | Servidor bloqueia | Responde normalmente |
| Instalar como app | Impossível | PWA instalável |
| Funcionar offline (shell) | Não | Sim (Service Worker) |
| Deploy size | ~106 MB | ~15 MB |
| Custo de banda/mês (1000 users) | Alto (sem cache/CDN) | -70% (cache + compress) |

---

## ENCAPSULAMENTO COMO APP MOBILE (Após Fases 0-5)

Com PWA implementado, temos 3 caminhos para stores:

### Opção A: TWA (Trusted Web Activity) — Android
- Wrapper nativo mínimo que abre a PWA em Chrome
- Publicável na Google Play Store
- Zero código nativo
- **Esforço:** 1 dia

### Opção B: Capacitor (iOS + Android)
- Wrapper WebView com acesso a APIs nativas (câmera, push notifications, filesystem)
- Publicável em Google Play E App Store
- **Esforço:** 2-3 dias

### Opção C: React Native (reescrita)
- App 100% nativo, melhor performance
- Requer reescrever todo o frontend
- **Esforço:** 2-3 meses
- **Recomendação:** NÃO fazer agora. PWA + Capacitor atendem 95% dos casos.

**Recomendação:** Capacitor (Opção B) — melhor custo-benefício para iOS + Android.

---

## RESUMO

O plano em 5 fases transforma o AgentZZ de um protótipo funcional em um produto production-ready:
- **App 70% mais leve** (code splitting + compressão + lazy loading)
- **3x mais rápido** no primeiro acesso
- **Instalável como app** no celular (PWA)
- **Seguro** contra abusos (rate limit, auth, CORS)
- **Estável** contra crashes (error boundaries, abort controllers)
- **Pronto para encapsular** em Capacitor para App Store e Google Play

Nenhuma funcionalidade existente será alterada ou removida. Todas as ações são ADITIVAS ou de OTIMIZAÇÃO.
