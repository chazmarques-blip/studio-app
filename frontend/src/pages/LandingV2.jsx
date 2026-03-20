import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRight, Zap, Shield, BarChart3, Globe, MessageSquare, Users, Check, Sparkles,
  ChevronRight, Bot, Megaphone, TrendingUp, Layers, Send, Target, Eye, MousePointer
} from 'lucide-react';

const gold = '#C9A84C';

/* ── Social Icons ── */
const WaIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
const IgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
const FbIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
const TgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
const SmsIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12zM7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;

/* ── Animated grid ── */
function TechGrid() {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="micro-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(201,168,76,0.03)" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="grid-fade" cx="50%" cy="40%" r="60%">
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="grid-mask"><rect width="100%" height="100%" fill="url(#grid-fade)" /></mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#micro-grid)" mask="url(#grid-mask)" />
      </svg>
    </div>
  );
}

function Glow({ className = '' }) {
  return <div className={`absolute rounded-full blur-[140px] pointer-events-none ${className}`} />;
}

function Glass({ children, className = '', hover = false, gold: isGold = false }) {
  return (
    <div className={`relative rounded-2xl border backdrop-blur-xl overflow-hidden group transition-all duration-500
      ${isGold ? 'border-[#C9A84C]/15 bg-[#C9A84C]/[0.02]' : 'border-white/[0.05] bg-white/[0.015]'}
      ${hover ? 'hover:border-[#C9A84C]/20 hover:bg-white/[0.025] hover:shadow-xl hover:shadow-[#C9A84C]/[0.03]' : ''}
      ${className}`}>
      {children}
    </div>
  );
}

