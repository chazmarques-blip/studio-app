# 🚀 AGENTFLOW - VISÃO COMPLETA DE PRODUTO
## Estudo Aprofundado: Marketplace de Agentes IA para WhatsApp

---

## 📊 EXECUTIVE SUMMARY

**AgentFlow** é um SaaS mobile-first que democratiza a automação inteligente no WhatsApp para pequenos e médios negócios. Diferente de ferramentas técnicas como n8n ou Botpress, o AgentFlow é um **marketplace de agentes IA prontos para usar**, onde qualquer pessoa — sem conhecimento técnico — pode:

1. **Escolher um agente pronto** (biblioteca com 20+ templates)
2. **Personalizar em 3 minutos** (wizard visual, sem código)
3. **Ativar e usar imediatamente** (conecta WhatsApp via QR code)
4. **Acompanhar resultados** (dashboard com métricas em tempo real)

**Diferencial:** Agentes IA realmente inteligentes (Claude 3.5 Sonnet) com orquestração multi-agente, handoff humano automático e aprendizado de contexto — não apenas respostas programadas.

---

## 🎯 POSICIONAMENTO DE MERCADO

### **Comparação com Concorrentes (2025)**

| Plataforma | Foco | Complexidade | IA Real | Preço Base | Público |
|------------|------|--------------|---------|------------|---------|
| **ManyChat** | Marketing/Broadcast | Médio | Limitada | $15/mês | eCommerce |
| **Typebot** | Conversational Forms | Baixo | Não | Grátis-$59 | Lead Gen |
| **Botpress** | Desenvolvimento Custom | Alto | Sim (GPT) | Grátis-$500 | Devs |
| **Tidio** | Chat + Chatbot Híbrido | Médio | Básica | $29/mês | SMBs |
| **AgentFlow** 🔥 | **Agentes IA Multi-Função** | **Baixo** | **Avançada (Claude)** | **$19/mês** | **Todos** |

### **Por que AgentFlow Vence:**

✅ **No-code real:** Configuração em 3 minutos vs 30+ minutos dos concorrentes  
✅ **IA contextual:** Lembra conversas anteriores, não só fluxos fixos  
✅ **Multi-agente nativo:** SAC → Vendas → Suporte sem reconfigurar  
✅ **Handoff inteligente:** IA sabe quando escalar para humano (concorrentes fazem manualmente)  
✅ **Mobile-first:** App instalável, não apenas webapp  
✅ **Preço justo:** $19/mês vs $50-100/mês da concorrência para features similares  

---

## 👥 PERSONAS E CASOS DE USO

### **Persona 1: MARIA - Dona de Loja de Roupas Online**
- **Perfil:** 35 anos, empreendedora, vende no Instagram + WhatsApp
- **Dor:** Gasta 4h/dia respondendo "Tem na cor X?" e "Qual o prazo?"
- **Objetivo:** Automatizar 70% das mensagens repetitivas
- **Agente Ideal:** **Vendas eCommerce**
  - Mostra catálogo de produtos
  - Responde sobre estoque/cores/tamanhos
  - Calcula frete automaticamente
  - Envia link de pagamento
  - Escala para Maria quando cliente quer negociar desconto

### **Persona 2: DR. CARLOS - Dentista**
- **Perfil:** 42 anos, clínica pequena, 1 secretária
- **Dor:** Pacientes ligam fora do horário, secretária sobrecarregada
- **Objetivo:** Agendamentos automáticos 24/7
- **Agente Ideal:** **Agendamento Clínico**
  - Consulta agenda em tempo real (integração Google Calendar)
  - Confirma disponibilidade
  - Envia lembretes 1 dia antes
  - Coleta dados do paciente (nome, CPF, convênio)
  - Escala para secretária se urgência/emergência

### **Persona 3: JOÃO - Advogado Autônomo**
- **Perfil:** 38 anos, escritório pequeno, atende consultas
- **Dor:** Perde tempo triando casos que não pode pegar
- **Objetivo:** Qualificar leads antes de gastar tempo
- **Agente Ideal:** **Qualificação de Leads Jurídicos**
  - Pergunta área do direito (trabalhista, família, etc)
  - Coleta detalhes do caso
  - Verifica se tem competência/disponibilidade
  - Agenda consulta paga ou descarta educadamente
  - Envia para João só leads qualificados

### **Persona 4: ANA - Gerente de Suporte SaaS**
- **Perfil:** 28 anos, startup tech, time de 3 pessoas
- **Dor:** 80% dos tickets são dúvidas básicas ("Como resetar senha?")
- **Objetivo:** Reduzir volume de atendimento humano
- **Agente Ideal:** **Suporte Técnico L1**
  - Base de conhecimento integrada (FAQ + docs)
  - Troubleshooting guiado (passo a passo)
  - Envia prints/vídeos explicativos
  - Só escala para humano após 3 tentativas falhadas

### **Persona 5: LUCAS - Dono de Restaurante**
- **Perfil:** 45 anos, 2 unidades, delivery próprio
- **Dor:** Atendentes erram pedidos no telefone
- **Objetivo:** Pedidos via WhatsApp sem erro
- **Agente Ideal:** **Atendimento Delivery**
  - Menu interativo com fotos
  - Monta carrinho (adiciona/remove itens)
  - Confirma endereço e forma de pagamento
  - Envia para cozinha + tracker de entrega
  - Coleta feedback pós-entrega

---

## 📚 BIBLIOTECA DE AGENTES PRONTOS (MARKETPLACE)

### **CATEGORIA: VENDAS & ECOMMERCE** 🛍️

#### 1. **Vendas eCommerce Geral**
- **Descrição:** Assistente de vendas completo para lojas online
- **Funções:**
  - Mostra catálogo de produtos (integra com Google Sheets/API)
  - Responde sobre estoque, cores, tamanhos
  - Calcula frete via API dos Correios
  - Envia link de pagamento (Mercado Pago, Stripe)
  - Handoff: Cliente quer negociar preço/desconto
