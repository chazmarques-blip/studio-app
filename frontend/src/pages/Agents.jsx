import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Search, Plus, Star, Settings2, Rocket, Lock, Crown, User, X, Sliders, Brain, MessageCircle, Link2, ArrowRight, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Agents() {
  const [marketplaceAgents, setMarketplaceAgents] = useState([]);
  const [myAgents, setMyAgents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [view, setView] = useState('marketplace');
  const [deploying, setDeploying] = useState(null);
  const [userPlan, setUserPlan] = useState('free');
  const [selectedAgent, setSelectedAgent] = useState(null);
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';

  useEffect(() => {
    axios.get(`${API}/agents/marketplace`).then(r => {
      setMarketplaceAgents(r.data.agents);
      if (r.data.plan) setUserPlan(r.data.plan);
    }).catch(() => {});
    axios.get(`${API}/agents`).then(r => setMyAgents(r.data.agents || [])).catch(() => {});
  }, []);

  const typeFilters = [
    { value: 'all', label: t('agents.all') },
    { value: 'sales', label: t('agents.type_sales') },
    { value: 'support', label: t('agents.type_support') },
    { value: 'scheduling', label: t('agents.type_scheduling') },
    { value: 'sac', label: t('agents.type_sac') },
    { value: 'onboarding', label: t('agents.type_onboarding') },
    { value: 'personal', label: t('agents.type_personal') },
  ];

  const deployAgent = async (agent) => {
    if (agent.locked) {
      toast.error(lang === 'pt' ? 'Agente Pessoal disponivel a partir do plano Pro. Faca upgrade!' : 'Personal Agent available from Pro plan. Upgrade!');
      navigate('/pricing');
      return;
    }
    setDeploying(agent.name);
    try {
      const { data } = await axios.post(`${API}/agents/deploy`, {
        template_name: agent.name,
        tone: 'friendly',
        emoji_level: 0.4,
        verbosity_level: 0.5,
      });
      setMyAgents(prev => [...prev, data]);
      toast.success(lang === 'pt' ? `${agent.name} publicado! Vamos configurar.` : `${agent.name} deployed! Let's configure.`);
      setSelectedAgent(null);
      navigate(`/agents/${data.id}/config`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error deploying agent');
    } finally {
      setDeploying(null);
    }
  };

  const agents = view === 'marketplace' ? marketplaceAgents : myAgents;
  const filtered = agents.filter(a => {
    const matchType = filter === 'all' || a.type === filter;
    const matchSearch = !search || a.name.toLowerCase().includes(search.toLowerCase()) || (a.description || '').toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  const personalAgents = filtered.filter(a => a.type === 'personal');
  const businessAgents = filtered.filter(a => a.type !== 'personal');

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-4">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{view === 'marketplace' ? t('agents.marketplace') : (lang === 'pt' ? 'Meus Agentes' : 'My Agents')}</h1>
        <button data-testid="create-agent-btn" onClick={() => navigate('/agents/builder')} className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C] text-[#0A0A0A]"><Plus size={18} /></button>
      </div>

      {/* Tabs */}
      <div className="mb-4 flex rounded-lg bg-[#111] border border-[#1A1A1A] p-1">
        <button data-testid="view-marketplace" onClick={() => setView('marketplace')}
          className={`flex-1 rounded-md py-2 text-xs font-medium transition ${view === 'marketplace' ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#666]'}`}>
          {t('agents.marketplace')} ({marketplaceAgents.length})
        </button>
        <button data-testid="view-my-agents" onClick={() => setView('my_agents')}
          className={`flex-1 rounded-md py-2 text-xs font-medium transition ${view === 'my_agents' ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#666]'}`}>
          {lang === 'pt' ? 'Meus Agentes' : 'My Agents'} ({myAgents.length})
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" />
        <input data-testid="agent-search" type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('agents.search')} className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2.5 pl-9 pr-4 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]" />
      </div>

      {/* Type Filters */}
      {view === 'marketplace' && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-2 no-scrollbar">
          {typeFilters.map(tf => (
            <button key={tf.value} onClick={() => setFilter(tf.value)}
              className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${filter === tf.value ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#888] border border-[#2A2A2A]'}`}>
              {tf.value === 'personal' && <Crown size={10} className="inline mr-1 -mt-0.5" />}
              {tf.label}
            </button>
          ))}
        </div>
      )}

      <p className="mb-3 text-xs text-[#666]">{t('agents.count', { count: filtered.length })}</p>

      {/* Personal Agents Section */}
      {view === 'marketplace' && personalAgents.length > 0 && (filter === 'all' || filter === 'personal') && (
        <div className="mb-5">
          <div className="mb-3 flex items-center gap-2">
            <Crown size={14} className="text-[#C9A84C]" />
            <h2 className="text-sm font-semibold text-white">{t('agents.personal_section')}</h2>
            {!['pro', 'enterprise'].includes(userPlan) && (
              <span className="rounded-full bg-[#C9A84C]/10 px-2 py-0.5 text-[8px] font-semibold text-[#C9A84C] uppercase tracking-wide">Pro+</span>
            )}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {personalAgents.map((agent, i) => (
              <AgentCard key={agent.name + i} agent={agent} view={view} deploying={deploying}
                onDeploy={deployAgent} onDetails={setSelectedAgent}
                onConfig={(id) => navigate(`/agents/${id}/config`)} lang={lang} t={t} />
            ))}
          </div>
        </div>
      )}

      {/* Business Agents */}
      <div className="grid gap-3 sm:grid-cols-2">
        {businessAgents.map((agent, i) => (
          <AgentCard key={agent.id || agent.name + i} agent={agent} view={view} deploying={deploying}
            onDeploy={deployAgent} onDetails={setSelectedAgent}
            onConfig={(id) => navigate(`/agents/${id}/config`)} lang={lang} t={t} />
        ))}
      </div>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <AgentDetailModal agent={selectedAgent} onClose={() => setSelectedAgent(null)}
          onDeploy={deployAgent} deploying={deploying} lang={lang} t={t} />
      )}
    </div>
  );
}

