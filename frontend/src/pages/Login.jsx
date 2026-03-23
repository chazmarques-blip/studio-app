import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, ArrowLeft, Check, Zap, Star, Crown, Phone, Calendar as CalendarIcon, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

const PLAN_ICONS = [null, Zap, Star, Crown];

export default function Login() {
  const [searchParams] = useSearchParams();
  const [isSignUp, setIsSignUp] = useState(searchParams.get('tab') === 'signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [phone, setPhone] = useState('');
  const [preferredContact, setPreferredContact] = useState('whatsapp');
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
        await signUp(email, password, fullName, { birth_date: birthDate, phone, preferred_contact: preferredContact });
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
              {isSignUp && (
                <>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="mb-1 flex items-center gap-1 text-[10px] font-semibold text-[#999] uppercase tracking-wider">
                        <CalendarIcon size={10} /> {t('auth.birth_date', 'Data de Nascimento')}
                      </label>
                      <input data-testid="input-birthdate" type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)}
                        className="w-full rounded-lg border border-[#222] bg-[#111] px-3.5 py-2 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#C9A84C]/40 focus:ring-1 focus:ring-[#C9A84C]/20 [color-scheme:dark]" />
                    </div>
                    <div>
                      <label className="mb-1 flex items-center gap-1 text-[10px] font-semibold text-[#999] uppercase tracking-wider">
                        <Phone size={10} /> {t('auth.phone', 'Telefone')}
                      </label>
                      <input data-testid="input-phone" type="tel" value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+55 11 99999-9999"
                        className="w-full rounded-lg border border-[#222] bg-[#111] px-3.5 py-2 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#C9A84C]/40 focus:ring-1 focus:ring-[#C9A84C]/20" />
                    </div>
                  </div>
                  <div>
                    <label className="mb-1 flex items-center gap-1 text-[10px] font-semibold text-[#999] uppercase tracking-wider">
                      <MessageSquare size={10} /> {t('auth.preferred_contact', 'Contato Preferido')}
                    </label>
                    <div className="flex gap-2">
                      <button type="button" data-testid="contact-whatsapp" onClick={() => setPreferredContact('whatsapp')}
                        className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-[11px] font-medium transition ${preferredContact === 'whatsapp' ? 'border-[#25D366]/50 bg-[#25D366]/10 text-[#25D366]' : 'border-[#222] bg-[#111] text-[#666] hover:border-[#333]'}`}>
                        <svg viewBox="0 0 24 24" fill="currentColor" className="h-3.5 w-3.5"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                        WhatsApp
                      </button>
                      <button type="button" data-testid="contact-sms" onClick={() => setPreferredContact('sms')}
                        className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-[11px] font-medium transition ${preferredContact === 'sms' ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#222] bg-[#111] text-[#666] hover:border-[#333]'}`}>
                        <MessageSquare size={13} />
                        SMS
                      </button>
                    </div>
                  </div>
                </>
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
