import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { User, Globe, CreditCard, Link2, LogOut, ChevronRight, Wifi, X, Save, Calendar, Camera, Upload, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/a8605e94e5c6af1d2e335c12fd5b50643e2f4c2aaad4cda320b5e404af96e2f6.png';

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
  const { t } = useTranslation();
  const [showAccount, setShowAccount] = useState(location.state?.openAccount || false);
  const [accountForm, setAccountForm] = useState({
    full_name: user?.full_name || '',
    company: user?.company || '',
  });
  const [saving, setSaving] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoBase64, setPhotoBase64] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [stream, setStream] = useState(null);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    axios.get(`${API}/avatar/me`).then(r => setAvatarUrl(r.data.avatar_url)).catch(() => {});
  }, []);

  const handleLogout = async () => {
    await signOut();
    toast.success(t('settings.sign_out'));
    navigate('/');
  };

  const handleSaveAccount = async () => {
    setSaving(true);
    try {
      await updateProfile(accountForm);
      toast.success(t('profile.saved'));
      setShowAccount(false);
    } catch {
      toast.error(t('profile.save_error'));
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { toast.error('Max 10MB'); return; }
    const reader = new FileReader();
    reader.onload = (ev) => { setPhotoPreview(ev.target.result); setPhotoBase64(ev.target.result); };
    reader.readAsDataURL(file);
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 512, height: 512 } });
      setStream(mediaStream);
      setCameraActive(true);
      if (videoRef.current) videoRef.current.srcObject = mediaStream;
    } catch { toast.error('Camera access denied'); }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    setPhotoPreview(dataUrl);
    setPhotoBase64(dataUrl);
    stopCamera();
  };

  const stopCamera = () => {
    if (stream) { stream.getTracks().forEach(t => t.stop()); setStream(null); }
    setCameraActive(false);
  };

  const generateAvatar = async () => {
    if (!photoBase64) return;
    setGenerating(true);
    try {
      const { data } = await axios.post(`${API}/avatar/generate`, { photo_base64: photoBase64 });
      setAvatarUrl(data.avatar_url);
      setPhotoPreview(null);
      setPhotoBase64(null);
      toast.success('Avatar generated!');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to generate avatar');
    } finally { setGenerating(false); }
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

      {/* Profile Card with Avatar */}
      <div data-testid="profile-card" className="glass-card mb-4 p-4 cursor-pointer transition-all hover:border-[rgba(201,168,76,0.3)]" onClick={() => setShowAccount(true)}>
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/30 shrink-0">
            <img src={avatarUrl || DEFAULT_AVATAR} alt="" className="h-full w-full object-cover object-[center_20%]" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
          </div>
          <div><p className="text-sm font-semibold text-white">{user?.full_name || 'User'}</p><p className="text-xs text-[#666666]">{user?.email}</p></div>
          <ChevronRight size={16} className="ml-auto text-[#3A3A3A]" />
        </div>
      </div>

      {showAccount && (
        <div data-testid="account-panel" className="mb-4 rounded-xl border border-[#C9A84C]/30 bg-[#141414] p-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-white">{t('settings.account')}</h2>
            <button data-testid="account-close-btn" onClick={() => setShowAccount(false)} className="rounded-lg p-1 text-[#999] hover:bg-[#1E1E1E] hover:text-white transition">
              <X size={16} />
            </button>
          </div>

          {/* Avatar Section */}
          <div className="mb-4 flex flex-col items-center">
            <div className="relative mb-3">
              <div className="h-20 w-20 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/30" data-testid="settings-avatar-preview">
                {generating ? (
                  <div className="h-full w-full flex items-center justify-center bg-[#111]">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
                  </div>
                ) : photoPreview ? (
                  <img src={photoPreview} alt="Photo" className="h-full w-full object-cover" />
                ) : (
                  <img src={avatarUrl || DEFAULT_AVATAR} alt="Avatar" className="h-full w-full object-cover object-[center_20%]" onError={(e) => { e.target.src = DEFAULT_AVATAR; }} />
                )}
              </div>
            </div>

            {/* Camera view */}
            {cameraActive && (
              <div className="mb-3 w-full relative rounded-xl overflow-hidden border border-white/[0.06]">
                <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-square object-cover" />
                <div className="absolute bottom-2 left-0 right-0 flex justify-center gap-2">
                  <button onClick={capturePhoto} data-testid="settings-capture-btn"
                    className="h-12 w-12 rounded-full bg-white/90 flex items-center justify-center shadow-lg">
                    <div className="h-10 w-10 rounded-full border-2 border-[#0A0A0A]" />
                  </button>
                  <button onClick={stopCamera} className="h-8 w-8 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 self-end text-xs">X</button>
                </div>
              </div>
            )}
            <canvas ref={canvasRef} className="hidden" />

            {/* Avatar action buttons */}
            {!cameraActive && (
              <div className="flex gap-2 w-full">
                <button onClick={startCamera} data-testid="settings-camera-btn"
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-white/[0.06] bg-white/[0.02] py-2 text-[10px] text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition">
                  <Camera size={13} className="text-[#C9A84C]" /> Selfie
                </button>
                <button onClick={() => fileInputRef.current?.click()} data-testid="settings-upload-btn"
                  className="flex-1 flex items-center justify-center gap-1.5 rounded-lg border border-white/[0.06] bg-white/[0.02] py-2 text-[10px] text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition">
                  <Upload size={13} className="text-[#C9A84C]" /> Upload
                </button>
                <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
              </div>
            )}

            {/* Generate button */}
            {photoPreview && !generating && (
              <button onClick={generateAvatar} data-testid="settings-generate-avatar-btn"
                className="btn-gold mt-2 w-full rounded-lg py-2 text-[11px] font-semibold flex items-center justify-center gap-1.5">
                <Sparkles size={13} /> Generate AI Avatar
              </button>
            )}
            {generating && (
              <div className="mt-2 flex items-center gap-2 text-[#C9A84C] text-[11px]">
                <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
                Creating avatar...
              </div>
            )}
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
            <div className="flex-1"><p className="text-sm font-medium text-white">{item.label}</p><p className="text-xs text-[#666666]">{item.desc}</p></div>
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
              <span className={`text-xs ${ch.connected ? 'text-[#4CAF50]' : 'text-[#666666]'}`}>{ch.connected ? t('settings.connected') : t('settings.not_connected')}</span>
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
