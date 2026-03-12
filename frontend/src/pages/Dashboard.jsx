import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Users, Target, DollarSign, TrendingUp, Bot } from 'lucide-react';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const displayName = user?.full_name || user?.email?.split('@')[0] || 'User';

  const stats = [
    { label: t('dashboard.messages_today'), value: '0', icon: MessageSquare, color: '#C9A84C' },
    { label: t('dashboard.resolution_rate'), value: '0%', icon: TrendingUp, color: '#4CAF50' },
    { label: t('dashboard.active_leads'), value: '0', icon: Target, color: '#2196F3' },
    { label: t('dashboard.revenue'), value: '$0', icon: DollarSign, color: '#C9A84C' },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs text-[#666666]">{t('dashboard.welcome')}</p>
          <h1 data-testid="dashboard-greeting" className="text-xl font-bold text-white">{displayName}</h1>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1A1A1A] border border-[#2A2A2A]"><Users size={16} className="text-[#A0A0A0]" /></div>
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3">
        {stats.map((s, i) => (
          <div key={i} data-testid={`stat-${i}`} className="glass-card p-4">
            <div className="mb-2"><s.icon size={16} style={{ color: s.color }} /></div>
            <p className="text-lg font-bold text-white">{s.value}</p>
            <p className="text-xs text-[#666666]">{s.label}</p>
          </div>
        ))}
      </div>
      <div className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">{t('dashboard.quick_actions')}</h2>
        <div className="grid grid-cols-2 gap-3">
          <button data-testid="quick-create-agent" onClick={() => navigate('/agents')} className="glass-card flex items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C]/10"><Bot size={18} className="text-[#C9A84C]" /></div>
            <div><p className="text-sm font-medium text-white">{t('dashboard.create_agent')}</p><p className="text-xs text-[#666666]">{t('dashboard.create_agent_desc')}</p></div>
          </button>
          <button data-testid="quick-view-inbox" onClick={() => navigate('/chat')} className="glass-card flex items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#C9A84C]/10"><MessageSquare size={18} className="text-[#C9A84C]" /></div>
            <div><p className="text-sm font-medium text-white">{t('dashboard.view_inbox')}</p><p className="text-xs text-[#666666]">{t('dashboard.view_inbox_desc')}</p></div>
          </button>
        </div>
      </div>
      <div className="mb-6">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">{t('dashboard.active_agents')}</h2>
        <div className="glass-card p-6 text-center">
          <Bot size={32} className="mx-auto mb-3 text-[#2A2A2A]" />
          <p className="mb-1 text-sm text-[#A0A0A0]">{t('dashboard.no_agents')}</p>
          <p className="mb-4 text-xs text-[#666666]">{t('dashboard.no_agents_desc')}</p>
          <button onClick={() => navigate('/agents')} className="btn-gold rounded-lg px-6 py-2 text-xs">{t('dashboard.create_first')}</button>
        </div>
      </div>
      <div className="mb-6 glass-card p-4">
        <div className="flex items-center justify-between">
          <div><p className="text-xs text-[#666666]">{t('dashboard.current_plan')}</p><p className="text-sm font-semibold text-white">{t('common.free')}</p></div>
          <div className="text-right"><p className="text-xs text-[#666666]">{t('dashboard.messages_week')}</p><p className="text-sm font-semibold text-white">0 / 50</p></div>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#1E1E1E]"><div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" style={{ width: '0%' }} /></div>
      </div>
    </div>
  );
}
