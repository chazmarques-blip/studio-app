# 🚀 AGENTFLOW - ESCOPO EXPANDIDO E DETALHAMENTO TÉCNICO
## Análise Completa dos Novos Requisitos + Arquitetura

---

## 📋 RESUMO EXECUTIVO

Analisei todos os novos requisitos que você adicionou. São **features avançadas e diferenciadores de mercado** que transformam o AgentFlow de um "chatbot automatizado" para uma **plataforma omnichannel de inteligência artificial multimodal**.

### **NOVOS REQUISITOS IDENTIFICADOS:**

1. ✅ **Multi-idiomas** (detecção automática + escolha manual)
2. ✅ **Múltiplas redes sociais** (Instagram, Facebook, Telegram, etc)
3. ✅ **Edição em tempo real** (hot reload de configurações)
4. ✅ **Multimodal** (voz + imagens além de texto)
5. ✅ **Multi-agente em um atendimento** (orquestração complexa)
6. ✅ **Sincronização tempo real** (agendas, produtos, estoque)
7. ✅ **Sistema de nutrição de leads** (recuperação, reengajamento)
8. ✅ **Auto-save** (persistência automática de configurações)

### **IMPACTO NO PROJETO:**

| Aspecto | Antes | Depois | Impacto |
|---------|-------|--------|---------|
| **Complexidade** | Média | Alta | +60% |
| **Tempo MVP** | 40 dias | 60-75 dias | +50% |
| **Integrações** | 3 (WhatsApp, Claude, Supabase) | 10+ (multi-canal, multi-modal) | +233% |
| **Diferenciação** | Boa | **Excelente** | 🔥 |
| **Valor percebido** | $19/mês | $29-49/mês | +100% |

### **VEREDITO: VALE A PENA? 🎯**

✅ **SIM, 100%!** Essas features transformam o AgentFlow em um **produto único no mercado**. Nenhum concorrente tem tudo isso junto:
- ManyChat → não tem IA real + não tem voz/imagem
- Typebot → não tem multi-agente + não tem nutrição
- Tidio → não tem multi-idioma nativo + não tem omnichannel completo

**AgentFlow seria o PRIMEIRO a ter:**
1. IA multimodal (texto + voz + imagem)
2. Multi-agente com transição suave
3. Omnichannel (WhatsApp + Instagram + Facebook + Telegram)
4. Nutrição de leads com IA
5. Edição em tempo real (hot reload)

---

## 🔍 ANÁLISE DETALHADA DE CADA REQUISITO

---

## 1️⃣ MULTI-IDIOMAS (Detecção Automática + Escolha Manual)

### **O QUE VOCÊ QUER:**
- Agente detecta automaticamente o idioma do cliente
- Ou permite escolha manual (ex: bandeiras 🇧🇷 🇺🇸 🇪🇸)
- Agente responde no mesmo idioma do cliente
- Suporte inicial: PT-BR, EN, ES (expandir depois)

### **COMO IMPLEMENTAR:**

#### **Detecção Automática (Método Híbrido - Best Practice 2025)**
```python
# Backend: /api/agents/detect_language.py
from langdetect import detect_langs
import fasttext  # Facebook AI Research

def detect_language(text: str, conversation_id: str):
    """
    1. Verifica se já há idioma salvo no contexto da conversa
    2. Se não, detecta via FastText (95% accuracy)
    3. Confirma com langdetect (fallback)
    4. Salva no conversations.language
    """
    
    # Busca contexto
    conv = await db.conversations.find_one({"id": conversation_id})
    
    if conv.get("language"):
        return conv["language"]  # Já detectado antes
    
    # Detecção via FastText
    model = fasttext.load_model('lid.176.bin')  # 176 idiomas
    predictions = model.predict(text, k=3)  # Top 3 mais prováveis
    
    primary_language = predictions[0][0].replace('__label__', '')
    confidence = predictions[1][0]
    
    # Confirma se confiança > 80%
    if confidence > 0.8:
        # Salva no banco
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$set": {"language": primary_language, "language_confidence": confidence}}
        )
        return primary_language
    
    # Fallback: langdetect
    fallback = detect_langs(text)[0].lang
    return fallback
```

#### **Escolha Manual (Frontend)**
```jsx
// Componente: LanguageSwitcher.jsx
const LanguageSwitcher = ({ conversationId, currentLanguage }) => {
  const languages = [
    { code: 'pt', flag: '🇧🇷', name: 'Português' },
    { code: 'en', flag: '🇺🇸', name: 'English' },
    { code: 'es', flag: '🇪🇸', name: 'Español' },
  ];

  const handleChange = async (langCode) => {
    await axios.post(`/api/conversations/${conversationId}/language`, {
      language: langCode,
      manual_override: true
    });
    // Realtime update via Supabase
  };

  return (
    <div className="language-switcher">
      {languages.map(lang => (
        <button 
          key={lang.code}
          className={currentLanguage === lang.code ? 'active' : ''}
          onClick={() => handleChange(lang.code)}
        >
          {lang.flag} {lang.name}
        </button>
      ))}
    </div>
  );
};
```

#### **Agente Responde no Idioma Certo**
```python
# Ao chamar Claude API
system_prompt = f"""
Você é {agent.name}, assistente da {company}.
IMPORTANTE: Responda SEMPRE em {conversation.language}.
Se o cliente escrever em outro idioma, detecte e mude para esse idioma.

{agent.base_prompt}
"""

response = anthropic.messages.create(
    model="claude-3-5-sonnet-20250514",
    system=system_prompt,
    messages=context_messages
)
```

### **SCHEMA ATUALIZADO:**
```javascript
// conversations collection
{
  id: "uuid",
  language: "pt",  // ISO 639-1 code
  language_confidence: 0.95,  // Confiança da detecção
  language_detection_method: "auto" | "manual",
  language_history: ["pt", "en"],  // Se cliente mudar de idioma
  // ... resto dos campos
}
```

### **COMPLEXIDADE:** ⭐⭐⭐ Média
### **TEMPO:** 3-4 dias
### **DEPENDÊNCIAS:** 
- `fasttext` (biblioteca Python)
- `langdetect` (fallback)
- Modelo pré-treinado (176 idiomas, 150MB)

---

## 2️⃣ MÚLTIPLAS REDES SOCIAIS (Omnichannel)

### **O QUE VOCÊ QUER:**
- WhatsApp (já planejado)
- Instagram Direct Messages
- Facebook Messenger
- Telegram
- SMS (futuro)
- Tudo em uma única inbox unificada

### **COMO IMPLEMENTAR:**

