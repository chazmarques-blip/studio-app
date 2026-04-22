import { useState, useEffect, useMemo, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Bot, Video, BookOpen, Music, Save, X, Search,
  Sparkles, RotateCcw, History, Power, PowerOff, FileText,
  Edit3, ChevronRight, Brain, Play, Loader2, Award,
  BarChart3, Download, Upload, DollarSign, Clock, Zap
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ─── Category & phase metadata ─────────────────────────── */
const CATEGORIES = {
  video: { label: 'Vídeo', Icon: Video, accent: '#8B5CF6' },
  book:  { label: 'Livro', Icon: BookOpen, accent: '#10B981' },
  audio: { label: 'Áudio', Icon: Music, accent: '#F97316' },
};

const PHASE_LABELS = {
  research: 'Pesquisa',
  consensus: 'Consenso',
  production: 'Produção',
  validation: 'Validação',
  execution: 'Execução',
};

/* ─── Mindset Card (top-level, per category) ───────────────── */
function MindsetCard({ mindset, onEdit }) {
  const cat = CATEGORIES[mindset.category] || CATEGORIES.video;
  const Icon = cat.Icon;
  const active = mindset.active === true;
  return (
    <div
      onClick={() => onEdit(mindset)}
      data-testid={`mindset-card-${mindset.category}`}
      className="group relative flex items-start gap-3 p-4 rounded-xl border-2 border-dashed border-violet-300 dark:border-violet-500/30 bg-gradient-to-br from-violet-50/60 to-orange-50/30 dark:from-violet-500/5 dark:to-orange-500/5 hover:border-violet-500 dark:hover:border-violet-400 cursor-pointer transition-all"
    >
      <div
        className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
        style={{ background: `linear-gradient(135deg, ${cat.accent}33, ${cat.accent}11)` }}
      >
        <Brain size={18} style={{ color: cat.accent }} strokeWidth={1.75} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <h3 className="text-[13px] font-bold text-gray-900 dark:text-white truncate">
            Mentalidade Global · {cat.label}
          </h3>
          {active ? (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold bg-violet-600 text-white">
              <Power size={8} className="inline mr-0.5" strokeWidth={2.5} />
              ATIVA
            </span>
          ) : (
            <span className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold bg-gray-200 dark:bg-[#2A2442] text-gray-600 dark:text-[#A3A3B2]">
              INATIVA
            </span>
          )}
        </div>
        <p className="text-[11px] text-gray-600 dark:text-[#A3A3B2] mt-1 line-clamp-2 leading-snug">
          {mindset.system_prompt?.split('\n')[0] || 'Preâmbulo aplicado a todos os agentes desta pipeline.'}
        </p>
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-violet-600 dark:text-violet-400 mt-1.5 opacity-0 group-hover:opacity-100 transition">
          <Edit3 size={10} /> Editar mentalidade
        </span>
      </div>
    </div>
  );
}

/* ─── Agent Card ──────────────────────────────────────────── */
function AgentCard({ agent, onEdit }) {
  const cat = CATEGORIES[agent.category] || CATEGORIES.video;
  const Icon = cat.Icon;
  const active = agent.active === true;
  return (
    <div
      onClick={() => onEdit(agent)}
      data-testid={`agent-card-${agent.id}`}
      className="group relative flex flex-col gap-2 p-4 rounded-xl border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#1A1430] hover:border-violet-300 dark:hover:border-violet-500/40 hover:shadow-sm cursor-pointer transition-all"
    >
      <div className="flex items-start gap-3">
        <div
          className="h-9 w-9 rounded-lg flex items-center justify-center shrink-0 shadow-sm"
          style={{ background: `linear-gradient(135deg, ${cat.accent}22, ${cat.accent}08)` }}
        >
          <Icon size={16} style={{ color: cat.accent }} strokeWidth={1.75} />
        </div>
        <div className="flex-1 min-w-0">
          {agent.master_reference ? (
            <>
              <h3 className="text-[13px] font-bold text-gray-900 dark:text-white truncate leading-tight inline-flex items-center gap-1">
                <Award size={11} style={{ color: cat.accent }} />
                {agent.master_reference}
              </h3>
              <p className="text-[10px] text-gray-500 dark:text-[#A3A3B2] truncate mt-0.5">
                {agent.name}
              </p>
            </>
          ) : (
            <h3 className="text-[13px] font-semibold text-gray-900 dark:text-white truncate leading-tight">
              {agent.name}
            </h3>
          )}
          <div className="flex items-center gap-1.5 mt-1">
            {agent.phase && (
              <span className="text-[10px] font-mono uppercase tracking-wide text-gray-500 dark:text-[#A3A3B2]">
                {PHASE_LABELS[agent.phase] || agent.phase}
              </span>
            )}
            {active ? (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold"
                style={{ background: `${cat.accent}22`, color: cat.accent }}
                title="Prompt customizado ativo"
              >
                <Power size={8} className="inline mr-0.5" strokeWidth={2.5} />
                CUSTOM
              </span>
            ) : (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold bg-gray-100 dark:bg-[#2A2442] text-gray-500 dark:text-[#A3A3B2]"
                title="Usando prompt padrão do sistema"
              >
                <PowerOff size={8} className="inline mr-0.5" strokeWidth={2.5} />
                DEFAULT
              </span>
            )}
          </div>
        </div>
      </div>
      <p className="text-[11px] text-gray-600 dark:text-[#A3A3B2] line-clamp-2 leading-snug">
        {agent.description || 'Sem descrição'}
      </p>
      <div className="flex items-center justify-between pt-1">
        <span className="text-[10px] font-mono text-gray-400 dark:text-[#6B647F]">
          v{agent.version || '1.0.0'} {agent.updated_at && `· ${agent.updated_at}`}
        </span>
        <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-violet-600 dark:text-violet-400 opacity-0 group-hover:opacity-100 transition">
          <Edit3 size={10} /> Editar
        </span>
      </div>
    </div>
  );
}

/* ─── Mindset Editor Modal ────────────────────────────────── */
function MindsetEditor({ mindset, onClose, onSaved }) {
  const [data, setData] = useState({ ...mindset });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/studio/agents/mindsets/${data.category}`, {
        active: data.active,
        system_prompt: data.system_prompt,
        temperature: data.temperature ?? 0.7,
        title: data.title,
      });
      toast.success(`Mentalidade ${CATEGORIES[data.category].label} atualizada`);
      onSaved();
      onClose();
    } catch (e) {
      toast.error('Erro ao salvar mentalidade');
    } finally {
      setSaving(false);
    }
  };

  const cat = CATEGORIES[data.category];
  const Icon = cat.Icon;

  return (
    <div
      className="fixed inset-y-0 right-0 left-0 md:left-60 top-12 z-[100] bg-black/60 backdrop-blur-sm flex items-start justify-center p-6 overflow-y-auto"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        data-testid="mindset-editor-modal"
        className="w-full max-w-3xl rounded-2xl border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] shadow-2xl my-6"
      >
        <div className="px-6 py-4 border-b border-gray-200 dark:border-[#2A2442] flex items-center gap-3">
          <div
            className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `linear-gradient(135deg, ${cat.accent}33, ${cat.accent}11)` }}
          >
            <Brain size={18} style={{ color: cat.accent }} strokeWidth={1.75} />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-bold text-gray-900 dark:text-white truncate">
              {data.title}
            </h2>
            <p className="text-[11px] text-gray-500 dark:text-[#A3A3B2]">
              Aplicada a TODOS os agentes da pipeline de {cat.label}
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition">
            <X size={18} />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5 max-h-[70vh] overflow-y-auto">
          <div
            className={`flex items-start gap-3 p-3 rounded-lg text-[12px] ${
              data.active
                ? 'bg-violet-50 dark:bg-violet-500/10 border border-violet-200 dark:border-violet-500/30'
                : 'bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442]'
            }`}
          >
            <Sparkles size={14} className="mt-0.5 text-violet-600 dark:text-violet-400" />
            <div className="flex-1">
              <p className="text-gray-900 dark:text-white font-medium">
                {data.active ? 'Mentalidade ATIVA — será concatenada a cada agente' : 'Mentalidade INATIVA — agentes usam apenas seu próprio prompt'}
              </p>
              <p className="text-gray-600 dark:text-[#A3A3B2] mt-0.5">
                {data.active
                  ? 'Este preâmbulo é prepended no system prompt de CADA agente da pipeline antes da execução.'
                  : 'Ative para que a filosofia do estúdio oriente todos os agentes desta pipeline.'}
              </p>
            </div>
            <button
              onClick={() => setData({ ...data, active: !data.active })}
              data-testid="mindset-active-toggle"
              className={`shrink-0 inline-flex items-center gap-1 h-7 px-3 rounded-full text-[11px] font-semibold transition ${
                data.active ? 'bg-violet-600 text-white' : 'bg-gray-200 dark:bg-[#2A2442] text-gray-600 dark:text-[#A3A3B2]'
              }`}
            >
              {data.active ? <Power size={11} /> : <PowerOff size={11} />}
              {data.active ? 'ATIVA' : 'INATIVA'}
            </button>
          </div>

          <Field label="Mentalidade (System Prompt)" hint="Esta é a 'filosofia do estúdio' — princípios que todo agente desta pipeline deve internalizar antes de executar sua tarefa específica.">
            <textarea
              value={data.system_prompt || ''}
              onChange={(e) => setData({ ...data, system_prompt: e.target.value })}
              data-testid="mindset-prompt"
              rows={16}
              className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-2 text-[12px] font-mono text-gray-900 dark:text-white outline-none focus:border-violet-500 transition resize-y"
            />
          </Field>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-[#2A2442] flex items-center justify-end gap-2 bg-gray-50 dark:bg-[#0A0614] rounded-b-2xl">
          <button onClick={onClose} className="h-9 px-4 rounded-lg text-[12px] font-medium text-gray-700 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-white/5 transition">
            Cancelar
          </button>
          <button
            onClick={save}
            disabled={saving}
            data-testid="mindset-save-btn"
            className="h-9 px-5 rounded-lg bg-gradient-to-r from-violet-600 to-orange-500 text-white text-[12px] font-semibold inline-flex items-center gap-1.5 hover:brightness-110 transition disabled:opacity-50"
          >
            <Save size={13} />
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─── Agent Editor Modal (with Playground) ───────────────── */
function AgentEditor({ agent, onClose, onSaved }) {
  const [data, setData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [tab, setTab] = useState('edit'); // 'edit' | 'playground'

  // Playground state
  const [plInput, setPlInput] = useState('');
  const [plOutput, setPlOutput] = useState('');
  const [plLoading, setPlLoading] = useState(false);
  const [plIncludeMindset, setPlIncludeMindset] = useState(true);

  useEffect(() => {
    if (!agent) return;
    (async () => {
      try {
        const { data: res } = await axios.get(`${API}/studio/agents/registry/${agent.id}`);
        setData({
          ...res.agent,
          active: res.agent.active === true,
          temperature: res.agent.temperature ?? 0.7,
          min_quality_score: res.agent.min_quality_score ?? 80,
        });
      } catch (e) {
        toast.error('Erro ao carregar agente');
        onClose();
      }
    })();
  }, [agent, onClose]);

  const save = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/studio/agents/registry/${agent.id}`, data);
      toast.success('Agente atualizado — pipeline usará o novo prompt');
      onSaved();
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao salvar');
    } finally {
      setSaving(false);
    }
  };

  const runPlayground = async () => {
    if (!plInput.trim()) { toast.error('Digite uma entrada de teste'); return; }
    setPlLoading(true); setPlOutput('');
    try {
      const { data: res } = await axios.post(`${API}/studio/agents/playground`, {
        agent_id: agent.id,
        system_prompt: data.system_prompt,
        user_input: plInput,
        temperature: data.temperature ?? 0.7,
        include_mindset: plIncludeMindset,
      });
      setPlOutput(res.output || '(sem resposta)');
    } catch (e) {
      setPlOutput(`❌ Erro: ${e.response?.data?.detail || e.message}`);
    } finally {
      setPlLoading(false);
    }
  };

  const rollback = async (index) => {
    if (!window.confirm('Restaurar esta versão? O prompt atual será substituído.')) return;
    try {
      await axios.post(`${API}/studio/agents/registry/${agent.id}/rollback`, { index });
      toast.success('Versão restaurada');
      onSaved(); onClose();
    } catch (e) {
      toast.error('Erro ao reverter');
    }
  };

  if (!agent) return null;
  const cat = CATEGORIES[agent.category] || CATEGORIES.video;
  const Icon = cat.Icon;

  return (
    <div
      className="fixed inset-y-0 right-0 left-0 md:left-60 top-12 z-[100] bg-black/60 backdrop-blur-sm flex items-start justify-center p-6 overflow-y-auto"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        data-testid="agent-editor-modal"
        className="w-full max-w-3xl rounded-2xl border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] shadow-2xl my-6"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-[#2A2442] flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0" style={{ background: `linear-gradient(135deg, ${cat.accent}33, ${cat.accent}11)` }}>
            <Icon size={18} style={{ color: cat.accent }} strokeWidth={1.75} />
          </div>
          <div className="flex-1 min-w-0">
            {data?.master_reference ? (
              <>
                <h2 className="text-base font-bold text-gray-900 dark:text-white truncate inline-flex items-center gap-1.5">
                  <Award size={13} style={{ color: cat.accent }} />
                  {data.master_reference}
                </h2>
                <p className="text-[11px] text-gray-500 dark:text-[#A3A3B2]">
                  {data.name} · {agent.id} · {PHASE_LABELS[agent.phase] || agent.phase}
                </p>
              </>
            ) : (
              <h2 className="text-base font-bold text-gray-900 dark:text-white truncate">{agent.name}</h2>
            )}
          </div>
          <button onClick={onClose} className="p-2 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition">
            <X size={18} />
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 border-b border-gray-200 dark:border-[#2A2442] flex items-center gap-1">
          {[
            { key: 'edit', label: 'Editar Prompt', Icon: Edit3 },
            { key: 'playground', label: 'Playground', Icon: Play },
          ].map(({ key, label, Icon: TI }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              data-testid={`agent-tab-${key}`}
              className={`inline-flex items-center gap-1.5 px-3 h-10 text-[12px] font-semibold border-b-2 transition ${
                tab === key
                  ? 'border-violet-600 text-violet-600 dark:text-violet-400'
                  : 'border-transparent text-gray-500 dark:text-[#A3A3B2] hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              <TI size={12} /> {label}
            </button>
          ))}
        </div>

        {!data ? (
          <div className="p-10 text-center text-sm text-gray-500">Carregando...</div>
        ) : tab === 'edit' ? (
          <div className="px-6 py-5 space-y-5 max-h-[60vh] overflow-y-auto">
            {/* Status banner */}
            <div className={`flex items-start gap-3 p-3 rounded-lg text-[12px] ${data.active ? 'bg-violet-50 dark:bg-violet-500/10 border border-violet-200 dark:border-violet-500/30' : 'bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442]'}`}>
              <Sparkles size={14} className="mt-0.5 text-violet-600 dark:text-violet-400" />
              <div className="flex-1">
                <p className="text-gray-900 dark:text-white font-medium">
                  {data.active ? 'Prompt customizado ATIVO' : 'Usando prompt padrão do sistema'}
                </p>
                <p className="text-gray-600 dark:text-[#A3A3B2] mt-0.5">
                  {data.active
                    ? 'Toda execução da pipeline usará o prompt abaixo. Se algo quebrar, desative.'
                    : 'Ative o toggle para que a pipeline use o prompt customizado abaixo.'}
                </p>
              </div>
              <button
                onClick={() => setData({ ...data, active: !data.active })}
                data-testid="agent-active-toggle"
                className={`shrink-0 inline-flex items-center gap-1 h-7 px-3 rounded-full text-[11px] font-semibold transition ${data.active ? 'bg-violet-600 text-white' : 'bg-gray-200 dark:bg-[#2A2442] text-gray-600 dark:text-[#A3A3B2]'}`}
              >
                {data.active ? <Power size={11} /> : <PowerOff size={11} />}
                {data.active ? 'ATIVO' : 'DESATIVADO'}
              </button>
            </div>

            {/* Master bio if present */}
            {data.master_bio && (
              <Field label="Sobre o mestre (referência)">
                <p className="text-[12px] text-gray-700 dark:text-[#A3A3B2] italic leading-snug bg-gray-50 dark:bg-[#0A0614] rounded-lg p-3 border border-gray-200 dark:border-[#2A2442]">
                  {data.master_bio}
                </p>
              </Field>
            )}

            <Field label="Descrição (interna)">
              <textarea
                value={data.description || ''}
                onChange={(e) => setData({ ...data, description: e.target.value })}
                rows={2}
                className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-2 text-[13px] text-gray-900 dark:text-white outline-none focus:border-violet-500 transition resize-y"
              />
            </Field>

            <Field label="System Prompt" hint={data.active ? 'Prompt enviado ao LLM. Mantenha placeholders como {lang_name}.' : 'Pré-visualização. Ative o toggle para usar na pipeline.'}>
              <textarea
                value={data.system_prompt || ''}
                onChange={(e) => setData({ ...data, system_prompt: e.target.value })}
                data-testid="agent-system-prompt"
                rows={14}
                className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-2 text-[12px] font-mono text-gray-900 dark:text-white outline-none focus:border-violet-500 transition resize-y"
              />
            </Field>

            <div className="grid grid-cols-2 gap-4">
              <Field label={`Temperatura: ${(data.temperature ?? 0.7).toFixed(2)}`} hint="0 = determinístico · 1 = criativo">
                <input type="range" min={0} max={1} step={0.05} value={data.temperature ?? 0.7}
                  onChange={(e) => setData({ ...data, temperature: parseFloat(e.target.value) })}
                  className="w-full accent-violet-600" />
              </Field>
              <Field label={`Min. Quality Score: ${data.min_quality_score ?? 80}`} hint="0–100">
                <input type="range" min={0} max={100} step={5} value={data.min_quality_score ?? 80}
                  onChange={(e) => setData({ ...data, min_quality_score: parseInt(e.target.value) })}
                  className="w-full accent-violet-600" />
              </Field>
            </div>

            {Array.isArray(data.responsibilities) && data.responsibilities.length > 0 && (
              <Field label="Responsabilidades">
                <ul className="space-y-1 text-[12px] text-gray-700 dark:text-[#A3A3B2] pl-4 list-disc">
                  {data.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </Field>
            )}

            {Array.isArray(data.edit_history) && data.edit_history.length > 0 && (
              <div>
                <button onClick={() => setShowHistory((v) => !v)} className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-violet-600 dark:text-violet-400 hover:underline">
                  <History size={13} /> Histórico ({data.edit_history.length})
                  <ChevronRight size={12} className={`transition ${showHistory ? 'rotate-90' : ''}`} />
                </button>
                {showHistory && (
                  <div className="mt-2 space-y-2 max-h-48 overflow-y-auto border border-gray-200 dark:border-[#2A2442] rounded-lg p-2">
                    {[...data.edit_history].reverse().map((h, i) => {
                      const realIdx = data.edit_history.length - 1 - i;
                      return (
                        <div key={i} className="flex items-start gap-2 text-[11px]">
                          <span className="font-mono text-gray-400 dark:text-[#6B647F] shrink-0">#{realIdx}</span>
                          <div className="flex-1 min-w-0">
                            <p className="text-gray-700 dark:text-[#A3A3B2] truncate">
                              {h.timestamp?.replace('T', ' ').replace('Z', '')} · {h.by || 'unknown'}
                              {h.note && <span className="ml-1 text-orange-500">({h.note})</span>}
                            </p>
                          </div>
                          <button onClick={() => rollback(realIdx)} className="shrink-0 text-[10px] text-violet-600 dark:text-violet-400 hover:underline inline-flex items-center gap-0.5">
                            <RotateCcw size={10} /> Restaurar
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          /* Playground tab */
          <div className="px-6 py-5 space-y-4 max-h-[60vh] overflow-y-auto">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-orange-50 dark:bg-orange-500/10 border border-orange-200 dark:border-orange-500/30 text-[12px]">
              <Play size={14} className="mt-0.5 text-orange-600 dark:text-orange-400" />
              <div className="flex-1">
                <p className="text-gray-900 dark:text-white font-medium">Playground de Teste Rápido</p>
                <p className="text-gray-600 dark:text-[#A3A3B2] mt-0.5">
                  Testa o prompt atual (não salvo ainda) com uma entrada customizada. Útil para iterar antes de salvar.
                </p>
              </div>
            </div>

            <Field label="Entrada de teste (simula briefing do usuário)">
              <textarea
                value={plInput}
                onChange={(e) => setPlInput(e.target.value)}
                data-testid="playground-input"
                rows={4}
                placeholder="Ex: Crie um roteiro curto sobre duas irmãs que se reencontram após 20 anos em uma viagem à Itália..."
                className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-2 text-[13px] text-gray-900 dark:text-white outline-none focus:border-violet-500 transition resize-y"
              />
            </Field>

            <label className="flex items-center gap-2 text-[11px] text-gray-700 dark:text-[#A3A3B2] cursor-pointer">
              <input
                type="checkbox"
                checked={plIncludeMindset}
                onChange={(e) => setPlIncludeMindset(e.target.checked)}
                className="accent-violet-600"
              />
              Aplicar Mentalidade Global de <strong className="text-gray-900 dark:text-white">{cat.label}</strong> no teste
            </label>

            <button
              onClick={runPlayground}
              disabled={plLoading || !plInput.trim()}
              data-testid="playground-run"
              className="h-10 px-5 rounded-lg bg-gradient-to-r from-orange-500 to-orange-600 text-white text-[13px] font-semibold inline-flex items-center gap-2 hover:brightness-110 transition disabled:opacity-50"
            >
              {plLoading ? <Loader2 size={14} className="animate-spin" /> : <Play size={13} />}
              {plLoading ? 'Gerando...' : 'Executar Teste'}
            </button>

            {plOutput && (
              <Field label="Saída do LLM">
                <pre
                  data-testid="playground-output"
                  className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-3 text-[12px] text-gray-900 dark:text-white whitespace-pre-wrap break-words max-h-80 overflow-y-auto"
                >
                  {plOutput}
                </pre>
              </Field>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-[#2A2442] flex items-center justify-end gap-2 bg-gray-50 dark:bg-[#0A0614] rounded-b-2xl">
          <button onClick={onClose} className="h-9 px-4 rounded-lg text-[12px] font-medium text-gray-700 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-white/5 transition">
            Cancelar
          </button>
          <button onClick={save} disabled={saving || !data}
            data-testid="agent-save-btn"
            className="h-9 px-5 rounded-lg bg-gradient-to-r from-violet-600 to-orange-500 text-white text-[12px] font-semibold inline-flex items-center gap-1.5 hover:brightness-110 transition disabled:opacity-50">
            <Save size={13} />
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-gray-700 dark:text-[#A3A3B2] uppercase tracking-wide mb-1.5">
        {label}
      </label>
      {children}
      {hint && <p className="text-[10px] text-gray-500 dark:text-[#6B647F] mt-1">{hint}</p>}
    </div>
  );
}

/* ─── Main Page ───────────────────────────────────────────── */
export function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [mindsets, setMindsets] = useState({});
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');
  const [editingAgent, setEditingAgent] = useState(null);
  const [editingMindset, setEditingMindset] = useState(null);
  const [metricsOpen, setMetricsOpen] = useState(false);
  const fileInputRef = useRef(null);

  const load = async () => {
    try {
      const [ag, mi] = await Promise.all([
        axios.get(`${API}/studio/agents/registry`),
        axios.get(`${API}/studio/agents/mindsets`),
      ]);
      setAgents(ag.data.agents || []);
      setMindsets(mi.data.mindsets || {});
    } catch (e) {
      toast.error('Erro ao carregar agentes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleExport = async () => {
    try {
      const { data } = await axios.get(`${API}/studio/agents/export`);
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const ts = new Date().toISOString().slice(0, 10);
      a.href = url; a.download = `studiox-agents-${ts}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
      toast.success(`Exportado: ${data.counts?.agents || 0} agentes + ${data.counts?.mindsets || 0} mindsets`);
    } catch (e) {
      toast.error('Falha ao exportar');
    }
  };

  const handleImport = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const payload = JSON.parse(text);
      // By default: overwrite=false (additive). Ask confirmation for overwrite.
      const shouldOverwrite = window.confirm(
        `Importar ${payload.agents?.length || 0} agentes e ${Object.keys(payload.mindsets || {}).length} mindsets.\n\nOK = substituir existentes\nCancelar = apenas adicionar novos`
      );
      const { data } = await axios.post(`${API}/studio/agents/import`, {
        ...payload,
        overwrite: shouldOverwrite,
      });
      toast.success(
        `Importados: ${data.imported_agents} agentes + ${data.imported_mindsets} mindsets (${data.skipped} pulados)`
      );
      if (data.errors?.length) {
        toast.warning(`${data.errors.length} erros — veja console`);
        console.warn('Import errors:', data.errors);
      }
      await load();
    } catch (e) {
      toast.error(`Erro ao importar: ${e.message || 'arquivo inválido'}`);
    } finally {
      // Reset input so same file can be re-selected
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const counts = useMemo(() => {
    const c = { all: agents.length, video: 0, book: 0, audio: 0 };
    agents.forEach((a) => { c[a.category] = (c[a.category] || 0) + 1; });
    return c;
  }, [agents]);

  const filtered = useMemo(() => {
    return agents.filter((a) => {
      if (tab !== 'all' && a.category !== tab) return false;
      if (search && !((a.name || '').toLowerCase().includes(search.toLowerCase()) ||
                       (a.master_reference || '').toLowerCase().includes(search.toLowerCase()) ||
                       (a.description || '').toLowerCase().includes(search.toLowerCase()))) return false;
      return true;
    });
  }, [agents, tab, search]);

  const grouped = useMemo(() => {
    if (tab !== 'all') return null;
    const g = { video: [], book: [], audio: [] };
    filtered.forEach((a) => { (g[a.category] || g.video).push(a); });
    return g;
  }, [filtered, tab]);

  const visibleCategories = tab === 'all' ? ['video', 'book', 'audio'] : [tab];

  return (
    <div className="min-h-screen bg-[#FAFAFC] dark:bg-[#0A0614]" style={{ fontFamily: "'Outfit', system-ui" }}>
      {/* Context bar */}
      <div className="sticky top-0 z-20 bg-white dark:bg-[#0A0614] border-b border-gray-200 dark:border-[#2A2442]">
        <div className="max-w-7xl mx-auto px-6 h-12 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Bot size={16} className="text-violet-600 dark:text-violet-400" />
            <h1 className="text-[15px] font-semibold tracking-tight text-gray-900 dark:text-white">
              Agentes de IA
            </h1>
            <span className="text-[10px] font-mono text-gray-400 dark:text-[#6B647F]">{agents.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400 dark:text-[#6B647F]" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar agente ou mestre..."
                className="h-7 pl-7 pr-3 rounded-md bg-gray-100 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-[#6B647F] outline-none focus:border-violet-500 transition w-52"
              />
            </div>
            <button
              onClick={() => setMetricsOpen(true)}
              data-testid="btn-open-metrics"
              className="h-7 inline-flex items-center gap-1 px-2.5 rounded-md bg-gray-100 hover:bg-violet-50 border border-gray-200 hover:border-violet-300 text-[11px] font-medium text-gray-700 hover:text-violet-700 transition"
              title="Ver métricas dos agentes"
            >
              <BarChart3 size={12} /> Métricas
            </button>
            <button
              onClick={handleExport}
              data-testid="btn-export-agents"
              className="h-7 inline-flex items-center gap-1 px-2.5 rounded-md bg-gray-100 hover:bg-emerald-50 border border-gray-200 hover:border-emerald-300 text-[11px] font-medium text-gray-700 hover:text-emerald-700 transition"
              title="Exportar agentes + mindsets"
            >
              <Download size={12} /> Exportar
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              data-testid="btn-import-agents"
              className="h-7 inline-flex items-center gap-1 px-2.5 rounded-md bg-gray-100 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 text-[11px] font-medium text-gray-700 hover:text-blue-700 transition"
              title="Importar configuração"
            >
              <Upload size={12} /> Importar
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json,application/json"
              onChange={handleImport}
              className="hidden"
              data-testid="import-file-input"
            />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-6 pt-5">
        <div className="max-w-7xl mx-auto flex items-center gap-2 flex-wrap" data-testid="agent-tabs">
          {[
            { key: 'all', label: 'Todos', Icon: Sparkles, count: counts.all },
            { key: 'video', label: 'Vídeo', Icon: Video, count: counts.video },
            { key: 'book', label: 'Livro', Icon: BookOpen, count: counts.book },
            { key: 'audio', label: 'Áudio', Icon: Music, count: counts.audio },
          ].map(({ key, label, Icon, count }) => {
            const active = tab === key;
            return (
              <button
                key={key}
                onClick={() => setTab(key)}
                data-testid={`agent-tab-${key}`}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                  active
                    ? 'bg-violet-600 text-white border-violet-600 shadow-sm'
                    : 'bg-white dark:bg-[#1A1430] text-gray-700 dark:text-[#A3A3B2] border-gray-200 dark:border-[#2A2442] hover:border-violet-300 dark:hover:border-violet-500/40'
                }`}
              >
                <Icon size={12} />
                {label}
                <span className={`ml-0.5 font-mono text-[10px] px-1.5 py-0.5 rounded-full ${active ? 'bg-white/25 text-white' : 'bg-gray-100 dark:bg-[#0A0614] text-gray-600 dark:text-[#A3A3B2]'}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Info banner */}
      <div className="px-6 mt-4">
        <div className="max-w-7xl mx-auto">
          <div className="rounded-xl border border-violet-200 dark:border-violet-500/20 bg-violet-50/50 dark:bg-violet-500/5 px-4 py-3 flex items-start gap-3">
            <FileText size={14} className="mt-0.5 text-violet-600 dark:text-violet-400 shrink-0" />
            <div className="text-[11px] text-gray-700 dark:text-[#A3A3B2] leading-snug">
              <p className="text-gray-900 dark:text-white font-semibold mb-0.5">Como funciona</p>
              A <strong>Mentalidade Global</strong> é a filosofia do estúdio — é <strong>prepended</strong> ao prompt de cada agente daquela pipeline. Os <strong>agentes</strong> são mestres reconhecidos mundialmente com sua assinatura técnica. Ative ambos para combinar filosofia + expertise. Use o <strong>Playground</strong> para testar antes de salvar.
            </div>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="px-6 py-5 pb-20">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="py-20 text-center text-sm text-gray-500 dark:text-[#A3A3B2]">Carregando...</div>
          ) : filtered.length === 0 && Object.keys(mindsets).length === 0 ? (
            <div className="py-20 flex flex-col items-center text-center">
              <div className="h-14 w-14 rounded-xl bg-gray-100 dark:bg-[#1A1430] flex items-center justify-center mb-3">
                <Bot size={24} className="text-gray-400 dark:text-[#6B647F]" />
              </div>
              <p className="text-sm text-gray-700 dark:text-white font-semibold">Nenhum agente encontrado</p>
              <p className="text-xs text-gray-500 dark:text-[#A3A3B2] mt-1">Ajuste a busca ou mude de categoria</p>
            </div>
          ) : (
            <div className="space-y-7">
              {visibleCategories.map((cat) => {
                const catMeta = CATEGORIES[cat];
                if (!catMeta) return null;
                const CatIcon = catMeta.Icon;
                const list = (grouped ? grouped[cat] : filtered) || [];
                const mindset = mindsets[cat];
                if (list.length === 0 && !mindset) return null;
                return (
                  <section key={cat}>
                    <header className="flex items-center gap-2 mb-3">
                      <CatIcon size={13} style={{ color: catMeta.accent }} />
                      <h2 className="text-[11px] font-bold uppercase tracking-wider text-gray-700 dark:text-white">
                        Pipeline de {catMeta.label}
                      </h2>
                      <span className="text-[10px] font-mono text-gray-400 dark:text-[#6B647F]">
                        {list.length} agente{list.length !== 1 && 's'}
                      </span>
                    </header>
                    {/* Mindset card always first */}
                    {mindset && (
                      <div className="mb-3">
                        <MindsetCard mindset={mindset} onEdit={setEditingMindset} />
                      </div>
                    )}
                    {list.length > 0 && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {list.map((a) => <AgentCard key={a.id} agent={a} onEdit={setEditingAgent} />)}
                      </div>
                    )}
                  </section>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {editingAgent && (
        <AgentEditor agent={editingAgent} onClose={() => setEditingAgent(null)} onSaved={load} />
      )}
      {editingMindset && (
        <MindsetEditor mindset={editingMindset} onClose={() => setEditingMindset(null)} onSaved={load} />
      )}
      {metricsOpen && (
        <MetricsModal agents={agents} onClose={() => setMetricsOpen(false)} />
      )}
    </div>
  );
}

/* ─── Metrics Modal ───────────────────────────────────────── */
function MetricsModal({ agents, onClose }) {
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({});
  const [totals, setTotals] = useState({ activations: 0, estimated_cost_usd: 0, total_duration_seconds: 0 });

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/studio/agents/metrics`);
      setMetrics(data.metrics || {});
      setTotals(data.totals || {});
    } catch {
      toast.error('Erro ao carregar métricas');
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => { load(); }, []);

  const reset = async () => {
    if (!window.confirm('Zerar todas as métricas? Isso não pode ser desfeito.')) return;
    try {
      await axios.post(`${API}/studio/agents/metrics/reset`);
      toast.success('Métricas resetadas');
      await load();
    } catch {
      toast.error('Falha ao resetar');
    }
  };

  const rows = useMemo(() => {
    const byId = {};
    agents.forEach((a) => { byId[a.id] = a; });
    return Object.entries(metrics || {}).map(([id, m]) => ({
      id,
      agent: byId[id],
      ...m,
    })).sort((a, b) => (b.activations || 0) - (a.activations || 0));
  }, [metrics, agents]);

  return (
    <div className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" data-testid="metrics-modal">
      <div className="w-full max-w-4xl bg-white rounded-xl shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-violet-600" />
            <h2 className="text-sm font-bold text-gray-900">Métricas dos Agentes</h2>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={reset} data-testid="metrics-reset-btn" className="text-[11px] text-red-600 hover:text-red-700 font-medium">Zerar</button>
            <button onClick={onClose} data-testid="metrics-close-btn" className="h-7 w-7 rounded-md hover:bg-gray-100 flex items-center justify-center">
              <X size={14} />
            </button>
          </div>
        </div>

        {/* Totals */}
        <div className="grid grid-cols-3 gap-3 p-5 border-b border-gray-100 bg-gray-50">
          <StatBox Icon={Zap} label="Ativações Totais" value={totals.activations ?? 0} color="#8B5CF6" />
          <StatBox Icon={DollarSign} label="Custo Estimado" value={`$${(totals.estimated_cost_usd ?? 0).toFixed(4)}`} color="#10B981" />
          <StatBox Icon={Clock} label="Tempo Total" value={formatDuration(totals.total_duration_seconds ?? 0)} color="#F97316" />
        </div>

        {/* Rows */}
        <div className="max-h-[50vh] overflow-y-auto">
          {loading ? (
            <div className="p-10 text-center text-gray-500 text-xs"><Loader2 size={16} className="animate-spin inline mr-2" /> Carregando…</div>
          ) : rows.length === 0 ? (
            <div className="p-10 text-center text-gray-500 text-xs" data-testid="metrics-empty">
              Nenhuma ativação registrada ainda.<br />
              <span className="text-[10px] text-gray-400">Execute um projeto para começar a coletar métricas.</span>
            </div>
          ) : (
            <table className="w-full text-xs">
              <thead className="bg-white sticky top-0 border-b border-gray-200">
                <tr className="text-left text-[10px] uppercase tracking-wider text-gray-500">
                  <th className="px-4 py-2 font-semibold">Agente</th>
                  <th className="px-3 py-2 font-semibold text-right">Ativações</th>
                  <th className="px-3 py-2 font-semibold text-right">Latência Média</th>
                  <th className="px-3 py-2 font-semibold text-right">Custo</th>
                  <th className="px-3 py-2 font-semibold text-right">Última uso</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id} data-testid={`metrics-row-${r.id}`} className="border-b border-gray-50 hover:bg-violet-50/40">
                    <td className="px-4 py-2.5">
                      <div className="font-medium text-gray-900">{r.agent?.name || r.id}</div>
                      {r.agent?.master_reference && (
                        <div className="text-[10px] text-orange-600 flex items-center gap-1">
                          <Award size={9} /> {r.agent.master_reference}
                        </div>
                      )}
                    </td>
                    <td className="px-3 py-2.5 text-right tabular-nums font-semibold text-violet-700">{r.activations || 0}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-gray-700">{formatDuration(r.avg_latency_seconds || 0)}</td>
                    <td className="px-3 py-2.5 text-right tabular-nums text-emerald-700 font-medium">${(r.estimated_cost_usd || 0).toFixed(4)}</td>
                    <td className="px-3 py-2.5 text-right text-[10px] text-gray-500">{r.last_used_at ? new Date(r.last_used_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

function StatBox({ Icon, label, value, color }) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3">
      <div className="flex items-center gap-2 mb-1">
        <div className="h-6 w-6 rounded-md flex items-center justify-center" style={{ backgroundColor: `${color}15`, color }}>
          <Icon size={12} />
        </div>
        <span className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">{label}</span>
      </div>
      <div className="text-lg font-bold text-gray-900 tabular-nums">{value}</div>
    </div>
  );
}

function formatDuration(seconds) {
  const s = Math.max(0, Number(seconds) || 0);
  if (s < 60) return `${s.toFixed(1)}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${Math.round(s % 60)}s`;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  return `${h}h ${m}m`;
}

export default AgentsPage;
