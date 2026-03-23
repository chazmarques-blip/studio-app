import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { BottomNav } from './BottomNav';
import { Zap, UserCog, CreditCard, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/36152c5b792ad0e3a5369214cbd423ca6b327833cf834f94d65f76c7c348c7a7.png';

function TechGridBg() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="app-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(201,168,76,0.025)" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="app-grid-fade" cx="50%" cy="30%" r="55%">
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="app-grid-mask"><rect width="100%" height="100%" fill="url(#app-grid-fade)" /></mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#app-grid)" mask="url(#app-grid-mask)" />
      </svg>
      <div className="absolute left-1/4 top-0 h-[350px] w-[450px] rounded-full bg-[#C9A84C]/[0.02] blur-[140px]" />
      <div className="absolute right-0 top-1/3 h-[250px] w-[300px] rounded-full bg-[#C9A84C]/[0.015] blur-[120px]" />
    </div>
  );
}

function AppHeader() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [profileOpen, setProfileOpen] = useState(false);
  const [stats, setStats] = useState(null);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const profileRef = useRef(null);
  const lang = i18n.language?.substring(0, 2) || 'en';

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => setStats(r.data)).catch(() => {});
    axios.get(`${API}/avatar/me`).then(r => setAvatarUrl(r.data.avatar_url)).catch(() => {});
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (profileRef.current && !profileRef.current.contains(e.target)) setProfileOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const msgsUsed = stats?.messages_used || 0;
  const msgsLimit = stats?.messages_limit || 50;
  const usagePercent = msgsLimit > 0 ? Math.min(100, Math.round((msgsUsed / msgsLimit) * 100)) : 0;
  const creditsLeft = msgsLimit - msgsUsed;

  return (
    <header className="fixed top-0 inset-x-0 z-50 border-b border-white/[0.04] bg-[#060606]/70 backdrop-blur-2xl" data-testid="app-header">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-2.5">
        {/* Logo */}
        <button onClick={() => navigate('/dashboard')} className="shrink-0" data-testid="header-logo">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-7 sm:h-8" />
        </button>

        <div className="flex items-center gap-2">
          {/* Language Selector */}
          <div className="hidden sm:flex items-center border border-white/[0.06] rounded-lg overflow-hidden" data-testid="header-lang-selector">
            {[
              { code: 'en', label: 'EN' },
              { code: 'pt', label: 'PT' },
              { code: 'es', label: 'ES' },
            ].map(lg => (
              <button key={lg.code} data-testid={`header-lang-${lg.code}`}
                onClick={() => i18n.changeLanguage(lg.code)}
                className={`px-2 py-1.5 text-[10px] font-mono font-semibold transition-all ${
                  lang === lg.code
                    ? 'bg-[#C9A84C]/[0.12] text-[#C9A84C]'
                    : 'text-[#B0B0B0] hover:text-[#E5E5E5]'
                }`}>
                {lg.label}
              </button>
            ))}
          </div>

          {/* Credits */}
          <div data-testid="header-credits" onClick={() => navigate('/pricing')}
            className="flex items-center gap-1 rounded-full border border-white/[0.06] bg-white/[0.02] px-2.5 py-1 cursor-pointer hover:border-[#C9A84C]/30 transition">
            <Zap size={11} className={usagePercent > 80 ? 'text-[#FF6B6B]' : 'text-[#C9A84C]'} />
            <span className={`text-[11px] font-bold font-mono ${usagePercent > 80 ? 'text-[#FF6B6B]' : 'text-white'}`}>{creditsLeft}</span>
            <span className="text-[9px] text-[#B0B0B0] font-mono">/{msgsLimit}</span>
          </div>

          {/* User Name + Avatar */}
          <div className="relative flex items-center gap-2" ref={profileRef}>
            <span className="hidden sm:block text-[11px] font-semibold text-[#E5E5E5] truncate max-w-[120px]" data-testid="header-user-name">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </span>
            <button data-testid="profile-menu-btn" onClick={() => setProfileOpen(!profileOpen)}
              className="h-9 w-9 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/30 transition hover:ring-[#C9A84C]/60 hover:shadow-md hover:shadow-[#C9A84C]/20 shrink-0">
              <img
                src={avatarUrl || DEFAULT_AVATAR}
                alt={user?.full_name || 'User'}
                className="h-full w-full object-cover object-[center_20%]"
                onError={(e) => { e.target.src = DEFAULT_AVATAR; }}
              />
            </button>
            {profileOpen && (
              <div data-testid="profile-dropdown" className="absolute right-0 top-10 z-50 w-52 rounded-2xl border border-white/[0.06] bg-[#0E0E0E]/95 backdrop-blur-xl p-1 shadow-2xl shadow-black/60">
                <div className="mb-1 border-b border-white/[0.04] px-3 py-2.5 flex items-center gap-2.5">
                  <div className="h-10 w-10 rounded-full overflow-hidden ring-1 ring-[#C9A84C]/20 shrink-0">
                    <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover object-[center_20%]" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-white truncate">{user?.full_name || 'User'}</p>
                    <p className="text-[10px] text-[#B0B0B0] truncate">{user?.email}</p>
                    <span className="mt-0.5 inline-block text-[7px] font-mono uppercase px-1.5 py-0.5 rounded bg-[#C9A84C]/10 text-[#C9A84C]">
                      {stats?.plan || 'free'}
                    </span>
                  </div>
                </div>
                <button data-testid="profile-edit-btn" onClick={() => { setProfileOpen(false); navigate('/settings', { state: { openAccount: true } }); }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[#888] transition hover:bg-[#1A1A1A] hover:text-white">
                  <UserCog size={13} /> {t('profile.edit')}
                </button>
                <button data-testid="profile-billing-btn" onClick={() => { setProfileOpen(false); navigate('/pricing'); }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[#888] transition hover:bg-[#1A1A1A] hover:text-white">
                  <CreditCard size={13} /> {t('profile.billing')}
                </button>
                <div className="my-0.5 border-t border-white/[0.04]" />
                <button data-testid="profile-logout-btn" onClick={async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-xs text-[#888] transition hover:bg-[#1A1A1A] hover:text-[#FF6B6B]">
                  <LogOut size={13} /> {t('settings.sign_out')}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export function AppLayout() {
  return (
    <div className="relative min-h-screen bg-[#0A0A0A]">
      <TechGridBg />
      <AppHeader />
      <main className="relative z-10 pt-14 pb-20">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
