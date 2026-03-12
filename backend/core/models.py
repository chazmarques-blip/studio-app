from pydantic import BaseModel
from typing import Optional, List


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    ui_language: Optional[str] = None


class SignUpRequest(BaseModel):
    email: str
    password: str
    full_name: str
    company_name: Optional[str] = None


class SignInRequest(BaseModel):
    email: str
    password: str


class TenantCreate(BaseModel):
    name: str
    slug: Optional[str] = None


class AgentCreate(BaseModel):
    name: str
    type: str
    description: Optional[str] = ""
    system_prompt: Optional[str] = ""
    personality: Optional[dict] = {}
    ai_config: Optional[dict] = {}
    tone: Optional[str] = "professional"
    emoji_level: Optional[str] = "low"
    verbosity_level: Optional[str] = "balanced"
    escalation_rules: Optional[dict] = {}
    follow_up_config: Optional[dict] = {}
    knowledge_instructions: Optional[str] = ""
    marketplace_template_id: Optional[str] = None
    language_mode: Optional[str] = "auto_detect"
    fixed_language: Optional[str] = "pt"


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    personality: Optional[dict] = None
    ai_config: Optional[dict] = None
    tone: Optional[str] = None
    emoji_level: Optional[float] = None
    verbosity_level: Optional[float] = None
    escalation_rules: Optional[dict] = None
    follow_up_config: Optional[dict] = None
    knowledge_instructions: Optional[str] = None
    personality_config: Optional[dict] = None
    integrations_config: Optional[dict] = None
    channel_config: Optional[dict] = None
    status: Optional[str] = None


class KnowledgeCreate(BaseModel):
    agent_id: str
    type: str
    title: str
    content: str


class FollowUpRuleCreate(BaseModel):
    agent_id: str
    trigger_type: str
    delay_hours: int
    message_template: str
    is_active: Optional[bool] = True


class DeployAgentRequest(BaseModel):
    template_name: str
    custom_name: Optional[str] = None
    tone: Optional[str] = "professional"
    emoji_level: Optional[str] = "low"
    verbosity_level: Optional[str] = "balanced"


class ChannelCreate(BaseModel):
    type: str
    config: Optional[dict] = {}


class ConversationCreate(BaseModel):
    channel_id: Optional[str] = None
    agent_id: Optional[str] = None
    contact_name: str
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    channel_type: Optional[str] = "whatsapp"


class MessageCreate(BaseModel):
    content: str
    message_type: Optional[str] = "text"
    metadata: Optional[dict] = None


class LeadCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    stage: Optional[str] = "new"
    score: Optional[int] = 0
    value: Optional[float] = 0.0
    conversation_id: Optional[str] = None


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    stage: Optional[str] = None
    score: Optional[int] = None
    value: Optional[float] = None
    ai_analysis: Optional[str] = None


class WhatsAppInstanceCreate(BaseModel):
    api_url: str
    api_key: str
    instance_name: str


class WhatsAppSendMessage(BaseModel):
    phone_number: str
    message: str
    instance_name: Optional[str] = None


class SandboxChatRequest(BaseModel):
    content: str
    agent_name: Optional[str] = "Carol"
    agent_type: Optional[str] = "sales"
    system_prompt: Optional[str] = None
    session_id: Optional[str] = None



class TelegramSetupRequest(BaseModel):
    agent_id: str
    bot_token: str
