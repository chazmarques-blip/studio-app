import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import { Globe, Check } from 'lucide-react';
import { toast } from 'sonner';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'pt', name: 'Portugues', flag: '🇧🇷' },
  { code: 'es', name: 'Espanol', flag: '🇪🇸' },
  { code: 'fr', name: 'Francais', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
];

export default function Onboarding() {
  const [selectedLang, setSelectedLang] = useState('en');
  const [loading, setLoading] = useState(false);
  const { updateProfile } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();

  const handleContinue = async () => {
    setLoading(true);
    try {
      i18n.changeLanguage(selectedLang);
      localStorage.setItem('agentzz_lang', selectedLang);
      await updateProfile({ ui_language: selectedLang, onboarding_completed: true });
      toast.success(selectedLang === 'pt' ? 'Idioma salvo!' : 'Language saved!');
      navigate('/dashboard');
    } catch {
      toast.error('Failed to save preference');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] px-4">
      <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[100px]" /></div>
      <div className="relative z-10 w-full max-w-lg">
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className="h-2 w-8 rounded-full bg-[#C9A84C]" />
          <div className="h-2 w-8 rounded-full bg-[#2A2A2A]" />
          <div className="h-2 w-8 rounded-full bg-[#2A2A2A]" />
        </div>
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#C9A84C]/10"><Globe size={28} className="text-[#C9A84C]" /></div>
          <h1 data-testid="onboarding-title" className="mb-2 text-2xl font-bold text-white">{t('onboarding.choose_language')}</h1>
          <p className="text-sm text-[#A0A0A0]">{t('onboarding.choose_language_desc')}</p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {languages.map(lang => (
            <button key={lang.code} data-testid={`lang-${lang.code}`} onClick={() => setSelectedLang(lang.code)}
              className={`glass-card group flex flex-col items-center gap-2 p-4 transition-all duration-200 ${selectedLang === lang.code ? 'border-[#C9A84C] bg-[#C9A84C]/10 gold-glow' : 'hover:border-[#3A3A3A]'}`}>
              <span className="text-2xl">{lang.flag}</span>
              <span className={`text-sm font-medium ${selectedLang === lang.code ? 'text-[#C9A84C]' : 'text-[#A0A0A0]'}`}>{lang.name}</span>
              {selectedLang === lang.code && <Check size={16} className="text-[#C9A84C]" />}
            </button>
          ))}
        </div>
        <button data-testid="onboarding-continue-btn" onClick={handleContinue} disabled={loading} className="btn-gold mt-8 w-full rounded-xl py-3 text-sm font-semibold disabled:opacity-50">
          {loading ? t('onboarding.saving') : t('onboarding.continue')}
        </button>
      </div>
    </div>
  );
}
