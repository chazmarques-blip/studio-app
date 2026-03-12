import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Check, Zap, Bot, MessageSquare, Crown, Sparkles } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLANS = [
  { key: 'free', agents: 1, msgs: 200, price: { annual: 0, monthly: 0 } },
  { key: 'starter', agents: 3, msgs: 1500, price: { annual: 49, monthly: 49 } },
  { key: 'pro', agents: 5, msgs: 5000, price: { annual: 299, monthly: 349 } },
  { key: 'enterprise', agents: 10, msgs: 10000, price: { annual: 699, monthly: 749 } },
];

function UsageBar({ label, icon: Icon, used, limit, color = '#C9A84C' }) {
  const pct = limit > 0 ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const isHigh = pct > 80;
  return (
    <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Icon size={14} className="text-[#C9A84C]" />
          <span className="text-xs font-medium text-white">{label}</span>
        </div>
        <span className={`text-xs font-bold ${isHigh ? 'text-red-400' : 'text-white'}`}>{used} / {limit.toLocaleString()}</span>
      </div>
      <div className="h-2 rounded-full bg-[#1A1A1A] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: isHigh ? '#EF4444' : color }} />
      </div>
      <p className="mt-1 text-right text-[10px] text-[#555]">{pct}% used</p>
    </div>
  );
}

