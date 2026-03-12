import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Target, DollarSign, TrendingUp, Bot, CreditCard, LogOut, UserCog, Zap, Clock, ArrowUpRight, ArrowDownRight, Users, Send, ChevronRight } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CHANNEL_COLORS = { whatsapp: '#25D366', telegram: '#0088CC', instagram: '#E4405F', facebook: '#1877F2', sms: '#FF9800', web: '#C9A84C' };
const PIPELINE_COLORS = { new: '#C9A84C', qualified: '#2196F3', proposal: '#9C27B0', won: '#4CAF50', lost: '#666' };
const PIPELINE_LABELS = { new: 'New', qualified: 'Qualified', proposal: 'Proposal', won: 'Won', lost: 'Lost' };

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'greeting_morning';
  if (h < 18) return 'greeting_afternoon';
  return 'greeting_evening';
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'now';
  if (mins < 60) return `${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h`;
  return `${Math.floor(hrs / 24)}d`;
}

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-lg border border-[#2A2A2A] bg-[#141414] px-3 py-2 shadow-xl">
        <p className="text-xs text-[#666]">{label}</p>
        <p className="text-sm font-bold text-[#C9A84C]">{payload[0].value} msgs</p>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(true);
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
    axios.get(`${API}/dashboard/stats`).then(r => { setStats(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const msgsUsed = stats?.messages_used || 0;
  const msgsLimit = stats?.messages_limit || 50;
  const usagePercent = msgsLimit > 0 ? Math.min(100, Math.round((msgsUsed / msgsLimit) * 100)) : 0;
  const creditsLeft = msgsLimit - msgsUsed;

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-5 pb-6">
      {/* Header */}
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs text-[#666]">{t(`dashboard.${getGreeting()}`)}</p>
          <h1 data-testid="dashboard-greeting" className="text-xl font-bold text-white">{displayName}</h1>
        </div>
        <div className="flex items-center gap-3">
          {/* Credit Counter */}
          <div data-testid="credit-counter" className="flex items-center gap-1.5 rounded-full border border-[#2A2A2A] bg-[#141414] px-3 py-1.5 cursor-pointer hover:border-[#C9A84C]/40 transition" onClick={() => navigate('/pricing')}>
            <Zap size={13} className={usagePercent > 80 ? 'text-red-400' : 'text-[#C9A84C]'} />
            <span className={`text-xs font-semibold ${usagePercent > 80 ? 'text-red-400' : 'text-white'}`}>{creditsLeft}</span>
            <span className="text-[10px] text-[#666]">/ {msgsLimit}</span>
          </div>
          {/* Profile */}
          <div className="relative" ref={profileRef}>
            <button data-testid="profile-menu-btn" onClick={() => setProfileOpen(!profileOpen)}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] transition-all hover:shadow-lg hover:shadow-[#C9A84C]/20">
              <span className="text-sm font-bold text-[#0A0A0A]">{(user?.full_name || user?.email || 'U')[0].toUpperCase()}</span>
            </button>
            {profileOpen && (
              <div data-testid="profile-dropdown" className="absolute right-0 top-11 z-50 w-52 rounded-xl border border-[#2A2A2A] bg-[#141414] p-1.5 shadow-2xl shadow-black/50">
                <div className="mb-1.5 border-b border-[#2A2A2A] px-3 py-2">
                  <p className="text-sm font-semibold text-white">{user?.full_name || 'User'}</p>
                  <p className="text-[11px] text-[#666]">{user?.email}</p>
                </div>
                <button data-testid="profile-edit-btn" onClick={() => { setProfileOpen(false); navigate('/settings', { state: { openAccount: true } }); }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-[#A0A0A0] transition hover:bg-[#1E1E1E] hover:text-white">
                  <UserCog size={14} /> {t('profile.edit')}
                </button>
                <button data-testid="profile-billing-btn" onClick={() => { setProfileOpen(false); navigate('/pricing'); }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-[#A0A0A0] transition hover:bg-[#1E1E1E] hover:text-white">
                  <CreditCard size={14} /> {t('profile.billing')}
                </button>
                <div className="my-1 border-t border-[#2A2A2A]" />
                <button data-testid="profile-logout-btn" onClick={async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-red-400 transition hover:bg-red-500/10">
                  <LogOut size={14} /> {t('settings.sign_out')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="mb-5 grid grid-cols-2 gap-2.5">
        {[
          { label: t('dashboard.messages_today'), value: stats?.messages_today || 0, icon: MessageSquare, color: '#C9A84C', trend: stats?.messages_today > 0 ? '+' : null },
          { label: t('dashboard.resolution_rate'), value: `${stats?.resolution_rate || 0}%`, icon: TrendingUp, color: '#4CAF50', trend: stats?.resolution_rate > 50 ? '+' : null },
          { label: t('dashboard.active_leads'), value: stats?.active_leads || 0, icon: Target, color: '#2196F3', sub: `${stats?.total_leads || 0} total` },
          { label: t('dashboard.revenue'), value: `$${(stats?.revenue || 0).toLocaleString()}`, icon: DollarSign, color: '#C9A84C' },
        ].map((s, i) => (
          <div key={i} data-testid={`stat-${i}`} className="group glass-card p-3.5 transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="mb-2 flex items-center justify-between">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg" style={{ backgroundColor: `${s.color}15` }}>
                <s.icon size={15} style={{ color: s.color }} />
              </div>
              {s.trend && <span className="flex items-center text-[10px] text-[#4CAF50]"><ArrowUpRight size={10} />{s.trend}</span>}
            </div>
            <p className="text-lg font-bold text-white">{s.value}</p>
            <p className="text-[11px] text-[#666]">{s.label}</p>
            {s.sub && <p className="text-[10px] text-[#555]">{s.sub}</p>}
          </div>
        ))}
      </div>

      {/* Messages Chart */}
      <div className="mb-5 glass-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">{t('dashboard.messages_week')}</h2>
          <span className="text-[10px] text-[#666]">{t('dashboard.last_7_days')}</span>
        </div>
        <div className="h-[140px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={stats?.messages_by_day || []} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="msgGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#C9A84C" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#C9A84C" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="label" tick={{ fontSize: 10, fill: '#666' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#555' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="count" stroke="#C9A84C" strokeWidth={2} fill="url(#msgGrad)" dot={{ r: 3, fill: '#C9A84C', strokeWidth: 0 }} activeDot={{ r: 5, fill: '#C9A84C' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* CRM Pipeline */}
      <div className="mb-5 glass-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">{t('dashboard.crm_pipeline')}</h2>
          <button onClick={() => navigate('/crm')} className="text-[10px] text-[#C9A84C] hover:underline">{t('dashboard.view_all')}</button>
        </div>
        <div className="flex gap-1.5">
          {Object.entries(stats?.crm_pipeline || {}).filter(([k]) => k !== 'lost').map(([stage, count]) => {
            const total = Object.values(stats?.crm_pipeline || {}).reduce((a, b) => a + b, 0) || 1;
            const pct = Math.max(8, Math.round((count / total) * 100));
            return (
              <div key={stage} className="flex flex-col items-center" style={{ flex: `${pct} 0 0%` }}>
                <div className="mb-1.5 h-16 w-full rounded-lg flex items-end justify-center transition-all hover:opacity-80" style={{ backgroundColor: `${PIPELINE_COLORS[stage]}20` }}>
                  <div className="w-full rounded-lg" style={{ height: `${Math.max(20, (count / (Math.max(...Object.values(stats?.crm_pipeline || { x: 1 })) || 1)) * 100)}%`, backgroundColor: PIPELINE_COLORS[stage] }} />
                </div>
                <p className="text-base font-bold text-white">{count}</p>
                <p className="text-[9px] text-[#666] capitalize">{PIPELINE_LABELS[stage]}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Conversations + Agent Performance side by side on larger screens */}
      <div className="mb-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Recent Conversations */}
        <div className="glass-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">{t('dashboard.recent_chats')}</h2>
            <button onClick={() => navigate('/chat')} className="text-[10px] text-[#C9A84C] hover:underline">{t('dashboard.view_all')}</button>
          </div>
          {(stats?.recent_conversations || []).length > 0 ? (
            <div className="space-y-2">
              {stats.recent_conversations.map(c => (
                <div key={c.id} className="flex items-center gap-3 rounded-lg bg-[#111] p-2.5 transition hover:bg-[#1A1A1A] cursor-pointer" onClick={() => navigate('/chat')}>
                  <div className="flex h-8 w-8 items-center justify-center rounded-full" style={{ backgroundColor: `${CHANNEL_COLORS[c.channel_type] || '#C9A84C'}20` }}>
                    <MessageSquare size={13} style={{ color: CHANNEL_COLORS[c.channel_type] || '#C9A84C' }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium text-white">{c.contact_name}</p>
                    <p className="text-[10px] capitalize text-[#666]">{c.channel_type}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-[9px] font-medium ${c.status === 'active' ? 'bg-[#4CAF50]/15 text-[#4CAF50]' : 'bg-[#666]/15 text-[#666]'}`}>
                      {c.status}
                    </span>
                    <p className="mt-0.5 text-[10px] text-[#555]">{timeAgo(c.last_message_at)}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center">
              <MessageSquare size={24} className="mx-auto mb-2 text-[#2A2A2A]" />
              <p className="text-xs text-[#666]">{t('dashboard.no_conversations')}</p>
            </div>
          )}
        </div>

        {/* Agent Performance */}
        <div className="glass-card p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">{t('dashboard.agent_performance')}</h2>
            <button onClick={() => navigate('/agents')} className="text-[10px] text-[#C9A84C] hover:underline">{t('dashboard.view_all')}</button>
          </div>
          {(stats?.agents || []).length > 0 ? (
            <div className="space-y-2">
              {stats.agents.map(a => (
                <div key={a.id} className="flex items-center gap-3 rounded-lg bg-[#111] p-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10">
                    <Bot size={14} className="text-[#C9A84C]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate text-sm font-medium text-white">{a.name}</p>
                    <p className="text-[10px] capitalize text-[#666]">{a.type}</p>
                  </div>
                  <div className="flex items-center gap-3 text-right">
                    <div>
                      <p className="text-sm font-bold text-white">{a.conversations}</p>
                      <p className="text-[9px] text-[#666]">chats</p>
                    </div>
                    <div className="h-6 w-px bg-[#2A2A2A]" />
                    <div>
                      <p className="text-sm font-bold text-[#4CAF50]">{a.resolved}</p>
                      <p className="text-[9px] text-[#666]">{t('dashboard.resolved')}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-6 text-center">
              <Bot size={24} className="mx-auto mb-2 text-[#2A2A2A]" />
              <p className="mb-2 text-xs text-[#666]">{t('dashboard.no_agents')}</p>
              <button onClick={() => navigate('/agents')} className="btn-gold rounded-lg px-4 py-1.5 text-xs">{t('dashboard.create_first')}</button>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mb-5">
        <h2 className="mb-2.5 text-sm font-semibold text-[#A0A0A0]">{t('dashboard.quick_actions')}</h2>
        <div className="grid grid-cols-3 gap-2">
          {[
            { icon: Bot, label: t('dashboard.create_agent'), path: '/agents', color: '#C9A84C' },
            { icon: MessageSquare, label: t('dashboard.view_inbox'), path: '/chat', color: '#2196F3' },
            { icon: Target, label: t('dashboard.view_crm'), path: '/crm', color: '#9C27B0' },
          ].map((a, i) => (
            <button key={i} data-testid={`quick-action-${i}`} onClick={() => navigate(a.path)}
              className="glass-card flex flex-col items-center gap-2 p-4 transition-all hover:border-[rgba(201,168,76,0.3)]">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl" style={{ backgroundColor: `${a.color}15` }}>
                <a.icon size={16} style={{ color: a.color }} />
              </div>
              <p className="text-center text-[11px] font-medium text-[#A0A0A0]">{a.label}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Plan & Usage */}
      <div className="glass-card p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="text-[10px] text-[#666]">{t('dashboard.current_plan')}</p>
            <p className="text-sm font-bold text-white capitalize">{stats?.plan || 'free'}</p>
          </div>
          <button onClick={() => navigate('/pricing')} className="rounded-full border border-[#C9A84C]/30 px-3 py-1 text-[10px] font-medium text-[#C9A84C] transition hover:bg-[#C9A84C]/10">
            {t('dashboard.upgrade')}
          </button>
        </div>
        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-[#666]">{t('dashboard.messages_usage')}</span>
              <span className={usagePercent > 80 ? 'text-red-400 font-semibold' : 'text-[#A0A0A0]'}>{msgsUsed} / {msgsLimit}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-[#1E1E1E]">
              <div className={`h-full rounded-full transition-all duration-500 ${usagePercent > 80 ? 'bg-gradient-to-r from-red-500 to-red-400' : 'bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]'}`} style={{ width: `${usagePercent}%` }} />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-[10px] mb-1">
              <span className="text-[#666]">{t('dashboard.agents_usage')}</span>
              <span className="text-[#A0A0A0]">{stats?.agents_count || 0} / {stats?.agents_limit || 1}</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-[#1E1E1E]">
              <div className="h-full rounded-full bg-gradient-to-r from-[#2196F3] to-[#42A5F5] transition-all duration-500" style={{ width: `${Math.min(100, ((stats?.agents_count || 0) / (stats?.agents_limit || 1)) * 100)}%` }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
