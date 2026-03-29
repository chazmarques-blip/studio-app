import { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, ArrowLeft, Check, Zap, Star, Crown, ChevronDown } from 'lucide-react';
import { toast } from 'sonner';
import { DateScrollPicker } from '../components/DateScrollPicker';
import { getErrorMsg } from '../utils/getErrorMsg';

const PLAN_ICONS = [null, Zap, Star, Crown];

const COUNTRIES = [
  { code: 'US', dial: '+1', flag: '\u{1F1FA}\u{1F1F8}', mask: '(###) ###-####', placeholder: '(727) 459-2334' },
  { code: 'BR', dial: '+55', flag: '\u{1F1E7}\u{1F1F7}', mask: '(##) #####-####', placeholder: '(11) 99999-9999' },
  { code: 'PT', dial: '+351', flag: '\u{1F1F5}\u{1F1F9}', mask: '### ### ###', placeholder: '912 345 678' },
  { code: 'GB', dial: '+44', flag: '\u{1F1EC}\u{1F1E7}', mask: '#### ######', placeholder: '7911 123456' },
  { code: 'ES', dial: '+34', flag: '\u{1F1EA}\u{1F1F8}', mask: '### ### ###', placeholder: '612 345 678' },
  { code: 'FR', dial: '+33', flag: '\u{1F1EB}\u{1F1F7}', mask: '# ## ## ## ##', placeholder: '6 12 34 56 78' },
  { code: 'DE', dial: '+49', flag: '\u{1F1E9}\u{1F1EA}', mask: '### #######', placeholder: '151 1234567' },
  { code: 'IT', dial: '+39', flag: '\u{1F1EE}\u{1F1F9}', mask: '### ### ####', placeholder: '312 345 6789' },
  { code: 'MX', dial: '+52', flag: '\u{1F1F2}\u{1F1FD}', mask: '## #### ####', placeholder: '55 1234 5678' },
  { code: 'AR', dial: '+54', flag: '\u{1F1E6}\u{1F1F7}', mask: '## ####-####', placeholder: '11 2345-6789' },
  { code: 'CO', dial: '+57', flag: '\u{1F1E8}\u{1F1F4}', mask: '### ### ####', placeholder: '301 234 5678' },
  { code: 'CL', dial: '+56', flag: '\u{1F1E8}\u{1F1F1}', mask: '# #### ####', placeholder: '9 1234 5678' },
];

function applyMask(value, mask) {
  const digits = value.replace(/\D/g, '');
  let result = '';
  let di = 0;
  for (let i = 0; i < mask.length && di < digits.length; i++) {
    if (mask[i] === '#') {
      result += digits[di++];
    } else {
      result += mask[i];
    }
  }
  return result;
}

