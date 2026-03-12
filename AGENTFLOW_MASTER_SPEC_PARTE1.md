# 🎨 AGENTFLOW - ESPECIFICAÇÃO COMPLETA DE PRODUTO
## Design, UX, Arquitetura e Implementação | Versão Final Completa

---

## 📋 ÍNDICE

1. [Visão Geral do Produto](#visão-geral)
2. [Design System Minimalista](#design-system)
3. [Wireframes e Layouts Completos](#wireframes)
4. [Fluxos de UX Detalhados](#fluxos-ux)
5. [Arquitetura Técnica](#arquitetura)
6. [Cronograma Completo](#cronograma)
7. [Guia de Implementação](#implementação)

---

## 🎯 VISÃO GERAL DO PRODUTO

### **O que é AgentFlow:**
Plataforma omnichannel de IA multimodal com CRM integrado para automação de atendimento em múltiplas redes sociais.

### **Features Completas (Produto Final):**

✅ **1. Multi-idiomas**
- Detecção automática (95% accuracy)
- 176 idiomas suportados
- Switcher manual com bandeiras

✅ **2. Omnichannel**
- WhatsApp, Instagram, Facebook, Telegram
- Unified Inbox (todas conversas em um lugar)
- Message Router normalizado

✅ **3. IA Multimodal**
- Texto: Claude 3.5 Sonnet
- Voz: OpenAI Whisper (transcrição)
- Imagens: Claude Vision (OCR + reconhecimento)

✅ **4. Multi-agente Inteligente**
- 20+ agentes prontos (marketplace)
- Orquestração automática (SAC → Vendas → Suporte)
- Contexto preservado entre transições

✅ **5. Handoff Humano**
- IA detecta quando escalar
- Notificação em tempo real
- Bot pausa enquanto humano digita

✅ **6. CRM Kanban com IA**
- Conversas → Leads automaticamente
- IA move leads pelo pipeline
- Score 0-100 em tempo real
- Drag-and-drop manual

✅ **7. Sincronização Tempo Real**
- Google Calendar (agendamentos)
- Google Sheets (produtos/estoque)
- APIs personalizadas

✅ **8. Nutrição de Leads**
- Campanhas automáticas
- Carrinho abandonado
- Follow-up inteligente
- Reengajamento

✅ **9. Edição em Tempo Real**
- Hot reload de configurações
- Auto-save a cada 2s
- Preview instantâneo

✅ **10. Dashboard Mobile-First**
- PWA instalável
- Bottom navigation
- Analytics em tempo real

---

## 🎨 DESIGN SYSTEM MINIMALISTA

### **Filosofia de Design:**
**"Hyper-minimalism com propósito"**
- Linhas finas (1px borders)
- Ícones outline (2px stroke)
- Espaçamento generoso (16-24px)
- Hierarquia clara
- Animações suaves (200-300ms)
- Zero ruído visual

---

### **PALETA DE CORES (Clean & Professional)**

```css
/* === BACKGROUND === */
--bg-primary:    #FAFAFA    /* Fundo principal (off-white) */
--bg-elevated:   #FFFFFF    /* Cards e modais */
--bg-subtle:     #F5F5F5    /* Hover states */
--bg-muted:      #E8E8E8    /* Disabled */

/* === BORDERS === */
--border-light:  #E5E5E5    /* Linhas finas principais */
--border-medium: #D4D4D4    /* Dividers */
--border-dark:   #A3A3A3    /* Focus states */

/* === TEXT === */
--text-primary:   #171717   /* Headings */
--text-secondary: #525252   /* Body text */
--text-tertiary:  #737373   /* Captions */
--text-disabled:  #A3A3A3   /* Disabled */

/* === BRAND (Indigo Minimalista) === */
--brand-50:  #EEF2FF
--brand-100: #E0E7FF
--brand-500: #6366F1    /* Primary actions */
--brand-600: #4F46E5    /* Hover */
--brand-700: #4338CA    /* Active */

/* === SUCCESS (Verde Suave) === */
--success-50:  #F0FDF4
--success-500: #22C55E
--success-600: #16A34A

/* === WARNING (Amarelo Suave) === */
--warning-50:  #FFFBEB
--warning-500: #F59E0B
--warning-600: #D97706

/* === ERROR (Vermelho Suave) === */
--error-50:  #FEF2F2
--error-500: #EF4444
--error-600: #DC2626

/* === NEUTRAL (Cinza Escala) === */
--neutral-50:  #FAFAFA
--neutral-100: #F5F5F5
--neutral-200: #E5E5E5
--neutral-300: #D4D4D4
--neutral-400: #A3A3A3
--neutral-500: #737373
--neutral-600: #525252
--neutral-700: #404040
--neutral-800: #262626
--neutral-900: #171717
```

---

### **TIPOGRAFIA (Inter — Clean & Modern)**

```css
/* === FONT FAMILY === */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* === TYPE SCALE === */
--text-xs:   11px / 16px / 400    /* Captions */
--text-sm:   13px / 18px / 400    /* Small text */
--text-base: 14px / 20px / 400    /* Body */
--text-lg:   16px / 24px / 400    /* Large body */
--text-xl:   18px / 28px / 500    /* Subheadings */
--text-2xl:  22px / 32px / 600    /* Headings */
--text-3xl:  28px / 36px / 700    /* Page titles */

/* === LETTER SPACING === */
--tracking-tight:  -0.02em  /* Headings */
--tracking-normal:  0       /* Body */
--tracking-wide:    0.01em  /* Captions */

/* === FONT WEIGHTS === */
--font-light:   300
--font-normal:  400
--font-medium:  500
--font-semibold: 600
--font-bold:    700
```

---

### **ÍCONES (Lucide React — 2px Stroke)**

```jsx
// Biblioteca: Lucide React
// Tamanho padrão: 20px
// Stroke: 2px
// Cor: inherit (do texto)

import {
  MessageSquare,  // Chat
  Users,          // Agentes
  BarChart3,      // Analytics
  Settings,       // Configurações
  Plus,           // Adicionar
  ChevronRight,   // Navegação
  Check,          // Sucesso
  X,              // Fechar
  AlertCircle,    // Aviso
  Zap,            // IA/Auto
  Bot,            // Bot
  UserCheck,      // Humano
  Globe,          // Idiomas
  Calendar,       // Agenda
  Package,        // Produtos
  TrendingUp,     // Score
  ArrowRight,     // Próximo
  Filter,         // Filtros
  Search,         // Busca
  MoreHorizontal  // Menu
} from 'lucide-react';

// Exemplo de uso:
<MessageSquare size={20} strokeWidth={2} />
```

---

### **COMPONENTES BASE**

#### **1. Button (Linha Fina)**

```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  border-radius: 8px;
  border: 1px solid transparent;
  transition: all 200ms ease;
  cursor: pointer;
}

/* Primary */
.btn-primary {
  background: var(--brand-500);
  color: white;
  border-color: var(--brand-500);
}
.btn-primary:hover {
  background: var(--brand-600);
  border-color: var(--brand-600);
}

/* Secondary (Outline) */
.btn-secondary {
  background: transparent;
  color: var(--text-primary);
  border-color: var(--border-light);
}
.btn-secondary:hover {
  background: var(--bg-subtle);
  border-color: var(--border-medium);
}

/* Ghost */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: none;
}
.btn-ghost:hover {
  background: var(--bg-subtle);
  color: var(--text-primary);
}
```

#### **2. Input (Linha Fina)**

```css
.input {
  width: 100%;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 20px;
  color: var(--text-primary);
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  transition: all 200ms ease;
}

.input:hover {
  border-color: var(--border-medium);
}

.input:focus {
  outline: none;
  border-color: var(--brand-500);
  box-shadow: 0 0 0 3px var(--brand-50);
}

.input::placeholder {
  color: var(--text-tertiary);
}
```

#### **3. Card (Elevado e Clean)**

```css
.card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 20px;
  transition: all 200ms ease;
}

.card:hover {
  border-color: var(--border-medium);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
}

.card-header {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}
```

#### **4. Badge (Pill Clean)**

```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 12px;
  border: 1px solid transparent;
}

.badge-success {
  background: var(--success-50);
  color: var(--success-600);
  border-color: var(--success-500);
}

.badge-warning {
  background: var(--warning-50);
  color: var(--warning-600);
  border-color: var(--warning-500);
}

.badge-error {
  background: var(--error-50);
  color: var(--error-600);
  border-color: var(--error-500);
}
```

#### **5. Status Dot (Animado)**

```css
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1.5px solid var(--bg-elevated);
}

.status-dot-active {
  background: var(--success-500);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-dot-inactive {
  background: var(--neutral-400);
}

.status-dot-error {
  background: var(--error-500);
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}
```

---

### **SPACING SYSTEM (8px Grid)**

```css
:root {
  --space-0: 0px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  --space-20: 80px;
}
```

---

### **SHADOW SYSTEM (Suave)**

```css
:root {
  --shadow-xs:  0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-sm:  0 2px 4px rgba(0, 0, 0, 0.04);
  --shadow-md:  0 4px 8px rgba(0, 0, 0, 0.04), 
                0 2px 4px rgba(0, 0, 0, 0.02);
  --shadow-lg:  0 8px 16px rgba(0, 0, 0, 0.06), 
                0 4px 8px rgba(0, 0, 0, 0.04);
  --shadow-xl:  0 16px 32px rgba(0, 0, 0, 0.08), 
                0 8px 16px rgba(0, 0, 0, 0.06);
}
```

---

### **BORDER RADIUS (Suave)**

```css
:root {
  --radius-sm:  6px;   /* Small elements */
  --radius-md:  8px;   /* Buttons, inputs */
  --radius-lg:  12px;  /* Cards */
  --radius-xl:  16px;  /* Modals */
  --radius-full: 9999px; /* Pills */
}
```

---

### **ANIMATIONS (Suaves e Rápidas)**

```css
:root {
  --duration-fast: 150ms;
  --duration-base: 200ms;
  --duration-slow: 300ms;
  
  --easing-default: cubic-bezier(0.4, 0, 0.2, 1);
  --easing-in:      cubic-bezier(0.4, 0, 1, 1);
  --easing-out:     cubic-bezier(0, 0, 0.2, 1);
}

/* Hover transitions */
.hover-lift {
  transition: transform var(--duration-base) var(--easing-default);
}
.hover-lift:hover {
  transform: translateY(-2px);
}

/* Fade in */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in {
  animation: fadeIn var(--duration-base) var(--easing-out);
}
```

---

## 📱 WIREFRAMES E LAYOUTS COMPLETOS

### **ARQUITETURA DE NAVEGAÇÃO**

```
┌─────────────────────────────────────────────────────────┐
│                   AGENTFLOW                             │
│                                                         │
│  Landing Page                                           │
│      ↓                                                  │
│  Login / Cadastro (Supabase Auth)                      │
│      ↓                                                  │
│  Onboarding (4 steps)                                   │
│      ↓                                                  │
│  ┌───────────────────────────────────────────────────┐ │
│  │           DASHBOARD PRINCIPAL                     │ │
│  │                                                   │ │
│  │  Bottom Navigation:                               │ │
│  │                                                   │ │
│  │  ├─ 💬 CHAT                                       │ │
│  │  │   ├─ Inbox (Lista de conversas)               │ │
│  │  │   └─ Conversa Individual                      │ │
│  │  │       └─ Detalhe do Cliente                   │ │
│  │  │                                               │ │
│  │  ├─ 🤖 AGENTES                                    │ │
│  │  │   ├─ Meus Agentes (Lista)                     │ │
│  │  │   ├─ Marketplace (20+ templates)              │ │
│  │  │   ├─ Criar/Editar Agente (Wizard)             │ │
│  │  │   └─ Analytics por Agente                     │ │
│  │  │                                               │ │
│  │  ├─ 🎯 CRM                                        │ │
│  │  │   ├─ Kanban Board                             │ │
│  │  │   ├─ Detalhe do Lead                          │ │
│  │  │   ├─ Configurar Pipeline                      │ │
│  │  │   └─ Campanhas de Nutrição                    │ │
│  │  │                                               │ │
│  │  ├─ 📊 ANALYTICS                                  │ │
│  │  │   ├─ Overview (Cards + Gráficos)              │ │
│  │  │   ├─ Por Canal                                │ │
│  │  │   ├─ Por Agente                               │ │
│  │  │   └─ Custo (Tokens + $)                       │ │
│  │  │                                               │ │
│  │  └─ ⚙️ CONFIGURAÇÕES                              │ │
│  │      ├─ Conta                                    │ │
│  │      ├─ Empresa                                  │ │
│  │      ├─ Canais (WhatsApp, Instagram, etc)       │ │
│  │      ├─ Integrações (Calendar, Sheets, APIs)    │ │
│  │      ├─ Plano e Pagamento                        │ │
│  │      └─ Notificações                             │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

### **WIREFRAME 1: ONBOARDING (Step 1 de 4)**

```
╔═══════════════════════════════════════════════════════════════╗
║                         AGENTFLOW                              ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │                     [LOGO AGENTFLOW]                     │ ║
║  │                                                          │ ║
║  │                  Vamos começar! 🚀                        │ ║
║  │                                                          │ ║
║  │         Configure sua conta em menos de 5 minutos        │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  STEP 1 DE 4: Dados da Empresa                          │ ║
║  │  ━━━━━━━━━━━━━━                                          │ ║
║  │  ▓▓▓▓▓▓▓░░░░░░░   25%                                   │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │  Nome da sua empresa                                     │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │ Boutique da Maria                                  │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │                                                          │ ║
║  │  Qual o seu setor?                                       │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │ Selecione...                                  ▾    │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │                                                          │ ║
║  │    • Varejo & eCommerce                                  │ ║
║  │    • Saúde & Bem-estar                                   │ ║
║  │    • Educação                                            │ ║
║  │    • Serviços Profissionais                              │ ║
║  │    • Restaurante & Delivery                              │ ║
║  │    • Outros                                              │ ║
║  │                                                          │ ║
║  │  Tamanho da equipe                                       │ ║
║  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐           │ ║
║  │  │ Só eu  │ │ 2-10   │ │ 11-50  │ │ 50+    │           │ ║
║  │  └────────┘ └────────┘ └────────┘ └────────┘           │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │  [Voltar]                             [Próximo →]       │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════╝
```

---

### **WIREFRAME 2: ONBOARDING (Step 2 de 4) - Conectar WhatsApp**

```
╔═══════════════════════════════════════════════════════════════╗
║                         AGENTFLOW                              ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  STEP 2 DE 4: Conectar WhatsApp                         │ ║
║  │  ━━━━━━━━━━━━━━                                          │ ║
║  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░   50%                                  │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │                📱 Conecte seu WhatsApp                    │ ║
║  │                                                          │ ║
║  │       Escaneie o QR Code com seu celular para conectar   │ ║
║  │                                                          │ ║
║  │  ┌───────────────────────────────────────────────────┐  │ ║
║  │  │                                                   │  │ ║
║  │  │                                                   │  │ ║
║  │  │         ████████████████████████████              │  │ ║
║  │  │         ██                        ██              │  │ ║
║  │  │         ██  ████  ██████  ████  ██              │  │ ║
║  │  │         ██  ████  ██████  ████  ██              │  │ ║
║  │  │         ██  ████  ██████  ████  ██              │  │ ║
║  │  │         ██                        ██              │  │ ║
║  │  │         ████████████████████████████              │  │ ║
║  │  │                                                   │  │ ║
║  │  │                                                   │  │ ║
║  │  └───────────────────────────────────────────────────┘  │ ║
║  │                                                          │ ║
║  │                    ⏳ Aguardando conexão...              │ ║
║  │                                                          │ ║
║  │  ┌───────────────────────────────────────────────────┐  │ ║
║  │  │  📍 COMO CONECTAR:                                │  │ ║
║  │  │                                                   │  │ ║
║  │  │  1. Abra o WhatsApp no seu celular                │  │ ║
║  │  │  2. Toque em ⋮ (Menu) > Aparelhos conectados     │  │ ║
║  │  │  3. Toque em "Conectar um aparelho"               │  │ ║
║  │  │  4. Aponte a câmera para este QR Code             │  │ ║
║  │  │                                                   │  │ ║
║  │  └───────────────────────────────────────────────────┘  │ ║
║  │                                                          │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  [← Voltar]                      [Pular por agora]       │ ║
║  └──────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════╝
```

**Após conexão bem-sucedida:**

```
╔═══════════════════════════════════════════════════════════════╗
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │                  ✅ WhatsApp conectado!                   │ ║
║  │                                                          │ ║
║  │               📞 +55 11 98765-4321                        │ ║
║  │                                                          │ ║
║  │          Seu WhatsApp está pronto para usar!             │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │                      [Próximo →]                          │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════╝
```

---

### **WIREFRAME 3: ONBOARDING (Step 3 de 4) - Escolher Primeiro Agente**

```
╔═══════════════════════════════════════════════════════════════╗
║                         AGENTFLOW                              ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  STEP 3 DE 4: Escolha seu primeiro agente               │ ║
║  │  ━━━━━━━━━━━━━━                                          │ ║
║  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░   75%                               │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │            🤖 Agentes prontos para você                   │ ║
║  │                                                          │ ║
║  │      Escolha um agente baseado no que você precisa       │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  🎯 RECOMENDADOS PARA VAREJO                             │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌────────────────────────┐  ┌────────────────────────┐      ║
║  │ 🛍️ Vendas eCommerce    │  │ 💬 SAC Triagem         │      ║
║  │ ────────────────────── │  │ ────────────────────── │      ║
║  │                        │  │                        │      ║
║  │ Mostra produtos,       │  │ Acolhe clientes e      │      ║
║  │ calcula frete e envia  │  │ direciona para área    │      ║
║  │ pagamento              │  │ certa                  │      ║
║  │                        │  │                        │      ║
║  │ ⭐ 4.8 (1.2k reviews)   │  │ ⭐ 4.9 (3.4k reviews)   │      ║
║  │                        │  │                        │      ║
║  │ [Escolher este]        │  │ [Escolher este]        │      ║
║  └────────────────────────┘  └────────────────────────┘      ║
║                                                                ║
║  ┌────────────────────────┐  ┌────────────────────────┐      ║
║  │ 📅 Agendamento         │  │ 🎯 Qualificação Leads  │      ║
║  │ ────────────────────── │  │ ────────────────────── │      ║
║  │                        │  │                        │      ║
║  │ Agenda horários        │  │ Filtra leads antes de  │      ║
║  │ automaticamente com    │  │ passar para vendedor   │      ║
║  │ sua agenda             │  │                        │      ║
║  │                        │  │                        │      ║
║  │ ⭐ 4.7 (890 reviews)    │  │ ⭐ 4.6 (650 reviews)    │      ║
║  │                        │  │                        │      ║
║  │ [Escolher este]        │  │ [Escolher este]        │      ║
║  └────────────────────────┘  └────────────────────────┘      ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │            [Ver todos os 20+ agentes →]                  │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  [← Voltar]                [Criar do zero (avançado)]    │ ║
║  └──────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════╝
```

---

### **WIREFRAME 4: ONBOARDING (Step 4 de 4) - Personalizar Agente**

```
╔═══════════════════════════════════════════════════════════════╗
║                         AGENTFLOW                              ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │  STEP 4 DE 4: Personalize seu agente                    │ ║
║  │  ━━━━━━━━━━━━━━                                          │ ║
║  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  100%                            │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │              ✏️ Vendas eCommerce                          │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │  📝 Nome do agente                                        │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │ Carol                                              │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │  Como seus clientes vão chamar o agente                  │ ║
║  │                                                          │ ║
║  │  💬 Tom de voz                                            │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │  Formal  ───────●──────  Casual                    │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │                                                          │ ║
║  │  📦 Catálogo de produtos                                  │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │  ( ) Upload CSV/Excel                              │ │ ║
║  │  │  (•) Google Sheets                                 │ │ ║
║  │  │  ( ) Digitar manualmente                           │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │                                                          │ ║
║  │  💳 Formas de pagamento                                   │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │  [✓] PIX    [✓] Cartão    [ ] Boleto              │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │                                                          │ ║
║  │  📦 Frete                                                 │ ║
║  │  ┌────────────────────────────────────────────────────┐ │ ║
║  │  │  (•) Fixo: R$ [15,00]                              │ │ ║
║  │  │  ( ) Grátis acima de R$ [____]                     │ │ ║
║  │  │  ( ) API Correios/Melhor Envio                     │ │ ║
║  │  └────────────────────────────────────────────────────┘ │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
║                                                                ║
║  ┌──────────────────────────────────────────────────────────┐ ║
║  │                                                          │ ║
║  │  [← Voltar]     [Testar antes de ativar]  [Ativar! →]   │ ║
║  │                                                          │ ║
║  └──────────────────────────────────────────────────────────┘ ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 💬 CONTINUA NO PRÓXIMO DOCUMENTO...

Esse documento está ficando muito grande. Vou criar **PARTE 2** com:
- Wireframes completos de todas as telas principais
- Fluxos de UX detalhados
- Arquitetura técnica
- Cronograma final
- Guia de implementação passo a passo

**Quer que eu continue?** 🚀
