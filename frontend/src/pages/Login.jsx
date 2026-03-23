import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, ArrowLeft, Check, Zap, Star, Crown } from 'lucide-react';
import { toast } from 'sonner';

const PLAN_ICONS = [null, Zap, Star, Crown];

export default function Login() {
  const [searchParams] = useSearchParams();
  const [isSignUp, setIsSignUp] = useState(searchParams.get('tab') === 'signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [annual, setAnnual] = useState(false);
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isSignUp) {
        await signUp(email, password, fullName);
        navigate('/onboarding');
      } else {
        const { data } = await signIn(email, password);
        navigate(data.user.onboarding_completed ? '/dashboard' : '/onboarding');
      }
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const suffix = annual ? 'annual' : 'monthly';
  const plans = [
    { name: t('landing.plan_free'), price: t('landing.plan_free_price'), period: t('landing.plan_free_period'),
      feats: ['f1','f2','f3','f4'].map(k => t(`landing.plan_free_${k}`)), pro: false, badge: null },
    { name: t('landing.plan_starter'),
      price: annual ? t('landing.plan_starter_price_annual') : t('landing.plan_starter_price_monthly'),
      period: annual ? t('landing.plan_starter_period_annual') : t('landing.plan_starter_period_monthly'),
      feats: ['f1','f2','f3','f4','f5'].map(k => t(`landing.plan_starter_${k}`)), pro: false, badge: t('landing.plan_starter_badge') },
    { name: t('landing.plan_pro'),
      price: t(`landing.plan_pro_price_${suffix}`), period: t(`landing.plan_pro_period_${suffix}`),
      feats: ['f1','f2','f3','f4','f5'].map(k => t(`landing.plan_pro_${k}`)), pro: true, badge: t('landing.plan_pro_badge') },
    { name: t('landing.plan_enterprise'),
      price: t(`landing.plan_enterprise_price_${suffix}`), period: t(`landing.plan_enterprise_period_${suffix}`),
      feats: ['f1','f2','f3','f4','f5','f6'].map(k => t(`landing.plan_enterprise_${k}`)), pro: false, badge: t('landing.plan_enterprise_badge') },
  ];

  return (
    <div className="flex min-h-screen bg-[#0A0A0A]">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute left-1/3 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/[0.03] blur-[120px]" />
      </div>

      {/* Left - Plans */}
      <div className="hidden lg:flex flex-col justify-center flex-1 relative z-10 px-8 xl:px-16">
        <div className="max-w-lg ml-auto mr-8">
          <button data-testid="back-to-landing" onClick={() => navigate('/')} className="mb-5 flex items-center gap-2 text-xs text-[#888] transition hover:text-white">
            <ArrowLeft size={14} /> {t('auth.back')}
          </button>
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-10 mb-5" />
          <h2 className="text-base font-bold text-white mb-0.5">{isSignUp ? t('auth.choose_plan_title', 'Choose your plan') : t('auth.upgrade_title', 'Upgrade anytime')}</h2>
          <p className="text-[11px] text-[#999] mb-4">{t('auth.plan_subtitle', 'Start free, upgrade when you need more power.')}</p>

          {/* Monthly / Annual toggle */}
          <div className="flex items-center gap-2 mb-4" data-testid="billing-toggle">
            <span className={`text-[10px] font-semibold transition ${!annual ? 'text-white' : 'text-[#666]'}`}>{t('landing.billing_monthly')}</span>
            <button onClick={() => setAnnual(!annual)} data-testid="billing-toggle-btn"
              className={`relative w-9 h-5 rounded-full transition-colors ${annual ? 'bg-[#C9A84C]/30' : 'bg-white/10'}`}>
              <div className={`absolute top-0.5 h-4 w-4 rounded-full transition-all ${annual ? 'left-[18px] bg-[#C9A84C]' : 'left-0.5 bg-[#888]'}`} />
            </button>
            <span className={`text-[10px] font-semibold transition ${annual ? 'text-white' : 'text-[#666]'}`}>{t('landing.billing_annual')}</span>
            {annual && <span className="text-[8px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">-20%</span>}
          </div>

          <div className="space-y-2" data-testid="login-plans">
            {plans.map((plan, i) => {
              const Icon = PLAN_ICONS[i];
              return (
                <div key={i} data-testid={`login-plan-${i}`}
                  className={`rounded-xl border p-3 transition-all ${
                    plan.pro
                      ? 'border-[#C9A84C]/20 bg-[#C9A84C]/[0.03]'
                      : 'border-white/[0.05] bg-white/[0.01] hover:border-white/[0.08]'
                  }`}>
                  <div className="flex items-center gap-2 mb-1.5">
                    {Icon && (
                      <div className={`h-6 w-6 rounded-md flex items-center justify-center ${plan.pro ? 'bg-[#C9A84C]/12' : 'bg-white/[0.03]'}`}>
                        <Icon size={11} className={plan.pro ? 'text-[#C9A84C]' : 'text-[#888]'} />
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-bold text-white">{plan.name}</span>
                        {plan.badge && (
                          <span className={`text-[6px] font-mono font-bold uppercase px-1.5 py-0.5 rounded ${
                            plan.pro ? 'bg-[#C9A84C]/12 text-[#C9A84C]' : 'bg-white/[0.04] text-[#777]'
                          }`}>{plan.badge}</span>
                        )}
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className={`text-sm font-bold font-mono ${plan.pro ? 'text-[#C9A84C]' : 'text-white'}`}>{plan.price}</span>
                        {plan.period && <span className="text-[8px] text-[#999]">{plan.period}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                    {plan.feats.slice(0, 4).map((f, fi) => (
                      <span key={fi} className="flex items-center gap-1 text-[8px] text-[#888]">
                        <Check size={7} className={plan.pro ? 'text-[#C9A84C]' : 'text-emerald-400/60'} />{f}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right - Auth Form */}
      <div className="flex flex-col items-center justify-center flex-1 relative z-10 px-4 lg:px-8">
        <div className="w-full max-w-md">
          {/* Mobile only: back + logo */}
          <div className="lg:hidden">
            <button data-testid="back-to-landing-mobile" onClick={() => navigate('/')} className="mb-6 flex items-center gap-2 text-xs text-[#888] transition hover:text-white">
              <ArrowLeft size={14} /> {t('auth.back')}
            </button>
            <img src="/logo-agentzz.png" alt="AgentZZ" className="h-12 mb-6" />
          </div>

          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.015] backdrop-blur-xl p-7" data-testid="auth-form-card">
            <h2 data-testid="auth-title" className="mb-1 text-lg font-bold text-white">{isSignUp ? t('auth.create_title') : t('auth.login_title')}</h2>
            <p className="mb-5 text-[12px] text-[#999]">{isSignUp ? t('auth.create_subtitle') : t('auth.login_subtitle')}</p>
            <form onSubmit={handleSubmit} className="space-y-3.5">
              {isSignUp && (
                <div>
                  <label className="mb-1 block text-[10px] font-semibold text-[#999] uppercase tracking-wider">{t('auth.full_name')}</label>
                  <input data-testid="input-fullname" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder={t('auth.full_name_placeholder')} className="w-full rounded-lg border border-[#222] bg-[#111] px-3.5 py-2 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#C9A84C]/40 focus:ring-1 focus:ring-[#C9A84C]/20" />
                </div>
              )}
              <div>
                <label className="mb-1 block text-[10px] font-semibold text-[#999] uppercase tracking-wider">{t('auth.email')}</label>
                <input data-testid="input-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('auth.email_placeholder')} required className="w-full rounded-lg border border-[#222] bg-[#111] px-3.5 py-2 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#C9A84C]/40 focus:ring-1 focus:ring-[#C9A84C]/20" />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-semibold text-[#999] uppercase tracking-wider">{t('auth.password')}</label>
                <div className="relative">
                  <input data-testid="input-password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t('auth.password_placeholder')} required minLength={6} className="w-full rounded-lg border border-[#222] bg-[#111] px-3.5 py-2 pr-9 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#C9A84C]/40 focus:ring-1 focus:ring-[#C9A84C]/20" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#555] transition hover:text-[#999]">{showPassword ? <EyeOff size={14} /> : <Eye size={14} />}</button>
                </div>
              </div>
              <button data-testid="auth-submit-btn" type="submit" disabled={loading} className="btn-gold w-full rounded-lg py-2 text-[12px] font-semibold disabled:opacity-50">{loading ? t('auth.loading') : isSignUp ? t('auth.create_btn') : t('auth.login_btn')}</button>
            </form>
            <div className="mt-5 text-center">
              <button data-testid="auth-toggle-btn" onClick={() => setIsSignUp(!isSignUp)} className="text-[11px] text-[#888] transition hover:text-[#C9A84C]">{isSignUp ? t('auth.has_account') : t('auth.no_account')}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
