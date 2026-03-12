import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Search, Plus, Star, Settings2, Rocket, Lock, Crown, User } from 'lucide-react';
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
      toast.success(lang === 'pt' ? `${agent.name} publicado!` : `${agent.name} deployed!`);
      navigate(`/agents/${data.id}/config`);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Error deploying agent';
      toast.error(msg);
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
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{view === 'marketplace' ? t('agents.marketplace') : (lang === 'pt' ? 'Meus Agentes' : 'My Agents')}</h1>
        <button data-testid="create-agent-btn" onClick={() => navigate('/agents/builder')} className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C] text-[#0A0A0A]"><Plus size={18} /></button>
      </div>

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

      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" />
        <input data-testid="agent-search" type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('agents.search')} className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2.5 pl-9 pr-4 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]" />
      </div>

      {view === 'marketplace' && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
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
            {userPlan !== 'pro' && userPlan !== 'enterprise' && (
              <span className="rounded-full bg-[#C9A84C]/10 px-2 py-0.5 text-[8px] font-semibold text-[#C9A84C] uppercase tracking-wide">Pro+</span>
            )}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {personalAgents.map((agent, i) => (
              <AgentCard key={agent.name + i} agent={agent} view={view} deploying={deploying} onDeploy={deployAgent} onConfig={(id) => navigate(`/agents/${id}/config`)} lang={lang} t={t} />
            ))}
          </div>
        </div>
      )}

      {/* Business Agents */}
      <div className="grid gap-3 sm:grid-cols-2">
        {businessAgents.map((agent, i) => (
          <AgentCard key={agent.id || agent.name + i} agent={agent} view={view} deploying={deploying} onDeploy={deployAgent} onConfig={(id) => navigate(`/agents/${id}/config`)} lang={lang} t={t} />
        ))}
      </div>
    </div>
  );
}

function AgentCard({ agent, view, deploying, onDeploy, onConfig, lang, t }) {
  const isLocked = agent.locked;
  const isPersonal = agent.type === 'personal';

  return (
    <div data-testid={`agent-card-${agent.name?.toLowerCase()}`}
      className={`glass-card group p-4 transition-all hover:border-[rgba(201,168,76,0.3)] ${isLocked ? 'opacity-75' : ''}`}>
      <div className="mb-3 flex items-center gap-3">
        <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${isPersonal ? 'bg-[#C9A84C]/15' : 'bg-[#C9A84C]/10'}`}>
          {isPersonal ? <User size={20} className="text-[#C9A84C]" /> : <Bot size={20} className="text-[#C9A84C]" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
            {isPersonal && <Crown size={11} className="text-[#C9A84C] shrink-0" />}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs capitalize text-[#888]">{t(`agents.type_${agent.type}`, agent.type)}</span>
            {agent.tone && <span className="rounded bg-[#1A1A1A] border border-[#2A2A2A] px-1.5 py-0.5 text-[9px] text-[#555]">{agent.tone}</span>}
          </div>
        </div>
        {agent.rating && <div className="flex items-center gap-1"><Star size={12} className="fill-[#C9A84C] text-[#C9A84C]" /><span className="text-xs text-[#888]">{agent.rating}</span></div>}
        {agent.is_deployed && <div className="h-2 w-2 rounded-full bg-[#C9A84C]" title="Active" />}
        {isLocked && <Lock size={14} className="text-[#555] shrink-0" />}
      </div>
      <p className="mb-3 text-xs leading-relaxed text-[#666]">{agent.description}</p>
      {view === 'marketplace' ? (
        <button data-testid={`deploy-${agent.name?.toLowerCase()}`} onClick={() => onDeploy(agent)} disabled={deploying === agent.name}
          className={`flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-xs font-semibold transition disabled:opacity-50 ${
            isLocked
              ? 'border border-[#C9A84C]/30 text-[#C9A84C] hover:bg-[#C9A84C]/10'
              : 'btn-gold'
          }`}>
          {deploying === agent.name ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#0A0A0A] border-t-transparent" /> :
            isLocked ? <><Lock size={12} /> {lang === 'pt' ? 'Upgrade para Pro' : 'Upgrade to Pro'}</> :
            <><Rocket size={13} /> {t('agents.deploy')}</>}
        </button>
      ) : (
        <button data-testid={`config-${agent.name?.toLowerCase()}`} onClick={() => onConfig(agent.id)}
          className="btn-gold-outline flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-xs">
          <Settings2 size={13} /> {lang === 'pt' ? 'Configurar' : 'Configure'}
        </button>
      )}
    </div>
  );
}