export default function Pricing() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [stats, setStats] = useState(null);
  const [billingAnnual, setBillingAnnual] = useState(true);
  const [upgrading, setUpgrading] = useState(null);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => setStats(r.data)).catch(() => {});
  }, []);

  const handleUpgrade = async (planKey) => {
    setUpgrading(planKey);
    try {
      await axios.post(`${API}/billing/upgrade`, { plan: planKey, billing_cycle: billingAnnual ? 'annual' : 'monthly' });
      toast.success(`Upgraded to ${planKey.charAt(0).toUpperCase() + planKey.slice(1)}!`);
      const { data } = await axios.get(`${API}/dashboard/stats`);
      setStats(data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Upgrade failed');
    } finally {
      setUpgrading(null);
    }
  };

  const currentPlan = stats?.plan || 'free';
  const planOrder = ['free', 'starter', 'pro', 'enterprise'];
  const currentIdx = planOrder.indexOf(currentPlan);

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-5 pb-24">
      {/* Header */}
      <div className="mb-5 flex items-center gap-3">
        <button onClick={() => navigate('/settings')} className="text-[#666] hover:text-white transition"><ArrowLeft size={20} /></button>
        <h1 className="text-lg font-bold text-white">Plan & Billing</h1>
      </div>

      {/* Current Plan Card */}
      {stats && (
        <div className="mb-5 rounded-xl border border-[#C9A84C]/20 bg-gradient-to-br from-[#C9A84C]/5 to-transparent p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#C9A84C]/15">
              <Crown size={18} className="text-[#C9A84C]" />
            </div>
            <div>
              <p className="text-xs text-[#C9A84C]/70">Current Plan</p>
              <p className="text-lg font-bold text-white capitalize">{currentPlan}</p>
            </div>
            <div className="ml-auto">
              <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${
                stats.plan_status === 'active' ? 'bg-[#4ADE80]/10 text-[#4ADE80]' : 'bg-red-500/10 text-red-400'
              }`}>{stats.plan_status === 'active' ? 'Active' : 'Inactive'}</span>
            </div>
          </div>
          {stats.period_start && (
            <p className="text-[10px] text-[#555]">Period started: {new Date(stats.period_start).toLocaleDateString()}</p>
          )}
        </div>
      )}

      {/* Usage Bars */}
      {stats && (
        <div className="mb-6 space-y-3">
          <UsageBar label="AI Messages" icon={MessageSquare} used={stats.messages_used || 0} limit={stats.messages_limit || 50} />
          <UsageBar label="Agents" icon={Bot} used={stats.agents_count || 0} limit={stats.agents_limit || 1} color="#60A5FA" />
        </div>
      )}

      {/* Billing Toggle */}
      <div className="mb-5 flex justify-center">
        <div className="inline-flex items-center gap-1 rounded-full border border-[#1E1E1E] bg-[#0D0D0D] p-1">
          <button data-testid="billing-annual-btn" onClick={() => setBillingAnnual(true)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#666]'}`}>
            Annual <span className="ml-1 text-[9px] opacity-80">Save 14%</span>
          </button>
          <button data-testid="billing-monthly-btn" onClick={() => setBillingAnnual(false)}
            className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${!billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#666]'}`}>
            Monthly
          </button>
        </div>
      </div>

      {/* Plan Cards */}
      <div className="space-y-3">
        {PLANS.map((plan, i) => {
          const isCurrent = plan.key === currentPlan;
          const isUpgrade = planOrder.indexOf(plan.key) > currentIdx;
          const isDowngrade = planOrder.indexOf(plan.key) < currentIdx;
          const price = billingAnnual ? plan.price.annual : plan.price.monthly;
          const features = [];
          for (let fi = 1; fi <= 8; fi++) {
            const key = `landing.plan_${plan.key}_f${fi}`;
            const val = t(key);
            if (val !== key) features.push(val);
          }

          return (
            <div key={plan.key} data-testid={`plan-card-${plan.key}`}
              className={`rounded-xl border p-4 transition ${
                isCurrent ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5' : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#222]'
              }`}>
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl flex-shrink-0" style={{ backgroundColor: isCurrent ? 'rgba(201,168,76,0.15)' : '#141414' }}>
                  {plan.key === 'free' ? <Zap size={16} className="text-[#888]" /> :
                   plan.key === 'starter' ? <Sparkles size={16} className="text-[#C9A84C]" /> :
                   plan.key === 'pro' ? <Crown size={16} className="text-[#C9A84C]" /> :
                   <Crown size={16} className="text-[#C9A84C]" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-white capitalize">{plan.key}</h3>
                    {isCurrent && <span className="rounded-full bg-[#C9A84C]/15 px-2 py-0.5 text-[9px] font-semibold text-[#C9A84C]">Current</span>}
                  </div>
                  <p className="text-[11px] text-[#555] mt-0.5">{plan.agents} agents · {plan.msgs.toLocaleString()} msgs/month</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-lg font-bold text-white">${price}</p>
                  <p className="text-[10px] text-[#555]">{price === 0 ? 'forever' : billingAnnual ? '/mo (annual)' : '/mo'}</p>
                </div>
              </div>

              {/* Features */}
              <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
                {features.map((f, fi) => (
                  <span key={fi} className="flex items-center gap-1 text-[11px] text-[#666]">
                    <Check size={10} className="text-[#C9A84C]" />{f}
                  </span>
                ))}
              </div>

              {/* Action Button */}
              <div className="mt-3">
                {isCurrent ? (
                  <div className="text-center py-2 text-xs text-[#C9A84C] font-medium">Your current plan</div>
                ) : isUpgrade ? (
                  <button data-testid={`upgrade-${plan.key}`} onClick={() => handleUpgrade(plan.key)} disabled={upgrading === plan.key}
                    className="btn-gold w-full rounded-lg py-2.5 text-sm font-semibold disabled:opacity-50">
                    {upgrading === plan.key ? 'Processing...' : `Upgrade to ${plan.key.charAt(0).toUpperCase() + plan.key.slice(1)}`}
                  </button>
                ) : (
                  <button data-testid={`downgrade-${plan.key}`} onClick={() => handleUpgrade(plan.key)} disabled={upgrading === plan.key}
                    className="w-full rounded-lg border border-[#1E1E1E] py-2.5 text-sm text-[#666] hover:border-[#C9A84C]/30 hover:text-white transition disabled:opacity-50">
                    {upgrading === plan.key ? 'Processing...' : `Downgrade to ${plan.key.charAt(0).toUpperCase() + plan.key.slice(1)}`}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Note */}
      <p className="mt-4 text-center text-[10px] text-[#444]">
        Only AI agent responses count as messages. Customer &amp; operator messages are free.
      </p>
    </div>
  );
}
