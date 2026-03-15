import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Target, TrendingUp, Play, Pause, Eye, Zap, BarChart3,
  MessageSquare, Instagram, Facebook, Send, Mail, Globe, ChevronRight, Shield,
  ArrowUpRight, ArrowDownRight, DollarSign, Users, MousePointerClick, Sparkles,
  AlertTriangle, CheckCircle2, Clock, RefreshCw, X, ChevronDown } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const TRAFFIC_AGENTS = [
  { id: 'james', name: 'James', role: 'Chief Traffic Manager', icon: Shield, color: '#C9A84C',
    channels: ['all'], skills: ['Omnichannel Strategy', 'Budget Allocation', 'ROI Optimization'] },
  { id: 'emily', name: 'Emily', role: 'Meta Ads Specialist', icon: Instagram, color: '#E1306C',
    channels: ['instagram', 'facebook'], skills: ['Custom Audiences', 'A/B Testing', 'Retargeting'] },
  { id: 'ryan', name: 'Ryan', role: 'TikTok Ads Specialist', icon: Zap, color: '#00F2EA',
    channels: ['tiktok'], skills: ['Spark Ads', 'Viral Hooks', 'UGC Strategy'] },
  { id: 'sarah', name: 'Sarah', role: 'Messaging Specialist', icon: MessageSquare, color: '#25D366',
    channels: ['whatsapp', 'telegram', 'sms'], skills: ['Drip Campaigns', 'Lead Nurturing', 'Conversational Sales'] },
  { id: 'mike', name: 'Mike', role: 'Google & Email Specialist', icon: Globe, color: '#4285F4',
    channels: ['google_ads', 'email'], skills: ['Keyword Strategy', 'Quality Score', 'Performance Max'] },
];

const CHANNEL_META = {
  whatsapp: { icon: MessageSquare, color: '#25D366', label: 'WhatsApp' },
  instagram: { icon: Instagram, color: '#E1306C', label: 'Instagram' },
  facebook: { icon: Facebook, color: '#1877F2', label: 'Facebook' },
  tiktok: { icon: Zap, color: '#00F2EA', label: 'TikTok' },
  telegram: { icon: Send, color: '#0088CC', label: 'Telegram' },
  google_ads: { icon: Globe, color: '#4285F4', label: 'Google Ads' },
  email: { icon: Mail, color: '#EA4335', label: 'Email' },
  sms: { icon: MessageSquare, color: '#FF9800', label: 'SMS' },
};

// Simulated performance data per campaign (will be real when APIs are connected)
function generateSimulatedMetrics(campaign) {
  const seed = campaign.id.charCodeAt(0) + campaign.id.charCodeAt(5);
  const r = (min, max) => Math.floor(min + ((seed * 7 + min) % (max - min)));
  const platforms = campaign.target_segment?.platforms || [];
  const isActive = campaign.status === 'active';
  const isCreated = campaign.status === 'created';

  const channelData = {};
  platforms.forEach(p => {
    const base = r(100, 900);
    channelData[p] = {
      impressions: isActive ? r(2000, 15000) : isCreated ? 0 : r(50, 500),
      clicks: isActive ? r(80, 600) : 0,
      ctr: isActive ? (r(15, 55) / 10).toFixed(1) : '0.0',
      cpc: isActive ? (r(3, 25) / 10).toFixed(2) : '0.00',
      spend: isActive ? r(15, 200) : 0,
      conversions: isActive ? r(2, 30) : 0,
      roas: isActive ? (r(15, 60) / 10).toFixed(1) : '0.0',
    };
  });

  const totalImpressions = Object.values(channelData).reduce((s, c) => s + c.impressions, 0);
  const totalClicks = Object.values(channelData).reduce((s, c) => s + c.clicks, 0);
  const totalSpend = Object.values(channelData).reduce((s, c) => s + c.spend, 0);
  const totalConversions = Object.values(channelData).reduce((s, c) => s + c.conversions, 0);
  const avgCtr = totalImpressions > 0 ? ((totalClicks / totalImpressions) * 100).toFixed(1) : '0.0';
  const avgRoas = totalSpend > 0 ? ((totalConversions * r(30, 80)) / totalSpend).toFixed(1) : '0.0';

  return {
    channels: channelData,
    totals: { impressions: totalImpressions, clicks: totalClicks, spend: totalSpend, conversions: totalConversions, ctr: avgCtr, roas: avgRoas },
    trend: isActive ? (r(0, 10) > 3 ? 'up' : 'down') : 'neutral',
    trendPct: isActive ? r(3, 22) : 0,
  };
}

