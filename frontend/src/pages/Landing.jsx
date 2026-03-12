import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Zap, Shield, BarChart3, Globe, MessageSquare, Users, Check, Sparkles } from 'lucide-react';

const gold = '#C9A84C';

const WaIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
const IgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
const FbIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
const TgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
const SmsIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12zM7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;

function LiveChatDemo() {
  const [msgs, setMsgs] = useState([]);
  const [typing, setTyping] = useState(false);
  const chatRef = useRef(null);

  const conversation = [
    { from: 'user', text: 'Hi! I need help choosing a plan for my business' },
    { from: 'agent', text: 'Welcome! What type of business do you have, and how many customers do you serve monthly?' },
    { from: 'user', text: 'E-commerce store, about 500 orders/month' },
    { from: 'agent', text: 'Perfect! I recommend our Starter Plan — unlimited agents, 5 channels, and AI-powered lead scoring. Want a free trial?' },
    { from: 'user', text: 'Yes please!' },
    { from: 'agent', text: 'Done! 14-day trial active. I\'ve deployed "Sofia" to handle your WhatsApp inquiries automatically.' },
  ];

  useEffect(() => {
    let i = 0;
    let cancelled = false;
    const addMsg = () => {
      if (cancelled) return;
      if (i >= conversation.length) {
        setTimeout(() => { if (!cancelled) { setMsgs([]); i = 0; addMsg(); } }, 3500);
        return;
      }
      const msg = conversation[i];
      if (msg.from === 'agent') {
        setTyping(true);
        setTimeout(() => { if (cancelled) return; setTyping(false); setMsgs(prev => [...prev, msg]); i++; setTimeout(addMsg, 1800); }, 1200);
      } else {
        setMsgs(prev => [...prev, msg]);
        i++;
        setTimeout(addMsg, 1400);
      }
    };
    const timer = setTimeout(addMsg, 800);
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [msgs, typing]);

  return (
    <div className="relative rounded-2xl border border-[#1E1E1E] bg-[#0D0D0D]/90 backdrop-blur-xl overflow-hidden shadow-2xl shadow-black/40">
      <div className="flex items-center gap-3 border-b border-[#1A1A1A] px-4 py-3 bg-[#0A0A0A]">
        <div className="relative">
          <div className="h-9 w-9 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] flex items-center justify-center">
            <span className="text-xs font-bold text-[#0A0A0A]">S</span>
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-[#C9A84C] border-2 border-[#0A0A0A]" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-semibold text-white">Sofia</p>
          <p className="text-[10px] text-[#C9A84C]/70 flex items-center gap-1"><span className="inline-block h-1 w-1 rounded-full bg-[#C9A84C]" /> Online</p>
        </div>
        <div className="flex items-center gap-1.5">
          <Sparkles size={12} className="text-[#C9A84C]" />
          <span className="text-[10px] text-[#C9A84C] font-medium">AI</span>
        </div>
      </div>
      <div ref={chatRef} className="h-[240px] overflow-y-auto px-4 py-3 space-y-2.5" style={{scrollbarWidth:'none'}}>
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`} style={{animation: 'slideUp 0.3s ease'}}>
            <div className={`max-w-[82%] rounded-2xl px-3.5 py-2 ${
              m.from === 'user' ? 'bg-[#C9A84C]/10 border border-[#C9A84C]/15' : 'bg-[#141414] border border-[#1E1E1E]'
            }`}>
              {m.from === 'agent' && <p className="text-[9px] text-[#C9A84C]/50 mb-0.5 font-medium">Sofia</p>}
              <p className="text-[12px] leading-relaxed text-[#E0E0E0]">{m.text}</p>
            </div>
          </div>
        ))}
        {typing && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-[#141414] border border-[#1E1E1E] px-5 py-3">
              <div className="flex gap-1.5">{[0,150,300].map(d=><div key={d} className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#C9A84C]/50" style={{animationDelay:`${d}ms`}}/>)}</div>
            </div>
          </div>
        )}
      </div>
      <div className="border-t border-[#1A1A1A] bg-[#0A0A0A] px-3 py-2.5 flex items-center gap-2">
        <div className="flex-1 h-8 rounded-full bg-[#141414] border border-[#1E1E1E] flex items-center px-4">
          <span className="text-[11px] text-[#444]">Type a message...</span>
        </div>
        <div className="h-8 w-8 rounded-full bg-[#C9A84C] flex items-center justify-center flex-shrink-0">
          <ArrowRight size={12} className="text-[#0A0A0A]" />
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [activeAgent, setActiveAgent] = useState(0);
  const [billingAnnual, setBillingAnnual] = useState(true);

  const agents = [
    { name: 'Sofia', role: 'Sales', desc: lang === 'pt' ? 'Vendas e-commerce' : 'E-commerce sales' },
    { name: 'Roberto', role: 'Support', desc: lang === 'pt' ? 'Suporte tecnico' : 'Tech support' },
    { name: 'Ana', role: 'Scheduling', desc: lang === 'pt' ? 'Agendamentos' : 'Scheduling' },
    { name: 'Marina', role: 'Onboarding', desc: lang === 'pt' ? 'Boas-vindas' : 'Onboarding' },
  ];

  useEffect(() => {
    const iv = setInterval(() => setActiveAgent(p => (p + 1) % agents.length), 3000);
    return () => clearInterval(iv);
  }, []);

  const features = [
    { icon: Users, title: t('landing.feat_agents'), desc: t('landing.feat_agents_desc') },
    { icon: MessageSquare, title: t('landing.feat_omni'), desc: t('landing.feat_omni_desc') },
    { icon: Zap, title: t('landing.feat_multi'), desc: t('landing.feat_multi_desc') },
    { icon: Globe, title: t('landing.feat_lang'), desc: t('landing.feat_lang_desc') },
    { icon: Shield, title: t('landing.feat_crm'), desc: t('landing.feat_crm_desc') },
    { icon: BarChart3, title: t('landing.feat_analytics'), desc: t('landing.feat_analytics_desc') },
  ];

  const stats = [
    { value: '22+', label: lang === 'pt' ? 'Agentes IA' : 'AI Agents' },
    { value: '5', label: lang === 'pt' ? 'Canais' : 'Channels' },
    { value: '3', label: lang === 'pt' ? 'Idiomas' : 'Languages' },
    { value: '24/7', label: lang === 'pt' ? 'Disponivel' : 'Available' },
  ];

  const channels = [
    { Icon: WaIcon, name: 'WhatsApp', desc: 'Business API' },
    { Icon: IgIcon, name: 'Instagram', desc: 'Direct Messages' },
    { Icon: FbIcon, name: 'Messenger', desc: 'Facebook Pages' },
    { Icon: TgIcon, name: 'Telegram', desc: 'Smart Bots' },
    { Icon: SmsIcon, name: 'SMS', desc: 'Via Twilio' },
  ];

  return (
    <div className="min-h-screen bg-[#070707] overflow-x-hidden">
      <style>{`
        @keyframes slideUp { from { opacity:0; transform:translateY(10px) } to { opacity:1; transform:translateY(0) } }
        @keyframes float { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-5px) } }
      `}</style>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-[#1A1A1A]/60 bg-[#070707]/70 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-9" />
          <div className="flex items-center gap-3">
            <button data-testid="landing-login-btn" onClick={() => navigate('/login')} className="rounded-lg border border-[#222] px-4 py-2 text-sm text-[#999] hover:border-[#C9A84C]/40 hover:text-white transition-all">{t('landing.signin')}</button>
            <button data-testid="landing-signup-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold rounded-lg px-5 py-2 text-sm font-semibold">{t('landing.hero_cta')}</button>
          </div>
        </div>
      </header>

      {/* ===== HERO ===== */}
      <section className="relative px-6 pt-24 pb-16 overflow-hidden">
        <div className="absolute top-10 left-1/2 -translate-x-1/2 h-[350px] w-[500px] rounded-full bg-[#C9A84C]/4 blur-[150px]" />

        <div className="relative z-10 mx-auto max-w-5xl w-full">
          {/* Content centered compact */}
          <div className="text-center mb-8">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#C9A84C]/15 bg-[#C9A84C]/5 px-3.5 py-1">
              <Zap size={12} className="text-[#C9A84C]" />
              <span className="text-[10px] font-medium text-[#C9A84C]/80">{t('landing.badge')}</span>
            </div>

            <h1 className="mb-3 text-3xl font-bold leading-[1.1] tracking-tight text-white sm:text-4xl lg:text-5xl">
              {t('landing.hero_title_1')}{' '}
              <span className="bg-gradient-to-r from-[#C9A84C] via-[#D9BD6A] to-[#C9A84C] bg-clip-text text-transparent">{t('landing.hero_title_2')}</span>
            </h1>

            <p className="mb-5 text-sm text-[#666] leading-relaxed max-w-md mx-auto sm:text-base">{t('landing.hero_subtitle')}</p>

            <div className="flex flex-col gap-2.5 sm:flex-row justify-center mb-6">
              <button data-testid="hero-start-free-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold flex items-center justify-center gap-2 rounded-xl px-7 py-2.5 text-sm font-semibold group">
                {t('landing.hero_cta')} <ArrowRight size={15} className="group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-7 py-2.5 text-sm text-[#888] hover:border-[#C9A84C]/30 hover:text-white transition-all">{t('landing.watch_demo')}</button>
            </div>

            {/* Stats inline */}
            <div className="flex justify-center gap-6 sm:gap-10">
              {stats.map((s, i) => (
                <div key={i} className="relative">
                  <p className="text-lg font-bold text-white sm:text-xl">{s.value}</p>
                  <p className="text-[10px] text-[#555]">{s.label}</p>
                  {i < stats.length - 1 && <div className="absolute top-0 -right-3 sm:-right-5 h-7 w-px bg-[#1E1E1E]" />}
                </div>
              ))}
            </div>
          </div>

          {/* Hero visual: Image + Chat side by side */}
          <div className="grid md:grid-cols-2 gap-6 items-center max-w-4xl mx-auto">
            {/* Hero image */}
            <div className="relative rounded-2xl overflow-hidden border border-[#1E1E1E]">
              <img src="/hero-person-robot.png" alt="AI Assistant" className="w-full h-auto object-cover" style={{maxHeight:'340px'}} />
              <div className="absolute inset-0 bg-gradient-to-t from-[#070707] via-transparent to-transparent" />
              <div className="absolute bottom-4 left-4 right-4">
                <div className="flex items-center gap-2 bg-[#0A0A0A]/80 backdrop-blur rounded-xl px-3 py-2 border border-[#1E1E1E]">
                  <Sparkles size={14} className="text-[#C9A84C]" />
                  <span className="text-[11px] text-[#999]">{lang === 'pt' ? 'IA que conversa como humano' : 'AI that talks like a human'}</span>
                </div>
              </div>
            </div>
            {/* Chat demo */}
            <div>
              <LiveChatDemo />
            </div>
          </div>
        </div>
      </section>

      {/* ===== CHANNELS - Compact horizontal grid ===== */}
      <section className="py-16 px-6 border-t border-[#141414]">
        <div className="mx-auto max-w-5xl">
          <div className="text-center mb-8">
            <p className="text-[10px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-2">Omnichannel</p>
            <h2 className="mb-2 text-2xl font-bold text-white leading-tight sm:text-3xl">
              {lang === 'pt' ? 'Todos os canais. ' : 'Every channel. '}
              <span className="text-[#C9A84C]">{lang === 'pt' ? 'Um painel.' : 'One dashboard.'}</span>
            </h2>
            <p className="text-sm text-[#666] max-w-md mx-auto">{lang === 'pt' ? 'Conecte todos os seus canais e gerencie tudo em um unico lugar.' : 'Connect all your channels and manage everything in one place.'}</p>
          </div>
          {/* Channel cards - horizontal grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {channels.map((ch, i) => (
              <div key={i} className="rounded-xl border border-[#141414] bg-[#0C0C0C] p-4 text-center hover:border-[#C9A84C]/20 hover:bg-[#0E0E0E] transition-all group cursor-default">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]/8 mx-auto mb-3 group-hover:bg-[#C9A84C]/12 transition">
                  <ch.Icon size={20} color={gold} />
                </div>
                <p className="text-sm font-medium text-white mb-0.5">{ch.name}</p>
                <p className="text-[10px] text-[#555]">{ch.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== AGENTS ===== */}
      <section className="py-16 px-6 border-t border-[#141414] bg-[#0A0A0A]">
        <div className="mx-auto max-w-5xl">
          <div className="text-center mb-10">
            <p className="text-[10px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-2">Marketplace</p>
            <h2 className="mb-2 text-2xl font-bold text-white sm:text-3xl">{lang === 'pt' ? '22 agentes especializados' : '22 specialized agents'}</h2>
            <p className="text-sm text-[#666] max-w-lg mx-auto">{lang === 'pt' ? 'Cada agente tem personalidade e conhecimento unicos para o seu setor' : 'Each agent has unique personality and knowledge for your industry'}</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            {agents.map((a, i) => (
              <button key={i} onClick={() => setActiveAgent(i)}
                className={`rounded-xl border p-4 text-left transition-all duration-300 ${
                  activeAgent === i ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5' : 'border-[#141414] bg-[#0C0C0C] hover:border-[#1E1E1E]'
                }`}>
                <div className="h-10 w-10 rounded-lg flex items-center justify-center text-sm font-bold mb-2 bg-[#C9A84C]/10 text-[#C9A84C]">{a.name[0]}</div>
                <p className="text-sm font-semibold text-white mb-0.5">{a.name}</p>
                <p className="text-[10px] text-[#555]">{a.role} · {a.desc}</p>
                {activeAgent === i && <div className="mt-2 h-0.5 rounded-full bg-gradient-to-r from-[#C9A84C] to-transparent" />}
              </button>
            ))}
          </div>
          <div className="text-center">
            <button onClick={() => navigate('/login?tab=signup')} className="inline-flex items-center gap-2 text-sm text-[#C9A84C]/80 hover:text-[#C9A84C] transition group">
              {lang === 'pt' ? 'Ver todos os 22 agentes' : 'See all 22 agents'} <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section className="mx-auto max-w-5xl px-6 py-16">
        <div className="text-center mb-10">
          <p className="text-[10px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-2">{lang === 'pt' ? 'Funcionalidades' : 'Features'}</p>
          <h2 className="mb-2 text-2xl font-bold text-white sm:text-3xl">{t('landing.features_title')}</h2>
          <p className="text-sm text-[#666]">{t('landing.features_subtitle')}</p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div key={i} className="group rounded-xl border border-[#141414] bg-[#0C0C0C] p-5 transition-all duration-300 hover:border-[#C9A84C]/20 hover:bg-[#0E0E0E]">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]/8 group-hover:bg-[#C9A84C]/12 transition">
                <f.icon size={18} className="text-[#C9A84C]" />
              </div>
              <h3 className="mb-1.5 text-sm font-semibold text-white">{f.title}</h3>
              <p className="text-[12px] leading-relaxed text-[#666]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ===== PRICING ===== */}
      <section className="mx-auto max-w-6xl px-6 py-16 border-t border-[#141414]">
        <div className="text-center mb-8">
          <p className="text-[10px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-2">Pricing</p>
          <h2 className="mb-2 text-2xl font-bold text-white sm:text-3xl">{t('landing.pricing_title')}</h2>
          <p className="text-sm text-[#666] mb-5">{t('landing.pricing_subtitle')}</p>
          {/* Billing toggle */}
          <div className="inline-flex items-center gap-2 rounded-full border border-[#1E1E1E] bg-[#0D0D0D] p-1">
            <button data-testid="billing-annual" onClick={() => setBillingAnnual(true)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#666] hover:text-white'}`}>
              {t('landing.billing_annual')} <span className="ml-1 text-[9px] opacity-80">{t('landing.billing_save')}</span>
            </button>
            <button data-testid="billing-monthly" onClick={() => setBillingAnnual(false)}
              className={`rounded-full px-4 py-1.5 text-xs font-medium transition ${!billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'text-[#666] hover:text-white'}`}>
              {t('landing.billing_monthly')}
            </button>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {/* FREE */}
          <div className="rounded-xl border border-[#141414] bg-[#0C0C0C] flex flex-col p-5 hover:border-[#1E1E1E] transition">
            <h3 className="mb-1 text-base font-bold text-white">{t('landing.plan_free')}</h3>
            <p className="mb-3 text-[11px] text-[#555]">{t('landing.plan_free_desc')}</p>
            <div className="mb-4"><span className="text-2xl font-bold text-white">{t('landing.plan_free_price')}</span><span className="text-xs text-[#555]">{t('landing.plan_free_period')}</span></div>
            <ul className="mb-5 flex-1 space-y-2 text-[12px] text-[#777]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><Check size={12} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_free_${k}`)}</li>)}
            </ul>
            <button onClick={() => navigate('/login?tab=signup')} className="w-full rounded-lg border border-[#1E1E1E] py-2 text-sm text-[#888] hover:border-[#C9A84C]/30 hover:text-white transition">{t('landing.plan_free_cta')}</button>
          </div>
          {/* STARTER */}
          <div className="rounded-xl border border-[#C9A84C]/25 bg-[#0C0C0C] relative flex flex-col p-5 shadow-lg shadow-[#C9A84C]/3">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#C9A84C] px-3 py-0.5 text-[10px] font-semibold text-[#0A0A0A]">{t('landing.plan_starter_badge')}</div>
            <h3 className="mb-1 text-base font-bold text-white">{t('landing.plan_starter')}</h3>
            <p className="mb-3 text-[11px] text-[#555]">{t('landing.plan_starter_desc')}</p>
            <div className="mb-4"><span className="text-2xl font-bold text-[#C9A84C]">{t('landing.plan_starter_price')}</span><span className="text-xs text-[#555]">{t('landing.plan_starter_period')}</span></div>
            <ul className="mb-5 flex-1 space-y-2 text-[12px] text-[#777]">
              {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2"><Check size={12} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_starter_${k}`)}</li>)}
            </ul>
            <button className="btn-gold w-full rounded-lg py-2 text-sm font-semibold">{t('landing.plan_starter_cta')}</button>
          </div>
          {/* PRO */}
          <div className="rounded-xl border border-[#141414] bg-[#0C0C0C] relative flex flex-col p-5 hover:border-[#1E1E1E] transition">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full border border-[#C9A84C]/30 bg-[#0D0D0D] px-3 py-0.5 text-[10px] font-medium text-[#C9A84C]">{t('landing.plan_pro_badge')}</div>
            <h3 className="mb-1 text-base font-bold text-white">{t('landing.plan_pro')}</h3>
            <p className="mb-3 text-[11px] text-[#555]">{t('landing.plan_pro_desc')}</p>
            <div className="mb-4">
              <span className="text-2xl font-bold text-white">{billingAnnual ? t('landing.plan_pro_price_annual') : t('landing.plan_pro_price_monthly')}</span>
              <span className="text-xs text-[#555]">{billingAnnual ? t('landing.plan_pro_period_annual') : t('landing.plan_pro_period_monthly')}</span>
            </div>
            <ul className="mb-5 flex-1 space-y-2 text-[12px] text-[#777]">
              {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2"><Check size={12} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_pro_${k}`)}</li>)}
            </ul>
            <button className="btn-gold w-full rounded-lg py-2 text-sm font-semibold">{t('landing.plan_pro_cta')}</button>
          </div>
          {/* ENTERPRISE */}
          <div className="rounded-xl border border-[#141414] bg-[#0C0C0C] flex flex-col p-5 hover:border-[#1E1E1E] transition">
            <h3 className="mb-1 text-base font-bold text-white">{t('landing.plan_enterprise')}</h3>
            <p className="mb-3 text-[11px] text-[#555]">{t('landing.plan_enterprise_desc')}</p>
            <div className="mb-4">
              <span className="text-2xl font-bold text-white">{billingAnnual ? t('landing.plan_enterprise_price_annual') : t('landing.plan_enterprise_price_monthly')}</span>
              <span className="text-xs text-[#555]">{billingAnnual ? t('landing.plan_enterprise_period_annual') : t('landing.plan_enterprise_period_monthly')}</span>
            </div>
            <ul className="mb-5 flex-1 space-y-2 text-[12px] text-[#777]">
              {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2"><Check size={12} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_enterprise_${k}`)}</li>)}
            </ul>
            <button className="w-full rounded-lg border border-[#1E1E1E] py-2 text-sm text-[#888] hover:border-[#C9A84C]/30 hover:text-white transition">{t('landing.plan_enterprise_cta')}</button>
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="py-16 px-6 border-t border-[#141414] relative">
        <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[200px] w-[400px] rounded-full bg-[#C9A84C]/3 blur-[100px]" /></div>
        <div className="relative z-10 mx-auto max-w-2xl text-center">
          <h2 className="mb-3 text-2xl font-bold text-white sm:text-3xl">{lang === 'pt' ? 'Pronto para automatizar?' : 'Ready to automate?'}</h2>
          <p className="mb-6 text-sm text-[#666]">{lang === 'pt' ? 'Comece gratis. Sem cartao de credito.' : 'Start free. No credit card required.'}</p>
          <button onClick={() => navigate('/login?tab=signup')} className="btn-gold rounded-xl px-8 py-3 text-sm font-semibold group inline-flex items-center gap-2">
            {t('landing.hero_cta')} <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#141414] px-6 py-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 sm:flex-row">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-6" />
          <div className="flex items-center gap-4">
            <WaIcon size={14} color="#666" /><IgIcon size={14} color="#666" /><FbIcon size={14} color="#666" /><TgIcon size={14} color="#666" />
          </div>
          <p className="text-[10px] text-[#444]">2026 AgentZZ</p>
        </div>
      </footer>
    </div>
  );
}
