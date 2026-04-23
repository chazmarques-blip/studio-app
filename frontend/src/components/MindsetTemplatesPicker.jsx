import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { X, Loader2, Sparkles, CheckCircle2, PowerOff } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * MindsetTemplatesPicker
 * Dropdown/modal to browse + apply "Dream Team" mindset templates.
 *
 * Props:
 *  - open: boolean
 *  - onClose: () => void
 *  - category: 'video' | 'book' | 'audio'
 *  - onApplied: () => void   (parent refetch hook)
 */
export default function MindsetTemplatesPicker({ open, onClose, category = 'video', onApplied }) {
  const [templates, setTemplates] = useState([]);
  const [activeByCategory, setActiveByCategory] = useState({});
  const [loading, setLoading] = useState(true);
  const [applying, setApplying] = useState(null);
  const [overwritePrompt, setOverwritePrompt] = useState(false);

  useEffect(() => {
    if (!open) return;
    (async () => {
      setLoading(true);
      try {
        const { data } = await axios.get(`${API}/studio/agents/mindset-templates`);
        setTemplates(data.templates || []);
        setActiveByCategory(data.active_by_category || {});
      } catch (e) {
        toast.error('Falha ao carregar templates');
      } finally {
        setLoading(false);
      }
    })();
  }, [open]);

  const activeId = activeByCategory?.[category];

  const applyTemplate = async (tpl) => {
    const confirm = window.confirm(
      `Aplicar template "${tpl.name}"?\n\n` +
        `Isso vai:\n` +
        `• Ativar a mentalidade global da categoria "${category}"\n` +
        `• Atualizar master reference + temperature de ${tpl.agents?.length || 0} agentes\n` +
        (overwritePrompt ? `• Sobrescrever system_prompt dos agentes (modo agressivo)\n` : '') +
        `\nO estado atual será salvo no edit_history (rollback disponível).`
    );
    if (!confirm) return;
    setApplying(tpl.id);
    try {
      const { data } = await axios.post(`${API}/studio/agents/mindset-templates/apply`, {
        template_id: tpl.id,
        category,
        apply_to_agents: true,
        overwrite_system_prompt: overwritePrompt,
      });
      toast.success(
        `✅ Template "${data.template_name}" aplicado! ${data.agents_updated?.length || 0} agentes atualizados.`
      );
      setActiveByCategory({ ...activeByCategory, [category]: tpl.id });
      onApplied?.();
    } catch (e) {
      toast.error(`Erro: ${e.response?.data?.detail || e.message}`);
    } finally {
      setApplying(null);
    }
  };

  const deactivate = async () => {
    if (!window.confirm('Desativar a mentalidade ativa? Os agentes mantém suas referências atuais.')) return;
    try {
      await axios.post(`${API}/studio/agents/mindset-templates/deactivate`, null, {
        params: { category },
      });
      toast.success('Mentalidade desativada');
      setActiveByCategory({ ...activeByCategory, [category]: null });
      onApplied?.();
    } catch (e) {
      toast.error(`Erro: ${e.response?.data?.detail || e.message}`);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      onClick={onClose}
      data-testid="mindset-templates-modal"
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <div>
              <h2 className="text-base font-bold text-gray-900">
                Dream Teams · Templates de Mentalidade
              </h2>
              <p className="text-xs text-gray-500">
                Categoria: <span className="font-semibold text-violet-600">{category}</span>
                {activeId && (
                  <>
                    {' · '}
                    <span className="text-emerald-600 font-semibold">Ativo: {activeId}</span>
                  </>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {activeId && (
              <button
                onClick={deactivate}
                data-testid="btn-deactivate-template"
                className="h-8 inline-flex items-center gap-1.5 px-3 rounded-md border border-amber-300 text-amber-700 hover:bg-amber-50 text-xs font-medium"
                title="Desativar a mentalidade ativa"
              >
                <PowerOff size={12} /> Desativar
              </button>
            )}
            <button
              onClick={onClose}
              data-testid="btn-close-templates"
              className="h-8 w-8 rounded-md hover:bg-gray-100 text-gray-500 flex items-center justify-center"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Aggressive mode toggle */}
        <div className="px-6 py-3 bg-amber-50 border-b border-amber-100 flex items-center gap-3">
          <label className="flex items-center gap-2 text-xs text-amber-900 cursor-pointer">
            <input
              type="checkbox"
              checked={overwritePrompt}
              onChange={(e) => setOverwritePrompt(e.target.checked)}
              data-testid="toggle-overwrite-prompt"
              className="accent-amber-600"
            />
            <span>
              <strong>Modo agressivo:</strong> sobrescrever também o <code>system_prompt</code> de cada agente
              (por padrão só master_reference + temperature são alterados)
            </span>
          </label>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 size={28} className="text-violet-500 animate-spin" />
            </div>
          ) : templates.length === 0 ? (
            <div className="text-center py-16 text-gray-500 text-sm">Nenhum template disponível.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((tpl) => {
                const isActive = activeId === tpl.id;
                const isApplying = applying === tpl.id;
                return (
                  <div
                    key={tpl.id}
                    data-testid={`template-card-${tpl.id}`}
                    className={`rounded-xl border-2 p-4 transition cursor-pointer hover:shadow-lg ${
                      isActive
                        ? 'border-emerald-400 bg-emerald-50/50 ring-2 ring-emerald-200'
                        : 'border-gray-200 bg-white hover:border-violet-300'
                    }`}
                    onClick={() => !isApplying && applyTemplate(tpl)}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="text-3xl leading-none">{tpl.emoji || '🎬'}</div>
                      {isActive && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                          <CheckCircle2 size={10} /> ATIVO
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-gray-900 mb-1">{tpl.name}</h3>
                    <p className="text-[11px] text-gray-600 leading-relaxed mb-3 line-clamp-3">
                      {tpl.description}
                    </p>

                    <div className="space-y-1.5 mb-3">
                      {(tpl.agents || []).slice(0, 4).map((a) => (
                        <div
                          key={a.agent_id}
                          className="flex items-center justify-between text-[10px]"
                        >
                          <span className="text-gray-500 truncate">
                            {a.agent_id.replace('_agent', '').replace('_', ' ')}
                          </span>
                          <span className="font-semibold text-violet-700 truncate ml-2">
                            {a.master_reference}
                          </span>
                        </div>
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-[10px] pt-2 border-t border-gray-100">
                      <span className="text-gray-500">
                        Qualidade:{' '}
                        <strong className="text-gray-800 uppercase">{tpl.production_quality}</strong>
                      </span>
                      <span className="text-gray-500">
                        Estilo:{' '}
                        <strong className="text-gray-800">{tpl.visual_style}</strong>
                      </span>
                    </div>

                    <button
                      disabled={isApplying}
                      className={`mt-3 w-full h-8 rounded-md text-xs font-semibold inline-flex items-center justify-center gap-1.5 transition ${
                        isActive
                          ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                          : 'bg-violet-500 text-white hover:bg-violet-600'
                      }`}
                      data-testid={`btn-apply-${tpl.id}`}
                    >
                      {isApplying ? (
                        <>
                          <Loader2 size={12} className="animate-spin" /> Aplicando...
                        </>
                      ) : isActive ? (
                        <>
                          <CheckCircle2 size={12} /> Reaplicar
                        </>
                      ) : (
                        <>
                          <Sparkles size={12} /> Aplicar Template
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
