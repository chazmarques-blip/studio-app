import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Globe, Check, Sparkles, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { AvatarPicker } from '../components/AvatarPicker';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
  const { updateProfile } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const handleLangContinue = () => {
    i18n.changeLanguage(selectedLang);
    localStorage.setItem('agentzz_lang', selectedLang);
    setStep(2);
  };

  const finishOnboarding = async () => {
    setLoading(true);
    try {
      await updateProfile({ ui_language: selectedLang, onboarding_completed: true });
      toast.success(selectedLang === 'pt' ? 'Bem-vindo ao AgentZZ!' : 'Welcome to AgentZZ!');
      navigate('/dashboard');
    } catch { toast.error('Failed'); }
    finally { setLoading(false); }
  };

  const handleAvatarSaved = () => { finishOnboarding(); };

  const handleSkipAvatar = async () => {
    await axios.post(`${API}/avatar/set-default`).catch(() => {});
    finishOnboarding();
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
        <div className="mb-6 flex items-center justify-center gap-2">
          <div className={`h-2 w-8 rounded-full transition-all ${step >= 1 ? 'bg-[#C9A84C]' : 'bg-[#2A2A2A]'}`} />
          <div className={`h-2 w-8 rounded-full transition-all ${step >= 2 ? 'bg-[#C9A84C]' : 'bg-[#2A2A2A]'}`} />
        </div>

        {step === 1 && (
          <div>
            <div className="mb-6 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
                <Globe size={24} className="text-[#C9A84C]" />
              </div>
              <h1 data-testid="onboarding-title" className="mb-1 text-xl font-bold text-white">{t('onboarding.choose_language')}</h1>
              <p className="text-xs text-[#A0A0A0]">{t('onboarding.choose_language_desc')}</p>
            </div>
            <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-3">
              {languages.map(lang => (
                <button key={lang.code} data-testid={`lang-${lang.code}`} onClick={() => setSelectedLang(lang.code)}
                  className={`glass-card flex flex-col items-center gap-1.5 p-3 transition-all ${selectedLang === lang.code ? 'border-[#C9A84C] bg-[#C9A84C]/10' : 'hover:border-[#3A3A3A]'}`}>
                  <span className="text-xl">{lang.flag}</span>
                  <span className={`text-xs font-medium ${selectedLang === lang.code ? 'text-[#C9A84C]' : 'text-[#A0A0A0]'}`}>{lang.name}</span>
                  {selectedLang === lang.code && <Check size={14} className="text-[#C9A84C]" />}
                </button>
              ))}
            </div>
            <button data-testid="onboarding-continue-btn" onClick={handleLangContinue}
              className="btn-gold mt-6 w-full rounded-xl py-3 text-sm font-semibold flex items-center justify-center gap-2">
              {t('onboarding.continue')} <ArrowRight size={16} />
            </button>
          </div>
        )}

        {step === 2 && (
          <div>
            <div className="mb-5 text-center">
              <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-[#C9A84C]/10">
                <Sparkles size={24} className="text-[#C9A84C]" />
              </div>
              <h1 data-testid="onboarding-avatar-title" className="mb-1 text-xl font-bold text-white">
                {selectedLang === 'pt' ? 'Crie seu Avatar' : selectedLang === 'es' ? 'Crea tu Avatar' : 'Create your Avatar'}
              </h1>
              <p className="text-xs text-[#A0A0A0]">
                {selectedLang === 'pt' ? 'Envie uma selfie e nossa IA criara seu avatar cyborg' : selectedLang === 'es' ? 'Sube una selfie y nuestra IA creara tu avatar cyborg' : 'Upload a selfie and our AI will create your cyborg avatar'}
              </p>
            </div>
            <AvatarPicker
              lang={selectedLang}
              onSave={handleAvatarSaved}
              onSkip={handleSkipAvatar}
            />
          </div>
        )}
      </div>
    </div>
  );
}
