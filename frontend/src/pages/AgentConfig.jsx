import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Bot, Save, Plus, Trash2, BookOpen, Clock, Sliders, Brain, MessageCircle } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TONES = [
  { value: 'professional', emoji: '👔', label: { en: 'Professional', pt: 'Profissional', es: 'Profesional' } },
  { value: 'friendly', emoji: '😊', label: { en: 'Friendly', pt: 'Amigavel', es: 'Amigable' } },
  { value: 'empathetic', emoji: '💛', label: { en: 'Empathetic', pt: 'Empatico', es: 'Empatico' } },
  { value: 'direct', emoji: '🎯', label: { en: 'Direct', pt: 'Direto', es: 'Directo' } },
  { value: 'consultive', emoji: '🤝', label: { en: 'Consultive', pt: 'Consultivo', es: 'Consultivo' } },
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
      });
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
    { key: 'followup', icon: Clock, label: { en: 'Follow-up', pt: 'Pos-atendimento', es: 'Seguimiento' } },
    { key: 'advanced', icon: Brain, label: { en: 'Advanced', pt: 'Avancado', es: 'Avanzado' } },
  ];

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-24">
      {/* Header */}
      <div className="border-b border-[#2A2A2A] px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/agents')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#C9A84C]/10"><Bot size={18} className="text-[#C9A84C]" /></div>
          <div className="flex-1">
            <input data-testid="agent-config-name" value={agent.name} onChange={e => setAgent(p => ({ ...p, name: e.target.value }))}
              className="bg-transparent text-sm font-semibold text-white outline-none border-b border-transparent focus:border-[#C9A84C] w-full" />
            <p className="text-[10px] capitalize text-[#666]">{agent.type} - {agent.tone}</p>
          </div>
          <button data-testid="agent-save-btn" onClick={saveAgent} disabled={saving}
            className="btn-gold flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs disabled:opacity-50">
            <Save size={14} /> {saving ? '...' : (lang === 'pt' ? 'Salvar' : lang === 'es' ? 'Guardar' : 'Save')}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto border-b border-[#1A1A1A] px-4 pt-2">
        {tabs.map(tb => (
          <button key={tb.key} data-testid={`tab-${tb.key}`} onClick={() => setTab(tb.key)}
            className={`flex items-center gap-1.5 whitespace-nowrap px-4 py-2.5 text-xs font-medium transition border-b-2 ${
              tab === tb.key ? 'border-[#C9A84C] text-[#C9A84C]' : 'border-transparent text-[#666] hover:text-[#A0A0A0]'}`}>
            <tb.icon size={14} /> {tb.label[lang] || tb.label.en}
          </button>
        ))}
      </div>

      <div className="px-4 pt-4">
        {/* PERSONALITY TAB */}
        {tab === 'personality' && (
          <div className="space-y-6">
            {/* Tone */}
            <div>
              <label className="mb-2 block text-xs font-medium text-[#A0A0A0]">{lang === 'pt' ? 'Tom de Atendimento' : lang === 'es' ? 'Tono de Atencion' : 'Service Tone'}</label>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {TONES.map(to => (
                  <button key={to.value} data-testid={`tone-${to.value}`} onClick={() => setAgent(p => ({ ...p, tone: to.value }))}
                    className={`glass-card p-3 text-center text-xs transition ${agent.tone === to.value ? 'border-[#C9A84C] text-[#C9A84C]' : 'text-[#A0A0A0]'}`}>
                    <span className="text-lg">{to.emoji}</span>
                    <p className="mt-1">{to.label[lang] || to.label.en}</p>
                  </button>
                ))}
              </div>
            </div>

            {/* Emoji Level */}
            <div>
              <div className="mb-2 flex justify-between"><label className="text-xs font-medium text-[#A0A0A0]">{lang === 'pt' ? 'Uso de Emojis' : lang === 'es' ? 'Uso de Emojis' : 'Emoji Usage'}</label><span className="text-xs text-[#C9A84C]">{Math.round(agent.emoji_level * 100)}%</span></div>
              <input type="range" min="0" max="1" step="0.1" value={agent.emoji_level} onChange={e => setAgent(p => ({ ...p, emoji_level: parseFloat(e.target.value) }))} className="w-full accent-[#C9A84C]" />
              <div className="flex justify-between text-[10px] text-[#444]"><span>{lang === 'pt' ? 'Nenhum' : 'None'}</span><span>{lang === 'pt' ? 'Frequente' : 'Frequent'}</span></div>
            </div>

            {/* Verbosity */}
            <div>
              <div className="mb-2 flex justify-between"><label className="text-xs font-medium text-[#A0A0A0]">{lang === 'pt' ? 'Nivel de Detalhe' : lang === 'es' ? 'Nivel de Detalle' : 'Detail Level'}</label><span className="text-xs text-[#C9A84C]">{Math.round(agent.verbosity_level * 100)}%</span></div>
              <input type="range" min="0" max="1" step="0.1" value={agent.verbosity_level} onChange={e => setAgent(p => ({ ...p, verbosity_level: parseFloat(e.target.value) }))} className="w-full accent-[#C9A84C]" />
              <div className="flex justify-between text-[10px] text-[#444]"><span>{lang === 'pt' ? 'Conciso' : 'Concise'}</span><span>{lang === 'pt' ? 'Detalhado' : 'Detailed'}</span></div>
            </div>

            {/* Preview */}
            <div className="glass-card p-4">
              <p className="mb-2 text-xs text-[#666]">{lang === 'pt' ? 'Preview da Personalidade' : 'Personality Preview'}</p>
              <div className="rounded-lg bg-[#111] p-3 border border-[#1E1E1E]">
                <p className="text-sm text-white">
                  {agent.tone === 'professional' && (agent.emoji_level > 0.4 ? 'Bom dia! 😊 Como posso ajudar com nossos serviços hoje?' : 'Bom dia. Como posso ajudá-lo hoje?')}
                  {agent.tone === 'friendly' && (agent.emoji_level > 0.4 ? 'Oi! 👋 Que bom te ver por aqui! Me conta, como posso te ajudar? 😄' : 'Oi! Que bom ter você aqui! Como posso te ajudar?')}
                  {agent.tone === 'empathetic' && (agent.emoji_level > 0.4 ? 'Olá! 💛 Entendo que isso pode ser frustrante. Estou aqui para te ajudar!' : 'Olá. Entendo sua situação e vou fazer o possível para ajudar.')}
                  {agent.tone === 'direct' && (agent.emoji_level > 0.4 ? 'Olá! 🎯 Me diga exatamente o que precisa.' : 'Olá. O que precisa?')}
                  {agent.tone === 'consultive' && (agent.emoji_level > 0.4 ? 'Olá! 🤝 Para encontrar a melhor solução, posso fazer algumas perguntas?' : 'Olá. Preciso entender melhor sua necessidade. Posso fazer algumas perguntas?')}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* KNOWLEDGE TAB */}
        {tab === 'knowledge' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-[#666]">{lang === 'pt' ? 'O agente usa essas informacoes para responder clientes' : 'The agent uses this info to answer customers'}</p>
              <button data-testid="add-knowledge-btn" onClick={() => setShowAddKb(!showAddKb)} className="btn-gold flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs"><Plus size={12} /> {lang === 'pt' ? 'Adicionar' : 'Add'}</button>
            </div>

            {showAddKb && (
              <div className="glass-card space-y-3 p-4">
                <select value={newKb.type} onChange={e => setNewKb(p => ({ ...p, type: e.target.value }))}
                  className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none">
                  {KB_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label[lang] || tp.label.en}</option>)}
                </select>
                <input data-testid="kb-title" value={newKb.title} onChange={e => setNewKb(p => ({ ...p, title: e.target.value }))} placeholder={lang === 'pt' ? 'Titulo' : 'Title'}
                  className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                <textarea data-testid="kb-content" value={newKb.content} onChange={e => setNewKb(p => ({ ...p, content: e.target.value }))} rows={3} placeholder={lang === 'pt' ? 'Conteudo que o agente deve saber...' : 'Content the agent should know...'}
                  className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none" />
                <button data-testid="kb-save-btn" onClick={addKnowledge} className="btn-gold w-full rounded-lg py-2 text-xs">{t('common.save')}</button>
              </div>
            )}

            {knowledge.map(item => (
              <div key={item.id} className="glass-card p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="rounded bg-[#C9A84C]/15 px-2 py-0.5 text-[9px] uppercase text-[#C9A84C]">{item.type}</span>
                      <h4 className="text-sm font-medium text-white truncate">{item.title}</h4>
                    </div>
                    <p className="text-xs text-[#666] line-clamp-2">{item.content}</p>
                  </div>
                  <button onClick={() => deleteKb(item.id)} className="ml-2 text-[#666] hover:text-red-400"><Trash2 size={14} /></button>
                </div>
              </div>
            ))}

            {knowledge.length === 0 && !showAddKb && (
              <div className="glass-card p-8 text-center">
                <BookOpen size={32} className="mx-auto mb-3 text-[#2A2A2A]" />
                <p className="text-sm text-[#A0A0A0]">{lang === 'pt' ? 'Nenhum conhecimento cadastrado' : 'No knowledge added yet'}</p>
                <p className="text-xs text-[#666]">{lang === 'pt' ? 'Adicione FAQs, produtos, politicas para o agente usar' : 'Add FAQs, products, policies for the agent to use'}</p>
              </div>
            )}

            {/* Knowledge Instructions */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{lang === 'pt' ? 'Instrucoes adicionais para uso do conhecimento' : 'Additional instructions for knowledge usage'}</label>
              <textarea value={agent.knowledge_instructions || ''} onChange={e => setAgent(p => ({ ...p, knowledge_instructions: e.target.value }))} rows={3}
                placeholder={lang === 'pt' ? 'Ex: Sempre mencione o horario de funcionamento quando perguntarem sobre disponibilidade...' : 'Ex: Always mention opening hours when asked about availability...'}
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none font-mono" />
            </div>
          </div>
        )}

        {/* FOLLOW-UP TAB */}
        {tab === 'followup' && (
          <div className="space-y-4">
            {/* Enable toggle */}
            <div className="glass-card flex items-center justify-between p-4">
              <div>
                <p className="text-sm font-medium text-white">{lang === 'pt' ? 'Pos-Atendimento Automatico' : 'Auto Follow-up'}</p>
                <p className="text-xs text-[#666]">{lang === 'pt' ? 'Enviar mensagens automaticas apos o atendimento' : 'Send automatic messages after service'}</p>
              </div>
              <button data-testid="followup-toggle" onClick={() => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, enabled: !p.follow_up_config?.enabled } }))}
                className={`h-6 w-11 rounded-full transition ${agent.follow_up_config?.enabled ? 'bg-[#C9A84C]' : 'bg-[#2A2A2A]'}`}>
                <div className={`h-5 w-5 rounded-full bg-white transition ${agent.follow_up_config?.enabled ? 'translate-x-5' : 'translate-x-0.5'}`} />
              </button>
            </div>

            {agent.follow_up_config?.enabled && (
              <>
                {/* Config */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="glass-card p-3">
                    <label className="text-[10px] text-[#666]">{lang === 'pt' ? 'Max. Reativacoes' : 'Max Follow-ups'}</label>
                    <input type="number" value={agent.follow_up_config?.max_follow_ups || 3} onChange={e => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, max_follow_ups: parseInt(e.target.value) } }))}
                      className="w-full bg-transparent text-lg font-bold text-white outline-none" />
                  </div>
                  <div className="glass-card p-3">
                    <label className="text-[10px] text-[#666]">{lang === 'pt' ? 'Intervalo (dias)' : 'Cooldown (days)'}</label>
                    <input type="number" value={agent.follow_up_config?.cool_down_days || 7} onChange={e => setAgent(p => ({ ...p, follow_up_config: { ...p.follow_up_config, cool_down_days: parseInt(e.target.value) } }))}
                      className="w-full bg-transparent text-lg font-bold text-white outline-none" />
                  </div>
                </div>

                {/* Rules */}
                <div className="flex items-center justify-between">
                  <p className="text-xs text-[#666]">{lang === 'pt' ? 'Regras de Reativacao' : 'Reactivation Rules'}</p>
                  <button data-testid="add-rule-btn" onClick={() => setShowAddRule(!showAddRule)} className="btn-gold flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs"><Plus size={12} /> {lang === 'pt' ? 'Adicionar' : 'Add'}</button>
                </div>

                {showAddRule && (
                  <div className="glass-card space-y-3 p-4">
                    <select value={newRule.trigger_type} onChange={e => setNewRule(p => ({ ...p, trigger_type: e.target.value }))}
                      className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none">
                      {TRIGGER_TYPES.map(tp => <option key={tp.value} value={tp.value}>{tp.label[lang] || tp.label.en}</option>)}
                    </select>
                    <div>
                      <label className="text-[10px] text-[#666]">{lang === 'pt' ? 'Atraso (horas)' : 'Delay (hours)'}</label>
                      <input type="number" value={newRule.delay_hours} onChange={e => setNewRule(p => ({ ...p, delay_hours: parseInt(e.target.value) }))}
                        className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none" />
                    </div>
                    <textarea data-testid="rule-template" value={newRule.message_template} onChange={e => setNewRule(p => ({ ...p, message_template: e.target.value }))} rows={2}
                      placeholder={lang === 'pt' ? 'Mensagem de reativacao... Use {name} para o nome do cliente' : 'Follow-up message... Use {name} for customer name'}
                      className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none" />
                    <button data-testid="rule-save-btn" onClick={addRule} className="btn-gold w-full rounded-lg py-2 text-xs">{t('common.save')}</button>
                  </div>
                )}

                {rules.map(rule => (
                  <div key={rule.id} className="glass-card flex items-start gap-3 p-4">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#C9A84C]/10"><Clock size={14} className="text-[#C9A84C]" /></div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-white">{TRIGGER_TYPES.find(t => t.value === rule.trigger_type)?.label[lang] || rule.trigger_type}</p>
                      <p className="text-[10px] text-[#666]">{lang === 'pt' ? `Apos ${rule.delay_hours}h` : `After ${rule.delay_hours}h`}</p>
                      <p className="mt-1 text-xs text-[#A0A0A0] italic">"{rule.message_template}"</p>
                    </div>
                    <button onClick={() => deleteRule(rule.id)} className="text-[#666] hover:text-red-400"><Trash2 size={14} /></button>
                  </div>
                ))}
              </>
            )}
          </div>
        )}

        {/* ADVANCED TAB */}
        {tab === 'advanced' && (
          <div className="space-y-4">
            {/* System Prompt */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{lang === 'pt' ? 'Prompt do Sistema (Personalizado)' : 'System Prompt (Custom)'}</label>
              <textarea data-testid="agent-system-prompt" value={agent.system_prompt || ''} onChange={e => setAgent(p => ({ ...p, system_prompt: e.target.value }))} rows={6}
                placeholder={lang === 'pt' ? 'Instrucoes personalizadas para o agente...' : 'Custom instructions for the agent...'}
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none font-mono" />
            </div>

            {/* Escalation Keywords */}
            <div>
              <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{lang === 'pt' ? 'Palavras de Escalacao (separadas por virgula)' : 'Escalation Keywords (comma separated)'}</label>
              <input data-testid="escalation-keywords" value={(agent.escalation_rules?.keywords || []).join(', ')}
                onChange={e => setAgent(p => ({ ...p, escalation_rules: { ...p.escalation_rules, keywords: e.target.value.split(',').map(k => k.trim()).filter(Boolean) } }))}
                className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none" />
              <p className="mt-1 text-[10px] text-[#444]">{lang === 'pt' ? 'Quando o cliente usar essas palavras, a conversa sera escalada para humano' : 'When customer uses these words, conversation will be escalated to human'}</p>
            </div>

            {/* Test button */}
            <button data-testid="test-agent-btn" onClick={() => navigate('/agents/sandbox')} className="btn-gold-outline flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-sm">
              <MessageCircle size={16} /> {lang === 'pt' ? 'Testar Agente no Sandbox' : 'Test Agent in Sandbox'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
