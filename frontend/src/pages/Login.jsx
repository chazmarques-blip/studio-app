import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

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

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A] px-4">
      <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[100px]" /></div>
      <div className="relative z-10 w-full max-w-md">
        <button data-testid="back-to-landing" onClick={() => navigate('/')} className="mb-8 flex items-center gap-2 text-sm text-[#A0A0A0] transition hover:text-white"><ArrowLeft size={16} /> {t('auth.back')}</button>
        <div className="mb-8 flex items-center gap-3">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-14" />
        </div>
        <div className="glass-card p-8">
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
  );
}
