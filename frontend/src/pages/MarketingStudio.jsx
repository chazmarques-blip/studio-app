import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Sparkles, Send, PenTool, Palette, CheckCircle, CalendarClock, Save, RotateCcw, Copy, Loader2, Lock } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AGENTS = [
  {
    key: 'copywriter',
    name: 'Sofia',
    role: 'Copywriter',
    rolePt: 'Copywriter',
    icon: PenTool,
    color: '#C9A84C',
    desc: 'Social posts, ad copy, emails, landing pages',
    descPt: 'Posts sociais, textos de anuncios, emails, landing pages',
    placeholder: 'Create 3 variations of an Instagram post about our AI platform launch...',
    placeholderPt: 'Crie 3 variacoes de post para Instagram sobre o lancamento da nossa plataforma de IA...',
  },
  {
    key: 'designer',
    name: 'Lucas',
    role: 'Designer',
    rolePt: 'Designer',
    icon: Palette,
    color: '#7CB9E8',
    desc: 'Visual concepts, image prompts, brand guidelines',
    descPt: 'Conceitos visuais, prompts de imagem, diretrizes de marca',
    placeholder: 'Design a visual concept for our social media campaign header...',
    placeholderPt: 'Crie um conceito visual para o cabecalho da nossa campanha nas redes sociais...',
  },
  {
    key: 'reviewer',
    name: 'Ana',
    role: 'Reviewer',
    rolePt: 'Revisora',
    icon: CheckCircle,
    color: '#4CAF50',
    desc: 'Content review, A/B suggestions, optimization',
    descPt: 'Revisao de conteudo, sugestoes A/B, otimizacao',
    placeholder: 'Review this copy and suggest improvements: "Try our AI platform today!"',
    placeholderPt: 'Revise este texto e sugira melhorias: "Experimente nossa plataforma de IA hoje!"',
  },
  {
    key: 'publisher',
    name: 'Pedro',
    role: 'Publisher',
    rolePt: 'Publisher',
    icon: CalendarClock,
    color: '#E8A87C',
    desc: 'Scheduling, content calendar, cross-platform',
    descPt: 'Agendamento, calendario editorial, multiplataforma',
    placeholder: 'Create a weekly content calendar for Instagram and WhatsApp...',
    placeholderPt: 'Crie um calendario de conteudo semanal para Instagram e WhatsApp...',
  },
];

function AgentCard({ agent, isSelected, onClick, lang }) {
  const Icon = agent.icon;
  return (
    <button data-testid={`studio-agent-${agent.key}`} onClick={onClick}
      className={`w-full rounded-xl border p-3 text-left transition ${
        isSelected ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#2A2A2A]'
      }`}>
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ backgroundColor: `${agent.color}15` }}>
          <Icon size={16} style={{ color: agent.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[12px] font-semibold text-white">{agent.name}</p>
          <p className="text-[9px] text-[#888]">{lang === 'pt' ? agent.rolePt : agent.role}</p>
        </div>
        {isSelected && <div className="h-2 w-2 rounded-full bg-[#C9A84C]" />}
      </div>
      <p className="mt-1.5 text-[9px] text-[#555] line-clamp-1">{lang === 'pt' ? agent.descPt : agent.desc}</p>
    </button>
  );
}

