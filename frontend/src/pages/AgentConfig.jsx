import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Bot, Save, Plus, Trash2, BookOpen, Clock, Sliders, Brain, MessageCircle, Link2, Radio, AlertTriangle, Zap, ChevronDown, ChevronUp, Calendar, Table2, HardDrive, Globe, Webhook, Send, MessageSquare, Instagram, Facebook, Smartphone, Monitor, RotateCcw, Pencil } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TONES = [
  { value: 'professional', label: { en: 'Professional', pt: 'Profissional', es: 'Profesional' } },
  { value: 'friendly', label: { en: 'Friendly', pt: 'Amigavel', es: 'Amigable' } },
  { value: 'empathetic', label: { en: 'Empathetic', pt: 'Empatico', es: 'Empatico' } },
  { value: 'direct', label: { en: 'Direct', pt: 'Direto', es: 'Directo' } },
  { value: 'consultive', label: { en: 'Consultive', pt: 'Consultivo', es: 'Consultivo' } },
];

const KB_TYPES = [
  { value: 'faq', label: { en: 'FAQ', pt: 'FAQ', es: 'FAQ' } },
  { value: 'product', label: { en: 'Product', pt: 'Produto', es: 'Producto' } },
  { value: 'policy', label: { en: 'Policy', pt: 'Politica', es: 'Politica' } },
  { value: 'hours', label: { en: 'Hours', pt: 'Horarios', es: 'Horarios' } },
  { value: 'custom', label: { en: 'Custom', pt: 'Personalizado', es: 'Personalizado' } },
];

const TRIGGER_TYPES = [
  { value: 'conversation_closed', label: { en: 'After conversation closes', pt: 'Apos conversa encerrar', es: 'Al cerrar conversacion' } },
  { value: 'inactive_24h', label: { en: 'Inactive 24h', pt: 'Inativo 24h', es: 'Inactivo 24h' } },
  { value: 'inactive_48h', label: { en: 'Inactive 48h', pt: 'Inativo 48h', es: 'Inactivo 48h' } },
  { value: 'post_sale', label: { en: 'After sale', pt: 'Pos-venda', es: 'Post-venta' } },
  { value: 'cart_abandoned', label: { en: 'Cart abandoned', pt: 'Carrinho abandonado', es: 'Carrito abandonado' } },
];

/* ── Compact Slider: title + bar + % on same line, desc below ── */
function Slider({ label, desc, value, onChange, min = 0, max = 1, step = 0.05 }) {
  const pct = Math.round(((value - min) / (max - min)) * 100);
  return (
    <div className="py-1.5">
      <div className="flex items-center gap-2">
        <span className="text-[11px] text-[#888] w-20 shrink-0">{label}</span>
        <input type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(parseFloat(e.target.value))}
          className="flex-1 accent-[#C9A84C] h-1 rounded-full appearance-none bg-[#1E1E1E] cursor-pointer
            [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#C9A84C]" />
        <span className="text-[11px] font-semibold text-[#C9A84C] w-8 text-right">{pct}%</span>
      </div>
      {desc && <p className="text-[9px] text-[#444] ml-[88px] mt-0.5">{desc}</p>}
    </div>
  );
}

/* ── Compact Toggle ── */
function Toggle({ label, desc, checked, onChange, testId }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-[#111] last:border-0">
      <div className="pr-3">
        <p className="text-[11px] font-medium text-white">{label}</p>
        {desc && <p className="text-[9px] text-[#444]">{desc}</p>}
      </div>
      <button data-testid={testId} onClick={onChange}
        className={`h-4.5 w-8 rounded-full flex-shrink-0 transition ${checked ? 'bg-[#C9A84C]' : 'bg-[#222]'}`}>
        <div className={`h-3.5 w-3.5 rounded-full bg-white transition ${checked ? 'translate-x-4' : 'translate-x-0.5'}`} />
      </button>
    </div>
  );
}

