import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Search, Star, Eye, Bot, Crown, ChevronRight, Zap } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { getAgentAvatar, DEFAULT_AVATAR } from '../data/agentAvatars';
import AgentDetailsDrawer from '../components/AgentDetailsDrawer';
import { getErrorMsg } from '../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPE_FILTERS = [
  { id: 'all', k: 'agents.all' }, { id: 'sales', k: 'agents.sales' }, { id: 'support', k: 'agents.support' },
  { id: 'scheduling', k: 'agents.scheduling' }, { id: 'sac', k: 'agents.sac' }, { id: 'onboarding', k: 'agents.onboarding' },
  { id: 'personal', k: 'agents.personal' },
];

function AgentCard({ agent, onDeploy, onDetails, isPersonal, lang }) {
  const avatar = getAgentAvatar(agent.name);
  return (
    <div data-testid={`agent-card-${agent.name}`}
      className="group relative glass-card p-2 transition-all duration-300 hover:border-[#C9A84C]/20 hover:shadow-[0_0_20px_rgba(201,168,76,0.04)]">
      <div className="flex gap-2 mb-1.5">
        <div className="h-10 w-10 rounded-lg overflow-hidden ring-1 ring-[#C9A84C]/15 shrink-0">
          {avatar ? <img src={avatar} alt={agent.name} className="h-full w-full object-cover" loading="lazy" />
            : <div className="h-full w-full bg-[#C9A84C]/10 flex items-center justify-center"><Bot size={16} className="text-[#C9A84C]/50" /></div>}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1 mb-px">
            <span className="text-[10px] font-bold text-white truncate">{agent.name}</span>
            {isPersonal && <Crown size={8} className="text-[#C9A84C] shrink-0" />}
            {agent.rating && <><Star size={7} className="text-[#C9A84C] fill-[#C9A84C] ml-auto shrink-0" /><span className="text-[7px] font-bold text-[#C9A84C]">{agent.rating}</span></>}
          </div>
          <p className="text-[7px] text-[#999] leading-[1.3] line-clamp-2">{agent.description}</p>
        </div>
      </div>
      <div className="flex gap-1">
        <button data-testid={`details-${agent.name}`} onClick={() => onDetails(agent)}
          className="flex-1 flex items-center justify-center gap-0.5 rounded-lg border border-[#1E1E1E] bg-[#111] py-1.5 text-[8px] font-medium text-[#777] transition-all hover:border-[#C9A84C]/30 hover:text-[#C9A84C] active:scale-[0.97]">
          <Eye size={10} /> Detalhes
        </button>
        <button data-testid={`deploy-${agent.name}`} onClick={() => onDeploy(agent)}
          className="flex-1 flex items-center justify-center gap-0.5 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#B89A40] py-1.5 text-[8px] font-bold text-[#0A0A0A] transition-all hover:shadow-[0_0_12px_rgba(201,168,76,0.15)] active:scale-[0.97]">
          <Zap size={10} /> Deploy
        </button>
      </div>
    </div>
  );
}

