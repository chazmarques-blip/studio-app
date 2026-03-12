import { useAuth } from '../contexts/AuthContext';
import { MessageSquare, Users, Target, DollarSign, TrendingUp, Bot } from 'lucide-react';

const stats = [
  { label: 'Messages Today', value: '0', icon: MessageSquare, trend: null, color: '#C9A84C' },
  { label: 'Resolution Rate', value: '0%', icon: TrendingUp, trend: null, color: '#4CAF50' },
  { label: 'Active Leads', value: '0', icon: Target, trend: null, color: '#2196F3' },
  { label: 'Revenue', value: '$0', icon: DollarSign, trend: null, color: '#C9A84C' },
];

export default function Dashboard() {
  const { user } = useAuth();
  const displayName = user?.full_name || user?.user_metadata?.full_name || user?.email?.split('@')[0] || 'User';

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs text-[#666666]">Welcome back</p>
          <h1 data-testid="dashboard-greeting" className="text-xl font-bold text-white">{displayName}</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1A1A1A] border border-[#2A2A2A]">
            <Users size={16} className="text-[#A0A0A0]" />
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="mb-6 grid grid-cols-2 gap-3">
        {stats.map((s, i) => (
          <div key={i} data-testid={`stat-${s.label.toLowerCase().replace(/\s/g, '-')}`} className="glass-card p-4">
            <div className="mb-2 flex items-center justify-between">
              <s.icon size={16} style={{ color: s.color }} />
            </div>
            <p className="text-lg font-bold text-white">{s.value}</p>
            <p className="text-xs text-[#666666]">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3">
          <button data-testid="quick-create-agent" className="glass-card flex items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C]/10">
              <Bot size={18} className="text-[#C9A84C]" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">Create Agent</p>
              <p className="text-xs text-[#666666]">Deploy a new AI agent</p>
            </div>
          </button>
          <button data-testid="quick-view-inbox" className="glass-card flex items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C]/10">
              <MessageSquare size={18} className="text-[#C9A84C]" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">View Inbox</p>
              <p className="text-xs text-[#666666]">Check conversations</p>
            </div>
          </button>
        </div>
      </div>

      {/* Active Agents */}
      <div className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">Active Agents</h2>
        <div className="glass-card p-6 text-center">
          <Bot size={32} className="mx-auto mb-3 text-[#2A2A2A]" />
          <p className="mb-1 text-sm text-[#A0A0A0]">No agents yet</p>
          <p className="mb-4 text-xs text-[#666666]">Create your first AI agent to get started</p>
          <button className="btn-gold rounded-lg px-6 py-2 text-xs">Create Your First Agent</button>
        </div>
      </div>

      {/* Plan Status */}
      <div className="mb-6 glass-card p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-[#666666]">Current Plan</p>
            <p className="text-sm font-semibold text-white">Free</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-[#666666]">Messages this week</p>
            <p className="text-sm font-semibold text-white">0 / 50</p>
          </div>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#1E1E1E]">
          <div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" style={{ width: '0%' }} />
        </div>
      </div>
    </div>
  );
}
