# 🎯 AGENTFLOW - CRM KANBAN AUTOMATIZADO POR IA
## Análise Completa da Feature + Implementação

---

## 📋 RESUMO EXECUTIVO

### **O QUE VOCÊ QUER:**
Um **CRM interno com Kanban visual** onde:
- ✅ Cada conversa pode virar lead automaticamente
- ✅ IA move leads entre colunas (Novo → Qualificado → Proposta → Ganho/Perdido)
- ✅ Regras configuráveis (quando automatizar, quando deixar manual)
- ✅ Drag-and-drop manual também disponível
- ✅ Completamente integrado com conversas e agentes

### **IMPACTO NO PRODUTO:**

| Aspecto | Antes | Depois | Impacto |
|---------|-------|--------|---------|
| **Posicionamento** | Chatbot + IA | **CRM + Chatbot + IA** | 🚀 +300% |
| **Valor percebido** | $29-79/mês | **$49-149/mês** | +70% |
| **Concorrência** | vs ManyChat, Typebot | **vs HubSpot, Pipedrive** | 🎯 Novo mercado |
| **Diferencial** | Alto | **EXTREMO** | 🔥 |
| **Complexidade** | Alta | Muito Alta | +30% |
| **Tempo** | 65 dias | **75 dias** | +10 dias |

### **VEREDITO: VALE A PENA? 🎯**

✅ **SIM, 1000%!** Essa feature transforma o AgentFlow em um **"HubSpot killer"** porque:

1. **Elimina integração externa:**
   - Não precisa pagar HubSpot ($45/mês) ou Pipedrive ($14/mês)
   - Tudo em uma plataforma só

2. **IA faz trabalho de CRM Manager:**
   - Qualifica leads automaticamente
   - Move pelo pipeline baseado em comportamento
   - Economiza 10h/semana de trabalho manual

3. **Diferencial ÚNICO no mercado:**
   - ManyChat → não tem CRM
   - Typebot → não tem CRM
   - HubSpot → tem CRM mas IA limitada + caro
   - **AgentFlow → CRM + IA real + conversas + omnichannel**

---

## 🎨 VISÃO DE PRODUTO: COMO FUNCIONA

### **Fluxo Completo:**

```
Cliente envia mensagem no WhatsApp
    ↓
Agente IA responde e detecta intenção
    ↓
[IA avalia: "Esse é um lead?"]
    ↓
SE SIM → Cria lead automaticamente no Kanban
    ↓
Lead aparece na coluna "Novos Leads"
    ↓
Agente continua conversando + coleta informações
    ↓
[IA avalia: "Lead está qualificado?"]
    ↓
SE SIM → Move para "Qualificados" automaticamente
    ↓
Vendedor recebe notificação
    ↓
Vendedor assume conversa ou continua no bot
    ↓
[IA detecta: "Vendedor enviou proposta"]
    ↓
Move para "Proposta Enviada"
    ↓
Cliente: "Vou fechar!"
    ↓
[IA detecta: "Fechamento confirmado"]
    ↓
Move para "Ganho" 🎉
```

---

## 📊 MOCKUP: TELA DO KANBAN

