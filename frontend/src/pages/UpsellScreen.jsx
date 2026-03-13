import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, Zap, Check, ArrowRight, Clock, Crown, Sparkles } from 'lucide-react';

export default function UpsellScreen() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';

  const plans = [
    {
      id: 'free',
      name: lang === 'pt' ? 'Free (atual)' : 'Free (current)',
      price: null,
      current: true,
      features: [
        { text: '1 Agent' },
        { text: '50 msgs/week' },
        { text: '1 Channel' },
      ],
    },
    {
      id: 'starter',
      name: 'Starter Plan',
      price: '$49',
      features: [
        { text: '5 Agents' },
        { text: '10,000 msgs/mo' },
        { text: lang === 'pt' ? 'Todos Canais' : 'All Channels' },
        { text: 'CRM' },
      ],
    },
    {
      id: 'pro',
      name: 'Pro Plan',
      price: '$99',
      recommended: true,
      features: [
        { text: '15 Agents' },
        { text: '50,000 msgs/mo' },
        { text: lang === 'pt' ? 'Todos Canais' : 'All Channels' },
        { text: 'CRM + Analytics' },
        { text: lang === 'pt' ? 'Agentes Pessoais' : 'Personal Agents' },
        { text: 'Google Calendar & Sheets' },
      ],
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      price: '$249',
      enterprise: true,
      features: [
        { text: lang === 'pt' ? 'Agentes Ilimitados' : 'Unlimited Agents' },
        { text: lang === 'pt' ? 'Mensagens Ilimitadas' : 'Unlimited Messages' },
        { text: lang === 'pt' ? 'Todos Canais' : 'All Channels' },
        { text: 'CRM + Analytics' },
        { text: 'Marketing AI Studio' },
        { text: lang === 'pt' ? 'Pipeline Autonomo' : 'Autonomous Pipeline' },
        { text: lang === 'pt' ? 'Campanhas IA' : 'AI Campaigns' },
        { text: lang === 'pt' ? 'Suporte Prioritario' : 'Priority Support' },
      ],
    },
  ];

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] px-4 py-8">
      <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/3 h-[400px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[120px]" /></div>
      <div className="relative z-10 w-full max-w-3xl">
        <div className="text-center mb-6">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
            <AlertTriangle size={28} className="text-[#C9A84C]" />
          </div>
          <h1 className="mb-1.5 text-xl font-bold text-white">{t('upsell.title')}</h1>
          <p className="mb-3 text-xs text-[#A0A0A0]">{t('upsell.used', { used: 50, limit: 50 })}</p>
          <div className="mx-auto max-w-xs mb-4 h-2 overflow-hidden rounded-full bg-[#1E1E1E]"><div className="h-full w-full rounded-full bg-gradient-to-r from-[#C9A84C] to-red-400" /></div>
          <div className="flex items-center gap-2 justify-center text-xs text-[#A0A0A0]">
            <Clock size={12} className="text-[#C9A84C]" />
            <span>{t('upsell.reset')}: <span className="font-semibold text-white">3{t('common.days')} 14{t('common.hours')} 22{t('common.minutes')}</span></span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mb-6">
          {plans.map(plan => (
            <div key={plan.id} data-testid={`plan-${plan.id}`}
              className={`rounded-xl border p-3.5 text-left transition ${
                plan.enterprise ? 'border-[#C9A84C]/50 bg-gradient-to-b from-[#C9A84C]/10 to-transparent shadow-[0_0_20px_rgba(201,168,76,0.1)]' :
                plan.recommended ? 'border-[#C9A84C]/30 bg-[#0D0D0D]' :
                plan.current ? 'border-[#1E1E1E] bg-[#0D0D0D]' :
                'border-[#1E1E1E] bg-[#0D0D0D]'
              }`}>
              <div className="flex items-center gap-1.5 mb-2">
                {plan.enterprise && <Crown size={12} className="text-[#C9A84C]" />}
                {plan.recommended && <Sparkles size={12} className="text-[#C9A84C]" />}
                <p className={`text-[11px] font-semibold ${plan.enterprise || plan.recommended ? 'text-[#C9A84C]' : plan.current ? 'text-[#666]' : 'text-white'}`}>
                  {plan.name}
                </p>
              </div>
              <ul className="space-y-1 mb-3">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-center gap-1 text-[10px] text-[#A0A0A0]">
                    {!plan.current && <Check size={8} className="text-[#C9A84C] shrink-0" />}
                    {f.text}
                  </li>
                ))}
              </ul>
              {plan.price && (
                <p className={`text-base font-bold ${plan.enterprise ? 'text-[#C9A84C]' : 'text-white'}`}>
                  {plan.price}<span className="text-[10px] text-[#666] font-normal">/mo</span>
                </p>
              )}
            </div>
          ))}
        </div>

        <button data-testid="upgrade-btn" className="btn-gold w-full max-w-sm mx-auto block rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2 animate-shimmer">
          <Zap size={16} /> {t('upsell.upgrade')} <ArrowRight size={16} />
        </button>
        <button onClick={() => navigate(-1)} className="mt-3 w-full py-2 text-xs text-[#666666] hover:text-[#A0A0A0] text-center">{t('upsell.continue_free')}</button>
      </div>
    </div>
  );
}