- **Personalização:** Nome da loja, catálogo (upload CSV), formas de pagamento
- **Tom:** Amigável, consultivo, não insistente

#### 2. **Qualificação de Leads B2B**
- **Descrição:** Filtra leads qualificados antes de passar para vendedor
- **Funções:**
  - Coleta: nome da empresa, setor, número de funcionários, orçamento
  - Pergunta sobre dor/necessidade específica
  - Agenda demo/reunião se qualificado (Google Calendar)
  - Descarta educadamente se não fit
  - Handoff: Lead qualificado + quente (pronto para fechar)
- **Personalização:** Critérios de qualificação, perguntas obrigatórias
- **Tom:** Profissional, objetivo

#### 3. **Recuperação de Carrinho Abandonado**
- **Descrição:** Reengaja clientes que não finalizaram compra
- **Funções:**
  - Envia lembrete 1h + 24h após abandono
  - Oferece desconto especial (ex: 10% off)
  - Responde dúvidas sobre produto
  - Finaliza compra direto no chat
  - Handoff: Cliente quer trocar produto
- **Personalização:** Tempo de lembrete, % de desconto
- **Tom:** Persuasivo, empático

---

### **CATEGORIA: ATENDIMENTO & SUPORTE** 💬

#### 4. **SAC (Triagem Geral)**
- **Descrição:** Primeiro contato, acolhe e direciona
- **Funções:**
  - Saúda cliente (varia saudação conforme horário)
  - Coleta nome e motivo do contato
  - Detecta intenção: compra/dúvida/reclamação
  - Redireciona para agente especializado ou humano
  - Handoff: Reclamação grave/urgente
- **Personalização:** Nome da empresa, horário de atendimento
- **Tom:** Acolhedor, empático

#### 5. **Suporte Técnico L1**
- **Descrição:** Resolve problemas técnicos comuns
- **Funções:**
  - Base de conhecimento integrada (FAQ, docs, vídeos)
  - Troubleshooting passo a passo
  - Coleta logs/prints para diagnóstico
  - Cria ticket se não resolver em 3 tentativas
  - Handoff: Problema técnico complexo
- **Personalização:** Upload de base de conhecimento (PDF/links)
- **Tom:** Didático, paciente

#### 6. **FAQ Automático**
- **Descrição:** Responde dúvidas frequentes instantaneamente
- **Funções:**
  - Detecta intenção da pergunta (NLP)
  - Busca resposta na base de conhecimento
  - Sugere artigos relacionados
  - Coleta feedback ("Isso respondeu sua dúvida?")
  - Handoff: Pergunta não cadastrada
- **Personalização:** Upload de FAQs (CSV/Excel)
- **Tom:** Direto, claro

---

### **CATEGORIA: AGENDAMENTO** 📅

#### 7. **Agendamento Clínico (Médico/Dentista)**
- **Descrição:** Marca consultas automaticamente
- **Funções:**
  - Consulta agenda em tempo real (Google Calendar/API)
  - Mostra horários disponíveis
  - Coleta dados: nome, CPF, convênio, sintomas
  - Confirma agendamento via SMS/email
  - Envia lembretes 1 dia antes
  - Handoff: Emergência/urgência
- **Personalização:** Tipo de consulta, duração, regras (ex: só maiores de 18)
- **Tom:** Profissional, tranquilizador

#### 8. **Agendamento Beleza (Salão/Estética)**
- **Descrição:** Agenda serviços de beleza
- **Funções:**
  - Lista serviços disponíveis (corte, manicure, massagem)
  - Sugere profissional especializado
  - Mostra horários vagos
  - Coleta preferências (cor de esmalte, tipo de corte)
  - Envia confirmação + lembrete
  - Handoff: Cliente quer profissional específico indisponível
- **Personalização:** Cardápio de serviços, preços
- **Tom:** Casual, amigável

#### 9. **Agendamento Consultoria/Advogado**
- **Descrição:** Agenda reuniões profissionais
- **Funções:**
  - Coleta área de interesse (trabalhista, familiar, etc)
  - Verifica disponibilidade do profissional
  - Envia formulário pré-consulta (Google Forms)
  - Agenda via Zoom/presencial
  - Envia lembrete com link da reunião
  - Handoff: Caso urgente/complexo
- **Personalização:** Áreas de atuação, valor da consulta
- **Tom:** Formal, respeitoso

---

### **CATEGORIA: RESTAURANTE & DELIVERY** 🍕

#### 10. **Atendimento Delivery Restaurante**
- **Descrição:** Recebe pedidos de comida
- **Funções:**
  - Menu interativo com fotos (integra cardápio)
  - Monta pedido: adiciona/remove itens, adicionais
  - Calcula total + taxa de entrega
  - Confirma endereço via geolocalização
  - Envia pedido para cozinha (integra sistema)
  - Tracking de entrega ("Seu pedido saiu para entrega!")
  - Handoff: Problema com pedido (faltou item)
- **Personalização:** Upload de cardápio (PDF/imagens), raio de entrega
- **Tom:** Informal, rápido

#### 11. **Reserva de Mesas**
- **Descrição:** Agenda mesas em restaurante
- **Funções:**
  - Verifica disponibilidade por data/hora/pessoas
  - Coleta nome, telefone, preferências (mesa externa, etc)
  - Confirma reserva
  - Envia lembrete 2h antes
  - Handoff: Grupo grande (>10 pessoas)
- **Personalização:** Capacidade, horários de funcionamento
- **Tom:** Hospitaleiro, cordial

---

### **CATEGORIA: EDUCAÇÃO** 🎓