```
╔═══════════════════════════════════════════════════════════════════╗
║  🎯 Pipeline de Vendas                          [+ Criar Lead]    ║
╠═══════════════════════════════════════════════════════════════════╣
║  Filtros: [Todos] [Meus] [Bot] [Humano]    Agente: [Todos ▾]     ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  ┌──────────────┬──────────────┬──────────────┬──────────────┐   ║
║  │ 🆕 NOVOS     │ ✅ QUALIF.   │ 📄 PROPOSTA  │ 🎉 GANHO     │   ║
║  │ 12 leads     │ 8 leads      │ 5 leads      │ 3 leads      │   ║
║  │ R$ 18.4k     │ R$ 24.5k     │ R$ 32.1k     │ R$ 15.7k     │   ║
║  ├──────────────┼──────────────┼──────────────┼──────────────┤   ║
║  │              │              │              │              │   ║
║  │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │   ║
║  │ │🤖 Maria  │ │ │👤 João   │ │ │👤 Pedro  │ │ │👤 Ana    │ │   ║
║  │ │Silva     │ │ │Costa     │ │ │Santos    │ │ │Lima      │ │   ║
║  │ │──────────│ │ │──────────│ │ │──────────│ │ │──────────│ │   ║
║  │ │R$ 2.5k   │ │ │R$ 8.2k   │ │ │R$ 12k    │ │ │R$ 5.7k   │ │   ║
║  │ │          │ │ │          │ │ │          │ │ │          │ │   ║
║  │ │Score: 65 │ │ │Score: 82 │ │ │Score: 91 │ │ │Fechado em│ │   ║
║  │ │🔥🔥🔥    │ │ │🔥🔥🔥🔥  │ │ │🔥🔥🔥🔥🔥│ │ │12/03/25  │ │   ║
║  │ │          │ │ │          │ │ │          │ │ │          │ │   ║
║  │ │Carol     │ │ │Carol     │ │ │Você      │ │ │Você      │ │   ║
║  │ │atendendo │ │ │→Humano   │ │ │          │ │ │          │ │   ║
║  │ │          │ │ │          │ │ │          │ │ │          │ │   ║
║  │ │2min atrás│ │ │1h atrás  │ │ │Ontem     │ │ │Hoje      │ │   ║
║  │ └──────────┘ │ └──────────┘ │ └──────────┘ │ └──────────┘ │   ║
║  │              │              │              │              │   ║
║  │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │   ║
║  │ │🤖 Carlos │ │ │🤖 Lucia  │ │ │👤 Rafael │ │ │👤 Bruna  │ │   ║
║  │ │Mendes    │ │ │Oliveira  │ │ │Souza     │ │ │Costa     │ │   ║
║  │ │──────────│ │ │──────────│ │ │──────────│ │ │──────────│ │   ║
║  │ │R$ 1.2k   │ │ │R$ 5.1k   │ │ │R$ 8.3k   │ │ │R$ 10k    │ │   ║
║  │ │Score: 42 │ │ │Score: 78 │ │ │Score: 88 │ │ │Fechado em│ │   ║
║  │ │🔥🔥      │ │ │🔥🔥🔥🔥  │ │ │🔥🔥🔥🔥  │ │ │10/03/25  │ │   ║
║  │ │Roberto   │ │ │Carol     │ │ │Você      │ │ │Carol     │ │   ║
║  │ │atendendo │ │ │atendendo │ │ │          │ │ │          │ │   ║
║  │ │1h atrás  │ │ │30min     │ │ │2 dias    │ │ │2 dias    │ │   ║
║  │ └──────────┘ │ └──────────┘ │ └──────────┘ │ └──────────┘ │   ║
║  │              │              │              │              │   ║
║  │ [Ver +9]     │ [Ver +5]     │ [Ver +2]     │ [Ver +1]     │   ║
║  └──────────────┴──────────────┴──────────────┴──────────────┘   ║
║                                                                    ║
║  ┌──────────────┐                                                 ║
║  │ ❌ PERDIDO   │                                                 ║
║  │ 7 leads      │                                                 ║
║  │ R$ 11.3k     │                                                 ║
║  └──────────────┘                                                 ║
╚═══════════════════════════════════════════════════════════════════╝
```

### **Detalhes do Card:**
- **Ícone:** 🤖 (bot atendendo) ou 👤 (humano atendendo)
- **Nome:** Nome do lead
- **Valor:** Valor da oportunidade (estimado ou informado)
- **Score:** 0-100 (qualificação automática por IA)
- **Fogo:** Visual do score (mais fogo = mais qualificado)
- **Agente atual:** Quem está atendendo
- **Última atividade:** Timestamp

---

## 🎯 TELA: DETALHE DO LEAD

```
╔═══════════════════════════════════════════════════════════════════╗
║  ← Voltar                Maria Silva                    [Editar]  ║
╠═══════════════════════════════════════════════════════════════════╣
║  Status: 🆕 NOVO LEAD              Score: 65 🔥🔥🔥                ║
║  Valor: R$ 2.500                   Prob. Fechar: 35%              ║
║                                                                    ║
║  [Mover para Qualificado] [Marcar como Perdido] [Assumir]        ║
╠═══════════════════════════════════════════════════════════════════╣
║  📋 INFORMAÇÕES                                                    ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │ Nome: Maria Silva                                           │  ║
║  │ WhatsApp: +55 11 98765-4321                                 │  ║
║  │ Email: maria@example.com                                    │  ║
║  │ Empresa: Boutique da Maria                                  │  ║
║  │ Cargo: Proprietária                                         │  ║
║  │ Origem: WhatsApp - Carol (Vendas)                           │  ║
║  │ Criado: 15/03/2025 14:32                                    │  ║
║  │ Última atividade: 2min atrás                                │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║  💬 CONTEXTO DA CONVERSA                                           ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │ Interesse: Automação de vendas no WhatsApp                  │  ║
║  │ Dor: Gasta 4h/dia respondendo mensagens repetitivas         │  ║
║  │ Orçamento: R$ 50-100/mês                                    │  ║
║  │ Urgência: Alta (precisa para a Black Friday)                │  ║
║  │ Decisor: Sim (é a dona)                                     │  ║
║  │ Concorrente: Já tentou ManyChat mas não gostou              │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║  🤖 ANÁLISE DA IA                                                  ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │ ✅ Lead qualificado - Alto potencial                         │  ║
║  │                                                              │  ║
║  │ Motivos:                                                     │  ║
║  │ • Dor clara e urgente                                        │  ║
║  │ • Orçamento alinhado com plano Pro                           │  ║
║  │ • É a decisora (fecha mais rápido)                           │  ║
║  │ • Conhece concorrente (sabe o que NÃO quer)                  │  ║
║  │ • Urgência real (deadline Black Friday)                      │  ║
║  │                                                              │  ║
║  │ Próxima ação sugerida:                                       │  ║
║  │ → Enviar demo personalizada (foco anti-ManyChat)             │  ║
║  │ → Mencionar setup em 3min (ela não tem tempo)               │  ║
║  │ → Oferecer trial até Black Friday                            │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║  📊 ATIVIDADES (Timeline)                                          ║
║  ┌─────────────────────────────────────────────────────────────┐  ║
║  │ 🤖 2min atrás - Carol perguntou sobre orçamento             │  ║
║  │ 👤 3min atrás - Maria: "Entre R$ 50-100"                    │  ║
║  │ 🤖 5min atrás - Carol explicou planos                       │  ║
║  │ 🔄 10min atrás - IA moveu de "Visitante" para "Novo Lead"   │  ║
║  │ 👤 10min atrás - Maria: "Quero automatizar meu WhatsApp"    │  ║
║  │ 🤖 11min atrás - Carol iniciou conversa                     │  ║
║  └─────────────────────────────────────────────────────────────┘  ║
║                                                                    ║
║  💬 [Abrir Conversa Completa]                                      ║
╚═══════════════════════════════════════════════════════════════════╝
```