/* ── Live Chat ── */
function MiniChat() {
  const [msgs, setMsgs] = useState([]);
  const [typing, setTyping] = useState(false);
  const ref = useRef(null);
  const convo = [
    { from: 'user', text: 'Preciso de ajuda com meu pedido' },
    { from: 'agent', text: 'Claro! Pode me informar o numero do pedido?' },
    { from: 'user', text: '#45892' },
    { from: 'agent', text: 'Encontrei! Seu pedido esta em transito e chega amanha ate 18h.' },
  ];
  useEffect(() => {
    let i = 0, cancel = false;
    const go = () => {
      if (cancel) return;
      if (i >= convo.length) { setTimeout(() => { if (!cancel) { setMsgs([]); i = 0; go(); } }, 3000); return; }
      const m = convo[i];
      if (m.from === 'agent') {
        setTyping(true);
        setTimeout(() => { if (cancel) return; setTyping(false); setMsgs(p => [...p, m]); i++; setTimeout(go, 1500); }, 1000);
      } else { setMsgs(p => [...p, m]); i++; setTimeout(go, 1200); }
    };
    const t = setTimeout(go, 600);
    return () => { cancel = true; clearTimeout(t); };
  }, []);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [msgs, typing]);

  return (
    <div className="rounded-xl border border-white/[0.06] bg-[#0A0A0A] overflow-hidden shadow-2xl shadow-black/60">
      <div className="flex items-center gap-2.5 border-b border-white/[0.05] px-4 py-2.5 bg-white/[0.02]">
        <div className="relative">
          <div className="h-7 w-7 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#9A7B3A] flex items-center justify-center">
            <span className="text-[9px] font-bold text-[#0A0A0A]">S</span>
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400 border border-[#0A0A0A]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-semibold text-white">Sofia</p>
          <p className="text-[8px] text-emerald-400/80 font-mono">Online</p>
        </div>
        <span className="text-[8px] font-mono text-[#C9A84C]/60 border border-[#C9A84C]/10 px-1.5 py-0.5 rounded bg-[#C9A84C]/[0.04]">AI</span>
      </div>
      <div ref={ref} className="h-[160px] overflow-y-auto px-3 py-3 space-y-2" style={{ scrollbarWidth: 'none' }}>
        {msgs.map((m, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            className={`flex ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl px-3 py-2 ${
              m.from === 'user' ? 'bg-[#C9A84C]/[0.07] border border-[#C9A84C]/10' : 'bg-white/[0.03] border border-white/[0.05]'
            }`}>
              <p className="text-[10px] leading-relaxed text-[#ccc]">{m.text}</p>
            </div>
          </motion.div>
        ))}
        {typing && (
          <div className="flex justify-start">
            <div className="rounded-xl bg-white/[0.03] border border-white/[0.05] px-4 py-2.5">
              <div className="flex gap-1">{[0, 120, 240].map(d => <div key={d} className="h-1 w-1 animate-bounce rounded-full bg-[#C9A84C]/40" style={{ animationDelay: `${d}ms` }} />)}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Animation Variants ── */
const fade = {
  hidden: { opacity: 0, y: 20 },
  visible: (d = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.5, delay: d * 0.1, ease: [0.25, 0.46, 0.45, 0.94] } }),
};

/* ═══════════════════════════ MAIN COMPONENT ═══════════════════════════ */
export default function LandingV2() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language?.startsWith('pt') ? 'pt' : i18n.language?.startsWith('es') ? 'es' : 'en';
  const [billingAnnual, setBillingAnnual] = useState(true);

  const L = {
    pt: {
      badge: 'Plataforma de agentes IA',
      h1a: 'Crie agentes.', h1b: 'Lance campanhas.', h1c: 'Conecte canais.',
      sub: 'Uma plataforma para criar agentes inteligentes, gerar campanhas com IA e publicar em todas as redes sociais — sem codigo.',
      cta: 'Comece Gratis', demo: 'Ver Demo',
      s1: 'Agentes IA', s2: 'Canais', s3: 'Idiomas', s4: 'Uptime',
      how_tag: 'Como funciona', how_title: 'Do agente a conversao em 3 passos',
      step1t: 'Crie seu agente', step1d: 'Escolha entre 22+ agentes pre-configurados ou crie o seu. Defina personalidade, conhecimento e regras de atendimento.',
      step2t: 'Conecte os canais', step2d: 'WhatsApp, Instagram, Facebook, Telegram e SMS. Seus agentes atendem em todas as plataformas, 24 horas.',
      step3t: 'Lance campanhas', step3d: 'A IA cria copys, imagens e videos comerciais. Publique, acompanhe metricas e converta leads automaticamente.',
      ch_tag: 'Integracao', ch_title: 'Um inbox. ', ch_title2: 'Todos os canais.',
      ch_sub: 'Seus agentes atendem simultaneamente em todas as plataformas com uma caixa de entrada unificada.',
      ai_tag: 'AI Marketing Studio', ai_title: 'Campanhas criadas por IA', ai_title2: ' do zero ao ar.',
      ai_sub: 'Agentes especializados escrevem copy, criam imagens, produzem videos com avatar e publicam — tudo automatico.',
      ai_f1: 'Copy inteligente', ai_f1d: 'Copywriter IA adapta tom e mensagem para cada canal',
      ai_f2: 'Imagens geradas', ai_f2d: 'Design IA cria visuais optimizados por plataforma',
      ai_f3: 'Videos com avatar', ai_f3d: 'Apresentador 3D com lip-sync e narração profissional',
      ai_f4: 'Publicacao multi-canal', ai_f4d: 'Variantes automaticas para Reels, TikTok e YouTube',
      feat_tag: 'Recursos', feat_title: 'Tudo que voce precisa',
      feat_sub: 'Ferramentas poderosas para automatizar o atendimento e marketing do seu negocio.',
      cta_title: 'Pronto para automatizar seu negocio?', cta_sub: 'Comece gratis. Sem cartao de credito. Configure em 5 minutos.',
    },
    en: {
      badge: 'AI Agent Platform',
      h1a: 'Create agents.', h1b: 'Launch campaigns.', h1c: 'Connect channels.',
      sub: 'One platform to create intelligent agents, generate AI campaigns, and publish across all social channels — no code needed.',
      cta: 'Start Free', demo: 'Watch Demo',
      s1: 'AI Agents', s2: 'Channels', s3: 'Languages', s4: 'Uptime',
      how_tag: 'How it works', how_title: 'From agent to conversion in 3 steps',
      step1t: 'Create your agent', step1d: 'Choose from 22+ pre-configured agents or build yours. Define personality, knowledge, and rules.',
      step2t: 'Connect channels', step2d: 'WhatsApp, Instagram, Facebook, Telegram and SMS. Your agents serve on every platform, 24/7.',
      step3t: 'Launch campaigns', step3d: 'AI creates copy, images, and commercial videos. Publish, track metrics, and convert leads automatically.',
      ch_tag: 'Integration', ch_title: 'One inbox. ', ch_title2: 'Every channel.',
      ch_sub: 'Your agents serve simultaneously across every platform with a unified inbox.',
      ai_tag: 'AI Marketing Studio', ai_title: 'AI-crafted campaigns', ai_title2: ' from zero to live.',
      ai_sub: 'Specialized agents write copy, create images, produce avatar videos, and publish — fully automatic.',
      ai_f1: 'Smart copy', ai_f1d: 'AI copywriter adapts tone and message per channel',
      ai_f2: 'Generated images', ai_f2d: 'AI designer creates platform-optimized visuals',
      ai_f3: 'Avatar videos', ai_f3d: '3D presenter with lip-sync and professional narration',
      ai_f4: 'Multi-channel publish', ai_f4d: 'Auto variants for Reels, TikTok, and YouTube',
      feat_tag: 'Features', feat_title: 'Everything you need',
      feat_sub: 'Powerful tools to automate customer service and marketing.',
      cta_title: 'Ready to automate your business?', cta_sub: 'Start free. No credit card. Set up in 5 minutes.',
    },
    es: {
      badge: 'Plataforma de agentes IA',
      h1a: 'Crea agentes.', h1b: 'Lanza campanas.', h1c: 'Conecta canales.',
      sub: 'Una plataforma para crear agentes inteligentes, generar campanas con IA y publicar en todas las redes sociales — sin codigo.',
      cta: 'Empieza Gratis', demo: 'Ver Demo',
      s1: 'Agentes IA', s2: 'Canales', s3: 'Idiomas', s4: 'Uptime',
      how_tag: 'Como funciona', how_title: 'Del agente a la conversion en 3 pasos',
      step1t: 'Crea tu agente', step1d: 'Elige entre 22+ agentes preconfigurados o crea el tuyo.',
      step2t: 'Conecta canales', step2d: 'WhatsApp, Instagram, Facebook, Telegram y SMS.',
      step3t: 'Lanza campanas', step3d: 'La IA crea copys, imagenes y videos. Publica y convierte automaticamente.',
      ch_tag: 'Integracion', ch_title: 'Un inbox. ', ch_title2: 'Todos los canales.',
      ch_sub: 'Tus agentes atienden simultaneamente en todas las plataformas.',
      ai_tag: 'AI Marketing Studio', ai_title: 'Campanas creadas por IA', ai_title2: ' de cero al aire.',
      ai_sub: 'Agentes especializados escriben copy, crean imagenes, producen videos y publican.',
      ai_f1: 'Copy inteligente', ai_f1d: 'Copywriter IA adapta tono y mensaje',
      ai_f2: 'Imagenes generadas', ai_f2d: 'Diseno IA crea visuales optimizados',
      ai_f3: 'Videos con avatar', ai_f3d: 'Presentador 3D con lip-sync profesional',
      ai_f4: 'Publicacion multicanal', ai_f4d: 'Variantes auto para Reels, TikTok y YouTube',
      feat_tag: 'Recursos', feat_title: 'Todo lo que necesitas',
      feat_sub: 'Herramientas poderosas para automatizar tu negocio.',
      cta_title: 'Listo para automatizar?', cta_sub: 'Empieza gratis. Sin tarjeta.',
    },
  };
  const l = L[lang] || L.en;

  const steps = [
    { num: '01', icon: Bot, title: l.step1t, desc: l.step1d, accent: 'from-[#C9A84C]/20 to-[#C9A84C]/5' },
    { num: '02', icon: Globe, title: l.step2t, desc: l.step2d, accent: 'from-[#C9A84C]/15 to-[#C9A84C]/5' },
    { num: '03', icon: Megaphone, title: l.step3t, desc: l.step3d, accent: 'from-[#C9A84C]/10 to-[#C9A84C]/5' },
  ];

  const channels = [
    { Icon: WaIcon, name: 'WhatsApp', status: 'API Business' },
    { Icon: IgIcon, name: 'Instagram', status: 'Direct Messages' },
    { Icon: FbIcon, name: 'Messenger', status: 'Pages' },
    { Icon: TgIcon, name: 'Telegram', status: 'Bots' },
    { Icon: SmsIcon, name: 'SMS', status: 'Twilio' },
  ];

  const features = [
    { icon: Users, title: t('landing.feat_agents'), desc: t('landing.feat_agents_desc') },
    { icon: MessageSquare, title: t('landing.feat_omni'), desc: t('landing.feat_omni_desc') },
    { icon: Zap, title: t('landing.feat_multi'), desc: t('landing.feat_multi_desc') },
    { icon: BarChart3, title: t('landing.feat_analytics'), desc: t('landing.feat_analytics_desc') },
    { icon: Globe, title: t('landing.feat_lang'), desc: t('landing.feat_lang_desc') },
    { icon: Shield, title: t('landing.feat_crm'), desc: t('landing.feat_crm_desc') },
  ];

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden selection:bg-[#C9A84C]/20 selection:text-[#C9A84C]">

      {/* ═══ HEADER ═══ */}
      <header className="fixed top-0 inset-x-0 z-50 border-b border-white/[0.04] bg-[#060606]/70 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <img src="/logo-agentzz.png" alt="Agents" className="h-7" />
          <div className="flex items-center gap-2.5">
            <button onClick={() => navigate('/login')}
              className="px-4 py-2 text-[13px] text-[#777] hover:text-white transition rounded-lg border border-transparent hover:border-white/[0.08]">
              {t('landing.signin')}
            </button>
            <button onClick={() => navigate('/login?tab=signup')}
              className="btn-gold rounded-lg px-5 py-2 text-[13px] font-semibold">
              {l.cta}
            </button>
          </div>
        </div>
      </header>

      {/* ═══ HERO ═══ */}
      <section className="relative pt-28 pb-24 px-5 overflow-hidden">
        <TechGrid />
        <Glow className="h-[500px] w-[600px] -top-32 left-[15%] bg-[#C9A84C]/[0.03]" />
        <Glow className="h-[300px] w-[400px] bottom-0 right-[5%] bg-[#C9A84C]/[0.02]" />

        <div className="relative z-10 mx-auto max-w-6xl">
          {/* Badge */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={0}
            className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#C9A84C]/12 bg-[#C9A84C]/[0.04] px-4 py-1.5">
              <Zap size={11} className="text-[#C9A84C]" />
              <span className="text-[10px] font-mono font-medium text-[#C9A84C]/80 tracking-wider uppercase">{l.badge}</span>
            </div>
          </motion.div>

          {/* Title */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={1}
            className="text-center max-w-3xl mx-auto mb-6">
            <h1 className="text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl lg:text-[3.5rem]">
              <span className="text-white">{l.h1a}</span>{' '}
              <span className="bg-gradient-to-r from-[#C9A84C] to-[#E0C76B] bg-clip-text text-transparent">{l.h1b}</span>{' '}
              <span className="text-white">{l.h1c}</span>
            </h1>
          </motion.div>

          <motion.p initial="hidden" animate="visible" variants={fade} custom={2}
            className="text-center text-[15px] text-[#666] leading-relaxed max-w-xl mx-auto mb-10">
            {l.sub}
          </motion.p>

          {/* CTAs */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={3}
            className="flex justify-center gap-3 mb-16">
            <button onClick={() => navigate('/login?tab=signup')}
              className="btn-gold flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-semibold group shadow-lg shadow-[#C9A84C]/10">
              {l.cta} <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button className="flex items-center gap-2 rounded-xl border border-white/[0.07] bg-white/[0.02] px-7 py-3 text-sm text-[#888] hover:text-white hover:border-white/[0.12] transition-all">
              {l.demo}
            </button>
          </motion.div>

          {/* Hero Visual: 3-panel showcase */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={4}
            className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto">

            {/* Panel 1: Agent Card */}
            <Glass hover className="p-5">
              <div className="flex items-center gap-3 mb-4">
                <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center border border-[#C9A84C]/10">
                  <Bot size={16} className="text-[#C9A84C]" />
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-white">Sofia</p>
                  <p className="text-[9px] text-[#555] font-mono">Sales Agent</p>
                </div>
                <div className="ml-auto h-2 w-2 rounded-full bg-emerald-400" />
              </div>
              <div className="space-y-2 mb-3">
                {['WhatsApp', 'Instagram', 'Telegram'].map(ch => (
                  <div key={ch} className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]/60" />
                    <span className="text-[9px] text-[#888] font-mono">{ch}</span>
                    <span className="ml-auto text-[8px] text-emerald-400/70 font-mono">Active</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-1.5 text-[9px] text-[#C9A84C]/60 font-mono">
                <Sparkles size={9} /> 847 conversations today
              </div>
            </Glass>

            {/* Panel 2: Live Chat */}
            <div className="md:translate-y-[-16px]">
              <MiniChat />
            </div>

            {/* Panel 3: Campaign Card */}
            <Glass hover className="p-5">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center border border-[#C9A84C]/10">
                  <Megaphone size={16} className="text-[#C9A84C]" />
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-white">Campaign</p>
                  <p className="text-[9px] text-[#555] font-mono">AI Marketing Studio</p>
                </div>
              </div>
              <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-3 mb-3">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[9px] text-[#888] font-mono">Impressions</span>
                  <span className="text-[9px] text-emerald-400 font-mono">+24%</span>
                </div>
                <div className="flex gap-0.5 items-end h-8">
                  {[30, 45, 38, 52, 48, 65, 58, 72, 68, 85, 78, 92].map((h, i) => (
                    <div key={i} className="flex-1 rounded-sm bg-gradient-to-t from-[#C9A84C]/30 to-[#C9A84C]/10"
                      style={{ height: `${h}%` }} />
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2 text-center">
                  <p className="text-[11px] font-bold text-white font-mono">12.4k</p>
                  <p className="text-[8px] text-[#555] font-mono">Leads</p>
                </div>
                <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2 text-center">
                  <p className="text-[11px] font-bold text-[#C9A84C] font-mono">4.2%</p>
                  <p className="text-[8px] text-[#555] font-mono">Conv. Rate</p>
                </div>
              </div>
            </Glass>
          </motion.div>

          {/* Stats bar */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={5}
            className="flex justify-center gap-10 lg:gap-16 mt-16">
            {[
              { v: '22+', l: l.s1 }, { v: '5', l: l.s2 }, { v: '3', l: l.s3 }, { v: '99.9%', l: l.s4 }
            ].map((s, i) => (
              <div key={i} className="text-center">
                <p className="text-xl font-bold font-mono text-white lg:text-2xl">{s.v}</p>
                <p className="text-[9px] text-[#555] tracking-widest uppercase mt-0.5 font-mono">{s.l}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS — 3 Steps ═══ */}
      <section className="py-24 px-5 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080808] to-transparent" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={fade}
            className="text-center mb-16">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-3">{l.how_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{l.how_title}</h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {steps.map((s, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i}>
                <Glass hover className="p-6 h-full relative">
                  {/* Step number */}
                  <div className="absolute top-4 right-4 text-[28px] font-mono font-black text-white/[0.03]">{s.num}</div>
                  {/* Connector line */}
                  {i < 2 && <div className="hidden md:block absolute top-1/2 -right-3 w-6 border-t border-dashed border-[#C9A84C]/15" />}
                  <div className={`h-12 w-12 rounded-xl bg-gradient-to-br ${s.accent} flex items-center justify-center mb-5 border border-[#C9A84C]/10`}>
                    <s.icon size={20} className="text-[#C9A84C]" />
                  </div>
                  <h3 className="text-base font-semibold text-white mb-2">{s.title}</h3>
                  <p className="text-[12px] text-[#555] leading-relaxed">{s.desc}</p>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CHANNELS ═══ */}
      <section className="py-24 px-5 relative">
        <TechGrid />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={fade}
            className="text-center mb-14">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-3">{l.ch_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">
              {l.ch_title}<span className="text-[#C9A84C]">{l.ch_title2}</span>
            </h2>
            <p className="text-sm text-[#555] max-w-md mx-auto mt-3">{l.ch_sub}</p>
          </motion.div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {channels.map((ch, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.5}>
                <Glass hover className="p-5 text-center">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#C9A84C]/[0.05] mx-auto mb-3 border border-[#C9A84C]/[0.08]">
                    <ch.Icon size={20} color={gold} />
                  </div>
                  <p className="text-[12px] font-semibold text-white mb-0.5">{ch.name}</p>
                  <p className="text-[9px] text-[#555] font-mono">{ch.status}</p>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ AI MARKETING STUDIO ═══ */}
      <section className="py-24 px-5 relative overflow-hidden">
        <Glow className="h-[400px] w-[500px] top-[10%] left-[-100px] bg-[#C9A84C]/[0.03]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={fade}
            className="text-center mb-14">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-3">{l.ai_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">
              {l.ai_title}<span className="text-[#C9A84C]">{l.ai_title2}</span>
            </h2>
            <p className="text-sm text-[#555] max-w-lg mx-auto mt-3">{l.ai_sub}</p>
          </motion.div>

          <div className="grid sm:grid-cols-2 gap-4">
            {[
              { icon: MessageSquare, t: l.ai_f1, d: l.ai_f1d },
              { icon: Eye, t: l.ai_f2, d: l.ai_f2d },
              { icon: Users, t: l.ai_f3, d: l.ai_f3d },
              { icon: Send, t: l.ai_f4, d: l.ai_f4d },
            ].map((f, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.5}>
                <Glass hover className="p-5 flex gap-4 items-start">
                  <div className="h-10 w-10 rounded-lg bg-[#C9A84C]/[0.06] flex items-center justify-center flex-shrink-0 border border-[#C9A84C]/[0.08]">
                    <f.icon size={16} className="text-[#C9A84C]" />
                  </div>
                  <div>
                    <h3 className="text-[13px] font-semibold text-white mb-1">{f.t}</h3>
                    <p className="text-[11px] text-[#555] leading-relaxed">{f.d}</p>
                  </div>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ FEATURES GRID ═══ */}
      <section className="py-24 px-5 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080808] to-transparent" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={fade}
            className="text-center mb-14">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-3">{l.feat_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{l.feat_title}</h2>
            <p className="text-sm text-[#555] mt-3">{l.feat_sub}</p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((f, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.3}>
                <Glass hover className="p-5 h-full">
                  <div className="h-10 w-10 rounded-lg bg-[#C9A84C]/[0.06] flex items-center justify-center mb-4 border border-[#C9A84C]/[0.08]">
                    <f.icon size={16} className="text-[#C9A84C]" />
                  </div>
                  <h3 className="text-[13px] font-semibold text-white mb-1.5">{f.title}</h3>
                  <p className="text-[11px] text-[#555] leading-relaxed">{f.desc}</p>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ PRICING ═══ */}
      <section className="py-24 px-5 relative">
        <TechGrid />
        <Glow className="h-[400px] w-[500px] top-[30%] left-[30%] bg-[#C9A84C]/[0.02]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-60px' }} variants={fade}
            className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-3">Pricing</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{t('landing.pricing_title')}</h2>
            <p className="text-sm text-[#555] mt-3 mb-6">{t('landing.pricing_subtitle')}</p>
            <div className="inline-flex items-center gap-0.5 rounded-full border border-white/[0.06] bg-white/[0.02] p-0.5">
              <button onClick={() => setBillingAnnual(true)}
                className={`rounded-full px-5 py-2 text-[11px] font-mono font-medium transition-all ${
                  billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A] shadow-lg shadow-[#C9A84C]/15' : 'text-[#666] hover:text-white'}`}>
                {t('landing.billing_annual')} <span className="text-[9px] opacity-70 ml-0.5">{t('landing.billing_save')}</span>
              </button>
              <button onClick={() => setBillingAnnual(false)}
                className={`rounded-full px-5 py-2 text-[11px] font-mono font-medium transition-all ${
                  !billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A] shadow-lg shadow-[#C9A84C]/15' : 'text-[#666] hover:text-white'}`}>
                {t('landing.billing_monthly')}
              </button>
            </div>
          </motion.div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { name: t('landing.plan_free'), desc: t('landing.plan_free_desc'), price: t('landing.plan_free_price'), period: t('landing.plan_free_period'),
                feats: ['f1','f2','f3','f4'].map(k => t(`landing.plan_free_${k}`)), cta: t('landing.plan_free_cta'), note: t('landing.plan_free_no_card'), pro: false, badge: null },
              { name: t('landing.plan_starter'), desc: t('landing.plan_starter_desc'), price: t('landing.plan_starter_price'), period: t('landing.plan_starter_period'),
                feats: ['f1','f2','f3','f4','f5'].map(k => t(`landing.plan_starter_${k}`)), cta: t('landing.plan_starter_cta'), note: null, pro: false, badge: t('landing.plan_starter_badge') },
              { name: t('landing.plan_pro'), desc: t('landing.plan_pro_desc'),
                price: billingAnnual ? t('landing.plan_pro_price_annual') : t('landing.plan_pro_price_monthly'),
                period: billingAnnual ? t('landing.plan_pro_period_annual') : t('landing.plan_pro_period_monthly'),
                feats: ['f1','f2','f3','f4','f5'].map(k => t(`landing.plan_pro_${k}`)), cta: t('landing.plan_pro_cta'), note: null, pro: true, badge: t('landing.plan_pro_badge') },
              { name: t('landing.plan_enterprise'), desc: t('landing.plan_enterprise_desc'),
                price: billingAnnual ? t('landing.plan_enterprise_price_annual') : t('landing.plan_enterprise_price_monthly'),
                period: billingAnnual ? t('landing.plan_enterprise_period_annual') : t('landing.plan_enterprise_period_monthly'),
                feats: ['f1','f2','f3','f4','f5','f6','f7','f8'].map(k => t(`landing.plan_enterprise_${k}`)), cta: t('landing.plan_enterprise_cta'), note: null, pro: false, badge: t('landing.plan_enterprise_badge') },
            ].map((plan, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i}>
                {plan.pro ? (
                  <div className="relative rounded-2xl p-px bg-gradient-to-b from-[#C9A84C]/30 via-[#C9A84C]/10 to-transparent h-full">
                    <div className="rounded-2xl bg-[#090909] h-full flex flex-col p-5 relative overflow-hidden">
                      <div className="absolute inset-0 bg-gradient-to-b from-[#C9A84C]/[0.03] to-transparent pointer-events-none" />
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 z-10 rounded-full bg-[#C9A84C] px-3 py-0.5 text-[9px] font-mono font-bold text-[#0A0A0A] shadow-lg shadow-[#C9A84C]/20">{plan.badge}</div>
                      <div className="relative z-10 flex flex-col h-full">
                        <h3 className="text-sm font-bold text-white mb-0.5">{plan.name}</h3>
                        <p className="text-[10px] text-[#555] font-mono mb-3">{plan.desc}</p>
                        <div className="mb-4"><span className="text-2xl font-bold text-white font-mono">{plan.price}</span><span className="text-[10px] text-[#555]">{plan.period}</span></div>
                        <ul className="flex-1 space-y-2 mb-5">{plan.feats.map((f, j) => <li key={j} className="flex items-start gap-2 text-[11px] text-[#666]"><Check size={11} className="text-[#C9A84C] mt-0.5 flex-shrink-0" />{f}</li>)}</ul>
                        <button className="btn-gold w-full rounded-xl py-2.5 text-[12px] font-semibold">{plan.cta}</button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <Glass hover className="flex flex-col p-5 h-full relative">
                    {plan.badge && <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 rounded-full border border-[#C9A84C]/15 bg-[#060606] px-3 py-0.5 text-[9px] font-mono text-[#C9A84C]">{plan.badge}</div>}
                    <h3 className="text-sm font-bold text-white mb-0.5">{plan.name}</h3>
                    <p className="text-[10px] text-[#555] font-mono mb-3">{plan.desc}</p>
                    <div className="mb-4"><span className="text-2xl font-bold text-white font-mono">{plan.price}</span><span className="text-[10px] text-[#555]">{plan.period}</span></div>
                    <ul className="flex-1 space-y-2 mb-5">{plan.feats.map((f, j) => <li key={j} className="flex items-start gap-2 text-[11px] text-[#666]"><Check size={11} className="text-[#C9A84C] mt-0.5 flex-shrink-0" />{f}</li>)}</ul>
                    {plan.note && <p className="text-center text-[9px] text-[#555] font-mono mb-2">{plan.note}</p>}
                    <button className="btn-gold w-full rounded-xl py-2.5 text-[12px] font-semibold">{plan.cta}</button>
                  </Glass>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="py-28 px-5 relative">
        <Glow className="h-[200px] w-[350px] top-[40%] left-[40%] bg-[#C9A84C]/[0.03]" />
        <div className="relative z-10 mx-auto max-w-2xl text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade}>
            <h2 className="text-3xl font-bold text-white mb-4 sm:text-4xl lg:text-5xl leading-tight">{l.cta_title}</h2>
            <p className="text-[15px] text-[#555] mb-8">{l.cta_sub}</p>
            <button onClick={() => navigate('/login?tab=signup')}
              className="btn-gold rounded-xl px-10 py-3.5 text-sm font-semibold inline-flex items-center gap-2.5 group shadow-lg shadow-[#C9A84C]/10 hover:shadow-[#C9A84C]/25 transition-shadow">
              {l.cta} <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-white/[0.04] px-5 py-6">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 sm:flex-row">
          <img src="/logo-agentzz.png" alt="Agents" className="h-5 opacity-60" />
          <div className="flex items-center gap-4">
            <WaIcon size={12} color="#444" /><IgIcon size={12} color="#444" /><FbIcon size={12} color="#444" /><TgIcon size={12} color="#444" />
          </div>
          <p className="text-[9px] text-[#444] font-mono">2026 Agents. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
