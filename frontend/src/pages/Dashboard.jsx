import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { MessageSquare, Target, DollarSign, TrendingUp, Bot, Lightbulb, ArrowUpRight, Megaphone, Shield } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── Channel SVG Icons ── */
const ChannelIcon = ({ type, size = 14 }) => {
  const s = { width: size, height: size };
  switch (type) {
    case 'whatsapp': return <svg {...s} viewBox="0 0 24 24" fill="#F97316"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
    case 'instagram': return <svg {...s} viewBox="0 0 24 24" fill="#F97316"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
    case 'telegram': return <svg {...s} viewBox="0 0 24 24" fill="#F97316"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0 12 12 0 0011.944 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
    case 'facebook': return <svg {...s} viewBox="0 0 24 24" fill="#F97316"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
    case 'sms': return <svg {...s} viewBox="0 0 24 24" fill="#F97316"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;
    default: return <svg {...s} viewBox="0 0 24 24" fill="#F97316"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>;
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
      <div className="rounded-xl border border-gray-200 bg-white/95 backdrop-blur-xl px-3 py-2 shadow-xl">
        <p className="text-xs text-gray-500">{label}</p>
        <p className="text-sm font-bold text-orange-600">{payload[0].value} msgs</p>
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => { setStats(r.data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-white">
        <div className="h-10 w-10 animate-spin rounded-full border-3 border-gray-200 border-t-orange-500" />
      </div>
    );
  }

  const pipeline = stats?.crm_pipeline || {};
  const pipelineMax = Math.max(...Object.values(pipeline).filter((_, i) => i < 4), 1);
  const agents = stats?.agents || [];
  const msgsUsed = stats?.messages_used || 0;
  const msgsLimit = stats?.messages_limit || 50;
  const usagePercent = msgsLimit > 0 ? Math.min(100, Math.round((msgsUsed / msgsLimit) * 100)) : 0;

  return (
    <div className="min-h-screen px-3 pt-2 pb-4">
        {/* ── Premium Quick Actions (replaces carousel) ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={1}
          className="mb-3 grid grid-cols-2 gap-2" data-testid="quick-actions-grid">
          {[
            { icon: Bot, label: t('dashboard.create_agent'), sub: `${agents.length} ${agents.length === 1 ? 'agent' : 'agents'}`, path: '/agents', accent: true },
            { icon: MessageSquare, label: t('dashboard.view_inbox'), sub: `${stats?.messages_today || 0} today`, path: '/chat' },
            { icon: Target, label: t('dashboard.view_crm'), sub: `${stats?.active_leads || 0} leads`, path: '/crm' },
            { icon: Megaphone, label: 'Marketing', sub: 'Campaigns', path: '/marketing' },
          ].map((a, i) => (
            <button key={i} data-testid={`quick-action-${i}`} onClick={() => navigate(a.path)}
              className={`group glass-card flex items-center gap-3 p-3.5 text-left transition-all hover:border-orange-500/30 hover:shadow-[0_0_20px_rgba(201,168,76,0.04)] ${a.accent ? 'border-orange-500/15' : ''}`}>
              <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl transition-all ${
                a.accent
                  ? 'bg-gradient-to-br from-[#F97316]/20 to-[#F97316]/5 shadow-[0_0_20px_rgba(201,168,76,0.08)] group-hover:shadow-[0_0_25px_rgba(201,168,76,0.15)]'
                  : 'bg-white/[0.03] group-hover:bg-orange-500/[0.08]'
              }`}>
                <a.icon size={18} className="text-orange-600" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-semibold text-gray-900 truncate">{a.label}</p>
                <p className="text-[9px] text-[#888] font-mono">{a.sub}</p>
              </div>
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
            <div key={i} data-testid={`stat-${i}`} className="glass-card p-2.5 transition hover:border-orange-500/20">
              <div className="mb-1.5 flex items-center justify-between">
                <s.icon size={13} className="text-orange-600/70" />
                {s.trend && <ArrowUpRight size={10} className="text-orange-600" />}
              </div>
              <p className="text-base font-bold text-gray-900 leading-tight font-mono">{s.value}</p>
              <p className="text-[9px] text-gray-500 leading-tight mt-0.5">{s.label}</p>
            </div>
          ))}
        </motion.div>

        {/* ── Messages Chart + CRM Pipeline ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={4}
          className="mb-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-gray-900">{t('dashboard.messages_week')}</h2>
              <span className="text-[9px] text-gray-500">{t('dashboard.last_7_days')}</span>
            </div>
            <div className="h-[100px]" style={{ minWidth: 0 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats?.messages_by_day || []} margin={{ top: 2, right: 2, left: -25, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gld" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#F97316" stopOpacity={0.25} />
                      <stop offset="100%" stopColor="#F97316" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="label" tick={{ fontSize: 9, fill: '#888' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 9, fill: '#777' }} axisLine={false} tickLine={false} allowDecimals={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Area type="monotone" dataKey="count" stroke="#F97316" strokeWidth={1.5} fill="url(#gld)" dot={{ r: 2, fill: '#F97316', strokeWidth: 0 }} activeDot={{ r: 4, fill: '#F97316' }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-gray-900">{t('dashboard.crm_pipeline')}</h2>
              <button onClick={() => navigate('/crm')} className="text-[9px] text-orange-600 hover:underline">{t('dashboard.view_all')}</button>
            </div>
            <div className="flex items-end gap-2 h-[100px]">
              {['new', 'qualified', 'proposal', 'won'].map((stage, i) => {
                const count = pipeline[stage] || 0;
                const h = Math.max(15, (count / pipelineMax) * 70);
                const opacity = 1 - i * 0.15;
                return (
                  <div key={stage} className="flex flex-1 flex-col items-center justify-end h-full">
                    <div className="w-full rounded-md transition-all hover:opacity-80" style={{ height: `${h}%`, backgroundColor: `rgba(201,168,76,${opacity})` }} />
                    <p className="mt-1 text-sm font-bold text-gray-900">{count}</p>
                    <p className="text-[8px] text-gray-500 capitalize">{PIPELINE_LABELS[stage]}</p>
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
              <h2 className="text-xs font-semibold text-gray-900">{t('dashboard.recent_chats')}</h2>
              <button onClick={() => navigate('/chat')} className="text-[9px] text-orange-600 hover:underline">{t('dashboard.view_all')}</button>
            </div>
            {(stats?.recent_conversations || []).length > 0 ? (
              <div className="space-y-1">
                {stats.recent_conversations.map(c => (
                  <div key={c.id} className="flex items-center gap-2.5 rounded-xl bg-white/[0.015] border border-white/[0.04] p-2 transition hover:bg-white/[0.03] hover:border-white/[0.08] cursor-pointer" onClick={() => navigate('/chat')}>
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-white/[0.03]">
                      <ChannelIcon type={c.channel_type} size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="truncate text-xs font-medium text-gray-900">{c.contact_name}</p>
                      <p className="text-[9px] capitalize text-gray-500">{c.channel_type}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={`inline-block rounded-full px-1.5 py-px text-[8px] font-medium ${c.status === 'active' ? 'bg-orange-500/15 text-orange-600' : 'bg-[#333]/30 text-gray-500'}`}>
                        {c.status}
                      </span>
                      <p className="mt-0.5 text-[9px] text-gray-500">{timeAgo(c.last_message_at)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-4 text-center">
                <MessageSquare size={20} className="mx-auto mb-1.5 text-[#444]" />
                <p className="text-[10px] text-gray-500">{t('dashboard.no_conversations')}</p>
              </div>
            )}
          </div>

          {/* Agent Team */}
          <div className="glass-card p-3">
            <div className="mb-2 flex items-center justify-between">
              <h2 className="text-xs font-semibold text-gray-900">{t('dashboard.agent_performance')}</h2>
              <button onClick={() => navigate('/agents')} className="text-[9px] text-orange-600 hover:underline">{t('dashboard.view_all')}</button>
            </div>
            {agents.length > 0 ? (
              <div className="space-y-1">
                {agents.map((a) => (
                  <div key={a.id} className="flex items-center gap-2.5 rounded-xl bg-white/[0.015] border border-white/[0.04] p-2 transition hover:bg-white/[0.03] hover:border-white/[0.08]">
                    <div className="relative">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-orange-500/10 ring-1 ring-[#F97316]/15">
                        <Bot size={14} className="text-orange-600" />
                      </div>
                      <div className={`absolute -bottom-px -right-px h-2 w-2 rounded-full border border-[#0A0A0A] ${a.status === 'active' ? 'bg-emerald-400' : 'bg-[#666]'}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-0.5">
                        <p className="truncate text-xs font-medium text-gray-900">{a.name}</p>
                        <span className="text-[9px] font-mono text-orange-600 ml-2">{a.resolved > 0 ? Math.round((a.resolved / Math.max(a.conversations, 1)) * 100) : 0}%</span>
                      </div>
                      <div className="h-1 overflow-hidden rounded-full bg-[#1A1A1A]">
                        <div className="h-full rounded-full bg-gradient-to-r from-[#F97316] to-[#D4B85A] transition-all duration-700" style={{ width: `${a.conversations > 0 ? Math.round((a.resolved / a.conversations) * 100) : 0}%` }} />
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
                <Bot size={20} className="mx-auto mb-1.5 text-[#444]" />
                <p className="mb-1.5 text-[10px] text-gray-500">{t('dashboard.no_agents')}</p>
                <button onClick={() => navigate('/agents')} className="btn-gold rounded-lg px-3 py-1 text-[10px]">{t('dashboard.create_first')}</button>
              </div>
            )}
          </div>
        </motion.div>

        {/* ── AI Insights Widget ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={6}
          data-testid="ai-insights-widget" className="mb-3 glass-card p-3 border-orange-500/15">
          <div className="mb-2 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-orange-500/10">
              <Lightbulb size={12} className="text-orange-600" />
            </div>
            <h2 className="text-xs font-semibold text-gray-900">{t('dashboard.ai_insights')}</h2>
            <span className="ml-auto rounded-full bg-orange-500/10 px-2 py-0.5 text-[8px] font-semibold text-orange-600 uppercase tracking-wide">AI</span>
          </div>
          <div className="space-y-1.5">
            {[
              { text: t('dashboard.insight_1', { count: pipeline.qualified || 0 }), type: 'alert' },
              { text: t('dashboard.insight_2', { count: stats?.agents_count || 0 }), type: 'tip' },
              { text: t('dashboard.insight_3'), type: 'opportunity' },
            ].map((insight, i) => (
              <div key={i} className="flex items-start gap-2 rounded-xl bg-white/[0.015] border border-white/[0.04] p-2">
                <div className="mt-0.5 h-1 w-1 shrink-0 rounded-full bg-orange-500" />
                <p className="text-[10px] leading-relaxed text-gray-500">{insight.text}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* ── Plan & Usage ── */}
        <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={7}
          className="glass-card p-3">
          <div className="flex items-center justify-between mb-2">
            <div>
              <p className="text-[9px] text-gray-500">{t('dashboard.current_plan')}</p>
              <p className="text-xs font-bold text-gray-900 capitalize">{stats?.plan || 'free'}</p>
            </div>
            <button onClick={() => navigate('/pricing')} className="rounded-full border border-orange-500/25 px-2.5 py-0.5 text-[9px] font-medium text-orange-600 transition hover:bg-orange-500/10">
              {t('dashboard.upgrade')}
            </button>
          </div>
          <div className="space-y-1.5">
            <div>
              <div className="flex justify-between text-[9px] mb-0.5">
                <span className="text-gray-500">{t('dashboard.messages_usage')}</span>
                <span className={usagePercent > 80 ? 'text-[#FF6B6B] font-semibold' : 'text-[#888]'}>{msgsUsed}/{msgsLimit}</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-[#1A1A1A]">
                <div className={`h-full rounded-full transition-all duration-500 ${usagePercent > 80 ? 'bg-[#FF6B6B]' : 'bg-gradient-to-r from-[#F97316] to-[#D4B85A]'}`} style={{ width: `${usagePercent}%` }} />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[9px] mb-0.5">
                <span className="text-gray-500">{t('dashboard.agents_usage')}</span>
                <span className="text-[#888]">{stats?.agents_count || 0}/{stats?.agents_limit || 1}</span>
              </div>
              <div className="h-1 overflow-hidden rounded-full bg-[#1A1A1A]">
                <div className="h-full rounded-full bg-gradient-to-r from-[#F97316] to-[#D4B85A] transition-all duration-500" style={{ width: `${Math.min(100, ((stats?.agents_count || 0) / (stats?.agents_limit || 1)) * 100)}%` }} />
              </div>
            </div>
          </div>
        </motion.div>
    </div>
  );
}
