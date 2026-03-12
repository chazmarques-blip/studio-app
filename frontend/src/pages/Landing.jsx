import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Zap, Shield, BarChart3, Globe, MessageSquare, Users, ChevronRight, Check } from 'lucide-react';

const gold = '#C9A84C';

// SVG Social Icons
const WaIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
const IgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
const FbIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
const TgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
const SmsIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12zM7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;

// Minimalist person SVG
const PersonSvg = ({ className = '', flip = false }) => (
  <svg className={className} viewBox="0 0 60 80" fill="none" style={{ transform: flip ? 'scaleX(-1)' : 'none' }}>
    <circle cx="30" cy="16" r="12" fill="#2A2A2A" stroke={gold} strokeWidth="1.5"/>
    <path d="M14 80V55c0-8.8 7.2-16 16-16s16 7.2 16 16v25" fill="#1A1A1A" stroke={gold} strokeWidth="1.5"/>
    <circle cx="26" cy="14" r="1.5" fill={gold}/>
    <circle cx="34" cy="14" r="1.5" fill={gold}/>
    <path d="M26 20c2 2 6 2 8 0" stroke={gold} strokeWidth="1.2" strokeLinecap="round" fill="none"/>
  </svg>
);

// Animated chat demo
function LiveChatDemo() {
  const [msgs, setMsgs] = useState([]);
  const [typing, setTyping] = useState(false);
  const chatRef = useRef(null);

  const conversation = [
    { from: 'user', text: 'Hi! I need help choosing a plan for my business' },
    { from: 'agent', text: 'Welcome! I\'d love to help. What type of business do you have, and how many customers do you serve monthly?' },
    { from: 'user', text: 'We\'re an e-commerce store with about 500 orders/month' },
    { from: 'agent', text: 'Great! For your volume, I recommend our Starter Plan. It includes unlimited agents, 5 channels, and AI-powered lead scoring. Shall I set up a free trial?' },
    { from: 'user', text: 'That sounds perfect! Yes please' },
    { from: 'agent', text: 'Done! Your 14-day trial is active. I\'ve also deployed our e-commerce specialist agent "Sofia" to handle your WhatsApp inquiries automatically.' },
  ];

  useEffect(() => {
    let i = 0;
    const addMsg = () => {
      if (i >= conversation.length) {
        setTimeout(() => { setMsgs([]); i = 0; addMsg(); }, 3000);
        return;
      }
      const msg = conversation[i];
      if (msg.from === 'agent') {
        setTyping(true);
        setTimeout(() => {
          setTyping(false);
          setMsgs(prev => [...prev, msg]);
          i++;
          setTimeout(addMsg, 1800);
        }, 1200);
      } else {
        setMsgs(prev => [...prev, msg]);
        i++;
        setTimeout(addMsg, 1400);
      }
    };
    const timer = setTimeout(addMsg, 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [msgs, typing]);

  return (
    <div className="w-full max-w-sm mx-auto">
      <div className="rounded-2xl border border-[#2A2A2A] bg-[#111] overflow-hidden shadow-2xl shadow-[#C9A84C]/5">
        <div className="flex items-center gap-3 border-b border-[#2A2A2A] bg-[#0D0D0D] px-4 py-3">
          <div className="relative">
            <div className="h-9 w-9 rounded-full bg-[#C9A84C]/15 flex items-center justify-center">
              <span className="text-sm font-bold text-[#C9A84C]">S</span>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-[#25D366] border-2 border-[#0D0D0D]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">Sofia</p>
            <p className="text-[10px] text-[#25D366]">Online via WhatsApp</p>
          </div>
          <WaIcon size={18} color="#25D366" />
        </div>
        <div ref={chatRef} className="h-64 overflow-y-auto px-3 py-3 space-y-2.5 scrollbar-hide">
          {msgs.map((m, i) => (
            <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'} animate-[slideUp_0.3s_ease]`}>
              <div className={`max-w-[85%] rounded-2xl px-3.5 py-2 ${
                m.from === 'user' ? 'bg-[#C9A84C]/15 border border-[#C9A84C]/20' : 'bg-[#1A1A1A] border border-[#2A2A2A]'
              }`}>
                <p className="text-[13px] leading-relaxed text-white">{m.text}</p>
              </div>
            </div>
          ))}
          {typing && (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-[#1A1A1A] border border-[#2A2A2A] px-4 py-3">
                <div className="flex gap-1"><div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#C9A84C]" style={{animationDelay:'0ms'}}/><div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#C9A84C]" style={{animationDelay:'150ms'}}/><div className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#C9A84C]" style={{animationDelay:'300ms'}}/></div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Floating channel orbits
function ChannelOrbit() {
  const channels = [
    { Icon: WaIcon, label: 'WhatsApp', angle: 0 },
    { Icon: IgIcon, label: 'Instagram', angle: 72 },
    { Icon: FbIcon, label: 'Facebook', angle: 144 },
    { Icon: TgIcon, label: 'Telegram', angle: 216 },
    { Icon: SmsIcon, label: 'SMS', angle: 288 },
  ];

  return (
    <div className="relative w-72 h-72 mx-auto">
      {/* Center */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-20 w-20 rounded-full bg-[#C9A84C]/10 border border-[#C9A84C]/30 flex items-center justify-center z-10">
        <img src="/logo-agentzz.png" alt="AgentZZ" className="h-10" />
      </div>
      {/* Orbit ring */}
      <div className="absolute inset-4 rounded-full border border-dashed border-[#2A2A2A] animate-[spin_30s_linear_infinite]" />
      {/* Channel nodes */}
      {channels.map((ch, i) => {
        const rad = (ch.angle * Math.PI) / 180;
        const r = 120;
        const x = 144 + r * Math.cos(rad) - 24;
        const y = 144 + r * Math.sin(rad) - 24;
        return (
          <div key={i} className="absolute h-12 w-12 rounded-xl bg-[#111] border border-[#2A2A2A] flex items-center justify-center hover:border-[#C9A84C]/50 hover:scale-110 transition-all duration-300 cursor-pointer group"
            style={{ left: `${x}px`, top: `${y}px` }}>
            <ch.Icon size={22} />
            <span className="absolute -bottom-6 text-[9px] text-[#666] group-hover:text-[#C9A84C] transition whitespace-nowrap">{ch.label}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [activeAgent, setActiveAgent] = useState(0);

  const agents = [
    { name: 'Sofia', type: 'Sales', color: '#C9A84C', desc: lang === 'pt' ? 'Vendas e-commerce' : 'E-commerce sales' },
    { name: 'Roberto', type: 'Support', color: '#2196F3', desc: lang === 'pt' ? 'Suporte tecnico' : 'Tech support' },
    { name: 'Ana', type: 'Scheduling', color: '#25D366', desc: lang === 'pt' ? 'Agendamentos' : 'Scheduling' },
    { name: 'Marina', type: 'Onboarding', color: '#E4405F', desc: lang === 'pt' ? 'Boas-vindas' : 'Onboarding' },
  ];

  useEffect(() => {
    const interval = setInterval(() => setActiveAgent(p => (p + 1) % agents.length), 3000);
    return () => clearInterval(interval);
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

  return (
    <div className="min-h-screen bg-[#0A0A0A] overflow-x-hidden">
      <style>{`
        @keyframes slideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
        @keyframes pulse-ring { 0% { transform: scale(0.8); opacity: 0.5; } 100% { transform: scale(1.8); opacity: 0; } }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .animate-float { animation: float 4s ease-in-out infinite; }
        .stagger-1 { animation-delay: 0.1s; }
        .stagger-2 { animation-delay: 0.2s; }
        .stagger-3 { animation-delay: 0.3s; }
        .stagger-4 { animation-delay: 0.4s; }
        .stagger-5 { animation-delay: 0.5s; }
      `}</style>

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 border-b border-[#2A2A2A]/50 bg-[#0A0A0A]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-9" />
          <div className="flex items-center gap-3">
            <button data-testid="landing-login-btn" onClick={() => navigate('/login')} className="rounded-lg border border-[#2A2A2A] bg-transparent px-4 py-2 text-sm text-[#A0A0A0] hover:border-[#C9A84C] hover:text-white transition">{t('landing.signin')}</button>
            <button data-testid="landing-signup-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold rounded-lg px-5 py-2 text-sm font-semibold">{t('landing.hero_cta')}</button>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="relative min-h-screen flex items-center px-6 pt-20 pb-16">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-[#C9A84C]/3 blur-[150px]" />
          <div className="absolute right-1/4 bottom-1/4 h-[400px] w-[400px] rounded-full bg-[#C9A84C]/2 blur-[120px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-6xl w-full grid lg:grid-cols-2 gap-12 items-center">
          {/* Left - Text */}
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[#C9A84C]/20 bg-[#C9A84C]/5 px-4 py-1.5 animate-[fadeIn_0.5s_ease]">
              <Zap size={14} className="text-[#C9A84C]" />
              <span className="text-xs font-medium text-[#C9A84C]">{t('landing.badge')}</span>
            </div>
            <h1 className="mb-6 text-4xl font-bold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-6xl animate-[slideUp_0.6s_ease]">
              {t('landing.hero_title_1')}<br />
              <span className="bg-gradient-to-r from-[#C9A84C] via-[#D4B85A] to-[#C9A84C] bg-clip-text text-transparent">{t('landing.hero_title_2')}</span>
            </h1>
            <p className="mb-8 max-w-lg text-base text-[#888] leading-relaxed sm:text-lg animate-[slideUp_0.7s_ease]">{t('landing.hero_subtitle')}</p>

            <div className="flex flex-col gap-4 sm:flex-row animate-[slideUp_0.8s_ease]">
              <button data-testid="hero-start-free-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold flex items-center justify-center gap-2 rounded-xl px-8 py-3.5 text-base font-semibold group">
                {t('landing.hero_cta')} <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="rounded-xl border border-[#2A2A2A] bg-[#111] px-8 py-3.5 text-base text-[#A0A0A0] hover:border-[#C9A84C]/50 hover:text-white transition">{t('landing.watch_demo')}</button>
            </div>

            {/* Stats */}
            <div className="mt-10 flex gap-8 animate-[slideUp_0.9s_ease]">
              {stats.map((s, i) => (
                <div key={i}>
                  <p className="text-2xl font-bold text-[#C9A84C]">{s.value}</p>
                  <p className="text-xs text-[#666]">{s.label}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Right - Live Chat Demo */}
          <div className="hidden lg:block animate-[fadeIn_1s_ease]">
            <div className="relative">
              {/* Floating people */}
              <div className="absolute -left-8 top-4 animate-float stagger-1"><PersonSvg className="h-16 opacity-60" /></div>
              <div className="absolute -right-4 top-16 animate-float stagger-3"><PersonSvg className="h-14 opacity-40" flip /></div>
              <div className="absolute -left-4 bottom-8 animate-float stagger-5"><PersonSvg className="h-12 opacity-30" flip /></div>
              <LiveChatDemo />
            </div>
          </div>
        </div>
      </section>

      {/* Channel Orbit Section */}
      <section className="py-20 px-6 border-t border-[#1A1A1A]">
        <div className="mx-auto max-w-6xl grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">
              {lang === 'pt' ? 'Todos os canais.' : 'Every channel.'}<br/>
              <span className="text-[#C9A84C]">{lang === 'pt' ? 'Um unico painel.' : 'One dashboard.'}</span>
            </h2>
            <p className="mb-8 text-base text-[#888] leading-relaxed">{lang === 'pt' ? 'Conecte WhatsApp, Instagram, Facebook, Telegram e SMS. Gerencie todas as conversas em um unico lugar com agentes IA respondendo automaticamente.' : 'Connect WhatsApp, Instagram, Facebook, Telegram, and SMS. Manage all conversations in one place with AI agents responding automatically.'}</p>
            <div className="space-y-3">
              {[
                { Icon: WaIcon, name: 'WhatsApp Business', desc: lang === 'pt' ? 'Via Evolution API' : 'Via Evolution API' },
                { Icon: IgIcon, name: 'Instagram DM', desc: lang === 'pt' ? 'Mensagens diretas' : 'Direct messages' },
                { Icon: FbIcon, name: 'Messenger', desc: lang === 'pt' ? 'Paginas do Facebook' : 'Facebook pages' },
                { Icon: TgIcon, name: 'Telegram Bot', desc: lang === 'pt' ? 'Bots inteligentes' : 'Smart bots' },
                { Icon: SmsIcon, name: 'SMS', desc: lang === 'pt' ? 'Via Twilio' : 'Via Twilio' },
              ].map((ch, i) => (
                <div key={i} className="flex items-center gap-4 rounded-xl border border-[#1A1A1A] bg-[#111]/50 p-3 hover:border-[#C9A84C]/30 hover:bg-[#C9A84C]/5 transition-all group cursor-default">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#1A1A1A] group-hover:bg-[#C9A84C]/10 transition"><ch.Icon size={20} /></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{ch.name}</p>
                    <p className="text-[11px] text-[#555]">{ch.desc}</p>
                  </div>
                  <ChevronRight size={14} className="text-[#333] group-hover:text-[#C9A84C] transition" />
                </div>
              ))}
            </div>
          </div>
          <div className="hidden lg:flex justify-center">
            <ChannelOrbit />
          </div>
        </div>
      </section>

      {/* Agent Showcase */}
      <section className="py-20 px-6 border-t border-[#1A1A1A] bg-[#0D0D0D]">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="mb-3 text-2xl font-bold text-white sm:text-3xl">{lang === 'pt' ? '22 agentes especializados' : '22 specialized agents'}</h2>
            <p className="text-base text-[#888]">{lang === 'pt' ? 'Cada agente tem personalidade, protocolo e conhecimento unicos' : 'Each agent has unique personality, protocol, and knowledge'}</p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {agents.map((a, i) => (
              <button key={i} data-testid={`agent-card-${a.name.toLowerCase()}`}
                onClick={() => setActiveAgent(i)}
                className={`rounded-xl border p-4 text-left transition-all duration-300 ${
                  activeAgent === i ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5 scale-[1.02]' : 'border-[#1A1A1A] bg-[#111] hover:border-[#2A2A2A]'
                }`}>
                <div className="flex items-center gap-3 mb-2">
                  <div className="h-10 w-10 rounded-full flex items-center justify-center text-sm font-bold" style={{ backgroundColor: `${a.color}15`, color: a.color }}>{a.name[0]}</div>
                  <div>
                    <p className="text-sm font-semibold text-white">{a.name}</p>
                    <p className="text-[10px] text-[#666]">{a.type}</p>
                  </div>
                </div>
                <p className="text-xs text-[#888]">{a.desc}</p>
                {activeAgent === i && <div className="mt-2 h-0.5 rounded-full bg-gradient-to-r from-[#C9A84C] to-transparent" />}
              </button>
            ))}
          </div>

          <div className="flex justify-center">
            <button onClick={() => navigate('/login?tab=signup')} className="flex items-center gap-2 text-sm text-[#C9A84C] hover:text-[#D4B85A] transition group">
              {lang === 'pt' ? 'Ver todos os 22 agentes' : 'See all 22 agents'} <ArrowRight size={14} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">{t('landing.features_title')}</h2>
          <p className="text-base text-[#888]">{t('landing.features_subtitle')}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div key={i} className="group rounded-xl border border-[#1A1A1A] bg-[#111]/50 p-6 transition-all duration-300 hover:border-[#C9A84C]/30 hover:bg-[#C9A84C]/5">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-[#C9A84C]/10 group-hover:bg-[#C9A84C]/15 transition">
                <f.icon size={22} className="text-[#C9A84C]" />
              </div>
              <h3 className="mb-2 text-base font-semibold text-white">{f.title}</h3>
              <p className="text-sm leading-relaxed text-[#888]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="mx-auto max-w-5xl px-6 py-24 border-t border-[#1A1A1A]">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-2xl font-bold text-white sm:text-3xl">{t('landing.pricing_title')}</h2>
          <p className="text-base text-[#888]">{t('landing.pricing_subtitle')}</p>
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border border-[#1A1A1A] bg-[#111]/50 flex flex-col p-6 hover:border-[#2A2A2A] transition">
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_free')}</h3>
            <p className="mb-4 text-sm text-[#666]">{t('landing.plan_free_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">{t('landing.plan_free_price')}</span><span className="text-sm text-[#666]">{t('landing.plan_free_period')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#888]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><Check size={14} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_free_${k}`)}</li>)}
            </ul>
            <button onClick={() => navigate('/login?tab=signup')} className="w-full rounded-lg border border-[#2A2A2A] py-2.5 text-sm text-[#A0A0A0] hover:border-[#C9A84C] hover:text-white transition">{t('landing.plan_free_cta')}</button>
          </div>
          <div className="rounded-xl border-2 border-[#C9A84C]/40 bg-[#111]/50 relative flex flex-col p-6 shadow-lg shadow-[#C9A84C]/5">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#C9A84C] px-4 py-1 text-xs font-semibold text-[#0A0A0A]">{t('landing.plan_starter_badge')}</div>
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_starter')}</h3>
            <p className="mb-4 text-sm text-[#666]">{t('landing.plan_starter_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-[#C9A84C]">{t('landing.plan_starter_price')}</span><span className="text-sm text-[#666]">{t('landing.plan_starter_period')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#888]">
              {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2"><Check size={14} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_starter_${k}`)}</li>)}
            </ul>
            <button className="btn-gold w-full rounded-lg py-2.5 text-sm font-semibold">{t('landing.plan_starter_cta')}</button>
          </div>
          <div className="rounded-xl border border-[#1A1A1A] bg-[#111]/50 flex flex-col p-6 hover:border-[#2A2A2A] transition">
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_enterprise')}</h3>
            <p className="mb-4 text-sm text-[#666]">{t('landing.plan_enterprise_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">{t('landing.plan_enterprise_price')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#888]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2"><Check size={14} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_enterprise_${k}`)}</li>)}
            </ul>
            <button className="w-full rounded-lg border border-[#2A2A2A] py-2.5 text-sm text-[#A0A0A0] hover:border-[#C9A84C] hover:text-white transition">{t('landing.plan_enterprise_cta')}</button>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-[#1A1A1A]">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="mb-4 text-3xl font-bold text-white sm:text-4xl">{lang === 'pt' ? 'Pronto para automatizar?' : 'Ready to automate?'}</h2>
          <p className="mb-8 text-base text-[#888]">{lang === 'pt' ? 'Comece gratis. Sem cartao de credito.' : 'Start free. No credit card required.'}</p>
          <button onClick={() => navigate('/login?tab=signup')} className="btn-gold rounded-xl px-10 py-4 text-base font-semibold group inline-flex items-center gap-2">
            {t('landing.hero_cta')} <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#1A1A1A] bg-[#0A0A0A] px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-7" />
          <div className="flex items-center gap-6">
            <WaIcon size={16} color="#555" /><IgIcon size={16} color="#555" /><FbIcon size={16} color="#555" /><TgIcon size={16} color="#555" />
          </div>
          <p className="text-xs text-[#555]">2026 AgentZZ. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
