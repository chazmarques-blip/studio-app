import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, Check, Sparkles, Building2, Target, MessageCircle, Briefcase, Bot, Loader2, RefreshCw, Rocket, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SEGMENTS = [
  { id: 'ecommerce', icon: '🛒', label: { pt: 'E-commerce', en: 'E-commerce', es: 'E-commerce' } },
  { id: 'restaurant', icon: '🍽️', label: { pt: 'Restaurante', en: 'Restaurant', es: 'Restaurante' } },
  { id: 'health', icon: '🏥', label: { pt: 'Saude', en: 'Healthcare', es: 'Salud' } },
  { id: 'beauty', icon: '💇', label: { pt: 'Beleza & Estetica', en: 'Beauty & Spa', es: 'Belleza' } },
  { id: 'real_estate', icon: '🏠', label: { pt: 'Imobiliaria', en: 'Real Estate', es: 'Inmobiliaria' } },
  { id: 'automotive', icon: '🚗', label: { pt: 'Automotivo', en: 'Automotive', es: 'Automotriz' } },
  { id: 'education', icon: '📚', label: { pt: 'Educacao', en: 'Education', es: 'Educacion' } },
  { id: 'finance', icon: '💰', label: { pt: 'Financeiro', en: 'Finance', es: 'Finanzas' } },
  { id: 'travel', icon: '✈️', label: { pt: 'Turismo & Viagem', en: 'Travel & Tourism', es: 'Turismo' } },
  { id: 'fitness', icon: '🏋️', label: { pt: 'Fitness & Academia', en: 'Fitness & Gym', es: 'Fitness' } },
  { id: 'legal', icon: '⚖️', label: { pt: 'Juridico', en: 'Legal', es: 'Legal' } },
  { id: 'events', icon: '🎉', label: { pt: 'Eventos', en: 'Events', es: 'Eventos' } },
  { id: 'saas', icon: '💻', label: { pt: 'SaaS / Tecnologia', en: 'SaaS / Tech', es: 'SaaS / Tech' } },
  { id: 'logistics', icon: '📦', label: { pt: 'Logistica', en: 'Logistics', es: 'Logistica' } },
  { id: 'telecom', icon: '📱', label: { pt: 'Telecom', en: 'Telecom', es: 'Telecom' } },
  { id: 'general', icon: '🏢', label: { pt: 'Outro', en: 'Other', es: 'Otro' } },
];

const OBJECTIVES = [
  { id: 'sales', icon: Target, label: { pt: 'Vender', en: 'Sell', es: 'Vender' }, desc: { pt: 'Qualificar leads, apresentar produtos, fechar vendas', en: 'Qualify leads, present products, close deals', es: 'Calificar leads, presentar productos, cerrar ventas' } },
  { id: 'support', icon: MessageCircle, label: { pt: 'Dar Suporte', en: 'Support', es: 'Soporte' }, desc: { pt: 'Resolver problemas, tirar duvidas, troubleshooting', en: 'Resolve issues, answer questions, troubleshoot', es: 'Resolver problemas, responder preguntas' } },
  { id: 'scheduling', icon: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>, label: { pt: 'Agendar', en: 'Schedule', es: 'Agendar' }, desc: { pt: 'Marcar consultas, reunioes, lembretes', en: 'Book appointments, meetings, reminders', es: 'Agendar citas, reuniones, recordatorios' } },
  { id: 'sac', icon: () => <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>, label: { pt: 'SAC / Reclamacoes', en: 'Customer Service', es: 'SAC' }, desc: { pt: 'Reclamacoes, devolucoes, reembolsos', en: 'Complaints, returns, refunds', es: 'Quejas, devoluciones, reembolsos' } },
  { id: 'onboarding', icon: Rocket, label: { pt: 'Onboarding', en: 'Onboarding', es: 'Onboarding' }, desc: { pt: 'Boas-vindas, setup guiado, primeiros passos', en: 'Welcome, guided setup, first steps', es: 'Bienvenida, configuracion guiada' } },
];

