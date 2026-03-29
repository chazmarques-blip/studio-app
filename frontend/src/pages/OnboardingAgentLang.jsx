import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Globe, Languages, Check, Sparkles } from 'lucide-react';

const langs = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'pt', name: 'Portugues', flag: '🇧🇷' },
  { code: 'es', name: 'Espanol', flag: '🇪🇸' },
  { code: 'fr', name: 'Francais', flag: '🇫🇷' },
];

export default function OnboardingAgentLang() {
  const [mode, setMode] = useState('auto_detect');
  const [fixedLang, setFixedLang] = useState('en');
  const [fallbackLang, setFallbackLang] = useState('en');
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] px-4">
      <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/3 h-[300px] w-[400px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#8B5CF6]/5 blur-[100px]" /></div>
      <div className="relative z-10 w-full max-w-lg">
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className="h-2 w-8 rounded-full bg-[#8B5CF6]" />
          <div className="h-2 w-8 rounded-full bg-[#8B5CF6]" />
          <div className="h-2 w-8 rounded-full bg-[#2A2A2A]" />
        </div>
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#8B5CF6]/10"><Languages size={28} className="text-[#8B5CF6]" /></div>
          <h1 data-testid="agent-lang-title" className="mb-2 text-2xl font-bold text-white">{t('onboarding.agent_language_title')}</h1>
          <p className="text-sm text-[#A0A0A0]">{t('onboarding.agent_language_desc')}</p>
        </div>
        <div className="space-y-3 mb-6">
          <button data-testid="mode-fixed" onClick={() => setMode('fixed')}
            className={`glass-card w-full flex items-center gap-4 p-5 text-left transition-all ${mode === 'fixed' ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 gold-glow' : 'hover:border-[#3A3A3A]'}`}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8B5CF6]/10"><Globe size={20} className="text-[#8B5CF6]" /></div>
            <div className="flex-1">
              <p className={`text-sm font-semibold ${mode === 'fixed' ? 'text-[#8B5CF6]' : 'text-white'}`}>{t('onboarding.fixed_lang')}</p>
              <p className="text-xs text-[#666666]">{t('onboarding.fixed_lang_desc')}</p>
            </div>
            {mode === 'fixed' && <Check size={18} className="text-[#8B5CF6]" />}
          </button>
          <button data-testid="mode-auto" onClick={() => setMode('auto_detect')}
            className={`glass-card w-full flex items-center gap-4 p-5 text-left transition-all ${mode === 'auto_detect' ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 gold-glow' : 'hover:border-[#3A3A3A]'}`}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8B5CF6]/10"><Sparkles size={20} className="text-[#8B5CF6]" /></div>
            <div className="flex-1">
              <p className={`text-sm font-semibold ${mode === 'auto_detect' ? 'text-[#8B5CF6]' : 'text-white'}`}>{t('onboarding.auto_detect')}</p>
              <p className="text-xs text-[#666666]">{t('onboarding.auto_detect_desc')}</p>
            </div>
            {mode === 'auto_detect' && <Check size={18} className="text-[#8B5CF6]" />}
          </button>
        </div>
        {mode === 'fixed' && (
          <div className="mb-6">
            <label className="mb-2 block text-xs font-medium text-[#A0A0A0]">{t('onboarding.select_language')}</label>
            <div className="grid grid-cols-2 gap-2">
              {langs.map(l => (
                <button key={l.code} onClick={() => setFixedLang(l.code)}
                  className={`glass-card flex items-center gap-2 p-3 text-sm ${fixedLang === l.code ? 'border-[#8B5CF6] text-[#8B5CF6]' : 'text-[#A0A0A0]'}`}>
                  <span>{l.flag}</span> {l.name}
                </button>
              ))}
            </div>
          </div>
        )}
        {mode === 'auto_detect' && (
          <div className="mb-6">
            <label className="mb-2 block text-xs font-medium text-[#A0A0A0]">{t('onboarding.fallback_lang')}</label>
            <select value={fallbackLang} onChange={e => setFallbackLang(e.target.value)}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white outline-none focus:border-[#8B5CF6]">
              {langs.map(l => <option key={l.code} value={l.code}>{l.flag} {l.name}</option>)}
            </select>
          </div>
        )}
        <div className="flex gap-3">
          <button onClick={() => navigate('/dashboard')} className="btn-gold-outline flex-1 rounded-xl py-3 text-sm">{t('onboarding.skip')}</button>
          <button data-testid="agent-lang-continue" onClick={() => navigate('/dashboard')} className="btn-gold flex-1 rounded-xl py-3 text-sm font-semibold">{t('onboarding.continue')}</button>
        </div>
      </div>
    </div>
  );
}
