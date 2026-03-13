import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Plus, Megaphone, Sparkles, Play, Pause, FileText, TrendingUp, Users, Send, BarChart3, Clock, Trash2, ChevronRight, Zap, Lock, Filter, LayoutGrid, List } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPE_META = {
  drip: { label: 'Drip', labelPt: 'Drip', color: '#C9A84C' },
  nurture: { label: 'Nurture', labelPt: 'Nutricao', color: '#7CB9E8' },
  promotional: { label: 'Promo', labelPt: 'Promocional', color: '#E8A87C' },
  seasonal: { label: 'Seasonal', labelPt: 'Sazonal', color: '#A87CE8' },
};

const STATUS_META = {
  draft: { label: 'Draft', labelPt: 'Rascunho', color: '#666', bg: '#666/10' },
  active: { label: 'Active', labelPt: 'Ativa', color: '#4CAF50', bg: '#4CAF50/10' },
  paused: { label: 'Paused', labelPt: 'Pausada', color: '#FF9800', bg: '#FF9800/10' },
  completed: { label: 'Done', labelPt: 'Concluida', color: '#2196F3', bg: '#2196F3/10' },
};

function StatCard({ icon: Icon, value, label, trend }) {
  return (
    <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#C9A84C]/8">
          <Icon size={13} className="text-[#C9A84C]" />
        </div>
        {trend && <span className="text-[9px] text-green-400 ml-auto">+{trend}%</span>}
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
      <p className="text-[9px] text-[#555]">{label}</p>
    </div>
  );
}