function MessageBubble({ msg, agent }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 ${
        isUser ? 'bg-[#C9A84C]/10 border border-[#C9A84C]/15' : 'bg-[#111] border border-[#1A1A1A]'
      }`}>
        {!isUser && (
          <p className="text-[9px] font-semibold mb-1" style={{ color: agent?.color || '#C9A84C' }}>{agent?.name}</p>
        )}
        <div className="text-[11px] text-[#ccc] leading-relaxed whitespace-pre-wrap">{msg.content}</div>
        {msg.metadata && (
          <p className="text-[8px] text-[#444] mt-1">{msg.metadata.response_time_ms}ms</p>
        )}
      </div>
    </div>
  );
}

export default function MarketingStudio() {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [selectedAgent, setSelectedAgent] = useState('copywriter');
  const [messages, setMessages] = useState({});
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionIds, setSessionIds] = useState({});
  const [plan, setPlan] = useState('');
  const [loading, setLoading] = useState(true);
  const [context, setContext] = useState({ company: 'AgentZZ', industry: 'SaaS / AI', audience: 'PMEs que buscam automacao de atendimento', brand_voice: 'Moderno, profissional, inovador' });
  const [showContext, setShowContext] = useState(false);
  const chatRef = useRef(null);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => {
      setPlan(r.data.plan || 'free');
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, selectedAgent]);

  const agentObj = AGENTS.find(a => a.key === selectedAgent);
  const agentMessages = messages[selectedAgent] || [];
  const isEnterprise = plan === 'enterprise';

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const userMsg = { role: 'user', content: input.trim() };
    setMessages(prev => ({ ...prev, [selectedAgent]: [...(prev[selectedAgent] || []), userMsg] }));
    setInput('');
    setSending(true);

    try {
      const { data } = await axios.post(`${API}/campaigns/studio/generate`, {
        agent_type: selectedAgent,
        prompt: input.trim(),
        context,
        session_id: sessionIds[selectedAgent] || null,
      });
      const aiMsg = { role: 'assistant', content: data.response, metadata: data.metadata };
      setMessages(prev => ({ ...prev, [selectedAgent]: [...(prev[selectedAgent] || []), aiMsg] }));
      setSessionIds(prev => ({ ...prev, [selectedAgent]: data.session_id }));
    } catch (e) {
      const detail = e.response?.data?.detail || 'Error';
      if (detail.includes('Enterprise')) {
        toast.error(lang === 'pt' ? 'Marketing AI Studio requer plano Enterprise' : 'Marketing AI Studio requires Enterprise plan');
      } else {
        toast.error(detail);
      }
      setMessages(prev => ({ ...prev, [selectedAgent]: (prev[selectedAgent] || []).slice(0, -1) }));
    }
    setSending(false);
  };

  const clearChat = async () => {
    const sid = sessionIds[selectedAgent];
    if (sid) {
      await axios.delete(`${API}/campaigns/studio/session/${sid}`).catch(() => {});
    }
    setMessages(prev => ({ ...prev, [selectedAgent]: [] }));
    setSessionIds(prev => ({ ...prev, [selectedAgent]: null }));
  };

  const saveAsCreative = async (content) => {
    try {
      await axios.post(`${API}/campaigns/creatives/save`, {
        type: selectedAgent === 'copywriter' ? 'copy' : selectedAgent === 'designer' ? 'image_prompt' : 'copy',
        title: `${agentObj.name}: ${new Date().toLocaleDateString()}`,
        content: { body: content, agent: selectedAgent, platform: 'multi' },
      });
      toast.success(lang === 'pt' ? 'Salvo na biblioteca!' : 'Saved to library!');
    } catch { toast.error('Error saving'); }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success(lang === 'pt' ? 'Copiado!' : 'Copied!');
  };

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" />
    </div>
  );

  if (!isEnterprise) return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-4">
      <div className="max-w-sm text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-[#C9A84C]/10 mx-auto mb-4">
          <Lock size={28} className="text-[#C9A84C]" />
        </div>
        <h1 className="text-lg font-bold text-white mb-2">Marketing AI Studio</h1>
        <p className="text-[12px] text-[#888] mb-4">{lang === 'pt' ? 'Este recurso exclusivo esta disponivel apenas no plano Enterprise. Faca upgrade para desbloquear 4 agentes IA de marketing.' : 'This exclusive feature is available on the Enterprise plan only. Upgrade to unlock 4 AI marketing agents.'}</p>
        <button data-testid="studio-upgrade-btn" onClick={() => navigate('/upgrade')} className="btn-gold rounded-xl px-6 py-2.5 text-[12px]">
          {lang === 'pt' ? 'Upgrade para Enterprise' : 'Upgrade to Enterprise'}
        </button>
        <button onClick={() => navigate('/marketing')} className="block mx-auto mt-3 text-[10px] text-[#555] hover:text-white">
          {lang === 'pt' ? 'Voltar' : 'Go back'}
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex flex-col">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-3 py-2 shrink-0">
        <div className="flex items-center gap-2.5">
          <button data-testid="studio-back" onClick={() => navigate('/marketing')} className="text-[#666] hover:text-white transition"><ArrowLeft size={18} /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#C9A84C] to-[#D4B85A] shrink-0">
            <Sparkles size={14} className="text-black" />
          </div>
          <div className="flex-1">
            <h1 className="text-sm font-semibold text-white">Marketing AI Studio</h1>
            <p className="text-[9px] text-[#555]">4 {lang === 'pt' ? 'agentes especializados' : 'specialized agents'}</p>
          </div>
          <button onClick={() => setShowContext(!showContext)} className="text-[9px] text-[#C9A84C] hover:underline">
            {lang === 'pt' ? 'Contexto' : 'Context'}
          </button>
        </div>
      </div>

      {/* Context Panel */}
      {showContext && (
        <div data-testid="context-panel" className="border-b border-[#1A1A1A] px-3 py-2 bg-[#0D0D0D]">
          <div className="grid grid-cols-2 gap-1.5 max-w-xl">
            {[
              { key: 'company', label: lang === 'pt' ? 'Empresa' : 'Company' },
              { key: 'industry', label: lang === 'pt' ? 'Segmento' : 'Industry' },
              { key: 'audience', label: lang === 'pt' ? 'Publico-alvo' : 'Audience' },
              { key: 'brand_voice', label: lang === 'pt' ? 'Tom da Marca' : 'Brand Voice' },
            ].map(f => (
              <div key={f.key}>
                <label className="text-[8px] text-[#555] uppercase">{f.label}</label>
                <input value={context[f.key] || ''} onChange={e => setContext(p => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full rounded border border-[#1E1E1E] bg-[#111] px-2 py-1 text-[10px] text-white outline-none" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Agents Sidebar */}
        <div className="w-[180px] md:w-[220px] shrink-0 border-r border-[#1A1A1A] p-2 overflow-y-auto space-y-1.5">
          {AGENTS.map(a => (
            <AgentCard key={a.key} agent={a} isSelected={selectedAgent === a.key} onClick={() => setSelectedAgent(a.key)} lang={lang} />
          ))}
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          {/* Agent Header */}
          <div className="border-b border-[#111] px-3 py-2 flex items-center gap-2">
            <agentObj.icon size={14} style={{ color: agentObj.color }} />
            <span className="text-[11px] font-semibold text-white">{agentObj.name}</span>
            <span className="text-[9px] text-[#555]">{lang === 'pt' ? agentObj.rolePt : agentObj.role}</span>
            <div className="ml-auto flex items-center gap-1">
              <button data-testid="clear-chat" onClick={clearChat} className="text-[#444] hover:text-white p-1 transition" title="Clear"><RotateCcw size={12} /></button>
            </div>
          </div>

          {/* Messages */}
          <div ref={chatRef} className="flex-1 overflow-y-auto px-3 py-3">
            {agentMessages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-10 opacity-60">
                <agentObj.icon size={32} style={{ color: agentObj.color }} className="mb-3 opacity-40" />
                <p className="text-[12px] text-[#888] mb-1">{lang === 'pt' ? `Ola! Eu sou ${agentObj.name}.` : `Hi! I'm ${agentObj.name}.`}</p>
                <p className="text-[10px] text-[#555] max-w-xs">{lang === 'pt' ? agentObj.descPt : agentObj.desc}</p>
              </div>
            )}
            {agentMessages.map((msg, i) => (
              <div key={i}>
                <MessageBubble msg={msg} agent={agentObj} />
                {msg.role === 'assistant' && (
                  <div className="flex gap-1 mb-3 ml-1 -mt-1">
                    <button onClick={() => copyToClipboard(msg.content)} className="text-[8px] text-[#444] hover:text-[#C9A84C] flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-[#111]">
                      <Copy size={8} /> {lang === 'pt' ? 'Copiar' : 'Copy'}
                    </button>
                    <button onClick={() => saveAsCreative(msg.content)} className="text-[8px] text-[#444] hover:text-[#C9A84C] flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-[#111]">
                      <Save size={8} /> {lang === 'pt' ? 'Salvar' : 'Save'}
                    </button>
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="flex justify-start mb-3">
                <div className="bg-[#111] border border-[#1A1A1A] rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Loader2 size={14} className="animate-spin" style={{ color: agentObj.color }} />
                    <span className="text-[10px] text-[#555]">{agentObj.name} {lang === 'pt' ? 'esta pensando...' : 'is thinking...'}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-[#1A1A1A] px-3 py-2">
            <div className="flex gap-2 items-end">
              <textarea data-testid="studio-input" value={input} onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                placeholder={lang === 'pt' ? agentObj.placeholderPt : agentObj.placeholder}
                rows={2}
                className="flex-1 rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2 text-[11px] text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/30" />
              <button data-testid="studio-send" onClick={sendMessage} disabled={sending || !input.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#C9A84C] text-black transition hover:bg-[#D4B85A] disabled:opacity-30 shrink-0">
                <Send size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
