import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Sparkles, Bot, Loader2, RefreshCw, Rocket, ChevronDown, ChevronUp, Search, Globe, MessageSquare, Shield, Link2, Clock, Brain, Check } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { getErrorMsg } from '../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SEGMENTS = [
  { id: 'ecommerce', icon: '🛒', l: 'E-commerce' },
  { id: 'restaurant', icon: '🍽️', l: 'Restaurante' },
  { id: 'health', icon: '🏥', l: 'Saude' },
  { id: 'beauty', icon: '💇', l: 'Beleza' },
  { id: 'real_estate', icon: '🏠', l: 'Imobiliaria' },
  { id: 'automotive', icon: '🚗', l: 'Automotivo' },
  { id: 'education', icon: '📚', l: 'Educacao' },
  { id: 'finance', icon: '💰', l: 'Financeiro' },
  { id: 'travel', icon: '✈️', l: 'Turismo' },
  { id: 'fitness', icon: '🏋️', l: 'Fitness' },
  { id: 'legal', icon: '⚖️', l: 'Juridico' },
  { id: 'events', icon: '🎉', l: 'Eventos' },
  { id: 'saas', icon: '💻', l: 'SaaS' },
  { id: 'logistics', icon: '📦', l: 'Logistica' },
  { id: 'telecom', icon: '📱', l: 'Telecom' },
  { id: 'general', icon: '🏢', l: 'Outro' },
];

const OBJECTIVES = [
  { id: 'sales', l: 'Vender', d: 'Qualificar leads e fechar vendas' },
  { id: 'support', l: 'Suporte', d: 'Resolver problemas e tirar duvidas' },
  { id: 'scheduling', l: 'Agendar', d: 'Marcar consultas e reunioes' },
  { id: 'sac', l: 'SAC', d: 'Reclamacoes e devolucoes' },
  { id: 'onboarding', l: 'Onboarding', d: 'Boas-vindas e setup guiado' },
];

const TONES = [
  { id: 'professional', l: 'Profissional', ex: 'Bom dia. Como posso ajuda-lo?' },
  { id: 'friendly', l: 'Amigavel', ex: 'Oi! Que bom te ver! Como posso ajudar?' },
  { id: 'empathetic', l: 'Empatico', ex: 'Entendo sua situacao. Estou aqui pra ajudar!' },
  { id: 'direct', l: 'Direto', ex: 'Ola. Me diga o que precisa.' },
  { id: 'consultive', l: 'Consultivo', ex: 'Posso fazer algumas perguntas antes?' },
];

const MINDSETS = [
  { id: 'closer', l: 'Closer', d: 'Foco em fechar negocios' },
  { id: 'consultant', l: 'Consultor', d: 'Entende antes de sugerir' },
  { id: 'concierge', l: 'Concierge', d: 'Servico premium e proativo' },
  { id: 'educator', l: 'Educador', d: 'Ensina e constroi confianca' },
  { id: 'friend', l: 'Amigo', d: 'Casual e acolhedor' },
  { id: 'resolver', l: 'Resolvedor', d: 'Acao rapida e eficiente' },
  { id: 'nurturer', l: 'Cuidador', d: 'Relacionamento longo prazo' },
  { id: 'guardian', l: 'Guardiao', d: 'Cautelo e transparente' },
];

const LANGS = [
  { id: 'pt', l: 'Portugues', flag: '🇧🇷' },
  { id: 'en', l: 'English', flag: '🇺🇸' },
  { id: 'es', l: 'Espanol', flag: '🇪🇸' },
  { id: 'fr', l: 'Francais', flag: '🇫🇷' },
  { id: 'de', l: 'Deutsch', flag: '🇩🇪' },
  { id: 'it', l: 'Italiano', flag: '🇮🇹' },
  { id: 'auto', l: 'Auto-detectar', flag: '🌐' },
];

const INTEGRATIONS = [
  { id: 'google_calendar', l: 'Google Calendar', icon: '📅' },
  { id: 'google_sheets', l: 'Google Sheets', icon: '📊' },
  { id: 'whatsapp', l: 'WhatsApp', icon: '💬' },
  { id: 'email', l: 'Email', icon: '📧' },
  { id: 'crm', l: 'CRM Interno', icon: '🎯' },
  { id: 'webhook', l: 'Webhook/API', icon: '🔗' },
];

