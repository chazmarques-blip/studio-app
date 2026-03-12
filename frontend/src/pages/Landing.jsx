import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Zap, Globe, ArrowRight, Shield, BarChart3, Bot } from 'lucide-react';

export default function Landing() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const features = [
    { icon: Bot, title: t('landing.feat_agents'), desc: t('landing.feat_agents_desc') },
    { icon: MessageSquare, title: t('landing.feat_omni'), desc: t('landing.feat_omni_desc') },
    { icon: Zap, title: t('landing.feat_multi'), desc: t('landing.feat_multi_desc') },
    { icon: Globe, title: t('landing.feat_lang'), desc: t('landing.feat_lang_desc') },
    { icon: Shield, title: t('landing.feat_crm'), desc: t('landing.feat_crm_desc') },
    { icon: BarChart3, title: t('landing.feat_analytics'), desc: t('landing.feat_analytics_desc') },
  ];

  const channels = [
    { name: 'WhatsApp', color: '#25D366' },
    { name: 'Instagram', color: '#E4405F' },
    { name: 'Facebook', color: '#1877F2' },
    { name: 'Telegram', color: '#0088CC' },
    { name: 'SMS', color: '#F22F46' },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-[#2A2A2A]/50 bg-[#0A0A0A]/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <img src="/logo-agentzz.png" alt="AgentZZ" className="h-10" />
          </div>
          <div className="flex items-center gap-3">
            <button data-testid="landing-login-btn" onClick={() => navigate('/login')} className="btn-gold-outline rounded-lg px-4 py-2 text-sm">{t('landing.signin')}</button>
            <button data-testid="landing-signup-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold rounded-lg px-4 py-2 text-sm">{t('landing.hero_cta')}</button>
          </div>
        </div>
      </header>

      <section className="relative flex min-h-screen flex-col items-center justify-center px-6 pt-20">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute left-1/2 top-1/3 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#C9A84C]/5 blur-[120px]" />
        </div>
        <div className="relative z-10 mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#2A2A2A] bg-[#1A1A1A] px-4 py-1.5">
            <Zap size={14} className="text-[#C9A84C]" />
            <span className="text-xs font-medium text-[#A0A0A0]">{t('landing.badge')}</span>
          </div>
          <h1 className="mb-6 text-4xl font-bold leading-tight tracking-tight text-white sm:text-5xl lg:text-6xl">
            {t('landing.hero_title_1')}<br />
            <span className="bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] bg-clip-text text-transparent">{t('landing.hero_title_2')}</span>
          </h1>
          <p className="mx-auto mb-8 max-w-xl text-base text-[#A0A0A0] sm:text-lg">{t('landing.hero_subtitle')}</p>
          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <button data-testid="hero-start-free-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold flex items-center gap-2 rounded-xl px-8 py-3.5 text-base font-semibold">
              {t('landing.hero_cta')} <ArrowRight size={18} />
            </button>
            <button className="btn-gold-outline rounded-xl px-8 py-3.5 text-base">{t('landing.watch_demo')}</button>
          </div>
        </div>
        <div className="relative z-10 mt-16 flex flex-wrap items-center justify-center gap-4">
          {channels.map(ch => (
            <div key={ch.name} className="glass-card flex items-center gap-2 px-5 py-2.5">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ch.color }} />
              <span className="text-sm font-medium text-[#A0A0A0]">{ch.name}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">{t('landing.features_title')}</h2>
          <p className="text-base text-[#A0A0A0]">{t('landing.features_subtitle')}</p>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div key={i} className="glass-card group p-6 transition-all duration-300 hover:border-[rgba(201,168,76,0.3)]">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]/10">
                <f.icon size={20} className="text-[#C9A84C]" />
              </div>
              <h3 className="mb-2 text-base font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-[#A0A0A0]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">{t('landing.pricing_title')}</h2>
          <p className="text-base text-[#A0A0A0]">{t('landing.pricing_subtitle')}</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <div className="glass-card flex flex-col p-6">
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_free')}</h3>
            <p className="mb-4 text-sm text-[#666666]">{t('landing.plan_free_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">{t('landing.plan_free_price')}</span><span className="text-sm text-[#666666]">{t('landing.plan_free_period')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#A0A0A0]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"/>{t(`landing.plan_free_${k}`)}</li>)}
            </ul>
            <button onClick={() => navigate('/login?tab=signup')} className="btn-gold-outline w-full rounded-lg py-2.5 text-sm">{t('landing.plan_free_cta')}</button>
          </div>
          <div className="glass-card gold-glow relative flex flex-col border-[rgba(201,168,76,0.4)] p-6">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#C9A84C] px-3 py-0.5 text-xs font-semibold text-[#0A0A0A]">{t('landing.plan_starter_badge')}</div>
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_starter')}</h3>
            <p className="mb-4 text-sm text-[#666666]">{t('landing.plan_starter_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-[#C9A84C]">{t('landing.plan_starter_price')}</span><span className="text-sm text-[#666666]">{t('landing.plan_starter_period')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#A0A0A0]">
              {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"/>{t(`landing.plan_starter_${k}`)}</li>)}
            </ul>
            <button className="btn-gold w-full rounded-lg py-2.5 text-sm">{t('landing.plan_starter_cta')}</button>
          </div>
          <div className="glass-card flex flex-col p-6">
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_enterprise')}</h3>
            <p className="mb-4 text-sm text-[#666666]">{t('landing.plan_enterprise_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">{t('landing.plan_enterprise_price')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#A0A0A0]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]"/>{t(`landing.plan_enterprise_${k}`)}</li>)}
            </ul>
            <button className="btn-gold-outline w-full rounded-lg py-2.5 text-sm">{t('landing.plan_enterprise_cta')}</button>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#2A2A2A] bg-[#0A0A0A] px-6 py-10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <div className="flex items-center gap-2">
            <img src="/logo-agentzz.png" alt="AgentZZ" className="h-8" />
          </div>
          <p className="text-xs text-[#666666]">2026 AgentZZ. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
