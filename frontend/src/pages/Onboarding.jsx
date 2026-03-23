import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Globe, Check, Camera, Upload, Sparkles, ArrowRight, SkipForward } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'pt', name: 'Portugues', flag: '🇧🇷' },
  { code: 'es', name: 'Espanol', flag: '🇪🇸' },
  { code: 'fr', name: 'Francais', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
];

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [selectedLang, setSelectedLang] = useState('en');
  const [loading, setLoading] = useState(false);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoBase64, setPhotoBase64] = useState(null);
  const [generatedAvatar, setGeneratedAvatar] = useState(null);
  const [generating, setGenerating] = useState(false);
  const { updateProfile } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [stream, setStream] = useState(null);

  const handleLangContinue = () => {
    i18n.changeLanguage(selectedLang);
    localStorage.setItem('agentzz_lang', selectedLang);
    setStep(2);
  };

  const handleFileUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Max 10MB');
      return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      setPhotoPreview(ev.target.result);
      setPhotoBase64(ev.target.result);
      setGeneratedAvatar(null);
    };
    reader.readAsDataURL(file);
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: 512, height: 512 }
      });
      setStream(mediaStream);
      setCameraActive(true);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch {
      toast.error('Camera access denied');
    }
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
    setGeneratedAvatar(null);
    stopCamera();
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      setStream(null);
    }
    setCameraActive(false);
  };

  const generateAvatar = async () => {
    if (!photoBase64) return;
    setGenerating(true);
    try {
      const { data } = await axios.post(`${API}/avatar/generate`, {
        photo_base64: photoBase64
      });
      setGeneratedAvatar(data.avatar_url);
      toast.success(selectedLang === 'pt' ? 'Avatar gerado!' : 'Avatar generated!');
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to generate avatar');
    } finally {
      setGenerating(false);
    }
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      if (!generatedAvatar) {
        await axios.post(`${API}/avatar/set-default`);
      }
      await updateProfile({ ui_language: selectedLang, onboarding_completed: true });
      toast.success(selectedLang === 'pt' ? 'Bem-vindo ao AgentZZ!' : 'Welcome to AgentZZ!');
      navigate('/dashboard');
    } catch {
      toast.error('Failed to save');
    } finally {
      setLoading(false);
    }
  };

  const handleSkipAvatar = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/avatar/set-default`);
      await updateProfile({ ui_language: selectedLang, onboarding_completed: true });
      toast.success(selectedLang === 'pt' ? 'Bem-vindo ao AgentZZ!' : 'Welcome to AgentZZ!');
      navigate('/dashboard');
    } catch {
      toast.error('Failed to save');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] px-4">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="ob-grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(201,168,76,0.025)" strokeWidth="0.5" />
            </pattern>
            <radialGradient id="ob-fade" cx="50%" cy="30%" r="55%">
              <stop offset="0%" stopColor="white" stopOpacity="1" />
              <stop offset="100%" stopColor="white" stopOpacity="0" />
            </radialGradient>
            <mask id="ob-mask"><rect width="100%" height="100%" fill="url(#ob-fade)" /></mask>
          </defs>
          <rect width="100%" height="100%" fill="url(#ob-grid)" mask="url(#ob-mask)" />
        </svg>
        <div className="absolute left-1/2 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[100px]" />
      </div>

      <div className="relative z-10 w-full max-w-lg">
        {/* Progress dots */}
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className={`h-2 w-8 rounded-full transition-all ${step >= 1 ? 'bg-[#C9A84C]' : 'bg-[#2A2A2A]'}`} />
          <div className={`h-2 w-8 rounded-full transition-all ${step >= 2 ? 'bg-[#C9A84C]' : 'bg-[#2A2A2A]'}`} />
        </div>

        {/* Step 1: Language */}
        {step === 1 && (
          <div>
            <div className="mb-8 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
                <Globe size={28} className="text-[#C9A84C]" />
              </div>
              <h1 data-testid="onboarding-title" className="mb-2 text-2xl font-bold text-white">{t('onboarding.choose_language')}</h1>
              <p className="text-sm text-[#A0A0A0]">{t('onboarding.choose_language_desc')}</p>
            </div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {languages.map(lang => (
                <button key={lang.code} data-testid={`lang-${lang.code}`} onClick={() => setSelectedLang(lang.code)}
                  className={`glass-card group flex flex-col items-center gap-2 p-4 transition-all duration-200 ${selectedLang === lang.code ? 'border-[#C9A84C] bg-[#C9A84C]/10' : 'hover:border-[#3A3A3A]'}`}>
                  <span className="text-2xl">{lang.flag}</span>
                  <span className={`text-sm font-medium ${selectedLang === lang.code ? 'text-[#C9A84C]' : 'text-[#A0A0A0]'}`}>{lang.name}</span>
                  {selectedLang === lang.code && <Check size={16} className="text-[#C9A84C]" />}
                </button>
              ))}
            </div>
            <button data-testid="onboarding-continue-btn" onClick={handleLangContinue}
              className="btn-gold mt-8 w-full rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2">
              {t('onboarding.continue')} <ArrowRight size={16} />
            </button>
          </div>
        )}

        {/* Step 2: Avatar */}
        {step === 2 && (
          <div>
            <div className="mb-6 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
                <Sparkles size={28} className="text-[#C9A84C]" />
              </div>
              <h1 data-testid="onboarding-avatar-title" className="mb-2 text-2xl font-bold text-white">
                {selectedLang === 'pt' ? 'Crie seu Avatar' : selectedLang === 'es' ? 'Crea tu Avatar' : 'Create your Avatar'}
              </h1>
              <p className="text-sm text-[#A0A0A0]">
                {selectedLang === 'pt' ? 'Envie uma selfie e nossa IA criara seu avatar futurista' : selectedLang === 'es' ? 'Sube una selfie y nuestra IA creara tu avatar futurista' : 'Upload a selfie and our AI will create your futuristic avatar'}
              </p>
            </div>

            {/* Avatar preview area */}
            <div className="flex justify-center mb-5">
              <div className="relative">
                <div className="h-32 w-32 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/30 bg-[#111]" data-testid="avatar-preview">
                  {generating ? (
                    <div className="h-full w-full flex items-center justify-center bg-[#111]">
                      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
                    </div>
                  ) : generatedAvatar ? (
                    <img src={generatedAvatar} alt="Avatar" className="h-full w-full object-cover" />
                  ) : photoPreview ? (
                    <img src={photoPreview} alt="Photo" className="h-full w-full object-cover" />
                  ) : (
                    <img src={DEFAULT_AVATAR} alt="Default" className="h-full w-full object-cover object-[center_20%]" />
                  )}
                </div>
                {generatedAvatar && (
                  <div className="absolute -bottom-1 -right-1 h-6 w-6 rounded-full bg-emerald-500 flex items-center justify-center ring-2 ring-[#0A0A0A]">
                    <Check size={12} className="text-white" />
                  </div>
                )}
              </div>
            </div>

            {/* Camera view */}
            {cameraActive && (
              <div className="mb-4 relative rounded-2xl overflow-hidden border border-white/[0.06]">
                <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-square object-cover" />
                <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-3">
                  <button onClick={capturePhoto} data-testid="capture-btn"
                    className="h-14 w-14 rounded-full bg-white/90 flex items-center justify-center shadow-lg transition hover:scale-105 active:scale-95">
                    <div className="h-12 w-12 rounded-full border-2 border-[#0A0A0A]" />
                  </button>
                  <button onClick={stopCamera} className="h-10 w-10 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 self-end">
                    X
                  </button>
                </div>
              </div>
            )}
            <canvas ref={canvasRef} className="hidden" />

            {/* Upload/Camera buttons */}
            {!cameraActive && (
              <div className="flex gap-3 mb-4">
                <button onClick={startCamera} data-testid="camera-btn"
                  className="flex-1 glass-card flex items-center justify-center gap-2 py-3 text-sm text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition">
                  <Camera size={18} className="text-[#C9A84C]" />
                  {selectedLang === 'pt' ? 'Selfie' : 'Camera'}
                </button>
                <button onClick={() => fileInputRef.current?.click()} data-testid="upload-btn"
                  className="flex-1 glass-card flex items-center justify-center gap-2 py-3 text-sm text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition">
                  <Upload size={18} className="text-[#C9A84C]" />
                  Upload
                </button>
                <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFileUpload} />
              </div>
            )}

            {/* Generate button */}
            {photoPreview && !generatedAvatar && !generating && (
              <button onClick={generateAvatar} data-testid="generate-avatar-btn"
                className="btn-gold w-full rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2 mb-3">
                <Sparkles size={16} />
                {selectedLang === 'pt' ? 'Gerar meu Avatar IA' : selectedLang === 'es' ? 'Generar mi Avatar IA' : 'Generate my AI Avatar'}
              </button>
            )}

            {/* Generating state */}
            {generating && (
              <div className="glass-card p-4 mb-3 text-center">
                <div className="flex items-center justify-center gap-2 text-[#C9A84C]">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
                  <span className="text-sm">
                    {selectedLang === 'pt' ? 'Criando seu avatar...' : selectedLang === 'es' ? 'Creando tu avatar...' : 'Creating your avatar...'}
                  </span>
                </div>
              </div>
            )}

            {/* Finish / Retry / Skip */}
            <div className="flex gap-3">
              {generatedAvatar ? (
                <>
                  <button onClick={() => { setGeneratedAvatar(null); setPhotoPreview(null); setPhotoBase64(null); }}
                    className="flex-1 glass-card py-3 text-sm text-[#B0B0B0] hover:text-white transition">
                    {selectedLang === 'pt' ? 'Tentar outra' : 'Try another'}
                  </button>
                  <button onClick={handleFinish} disabled={loading} data-testid="finish-onboarding-btn"
                    className="flex-1 btn-gold rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-50">
                    {loading ? '...' : selectedLang === 'pt' ? 'Continuar' : 'Continue'}
                    <ArrowRight size={16} />
                  </button>
                </>
              ) : (
                <button onClick={handleSkipAvatar} disabled={loading} data-testid="skip-avatar-btn"
                  className="w-full flex items-center justify-center gap-2 py-2.5 text-[11px] text-[#888] hover:text-[#C9A84C] transition">
                  <SkipForward size={14} />
                  {selectedLang === 'pt' ? 'Pular por agora' : selectedLang === 'es' ? 'Saltar por ahora' : 'Skip for now'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
