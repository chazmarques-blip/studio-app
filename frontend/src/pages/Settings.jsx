import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { User, Globe, CreditCard, Link2, LogOut, ChevronRight, Wifi, X, Save, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { AvatarPicker } from '../components/AvatarPicker';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png';

const channelStatus = [
  { name: 'WhatsApp', connected: false },
  { name: 'Instagram', connected: false },
  { name: 'Facebook', connected: false },
  { name: 'Telegram', connected: false },
];

export default function SettingsPage() {
  const { user, signOut, updateProfile } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [showAccount, setShowAccount] = useState(location.state?.openAccount || false);
  const [accountForm, setAccountForm] = useState({ full_name: user?.full_name || '', company: user?.company || '' });
  const [saving, setSaving] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const lang = i18n.language?.substring(0, 2) || 'en';

  useEffect(() => {
    axios.get(`${API}/avatar/me`).then(r => setAvatarUrl(r.data.avatar_url)).catch(() => {});
  }, []);

  const handleLogout = async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); };

  const handleSaveAccount = async () => {
    setSaving(true);
    try { await updateProfile(accountForm); toast.success(t('profile.saved')); setShowAccount(false); }
    catch { toast.error(t('profile.save_error')); }
    finally { setSaving(false); }
  };

  const menuItems = [
    { icon: User, label: t('settings.account'), desc: t('settings.account_desc'), action: () => setShowAccount(true) },
    { icon: Globe, label: t('settings.language'), desc: t('settings.language_desc'), path: '/onboarding' },
    { icon: CreditCard, label: t('settings.billing'), desc: t('settings.billing_desc'), path: '/pricing' },
    { icon: Calendar, label: 'Google', desc: 'Calendar, Sheets, Drive', path: '/settings/google' },
    { icon: Wifi, label: t('channels.title'), desc: t('settings.integrations_desc'), path: '/settings/channels' },
    { icon: Link2, label: t('settings.integrations'), desc: t('settings.integrations_desc'), action: () => toast.info(t('common.coming_soon') || 'Coming soon') },
  ];

  return (
    <div className="min-h-screen px-4 pt-6">
      <h1 className="mb-6 text-xl font-bold text-white">{t('settings.title')}</h1>

      {/* Profile Card */}
      <div data-testid="profile-card" className="glass-card mb-4 p-4 cursor-pointer transition-all hover:border-[rgba(201,168,76,0.3)]" onClick={() => setShowAccount(true)}>
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/30 shrink-0">
            <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
          </div>
          <div><p className="text-sm font-semibold text-white">{user?.full_name || 'User'}</p><p className="text-xs text-[#666]">{user?.email}</p></div>
          <ChevronRight size={16} className="ml-auto text-[#3A3A3A]" />
        </div>
      </div>

      {showAccount && (
        <div data-testid="account-panel" className="mb-4 rounded-xl border border-[#C9A84C]/30 bg-[#141414] p-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">{t('settings.account')}</h2>
            <button data-testid="account-close-btn" onClick={() => setShowAccount(false)} className="rounded-lg p-1 text-[#999] hover:bg-[#1E1E1E] hover:text-white transition"><X size={16} /></button>
          </div>

          {/* Avatar Picker */}
          <div className="mb-4">
            <AvatarPicker
              currentAvatar={avatarUrl}
              lang={lang}
              compact={true}
              onSave={(url) => { setAvatarUrl(url); toast.success('Avatar saved!'); }}
            />
          </div>

          <div className="space-y-3">
            <div>
              <label className="mb-1 block text-xs text-[#999]">{t('profile.name')}</label>
              <input data-testid="account-name-input" value={accountForm.full_name} onChange={e => setAccountForm(p => ({ ...p, full_name: e.target.value }))}
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2.5 text-sm text-white outline-none transition focus:border-[#C9A84C]/50" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[#999]">{t('profile.company')}</label>
              <input data-testid="account-company-input" value={accountForm.company} onChange={e => setAccountForm(p => ({ ...p, company: e.target.value }))}
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2.5 text-sm text-white outline-none transition focus:border-[#C9A84C]/50" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-[#999]">Email</label>
              <input disabled value={user?.email || ''} className="w-full rounded-lg border border-[#2A2A2A] bg-[#111] px-3 py-2.5 text-sm text-[#999] cursor-not-allowed" />
            </div>
          </div>
          <button data-testid="account-save-btn" onClick={handleSaveAccount} disabled={saving}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-2.5 text-sm font-semibold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-50">
            <Save size={15} /> {saving ? t('common.loading') : t('common.save')}
          </button>
        </div>
      )}

      <div className="mb-4 space-y-1">
        {menuItems.filter(item => !(showAccount && item.label === t('settings.account'))).map((item, i) => (
          <button key={i} data-testid={`settings-${item.label.toLowerCase().replace(/\s/g, '-')}`}
            onClick={() => item.action ? item.action() : item.path && navigate(item.path)}
            className="glass-card flex w-full items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1E1E1E]"><item.icon size={16} className="text-[#A0A0A0]" /></div>
            <div className="flex-1"><p className="text-sm font-medium text-white">{item.label}</p><p className="text-xs text-[#666]">{item.desc}</p></div>
            <ChevronRight size={16} className="text-[#3A3A3A]" />
          </button>
        ))}
      </div>

      <div className="mb-4">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">{t('settings.channels')}</h2>
        <div className="space-y-1">
          {channelStatus.map(ch => (
            <div key={ch.name} data-testid={`channel-${ch.name.toLowerCase()}`} className="glass-card flex items-center gap-3 p-3">
              <div className="h-2.5 w-2.5 rounded-full bg-[#C9A84C]" />
              <span className="flex-1 text-sm text-white">{ch.name}</span>
              <span className={`text-xs ${ch.connected ? 'text-[#4CAF50]' : 'text-[#666]'}`}>{ch.connected ? t('settings.connected') : t('settings.not_connected')}</span>
            </div>
          ))}
        </div>
      </div>

      <button data-testid="logout-btn" onClick={handleLogout} className="flex w-full items-center gap-3 glass-card p-4 text-left transition hover:border-red-500/30">
        <LogOut size={16} className="text-red-400" /><span className="text-sm font-medium text-red-400">{t('settings.sign_out')}</span>
      </button>
    </div>
  );
}