---

## 🏗️ ARQUITETURA TÉCNICA

### **Schema MongoDB: Leads**

```javascript
// leads collection
{
  id: "uuid",
  tenant_id: "uuid",
  
  // Dados básicos
  name: "Maria Silva",
  email: "maria@example.com",
  phone: "+55 11 98765-4321",
  company: "Boutique da Maria",
  job_title: "Proprietária",
  
  // Pipeline
  stage: "new" | "qualified" | "proposal" | "won" | "lost",
  stage_history: [
    {
      stage: "new",
      entered_at: "2025-03-15T14:32:00Z",
      exited_at: "2025-03-15T15:00:00Z",
      moved_by: "ai",  // "ai" | "user_id" | "manual"
      reason: "Lead demonstrou interesse claro"
    }
  ],
  
  // Valor e score
  value: 2500.00,  // R$
  currency: "BRL",
  probability: 0.35,  // 35% de chance de fechar
  score: 65,  // 0-100 (calculado por IA)
  
  // Origem
  source: {
    channel: "whatsapp",  // whatsapp | instagram | facebook | telegram
    agent_id: "uuid",
    agent_name: "Carol",
    conversation_id: "uuid",
    first_message: "Quero automatizar meu WhatsApp",
    created_at: "2025-03-15T14:32:00Z"
  },
  
  // Contexto coletado pela IA
  context: {
    pain_points: ["Gasta 4h/dia em mensagens repetitivas", "Sobrecarga"],
    interests: ["Automação de vendas", "Economia de tempo"],
    budget: "R$ 50-100/mês",
    urgency: "high",  // low | medium | high
    decision_maker: true,
    competitors_mentioned: ["ManyChat"],
    timeline: "Black Friday (60 dias)"
  },
  
  // Análise da IA
  ai_analysis: {
    qualification_reason: "Dor clara, orçamento alinhado, decisora, urgência real",
    suggested_actions: [
      "Enviar demo personalizada",
      "Mencionar setup em 3min",
      "Oferecer trial até Black Friday"
    ],
    deal_breakers: [],  // Possíveis objeções
    winning_factors: ["É decisora", "Conhece concorrente", "Urgência"]
  },
  
  // Atribuição
  assigned_to: null,  // user_id quando assumido por humano
  current_handler: "agent_vendas_123",  // Quem está atendendo (bot ou humano)
  handler_type: "bot" | "human",
  
  // Timestamps
  created_at: "2025-03-15T14:32:00Z",
  updated_at: "2025-03-15T14:34:00Z",
  last_activity_at: "2025-03-15T14:34:00Z",
  won_at: null,
  lost_at: null,
  
  // Motivo de perda (se perdido)
  lost_reason: null,  // "price" | "competitor" | "timing" | "not_interested" | "other"
  lost_notes: null
}
```

### **Schema: Pipeline Stages**

