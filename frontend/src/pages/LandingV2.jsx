import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRight, Zap, Shield, BarChart3, Globe, MessageSquare, Users, Check, Sparkles,
  ChevronRight, Bot, Megaphone, TrendingUp, Layers, Send, Target, Eye,
  Settings, Brain, Languages, Clock, Sliders, Star, Play, Volume2, Image, Video,
  Quote, Heart, ThumbsUp, BarChart2
} from 'lucide-react';

const gold = '#C9A84C';

const AVATARS = {
  Sarah: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/4d686b82885d8f4f90f35055251245df4e68fbfb5f3c8b9fc5b6296511151a5a.png",
  Emily: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7cf1f980e31d97ccb986f55c090c7303614a2952d6ca744b7ef14418e2ba6a4a.png",
  Sophia: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/7f7b2e7ab2562fa5619f6e4f6546512e49d14080b6600d8874ae7ab6c99d109a.png",
  Carlos: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/3f76d9a72b1b7c775b44da50a077ee6f03cdbb1232efcfd607bfabc6eb3185af.png",
  James: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/88cfe39c6a5319218155267be07401ca74245e2076c5805a10e5c4aa82e5da90.png",
};

const CAMPAIGN_IMAGES = {
  feed: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/49ed7b5af6869971dee9f2dcd5a7164df842cb17290129ae0565882fc3b6b2e5.png",
  story: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/a90b958a7a2e499ced4c2f685c9fc0a1461e59c6243de42f0b617b065f800a12.png",
  wide: "https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/dca8ff31dfd717773cb8e6e891bd6e6c76851c74972a896b72cf65ed7f8e18ea.png",
};

const TESTIMONIAL_PHOTOS = [
  "https://images.pexels.com/photos/5920775/pexels-photo-5920775.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
  "https://images.unsplash.com/photo-1770627000564-3feb36aecbcd?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHw0fHxidXNpbmVzcyUyMG93bmVyJTIwZW50cmVwcmVuZXVyJTIwcG9ydHJhaXQlMjBwcm9mZXNzaW9uYWx8ZW58MHx8fHwxNzczOTc4Mzc2fDA&ixlib=rb-4.1.0&q=85",
  "https://images.unsplash.com/photo-1758887261865-a2b89c0f7ac5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxidXNpbmVzcyUyMG93bmVyJTIwZW50cmVwcmVuZXVyJTIwcG9ydHJhaXQlMjBwcm9mZXNzaW9uYWx8ZW58MHx8fHwxNzczOTc4Mzc2fDA&ixlib=rb-4.1.0&q=85",
];

/* ── Social Icons ── */
const WaIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
const IgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
const FbIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
const TgIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
const SmsIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H5.17L4 17.17V4h16v12zM7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;

/* ── Background ── */
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
function Glass({ children, className = '', hover = false }) {
  return (
    <div className={`relative rounded-2xl border backdrop-blur-xl overflow-hidden transition-all duration-500
      border-white/[0.06] bg-white/[0.015]
      ${hover ? 'hover:border-[#C9A84C]/20 hover:bg-white/[0.03] hover:shadow-xl hover:shadow-[#C9A84C]/[0.04]' : ''}
      ${className}`}>
      {children}
    </div>
  );
}

/* ── Live Chat with Agent Avatar ── */
/* TikTok icon */
const TkIcon = ({ size = 28, color = gold }) => <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.53v-3.4a4.85 4.85 0 01-.81-.21z"/></svg>;

/* ── Multi-channel Chat rotating agents ── */
const CHAT_CHANNELS = [
  {
    agent: 'Sarah', avatar: AVATARS.Sarah, channel: 'WhatsApp', color: '#25D366',
    Icon: WaIcon,
    convo: [
      { from: 'user', text: 'Preciso agendar uma consulta para amanha' },
      { from: 'agent', text: 'Claro! Vou verificar os horarios disponiveis.' },
      { from: 'agent', text: 'Manha ou tarde?' },
      { from: 'user', text: 'Pela manha' },
      { from: 'agent', text: 'Perfeito! Tenho 9h ou 10h30 — qual prefere?' },
      { from: 'user', text: '9h por favor!' },
      { from: 'agent', text: 'Agendado para amanha as 9h! Confirmacao enviada por WhatsApp.' },
      { from: 'user', text: 'Muito obrigado!' },
      { from: 'agent', text: 'Disponha! Qualquer duvida, estou aqui 24h.' },
    ]
  },
  {
    agent: 'Carlos', avatar: AVATARS.Carlos, channel: 'Instagram', color: '#E1306C',
    Icon: IgIcon,
    convo: [
      { from: 'user', text: 'Oi, meu pedido nao chegou ainda' },
      { from: 'agent', text: 'Ola! Sinto muito pelo inconveniente.' },
      { from: 'agent', text: 'Qual o numero do seu pedido?' },
      { from: 'user', text: '#45892' },
      { from: 'agent', text: 'Encontrei! Pedido #45892 saiu para entrega hoje as 14h.' },
      { from: 'user', text: 'Tem como rastrear?' },
      { from: 'agent', text: 'Claro! Aqui o link de rastreio: trk.io/45892' },
      { from: 'user', text: 'Otimo, obrigado!' },
      { from: 'agent', text: 'Precisando, estou aqui!' },
    ]
  },
  {
    agent: 'Sophia', avatar: AVATARS.Sophia, channel: 'Messenger', color: '#0084FF',
    Icon: FbIcon,
    convo: [
      { from: 'user', text: 'Quais planos voces tem?' },
      { from: 'agent', text: 'Temos 3 planos! Free, Pro e Enterprise.' },
      { from: 'user', text: 'Qual a diferenca do Pro?' },
      { from: 'agent', text: 'O Pro inclui agentes ilimitados, AI Studio e suporte prioritario!' },
      { from: 'user', text: 'E o Enterprise?' },
      { from: 'agent', text: 'Enterprise adiciona gerador de campanhas com IA, video e avatar.' },
      { from: 'user', text: 'Quero testar o Pro' },
      { from: 'agent', text: 'Criado! 14 dias gratis. Acesse seu painel agora.' },
    ]
  },
  {
    agent: 'Emily', avatar: AVATARS.Emily, channel: 'Telegram', color: '#26A5E4',
    Icon: TgIcon,
    convo: [
      { from: 'user', text: 'Como funciona a integracao com WhatsApp?' },
      { from: 'agent', text: 'Basta conectar sua conta Business API!' },
      { from: 'user', text: 'E demora muito?' },
      { from: 'agent', text: 'Menos de 5 minutos! Posso te guiar agora.' },
      { from: 'user', text: 'Vamos la!' },
      { from: 'agent', text: 'Perfeito! Acesse Configuracoes > Canais > WhatsApp.' },
      { from: 'user', text: 'Conectou! E agora?' },
      { from: 'agent', text: 'Pronto! Seu agente ja esta ativo no WhatsApp respondendo clientes.' },
    ]
  },
];

