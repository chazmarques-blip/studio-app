import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Bot, Eye, EyeOff, ArrowLeft } from 'lucide-react';
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isSignUp) {
        await signUp(email, password, fullName);
        toast.success('Account created!');
        navigate('/onboarding');
      } else {
        const { data } = await signIn(email, password);
        toast.success('Welcome back!');
        navigate(data.user.onboarding_completed ? '/dashboard' : '/onboarding');
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Authentication failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A] px-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[100px]" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        <button
          data-testid="back-to-landing"
          onClick={() => navigate('/')}
          className="mb-8 flex items-center gap-2 text-sm text-[#A0A0A0] transition hover:text-white"
        >
          <ArrowLeft size={16} /> Back
        </button>

        <div className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#C9A84C] to-[#A88B3D]">
            <Bot size={22} className="text-[#0A0A0A]" />
          </div>
          <span className="text-xl font-bold text-white">AgentFlow</span>
        </div>

        <div className="glass-card p-8">
          <h2 data-testid="auth-title" className="mb-2 text-xl font-bold text-white">
            {isSignUp ? 'Create your account' : 'Welcome back'}
          </h2>
          <p className="mb-6 text-sm text-[#A0A0A0]">
            {isSignUp ? 'Start automating your conversations today' : 'Sign in to your AgentFlow dashboard'}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isSignUp && (
              <div>
                <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">Full Name</label>
                <input
                  data-testid="input-fullname"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Your full name"
                  className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none transition focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]/30"
                />
              </div>
            )}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">Email</label>
              <input
                data-testid="input-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none transition focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]/30"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">Password</label>
              <div className="relative">
                <input
                  data-testid="input-password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Min. 6 characters"
                  required
                  minLength={6}
                  className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 pr-10 text-sm text-white placeholder-[#666666] outline-none transition focus:border-[#C9A84C] focus:ring-1 focus:ring-[#C9A84C]/30"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#666666] transition hover:text-[#A0A0A0]"
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              data-testid="auth-submit-btn"
              type="submit"
              disabled={loading}
              className="btn-gold w-full rounded-lg py-2.5 text-sm disabled:opacity-50"
            >
              {loading ? 'Loading...' : isSignUp ? 'Create Account' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              data-testid="auth-toggle-btn"
              onClick={() => setIsSignUp(!isSignUp)}
              className="text-sm text-[#A0A0A0] transition hover:text-[#C9A84C]"
            >
              {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Start Free"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
