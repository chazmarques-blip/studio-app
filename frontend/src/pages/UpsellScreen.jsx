import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, Zap, Check, ArrowRight, Clock } from 'lucide-react';

export default function UpsellScreen() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] px-4">
      <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/3 h-[400px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[120px]" /></div>
      <div className="relative z-10 w-full max-w-md text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
          <AlertTriangle size={32} className="text-[#C9A84C]" />
        </div>
        <h1 className="mb-2 text-2xl font-bold text-white">{t('upsell.title')}</h1>
        <p className="mb-4 text-sm text-[#A0A0A0]">{t('upsell.used', { used: 50, limit: 50 })}</p>
        <div className="mb-6 h-2 overflow-hidden rounded-full bg-[#1E1E1E]"><div className="h-full w-full rounded-full bg-gradient-to-r from-[#C9A84C] to-red-400" /></div>

        <div className="mb-6 flex items-center gap-2 justify-center text-sm text-[#A0A0A0]">
          <Clock size={14} className="text-[#C9A84C]" />
          <span>{t('upsell.reset')}: <span className="font-semibold text-white">3{t('common.days')} 14{t('common.hours')} 22{t('common.minutes')}</span></span>
        </div>

        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="glass-card p-4 text-left">
            <p className="mb-2 text-xs font-semibold text-[#666666]">{t('upsell.current_plan')}</p>
            <ul className="space-y-1.5 text-xs text-[#A0A0A0]">
              <li>1 Agent</li>
              <li>50 msgs/week</li>
              <li>1 Channel</li>
            </ul>
          </div>
          <div className="glass-card border-[rgba(201,168,76,0.4)] gold-glow p-4 text-left">
            <p className="mb-2 text-xs font-semibold text-[#C9A84C]">{t('upsell.recommended')}</p>
            <ul className="space-y-1.5 text-xs text-[#A0A0A0]">
              <li className="flex items-center gap-1"><Check size={10} className="text-[#C9A84C]" /> 5 Agents</li>
              <li className="flex items-center gap-1"><Check size={10} className="text-[#C9A84C]" /> 10,000 msgs/mo</li>
              <li className="flex items-center gap-1"><Check size={10} className="text-[#C9A84C]" /> All Channels</li>
              <li className="flex items-center gap-1"><Check size={10} className="text-[#C9A84C]" /> Full CRM</li>
            </ul>
            <p className="mt-2 text-lg font-bold text-[#C9A84C]">$49<span className="text-xs text-[#666666]">/mo</span></p>
          </div>
        </div>

        <button className="btn-gold w-full rounded-xl py-3.5 text-sm font-semibold flex items-center justify-center gap-2 animate-shimmer">
          <Zap size={16} /> {t('upsell.upgrade')} <ArrowRight size={16} />
        </button>
        <button onClick={() => navigate('/dashboard')} className="mt-3 w-full py-2 text-xs text-[#666666] hover:text-[#A0A0A0]">{t('upsell.continue_free')}</button>
      </div>
    </div>
  );
}