#### **Arquitetura Omnichannel**
```
┌─────────────────────────────────────────────┐
│           UNIFIED INBOX (Frontend)          │
│  Todas as conversas de todos os canais      │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│      MESSAGE ROUTER (Backend FastAPI)       │
│  Normaliza mensagens de todos os canais     │
└─────────────────────────────────────────────┘
         ↓          ↓          ↓          ↓
   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │WhatsApp │ │Instagram│ │Facebook │ │Telegram │
   │Evolution│ │  Graph  │ │  Graph  │ │Bot API  │
   │  API    │ │   API   │ │   API   │ │         │
   └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

#### **Schema Unificado de Mensagens**
```javascript
// messages collection (normalizado)
{
  id: "uuid",
  conversation_id: "uuid",
  channel: "whatsapp" | "instagram" | "facebook" | "telegram",
  channel_message_id: "msg_123abc",  // ID original do canal
  sender: {
    id: "user_id_no_canal",
    name: "João Silva",
    username: "@joaosilva",  // Se aplicável
    channel_profile_url: "https://instagram.com/joaosilva"
  },
  content: {
    type: "text" | "image" | "video" | "audio" | "document",
    text: "Mensagem aqui",
    media_url: "https://...",  // Se for mídia
    media_type: "image/jpeg"
  },
  direction: "inbound" | "outbound",
  timestamp: "2025-12-15T14:30:00Z",
  status: "sent" | "delivered" | "read" | "failed",
  
  // Metadata específica do canal
  channel_metadata: {
    instagram_story_reply: true,  // Se for resposta de story
    telegram_message_type: "private",
    whatsapp_context_message_id: "..."  // Se for resposta
  }
}
```

#### **Conectores por Canal**

##### **1. WhatsApp (Evolution API v2)**
```python
# /backend/connectors/whatsapp.py
class WhatsAppConnector:
    async def receive_webhook(self, payload):
        # Já implementado na FASE 1
        pass
    
    async def send_message(self, conversation_id, content):
        # POST para Evolution API
        pass
```

##### **2. Instagram DM (Meta Graph API)**
```python
# /backend/connectors/instagram.py
class InstagramConnector:
    async def setup_webhook(self, page_id, access_token):
        """
        1. Criar app no Meta Developers
        2. Solicitar permissões: instagram_basic, instagram_manage_messages
        3. Configurar webhook URL
        """
        webhook_url = f"{BACKEND_URL}/api/webhooks/instagram"
        
        response = requests.post(
            f"https://graph.facebook.com/v21.0/{page_id}/subscribed_apps",
            params={
                "subscribed_fields": "messages,messaging_postbacks,message_reactions",
                "access_token": access_token
            }
        )
        return response.json()
    
    async def receive_webhook(self, payload):
        """
        Normaliza webhook do Instagram para formato unificado
        """
        entry = payload["entry"][0]
        messaging = entry["messaging"][0]
        
        # Normaliza para schema universal
        normalized = {
            "channel": "instagram",
            "channel_message_id": messaging["message"]["mid"],
            "sender": {
                "id": messaging["sender"]["id"],
                "name": await self.get_user_name(messaging["sender"]["id"])
            },
            "content": {
                "type": "text" if "text" in messaging["message"] else "image",
                "text": messaging["message"].get("text", "")
            }
        }
        
        # Salva no banco
        await save_message(normalized)
    
    async def send_message(self, recipient_id, text):
        response = requests.post(
            "https://graph.facebook.com/v21.0/me/messages",
            params={"access_token": self.access_token},
            json={
                "recipient": {"id": recipient_id},
                "message": {"text": text}
            }
        )
        return response.json()
```

##### **3. Facebook Messenger (Meta Graph API)**
```python
# /backend/connectors/facebook.py
class FacebookMessengerConnector:
    # Muito similar ao Instagram
    # Usa mesma Graph API com endpoints diferentes
    pass
```

##### **4. Telegram (Bot API)**
```python
# /backend/connectors/telegram.py
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters

class TelegramConnector:
    async def setup_bot(self, bot_token):
        """
        1. Criar bot via @BotFather
        2. Configurar webhook
        """
        bot = Bot(token=bot_token)
        
        await bot.set_webhook(
            url=f"{BACKEND_URL}/api/webhooks/telegram",
            allowed_updates=["message", "callback_query"]
        )
    
    async def receive_webhook(self, update_data):
        update = Update.de_json(update_data, bot)
        message = update.message
        
        # Normaliza
        normalized = {
            "channel": "telegram",
            "channel_message_id": str(message.message_id),
            "sender": {
                "id": str(message.from_user.id),
                "name": message.from_user.full_name,
                "username": f"@{message.from_user.username}"
            },
            "content": {
                "type": "text" if message.text else "photo",
                "text": message.text or message.caption or ""
            }
        }
        
        await save_message(normalized)
    
    async def send_message(self, chat_id, text):
        await self.bot.send_message(chat_id=chat_id, text=text)
```

#### **Message Router (Unified Handler)**
```python
# /backend/services/message_router.py
class MessageRouter:
    def __init__(self):
        self.connectors = {
            "whatsapp": WhatsAppConnector(),
            "instagram": InstagramConnector(),
            "facebook": FacebookMessengerConnector(),
            "telegram": TelegramConnector()
        }
    
    async def route_inbound(self, channel: str, payload: dict):
        """
        Recebe mensagem de qualquer canal e normaliza
        """
        connector = self.connectors[channel]
        normalized_message = await connector.receive_webhook(payload)
        
        # Identifica ou cria conversa
        conversation = await self.get_or_create_conversation(
            channel=channel,
            sender_id=normalized_message["sender"]["id"]
        )
        
        # Salva mensagem
        await db.messages.insert_one({
            **normalized_message,
            "conversation_id": conversation["id"]
        })
        
        # Envia para fila de processamento
        await redis.lpush("message_queue", json.dumps({
            "conversation_id": conversation["id"],
            "message_id": normalized_message["id"]
        }))
    
    async def route_outbound(self, conversation_id: str, content: dict):
        """
        Envia resposta pelo canal correto
        """
        conversation = await db.conversations.find_one({"id": conversation_id})
        channel = conversation["channel"]
        
        connector = self.connectors[channel]
        await connector.send_message(
            recipient_id=conversation["channel_user_id"],
            content=content
        )
```

#### **Frontend: Unified Inbox**
```jsx
// ConversationList.jsx (atualizado)
const ConversationList = () => {
  const conversations = useRealtimeConversations();  // Todas as redes
  
  return (
    <div className="conversation-list">
      {conversations.map(conv => (
        <ConversationCard 
          key={conv.id}
          conversation={conv}
          channelIcon={getChannelIcon(conv.channel)}  // WhatsApp, Instagram, etc
        />
      ))}
    </div>
  );
};

const getChannelIcon = (channel) => {
  const icons = {
    whatsapp: "💬",
    instagram: "📷",
    facebook: "👤",
    telegram: "✈️"
  };
  return icons[channel] || "💬";
};
```

#### **Tela de Configuração: Conectar Redes**
```jsx
// Settings > Integrações
<div className="channel-connections">
  <ChannelCard 
    channel="whatsapp"
    status="connected"
    phone="+55 11 98765-4321"
    onDisconnect={handleDisconnectWhatsApp}
  />
  
  <ChannelCard 
    channel="instagram"
    status="disconnected"
    onConnect={() => window.open('/auth/instagram')}  // OAuth
  />
  
  <ChannelCard 
    channel="facebook"
    status="disconnected"
    onConnect={() => window.open('/auth/facebook')}
  />
  
  <ChannelCard 
    channel="telegram"
    status="disconnected"
    onConnect={handleConnectTelegram}  // Modal com bot token
  />