function capitalizeWord(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function capitalizeName(str) {
  return str.split(' ').map(w => w ? capitalizeWord(w) : '').join(' ');
}

export default function Login() {
  const [searchParams] = useSearchParams();
  const [isSignUp, setIsSignUp] = useState(searchParams.get('tab') === 'signup');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [birthDateISO, setBirthDateISO] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [selectedCountry, setSelectedCountry] = useState(COUNTRIES[0]);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [preferredContact, setPreferredContact] = useState('whatsapp');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [annual, setAnnual] = useState(false);
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const handlePhoneChange = useCallback((e) => {
    const masked = applyMask(e.target.value, selectedCountry.mask);
    setPhoneNumber(masked);
  }, [selectedCountry]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isSignUp) {
        const fullPhone = phoneNumber ? `${selectedCountry.dial} ${phoneNumber}` : '';
        const fullName = `${firstName} ${lastName}`.trim();
        await signUp(email, password, fullName, { birth_date: birthDateISO, phone: fullPhone, preferred_contact: preferredContact });
        navigate('/onboarding');
      } else {
        const { data } = await signIn(email, password);
        navigate(data.user.onboarding_completed ? '/dashboard' : '/onboarding');
      }
    } catch (err) {
      toast.error(getErrorMsg(err, 'Authentication failed'));
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
        <div className="absolute left-1/3 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#8B5CF6]/[0.03] blur-[120px]" />
      </div>

      {/* Left - Plans */}
      <div className="hidden lg:flex flex-col justify-center flex-1 relative z-10 px-8 xl:px-16">
        <div className="max-w-lg ml-auto mr-8">
          <button data-testid="back-to-landing" onClick={() => navigate('/')} className="mb-5 flex items-center gap-2 text-xs text-[#888] transition hover:text-white">
            <ArrowLeft size={14} /> {t('auth.back')}
          </button>
          <img src="/logo-studiox.png" alt="StudioX" className="h-10 mb-5" />
          <h2 className="text-base font-bold text-white mb-0.5">{isSignUp ? t('auth.choose_plan_title', 'Choose your plan') : t('auth.upgrade_title', 'Upgrade anytime')}</h2>
          <p className="text-[11px] text-[#999] mb-4">{t('auth.plan_subtitle', 'Start free, upgrade when you need more power.')}</p>

          {/* Monthly / Annual toggle */}
          <div className="flex items-center gap-2 mb-4" data-testid="billing-toggle">
            <span className={`text-[10px] font-semibold transition ${!annual ? 'text-white' : 'text-[#666]'}`}>{t('landing.billing_monthly')}</span>
            <button onClick={() => setAnnual(!annual)} data-testid="billing-toggle-btn"
              className={`relative w-9 h-5 rounded-full transition-colors ${annual ? 'bg-[#8B5CF6]/30' : 'bg-white/10'}`}>
              <div className={`absolute top-0.5 h-4 w-4 rounded-full transition-all ${annual ? 'left-[18px] bg-[#8B5CF6]' : 'left-0.5 bg-[#888]'}`} />
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
                      ? 'border-[#8B5CF6]/20 bg-[#8B5CF6]/[0.03]'
                      : 'border-white/[0.05] bg-white/[0.01] hover:border-white/[0.08]'
                  }`}>
                  <div className="flex items-center gap-2 mb-1.5">
                    {Icon && (
                      <div className={`h-6 w-6 rounded-md flex items-center justify-center ${plan.pro ? 'bg-[#8B5CF6]/12' : 'bg-white/[0.03]'}`}>
                        <Icon size={11} className={plan.pro ? 'text-[#8B5CF6]' : 'text-[#888]'} />
                      </div>
                    )}
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[12px] font-bold text-white">{plan.name}</span>
                        {plan.badge && (
                          <span className={`text-[6px] font-mono font-bold uppercase px-1.5 py-0.5 rounded ${
                            plan.pro ? 'bg-[#8B5CF6]/12 text-[#8B5CF6]' : 'bg-white/[0.04] text-[#777]'
                          }`}>{plan.badge}</span>
                        )}
                      </div>
                      <div className="flex items-baseline gap-1">
                        <span className={`text-sm font-bold font-mono ${plan.pro ? 'text-[#8B5CF6]' : 'text-white'}`}>{plan.price}</span>
                        {plan.period && <span className="text-[8px] text-[#999]">{plan.period}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex flex-wrap gap-x-3 gap-y-0.5">
                    {plan.feats.slice(0, 4).map((f, fi) => (
                      <span key={fi} className="flex items-center gap-1 text-[8px] text-[#888]">
                        <Check size={7} className={plan.pro ? 'text-[#8B5CF6]' : 'text-emerald-400/60'} />{f}
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
            <img src="/logo-studiox.png" alt="StudioX" className="h-12 mb-6" />
          </div>

          <div className="rounded-2xl border border-white/[0.06] bg-white/[0.015] backdrop-blur-xl p-5" data-testid="auth-form-card">
            <h2 data-testid="auth-title" className="mb-0.5 text-lg font-bold text-white">{isSignUp ? 'Create your account' : t('auth.login_title')}</h2>
            <p className="mb-4 text-[11px] text-[#999]">{isSignUp ? 'Start automating your conversations today' : t('auth.login_subtitle')}</p>
            <form onSubmit={handleSubmit} className="space-y-2.5">
              {isSignUp && (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">First Name</label>
                      <input data-testid="input-firstname" type="text" value={firstName} onChange={(e) => setFirstName(capitalizeName(e.target.value))} placeholder="John"
                        className="w-full rounded-lg border border-[#222] bg-[#111] px-3 py-1.5 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#8B5CF6]/40 focus:ring-1 focus:ring-[#8B5CF6]/20" />
                    </div>
                    <div>
                      <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">Last Name</label>
                      <input data-testid="input-lastname" type="text" value={lastName} onChange={(e) => setLastName(capitalizeName(e.target.value))} placeholder="Smith"
                        className="w-full rounded-lg border border-[#222] bg-[#111] px-3 py-1.5 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#8B5CF6]/40 focus:ring-1 focus:ring-[#8B5CF6]/20" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">Birth Date</label>
                      <DateScrollPicker value={birthDateISO} onChange={setBirthDateISO} />
                    </div>
                    <div>
                      <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">Preferred Contact</label>
                      <div className="flex gap-1.5">
                        <button type="button" data-testid="contact-whatsapp" onClick={() => setPreferredContact('whatsapp')}
                          className={`flex-1 flex items-center justify-center gap-1 rounded-lg border py-1.5 text-[10px] font-medium transition ${preferredContact === 'whatsapp' ? 'border-[#25D366]/50 bg-[#25D366]/10 text-[#25D366]' : 'border-[#222] bg-[#111] text-[#555] hover:border-[#333]'}`}>
                          <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
                          WhatsApp
                        </button>
                        <button type="button" data-testid="contact-sms" onClick={() => setPreferredContact('sms')}
                          className={`flex-1 flex items-center justify-center gap-1 rounded-lg border py-1.5 text-[10px] font-medium transition ${preferredContact === 'sms' ? 'border-[#8B5CF6]/50 bg-[#8B5CF6]/10 text-[#8B5CF6]' : 'border-[#222] bg-[#111] text-[#555] hover:border-[#333]'}`}>
                          SMS
                        </button>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">Phone</label>
                    <div className="flex gap-1.5">
                      <div className="relative">
                        <button type="button" data-testid="country-picker-btn" onClick={() => setShowCountryPicker(!showCountryPicker)}
                          className="flex items-center gap-1 rounded-lg border border-[#222] bg-[#111] px-2 py-1.5 text-[11px] text-white transition hover:border-[#333] whitespace-nowrap">
                          <span>{selectedCountry.flag}</span>
                          <span className="text-[#999] font-mono">{selectedCountry.dial}</span>
                          <ChevronDown size={10} className="text-[#555]" />
                        </button>
                        {showCountryPicker && (
                          <div className="absolute top-full left-0 mt-1 z-50 max-h-48 w-48 overflow-y-auto rounded-lg border border-[#222] bg-[#111] shadow-xl" data-testid="country-dropdown">
                            {COUNTRIES.map(c => (
                              <button type="button" key={c.code} data-testid={`country-${c.code}`}
                                onClick={() => { setSelectedCountry(c); setShowCountryPicker(false); setPhoneNumber(''); }}
                                className={`flex w-full items-center gap-2 px-3 py-1.5 text-[11px] transition hover:bg-white/5 ${selectedCountry.code === c.code ? 'bg-[#8B5CF6]/10 text-[#8B5CF6]' : 'text-white'}`}>
                                <span>{c.flag}</span>
                                <span className="font-mono text-[#999]">{c.dial}</span>
                                <span className="text-[#666]">{c.code}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <input data-testid="input-phone" type="tel" value={phoneNumber} onChange={handlePhoneChange} placeholder={selectedCountry.placeholder}
                        className="flex-1 rounded-lg border border-[#222] bg-[#111] px-3 py-1.5 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#8B5CF6]/40 focus:ring-1 focus:ring-[#8B5CF6]/20" />
                    </div>
                  </div>
                </>
              )}
              <div>
                <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">Email</label>
                <input data-testid="input-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" required
                  className="w-full rounded-lg border border-[#222] bg-[#111] px-3 py-1.5 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#8B5CF6]/40 focus:ring-1 focus:ring-[#8B5CF6]/20" />
              </div>
              <div>
                <label className="mb-0.5 block text-[9px] font-semibold text-[#777] uppercase tracking-wider">Password</label>
                <div className="relative">
                  <input data-testid="input-password" type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min. 6 characters" required minLength={6}
                    className="w-full rounded-lg border border-[#222] bg-[#111] px-3 py-1.5 pr-9 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#8B5CF6]/40 focus:ring-1 focus:ring-[#8B5CF6]/20" />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#555] transition hover:text-[#999]">{showPassword ? <EyeOff size={13} /> : <Eye size={13} />}</button>
                </div>
              </div>
              <button data-testid="auth-submit-btn" type="submit" disabled={loading} className="btn-gold w-full rounded-lg py-2 text-[11px] font-semibold disabled:opacity-50">{loading ? 'Loading...' : isSignUp ? 'Create Account' : 'Sign In'}</button>
              {isSignUp && (
                <p data-testid="no-credit-card-msg" className="text-center text-[10px] text-[#666]">No credit card required</p>
              )}
            </form>
            <div className="mt-4 text-center">
              <button data-testid="auth-toggle-btn" onClick={() => setIsSignUp(!isSignUp)} className="text-[11px] text-[#888] transition hover:text-[#8B5CF6]">{isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Start Free"}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
