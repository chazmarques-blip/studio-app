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
function AgentChat() {
  const [msgs, setMsgs] = useState([]);
  const [typing, setTyping] = useState(false);
  const ref = useRef(null);
  const convo = [
    { from: 'user', text: 'Preciso agendar uma consulta para amanha' },
    { from: 'agent', text: 'Vou verificar os horarios! Manha ou tarde?' },
    { from: 'user', text: 'Pela manha' },
    { from: 'agent', text: 'Perfeito! 9h ou 10h30 — qual prefere?' },
    { from: 'user', text: '9h!' },
    { from: 'agent', text: 'Agendado! Confirmacao enviada no seu WhatsApp.' },
  ];
  useEffect(() => {
    let i = 0, cancel = false;
    const go = () => {
      if (cancel) return;
      if (i >= convo.length) { setTimeout(() => { if (!cancel) { setMsgs([]); i = 0; go(); } }, 3000); return; }
      const m = convo[i];
      if (m.from === 'agent') {
        setTyping(true);
        setTimeout(() => { if (cancel) return; setTyping(false); setMsgs(p => [...p, m]); i++; setTimeout(go, 1500); }, 1200);
      } else { setMsgs(p => [...p, m]); i++; setTimeout(go, 1200); }
    };
    setTimeout(go, 600);
    return () => { cancel = true; };
  }, []);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [msgs, typing]);

  return (
    <div className="rounded-2xl border border-white/[0.07] bg-[#0A0A0A] overflow-hidden shadow-2xl shadow-black/60">
      <div className="flex items-center gap-3 border-b border-white/[0.06] px-4 py-2.5 bg-white/[0.02]">
        <div className="relative">
          <div className="h-8 w-8 rounded-full overflow-hidden ring-2 ring-[#C9A84C]/20">
            <img src={AVATARS.Sarah} alt="Sarah" className="h-full w-full object-cover" />
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-400 border-2 border-[#0A0A0A]" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[11px] font-semibold text-white">Sarah</p>
          <p className="text-[8px] text-emerald-400/80 font-mono">WhatsApp</p>
        </div>
        <WaIcon size={14} color="#25D366" />
      </div>
      <div ref={ref} className="h-[170px] overflow-y-auto px-3 py-2.5 space-y-2" style={{ scrollbarWidth: 'none' }}>
        {msgs.map((m, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
            className={`flex gap-1.5 ${m.from === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.from === 'agent' && (
              <div className="h-5 w-5 rounded-full overflow-hidden flex-shrink-0 mt-1 ring-1 ring-[#C9A84C]/10">
                <img src={AVATARS.Sarah} alt="" className="h-full w-full object-cover" />
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
              <img src={AVATARS.Sarah} alt="" className="h-full w-full object-cover" />
            </div>
            <div className="rounded-xl bg-white/[0.03] border border-white/[0.06] px-3 py-2">
              <div className="flex gap-1">{[0, 120, 240].map(d => <div key={d} className="h-1 w-1 animate-bounce rounded-full bg-[#C9A84C]/40" style={{ animationDelay: `${d}ms` }} />)}</div>
            </div>
          </div>
        )}
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

  const campaigns = [
    { name: lang === 'pt' ? 'Black Friday Tech' : 'Black Friday Tech', type: 'E-commerce', impressions: '45.2k', conversions: '3.8%', leads: '1,720', channels: ['Instagram', 'WhatsApp', 'Facebook'] },
    { name: lang === 'pt' ? 'Lancamento FitLife Pro' : 'FitLife Pro Launch', type: 'SaaS', impressions: '28.6k', conversions: '5.1%', leads: '892', channels: ['Instagram', 'TikTok', 'YouTube'] },
    { name: lang === 'pt' ? 'Promocao Verao Moda' : 'Summer Fashion Promo', type: lang === 'pt' ? 'Moda' : 'Fashion', impressions: '62.1k', conversions: '4.3%', leads: '2,340', channels: ['Instagram', 'WhatsApp'] },
  ];

  const current = agents[activeAgent];

  useEffect(() => {
    const i1 = setInterval(() => setActiveAgent(p => (p + 1) % agents.length), 5000);
    const i2 = setInterval(() => setActiveStep(p => (p + 1) % pipelineSteps.length), 2000);
    return () => { clearInterval(i1); clearInterval(i2); };
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
              className="flex items-center gap-2 rounded-xl border border-white/[0.07] bg-white/[0.02] px-7 py-3 text-sm text-[#888] hover:text-white hover:border-white/[0.12] transition-all">
              {l.demo}
            </button>
          </motion.div>

          {/* Hero 3 panels */}
          <motion.div initial="hidden" animate="visible" variants={fade} custom={4}
            className="grid grid-cols-1 md:grid-cols-3 gap-3 max-w-4xl mx-auto">
            <Glass hover className="p-4">
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
              <div className="space-y-1.5 mb-2">
                {['WhatsApp', 'Instagram', 'Telegram'].map(ch => (
                  <div key={ch} className="flex items-center gap-2 px-2 py-1 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                    <div className="h-1.5 w-1.5 rounded-full bg-[#C9A84C]/60" />
                    <span className="text-[8px] text-[#888] font-mono">{ch}</span>
                    <span className="ml-auto text-[7px] text-emerald-400/70 font-mono">Active</span>
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-1 text-[8px] text-[#C9A84C]/60 font-mono">
                <Sparkles size={8} /> 847 conversations
              </div>
            </Glass>

            <div className="md:translate-y-[-12px]"><AgentChat /></div>

            <Glass hover className="p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center border border-[#C9A84C]/10">
                  <Megaphone size={14} className="text-[#C9A84C]" />
                </div>
                <div>
                  <p className="text-[10px] font-semibold text-white">Campaign</p>
                  <p className="text-[8px] text-[#555] font-mono">AI Studio</p>
                </div>
              </div>
              <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2.5 mb-2.5">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="text-[8px] text-[#888] font-mono">Impressions</span>
                  <span className="text-[8px] text-emerald-400 font-mono">+24%</span>
                </div>
                <div className="flex gap-0.5 items-end h-7">
                  {[30, 45, 38, 52, 48, 65, 58, 72, 68, 85, 78, 92].map((h, i) => (
                    <div key={i} className="flex-1 rounded-sm bg-gradient-to-t from-[#C9A84C]/30 to-[#C9A84C]/10" style={{ height: `${h}%` }} />
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-1.5 text-center">
                  <p className="text-[10px] font-bold text-white font-mono">12.4k</p>
                  <p className="text-[7px] text-[#555] font-mono">Leads</p>
                </div>
                <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-1.5 text-center">
                  <p className="text-[10px] font-bold text-[#C9A84C] font-mono">4.2%</p>
                  <p className="text-[7px] text-[#555] font-mono">Conv.</p>
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
                  <Glass className="p-5">
                    <div className="flex items-center gap-3 mb-5">
                      <div className="h-14 w-14 rounded-xl overflow-hidden ring-2 ring-[#C9A84C]/20">
                        <img src={current.avatar} alt={current.name} className="h-full w-full object-cover" />
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-white">{current.name}</h3>
                        <p className="text-[10px] text-[#C9A84C] font-mono">{current.role}</p>
                      </div>
                      <div className="ml-auto flex items-center gap-1.5 rounded-full border border-emerald-400/15 bg-emerald-400/[0.05] px-2.5 py-1">
                        <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                        <span className="text-[8px] text-emerald-400 font-mono">Online</span>
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-[8px] font-mono text-[#555] uppercase tracking-widest mb-2"><Brain size={8} className="inline mr-1 text-[#C9A84C]" />Habilidades</p>
                      <div className="flex flex-wrap gap-1.5">
                        {current.skills.map((skill, si) => (
                          <motion.div key={si} initial={{ opacity: 0, scale: 0.9 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: si * 0.05 }}
                            className="flex items-center gap-1 rounded-full border border-[#C9A84C]/10 bg-[#C9A84C]/[0.04] px-2.5 py-1">
                            <Star size={8} className="text-[#C9A84C]" />
                            <span className="text-[8px] font-mono text-[#C9A84C]/80">{skill}</span>
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-[8px] font-mono text-[#555] uppercase tracking-widest mb-2"><Globe size={8} className="inline mr-1 text-[#C9A84C]" />{l.ag_channels}</p>
                      <div className="flex gap-1.5">
                        {current.channels.map((ch, ci) => (
                          <div key={ci} className="flex items-center gap-1 rounded-lg border border-white/[0.06] bg-white/[0.02] px-2.5 py-1">
                            <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                            <span className="text-[9px] text-[#888] font-mono">{ch}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="rounded-xl border border-white/[0.05] bg-white/[0.01] p-3.5">
                      <div className="flex items-center gap-2 mb-2.5">
                        <Sliders size={11} className="text-[#C9A84C]" />
                        <p className="text-[10px] font-semibold text-white">{l.config_title}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        {[
                          { icon: Brain, label: l.ag_personality, value: current.role },
                          { icon: Layers, label: l.ag_knowledge, value: '3 docs' },
                          { icon: Languages, label: l.ag_lang, value: 'PT, EN, ES' },
                          { icon: Clock, label: l.ag_rules, value: '24/7' },
                        ].map((cfg, ci) => (
                          <div key={ci} className="rounded-lg border border-white/[0.04] bg-white/[0.02] p-2">
                            <div className="flex items-center gap-1 mb-0.5">
                              <cfg.icon size={8} className="text-[#C9A84C]/60" />
                              <span className="text-[7px] text-[#555] font-mono uppercase">{cfg.label}</span>
                            </div>
                            <p className="text-[9px] text-white font-medium">{cfg.value}</p>
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

      {/* ═══ AI MARKETING STUDIO ═══ */}
      <section className="py-16 px-5 relative overflow-hidden" data-testid="ai-studio-section">
        <Glow className="h-[300px] w-[400px] top-[10%] left-[-80px] bg-[#C9A84C]/[0.03]" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.ai_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{l.ai_title}<span className="text-[#C9A84C]">{l.ai_title2}</span></h2>
            <p className="text-sm text-[#555] max-w-lg mx-auto mt-2">{l.ai_sub}</p>
          </motion.div>

          {/* Animated Pipeline */}
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade}
            className="mb-8">
            <Glass className="p-5">
              <div className="flex items-center justify-between">
                {pipelineSteps.map((step, si) => (
                  <div key={si} className="flex items-center gap-2 sm:gap-3">
                    <PipelineStep icon={step.icon} label={step.label} color={step.color} active={activeStep === si} delay={si * 0.08} />
                    {si < pipelineSteps.length - 1 && (
                      <div className={`hidden sm:block transition-colors duration-500 ${activeStep > si ? 'text-[#C9A84C]/40' : 'text-[#333]'}`}>
                        <ChevronRight size={14} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Glass>
          </motion.div>

          {/* 4 Steps detail */}
          <div className="grid sm:grid-cols-2 gap-3">
            {studioSteps.map((step, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.4}>
                <Glass hover className="p-4 flex gap-3 items-start h-full">
                  <div className="h-11 w-11 rounded-xl bg-[#C9A84C]/[0.06] flex items-center justify-center flex-shrink-0 border border-[#C9A84C]/[0.08]">
                    <step.icon size={18} className="text-[#C9A84C]" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[8px] font-mono text-[#C9A84C]/50 bg-[#C9A84C]/[0.06] rounded px-1.5 py-0.5">0{i + 1}</span>
                      <h3 className="text-[12px] font-semibold text-white">{step.title}</h3>
                    </div>
                    <p className="text-[10px] text-[#555] leading-relaxed">{step.desc}</p>
                  </div>
                </Glass>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ CAMPAIGNS SHOWCASE ═══ */}
      <section className="py-14 px-5 relative" data-testid="campaigns-section">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#080808] to-transparent" />
        <div className="relative z-10 mx-auto max-w-5xl">
          <motion.div initial="hidden" whileInView="visible" viewport={{ once: true, margin: '-40px' }} variants={fade} className="text-center mb-10">
            <p className="text-[9px] font-mono font-semibold text-[#C9A84C] tracking-[0.3em] uppercase mb-2">{l.camp_tag}</p>
            <h2 className="text-2xl font-bold text-white sm:text-3xl lg:text-4xl">{l.camp_title}<span className="text-[#C9A84C]">{l.camp_title2}</span></h2>
            <p className="text-sm text-[#555] max-w-md mx-auto mt-2">{l.camp_sub}</p>
          </motion.div>

          <div className="grid sm:grid-cols-3 gap-3">
            {campaigns.map((camp, i) => (
              <motion.div key={i} initial="hidden" whileInView="visible" viewport={{ once: true }} variants={fade} custom={i * 0.3}>
                <Glass hover className="p-4 h-full">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <p className="text-[12px] font-semibold text-white">{camp.name}</p>
                      <p className="text-[8px] text-[#C9A84C] font-mono">{camp.type}</p>
                    </div>
                    <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-[#C9A84C]/20 to-[#C9A84C]/5 flex items-center justify-center border border-[#C9A84C]/10">
                      <BarChart2 size={14} className="text-[#C9A84C]" />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 mb-3">
                    <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2 text-center">
                      <p className="text-[10px] font-bold text-white font-mono">{camp.impressions}</p>
                      <p className="text-[7px] text-[#555] font-mono">Impressions</p>
                    </div>
                    <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2 text-center">
                      <p className="text-[10px] font-bold text-emerald-400 font-mono">{camp.conversions}</p>
                      <p className="text-[7px] text-[#555] font-mono">Conv.</p>
                    </div>
                    <div className="rounded-lg bg-white/[0.02] border border-white/[0.04] p-2 text-center">
                      <p className="text-[10px] font-bold text-[#C9A84C] font-mono">{camp.leads}</p>
                      <p className="text-[7px] text-[#555] font-mono">Leads</p>
                    </div>
                  </div>
                  <div className="flex gap-1.5">
                    {camp.channels.map((ch, ci) => (
                      <span key={ci} className="text-[7px] font-mono text-[#666] border border-white/[0.05] rounded px-1.5 py-0.5 bg-white/[0.02]">{ch}</span>
                    ))}
                  </div>
                </Glass>
              </motion.div>
            ))}
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