</div>
```

### **COMPLEXIDADE:** ⭐⭐⭐⭐⭐ Muito Alta
### **TEMPO:** 12-15 dias (todos os canais)
- WhatsApp: 3 dias (já planejado)
- Instagram: 4 dias (OAuth + webhooks)
- Facebook: 3 dias (similar ao Instagram)
- Telegram: 3 dias (bot setup)
- Unified Router: 2 dias

### **DEPENDÊNCIAS:**
- Meta Graph API (Instagram + Facebook)
- Telegram Bot API
- Evolution API v2 (WhatsApp)
- OAuth flows (Meta)

---

## 3️⃣ EDIÇÃO EM TEMPO REAL (Hot Reload)

### **O QUE VOCÊ QUER:**
- Editar nome, personalidade, prompt do agente
- Ver mudanças aplicadas IMEDIATAMENTE
- Próxima mensagem já usa nova configuração
- Sem necessidade de recarregar página ou reiniciar serviços

### **COMO IMPLEMENTAR:**

#### **Arquitetura: Config Cache + Realtime Sync**
```
┌─────────────────────────────────────────────┐
│      FRONTEND (Edita Agente)                │
│  ┌─────────────────────────────────┐        │
│  │ Nome: [Carol_______________]    │        │
│  │ Tom:  Formal ●─── Casual        │        │
│  │ [Salvar] ← Auto-save a cada 2s  │        │
│  └─────────────────────────────────┘        │
└─────────────────────────────────────────────┘
                ↓ POST /api/agents/:id
┌─────────────────────────────────────────────┐
│      BACKEND (Atualiza Banco + Cache)       │
│  1. Salva no MongoDB                        │
│  2. Invalida cache Redis                    │
│  3. Publica evento no Supabase Realtime     │
└─────────────────────────────────────────────┘
                ↓ Realtime Event
┌─────────────────────────────────────────────┐
│      AGENT PROCESSOR (Worker)               │
│  Ouve evento → Recarrega config do agente   │
│  Próxima mensagem usa nova configuração     │
└─────────────────────────────────────────────┘
```

#### **Implementação: Auto-Save com Debounce**
```jsx
// Frontend: AgentEditor.jsx
import { useDebounce } from 'use-debounce';

const AgentEditor = ({ agentId }) => {
  const [config, setConfig] = useState({});
  const [debouncedConfig] = useDebounce(config, 2000);  // 2s delay
  
  useEffect(() => {
    // Auto-save quando config mudar (após 2s sem editar)
    saveAgent(agentId, debouncedConfig);
  }, [debouncedConfig]);
  
  const saveAgent = async (id, data) => {
    await axios.patch(`/api/agents/${id}`, data);
    toast.success("Salvo automaticamente ✓");
  };
  
  return (
    <div>
      <input 
        value={config.name}
        onChange={(e) => setConfig({...config, name: e.target.value})}
        placeholder="Nome do agente"
      />
      
      <Slider 
        value={config.temperature}
        onChange={(val) => setConfig({...config, temperature: val})}
        min={0} max={1} step={0.1}
      />
      
      <textarea 
        value={config.system_prompt}
        onChange={(e) => setConfig({...config, system_prompt: e.target.value})}
      />
      
      <div className="save-indicator">
        {isSaving ? "Salvando..." : "✓ Salvo"}
      </div>
    </div>
  );
};
```

#### **Backend: Invalidação de Cache**
```python
# /backend/api/agents.py
from fastapi import APIRouter
import redis

router = APIRouter()
cache = redis.Redis(host='localhost', port=6379)

@router.patch("/agents/{agent_id}")
async def update_agent(agent_id: str, updates: dict):
    # 1. Atualiza no MongoDB
    result = await db.agents.update_one(
        {"id": agent_id},
        {"$set": {**updates, "updated_at": datetime.now()}}
    )
    
    # 2. Invalida cache Redis
    cache_key = f"agent_config:{agent_id}"
    cache.delete(cache_key)
    
    # 3. Publica evento no Supabase Realtime
    supabase.from_("agent_updates").insert({
        "agent_id": agent_id,
        "updated_fields": list(updates.keys()),
        "timestamp": datetime.now().isoformat()
    }).execute()
    
    return {"status": "updated", "agent_id": agent_id}
```

#### **Agent Processor: Recarrega Config em Tempo Real**
```python
# /backend/services/agent_processor.py
class AgentProcessor:
    def __init__(self):
        self.config_cache = {}
        
        # Subscribe to Supabase Realtime
        supabase.from_("agent_updates").on("INSERT", self.on_agent_update).subscribe()
    
    def on_agent_update(self, payload):
        """
        Callback quando agente é atualizado
        """
        agent_id = payload["new"]["agent_id"]
        print(f"♻️ Recarregando config do agente {agent_id}")
        
        # Remove do cache local
        if agent_id in self.config_cache:
            del self.config_cache[agent_id]
    
    async def get_agent_config(self, agent_id: str):
        """
        Busca config do agente (com cache)
        """
        cache_key = f"agent_config:{agent_id}"
        
        # Tenta Redis primeiro
        cached = cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Se não, busca no MongoDB
        agent = await db.agents.find_one({"id": agent_id})
        
        # Salva no Redis (TTL 5 min)
        cache.setex(cache_key, 300, json.dumps(agent))
        
        return agent
    
    async def process_message(self, conversation_id: str):
        conversation = await db.conversations.find_one({"id": conversation_id})
        agent_id = conversation["current_agent_id"]
        
        # Sempre busca config atualizada (cache ou banco)
        agent_config = await self.get_agent_config(agent_id)
        
        # Usa config para montar prompt
        system_prompt = self.build_prompt(agent_config)
        
        # Chama Claude
        response = await self.call_claude(system_prompt, context)
        
        # Envia resposta
        await self.send_response(conversation_id, response)
```

#### **Indicador Visual de Sincronização**
```jsx
// Frontend: Real-time Sync Indicator
const AgentSyncStatus = ({ agentId }) => {
  const [lastSync, setLastSync] = useState(null);
  
  useEffect(() => {
    // Subscribe to Supabase Realtime
    const subscription = supabase
      .from(`agent_updates:agent_id=eq.${agentId}`)
      .on('INSERT', (payload) => {
        setLastSync(new Date());
        toast.success("⚡ Alterações aplicadas!");
      })
      .subscribe();
    
    return () => subscription.unsubscribe();
  }, [agentId]);
  
  return (
    <div className="sync-status">
      {lastSync && (
        <span className="text-green-500">
          ✓ Sincronizado há {formatDistanceToNow(lastSync)}
        </span>
      )}
    </div>
  );
};
```

### **COMPLEXIDADE:** ⭐⭐⭐⭐ Alta
### **TEMPO:** 4-5 dias
### **DEPENDÊNCIAS:**
- Redis (cache)
- Supabase Realtime (pub/sub)
- React hooks (useDebounce)

---

## 4️⃣ MULTIMODAL (Voz + Imagens)

### **O QUE VOCÊ QUER:**
- Agente entende áudios (transcrição + resposta)
- Agente entende imagens (OCR, reconhecimento de objetos)
- Responde de acordo (ex: cliente manda foto de produto defeituoso)

### **COMO IMPLEMENTAR:**

#### **Fluxo: Mensagem com Áudio**
```
Cliente envia áudio no WhatsApp
    ↓
Evolution API webhook: type="audio"
    ↓
Backend baixa áudio → OpenAI Whisper (transcrição)
    ↓
Texto transcrito → Claude processa normalmente
    ↓
Claude responde em texto
    ↓
Opcional: Converte resposta em áudio (OpenAI TTS)
    ↓
