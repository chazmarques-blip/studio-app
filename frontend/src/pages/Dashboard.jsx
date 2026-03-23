import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { MessageSquare, Target, DollarSign, TrendingUp, Bot, CreditCard, LogOut, UserCog, Zap, Lightbulb, ChevronRight, ArrowUpRight, Megaphone, Sparkles, Shield, BarChart3, Send } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── Avatar URLs (same as Landing) ── */
const AVATARS = {
  Sarah: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/4d686b82885d8f4f90f35055251245df4e68fbfb5f3c8b9fc5b6296511151a5a.png",
  Emily: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7cf1f980e31d97ccb986f55c090c7303614a2952d6ca744b7ef14418e2ba6a4a.png",
  Sophia: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7f7b2e7ab2562fa5619f6e4f6546512e49d14080b6600d8874ae7ab6c99d109a.png",
  Carlos: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/3f76d9a72b1b7c775b44da50a077ee6f03cdbb1232efcfd607bfabc6eb3185af.png",
  James: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/88cfe39c6a5319218155267be07401ca74245e2076c5805a10e5c4aa82e5da90.png",
};
const AVATAR_LIST = Object.values(AVATARS);
const AVATAR_NAMES = Object.keys(AVATARS);

/* Map agent type/name to an avatar */
function getAgentAvatar(agent, index) {
  const nameMatch = AVATAR_NAMES.find(n => agent.name?.toLowerCase().includes(n.toLowerCase()));
  if (nameMatch) return AVATARS[nameMatch];
  return AVATAR_LIST[index % AVATAR_LIST.length];
}

/* ── Channel SVG Icons ── */
const ChannelIcon = ({ type, size = 14 }) => {
  const s = { width: size, height: size };
  switch (type) {
    case 'whatsapp': return <svg {...s} viewBox="0 0 24 24" fill="#C9A84C"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
    case 'instagram': return <svg {...s} viewBox="0 0 24 24" fill="#C9A84C"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
    case 'telegram': return <svg {...s} viewBox="0 0 24 24" fill="#C9A84C"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0 12 12 0 0011.944 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
    case 'facebook': return <svg {...s} viewBox="0 0 24 24" fill="#C9A84C"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
    case 'sms': return <svg {...s} viewBox="0 0 24 24" fill="#C9A84C"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;
    default: return <svg {...s} viewBox="0 0 24 24" fill="#C9A84C"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>;
  }
};

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

const ChartTooltip = ({ active, payload, label }) => {
  if (active && payload?.length) {
    return (
      <div className="rounded-xl border border-white/[0.06] bg-[#0E0E0E]/95 backdrop-blur-xl px-2.5 py-1.5 shadow-xl">
        <p className="text-[10px] text-[#999]">{label}</p>
        <p className="text-xs font-bold text-[#C9A84C]">{payload[0].value} msgs</p>
      </div>
    );
  }
  return null;
};

/* ── Motion variants ── */
const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  visible: (d = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.4, delay: d * 0.06, ease: [0.25, 0.46, 0.45, 0.94] } }),
};

