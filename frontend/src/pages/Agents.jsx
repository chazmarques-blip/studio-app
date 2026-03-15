import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Search, Star, Eye, Rocket, Bot, Sparkles, Crown, ChevronRight, Zap } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { getAgentAvatar } from '../data/agentAvatars';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPE_FILTERS = [
  { id: 'all', l: { pt: 'Todos', en: 'All', es: 'Todos' } },
  { id: 'sales', l: { pt: 'Vendas', en: 'Sales', es: 'Ventas' } },
  { id: 'support', l: { pt: 'Suporte', en: 'Support', es: 'Soporte' } },
  { id: 'scheduling', l: { pt: 'Agenda', en: 'Scheduling', es: 'Agenda' } },
  { id: 'sac', l: { pt: 'SAC', en: 'SAC', es: 'SAC' } },
  { id: 'onboarding', l: { pt: 'Onboarding', en: 'Onboarding', es: 'Onboarding' } },
  { id: 'personal', l: { pt: 'Pessoal', en: 'Personal', es: 'Personal' } },
];

/* ── Avatar Component ── */
function AgentAvatar({ name, size = 'md', className = '' }) {
  const url = getAgentAvatar(name);
  const sizes = { sm: 'h-8 w-8', md: 'h-11 w-11', lg: 'h-14 w-14' };
  if (url) {
    return (
      <div className={`${sizes[size]} rounded-xl overflow-hidden ring-2 ring-[#C9A84C]/20 shrink-0 ${className}`}>
        <img src={url} alt={name} className="h-full w-full object-cover" loading="lazy" />
      </div>
    );
  }
  return (
    <div className={`${sizes[size]} rounded-xl bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center ring-2 ring-[#C9A84C]/10 shrink-0 ${className}`}>
      <Bot size={size === 'lg' ? 24 : size === 'md' ? 18 : 14} className="text-[#C9A84C]/60" />
    </div>
  );
}