Envia áudio de volta ao cliente
```

#### **Implementação: Transcrição de Áudio**
```python
# /backend/services/transcription.py
from openai import OpenAI

class TranscriptionService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def transcribe_audio(self, audio_url: str, language: str = None):
        """
        Transcreve áudio usando Whisper
        Suporta 30+ idiomas automaticamente
        """
        # 1. Baixa áudio
        audio_response = requests.get(audio_url)
        audio_file = io.BytesIO(audio_response.content)
        audio_file.name = "audio.ogg"  # WhatsApp usa OGG
        
        # 2. Transcreve com Whisper
        transcript = self.client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language,  # pt, en, es, etc (opcional)
            response_format="json"
        )
        
        return {
            "text": transcript.text,
            "language": transcript.language,
            "duration": transcript.duration
        }
```

#### **Webhook Handler para Áudio**
```python
# /backend/api/webhooks.py
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(payload: dict):
    message = payload["data"]
    
    if message["messageType"] == "audioMessage":
        # 1. Extrai URL do áudio
        audio_url = message["message"]["audioMessage"]["url"]
        
        # 2. Transcreve
        transcription_service = TranscriptionService()
        result = await transcription_service.transcribe_audio(audio_url)
        
        # 3. Salva mensagem com transcrição
        await db.messages.insert_one({
            "conversation_id": message["key"]["remoteJid"],
            "content": {
                "type": "audio",
                "audio_url": audio_url,
                "transcription": result["text"],  # ← Texto transcrito
                "duration": result["duration"]
            },
            "timestamp": datetime.now()
        })
        
        # 4. Processa como mensagem de texto normal
        await message_queue.enqueue({
            "conversation_id": message["key"]["remoteJid"],
            "text": result["text"]  # Claude recebe texto
        })
    
    return {"status": "ok"}
```

#### **Fluxo: Mensagem com Imagem**
```
Cliente envia imagem no WhatsApp
    ↓
Evolution API webhook: type="image"
    ↓
Backend baixa imagem → Claude Vision (análise)
    ↓
Claude extrai texto (OCR) + descreve conteúdo
    ↓
Responde baseado no contexto
```

#### **Implementação: Análise de Imagem**
```python
# /backend/services/vision.py
import anthropic

class VisionService:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
    
    async def analyze_image(self, image_url: str, context: str = ""):
        """
        Analisa imagem usando Claude Vision
        """
        # 1. Baixa imagem e converte para base64
        response = requests.get(image_url)
        image_base64 = base64.b64encode(response.content).decode()
        image_media_type = response.headers.get("Content-Type", "image/jpeg")
        
        # 2. Chama Claude com visão
        message = self.client.messages.create(
            model="claude-3-5-sonnet-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image_media_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": f"""
                        Analise esta imagem e responda:
                        
                        1. O que você vê na imagem?
                        2. Há texto visível? Se sim, transcreva.
                        3. Baseado no contexto: {context}, como devo responder?
                        
                        Seja específico e útil.
                        """
                    }
                ]
            }]
        )
        
        return {
            "analysis": message.content[0].text,
            "model": message.model
        }
```

#### **Webhook Handler para Imagem**
```python
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(payload: dict):
    message = payload["data"]
    
    if message["messageType"] == "imageMessage":
        image_url = message["message"]["imageMessage"]["url"]
        caption = message["message"]["imageMessage"].get("caption", "")
        
        # Busca contexto da conversa
        conversation = await db.conversations.find_one({
            "channel_user_id": message["key"]["remoteJid"]
        })
        
        context = f"""
        Conversa com: {conversation['customer_name']}
        Agente ativo: {conversation['current_agent_name']}
        Mensagem do cliente: {caption}
        """
        
        # Analisa imagem
        vision_service = VisionService()
        analysis = await vision_service.analyze_image(image_url, context)
        
        # Salva mensagem
        await db.messages.insert_one({
            "conversation_id": conversation["id"],
            "content": {
                "type": "image",
                "image_url": image_url,
                "caption": caption,
                "ai_analysis": analysis["analysis"]  # ← Análise do Claude
            }
        })
        
        # Envia para fila (Claude já analisou, só precisa responder)
        await message_queue.enqueue({
            "conversation_id": conversation["id"],
            "text": f"[Cliente enviou imagem: {analysis['analysis']}]"
        })
```

#### **Casos de Uso - Imagem:**
```
Exemplo 1: eCommerce
Cliente: [foto de vestido] "Tem na cor azul?"
→ Claude vê: "Vestido floral branco e rosa, modelo verão"
→ Responde: "Esse modelo lindo! Temos sim em azul, mas só nos tamanhos M e G. Quer que eu reserve?"

Exemplo 2: Suporte Técnico
Cliente: [print de erro] "Não consigo acessar"
→ Claude vê: "Tela de erro 404, URL: app.example.com/dashboard"
→ Responde: "Vi o erro 404. Você está tentando acessar o dashboard antigo. Use: app.example.com/novo-dashboard"

Exemplo 3: Restaurante
Cliente: [foto de prato] "Esse prato ainda tem?"
→ Claude vê: "Prato com frango grelhado, arroz e legumes"
→ Responde: "Sim! Nosso Frango Tropical (R$ 32). Quer pedir?"
```

### **COMPLEXIDADE:** ⭐⭐⭐⭐ Alta
### **TEMPO:** 6-7 dias
- Whisper (transcrição): 2 dias
- Claude Vision (imagem): 3 dias
- Integração end-to-end: 2 dias

### **DEPENDÊNCIAS:**
- OpenAI API (Whisper para áudio)
- Claude 3.5 Sonnet (Vision para imagens)
- Evolution API v2 (suporte a mídia)

---

## 5️⃣ MULTI-AGENTE EM UM ATENDIMENTO

### **O QUE VOCÊ QUER:**
- Cliente começa com SAC → transfere para Vendas → depois para Suporte
- Contexto preservado (cliente não repete dados)
- Transições suaves e naturais
- Agente sabe quando passar para outro

### **COMO IMPLEMENTAR:**

#### **Orquestração com Tool Use**
```python
# Claude Tool: switch_agent
tools = [
    {
        "name": "switch_agent",
        "description": "Transfere conversa para outro agente especializado",
        "input_schema": {
            "type": "object",
            "properties": {
                "target_agent": {
                    "type": "string",
                    "enum": ["sac", "vendas", "suporte", "agendamento"],
                    "description": "Agente de destino"
                },
                "reason": {
                    "type": "string",
                    "description": "Por que está transferindo"
                },
                "context_summary": {
                    "type": "string",
                    "description": "Resumo do que foi discutido até agora"
                }
            },
            "required": ["target_agent", "reason", "context_summary"]
        }
    }
]

# Agent Processor detecta tool use
if response.stop_reason == "tool_use":
    tool_use = response.content[1]  # Claude retornou tool_use
    
    if tool_use.name == "switch_agent":
        await handle_agent_switch(
            conversation_id=conversation_id,
            target_agent=tool_use.input["target_agent"],
            reason=tool_use.input["reason"],
            context=tool_use.input["context_summary"]
        )
