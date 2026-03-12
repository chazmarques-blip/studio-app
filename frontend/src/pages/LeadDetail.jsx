import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Phone, Mail, Building, Target, Sparkles, Trash2, ChevronDown } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STAGES = [
  { key: 'new', color: '#C9A84C', label: 'New' },
  { key: 'qualified', color: '#60A5FA', label: 'Qualified' },
  { key: 'proposal', color: '#A78BFA', label: 'Proposal' },
  { key: 'won', color: '#4ADE80', label: 'Won' },
  { key: 'lost', color: '#666666', label: 'Lost' },
];

export default function LeadDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [lead, setLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [stageOpen, setStageOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    axios.get(`${API}/leads/${id}`).then(r => setLead(r.data)).catch(() => navigate('/crm')).finally(() => setLoading(false));
  }, [id, navigate]);

  const handleStageChange = async (newStage) => {
    setStageOpen(false);
    if (!lead || lead.stage === newStage) return;
    setLead(prev => ({ ...prev, stage: newStage }));
    try {
      await axios.put(`${API}/leads/${id}`, { stage: newStage });
    } catch { }
  };

  const handleAiScore = async () => {
    setScoring(true);
    try {
      const res = await axios.post(`${API}/leads/${id}/ai-score`);
      setLead(prev => ({ ...prev, score: res.data.score, ai_analysis: res.data }));
    } catch (e) {
      console.error(e);
    } finally {
      setScoring(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('Delete this lead?')) return;
    setDeleting(true);
    try {
      await axios.delete(`${API}/leads/${id}`);
      navigate('/crm');
    } catch { setDeleting(false); }
  };

  if (loading) return <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center"><div className="h-6 w-6 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" /></div>;
  if (!lead) return null;

  const currentStage = STAGES.find(s => s.key === lead.stage) || STAGES[0];
  const ai = lead.ai_analysis || {};

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-5 pb-24">
      {/* Header */}
      <div className="mb-5 flex items-center gap-3">
        <button data-testid="back-to-crm" onClick={() => navigate('/crm')} className="text-[#666] hover:text-white transition"><ArrowLeft size={20} /></button>
        <h1 className="text-lg font-bold text-white flex-1">{lead.name}</h1>
        <button data-testid="delete-lead-btn" onClick={handleDelete} disabled={deleting} className="text-[#444] hover:text-red-400 transition"><Trash2 size={16} /></button>
      </div>

      {/* Lead info card */}
      <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4 mb-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-11 w-11 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] flex items-center justify-center flex-shrink-0">
            <span className="text-base font-bold text-[#0A0A0A]">{lead.name?.[0] || '?'}</span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-white truncate">{lead.name}</p>
            {/* Stage badge with dropdown */}
            <div className="relative inline-block">
              <button data-testid="stage-dropdown-btn" onClick={() => setStageOpen(!stageOpen)} className="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium mt-0.5" style={{ backgroundColor: `${currentStage.color}15`, color: currentStage.color }}>
                <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: currentStage.color }} />
                {currentStage.label}
                <ChevronDown size={10} />
              </button>
              {stageOpen && (
                <div className="absolute left-0 top-full mt-1 z-20 rounded-lg border border-[#1E1E1E] bg-[#111] py-1 shadow-xl min-w-[120px]">
                  {STAGES.map(s => (
                    <button key={s.key} data-testid={`stage-option-${s.key}`} onClick={() => handleStageChange(s.key)}
                      className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-xs text-white hover:bg-[#1A1A1A] transition">
                      <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
                      {s.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          {/* Score circle */}
          {lead.score > 0 && (
            <div className="flex h-11 w-11 items-center justify-center rounded-full border-2 flex-shrink-0" style={{ borderColor: lead.score >= 70 ? '#4ADE80' : lead.score >= 40 ? '#C9A84C' : '#666' }}>
              <span className="text-sm font-bold" style={{ color: lead.score >= 70 ? '#4ADE80' : lead.score >= 40 ? '#C9A84C' : '#666' }}>{lead.score}</span>
            </div>
          )}
        </div>
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          {lead.phone && <div className="flex items-center gap-1.5 text-[#888]"><Phone size={11} className="text-[#555]" />{lead.phone}</div>}
          {lead.email && <div className="flex items-center gap-1.5 text-[#888]"><Mail size={11} className="text-[#555]" />{lead.email}</div>}
          {lead.company && <div className="flex items-center gap-1.5 text-[#888]"><Building size={11} className="text-[#555]" />{lead.company}</div>}
          {lead.value > 0 && <div className="flex items-center gap-1.5 text-[#C9A84C] font-semibold"><Target size={11} />${parseFloat(lead.value).toLocaleString()}</div>}
        </div>
      </div>

      {/* AI Analysis */}
      <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4 mb-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="flex items-center gap-2 text-xs font-semibold text-[#C9A84C]"><Sparkles size={14} /> {t('crm.ai_analysis')}</h3>
          <button data-testid="ai-score-btn" onClick={handleAiScore} disabled={scoring} className="rounded-lg border border-[#C9A84C]/20 bg-[#C9A84C]/5 px-3 py-1 text-[10px] font-medium text-[#C9A84C] hover:bg-[#C9A84C]/10 transition disabled:opacity-40">
            {scoring ? 'Analyzing...' : 'Run AI Score'}
          </button>
        </div>
        {ai.reason ? (
          <div className="space-y-2.5 text-xs">
            <div>
              <p className="text-[10px] text-[#555] mb-1">Score</p>
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 rounded-full bg-[#1E1E1E]">
                  <div className="h-full rounded-full transition-all duration-500" style={{ width: `${ai.score || 0}%`, backgroundColor: (ai.score || 0) >= 70 ? '#4ADE80' : (ai.score || 0) >= 40 ? '#C9A84C' : '#666' }} />
                </div>
                <span className="text-xs font-bold text-white">{ai.score || 0}/100</span>
              </div>
            </div>
            <div><p className="text-[10px] text-[#555]">Analysis</p><p className="text-[#999]">{ai.reason}</p></div>
            {ai.stage_suggestion && ai.stage_suggestion !== lead.stage && (
              <div className="flex items-center gap-2">
                <p className="text-[10px] text-[#555]">Suggested stage:</p>
                <button onClick={() => handleStageChange(ai.stage_suggestion)} className="rounded-full bg-[#C9A84C]/10 px-2 py-0.5 text-[10px] font-medium text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
                  Move to {ai.stage_suggestion}
                </button>
              </div>
            )}
            {ai.next_action && <div><p className="text-[10px] text-[#555]">Next action</p><p className="text-[#C9A84C]">{ai.next_action}</p></div>}
          </div>
        ) : (
          <p className="text-xs text-[#444]">Click "Run AI Score" to get an AI analysis of this lead</p>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-2">
        <button data-testid="mark-won-btn" onClick={() => handleStageChange('won')} className="rounded-lg border border-[#4ADE80]/20 bg-[#4ADE80]/5 py-2.5 text-xs text-[#4ADE80] font-medium hover:bg-[#4ADE80]/10 transition">{t('crm.mark_won')}</button>
        <button data-testid="mark-lost-btn" onClick={() => handleStageChange('lost')} className="rounded-lg border border-red-500/20 bg-red-500/5 py-2.5 text-xs text-red-400 font-medium hover:bg-red-500/10 transition">{t('crm.mark_lost')}</button>
      </div>
    </div>
  );
}