#### 12. **Matrícula/Inscrição Curso**
- **Descrição:** Vende e matricula alunos em cursos
- **Funções:**
  - Apresenta cursos disponíveis (próximas turmas)
  - Responde sobre grade, certificado, preço
  - Coleta dados do aluno (nome, email, CPF)
  - Envia contrato/boleto
  - Confirma matrícula
  - Handoff: Cliente quer parcelamento especial
- **Personalização:** Catálogo de cursos, formas de pagamento
- **Tom:** Educativo, motivador

#### 13. **Suporte ao Aluno (EAD)**
- **Descrição:** Ajuda alunos com plataforma/conteúdo
- **Funções:**
  - Dúvidas sobre acesso à plataforma
  - Envia links de aulas/materiais
  - Explica conteúdo de forma simplificada
  - Coleta feedback sobre curso
  - Handoff: Problema técnico grave (vídeo não carrega)
- **Personalização:** Estrutura do curso, materiais
- **Tom:** Didático, encorajador

---

### **CATEGORIA: IMOBILIÁRIO** 🏠

#### 14. **Qualificação Leads Imobiliária**
- **Descrição:** Filtra interessados em imóveis
- **Funções:**
  - Pergunta: comprar/alugar, tipo (apto/casa), bairro, orçamento
  - Envia fotos de imóveis que combinam
  - Agenda visita com corretor
  - Coleta dados para proposta
  - Handoff: Cliente quer negociar preço
- **Personalização:** Portfólio de imóveis (link API/Sheets)
- **Tom:** Consultivo, prestativo

---

### **CATEGORIA: SAÚDE & BEM-ESTAR** 💊

#### 15. **Lembretes de Medicação**
- **Descrição:** Envia lembretes para tomar remédio
- **Funções:**
  - Cadastra medicamentos e horários
  - Envia alertas nos horários (push + WhatsApp)
  - Confirma se tomou ("Tomei" / "Adiar 15min")
  - Alerta se esquecer 2x seguidas
  - Handoff: Reação adversa ao medicamento
- **Personalização:** Lista de medicamentos, horários
- **Tom:** Cuidadoso, não invasivo

#### 16. **Triagem de Sintomas**
- **Descrição:** Avalia sintomas e orienta
- **Funções:**
  - Pergunta sobre sintomas (febre, dor, etc)
  - Avalia gravidade (algoritmo de triagem)
  - Orienta: procurar emergência/marcar consulta/cuidados em casa
  - Envia dicas de cuidados (chá, repouso)
  - Handoff: Sintomas graves (dor no peito, falta de ar)
- **Personalização:** Protocolo de triagem da clínica
- **Tom:** Calmo, tranquilizador
- **⚠️ AVISO:** Não substitui médico, apenas orienta

---

### **CATEGORIA: RECURSOS HUMANOS** 👔

#### 17. **Onboarding de Funcionários**
- **Descrição:** Guia novo funcionário nos primeiros dias
- **Funções:**
  - Envia checklist de documentos (RG, conta, etc)
  - Explica benefícios (VR, VT, plano de saúde)
  - Agenda treinamentos obrigatórios
  - Responde dúvidas sobre políticas internas
  - Coleta feedback pós-onboarding
  - Handoff: Problema com pagamento/documentação
- **Personalização:** Documentos necessários, benefícios
- **Tom:** Acolhedor, institucional

#### 18. **Recrutamento (Triagem Currículos)**
- **Descrição:** Filtra candidatos para vagas
- **Funções:**
  - Apresenta vaga (requisitos, salário, local)
  - Coleta currículo (PDF) e dados
  - Faz perguntas eliminatórias (ex: disponibilidade para viajar?)
  - Agenda entrevista se aprovado
  - Descarta educadamente se não fit
  - Handoff: Candidato excepcional (fast-track)
- **Personalização:** Requisitos da vaga, perguntas eliminatórias
- **Tom:** Profissional, motivador

---

### **CATEGORIA: FINANÇAS** 💰

#### 19. **Cobrança Amigável**
- **Descrição:** Lembra clientes sobre pagamentos atrasados
- **Funções:**
  - Envia lembrete educado 3, 7, 15 dias após vencimento
  - Envia 2ª via de boleto/link de pagamento
  - Negocia parcelamento se cliente pedir
  - Confirma recebimento após pagamento
  - Handoff: Cliente alega dificuldade financeira
- **Personalização:** Datas de lembrete, tom (mais/menos formal)
- **Tom:** Firme mas empático

#### 20. **Consultoria Financeira Básica**
- **Descrição:** Orienta sobre produtos financeiros
- **Funções:**
  - Explica produtos (conta digital, investimentos, crédito)
  - Simula: empréstimo, rendimento, parcelas
  - Coleta dados para proposta
  - Agenda reunião com consultor
  - Handoff: Cliente quer produto complexo (previdência, etc)
- **Personalização:** Portfólio de produtos, taxas
- **Tom:** Educativo, confiável

---

## 🎨 FLUXO COMPLETO DA APLICAÇÃO (UX/UI)

### **JORNADA DO USUÁRIO - DO CADASTRO AO USO DIÁRIO**

---

### **FASE 1: DESCOBERTA E CADASTRO (2 min)**

#### Tela 1: **Landing Page**
```
╔════════════════════════════════════════╗
║  🤖 AGENTFLOW                         ║
║                                        ║
║  Agentes IA que atendem no WhatsApp   ║
║  Configure em 3 minutos, sem código   ║
║                                        ║
║  [Começar Grátis] [Ver Agentes]       ║
║                                        ║
║  ✅ 2.847 empresas atendendo agora    ║
╚════════════════════════════════════════╝
```

#### Tela 2: **Cadastro (Supabase Auth)**
```
╔════════════════════════════════════════╗
║  Criar conta                           ║
║                                        ║
║  📧 Email: ___________________         ║
║  🔒 Senha: ___________________         ║
║                                        ║
║  ou                                    ║
║                                        ║
║  [🔵 Continuar com Google]             ║
║                                        ║
║  [Criar Conta]                         ║
╚════════════════════════════════════════╝
```