```

#### **Handler de Transição**
```python
async def handle_agent_switch(
    conversation_id: str,
    target_agent: str,
    reason: str,
    context: str
):
    """
    Executa transição entre agentes
    """
    conversation = await db.conversations.find_one({"id": conversation_id})
    previous_agent = conversation["current_agent_name"]
    
    # 1. Atualiza agente atual
    new_agent = await db.agents.find_one({"type": target_agent, "tenant_id": conversation["tenant_id"]})
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {
            "$set": {
                "current_agent_id": new_agent["id"],
                "current_agent_name": new_agent["name"],
                "updated_at": datetime.now()
            },
            "$push": {
                "agent_history": {
                    "agent_id": conversation["current_agent_id"],
                    "agent_name": previous_agent,
                    "switched_at": datetime.now(),
                    "reason": reason
                }
            }
        }
    )
    
    # 2. Atualiza contexto com resumo
    await db.conversations.update_one(
        {"id": conversation_id},
        {
            "$set": {
                f"context.handoff_context": context
            }
        }
    )
    
    # 3. Envia mensagem de transição (opcional)
    await send_transition_message(
        conversation_id=conversation_id,
        from_agent=previous_agent,
        to_agent=new_agent["name"],
        reason=reason
    )
    
    # 4. Notifica Realtime
    supabase.from_("conversation_updates").insert({
        "conversation_id": conversation_id,
        "event_type": "agent_switch",
        "from_agent": previous_agent,
        "to_agent": new_agent["name"],
        "timestamp": datetime.now().isoformat()
    }).execute()

async def send_transition_message(
    conversation_id: str,
    from_agent: str,
    to_agent: str,
    reason: str
):
    """
    Mensagem de transição (opcional, pode ser silencioso)
    """
    message = f"Vou te passar para {to_agent}, que é especialista nisso! Um momento 😊"
    
    await db.messages.insert_one({
        "conversation_id": conversation_id,
        "content": {"type": "text", "text": message},
        "sender": "agent",
        "sender_name": from_agent,
        "is_system_message": True,  # Marca como mensagem de sistema
        "timestamp": datetime.now()
    })
    
    # Envia via canal
    await message_router.route_outbound(conversation_id, {"text": message})
```

#### **Exemplo de Fluxo Multi-Agente**
```
Cliente: "Oi, quero comprar um vestido"
→ SAC: "Olá! Vou te passar para nossa especialista em vendas 😊"
→ [TROCA AUTOMÁTICA PARA VENDAS]

Vendas: "Oi! Sou a Carol. Qual estilo você procura?"
Cliente: "Algo para festa"
Vendas: "Lindo! Temos esses 3 modelos [fotos]"
Cliente: "Gostei do 2. Mas tá com defeito quando chega?"
→ Vendas detecta dúvida técnica: "Sobre garantia/defeito"
→ [TROCA AUTOMÁTICA PARA SUPORTE]

Suporte: "Oi! Sou o Roberto, especialista em pós-venda."
Suporte: "Nossos produtos têm garantia de 30 dias. Se chegar com defeito, trocamos imediatamente."
Cliente: "Ah, ok. Então vou levar!"
→ Suporte detecta fechamento: "Cliente decidiu comprar"
→ [VOLTA PARA VENDAS]

Vendas: "Ótimo! Qual tamanho?"
[... finaliza venda ...]
```

#### **Schema: Histórico de Agentes**
```javascript
// conversations collection
{
  id: "uuid",
  current_agent_id: "agent_vendas_123",
  current_agent_name: "Carol",
  
  agent_history: [
    {
      agent_id: "agent_sac_456",
      agent_name: "Roberto",
      started_at: "2025-12-15T14:00:00Z",
      ended_at: "2025-12-15T14:02:00Z",
      reason: "Cliente quer comprar → Vendas"
    },
    {
      agent_id: "agent_vendas_123",
      agent_name: "Carol",
      started_at: "2025-12-15T14:02:00Z",
      ended_at: "2025-12-15T14:05:00Z",
      reason: "Dúvida sobre garantia → Suporte"
    },
    {
      agent_id: "agent_suporte_789",
      agent_name: "Roberto",
      started_at: "2025-12-15T14:05:00Z",
      ended_at: "2025-12-15T14:06:00Z",
      reason: "Cliente decidiu comprar → Volta para Vendas"
    },
    {
      agent_id: "agent_vendas_123",
      agent_name: "Carol",
      started_at: "2025-12-15T14:06:00Z",
      ended_at: null,  // Agente atual
      reason: "Finalizar venda"
    }
  ],
  
  context: {
    customer_name: "Maria",
    intent: "compra",
    product_interest: "vestido festa",
    handoff_context: "Cliente quer vestido para festa, gostou do modelo 2, confirmou sobre garantia"
  }
}
```

### **COMPLEXIDADE:** ⭐⭐⭐⭐ Alta
### **TEMPO:** 5-6 dias
### **DEPENDÊNCIAS:**
- Claude Tool Use
- Contexto bem estruturado
- Lógica de transição

---

## 6️⃣ SINCRONIZAÇÃO TEMPO REAL (Agendas + Produtos)

### **O QUE VOCÊ QUER:**
- Agente consulta agenda real (Google Calendar, Outlook)
- Agente consulta estoque/produtos em tempo real
- Integração via API ou Google Sheets
- Sem dados defasados

### **COMO IMPLEMENTAR:**

#### **Integração: Google Calendar**
```python
# /backend/integrations/google_calendar.py
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class GoogleCalendarIntegration:
    async def get_available_slots(
        self,
        tenant_id: str,
        date: str,  # "2025-12-20"
        duration_minutes: int = 60
    ):
        """
        Busca horários disponíveis na agenda
        """
        # 1. Busca credenciais do tenant
        integration = await db.integrations.find_one({
            "tenant_id": tenant_id,
            "type": "google_calendar",
            "status": "active"
        })
        
        creds = Credentials.from_authorized_user_info(integration["credentials"])
        service = build('calendar', 'v3', credentials=creds)
        
        # 2. Busca eventos do dia
        time_min = f"{date}T00:00:00Z"
        time_max = f"{date}T23:59:59Z"
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # 3. Calcula slots disponíveis
        busy_times = [(e['start']['dateTime'], e['end']['dateTime']) for e in events]
        available_slots = self.calculate_free_slots(busy_times, date, duration_minutes)
        
        return available_slots
    
    def calculate_free_slots(self, busy_times, date, duration):
        """
        Calcula janelas livres entre 9h-18h
        """
        start = datetime.fromisoformat(f"{date}T09:00:00")
        end = datetime.fromisoformat(f"{date}T18:00:00")
        
        free_slots = []
        current = start
        
        while current + timedelta(minutes=duration) <= end:
            slot_end = current + timedelta(minutes=duration)
            
            # Verifica se slot está livre
            is_free = not any(
                self.overlaps(current, slot_end, busy_start, busy_end)
                for busy_start, busy_end in busy_times
            )
            
            if is_free:
                free_slots.append({
                    "start": current.strftime("%H:%M"),
                    "end": slot_end.strftime("%H:%M")
                })
            
            current += timedelta(minutes=30)  # Incremento de 30min
        
        return free_slots
    
    async def book_appointment(
        self,
        tenant_id: str,
        datetime_str: str,  # "2025-12-20T14:00:00"
        duration_minutes: int,
        customer_name: str,
        customer_phone: str,
        notes: str = ""
    ):
        """
        Cria evento na agenda
        """
        integration = await db.integrations.find_one({
            "tenant_id": tenant_id,
            "type": "google_calendar"
        })
        
        creds = Credentials.from_authorized_user_info(integration["credentials"])
        service = build('calendar', 'v3', credentials=creds)
        
        start_time = datetime.fromisoformat(datetime_str)
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': f'Consulta - {customer_name}',
            'description': f'Cliente: {customer_name}\nTelefone: {customer_phone}\n\n{notes}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'America/Sao_Paulo',
            },
            'attendees': [
                {'email': customer_phone + '@whatsapp.com'}  # Fake email
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 24 * 60},  # 1 dia antes
                    {'method': 'popup', 'minutes': 60},  # 1h antes
                ],
            },
        }
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        
        return {
            "event_id": created_event['id'],
            "link": created_event.get('htmlLink')
        }