```javascript
// pipeline_stages collection (configurável por tenant)
{
  id: "uuid",
  tenant_id: "uuid",
  
  stages: [
    {
      id: "new",
      name: "Novos Leads",
      order: 1,
      color: "#6366F1",  // Indigo
      icon: "🆕",
      
      // Regras de entrada automática
      auto_entry_rules: {
        enabled: true,
        conditions: [
          {
            type: "intent_detected",
            value: ["compra", "interesse", "orçamento"]
          },
          {
            type: "message_count",
            operator: ">=",
            value: 3  // Após 3 mensagens
          }
        ]
      },
      
      // Regras de saída automática (mover para próximo stage)
      auto_exit_rules: {
        enabled: true,
        target_stage: "qualified",
        conditions: [
          {
            type: "score",
            operator: ">=",
            value: 60  // Score >= 60 → Qualificado
          },
          {
            type: "field_collected",
            fields: ["name", "email", "budget"]
          }
        ]
      }
    },
    {
      id: "qualified",
      name: "Qualificados",
      order: 2,
      color: "#10B981",  // Verde
      icon: "✅",
      
      auto_entry_rules: {
        enabled: true,
        conditions: [
          {
            type: "score",
            operator: ">=",
            value: 60
          }
        ]
      },
      
      auto_exit_rules: {
        enabled: true,
        target_stage: "proposal",
        conditions: [
          {
            type: "keyword_detected",
            keywords: ["proposta", "orçamento", "quanto custa", "preço"]
          },
          {
            type: "human_takeover",
            value: true  // Quando humano assume
          }
        ]
      }
    },
    {
      id: "proposal",
      name: "Proposta Enviada",
      order: 3,
      color: "#F59E0B",  // Laranja
      icon: "📄",
      
      auto_entry_rules: {
        enabled: true,
        conditions: [
          {
            type: "keyword_detected",
            keywords: ["enviada", "segue proposta", "orçamento"]
          }
        ]
      },
      
      auto_exit_rules: {
        enabled: false  // Precisa ação manual
      }
    },
    {
      id: "won",
      name: "Ganho",
      order: 4,
      color: "#10B981",  // Verde
      icon: "🎉",
      
      auto_entry_rules: {
        enabled: true,
        conditions: [
          {
            type: "keyword_detected",
            keywords: ["fechado", "vou comprar", "aceito", "pode enviar"]
          },
          {
            type: "payment_detected",
            value: true
          }
        ]
      }
    },
    {
      id: "lost",
      name: "Perdido",
      order: 5,
      color: "#EF4444",  // Vermelho
      icon: "❌",
      
      auto_entry_rules: {
        enabled: true,
        conditions: [
          {
            type: "keyword_detected",
            keywords: ["não quero", "caro demais", "não tenho interesse"]
          },
          {
            type: "inactive_days",
            operator: ">",
            value: 30  // Sem atividade há 30 dias
          }
        ]
      }
    }
  ],
  
  created_at: "2025-03-01T00:00:00Z",
  updated_at: "2025-03-15T10:00:00Z"
}
```

---

## 🤖 IMPLEMENTAÇÃO: IA MOVE LEADS

### **Tool Use: Gerenciar Pipeline**

```python
# Claude Tools para CRM
tools = [
    {
        "name": "create_lead",
        "description": "Cria um novo lead no CRM quando detecta interesse comercial",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "phone": {"type": "string"},
                "company": {"type": "string"},
                "value": {"type": "number", "description": "Valor estimado em R$"},
                "pain_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dores identificadas"
                },
                "interests": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "budget": {"type": "string"},
                "urgency": {"type": "string", "enum": ["low", "medium", "high"]},
                "decision_maker": {"type": "boolean"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "move_lead_stage",
        "description": "Move lead para outro estágio do pipeline",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "target_stage": {
                    "type": "string",
                    "enum": ["new", "qualified", "proposal", "won", "lost"]
                },
                "reason": {
                    "type": "string",
                    "description": "Por que está movendo"
                }
            },
            "required": ["lead_id", "target_stage", "reason"]
        }
    },
    {
        "name": "update_lead_score",
        "description": "Atualiza score de qualificação do lead (0-100)",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "factors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fatores que influenciaram o score"
                }
            },
            "required": ["lead_id", "score"]
        }
    },
    {
        "name": "update_lead_context",
        "description": "Atualiza informações coletadas sobre o lead",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "updates": {
                    "type": "object",
                    "description": "Campos para atualizar"
                }
            },
            "required": ["lead_id", "updates"]
        }
    }
]
```

### **Agent Processor: Avaliação Contínua**

