import { useTranslation } from 'react-i18next';
import { BarChart3 } from 'lucide-react';

export default function Analytics() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('analytics.title')}</h1>
        <button className="glass-card px-3 py-1.5 text-xs text-[#A0A0A0]">{t('analytics.last_7_days')}</button>
      </div>
      <div className="mb-6 grid grid-cols-2 gap-3">
        {[{ label: t('analytics.total_messages'), value: '0', color: '#C9A84C' }, { label: t('dashboard.resolution_rate'), value: '0%', color: '#4CAF50' }, { label: t('analytics.avg_response'), value: '0s', color: '#2196F3' }, { label: t('analytics.total_cost'), value: '$0.00', color: '#FF9800' }].map((s, i) => (
          <div key={i} className="glass-card p-4"><p className="text-lg font-bold text-white">{s.value}</p><p className="text-xs text-[#666666]">{s.label}</p></div>
        ))}
      </div>
      <div data-testid="analytics-chart-placeholder" className="glass-card mb-6 p-6">
        <h3 className="mb-4 text-sm font-semibold text-[#A0A0A0]">{t('analytics.messages_over_time')}</h3>
        <div className="flex h-40 items-center justify-center"><div className="text-center"><BarChart3 size={32} className="mx-auto mb-2 text-[#2A2A2A]" /><p className="text-xs text-[#666666]">{t('analytics.no_data')}</p></div></div>
      </div>
      <div className="glass-card p-6">
        <h3 className="mb-4 text-sm font-semibold text-[#A0A0A0]">{t('analytics.agent_performance')}</h3>
        <div className="flex h-24 items-center justify-center"><p className="text-xs text-[#666666]">{t('analytics.no_agent_data')}</p></div>
      </div>
    </div>
  );
}
