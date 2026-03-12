import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Search, Plus, Star, Settings2, Rocket } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const typeColors = { sales: '#C9A84C', support: '#2196F3', scheduling: '#4CAF50', sac: '#FF9800', onboarding: '#9C27B0', custom: '#666666' };

export default function Agents() {
  const [marketplaceAgents, setMarketplaceAgents] = useState([]);
  const [myAgents, setMyAgents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [view, setView] = useState('marketplace'); // marketplace | my_agents
  const [deploying, setDeploying] = useState(null);
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';

  useEffect(() => {
    axios.get(`${API}/agents/marketplace`).then(r => setMarketplaceAgents(r.data.agents)).catch(() => {});
    axios.get(`${API}/agents`).then(r => setMyAgents(r.data.agents || [])).catch(() => {});
  }, []);

  const typeFilters = [
    { value: 'all', label: t('agents.all') },
    { value: 'sales', label: t('agents.type_sales') },
    { value: 'support', label: t('agents.type_support') },
    { value: 'scheduling', label: t('agents.type_scheduling') },
    { value: 'sac', label: t('agents.type_sac') },
    { value: 'onboarding', label: t('agents.type_onboarding') },
  ];

  const deployAgent = async (agent) => {
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

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{view === 'marketplace' ? t('agents.marketplace') : (lang === 'pt' ? 'Meus Agentes' : 'My Agents')}</h1>
        <button data-testid="create-agent-btn" onClick={() => navigate('/agents/builder')} className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C] text-[#0A0A0A]"><Plus size={18} /></button>
      </div>

      {/* View toggle */}
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
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
        <input data-testid="agent-search" type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('agents.search')} className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2.5 pl-9 pr-4 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
      </div>

      {view === 'marketplace' && (
        <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
          {typeFilters.map(tf => (
            <button key={tf.value} onClick={() => setFilter(tf.value)} className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${filter === tf.value ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#A0A0A0] border border-[#2A2A2A]'}`}>{tf.label}</button>
          ))}
        </div>
      )}

      <p className="mb-3 text-xs text-[#666666]">{t('agents.count', { count: filtered.length })}</p>

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered.map((agent, i) => (
          <div key={agent.id || i} data-testid={`agent-card-${agent.name?.toLowerCase()}`} className="glass-card group p-4 transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ backgroundColor: `${typeColors[agent.type] || '#666'}15` }}>
                <Bot size={20} style={{ color: typeColors[agent.type] || '#666' }} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs capitalize text-[#A0A0A0]">{t(`agents.type_${agent.type}`, agent.type)}</span>
                  {agent.tone && <span className="rounded bg-[#1A1A1A] border border-[#2A2A2A] px-1.5 py-0.5 text-[9px] text-[#666]">{agent.tone}</span>}
                </div>
              </div>
              {agent.rating && <div className="flex items-center gap-1"><Star size={12} className="fill-[#C9A84C] text-[#C9A84C]" /><span className="text-xs text-[#A0A0A0]">{agent.rating}</span></div>}
              {agent.is_deployed && <div className="h-2 w-2 rounded-full bg-[#4CAF50]" title="Active" />}
            </div>
            <p className="mb-3 text-xs leading-relaxed text-[#666666]">{agent.description}</p>
            {view === 'marketplace' ? (
              <button data-testid={`deploy-${agent.name?.toLowerCase()}`} onClick={() => deployAgent(agent)} disabled={deploying === agent.name}
                className="btn-gold flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-xs disabled:opacity-50">
                {deploying === agent.name ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#0A0A0A] border-t-transparent" /> : <Rocket size={13} />}
                {t('agents.deploy')}
              </button>
            ) : (
              <button data-testid={`config-${agent.name?.toLowerCase()}`} onClick={() => navigate(`/agents/${agent.id}/config`)}
                className="btn-gold-outline flex w-full items-center justify-center gap-1.5 rounded-lg py-2 text-xs">
                <Settings2 size={13} /> {lang === 'pt' ? 'Configurar' : 'Configure'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