---

### **FASE 2: ONBOARDING GUIADO (3 min)**

#### **Step 1/4: Dados da Empresa**
```
╔════════════════════════════════════════╗
║  📋 Sobre seu negócio                  ║
║                                        ║
║  Nome da empresa:                      ║
║  [_________________________]          ║
║                                        ║
║  Setor:                                ║
║  [ ] Varejo    [ ] Saúde              ║
║  [ ] Serviços  [ ] Outros             ║
║                                        ║
║  Tamanho da equipe:                    ║
║  ( ) Só eu  ( ) 2-10  ( ) 11-50       ║
║                                        ║
║  [Próximo →]                           ║
╚════════════════════════════════════════╝
```

#### **Step 2/4: Conectar WhatsApp**
```
╔════════════════════════════════════════╗
║  📱 Conecte seu WhatsApp                ║
║                                        ║
║  1. Abra o WhatsApp no celular         ║
║  2. Toque em ⋮ > Aparelhos conectados  ║
║  3. Escaneie o QR Code abaixo:         ║
║                                        ║
║       ▄▄▄▄▄▄▄  ▄▄  ▄▄▄▄▄▄▄            ║
║       █ ▄▄▄ █ ▀▄▀ █ ▄▄▄ █            ║
║       █ ███ █ ███ █ ███ █            ║
║       █▄▄▄▄▄█ ▄▀█ █▄▄▄▄▄█            ║
║       ▄▄▄▄  ▄ ▀▀▄▀▄  ▄▄▄             ║
║       ▄▄▄▄▄▄▄ █▀▄ ▄▄▄▄▄▄▄            ║
║                                        ║
║  ⏳ Aguardando conexão...              ║
║                                        ║
║  [Já conectei]                         ║
╚════════════════════════════════════════╝
```

Após conectar:
```
╔════════════════════════════════════════╗
║  ✅ WhatsApp conectado!                 ║
║                                        ║
║  📞 +55 11 98765-4321                  ║
║                                        ║
║  [Próximo →]                           ║
╚════════════════════════════════════════╝
```

#### **Step 3/4: Escolher Primeiro Agente**
```
╔════════════════════════════════════════╗
║  🤖 Escolha seu primeiro agente         ║
║                                        ║
║  🎯 RECOMENDADOS PARA VOCÊ             ║
║  (baseado em "Varejo")                 ║
║                                        ║
║  ┌──────────────────────────────────┐  ║
║  │ 🛍️ Vendas eCommerce              │  ║
║  │ Mostra produtos, calcula frete   │  ║
║  │ e envia pagamento                │  ║
║  │ ⭐ 4.8 (1.2k avaliações)          │  ║
║  │ [Escolher]                       │  ║
║  └──────────────────────────────────┘  ║
║                                        ║
║  ┌──────────────────────────────────┐  ║
║  │ 💬 SAC Triagem                   │  ║
║  │ Acolhe clientes e direciona     │  ║
║  │ ⭐ 4.9 (3.4k avaliações)          │  ║
║  │ [Escolher]                       │  ║
║  └──────────────────────────────────┘  ║
║                                        ║
║  [Ver todos os agentes (20+)]          ║
╚════════════════════════════════════════╝
```

#### **Step 4/4: Personalizar Agente (Wizard)**
```
╔════════════════════════════════════════╗
║  ✏️ Personalize: Vendas eCommerce       ║
║                                        ║
║  📝 Nome do agente:                     ║
║  [Carol] (como os clientes vão chamar) ║
║                                        ║
║  💬 Catálogo de produtos:               ║
║  [ ] Upload CSV/Excel                  ║
║  [ ] Conectar Google Sheets            ║
║  [ ] Digitar manualmente               ║
║                                        ║
║  💳 Formas de pagamento:                ║
║  ☑ PIX  ☑ Cartão  ☐ Boleto            ║
║                                        ║
║  📦 Como calcular frete:                ║
║  ( ) Fixo (R$ ____)                    ║
║  ( ) Grátis acima de R$ ____           ║
║  ( ) API Correios/Melhor Envio         ║
║                                        ║
║  🎭 Tom de voz:                         ║
║  Formal ●─────○───── Casual            ║
║                                        ║
║  [← Voltar]  [Testar Agente →]         ║
╚════════════════════════════════════════╝
```

#### **Teste do Agente (Sandbox)**
```
╔════════════════════════════════════════╗
║  🧪 Teste antes de ativar               ║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ 🤖 Carol                           │║
║  │ Olá! 👋 Sou a Carol da TrendStore  │║
║  │ Como posso te ajudar hoje?         │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ Você (teste)                       │║
║  │ Tem esse vestido em preto? →      │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ 🤖 Carol                           │║
║  │ Deixa eu consultar! 🔍             │║
║  │ Vestido Floral Summer:             │║
║  │ ✅ Preto - P, M, G (R$ 89,90)      │║
║  │ Quer adicionar ao carrinho?        │║
║  └────────────────────────────────────┘║
║                                        ║
║  [Testar mais] [Está ótimo, ativar!]   ║
╚════════════════════════════════════════╝
```

#### **Agente Ativado! 🎉**
```
╔════════════════════════════════════════╗
║  🎉 Carol está ativa!                   ║
║                                        ║
║  Envie uma mensagem para seu WhatsApp  ║
║  e veja a mágica acontecer ✨           ║
║                                        ║
║  [Ir para Dashboard]                   ║
╚════════════════════════════════════════╝
```

---

### **FASE 3: USO DIÁRIO (Dashboard Mobile)**

---

