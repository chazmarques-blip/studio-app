import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Users, Target, TrendingUp, BarChart3, Play, Pause, Settings2, Eye, Zap,
  MessageSquare, Instagram, Facebook, Send, Mail, Globe, ChevronRight, Shield } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// Traffic Manager agents with their specialties
const TRAFFIC_AGENTS = [
  {
    id: 'james',
    name: 'James',
    role: 'Chief Traffic Manager',
    specialty: 'Orquestra todos os canais com a mentalidade de Russell Brunson + Neil Patel + Dan Kennedy',
    icon: Shield,
    color: '#C9A84C',
    channels: ['all'],
    skills: ['Estratégia Omnichannel', 'Budget Allocation', 'ROI Optimization', 'Growth Hacking'],
  },
  {
    id: 'emily',
    name: 'Emily',
    role: 'Meta Ads Manager',
    specialty: 'Especialista em Facebook + Instagram Ads com domínio de Pixel, Lookalike Audiences e Creative Testing',
    icon: Instagram,
    color: '#E1306C',
    channels: ['instagram', 'facebook'],
    skills: ['Custom Audiences', 'A/B Testing', 'Retargeting', 'ROAS Optimization'],
  },
  {
    id: 'ryan',
    name: 'Ryan',
    role: 'TikTok Ads Manager',
    specialty: 'Expert em TikTok Ads, Spark Ads, trends virais, UGC hooks e algoritmo For You',
    icon: Zap,
    color: '#00F2EA',
    channels: ['tiktok'],
    skills: ['Spark Ads', 'Viral Hooks', 'UGC Strategy', 'Trend Riding'],
  },
  {
    id: 'sarah',
    name: 'Sarah',
    role: 'Messaging Manager',
    specialty: 'Automação e sequências para WhatsApp Business, Telegram e SMS com foco em nurturing',
    icon: MessageSquare,
    color: '#25D366',
    channels: ['whatsapp', 'telegram', 'sms'],
    skills: ['Drip Campaigns', 'Automation Flows', 'Lead Nurturing', 'Conversational Sales'],
  },
  {
    id: 'mike',
    name: 'Mike',
    role: 'Google Ads Manager',
    specialty: 'Search, Display, YouTube e Performance Max com foco absoluto em ROI e keyword strategy',
    icon: Globe,
    color: '#4285F4',
    channels: ['google_ads', 'email'],
    skills: ['Keyword Strategy', 'Quality Score', 'Bid Optimization', 'Performance Max'],
  },
];

const CHANNEL_ICONS = {
  whatsapp: MessageSquare,
  instagram: Instagram,
  facebook: Facebook,
  tiktok: Zap,
  telegram: Send,
  google_ads: Globe,
  email: Mail,
  sms: MessageSquare,
};

const CHANNEL_COLORS = {
  whatsapp: '#25D366',
  instagram: '#E1306C',
  facebook: '#1877F2',
  tiktok: '#00F2EA',
  telegram: '#0088CC',
  google_ads: '#4285F4',
  email: '#EA4335',
  sms: '#FF9800',
};