```

#### **Tool Use: Consultar e Agendar**
```python
# Claude Tools para agendamento
tools = [
    {
        "name": "check_availability",
        "description": "Consulta horários disponíveis na agenda",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "duration_minutes": {"type": "integer", "default": 60}
            },
            "required": ["date"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Agenda horário para o cliente",
        "input_schema": {
            "type": "object",
            "properties": {
                "datetime": {"type": "string", "description": "Data e hora YYYY-MM-DDTHH:MM"},
                "customer_name": {"type": "string"},
                "customer_phone": {"type": "string"},
                "service_type": {"type": "string"}
            },
            "required": ["datetime", "customer_name"]
        }
    }
]

# Handler
if tool_use.name == "check_availability":
    calendar = GoogleCalendarIntegration()
    slots = await calendar.get_available_slots(
        tenant_id=conversation["tenant_id"],
        date=tool_use.input["date"]
    )
    
    # Retorna para Claude
    tool_result = {
        "available_slots": slots,
        "message": f"Encontrei {len(slots)} horários disponíveis"
    }
```

#### **Integração: Produtos (Google Sheets)**
```python
# /backend/integrations/google_sheets.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class GoogleSheetsIntegration:
    async def get_products(self, tenant_id: str):
        """
        Busca produtos da planilha do cliente
        """
        # 1. Busca configuração
        integration = await db.integrations.find_one({
            "tenant_id": tenant_id,
            "type": "google_sheets",
            "purpose": "product_catalog"
        })
        
        sheet_id = integration["config"]["sheet_id"]
        
        # 2. Conecta na planilha
        scope = ['https://spreadsheets.google.com/feeds']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            integration["credentials"],
            scope
        )
        client = gspread.authorize(creds)
        
        # 3. Lê dados
        sheet = client.open_by_key(sheet_id).sheet1
        records = sheet.get_all_records()
        
        # 4. Normaliza formato
        products = []
        for row in records:
            products.append({
                "id": str(row.get("ID") or row.get("id")),
                "name": row.get("Nome") or row.get("name"),
                "price": float(row.get("Preço") or row.get("price") or 0),
                "stock": int(row.get("Estoque") or row.get("stock") or 0),
                "description": row.get("Descrição") or row.get("description"),
                "image_url": row.get("Imagem") or row.get("image")
            })
        
        return products
    
    async def search_products(self, tenant_id: str, query: str):
        """
        Busca produtos por nome/descrição
        """
        all_products = await self.get_products(tenant_id)
        
        query_lower = query.lower()
        matches = [
            p for p in all_products
            if query_lower in p["name"].lower() or query_lower in (p["description"] or "").lower()
        ]
        
        return matches
```

#### **Tool Use: Produtos**
```python
tools = [
    {
        "name": "search_products",
        "description": "Busca produtos no catálogo",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Termo de busca"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "check_stock",
        "description": "Verifica estoque de um produto",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"}
            },
            "required": ["product_id"]
        }
    }
]

# Handler
if tool_use.name == "search_products":
    sheets = GoogleSheetsIntegration()
    products = await sheets.search_products(
        tenant_id=conversation["tenant_id"],
        query=tool_use.input["query"]
    )
    
    tool_result = {
        "products": products[:5],  # Retorna top 5
        "total_found": len(products)
    }
```

### **COMPLEXIDADE:** ⭐⭐⭐⭐ Alta
### **TEMPO:** 6-7 dias
- Google Calendar: 3 dias
- Google Sheets: 2 dias
- Tool Use integration: 2 dias

### **DEPENDÊNCIAS:**
- Google Calendar API
- Google Sheets API
- gspread (Python library)

---

## 7️⃣ SISTEMA DE NUTRIÇÃO DE LEADS

### **O QUE VOCÊ QUER:**
- Recuperação automática de leads inativos
- Regras de follow-up (ex: "Se não respondeu em 24h, enviar lembrete")
- Campanhas de reengajamento
- Automação de manutenção de contato

### **COMO IMPLEMENTAR:**

#### **Arquitetura: Campaign Engine**
```
┌─────────────────────────────────────────────┐
│    CAMPAIGN MANAGER (Cron Jobs)             │
│  Roda a cada 1 hora, verifica regras        │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│    REGRAS DE NUTRIÇÃO                       │
│  • Lead não respondeu em 24h → Lembrete     │
│  • Carrinho abandonado → Desconto           │
│  • Cliente inativo 7 dias → Novidade        │
│  • Aniversário → Parabéns + cupom           │
└─────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────┐
│    MESSAGE SCHEDULER                        │
│  Enfileira mensagens para envio             │
└─────────────────────────────────────────────┘
                ↓
        Evolution API (envia)