#### **BOTTOM NAVIGATION (Sempre visível)**
```
╔════════════════════════════════════════╗
║                                        ║
║    [Conteúdo da tela ativa aqui]      ║
║                                        ║
╠════════════════════════════════════════╣
║  💬 Chat  🤖 Agentes  📊 Stats  ⚙️ Mais ║
║   (3)        ●                         ║
╚════════════════════════════════════════╝
```
*(Badge "3" = 3 conversas aguardando)*  
*(Ponto verde em Agentes = pelo menos 1 ativo)*

---

#### **TAB 1: 💬 CHAT (Inbox)**
```
╔════════════════════════════════════════╗
║  💬 Conversas                   🔍 [ ]  ║
╠════════════════════════════════════════╣
║  🔴 AGUARDANDO VOCÊ (2)                ║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ JM  João Mendes         🔴 2min    │║
║  │ "Quero negociar o preço desse..."  │║
║  │ 🤖→👤 Carol escalou para você      │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ AS  Ana Silva           🔴 8min    │║
║  │ "Não recebi meu pedido ainda"      │║
║  │ 🤖→👤 Carol escalou para você      │║
║  └────────────────────────────────────┘║
║                                        ║
║  🟢 ATENDIDAS POR AGENTES (12)         ║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ MF  Maria Fernanda      🟢 agora   │║
║  │ "Obrigada! Já fiz o pagamento"     │║
║  │ 🤖 Carol está atendendo            │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ PC  Pedro Costa         🟢 5min    │║
║  │ "Qual o prazo de entrega?"         │║
║  │ 🤖 Carol está atendendo            │║
║  └────────────────────────────────────┘║
║                                        ║
║  [Ver todas (47)]                      ║
╚════════════════════════════════════════╝
```

**Ao clicar em uma conversa (ex: João Mendes):**

```
╔════════════════════════════════════════╗
║  ← JM João Mendes            ⋮         ║
║  🔴 Aguardando você                    ║
╠════════════════════════════════════════╣
║  ⚠️ HANDOFF SOLICITADO                 ║
║  🤖 Carol: "Cliente quer negociar      ║
║  desconto. Valor do carrinho: R$ 340"  ║
║  [Assumir Atendimento] [Ver Contexto]  ║
╠════════════════════════════════════════╣
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ Hoje, 14:23                        │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ João                               │║
║  │ Oi, tem esse vestido em preto?     │║
║  │ 14:23                              │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │                            🤖 Carol│║
║  │ Oi João! 👋 Sim, temos em P, M, G  │║
║  │                              14:23 │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ João                               │║
║  │ Vou querer 2 unidades, M e G.      │║
║  │ Rola um desconto? 😅                │║
║  │ 14:25                              │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │                            🤖 Carol│║
║  │ Vou transferir você para minha     │║
║  │ gerente! Um momento 😊              │║
║  │                              14:25 │║
║  └────────────────────────────────────┘║
║                                        ║
║  ⏸️ Bot pausado - Você está no controle║
║                                        ║
║  [__________________________] [Enviar] ║
╚════════════════════════════════════════╝
```

**Botões no menu ⋮ (canto superior direito):**
- Ver perfil do cliente (nome, histórico)
- Devolver para o bot
- Marcar como resolvido
- Adicionar nota interna
- Bloquear contato

**Ver Contexto (botão no HandoffBanner):**
```
╔════════════════════════════════════════╗
║  📋 Contexto da Conversa               ║
║                                        ║
║  👤 Cliente: João Mendes                ║
║  📞 Telefone: +55 11 98765-1234         ║
║  📧 Email: —                            ║
║                                        ║
║  🛒 Carrinho Atual:                     ║
║  • Vestido Floral Summer (M) - R$ 170  ║
║  • Vestido Floral Summer (G) - R$ 170  ║
║  • Frete: R$ 15                        ║
║  💰 Total: R$ 355                       ║
║                                        ║
║  📊 Histórico:                          ║
║  • 1ª conversa (cliente novo)           ║
║  • Intenção: Compra                    ║
║  • Sentimento: Positivo                ║
║                                        ║
║  🤖 Agente: Carol (Vendas eCommerce)    ║
║  ⏱️ Tempo de atendimento: 4min          ║
║                                        ║
║  [Fechar]                              ║
╚════════════════════════════════════════╝
```

---

#### **TAB 2: 🤖 AGENTES (Gestão)**
```
╔════════════════════════════════════════╗
║  🤖 Meus Agentes            [+ Criar]  ║
╠════════════════════════════════════════╣
║  ATIVOS (2)                            ║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ 🛍️ Carol (Vendas eCommerce)  🟢    │║
║  │ ━━━━━━━━━━ 47 mensagens hoje       │║
║  │ Taxa resolução: 78% (36 resolvidas)│║
║  │ Handoffs: 11  Custo: R$ 2,34       │║
║  │                                    │║
║  │ [Editar] [Pausar] [Ver Analytics]  │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ 💬 Roberto (SAC Triagem)      🟢   │║
║  │ ━━━━━━━━━━ 23 mensagens hoje       │║
║  │ Taxa resolução: 91% (21 resolvidas)│║
║  │ Handoffs: 2  Custo: R$ 1,12        │║
║  │                                    │║
║  │ [Editar] [Pausar] [Ver Analytics]  │║
║  └────────────────────────────────────┘║
║                                        ║
║  INATIVOS (0)                          ║
║                                        ║
║  [+ Criar Novo Agente]                 ║
╚════════════════════════════════════════╝
```