/* ── Collapsible Section ── */
function Section({ title, icon: Icon, children, defaultOpen = false, badge }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-[#1A1A1A] rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)} className="flex w-full items-center gap-2.5 px-3.5 py-3 text-left bg-[#0D0D0D] hover:bg-[#111] transition">
        <Icon size={15} className="text-[#C9A84C] shrink-0" />
        <span className="text-xs font-semibold text-white flex-1">{title}</span>
        {badge && <span className="rounded-full bg-[#C9A84C]/10 px-2 py-0.5 text-[8px] font-bold text-[#C9A84C]">{badge}</span>}
        {open ? <ChevronUp size={14} className="text-[#B0B0B0]" /> : <ChevronDown size={14} className="text-[#B0B0B0]" />}
      </button>
      {open && <div className="px-3.5 py-3 space-y-2.5 bg-[#0A0A0A]">{children}</div>}
    </div>
  );
}

/* ── Chip Selector ── */
function Chips({ items, value, onChange, multi = false, cols = 3 }) {
  const toggle = (id) => {
    if (multi) {
      const arr = value || [];
      onChange(arr.includes(id) ? arr.filter(x => x !== id) : [...arr, id]);
    } else {
      onChange(id);
    }
  };
  const isActive = (id) => multi ? (value || []).includes(id) : value === id;
  return (
    <div className={`grid gap-1.5 ${cols === 2 ? 'grid-cols-2' : cols === 4 ? 'grid-cols-4' : 'grid-cols-3'}`}>
      {items.map(item => (
        <button key={item.id} data-testid={`chip-${item.id}`} onClick={() => toggle(item.id)}
          className={`rounded-lg border px-2 py-2 text-left transition-all ${
            isActive(item.id)
              ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8'
              : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#2A2A2A]'
          }`}>
          {item.icon && <span className="text-sm">{item.icon}</span>}
          {item.flag && <span className="text-sm mr-1">{item.flag}</span>}
          <span className={`text-[10px] font-medium block ${isActive(item.id) ? 'text-[#C9A84C]' : 'text-[#999]'}`}>
            {item.l}
          </span>
          {item.d && <span className="text-[8px] text-[#B0B0B0] block mt-0.5">{item.d}</span>}
          {item.ex && <span className="text-[8px] text-[#B0B0B0] italic block mt-0.5">"{item.ex}"</span>}
        </button>
      ))}
    </div>
  );
}

/* ── Small Input ── */
function Input({ label, value, onChange, placeholder, textarea, required }) {
  const C = textarea ? 'textarea' : 'input';
  return (
    <div>
      <label className="mb-1 block text-[10px] font-medium text-[#999]">
        {label} {required && <span className="text-[#C9A84C]">*</span>}
      </label>
      <C value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
        rows={textarea ? 2 : undefined}
        className="w-full rounded-lg border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2 text-xs text-white placeholder-[#666] outline-none resize-none focus:border-[#C9A84C]/40" />
    </div>
  );
}