```python
# /backend/services/crm_manager.py
class CRMManager:
    async def evaluate_conversation_for_lead(
        self,
        conversation_id: str,
        latest_messages: list
    ):
        """
        Avalia se conversa deve virar lead
        Chamado após cada mensagem do agente
        """
        conversation = await db.conversations.find_one({"id": conversation_id})
        
        # Verifica se já é lead
        existing_lead = await db.leads.find_one({
            "source.conversation_id": conversation_id
        })
        
        if existing_lead:
            # Já é lead, atualiza score e stage
            await self.update_existing_lead(existing_lead, latest_messages)
        else:
            # Avalia se deve criar lead
            should_create = await self.should_create_lead(
                conversation,
                latest_messages
            )
            
            if should_create:
                await self.create_lead_from_conversation(
                    conversation,
                    latest_messages
                )
    
    async def should_create_lead(
        self,
        conversation: dict,
        messages: list
    ) -> bool:
        """
        IA decide se conversa deve virar lead
        """
        # Monta contexto para Claude
        context = f"""
        Analise esta conversa e determine se o cliente é um LEAD (potencial comprador).
        
        Cliente: {conversation.get('customer_name', 'Desconhecido')}
        Canal: {conversation['channel']}
        Agente: {conversation['current_agent_name']}
        
        Últimas mensagens:
        {self.format_messages(messages)}
        
        Um lead é alguém que:
        - Demonstra interesse em comprar/contratar
        - Fez perguntas sobre preço, produto, serviço
        - Solicitou orçamento ou proposta
        - Tem dor/necessidade clara que nosso produto resolve
        
        NÃO é lead se:
        - É apenas dúvida pontual (FAQ)
        - Já é cliente (suporte técnico)
        - Spam ou mensagem sem sentido
        
        Responda com JSON:
        {{
            "is_lead": true/false,
            "confidence": 0.0-1.0,
            "reason": "explicação breve"
        }}
        """
        
        response = await self.claude.messages.create(
            model="claude-3-5-sonnet-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": context}]
        )
        
        result = json.loads(response.content[0].text)
        
        return result["is_lead"] and result["confidence"] > 0.7
    
    async def create_lead_from_conversation(
        self,
        conversation: dict,
        messages: list
    ):
        """
        Cria lead a partir da conversa
        """
        # Extrai informações com Claude
        extraction_prompt = f"""
        Extraia as seguintes informações desta conversa:
        
        {self.format_messages(messages)}
        
        Retorne JSON:
        {{
            "name": "nome do cliente",
            "email": "email se mencionado",
            "company": "empresa se mencionado",
            "value": 0,  // valor estimado em R$ (baseado no interesse)
            "pain_points": ["dor 1", "dor 2"],
            "interests": ["interesse 1"],
            "budget": "orçamento mencionado",
            "urgency": "low/medium/high",
            "decision_maker": true/false
        }}
        
        Se informação não foi mencionada, use null.
        """
        
        response = await self.claude.messages.create(
            model="claude-3-5-sonnet-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": extraction_prompt}]
        )
        
        extracted_data = json.loads(response.content[0].text)
        
        # Calcula score inicial
        score = await self.calculate_lead_score(extracted_data, messages)
        
        # Cria lead
        lead = {
            "id": str(uuid.uuid4()),
            "tenant_id": conversation["tenant_id"],
            **extracted_data,
            "stage": "new",
            "score": score,
            "probability": score / 100,  # Score 70 = 70% prob
            "source": {
                "channel": conversation["channel"],
                "agent_id": conversation["current_agent_id"],
                "agent_name": conversation["current_agent_name"],
                "conversation_id": conversation["id"],
                "first_message": messages[0]["content"]["text"],
                "created_at": datetime.now()
            },
            "handler_type": "bot",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "last_activity_at": datetime.now()
        }
        
        await db.leads.insert_one(lead)
        
        # Notifica via Realtime
        supabase.from_("lead_updates").insert({
            "lead_id": lead["id"],
            "event": "created",
            "stage": "new",
            "timestamp": datetime.now().isoformat()
        }).execute()
        
        return lead
    
    async def calculate_lead_score(
        self,
        lead_data: dict,
        messages: list
    ) -> int:
        """
        Calcula score 0-100 baseado em fatores
        """
        score = 0
        
        # Fatores demográficos
        if lead_data.get("email"):
            score += 10
        if lead_data.get("company"):
            score += 10
        if lead_data.get("decision_maker"):
            score += 20
        
        # Fatores comportamentais
        if lead_data.get("budget"):
            score += 15
        
        urgency_scores = {"low": 5, "medium": 10, "high": 20}
        score += urgency_scores.get(lead_data.get("urgency", "low"), 0)
        
        if len(lead_data.get("pain_points", [])) > 0:
            score += 10 * min(len(lead_data["pain_points"]), 3)
        
        # Engajamento
        if len(messages) >= 5:
            score += 10
        if len(messages) >= 10:
            score += 10
        
        return min(score, 100)
    
    async def update_existing_lead(
        self,
        lead: dict,
        latest_messages: list
    ):
        """
        Atualiza lead existente (score, stage, contexto)
        """
        # Recalcula score
        new_score = await self.calculate_lead_score(
            lead["context"],
            latest_messages
        )
        
        updates = {
            "score": new_score,
            "probability": new_score / 100,
            "updated_at": datetime.now(),
            "last_activity_at": datetime.now()
        }
        
        # Verifica se deve mudar de stage
        pipeline_config = await db.pipeline_stages.find_one({
            "tenant_id": lead["tenant_id"]
        })
        
        current_stage_config = next(
            s for s in pipeline_config["stages"]
            if s["id"] == lead["stage"]
        )
        
        if current_stage_config.get("auto_exit_rules", {}).get("enabled"):
            should_move, target_stage = await self.evaluate_stage_transition(
                lead,
                current_stage_config["auto_exit_rules"],
                latest_messages
            )
            
            if should_move:
                updates["stage"] = target_stage
                updates["stage_history"] = lead.get("stage_history", []) + [{
                    "stage": lead["stage"],
                    "entered_at": lead.get("updated_at"),
                    "exited_at": datetime.now(),
                    "moved_by": "ai",
                    "reason": f"Regras automáticas: mudou para {target_stage}"
                }]
                
                # Notifica Realtime
                supabase.from_("lead_updates").insert({
                    "lead_id": lead["id"],
                    "event": "stage_changed",
                    "from_stage": lead["stage"],
                    "to_stage": target_stage,
                    "moved_by": "ai",
                    "timestamp": datetime.now().isoformat()
                }).execute()
        
        await db.leads.update_one(
            {"id": lead["id"]},
            {"$set": updates}
        )
    
    async def evaluate_stage_transition(
        self,
        lead: dict,
        exit_rules: dict,
        messages: list
    ) -> tuple[bool, str]:
        """
        Avalia se lead deve mudar de stage
        """
        conditions = exit_rules["conditions"]
        target_stage = exit_rules["target_stage"]
        
        for condition in conditions:
            if condition["type"] == "score":
                if not self.check_condition(
                    lead["score"],
                    condition["operator"],
                    condition["value"]
                ):
                    return False, None
            
            elif condition["type"] == "keyword_detected":
                last_messages_text = " ".join([
                    m["content"]["text"]
                    for m in messages[-5:]  # Últimas 5 mensagens
                    if m["content"].get("text")
                ])
                
                keywords = condition["keywords"]
                if not any(kw in last_messages_text.lower() for kw in keywords):
                    return False, None
            
            elif condition["type"] == "field_collected":
                required_fields = condition["fields"]
                for field in required_fields:
                    if not lead["context"].get(field):
                        return False, None
        
        return True, target_stage
```