/* ── Agent Card ── */
function AgentCard({ agent, onDeploy, onDetails, isPersonal, lang }) {
  const avatar = getAgentAvatar(agent.name);

  return (
    <div data-testid={`agent-card-${agent.name}`}
      className="group relative rounded-2xl border border-[#1A1A1A] bg-[#0D0D0D] overflow-hidden transition-all duration-300 hover:border-[#C9A84C]/20 hover:shadow-[0_0_30px_rgba(201,168,76,0.04)]">

      {/* Subtle glow on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-[#C9A84C]/[0.02] to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

      <div className="relative p-3.5">
        {/* Header */}
        <div className="flex items-start gap-3 mb-2.5">
          <AgentAvatar name={agent.name} size="md" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="text-sm font-bold text-white truncate">{agent.name}</h3>
              {isPersonal && <Crown size={11} className="text-[#C9A84C] shrink-0" />}
            </div>
            <p className="text-[10px] text-[#666] capitalize">{agent.type}</p>
          </div>
          {agent.rating && (
            <div className="flex items-center gap-0.5 shrink-0">
              <Star size={10} className="text-[#C9A84C] fill-[#C9A84C]" />
              <span className="text-[10px] font-semibold text-[#C9A84C]">{agent.rating}</span>
            </div>
          )}
        </div>

        {/* Description */}
        <p className="text-[10px] text-[#888] leading-relaxed mb-3 line-clamp-2">{agent.description}</p>

        {/* Actions */}
        <div className="flex gap-1.5">
          <button data-testid={`details-${agent.name}`} onClick={() => onDetails(agent)}
            className="flex-1 flex items-center justify-center gap-1 rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-2 text-[10px] font-medium text-[#888] transition-all duration-200 hover:border-[#C9A84C]/30 hover:text-[#C9A84C] hover:bg-[#C9A84C]/5 hover:shadow-[0_0_12px_rgba(201,168,76,0.06)] active:scale-[0.97]">
            <Eye size={12} /> {lang === 'pt' ? 'Detalhes' : 'Details'}
          </button>
          <button data-testid={`deploy-${agent.name}`} onClick={() => onDeploy(agent)}
            className="flex-1 flex items-center justify-center gap-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#B89A40] px-2 py-2 text-[10px] font-bold text-[#0A0A0A] transition-all duration-200 hover:shadow-[0_0_18px_rgba(201,168,76,0.2)] hover:from-[#D4B85A] hover:to-[#C9A84C] active:scale-[0.97]">
            <Zap size={12} /> Deploy
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── My Agent Card ── */
function MyAgentCard({ agent, lang }) {
  const navigate = useNavigate();
  return (
    <button data-testid={`my-agent-${agent.id}`} onClick={() => navigate(`/agents/${agent.id}/config`)}
      className="group flex items-center gap-3 rounded-2xl border border-[#1A1A1A] bg-[#0D0D0D] p-3.5 text-left transition-all duration-300 hover:border-[#C9A84C]/20 hover:shadow-[0_0_20px_rgba(201,168,76,0.04)] active:scale-[0.99]">
      <AgentAvatar name={agent.name} size="md" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <h3 className="text-sm font-semibold text-white truncate">{agent.name}</h3>
          <span className={`rounded-full px-1.5 py-px text-[7px] font-bold ${
            agent.status === 'active' ? 'bg-green-500/10 text-green-400' : 'bg-[#333]/50 text-[#666]'
          }`}>{agent.status === 'active' ? (lang === 'pt' ? 'ATIVO' : 'ACTIVE') : 'OFF'}</span>
        </div>
        <p className="text-[10px] text-[#666] capitalize">{agent.type}</p>
        {agent.description && <p className="text-[9px] text-[#555] truncate mt-0.5">{agent.description}</p>}
      </div>
      <ChevronRight size={16} className="text-[#333] group-hover:text-[#C9A84C] transition shrink-0" />
    </button>
  );
}

export default function Agents() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'pt';
  const [tab, setTab] = useState('marketplace');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [marketplace, setMarketplace] = useState([]);
  const [myAgents, setMyAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deploying, setDeploying] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [mpRes, myRes] = await Promise.all([
        axios.get(`${API}/agents/marketplace`),
        axios.get(`${API}/agents`),
      ]);
      setMarketplace(mpRes.data?.agents || mpRes.data || []);
      setMyAgents(myRes.data?.agents || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filtered = marketplace.filter(a => {
    if (filter !== 'all' && filter !== 'personal' && a.type !== filter) return false;
    if (filter === 'personal' && !a.is_personal) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && !a.description.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const personalAgents = filtered.filter(a => a.is_personal);
  const businessAgents = filtered.filter(a => !a.is_personal);

  const handleDeploy = async (agent) => {
    setDeploying(agent.name);
    try {
      await axios.post(`${API}/agents/deploy`, { template_name: agent.name });
      toast.success(lang === 'pt' ? `${agent.name} ativado!` : `${agent.name} deployed!`);
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao fazer deploy');
    } finally {
      setDeploying(null);
    }
  };

  const handleDetails = (agent) => {
    toast(
      <div className="text-left">
        <div className="flex items-center gap-2 mb-2">
          {getAgentAvatar(agent.name) && <img src={getAgentAvatar(agent.name)} className="h-8 w-8 rounded-lg object-cover" alt="" />}
          <div>
            <p className="font-bold text-white text-sm">{agent.name}</p>
            <p className="text-[10px] text-[#888] capitalize">{agent.type}</p>
          </div>
        </div>
        <p className="text-[11px] text-[#999]">{agent.description}</p>
      </div>,
      { duration: 5000 }
    );
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      {/* Header */}
      <div className="px-4 pt-5 pb-3">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-bold text-white">Agent Marketplace</h1>
            <p className="text-[10px] text-[#666] mt-0.5">{marketplace.length} {lang === 'pt' ? 'agentes disponiveis' : 'agents available'}</p>
          </div>
          <button data-testid="create-agent-btn" onClick={() => navigate('/agents/builder')}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#B89A40] pl-3 pr-3.5 py-2.5 text-xs font-bold text-[#0A0A0A] transition-all duration-200 hover:shadow-[0_0_24px_rgba(201,168,76,0.25)] hover:from-[#D4B85A] hover:to-[#C9A84C] active:scale-[0.97]">
            <Sparkles size={15} />
            <span>{lang === 'pt' ? 'Criar Agente' : 'Create Agent'}</span>
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="flex rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-1 mb-3">
          {[
            { id: 'marketplace', l: `Marketplace (${marketplace.length})` },
            { id: 'my', l: `${lang === 'pt' ? 'Meus Agentes' : 'My Agents'} (${myAgents.length})` },
          ].map(t => (
            <button key={t.id} data-testid={`tab-${t.id}`} onClick={() => setTab(t.id)}
              className={`flex-1 rounded-lg py-2.5 text-xs font-semibold transition-all duration-200 ${
                tab === t.id
                  ? 'bg-gradient-to-r from-[#C9A84C] to-[#B89A40] text-[#0A0A0A] shadow-[0_0_16px_rgba(201,168,76,0.12)]'
                  : 'text-[#666] hover:text-[#999]'
              }`}>
              {t.l}
            </button>
          ))}
        </div>
      </div>

      {/* Marketplace Tab */}
      {tab === 'marketplace' && (
        <div className="px-4">
          {/* Search */}
          <div className="relative mb-3">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#444]" />
            <input data-testid="agent-search" value={search} onChange={e => setSearch(e.target.value)}
              placeholder={lang === 'pt' ? 'Buscar agentes...' : 'Search agents...'}
              className="w-full rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] pl-9 pr-3 py-2.5 text-xs text-white placeholder-[#444] outline-none transition focus:border-[#C9A84C]/30 focus:shadow-[0_0_12px_rgba(201,168,76,0.05)]" />
          </div>

          {/* Filter Chips */}
          <div className="flex gap-1.5 overflow-x-auto no-scrollbar mb-4 pb-0.5">
            {TYPE_FILTERS.map(f => (
              <button key={f.id} data-testid={`filter-${f.id}`} onClick={() => setFilter(f.id)}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-[10px] font-semibold transition-all duration-200 ${
                  filter === f.id
                    ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/30 shadow-[0_0_10px_rgba(201,168,76,0.08)]'
                    : 'border border-[#1A1A1A] text-[#666] hover:border-[#2A2A2A] hover:text-[#999]'
                }`}>
                {f.l[lang] || f.l.pt}
              </button>
            ))}
          </div>

          {/* Personal Agents */}
          {personalAgents.length > 0 && (
            <div className="mb-4">
              <div className="flex items-center gap-1.5 mb-2.5">
                <Crown size={13} className="text-[#C9A84C]" />
                <h2 className="text-xs font-bold text-white">{lang === 'pt' ? 'Agentes Pessoais' : 'Personal Agents'}</h2>
                <span className="text-[8px] text-[#C9A84C]/60 bg-[#C9A84C]/5 px-1.5 py-0.5 rounded-full font-bold">PRO</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {personalAgents.map(a => (
                  <AgentCard key={a.name} agent={a} onDeploy={handleDeploy} onDetails={handleDetails} isPersonal lang={lang} />
                ))}
              </div>
            </div>
          )}

          {/* Business Agents */}
          {businessAgents.length > 0 && (
            <div className="pb-4">
              {personalAgents.length > 0 && (
                <div className="flex items-center gap-1.5 mb-2.5">
                  <Bot size={13} className="text-[#888]" />
                  <h2 className="text-xs font-bold text-white">{lang === 'pt' ? 'Agentes de Negocio' : 'Business Agents'}</h2>
                </div>
              )}
              <div className="grid grid-cols-2 gap-2">
                {businessAgents.map(a => (
                  <AgentCard key={a.name} agent={a} onDeploy={handleDeploy} onDetails={handleDetails} lang={lang} />
                ))}
              </div>
            </div>
          )}

          {filtered.length === 0 && !loading && (
            <div className="text-center py-12">
              <Bot size={32} className="text-[#333] mx-auto mb-2" />
              <p className="text-sm text-[#666]">{lang === 'pt' ? 'Nenhum agente encontrado' : 'No agents found'}</p>
            </div>
          )}
        </div>
      )}

      {/* My Agents Tab */}
      {tab === 'my' && (
        <div className="px-4 pb-4 space-y-2">
          {myAgents.length === 0 && !loading ? (
            <div className="text-center py-12">
              <Bot size={32} className="text-[#333] mx-auto mb-2" />
              <p className="text-sm text-[#666] mb-3">{lang === 'pt' ? 'Voce ainda nao tem agentes' : 'No agents yet'}</p>
              <button onClick={() => navigate('/agents/builder')}
                className="rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#B89A40] px-5 py-2.5 text-xs font-bold text-[#0A0A0A] hover:shadow-[0_0_24px_rgba(201,168,76,0.25)] active:scale-[0.97] transition-all">
                <Sparkles size={14} className="inline mr-1" /> {lang === 'pt' ? 'Criar Primeiro Agente' : 'Create First Agent'}
              </button>
            </div>
          ) : (
            myAgents.map(a => <MyAgentCard key={a.id} agent={a} lang={lang} />)
          )}
        </div>
      )}
    </div>
  );
}
