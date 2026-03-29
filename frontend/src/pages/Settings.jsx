import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { User, Globe, CreditCard, Link2, LogOut, ChevronRight, Wifi, X, Save, Calendar, Camera, ChevronDown, Check } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { AvatarPicker } from '../components/AvatarPicker';
import { DateScrollPicker } from '../components/DateScrollPicker';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png';

const COUNTRIES = [
  { code: 'US', dial: '+1', flag: '\u{1F1FA}\u{1F1F8}', mask: '(###) ###-####', placeholder: '(727) 459-2334' },
  { code: 'BR', dial: '+55', flag: '\u{1F1E7}\u{1F1F7}', mask: '(##) #####-####', placeholder: '(11) 99999-9999' },
  { code: 'PT', dial: '+351', flag: '\u{1F1F5}\u{1F1F9}', mask: '### ### ###', placeholder: '912 345 678' },
  { code: 'GB', dial: '+44', flag: '\u{1F1EC}\u{1F1E7}', mask: '#### ######', placeholder: '7911 123456' },
  { code: 'ES', dial: '+34', flag: '\u{1F1EA}\u{1F1F8}', mask: '### ### ###', placeholder: '612 345 678' },
  { code: 'FR', dial: '+33', flag: '\u{1F1EB}\u{1F1F7}', mask: '# ## ## ## ##', placeholder: '6 12 34 56 78' },
  { code: 'DE', dial: '+49', flag: '\u{1F1E9}\u{1F1EA}', mask: '### #######', placeholder: '151 1234567' },
  { code: 'MX', dial: '+52', flag: '\u{1F1F2}\u{1F1FD}', mask: '## #### ####', placeholder: '55 1234 5678' },
  { code: 'AR', dial: '+54', flag: '\u{1F1E6}\u{1F1F7}', mask: '## ####-####', placeholder: '11 2345-6789' },
  { code: 'CO', dial: '+57', flag: '\u{1F1E8}\u{1F1F4}', mask: '### ### ####', placeholder: '301 234 5678' },
];

function applyMask(value, mask) {
  const digits = value.replace(/\D/g, '');
  let result = '', di = 0;
  for (let i = 0; i < mask.length && di < digits.length; i++) {
    result += mask[i] === '#' ? digits[di++] : mask[i];
  }
  return result;
}

function parsePhoneCountry(fullPhone) {
  if (!fullPhone) return { country: COUNTRIES[0], number: '' };
  for (const c of COUNTRIES) {
    if (fullPhone.startsWith(c.dial)) {
      const rest = fullPhone.slice(c.dial.length).trim();
      return { country: c, number: applyMask(rest, c.mask) };
    }
  }
  return { country: COUNTRIES[0], number: fullPhone };
}