function CampaignCard({ campaign, lang, onAction }) {
  const type = TYPE_META[campaign.type] || TYPE_META.nurture;
  const status = STATUS_META[campaign.status] || STATUS_META.draft;
  const stats = campaign.stats || {};
  const openRate = stats.sent > 0 ? Math.round((stats.opened / stats.sent) * 100) : 0;
  const convRate = stats.sent > 0 ? Math.round((stats.converted / stats.sent) * 100) : 0;

  return (
    <div data-testid={`campaign-card-${campaign.id}`} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3.5 hover:border-[#2A2A2A] transition group">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="text-[8px] uppercase font-semibold px-1.5 py-0.5 rounded" style={{ color: type.color, backgroundColor: `${type.color}15` }}>
              {lang === 'pt' ? type.labelPt : type.label}
            </span>
            <span className="text-[8px] uppercase font-semibold px-1.5 py-0.5 rounded" style={{ color: status.color, backgroundColor: `${status.color}15` }}>
              {lang === 'pt' ? status.labelPt : status.label}
            </span>
          </div>
          <h3 className="text-[13px] font-semibold text-white truncate">{campaign.name}</h3>
          <div className="flex items-center gap-3 mt-1.5">
            <span className="text-[9px] text-[#555] flex items-center gap-1"><Send size={9} />{stats.sent || 0} {lang === 'pt' ? 'enviadas' : 'sent'}</span>
            <span className="text-[9px] text-[#555] flex items-center gap-1"><TrendingUp size={9} />{openRate}% open</span>
            <span className="text-[9px] text-[#555] flex items-center gap-1"><Users size={9} />{convRate}% conv</span>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition">
          {campaign.status === 'draft' && (
            <button data-testid={`activate-${campaign.id}`} onClick={() => onAction('activate', campaign.id)} className="p-1.5 rounded-lg hover:bg-[#C9A84C]/10 text-[#C9A84C]" title="Activate">
              <Play size={13} />
            </button>
          )}
          {campaign.status === 'active' && (
            <button data-testid={`pause-${campaign.id}`} onClick={() => onAction('pause', campaign.id)} className="p-1.5 rounded-lg hover:bg-yellow-500/10 text-yellow-500" title="Pause">
              <Pause size={13} />
            </button>
          )}
          {campaign.status === 'paused' && (
            <button onClick={() => onAction('activate', campaign.id)} className="p-1.5 rounded-lg hover:bg-[#C9A84C]/10 text-[#C9A84C]" title="Resume">
              <Play size={13} />
            </button>
          )}
          <button data-testid={`delete-${campaign.id}`} onClick={() => onAction('delete', campaign.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-[#444] hover:text-red-400">
            <Trash2 size={13} />
          </button>
        </div>
      </div>
      {/* Steps preview */}
      {campaign.messages?.length > 0 && (
        <div className="mt-2.5 pt-2 border-t border-[#111] flex items-center gap-1.5">
          {campaign.messages.map((m, i) => (
            <div key={i} className="flex items-center gap-1">
              {i > 0 && <div className="w-4 h-px bg-[#222]" />}
              <div className="flex items-center gap-0.5 bg-[#111] rounded-md px-1.5 py-0.5">
                <Clock size={8} className="text-[#555]" />
                <span className="text-[8px] text-[#555]">{m.delay_hours === 0 ? 'Now' : `${m.delay_hours}h`}</span>
              </div>
            </div>
          ))}
          <span className="text-[8px] text-[#444] ml-1">{campaign.messages.length} {lang === 'pt' ? 'etapas' : 'steps'}</span>
        </div>
      )}
    </div>
  );
}

export default function Marketing() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const lang = i18n.language || 'en';
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState('free');
  const [filter, setFilter] = useState('all');
  const [view, setView] = useState('grid');
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('nurture');
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [campRes, statsRes] = await Promise.all([
        axios.get(`${API}/campaigns`),
        axios.get(`${API}/dashboard/stats`),
      ]);
      setCampaigns(campRes.data.campaigns || []);
      setPlan(statsRes.data.plan || 'free');
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const loadTemplates = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/templates/list`);
      setTemplates(data.templates || []);
      setShowTemplates(true);
    } catch { toast.error('Error loading templates'); }
  };

  const createCampaign = async (name, type, messages) => {
    try {
      const { data } = await axios.post(`${API}/campaigns`, { name, type, messages: messages || [] });
      setCampaigns(prev => [data, ...prev]);
      setShowNew(false);
      setNewName('');
      toast.success(lang === 'pt' ? 'Campanha criada!' : 'Campaign created!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };

  const handleAction = async (action, id) => {
    try {
      if (action === 'activate') {
        await axios.post(`${API}/campaigns/${id}/activate`);
        setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'active' } : c));
        toast.success(lang === 'pt' ? 'Campanha ativada!' : 'Campaign activated!');
      } else if (action === 'pause') {
        await axios.post(`${API}/campaigns/${id}/pause`);
        setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'paused' } : c));
        toast.success(lang === 'pt' ? 'Campanha pausada' : 'Campaign paused');
      } else if (action === 'delete') {
        if (!window.confirm(lang === 'pt' ? 'Excluir campanha?' : 'Delete campaign?')) return;
        await axios.delete(`${API}/campaigns/${id}`);
        setCampaigns(prev => prev.filter(c => c.id !== id));
        toast.success(lang === 'pt' ? 'Excluida' : 'Deleted');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    }
  };

  const seedTest = async () => {
    try {
      await axios.post(`${API}/campaigns/seed-test`);
      await loadData();
      toast.success(lang === 'pt' ? 'Dados de teste criados!' : 'Test data created!');
    } catch { toast.error('Error seeding'); }
  };

  const filtered = filter === 'all' ? campaigns : campaigns.filter(c => c.status === filter);
  const totalSent = campaigns.reduce((s, c) => s + (c.stats?.sent || 0), 0);
  const totalConverted = campaigns.reduce((s, c) => s + (c.stats?.converted || 0), 0);
  const avgOpenRate = campaigns.length > 0 ? Math.round(campaigns.reduce((s, c) => s + (c.stats?.sent > 0 ? (c.stats.opened / c.stats.sent) * 100 : 0), 0) / campaigns.length) : 0;
  const isEnterprise = plan === 'enterprise';

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-20">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-3 py-2.5">
        <div className="flex items-center gap-2.5">
          <button data-testid="marketing-back" onClick={() => navigate('/dashboard')} className="text-[#666] hover:text-white transition"><ArrowLeft size={18} /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10 shrink-0"><Megaphone size={16} className="text-[#C9A84C]" /></div>
          <div className="flex-1">
            <h1 className="text-sm font-semibold text-white">{lang === 'pt' ? 'Marketing & Campanhas' : 'Marketing & Campaigns'}</h1>
            <p className="text-[9px] text-[#555]">{campaigns.length} {lang === 'pt' ? 'campanhas' : 'campaigns'}</p>
          </div>
          <div className="flex items-center gap-1.5">
            {isEnterprise && (
              <button data-testid="open-studio-btn" onClick={() => navigate('/marketing/studio')}
                className="flex items-center gap-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-3 py-1.5 text-[10px] font-semibold text-black transition hover:opacity-90">
                <Sparkles size={12} /> AI Studio
              </button>
            )}
            <button data-testid="new-campaign-btn" onClick={() => setShowNew(true)}
              className="flex items-center gap-1 rounded-lg border border-[#C9A84C]/30 px-2.5 py-1.5 text-[10px] text-[#C9A84C] hover:bg-[#C9A84C]/5 transition">
              <Plus size={12} /> {lang === 'pt' ? 'Nova' : 'New'}
            </button>
          </div>
        </div>
      </div>

      <div className="px-3 pt-3 max-w-4xl mx-auto">
        {/* AI Studio CTA for non-Enterprise */}
        {!isEnterprise && (
          <div data-testid="studio-upsell" className="mb-3 rounded-xl border border-[#C9A84C]/15 bg-gradient-to-r from-[#C9A84C]/5 to-transparent p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#C9A84C]/10 shrink-0">
                <Sparkles size={18} className="text-[#C9A84C]" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <h3 className="text-[12px] font-semibold text-white">Marketing AI Studio</h3>
                  <span className="text-[8px] font-bold bg-[#C9A84C]/15 text-[#C9A84C] px-1.5 py-0.5 rounded flex items-center gap-0.5"><Lock size={7} /> ENTERPRISE</span>
                </div>
                <p className="text-[10px] text-[#888] mb-2">{lang === 'pt' ? '4 agentes IA especializados: Copywriter, Designer, Reviewer e Publisher. Crie campanhas completas com inteligencia artificial.' : '4 specialized AI agents: Copywriter, Designer, Reviewer and Publisher. Create complete campaigns with AI.'}</p>
                <button data-testid="upgrade-enterprise-btn" onClick={() => navigate('/upgrade')}
                  className="btn-gold rounded-lg px-3 py-1.5 text-[10px]">
                  {lang === 'pt' ? 'Upgrade para Enterprise' : 'Upgrade to Enterprise'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          <StatCard icon={Megaphone} value={campaigns.length} label={lang === 'pt' ? 'Campanhas' : 'Campaigns'} />
          <StatCard icon={Send} value={totalSent} label={lang === 'pt' ? 'Enviadas' : 'Sent'} trend={12} />
          <StatCard icon={BarChart3} value={`${avgOpenRate}%`} label={lang === 'pt' ? 'Taxa Abertura' : 'Open Rate'} />
          <StatCard icon={Users} value={totalConverted} label={lang === 'pt' ? 'Conversoes' : 'Conversions'} trend={8} />
        </div>

        {/* Filter + View Toggle */}
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex gap-1">
            {['all', 'active', 'draft', 'paused'].map(f => (
              <button key={f} data-testid={`filter-${f}`} onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition ${filter === f ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
                {f === 'all' ? (lang === 'pt' ? 'Todas' : 'All') : (STATUS_META[f]?.[lang === 'pt' ? 'labelPt' : 'label'] || f)}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={loadTemplates} className="text-[9px] text-[#C9A84C] hover:underline mr-2">
              {lang === 'pt' ? 'Templates' : 'Templates'}
            </button>
            <button onClick={() => setView('grid')} className={`p-1 rounded ${view === 'grid' ? 'text-[#C9A84C]' : 'text-[#444]'}`}><LayoutGrid size={13} /></button>
            <button onClick={() => setView('list')} className={`p-1 rounded ${view === 'list' ? 'text-[#C9A84C]' : 'text-[#444]'}`}><List size={13} /></button>
          </div>
        </div>

        {/* New Campaign Form */}
        {showNew && (
          <div data-testid="new-campaign-form" className="mb-3 rounded-xl border border-[#C9A84C]/20 bg-[#0D0D0D] p-3 space-y-2">
            <input data-testid="campaign-name-input" value={newName} onChange={e => setNewName(e.target.value)}
              placeholder={lang === 'pt' ? 'Nome da campanha...' : 'Campaign name...'}
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[12px] text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/30" autoFocus />
            <div className="flex gap-1.5 flex-wrap">
              {Object.entries(TYPE_META).map(([key, meta]) => (
                <button key={key} onClick={() => setNewType(key)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-medium border transition ${newType === key ? 'border-[#C9A84C]/30 text-[#C9A84C] bg-[#C9A84C]/5' : 'border-[#1A1A1A] text-[#555]'}`}>
                  {lang === 'pt' ? meta.labelPt : meta.label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowNew(false)} className="flex-1 rounded-lg border border-[#1E1E1E] py-1.5 text-[10px] text-[#666]">{lang === 'pt' ? 'Cancelar' : 'Cancel'}</button>
              <button data-testid="create-campaign-submit" onClick={() => newName && createCampaign(newName, newType)}
                className="flex-1 btn-gold rounded-lg py-1.5 text-[10px]">{lang === 'pt' ? 'Criar' : 'Create'}</button>
            </div>
          </div>
        )}

        {/* Templates Modal */}
        {showTemplates && (
          <div className="mb-3 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-[11px] font-semibold text-white">{lang === 'pt' ? 'Templates Prontos' : 'Ready Templates'}</h3>
              <button onClick={() => setShowTemplates(false)} className="text-[#555] text-[10px]">x</button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {templates.map(tpl => (
                <button key={tpl.id} data-testid={`template-${tpl.id}`}
                  onClick={() => { createCampaign(lang === 'pt' ? tpl.name_pt : tpl.name, tpl.type, tpl.messages); setShowTemplates(false); }}
                  className="rounded-lg border border-[#1A1A1A] p-2.5 text-left hover:border-[#C9A84C]/20 transition">
                  <p className="text-[10px] font-medium text-white mb-0.5">{lang === 'pt' ? tpl.name_pt : tpl.name}</p>
                  <p className="text-[8px] text-[#555] line-clamp-2">{lang === 'pt' ? tpl.description_pt : tpl.description}</p>
                  <p className="text-[8px] text-[#C9A84C] mt-1">{tpl.messages?.length || 0} {lang === 'pt' ? 'etapas' : 'steps'}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Campaign List */}
        <div className={view === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-2' : 'space-y-2'}>
          {filtered.map(c => (
            <CampaignCard key={c.id} campaign={c} lang={lang} onAction={handleAction} />
          ))}
        </div>

        {filtered.length === 0 && !showNew && (
          <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-8 text-center mt-2">
            <Megaphone size={28} className="mx-auto mb-2 text-[#222]" />
            <p className="text-[11px] text-[#666] mb-2">{lang === 'pt' ? 'Nenhuma campanha encontrada' : 'No campaigns found'}</p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setShowNew(true)} className="btn-gold rounded-lg px-3 py-1.5 text-[10px]">
                <Plus size={11} className="inline mr-1" />{lang === 'pt' ? 'Criar Campanha' : 'Create Campaign'}
              </button>
              <button onClick={seedTest} className="rounded-lg border border-[#1E1E1E] px-3 py-1.5 text-[10px] text-[#666] hover:text-white transition">
                <Zap size={11} className="inline mr-1" />{lang === 'pt' ? 'Dados de Teste' : 'Test Data'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