**Ao clicar em [Editar] (ex: Carol):**
```
╔════════════════════════════════════════╗
║  ← Editar Agente: Carol                ║
╠════════════════════════════════════════╣
║  📝 INFORMAÇÕES BÁSICAS                 ║
║                                        ║
║  Nome: [Carol____________]             ║
║  Tipo: Vendas eCommerce   [Trocar]     ║
║  Status: 🟢 Ativo  [Pausar]            ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  💬 PERSONALIDADE                       ║
║                                        ║
║  Tom de voz:                           ║
║  Formal ──────●── Casual               ║
║                                        ║
║  Tamanho das respostas:                ║
║  Conciso ●─────── Detalhado            ║
║                                        ║
║  Uso de emojis:                        ║
║  Nunca ─────●──── Sempre               ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  🧠 PROMPT DO SISTEMA (Avançado)        ║
║  [Expandir para editar]                ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  ⚙️ PARÂMETROS TÉCNICOS                 ║
║                                        ║
║  Temperature (criatividade):           ║
║  Conservador ──●───── Criativo         ║
║  (0.4 - respostas consistentes)        ║
║                                        ║
║  Max tokens (tamanho resposta):        ║
║  [500] tokens (~200 palavras)          ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  🔗 INTEGRAÇÕES                         ║
║                                        ║
║  ✅ Google Sheets (Catálogo Produtos)  ║
║  ✅ API Correios (Cálculo Frete)       ║
║  ❌ Mercado Pago (Pagamentos)          ║
║     [Conectar]                         ║
║                                        ║
║  [+ Adicionar Integração]              ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  🚨 QUANDO ESCALAR PARA HUMANO          ║
║                                        ║
║  ☑ Cliente pede para falar com humano  ║
║  ☑ Não conseguiu resolver em 3 msgs    ║
║  ☑ Cliente usa palavras: "urgente",    ║
║    "reclamação", "processo"            ║
║  ☑ Cliente quer negociar preço         ║
║  ☐ Sentimento negativo detectado       ║
║                                        ║
║  [Salvar Alterações]  [Cancelar]       ║
╚════════════════════════════════════════╝
```

**Ao clicar em [+ Criar Novo Agente]:**
```
╔════════════════════════════════════════╗
║  🤖 Criar Novo Agente                   ║
╠════════════════════════════════════════╣
║  🎯 COMECE COM UM TEMPLATE              ║
║                                        ║
║  [🔍 Buscar agente...____________]     ║
║                                        ║
║  📂 CATEGORIAS                          ║
║  • Vendas & eCommerce (5)              ║
║  • Atendimento & Suporte (6)           ║
║  • Agendamento (4)                     ║
║  • Restaurante & Delivery (2)          ║
║  • Educação (3)                        ║
║  • Imobiliário (1)                     ║
║  • Saúde (2)                           ║
║  • RH (2)                              ║
║  • Finanças (2)                        ║
║                                        ║
║  ⭐ MAIS POPULARES                      ║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ 💬 SAC Triagem                     │║
║  │ Acolhe e direciona clientes        │║
║  │ ⭐ 4.9 (3.4k) • 12k usando agora   │║
║  │ [Escolher]                         │║
║  └────────────────────────────────────┘║
║                                        ║
║  ┌────────────────────────────────────┐║
║  │ 🛍️ Vendas eCommerce                │║
║  │ Vende produtos pelo WhatsApp       │║
║  │ ⭐ 4.8 (1.2k) • 8k usando agora    │║
║  │ [Escolher]                         │║
║  └────────────────────────────────────┘║
║                                        ║
║  [Ver todos (27 agentes)]              ║
║                                        ║
║  ou [Criar do Zero] (avançado)         ║
╚════════════════════════════════════════╝
```

---

#### **TAB 3: 📊 ANALYTICS (Métricas)**
```
╔════════════════════════════════════════╗
║  📊 Analytics           [Hoje ▾]       ║
╠════════════════════════════════════════╣
║  📅 HOJE (15 Dez 2025)                  ║
║                                        ║
║  ┌───────────┬───────────┬───────────┐ ║
║  │ 💬 MENSAG │ 🤖 RESOLV │ 👤 HANDOFF│ ║
║  │    70     │   78%     │    13     │ ║
║  │ +23 ontem │ -2% ontem │ +5 ontem  │ ║
║  └───────────┴───────────┴───────────┘ ║
║                                        ║
║  ┌───────────────────────────────────┐ ║
║  │ 💰 CUSTO HOJE                     │ ║
║  │ R$ 3,46                           │ ║
║  │ (12.450 tokens × $0,003/1k)       │ ║
║  │ Projeção mês: R$ 104 (dentro do  │ ║
║  │ limite do plano)                  │ ║
║  └───────────────────────────────────┘ ║
║                                        ║
║  📈 MENSAGENS (últimos 7 dias)          ║
║                                        ║
║   80│        ▄                         ║
║   60│   ▄   █  ▄                       ║
║   40│  █ ▄ █  █                        ║
║   20│ █  █ █  █ ▄                      ║
║    0└─┬──┬──┬──┬──┬──┬─┬              ║
║      9 10 11 12 13 14 15               ║
║                                        ║
║  🎯 TOP 5 INTENÇÕES DETECTADAS          ║
║                                        ║
║  1. Dúvida sobre produto  ██████ 42%  ║
║  2. Fazer pedido          ████ 28%    ║
║  3. Rastrear entrega      ███ 15%     ║
║  4. Negociar preço        ██ 9%       ║
║  5. Reclamação            █ 6%        ║
║                                        ║
║  ⚡ DESEMPENHO POR AGENTE                ║
║                                        ║
║  🛍️ Carol (Vendas)                     ║
║  ━━━━━━━━━━ 78% resolução              ║
║  47 msgs • 11 handoffs • R$ 2,34      ║
║                                        ║
║  💬 Roberto (SAC)                       ║
║  ━━━━━━━━━━━━━━━━ 91% resolução        ║
║  23 msgs • 2 handoffs • R$ 1,12       ║
║                                        ║
║  [Ver Relatório Completo]              ║
╚════════════════════════════════════════╝
```

---

