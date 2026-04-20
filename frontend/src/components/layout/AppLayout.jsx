import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import Sidebar from './Sidebar';
import { UserCog, CreditCard, LogOut, Globe, Check, Sun, Moon } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png';

function AppHeader() {
  const { user, signOut } = useAuth();
  const { theme, toggle: toggleTheme } = useTheme();
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

  return (
    <header
      className="fixed top-0 right-0 left-0 md:left-60 z-30 h-12 border-b border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#0A0614] flex items-center justify-end px-4 gap-2"
      data-testid="app-header"
      style={{ fontFamily: "'Outfit', system-ui" }}
    >
      {/* Theme toggle */}
      <button
        onClick={toggleTheme}
        data-testid="header-theme-toggle"
        className="h-8 w-8 rounded-md flex items-center justify-center text-gray-600 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-white/5 transition"
        title={theme === 'dark' ? 'Modo claro' : 'Modo escuro'}
      >
        {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
      </button>

      {/* User Avatar */}
      <div className="relative" ref={profileRef}>
        <button
          data-testid="profile-menu-btn"
          onClick={() => setProfileOpen(!profileOpen)}
          className="h-8 w-8 rounded-full overflow-hidden ring-1 ring-orange-200 dark:ring-violet-500/40 transition hover:ring-2 hover:ring-orange-400 dark:hover:ring-violet-400"
        >
          <img
            src={avatarUrl || DEFAULT_AVATAR}
            alt={user?.full_name || 'User'}
            className="h-full w-full object-cover object-[center_20%]"
            onError={(e) => { e.target.src = DEFAULT_AVATAR; }}
          />
        </button>
        {profileOpen && (
          <div data-testid="profile-dropdown" className="absolute right-0 top-10 z-50 w-56 rounded-xl border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] backdrop-blur-xl p-1.5 shadow-2xl">
            <div className="mb-1.5 border-b border-gray-100 dark:border-[#2A2442] px-3 py-3 flex items-center gap-3">
              <div className="h-11 w-11 rounded-full overflow-hidden ring-1 ring-orange-100 dark:ring-violet-500/40 shrink-0">
                <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover object-[center_20%]" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{user?.full_name || 'User'}</p>
                <p className="text-xs text-gray-500 dark:text-[#A3A3B2] truncate">{user?.email}</p>
                <span className="mt-1 inline-block text-[9px] font-mono uppercase px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 dark:bg-violet-500/20 dark:text-violet-300 font-semibold">
                  {stats?.plan || 'free'}
                </span>
              </div>
            </div>
            <button data-testid="profile-edit-btn" onClick={() => { setProfileOpen(false); navigate('/settings', { state: { openAccount: true } }); }}
              className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-600 dark:text-[#A3A3B2] font-medium transition hover:bg-gray-50 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white">
              <UserCog size={15} /> {t('profile.edit')}
            </button>
            <button data-testid="profile-billing-btn" onClick={() => { setProfileOpen(false); navigate('/pricing'); }}
              className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-600 dark:text-[#A3A3B2] font-medium transition hover:bg-gray-50 dark:hover:bg-white/5 hover:text-gray-900 dark:hover:text-white">
              <CreditCard size={15} /> {t('profile.billing')}
            </button>

            <div className="my-1 border-t border-gray-100 dark:border-[#2A2442]" />
            <div className="px-3 pt-2 pb-1 flex items-center gap-2 text-[10px] uppercase tracking-wider text-gray-400 dark:text-[#6B647F] font-semibold">
              <Globe size={11} /> Idioma
            </div>
            <div className="px-1.5 pb-1.5 grid grid-cols-3 gap-1" data-testid="profile-lang-selector">
              {[
                { code: 'pt', label: 'PT' },
                { code: 'en', label: 'EN' },
                { code: 'es', label: 'ES' },
              ].map(lg => (
                <button
                  key={lg.code}
                  data-testid={`profile-lang-${lg.code}`}
                  onClick={() => i18n.changeLanguage(lg.code)}
                  className={`flex items-center justify-center gap-1 py-1.5 rounded-md text-[11px] font-mono font-semibold transition ${
                    lang === lg.code
                      ? 'bg-violet-500 text-white'
                      : 'text-gray-600 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-white/5'
                  }`}
                >
                  {lang === lg.code && <Check size={10} />}
                  {lg.label}
                </button>
              ))}
            </div>
            <div className="my-1 border-t border-gray-100 dark:border-[#2A2442]" />
            <button data-testid="profile-logout-btn" onClick={async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); }}
              className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-600 dark:text-[#A3A3B2] font-medium transition hover:bg-red-50 dark:hover:bg-red-500/10 hover:text-red-600 dark:hover:text-red-400">
              <LogOut size={15} /> {t('settings.sign_out')}
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export function AppLayout() {
  return (
    <div className="relative min-h-screen bg-white dark:bg-[#0A0614] text-gray-900 dark:text-white transition-colors">
      <Sidebar />
      <AppHeader />
      <main className="relative z-10 md:ml-60 pt-12">
        <Outlet />
      </main>
    </div>
  );
}