function capitalizeName(str) {
  return str.split(' ').map(w => w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : '').join(' ');
}

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
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [company, setCompany] = useState('');
  const [preferredContact, setPreferredContact] = useState('whatsapp');
  const [birthDateISO, setBirthDateISO] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [phoneCountry, setPhoneCountry] = useState(COUNTRIES[0]);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [saving, setSaving] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(() => localStorage.getItem('studiox_avatar') || null);
  const [showAvatarPicker, setShowAvatarPicker] = useState(false);
  const lang = i18n.language?.substring(0, 2) || 'en';

  useEffect(() => {
    axios.get(`${API}/avatar/me`).then(r => {
      const url = r.data.avatar_url;
      setAvatarUrl(url);
      if (url) localStorage.setItem('studiox_avatar', url);
    }).catch(() => {});
    axios.get(`${API}/auth/me`).then(r => {
      const nameParts = (r.data.full_name || '').split(' ');
      setFirstName(nameParts[0] || '');
      setLastName(nameParts.slice(1).join(' ') || '');
      setCompany(r.data.company_name || '');
      setBirthDateISO(r.data.birth_date || '');
      const parsed = parsePhoneCountry(r.data.phone || '');
      setPhoneCountry(parsed.country);
      setPhoneNumber(parsed.number);
      setPreferredContact(r.data.preferred_contact || 'whatsapp');
    }).catch(() => {});
  }, []);

  const handlePhoneChange = useCallback((e) => {
    setPhoneNumber(applyMask(e.target.value, phoneCountry.mask));
  }, [phoneCountry]);

  const handleLogout = async () => { await signOut(); toast.success(t('settings.sign_out')); navigate('/'); };

  const handleSaveAccount = async () => {
    setSaving(true);
    try {
      const fullPhone = phoneNumber ? `${phoneCountry.dial} ${phoneNumber}` : '';
      const fullName = `${firstName} ${lastName}`.trim();
      await updateProfile({
        full_name: fullName,
        company_name: company,
        birth_date: birthDateISO,
        phone: fullPhone,
        preferred_contact: preferredContact,
      });
      toast.success(t('profile.saved'));
      setShowAccount(false);
    }
    catch { toast.error(t('profile.save_error')); }
    finally { setSaving(false); }
  };

  const [showLangPicker, setShowLangPicker] = useState(false);

  const LANGUAGES = [
    { code: 'en', name: 'English', flag: '\u{1F1FA}\u{1F1F8}' },
    { code: 'pt', name: 'Portugu\u00eas', flag: '\u{1F1E7}\u{1F1F7}' },
    { code: 'es', name: 'Espa\u00f1ol', flag: '\u{1F1EA}\u{1F1F8}' },
    { code: 'fr', name: 'Fran\u00e7ais', flag: '\u{1F1EB}\u{1F1F7}' },
    { code: 'de', name: 'Deutsch', flag: '\u{1F1E9}\u{1F1EA}' },
    { code: 'it', name: 'Italiano', flag: '\u{1F1EE}\u{1F1F9}' },
  ];

  const handleChangeLang = (code) => {
    i18n.changeLanguage(code);
    localStorage.setItem('studiox_lang', code);
    setShowLangPicker(false);
    toast.success(code === 'pt' ? 'Idioma alterado!' : code === 'es' ? 'Idioma cambiado!' : 'Language changed!');
  };

  const menuItems = [
    { icon: User, label: t('settings.account'), desc: t('settings.account_desc'), action: () => setShowAccount(true) },
    { icon: Globe, label: t('settings.language'), desc: t('settings.language_desc'), action: () => setShowLangPicker(!showLangPicker) },
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
          <div className="relative group shrink-0">
            <div className="h-12 w-12 rounded-full overflow-hidden ring-2 ring-[#8B5CF6]/30">
              <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
            </div>
            <button data-testid="change-photo-btn"
              onClick={(e) => { e.stopPropagation(); setShowAccount(true); setShowAvatarPicker(true); }}
              className="absolute inset-0 rounded-full flex items-center justify-center bg-black/0 group-hover:bg-black/50 transition-all">
              <div className="flex flex-col items-center opacity-0 group-hover:opacity-100 transition-all">
                <Camera size={12} className="text-white" />
                <span className="text-[7px] text-white font-medium mt-0.5">
                  {lang === 'pt' ? 'Trocar' : lang === 'es' ? 'Cambiar' : 'Change'}
                </span>
              </div>
            </button>
          </div>
          <div><p className="text-sm font-semibold text-white">{user?.full_name || 'User'}</p><p className="text-xs text-[#666]">{user?.email}</p></div>
          <ChevronRight size={16} className="ml-auto text-[#3A3A3A]" />
        </div>
      </div>

      {showAccount && (
        <div data-testid="account-panel" className="mb-4 rounded-xl border border-[#8B5CF6]/30 bg-[#141414] p-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">{t('settings.account')}</h2>
            <button data-testid="account-close-btn" onClick={() => { setShowAccount(false); setShowAvatarPicker(false); }} className="rounded-lg p-1 text-[#999] hover:bg-[#1E1E1E] hover:text-white transition"><X size={16} /></button>
          </div>

          {/* Avatar Picker */}
          <div className="mb-4">
            {showAvatarPicker ? (
              <AvatarPicker
                currentAvatar={avatarUrl}
                lang={lang}
                compact={true}
                showGallery={true}
                onSave={(url) => { setAvatarUrl(url); if (url) localStorage.setItem('studiox_avatar', url); setShowAvatarPicker(false); toast.success('Avatar saved!'); }}
              />
            ) : (
              <div className="flex flex-col items-center">
                <div className="relative group cursor-pointer" onClick={() => setShowAvatarPicker(true)}>
                  <div className="h-20 w-20 rounded-full overflow-hidden ring-2 ring-[#8B5CF6]/30">
                    <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
                  </div>
                  <div className="absolute inset-0 rounded-full flex items-center justify-center bg-black/0 group-hover:bg-black/50 transition-all">
                    <div className="flex flex-col items-center opacity-0 group-hover:opacity-100 transition-all">
                      <Camera size={16} className="text-white" />
                      <span className="text-[8px] text-white font-medium mt-0.5">
                        {lang === 'pt' ? 'Trocar Foto' : lang === 'es' ? 'Cambiar Foto' : 'Change Photo'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs text-[#999]">{lang === 'pt' ? 'Nome' : lang === 'es' ? 'Nombre' : 'First Name'}</label>
                <input data-testid="account-firstname-input" value={firstName} onChange={e => setFirstName(capitalizeName(e.target.value))}
                  placeholder="John" className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2 text-sm text-white outline-none transition focus:border-[#8B5CF6]/50" />
              </div>
              <div>
                <label className="mb-1 block text-xs text-[#999]">{lang === 'pt' ? 'Sobrenome' : lang === 'es' ? 'Apellido' : 'Last Name'}</label>
                <input data-testid="account-lastname-input" value={lastName} onChange={e => setLastName(capitalizeName(e.target.value))}
                  placeholder="Smith" className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2 text-sm text-white outline-none transition focus:border-[#8B5CF6]/50" />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-[#999]">{t('profile.company')}</label>
              <input data-testid="account-company-input" value={company} onChange={e => setCompany(e.target.value)}
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2 text-sm text-white outline-none transition focus:border-[#8B5CF6]/50" />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="mb-1 block text-xs text-[#999]">
                  {lang === 'pt' ? 'Nascimento' : lang === 'es' ? 'Nacimiento' : 'Birth Date'}
                </label>
                <DateScrollPicker value={birthDateISO} onChange={setBirthDateISO} compact />
              </div>
              <div>
                <label className="mb-1 block text-xs text-[#999]">
                  {lang === 'pt' ? 'Contato Preferido' : lang === 'es' ? 'Contacto' : 'Preferred Contact'}
                </label>
                <div className="flex gap-1.5">
                  <button type="button" data-testid="settings-contact-whatsapp" onClick={() => setPreferredContact('whatsapp')}
                    className={`flex-1 flex items-center justify-center gap-1 rounded-lg border py-2 text-[10px] font-medium transition ${preferredContact === 'whatsapp' ? 'border-[#25D366]/50 bg-[#25D366]/10 text-[#25D366]' : 'border-[#2A2A2A] bg-[#1A1A1A] text-[#666] hover:border-[#333]'}`}>
                    WhatsApp
                  </button>
                  <button type="button" data-testid="settings-contact-sms" onClick={() => setPreferredContact('sms')}
                    className={`flex-1 flex items-center justify-center gap-1 rounded-lg border py-2 text-[10px] font-medium transition ${preferredContact === 'sms' ? 'border-[#8B5CF6]/50 bg-[#8B5CF6]/10 text-[#8B5CF6]' : 'border-[#2A2A2A] bg-[#1A1A1A] text-[#666] hover:border-[#333]'}`}>
                    SMS
                  </button>
                </div>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-[#999]">
                {lang === 'pt' ? 'Telefone' : lang === 'es' ? 'Teléfono' : 'Phone'}
              </label>
              <div className="flex gap-1.5">
                <div className="relative">
                  <button type="button" data-testid="settings-country-picker-btn" onClick={() => setShowCountryPicker(!showCountryPicker)}
                    className="flex items-center gap-1 rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-2 py-2 text-[11px] text-white transition hover:border-[#333] whitespace-nowrap">
                    <span>{phoneCountry.flag}</span>
                    <span className="text-[#999] font-mono text-[10px]">{phoneCountry.dial}</span>
                    <ChevronDown size={10} className="text-[#555]" />
                  </button>
                  {showCountryPicker && (
                    <div className="absolute top-full left-0 mt-1 z-50 max-h-40 w-44 overflow-y-auto rounded-lg border border-[#2A2A2A] bg-[#141414] shadow-xl">
                      {COUNTRIES.map(c => (
                        <button type="button" key={c.code}
                          onClick={() => { setPhoneCountry(c); setShowCountryPicker(false); setPhoneNumber(''); }}
                          className={`flex w-full items-center gap-2 px-3 py-1.5 text-[11px] transition hover:bg-white/5 ${phoneCountry.code === c.code ? 'bg-[#8B5CF6]/10 text-[#8B5CF6]' : 'text-white'}`}>
                          <span>{c.flag}</span>
                          <span className="font-mono text-[#999]">{c.dial}</span>
                          <span className="text-[#666]">{c.code}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <input data-testid="account-phone-input" type="tel" value={phoneNumber} onChange={handlePhoneChange} placeholder={phoneCountry.placeholder}
                  className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2 text-sm text-white outline-none transition focus:border-[#8B5CF6]/50" />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-[#999]">Email</label>
              <input disabled value={user?.email || ''} className="w-full rounded-lg border border-[#2A2A2A] bg-[#111] px-3 py-2 text-sm text-[#999] cursor-not-allowed" />
            </div>
          </div>
          <button data-testid="account-save-btn" onClick={handleSaveAccount} disabled={saving}
            className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#A88B3D] py-2.5 text-sm font-semibold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-50">
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

      {/* Inline Language Picker */}
      {showLangPicker && (
        <div data-testid="language-picker-panel" className="mb-4 rounded-xl border border-[#8B5CF6]/30 bg-[#141414] p-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
              <Globe size={14} className="text-[#8B5CF6]" />
              {t('settings.language')}
            </h2>
            <button data-testid="lang-picker-close" onClick={() => setShowLangPicker(false)} className="rounded-lg p-1 text-[#999] hover:bg-[#1E1E1E] hover:text-white transition"><X size={16} /></button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {LANGUAGES.map(l => (
              <button key={l.code} data-testid={`lang-option-${l.code}`}
                onClick={() => handleChangeLang(l.code)}
                className={`flex items-center gap-2.5 rounded-lg border p-3 transition-all ${
                  lang === l.code ? 'border-[#8B5CF6]/50 bg-[#8B5CF6]/10' : 'border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#444]'
                }`}>
                <span className="text-lg">{l.flag}</span>
                <span className={`text-xs font-medium ${lang === l.code ? 'text-[#8B5CF6]' : 'text-white'}`}>{l.name}</span>
                {lang === l.code && <Check size={12} className="text-[#8B5CF6] ml-auto" />}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="mb-4">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">{t('settings.channels')}</h2>
        <div className="space-y-1">
          {channelStatus.map(ch => (
            <div key={ch.name} data-testid={`channel-${ch.name.toLowerCase()}`} className="glass-card flex items-center gap-3 p-3">
              <div className="h-2.5 w-2.5 rounded-full bg-[#8B5CF6]" />
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
