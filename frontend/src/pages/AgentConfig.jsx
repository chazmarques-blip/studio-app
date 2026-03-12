import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Bot, Save, Plus, Trash2, BookOpen, Clock, Sliders, Brain, MessageCircle, Link2, Radio, AlertTriangle, Zap } from 'lucide-react';
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

/* ---- Reusable UI pieces ---- */
function Slider({ label, labelRight, value, onChange, min = 0, max = 1, step = 0.05 }) {
  const pct = Math.round(((value - min) / (max - min)) * 100);
  return (
    <div className="mb-4">
      <div className="mb-1.5 flex justify-between">
        <span className="text-xs text-[#888]">{label}</span>
        <span className="text-xs font-medium text-[#C9A84C]">{pct}%</span>
      </div>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="w-full accent-[#C9A84C] h-1.5 rounded-full appearance-none bg-[#1E1E1E] cursor-pointer
          [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-[#C9A84C]" />
      {labelRight && <div className="flex justify-between text-[9px] text-[#444] mt-0.5"><span>{labelRight[0]}</span><span>{labelRight[1]}</span></div>}
    </div>
  );
}

function Toggle({ label, desc, checked, onChange, testId }) {
  return (
    <div className="flex items-center justify-between py-2.5 border-b border-[#141414] last:border-0">
      <div className="pr-4">
        <p className="text-xs font-medium text-white">{label}</p>
        {desc && <p className="text-[10px] text-[#555] mt-0.5">{desc}</p>}
      </div>
      <button data-testid={testId} onClick={onChange}
        className={`h-5 w-9 rounded-full flex-shrink-0 transition ${checked ? 'bg-[#C9A84C]' : 'bg-[#222]'}`}>
        <div className={`h-4 w-4 rounded-full bg-white transition ${checked ? 'translate-x-4' : 'translate-x-0.5'}`} />
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

  useEffect(() => {
    if (agentId) {
      axios.get(`${API}/agents/${agentId}`).then(r => setAgent(r.data)).catch(() => navigate('/agents'));
      axios.get(`${API}/agents/${agentId}/knowledge`).then(r => setKnowledge(r.data.items)).catch(() => {});
      axios.get(`${API}/agents/${agentId}/follow-up-rules`).then(r => setRules(r.data.rules)).catch(() => {});
    }
  }, [agentId, navigate]);

  // Helper to safely get personality_config fields
  const pc = agent?.personality_config || {};
  const setPC = (key, val) => setAgent(p => ({ ...p, personality_config: { ...p.personality_config, [key]: val } }));
  const flags = pc.flags || {};
  const setFlag = (key) => setPC('flags', { ...flags, [key]: !flags[key] });

  const saveAgent = async () => {
    if (!agent) return;
    setSaving(true);
    try {
      await axios.put(`${API}/agents/${agentId}`, {
        name: agent.name,
        tone: agent.tone,
        emoji_level: agent.emoji_level,
        verbosity_level: agent.verbosity_level,
        system_prompt: agent.system_prompt,
        knowledge_instructions: agent.knowledge_instructions,
        escalation_rules: agent.escalation_rules,
        follow_up_config: agent.follow_up_config,
        personality_config: agent.personality_config,
        integrations_config: agent.integrations_config,
        channel_config: agent.channel_config,
      });
      toast.success(lang === 'pt' ? 'Salvo!' : 'Saved!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error saving');
    } finally { setSaving(false); }
  };

  const addKnowledge = async () => {
    if (!newKb.title || !newKb.content) return;
    const { data } = await axios.post(`${API}/agents/${agentId}/knowledge`, newKb);
    setKnowledge(prev => [...prev, data]);
    setNewKb({ type: 'faq', title: '', content: '' });
    setShowAddKb(false);
  };

  const deleteKb = async (id) => {
    await axios.delete(`${API}/agents/${agentId}/knowledge/${id}`);
    setKnowledge(prev => prev.filter(k => k.id !== id));
  };

  const addRule = async () => {
    if (!newRule.message_template) return;
    const { data } = await axios.post(`${API}/agents/${agentId}/follow-up-rules`, newRule);
    setRules(prev => [...prev, data]);
    setNewRule({ trigger_type: 'conversation_closed', delay_hours: 24, message_template: '' });
    setShowAddRule(false);
  };

  const deleteRule = async (id) => {
    await axios.delete(`${API}/agents/${agentId}/follow-up-rules/${id}`);
    setRules(prev => prev.filter(r => r.id !== id));
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

  /* ---- Preview text generation ---- */
  const previewText = () => {
    const emo = (agent.emoji_level || 0) > 0.4;
    const verb = (agent.verbosity_level || 0) > 0.6;
    const greet = {
      professional: emo ? 'Bom dia! Como posso ajudar com nossos servicos hoje?' : 'Bom dia. Como posso ajuda-lo?',
      friendly: emo ? 'Oi! Que bom te ver por aqui! Me conta, como posso te ajudar?' : 'Oi! Como posso te ajudar?',
      empathetic: emo ? 'Ola! Entendo que isso pode ser frustrante. Estou aqui para te ajudar!' : 'Ola. Entendo sua situacao e vou fazer o possivel para ajudar.',
      direct: emo ? 'Ola! Me diga exatamente o que precisa.' : 'Ola. O que precisa?',
      consultive: emo ? 'Ola! Para encontrar a melhor solucao, posso fazer algumas perguntas?' : 'Ola. Posso fazer algumas perguntas para entender melhor?',
    };
    let txt = greet[agent.tone] || greet.professional;
    if (verb) txt += lang === 'pt' ? ' Posso explicar em detalhes cada opcao disponivel para voce.' : ' I can explain each available option in detail for you.';
    return txt;
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-24">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/agents')} className="text-[#666] hover:text-white transition"><ArrowLeft size={20} /></button>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#C9A84C]/10 flex-shrink-0"><Bot size={18} className="text-[#C9A84C]" /></div>
          <div className="flex-1 min-w-0">
            <input data-testid="agent-config-name" value={agent.name} onChange={e => setAgent(p => ({ ...p, name: e.target.value }))}
              className="bg-transparent text-sm font-semibold text-white outline-none border-b border-transparent focus:border-[#C9A84C] w-full" />
            <p className="text-[10px] capitalize text-[#555]">{agent.type} · {agent.tone}</p>
          </div>
          <button data-testid="agent-save-btn" onClick={saveAgent} disabled={saving}
            className="btn-gold flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs disabled:opacity-50">
            <Save size={13} /> {saving ? '...' : (lang === 'pt' ? 'Salvar' : 'Save')}
          </button>
        </div>
      </div>

      {/* Tabs - scrollable */}
      <div className="flex gap-0.5 overflow-x-auto border-b border-[#141414] px-3 pt-1" style={{scrollbarWidth:'none'}}>
        {tabs.map(tb => (
          <button key={tb.key} data-testid={`tab-${tb.key}`} onClick={() => setTab(tb.key)}
            className={`flex items-center gap-1 whitespace-nowrap px-3 py-2 text-[11px] font-medium transition border-b-2 ${
              tab === tb.key ? 'border-[#C9A84C] text-[#C9A84C]' : 'border-transparent text-[#555] hover:text-[#888]'}`}>
            <tb.icon size={12} /> {tb.label[lang] || tb.label.en}
          </button>
        ))}
      </div>

      <div className="px-4 pt-4 max-w-2xl mx-auto">

        {/* ============ PERSONALITY ============ */}
        {tab === 'personality' && (
          <div className="space-y-5">
            {/* Tone selection */}
            <div>
              <label className="mb-2 block text-xs font-medium text-[#888]">{lang === 'pt' ? 'Tom' : 'Tone'}</label>
              <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                {TONES.map(to => (
                  <button key={to.value} data-testid={`tone-${to.value}`} onClick={() => setAgent(p => ({ ...p, tone: to.value }))}
                    className={`rounded-lg border p-2.5 text-center text-[11px] transition ${
                      agent.tone === to.value ? 'border-[#C9A84C]/40 bg-[#C9A84C]/8 text-[#C9A84C]' : 'border-[#1A1A1A] text-[#666] hover:border-[#222]'}`}>
                    {to.label[lang] || to.label.en}
                  </button>
                ))}
              </div>
            </div>

            {/* Sliders */}
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
              <h3 className="text-xs font-semibold text-white mb-4">{lang === 'pt' ? 'Ajustes Finos' : 'Fine Tuning'}</h3>
              <Slider label={lang === 'pt' ? 'Emojis' : 'Emoji Usage'} value={agent.emoji_level || 0} onChange={v => setAgent(p => ({...p, emoji_level: v}))} labelRight={[lang === 'pt' ? 'Nenhum' : 'None', lang === 'pt' ? 'Frequente' : 'Frequent']} />
              <Slider label={lang === 'pt' ? 'Verbosidade' : 'Verbosity'} value={agent.verbosity_level || 0} onChange={v => setAgent(p => ({...p, verbosity_level: v}))} labelRight={[lang === 'pt' ? 'Conciso' : 'Concise', lang === 'pt' ? 'Detalhado' : 'Detailed']} />
              <Slider label={lang === 'pt' ? 'Proatividade' : 'Proactivity'} value={pc.proactivity || 0.3} onChange={v => setPC('proactivity', v)} labelRight={[lang === 'pt' ? 'Reativo' : 'Reactive', lang === 'pt' ? 'Proativo' : 'Proactive']} />
              <Slider label={lang === 'pt' ? 'Criatividade' : 'Creativity'} value={pc.creativity || 0.5} onChange={v => setPC('creativity', v)} labelRight={[lang === 'pt' ? 'Conservador' : 'Conservative', lang === 'pt' ? 'Criativo' : 'Creative']} />
              <Slider label={lang === 'pt' ? 'Formalidade' : 'Formality'} value={pc.formality || 0.5} onChange={v => setPC('formality', v)} labelRight={['Casual', 'Formal']} />
            </div>

            {/* Flags */}
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
              <h3 className="text-xs font-semibold text-white mb-2">{lang === 'pt' ? 'Comportamentos' : 'Behaviors'}</h3>
              <Toggle label={lang === 'pt' ? 'Multilingue automatico' : 'Auto multilingual'} desc={lang === 'pt' ? 'Responde no idioma do cliente' : 'Responds in customer language'} checked={flags.auto_multilingual !== false} onChange={() => setFlag('auto_multilingual')} testId="flag-multilingual" />
              <Toggle label={lang === 'pt' ? 'Lembrar contexto' : 'Remember context'} desc={lang === 'pt' ? 'Mantem historico da conversa' : 'Keeps conversation history'} checked={flags.remember_context !== false} onChange={() => setFlag('remember_context')} testId="flag-context" />
              <Toggle label={lang === 'pt' ? 'Escalar automaticamente' : 'Auto escalate'} desc={lang === 'pt' ? 'Transfere para humano quando frustrado' : 'Transfer to human when frustrated'} checked={flags.auto_escalate !== false} onChange={() => setFlag('auto_escalate')} testId="flag-escalate" />
              <Toggle label={lang === 'pt' ? 'Sugerir produtos' : 'Suggest products'} desc={lang === 'pt' ? 'Recomenda produtos/servicos proativamente' : 'Proactively recommends products/services'} checked={!!flags.suggest_products} onChange={() => setFlag('suggest_products')} testId="flag-suggest" />
              <Toggle label={lang === 'pt' ? 'Coletar dados' : 'Collect data'} desc={lang === 'pt' ? 'Pede nome, email, telefone naturalmente' : 'Naturally asks for name, email, phone'} checked={!!flags.collect_data} onChange={() => setFlag('collect_data')} testId="flag-collect" />
            </div>

            {/* Preview */}
            <div className="rounded-xl border border-[#C9A84C]/15 bg-[#C9A84C]/3 p-4">
              <p className="text-[10px] text-[#C9A84C]/60 mb-1.5 font-medium">{lang === 'pt' ? 'Preview' : 'Preview'}</p>
              <div className="rounded-lg bg-[#0A0A0A] p-3 border border-[#1A1A1A]">
                <p className="text-sm text-white leading-relaxed">{previewText()}</p>
              </div>
            </div>
          </div>
        )}

        {/* ============ KNOWLEDGE ============ */}
        {tab === 'knowledge' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-[#666]">{lang === 'pt' ? 'Base de conhecimento do agente' : 'Agent knowledge base'}</p>
              <button data-testid="add-knowledge-btn" onClick={() => setShowAddKb(!showAddKb)} className="btn-gold flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs"><Plus size={12} /> {lang === 'pt' ? 'Adicionar' : 'Add'}</button>
            </div>

            {showAddKb && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] space-y-3 p-4">
                <select value={newKb.type} onChange={e => setNewKb(p => ({ ...p, type: e.target.value }))}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white outline-none">
                  {KB_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label[lang] || tp.label.en}</option>)}
                </select>
                <input data-testid="kb-title" value={newKb.title} onChange={e => setNewKb(p => ({ ...p, title: e.target.value }))} placeholder={lang === 'pt' ? 'Titulo' : 'Title'}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                <textarea data-testid="kb-content" value={newKb.content} onChange={e => setNewKb(p => ({ ...p, content: e.target.value }))} rows={3}
                  placeholder={lang === 'pt' ? 'Conteudo que o agente deve saber...' : 'Content the agent should know...'}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none" />
                <button data-testid="kb-save-btn" onClick={addKnowledge} className="btn-gold w-full rounded-lg py-2 text-xs">{lang === 'pt' ? 'Salvar' : 'Save'}</button>
              </div>
            )}

            {knowledge.map(item => (
              <div key={item.id} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="rounded bg-[#C9A84C]/15 px-2 py-0.5 text-[9px] uppercase text-[#C9A84C]">{item.type}</span>
                      <h4 className="text-sm font-medium text-white truncate">{item.title}</h4>
                    </div>
                    <p className="text-xs text-[#555] line-clamp-2">{item.content}</p>
                  </div>
                  <button onClick={() => deleteKb(item.id)} className="ml-2 text-[#444] hover:text-red-400 transition"><Trash2 size={14} /></button>
                </div>
              </div>
            ))}

            {knowledge.length === 0 && !showAddKb && (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-8 text-center">
                <BookOpen size={28} className="mx-auto mb-2 text-[#222]" />
                <p className="text-xs text-[#666]">{lang === 'pt' ? 'Nenhum conhecimento cadastrado' : 'No knowledge added yet'}</p>
              </div>
            )}

            <div>
              <label className="mb-1.5 block text-xs font-medium text-[#888]">{lang === 'pt' ? 'Instrucoes adicionais' : 'Additional instructions'}</label>
              <textarea value={agent.knowledge_instructions || ''} onChange={e => setAgent(p => ({ ...p, knowledge_instructions: e.target.value }))} rows={3}
                placeholder={lang === 'pt' ? 'Ex: Sempre mencione o horario de funcionamento...' : 'Ex: Always mention opening hours...'}
                className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none" />
            </div>
          </div>
        )}

        {/* ============ INTEGRATIONS ============ */}
        {tab === 'integrations' && (
          <div className="space-y-4">
            <p className="text-xs text-[#666]">{lang === 'pt' ? 'Conecte servicos externos que o agente pode usar' : 'Connect external services the agent can use'}</p>

            {[
              { key: 'google_calendar', name: 'Google Calendar', desc: lang === 'pt' ? 'Agendar, consultar e criar eventos' : 'Schedule, query and create events', icon: '📅', color: '#4285F4' },
              { key: 'google_sheets', name: 'Google Sheets', desc: lang === 'pt' ? 'Ler e escrever dados em planilhas' : 'Read and write spreadsheet data', icon: '📊', color: '#34A853' },
              { key: 'google_drive', name: 'Google Drive', desc: lang === 'pt' ? 'Acessar documentos como base de conhecimento' : 'Access docs as knowledge base', icon: '📁', color: '#FBBC04' },
              { key: 'custom_api', name: 'Custom API', desc: lang === 'pt' ? 'Conectar a qualquer API REST externa' : 'Connect to any external REST API', icon: '🔗', color: '#C9A84C' },
              { key: 'webhook', name: 'Webhooks', desc: lang === 'pt' ? 'Disparar webhooks em eventos' : 'Trigger webhooks on events', icon: '⚡', color: '#A78BFA' },
            ].map(integ => {
              const cfg = agent.integrations_config || {};
              const connected = cfg[integ.key]?.enabled;
              return (
                <div key={integ.key} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg text-lg" style={{ backgroundColor: `${integ.color}10` }}>{integ.icon}</div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{integ.name}</p>
                      <p className="text-[10px] text-[#555]">{integ.desc}</p>
                    </div>
                    <button
                      data-testid={`integ-${integ.key}`}
                      onClick={() => {
                        setAgent(p => ({
                          ...p, integrations_config: { ...p.integrations_config, [integ.key]: { ...p.integrations_config?.[integ.key], enabled: !connected } }
                        }));
                      }}
                      className={`rounded-lg px-3 py-1.5 text-[11px] font-medium transition ${
                        connected ? 'bg-[#4ADE80]/10 text-[#4ADE80] border border-[#4ADE80]/20' : 'bg-[#1A1A1A] text-[#666] border border-[#1E1E1E] hover:border-[#C9A84C]/30'
                      }`}>
                      {connected ? (lang === 'pt' ? 'Conectado' : 'Connected') : (lang === 'pt' ? 'Conectar' : 'Connect')}
                    </button>
                  </div>

                  {/* Custom API config */}
                  {connected && integ.key === 'custom_api' && (
                    <div className="mt-3 space-y-2 pt-3 border-t border-[#141414]">
                      <input value={cfg.custom_api?.url || ''} onChange={e => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, custom_api: { ...p.integrations_config?.custom_api, url: e.target.value } } }))}
                        placeholder="API URL (https://...)" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#444] outline-none" />
                      <input value={cfg.custom_api?.api_key || ''} onChange={e => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, custom_api: { ...p.integrations_config?.custom_api, api_key: e.target.value } } }))}
                        placeholder="API Key" type="password" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#444] outline-none" />
                    </div>
                  )}

                  {/* Webhook config */}
                  {connected && integ.key === 'webhook' && (
                    <div className="mt-3 pt-3 border-t border-[#141414]">
                      <input value={cfg.webhook?.url || ''} onChange={e => setAgent(p => ({ ...p, integrations_config: { ...p.integrations_config, webhook: { ...p.integrations_config?.webhook, url: e.target.value } } }))}
                        placeholder="Webhook URL (https://...)" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#444] outline-none" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ============ CHANNELS ============ */}
        {tab === 'channels' && (
          <div className="space-y-4">
            <p className="text-xs text-[#666]">{lang === 'pt' ? 'Canais onde o agente atende' : 'Channels where the agent operates'}</p>

            {[
              { key: 'telegram', name: 'Telegram Bot', desc: lang === 'pt' ? 'Conecte via @BotFather' : 'Connect via @BotFather', color: '#C9A84C', hasConfig: true },
              { key: 'whatsapp', name: 'WhatsApp', desc: lang === 'pt' ? 'Via Evolution API' : 'Via Evolution API', color: '#C9A84C' },
              { key: 'instagram', name: 'Instagram DM', desc: lang === 'pt' ? 'Meta Business' : 'Meta Business', color: '#C9A84C' },
              { key: 'messenger', name: 'Facebook Messenger', desc: 'Meta Pages', color: '#C9A84C' },
              { key: 'sms', name: 'SMS', desc: 'Twilio', color: '#C9A84C' },
              { key: 'webchat', name: 'Web Chat', desc: lang === 'pt' ? 'Widget no seu site' : 'Widget on your site', color: '#C9A84C' },
            ].map(ch => {
              const chCfg = agent.channel_config || {};
              const enabled = chCfg[ch.key]?.enabled;
              return (
                <div key={ch.key} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]/8">
                      <Radio size={18} className="text-[#C9A84C]" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{ch.name}</p>
                      <p className="text-[10px] text-[#555]">{ch.desc}</p>
                    </div>
                    <button
                      data-testid={`channel-${ch.key}`}
                      onClick={() => {
                        setAgent(p => ({
                          ...p, channel_config: { ...p.channel_config, [ch.key]: { ...p.channel_config?.[ch.key], enabled: !enabled } }
                        }));
                      }}
                      className={`rounded-lg px-3 py-1.5 text-[11px] font-medium transition ${
                        enabled ? 'bg-[#4ADE80]/10 text-[#4ADE80] border border-[#4ADE80]/20' : 'bg-[#1A1A1A] text-[#666] border border-[#1E1E1E] hover:border-[#C9A84C]/30'
                      }`}>
                      {enabled ? (lang === 'pt' ? 'Ativo' : 'Active') : (lang === 'pt' ? 'Ativar' : 'Enable')}
                    </button>
                  </div>

                  {/* Telegram Bot Token config */}
                  {enabled && ch.key === 'telegram' && (
                    <div className="mt-3 space-y-2 pt-3 border-t border-[#141414]">
                      <input
                        data-testid="telegram-bot-token"
                        value={chCfg.telegram?.bot_token || ''}
                        onChange={e => setAgent(p => ({ ...p, channel_config: { ...p.channel_config, telegram: { ...p.channel_config?.telegram, bot_token: e.target.value } } }))}
                        placeholder="Bot Token (from @BotFather)"
                        className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#444] outline-none" />
                      <p className="text-[10px] text-[#555]">
                        {lang === 'pt' ? '1. Abra @BotFather no Telegram  2. Crie um bot com /newbot  3. Cole o token aqui' : '1. Open @BotFather on Telegram  2. Create bot with /newbot  3. Paste token here'}
                      </p>
                      {chCfg.telegram?.bot_token && (
                        <button
                          data-testid="telegram-connect-btn"
                          onClick={async () => {
                            try {
                              const { data } = await axios.post(`${API}/telegram/setup`, { agent_id: agentId, bot_token: chCfg.telegram.bot_token });
                              toast.success(data.message || 'Telegram connected!');
                              setAgent(p => ({ ...p, channel_config: { ...p.channel_config, telegram: { ...p.channel_config?.telegram, connected: true, bot_username: data.bot_username } } }));
                            } catch (e) {
                              toast.error(e.response?.data?.detail || 'Connection failed');
                            }
                          }}
                          className="btn-gold w-full rounded-lg py-2 text-xs">
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

        {/* ============ ESCALATION ============ */}
        {tab === 'escalation' && (
          <div className="space-y-4">
            <p className="text-xs text-[#666]">{lang === 'pt' ? 'Configure quando transferir para humano' : 'Configure when to transfer to human'}</p>

            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4 space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-[#888]">{lang === 'pt' ? 'Palavras-chave de escalacao' : 'Escalation keywords'}</label>
                <input data-testid="escalation-keywords" value={(agent.escalation_rules?.keywords || []).join(', ')}
                  onChange={e => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean) } }))}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white outline-none" />
                <p className="mt-1 text-[10px] text-[#444]">{lang === 'pt' ? 'Separadas por virgula. Ex: atendente, humano, gerente' : 'Comma separated. Ex: agent, human, manager'}</p>
              </div>

              <Slider
                label={lang === 'pt' ? 'Limiar de frustracao' : 'Frustration threshold'}
                value={agent.escalation_rules?.sentiment_threshold || 0.3}
                onChange={v => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, sentiment_threshold: v } }))}
                labelRight={[lang === 'pt' ? 'Sensivel' : 'Sensitive', lang === 'pt' ? 'Tolerante' : 'Tolerant']}
              />

              <Toggle
                label={lang === 'pt' ? 'Notificar operador' : 'Notify operator'}
                desc={lang === 'pt' ? 'Enviar notificacao quando escalar' : 'Send notification when escalating'}
                checked={agent.escalation_rules?.notify_operator !== false}
                onChange={() => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, notify_operator: !p.escalation_rules?.notify_operator } }))}
                testId="flag-notify-escalation"
              />
            </div>

            {/* System Prompt */}
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
              <label className="mb-1.5 block text-xs font-medium text-[#888]">{lang === 'pt' ? 'Prompt do Sistema (avancado)' : 'System Prompt (advanced)'}</label>
              <textarea data-testid="agent-system-prompt" value={agent.system_prompt || ''} onChange={e => setAgent(p => ({ ...p, system_prompt: e.target.value }))} rows={5}
                placeholder={lang === 'pt' ? 'Instrucoes personalizadas...' : 'Custom instructions...'}
                className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none font-mono" />
            </div>

            <button data-testid="test-agent-btn" onClick={() => navigate('/agents/sandbox')} className="flex w-full items-center justify-center gap-2 rounded-lg border border-[#C9A84C]/20 bg-[#C9A84C]/5 py-2.5 text-xs text-[#C9A84C] hover:bg-[#C9A84C]/10 transition">
              <MessageCircle size={14} /> {lang === 'pt' ? 'Testar Agente no Sandbox' : 'Test Agent in Sandbox'}
            </button>
          </div>
        )}

        {/* ============ AUTOMATIONS ============ */}
        {tab === 'automations' && (
          <div className="space-y-4">
            {/* Follow-up toggle */}
            <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-4">
              <Toggle
                label={lang === 'pt' ? 'Pos-Atendimento Automatico' : 'Auto Follow-up'}
                desc={lang === 'pt' ? 'Enviar mensagens automaticas apos o atendimento' : 'Send automatic messages after service'}
                checked={agent.follow_up_config?.enabled}
                onChange={() => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, enabled: !p.follow_up_config?.enabled } }))}
                testId="followup-toggle"
              />

              {agent.follow_up_config?.enabled && (
                <div className="mt-3 pt-3 border-t border-[#141414] grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] text-[#555]">{lang === 'pt' ? 'Max. Reativacoes' : 'Max Follow-ups'}</label>
                    <input type="number" value={agent.follow_up_config?.max_follow_ups || 3} onChange={e => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, max_follow_ups: parseInt(e.target.value) } }))}
                      className="w-full bg-transparent text-lg font-bold text-white outline-none border-b border-[#1E1E1E] focus:border-[#C9A84C]" />
                  </div>
                  <div>
                    <label className="text-[10px] text-[#555]">{lang === 'pt' ? 'Intervalo (dias)' : 'Cooldown (days)'}</label>
                    <input type="number" value={agent.follow_up_config?.cool_down_days || 7} onChange={e => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, cool_down_days: parseInt(e.target.value) } }))}
                      className="w-full bg-transparent text-lg font-bold text-white outline-none border-b border-[#1E1E1E] focus:border-[#C9A84C]" />
                  </div>
                </div>
              )}
            </div>

            {/* Rules */}
            {agent.follow_up_config?.enabled && (
              <>
                <div className="flex items-center justify-between">
                  <p className="text-xs text-[#666]">{lang === 'pt' ? 'Regras de Reativacao' : 'Reactivation Rules'}</p>
                  <button data-testid="add-rule-btn" onClick={() => setShowAddRule(!showAddRule)} className="btn-gold flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs"><Plus size={12} /> {lang === 'pt' ? 'Adicionar' : 'Add'}</button>
                </div>

                {showAddRule && (
                  <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] space-y-3 p-4">
                    <select value={newRule.trigger_type} onChange={e => setNewRule(p => ({ ...p, trigger_type: e.target.value }))}
                      className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white outline-none">
                      {TRIGGER_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label[lang] || tp.label.en}</option>)}
                    </select>
                    <input type="number" value={newRule.delay_hours} onChange={e => setNewRule(p => ({ ...p, delay_hours: parseInt(e.target.value) }))}
                      placeholder={lang === 'pt' ? 'Atraso (horas)' : 'Delay (hours)'}
                      className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white outline-none" />
                    <textarea data-testid="rule-template" value={newRule.message_template} onChange={e => setNewRule(p => ({ ...p, message_template: e.target.value }))} rows={2}
                      placeholder={lang === 'pt' ? 'Mensagem... Use {name} para nome do cliente' : 'Message... Use {name} for customer name'}
                      className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none" />
                    <button data-testid="rule-save-btn" onClick={addRule} className="btn-gold w-full rounded-lg py-2 text-xs">{lang === 'pt' ? 'Salvar' : 'Save'}</button>
                  </div>
                )}

                {rules.map(rule => (
                  <div key={rule.id} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] flex items-start gap-3 p-4">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#C9A84C]/10"><Clock size={14} className="text-[#C9A84C]" /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white">{TRIGGER_TYPES.find(t => t.value === rule.trigger_type)?.label[lang] || rule.trigger_type}</p>
                      <p className="text-[10px] text-[#555]">{lang === 'pt' ? `Apos ${rule.delay_hours}h` : `After ${rule.delay_hours}h`}</p>
                      <p className="mt-1 text-xs text-[#888] italic">"{rule.message_template}"</p>
                    </div>
                    <button onClick={() => deleteRule(rule.id)} className="text-[#444] hover:text-red-400 transition"><Trash2 size={14} /></button>
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
