import { useTranslation } from 'react-i18next';
import { Target, Plus } from 'lucide-react';

export default function CRM() {
  const { t } = useTranslation();
  const stages = [
    { name: t('crm.new'), color: '#C9A84C', count: 0 },
    { name: t('crm.qualified'), color: '#2196F3', count: 0 },
    { name: t('crm.proposal'), color: '#9C27B0', count: 0 },
    { name: t('crm.won'), color: '#4CAF50', count: 0 },
    { name: t('crm.lost'), color: '#666666', count: 0 },
  ];
  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('crm.pipeline')}</h1>
        <button data-testid="add-lead-btn" className="btn-gold flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs"><Plus size={14} /> {t('crm.add_lead')}</button>
      </div>
      <div className="mb-4 flex gap-3 overflow-x-auto pb-2">
        <div className="glass-card flex-shrink-0 px-4 py-2.5"><p className="text-xs text-[#666666]">{t('crm.total_leads')}</p><p className="text-base font-bold text-white">0</p></div>
        <div className="glass-card flex-shrink-0 px-4 py-2.5"><p className="text-xs text-[#666666]">{t('crm.pipeline_value')}</p><p className="text-base font-bold text-white">$0</p></div>
        <div className="glass-card flex-shrink-0 px-4 py-2.5"><p className="text-xs text-[#666666]">{t('crm.conversion')}</p><p className="text-base font-bold text-white">0%</p></div>
      </div>
      <div className="flex gap-3 overflow-x-auto pb-4">
        {stages.map(stage => (
          <div key={stage.name} data-testid={`stage-${stage.name.toLowerCase()}`} className="w-64 flex-shrink-0">
            <div className="mb-3 flex items-center gap-2">
              <div className="h-2 w-2 rounded-full" style={{ backgroundColor: stage.color }} />
              <span className="text-sm font-semibold text-white">{stage.name}</span>
              <span className="ml-auto rounded-full bg-[#1A1A1A] px-2 py-0.5 text-xs text-[#666666]">{stage.count}</span>
            </div>
            <div className="min-h-[200px] rounded-xl bg-[#111111] border border-[#1A1A1A] p-3">
              <div className="flex h-32 items-center justify-center"><p className="text-center text-xs text-[#3A3A3A]">{t('crm.no_leads')}</p></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