// Campaign card for Traffic Hub
function CampaignCard({ campaign, onManage }) {
  const stats = campaign.stats || {};
  const platforms = campaign.target_segment?.platforms || [];
  const copyText = campaign.messages?.[0]?.content || '';
  const preview = copyText.substring(0, 100) + (copyText.length > 100 ? '...' : '');
  const isCreated = campaign.status === 'created';
  const isActive = campaign.status === 'active';
  const isDraft = campaign.status === 'draft';

  return (
    <div data-testid={`traffic-campaign-${campaign.id}`}
      className="bg-[#111] border border-[#1E1E1E] rounded-xl p-4 hover:border-[#C9A84C]/30 transition group">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white truncate">{campaign.name}</h3>
          <p className="text-[10px] text-[#666] mt-0.5">{preview}</p>
        </div>
        <span data-testid={`campaign-status-${campaign.id}`} className={`text-[8px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
          isActive ? 'bg-green-500/15 text-green-400' :
          isCreated ? 'bg-[#C9A84C]/15 text-[#C9A84C]' :
          'bg-[#333]/50 text-[#666]'
        }`}>
          {isActive ? 'Ativa' : isCreated ? 'Criada' : isDraft ? 'Rascunho' : campaign.status}
        </span>
      </div>

      {/* Platform chips */}
      <div className="flex gap-1.5 flex-wrap mb-3">
        {platforms.map(p => {
          const Icon = CHANNEL_ICONS[p] || Globe;
          const col = CHANNEL_COLORS[p] || '#888';
          return (
            <span key={p} className="flex items-center gap-1 text-[8px] px-1.5 py-0.5 rounded bg-[#1A1A1A] border border-[#222]"
              style={{ color: col, borderColor: `${col}33` }}>
              <Icon size={9} /> {p === 'google_ads' ? 'Google Ads' : p}
            </span>
          );
        })}
      </div>

      {/* Mini stats */}
      <div className="grid grid-cols-4 gap-2 mb-3">
        {[
          { label: 'Enviados', value: stats.sent || 0 },
          { label: 'Entregues', value: stats.delivered || 0 },
          { label: 'Abertos', value: stats.opened || 0 },
          { label: 'Cliques', value: stats.clicked || 0 },
        ].map(s => (
          <div key={s.label} className="text-center">
            <div className="text-xs font-bold text-white">{s.value}</div>
            <div className="text-[7px] text-[#555]">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        {isCreated && (
          <button data-testid={`activate-campaign-${campaign.id}`}
            onClick={() => onManage(campaign, 'activate')}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg bg-[#C9A84C] text-[#0A0A0A] text-[10px] font-semibold hover:bg-[#D4B85C] transition">
            <Play size={10} /> Ativar Campanha
          </button>
        )}
        {isActive && (
          <button data-testid={`pause-campaign-${campaign.id}`}
            onClick={() => onManage(campaign, 'pause')}
            className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg border border-yellow-500/30 text-yellow-400 text-[10px] font-semibold hover:bg-yellow-500/10 transition">
            <Pause size={10} /> Pausar
          </button>
        )}
        <button data-testid={`view-campaign-${campaign.id}`}
          onClick={() => onManage(campaign, 'view')}
          className="flex items-center justify-center gap-1 px-3 py-1.5 rounded-lg border border-[#333] text-[#888] text-[10px] hover:text-white hover:border-[#555] transition">
          <Eye size={10} /> Ver
        </button>
      </div>
    </div>
  );
}

// Agent card for the Traffic Hub sidebar
function AgentCard({ agent, isSelected, onClick, assignedCount }) {
  const Icon = agent.icon;
  return (
    <button data-testid={`traffic-agent-${agent.id}`}
      onClick={onClick}
      className={`w-full text-left p-3 rounded-xl border transition ${
        isSelected
          ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5'
          : 'border-[#1E1E1E] bg-[#111] hover:border-[#333]'
      }`}>
      <div className="flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${agent.color}15` }}>
          <Icon size={15} style={{ color: agent.color }} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-white">{agent.name}</span>
            {assignedCount > 0 && (
              <span className="text-[7px] px-1 py-0.5 rounded bg-[#C9A84C]/15 text-[#C9A84C] font-bold">{assignedCount}</span>
            )}
          </div>
          <p className="text-[9px] text-[#666] truncate">{agent.role}</p>
        </div>
        <ChevronRight size={12} className="text-[#444]" />
      </div>
    </button>
  );
}

export default function TrafficHub() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [campaigns, setCampaigns] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(TRAFFIC_AGENTS[0]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, created, active, draft

  const fetchCampaigns = useCallback(async () => {
    try {
      const token = localStorage.getItem('agentzz_token');
      const res = await fetch(`${API}/api/campaigns`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data.campaigns || data || []);
      }
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCampaigns(); }, [fetchCampaigns]);

  const handleManage = async (campaign, action) => {
    if (action === 'view') {
      navigate(`/marketing`);
      return;
    }
    if (action === 'activate' || action === 'pause') {
      try {
        const token = localStorage.getItem('agentzz_token');
        const newStatus = action === 'activate' ? 'active' : 'paused';
        await fetch(`${API}/api/campaigns/${campaign.id}`, {
          method: 'PUT',
          headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ status: newStatus }),
        });
        fetchCampaigns();
      } catch (err) {
        console.error('Action failed:', err);
      }
    }
  };

  // Filter campaigns based on selected agent's channels
  const agentCampaigns = campaigns.filter(c => {
    const platforms = c.target_segment?.platforms || [];
    if (selectedAgent.channels.includes('all')) return true;
    return platforms.some(p => selectedAgent.channels.includes(p));
  });

  const filteredCampaigns = agentCampaigns.filter(c => {
    if (filter === 'all') return true;
    return c.status === filter;
  });

  const stats = {
    total: campaigns.length,
    created: campaigns.filter(c => c.status === 'created').length,
    active: campaigns.filter(c => c.status === 'active').length,
    draft: campaigns.filter(c => c.status === 'draft').length,
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white" data-testid="traffic-hub-page">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] bg-[#0A0A0A]/95 backdrop-blur sticky top-0 z-30">
        <div className="max-w-[1400px] mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button data-testid="traffic-back" onClick={() => navigate('/marketing')} className="text-[#666] hover:text-white transition">
              <ArrowLeft size={18} />
            </button>
            <div>
              <h1 className="text-base font-bold text-white flex items-center gap-2">
                <Target size={18} className="text-[#C9A84C]" />
                Traffic Hub
              </h1>
              <p className="text-[10px] text-[#555]">Gestão de tráfego inteligente com agentes especializados</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {/* Quick stats */}
            <div className="flex items-center gap-3">
              {[
                { label: 'Criadas', value: stats.created, color: '#C9A84C' },
                { label: 'Ativas', value: stats.active, color: '#4CAF50' },
                { label: 'Total', value: stats.total, color: '#888' },
              ].map(s => (
                <div key={s.label} className="text-center">
                  <div className="text-sm font-bold" style={{ color: s.color }}>{s.value}</div>
                  <div className="text-[7px] text-[#555] uppercase">{s.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-4 py-4">
        <div className="flex gap-4">
          {/* Left: Agent Panel */}
          <div className="w-[260px] flex-shrink-0 space-y-2">
            <p className="text-[9px] text-[#555] uppercase tracking-wider px-1 mb-2">Especialistas de Tráfego</p>
            {TRAFFIC_AGENTS.map(agent => {
              const count = campaigns.filter(c => {
                const platforms = c.target_segment?.platforms || [];
                if (agent.channels.includes('all')) return true;
                return platforms.some(p => agent.channels.includes(p));
              }).length;
              return (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  isSelected={selectedAgent.id === agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  assignedCount={count}
                />
              );
            })}
          </div>

          {/* Right: Agent Detail + Campaigns */}
          <div className="flex-1 space-y-4">
            {/* Agent Profile */}
            <div className="bg-[#111] border border-[#1E1E1E] rounded-xl p-4" data-testid={`agent-profile-${selectedAgent.id}`}>
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ backgroundColor: `${selectedAgent.color}15` }}>
                  <selectedAgent.icon size={22} style={{ color: selectedAgent.color }} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-white">{selectedAgent.name}</h2>
                    <span className="text-[9px] px-2 py-0.5 rounded-full bg-[#C9A84C]/10 text-[#C9A84C] font-semibold">{selectedAgent.role}</span>
                  </div>
                  <p className="text-[11px] text-[#888] mt-1">{selectedAgent.specialty}</p>
                  <div className="flex gap-2 mt-2">
                    {selectedAgent.skills.map(skill => (
                      <span key={skill} className="text-[8px] px-2 py-0.5 rounded-full bg-[#1A1A1A] border border-[#222] text-[#777]">{skill}</span>
                    ))}
                  </div>
                </div>
                <div className="flex items-center gap-1 text-[9px] px-2 py-1 rounded-lg bg-green-500/10 text-green-400 border border-green-500/20">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
                  Online
                </div>
              </div>
            </div>

            {/* Filter tabs */}
            <div className="flex items-center gap-2">
              {[
                { id: 'all', label: 'Todas', count: agentCampaigns.length },
                { id: 'created', label: 'Criadas', count: agentCampaigns.filter(c => c.status === 'created').length },
                { id: 'active', label: 'Ativas', count: agentCampaigns.filter(c => c.status === 'active').length },
                { id: 'draft', label: 'Rascunho', count: agentCampaigns.filter(c => c.status === 'draft').length },
              ].map(tab => (
                <button key={tab.id} data-testid={`filter-${tab.id}`}
                  onClick={() => setFilter(tab.id)}
                  className={`text-[10px] px-3 py-1 rounded-full border transition font-medium ${
                    filter === tab.id
                      ? 'bg-[#C9A84C]/10 border-[#C9A84C]/30 text-[#C9A84C]'
                      : 'border-[#222] text-[#666] hover:text-white hover:border-[#444]'
                  }`}>
                  {tab.label} ({tab.count})
                </button>
              ))}
            </div>

            {/* Campaign grid */}
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-6 h-6 border-2 border-[#C9A84C]/30 border-t-[#C9A84C] rounded-full animate-spin" />
              </div>
            ) : filteredCampaigns.length === 0 ? (
              <div className="text-center py-12 bg-[#111] border border-[#1E1E1E] rounded-xl">
                <Target size={32} className="mx-auto text-[#333] mb-3" />
                <p className="text-sm text-[#555]">Nenhuma campanha para {selectedAgent.name}</p>
                <p className="text-[10px] text-[#444] mt-1">Crie campanhas no AI Studio para começar</p>
                <button data-testid="go-to-studio"
                  onClick={() => navigate('/marketing/studio')}
                  className="mt-3 text-[10px] px-4 py-1.5 rounded-lg bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20 hover:bg-[#C9A84C]/20 transition">
                  Ir para AI Studio
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {filteredCampaigns.map(c => (
                  <CampaignCard key={c.id} campaign={c} onManage={handleManage} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