const TONES = [
  { id: 'professional', label: { pt: 'Profissional', en: 'Professional', es: 'Profesional' }, desc: { pt: 'Formal e respeitoso', en: 'Formal and respectful', es: 'Formal y respetuoso' }, example: { pt: 'Bom dia. Como posso ajuda-lo?', en: 'Good morning. How may I help you?', es: 'Buenos dias. Como puedo ayudarle?' } },
  { id: 'friendly', label: { pt: 'Amigavel', en: 'Friendly', es: 'Amigable' }, desc: { pt: 'Casual e acolhedor', en: 'Casual and welcoming', es: 'Casual y acogedor' }, example: { pt: 'Oi! Que bom te ver por aqui! Como posso te ajudar?', en: 'Hi! Great to see you! How can I help?', es: 'Hola! Que bueno verte! Como puedo ayudarte?' } },
  { id: 'empathetic', label: { pt: 'Empatico', en: 'Empathetic', es: 'Empatico' }, desc: { pt: 'Compreensivo e acolhedor', en: 'Understanding and caring', es: 'Comprensivo y acogedor' }, example: { pt: 'Entendo sua situacao. Estou aqui para ajudar!', en: 'I understand your situation. I\'m here to help!', es: 'Entiendo tu situacion. Estoy aqui para ayudarte!' } },
  { id: 'direct', label: { pt: 'Direto', en: 'Direct', es: 'Directo' }, desc: { pt: 'Claro e objetivo', en: 'Clear and to the point', es: 'Claro y directo' }, example: { pt: 'Ola. Me diga o que precisa.', en: 'Hello. Tell me what you need.', es: 'Hola. Dime que necesitas.' } },
  { id: 'consultive', label: { pt: 'Consultivo', en: 'Consultive', es: 'Consultivo' }, desc: { pt: 'Pergunta antes de sugerir', en: 'Asks before suggesting', es: 'Pregunta antes de sugerir' }, example: { pt: 'Para te ajudar melhor, posso fazer algumas perguntas?', en: 'To help you better, may I ask a few questions?', es: 'Para ayudarte mejor, puedo hacerte algunas preguntas?' } },
];

const STEP_LABELS = {
  pt: ['Segmento', 'Objetivo', 'Tom', 'Negocio', 'Gerar'],
  en: ['Segment', 'Objective', 'Tone', 'Business', 'Generate'],
  es: ['Segmento', 'Objetivo', 'Tono', 'Negocio', 'Generar'],
};