#### **TAB 4: ⚙️ CONFIGURAÇÕES**
```
╔════════════════════════════════════════╗
║  ⚙️ Configurações                       ║
╠════════════════════════════════════════╣
║  👤 CONTA                               ║
║  maria@trendstore.com.br               ║
║  [Editar Perfil] [Alterar Senha]       ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  🏢 EMPRESA                             ║
║  TrendStore                            ║
║  Varejo • 1-5 funcionários             ║
║  [Editar Dados]                        ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  📱 WHATSAPP CONECTADO                  ║
║  +55 11 98765-4321                     ║
║  🟢 Online                              ║
║  [Desconectar] [Trocar Número]         ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  🔗 INTEGRAÇÕES                         ║
║  • Google Sheets      ✅ Conectado     ║
║  • Google Calendar    ❌ Desconectado  ║
║  • Mercado Pago       ❌ Desconectado  ║
║  • API dos Correios   ✅ Conectado     ║
║  [+ Adicionar Integração]              ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  💳 PLANO E PAGAMENTO                   ║
║  Plano: Starter ($19/mês)              ║
║  Próxima cobrança: 01 Jan 2026         ║
║  Uso: 3.450 / 10.000 mensagens         ║
║  [Upgrade para Pro] [Fatura]           ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  🔔 NOTIFICAÇÕES                        ║
║  ☑ Push: Handoff solicitado            ║
║  ☑ Push: Cliente aguarda > 5min        ║
║  ☑ Email: Relatório semanal            ║
║  ☐ Email: Toda mensagem                ║
║  [Salvar]                              ║
║                                        ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                        ║
║  ❓ AJUDA E SUPORTE                     ║
║  [Central de Ajuda] [Chat com Suporte] ║
║  [Tutoriais em Vídeo]                  ║
║                                        ║
║  🚪 [Sair da Conta]                     ║
╚════════════════════════════════════════╝
```

---

## 🎨 DESIGN SYSTEM DETALHADO

### **CORES (Paleta Completa)**
```css
/* Background */
--bg-primary: #F8F9FA     /* Fundo principal */
--bg-secondary: #FFFFFF   /* Cards/elevados */
--bg-tertiary: #E9ECEF    /* Áreas desabilitadas */

/* Primary (Indigo) */
--primary-50: #EEF2FF
--primary-100: #E0E7FF
--primary-500: #6366F1    /* Principal */
--primary-600: #4F46E5    /* Hover */
--primary-700: #4338CA    /* Pressed */

/* Success (Verde) */
--success-50: #ECFDF5
--success-500: #10B981    /* Agente ativo */
--success-700: #047857    /* Hover */

/* Warning (Laranja) */
--warning-50: #FFF7ED
--warning-500: #F59E0B    /* Atenção */
--warning-700: #C2410C    /* Hover */

/* Error (Vermelho) */
--error-50: #FEF2F2
--error-500: #EF4444      /* Handoff/urgente */
--error-700: #B91C1C      /* Hover */

/* Neutral (Cinza) */
--gray-50: #F9FAFB
--gray-100: #F3F4F6       /* Bubbles do usuário */
--gray-500: #6B7280       /* Textos secundários */
--gray-900: #111827       /* Textos principais */
```

### **TIPOGRAFIA**
```css
/* Fonte: Inter (Google Fonts) */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Hierarchy */
H1: 24px / bold / letter-spacing -0.5px
H2: 20px / semibold / letter-spacing -0.3px
H3: 16px / semibold
Body: 14px / regular / line-height 1.5
Caption: 12px / regular / color: gray-500
```

### **COMPONENTES ESPECÍFICOS**

#### **ChatBubble (Bolhas de Mensagem)**
```jsx
/* Usuário (cinza, esquerda) */
.bubble-user {
  background: #F3F4F6;
  color: #111827;
  border-radius: 16px 16px 16px 4px;
  padding: 12px 16px;
  max-width: 70%;
  align-self: flex-start;
}

/* Agente IA (indigo, direita) */
.bubble-agent {
  background: #E0E7FF;
  color: #4338CA;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
  max-width: 70%;
  align-self: flex-end;
}

/* Humano (verde, direita) */
.bubble-human {
  background: #ECFDF5;
  color: #047857;
  border-radius: 16px 16px 4px 16px;
  padding: 12px 16px;
  max-width: 70%;
  align-self: flex-end;
}

/* Timestamp */
.bubble-timestamp {
  font-size: 11px;
  color: #6B7280;
  margin-top: 4px;
}
```

#### **TypingIndicator (3 pontos animados)**
```jsx
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #F3F4F6;
  border-radius: 16px;
  width: fit-content;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #6B7280;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.7; }
  30% { transform: translateY(-10px); opacity: 1; }
}
```

#### **StatusDot (Indicador de Status)**
```jsx
/* Verde pulsante (ativo) */
.status-dot-active {
  width: 8px;
  height: 8px;
  background: #10B981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
}

/* Cinza (inativo) */
.status-dot-inactive {
  width: 8px;
  height: 8px;
  background: #9CA3AF;
  border-radius: 50%;
}

/* Vermelho (erro) */
.status-dot-error {
  width: 8px;
  height: 8px;
  background: #EF4444;
  border-radius: 50%;
}
```

#### **HandoffBanner (Banner de Transferência)**
```jsx
.handoff-banner {
  background: #FEF2F2;
  border-left: 4px solid #EF4444;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.handoff-banner-icon {
  font-size: 24px;
  color: #EF4444;
}

.handoff-banner-text {
  flex: 1;
  font-size: 14px;
  color: #7F1D1D;
  font-weight: 500;
}

.handoff-banner-buttons {
  display: flex;
  gap: 8px;
}

.handoff-btn-primary {
  background: #EF4444;
  color: white;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
}

.handoff-btn-secondary {
  background: white;
  color: #EF4444;
  border: 1px solid #EF4444;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
}
```

---

## 🚀 DIFERENCIAÇÃO COMPETITIVA

### **O QUE AGENTFLOW FAZ QUE OS OUTROS NÃO FAZEM:**

