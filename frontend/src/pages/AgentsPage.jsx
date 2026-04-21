import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Bot, Video, BookOpen, Music, Save, X, Search,
  Sparkles, RotateCcw, History, Power, PowerOff, FileText,
  Edit3, ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ─── Category & phase metadata ─────────────────────────── */
const CATEGORIES = {
  video: { label: 'Vídeo', Icon: Video, color: 'violet', accent: '#8B5CF6' },
  book:  { label: 'Livro', Icon: BookOpen, color: 'emerald', accent: '#10B981' },
  audio: { label: 'Áudio', Icon: Music, color: 'orange', accent: '#F97316' },
};

const PHASE_LABELS = {
  research: 'Pesquisa',
  consensus: 'Consenso',
  production: 'Produção',
  validation: 'Validação',
  execution: 'Execução',
};

/* ─── Card ────────────────────────────────────────────────── */
function AgentCard({ agent, onEdit }) {
  const cat = CATEGORIES[agent.category] || CATEGORIES.video;
  const Icon = cat.Icon;
  const active = agent.active !== false;
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
          <h3 className="text-[13px] font-semibold text-gray-900 dark:text-white truncate leading-tight">
            {agent.name}
          </h3>
          <div className="flex items-center gap-1.5 mt-0.5">
            {agent.phase && (
              <span className="text-[10px] font-mono uppercase tracking-wide text-gray-500 dark:text-[#A3A3B2]">
                {PHASE_LABELS[agent.phase] || agent.phase}
              </span>
            )}
            {active ? (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded-full font-semibold"
                style={{ background: `${cat.accent}22`, color: cat.accent }}
                title="Prompt personalizado ativo — pipeline usa este prompt"
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

/* ─── Edit modal ──────────────────────────────────────────── */
function AgentEditor({ agent, onClose, onSaved }) {
  const [data, setData] = useState(null);
  const [saving, setSaving] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (!agent) return;
    (async () => {
      try {
        const { data: res } = await axios.get(`${API}/studio/agents/registry/${agent.id}`);
        setData({
          ...res.agent,
          active: res.agent.active !== false,
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

  const rollback = async (index) => {
    if (!window.confirm('Restaurar esta versão? O prompt atual será substituído.')) return;
    try {
      await axios.post(`${API}/studio/agents/registry/${agent.id}/rollback`, { index });
      toast.success('Versão restaurada');
      onSaved();
      onClose();
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
          <div
            className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `linear-gradient(135deg, ${cat.accent}33, ${cat.accent}11)` }}
          >
            <Icon size={18} style={{ color: cat.accent }} strokeWidth={1.75} />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-bold text-gray-900 dark:text-white truncate">
              {agent.name}
            </h2>
            <p className="text-[11px] text-gray-500 dark:text-[#A3A3B2]">
              {agent.id} · {cat.label} · {PHASE_LABELS[agent.phase] || agent.phase}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition"
          >
            <X size={18} />
          </button>
        </div>

        {!data ? (
          <div className="p-10 text-center text-sm text-gray-500">Carregando...</div>
        ) : (
          <div className="px-6 py-5 space-y-5 max-h-[70vh] overflow-y-auto">
            {/* Status banner */}
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
                  {data.active ? 'Prompt customizado ATIVO' : 'Usando prompt padrão do sistema'}
                </p>
                <p className="text-gray-600 dark:text-[#A3A3B2] mt-0.5">
                  {data.active
                    ? 'Toda execução da pipeline usará o prompt abaixo. Se algo quebrar, desative para voltar ao padrão.'
                    : 'Ative o toggle para que a pipeline use o prompt customizado abaixo.'}
                </p>
              </div>
              <button
                onClick={() => setData({ ...data, active: !data.active })}
                data-testid="agent-active-toggle"
                className={`shrink-0 inline-flex items-center gap-1 h-7 px-3 rounded-full text-[11px] font-semibold transition ${
                  data.active
                    ? 'bg-violet-600 text-white'
                    : 'bg-gray-200 dark:bg-[#2A2442] text-gray-600 dark:text-[#A3A3B2]'
                }`}
              >
                {data.active ? <Power size={11} /> : <PowerOff size={11} />}
                {data.active ? 'ATIVO' : 'DESATIVADO'}
              </button>
            </div>

            {/* Description */}
            <Field label="Descrição (interna)">
              <textarea
                value={data.description || ''}
                onChange={(e) => setData({ ...data, description: e.target.value })}
                rows={2}
                className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-2 text-[13px] text-gray-900 dark:text-white outline-none focus:border-violet-500 transition resize-y"
              />
            </Field>

            {/* System prompt */}
            <Field
              label="System Prompt"
              hint={
                data.active
                  ? 'Este é o prompt que alimenta o modelo. Placeholders como {lang_name} devem ser preservados.'
                  : 'Pré-visualização. Para alterar a pipeline, ative o toggle acima.'
              }
            >
              <textarea
                value={data.system_prompt || ''}
                onChange={(e) => setData({ ...data, system_prompt: e.target.value })}
                data-testid="agent-system-prompt"
                rows={14}
                className="w-full rounded-lg bg-gray-50 dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] px-3 py-2 text-[12px] font-mono text-gray-900 dark:text-white outline-none focus:border-violet-500 transition resize-y"
              />
            </Field>

            {/* Temperature + min_quality */}
            <div className="grid grid-cols-2 gap-4">
              <Field label={`Temperatura: ${data.temperature?.toFixed(2) ?? '0.70'}`} hint="0 = determinístico · 1 = criativo">
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.05}
                  value={data.temperature ?? 0.7}
                  onChange={(e) => setData({ ...data, temperature: parseFloat(e.target.value) })}
                  className="w-full accent-violet-600"
                />
              </Field>
              <Field label={`Min. Quality Score: ${data.min_quality_score ?? 80}`} hint="0–100">
                <input
                  type="range"
                  min={0}
                  max={100}
                  step={5}
                  value={data.min_quality_score ?? 80}
                  onChange={(e) => setData({ ...data, min_quality_score: parseInt(e.target.value) })}
                  className="w-full accent-violet-600"
                />
              </Field>
            </div>

            {/* Responsibilities */}
            {Array.isArray(data.responsibilities) && data.responsibilities.length > 0 && (
              <Field label="Responsabilidades">
                <ul className="space-y-1 text-[12px] text-gray-700 dark:text-[#A3A3B2] pl-4 list-disc">
                  {data.responsibilities.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </Field>
            )}

            {/* History */}
            {Array.isArray(data.edit_history) && data.edit_history.length > 0 && (
              <div>
                <button
                  onClick={() => setShowHistory((v) => !v)}
                  className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-violet-600 dark:text-violet-400 hover:underline"
                >
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
                          <button
                            onClick={() => rollback(realIdx)}
                            className="shrink-0 text-[10px] text-violet-600 dark:text-violet-400 hover:underline inline-flex items-center gap-0.5"
                          >
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
        )}

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-[#2A2442] flex items-center justify-end gap-2 bg-gray-50 dark:bg-[#0A0614] rounded-b-2xl">
          <button
            onClick={onClose}
            className="h-9 px-4 rounded-lg text-[12px] font-medium text-gray-700 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-white/5 transition"
          >
            Cancelar
          </button>
          <button
            onClick={save}
            disabled={saving || !data}
            data-testid="agent-save-btn"
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

/* ─── Main page ───────────────────────────────────────────── */
export function AgentsPage() {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState(null);

  const load = async () => {
    try {
      const { data } = await axios.get(`${API}/studio/agents/registry`);
      setAgents(data.agents || []);
    } catch (e) {
      toast.error('Erro ao carregar agentes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const counts = useMemo(() => {
    const c = { all: agents.length, video: 0, book: 0, audio: 0 };
    agents.forEach((a) => { c[a.category] = (c[a.category] || 0) + 1; });
    return c;
  }, [agents]);

  const filtered = useMemo(() => {
    return agents.filter((a) => {
      if (tab !== 'all' && a.category !== tab) return false;
      if (search && !((a.name || '').toLowerCase().includes(search.toLowerCase()) ||
                       (a.description || '').toLowerCase().includes(search.toLowerCase()))) return false;
      return true;
    });
  }, [agents, tab, search]);

  // Group by category when showing "all"
  const grouped = useMemo(() => {
    if (tab !== 'all') return null;
    const g = { video: [], book: [], audio: [] };
    filtered.forEach((a) => { (g[a.category] || g.video).push(a); });
    return g;
  }, [filtered, tab]);

  return (
    <div
      className="min-h-screen bg-[#FAFAFC] dark:bg-[#0A0614]"
      style={{ fontFamily: "'Outfit', system-ui" }}
    >
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
                placeholder="Buscar agente..."
                className="h-7 pl-7 pr-3 rounded-md bg-gray-100 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-[#6B647F] outline-none focus:border-violet-500 transition w-52"
              />
            </div>
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
                <span
                  className={`ml-0.5 font-mono text-[10px] px-1.5 py-0.5 rounded-full ${
                    active ? 'bg-white/25 text-white' : 'bg-gray-100 dark:bg-[#0A0614] text-gray-600 dark:text-[#A3A3B2]'
                  }`}
                >
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
              Cada agente aqui controla um prompt da pipeline. Ative o modo <span className="font-mono bg-violet-100 dark:bg-violet-500/20 px-1 rounded">CUSTOM</span> e edite o system prompt para afetar diretamente o resultado dos vídeos, livros ou áudios gerados. Quando desativado, o sistema usa o prompt padrão (fallback seguro).
            </div>
          </div>
        </div>
      </div>

      {/* Grid */}
      <div className="px-6 py-5 pb-20">
        <div className="max-w-7xl mx-auto">
          {loading ? (
            <div className="py-20 text-center text-sm text-gray-500 dark:text-[#A3A3B2]">Carregando...</div>
          ) : filtered.length === 0 ? (
            <div className="py-20 flex flex-col items-center text-center">
              <div className="h-14 w-14 rounded-xl bg-gray-100 dark:bg-[#1A1430] flex items-center justify-center mb-3">
                <Bot size={24} className="text-gray-400 dark:text-[#6B647F]" />
              </div>
              <p className="text-sm text-gray-700 dark:text-white font-semibold">Nenhum agente encontrado</p>
              <p className="text-xs text-gray-500 dark:text-[#A3A3B2] mt-1">Ajuste a busca ou mude de categoria</p>
            </div>
          ) : grouped ? (
            <div className="space-y-7">
              {['video', 'book', 'audio'].map((cat) => {
                const list = grouped[cat];
                if (!list || list.length === 0) return null;
                const meta = CATEGORIES[cat];
                const Icon = meta.Icon;
                return (
                  <section key={cat}>
                    <header className="flex items-center gap-2 mb-3">
                      <Icon size={13} style={{ color: meta.accent }} />
                      <h2 className="text-[11px] font-bold uppercase tracking-wider text-gray-700 dark:text-white">
                        Pipeline de {meta.label}
                      </h2>
                      <span className="text-[10px] font-mono text-gray-400 dark:text-[#6B647F]">
                        {list.length}
                      </span>
                    </header>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {list.map((a) => <AgentCard key={a.id} agent={a} onEdit={setEditing} />)}
                    </div>
                  </section>
                );
              })}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {filtered.map((a) => <AgentCard key={a.id} agent={a} onEdit={setEditing} />)}
            </div>
          )}
        </div>
      </div>

      {editing && (
        <AgentEditor agent={editing} onClose={() => setEditing(null)} onSaved={load} />
      )}
    </div>
  );
}

export default AgentsPage;