```

#### **Schema: Campanhas**
```javascript
// campaigns collection
{
  id: "uuid",
  tenant_id: "uuid",
  name: "Recuperação Carrinho Abandonado",
  type: "abandoned_cart" | "inactive_lead" | "follow_up" | "birthday" | "custom",
  status: "active" | "paused" | "completed",
  
  trigger: {
    event: "cart_abandoned",  // Evento que dispara
    conditions: {
      time_elapsed_hours: 24,  // Após 24h
      cart_value_min: 50,  // Carrinho > R$ 50
      customer_segment: "engaged"  // Apenas leads engajados
    }
  },
  
  messages: [
    {
      delay_hours: 1,  // 1h após trigger
      template: "Oi {{name}}! Vi que você deixou itens no carrinho. Quer finalizar a compra? 😊",
      variables: ["name", "cart_total", "cart_items"]
    },
    {
      delay_hours: 24,  // 24h após trigger
      template: "{{name}}, preparei um desconto especial de 10% pra você! Use o cupom: VOLTA10",
      variables: ["name"]
    },
    {
      delay_hours: 72,  // 3 dias
      template: "Última chance! Seu carrinho expira em 24h. Garanta seus produtos antes que acabem!",
      variables: []
    }
  ],
  
  statistics: {
    triggered: 145,  // Quantas vezes disparou
    sent: 435,  // Total de mensagens enviadas (145 × 3)
    replied: 67,  // Quantos responderam
    converted: 23,  // Quantos compraram
    conversion_rate: 0.16  // 16%
  },
  
  created_at: "2025-12-01T00:00:00Z",
  updated_at: "2025-12-15T10:30:00Z"
}
```

#### **Schema: Execuções de Campanha**
```javascript
// campaign_executions collection
{
  id: "uuid",
  campaign_id: "uuid",
  conversation_id: "uuid",
  customer_name: "Maria Silva",
  
  triggered_at: "2025-12-15T14:00:00Z",
  trigger_reason: "Carrinho abandonado há 24h",
  
  messages_schedule: [
    {
      message_index: 0,
      scheduled_for: "2025-12-15T15:00:00Z",  // 1h depois
      status: "sent",
      sent_at: "2025-12-15T15:00:05Z",
      message_id: "msg_123"
    },
    {
      message_index: 1,
      scheduled_for: "2025-12-16T14:00:00Z",  // 24h depois
      status: "pending",
      sent_at: null,
      message_id: null
    },
    {
      message_index: 2,
      scheduled_for: "2025-12-18T14:00:00Z",  // 72h depois
      status: "cancelled",  // Cancelado pois cliente respondeu
      sent_at: null,
      message_id: null,
      cancelled_reason: "Cliente respondeu à mensagem 1"
    }
  ],
  
  outcome: {
    replied: true,
    reply_at: "2025-12-15T15:30:00Z",
    converted: true,  // Comprou
    converted_at: "2025-12-15T16:00:00Z",
    revenue: 127.50
  }
}
```

#### **Campaign Manager (Cron Job)**
```python
# /backend/services/campaign_manager.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class CampaignManager:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        
        # Roda a cada hora
        self.scheduler.add_job(
            self.process_campaigns,
            'cron',
            minute=0  # Todo início de hora
        )
        
        self.scheduler.start()
    
    async def process_campaigns(self):
        """
        Verifica todas as campanhas ativas e dispara se necessário
        """
        campaigns = await db.campaigns.find({"status": "active"}).to_list(None)
        
        for campaign in campaigns:
            await self.check_and_trigger_campaign(campaign)
    
    async def check_and_trigger_campaign(self, campaign: dict):
        """
        Verifica se campanha deve ser disparada
        """
        trigger = campaign["trigger"]
        
        if trigger["event"] == "abandoned_cart":
            await self.handle_abandoned_cart(campaign)
        elif trigger["event"] == "inactive_lead":
            await self.handle_inactive_lead(campaign)
        elif trigger["event"] == "follow_up":
            await self.handle_follow_up(campaign)
    
    async def handle_abandoned_cart(self, campaign: dict):
        """
        Busca carrinhos abandonados e dispara campanha
        """
        time_threshold = datetime.now() - timedelta(
            hours=campaign["trigger"]["conditions"]["time_elapsed_hours"]
        )
        
        # Busca conversas com carrinho abandonado
        conversations = await db.conversations.find({
            "tenant_id": campaign["tenant_id"],
            "context.cart_value": {"$gte": campaign["trigger"]["conditions"]["cart_value_min"]},
            "context.cart_abandoned_at": {"$lte": time_threshold},
            "context.cart_recovered": {"$ne": True},
            # Não enviar se já tem execução dessa campanha
            "id": {"$nin": await self.get_executed_conversation_ids(campaign["id"])}
        }).to_list(None)
        
        for conv in conversations:
            await self.trigger_campaign_for_conversation(campaign, conv)
    
    async def trigger_campaign_for_conversation(self, campaign: dict, conversation: dict):
        """
        Dispara campanha para uma conversa específica
        """
        # 1. Cria execução
        execution = {
            "id": str(uuid.uuid4()),
            "campaign_id": campaign["id"],
            "conversation_id": conversation["id"],
            "customer_name": conversation.get("customer_name", "Cliente"),
            "triggered_at": datetime.now(),
            "trigger_reason": f"Campanha: {campaign['name']}",
            "messages_schedule": []
        }
        
        # 2. Agenda mensagens
        for i, message_template in enumerate(campaign["messages"]):
            scheduled_time = datetime.now() + timedelta(hours=message_template["delay_hours"])
            
            execution["messages_schedule"].append({
                "message_index": i,
                "scheduled_for": scheduled_time,
                "status": "pending",
                "sent_at": None,
                "message_id": None
            })
        
        # 3. Salva execução
        await db.campaign_executions.insert_one(execution)
        
        # 4. Atualiza estatísticas
        await db.campaigns.update_one(
            {"id": campaign["id"]},
            {"$inc": {"statistics.triggered": 1}}
        )
    
    async def send_scheduled_messages(self):
        """
        Roda a cada 5 minutos, envia mensagens agendadas
        """
        now = datetime.now()
        
        # Busca execuções com mensagens pendentes
        executions = await db.campaign_executions.find({
            "messages_schedule": {
                "$elemMatch": {
                    "status": "pending",
                    "scheduled_for": {"$lte": now}
                }
            }
        }).to_list(None)
        
        for execution in executions:
            await self.send_execution_messages(execution)
    
    async def send_execution_messages(self, execution: dict):
        """
        Envia mensagens pendentes de uma execução
        """
        conversation = await db.conversations.find_one({"id": execution["conversation_id"]})
        campaign = await db.campaigns.find_one({"id": execution["campaign_id"]})
        
        for i, msg_schedule in enumerate(execution["messages_schedule"]):
            if msg_schedule["status"] != "pending":
                continue
            
            if datetime.fromisoformat(msg_schedule["scheduled_for"]) > datetime.now():
                continue  # Ainda não é hora
            
            # Verifica se cliente já respondeu (cancela resto da campanha)
            recent_messages = await db.messages.find({
                "conversation_id": conversation["id"],
                "direction": "inbound",
                "timestamp": {"$gte": execution["triggered_at"]}
            }).to_list(None)
            
            if recent_messages:
                # Cliente respondeu, cancela mensagens restantes
                await self.cancel_remaining_messages(execution["id"], i)
                break
            
            # Monta mensagem com variáveis
            message_text = campaign["messages"][i]["template"]
            variables = self.extract_variables(conversation, campaign["messages"][i]["variables"])
            
            for key, value in variables.items():
                message_text = message_text.replace(f"{{{{{key}}}}}", str(value))
            
            # Envia
            await message_router.route_outbound(
                conversation_id=conversation["id"],
                content={"text": message_text}
            )
            
            # Atualiza status
            await db.campaign_executions.update_one(
                {"id": execution["id"]},
                {
                    "$set": {
                        f"messages_schedule.{i}.status": "sent",
                        f"messages_schedule.{i}.sent_at": datetime.now()
                    }
                }
            )
            
            # Atualiza estatísticas
            await db.campaigns.update_one(
                {"id": campaign["id"]},
                {"$inc": {"statistics.sent": 1}}
            )