---

## 📱 FRONTEND: Kanban Board

### **Componente Principal:**

```jsx
// /frontend/src/components/crm/KanbanBoard.jsx
import { DndContext, DragOverlay } from '@dnd-kit/core';
import { useRealtimeLeads } from '@/hooks/useRealtimeLeads';

const KanbanBoard = () => {
  const { stages, leads, moveLeadManually, isMoving } = useRealtimeLeads();
  const [activeCard, setActiveCard] = useState(null);
  
  // Realtime subscription
  useEffect(() => {
    const subscription = supabase
      .from('lead_updates')
      .on('INSERT', (payload) => {
        if (payload.new.event === 'stage_changed') {
          toast.info(`Lead movido: ${payload.new.from_stage} → ${payload.new.to_stage}`);
          // Refetch leads (já faz automaticamente via hook)
        }
      })
      .subscribe();
    
    return () => subscription.unsubscribe();
  }, []);
  
  const handleDragEnd = async (event) => {
    const { active, over } = event;
    
    if (!over || active.id === over.id) return;
    
    const leadId = active.id;
    const targetStage = over.id;
    
    await moveLeadManually(leadId, targetStage);
  };
  
  return (
    <div className="kanban-board">
      <div className="board-header">
        <h1>🎯 Pipeline de Vendas</h1>
        <button onClick={() => setShowCreateLead(true)}>
          + Criar Lead
        </button>
      </div>
      
      <div className="board-filters">
        <select onChange={(e) => setFilter(e.target.value)}>
          <option value="all">Todos</option>
          <option value="mine">Meus</option>
          <option value="bot">Bot</option>
          <option value="human">Humano</option>
        </select>
      </div>
      
      <DndContext onDragEnd={handleDragEnd}>
        <div className="board-columns">
          {stages.map(stage => (
            <KanbanColumn
              key={stage.id}
              stage={stage}
              leads={leads.filter(l => l.stage === stage.id)}
              onCardClick={setSelectedLead}
            />
          ))}
        </div>
        
        <DragOverlay>
          {activeCard && <LeadCard lead={activeCard} isDragging />}
        </DragOverlay>
      </DndContext>
    </div>
  );
};
```

### **Coluna do Kanban:**

```jsx
// KanbanColumn.jsx
import { useDroppable } from '@dnd-kit/core';

const KanbanColumn = ({ stage, leads, onCardClick }) => {
  const { setNodeRef, isOver } = useDroppable({ id: stage.id });
  
  const totalValue = leads.reduce((sum, l) => sum + (l.value || 0), 0);
  
  return (
    <div
      ref={setNodeRef}
      className={`kanban-column ${isOver ? 'drag-over' : ''}`}
      style={{ borderTopColor: stage.color }}
    >
      <div className="column-header">
        <h3>
          {stage.icon} {stage.name}
        </h3>
        <div className="column-stats">
          <span className="count">{leads.length} leads</span>
          <span className="value">
            {new Intl.NumberFormat('pt-BR', {
              style: 'currency',
              currency: 'BRL'
            }).format(totalValue)}
          </span>
        </div>
      </div>
      
      <div className="column-body">
        {leads.map(lead => (
          <LeadCard
            key={lead.id}
            lead={lead}
            onClick={() => onCardClick(lead)}
          />
        ))}
        
        {leads.length === 0 && (
          <div className="empty-state">
            <p>Nenhum lead neste estágio</p>
          </div>
        )}
      </div>
    </div>
  );
};
```

### **Card do Lead:**

