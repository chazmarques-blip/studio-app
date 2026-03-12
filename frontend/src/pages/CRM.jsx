import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Target, Plus, Phone, Mail, GripVertical } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function CRM() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/leads`).then(r => setLeads(r.data.leads)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const stages = [
    { key: 'new', name: t('crm.new'), color: '#C9A84C' },
    { key: 'qualified', name: t('crm.qualified'), color: '#2196F3' },
    { key: 'proposal', name: t('crm.proposal'), color: '#9C27B0' },
    { key: 'won', name: t('crm.won'), color: '#4CAF50' },
    { key: 'lost', name: t('crm.lost'), color: '#666666' },
  ];

  const leadsByStage = (stageKey) => leads.filter(l => l.stage === stageKey);
  const totalValue = leads.reduce((sum, l) => sum + (parseFloat(l.value) || 0), 0);
  const wonCount = leads.filter(l => l.stage === 'won').length;
  const convRate = leads.length > 0 ? Math.round((wonCount / leads.length) * 100) : 0;

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('crm.pipeline')}</h1>
        <button data-testid="add-lead-btn" className="btn-gold flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs"><Plus size={14} /> {t('crm.add_lead')}</button>
      </div>
      <div className="mb-4 flex gap-3 overflow-x-auto pb-2">
        <div className="glass-card flex-shrink-0 px-4 py-2.5"><p className="text-xs text-[#666666]">{t('crm.total_leads')}</p><p className="text-base font-bold text-white">{leads.length}</p></div>
        <div className="glass-card flex-shrink-0 px-4 py-2.5"><p className="text-xs text-[#666666]">{t('crm.pipeline_value')}</p><p className="text-base font-bold text-white">${totalValue.toLocaleString()}</p></div>
        <div className="glass-card flex-shrink-0 px-4 py-2.5"><p className="text-xs text-[#666666]">{t('crm.conversion')}</p><p className="text-base font-bold text-white">{convRate}%</p></div>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-4">
        {stages.map(stage => {
          const stageLeads = leadsByStage(stage.key);
          return (
            <div key={stage.key} data-testid={`stage-${stage.key}`} className="w-64 flex-shrink-0">
              <div className="mb-3 flex items-center gap-2">
                <div className="h-2 w-2 rounded-full" style={{ backgroundColor: stage.color }} />
                <span className="text-sm font-semibold text-white">{stage.name}</span>
                <span className="ml-auto rounded-full bg-[#1A1A1A] px-2 py-0.5 text-xs text-[#666666]">{stageLeads.length}</span>
              </div>
              <div className="min-h-[200px] rounded-xl bg-[#111111] border border-[#1A1A1A] p-2 space-y-2">
                {stageLeads.length > 0 ? stageLeads.map(lead => (
                  <button key={lead.id} data-testid={`lead-${lead.id}`} onClick={() => navigate(`/crm/lead/${lead.id}`)}
                    className="glass-card w-full p-3 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
                    <div className="flex items-center gap-2 mb-1">
                      <GripVertical size={12} className="text-[#333]" />
                      <p className="text-sm font-medium text-white truncate">{lead.name}</p>
                    </div>
                    {lead.phone && <p className="flex items-center gap-1 text-[10px] text-[#666666]"><Phone size={9} />{lead.phone}</p>}
                    {lead.email && <p className="flex items-center gap-1 text-[10px] text-[#666666]"><Mail size={9} />{lead.email}</p>}
                    {lead.value > 0 && <p className="mt-1 text-xs font-semibold text-[#C9A84C]">${parseFloat(lead.value).toLocaleString()}</p>}
                    {lead.score > 0 && (
                      <div className="mt-1 flex items-center gap-1">
                        <div className="h-1 flex-1 rounded bg-[#1E1E1E]"><div className="h-full rounded bg-[#C9A84C]" style={{ width: `${lead.score}%` }} /></div>
                        <span className="text-[9px] text-[#666]">{lead.score}</span>
                      </div>
                    )}
                  </button>
                )) : (
                  <div className="flex h-32 items-center justify-center"><p className="text-center text-xs text-[#3A3A3A]">{t('crm.no_leads')}</p></div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
