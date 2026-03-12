import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function Pricing() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <h1 className="mb-2 text-center text-2xl font-bold text-white">{t('landing.pricing_title')}</h1>
      <p className="mb-8 text-center text-sm text-[#A0A0A0]">{t('landing.pricing_subtitle')}</p>
      <div className="mx-auto max-w-md space-y-4">
        <div className="glass-card p-6">
          <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_free')}</h3>
          <p className="mb-3 text-sm text-[#666666]">{t('landing.plan_free_desc')}</p>
          <div className="mb-4"><span className="text-3xl font-bold text-white">{t('landing.plan_free_price')}</span><span className="text-sm text-[#666666]">{t('landing.plan_free_period')}</span></div>
          <ul className="mb-4 space-y-2 text-sm text-[#A0A0A0]">
            {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"/>{t(`landing.plan_free_${k}`)}</li>)}
          </ul>
          <button className="btn-gold-outline w-full rounded-lg py-2.5 text-sm">{t('landing.plan_free_cta')}</button>
        </div>
        <div className="glass-card gold-glow relative border-[rgba(201,168,76,0.4)] p-6">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#C9A84C] px-3 py-0.5 text-xs font-semibold text-[#0A0A0A]">{t('landing.plan_starter_badge')}</div>
          <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_starter')}</h3>
          <p className="mb-3 text-sm text-[#666666]">{t('landing.plan_starter_desc')}</p>
          <div className="mb-4"><span className="text-3xl font-bold text-[#C9A84C]">{t('landing.plan_starter_price')}</span><span className="text-sm text-[#666666]">{t('landing.plan_starter_period')}</span></div>
          <ul className="mb-4 space-y-2 text-sm text-[#A0A0A0]">
            {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"/>{t(`landing.plan_starter_${k}`)}</li>)}
          </ul>
          <button className="btn-gold w-full rounded-lg py-2.5 text-sm">{t('landing.plan_starter_cta')}</button>
        </div>
        <div className="glass-card p-6">
          <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_enterprise')}</h3>
          <p className="mb-3 text-sm text-[#666666]">{t('landing.plan_enterprise_desc')}</p>
          <div className="mb-4"><span className="text-3xl font-bold text-white">{t('landing.plan_enterprise_price')}</span></div>
          <ul className="mb-4 space-y-2 text-sm text-[#A0A0A0]">
            {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"/>{t(`landing.plan_enterprise_${k}`)}</li>)}
          </ul>
          <button className="btn-gold-outline w-full rounded-lg py-2.5 text-sm">{t('landing.plan_enterprise_cta')}</button>
        </div>
      </div>
    </div>
  );
}