```jsx
// LeadCard.jsx
import { useDraggable } from '@dnd-kit/core';

const LeadCard = ({ lead, onClick, isDragging }) => {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: lead.id,
  });
  
  const style = transform ? {
    transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
  } : undefined;
  
  const getScoreFire = (score) => {
    if (score >= 80) return '🔥🔥🔥🔥🔥';
    if (score >= 60) return '🔥🔥🔥🔥';
    if (score >= 40) return '🔥🔥🔥';
    if (score >= 20) return '🔥🔥';
    return '🔥';
  };
  
  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      className={`lead-card ${isDragging ? 'dragging' : ''}`}
      onClick={() => !isDragging && onClick()}
    >
      <div className="card-header">
        <span className="handler-icon">
          {lead.handler_type === 'bot' ? '🤖' : '👤'}
        </span>
        <h4>{lead.name}</h4>
      </div>
      
      <div className="card-body">
        <div className="value">
          {new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 0
          }).format(lead.value || 0)}
        </div>
        
        <div className="score">
          <span>Score: {lead.score}</span>
          <span>{getScoreFire(lead.score)}</span>
        </div>
        
        <div className="handler">
          {lead.current_handler === 'agent'
            ? `${lead.source.agent_name} atendendo`
            : lead.assigned_to
              ? 'Você'
              : 'Não atribuído'
          }
        </div>
        
        <div className="timestamp">
          {formatDistanceToNow(new Date(lead.last_activity_at), {
            locale: ptBR,
            addSuffix: true
          })}
        </div>
      </div>
    </div>
  );
};
```

---

## ⚙️ TELA: CONFIGURAÇÃO DO PIPELINE

```jsx
// PipelineSettings.jsx
const PipelineSettings = () => {
  const [stages, setStages] = useState([]);
  const [editingStage, setEditingStage] = useState(null);
  
  return (
    <div className="pipeline-settings">
      <h2>⚙️ Configurar Pipeline de Vendas</h2>
      
      <div className="stages-list">
        {stages.map((stage, index) => (
          <div key={stage.id} className="stage-config">
            <div className="stage-header">
              <input
                type="text"
                value={stage.icon}
                onChange={(e) => updateStage(stage.id, 'icon', e.target.value)}
                className="icon-input"
                maxLength={2}
              />
              <input
                type="text"
                value={stage.name}
                onChange={(e) => updateStage(stage.id, 'name', e.target.value)}
                className="name-input"
              />
              <input
                type="color"
                value={stage.color}
                onChange={(e) => updateStage(stage.id, 'color', e.target.value)}
              />
            </div>
            
            <div className="stage-rules">
              <h4>🤖 Automações</h4>
              
              <label>
                <input
                  type="checkbox"
                  checked={stage.auto_entry_rules?.enabled}
                  onChange={(e) => toggleAutoEntry(stage.id, e.target.checked)}
                />
                Mover leads automaticamente PARA este estágio
              </label>
              
              {stage.auto_entry_rules?.enabled && (
                <div className="rules-config">
                  <h5>Quando:</h5>
                  {stage.auto_entry_rules.conditions.map((condition, i) => (
                    <ConditionBuilder
                      key={i}
                      condition={condition}
                      onChange={(updated) => updateCondition(stage.id, i, updated)}
                    />
                  ))}
                  <button onClick={() => addCondition(stage.id)}>
                    + Adicionar Condição
                  </button>
                </div>
              )}
              
              <label>
                <input
                  type="checkbox"
                  checked={stage.auto_exit_rules?.enabled}
                  onChange={(e) => toggleAutoExit(stage.id, e.target.checked)}
                />
                Mover leads automaticamente DESTE estágio
              </label>
              
              {stage.auto_exit_rules?.enabled && (
                <div className="rules-config">
                  <h5>Para:</h5>
                  <select
                    value={stage.auto_exit_rules.target_stage}
                    onChange={(e) => updateTargetStage(stage.id, e.target.value)}
                  >
                    {stages.filter(s => s.order > stage.order).map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                  
                  <h5>Quando:</h5>
                  {stage.auto_exit_rules.conditions.map((condition, i) => (
                    <ConditionBuilder
                      key={i}
                      condition={condition}
                      onChange={(updated) => updateExitCondition(stage.id, i, updated)}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <button onClick={saveSettings} className="btn-primary">
        Salvar Configurações
      </button>
    </div>
  );
};
```

---

## 📊 COMPLEXIDADE E TEMPO

### **ANÁLISE DETALHADA:**

| Componente | Complexidade | Tempo | Dependências |
|------------|--------------|-------|--------------|
| **Schema MongoDB** | ⭐⭐ Baixa | 1 dia | Nenhuma |
| **Backend CRUD** | ⭐⭐⭐ Média | 2 dias | FastAPI |
| **IA: Criar Leads** | ⭐⭐⭐⭐ Alta | 2 dias | Claude Tool Use |
| **IA: Mover Leads** | ⭐⭐⭐⭐ Alta | 2 dias | Lógica de regras |
| **IA: Scoring** | ⭐⭐⭐ Média | 1 dia | Algoritmo |
| **Frontend: Kanban** | ⭐⭐⭐⭐ Alta | 3 dias | dnd-kit, CSS |
| **Frontend: Detalhe** | ⭐⭐ Baixa | 1 dia | React |
| **Realtime Sync** | ⭐⭐⭐ Média | 1 dia | Supabase |
| **Config Pipeline** | ⭐⭐⭐ Média | 2 dias | Form builder |
| **Testes** | ⭐⭐ Baixa | 1 dia | QA manual |

