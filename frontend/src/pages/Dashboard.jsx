import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Target, DollarSign, TrendingUp, Bot, CreditCard, LogOut, UserCog } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [agents, setAgents] = useState([]);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef(null);
  const displayName = user?.full_name || user?.email?.split('@')[0] || 'User';

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (profileRef.current && !profileRef.current.contains(e.target)) setProfileOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => setStats(r.data)).catch(() => {});
    axios.get(`${API}/agents`).then(r => setAgents(r.data.agents || [])).catch(() => {});
  }, []);

  const statCards = [
    { label: t('dashboard.messages_today'), value: stats?.messages_today || 0, icon: MessageSquare, color: '#C9A84C' },
    { label: t('dashboard.resolution_rate'), value: `${stats?.resolution_rate || 0}%`, icon: TrendingUp, color: '#4CAF50' },
    { label: t('dashboard.active_leads'), value: stats?.active_leads || 0, icon: Target, color: '#2196F3' },
    { label: t('dashboard.revenue'), value: `$${stats?.revenue || 0}`, icon: DollarSign, color: '#C9A84C' },
  ];

  const msgsUsed = stats?.messages_used || 0;
  const msgsLimit = stats?.messages_limit || 50;
  const usagePercent = msgsLimit > 0 ? Math.min(100, Math.round((msgsUsed / msgsLimit) * 100)) : 0;

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs text-[#666666]">{t('dashboard.welcome')}</p>
          <h1 data-testid="dashboard-greeting" className="text-xl font-bold text-white">{displayName}</h1>
        </div>
        <div className="relative" ref={profileRef}>
          <button data-testid="profile-menu-btn" onClick={() => setProfileOpen(!profileOpen)}
            className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] transition-all hover:shadow-lg hover:shadow-[#C9A84C]/20">
            <span className="text-sm font-bold text-[#0A0A0A]">{(user?.full_name || user?.email || 'U')[0].toUpperCase()}</span>
          </button>
          {profileOpen && (
            <div data-testid="profile-dropdown" className="absolute right-0 top-12 z-50 w-56 rounded-xl border border-[#2A2A2A] bg-[#141414] p-1.5 shadow-2xl shadow-black/50 animate-in fade-in slide-in-from-top-2 duration-200">
              <div className="mb-1.5 border-b border-[#2A2A2A] px-3 py-2.5">
                <p className="text-sm font-semibold text-white">{user?.full_name || 'User'}</p>
                <p className="text-xs text-[#666]">{user?.email}</p>
              </div>
              <button data-testid="profile-edit-btn" onClick={() => { setProfileOpen(false); navigate('/settings', { state: { openAccount: true } }); }}
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-[#A0A0A0] transition hover:bg-[#1E1E1E] hover:text-white">
                <UserCog size={15} /> {t('profile.edit')}
              </button>
              <button data-testid="profile-billing-btn" onClick={() => { setProfileOpen(false); navigate('/pricing'); }}
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-[#A0A0A0] transition hover:bg-[#1E1E1E] hover:text-white">
                <CreditCard size={15} /> {t('profile.billing')}
              </button>
              <div className="my-1 border-t border-[#2A2A2A]" />
              <button data-testid="profile-logout-btn" onClick={async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); }}
                className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-red-400 transition hover:bg-red-500/10">
                <LogOut size={15} /> {t('settings.sign_out')}
              </button>
            </div>
          )}
        </div>
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3">
        {statCards.map((s, i) => (
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
        {agents.length > 0 ? (
          <div className="space-y-2">
            {agents.map(agent => (
              <div key={agent.id} className="glass-card flex items-center gap-3 p-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#C9A84C]/10"><Bot size={18} className="text-[#C9A84C]" /></div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white">{agent.name}</p>
                  <p className="text-xs capitalize text-[#666666]">{agent.type} - {agent.status}</p>
                </div>
                <div className="h-2 w-2 rounded-full bg-[#4CAF50]" />
              </div>
            ))}
          </div>
        ) : (
          <div className="glass-card p-6 text-center">
            <Bot size={32} className="mx-auto mb-3 text-[#2A2A2A]" />
            <p className="mb-1 text-sm text-[#A0A0A0]">{t('dashboard.no_agents')}</p>
            <p className="mb-4 text-xs text-[#666666]">{t('dashboard.no_agents_desc')}</p>
            <button onClick={() => navigate('/agents')} className="btn-gold rounded-lg px-6 py-2 text-xs">{t('dashboard.create_first')}</button>
          </div>
        )}
      </div>
      <div className="mb-6 glass-card p-4">
        <div className="flex items-center justify-between">
          <div><p className="text-xs text-[#666666]">{t('dashboard.current_plan')}</p><p className="text-sm font-semibold text-white">{t(`common.${stats?.plan || 'free'}`)}</p></div>
          <div className="text-right"><p className="text-xs text-[#666666]">{t('dashboard.messages_week')}</p><p className="text-sm font-semibold text-white">{msgsUsed} / {msgsLimit}</p></div>
        </div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[#1E1E1E]"><div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" style={{ width: `${usagePercent}%` }} /></div>
      </div>
    </div>
  );
}