/* ── Agent Card ── */
function AgentCard({ agent, view, deploying, onDeploy, onDetails, onConfig, lang, t }) {
  const isLocked = agent.locked;
  const isPersonal = agent.type === 'personal';

  return (
    <div data-testid={`agent-card-${agent.name?.toLowerCase()}`}
      className={`glass-card group p-4 transition-all hover:border-[rgba(201,168,76,0.3)] ${isLocked ? 'opacity-75' : ''}`}>
      {/* Clickable header area */}
      <div className="mb-3 flex items-center gap-3 cursor-pointer" onClick={() => view === 'marketplace' ? onDetails(agent) : onConfig(agent.id)}>
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${isPersonal ? 'bg-[#C9A84C]/15' : 'bg-[#C9A84C]/10'}`}>
          {isPersonal ? <User size={20} className="text-[#C9A84C]" /> : <Bot size={20} className="text-[#C9A84C]" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
            {isPersonal && <Crown size={11} className="text-[#C9A84C] shrink-0" />}
          </div>
          <span className="text-xs capitalize text-[#888]">{t(`agents.type_${agent.type}`, agent.type)}</span>
        </div>
        {agent.rating && <div className="flex items-center gap-1"><Star size={12} className="fill-[#C9A84C] text-[#C9A84C]" /><span className="text-xs text-[#888]">{agent.rating}</span></div>}
        {isLocked && <Lock size={14} className="text-[#555] shrink-0" />}
      </div>

      <p className="mb-3 text-xs leading-relaxed text-[#666] cursor-pointer" onClick={() => view === 'marketplace' ? onDetails(agent) : onConfig(agent.id)}>{agent.description}</p>

      {/* Buttons */}
      {view === 'marketplace' ? (
        <div className="flex gap-2">
          <button data-testid={`details-${agent.name?.toLowerCase()}`} onClick={() => onDetails(agent)}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-[#2A2A2A] py-2 text-xs font-medium text-[#888] transition hover:border-[#C9A84C]/30 hover:text-white">
            <Eye size={13} /> {lang === 'pt' ? 'Detalhes' : 'Details'}
          </button>
          <button data-testid={`deploy-${agent.name?.toLowerCase()}`} onClick={() => onDeploy(agent)} disabled={deploying === agent.name}
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold transition disabled:opacity-50 ${
              isLocked ? 'border border-[#C9A84C]/30 text-[#C9A84C] hover:bg-[#C9A84C]/10' : 'btn-gold'
            }`}>
            {deploying === agent.name ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#0A0A0A] border-t-transparent" /> :
              isLocked ? <><Lock size={12} /> Pro</> :
              <><Rocket size={13} /> Deploy</>}
          </button>
        </div>
      ) : (
        <button data-testid={`config-${agent.name?.toLowerCase()}`} onClick={() => onConfig(agent.id)}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-[#C9A84C]/30 py-2.5 text-xs font-semibold text-[#C9A84C] transition hover:bg-[#C9A84C]/10">
          <Settings2 size={13} /> {lang === 'pt' ? 'Configurar Agente' : 'Configure Agent'}
        </button>
      )}
    </div>
  );
}