// AI recommendations per agent per campaign
function generateAgentRecommendations(agent, campaign, metrics) {
  const isActive = campaign.status === 'active';
  const isCreated = campaign.status === 'created';
  const name = campaign.name;

  const recommendations = {
    james: isActive ? [
      { type: 'optimization', text: `Redistribuir 30% do budget de canais com CPC alto para os com melhor ROAS`, priority: 'high' },
      { type: 'insight', text: `"${name}" tem melhor performance em horario noturno (20h-23h). Concentrar veiculacao nesse periodo`, priority: 'medium' },
      { type: 'action', text: `Criar variacao A/B do headline principal — o CTR pode subir 15-20%`, priority: 'medium' },
    ] : isCreated ? [
      { type: 'action', text: `Campanha pronta para ativar. Recomendo comecar com budget de R$50/dia nos 3 canais principais`, priority: 'high' },
      { type: 'insight', text: `Melhor dia para lancar: Segunda ou Terca (menor concorrencia no nicho)`, priority: 'medium' },
    ] : [
      { type: 'warning', text: `Campanha em rascunho. Finalize o conteudo no AI Studio antes de ativar`, priority: 'low' },
    ],
    emily: isActive ? [
      { type: 'optimization', text: `Instagram Stories tem 2.3x mais engajamento que Feed. Priorizar formato vertical`, priority: 'high' },
      { type: 'action', text: `Criar Lookalike Audience baseada nos ${metrics.totals.conversions} leads convertidos`, priority: 'high' },
      { type: 'insight', text: `Custo por lead no Facebook esta 40% menor que Instagram. Considerar aumentar budget FB`, priority: 'medium' },
    ] : [
      { type: 'action', text: `Configurar Pixel do Meta e Custom Audiences antes de ativar`, priority: 'high' },
      { type: 'insight', text: `O publico-alvo tem alta presenca no Instagram entre 18h-22h`, priority: 'medium' },
    ],
    ryan: isActive ? [
      { type: 'optimization', text: `O hook dos primeiros 3 segundos do video precisa ser mais agressivo — 60% dos viewers saem antes`, priority: 'high' },
      { type: 'action', text: `Transformar o video em Spark Ad usando conta de criador parceiro para maior autenticidade`, priority: 'medium' },
      { type: 'insight', text: `Hashtag trending "#selfcare" pode amplificar alcance em 3x se usada nos proximos 2 dias`, priority: 'medium' },
    ] : [
      { type: 'action', text: `O formato vertical 9:16 ja esta pronto. Ideal para TikTok In-Feed Ads`, priority: 'medium' },
    ],
    sarah: isActive ? [
      { type: 'optimization', text: `Taxa de abertura no WhatsApp: 94%. Enviar follow-up para os ${metrics.totals.clicks} que clicaram mas nao converteram`, priority: 'high' },
      { type: 'action', text: `Criar sequencia de nurturing: Dia 1 (oferta), Dia 3 (depoimento), Dia 7 (urgencia)`, priority: 'high' },
      { type: 'insight', text: `Mensagens enviadas entre 10h-11h tem 28% mais resposta que tarde/noite`, priority: 'medium' },
    ] : [
      { type: 'action', text: `Preparar template de mensagem aprovado pelo WhatsApp Business API`, priority: 'high' },
      { type: 'insight', text: `Iniciar com mensagem de valor (conteudo) antes de oferta direta`, priority: 'medium' },
    ],
    mike: isActive ? [
      { type: 'optimization', text: `Quality Score das keywords principais esta em 7/10. Otimizar landing page para subir para 9+`, priority: 'high' },
      { type: 'action', text: `Adicionar negative keywords: "${campaign.name?.split(' ')[0]} gratis", "${campaign.name?.split(' ')[0]} reclamacao"`, priority: 'medium' },
      { type: 'insight', text: `Email tem a melhor taxa de conversao (${(metrics.channels?.email?.conversions || 0)} conv). Aumentar frequencia de envio`, priority: 'medium' },
    ] : [
      { type: 'action', text: `Pesquisar keywords de cauda longa para reduzir CPC em 30-40%`, priority: 'high' },
    ],
  };

  return recommendations[agent.id] || [];
}

