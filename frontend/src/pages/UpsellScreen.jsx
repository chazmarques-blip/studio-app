import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AlertTriangle, Zap, Check, ArrowRight, Clock, Crown, Sparkles } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { getErrorMsg } from '../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLANS = [
  { key: 'free', agents: 1, msgs: 200, price: { annual: 0, monthly: 0 } },
  { key: 'starter', agents: 3, msgs: 1500, price: { annual: 49, monthly: 49 } },
  { key: 'pro', agents: 5, msgs: 5000, price: { annual: 299, monthly: 349 } },
  { key: 'enterprise', agents: 10, msgs: 10000, price: { annual: 699, monthly: 749 } },
];

export default function UpsellScreen() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [billingAnnual, setBillingAnnual] = useState(true);
  const [upgrading, setUpgrading] = useState(null);

  const handleUpgrade = async (planKey) => {
    setUpgrading(planKey);
    try {
      await axios.post(`${API}/billing/upgrade`, { plan: planKey, billing_cycle: billingAnnual ? 'annual' : 'monthly' });
      toast.success(lang === 'pt' ? `Upgrade para ${planKey} realizado!` : `Upgraded to ${planKey}!`);
      navigate(-1);
    } catch (e) {
      toast.error(getErrorMsg(e, 'Upgrade failed'));
    } finally {
      setUpgrading(null);
    }
  };

  const planIcons = { free: Zap, starter: Sparkles, pro: Crown, enterprise: Crown };
  const planExtras = {
    enterprise: lang === 'pt'
      ? ['Marketing AI Studio', 'Pipeline Autonomo', 'Campanhas IA', 'Suporte Prioritario']
      : ['Marketing AI Studio', 'Autonomous Pipeline', 'AI Campaigns', 'Priority Support'],
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] px-4 py-8">
      <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/3 h-[400px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[120px]" /></div>
      <div className="relative z-10 w-full max-w-3xl">
        <div className="text-center mb-5">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
            <AlertTriangle size={28} className="text-[#C9A84C]" />
          </div>
          <h1 className="mb-1.5 text-xl font-bold text-white">{t('upsell.title')}</h1>
          <p className="mb-3 text-xs text-[#A0A0A0]">{t('upsell.used', { used: 50, limit: 50 })}</p>
          <div className="mx-auto max-w-xs mb-3 h-2 overflow-hidden rounded-full bg-[#1E1E1E]"><div className="h-full w-full rounded-full bg-gradient-to-r from-[#C9A84C] to-red-400" /></div>
          <div className="flex items-center gap-2 justify-center text-xs text-[#A0A0A0]">
            <Clock size={12} className="text-[#C9A84C]" />
            <span>{t('upsell.reset')}: <span className="font-semibold text-white">3{t('common.days')} 14{t('common.hours')} 22{t('common.minutes')}</span></span>
          </div>
        </div>

        {/* Billing Toggle */}
        <div className="mb-5 flex justify-center">
          <div className="inline-flex items-center gap-1 rounded-full border border-[#1E1E1E] bg-[#0D0D0D] p-1">
            <button data-testid="billing-annual" onClick={() => setBillingAnnual(true)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#999]'}`}>
              {lang === 'pt' ? 'Anual' : 'Annual'} <span className="ml-1 text-[9px] opacity-80">{lang === 'pt' ? 'Economize 14%' : 'Save 14%'}</span>
            </button>
            <button data-testid="billing-monthly" onClick={() => setBillingAnnual(false)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${!billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#999]'}`}>
              {lang === 'pt' ? 'Mensal' : 'Monthly'}
            </button>
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5 mb-6">
          {PLANS.map(plan => {
            const price = billingAnnual ? plan.price.annual : plan.price.monthly;
            const Icon = planIcons[plan.key];
            const isFree = plan.key === 'free';
            const isEnterprise = plan.key === 'enterprise';
            const extras = planExtras[plan.key] || [];

            return (
              <div key={plan.key} data-testid={`plan-${plan.key}`}
                className={`rounded-xl border p-3.5 text-left flex flex-col transition ${
                  isEnterprise ? 'border-[#C9A84C]/50 bg-gradient-to-b from-[#C9A84C]/10 to-transparent shadow-[0_0_20px_rgba(201,168,76,0.1)]' :
                  isFree ? 'border-[#1E1E1E] bg-[#0D0D0D]' :
                  'border-[#1E1E1E] bg-[#0D0D0D]'
                }`}>
                <div className="flex items-center gap-1.5 mb-2">
                  {!isFree && <Icon size={12} className="text-[#C9A84C]" />}
                  <p className={`text-[11px] font-semibold capitalize ${isEnterprise ? 'text-[#C9A84C]' : isFree ? 'text-[#999]' : 'text-white'}`}>
                    {plan.key}{isFree ? (lang === 'pt' ? ' (atual)' : ' (current)') : ''}
                  </p>
                </div>
                <ul className="space-y-1 mb-3 flex-1">
                  <li className="flex items-center gap-1 text-[10px] text-[#A0A0A0]">
                    {!isFree && <Check size={8} className="text-[#C9A84C] shrink-0" />}
                    {plan.agents} {plan.agents === 1 ? 'Agent' : 'Agents'}
                  </li>
                  <li className="flex items-center gap-1 text-[10px] text-[#A0A0A0]">
                    {!isFree && <Check size={8} className="text-[#C9A84C] shrink-0" />}
                    {plan.msgs.toLocaleString()} msgs/mo
                  </li>
                  {!isFree && (
                    <li className="flex items-center gap-1 text-[10px] text-[#A0A0A0]">
                      <Check size={8} className="text-[#C9A84C] shrink-0" />
                      {lang === 'pt' ? 'Todos Canais' : 'All Channels'}
                    </li>
                  )}
                  {extras.map((e, i) => (
                    <li key={i} className="flex items-center gap-1 text-[10px] text-[#A0A0A0]">
                      <Check size={8} className="text-[#C9A84C] shrink-0" />{e}
                    </li>
                  ))}
                </ul>
                {!isFree && (
                  <div>
                    <p className={`text-base font-bold ${isEnterprise ? 'text-[#C9A84C]' : 'text-white'}`}>
                      ${price}<span className="text-[10px] text-[#999] font-normal">/{lang === 'pt' ? 'mes' : 'mo'}</span>
                    </p>
                    {billingAnnual && plan.price.monthly > plan.price.annual && (
                      <p className="text-[8px] text-[#B0B0B0] line-through">${plan.price.monthly}/{lang === 'pt' ? 'mes' : 'mo'}</p>
                    )}
                  </div>
                )}
                {!isFree && (
                  <button data-testid={`upgrade-${plan.key}`}
                    onClick={() => handleUpgrade(plan.key)}
                    disabled={upgrading === plan.key}
                    className={`mt-2 w-full rounded-lg py-2 text-[10px] font-semibold transition disabled:opacity-50 ${
                      isEnterprise
                        ? 'bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] text-black hover:opacity-90'
                        : 'border border-[#1E1E1E] text-[#888] hover:border-[#C9A84C]/30 hover:text-white'
                    }`}>
                    {upgrading === plan.key ? '...' : (lang === 'pt' ? `Upgrade` : `Upgrade`)}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <button onClick={() => navigate(-1)} className="block mx-auto py-2 text-xs text-[#666666] hover:text-[#A0A0A0]">
          {t('upsell.continue_free')}
        </button>
      </div>
    </div>
  );
}