/* ── Agent Detail Modal ── */
function AgentDetailModal({ agent, onClose, onDeploy, deploying, lang, t }) {
  const isLocked = agent.locked;
  const isPersonal = agent.type === 'personal';
  const personality = agent.personality || {};

  const capabilities = {
    sales: lang === 'pt'
      ? ['Qualificacao de leads', 'Apresentacao de produtos', 'Fechamento de vendas', 'Cross-sell e Upsell']
      : ['Lead qualification', 'Product presentation', 'Deal closing', 'Cross-sell & Upsell'],
    support: lang === 'pt'
      ? ['Troubleshooting', 'Escalonamento inteligente', 'Base de conhecimento', 'Resolucao de tickets']
      : ['Troubleshooting', 'Smart escalation', 'Knowledge base', 'Ticket resolution'],
    scheduling: lang === 'pt'
      ? ['Agendamento automatico', 'Lembretes', 'Reagendamento', 'Gestao de calendario']
      : ['Auto scheduling', 'Reminders', 'Rescheduling', 'Calendar management'],
    sac: lang === 'pt'
      ? ['Gestao de reclamacoes', 'Devolucoes', 'Reembolsos', 'Satisfacao do cliente']
      : ['Complaint management', 'Returns', 'Refunds', 'Customer satisfaction'],
    onboarding: lang === 'pt'
      ? ['Boas-vindas', 'Setup guiado', 'Tour de funcionalidades', 'Best practices']
      : ['Welcome flow', 'Guided setup', 'Feature tour', 'Best practices'],
    personal: lang === 'pt'
      ? ['Gestao de tarefas', 'Notas e lembretes', 'Planejamento diario', 'Pesquisa e escrita']
      : ['Task management', 'Notes & reminders', 'Daily planning', 'Research & writing'],
  };

  const tabs = [
    { id: 'overview', label: lang === 'pt' ? 'Visao Geral' : 'Overview', icon: Bot },
    { id: 'config', label: lang === 'pt' ? 'Configuracao' : 'Configuration', icon: Sliders },
  ];
  const [tab, setTab] = useState('overview');

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/70 backdrop-blur-sm" onClick={onClose}>
      <div data-testid="agent-detail-modal" onClick={e => e.stopPropagation()}
        className="w-full max-w-lg max-h-[85vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl border border-[#2A2A2A] bg-[#0D0D0D] shadow-2xl">

        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center gap-3 border-b border-[#1A1A1A] bg-[#0D0D0D] px-5 py-4">
          <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${isPersonal ? 'bg-[#C9A84C]/15' : 'bg-[#C9A84C]/10'}`}>
            {isPersonal ? <User size={22} className="text-[#C9A84C]" /> : <Bot size={22} className="text-[#C9A84C]" />}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-1.5">
              <h2 className="text-base font-bold text-white">{agent.name}</h2>
              {isPersonal && <Crown size={13} className="text-[#C9A84C]" />}
              {agent.rating && <div className="flex items-center gap-0.5 ml-2"><Star size={11} className="fill-[#C9A84C] text-[#C9A84C]" /><span className="text-[11px] text-[#888]">{agent.rating}</span></div>}
            </div>
            <span className="text-xs capitalize text-[#888]">{t(`agents.type_${agent.type}`, agent.type)} · {agent.category || 'general'}</span>
          </div>
          <button data-testid="close-detail-modal" onClick={onClose} className="flex h-8 w-8 items-center justify-center rounded-lg text-[#666] transition hover:bg-[#1A1A1A] hover:text-white">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[#1A1A1A] px-5">
          {tabs.map(tb => (
            <button key={tb.id} onClick={() => setTab(tb.id)}
              className={`flex items-center gap-1.5 border-b-2 px-4 py-2.5 text-xs font-medium transition ${tab === tb.id ? 'border-[#C9A84C] text-[#C9A84C]' : 'border-transparent text-[#666] hover:text-white'}`}>
              <tb.icon size={13} /> {tb.label}
            </button>
          ))}
        </div>

        <div className="px-5 py-4">
          {tab === 'overview' && (
            <>
              {/* Description */}
              <p className="mb-4 text-sm leading-relaxed text-[#999]">{agent.description}</p>

              {/* Capabilities */}
              <h3 className="mb-2 text-xs font-semibold text-white">{lang === 'pt' ? 'Capacidades' : 'Capabilities'}</h3>
              <div className="mb-4 grid grid-cols-2 gap-1.5">
                {(capabilities[agent.type] || capabilities.support).map((cap, i) => (
                  <div key={i} className="flex items-center gap-2 rounded-lg bg-[#111] p-2">
                    <div className="h-1 w-1 rounded-full bg-[#C9A84C]" />
                    <span className="text-[11px] text-[#888]">{cap}</span>
                  </div>
                ))}
              </div>

              {/* What you can configure */}
              <h3 className="mb-2 text-xs font-semibold text-white">{lang === 'pt' ? 'Apos publicar voce podera configurar' : 'After deploying you can configure'}</h3>
              <div className="mb-4 space-y-1.5">
                {[
                  { icon: Sliders, text: lang === 'pt' ? 'Personalidade: tom, verbosidade, uso de emojis' : 'Personality: tone, verbosity, emoji usage' },
                  { icon: Brain, text: lang === 'pt' ? 'Prompts e instrucoes customizadas' : 'Custom prompts and instructions' },
                  { icon: MessageCircle, text: lang === 'pt' ? 'Base de conhecimento (FAQ, produtos, politicas)' : 'Knowledge base (FAQ, products, policies)' },
                  { icon: Link2, text: lang === 'pt' ? 'Integracoes: Google Sheets, Calendar, APIs' : 'Integrations: Google Sheets, Calendar, APIs' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-2.5 rounded-lg bg-[#111] p-2.5">
                    <item.icon size={14} className="text-[#C9A84C] shrink-0" />
                    <span className="text-[11px] text-[#888]">{item.text}</span>
                  </div>
                ))}
              </div>

              {/* System Prompt Preview */}
              {agent.system_prompt && (
                <>
                  <h3 className="mb-2 text-xs font-semibold text-white">{lang === 'pt' ? 'Preview do Comportamento' : 'Behavior Preview'}</h3>
                  <div className="mb-4 rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                    <p className="text-[11px] leading-relaxed text-[#666] line-clamp-4">{agent.system_prompt}</p>
                    <p className="mt-1.5 text-[9px] text-[#444] italic">{lang === 'pt' ? 'Voce podera editar o prompt completo apos publicar' : 'You can edit the full prompt after deploying'}</p>
                  </div>
                </>
              )}
            </>
          )}

          {tab === 'config' && (
            <>
              <p className="mb-4 text-xs text-[#888]">
                {lang === 'pt'
                  ? 'Estas sao as configuracoes padrao do agente. Apos publicar, voce tera acesso completo para ajustar cada detalhe.'
                  : 'These are the agent default settings. After deploying, you will have full access to adjust every detail.'}
              </p>

              {/* Default Personality */}
              <h3 className="mb-3 text-xs font-semibold text-white">{lang === 'pt' ? 'Personalidade Padrao' : 'Default Personality'}</h3>
              <div className="mb-4 space-y-3">
                {[
                  { label: lang === 'pt' ? 'Tom' : 'Tone', value: personality.tone ?? 0.5, left: lang === 'pt' ? 'Formal' : 'Formal', right: lang === 'pt' ? 'Casual' : 'Casual' },
                  { label: lang === 'pt' ? 'Verbosidade' : 'Verbosity', value: personality.verbosity ?? 0.5, left: lang === 'pt' ? 'Conciso' : 'Concise', right: lang === 'pt' ? 'Detalhado' : 'Detailed' },
                  { label: lang === 'pt' ? 'Uso de Emojis' : 'Emoji Usage', value: personality.emoji_usage ?? 0.3, left: lang === 'pt' ? 'Nenhum' : 'None', right: lang === 'pt' ? 'Frequente' : 'Frequent' },
                ].map((s, i) => (
                  <div key={i}>
                    <div className="flex justify-between mb-1">
                      <span className="text-[11px] text-[#888]">{s.label}</span>
                      <span className="text-[11px] font-medium text-[#C9A84C]">{Math.round(s.value * 100)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-[#1A1A1A]">
                      <div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" style={{ width: `${s.value * 100}%` }} />
                    </div>
                    <div className="flex justify-between mt-0.5">
                      <span className="text-[9px] text-[#444]">{s.left}</span>
                      <span className="text-[9px] text-[#444]">{s.right}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Features after deploy */}
              <h3 className="mb-2 text-xs font-semibold text-white">{lang === 'pt' ? 'Abas de Configuracao Completa' : 'Full Configuration Tabs'}</h3>
              <div className="space-y-1.5">
                {[
                  { icon: Sliders, name: lang === 'pt' ? 'Personalidade' : 'Personality', desc: lang === 'pt' ? 'Barras de ajuste fino para tom, criatividade e verbosidade' : 'Fine-tune sliders for tone, creativity and verbosity' },
                  { icon: Brain, name: lang === 'pt' ? 'Comportamento' : 'Behavior', desc: lang === 'pt' ? 'Flags e toggles de comportamento (transferir humano, coletar dados, etc)' : 'Behavior flags & toggles (human handoff, data collection, etc)' },
                  { icon: MessageCircle, name: lang === 'pt' ? 'Conhecimento' : 'Knowledge', desc: lang === 'pt' ? 'Adicionar FAQs, documentos, URLs e instrucoes' : 'Add FAQs, documents, URLs and instructions' },
                  { icon: Link2, name: lang === 'pt' ? 'Integracoes' : 'Integrations', desc: lang === 'pt' ? 'Conectar Google Sheets, Calendar e APIs externas' : 'Connect Google Sheets, Calendar and external APIs' },
                ].map((feat, i) => (
                  <div key={i} className="flex items-start gap-2.5 rounded-lg bg-[#111] p-3">
                    <feat.icon size={14} className="text-[#C9A84C] mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-medium text-white">{feat.name}</p>
                      <p className="text-[10px] text-[#666]">{feat.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Footer CTA */}
        <div className="sticky bottom-0 border-t border-[#1A1A1A] bg-[#0D0D0D] px-5 py-4">
          <button data-testid="modal-deploy-btn" onClick={() => onDeploy(agent)} disabled={deploying === agent.name}
            className={`flex w-full items-center justify-center gap-2 rounded-xl py-3 text-sm font-bold transition disabled:opacity-50 ${
              isLocked ? 'border border-[#C9A84C]/40 text-[#C9A84C] hover:bg-[#C9A84C]/10' : 'bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] text-[#0A0A0A] hover:opacity-90'
            }`}>
            {deploying === agent.name ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#0A0A0A] border-t-transparent" /> :
              isLocked ? <><Lock size={15} /> {lang === 'pt' ? 'Upgrade para Pro' : 'Upgrade to Pro'}</> :
              <><Rocket size={16} /> {lang === 'pt' ? 'Publicar e Configurar' : 'Deploy & Configure'} <ArrowRight size={15} /></>}
          </button>
          <p className="mt-2 text-center text-[10px] text-[#555]">
            {lang === 'pt' ? 'Apos publicar, voce sera redirecionado para a configuracao completa do agente' : 'After deploying, you will be redirected to the full agent configuration'}
          </p>
        </div>
      </div>
    </div>
  );
}
