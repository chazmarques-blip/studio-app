import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Target, Plus, Phone, Mail, Building, X, Sparkles, GripVertical, DollarSign } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STAGES = [
  { key: 'new', color: '#C9A84C' },
  { key: 'qualified', color: '#60A5FA' },
  { key: 'proposal', color: '#A78BFA' },
  { key: 'won', color: '#4ADE80' },
  { key: 'lost', color: '#666666' },
];

function LeadCard({ lead, onDragStart }) {
  const navigate = useNavigate();
  return (
    <div
      data-testid={`lead-card-${lead.id}`}
      draggable
      onDragStart={(e) => { e.dataTransfer.setData('lead_id', lead.id); onDragStart(lead.id); }}
      onClick={() => navigate(`/crm/lead/${lead.id}`)}
      className="group rounded-lg border border-[#1A1A1A] bg-[#0E0E0E] p-3 cursor-grab active:cursor-grabbing hover:border-[#C9A84C]/25 transition-all"
    >
      <div className="flex items-start gap-2 mb-1.5">
        <GripVertical size={12} className="text-[#999] mt-0.5 flex-shrink-0 opacity-0 group-hover:opacity-100 transition" />
        <p className="text-sm font-medium text-white truncate flex-1">{lead.name}</p>
        {lead.score > 0 && (
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
            lead.score >= 70 ? 'bg-[#4ADE80]/10 text-[#4ADE80]' : lead.score >= 40 ? 'bg-[#C9A84C]/10 text-[#C9A84C]' : 'bg-[#666]/10 text-[#999]'
          }`}>{lead.score}</span>
        )}
      </div>
      {lead.company && <p className="flex items-center gap-1 text-[10px] text-[#B0B0B0] mb-0.5"><Building size={9} />{lead.company}</p>}
      {lead.phone && <p className="flex items-center gap-1 text-[10px] text-[#B0B0B0]"><Phone size={9} />{lead.phone}</p>}
      {lead.value > 0 && <p className="mt-1.5 text-xs font-semibold text-[#C9A84C]">${parseFloat(lead.value).toLocaleString()}</p>}
    </div>
  );
}

function StageColumn({ stage, leads, onDrop, onDragStart, t }) {
  const [dragOver, setDragOver] = useState(false);
  const stageLeads = leads.filter(l => l.stage === stage.key);

  return (
    <div data-testid={`stage-${stage.key}`} className="w-60 flex-shrink-0">
      <div className="mb-2 flex items-center gap-2">
        <div className="h-2 w-2 rounded-full" style={{ backgroundColor: stage.color }} />
        <span className="text-xs font-semibold text-white">{t(`crm.${stage.key}`)}</span>
        <span className="ml-auto rounded-full bg-[#1A1A1A] px-1.5 py-0.5 text-[10px] text-[#B0B0B0]">{stageLeads.length}</span>
      </div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); const id = e.dataTransfer.getData('lead_id'); if (id) onDrop(id, stage.key); }}
        className={`min-h-[180px] rounded-xl border p-2 space-y-2 transition-all ${
          dragOver ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1A1A1A] bg-[#0B0B0B]'
        }`}
      >
        {stageLeads.length > 0 ? stageLeads.map(lead => (
          <LeadCard key={lead.id} lead={lead} onDragStart={onDragStart} />
        )) : (
          <div className="flex h-28 items-center justify-center">
            <p className="text-center text-[10px] text-[#999]">{t('crm.no_leads')}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function NewLeadModal({ open, onClose, onCreated }) {
  const { t } = useTranslation();
  const [form, setForm] = useState({ name: '', phone: '', email: '', company: '', value: '', stage: 'new' });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      const res = await axios.post(`${API}/leads`, { ...form, value: parseFloat(form.value) || 0 });
      onCreated(res.data);
      setForm({ name: '', phone: '', email: '', company: '', value: '', stage: 'new' });
      onClose();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4" onClick={onClose}>
      <div className="w-full max-w-sm rounded-2xl border border-[#1E1E1E] bg-[#0D0D0D] p-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-white">{t('crm.add_lead')}</h2>
          <button onClick={onClose} className="text-[#999] hover:text-white"><X size={18} /></button>
        </div>
        <div className="space-y-3">
          <input data-testid="lead-name-input" value={form.name} onChange={e => setForm(p => ({...p, name: e.target.value}))} placeholder="Name *" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/40" />
          <input data-testid="lead-phone-input" value={form.phone} onChange={e => setForm(p => ({...p, phone: e.target.value}))} placeholder="Phone" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/40" />
          <input data-testid="lead-email-input" value={form.email} onChange={e => setForm(p => ({...p, email: e.target.value}))} placeholder="Email" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/40" />
          <input data-testid="lead-company-input" value={form.company} onChange={e => setForm(p => ({...p, company: e.target.value}))} placeholder="Company" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/40" />
          <input data-testid="lead-value-input" value={form.value} onChange={e => setForm(p => ({...p, value: e.target.value}))} placeholder="Value ($)" type="number" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/40" />
          <select data-testid="lead-stage-select" value={form.stage} onChange={e => setForm(p => ({...p, stage: e.target.value}))} className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white outline-none focus:border-[#C9A84C]/40">
            {STAGES.map(s => <option key={s.key} value={s.key}>{s.key.charAt(0).toUpperCase() + s.key.slice(1)}</option>)}
          </select>
        </div>
        <button data-testid="save-lead-btn" onClick={handleSave} disabled={saving || !form.name.trim()} className="btn-gold mt-4 w-full rounded-lg py-2.5 text-sm font-semibold disabled:opacity-40">
          {saving ? '...' : t('crm.add_lead')}
        </button>
      </div>
    </div>
  );
}

export default function CRM() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [draggingId, setDraggingId] = useState(null);

  const fetchLeads = useCallback(() => {
    axios.get(`${API}/leads`).then(r => setLeads(r.data.leads)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  const handleDrop = async (leadId, newStage) => {
    const lead = leads.find(l => l.id === leadId);
    if (!lead || lead.stage === newStage) return;
    // Optimistic update
    setLeads(prev => prev.map(l => l.id === leadId ? { ...l, stage: newStage } : l));
    setDraggingId(null);
    try {
      await axios.put(`${API}/leads/${leadId}`, { stage: newStage });
    } catch {
      fetchLeads(); // Revert on error
    }
  };

  const handleCreated = (newLead) => {
    setLeads(prev => [newLead, ...prev]);
  };

  const totalValue = leads.reduce((sum, l) => sum + (parseFloat(l.value) || 0), 0);
  const wonValue = leads.filter(l => l.stage === 'won').reduce((sum, l) => sum + (parseFloat(l.value) || 0), 0);
  const convRate = leads.length > 0 ? Math.round((leads.filter(l => l.stage === 'won').length / leads.length) * 100) : 0;

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-5 pb-8">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">{t('crm.pipeline')}</h1>
          <p className="text-[11px] text-[#B0B0B0]">Drag & drop leads between stages</p>
        </div>
        <button data-testid="add-lead-btn" onClick={() => setShowModal(true)} className="btn-gold flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs">
          <Plus size={14} /> {t('crm.add_lead')}
        </button>
      </div>

      {/* Stats */}
      <div className="mb-4 flex gap-3 overflow-x-auto pb-1">
        <div className="flex-shrink-0 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-4 py-2.5">
          <p className="text-[10px] text-[#B0B0B0]">{t('crm.total_leads')}</p>
          <p className="text-base font-bold text-white">{leads.length}</p>
        </div>
        <div className="flex-shrink-0 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-4 py-2.5">
          <p className="text-[10px] text-[#B0B0B0]">{t('crm.pipeline_value')}</p>
          <p className="text-base font-bold text-white flex items-center gap-1"><DollarSign size={14} className="text-[#C9A84C]" />{totalValue.toLocaleString()}</p>
        </div>
        <div className="flex-shrink-0 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-4 py-2.5">
          <p className="text-[10px] text-[#B0B0B0]">Won</p>
          <p className="text-base font-bold text-[#4ADE80]">${wonValue.toLocaleString()}</p>
        </div>
        <div className="flex-shrink-0 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-4 py-2.5">
          <p className="text-[10px] text-[#B0B0B0]">{t('crm.conversion')}</p>
          <p className="text-base font-bold text-white">{convRate}%</p>
        </div>
      </div>

      {/* Kanban Board */}
      {loading ? (
        <div className="flex h-48 items-center justify-center"><div className="h-6 w-6 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" /></div>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-4">
          {STAGES.map(stage => (
            <StageColumn key={stage.key} stage={stage} leads={leads} onDrop={handleDrop} onDragStart={setDraggingId} t={t} />
          ))}
        </div>
      )}

      <NewLeadModal open={showModal} onClose={() => setShowModal(false)} onCreated={handleCreated} />
    </div>
  );
}
