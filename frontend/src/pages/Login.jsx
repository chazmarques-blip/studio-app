import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, ArrowLeft, Check, Star, Zap, Crown } from 'lucide-react';
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

  const plans = [
    { name: t('landing.plan_free'), price: t('landing.plan_free_price'), period: t('landing.plan_free_period'),
      feats: ['f1','f2','f3','f4'].map(k => t(`landing.plan_free_${k}`)), pro: false, badge: null },
    { name: t('landing.plan_starter'), price: t('landing.plan_starter_price'), period: t('landing.plan_starter_period'),
      feats: ['f1','f2','f3','f4','f5'].map(k => t(`landing.plan_starter_${k}`)), pro: false, badge: t('landing.plan_starter_badge') },
    { name: t('landing.plan_pro'), price: t('landing.plan_pro_price_monthly'), period: t('landing.plan_pro_period_monthly'),
      feats: ['f1','f2','f3','f4','f5'].map(k => t(`landing.plan_pro_${k}`)), pro: true, badge: t('landing.plan_pro_badge') },
    { name: t('landing.plan_enterprise'), price: t('landing.plan_enterprise_price_monthly'), period: t('landing.plan_enterprise_period_monthly'),
      feats: ['f1','f2','f3','f4','f5','f6'].map(k => t(`landing.plan_enterprise_${k}`)), pro: false, badge: t('landing.plan_enterprise_badge') },
  ];

  return (
    <div className="flex min-h-screen bg-[#0A0A0A]">
      {/* Background glow */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute left-1/2 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[100px]" />
      </div>

      {/* Left — Pricing Plans */}
      <div className="hidden lg:flex flex-col justify-center flex-1 relative z-10 px-8 xl:px-16">
        <div className="max-w-lg ml-auto mr-8">
          <button data-testid="back-to-landing" onClick={() => navigate('/')} className="mb-6 flex items-center gap-2 text-sm text-[#A0A0A0] transition hover:text-white">
            <ArrowLeft size={16} /> {t('auth.back')}
          </button>
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-20 mb-6" />
          <h2 className="text-lg font-bold text-white mb-1">{isSignUp ? t('auth.choose_plan_title', 'Choose your plan') : t('auth.upgrade_title', 'Upgrade anytime')}</h2>
          <p className="text-[13px] text-[#999] mb-5">{t('auth.plan_subtitle', 'Start free, upgrade when you need more power.')}</p>

          <div className="space-y-2.5" data-testid="login-plans">
            {plans.map((plan, i) => {
              const Icon = PLAN_ICONS[i];
              return (
                <div key={i} data-testid={`login-plan-${i}`}
                  className={`rounded-xl border p-3.5 transition-all ${
                    plan.pro
                      ? 'border-[#C9A84C]/25 bg-[#C9A84C]/[0.04]'
                      : 'border-white/[0.06] bg-white/[0.01] hover:border-white/[0.1]'
                  }`}>
                  <div className="flex items-center gap-2.5 mb-2">
                    {Icon && (
                      <div className={`h-7 w-7 rounded-lg flex items-center justify-center ${plan.pro ? 'bg-[#C9A84C]/15' : 'bg-white/[0.03]'}`}>
                        <Icon size={13} className={plan.pro ? 'text-[#C9A84C]' : 'text-[#999]'} />
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[13px] font-bold text-white">{plan.name}</span>
                        {plan.badge && (
                          <span className={`text-[7px] font-mono font-bold uppercase px-1.5 py-0.5 rounded ${
                            plan.pro ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'bg-white/[0.05] text-[#888]'
                          }`}>{plan.badge}</span>
                        )}
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className={`text-sm font-bold font-mono ${plan.pro ? 'text-[#C9A84C]' : 'text-white'}`}>{plan.price}</span>
                        {plan.period && <span className="text-[9px] text-[#B0B0B0]">/{plan.period}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                    {plan.feats.slice(0, 4).map((f, fi) => (
                      <span key={fi} className="flex items-center gap-1 text-[9px] text-[#777]">
                        <Check size={8} className={plan.pro ? 'text-[#C9A84C]' : 'text-emerald-400/60'} />{f}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right — Auth Form */}
      <div className="flex flex-col items-center justify-center flex-1 relative z-10 px-4 lg:px-8">
        <div className="w-full max-w-md">
          {/* Mobile-only back + logo */}
          <div className="lg:hidden">
            <button data-testid="back-to-landing-mobile" onClick={() => navigate('/')} className="mb-8 flex items-center gap-2 text-sm text-[#A0A0A0] transition hover:text-white">
              <ArrowLeft size={16} /> {t('auth.back')}
            </button>
            <div className="mb-8">
              <img src="/logo-agentzz.png" alt="AgentZZ" className="h-24" />
            </div>
          </div>

          <div className="glass-card p-8" data-testid="auth-form-card">
            <h2 data-testid="auth-title" className="mb-2 text-xl font-bold text-white">{isSignUp ? t('auth.create_title') : t('auth.login_title')}</h2>
            <p className="mb-6 text-sm text-[#A0A0A0]">{isSignUp ? t('auth.create_subtitle') : t('auth.login_subtitle')}</p>
            <form onSubmit={handleSubmit} className="space-y-4">
              {isSignUp && (
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('auth.full_name')}</label>
                  <input data-testid="input-fullname" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder={t('auth.full_name_placeholder')} className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none transition focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]/30" />
                </div>
              )}
              <div>
                <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('auth.email')}</label>
                <input data-testid="input-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder={t('auth.email_placeholder')} required className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none transition focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]/30" />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('auth.password')}</label>
                <div className="relative">
                  <input data-testid="input-password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder={t('auth.password_placeholder')} required minLength={6} className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 pr-10 text-sm text-white placeholder-[#666666] outline-none transition focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]/30" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#666666] transition hover:text-[#A0A0A0]">{showPassword ? <EyeOff size={16} /> : <Eye size={16} />}</button>
                </div>
              </div>
              <button data-testid="auth-submit-btn" type="submit" disabled={loading} className="btn-gold w-full rounded-lg py-2.5 text-sm disabled:opacity-50">{loading ? t('auth.loading') : isSignUp ? t('auth.create_btn') : t('auth.login_btn')}</button>
            </form>
            <div className="mt-6 text-center">
              <button data-testid="auth-toggle-btn" onClick={() => setIsSignUp(!isSignUp)} className="text-sm text-[#A0A0A0] transition hover:text-[#C9A84C]">{isSignUp ? t('auth.has_account') : t('auth.no_account')}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
