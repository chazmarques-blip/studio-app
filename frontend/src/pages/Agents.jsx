import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, Search, Plus, Star } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const typeColors = { sales: '#C9A84C', support: '#2196F3', scheduling: '#4CAF50', sac: '#FF9800', onboarding: '#9C27B0', custom: '#666666' };

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    axios.get(`${API}/agents/marketplace`).then(r => setAgents(r.data.agents)).catch(() => {});
  }, []);

  const typeFilters = [
    { value: 'all', label: t('agents.all') },
    { value: 'sales', label: t('agents.type_sales') },
    { value: 'support', label: t('agents.type_support') },
    { value: 'scheduling', label: t('agents.type_scheduling') },
    { value: 'sac', label: t('agents.type_sac') },
    { value: 'onboarding', label: t('agents.type_onboarding') },
  ];

  const filtered = agents.filter(a => {
    const matchType = filter === 'all' || a.type === filter;
    const matchSearch = !search || a.name.toLowerCase().includes(search.toLowerCase()) || a.description.toLowerCase().includes(search.toLowerCase());
    return matchType && matchSearch;
  });

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('agents.marketplace')}</h1>
        <button data-testid="create-agent-btn" onClick={() => navigate('/agents/builder')} className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C] text-[#0A0A0A]"><Plus size={18} /></button>
      </div>
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
        <input data-testid="agent-search" type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder={t('agents.search')} className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2.5 pl-9 pr-4 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
      </div>
      <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
        {typeFilters.map(tf => (
          <button key={tf.value} onClick={() => setFilter(tf.value)} className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${filter === tf.value ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#A0A0A0] border border-[#2A2A2A]'}`}>{tf.label}</button>
        ))}
      </div>
      <p className="mb-3 text-xs text-[#666666]">{t('agents.count', { count: filtered.length })}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {filtered.map((agent, i) => (
          <div key={i} data-testid={`agent-card-${agent.name.toLowerCase()}`} className="glass-card group p-4 transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ backgroundColor: `${typeColors[agent.type] || '#666'}15` }}>
                <Bot size={20} style={{ color: typeColors[agent.type] || '#666' }} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                <span className="text-xs capitalize text-[#A0A0A0]">{t(`agents.type_${agent.type}`, agent.type)}</span>
              </div>
              <div className="flex items-center gap-1"><Star size={12} className="fill-[#C9A84C] text-[#C9A84C]" /><span className="text-xs text-[#A0A0A0]">{agent.rating || '4.5'}</span></div>
            </div>
            <p className="mb-3 text-xs leading-relaxed text-[#666666]">{agent.description}</p>
            <button className="btn-gold w-full rounded-lg py-2 text-xs">{t('agents.deploy')}</button>
          </div>
        ))}
      </div>
    </div>
  );
}