#### 1. **IA Contextual de Verdade (não apenas fluxos)**
- **Concorrentes:** Fluxos if/else programados (ex: ManyChat)
- **AgentFlow:** Claude 3.5 Sonnet entende contexto, aprende com histórico, responde naturalmente

#### 2. **Orquestração Multi-Agente Nativa**
- **Concorrentes:** Precisa criar vários bots separados e conectar manualmente
- **AgentFlow:** Agentes conversam entre si, passam contexto automaticamente (SAC → Vendas sem perder dados)

#### 3. **Handoff Inteligente (não manual)**
- **Concorrentes:** Botão "Falar com humano" → usuário fica esperando
- **AgentFlow:** IA detecta frustração/urgência e escala automaticamente + notifica operador

#### 4. **Marketplace com 20+ Agentes Prontos**
- **Concorrentes:** Template genérico ou precisa construir do zero
- **AgentFlow:** Clica no agente (ex: "Dentista"), personaliza 3 campos, ativa

#### 5. **Mobile-First Real (não responsivo genérico)**
- **Concorrentes:** Desktop adaptado para mobile
- **AgentFlow:** Bottom navigation, gestos, PWA instalável — UX nativa mobile

#### 6. **Pricing Justo e Transparente**
- **Concorrentes:** $50-100/mês + cobranças ocultas
- **AgentFlow:** $19/mês fixo (até 10k msgs) — sem surpresas

---

## 💰 MODELO DE NEGÓCIO E PLANOS

### **PLANOS DE ASSINATURA**

#### **FREE (Pra Testar)**
- ✅ 1 agente ativo
- ✅ 100 mensagens/mês
- ✅ Marketplace completo
- ✅ 7 dias de histórico
- ❌ Sem integrações
- ❌ Sem analytics avançado
- **Preço:** Grátis

#### **STARTER (Pequenos Negócios)** ⭐ Mais Popular
- ✅ 3 agentes ativos
- ✅ 10.000 mensagens/mês
- ✅ Todas as integrações
- ✅ Analytics completo
- ✅ Histórico ilimitado
- ✅ Suporte por email (24h)
- **Preço:** $19/mês (ou $190/ano, economiza $38)

#### **PRO (Negócios em Crescimento)**
- ✅ 10 agentes ativos
- ✅ 50.000 mensagens/mês
- ✅ Multi-usuários (até 5 operadores)
- ✅ API access (webhooks personalizados)
- ✅ White label (remove logo AgentFlow)
- ✅ Suporte prioritário (chat ao vivo)
- **Preço:** $79/mês (ou $790/ano, economiza $158)

#### **ENTERPRISE (Grandes Operações)**
- ✅ Agentes ilimitados
- ✅ Mensagens ilimitadas
- ✅ Multi-usuários ilimitados
- ✅ SLA 99.9% uptime
- ✅ Gerente de conta dedicado
- ✅ Treinamento personalizado
- ✅ Infraestrutura dedicada (opcional)
- **Preço:** Custom (contato comercial)

---

## 🛣️ ROADMAP DE FUNCIONALIDADES

### **MVP (Fases 1-4 — 40 dias)**
✅ WhatsApp conectado  
✅ Claude respondendo (single agent)  
✅ Multi-agente + handoff  
✅ Dashboard mobile completo  
✅ Marketplace com 20 agentes  
✅ Analytics básico  

### **Versão 1.5 (3 meses pós-MVP)**
🔜 Integrações avançadas (Shopify, WooCommerce, HubSpot)  
🔜 Suporte a Instagram DM e Telegram  
🔜 Agendamento automático com Google Calendar/Calendly  
🔜 Broadcast de mensagens (campanhas)  
🔜 A/B testing de agentes  
🔜 Exportar conversas (CSV, PDF)  

### **Versão 2.0 (6 meses pós-MVP)**
🔮 Agente Builder visual (drag-and-drop)  
🔮 Treinamento custom com arquivos próprios (RAG)  
🔮 Voz (WhatsApp voice messages + TTS)  
🔮 Multi-idiomas automático (detecta idioma do cliente)  
🔮 Marketplace público (venda seus agentes)  
🔮 Co-pilot para operadores (IA sugere respostas)  

---

## 🎓 ESTRATÉGIA DE GO-TO-MARKET

### **Público-Alvo Primário (Primeiros 6 meses):**
1. **Pequenos varejistas** (Instagram + WhatsApp)
2. **Clínicas/consultórios** (agendamento sobrecarregado)
3. **Restaurantes delivery** (pedidos por WhatsApp)
4. **Prestadores de serviço** (advogados, contadores, etc)

### **Canais de Aquisição:**
1. **Orgânico (SEO):** "Como automatizar WhatsApp", "Chatbot para clínica"
2. **Conteúdo:** YouTube (tutoriais), blog (casos de uso)
3. **Freemium:** Plano grátis → upsell natural após 100 msgs
4. **Indicação:** "Indique e ganhe" (1 mês grátis para cada amigo)
5. **Parcerias:** Agências de marketing digital, ERPs pequenos

### **Posicionamento:**
> "ManyChat é complicado. WhatsApp Business é limitado.  
> **AgentFlow é simples e poderoso.**  
> Configure um agente IA em 3 minutos. Sem código."

---

## ✅ PRÓXIMA DECISÃO

**Perguntas para você:**

1. ✅ **Este estudo reflete a visão que você tinha?**  
   - Algo faltou ou precisa ajustar?

2. 🤖 **Quantos agentes quer no MVP?**  
   - Sugeri 20, mas podemos começar com 8-10 essenciais

3. 🎨 **Design aprovado?**  
   - Mobile-first, bottom nav, cores indigo/verde/vermelho

4. 🚀 **Pronto para executar FASE 1?**  
   - Fundação + WhatsApp conectado + banco configurado

**Aguardo seu feedback para começarmos! 🔥**
