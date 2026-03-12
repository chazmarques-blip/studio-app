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
    { type: 'whatsapp', name: 'WhatsApp' },
    { type: 'instagram', name: 'Instagram' },
    { type: 'facebook', name: 'Facebook' },
    { type: 'telegram', name: 'Telegram' },
    { type: 'sms', name: 'SMS' },
  ];

  const ChannelIcon = ({ type }) => {
    const cls = "h-5 w-5 flex-shrink-0";
    const gold = "#C9A84C";
    switch (type) {
      case 'whatsapp': return (
        <svg className={cls} viewBox="0 0 24 24" fill={gold}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>
      );
      case 'instagram': return (
        <svg className={cls} viewBox="0 0 24 24" fill={gold}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>
      );
      case 'facebook': return (
        <svg className={cls} viewBox="0 0 24 24" fill={gold}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
      );
      case 'telegram': return (
        <svg className={cls} viewBox="0 0 24 24" fill={gold}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>
      );
      case 'sms': return (
        <svg className={cls} viewBox="0 0 24 24" fill={gold}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12zM7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>
      );
      default: return null;
    }
  };

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
            <div key={ch.name} className="glass-card flex items-center gap-3 px-5 py-3">
              <ChannelIcon type={ch.type} />
              <span className="text-sm font-medium text-[#C9A84C]">{ch.name}</span>
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