export default function AgentBuilder() {
  const navigate = useNavigate();
  const [generating, setGenerating] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [result, setResult] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);
  const [mindsetSearch, setMindsetSearch] = useState('');

  const [f, setF] = useState({
    segment: '', objective: '', tone: '', mindset: '',
    business_name: '', business_description: '', products_services: '', hours: '',
    differentials: '', target_audience: '',
    language: 'pt', response_length: 'medium',
    topic_scope: '', forbidden_topics: '',
    no_response_action: 'follow_up_24h', context_recovery: true,
    integrations: [],
  });

  const set = (k, v) => setF(p => ({ ...p, [k]: v }));
  const canGenerate = f.segment && f.objective && f.tone && f.business_name && f.business_description;

  const filteredMindsets = MINDSETS.filter(m =>
    !mindsetSearch || m.l.toLowerCase().includes(mindsetSearch.toLowerCase()) || m.d.toLowerCase().includes(mindsetSearch.toLowerCase())
  );

  const generate = async () => {
    setGenerating(true);
    setResult(null);
    try {
      const { data } = await axios.post(`${API}/agents/generate-preview`, f);
      if (data.task_id) {
        // Poll for result
        const poll = async () => {
          try {
            const { data: status } = await axios.get(`${API}/agents/generate-status/${data.task_id}`);
            if (status.status === 'completed') {
              setResult(status.result);
              setGenerating(false);
              setTimeout(() => document.getElementById('result-section')?.scrollIntoView({ behavior: 'smooth' }), 300);
            } else if (status.status === 'failed') {
              toast.error(status.error || 'Erro ao gerar agente.');
              setGenerating(false);
            } else {
              setTimeout(poll, 3000);
            }
          } catch {
            setTimeout(poll, 3000);
          }
        };
        setTimeout(poll, 5000);
      } else {
        setResult(data);
        setGenerating(false);
      }
    } catch (err) {
      toast.error('Erro ao gerar agente. Tente novamente.');
      setGenerating(false);
    }
  };

  const deploy = async () => {
    if (!result) return;
    setDeploying(true);
    try {
      const { data } = await axios.post(`${API}/agents/deploy-generated`, {
        ...result, objective: f.objective, tone: f.tone, language: f.language,
        mindset: f.mindset, no_response_action: f.no_response_action,
        context_recovery: f.context_recovery, response_length: f.response_length,
        integrations: f.integrations,
      });
      toast.success('Agente criado com sucesso!');
      navigate(`/agents/${data.id}/config`);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao publicar agente'));
    } finally {
      setDeploying(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-28">
      {/* Header */}
      <div className="sticky top-0 z-40 border-b border-[#1A1A1A] bg-[#0A0A0A]/95 backdrop-blur-sm px-4 py-3">
        <div className="flex items-center gap-3">
          <button data-testid="builder-back-btn" onClick={() => navigate('/agents')} className="text-[#999] hover:text-white transition">
            <ArrowLeft size={18} />
          </button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10">
            <Sparkles size={16} className="text-[#C9A84C]" />
          </div>
          <div className="flex-1">
            <h1 className="text-sm font-bold text-white">Criar Agente com IA</h1>
            <p className="text-[9px] text-[#B0B0B0]">Preencha e gere um agente personalizado</p>
          </div>
          {canGenerate && !generating && (
            <button data-testid="builder-generate-btn-top" onClick={generate}
              className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] px-3 py-1.5 text-[10px] font-bold text-[#0A0A0A] flex items-center gap-1">
              <Sparkles size={12} /> Gerar
            </button>
          )}
          {generating && <Loader2 size={16} className="text-[#C9A84C] animate-spin" />}
        </div>
      </div>

      <div className="px-4 pt-3 space-y-2.5 max-w-lg mx-auto">

        {/* ═══ IDENTIDADE ═══ */}
        <Section title="Identidade do Agente" icon={Bot} defaultOpen={true} badge={f.segment && f.objective ? '✓' : null}>
          <p className="text-[9px] text-[#B0B0B0] -mt-1 mb-2">Segmento, objetivo e tom de voz</p>

          <label className="text-[10px] font-medium text-[#999] mb-1 block">Segmento *</label>
          <Chips items={SEGMENTS} value={f.segment} onChange={v => set('segment', v)} cols={4} />

          <label className="text-[10px] font-medium text-[#999] mb-1 block mt-3">Objetivo Principal *</label>
          <Chips items={OBJECTIVES} value={f.objective} onChange={v => set('objective', v)} cols={3} />

          <label className="text-[10px] font-medium text-[#999] mb-1 block mt-3">Tom de Voz *</label>
          <Chips items={TONES} value={f.tone} onChange={v => set('tone', v)} cols={3} />
        </Section>

        {/* ═══ MENTALIDADE ═══ */}
        <Section title="Mentalidade" icon={Brain}>
          <p className="text-[9px] text-[#B0B0B0] -mt-1 mb-2">Como o agente pensa e reage</p>
          <div className="relative mb-2">
            <Search size={12} className="absolute left-2.5 top-2.5 text-[#999]" />
            <input data-testid="mindset-search" value={mindsetSearch} onChange={e => setMindsetSearch(e.target.value)}
              placeholder="Buscar mentalidade..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#0D0D0D] pl-7 pr-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/40" />
          </div>
          <Chips items={filteredMindsets} value={f.mindset} onChange={v => set('mindset', v)} cols={2} />
        </Section>

        {/* ═══ NEGOCIO ═══ */}
        <Section title="Sobre o Negocio" icon={MessageSquare} defaultOpen={true} badge={f.business_name ? '✓' : null}>
          <Input label="Nome da empresa" value={f.business_name} onChange={v => set('business_name', v)} placeholder="Ex: Clinica Sorriso" required />
          <Input label="Descricao do negocio" value={f.business_description} onChange={v => set('business_description', v)} placeholder="O que faz, especialidade..." textarea required />
          <div className="grid grid-cols-2 gap-2">
            <Input label="Produtos/Servicos" value={f.products_services} onChange={v => set('products_services', v)} placeholder="Lista principal..." />
            <Input label="Horario" value={f.hours} onChange={v => set('hours', v)} placeholder="Seg-Sex 8h-18h" />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Input label="Publico-alvo" value={f.target_audience} onChange={v => set('target_audience', v)} placeholder="Adultos 25-55" />
            <Input label="Diferenciais" value={f.differentials} onChange={v => set('differentials', v)} placeholder="20 anos exp..." />
          </div>
        </Section>

        {/* ═══ IDIOMA ═══ */}
        <Section title="Idioma" icon={Globe}>
          <p className="text-[9px] text-[#B0B0B0] -mt-1 mb-2">Idioma principal do agente (auto-detectar reconhece o idioma do cliente)</p>
          <Chips items={LANGS} value={f.language} onChange={v => set('language', v)} cols={4} />
        </Section>

        {/* ═══ COMPORTAMENTO ═══ */}
        <Section title="Comportamento" icon={MessageSquare}>
          <label className="text-[10px] font-medium text-[#999] mb-1 block">Tamanho das Respostas</label>
          <Chips items={[
            { id: 'short', l: 'Curta', d: '1-3 frases' },
            { id: 'medium', l: 'Media', d: '2-5 frases' },
            { id: 'detailed', l: 'Detalhada', d: '4-8 frases' },
          ]} value={f.response_length} onChange={v => set('response_length', v)} cols={3} />

          <label className="text-[10px] font-medium text-[#999] mb-1 block mt-3">Se o cliente nao responder</label>
          <Chips items={[
            { id: 'follow_up_1h', l: 'Follow-up 1h', d: 'Msg apos 1 hora' },
            { id: 'follow_up_24h', l: 'Follow-up 24h', d: 'Msg apos 24 horas' },
            { id: 'close_48h', l: 'Encerrar 48h', d: 'Fecha conversa' },
            { id: 'wait', l: 'Aguardar', d: 'Nao faz nada' },
          ]} value={f.no_response_action} onChange={v => set('no_response_action', v)} cols={2} />

          <div className="flex items-center gap-2 mt-3 p-2.5 rounded-lg border border-[#1A1A1A] bg-[#0D0D0D]">
            <button data-testid="context-toggle" onClick={() => set('context_recovery', !f.context_recovery)}
              className={`h-5 w-9 rounded-full transition-all flex items-center shrink-0 ${f.context_recovery ? 'bg-[#C9A84C] justify-end' : 'bg-[#2A2A2A] justify-start'}`}>
              <div className="h-4 w-4 rounded-full bg-white mx-0.5" />
            </button>
            <div>
              <p className="text-[10px] font-medium text-white">Recuperar Contexto</p>
              <p className="text-[8px] text-[#B0B0B0]">Lembrar conversas anteriores com o mesmo cliente</p>
            </div>
          </div>
        </Section>

        {/* ═══ ESCOPO DE ASSUNTO ═══ */}
        <Section title="Escopo de Assunto" icon={Shield}>
          <p className="text-[9px] text-[#B0B0B0] -mt-1 mb-2">Defina os limites do que o agente pode ou nao falar</p>
          <Input label="Assuntos permitidos" value={f.topic_scope} onChange={v => set('topic_scope', v)}
            placeholder="Ex: Vendas de carros, financiamento, test drive, pecas..." textarea />
          <Input label="Assuntos proibidos" value={f.forbidden_topics} onChange={v => set('forbidden_topics', v)}
            placeholder="Ex: Politica, religiao, concorrentes, outros produtos..." textarea />
          <p className="text-[8px] text-[#C9A84C]/60 mt-1">Se o cliente perguntar sobre um assunto proibido, o agente redireciona educadamente.</p>
        </Section>

        {/* ═══ INTEGRACOES ═══ */}
        <Section title="Integracoes" icon={Link2}>
          <p className="text-[9px] text-[#B0B0B0] -mt-1 mb-2">Conecte o agente com suas ferramentas</p>
          <Chips items={INTEGRATIONS} value={f.integrations} onChange={v => set('integrations', v)} multi cols={3} />
          <p className="text-[8px] text-[#B0B0B0] mt-1">O agente mencionara naturalmente as integracoes ativas (ex: "Posso verificar na agenda...")</p>
        </Section>

        {/* ═══ GENERATE BUTTON ═══ */}
        <button data-testid="builder-generate-btn" onClick={generate} disabled={!canGenerate || generating}
          className="w-full rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-3.5 text-sm font-bold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-2">
          {generating ? <Loader2 size={16} className="animate-spin" /> : <Sparkles size={16} />}
          {generating ? 'Gerando agente com IA...' : 'Gerar Agente com IA'}
        </button>

        {/* ═══ GENERATING STATE ═══ */}
        {generating && (
          <div className="flex flex-col items-center py-8 text-center">
            <div className="relative mb-4">
              <div className="h-16 w-16 rounded-2xl bg-[#C9A84C]/10 flex items-center justify-center">
                <Sparkles size={28} className="text-[#C9A84C] animate-pulse" />
              </div>
              <div className="absolute -inset-2 rounded-3xl border border-[#C9A84C]/20 animate-ping" style={{ animationDuration: '2s' }} />
            </div>
            <p className="text-xs text-[#888]">A IA esta criando seu agente personalizado...</p>
            <p className="text-[10px] text-[#B0B0B0] mt-1">Isso pode levar ate 60 segundos</p>
          </div>
        )}

        {/* ═══ RESULT ═══ */}
        {result && !generating && (
          <div id="result-section" className="space-y-2.5 pt-2">
            <div className="rounded-xl border border-[#C9A84C]/25 bg-[#C9A84C]/5 p-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="h-11 w-11 rounded-xl bg-[#C9A84C]/15 flex items-center justify-center">
                  <Bot size={22} className="text-[#C9A84C]" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-bold text-white truncate">{result.agent_name}</h3>
                  <p className="text-[9px] text-[#888]">{f.business_name} · {OBJECTIVES.find(o => o.id === f.objective)?.l}</p>
                </div>
                <span className="rounded-full bg-[#C9A84C]/10 px-2 py-0.5 text-[8px] font-bold text-[#C9A84C] shrink-0">IA</span>
              </div>
              <p className="text-[11px] text-[#999] leading-relaxed">{result.description}</p>
            </div>

            {/* Sample Conversation */}
            {result.sample_conversation?.length > 0 && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 space-y-1.5">
                <p className="text-[9px] font-semibold text-[#999] uppercase tracking-wider mb-1">Conversa de Exemplo</p>
                {result.sample_conversation.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'customer' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[80%] rounded-xl px-2.5 py-1.5 ${
                      msg.role === 'customer' ? 'bg-[#1A1A1A]' : 'bg-[#C9A84C]/8 border border-[#C9A84C]/10'
                    }`}>
                      <p className={`text-[8px] font-semibold mb-0.5 ${msg.role === 'customer' ? 'text-[#B0B0B0]' : 'text-[#C9A84C]/60'}`}>
                        {msg.role === 'customer' ? 'Cliente' : result.agent_name}
                      </p>
                      <p className="text-[10px] text-[#999] leading-relaxed">{msg.message}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Personality */}
            {result.personality && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 space-y-1.5">
                <p className="text-[9px] font-semibold text-[#999] uppercase tracking-wider mb-1">Personalidade</p>
                {[
                  { l: 'Tom', v: result.personality.tone_value },
                  { l: 'Verbosidade', v: result.personality.verbosity_value },
                  { l: 'Emojis', v: result.personality.emoji_value },
                  { l: 'Proatividade', v: result.personality.proactivity },
                  { l: 'Formalidade', v: result.personality.formality },
                ].map((p, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="text-[9px] text-[#999] w-16 shrink-0">{p.l}</span>
                    <div className="flex-1 h-1 rounded-full bg-[#1A1A1A]">
                      <div className="h-full rounded-full bg-[#C9A84C]" style={{ width: `${(p.v || 0) * 100}%` }} />
                    </div>
                    <span className="text-[9px] font-bold text-[#C9A84C] w-7 text-right">{Math.round((p.v || 0) * 100)}%</span>
                  </div>
                ))}
              </div>
            )}

            {/* Topic Boundaries */}
            {result.topic_boundaries && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
                <p className="text-[9px] font-semibold text-[#999] uppercase tracking-wider mb-1.5">Escopo de Assunto</p>
                {result.topic_boundaries.allowed?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-1.5">
                    {result.topic_boundaries.allowed.map((t, i) => (
                      <span key={i} className="rounded-full bg-green-500/10 border border-green-500/20 px-2 py-0.5 text-[8px] text-green-400">{t}</span>
                    ))}
                  </div>
                )}
                {result.topic_boundaries.forbidden?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {result.topic_boundaries.forbidden.map((t, i) => (
                      <span key={i} className="rounded-full bg-red-500/10 border border-red-500/20 px-2 py-0.5 text-[8px] text-red-400">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* System Prompt */}
            <button data-testid="toggle-prompt" onClick={() => setShowPrompt(!showPrompt)}
              className="flex w-full items-center gap-2 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-3 py-2.5">
              <span className="text-[9px] font-semibold text-[#999] uppercase tracking-wider flex-1 text-left">System Prompt Gerado</span>
              {showPrompt ? <ChevronUp size={12} className="text-[#B0B0B0]" /> : <ChevronDown size={12} className="text-[#B0B0B0]" />}
            </button>
            {showPrompt && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 -mt-1">
                <p className="text-[9px] leading-relaxed text-[#888] whitespace-pre-wrap font-mono">{result.system_prompt}</p>
              </div>
            )}

            {/* Knowledge */}
            {result.suggested_knowledge?.length > 0 && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
                <p className="text-[9px] font-semibold text-[#999] uppercase tracking-wider mb-1.5">Knowledge Base ({result.suggested_knowledge.length})</p>
                <div className="space-y-1">
                  {result.suggested_knowledge.map((item, i) => (
                    <div key={i} className="flex items-start gap-1.5 p-1.5 rounded-lg bg-[#111]">
                      <span className="rounded bg-[#C9A84C]/10 px-1 py-px text-[7px] uppercase text-[#C9A84C] shrink-0 mt-0.5">{item.type}</span>
                      <div className="min-w-0">
                        <p className="text-[9px] font-medium text-white truncate">{item.title}</p>
                        <p className="text-[8px] text-[#B0B0B0] line-clamp-1">{item.content}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ═══ BOTTOM BAR ═══ */}
      {result && !generating && (
        <div className="fixed bottom-0 left-0 right-0 border-t border-[#1A1A1A] bg-[#0A0A0A]/95 backdrop-blur-sm px-4 py-3 pb-5">
          <div className="mx-auto flex max-w-lg gap-2">
            <button data-testid="builder-regenerate-btn" onClick={() => { setResult(null); generate(); }}
              className="rounded-xl border border-[#2A2A2A] px-4 py-3 text-[10px] font-medium text-[#888] hover:border-[#C9A84C]/30 hover:text-white flex items-center gap-1.5 transition">
              <RefreshCw size={13} /> Regenerar
            </button>
            <button data-testid="builder-deploy-btn" onClick={deploy} disabled={deploying}
              className="flex-1 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-3 text-xs font-bold text-[#0A0A0A] hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-1.5 transition">
              {deploying ? <Loader2 size={14} className="animate-spin" /> : <Rocket size={14} />}
              {deploying ? 'Publicando...' : 'Publicar Agente'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