function AgentChat() {
  const [msgs, setMsgs] = useState([]);
  const [typing, setTyping] = useState(false);
  const [channelIdx, setChannelIdx] = useState(0);
  const ref = useRef(null);
  const ch = CHAT_CHANNELS[channelIdx];

  useEffect(() => {
    let i = 0, cancel = false;
    setMsgs([]); setTyping(false);
    const convo = ch.convo;
    const go = () => {
      if (cancel) return;
      if (i >= convo.length) {
        setTimeout(() => {
          if (cancel) return;
          setChannelIdx(p => (p + 1) % CHAT_CHANNELS.length);
        }, 2500);
        return;
      }
      const m = convo[i];
      if (m.from === 'agent') {
        setTyping(true);
        setTimeout(() => { if (cancel) return; setTyping(false); setMsgs(p => [...p, m]); i++; setTimeout(go, 1200); }, 1000);
      } else { setMsgs(p => [...p, m]); i++; setTimeout(go, 900); }
    };
    const t = setTimeout(go, 500);
    return () => { cancel = true; clearTimeout(t); };
  }, [channelIdx]);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [msgs, typing]);

  return (
    <div className="rounded-2xl border border-white/[0.07] bg-[#0A0A0A] overflow-hidden shadow-2xl shadow-black/60 flex flex-col h-full">
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-4 py-2.5 bg-white/[0.02]">
        <AnimatePresence mode="wait">
          <motion.div key={channelIdx} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="flex items-center gap-3 flex-1 min-w-0">
            <div className="relative">
              <div className="h-8 w-8 rounded-full overflow-hidden ring-2" style={{ borderColor: ch.color + '33' }}>
                <img src={ch.avatar} alt={ch.agent} className="h-full w-full object-cover" />
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full border-2 border-[#0A0A0A]" style={{ backgroundColor: ch.color }} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-semibold text-white">{ch.agent}</p>
              <p className="text-[8px] font-mono" style={{ color: ch.color }}>{ch.channel}</p>
            </div>
          </motion.div>
        </AnimatePresence>
        <ch.Icon size={14} color={ch.color} />
      </div>
      {/* Channel indicator dots */}
      <div className="flex justify-center gap-1.5 py-1.5 bg-white/[0.01]">
        {CHAT_CHANNELS.map((_, i) => (
          <div key={i} className={`h-1 rounded-full transition-all duration-300 ${i === channelIdx ? 'w-4 bg-[#C9A84C]/60' : 'w-1 bg-white/[0.08]'}`} />
        ))}
      </div>
      <div ref={ref} className="flex-1 overflow-y-auto px-3 py-2 space-y-2" style={{ scrollbarWidth: 'none' }}>
        <AnimatePresence mode="wait">
          <motion.div key={channelIdx} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {msgs.map((m, i) => (
              <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
                className={`flex gap-1.5 mb-2 ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.from === 'agent' && (
                  <div className="h-5 w-5 rounded-full overflow-hidden flex-shrink-0 mt-1 ring-1 ring-[#C9A84C]/10">
                    <img src={ch.avatar} alt="" className="h-full w-full object-cover" />
                  </div>
                )}
                <div className={`max-w-[78%] rounded-xl px-2.5 py-1.5 ${
                  m.from === 'user' ? 'bg-[#C9A84C]/[0.08] border border-[#C9A84C]/12' : 'bg-white/[0.03] border border-white/[0.06]'
                }`}>
                  <p className="text-[9px] leading-relaxed text-[#ccc]">{m.text}</p>
                </div>
              </motion.div>
            ))}
            {typing && (
              <div className="flex gap-1.5 justify-start">
                <div className="h-5 w-5 rounded-full overflow-hidden flex-shrink-0 mt-1 ring-1 ring-[#C9A84C]/10">
                  <img src={ch.avatar} alt="" className="h-full w-full object-cover" />
                </div>
                <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] px-3 py-2">
                  <div className="flex gap-1">{[0, 120, 240].map(d => <div key={d} className="h-1 w-1 animate-bounce rounded-full bg-[#C9A84C]/40" style={{ animationDelay: `${d}ms` }} />)}</div>
                </div>
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}

/* ── Campaign Demo Showcase ── */
function CampaignDemo({ lang }) {
  const [demoStep, setDemoStep] = useState(0);
  const [typedText, setTypedText] = useState('');
  const [autoPlay, setAutoPlay] = useState(true);

  const L = {
    pt: {
      tag: 'DEMO AO VIVO', title: 'Veja uma campanha sendo criada',
      sub: 'Acompanhe o processo completo da IA criando uma campanha real para a marca AgentZZ.',
      steps: [
        { label: 'Brief', title: 'Briefing da campanha', desc: 'A IA recebe o objetivo e analisa a marca.' },
        { label: 'Copy', title: 'Textos gerados pela IA', desc: 'Copywriter IA cria textos para cada formato.' },
        { label: 'Design', title: 'Imagens criadas', desc: 'Designer IA gera visuais para Feed, Story e Banner.' },
        { label: 'Video', title: 'Video com avatar', desc: 'Apresentador IA com lip-sync e narracao.' },
        { label: 'Resultado', title: 'Campanha pronta!', desc: 'Todos os formatos prontos para publicacao.' },
      ],
      brief_brand: 'Marca:', brief_goal: 'Objetivo:', brief_goal_v: 'Lancamento da plataforma AgentZZ — mostrar que qualquer negocio pode ter agentes IA atendendo 24h em todos os canais.',
      brief_tone: 'Tom:', brief_tone_v: 'Premium, tecnologico, confiavel',
      brief_channels: 'Canais:', brief_channels_v: 'Instagram Feed, Story, Facebook, WhatsApp',
      copy_feed: 'Seus clientes nunca mais esperam. Com AgentZZ, seus agentes IA atendem 24h no WhatsApp, Instagram e Telegram. Configure em 5 minutos.',
      copy_story: 'Atendimento 24h. Sem codigo. Sem espera. Comece gratis agora.',
      copy_cta: 'Comece Gratis',
      video_title: 'Video Comercial — AgentZZ', video_dur: '0:30', video_res: '1080p', video_avatar: 'James — Apresentador IA', video_voice: 'Narracao profissional PT-BR',
      result_title: 'Campanha AgentZZ — Pronta', result_formats: '4 formatos gerados', result_ready: 'Pronto para publicar',
    },
    en: {
      tag: 'LIVE DEMO', title: 'Watch a campaign being created',
      sub: 'Follow the complete AI process creating a real campaign for the AgentZZ brand.',
      steps: [
        { label: 'Brief', title: 'Campaign briefing', desc: 'AI receives the goal and analyzes the brand.' },
        { label: 'Copy', title: 'AI-generated copy', desc: 'AI copywriter creates text for each format.' },
        { label: 'Design', title: 'Images created', desc: 'AI designer generates visuals for Feed, Story, and Banner.' },
        { label: 'Video', title: 'Avatar video', desc: 'AI presenter with lip-sync and narration.' },
        { label: 'Result', title: 'Campaign ready!', desc: 'All formats ready for publishing.' },
      ],
      brief_brand: 'Brand:', brief_goal: 'Goal:', brief_goal_v: 'AgentZZ platform launch — show any business can have AI agents serving 24/7 on all channels.',
      brief_tone: 'Tone:', brief_tone_v: 'Premium, technological, trustworthy',
      brief_channels: 'Channels:', brief_channels_v: 'Instagram Feed, Story, Facebook, WhatsApp',
      copy_feed: 'Your customers never wait again. With AgentZZ, your AI agents serve 24/7 on WhatsApp, Instagram, and Telegram. Set up in 5 minutes.',
      copy_story: '24/7 support. No code. No waiting. Start free now.',
      copy_cta: 'Start Free',
      video_title: 'Commercial Video — AgentZZ', video_dur: '0:30', video_res: '1080p', video_avatar: 'James — AI Presenter', video_voice: 'Professional narration EN',
      result_title: 'AgentZZ Campaign — Ready', result_formats: '4 formats generated', result_ready: 'Ready to publish',
    },
    es: {
      tag: 'DEMO EN VIVO', title: 'Mira una campana siendo creada',
      sub: 'Acompana el proceso completo de IA creando una campana real para AgentZZ.',
      steps: [
        { label: 'Brief', title: 'Briefing de campana', desc: 'La IA recibe el objetivo y analiza la marca.' },
        { label: 'Copy', title: 'Textos generados', desc: 'Copywriter IA crea textos para cada formato.' },
        { label: 'Diseno', title: 'Imagenes creadas', desc: 'Designer IA genera visuales para Feed, Story y Banner.' },
        { label: 'Video', title: 'Video con avatar', desc: 'Presentador IA con lip-sync y narracion.' },
        { label: 'Resultado', title: 'Campana lista!', desc: 'Todos los formatos listos para publicar.' },
      ],
      brief_brand: 'Marca:', brief_goal: 'Objetivo:', brief_goal_v: 'Lanzamiento AgentZZ — mostrar que cualquier negocio puede tener agentes IA 24h.',
      brief_tone: 'Tono:', brief_tone_v: 'Premium, tecnologico, confiable',
      brief_channels: 'Canales:', brief_channels_v: 'Instagram Feed, Story, Facebook, WhatsApp',
      copy_feed: 'Tus clientes nunca mas esperan. Con AgentZZ, tus agentes IA atienden 24h. Configura en 5 minutos.',
      copy_story: 'Atencion 24h. Sin codigo. Sin espera. Empieza gratis.',
      copy_cta: 'Empieza Gratis',
      video_title: 'Video Comercial — AgentZZ', video_dur: '0:30', video_res: '1080p', video_avatar: 'James — Presentador IA', video_voice: 'Narracion profesional ES',
      result_title: 'Campana AgentZZ — Lista', result_formats: '4 formatos generados', result_ready: 'Listo para publicar',
    },
  };
  const d = L[lang] || L.en;

  // Typing effect for copy step
  useEffect(() => {
    if (demoStep === 1) {
      setTypedText('');
      const text = d.copy_feed;
      let i = 0;
      const interval = setInterval(() => {
        if (i < text.length) { setTypedText(text.slice(0, i + 1)); i++; }
        else clearInterval(interval);
      }, 25);
      return () => clearInterval(interval);
    }
  }, [demoStep, lang]);

  // Auto-advance
  useEffect(() => {
    if (!autoPlay) return;
    if (demoStep === 4) return; // Stop at result step
    const delays = [5000, 5500, 5000, 5000, 0];
    const timer = setTimeout(() => {
      setDemoStep(p => (p + 1) % 5);
    }, delays[demoStep]);
    return () => clearTimeout(timer);
  }, [demoStep, autoPlay]);

  const stepIcons = [Target, MessageSquare, Image, Video, Check];

  return (
    <div>
      <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-10">
        <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{d.tag}</p>
        <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{d.title}</h2>
        <p className="text-sm text-[#555] max-w-lg mx-auto mt-2">{d.sub}</p>
      </motion.div>

      {/* Step indicators */}
      <div className="flex items-center justify-center gap-1 sm:gap-2 mb-6">
        {d.steps.map((s, i) => {
          const Icon = stepIcons[i];
          return (
            <button key={i} onClick={() => { setDemoStep(i); setAutoPlay(false); }}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-all duration-400 text-[9px] font-mono ${
                demoStep === i ? 'bg-[#C9A84C]/[0.12] border border-[#C9A84C]/20 text-[#C9A84C]' : 'border border-white/[0.05] text-[#555] hover:text-[#888]'
              }`} data-testid={`demo-step-${i}`}>
              <Icon size={10} />
              <span className="hidden sm:inline">{s.label}</span>
            </button>
          );
        })}
      </div>

      {/* Demo content area */}
      <div className="rounded-2xl border border-white/[0.06] bg-[#0A0A0A] overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center justify-between border-b border-white/[0.05] px-5 py-3 bg-white/[0.01]">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
              <div className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
              <div className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
            </div>
            <span className="text-[9px] font-mono text-[#555] ml-3">AgentZZ AI Marketing Studio</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[8px] font-mono text-[#C9A84C]/50 border border-[#C9A84C]/10 rounded px-2 py-0.5 bg-[#C9A84C]/[0.03]">
              {d.steps[demoStep].label} — {demoStep + 1}/5
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 min-h-[380px]">
          <AnimatePresence mode="wait">
            <motion.div key={demoStep} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.35 }}>

              <div className="mb-4">
                <h3 className="text-base font-bold text-white mb-1">{d.steps[demoStep].title}</h3>
                <p className="text-[11px] text-[#555]">{d.steps[demoStep].desc}</p>
              </div>

              {/* Step 0: Brief */}
              {demoStep === 0 && (
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-2">{d.brief_brand}</p>
                      <div className="flex items-center gap-3">
                        <img src="/logo-agentzz.png" alt="AgentZZ" className="h-6" />
                        <span className="text-[12px] text-white font-semibold">AgentZZ</span>
                      </div>
                    </div>
                    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-2">{d.brief_goal}</p>
                      <p className="text-[11px] text-[#ccc] leading-relaxed">{d.brief_goal_v}</p>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                        <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-1">{d.brief_tone}</p>
                        <p className="text-[10px] text-[#999]">{d.brief_tone_v}</p>
                      </div>
                      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3">
                        <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-1">{d.brief_channels}</p>
                        <p className="text-[10px] text-[#999]">{d.brief_channels_v}</p>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-center">
                    <div className="relative">
                      <motion.div animate={{ rotate: 360 }} transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                        className="h-40 w-40 rounded-full border border-[#C9A84C]/10" />
                      <motion.div animate={{ rotate: -360 }} transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
                        className="absolute inset-4 rounded-full border border-dashed border-[#C9A84C]/15" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center border border-[#C9A84C]/15">
                          <Brain size={28} className="text-[#C9A84C]" />
                        </div>
                      </div>
                      <motion.div animate={{ scale: [1, 1.3, 1] }} transition={{ duration: 2, repeat: Infinity }} className="absolute top-2 right-6 h-3 w-3 rounded-full bg-[#C9A84C]/20" />
                      <motion.div animate={{ scale: [1, 1.2, 1] }} transition={{ duration: 2.5, repeat: Infinity }} className="absolute bottom-4 left-4 h-2 w-2 rounded-full bg-[#C9A84C]/15" />
                    </div>
                  </div>
                </div>
              )}

              {/* Step 1: Copy */}
              {demoStep === 1 && (
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-5 w-5 rounded bg-[#C9A84C]/[0.1] flex items-center justify-center"><MessageSquare size={10} className="text-[#C9A84C]" /></div>
                        <span className="text-[9px] font-mono text-[#C9A84C]">Instagram Feed</span>
                      </div>
                      <p className="text-[11px] text-[#ccc] leading-relaxed">{typedText}<motion.span animate={{ opacity: [1, 0] }} transition={{ duration: 0.5, repeat: Infinity }} className="text-[#C9A84C]">|</motion.span></p>
                    </div>
                    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <div className="h-5 w-5 rounded bg-[#C9A84C]/[0.1] flex items-center justify-center"><MessageSquare size={10} className="text-[#C9A84C]" /></div>
                        <span className="text-[9px] font-mono text-[#C9A84C]">Story / Reels</span>
                      </div>
                      <p className="text-[11px] text-[#999]">{d.copy_story}</p>
                    </div>
                    <div className="rounded-xl border border-[#C9A84C]/10 bg-[#C9A84C]/[0.03] p-3 flex items-center gap-2">
                      <Send size={12} className="text-[#C9A84C]" />
                      <span className="text-[10px] text-[#C9A84C] font-semibold">CTA: {d.copy_cta}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-center">
                    <div className="rounded-xl border border-white/[0.06] overflow-hidden shadow-2xl shadow-black/50 max-w-[200px]">
                      <img src={CAMPAIGN_IMAGES.feed} alt="Feed post" className="w-full" />
                    </div>
                  </div>
                </div>
              )}

              {/* Step 2: Design */}
              {demoStep === 2 && (
                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-1">
                    <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-2">Instagram Feed</p>
                    <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.1 }}
                      className="rounded-xl border border-white/[0.08] overflow-hidden shadow-xl shadow-black/40 hover:border-[#C9A84C]/20 transition-colors">
                      <img src={CAMPAIGN_IMAGES.feed} alt="Feed" className="w-full aspect-square object-cover" />
                    </motion.div>
                  </div>
                  <div className="col-span-1">
                    <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-2">Story / Reels</p>
                    <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.3 }}
                      className="rounded-xl border border-white/[0.08] overflow-hidden shadow-xl shadow-black/40 hover:border-[#C9A84C]/20 transition-colors">
                      <img src={CAMPAIGN_IMAGES.story} alt="Story" className="w-full aspect-[9/16] object-cover" />
                    </motion.div>
                  </div>
                  <div className="col-span-1">
                    <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-2">Facebook / Banner</p>
                    <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.5 }}
                      className="rounded-xl border border-white/[0.08] overflow-hidden shadow-xl shadow-black/40 hover:border-[#C9A84C]/20 transition-colors mb-3">
                      <img src={CAMPAIGN_IMAGES.wide} alt="Banner" className="w-full aspect-video object-cover" />
                    </motion.div>
                    <div className="flex items-center gap-2 text-[9px]">
                      <Check size={10} className="text-emerald-400" />
                      <span className="text-[#888] font-mono">3 formatos gerados</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 3: Video */}
              {demoStep === 3 && (
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
                      <p className="text-[8px] font-mono text-[#C9A84C] uppercase tracking-widest mb-3">{d.video_title}</p>
                      <div className="space-y-2.5">
                        {[
                          { icon: Clock, label: 'Duration', value: d.video_dur },
                          { icon: Video, label: 'Resolution', value: d.video_res },
                          { icon: Users, label: 'Avatar', value: d.video_avatar },
                          { icon: Volume2, label: 'Audio', value: d.video_voice },
                        ].map((item, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <item.icon size={10} className="text-[#C9A84C]/50" />
                            <span className="text-[9px] text-[#555] font-mono w-16">{item.label}</span>
                            <span className="text-[10px] text-[#ccc]">{item.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <motion.div animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 1.5, repeat: Infinity }}
                        className="h-8 w-8 rounded-full bg-[#C9A84C]/[0.1] flex items-center justify-center border border-[#C9A84C]/15">
                        <Volume2 size={12} className="text-[#C9A84C]" />
                      </motion.div>
                      <div className="flex-1 h-6 rounded-full bg-white/[0.03] border border-white/[0.06] overflow-hidden flex items-center px-2 gap-0.5">
                        {[...Array(30)].map((_, wi) => (
                          <motion.div key={wi} animate={{ scaleY: [0.3, Math.random() * 0.8 + 0.2, 0.3] }}
                            transition={{ duration: 0.5 + Math.random() * 0.5, repeat: Infinity, delay: wi * 0.03 }}
                            className="w-1 bg-[#C9A84C]/40 rounded-full" style={{ height: '16px' }} />
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-center">
                    <div className="relative rounded-xl border border-white/[0.08] overflow-hidden shadow-2xl shadow-black/50 max-w-[260px]">
                      <video autoPlay muted loop playsInline className="w-full aspect-video object-cover">
                        <source src="/agentzz-demo.mp4" type="video/mp4" />
                      </video>
                      <div className="absolute top-2 left-2">
                        <div className="flex items-center gap-1 bg-[#C9A84C]/80 backdrop-blur-sm rounded px-1.5 py-0.5">
                          <span className="text-[6px] text-[#0A0A0A] font-bold">SORA 2</span>
                        </div>
                      </div>
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3">
                        <div className="flex items-center gap-2">
                          <div className="h-6 w-6 rounded-full overflow-hidden ring-1 ring-[#C9A84C]/20">
                            <img src={AVATARS.James} alt="" className="h-full w-full object-cover" />
                          </div>
                          <div>
                            <p className="text-[9px] text-white font-semibold">James</p>
                            <p className="text-[7px] text-[#C9A84C]/60 font-mono">AI Presenter</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Step 4: Result - Channel Templates */}
              {demoStep === 4 && (
                <div>
                  <div className="flex items-center gap-3 mb-4 p-3 rounded-xl border border-emerald-400/15 bg-emerald-400/[0.03]">
                    <div className="h-8 w-8 rounded-full bg-emerald-400/10 flex items-center justify-center">
                      <Check size={14} className="text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold text-emerald-400">{d.result_title}</p>
                      <p className="text-[9px] text-emerald-400/60 font-mono">{d.result_formats}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    {/* Instagram Post Template */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#E1306C]/30 transition-colors">
                      <div className="flex items-center gap-2 px-2.5 py-2 border-b border-white/[0.05]">
                        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center">
                          <span className="text-[6px] font-bold text-[#C9A84C]">Az</span>
                        </div>
                        <span className="text-[8px] text-white font-semibold">agentzz</span>
                        <IgIcon size={8} color="#E1306C" className="ml-auto" />
                      </div>
                      <img src={CAMPAIGN_IMAGES.feed} alt="IG Feed" className="w-full aspect-square object-cover" />
                      <div className="px-2.5 py-2">
                        <div className="flex gap-2 mb-1.5">
                          <Heart size={10} className="text-[#ccc]" /><MessageSquare size={10} className="text-[#ccc]" /><Send size={10} className="text-[#ccc]" />
                        </div>
                        <p className="text-[7px] text-[#888] leading-relaxed mb-1"><span className="text-white font-semibold">agentzz </span>Seus clientes nunca mais esperam. Com AgentZZ, seus agentes IA atendem 24h no WhatsApp, Instagram e Telegram. Configure em 5 minutos.</p>
                        <p className="text-[6px] text-[#555]">#IA #Atendimento #ChatBot #AgentZZ #Marketing</p>
                      </div>
                      <div className="px-2.5 pb-2 flex items-center gap-1">
                        <IgIcon size={7} color="#E1306C" />
                        <span className="text-[7px] text-[#555] font-mono">Instagram Feed</span>
                      </div>
                    </motion.div>

                    {/* Facebook Post Template */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#0084FF]/30 transition-colors">
                      <div className="flex items-center gap-2 px-2.5 py-2 border-b border-white/[0.05]">
                        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center">
                          <span className="text-[6px] font-bold text-[#C9A84C]">Az</span>
                        </div>
                        <div>
                          <span className="text-[8px] text-white font-semibold block leading-none">AgentZZ</span>
                          <span className="text-[6px] text-[#555]">Sponsored</span>
                        </div>
                        <FbIcon size={8} color="#0084FF" className="ml-auto" />
                      </div>
                      <div className="px-2.5 py-1.5">
                        <p className="text-[7px] text-[#999] leading-relaxed">Automatize seu negocio com agentes IA inteligentes. Atendimento 24h no WhatsApp, Instagram e Telegram. Sem codigo, sem espera. Comece gratis!</p>
                      </div>
                      <img src={CAMPAIGN_IMAGES.wide} alt="FB Banner" className="w-full aspect-video object-cover" />
                      <div className="px-2.5 py-1.5">
                        <p className="text-[7px] text-[#888] leading-relaxed">Mais de 22 agentes prontos para usar. Crie campanhas com IA e publique em todos os canais.</p>
                        <p className="text-[6px] text-[#0084FF] mt-1 font-semibold">Saiba mais</p>
                      </div>
                      <div className="px-2.5 py-1.5 flex items-center justify-between border-t border-white/[0.04]">
                        <div className="flex items-center gap-1">
                          <ThumbsUp size={8} className="text-[#0084FF]" />
                          <span className="text-[7px] text-[#888]">2.4k</span>
                        </div>
                        <span className="text-[7px] text-[#555]">342 shares</span>
                      </div>
                      <div className="px-2.5 pb-2 flex items-center gap-1">
                        <FbIcon size={7} color="#0084FF" />
                        <span className="text-[7px] text-[#555] font-mono">Facebook Ads</span>
                      </div>
                    </motion.div>

                    {/* WhatsApp Status Template */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#25D366]/30 transition-colors">
                      <div className="flex items-center gap-2 px-2.5 py-2 border-b border-white/[0.05]">
                        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center">
                          <span className="text-[6px] font-bold text-[#C9A84C]">Az</span>
                        </div>
                        <div>
                          <span className="text-[8px] text-white font-semibold block leading-none">AgentZZ</span>
                          <span className="text-[6px] text-[#555]">Business</span>
                        </div>
                        <WaIcon size={8} color="#25D366" className="ml-auto" />
                      </div>
                      <div className="relative">
                        <img src={CAMPAIGN_IMAGES.story} alt="WA Status" className="w-full aspect-[9/14] object-cover" />
                        <div className="absolute top-0 left-0 right-0 h-1 bg-white/[0.1] rounded-full mx-2 mt-1.5">
                          <div className="h-full w-1/3 bg-[#25D366] rounded-full" />
                        </div>
                      </div>
                      <div className="px-2.5 py-2">
                        <p className="text-[7px] text-[#888] leading-relaxed">Atendimento 24h no WhatsApp. Seus agentes IA respondem, agendam e vendem automaticamente.</p>
                      </div>
                      <div className="px-2.5 pb-2 flex items-center gap-1">
                        <WaIcon size={7} color="#25D366" />
                        <span className="text-[7px] text-[#555] font-mono">WhatsApp Status</span>
                      </div>
                    </motion.div>

                    {/* TikTok Video Template - Real Sora 2 Video */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#ff0050]/30 transition-colors">
                      <div className="relative">
                        <video
                          autoPlay muted loop playsInline
                          className="w-full aspect-[9/14] object-cover"
                          poster={CAMPAIGN_IMAGES.feed}
                        >
                          <source src="/agentzz-demo.mp4" type="video/mp4" />
                        </video>
                        {/* TikTok sidebar */}
                        <div className="absolute right-2 bottom-12 flex flex-col items-center gap-3">
                          <div className="flex flex-col items-center"><Heart size={12} className="text-white" /><span className="text-[6px] text-white">24.5k</span></div>
                          <div className="flex flex-col items-center"><MessageSquare size={12} className="text-white" /><span className="text-[6px] text-white">1.2k</span></div>
                          <div className="flex flex-col items-center"><Send size={12} className="text-white" /><span className="text-[6px] text-white">856</span></div>
                        </div>
                        {/* Bottom text */}
                        <div className="absolute left-2 bottom-2 right-10">
                          <p className="text-[8px] text-white font-semibold">@agentzz</p>
                          <p className="text-[6px] text-white/70">Agentes IA que nunca dormem #IA #Marketing</p>
                        </div>
                        {/* Live badge */}
                        <div className="absolute top-2 left-2">
                          <div className="flex items-center gap-1 bg-red-500/80 backdrop-blur-sm rounded px-1.5 py-0.5">
                            <div className="h-1 w-1 rounded-full bg-white animate-pulse" />
                            <span className="text-[6px] text-white font-bold">SORA 2</span>
                          </div>
                        </div>
                      </div>
                      <div className="px-2.5 py-2 flex items-center gap-1">
                        <TkIcon size={7} color="#ff0050" />
                        <span className="text-[7px] text-[#555] font-mono">TikTok Video — Sora 2 AI</span>
                      </div>
                    </motion.div>
                  </div>
                </div>
              )}

            </motion.div>
          </AnimatePresence>
        </div>

        {/* Progress bar */}
        <div className="border-t border-white/[0.05] px-5 py-2.5 flex items-center gap-3">
          <div className="flex-1 h-1 rounded-full bg-white/[0.04] overflow-hidden">
            <motion.div className="h-full bg-[#C9A84C]/40 rounded-full"
              animate={{ width: `${((demoStep + 1) / 5) * 100}%` }}
              transition={{ duration: 0.5 }} />
          </div>
          <span className="text-[8px] font-mono text-[#555]">{demoStep + 1}/5</span>
        </div>
      </div>
    </div>
  );
}

/* ── Animated Pipeline Step ── */
function PipelineStep({ icon: Icon, label, color, active, delay }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.4 }}
      className={`flex flex-col items-center transition-all duration-500 ${active ? 'scale-105' : ''}`}
    >
      <div className={`h-14 w-14 rounded-xl border flex items-center justify-center mb-2 transition-all duration-500 ${
        active ? 'border-[#C9A84C]/30 bg-[#C9A84C]/[0.08] shadow-lg shadow-[#C9A84C]/10' : 'border-white/[0.06] bg-white/[0.02]'
      }`}>
        <Icon size={20} className={active ? 'text-[#C9A84C]' : color} />
      </div>
      <span className={`text-[9px] font-mono transition-colors ${active ? 'text-[#C9A84C]' : 'text-[#555]'}`}>{label}</span>
    </motion.div>
  );
}

const fade = {
  hidden: { opacity: 0, y: 16 },
  visible: (d = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.45, delay: d * 0.08, ease: [0.25, 0.46, 0.45, 0.94] } }),
};

/* ═══════════════════════════ MAIN ═══════════════════════════ */
export default function LandingV2() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language?.startsWith('pt') ? 'pt' : i18n.language?.startsWith('es') ? 'es' : 'en';
  const [billingAnnual, setBillingAnnual] = useState(true);
  const [activeAgent, setActiveAgent] = useState(0);
  const [activeStep, setActiveStep] = useState(0);

  const L = {
    pt: {
      badge: 'Plataforma de agentes IA',
      h1a: 'Seus agentes.', h1b: 'Suas campanhas.', h1c: 'Todos os canais.',
      sub: 'Crie agentes inteligentes, gere campanhas completas com IA e publique em todas as redes — sem codigo.',
      cta: 'Comece Gratis', demo: 'Ver Demo',
      s1: 'Agentes IA', s2: 'Canais', s3: 'Idiomas', s4: 'Uptime',
      how_tag: 'Seus agentes', how_title: 'Agentes com personalidade. ', how_title2: 'Configuracao intuitiva.',
      how_sub: 'Cada agente tem habilidades unicas e pode ser configurado em minutos.',
      skill_sales: 'Vendas', skill_support: 'Suporte', skill_schedule: 'Agendamento',
      skill_qualify: 'Qualificacao', skill_followup: 'Follow-up', skill_multilang: 'Multi-idioma',
      ag1_name: 'Sarah', ag1_role: 'Agente de Vendas', ag1_desc: 'Especialista em conversao e qualificacao de leads.',
      ag2_name: 'Carlos', ag2_role: 'Suporte Tecnico', ag2_desc: 'Resolve duvidas tecnicas com clareza.',
      ag3_name: 'Sophia', ag3_role: 'Agendamento', ag3_desc: 'Gerencia agenda e envia lembretes automaticos.',
      ag_personality: 'Personalidade', ag_knowledge: 'Base de conhecimento', ag_channels: 'Canais ativos',
      ag_lang: 'Idiomas', ag_rules: 'Regras',
      config_title: 'Configure em minutos',
      ch_tag: 'Canais integrados', ch_title: 'Um inbox. ', ch_title2: 'Todos os canais.',
      ch_sub: 'Seus agentes atendem em todas as plataformas com inbox unificado.',
      ai_tag: 'AI Marketing Studio', ai_title: 'Da ideia ao ar ', ai_title2: 'em minutos.',
      ai_sub: 'A IA cria copy, imagens, audio e video com avatar — tudo automatico. Veja o processo:',
      ai_step1: 'Descreva seu objetivo', ai_step1d: 'A IA analisa seu negocio e gera a estrategia da campanha automaticamente.',
      ai_step2: 'Copy + Design gerados', ai_step2d: 'Textos persuasivos e imagens profissionais criados em segundos.',
      ai_step3: 'Video com avatar IA', ai_step3d: 'Apresentador virtual com lip-sync e narracao em qualquer idioma.',
      ai_step4: 'Publicado nos canais', ai_step4d: 'Variantes automaticas para Instagram, WhatsApp, TikTok e mais.',
      camp_tag: 'Campanhas criadas', camp_title: 'Resultados reais. ', camp_title2: 'Campanhas reais.',
      camp_sub: 'Veja exemplos de campanhas geradas pela nossa IA.',
      test_tag: 'Depoimentos', test_title: 'O que nossos clientes dizem',
      feat_tag: 'Recursos', feat_title: 'Tudo que voce precisa',
      feat_sub: 'Ferramentas poderosas para automatizar seu negocio.',
      cta_title: 'Pronto para automatizar?', cta_sub: 'Comece gratis. Sem cartao. Configure em 5 minutos.',
    },
    en: {
      badge: 'AI Agent Platform',
      h1a: 'Your agents.', h1b: 'Your campaigns.', h1c: 'Every channel.',
      sub: 'Create intelligent agents, generate full AI campaigns, and publish everywhere — no code needed.',
      cta: 'Start Free', demo: 'Watch Demo',
      s1: 'AI Agents', s2: 'Channels', s3: 'Languages', s4: 'Uptime',
      how_tag: 'Your agents', how_title: 'Agents with personality. ', how_title2: 'Intuitive setup.',
      how_sub: 'Each agent has unique skills and can be configured in minutes.',
      skill_sales: 'Sales', skill_support: 'Support', skill_schedule: 'Scheduling',
      skill_qualify: 'Qualification', skill_followup: 'Follow-up', skill_multilang: 'Multi-language',
      ag1_name: 'Sarah', ag1_role: 'Sales Agent', ag1_desc: 'Lead conversion specialist with a consultative approach.',
      ag2_name: 'Carlos', ag2_role: 'Tech Support', ag2_desc: 'Resolves technical issues with clarity.',
      ag3_name: 'Sophia', ag3_role: 'Scheduling', ag3_desc: 'Manages calendar and sends automatic reminders.',
      ag_personality: 'Personality', ag_knowledge: 'Knowledge base', ag_channels: 'Active channels',
      ag_lang: 'Languages', ag_rules: 'Rules',
      config_title: 'Set up in minutes',
      ch_tag: 'Integrated channels', ch_title: 'One inbox. ', ch_title2: 'Every channel.',
      ch_sub: 'Your agents serve across every platform with a unified inbox.',
      ai_tag: 'AI Marketing Studio', ai_title: 'From idea to live ', ai_title2: 'in minutes.',
      ai_sub: 'AI creates copy, images, audio, and avatar video — fully automatic. See the process:',
      ai_step1: 'Describe your goal', ai_step1d: 'AI analyzes your business and generates the campaign strategy.',
      ai_step2: 'Copy + Design generated', ai_step2d: 'Persuasive text and professional images created in seconds.',
      ai_step3: 'AI avatar video', ai_step3d: 'Virtual presenter with lip-sync and narration in any language.',
      ai_step4: 'Published on channels', ai_step4d: 'Auto variants for Instagram, WhatsApp, TikTok, and more.',
      camp_tag: 'Created campaigns', camp_title: 'Real results. ', camp_title2: 'Real campaigns.',
      camp_sub: 'See examples of AI-generated campaigns.',
      test_tag: 'Testimonials', test_title: 'What our clients say',
      feat_tag: 'Features', feat_title: 'Everything you need',
      feat_sub: 'Powerful tools to automate your business.',
      cta_title: 'Ready to automate?', cta_sub: 'Start free. No credit card. Set up in 5 minutes.',
    },
    es: {
      badge: 'Plataforma de agentes IA',
      h1a: 'Tus agentes.', h1b: 'Tus campanas.', h1c: 'Todos los canales.',
      sub: 'Crea agentes inteligentes, genera campanas con IA y publica en todas las redes — sin codigo.',
      cta: 'Empieza Gratis', demo: 'Ver Demo',
      s1: 'Agentes IA', s2: 'Canales', s3: 'Idiomas', s4: 'Uptime',
      how_tag: 'Tus agentes', how_title: 'Agentes con personalidad. ', how_title2: 'Configuracion intuitiva.',
      how_sub: 'Cada agente tiene habilidades unicas y se configura en minutos.',
      skill_sales: 'Ventas', skill_support: 'Soporte', skill_schedule: 'Agendamiento',
      skill_qualify: 'Calificacion', skill_followup: 'Follow-up', skill_multilang: 'Multi-idioma',
      ag1_name: 'Sarah', ag1_role: 'Agente de Ventas', ag1_desc: 'Especialista en conversion de leads.',
      ag2_name: 'Carlos', ag2_role: 'Soporte Tecnico', ag2_desc: 'Resuelve dudas tecnicas con claridad.',
      ag3_name: 'Sophia', ag3_role: 'Agendamiento', ag3_desc: 'Gestiona agenda y envia recordatorios.',
      ag_personality: 'Personalidad', ag_knowledge: 'Base de conocimiento', ag_channels: 'Canales activos',
      ag_lang: 'Idiomas', ag_rules: 'Reglas',
      config_title: 'Configura en minutos',
      ch_tag: 'Canales integrados', ch_title: 'Un inbox. ', ch_title2: 'Todos los canales.',
      ch_sub: 'Tus agentes atienden en todas las plataformas.',
      ai_tag: 'AI Marketing Studio', ai_title: 'De la idea al aire ', ai_title2: 'en minutos.',
      ai_sub: 'La IA crea copy, imagenes, audio y video con avatar — todo automatico.',
      ai_step1: 'Describe tu objetivo', ai_step1d: 'La IA analiza tu negocio y genera la estrategia.',
      ai_step2: 'Copy + Diseno generados', ai_step2d: 'Textos persuasivos e imagenes en segundos.',
      ai_step3: 'Video con avatar IA', ai_step3d: 'Presentador virtual con lip-sync profesional.',
      ai_step4: 'Publicado en canales', ai_step4d: 'Variantes auto para Instagram, WhatsApp, TikTok.',
      camp_tag: 'Campanas creadas', camp_title: 'Resultados reales. ', camp_title2: 'Campanas reales.',
      camp_sub: 'Mira ejemplos de campanas generadas por IA.',
      test_tag: 'Testimonios', test_title: 'Lo que dicen nuestros clientes',
      feat_tag: 'Recursos', feat_title: 'Todo lo que necesitas',
      feat_sub: 'Herramientas poderosas para automatizar tu negocio.',
      cta_title: 'Listo para automatizar?', cta_sub: 'Empieza gratis. Sin tarjeta.',
    },
  };
  const l = L[lang] || L.en;

  const agents = [
    { name: l.ag1_name, role: l.ag1_role, desc: l.ag1_desc, avatar: AVATARS.Sarah, channels: ['WhatsApp', 'Instagram', 'Telegram'], skills: [l.skill_sales, l.skill_qualify, l.skill_followup] },
    { name: l.ag2_name, role: l.ag2_role, desc: l.ag2_desc, avatar: AVATARS.Carlos, channels: ['WhatsApp', 'Messenger', 'SMS'], skills: [l.skill_support, l.skill_multilang, l.skill_followup] },
    { name: l.ag3_name, role: l.ag3_role, desc: l.ag3_desc, avatar: AVATARS.Sophia, channels: ['WhatsApp', 'Instagram'], skills: [l.skill_schedule, l.skill_followup, l.skill_multilang] },
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

  const pipelineSteps = [
    { icon: Target, label: 'Brief', color: 'text-blue-400' },
    { icon: MessageSquare, label: 'Copy', color: 'text-purple-400' },
    { icon: Image, label: 'Design', color: 'text-pink-400' },
    { icon: Volume2, label: 'Audio', color: 'text-emerald-400' },
    { icon: Video, label: 'Video', color: 'text-orange-400' },
    { icon: Send, label: 'Publish', color: 'text-[#C9A84C]' },
  ];

  const studioSteps = [
    { title: l.ai_step1, desc: l.ai_step1d, icon: Target, visual: 'brief' },
    { title: l.ai_step2, desc: l.ai_step2d, icon: Image, visual: 'design' },
    { title: l.ai_step3, desc: l.ai_step3d, icon: Video, visual: 'video' },
    { title: l.ai_step4, desc: l.ai_step4d, icon: Send, visual: 'publish' },
  ];

  const testimonials = [
    { name: 'Rafael Costa', role: lang === 'pt' ? 'CEO, TechStore' : 'CEO, TechStore', text: lang === 'pt' ? 'Triplicamos nossas conversoes no WhatsApp em 2 semanas. Os agentes respondem 24h e nunca perdem um lead.' : 'We tripled our WhatsApp conversions in 2 weeks. Agents respond 24/7 and never miss a lead.', photo: TESTIMONIAL_PHOTOS[0] },
    { name: 'Ana Ferreira', role: lang === 'pt' ? 'Diretora de Marketing, Moda Plus' : 'Marketing Director, Moda Plus', text: lang === 'pt' ? 'O AI Studio mudou completamente nossa producao de conteudo. Campanhas que levavam dias agora ficam prontas em minutos.' : 'AI Studio completely changed our content production. Campaigns that took days are now ready in minutes.', photo: TESTIMONIAL_PHOTOS[1] },
    { name: 'Pedro Santos', role: lang === 'pt' ? 'Fundador, FitLife' : 'Founder, FitLife', text: lang === 'pt' ? 'A Sophia gerencia todos os agendamentos da academia automaticamente. Nossos clientes adoram a experiencia.' : 'Sophia manages all gym scheduling automatically. Our clients love the experience.', photo: TESTIMONIAL_PHOTOS[2] },
  ];

  /* Real campaigns from AI Studio — full format data */
  const REAL_CAMPAIGNS = [
    {
      name: 'Crafting Hands',
      handle: 'craftinghands',
      type: 'NGO / Social',
      igCaption: 'Si 30 minutos tuyos pudieran alegrar el dia mas dificil de un nino? Unete a nuestro club de estudiantes que hacen pulseras y tarjetas con amor para ninos hospitalizados.',
      fbText: 'Mientras estas en casa viendo series, hay un nino de 6 anos en un hospital que no recibe visitas. Pero TU puedes cambiar eso. Unete gratis ahora!',
      hashtags: '#AmorEnCadaPulsera #JovenesQueCambian #ServicioComunitario #CreaConAmor',
      feedImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/19b6bdd8-51c9-4859-af32-007dd14a146b_1_7597f1.png',
      wideImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/19b6bdd8-51c9-4859-af32-007dd14a146b_v1_16x9_a17d42.png',
      storyImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/19b6bdd8-51c9-4859-af32-007dd14a146b_v1_9x16_32bd28.png',
      video: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/videos/19b6bdd8-51c9-4859-af32-007dd14a146b_commercial.mp4',
    },
    {
      name: 'Apice Detailing',
      handle: 'apicedetailing',
      type: 'Luxury Auto Care',
      igCaption: 'Your Supercar Deserves Supercar Treatment. We Come to You. Ferrari, Lamborghini, Porsche gleaming like the day they left the factory.',
      fbText: 'Imagine this: Your Ferrari gleaming like the day it left Maranello. Your Lamborghini reflecting perfection in every curve. Mobile luxury detailing at your door.',
      hashtags: '#SupercarDetailing #MobileCarCare #LuxuryLifestyle #CeramicCoating',
      feedImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/4da83978-5af3-4736-8b5f-959df4a08071_1_21e9f2.png',
      wideImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/4da83978-5af3-4736-8b5f-959df4a08071_v1_16x9_6d1c59.png',
      storyImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/4da83978-5af3-4736-8b5f-959df4a08071_v1_9x16_84f9ee.png',
      video: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/videos/4da83978-5af3-4736-8b5f-959df4a08071_commercial.mp4',
    },
    {
      name: 'My Truck Pickup Shop',
      handle: 'mytruckshop',
      type: 'Automotive Sales',
      igCaption: 'Cansado de vender sin apoyo financiero? My Truck te da TODO. 17+ bancos listos para aprobar. Gana hasta $1,500 por vehiculo vendido.',
      fbText: 'Eres vendedor de autos pero no tienes equipo de financiamiento? En My Truck Orlando tenemos 17+ bancos listos para aprobar. Unete hoy!',
      hashtags: '#VentaDeCarros #TrucksUSA #MyTruckOrlando #ComisionesAltas #FinanciamientoFacil',
      feedImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/89fdfe02-0fb0-46cf-b2eb-c9b20f752847_1_880d42.png',
      wideImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/89fdfe02-0fb0-46cf-b2eb-c9b20f752847_2_2bbf67.png',
      storyImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/89fdfe02-0fb0-46cf-b2eb-c9b20f752847_3_af19d4.png',
      video: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/videos/89fdfe02-0fb0-46cf-b2eb-c9b20f752847_commercial.mp4',
    },
    {
      name: 'Hercules Solutions',
      handle: 'herculessolutions',
      type: 'Construction & Design',
      igCaption: 'Your Dream Home Doesn\'t Have to Wait Years. Custom renovations with impeccable finishes, delivered on time. Transform your space today.',
      fbText: 'Most homeowners spend months waiting for renovations. Delays, cost overruns, mediocre craftsmanship. You deserve better. Premium results, on schedule.',
      hashtags: '#LuxuryRemodeling #HomeTransformation #CustomHomes #DreamHomeUSA',
      feedImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/c561486a-a04e-442d-b53e-66c16f95d78a_1_5dddb1.png',
      wideImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/c561486a-a04e-442d-b53e-66c16f95d78a_v1_16x9_602a87.png',
      storyImg: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/c561486a-a04e-442d-b53e-66c16f95d78a_v1_9x16_b51a77.png',
      video: 'https://rzwpuitdsejtmuuabxwh.supabase.co/storage/v1/object/public/pipeline-assets/videos/c561486a-a04e-442d-b53e-66c16f95d78a_commercial.mp4',
    },
  ];
  const [activeCamp, setActiveCamp] = useState(0);

  const current = agents[activeAgent];

  useEffect(() => {
    const i1 = setInterval(() => setActiveAgent(p => (p + 1) % agents.length), 5000);
    const i2 = setInterval(() => setActiveStep(p => (p + 1) % pipelineSteps.length), 2000);
    const i3 = setInterval(() => setActiveCamp(p => (p + 1) % 4), 6000);
    return () => { clearInterval(i1); clearInterval(i2); clearInterval(i3); };
  }, []);

  return (
    <div className="min-h-screen bg-[#060606] text-white overflow-x-hidden selection:bg-[#C9A84C]/20 selection:text-[#C9A84C]">

      {/* ═══ HEADER ═══ */}
      <header className="fixed top-0 inset-x-0 z-50 border-b border-white/[0.04] bg-[#060606]/70 backdrop-blur-2xl">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-3">
          <img src="/logo-agentzz.png" alt="Agents" className="h-7" data-testid="landing-logo" />
          <div className="flex items-center gap-2.5">
            <button onClick={() => navigate('/login')} data-testid="landing-signin-btn"
              className="px-4 py-2 text-[13px] text-[#777] hover:text-white transition rounded-lg">
              {t('landing.signin')}
            </button>
            <button onClick={() => navigate('/login?tab=signup')} data-testid="landing-signup-btn"
              className="btn-gold rounded-lg px-5 py-2 text-[13px] font-semibold">
              {l.cta}
            </button>
          </div>
        </div>
      </header>

      {/* ═══ HERO ═══ */}
      <section className="relative pt-24 pb-14 px-5 overflow-hidden" data-testid="hero-section">
        <TechGrid />
        <Glow className="h-[400px] w-[500px] -top-24 left-[15%] bg-[#C9A84C]/[0.03]" />
        <div className="relative z-10 mx-auto max-w-6xl">
          <motion.div initial="hidden" animate="visible" variants={fade} custom={0} className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#C9A84C]/12 bg-[#C9A84C]/[0.04] px-4 py-1.5">
              <Zap size={11} className="text-[#C9A84C]" />
              <span className="text-[10px] font-mono font-medium text-[#C9A84C]/80 tracking-wider uppercase">{l.badge}</span>
            </div>
          </motion.div>

          <motion.div initial="hidden" animate="visible" variants={fade} custom={1} className="text-center max-w-3xl mx-auto mb-4">
            <h1 className="text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl lg:text-[3.5rem]">
              <span className="text-white">{l.h1a}</span>{' '}
              <span className="bg-gradient-to-r from-[#C9A84C] to-[#E0C76B] bg-clip-text text-transparent">{l.h1b}</span>{' '}
              <span className="text-white">{l.h1c}</span>
            </h1>
          </motion.div>

          <motion.p initial="hidden" animate="visible" variants={fade} custom={2}
            className="text-center text-[14px] text-[#666] leading-relaxed max-w-lg mx-auto mb-8">
            {l.sub}
          </motion.p>

          <motion.div initial="hidden" animate="visible" variants={fade} custom={3} className="flex justify-center gap-3 mb-12">
            <button onClick={() => navigate('/login?tab=signup')} data-testid="hero-cta-btn"
              className="btn-gold flex items-center gap-2 rounded-xl px-7 py-3 text-sm font-semibold group shadow-lg shadow-[#C9A84C]/10">
              {l.cta} <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button data-testid="hero-demo-btn"
              onClick={() => document.getElementById('demo-section')?.scrollIntoView({ behavior: 'smooth' })}
              className="flex items-center gap-2 rounded-xl border border-white/[0.07] bg-white/[0.02] px-7 py-3 text-sm text-[#888] hover:text-white hover:border-white/[0.12] transition-all">
              <Play size={14} /> {l.demo}
            </button>
          </motion.div>

          {/* Hero 3 panels */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={4}
            className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-4xl mx-auto items-stretch">
            <Glass hover className="p-4 flex flex-col">
              {/* Header */}
              <div className="flex items-center gap-3 mb-3">
                <div className="h-10 w-10 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/15">
                  <img src={AVATARS.Sarah} alt="Sarah" className="h-full w-full object-cover" />
                </div>
                <div>
                  <p className="text-[11px] font-semibold text-white">Sarah</p>
                  <p className="text-[9px] text-[#555] font-mono">Sales Agent</p>
                </div>
                <div className="ml-auto h-2 w-2 rounded-full bg-emerald-400" />
              </div>
              {/* Channels */}
              <div className="space-y-1.5 mb-3">
                {['WhatsApp', 'Instagram', 'Telegram'].map(ch => (
                  <div key={ch} className="flex items-center gap-2 px-2 py-1 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]/60" />
                    <span className="text-[8px] text-[#888] font-mono">{ch}</span>
                    <span className="ml-auto text-[7px] text-emerald-400/70 font-mono">Active</span>
                  </div>
                ))}
              </div>
              {/* Mentalidade */}
              <div className="border-t border-white/[0.05] pt-3 mb-3">
                <div className="flex items-center gap-1.5 mb-2">
                  <Brain size={9} className="text-[#C9A84C]" />
                  <p className="text-[8px] text-white font-semibold tracking-wide">Mentalidade</p>
                </div>
                <p className="text-[7px] text-[#666] leading-relaxed">
                  Sarah combina técnicas de vendas consultivas com inteligência emocional. Treinada para identificar necessidades, qualificar leads e converter com empatia — disponível 24/7 em múltiplos canais.
                </p>
              </div>
              {/* Skills with progress bars */}
              <div className="border-t border-white/[0.05] pt-3 flex-1">
                <div className="flex items-center gap-1.5 mb-2.5">
                  <Settings size={9} className="text-[#C9A84C]" />
                  <p className="text-[8px] text-white font-semibold tracking-wide">Skills</p>
                </div>
                <div className="space-y-2">
                  {[
                    { name: 'Lead Qualification', pct: 98 },
                    { name: 'Appointment Scheduling', pct: 97 },
                    { name: 'Follow-up & Nurturing', pct: 95 },
                    { name: 'Objection Handling', pct: 94 },
                    { name: 'Multilingual (PT/EN/ES)', pct: 96 },
                    { name: 'Upsell & Cross-sell', pct: 92 },
                  ].map(s => (
                    <div key={s.name}>
                      <div className="flex items-center justify-between mb-0.5">
                        <span className="text-[7px] text-[#888]">{s.name}</span>
                        <span className="text-[7px] text-[#C9A84C] font-bold font-mono">{s.pct}%</span>
                      </div>
                      <div className="h-[3px] rounded-full bg-white/[0.04] overflow-hidden">
                        <motion.div initial={{ width: 0 }} whileInView={{ width: `${s.pct}%` }} viewport={{ once: true }}
                          transition={{ duration: 1, delay: 0.2 }}
                          className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#C9A84C]/70" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              {/* Footer stat */}
              <div className="flex items-center gap-1 text-[8px] text-[#C9A84C]/60 font-mono mt-3 pt-2 border-t border-white/[0.05]">
                <Sparkles size={8} /> 847 conversations
              </div>
            </Glass>

            <div className="md:translate-y-[-12px] h-full"><AgentChat /></div>

            <Glass hover className="p-4 flex flex-col">
              <div className="flex items-center gap-2 mb-2.5">
                <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center border border-[#C9A84C]/10">
                  <Megaphone size={13} className="text-[#C9A84C]" />
                </div>
                <div>
                  <p className="text-[10px] font-semibold text-white">AI Campaign</p>
                  <p className="text-[7px] text-emerald-400 font-mono">Published</p>
                </div>
              </div>
              {/* Campaign preview image */}
              <div className="rounded-lg overflow-hidden border border-white/[0.06] mb-2.5 relative">
                <img src={CAMPAIGN_IMAGES.feed} alt="Campaign" className="w-full aspect-[4/3] object-cover object-top" />
                <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A]/80 to-transparent" />
                <div className="absolute bottom-2 left-2.5 right-2.5">
                  <p className="text-[9px] font-bold text-white">AgentZZ</p>
                  <p className="text-[7px] text-[#C9A84C]/70 font-mono">AI-Powered Campaign</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-1 mb-3">
                <div className="rounded bg-white/[0.02] border border-white/[0.04] p-1 text-center">
                  <p className="text-[9px] font-bold text-white font-mono">45k</p>
                  <p className="text-[6px] text-[#555] font-mono">Views</p>
                </div>
                <div className="rounded bg-white/[0.02] border border-white/[0.04] p-1 text-center">
                  <p className="text-[9px] font-bold text-emerald-400 font-mono">3.8%</p>
                  <p className="text-[6px] text-[#555] font-mono">Conv.</p>
                </div>
                <div className="rounded bg-white/[0.02] border border-white/[0.04] p-1 text-center">
                  <p className="text-[9px] font-bold text-[#C9A84C] font-mono">1.7k</p>
                  <p className="text-[6px] text-[#555] font-mono">Leads</p>
                </div>
              </div>
              {/* 3 Mini campaign cards — IG, FB, TikTok */}
              <div className="border-t border-white/[0.05] pt-3 flex-1">
                <p className="text-[8px] text-[#555] font-mono uppercase tracking-widest mb-2">Distributed to</p>
                <div className="grid grid-cols-3 gap-1.5">
                  {/* Instagram mini */}
                  <div className="rounded-lg border border-white/[0.06] bg-[#0D0D0D] overflow-hidden hover:border-[#E1306C]/25 transition-colors">
                    <div className="flex items-center gap-1 px-1.5 py-1 border-b border-white/[0.04]">
                      <IgIcon size={7} color="#E1306C" />
                      <span className="text-[6px] text-[#888] font-mono">Instagram</span>
                    </div>
                    <img src={CAMPAIGN_IMAGES.feed} alt="IG" className="w-full aspect-square object-cover object-top" />
                    <div className="px-1.5 py-1">
                      <div className="flex gap-1.5 mb-0.5">
                        <Heart size={6} className="text-[#ccc]" /><MessageSquare size={6} className="text-[#ccc]" /><Send size={6} className="text-[#ccc]" />
                      </div>
                      <p className="text-[5px] text-[#555]">12.4k likes</p>
                    </div>
                  </div>
                  {/* Facebook mini */}
                  <div className="rounded-lg border border-white/[0.06] bg-[#0D0D0D] overflow-hidden hover:border-[#0084FF]/25 transition-colors">
                    <div className="flex items-center gap-1 px-1.5 py-1 border-b border-white/[0.04]">
                      <FbIcon size={7} color="#0084FF" />
                      <span className="text-[6px] text-[#888] font-mono">Facebook</span>
                    </div>
                    <img src={CAMPAIGN_IMAGES.wide} alt="FB" className="w-full aspect-video object-cover" />
                    <div className="px-1.5 py-1">
                      <p className="text-[5px] text-[#888] leading-tight mb-0.5">AI que vende por voce 24/7</p>
                      <div className="flex items-center gap-1">
                        <ThumbsUp size={5} className="text-[#0084FF]" />
                        <span className="text-[5px] text-[#555]">3.2k</span>
                      </div>
                    </div>
                  </div>
                  {/* TikTok mini */}
                  <div className="rounded-lg border border-white/[0.06] bg-[#0D0D0D] overflow-hidden hover:border-[#ff0050]/25 transition-colors">
                    <div className="flex items-center gap-1 px-1.5 py-1 border-b border-white/[0.04]">
                      <TkIcon size={7} color="#ff0050" />
                      <span className="text-[6px] text-[#888] font-mono">TikTok</span>
                    </div>
                    <div className="relative">
                      <img src={CAMPAIGN_IMAGES.story} alt="TK" className="w-full aspect-[9/14] object-cover" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="h-5 w-5 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                          <Play size={8} className="text-white ml-0.5" fill="currentColor" />
                        </div>
                      </div>
                      <div className="absolute right-1 bottom-2 flex flex-col items-center gap-1">
                        <Heart size={7} className="text-white" />
                        <MessageSquare size={7} className="text-white" />
                      </div>
                    </div>
                    <div className="px-1.5 py-1">
                      <p className="text-[5px] text-[#555]">28.7k views</p>
                    </div>
                  </div>
                </div>
              </div>
            </Glass>
          </motion.div>

          <motion.div initial="hidden" animate="visible" variants={fade} custom={5} className="flex justify-center gap-10 lg:gap-14 mt-12">
            {[{ v: '22+', l: l.s1 }, { v: '5', l: l.s2 }, { v: '3', l: l.s3 }, { v: '99.9%', l: l.s4 }].map((s, i) => (
              <div key={i} className="text-center">
                <p className="text-lg font-bold font-mono text-white lg:text-xl">{s.v}</p>
                <p className="text-[8px] text-[#555] tracking-widest uppercase mt-0.5 font-mono">{s.l}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ═══ AGENTS ═══ */}
      <section className="py-16 px-5 relative" data-testid="agents-section">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080808] to-transparent" />
        <Glow className="h-[300px] w-[400px] top-[20%] right-[-80px] bg-[#C9A84C]/[0.02]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade}
            className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.how_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">
              {l.how_title}<span className="text-[#C9A84C]">{l.how_title2}</span>
            </h2>
            <p className="text-sm text-[#555] max-w-md mx-auto mt-2">{l.how_sub}</p>
          </motion.div>

          <div className="grid lg:grid-cols-5 gap-5">
            <div className="lg:col-span-2 space-y-2.5">
              {agents.map((ag, i) => (
                <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i}
                  onClick={() => setActiveAgent(i)}
                  className={`cursor-pointer rounded-xl border p-3.5 transition-all duration-400 ${
                    activeAgent === i ? 'border-[#C9A84C]/20 bg-[#C9A84C]/[0.03]' : 'border-white/[0.05] bg-white/[0.01] hover:border-white/[0.08]'
                  }`} data-testid={`agent-selector-${i}`}>
                  <div className="flex items-center gap-3">
                    <div className={`h-11 w-11 rounded-full overflow-hidden ring-2 transition-all ${activeAgent === i ? 'ring-[#C9A84C]/30' : 'ring-white/[0.06]'}`}>
                      <img src={ag.avatar} alt={ag.name} className="h-full w-full object-cover" />
                    </div>
                    <div className="flex-1">
                      <p className="text-[12px] font-semibold text-white">{ag.name}</p>
                      <p className="text-[9px] text-[#666] font-mono">{ag.role}</p>
                    </div>
                    {activeAgent === i && <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="h-2 w-2 rounded-full bg-[#C9A84C]" />}
                  </div>
                  <p className="text-[10px] text-[#555] leading-relaxed mt-2">{ag.desc}</p>
                </motion.div>
              ))}
            </div>

            <div className="lg:col-span-3">
              <AnimatePresence mode="wait">
                <motion.div key={activeAgent} initial={{ opacity: 0, x: 16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -16 }} transition={{ duration: 0.3 }}>
                  <Glass className="p-4">
                    {/* Agent header */}
                    <div className="flex items-center gap-3 mb-3">
                      <div className="h-11 w-11 rounded-xl overflow-hidden ring-2 ring-[#C9A84C]/20">
                        <img src={current.avatar} alt={current.name} className="h-full w-full object-cover" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-white">{current.name}</h3>
                        <p className="text-[9px] text-[#C9A84C] font-mono">{current.role}</p>
                      </div>
                      <div className="ml-auto flex items-center gap-1 rounded-full border border-emerald-400/15 bg-emerald-400/[0.05] px-2 py-0.5">
                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                        <span className="text-[8px] text-emerald-400 font-mono">Online</span>
                      </div>
                    </div>

                    {/* Skills + Channels row */}
                    <div className="grid grid-cols-2 gap-3 mb-3">
                      <div>
                        <p className="text-[7px] font-mono text-[#555] uppercase tracking-widest mb-1.5"><Brain size={7} className="inline mr-1 text-[#C9A84C]" />Habilidades</p>
                        <div className="flex flex-wrap gap-1">
                          {current.skills.map((skill, si) => (
                            <span key={si} className="flex items-center gap-1 rounded-full border border-[#C9A84C]/10 bg-[#C9A84C]/[0.04] px-2 py-0.5 text-[7px] font-mono text-[#C9A84C]/80">
                              <Star size={7} className="text-[#C9A84C]" />{skill}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-[7px] font-mono text-[#555] uppercase tracking-widest mb-1.5"><Globe size={7} className="inline mr-1 text-[#C9A84C]" />{l.ag_channels}</p>
                        <div className="flex flex-wrap gap-1">
                          {current.channels.map((ch, ci) => (
                            <span key={ci} className="flex items-center gap-1 rounded-lg border border-white/[0.06] bg-white/[0.02] px-2 py-0.5 text-[8px] text-[#888] font-mono">
                              <span className="h-1 w-1 rounded-full bg-emerald-400" />{ch}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Config compact */}
                    <div className="rounded-lg border border-white/[0.05] bg-white/[0.01] p-2.5">
                      <div className="flex items-center gap-1.5 mb-2">
                        <Sliders size={9} className="text-[#C9A84C]" />
                        <p className="text-[9px] font-semibold text-white">{l.config_title}</p>
                      </div>
                      <div className="grid grid-cols-4 gap-1.5">
                        {[
                          { icon: Brain, label: l.ag_personality, value: current.role },
                          { icon: Layers, label: l.ag_knowledge, value: '3 docs' },
                          { icon: Languages, label: l.ag_lang, value: 'PT, EN, ES' },
                          { icon: Clock, label: l.ag_rules, value: '24/7' },
                        ].map((cfg, ci) => (
                          <div key={ci} className="rounded border border-white/[0.04] bg-white/[0.02] p-1.5">
                            <div className="flex items-center gap-1 mb-0.5">
                              <cfg.icon size={7} className="text-[#C9A84C]/60" />
                              <span className="text-[6px] text-[#555] font-mono uppercase">{cfg.label}</span>
                            </div>
                            <p className="text-[8px] text-white font-medium truncate">{cfg.value}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </Glass>
                </motion.div>
              </AnimatePresence>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ CHANNELS ═══ */}
      <section className="py-14 px-5 relative" data-testid="channels-section">
        <TechGrid />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.ch_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{l.ch_title}<span className="text-[#C9A84C]">{l.ch_title2}</span></h2>
            <p className="text-sm text-[#555] max-w-md mx-auto mt-2">{l.ch_sub}</p>
          </motion.div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {channels.map((ch, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.4}>
                <Glass hover className="p-4 text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]/[0.05] mx-auto mb-2 border border-[#C9A84C]/[0.08]">
                    <ch.Icon size={18} color={gold} />
                  </div>
                  <p className="text-[11px] font-semibold text-white mb-0.5">{ch.name}</p>
                  <p className="text-[8px] text-[#555] font-mono">{ch.status}</p>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ DEMO SHOWCASE ═══ */}
      <section id="demo-section" className="py-16 px-5 relative overflow-hidden" data-testid="demo-section">
        <Glow className="h-[300px] w-[400px] top-[10%] left-[-80px] bg-[#C9A84C]/[0.03]" />
        <Glow className="h-[250px] w-[350px] bottom-[10%] right-[-80px] bg-[#C9A84C]/[0.02]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <CampaignDemo lang={lang} />
        </div>
      </section>

      {/* ═══ CAMPAIGNS SHOWCASE — Full Format Cards ═══ */}
      <section className="py-14 px-5 relative" data-testid="campaigns-section">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080808] to-transparent" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-8">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.camp_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{l.camp_title}<span className="text-[#C9A84C]">{l.camp_title2}</span></h2>
            <p className="text-sm text-[#555] max-w-md mx-auto mt-2">{l.camp_sub}</p>
          </motion.div>

          {/* Campaign selector tabs */}
          <div className="flex justify-center gap-2 mb-6 flex-wrap" data-testid="campaign-tabs">
            {REAL_CAMPAIGNS.map((c, i) => (
              <button key={i} onClick={() => setActiveCamp(i)} data-testid={`camp-tab-${i}`}
                className={`px-4 py-2 rounded-full text-[11px] font-semibold transition-all duration-300 border ${
                  activeCamp === i
                    ? 'bg-[#C9A84C]/[0.12] border-[#C9A84C]/25 text-[#C9A84C]'
                    : 'border-white/[0.06] text-[#555] hover:text-[#999] hover:border-white/[0.12]'
                }`}>
                {c.name}
              </button>
            ))}
          </div>

          {/* Active campaign — 4 format cards */}
          <AnimatePresence mode="wait">
            <motion.div key={activeCamp} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.4 }}
              className="grid grid-cols-2 lg:grid-cols-4 gap-3" data-testid="campaign-cards">
              {(() => {
                const camp = REAL_CAMPAIGNS[activeCamp];
                const initials = camp.name[0] + (camp.name.split(' ')[1]?.[0] || '');
                return (
                  <>
                    {/* Instagram Post */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.1 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#E1306C]/30 transition-colors">
                      <div className="flex items-center gap-2 px-2.5 py-2 border-b border-white/[0.05]">
                        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center">
                          <span className="text-[5px] font-bold text-[#C9A84C]">{initials}</span>
                        </div>
                        <span className="text-[8px] text-white font-semibold">{camp.handle}</span>
                        <IgIcon size={8} color="#E1306C" />
                      </div>
                      <img src={camp.feedImg} alt="IG Feed" className="w-full aspect-square object-cover" />
                      <div className="px-2.5 py-2">
                        <div className="flex gap-2 mb-1.5">
                          <Heart size={10} className="text-[#ccc]" /><MessageSquare size={10} className="text-[#ccc]" /><Send size={10} className="text-[#ccc]" />
                        </div>
                        <p className="text-[7px] text-[#888] leading-relaxed mb-1"><span className="text-white font-semibold">{camp.handle} </span>{camp.igCaption}</p>
                        <p className="text-[6px] text-[#555]">{camp.hashtags}</p>
                      </div>
                      <div className="px-2.5 pb-2 flex items-center gap-1">
                        <IgIcon size={7} color="#E1306C" />
                        <span className="text-[7px] text-[#555] font-mono">Instagram Feed</span>
                      </div>
                    </motion.div>

                    {/* Facebook Ad */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.2 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#0084FF]/30 transition-colors">
                      <div className="flex items-center gap-2 px-2.5 py-2 border-b border-white/[0.05]">
                        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center">
                          <span className="text-[5px] font-bold text-[#C9A84C]">{initials}</span>
                        </div>
                        <div>
                          <span className="text-[8px] text-white font-semibold block leading-none">{camp.name}</span>
                          <span className="text-[6px] text-[#555]">Sponsored</span>
                        </div>
                        <FbIcon size={8} color="#0084FF" />
                      </div>
                      <div className="px-2.5 py-1.5">
                        <p className="text-[7px] text-[#999] leading-relaxed">{camp.fbText}</p>
                      </div>
                      <img src={camp.wideImg} alt="FB Banner" className="w-full aspect-video object-cover" />
                      <div className="px-2.5 py-1.5">
                        <p className="text-[7px] text-[#888] leading-relaxed">{camp.igCaption.slice(0, 80)}...</p>
                        <p className="text-[6px] text-[#0084FF] mt-1 font-semibold">Learn more</p>
                      </div>
                      <div className="px-2.5 py-1.5 flex items-center justify-between border-t border-white/[0.04]">
                        <div className="flex items-center gap-1">
                          <ThumbsUp size={8} className="text-[#0084FF]" />
                          <span className="text-[7px] text-[#888]">1.8k</span>
                        </div>
                        <span className="text-[7px] text-[#555]">247 shares</span>
                      </div>
                      <div className="px-2.5 pb-2 flex items-center gap-1">
                        <FbIcon size={7} color="#0084FF" />
                        <span className="text-[7px] text-[#555] font-mono">Facebook Ads</span>
                      </div>
                    </motion.div>

                    {/* WhatsApp Story */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.3 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#25D366]/30 transition-colors">
                      <div className="flex items-center gap-2 px-2.5 py-2 border-b border-white/[0.05]">
                        <div className="h-5 w-5 rounded-full bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center">
                          <span className="text-[5px] font-bold text-[#C9A84C]">{initials}</span>
                        </div>
                        <div>
                          <span className="text-[8px] text-white font-semibold block leading-none">{camp.name}</span>
                          <span className="text-[6px] text-[#555]">Business</span>
                        </div>
                        <WaIcon size={8} color="#25D366" />
                      </div>
                      <div className="relative">
                        <img src={camp.storyImg} alt="WA Status" className="w-full aspect-[9/14] object-cover" />
                        <div className="absolute top-0 left-0 right-0 h-1 bg-white/[0.1] rounded-full mx-2 mt-1.5">
                          <div className="h-full w-1/3 bg-[#25D366] rounded-full" />
                        </div>
                      </div>
                      <div className="px-2.5 py-2">
                        <p className="text-[7px] text-[#888] leading-relaxed">{camp.igCaption.slice(0, 100)}...</p>
                      </div>
                      <div className="px-2.5 pb-2 flex items-center gap-1">
                        <WaIcon size={7} color="#25D366" />
                        <span className="text-[7px] text-[#555] font-mono">WhatsApp Status</span>
                      </div>
                    </motion.div>

                    {/* Video / TikTok */}
                    <motion.div initial={{ y: 12, opacity: 0 }} animate={{ y: 0, opacity: 1 }} transition={{ delay: 0.4 }}
                      className="rounded-xl border border-white/[0.08] bg-[#111] overflow-hidden hover:border-[#ff0050]/30 transition-colors">
                      <div className="relative">
                        <video autoPlay muted loop playsInline className="w-full aspect-[9/14] object-cover" poster={camp.feedImg}>
                          <source src={camp.video} type="video/mp4" />
                        </video>
                        <div className="absolute right-2 bottom-12 flex flex-col items-center gap-3">
                          <div className="flex flex-col items-center"><Heart size={12} className="text-white" /><span className="text-[6px] text-white">18.2k</span></div>
                          <div className="flex flex-col items-center"><MessageSquare size={12} className="text-white" /><span className="text-[6px] text-white">943</span></div>
                          <div className="flex flex-col items-center"><Send size={12} className="text-white" /><span className="text-[6px] text-white">612</span></div>
                        </div>
                        <div className="absolute left-2 bottom-2 right-10">
                          <p className="text-[8px] text-white font-semibold">@{camp.handle}</p>
                          <p className="text-[6px] text-white/70">{camp.hashtags.split(' ').slice(0, 3).join(' ')}</p>
                        </div>
                        <div className="absolute top-2 left-2">
                          <div className="flex items-center gap-1 bg-red-500/80 backdrop-blur-sm rounded px-1.5 py-0.5">
                            <div className="h-1 w-1 rounded-full bg-white animate-pulse" />
                            <span className="text-[6px] text-white font-bold">LIVE</span>
                          </div>
                        </div>
                      </div>
                      <div className="px-2.5 pb-2 pt-1.5 flex items-center gap-1">
                        <TkIcon size={7} color="#ff0050" />
                        <span className="text-[7px] text-[#555] font-mono">TikTok / Video</span>
                      </div>
                    </motion.div>
                  </>
                );
              })()}
            </motion.div>
          </AnimatePresence>

          {/* Campaign name + type below cards */}
          <div className="text-center mt-5">
            <p className="text-[13px] font-semibold text-white">{REAL_CAMPAIGNS[activeCamp].name}</p>
            <p className="text-[10px] text-[#C9A84C] font-mono">{REAL_CAMPAIGNS[activeCamp].type}</p>
          </div>
        </div>
      </section>

      {/* ═══ TESTIMONIALS ═══ */}
      <section className="py-14 px-5 relative" data-testid="testimonials-section">
        <TechGrid />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.test_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl">{l.test_title}</h2>
          </motion.div>

          <div className="grid sm:grid-cols-3 gap-3">
            {testimonials.map((t, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.3}>
                <Glass hover className="p-5 h-full flex flex-col">
                  <div className="flex items-center gap-1 mb-3">
                    {[...Array(5)].map((_, si) => (
                      <Star key={si} size={10} className="text-[#C9A84C] fill-[#C9A84C]" />
                    ))}
                  </div>
                  <p className="text-[11px] text-[#999] leading-relaxed flex-1 mb-4">"{t.text}"</p>
                  <div className="flex items-center gap-3 pt-3 border-t border-white/[0.05]">
                    <div className="h-9 w-9 rounded-full overflow-hidden ring-1 ring-white/[0.08]">
                      <img src={t.photo} alt={t.name} className="h-full w-full object-cover" />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold text-white">{t.name}</p>
                      <p className="text-[9px] text-[#555] font-mono">{t.role}</p>
                    </div>
                  </div>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section className="py-14 px-5 relative" data-testid="features-section">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080808] to-transparent" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.feat_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl">{l.feat_title}</h2>
            <p className="text-sm text-[#555] mt-2">{l.feat_sub}</p>
          </motion.div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {features.map((f, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.2}>
                <Glass hover className="p-4 h-full">
                  <div className="h-9 w-9 rounded-lg bg-[#C9A84C]/[0.06] flex items-center justify-center mb-3 border border-[#C9A84C]/[0.08]">
                    <f.icon size={14} className="text-[#C9A84C]" />
                  </div>
                  <h3 className="text-[12px] font-semibold text-white mb-1">{f.title}</h3>
                  <p className="text-[10px] text-[#555] leading-relaxed">{f.desc}</p>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ PRICING ═══ */}
      <section className="py-14 px-5 relative" data-testid="pricing-section">
        <TechGrid />
        <Glow className="h-[300px] w-[400px] top-[30%] left-[30%] bg-[#C9A84C]/[0.02]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-8">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">Pricing</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl">{t('landing.pricing_title')}</h2>
            <p className="text-sm text-[#555] mt-2 mb-5">{t('landing.pricing_subtitle')}</p>
            <div className="inline-flex items-center gap-0.5 rounded-full border border-white/[0.06] bg-white/[0.02] p-0.5">
              <button onClick={() => setBillingAnnual(true)}
                className={`rounded-full px-5 py-2 text-[11px] font-mono font-medium transition-all ${billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A] shadow-lg shadow-[#C9A84C]/15' : 'text-[#666] hover:text-white'}`}>
                {t('landing.billing_annual')} <span className="text-[9px] opacity-70 ml-0.5">{t('landing.billing_save')}</span>
              </button>
              <button onClick={() => setBillingAnnual(false)}
                className={`rounded-full px-5 py-2 text-[11px] font-mono font-medium transition-all ${!billingAnnual ? 'bg-[#C9A84C] text-[#0A0A0A] shadow-lg shadow-[#C9A84C]/15' : 'text-[#666] hover:text-white'}`}>
                {t('landing.billing_monthly')}
              </button>
            </div>
          </motion.div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 pt-4">
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
                    <div className="rounded-2xl bg-[#090909] h-full flex flex-col pt-7 px-5 pb-5 relative">
                      <div className="absolute inset-0 bg-gradient-to-b from-[#C9A84C]/[0.03] to-transparent pointer-events-none rounded-2xl" />
                      <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 rounded-full bg-[#C9A84C] px-3 py-1 text-[9px] font-mono font-bold text-[#0A0A0A] shadow-lg shadow-[#C9A84C]/20 whitespace-nowrap">{plan.badge}</div>
                      <div className="relative z-10 flex flex-col h-full">
                        <h3 className="text-sm font-bold text-white mb-0.5">{plan.name}</h3>
                        <p className="text-[10px] text-[#555] font-mono mb-3">{plan.desc}</p>
                        <div className="mb-3"><span className="text-2xl font-bold text-white font-mono">{plan.price}</span><span className="text-[10px] text-[#555]">{plan.period}</span></div>
                        <ul className="flex-1 space-y-1.5 mb-4">{plan.feats.map((f, j) => <li key={j} className="flex items-start gap-2 text-[10px] text-[#666]"><Check size={10} className="text-[#C9A84C] mt-0.5 flex-shrink-0" />{f}</li>)}</ul>
                        <button className="btn-gold w-full rounded-xl py-2.5 text-[12px] font-semibold">{plan.cta}</button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={`relative rounded-2xl border backdrop-blur-xl transition-all duration-500
                    border-white/[0.06] bg-white/[0.015] hover:border-[#C9A84C]/20 hover:bg-white/[0.03]
                    flex flex-col ${plan.badge ? 'pt-7 px-5 pb-5' : 'p-5'} h-full`}>
                    {plan.badge && <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-10 rounded-full border border-[#C9A84C]/15 bg-[#060606] px-3 py-1 text-[9px] font-mono text-[#C9A84C] whitespace-nowrap">{plan.badge}</div>}
                    <h3 className="text-sm font-bold text-white mb-0.5">{plan.name}</h3>
                    <p className="text-[10px] text-[#555] font-mono mb-3">{plan.desc}</p>
                    <div className="mb-3"><span className="text-2xl font-bold text-white font-mono">{plan.price}</span><span className="text-[10px] text-[#555]">{plan.period}</span></div>
                    <ul className="flex-1 space-y-1.5 mb-4">{plan.feats.map((f, j) => <li key={j} className="flex items-start gap-2 text-[10px] text-[#666]"><Check size={10} className="text-[#C9A84C] mt-0.5 flex-shrink-0" />{f}</li>)}</ul>
                    {plan.note && <p className="text-center text-[9px] text-[#555] font-mono mb-2">{plan.note}</p>}
                    <button className="btn-gold w-full rounded-xl py-2.5 text-[12px] font-semibold">{plan.cta}</button>
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CTA ═══ */}
      <section className="py-20 px-5 relative" data-testid="cta-section">
        <Glow className="h-[200px] w-[300px] top-[40%] left-[40%] bg-[#C9A84C]/[0.03]" />
        <div className="relative z-10 mx-auto max-w-2xl text-center">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade}>
            <h2 className="text-3xl font-bold text-white mb-3 sm:text-4xl leading-tight">{l.cta_title}</h2>
            <p className="text-[14px] text-[#555] mb-6">{l.cta_sub}</p>
            <button onClick={() => navigate('/login?tab=signup')} data-testid="final-cta-btn"
              className="btn-gold rounded-xl px-10 py-3.5 text-sm font-semibold inline-flex items-center gap-2 group shadow-lg shadow-[#C9A84C]/10 hover:shadow-[#C9A84C]/25 transition-shadow">
              {l.cta} <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-white/[0.04] px-5 py-5">
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