export default function AgentBuilder() {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const lang = i18n.language || 'pt';
  const [step, setStep] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [generatedAgent, setGeneratedAgent] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);

  const [form, setForm] = useState({
    segment: '',
    objective: '',
    tone: '',
    business_name: '',
    business_description: '',
    products_services: '',
    hours: '',
    differentials: '',
    target_audience: '',
  });

  const set = (key, val) => setForm(p => ({ ...p, [key]: val }));
  const steps = STEP_LABELS[lang] || STEP_LABELS.pt;

  const canNext = () => {
    if (step === 0) return !!form.segment;
    if (step === 1) return !!form.objective;
    if (step === 2) return !!form.tone;
    if (step === 3) return !!form.business_name && !!form.business_description;
    return true;
  };

  const generateAgent = async () => {
    setGenerating(true);
    try {
      const { data } = await axios.post(`${API}/agents/generate-preview`, {
        ...form,
        language: lang,
      });
      setGeneratedAgent(data);
      setStep(4);
    } catch (err) {
      toast.error(lang === 'pt' ? 'Erro ao gerar agente. Tente novamente.' : 'Error generating agent. Try again.');
    } finally {
      setGenerating(false);
    }
  };

  const deployAgent = async () => {
    if (!generatedAgent) return;
    setDeploying(true);
    try {
      const { data } = await axios.post(`${API}/agents/deploy-generated`, {
        ...generatedAgent,
        objective: form.objective,
        tone: form.tone,
        language: lang,
      });
      toast.success(lang === 'pt' ? 'Agente criado com sucesso!' : 'Agent created successfully!');
      navigate(`/agents/${data.id}/config`);
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : (lang === 'pt' ? 'Erro ao publicar agente' : 'Error deploying agent'));
    } finally {
      setDeploying(false);
    }
  };

  const handleNext = () => {
    if (step === 3) {
      generateAgent();
    } else if (step < 4) {
      setStep(s => s + 1);
    }
  };

  const T = (pt, en) => lang === 'pt' ? pt : (lang === 'es' ? pt : en);

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-28">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-4 py-3">
        <div className="flex items-center gap-3">
          <button data-testid="builder-back-btn" onClick={() => navigate('/agents')} className="text-[#666] hover:text-white transition">
            <ArrowLeft size={18} />
          </button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10">
            <Sparkles size={16} className="text-[#C9A84C]" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">{T('Criar Agente com IA', 'Create Agent with AI')}</h1>
            <p className="text-[9px] text-[#555]">{T('Questionario inteligente', 'Smart questionnaire')}</p>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between">
          {steps.map((s, i) => (
            <div key={i} className="flex items-center">
              <div className={`flex h-7 w-7 items-center justify-center rounded-full text-[10px] font-bold transition-all ${
                i < step ? 'bg-[#C9A84C] text-[#0A0A0A]' :
                i === step ? 'bg-[#C9A84C]/20 text-[#C9A84C] ring-2 ring-[#C9A84C]/30' :
                'bg-[#1A1A1A] text-[#555]'
              }`}>
                {i < step ? <Check size={12} /> : i + 1}
              </div>
              {i < steps.length - 1 && (
                <div className={`mx-1 h-px w-6 sm:w-10 ${i < step ? 'bg-[#C9A84C]' : 'bg-[#1A1A1A]'}`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-1 px-0.5">
          {steps.map((s, i) => (
            <span key={i} className={`text-[8px] ${i <= step ? 'text-[#C9A84C]' : 'text-[#444]'}`}>{s}</span>
          ))}
        </div>
      </div>

      <div className="px-4 pt-2">

        {/* ══════ STEP 0: SEGMENT ══════ */}
        {step === 0 && (
          <div>
            <h2 className="mb-1 text-base font-bold text-white">{T('Qual o segmento do seu negocio?', 'What is your business segment?')}</h2>
            <p className="mb-4 text-xs text-[#666]">{T('Isso ajuda a IA a entender o contexto do seu mercado', 'This helps the AI understand your market context')}</p>
            <div className="grid grid-cols-2 gap-2">
              {SEGMENTS.map(seg => (
                <button key={seg.id} data-testid={`seg-${seg.id}`} onClick={() => set('segment', seg.id)}
                  className={`flex items-center gap-2.5 rounded-xl border p-3 text-left transition-all ${
                    form.segment === seg.id
                      ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8 shadow-[0_0_15px_rgba(201,168,76,0.08)]'
                      : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#2A2A2A]'
                  }`}>
                  <span className="text-lg">{seg.icon}</span>
                  <span className={`text-xs font-medium ${form.segment === seg.id ? 'text-[#C9A84C]' : 'text-[#999]'}`}>
                    {seg.label[lang] || seg.label.pt}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ══════ STEP 1: OBJECTIVE ══════ */}
        {step === 1 && (
          <div>
            <h2 className="mb-1 text-base font-bold text-white">{T('Qual o objetivo principal do agente?', 'What is the agent\'s main objective?')}</h2>
            <p className="mb-4 text-xs text-[#666]">{T('O que ele deve fazer de melhor', 'What should it do best')}</p>
            <div className="space-y-2">
              {OBJECTIVES.map(obj => {
                const Icon = obj.icon;
                return (
                  <button key={obj.id} data-testid={`obj-${obj.id}`} onClick={() => set('objective', obj.id)}
                    className={`flex w-full items-center gap-3 rounded-xl border p-4 text-left transition-all ${
                      form.objective === obj.id
                        ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8'
                        : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#2A2A2A]'
                    }`}>
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg shrink-0 ${
                      form.objective === obj.id ? 'bg-[#C9A84C]/20' : 'bg-[#1A1A1A]'
                    }`}>
                      <Icon size={20} className={form.objective === obj.id ? 'text-[#C9A84C]' : 'text-[#666]'} />
                    </div>
                    <div>
                      <p className={`text-sm font-semibold ${form.objective === obj.id ? 'text-[#C9A84C]' : 'text-white'}`}>
                        {obj.label[lang] || obj.label.pt}
                      </p>
                      <p className="text-[10px] text-[#666]">{obj.desc[lang] || obj.desc.pt}</p>
                    </div>
                    {form.objective === obj.id && <Check size={16} className="ml-auto text-[#C9A84C] shrink-0" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* ══════ STEP 2: TONE ══════ */}
        {step === 2 && (
          <div>
            <h2 className="mb-1 text-base font-bold text-white">{T('Qual o tom ideal?', 'What is the ideal tone?')}</h2>
            <p className="mb-4 text-xs text-[#666]">{T('Como o agente deve se comunicar com seus clientes', 'How should the agent communicate with your customers')}</p>
            <div className="space-y-2">
              {TONES.map(t => (
                <button key={t.id} data-testid={`tone-${t.id}`} onClick={() => set('tone', t.id)}
                  className={`w-full rounded-xl border p-4 text-left transition-all ${
                    form.tone === t.id
                      ? 'border-[#C9A84C]/50 bg-[#C9A84C]/8'
                      : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#2A2A2A]'
                  }`}>
                  <div className="flex items-center justify-between mb-1.5">
                    <p className={`text-sm font-semibold ${form.tone === t.id ? 'text-[#C9A84C]' : 'text-white'}`}>
                      {t.label[lang] || t.label.pt}
                    </p>
                    {form.tone === t.id && <Check size={14} className="text-[#C9A84C]" />}
                  </div>
                  <p className="text-[10px] text-[#666] mb-2">{t.desc[lang] || t.desc.pt}</p>
                  <div className="rounded-lg bg-[#111] border border-[#1A1A1A] px-3 py-2">
                    <p className="text-[10px] text-[#C9A84C]/50 mb-0.5">{T('Exemplo:', 'Example:')}</p>
                    <p className="text-[11px] text-[#888] italic">"{t.example[lang] || t.example.pt}"</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* ══════ STEP 3: BUSINESS INFO ══════ */}
        {step === 3 && (
          <div>
            <h2 className="mb-1 text-base font-bold text-white">{T('Informacoes do seu negocio', 'Your business information')}</h2>
            <p className="mb-4 text-xs text-[#666]">{T('Quanto mais detalhes, melhor sera o agente gerado', 'The more details, the better the generated agent')}</p>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-[10px] font-medium text-[#888]">{T('Nome da empresa *', 'Company name *')}</label>
                <input data-testid="biz-name" value={form.business_name} onChange={e => set('business_name', e.target.value)}
                  placeholder={T('Ex: Clinica Sorriso', 'Ex: Smile Clinic')}
                  className="w-full rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3.5 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/40" />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-medium text-[#888]">{T('Descricao do negocio *', 'Business description *')}</label>
                <textarea data-testid="biz-desc" value={form.business_description} onChange={e => set('business_description', e.target.value)} rows={2}
                  placeholder={T('Ex: Clinica odontologica especializada em implantes e estetica dental', 'Ex: Dental clinic specialized in implants and cosmetic dentistry')}
                  className="w-full rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3.5 py-2.5 text-sm text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/40" />
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-medium text-[#888]">{T('Produtos/Servicos oferecidos', 'Products/Services offered')}</label>
                <textarea data-testid="biz-products" value={form.products_services} onChange={e => set('products_services', e.target.value)} rows={2}
                  placeholder={T('Ex: Implantes, clareamento, ortodontia, limpeza', 'Ex: Implants, whitening, orthodontics, cleaning')}
                  className="w-full rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3.5 py-2.5 text-sm text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/40" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="mb-1 block text-[10px] font-medium text-[#888]">{T('Horario de funcionamento', 'Operating hours')}</label>
                  <input value={form.hours} onChange={e => set('hours', e.target.value)}
                    placeholder={T('Ex: Seg-Sex 8h-18h', 'Ex: Mon-Fri 8am-6pm')}
                    className="w-full rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2.5 text-xs text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/40" />
                </div>
                <div>
                  <label className="mb-1 block text-[10px] font-medium text-[#888]">{T('Publico-alvo', 'Target audience')}</label>
                  <input value={form.target_audience} onChange={e => set('target_audience', e.target.value)}
                    placeholder={T('Ex: Adultos 25-55 anos', 'Ex: Adults 25-55')}
                    className="w-full rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2.5 text-xs text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/40" />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-[10px] font-medium text-[#888]">{T('Diferenciais do negocio', 'Business differentials')}</label>
                <input value={form.differentials} onChange={e => set('differentials', e.target.value)}
                  placeholder={T('Ex: 20 anos de experiencia, tecnologia 3D, parcelamento em 12x', 'Ex: 20 years experience, 3D technology, 12x installment')}
                  className="w-full rounded-xl border border-[#1E1E1E] bg-[#0D0D0D] px-3.5 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/40" />
              </div>
            </div>
          </div>
        )}

        {/* ══════ STEP 4: GENERATING / RESULT ══════ */}
        {step === 4 && generating && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="relative mb-6">
              <div className="h-20 w-20 rounded-2xl bg-[#C9A84C]/10 flex items-center justify-center">
                <Sparkles size={32} className="text-[#C9A84C] animate-pulse" />
              </div>
              <div className="absolute -inset-3 rounded-3xl border border-[#C9A84C]/20 animate-ping" style={{ animationDuration: '2s' }} />
            </div>
            <h2 className="mb-2 text-lg font-bold text-white">{T('Gerando seu agente...', 'Generating your agent...')}</h2>
            <p className="text-xs text-[#666] max-w-[280px]">{T('A IA esta criando um agente personalizado para o seu negocio. Isso leva alguns segundos.', 'AI is creating a personalized agent for your business. This takes a few seconds.')}</p>
            <Loader2 size={20} className="mt-4 text-[#C9A84C] animate-spin" />
          </div>
        )}

        {step === 4 && !generating && generatedAgent && (
          <div className="space-y-3">
            {/* Agent Card */}
            <div className="rounded-xl border border-[#C9A84C]/20 bg-[#C9A84C]/5 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="h-12 w-12 rounded-xl bg-[#C9A84C]/15 flex items-center justify-center">
                  <Bot size={24} className="text-[#C9A84C]" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{generatedAgent.agent_name}</h3>
                  <p className="text-[10px] text-[#888]">{form.business_name} · {OBJECTIVES.find(o => o.id === form.objective)?.label[lang]}</p>
                </div>
                <div className="ml-auto rounded-full bg-[#C9A84C]/10 px-2 py-0.5">
                  <span className="text-[9px] font-semibold text-[#C9A84C]">{T('GERADO POR IA', 'AI GENERATED')}</span>
                </div>
              </div>
              <p className="text-xs text-[#999] leading-relaxed">{generatedAgent.description}</p>
              {generatedAgent.generation_time_ms && (
                <p className="mt-2 text-[9px] text-[#444]">{T('Gerado em', 'Generated in')} {(generatedAgent.generation_time_ms / 1000).toFixed(1)}s</p>
              )}
            </div>

            {/* Sample Conversation */}
            {generatedAgent.sample_conversation?.length > 0 && (
              <div>
                <h4 className="mb-2 text-[10px] font-semibold text-[#888] uppercase tracking-wider">{T('Conversa de Exemplo', 'Sample Conversation')}</h4>
                <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 space-y-2">
                  {generatedAgent.sample_conversation.map((msg, i) => (
                    <div key={i} className={`flex ${msg.role === 'customer' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[85%] rounded-2xl px-3 py-2 ${
                        msg.role === 'customer'
                          ? 'bg-[#1A1A1A] border border-[#2A2A2A]'
                          : 'bg-[#C9A84C]/8 border border-[#C9A84C]/15'
                      }`}>
                        <p className={`text-[10px] font-medium mb-0.5 ${msg.role === 'customer' ? 'text-[#666]' : 'text-[#C9A84C]/70'}`}>
                          {msg.role === 'customer' ? T('Cliente', 'Customer') : generatedAgent.agent_name}
                        </p>
                        <p className="text-[11px] text-[#999]">{msg.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* System Prompt (collapsible) */}
            <div>
              <button data-testid="toggle-prompt" onClick={() => setShowPrompt(!showPrompt)}
                className="flex w-full items-center gap-2 text-left mb-2">
                <h4 className="text-[10px] font-semibold text-[#888] uppercase tracking-wider">{T('System Prompt Gerado', 'Generated System Prompt')}</h4>
                <ChevronDown size={12} className={`text-[#555] transition-transform ${showPrompt ? 'rotate-180' : ''}`} />
              </button>
              {showPrompt && (
                <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
                  <p className="text-[10px] leading-relaxed text-[#888] whitespace-pre-wrap font-mono">{generatedAgent.system_prompt}</p>
                </div>
              )}
            </div>

            {/* Suggested Knowledge */}
            {generatedAgent.suggested_knowledge?.length > 0 && (
              <div>
                <h4 className="mb-2 text-[10px] font-semibold text-[#888] uppercase tracking-wider">{T('Base de Conhecimento Sugerida', 'Suggested Knowledge Base')}</h4>
                <div className="space-y-1.5">
                  {generatedAgent.suggested_knowledge.map((item, i) => (
                    <div key={i} className="rounded-lg border border-[#1A1A1A] bg-[#0D0D0D] p-2.5">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="rounded bg-[#C9A84C]/10 px-1.5 py-px text-[8px] uppercase text-[#C9A84C]">{item.type}</span>
                        <span className="text-[10px] font-medium text-white">{item.title}</span>
                      </div>
                      <p className="text-[9px] text-[#666] line-clamp-2">{item.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Personality */}
            {generatedAgent.personality && (
              <div>
                <h4 className="mb-2 text-[10px] font-semibold text-[#888] uppercase tracking-wider">{T('Personalidade', 'Personality')}</h4>
                <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 space-y-2">
                  {[
                    { label: T('Tom', 'Tone'), value: generatedAgent.personality.tone_value },
                    { label: T('Verbosidade', 'Verbosity'), value: generatedAgent.personality.verbosity_value },
                    { label: T('Emojis', 'Emojis'), value: generatedAgent.personality.emoji_value },
                    { label: T('Proatividade', 'Proactivity'), value: generatedAgent.personality.proactivity },
                    { label: T('Formalidade', 'Formality'), value: generatedAgent.personality.formality },
                  ].map((p, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-[10px] text-[#666] w-20 shrink-0">{p.label}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-[#1A1A1A]">
                        <div className="h-full rounded-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A]" style={{ width: `${(p.value || 0) * 100}%` }} />
                      </div>
                      <span className="text-[10px] font-semibold text-[#C9A84C] w-8 text-right">{Math.round((p.value || 0) * 100)}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      <div className="fixed bottom-0 left-0 right-0 border-t border-[#1A1A1A] bg-[#0A0A0A]/95 backdrop-blur-sm px-4 py-3 pb-5">
        <div className="mx-auto flex max-w-lg gap-2">
          {step > 0 && step < 4 && (
            <button data-testid="builder-prev-btn" onClick={() => setStep(s => s - 1)}
              className="flex-1 rounded-xl border border-[#2A2A2A] py-3 text-xs font-medium text-[#888] transition hover:border-[#C9A84C]/30 hover:text-white">
              <ArrowLeft size={14} className="inline mr-1" /> {T('Voltar', 'Back')}
            </button>
          )}

          {step < 3 && (
            <button data-testid="builder-next-btn" onClick={handleNext} disabled={!canNext()}
              className="flex-1 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-3 text-xs font-bold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-1.5">
              {T('Proximo', 'Next')} <ArrowRight size={14} />
            </button>
          )}

          {step === 3 && (
            <button data-testid="builder-generate-btn" onClick={handleNext} disabled={!canNext() || generating}
              className="flex-1 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-3 text-xs font-bold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-1.5">
              {generating ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              {generating ? T('Gerando...', 'Generating...') : T('Gerar Agente com IA', 'Generate Agent with AI')}
            </button>
          )}

          {step === 4 && generatedAgent && !generating && (
            <>
              <button data-testid="builder-regenerate-btn" onClick={() => { setGeneratedAgent(null); generateAgent(); }}
                className="rounded-xl border border-[#2A2A2A] px-4 py-3 text-xs font-medium text-[#888] transition hover:border-[#C9A84C]/30 hover:text-white flex items-center gap-1.5">
                <RefreshCw size={13} /> {T('Regenerar', 'Regenerate')}
              </button>
              <button data-testid="builder-deploy-btn" onClick={deployAgent} disabled={deploying}
                className="flex-1 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-3 text-xs font-bold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-1.5">
                {deploying ? <Loader2 size={14} className="animate-spin" /> : <Rocket size={14} />}
                {deploying ? T('Publicando...', 'Deploying...') : T('Publicar Agente', 'Deploy Agent')}
              </button>
            </>
          )}

          {step === 4 && generating && (
            <div className="flex-1 rounded-xl border border-[#C9A84C]/20 bg-[#C9A84C]/5 py-3 text-center">
              <span className="text-xs text-[#C9A84C] flex items-center justify-center gap-2">
                <Loader2 size={14} className="animate-spin" /> {T('A IA esta trabalhando...', 'AI is working...')}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