**TOTAL: 16 dias**

Mas com paralelização (backend + frontend simultâneo):
**REAL: 10-12 dias**

---

## 💰 IMPACTO NO PRICING

Com CRM integrado, o valor percebido explode:

### **NOVO PRICING:**

| Plano | Antes | **DEPOIS** | Diferença |
|-------|-------|-----------|-----------|
| **STARTER** | $29/mês | **$49/mês** | +69% |
| **PRO** | $79/mês | **$99/mês** | +25% |
| **ENTERPRISE** | $199/mês | **$249/mês** | +25% |

### **JUSTIFICATIVA:**

**Com CRM você compete com:**
- HubSpot Sales Hub: $45-500/mês
- Pipedrive: $14-99/mês
- Salesforce: $25-300/mês

**AgentFlow oferece:**
- ✅ CRM completo
- ✅ Kanban visual
- ✅ IA move leads automaticamente
- ✅ + Chatbot omnichannel
- ✅ + Multimodal (voz/imagem)
- ✅ + Multi-agente
- ✅ Tudo por $49-99/mês

**Valor real:** $150-300/mês (CRM $50 + Chatbot $100)  
**Cobrado:** $49-99/mês  
**Percepção:** 🔥 Bargain absoluto

---

## 🎯 INTEGRAÇÃO NO CRONOGRAMA

### **OPÇÃO A: Adicionar como FASE 6 (recomendado)**

```
FASE 0: Fundação (5d)
FASE 1: WhatsApp + Multi-idioma (8d)
FASE 2: IA Multimodal + Multi-agente (15d)
FASE 3: Omnichannel (15d)
FASE 4: Dashboard + Sync (12d)
FASE 5: Nutrição de Leads (10d)
+ FASE 6: CRM Kanban (10d) ← NOVA

TOTAL: 75 dias (~15 semanas / 3.5 meses)
```

**Vantagem:** Lança MVP sem CRM (valida mercado), adiciona CRM depois baseado em feedback.

---

### **OPÇÃO B: MVP com CRM desde o início**

```
FASE 0: Fundação (5d)
FASE 1: WhatsApp + Multi-idioma + CRM (18d) ← Inclui CRM
FASE 2: IA Multimodal + Multi-agente (15d)
FASE 3: Dashboard (8d) ← Simplificado
FASE 4: Omnichannel (15d)

TOTAL: 61 dias (~12 semanas / 3 meses)
```

**Vantagem:** Lança direto como "plataforma completa", mais impressionante.

---

## ✅ MINHA RECOMENDAÇÃO FINAL

### **IR COM OPÇÃO A (CRM na FASE 6) PORQUE:**

1. **MVP mais rápido**
   - Lança em 45 dias sem CRM
   - Valida chatbot + IA multimodal primeiro
   - Adiciona CRM depois se clientes pedirem

2. **Reduz risco**
   - CRM é complexo, pode ter bugs
   - Melhor iterar com clientes reais
   - Feedback guia features do CRM

3. **Priorização inteligente**
   - Chatbot + IA = diferencial imediato
   - CRM = nice to have, não blocker
   - Pode usar integração temporária (Zapier → HubSpot)

4. **Cashflow**
   - Cobra $29-79/mês desde dia 45
   - Quando adicionar CRM (dia 75), aumenta preço → upsell
   - ROI mais rápido

---

## 📊 RESUMO EXECUTIVO: CRM FEATURE

**O QUE É:**
- Kanban visual com drag-and-drop
- IA cria leads automaticamente das conversas
- IA move leads entre estágios baseado em regras
- Score 0-100 calculado em tempo real
- Configurável (automático ou manual)

**COMPLEXIDADE:** ⭐⭐⭐⭐ Alta

**TEMPO:** 10-12 dias (paralelo)

**VALOR AGREGADO:** 🔥🔥🔥🔥🔥 ENORME
- Transforma AgentFlow em HubSpot killer
- Elimina necessidade de CRM externo
- IA como CRM manager

**PREÇO:** +$20/mês por plano

**QUANDO:** FASE 6 (após MVP) - Recomendado

---

## ❓ DECISÃO: O QUE VOCÊ PREFERE?

### **1. Cronograma:**
- [ ] **Opção A:** CRM na FASE 6 (lança MVP em 45d, CRM em +10d) ← Recomendado
- [ ] **Opção B:** CRM desde o início (lança tudo em 61d)

### **2. Features do CRM:**
- [ ] Kanban básico (criar, mover, visualizar)
- [ ] Kanban completo (+ scoring, + automação IA, + regras configuráveis)

### **3. Começar desenvolvimento:**
- [ ] SIM, aprovar CRM e começar
- [ ] NÃO, focar no MVP sem CRM primeiro

---

**O que você acha dessa feature? Quer incluir?** 🚀