export default function AgentConfig() {
  const { agentId } = useParams();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [agent, setAgent] = useState(null);
  const [knowledge, setKnowledge] = useState([]);
  const [rules, setRules] = useState([]);
  const [tab, setTab] = useState('personality');
  const [saving, setSaving] = useState(false);
  const [newKb, setNewKb] = useState({ type: 'faq', title: '', content: '' });
  const [newRule, setNewRule] = useState({ trigger_type: 'conversation_closed', delay_hours: 24, message_template: '' });
  const [showAddKb, setShowAddKb] = useState(false);
  const [showAddRule, setShowAddRule] = useState(false);
  const [promptOpen, setPromptOpen] = useState(false);
  const [resetting, setResetting] = useState(false);

  useEffect(() => {
    if (agentId) {
      axios.get(`${API}/agents/${agentId}`).then(r => setAgent(r.data)).catch(() => navigate('/agents'));
      axios.get(`${API}/agents/${agentId}/knowledge`).then(r => setKnowledge(r.data.items)).catch(() => {});
      axios.get(`${API}/agents/${agentId}/follow-up-rules`).then(r => setRules(r.data.rules)).catch(() => {});
    }
  }, [agentId, navigate]);

  const pc = agent?.personality_config || {};
  const setPC = (key, val) => setAgent(p => ({ ...p, personality_config: { ...p.personality_config, [key]: val } }));
  const flags = pc.flags || {};
  const setFlag = (key) => setPC('flags', { ...flags, [key]: !flags[key] });

  const saveAgent = async () => {
    if (!agent) return;
    setSaving(true);
    try {
      await axios.put(`${API}/agents/${agentId}`, {
        name: agent.name, tone: agent.tone, emoji_level: agent.emoji_level, verbosity_level: agent.verbosity_level,
        system_prompt: agent.system_prompt, knowledge_instructions: agent.knowledge_instructions,
        escalation_rules: agent.escalation_rules, follow_up_config: agent.follow_up_config,
        personality_config: agent.personality_config, integrations_config: agent.integrations_config, channel_config: agent.channel_config,
      });
      toast.success(lang === 'pt' ? 'Salvo!' : 'Saved!');
    } catch (e) {
      const detail = e.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : (Array.isArray(detail) ? detail.map(d => d.msg || '').join(', ') : 'Error'));
    } finally { setSaving(false); }
  };

  const addKnowledge = async () => {
    if (!newKb.title || !newKb.content) return;
    const { data } = await axios.post(`${API}/agents/${agentId}/knowledge`, newKb);
    setKnowledge(prev => [...prev, data]);
    setNewKb({ type: 'faq', title: '', content: '' });
    setShowAddKb(false);
  };

  const deleteKb = async (id) => { await axios.delete(`${API}/agents/${agentId}/knowledge/${id}`); setKnowledge(prev => prev.filter(k => k.id !== id)); };

  const addRule = async () => {
    if (!newRule.message_template) return;
    const { data } = await axios.post(`${API}/agents/${agentId}/follow-up-rules`, newRule);
    setRules(prev => [...prev, data]);
    setNewRule({ trigger_type: 'conversation_closed', delay_hours: 24, message_template: '' });
    setShowAddRule(false);
  };

  const deleteRule = async (id) => { await axios.delete(`${API}/agents/${agentId}/follow-up-rules/${id}`); setRules(prev => prev.filter(r => r.id !== id)); };

  const resetAgent = async () => {
    if (!window.confirm(lang === 'pt' ? 'Restaurar agente para a versao original? Suas alteracoes serao perdidas.' : 'Reset agent to original version? Your changes will be lost.')) return;
    setResetting(true);
    try {
      const { data } = await axios.post(`${API}/agents/${agentId}/reset`);
      setAgent(data);
      toast.success(lang === 'pt' ? 'Agente restaurado!' : 'Agent restored!');
    } catch (e) {
      const detail = e.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Error resetting');
    } finally { setResetting(false); }
  };

  if (!agent) return <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]"><div className="h-8 w-8 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" /></div>;

  const tabs = [
    { key: 'personality', icon: Sliders, label: { en: 'Personality', pt: 'Personalidade', es: 'Personalidad' } },
    { key: 'knowledge', icon: BookOpen, label: { en: 'Knowledge', pt: 'Conhecimento', es: 'Conocimiento' } },
    { key: 'integrations', icon: Link2, label: { en: 'Integrations', pt: 'Integracoes', es: 'Integraciones' } },
    { key: 'channels', icon: Radio, label: { en: 'Channels', pt: 'Canais', es: 'Canales' } },
    { key: 'escalation', icon: AlertTriangle, label: { en: 'Escalation', pt: 'Escalacao', es: 'Escalacion' } },
    { key: 'automations', icon: Zap, label: { en: 'Automations', pt: 'Automacoes', es: 'Automatizaciones' } },
  ];

  const previewText = () => {
    const emo = (agent.emoji_level || 0) > 0.4;
    const verb = (agent.verbosity_level || 0) > 0.6;
    const greet = {
      professional: emo ? 'Bom dia! Como posso ajudar hoje?' : 'Bom dia. Como posso ajuda-lo?',
      friendly: emo ? 'Oi! Que bom te ver! Como posso te ajudar?' : 'Oi! Como posso te ajudar?',
      empathetic: emo ? 'Ola! Estou aqui para te ajudar!' : 'Ola. Entendo sua situacao.',
      direct: emo ? 'Ola! Me diga o que precisa.' : 'Ola. O que precisa?',
      consultive: emo ? 'Ola! Posso fazer algumas perguntas?' : 'Ola. Posso entender melhor?',
    };
    let txt = greet[agent.tone] || greet.professional;
    if (verb) txt += ' Posso explicar em detalhes cada opcao.';
    return txt;
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-20">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-3 py-2.5">
        <div className="flex items-center gap-2.5">
          <button onClick={() => navigate('/agents')} className="text-[#666] hover:text-white transition"><ArrowLeft size={18} /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10 shrink-0"><Bot size={16} className="text-[#C9A84C]" /></div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <input data-testid="agent-config-name" value={agent.name} onChange={e => setAgent(p => ({ ...p, name: e.target.value }))}
                className="bg-transparent text-sm font-semibold text-white outline-none border-b border-transparent focus:border-[#C9A84C] w-full" />
              <Pencil size={11} className="text-[#555] shrink-0" />
            </div>
            <p className="text-[9px] capitalize text-[#555]">{agent.type} · {agent.tone}</p>
          </div>
          <div className="flex items-center gap-1.5">
            {agent.has_original && (
              <button data-testid="agent-reset-btn" onClick={resetAgent} disabled={resetting}
                className="flex items-center gap-1 rounded-lg border border-[#2A2A2A] px-2.5 py-1.5 text-[10px] text-[#888] transition hover:border-[#C9A84C]/30 hover:text-white disabled:opacity-50">
                <RotateCcw size={11} className={resetting ? 'animate-spin' : ''} /> Reset
              </button>
            )}
            <button data-testid="agent-save-btn" onClick={saveAgent} disabled={saving}
              className="btn-gold flex items-center gap-1 rounded-lg px-3 py-1.5 text-[11px] disabled:opacity-50">
              <Save size={12} /> {saving ? '...' : (lang === 'pt' ? 'Salvar' : 'Save')}
            </button>
          </div>
        </div>
      </div>

      {/* System Prompt - Collapsible */}
      <div className="border-b border-[#141414] px-3 py-2">
        <button onClick={() => setPromptOpen(!promptOpen)} className="flex w-full items-center gap-2 text-left">
          <Brain size={12} className="text-[#C9A84C]" />
          <span className="text-[10px] font-medium text-[#888] flex-1">{lang === 'pt' ? 'System Prompt' : 'System Prompt'}</span>
          {promptOpen ? <ChevronUp size={12} className="text-[#555]" /> : <ChevronDown size={12} className="text-[#555]" />}
        </button>
        {promptOpen && (
          <textarea data-testid="agent-system-prompt" value={agent.system_prompt || ''} onChange={e => setAgent(p => ({ ...p, system_prompt: e.target.value }))} rows={6}
            className="mt-2 w-full rounded-lg border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2 text-[11px] leading-relaxed text-[#999] outline-none resize-none font-mono focus:border-[#C9A84C]/30" />
        )}
        {!promptOpen && agent.system_prompt && (
          <p className="mt-1 text-[9px] text-[#444] line-clamp-2 cursor-pointer" onClick={() => setPromptOpen(true)}>{agent.system_prompt}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-0.5 overflow-x-auto border-b border-[#111] px-2 no-scrollbar">
        {tabs.map(tb => (
          <button key={tb.key} data-testid={`tab-${tb.key}`} onClick={() => setTab(tb.key)}
            className={`flex items-center gap-1 whitespace-nowrap px-2.5 py-2 text-[10px] font-medium transition border-b-2 ${
              tab === tb.key ? 'border-[#C9A84C] text-[#C9A84C]' : 'border-transparent text-[#555] hover:text-[#888]'}`}>
            <tb.icon size={11} /> {tb.label[lang] || tb.label.en}
          </button>
        ))}
      </div>

      <div className="px-3 pt-3 max-w-2xl mx-auto">

        {/* ══════ PERSONALITY ══════ */}
        {tab === 'personality' && (
          <div className="space-y-3">
            {/* Tone */}
            <div>
              <p className="mb-1.5 text-[10px] font-medium text-[#888]">{lang === 'pt' ? 'Tom' : 'Tone'}</p>
              <div className="flex gap-1.5 flex-wrap">
                {TONES.map(to => (
                  <button key={to.value} data-testid={`tone-${to.value}`} onClick={() => setAgent(p => ({ ...p, tone: to.value }))}
                    className={`rounded-lg border px-3 py-1.5 text-[10px] transition ${
                      agent.tone === to.value ? 'border-[#C9A84C]/40 bg-[#C9A84C]/8 text-[#C9A84C]' : 'border-[#1A1A1A] text-[#666] hover:border-[#222]'}`}>
                    {to.label[lang] || to.label.en}
                  </button>
                ))}
              </div>
            </div>

            {/* Sliders */}
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-3 py-2">
              <h3 className="text-[10px] font-semibold text-white mb-1">{lang === 'pt' ? 'Ajustes Finos' : 'Fine Tuning'}</h3>
              <Slider label={lang === 'pt' ? 'Emojis' : 'Emojis'} desc={lang === 'pt' ? 'Frequencia de emojis nas respostas' : 'Emoji frequency in responses'} value={agent.emoji_level || 0} onChange={v => setAgent(p => ({...p, emoji_level: v}))} />
              <Slider label={lang === 'pt' ? 'Verbosidade' : 'Verbosity'} desc={lang === 'pt' ? 'Nivel de detalhe nas respostas' : 'Detail level in responses'} value={agent.verbosity_level || 0} onChange={v => setAgent(p => ({...p, verbosity_level: v}))} />
              <Slider label={lang === 'pt' ? 'Proatividade' : 'Proactivity'} desc={lang === 'pt' ? 'Sugestoes e acoes sem solicitar' : 'Unsolicited suggestions and actions'} value={pc.proactivity || 0.3} onChange={v => setPC('proactivity', v)} />
              <Slider label={lang === 'pt' ? 'Criatividade' : 'Creativity'} desc={lang === 'pt' ? 'Variacao nas respostas geradas' : 'Variation in generated responses'} value={pc.creativity || 0.5} onChange={v => setPC('creativity', v)} />
              <Slider label={lang === 'pt' ? 'Formalidade' : 'Formality'} desc={lang === 'pt' ? 'Nivel de formalidade da linguagem' : 'Language formality level'} value={pc.formality || 0.5} onChange={v => setPC('formality', v)} />
            </div>

            {/* Flags */}
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-3 py-2">
              <h3 className="text-[10px] font-semibold text-white mb-1">{lang === 'pt' ? 'Comportamentos' : 'Behaviors'}</h3>
              <Toggle label={lang === 'pt' ? 'Multilingue automatico' : 'Auto multilingual'} desc={lang === 'pt' ? 'Responde no idioma do cliente' : 'Responds in customer language'} checked={flags.auto_multilingual !== false} onChange={() => setFlag('auto_multilingual')} testId="flag-multilingual" />
              <Toggle label={lang === 'pt' ? 'Lembrar contexto' : 'Remember context'} desc={lang === 'pt' ? 'Mantem historico da conversa' : 'Keeps conversation history'} checked={flags.remember_context !== false} onChange={() => setFlag('remember_context')} testId="flag-context" />
              <Toggle label={lang === 'pt' ? 'Escalar automaticamente' : 'Auto escalate'} desc={lang === 'pt' ? 'Transfere para humano se frustrado' : 'Transfer to human when frustrated'} checked={flags.auto_escalate !== false} onChange={() => setFlag('auto_escalate')} testId="flag-escalate" />
              <Toggle label={lang === 'pt' ? 'Sugerir produtos' : 'Suggest products'} desc={lang === 'pt' ? 'Recomenda produtos proativamente' : 'Proactively recommends products'} checked={!!flags.suggest_products} onChange={() => setFlag('suggest_products')} testId="flag-suggest" />
              <Toggle label={lang === 'pt' ? 'Coletar dados' : 'Collect data'} desc={lang === 'pt' ? 'Pede nome, email, telefone' : 'Asks for name, email, phone'} checked={!!flags.collect_data} onChange={() => setFlag('collect_data')} testId="flag-collect" />
            </div>

            {/* Preview */}
            <div className="rounded-xl border border-[#C9A84C]/10 bg-[#C9A84C]/3 px-3 py-2">
              <p className="text-[9px] text-[#C9A84C]/60 font-medium mb-1">Preview</p>
              <p className="text-[11px] text-white leading-relaxed">{previewText()}</p>
            </div>
          </div>
        )}

        {/* ══════ KNOWLEDGE ══════ */}
        {tab === 'knowledge' && (
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Base de conhecimento' : 'Knowledge base'}</p>
              <button data-testid="add-knowledge-btn" onClick={() => setShowAddKb(!showAddKb)} className="btn-gold flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px]"><Plus size={11} /> {lang === 'pt' ? 'Adicionar' : 'Add'}</button>
            </div>

            {showAddKb && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] space-y-2 p-3">
                <select value={newKb.type} onChange={e => setNewKb(p => ({ ...p, type: e.target.value }))} className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white outline-none">
                  {KB_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label[lang] || tp.label.en}</option>)}
                </select>
                <input data-testid="kb-title" value={newKb.title} onChange={e => setNewKb(p => ({ ...p, title: e.target.value }))} placeholder={lang === 'pt' ? 'Titulo' : 'Title'}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white placeholder-[#444] outline-none" />
                <textarea data-testid="kb-content" value={newKb.content} onChange={e => setNewKb(p => ({ ...p, content: e.target.value }))} rows={2}
                  placeholder={lang === 'pt' ? 'Conteudo...' : 'Content...'} className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white placeholder-[#444] outline-none resize-none" />
                <button data-testid="kb-save-btn" onClick={addKnowledge} className="btn-gold w-full rounded-lg py-1.5 text-[10px]">{lang === 'pt' ? 'Salvar' : 'Save'}</button>
              </div>
            )}

            {knowledge.map(item => (
              <div key={item.id} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="rounded bg-[#C9A84C]/15 px-1.5 py-px text-[8px] uppercase text-[#C9A84C]">{item.type}</span>
                    <h4 className="text-[11px] font-medium text-white truncate">{item.title}</h4>
                  </div>
                  <p className="text-[10px] text-[#555] line-clamp-2">{item.content}</p>
                </div>
                <button onClick={() => deleteKb(item.id)} className="text-[#444] hover:text-red-400 transition shrink-0"><Trash2 size={13} /></button>
              </div>
            ))}

            {knowledge.length === 0 && !showAddKb && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-6 text-center">
                <BookOpen size={22} className="mx-auto mb-1.5 text-[#222]" />
                <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Nenhum conhecimento' : 'No knowledge yet'}</p>
              </div>
            )}

            <div>
              <label className="mb-1 block text-[10px] font-medium text-[#888]">{lang === 'pt' ? 'Instrucoes adicionais' : 'Additional instructions'}</label>
              <textarea value={agent.knowledge_instructions || ''} onChange={e => setAgent(p => ({ ...p, knowledge_instructions: e.target.value }))} rows={2}
                placeholder={lang === 'pt' ? 'Ex: Sempre mencione o horario...' : 'Ex: Always mention hours...'}
                className="w-full rounded-lg border border-[#1E1E1E] bg-[#0D0D0D] px-2.5 py-1.5 text-[11px] text-white placeholder-[#444] outline-none resize-none" />
            </div>
          </div>
        )}

        {/* ══════ INTEGRATIONS ══════ */}
        {tab === 'integrations' && (
          <div className="space-y-2">
            {[
              { key: 'google_calendar', name: 'Google Calendar', desc: lang === 'pt' ? 'Agendar e consultar eventos' : 'Schedule and query events', icon: Calendar },
              { key: 'google_sheets', name: 'Google Sheets', desc: lang === 'pt' ? 'Ler e escrever planilhas' : 'Read and write spreadsheets', icon: Table2 },
              { key: 'google_drive', name: 'Google Drive', desc: lang === 'pt' ? 'Documentos como base de conhecimento' : 'Docs as knowledge base', icon: HardDrive },
              { key: 'custom_api', name: 'Custom API', desc: lang === 'pt' ? 'Conectar a qualquer API REST' : 'Connect to any REST API', icon: Globe },
              { key: 'webhook', name: 'Webhooks', desc: lang === 'pt' ? 'Disparar webhooks em eventos' : 'Trigger webhooks on events', icon: Webhook },
            ].map(integ => {
              const cfg = agent.integrations_config || {};
              const connected = cfg[integ.key]?.enabled;
              return (
                <div key={integ.key} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/8"><integ.icon size={14} className="text-[#C9A84C]" /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-medium text-white">{integ.name}</p>
                      <p className="text-[9px] text-[#555]">{integ.desc}</p>
                    </div>
                    <button data-testid={`integ-${integ.key}`}
                      onClick={() => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, [integ.key]: { ...p.integrations_config?.[integ.key], enabled: !connected } } }))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] font-medium transition ${connected ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20' : 'bg-[#1A1A1A] text-[#666] border border-[#1E1E1E]'}`}>
                      {connected ? (lang === 'pt' ? 'Conectado' : 'Connected') : (lang === 'pt' ? 'Conectar' : 'Connect')}
                    </button>
                  </div>
                  {connected && integ.key === 'custom_api' && (
                    <div className="mt-2 space-y-1.5 pt-2 border-t border-[#111]">
                      <input value={cfg.custom_api?.url || ''} onChange={e => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, custom_api: { ...p.integrations_config?.custom_api, url: e.target.value } } }))}
                        placeholder="API URL" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[10px] text-white placeholder-[#444] outline-none" />
                      <input value={cfg.custom_api?.api_key || ''} onChange={e => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, custom_api: { ...p.integrations_config?.custom_api, api_key: e.target.value } } }))}
                        placeholder="API Key" type="password" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[10px] text-white placeholder-[#444] outline-none" />
                    </div>
                  )}
                  {connected && integ.key === 'webhook' && (
                    <div className="mt-2 pt-2 border-t border-[#111]">
                      <input value={cfg.webhook?.url || ''} onChange={e => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, webhook: { ...p.integrations_config?.webhook, url: e.target.value } } }))}
                        placeholder="Webhook URL" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[10px] text-white placeholder-[#444] outline-none" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ══════ CHANNELS ══════ */}
        {tab === 'channels' && (
          <div className="space-y-2">
            {[
              { key: 'telegram', name: 'Telegram Bot', desc: lang === 'pt' ? 'Via @BotFather' : 'Via @BotFather', icon: Send },
              { key: 'whatsapp', name: 'WhatsApp', desc: 'Evolution API', icon: MessageCircle },
              { key: 'instagram', name: 'Instagram DM', desc: 'Meta Business', icon: Instagram },
              { key: 'messenger', name: 'Facebook Messenger', desc: 'Meta Pages', icon: Facebook },
              { key: 'sms', name: 'SMS', desc: 'Twilio', icon: Smartphone },
              { key: 'webchat', name: 'Web Chat', desc: lang === 'pt' ? 'Widget no seu site' : 'Site widget', icon: Monitor },
            ].map(ch => {
              const chCfg = agent.channel_config || {};
              const enabled = chCfg[ch.key]?.enabled;
              return (
                <div key={ch.key} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/8"><ch.icon size={14} className="text-[#C9A84C]" /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-medium text-white">{ch.name}</p>
                      <p className="text-[9px] text-[#555]">{ch.desc}</p>
                    </div>
                    <button data-testid={`channel-${ch.key}`}
                      onClick={() => setAgent(p => ({ ...p, channel_config: { ...p.channel_config, [ch.key]: { ...p.channel_config?.[ch.key], enabled: !enabled } } }))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] font-medium transition ${enabled ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20' : 'bg-[#1A1A1A] text-[#666] border border-[#1E1E1E]'}`}>
                      {enabled ? (lang === 'pt' ? 'Ativo' : 'Active') : (lang === 'pt' ? 'Ativar' : 'Enable')}
                    </button>
                  </div>
                  {enabled && ch.key === 'telegram' && (
                    <div className="mt-2 space-y-1.5 pt-2 border-t border-[#111]">
                      <input data-testid="telegram-bot-token" value={chCfg.telegram?.bot_token || ''}
                        onChange={e => setAgent(p => ({ ...p, channel_config: { ...p.channel_config, telegram: { ...p.channel_config?.telegram, bot_token: e.target.value } } }))}
                        placeholder="Bot Token (@BotFather)" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[10px] text-white placeholder-[#444] outline-none" />
                      <p className="text-[9px] text-[#444]">{lang === 'pt' ? '1. @BotFather → /newbot → Cole token' : '1. @BotFather → /newbot → Paste token'}</p>
                      {chCfg.telegram?.bot_token && (
                        <button data-testid="telegram-connect-btn" onClick={async () => {
                          try { const { data } = await axios.post(`${API}/telegram/setup`, { agent_id: agentId, bot_token: chCfg.telegram.bot_token }); toast.success(data.message || 'Connected!');
                            setAgent(p => ({ ...p, channel_config: { ...p.channel_config, telegram: { ...p.channel_config?.telegram, connected: true, bot_username: data.bot_username } } }));
                          } catch (e) { toast.error(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Failed'); }
                        }} className="btn-gold w-full rounded-lg py-1.5 text-[10px]">
                          {chCfg.telegram?.connected ? `@${chCfg.telegram.bot_username || 'Connected'}` : (lang === 'pt' ? 'Conectar Bot' : 'Connect Bot')}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ══════ ESCALATION ══════ */}
        {tab === 'escalation' && (
          <div className="space-y-2.5">
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 space-y-2">
              <div>
                <label className="mb-1 block text-[10px] font-medium text-[#888]">{lang === 'pt' ? 'Palavras-chave de escalacao' : 'Escalation keywords'}</label>
                <input data-testid="escalation-keywords" value={(agent.escalation_rules?.keywords || []).join(', ')}
                  onChange={e => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean) } }))}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white outline-none" />
                <p className="mt-0.5 text-[9px] text-[#444]">{lang === 'pt' ? 'Separadas por virgula' : 'Comma separated'}</p>
              </div>
              <Slider label={lang === 'pt' ? 'Frustracao' : 'Frustration'} desc={lang === 'pt' ? 'Sensibilidade para escalar' : 'Sensitivity to escalate'} value={agent.escalation_rules?.sentiment_threshold || 0.3} onChange={v => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, sentiment_threshold: v } }))} />
              <Toggle label={lang === 'pt' ? 'Notificar operador' : 'Notify operator'} desc={lang === 'pt' ? 'Notificacao ao escalar' : 'Notification on escalation'} checked={agent.escalation_rules?.notify_operator !== false}
                onChange={() => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, notify_operator: !p.escalation_rules?.notify_operator } }))} testId="flag-notify" />
            </div>

            <button data-testid="test-agent-btn" onClick={() => navigate('/agents/sandbox')} className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-[#C9A84C]/15 bg-[#C9A84C]/3 py-2 text-[10px] text-[#C9A84C] hover:bg-[#C9A84C]/8 transition">
              <MessageCircle size={12} /> {lang === 'pt' ? 'Testar no Sandbox' : 'Test in Sandbox'}
            </button>
          </div>
        )}

        {/* ══════ AUTOMATIONS ══════ */}
        {tab === 'automations' && (
          <div className="space-y-2.5">
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
              <Toggle label={lang === 'pt' ? 'Pos-Atendimento Automatico' : 'Auto Follow-up'} desc={lang === 'pt' ? 'Mensagens automaticas apos atendimento' : 'Auto messages after service'}
                checked={agent.follow_up_config?.enabled} onChange={() => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, enabled: !p.follow_up_config?.enabled } }))} testId="followup-toggle" />
              {agent.follow_up_config?.enabled && (
                <div className="mt-2 pt-2 border-t border-[#111] grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-[9px] text-[#555]">{lang === 'pt' ? 'Max. Reativacoes' : 'Max Follow-ups'}</label>
                    <input type="number" value={agent.follow_up_config?.max_follow_ups || 3} onChange={e => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, max_follow_ups: parseInt(e.target.value) } }))}
                      className="w-full bg-transparent text-sm font-bold text-white outline-none border-b border-[#1E1E1E] focus:border-[#C9A84C]" />
                  </div>
                  <div>
                    <label className="text-[9px] text-[#555]">{lang === 'pt' ? 'Intervalo (dias)' : 'Cooldown (days)'}</label>
                    <input type="number" value={agent.follow_up_config?.cool_down_days || 7} onChange={e => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, cool_down_days: parseInt(e.target.value) } }))}
                      className="w-full bg-transparent text-sm font-bold text-white outline-none border-b border-[#1E1E1E] focus:border-[#C9A84C]" />
                  </div>
                </div>
              )}
            </div>

            {agent.follow_up_config?.enabled && (
              <>
                <div className="flex items-center justify-between">
                  <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Regras' : 'Rules'}</p>
                  <button data-testid="add-rule-btn" onClick={() => setShowAddRule(!showAddRule)} className="btn-gold flex items-center gap-1 rounded-lg px-2.5 py-1 text-[10px]"><Plus size={11} /> {lang === 'pt' ? 'Adicionar' : 'Add'}</button>
                </div>
                {showAddRule && (
                  <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] space-y-2 p-3">
                    <select value={newRule.trigger_type} onChange={e => setNewRule(p => ({ ...p, trigger_type: e.target.value }))} className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white outline-none">
                      {TRIGGER_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label[lang] || tp.label.en}</option>)}
                    </select>
                    <input type="number" value={newRule.delay_hours} onChange={e => setNewRule(p => ({ ...p, delay_hours: parseInt(e.target.value) }))} placeholder={lang === 'pt' ? 'Atraso (h)' : 'Delay (h)'}
                      className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white outline-none" />
                    <textarea data-testid="rule-template" value={newRule.message_template} onChange={e => setNewRule(p => ({ ...p, message_template: e.target.value }))} rows={2}
                      placeholder={lang === 'pt' ? 'Mensagem... {name}' : 'Message... {name}'} className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2.5 py-1.5 text-[11px] text-white placeholder-[#444] outline-none resize-none" />
                    <button data-testid="rule-save-btn" onClick={addRule} className="btn-gold w-full rounded-lg py-1.5 text-[10px]">{lang === 'pt' ? 'Salvar' : 'Save'}</button>
                  </div>
                )}
                {rules.map(rule => (
                  <div key={rule.id} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] flex items-start gap-2 p-3">
                    <Clock size={13} className="text-[#C9A84C] shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <p className="text-[10px] font-medium text-white">{TRIGGER_TYPES.find(t => t.value === rule.trigger_type)?.label[lang] || rule.trigger_type}</p>
                      <p className="text-[9px] text-[#555]">{lang === 'pt' ? `Apos ${rule.delay_hours}h` : `After ${rule.delay_hours}h`} — <span className="italic text-[#888]">"{rule.message_template}"</span></p>
                    </div>
                    <button onClick={() => deleteRule(rule.id)} className="text-[#444] hover:text-red-400 transition shrink-0"><Trash2 size={12} /></button>
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
