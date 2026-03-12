import { useState, useEffect } from 'react';
import { Bot, Search, Plus, Star } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const typeColors = {
  sales: '#C9A84C',
  support: '#2196F3',
  scheduling: '#4CAF50',
  sac: '#FF9800',
  onboarding: '#9C27B0',
  custom: '#666666',
};

export default function Agents() {
  const [agents, setAgents] = useState([]);
  const [filter, setFilter] = useState('All');

  useEffect(() => {
    axios.get(`${API}/agents/marketplace`).then(r => setAgents(r.data.agents)).catch(() => {});
  }, []);

  const types = ['All', 'Sales', 'Support', 'Scheduling', 'SAC', 'Custom'];

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Agent Marketplace</h1>
        <button data-testid="create-agent-btn" className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C] text-[#0A0A0A]">
          <Plus size={18} />
        </button>
      </div>

      {/* Search */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
        <input
          data-testid="agent-search"
          type="text"
          placeholder="Search agents..."
          className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2.5 pl-9 pr-4 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]"
        />
      </div>

      {/* Filter */}
      <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
        {types.map(t => (
          <button
            key={t}
            onClick={() => setFilter(t)}
            className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${
              filter === t
                ? 'bg-[#C9A84C] text-[#0A0A0A]'
                : 'bg-[#1A1A1A] text-[#A0A0A0] border border-[#2A2A2A]'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Agent Grid */}
      <div className="grid gap-3 sm:grid-cols-2">
        {agents.map((agent, i) => (
          <div key={i} data-testid={`agent-card-${agent.name.toLowerCase()}`} className="glass-card group p-4 transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ backgroundColor: `${typeColors[agent.type]}15` }}>
                <Bot size={20} style={{ color: typeColors[agent.type] }} />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-white">{agent.name}</h3>
                <span className="text-xs capitalize text-[#A0A0A0]">{agent.type}</span>
              </div>
              <div className="flex items-center gap-1">
                <Star size={12} className="fill-[#C9A84C] text-[#C9A84C]" />
                <span className="text-xs text-[#A0A0A0]">4.8</span>
              </div>
            </div>
            <p className="mb-3 text-xs leading-relaxed text-[#666666]">{agent.description}</p>
            <button className="btn-gold w-full rounded-lg py-2 text-xs">Deploy Agent</button>
          </div>
        ))}
      </div>
    </div>
  );
}