function MyAgentCard({ agent }) {
  const navigate = useNavigate();
  const avatar = getAgentAvatar(agent.name);
  return (
    <button data-testid={`my-agent-${agent.id}`} onClick={() => navigate(`/agents/${agent.id}/config`)}
      className="group flex items-center gap-2.5 glass-card p-2.5 text-left transition-all hover:border-[#C9A84C]/20 active:scale-[0.99] w-full">
      <div className="h-9 w-9 rounded-lg overflow-hidden ring-1 ring-[#C9A84C]/15 shrink-0">
        {avatar ? <img src={avatar} alt={agent.name} className="h-full w-full object-cover" loading="lazy" />
          : <div className="h-full w-full bg-[#C9A84C]/10 flex items-center justify-center"><Bot size={16} className="text-[#C9A84C]/50" /></div>}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] font-semibold text-white truncate">{agent.name}</span>
          <span className={`rounded-full px-1.5 py-px text-[7px] font-bold ${agent.status === 'active' ? 'bg-green-500/10 text-green-400' : 'bg-[#333]/50 text-[#B0B0B0]'}`}>
            {agent.status === 'active' ? 'ON' : 'OFF'}
          </span>
        </div>
        <span className="text-[8px] text-[#B0B0B0] capitalize">{agent.type}</span>
      </div>
      <ChevronRight size={14} className="text-[#999] group-hover:text-[#C9A84C] transition shrink-0" />
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
  const [detailsAgent, setDetailsAgent] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    try {
      const [mpRes, myRes] = await Promise.all([axios.get(`${API}/agents/marketplace`), axios.get(`${API}/agents`)]);
      setMarketplace(mpRes.data?.agents || mpRes.data || []);
      setMyAgents(myRes.data?.agents || []);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  const filtered = marketplace.filter(a => {
    if (filter !== 'all' && filter !== 'personal' && a.type !== filter) return false;
    if (filter === 'personal' && !a.is_personal) return false;
    if (search && !a.name.toLowerCase().includes(search.toLowerCase()) && !(a.description || '').toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const personal = filtered.filter(a => a.is_personal);
  const business = filtered.filter(a => !a.is_personal);

  const handleDeploy = async (agent) => {
    try {
      await axios.post(`${API}/agents/deploy`, { template_name: agent.name });
      toast.success(`${agent.name} deployed!`);
      loadData();
    } catch (err) { toast.error(getErrorMsg(err, 'Deploy error')); }
  };

  const handleDetails = (agent) => {
    setDetailsAgent(agent);
  };

  return (
    <div className="min-h-screen">
      <div className="px-4 pt-4 pb-2">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h1 className="text-lg font-bold text-white">Agents</h1>
            <p className="text-[9px] text-[#B0B0B0]">{marketplace.length} disponiveis</p>
          </div>
          <button data-testid="create-agent-btn" onClick={() => navigate('/agents/builder')}
            className="btn-gold flex items-center gap-1.5 rounded-xl pl-1.5 pr-3 py-1.5 text-[10px] font-bold">
            <img src={DEFAULT_AVATAR} alt="" className="h-6 w-6 rounded-lg object-cover" />
            {t('agents.builder_title') || 'Create Agent'}
          </button>
        </div>

        {/* Tabs */}
        <div className="flex rounded-xl glass-card p-0.5 mb-2.5">
          {[{ id: 'marketplace', label: `Marketplace (${marketplace.length})` }, { id: 'my', label: `${t('agents.my_agents') || 'My Agents'} (${myAgents.length})` }].map(tb => (
            <button key={tb.id} data-testid={`tab-${tb.id}`} onClick={() => setTab(tb.id)}
              className={`flex-1 rounded-lg py-2 text-[10px] font-semibold transition-all ${
                tab === tb.id ? 'btn-gold shadow-[0_0_12px_rgba(201,168,76,0.1)]' : 'text-[#B0B0B0] hover:text-[#999]'}`}>
              {tb.label}
            </button>
          ))}
        </div>
      </div>

      {tab === 'marketplace' && (
        <div className="px-4">
          <div className="relative mb-2">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#999]" />
            <input data-testid="agent-search" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('agents.search_placeholder') || "Search agents..."}
              className="w-full rounded-lg border border-[#1A1A1A] bg-[#0D0D0D] pl-8 pr-3 py-2 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30" />
          </div>
          <div className="flex gap-1 overflow-x-auto no-scrollbar mb-3 pb-0.5">
            {TYPE_FILTERS.map(f => (
              <button key={f.id} data-testid={`filter-${f.id}`} onClick={() => setFilter(f.id)}
                className={`shrink-0 rounded-md px-2.5 py-1 text-[9px] font-semibold transition-all ${
                  filter === f.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1A1A1A] text-[#B0B0B0] hover:text-[#999]'}`}>
                {t(f.k) || f.id}
              </button>
            ))}
          </div>

          {personal.length > 0 && (
            <div className="mb-3">
              <div className="flex items-center gap-1 mb-1.5">
                <Crown size={11} className="text-[#C9A84C]" />
                <span className="text-[10px] font-bold text-white">Pessoais</span>
                <span className="text-[7px] text-[#C9A84C]/60 bg-[#C9A84C]/5 px-1 py-px rounded-full font-bold">PRO</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                {personal.map(a => <AgentCard key={a.name} agent={a} onDeploy={handleDeploy} onDetails={handleDetails} isPersonal lang={lang} />)}
              </div>
            </div>
          )}

          {business.length > 0 && (
            <div className="pb-20">
              {personal.length > 0 && (
                <div className="flex items-center gap-1 mb-1.5">
                  <Bot size={11} className="text-[#777]" />
                  <span className="text-[10px] font-bold text-white">Negocio</span>
                </div>
              )}
              <div className="grid grid-cols-2 gap-1.5">
                {business.map(a => <AgentCard key={a.name} agent={a} onDeploy={handleDeploy} onDetails={handleDetails} lang={lang} />)}
              </div>
            </div>
          )}

          {filtered.length === 0 && !loading && (
            <div className="text-center py-10">
              <Bot size={28} className="text-[#999] mx-auto mb-2" />
              <p className="text-xs text-[#B0B0B0]">{t('agents.no_agents_found') || 'No agents found'}</p>
            </div>
          )}
        </div>
      )}

      {tab === 'my' && (
        <div className="px-4 pb-20 space-y-1.5">
          {myAgents.length === 0 && !loading ? (
            <div className="text-center py-10">
              <Bot size={28} className="text-[#999] mx-auto mb-2" />
              <p className="text-xs text-[#B0B0B0] mb-3">{t('agents.no_agents_yet') || 'No agents yet'}</p>
              <button onClick={() => navigate('/agents/builder')}
                className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#B89A40] px-4 py-2 text-[10px] font-bold text-[#0A0A0A] active:scale-[0.97] transition-all">
                {t('agents.create_first') || 'Create First Agent'}
              </button>
            </div>
          ) : myAgents.map(a => <MyAgentCard key={a.id} agent={a} />)}
        </div>
      )}

      <AgentDetailsDrawer
        agent={detailsAgent}
        open={!!detailsAgent}
        onClose={() => setDetailsAgent(null)}
        onDeploy={handleDeploy}
      />
    </div>
  );
}