// Metric card component
function MetricCard({ label, value, prefix, suffix, trend, trendPct, small }) {
  return (
    <div className={`bg-[#111] border border-[#1E1E1E] rounded-xl ${small ? 'p-2.5' : 'p-3'}`}>
      <p className="text-[8px] text-[#555] uppercase tracking-wider">{label}</p>
      <div className="flex items-end gap-1.5 mt-1">
        <span className={`${small ? 'text-lg' : 'text-xl'} font-bold text-white`}>
          {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
        </span>
        {trend && trend !== 'neutral' && (
          <span className={`flex items-center text-[9px] font-semibold mb-0.5 ${trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
            {trend === 'up' ? <ArrowUpRight size={10} /> : <ArrowDownRight size={10} />}
            {trendPct}%
          </span>
        )}
      </div>
    </div>
  );
}

// Channel performance row
function ChannelRow({ channel, data }) {
  const meta = CHANNEL_META[channel];
  if (!meta) return null;
  const Icon = meta.icon;
  const maxSpend = 200;
  const barWidth = Math.min((data.spend / maxSpend) * 100, 100);

  return (
    <div className="flex items-center gap-3 py-2 border-b border-[#151515] last:border-0">
      <div className="w-6 h-6 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${meta.color}15` }}>
        <Icon size={12} style={{ color: meta.color }} />
      </div>
      <div className="w-20">
        <span className="text-[10px] text-white font-medium">{meta.label}</span>
      </div>
      <div className="flex-1 grid grid-cols-5 gap-2 text-center">
        <div>
          <span className="text-[10px] text-white font-semibold">{data.impressions.toLocaleString()}</span>
          <p className="text-[7px] text-[#555]">Impres.</p>
        </div>
        <div>
          <span className="text-[10px] text-white font-semibold">{data.clicks}</span>
          <p className="text-[7px] text-[#555]">Cliques</p>
        </div>
        <div>
          <span className="text-[10px] font-semibold" style={{ color: parseFloat(data.ctr) > 3 ? '#4CAF50' : '#FF9800' }}>{data.ctr}%</span>
          <p className="text-[7px] text-[#555]">CTR</p>
        </div>
        <div>
          <span className="text-[10px] text-white font-semibold">${data.spend}</span>
          <p className="text-[7px] text-[#555]">Gasto</p>
        </div>
        <div>
          <span className="text-[10px] font-semibold" style={{ color: parseFloat(data.roas) > 3 ? '#4CAF50' : '#FF9800' }}>{data.roas}x</span>
          <p className="text-[7px] text-[#555]">ROAS</p>
        </div>
      </div>
    </div>
  );
}

// Campaign detail panel
function CampaignPanel({ campaign, metrics, agent, onClose, onAction }) {
  const recs = generateAgentRecommendations(agent, campaign, metrics);
  const platforms = campaign.target_segment?.platforms || [];
  const isActive = campaign.status === 'active';
  const isCreated = campaign.status === 'created';

  return (
    <div data-testid="campaign-panel" className="bg-[#0D0D0D] border border-[#1E1E1E] rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[#1A1A1A] flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-bold text-white truncate">{campaign.name}</h3>
            <span className={`text-[7px] font-bold px-2 py-0.5 rounded-full uppercase ${
              isActive ? 'bg-green-500/15 text-green-400' :
              isCreated ? 'bg-[#C9A84C]/15 text-[#C9A84C]' :
              'bg-[#333]/50 text-[#666]'
            }`}>
              {isActive ? 'Ativa' : isCreated ? 'Pronta' : 'Rascunho'}
            </span>
          </div>
          <div className="flex gap-1.5 flex-wrap mt-2">
            {platforms.map(p => {
              const m = CHANNEL_META[p];
              if (!m) return null;
              const I = m.icon;
              return <span key={p} className="flex items-center gap-1 text-[7px] px-1.5 py-0.5 rounded-full border" style={{ color: m.color, borderColor: `${m.color}33`, backgroundColor: `${m.color}08` }}><I size={8} />{m.label}</span>;
            })}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isCreated && (
            <button data-testid="panel-activate" onClick={() => onAction(campaign, 'activate')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#C9A84C] text-[#0A0A0A] text-[10px] font-bold hover:bg-[#D4B85C] transition">
              <Play size={10} /> Ativar
            </button>
          )}
          {isActive && (
            <button data-testid="panel-pause" onClick={() => onAction(campaign, 'pause')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-yellow-500/30 text-yellow-400 text-[10px] font-bold hover:bg-yellow-500/10 transition">
              <Pause size={10} /> Pausar
            </button>
          )}
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[#1A1A1A] text-[#666] hover:text-white transition">
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Metrics overview */}
      <div className="p-4 border-b border-[#1A1A1A]">
        <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
          <MetricCard label="Impressoes" value={metrics.totals.impressions} trend={metrics.trend} trendPct={metrics.trendPct} small />
          <MetricCard label="Cliques" value={metrics.totals.clicks} trend={metrics.trend} trendPct={metrics.trendPct} small />
          <MetricCard label="CTR" value={metrics.totals.ctr} suffix="%" small />
          <MetricCard label="Gasto" value={metrics.totals.spend} prefix="$" small />
          <MetricCard label="Conversoes" value={metrics.totals.conversions} trend={metrics.trend} trendPct={metrics.trendPct} small />
          <MetricCard label="ROAS" value={metrics.totals.roas} suffix="x" small />
        </div>
      </div>

      {/* Channel breakdown */}
      {isActive && (
        <div className="p-4 border-b border-[#1A1A1A]">
          <p className="text-[9px] text-[#555] uppercase tracking-wider mb-2">Performance por Canal</p>
          <div className="bg-[#0A0A0A] rounded-xl border border-[#151515] px-3">
            {platforms.map(p => metrics.channels[p] && (
              <ChannelRow key={p} channel={p} data={metrics.channels[p]} />
            ))}
          </div>
        </div>
      )}

      {/* Agent Recommendations */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${agent.color}15` }}>
            <agent.icon size={12} style={{ color: agent.color }} />
          </div>
          <div>
            <p className="text-[10px] text-white font-semibold">{agent.name}</p>
            <p className="text-[8px] text-[#555]">{agent.role}</p>
          </div>
          <Sparkles size={12} className="text-[#C9A84C] ml-auto" />
          <span className="text-[8px] text-[#C9A84C] font-semibold">Analise IA</span>
        </div>
        <div className="space-y-2">
          {recs.map((rec, i) => (
            <div key={i} className={`flex items-start gap-2.5 p-2.5 rounded-lg border ${
              rec.priority === 'high' ? 'border-[#C9A84C]/20 bg-[#C9A84C]/5' :
              rec.priority === 'medium' ? 'border-[#333] bg-[#111]' :
              'border-[#1A1A1A] bg-[#0D0D0D]'
            }`}>
              <div className="mt-0.5">
                {rec.type === 'optimization' && <TrendingUp size={11} className="text-[#C9A84C]" />}
                {rec.type === 'action' && <CheckCircle2 size={11} className="text-green-400" />}
                {rec.type === 'insight' && <BarChart3 size={11} className="text-blue-400" />}
                {rec.type === 'warning' && <AlertTriangle size={11} className="text-orange-400" />}
              </div>
              <div className="flex-1">
                <span className={`text-[8px] font-bold uppercase tracking-wider ${
                  rec.type === 'optimization' ? 'text-[#C9A84C]' :
                  rec.type === 'action' ? 'text-green-400' :
                  rec.type === 'insight' ? 'text-blue-400' : 'text-orange-400'
                }`}>
                  {rec.type === 'optimization' ? 'Otimizacao' : rec.type === 'action' ? 'Acao' : rec.type === 'insight' ? 'Insight' : 'Atencao'}
                </span>
                <p className="text-[10px] text-[#ccc] mt-0.5 leading-relaxed">{rec.text}</p>
              </div>
              {rec.priority === 'high' && (
                <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-red-500/15 text-red-400 font-bold whitespace-nowrap">PRIORIDADE</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Compact campaign row for the list
function CampaignRow({ campaign, metrics, isSelected, onClick }) {
  const isActive = campaign.status === 'active';
  const isCreated = campaign.status === 'created';
  const platforms = campaign.target_segment?.platforms || [];

  return (
    <button data-testid={`traffic-row-${campaign.id}`} onClick={onClick}
      className={`w-full text-left p-3 rounded-xl border transition ${
        isSelected ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] bg-[#111] hover:border-[#333]'
      }`}>
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="text-[11px] font-semibold text-white truncate">{campaign.name}</h4>
            <span className={`text-[7px] font-bold px-1.5 py-0.5 rounded-full uppercase ${
              isActive ? 'bg-green-500/15 text-green-400' :
              isCreated ? 'bg-[#C9A84C]/15 text-[#C9A84C]' :
              'bg-[#333]/50 text-[#555]'
            }`}>
              {isActive ? 'Ativa' : isCreated ? 'Pronta' : 'Rascunho'}
            </span>
          </div>
          <div className="flex gap-1 mt-1.5">
            {platforms.slice(0, 5).map(p => {
              const m = CHANNEL_META[p];
              if (!m) return null;
              const I = m.icon;
              return <span key={p} className="w-4 h-4 rounded flex items-center justify-center" style={{ backgroundColor: `${m.color}15` }}><I size={8} style={{ color: m.color }} /></span>;
            })}
            {platforms.length > 5 && <span className="text-[8px] text-[#555] self-center">+{platforms.length - 5}</span>}
          </div>
        </div>
        <div className="text-right ml-3">
          {isActive ? (
            <>
              <div className="text-[11px] font-bold text-white">{metrics.totals.conversions} <span className="text-[8px] text-[#555] font-normal">conv</span></div>
              <div className="flex items-center gap-1 justify-end">
                <span className={`text-[9px] font-semibold flex items-center ${metrics.trend === 'up' ? 'text-green-400' : 'text-red-400'}`}>
                  {metrics.trend === 'up' ? <ArrowUpRight size={9} /> : <ArrowDownRight size={9} />}{metrics.trendPct}%
                </span>
                <span className="text-[8px] text-[#555]">${metrics.totals.spend}</span>
              </div>
            </>
          ) : (
            <span className="text-[9px] text-[#555]">{platforms.length} canais</span>
          )}
        </div>
      </div>
    </button>
  );
}

export default function TrafficHub() {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(TRAFFIC_AGENTS[0]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [metricsMap, setMetricsMap] = useState({});

  const fetchCampaigns = useCallback(async () => {
    try {
      const token = localStorage.getItem('agentzz_token');
      const res = await fetch(`${API}/api/campaigns`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) {
        const data = await res.json();
        const list = data.campaigns || data || [];
        setCampaigns(list);
        // Generate simulated metrics for each campaign
        const mMap = {};
        list.forEach(c => { mMap[c.id] = generateSimulatedMetrics(c); });
        setMetricsMap(mMap);
        if (list.length > 0 && !selectedCampaign) setSelectedCampaign(list[0]);
      }
    } catch (err) {
      console.error('Failed to fetch campaigns:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchCampaigns(); }, [fetchCampaigns]);

  const handleAction = async (campaign, action) => {
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

  // Filter by agent channels
  const agentCampaigns = campaigns.filter(c => {
    const platforms = c.target_segment?.platforms || [];
    if (selectedAgent.channels.includes('all')) return true;
    return platforms.some(p => selectedAgent.channels.includes(p));
  });

  const filteredCampaigns = agentCampaigns.filter(c => {
    if (filter === 'all') return true;
    return c.status === filter;
  });

  // Global stats
  const totalSpend = Object.values(metricsMap).reduce((s, m) => s + m.totals.spend, 0);
  const totalConversions = Object.values(metricsMap).reduce((s, m) => s + m.totals.conversions, 0);
  const totalImpressions = Object.values(metricsMap).reduce((s, m) => s + m.totals.impressions, 0);
  const activeCampaigns = campaigns.filter(c => c.status === 'active').length;

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
              <p className="text-[10px] text-[#555]">Centro de comando — performance e otimizacao de campanhas</p>
            </div>
          </div>
          {/* Global KPIs */}
          <div className="hidden md:flex items-center gap-4">
            {[
              { icon: DollarSign, label: 'Gasto Total', value: `$${totalSpend.toLocaleString()}`, color: '#C9A84C' },
              { icon: Users, label: 'Conversoes', value: totalConversions, color: '#4CAF50' },
              { icon: MousePointerClick, label: 'Impressoes', value: totalImpressions > 1000 ? `${(totalImpressions/1000).toFixed(1)}k` : totalImpressions, color: '#4285F4' },
              { icon: Play, label: 'Ativas', value: activeCampaigns, color: '#E1306C' },
            ].map(kpi => (
              <div key={kpi.label} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#111] border border-[#1E1E1E]">
                <kpi.icon size={13} style={{ color: kpi.color }} />
                <div>
                  <div className="text-xs font-bold text-white">{kpi.value}</div>
                  <div className="text-[7px] text-[#555]">{kpi.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-4 py-4">
        <div className="flex gap-4">
          {/* Left sidebar: Agents + Campaign list */}
          <div className="w-[300px] flex-shrink-0 space-y-3">
            {/* Agent selector */}
            <div className="space-y-1.5">
              <p className="text-[8px] text-[#555] uppercase tracking-wider px-1">Especialista</p>
              {TRAFFIC_AGENTS.map(agent => {
                const count = campaigns.filter(c => {
                  const p = c.target_segment?.platforms || [];
                  if (agent.channels.includes('all')) return true;
                  return p.some(x => agent.channels.includes(x));
                }).length;
                const isSelected = selectedAgent.id === agent.id;
                const Icon = agent.icon;
                return (
                  <button key={agent.id} data-testid={`traffic-agent-${agent.id}`}
                    onClick={() => { setSelectedAgent(agent); setSelectedCampaign(null); }}
                    className={`w-full flex items-center gap-2.5 p-2.5 rounded-xl border transition ${
                      isSelected ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] bg-[#111] hover:border-[#333]'
                    }`}>
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${agent.color}15` }}>
                      <Icon size={13} style={{ color: agent.color }} />
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <span className="text-[10px] font-semibold text-white">{agent.name}</span>
                      <p className="text-[8px] text-[#555] truncate">{agent.role}</p>
                    </div>
                    <span className="text-[8px] px-1.5 py-0.5 rounded-full bg-[#1A1A1A] text-[#666] font-bold">{count}</span>
                  </button>
                );
              })}
            </div>

            {/* Filter tabs */}
            <div className="flex gap-1.5 flex-wrap">
              {[
                { id: 'all', label: 'Todas' },
                { id: 'active', label: 'Ativas' },
                { id: 'created', label: 'Prontas' },
                { id: 'draft', label: 'Rascunho' },
              ].map(tab => (
                <button key={tab.id} data-testid={`filter-${tab.id}`}
                  onClick={() => setFilter(tab.id)}
                  className={`text-[9px] px-2.5 py-1 rounded-full border transition font-medium ${
                    filter === tab.id
                      ? 'bg-[#C9A84C]/10 border-[#C9A84C]/30 text-[#C9A84C]'
                      : 'border-[#1E1E1E] text-[#555] hover:text-white hover:border-[#333]'
                  }`}>
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Campaign list */}
            <div className="space-y-1.5 max-h-[calc(100vh-340px)] overflow-y-auto pr-1">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-5 h-5 border-2 border-[#C9A84C]/30 border-t-[#C9A84C] rounded-full animate-spin" />
                </div>
              ) : filteredCampaigns.length === 0 ? (
                <div className="text-center py-8 bg-[#111] border border-[#1E1E1E] rounded-xl">
                  <Target size={24} className="mx-auto text-[#333] mb-2" />
                  <p className="text-[10px] text-[#555]">Nenhuma campanha</p>
                </div>
              ) : (
                filteredCampaigns.map(c => (
                  <CampaignRow key={c.id} campaign={c} metrics={metricsMap[c.id] || { totals: {}, channels: {}, trend: 'neutral', trendPct: 0 }}
                    isSelected={selectedCampaign?.id === c.id}
                    onClick={() => setSelectedCampaign(c)} />
                ))
              )}
            </div>
          </div>

          {/* Right: Campaign detail panel */}
          <div className="flex-1">
            {selectedCampaign && metricsMap[selectedCampaign.id] ? (
              <CampaignPanel
                campaign={selectedCampaign}
                metrics={metricsMap[selectedCampaign.id]}
                agent={selectedAgent}
                onClose={() => setSelectedCampaign(null)}
                onAction={handleAction}
              />
            ) : (
              <div className="flex flex-col items-center justify-center py-20 bg-[#111] border border-[#1E1E1E] rounded-2xl">
                <BarChart3 size={40} className="text-[#222] mb-3" />
                <p className="text-sm text-[#555]">Selecione uma campanha</p>
                <p className="text-[10px] text-[#444] mt-1">Clique em uma campanha para ver a analise do {selectedAgent.name}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Simulated data notice */}
      <div className="fixed bottom-4 right-4 z-20">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#1A1A1A] border border-[#333] text-[9px] text-[#666]">
          <Clock size={10} className="text-[#C9A84C]" />
          Dados simulados — metricas reais quando APIs de trafego forem conectadas
        </div>
      </div>
    </div>
  );
}