```

#### **Frontend: Criar Campanha**
```jsx
// CampaignBuilder.jsx
const CampaignBuilder = () => {
  const [campaign, setCampaign] = useState({
    name: "",
    type: "follow_up",
    trigger: {
      event: "no_reply",
      conditions: { time_elapsed_hours: 24 }
    },
    messages: [
      { delay_hours: 1, template: "" }
    ]
  });
  
  return (
    <div className="campaign-builder">
      <h2>Criar Campanha de Nutrição</h2>
      
      {/* Step 1: Tipo e Nome */}
      <div className="step">
        <label>Nome da Campanha:</label>
        <input 
          value={campaign.name}
          onChange={(e) => setCampaign({...campaign, name: e.target.value})}
          placeholder="Ex: Recuperação de Leads Inativos"
        />
        
        <label>Tipo:</label>
        <select 
          value={campaign.type}
          onChange={(e) => setCampaign({...campaign, type: e.target.value})}
        >
          <option value="abandoned_cart">Carrinho Abandonado</option>
          <option value="inactive_lead">Lead Inativo</option>
          <option value="follow_up">Follow-up Automático</option>
          <option value="birthday">Aniversário</option>
        </select>
      </div>
      
      {/* Step 2: Trigger */}
      <div className="step">
        <h3>Quando disparar?</h3>
        
        {campaign.type === "inactive_lead" && (
          <div>
            <label>Cliente sem responder há:</label>
            <input 
              type="number"
              value={campaign.trigger.conditions.time_elapsed_hours}
              onChange={(e) => setCampaign({
                ...campaign,
                trigger: {
                  ...campaign.trigger,
                  conditions: { time_elapsed_hours: parseInt(e.target.value) }
                }
              })}
            /> horas
          </div>
        )}
        
        {campaign.type === "abandoned_cart" && (
          <div>
            <label>Carrinho mínimo:</label>
            <input 
              type="number"
              placeholder="R$ 50"
            />
            
            <label>Tempo sem finalizar:</label>
            <input type="number" /> horas
          </div>
        )}
      </div>
      
      {/* Step 3: Mensagens */}
      <div className="step">
        <h3>Sequência de Mensagens</h3>
        
        {campaign.messages.map((msg, index) => (
          <div key={index} className="message-item">
            <label>Enviar após {msg.delay_hours}h:</label>
            <textarea 
              value={msg.template}
              onChange={(e) => {
                const newMessages = [...campaign.messages];
                newMessages[index].template = e.target.value;
                setCampaign({...campaign, messages: newMessages});
              }}
              placeholder="Oi {{name}}! Notei que você..."
            />
            
            <small>Variáveis disponíveis: {"{{name}}"}, {"{{cart_total}}"}</small>
          </div>
        ))}
        
        <button onClick={() => setCampaign({
          ...campaign,
          messages: [...campaign.messages, { delay_hours: 24, template: "" }]
        })}>
          + Adicionar Mensagem
        </button>
      </div>
      
      {/* Step 4: Ativar */}
      <button className="btn-primary" onClick={handleCreate}>
        Criar e Ativar Campanha
      </button>
    </div>
  );
};
```

### **COMPLEXIDADE:** ⭐⭐⭐⭐⭐ Muito Alta
### **TEMPO:** 8-10 dias
### **DEPENDÊNCIAS:**
- APScheduler (cron jobs)
- Redis (queue)
- Lógica complexa de triggers

---

## 8️⃣ AUTO-SAVE (Persistência Automática)

### **JÁ COBERTO NO ITEM 3** ✅

Edições em tempo real incluem auto-save automático com debounce de 2s.

---

## 📊 RESUMO GERAL: IMPACTO E PRIORIZAÇÃO

### **MATRIZ DE COMPLEXIDADE vs VALOR**

| Feature | Complexidade | Valor p/ Usuário | Diferencial Mercado | Prioridade | Tempo |
|---------|--------------|------------------|---------------------|------------|-------|
| **Multi-idiomas** | ⭐⭐⭐ Média | ⭐⭐⭐⭐⭐ Muito Alto | ⭐⭐⭐⭐ Alto | **P0 (MVP)** | 3-4d |
| **Omnichannel** | ⭐⭐⭐⭐⭐ Muito Alta | ⭐⭐⭐⭐⭐ Muito Alto | ⭐⭐⭐⭐⭐ Muito Alto | **P1 (Pós-MVP)** | 12-15d |
| **Edição Tempo Real** | ⭐⭐⭐⭐ Alta | ⭐⭐⭐⭐ Alto | ⭐⭐⭐ Médio | **P0 (MVP)** | 4-5d |
| **Multimodal (Voz+Img)** | ⭐⭐⭐⭐ Alta | ⭐⭐⭐⭐⭐ Muito Alto | ⭐⭐⭐⭐⭐ Muito Alto | **P0 (MVP)** | 6-7d |
| **Multi-agente** | ⭐⭐⭐⭐ Alta | ⭐⭐⭐⭐⭐ Muito Alto | ⭐⭐⭐⭐ Alto | **P0 (MVP)** | 5-6d |
| **Sync Tempo Real** | ⭐⭐⭐⭐ Alta | ⭐⭐⭐⭐ Alto | ⭐⭐⭐ Médio | **P1 (Pós-MVP)** | 6-7d |
| **Nutrição de Leads** | ⭐⭐⭐⭐⭐ Muito Alta | ⭐⭐⭐⭐ Alto | ⭐⭐⭐⭐ Alto | **P2 (Futuro)** | 8-10d |

### **NOVO CRONOGRAMA (Adaptado)**

#### **FASE 0: FUNDAÇÃO (5 dias)**
- Setup projeto + banco + auth
- Infraestrutura base

#### **FASE 1: WHATSAPP + MULTI-IDIOMA (8 dias)**
- WhatsApp conectado (Evolution API)
- Detecção automática de idioma
- Backend configurado

#### **FASE 2: IA MULTIMODAL + MULTI-AGENTE (15 dias)**
- Claude respondendo (texto)
- **Voz** (Whisper transcrição)
- **Imagens** (Claude Vision)
- Multi-agente com tool use
- Edição tempo real (hot reload)

#### **FASE 3: OMNICHANNEL (15 dias)**
- Instagram DM
- Facebook Messenger
- Telegram
- Unified Inbox

#### **FASE 4: DASHBOARD + SINCRONIZAÇÃO (12 dias)**
- UI mobile completa
- Google Calendar integration
- Google Sheets integration
- Analytics

#### **FASE 5: NUTRIÇÃO DE LEADS (10 dias)**
- Campaign Manager
- Regras de automação
- Follow-up automático

**TOTAL: 65 dias (~13 semanas / 3 meses)**

---

## 💰 NOVO PRICING (Justificado)

Com essas features, o AgentFlow vale muito mais:

### **PLANOS ATUALIZADOS:**

#### **STARTER:** $29/mês
- 3 agentes
- 10k mensagens/mês
- **2 canais** (WhatsApp + 1 outro)
- Multi-idioma (3 idiomas)
- Voz + Imagens
- Sync básico (Sheets)

#### **PRO:** $79/mês
- 10 agentes
- 50k mensagens/mês
- **Todos os canais** (WhatsApp, Instagram, Facebook, Telegram)
- Multi-idioma ilimitado
- Voz + Imagens
- Sync avançado (Calendar + Sheets + APIs)
- **Nutrição de leads** (3 campanhas)

#### **ENTERPRISE:** $199/mês
- Agentes ilimitados
- Mensagens ilimitadas
- Todos os canais
- **Nutrição ilimitada**
- White label
- API access
- SLA 99.9%

---

## ✅ PRÓXIMA DECISÃO

**Preciso que você confirme:**

1. ✅ **Escopo aprovado?**
   - Todos os 8 requisitos fazem sentido?
   - Algo mais para adicionar?

2. 📅 **Cronograma ok?**
   - 65 dias (~3 meses) é viável?
   - Ou prefere MVP menor primeiro (45 dias sem omnichannel)?

3. 🔑 **Credenciais disponíveis?**
   - Claude API key
   - OpenAI API key (Whisper)
   - Supabase (URL + keys)
   - Railway (você sobe ou eu preparo?)

4. 🚦 **Começar pela FASE 1?**
   - WhatsApp + Multi-idioma (8 dias)
   - Ou quer ajustar algo antes?

**Me diga como quer prosseguir! 🚀**
