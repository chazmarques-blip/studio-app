import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { BottomNav } from './BottomNav';
import { Zap, UserCog, CreditCard, LogOut } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png';

function TechGridBg() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      {/* Hero Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-orange-50 via-blue-50 to-green-50 opacity-40" />
      
      {/* Subtle Grid Pattern */}
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" className="opacity-30">
        <defs>
          <pattern id="app-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(249,115,22,0.05)" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="app-grid-fade" cx="50%" cy="30%" r="55%">
            <stop offset="0%" stopColor="black" stopOpacity="0.1" />
            <stop offset="100%" stopColor="black" stopOpacity="0" />
          </radialGradient>
          <mask id="app-grid-mask"><rect width="100%" height="100%" fill="url(#app-grid-fade)" /></mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#app-grid)" mask="url(#app-grid-mask)" />
      </svg>
      
      {/* Soft Color Blobs */}
      <div className="absolute left-1/4 top-0 h-[400px] w-[500px] rounded-full bg-orange-200/20 blur-[140px]" />
      <div className="absolute right-0 top-1/3 h-[300px] w-[350px] rounded-full bg-blue-200/15 blur-[120px]" />
      <div className="absolute left-1/2 bottom-0 h-[250px] w-[300px] rounded-full bg-green-200/15 blur-[100px]" />
    </div>
  );
}

function AppHeader() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [profileOpen, setProfileOpen] = useState(false);
  const [stats, setStats] = useState(null);
  const [avatarUrl, setAvatarUrl] = useState(() => localStorage.getItem('studiox_avatar') || null);
  const profileRef = useRef(null);
  const lang = i18n.language?.substring(0, 2) || 'en';

  const fetchAvatar = () => {
    axios.get(`${API}/avatar/me`).then(r => {
      const url = r.data.avatar_url;
      setAvatarUrl(url);
      if (url) localStorage.setItem('studiox_avatar', url);
    }).catch(() => {});
  };

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => setStats(r.data)).catch(() => {});
    fetchAvatar();
    const handleAvatarChange = () => fetchAvatar();
    window.addEventListener('avatar-changed', handleAvatarChange);
    return () => window.removeEventListener('avatar-changed', handleAvatarChange);
  }, []);

  useEffect(() => {
    fetchAvatar();
  }, [location.pathname]);

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
    <header className="fixed top-0 inset-x-0 z-50 border-b border-gray-200/60 bg-white/80 backdrop-blur-2xl shadow-sm" data-testid="app-header">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <button onClick={() => navigate('/dashboard')} className="shrink-0" data-testid="header-logo">
          <img src="/logo-studiox.svg" alt="StudioX" className="h-7 sm:h-8" />
        </button>

        <div className="flex items-center gap-2">
          {/* Language Selector */}
          <div className="hidden sm:flex items-center border border-gray-300 rounded-lg overflow-hidden" data-testid="header-lang-selector">
            {[
              { code: 'en', label: 'EN' },
              { code: 'pt', label: 'PT' },
              { code: 'es', label: 'ES' },
            ].map(lg => (
              <button key={lg.code} data-testid={`header-lang-${lg.code}`}
                onClick={() => i18n.changeLanguage(lg.code)}
                className={`px-2.5 py-1.5 text-[11px] font-mono font-semibold transition-all ${
                  lang === lg.code
                    ? 'bg-orange-500 text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}>
                {lg.label}
              </button>
            ))}
          </div>

          {/* Credits */}
          <div data-testid="header-credits" onClick={() => navigate('/pricing')}
            className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-white px-3 py-1.5 cursor-pointer hover:border-orange-300 hover:shadow-md transition-all">
            <Zap size={13} className={usagePercent > 80 ? 'text-red-500' : 'text-orange-500'} />
            <span className={`text-sm font-bold font-mono ${usagePercent > 80 ? 'text-red-600' : 'text-gray-900'}`}>{creditsLeft}</span>
            <span className="text-xs text-gray-500 font-mono">/{msgsLimit}</span>
          </div>

          {/* User Name + Avatar */}
          <div className="relative flex items-center gap-2.5" ref={profileRef}>
            <span className="hidden sm:block text-sm font-semibold text-gray-900 truncate max-w-[120px]" data-testid="header-user-name">
              {user?.full_name || user?.email?.split('@')[0] || 'User'}
            </span>
            <button data-testid="profile-menu-btn" onClick={() => setProfileOpen(!profileOpen)}
              className="h-10 w-10 rounded-full overflow-hidden ring-2 ring-orange-200 transition hover:ring-orange-400 hover:shadow-lg hover:shadow-orange-200/40 shrink-0">
              <img
                src={avatarUrl || DEFAULT_AVATAR}
                alt={user?.full_name || 'User'}
                className="h-full w-full object-cover object-[center_20%]"
                onError={(e) => { e.target.src = DEFAULT_AVATAR; }}
              />
            </button>
            {profileOpen && (
              <div data-testid="profile-dropdown" className="absolute right-0 top-12 z-50 w-56 rounded-2xl border border-gray-200 bg-white backdrop-blur-xl p-1.5 shadow-2xl">
                <div className="mb-1.5 border-b border-gray-100 px-3 py-3 flex items-center gap-3">
                  <div className="h-11 w-11 rounded-full overflow-hidden ring-2 ring-orange-100 shrink-0">
                    <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover object-[center_20%]" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-gray-900 truncate">{user?.full_name || 'User'}</p>
                    <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                    <span className="mt-1 inline-block text-[9px] font-mono uppercase px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 font-semibold">
                      {stats?.plan || 'free'}
                    </span>
                  </div>
                </div>
                <button data-testid="profile-edit-btn" onClick={() => { setProfileOpen(false); navigate('/settings', { state: { openAccount: true } }); }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-600 font-medium transition hover:bg-gray-50 hover:text-gray-900">
                  <UserCog size={15} /> {t('profile.edit')}
                </button>
                <button data-testid="profile-billing-btn" onClick={() => { setProfileOpen(false); navigate('/pricing'); }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-600 font-medium transition hover:bg-gray-50 hover:text-gray-900">
                  <CreditCard size={15} /> {t('profile.billing')}
                </button>
                <div className="my-1 border-t border-gray-100" />
                <button data-testid="profile-logout-btn" onClick={async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); }}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-600 font-medium transition hover:bg-red-50 hover:text-red-600">
                  <LogOut size={15} /> {t('settings.sign_out')}
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
    <div className="relative min-h-screen bg-white">
      <TechGridBg />
      <AppHeader />
      <main className="relative z-10 pt-16 pb-20">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