export default function Dashboard() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [profileOpen, setProfileOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeAgentIdx, setActiveAgentIdx] = useState(0);
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

  /* Rotate featured agent */
  useEffect(() => {
    if (!stats?.agents?.length) return;
    const interval = setInterval(() => setActiveAgentIdx(p => (p + 1) % stats.agents.length), 5000);
    return () => clearInterval(interval);
  }, [stats?.agents?.length]);

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

  const pipeline = stats?.crm_pipeline || {};
  const pipelineMax = Math.max(...Object.values(pipeline).filter((_, i) => i < 4), 1);
  const agents = stats?.agents || [];
  const featuredAgent = agents[activeAgentIdx] || null;

  return (
    <div className="relative min-h-screen bg-[#0A0A0A] px-3 pt-4 pb-4 overflow-hidden">
      {/* ── Background Effects (like Landing) ── */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="dash-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(201,168,76,0.025)" strokeWidth="0.5" />
            </pattern>
            <radialGradient id="grid-fade-d" cx="50%" cy="30%" r="55%">
              <stop offset="0%" stopColor="white" stopOpacity="1" />
              <stop offset="100%" stopColor="white" stopOpacity="0" />
            </radialGradient>
            <mask id="grid-mask-d"><rect width="100%" height="100%" fill="url(#grid-fade-d)" /></mask>
          </defs>
          <rect width="100%" height="100%" fill="url(#dash-grid)" mask="url(#grid-mask-d)" />
        </svg>
        <div className="absolute left-1/4 top-0 h-[350px] w-[450px] rounded-full bg-[#C9A84C]/[0.02] blur-[140px]" />
        <div className="absolute right-0 top-1/3 h-[250px] w-[300px] rounded-full bg-[#C9A84C]/[0.015] blur-[120px]" />
      </div>

      <div className="relative z-10">
        {/* ── Header ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={0}
          className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-[11px] text-[#B0B0B0]">{t(`dashboard.${getGreeting()}`)}</p>
            <h1 data-testid="dashboard-greeting" className="text-lg font-bold text-white">{displayName}</h1>
          </div>
          <div className="flex items-center gap-2">
            <div data-testid="credit-counter" onClick={() => navigate('/pricing')}
              className="flex items-center gap-1 rounded-full border border-white/[0.06] bg-white/[0.02] px-2.5 py-1 cursor-pointer hover:border-[#C9A84C]/30 transition">
              <Zap size={11} className={usagePercent > 80 ? 'text-[#FF6B6B]' : 'text-[#C9A84C]'} />
              <span className={`text-[11px] font-bold ${usagePercent > 80 ? 'text-[#FF6B6B]' : 'text-white'}`}>{creditsLeft}</span>
              <span className="text-[9px] text-[#B0B0B0]">/{msgsLimit}</span>
            </div>
            <div className="relative" ref={profileRef}>
              <button data-testid="profile-menu-btn" onClick={() => setProfileOpen(!profileOpen)}
                className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] transition hover:shadow-md hover:shadow-[#C9A84C]/20">
                <span className="text-xs font-bold text-[#0A0A0A]">{(user?.full_name || user?.email || 'U')[0].toUpperCase()}</span>
              </button>
              {profileOpen && (
                <div data-testid="profile-dropdown" className="absolute right-0 top-10 z-50 w-48 rounded-2xl border border-white/[0.06] bg-[#0E0E0E]/95 backdrop-blur-xl p-1 shadow-2xl shadow-black/60">
                  <div className="mb-1 border-b border-white/[0.04] px-3 py-2">
                    <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'User'}</p>
                    <p className="text-[10px] text-[#B0B0B0] truncate">{user?.email}</p>
                  </div>
                  <button data-testid="profile-edit-btn" onClick={() => { setProfileOpen(false); navigate('/settings', { state: { openAccount: true } }); }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[#888] transition hover:bg-[#1A1A1A] hover:text-white">
                    <UserCog size={13} /> {t('profile.edit')}
                  </button>
                  <button data-testid="profile-billing-btn" onClick={() => { setProfileOpen(false); navigate('/pricing'); }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[#888] transition hover:bg-[#1A1A1A] hover:text-white">
                    <CreditCard size={13} /> {t('profile.billing')}
                  </button>
                  <div className="my-0.5 border-t border-white/[0.04]" />
                  <button data-testid="profile-logout-btn" onClick={async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); }}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[#888] transition hover:bg-[#1A1A1A] hover:text-[#FF6B6B]">
                    <LogOut size={13} /> {t('settings.sign_out')}
                  </button>
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* ── Featured Agent Showcase (Hero from Landing style) ── */}
        {agents.length > 0 && (
          <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={1}
            className="mb-3 glass-card p-3 overflow-hidden" data-testid="featured-agent-card">
            <div className="flex items-center gap-3">
              {/* Avatar */}
              <div className="relative shrink-0">
                {featuredAgent && (
                  <motion.div key={activeAgentIdx} initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.4 }}>
                    <div className="h-14 w-14 sm:h-16 sm:w-16 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/20 shadow-lg shadow-[#C9A84C]/10">
                      <img src={getAgentAvatar(featuredAgent, activeAgentIdx)} alt={featuredAgent.name} className="h-full w-full object-cover" />
                    </div>
                  </motion.div>
                )}
                <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#0A0A0A] bg-emerald-400" />
              </div>

              {/* Agent info */}
              <div className="flex-1 min-w-0">
                {featuredAgent && (
                  <motion.div key={activeAgentIdx} initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.3 }}>
                    <div className="flex items-center gap-1.5 mb-1 flex-wrap">
                      <p className="text-sm font-bold text-white truncate max-w-[140px] sm:max-w-none">{featuredAgent.name}</p>
                      <span className="text-[7px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#C9A84C]/10 text-[#C9A84C] shrink-0">
                        {featuredAgent.type}
                      </span>
                      <span className={`text-[7px] px-1.5 py-0.5 rounded font-mono shrink-0 ${featuredAgent.status === 'active' ? 'bg-emerald-400/10 text-emerald-400' : 'bg-[#333]/30 text-[#999]'}`}>
                        {featuredAgent.status || 'active'}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mb-1.5">
                      <div className="flex items-center gap-1">
                        <MessageSquare size={9} className="text-[#C9A84C]/50" />
                        <span className="text-[10px] text-[#B0B0B0] font-mono">{featuredAgent.conversations} chats</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Shield size={9} className="text-[#C9A84C]/50" />
                        <span className="text-[10px] text-[#B0B0B0] font-mono">{featuredAgent.resolved} resolved</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 overflow-hidden rounded-full bg-[#1A1A1A]">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${featuredAgent.conversations > 0 ? Math.round((featuredAgent.resolved / featuredAgent.conversations) * 100) : 0}%` }}
                          transition={{ duration: 0.8, delay: 0.3 }}
                          className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" />
                      </div>
                      <span className="text-[9px] font-mono text-[#C9A84C]">
                        {featuredAgent.conversations > 0 ? Math.round((featuredAgent.resolved / featuredAgent.conversations) * 100) : 0}%
                      </span>
                    </div>
                  </motion.div>
                )}
              </div>
            </div>

            {/* Agent selector row + CTA */}
            <div className="mt-2.5 flex items-center justify-between">
              <div className="flex gap-1.5">
                {agents.slice(0, 5).map((a, i) => (
                  <button key={i} onClick={() => setActiveAgentIdx(i)}
                    className={`h-7 w-7 rounded-full overflow-hidden ring-1 transition-all ${i === activeAgentIdx ? 'ring-[#C9A84C]/50 scale-110' : 'ring-white/[0.06] opacity-40 hover:opacity-70'}`}>
                    <img src={getAgentAvatar(a, i)} alt="" className="h-full w-full object-cover" />
                  </button>
                ))}
              </div>
              <button onClick={() => navigate('/agents')} data-testid="featured-agent-manage-btn"
                className="btn-gold rounded-lg px-3 py-1.5 text-[10px] flex items-center gap-1.5">
                <Bot size={11} />
                <span className="hidden sm:inline">{t('dashboard.create_agent')}</span>
                <span className="sm:hidden">Agents</span>
              </button>
            </div>
          </motion.div>
        )}

        {/* ── Quick Actions ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={2}
          className="mb-3 grid grid-cols-4 gap-2">
          {[
            { icon: Bot, label: t('dashboard.create_agent'), path: '/agents' },
            { icon: MessageSquare, label: t('dashboard.view_inbox'), path: '/chat' },
            { icon: Target, label: t('dashboard.view_crm'), path: '/crm' },
            { icon: Megaphone, label: 'Marketing', path: '/marketing' },
          ].map((a, i) => (
            <button key={i} data-testid={`quick-action-${i}`} onClick={() => navigate(a.path)}
              className="glass-card group flex flex-col items-center gap-1.5 p-3 transition hover:border-[#C9A84C]/25 hover:shadow-[0_0_15px_rgba(201,168,76,0.05)]">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#C9A84C]/[0.06] transition group-hover:bg-[#C9A84C]/[0.12] group-hover:shadow-[0_0_10px_rgba(201,168,76,0.1)]">
                <a.icon size={15} className="text-[#C9A84C]" />
              </div>
              <p className="text-center text-[9px] font-medium text-[#888] group-hover:text-[#B0B0B0] transition">{a.label}</p>
            </button>
          ))}
        </motion.div>

        {/* ── KPI Cards ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={3}
          className="mb-3 grid grid-cols-4 gap-2">
          {[
            { label: t('dashboard.messages_today'), value: stats?.messages_today || 0, icon: MessageSquare, trend: stats?.messages_today > 0 },
            { label: t('dashboard.resolution_rate'), value: `${stats?.resolution_rate || 0}%`, icon: TrendingUp },
            { label: t('dashboard.active_leads'), value: stats?.active_leads || 0, icon: Target, sub: `${stats?.total_leads || 0}` },
            { label: t('dashboard.revenue'), value: `$${(stats?.revenue || 0).toLocaleString()}`, icon: DollarSign },
          ].map((s, i) => (
            <div key={i} data-testid={`stat-${i}`} className="glass-card p-2.5 transition hover:border-[#C9A84C]/20">
              <div className="mb-1.5 flex items-center justify-between">
                <s.icon size={13} className="text-[#C9A84C]/70" />
                {s.trend && <ArrowUpRight size={10} className="text-[#C9A84C]" />}
              </div>
              <p className="text-base font-bold text-white leading-tight font-mono">{s.value}</p>
              <p className="text-[9px] text-[#B0B0B0] leading-tight mt-0.5">{s.label}</p>
            </div>
          ))}
        </motion.div>

        {/* ── Messages Chart + CRM Pipeline ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={4}
          className="mb-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-white">{t('dashboard.messages_week')}</h2>
              <span className="text-[9px] text-[#B0B0B0]">{t('dashboard.last_7_days')}</span>
            </div>
            <div className="h-[100px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats?.messages_by_day || []} margin={{ top: 2, right: 2, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gld" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#C9A84C" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#C9A84C" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#888' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: '#777' }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="count" stroke="#C9A84C" strokeWidth={1.5} fill="url(#gld)" dot={{ r: 2, fill: '#C9A84C', strokeWidth: 0 }} activeDot={{ r: 4, fill: '#C9A84C' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-white">{t('dashboard.crm_pipeline')}</h2>
              <button onClick={() => navigate('/crm')} className="text-[9px] text-[#C9A84C] hover:underline">{t('dashboard.view_all')}</button>
            </div>
            <div className="flex items-end gap-2 h-[100px]">
              {['new', 'qualified', 'proposal', 'won'].map((stage, i) => {
                const count = pipeline[stage] || 0;
                const h = Math.max(15, (count / pipelineMax) * 70);
                const opacity = 1 - i * 0.15;
                return (
                  <div key={stage} className="flex flex-1 flex-col items-center justify-end h-full">
                    <div className="w-full rounded-md transition-all hover:opacity-80" style={{ height: `${h}%`, backgroundColor: `rgba(201,168,76,${opacity})` }} />
                    <p className="mt-1 text-sm font-bold text-white">{count}</p>
                    <p className="text-[8px] text-[#B0B0B0] capitalize">{PIPELINE_LABELS[stage]}</p>
                  </div>
                );
              })}
            </div>
          </div>
        </motion.div>

        {/* ── Recent Conversations + Agent Team ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={5}
          className="mb-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
          {/* Recent Conversations */}
          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-white">{t('dashboard.recent_chats')}</h2>
              <button onClick={() => navigate('/chat')} className="text-[9px] text-[#C9A84C] hover:underline">{t('dashboard.view_all')}</button>
            </div>
            {(stats?.recent_conversations || []).length > 0 ? (
              <div className="space-y-1">
                {stats.recent_conversations.map(c => (
                  <div key={c.id} className="flex items-center gap-2.5 rounded-xl bg-white/[0.015] border border-white/[0.04] p-2 transition hover:bg-white/[0.03] hover:border-white/[0.08] cursor-pointer" onClick={() => navigate('/chat')}>
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/[0.03]">
                      <ChannelIcon type={c.channel_type} size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-xs font-medium text-white">{c.contact_name}</p>
                      <p className="text-[9px] capitalize text-[#B0B0B0]">{c.channel_type}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={`inline-block rounded-full px-1.5 py-px text-[8px] font-medium ${c.status === 'active' ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'bg-[#333]/30 text-[#999]'}`}>
                        {c.status}
                      </span>
                      <p className="mt-0.5 text-[9px] text-[#999]">{timeAgo(c.last_message_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-4 text-center">
                <MessageSquare size={20} className="mx-auto mb-1.5 text-[#444]" />
                <p className="text-[10px] text-[#B0B0B0]">{t('dashboard.no_conversations')}</p>
              </div>
            )}
          </div>

          {/* Agent Team (with Avatars like Landing Page) */}
          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-white">{t('dashboard.agent_performance')}</h2>
              <button onClick={() => navigate('/agents')} className="text-[9px] text-[#C9A84C] hover:underline">{t('dashboard.view_all')}</button>
            </div>
            {agents.length > 0 ? (
              <div className="space-y-1">
                {agents.map((a, idx) => (
                  <div key={a.id} className="flex items-center gap-2.5 rounded-xl bg-white/[0.015] border border-white/[0.04] p-2 transition hover:bg-white/[0.03] hover:border-white/[0.08]">
                    {/* Avatar photo instead of generic icon */}
                    <div className="relative">
                      <div className="h-8 w-8 rounded-full overflow-hidden ring-1 ring-[#C9A84C]/15">
                        <img src={getAgentAvatar(a, idx)} alt={a.name} className="h-full w-full object-cover" />
                      </div>
                      <div className={`absolute -bottom-px -right-px h-2 w-2 rounded-full border border-[#0A0A0A] ${a.status === 'active' ? 'bg-emerald-400' : 'bg-[#666]'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <p className="truncate text-xs font-medium text-white">{a.name}</p>
                        <span className="text-[9px] font-mono text-[#C9A84C] ml-2">{a.resolved > 0 ? Math.round((a.resolved / Math.max(a.conversations, 1)) * 100) : 0}%</span>
                      </div>
                      <div className="h-1 overflow-hidden rounded-full bg-[#1A1A1A]">
                        <div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] transition-all duration-700" style={{ width: `${a.conversations > 0 ? Math.round((a.resolved / a.conversations) * 100) : 0}%` }} />
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        <p className="text-[8px] capitalize text-[#888]">{a.type}</p>
                        <span className="text-[8px] text-[#666]">{a.conversations} chats / {a.resolved} resolved</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-4 text-center">
                {/* Avatar collage for empty state */}
                <div className="flex justify-center -space-x-2 mb-3">
                  {AVATAR_LIST.slice(0, 4).map((av, i) => (
                    <div key={i} className="h-8 w-8 rounded-full overflow-hidden ring-2 ring-[#0A0A0A] opacity-40">
                      <img src={av} alt="" className="h-full w-full object-cover" />
                    </div>
                  ))}
                </div>
                <p className="mb-1.5 text-[10px] text-[#B0B0B0]">{t('dashboard.no_agents')}</p>
                <button onClick={() => navigate('/agents')} className="btn-gold rounded-lg px-3 py-1 text-[10px]">{t('dashboard.create_first')}</button>
              </div>
            )}
          </div>
        </motion.div>

        {/* ── AI Insights Widget ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={6}
          data-testid="ai-insights-widget" className="mb-3 glass-card p-3 border-[#C9A84C]/15">
          <div className="mb-2 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#C9A84C]/10">
              <Lightbulb size={12} className="text-[#C9A84C]" />
            </div>
            <h2 className="text-xs font-semibold text-white">{t('dashboard.ai_insights')}</h2>
            <span className="ml-auto rounded-full bg-[#C9A84C]/10 px-2 py-0.5 text-[8px] font-semibold text-[#C9A84C] uppercase tracking-wide">AI</span>
          </div>
          <div className="space-y-1.5">
            {[
              { text: t('dashboard.insight_1', { count: pipeline.qualified || 0 }), type: 'alert' },
              { text: t('dashboard.insight_2', { count: stats?.agents_count || 0 }), type: 'tip' },
              { text: t('dashboard.insight_3'), type: 'opportunity' },
            ].map((insight, i) => (
              <div key={i} className="flex items-start gap-2 rounded-xl bg-white/[0.015] border border-white/[0.04] p-2">
                <div className="mt-0.5 h-1 w-1 shrink-0 rounded-full bg-[#C9A84C]" />
                <p className="text-[10px] leading-relaxed text-[#999]">{insight.text}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* ── Plan & Usage ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={7}
          className="glass-card p-3">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-[9px] text-[#B0B0B0]">{t('dashboard.current_plan')}</p>
              <p className="text-xs font-bold text-white capitalize">{stats?.plan || 'free'}</p>
            </div>
            <button onClick={() => navigate('/pricing')} className="rounded-full border border-[#C9A84C]/25 px-2.5 py-0.5 text-[9px] font-medium text-[#C9A84C] transition hover:bg-[#C9A84C]/10">
              {t('dashboard.upgrade')}
            </button>
          </div>
          <div className="space-y-1.5">
            <div>
              <div className="flex justify-between text-[9px] mb-0.5">
                <span className="text-[#B0B0B0]">{t('dashboard.messages_usage')}</span>
                <span className={usagePercent > 80 ? 'text-[#FF6B6B] font-semibold' : 'text-[#888]'}>{msgsUsed}/{msgsLimit}</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-[#1A1A1A]">
                <div className={`h-full rounded-full transition-all duration-500 ${usagePercent > 80 ? 'bg-[#FF6B6B]' : 'bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]'}`} style={{ width: `${usagePercent}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[9px] mb-0.5">
                <span className="text-[#B0B0B0]">{t('dashboard.agents_usage')}</span>
                <span className="text-[#888]">{stats?.agents_count || 0}/{stats?.agents_limit || 1}</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-[#1A1A1A]">
                <div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] transition-all duration-500" style={{ width: `${Math.min(100, ((stats?.agents_count || 0) / (stats?.agents_limit || 1)) * 100)}%` }} />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
