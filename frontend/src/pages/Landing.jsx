import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Zap, Shield, BarChart3, Globe, MessageSquare, Users, ChevronRight, Check, Sparkles } from 'lucide-react';

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
    <div className="relative">
      {/* Glow behind chat */}
      <div className="absolute -inset-6 rounded-3xl bg-[#C9A84C]/5 blur-2xl" />
      <div className="relative rounded-2xl border border-[#1E1E1E] bg-[#0D0D0D]/90 backdrop-blur-xl overflow-hidden shadow-2xl shadow-black/40">
        {/* Chat header */}
        <div className="flex items-center gap-3 border-b border-[#1A1A1A] px-5 py-3.5 bg-[#0A0A0A]">
          <div className="relative">
            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] flex items-center justify-center">
              <span className="text-sm font-bold text-[#0A0A0A]">S</span>
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-[#25D366] border-2 border-[#0A0A0A]" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">Sofia</p>
            <p className="text-[10px] text-[#25D366] flex items-center gap-1"><span className="inline-block h-1 w-1 rounded-full bg-[#25D366]" /> Online via WhatsApp</p>
          </div>
          <div className="flex items-center gap-2">
            <Sparkles size={14} className="text-[#C9A84C]" />
            <span className="text-[10px] text-[#C9A84C] font-medium">AI</span>
          </div>
        </div>
        {/* Messages */}
        <div ref={chatRef} className="h-[280px] overflow-y-auto px-4 py-4 space-y-3" style={{scrollbarWidth:'none'}}>
          {msgs.map((m, i) => (
            <div key={i} className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`} style={{animation: 'slideUp 0.3s ease'}}>
              <div className={`max-w-[82%] rounded-2xl px-4 py-2.5 ${
                m.from === 'user' ? 'bg-[#C9A84C]/12 border border-[#C9A84C]/15' : 'bg-[#141414] border border-[#1E1E1E]'
              }`}>
                {m.from === 'agent' && <p className="text-[9px] text-[#C9A84C]/60 mb-0.5 font-medium">Sofia</p>}
                <p className="text-[13px] leading-relaxed text-[#E0E0E0]">{m.text}</p>
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
        {/* Input bar */}
        <div className="border-t border-[#1A1A1A] bg-[#0A0A0A] px-4 py-3 flex items-center gap-2">
          <div className="flex-1 h-9 rounded-full bg-[#141414] border border-[#1E1E1E] flex items-center px-4">
            <span className="text-xs text-[#444]">Type a message...</span>
          </div>
          <div className="h-9 w-9 rounded-full bg-[#C9A84C] flex items-center justify-center flex-shrink-0">
            <ArrowRight size={14} className="text-[#0A0A0A]" />
          </div>
        </div>
      </div>
      {/* Floating channel pills around chat */}
      <div className="absolute -top-3 -left-6 flex items-center gap-1.5 rounded-full bg-[#111]/90 backdrop-blur border border-[#1E1E1E] px-3 py-1.5 shadow-lg" style={{animation:'float 5s ease-in-out infinite'}}>
        <WaIcon size={14} color="#25D366" /><span className="text-[10px] text-[#888]">WhatsApp</span>
      </div>
      <div className="absolute top-12 -right-8 flex items-center gap-1.5 rounded-full bg-[#111]/90 backdrop-blur border border-[#1E1E1E] px-3 py-1.5 shadow-lg" style={{animation:'float 4s ease-in-out infinite 0.5s'}}>
        <IgIcon size={14} color="#E4405F" /><span className="text-[10px] text-[#888]">Instagram</span>
      </div>
      <div className="absolute bottom-16 -left-10 flex items-center gap-1.5 rounded-full bg-[#111]/90 backdrop-blur border border-[#1E1E1E] px-3 py-1.5 shadow-lg" style={{animation:'float 6s ease-in-out infinite 1s'}}>
        <TgIcon size={14} color="#0088CC" /><span className="text-[10px] text-[#888]">Telegram</span>
      </div>
      <div className="absolute -bottom-2 right-4 flex items-center gap-1.5 rounded-full bg-[#111]/90 backdrop-blur border border-[#1E1E1E] px-3 py-1.5 shadow-lg" style={{animation:'float 5s ease-in-out infinite 1.5s'}}>
        <FbIcon size={14} color="#1877F2" /><span className="text-[10px] text-[#888]">Messenger</span>
      </div>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [activeAgent, setActiveAgent] = useState(0);

  const agents = [
    { name: 'Sofia', role: 'Sales', color: '#C9A84C', desc: lang === 'pt' ? 'Vendas e-commerce' : 'E-commerce sales', cat: 'ecommerce' },
    { name: 'Roberto', role: 'Support', color: '#2196F3', desc: lang === 'pt' ? 'Suporte tecnico' : 'Tech support', cat: 'general' },
    { name: 'Ana', role: 'Scheduling', color: '#25D366', desc: lang === 'pt' ? 'Agendamentos' : 'Scheduling', cat: 'general' },
    { name: 'Marina', role: 'Onboarding', color: '#E4405F', desc: lang === 'pt' ? 'Boas-vindas' : 'Onboarding', cat: 'general' },
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

  return (
    <div className="min-h-screen bg-[#070707] overflow-x-hidden">
      <style>{`
        @keyframes slideUp { from { opacity:0; transform:translateY(10px) } to { opacity:1; transform:translateY(0) } }
        @keyframes float { 0%,100% { transform:translateY(0) } 50% { transform:translateY(-6px) } }
        @keyframes gridPulse { 0%,100% { opacity:0.02 } 50% { opacity:0.05 } }
      `}</style>

      {/* Grid background texture */}
      <div className="fixed inset-0 pointer-events-none z-0" style={{backgroundImage:'linear-gradient(rgba(201,168,76,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(201,168,76,0.03) 1px, transparent 1px)', backgroundSize:'60px 60px'}} />

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
      <section className="relative px-6 pt-28 pb-20 overflow-hidden">
        {/* Background glow orbs */}
        <div className="absolute top-10 left-1/2 -translate-x-1/2 h-[400px] w-[600px] rounded-full bg-[#C9A84C]/4 blur-[150px]" />

        <div className="relative z-10 mx-auto max-w-5xl w-full">
          {/* Top content - centered and compact */}
          <div className="text-center mb-12">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-[#C9A84C]/15 bg-[#C9A84C]/5 px-4 py-1.5">
              <Zap size={13} className="text-[#C9A84C]" />
              <span className="text-[11px] font-medium text-[#C9A84C]/80">{t('landing.badge')}</span>
            </div>

            <h1 className="mb-4 text-4xl font-bold leading-[1.1] tracking-tight text-white sm:text-5xl lg:text-[3.25rem]">
              {t('landing.hero_title_1')}{' '}
              <span className="bg-gradient-to-r from-[#C9A84C] via-[#D9BD6A] to-[#C9A84C] bg-clip-text text-transparent">{t('landing.hero_title_2')}</span>
            </h1>

            <p className="mb-6 text-base text-[#666] leading-relaxed max-w-lg mx-auto">{t('landing.hero_subtitle')}</p>

            <div className="flex flex-col gap-3 sm:flex-row justify-center mb-8">
              <button data-testid="hero-start-free-btn" onClick={() => navigate('/login?tab=signup')} className="btn-gold flex items-center justify-center gap-2 rounded-xl px-8 py-3 text-sm font-semibold group">
                {t('landing.hero_cta')} <ArrowRight size={16} className="group-hover:translate-x-1 transition-transform" />
              </button>
              <button className="rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-8 py-3 text-sm text-[#888] hover:border-[#C9A84C]/30 hover:text-white transition-all">{t('landing.watch_demo')}</button>
            </div>

            {/* Stats row - centered */}
            <div className="flex justify-center gap-8 sm:gap-12">
              {stats.map((s, i) => (
                <div key={i} className="relative">
                  <p className="text-xl font-bold text-white sm:text-2xl">{s.value}</p>
                  <p className="text-[10px] text-[#555] mt-0.5 sm:text-[11px]">{s.label}</p>
                  {i < stats.length - 1 && <div className="absolute top-0.5 -right-4 sm:-right-6 h-8 w-px bg-[#1E1E1E]" />}
                </div>
              ))}
            </div>
          </div>

          {/* Chat Demo - centered below content */}
          <div className="mx-auto max-w-md sm:max-w-lg">
            <LiveChatDemo />
          </div>
        </div>
      </section>

      {/* ===== CHANNELS ===== */}
      <section className="py-24 px-6 border-t border-[#141414]">
        <div className="mx-auto max-w-6xl grid lg:grid-cols-2 gap-20 items-center">
          <div>
            <p className="text-[11px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-4">Omnichannel</p>
            <h2 className="mb-4 text-3xl font-bold text-white leading-tight">
              {lang === 'pt' ? 'Todos os canais.' : 'Every channel.'}<br/>
              <span className="text-[#C9A84C]">{lang === 'pt' ? 'Um unico painel.' : 'One dashboard.'}</span>
            </h2>
            <p className="mb-10 text-base text-[#777] leading-relaxed max-w-md">{lang === 'pt' ? 'Conecte WhatsApp, Instagram, Facebook, Telegram e SMS. Gerencie todas as conversas em um unico lugar.' : 'Connect WhatsApp, Instagram, Facebook, Telegram, and SMS. Manage all conversations in one place.'}</p>
            <div className="space-y-2.5">
              {[
                { Icon: WaIcon, name: 'WhatsApp Business', desc: 'Evolution API', c: '#25D366' },
                { Icon: IgIcon, name: 'Instagram DM', desc: 'Direct Messages', c: '#E4405F' },
                { Icon: FbIcon, name: 'Messenger', desc: 'Facebook Pages', c: '#1877F2' },
                { Icon: TgIcon, name: 'Telegram Bot', desc: 'Smart Bots', c: '#0088CC' },
                { Icon: SmsIcon, name: 'SMS', desc: 'Via Twilio', c: '#F22F46' },
              ].map((ch, i) => (
                <div key={i} className="flex items-center gap-4 rounded-xl border border-[#141414] bg-[#0C0C0C] p-3.5 hover:border-[#C9A84C]/20 hover:bg-[#0E0E0E] transition-all group cursor-default">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: `${ch.c}08` }}><ch.Icon size={20} color={ch.c} /></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{ch.name}</p>
                    <p className="text-[11px] text-[#444]">{ch.desc}</p>
                  </div>
                  <ChevronRight size={14} className="text-[#222] group-hover:text-[#C9A84C]/50 transition" />
                </div>
              ))}
            </div>
          </div>
          {/* Right - visual */}
          <div className="hidden lg:flex justify-center">
            <div className="relative w-80 h-80">
              {/* Center logo */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-24 w-24 rounded-2xl bg-[#0D0D0D] border border-[#1E1E1E] flex items-center justify-center z-10 shadow-xl shadow-black/30">
                <img src="/logo-agentzz.png" alt="" className="h-12" />
              </div>
              {/* Orbit ring */}
              <div className="absolute inset-8 rounded-full border border-[#1A1A1A]" />
              <div className="absolute inset-4 rounded-full border border-[#141414]" />
              {/* Channel nodes */}
              {[
                { Icon: WaIcon, c: '#25D366', angle: -90 },
                { Icon: IgIcon, c: '#E4405F', angle: -18 },
                { Icon: FbIcon, c: '#1877F2', angle: 54 },
                { Icon: TgIcon, c: '#0088CC', angle: 126 },
                { Icon: SmsIcon, c: '#F22F46', angle: 198 },
              ].map((ch, i) => {
                const r = 130;
                const rad = (ch.angle * Math.PI) / 180;
                return (
                  <div key={i} className="absolute h-12 w-12 rounded-xl bg-[#0C0C0C] border border-[#1E1E1E] flex items-center justify-center hover:scale-110 hover:border-opacity-50 transition-all duration-300"
                    style={{ left: `${160 + r * Math.cos(rad) - 24}px`, top: `${160 + r * Math.sin(rad) - 24}px`, borderColor: `${ch.c}20`, animation: `float ${4 + i * 0.5}s ease-in-out infinite ${i * 0.3}s` }}>
                    <ch.Icon size={20} color={ch.c} />
                  </div>
                );
              })}
              {/* Connection lines */}
              <svg className="absolute inset-0 w-full h-full" style={{zIndex:0}}>
                {[{a:-90,c:'#25D366'},{a:-18,c:'#E4405F'},{a:54,c:'#1877F2'},{a:126,c:'#0088CC'},{a:198,c:'#F22F46'}].map((ch,i)=>{
                  const r=130;const rad=(ch.a*Math.PI)/180;
                  return <line key={i} x1="160" y1="160" x2={160+r*Math.cos(rad)} y2={160+r*Math.sin(rad)} stroke={ch.c} strokeWidth="0.5" strokeOpacity="0.15" strokeDasharray="4 4"/>;
                })}
              </svg>
            </div>
          </div>
        </div>
      </section>

      {/* ===== AGENTS ===== */}
      <section className="py-24 px-6 border-t border-[#141414] bg-[#0A0A0A]">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-14">
            <p className="text-[11px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-4">{lang === 'pt' ? 'Marketplace' : 'Marketplace'}</p>
            <h2 className="mb-3 text-3xl font-bold text-white">{lang === 'pt' ? '22 agentes especializados' : '22 specialized agents'}</h2>
            <p className="text-base text-[#777] max-w-lg mx-auto">{lang === 'pt' ? 'Cada agente tem personalidade, protocolo e conhecimento unicos para o seu setor' : 'Each agent has unique personality, protocol, and knowledge for your industry'}</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {agents.map((a, i) => (
              <button key={i} onClick={() => setActiveAgent(i)}
                className={`rounded-xl border p-5 text-left transition-all duration-300 ${
                  activeAgent === i ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5' : 'border-[#141414] bg-[#0C0C0C] hover:border-[#1E1E1E]'
                }`}>
                <div className="h-11 w-11 rounded-xl flex items-center justify-center text-sm font-bold mb-3" style={{ backgroundColor: `${a.color}12`, color: a.color }}>{a.name[0]}</div>
                <p className="text-sm font-semibold text-white mb-0.5">{a.name}</p>
                <p className="text-[11px] text-[#555]">{a.role} &middot; {a.desc}</p>
                {activeAgent === i && <div className="mt-3 h-0.5 rounded-full bg-gradient-to-r from-[#C9A84C] to-transparent" />}
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
      <section className="mx-auto max-w-6xl px-6 py-24">
        <div className="text-center mb-14">
          <p className="text-[11px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-4">{lang === 'pt' ? 'Funcionalidades' : 'Features'}</p>
          <h2 className="mb-3 text-3xl font-bold text-white">{t('landing.features_title')}</h2>
          <p className="text-base text-[#777]">{t('landing.features_subtitle')}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div key={i} className="group rounded-xl border border-[#141414] bg-[#0C0C0C] p-6 transition-all duration-300 hover:border-[#C9A84C]/20 hover:bg-[#0E0E0E]">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-[#C9A84C]/8 group-hover:bg-[#C9A84C]/12 transition">
                <f.icon size={20} className="text-[#C9A84C]" />
              </div>
              <h3 className="mb-2 text-sm font-semibold text-white">{f.title}</h3>
              <p className="text-[13px] leading-relaxed text-[#666]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ===== PRICING ===== */}
      <section className="mx-auto max-w-5xl px-6 py-24 border-t border-[#141414]">
        <div className="text-center mb-14">
          <p className="text-[11px] font-semibold text-[#C9A84C] tracking-widest uppercase mb-4">Pricing</p>
          <h2 className="mb-3 text-3xl font-bold text-white">{t('landing.pricing_title')}</h2>
          <p className="text-base text-[#777]">{t('landing.pricing_subtitle')}</p>
        </div>
        <div className="grid gap-5 md:grid-cols-3">
          <div className="rounded-xl border border-[#141414] bg-[#0C0C0C] flex flex-col p-6 hover:border-[#1E1E1E] transition">
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_free')}</h3>
            <p className="mb-4 text-sm text-[#555]">{t('landing.plan_free_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">{t('landing.plan_free_price')}</span><span className="text-sm text-[#555]">{t('landing.plan_free_period')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#777]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2.5"><Check size={14} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_free_${k}`)}</li>)}
            </ul>
            <button onClick={() => navigate('/login?tab=signup')} className="w-full rounded-lg border border-[#1E1E1E] py-2.5 text-sm text-[#888] hover:border-[#C9A84C]/30 hover:text-white transition">{t('landing.plan_free_cta')}</button>
          </div>
          <div className="rounded-xl border border-[#C9A84C]/25 bg-[#0C0C0C] relative flex flex-col p-6 shadow-lg shadow-[#C9A84C]/3">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#C9A84C] px-4 py-1 text-[11px] font-semibold text-[#0A0A0A]">{t('landing.plan_starter_badge')}</div>
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_starter')}</h3>
            <p className="mb-4 text-sm text-[#555]">{t('landing.plan_starter_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-[#C9A84C]">{t('landing.plan_starter_price')}</span><span className="text-sm text-[#555]">{t('landing.plan_starter_period')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#777]">
              {['f1','f2','f3','f4','f5'].map(k=><li key={k} className="flex items-center gap-2.5"><Check size={14} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_starter_${k}`)}</li>)}
            </ul>
            <button className="btn-gold w-full rounded-lg py-2.5 text-sm font-semibold">{t('landing.plan_starter_cta')}</button>
          </div>
          <div className="rounded-xl border border-[#141414] bg-[#0C0C0C] flex flex-col p-6 hover:border-[#1E1E1E] transition">
            <h3 className="mb-1 text-lg font-bold text-white">{t('landing.plan_enterprise')}</h3>
            <p className="mb-4 text-sm text-[#555]">{t('landing.plan_enterprise_desc')}</p>
            <div className="mb-6"><span className="text-3xl font-bold text-white">{t('landing.plan_enterprise_price')}</span></div>
            <ul className="mb-8 flex-1 space-y-3 text-sm text-[#777]">
              {['f1','f2','f3','f4'].map(k=><li key={k} className="flex items-center gap-2.5"><Check size={14} className="text-[#C9A84C] flex-shrink-0"/>{t(`landing.plan_enterprise_${k}`)}</li>)}
            </ul>
            <button className="w-full rounded-lg border border-[#1E1E1E] py-2.5 text-sm text-[#888] hover:border-[#C9A84C]/30 hover:text-white transition">{t('landing.plan_enterprise_cta')}</button>
          </div>
        </div>
      </section>

      {/* ===== CTA ===== */}
      <section className="py-24 px-6 border-t border-[#141414] relative">
        <div className="absolute inset-0 overflow-hidden"><div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 h-[300px] w-[500px] rounded-full bg-[#C9A84C]/3 blur-[100px]" /></div>
        <div className="relative z-10 mx-auto max-w-2xl text-center">
          <h2 className="mb-4 text-3xl font-bold text-white">{lang === 'pt' ? 'Pronto para automatizar?' : 'Ready to automate?'}</h2>
          <p className="mb-8 text-base text-[#777]">{lang === 'pt' ? 'Comece gratis. Sem cartao de credito.' : 'Start free. No credit card required.'}</p>
          <button onClick={() => navigate('/login?tab=signup')} className="btn-gold rounded-xl px-10 py-4 text-base font-semibold group inline-flex items-center gap-2">
            {t('landing.hero_cta')} <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[#141414] px-6 py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 sm:flex-row">
          <img src="/logo-agentzz.png" alt="AgentZZ" className="h-7" />
          <div className="flex items-center gap-5">
            <WaIcon size={15} color="#444" /><IgIcon size={15} color="#444" /><FbIcon size={15} color="#444" /><TgIcon size={15} color="#444" />
          </div>
          <p className="text-[11px] text-[#444]">2026 AgentZZ</p>
        </div>
      </footer>
    </div>
  );
}
