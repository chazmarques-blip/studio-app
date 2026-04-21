import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  X, Eye, Shield, Loader2, AlertTriangle, AlertCircle, Info,
  RefreshCw, Film, BookOpen, Award, ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SEV_META = {
  high:     { color: '#DC2626', bg: 'bg-red-50 dark:bg-red-500/10',       border: 'border-red-200 dark:border-red-500/30',       Icon: AlertTriangle, label: 'Crítico' },
  critical: { color: '#DC2626', bg: 'bg-red-50 dark:bg-red-500/10',       border: 'border-red-200 dark:border-red-500/30',       Icon: AlertTriangle, label: 'Crítico' },
  medium:   { color: '#F59E0B', bg: 'bg-amber-50 dark:bg-amber-500/10',   border: 'border-amber-200 dark:border-amber-500/30',   Icon: AlertCircle,  label: 'Médio' },
  low:      { color: '#3B82F6', bg: 'bg-blue-50 dark:bg-blue-500/10',     border: 'border-blue-200 dark:border-blue-500/30',     Icon: Info,        label: 'Menor' },
};

const TYPE_LABELS = {
  character_appearance: 'Aparência de Personagem',
  character_integrity: 'Integridade de Personagem',
  location: 'Locação',
  world_consistency: 'Consistência do Mundo',
  voice_continuity: 'Continuidade Vocal',
  timeline: 'Timeline',
  plot: 'Plot',
  color_story: 'Paleta de Cores',
  object_canon: 'Cânone de Objetos',
  scale: 'Escala',
  style_drift: 'Drift de Estilo',
};

function scoreColor(s) {
  if (s >= 85) return '#10B981';
  if (s >= 60) return '#F59E0B';
  return '#DC2626';
}

export function ContinuityAuditModal({ open, onClose, projectId, mode = 'video' }) {
  // mode: 'video' → Thelma Schoonmaker  |  'book' → Glen Keane
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [running, setRunning] = useState(false);

  const cfg = mode === 'book'
    ? {
        title: 'Auditoria Visual — Glen Keane',
        subtitle: 'Continuidade visual entre spreads',
        Icon: BookOpen,
        accent: '#10B981',
        postUrl: `${API}/studio/book/projects/${projectId}/visual-continuity-audit`,
        getUrl:  `${API}/studio/book/projects/${projectId}/visual-continuity-report`,
        issueBuckets: ['critical_issues', 'medium_issues', 'minor_issues'],
      }
    : {
        title: 'Auditoria de Continuidade — Thelma Schoonmaker',
        subtitle: 'Análise editorial do projeto de vídeo',
        Icon: Film,
        accent: '#8B5CF6',
        postUrl: `${API}/studio/projects/${projectId}/continuity-audit`,
        getUrl:  `${API}/studio/projects/${projectId}/continuity-report`,
        issueBuckets: null, // flat 'issues' array
      };

  const Icon = cfg.Icon;

  const loadExisting = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(cfg.getUrl);
      if (data.report) setReport(data.report);
    } catch (e) { /* no report yet — fine */ }
    setLoading(false);
  };

  useEffect(() => {
    if (open && projectId) loadExisting();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, projectId]);

  const runAudit = async () => {
    setRunning(true);
    try {
      const { data } = await axios.post(cfg.postUrl);
      setReport(data.report);
      if (data.report?.error) {
        toast.warning('Auditoria retornou erro — verifique o relatório');
      } else {
        toast.success('Auditoria concluída');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao executar auditoria');
    } finally {
      setRunning(false);
    }
  };

  if (!open) return null;

  // Normalize issues into a flat list
  let flatIssues = [];
  if (report) {
    if (cfg.issueBuckets) {
      cfg.issueBuckets.forEach(bk => {
        const sev = bk.startsWith('crit') ? 'high' : bk.startsWith('med') ? 'medium' : 'low';
        (report[bk] || []).forEach(it => flatIssues.push({ ...it, severity: it.severity || sev }));
      });
    } else {
      flatIssues = report.issues || [];
    }
  }

  // Group by severity for display
  const groups = { high: [], medium: [], low: [] };
  flatIssues.forEach(it => {
    const key = (it.severity || 'medium').toLowerCase();
    if (key === 'critical' || key === 'high') groups.high.push(it);
    else if (key === 'low' || key === 'minor') groups.low.push(it);
    else groups.medium.push(it);
  });

  return (
    <div
      className="fixed inset-y-0 right-0 left-0 md:left-60 top-12 z-[100] bg-black/60 backdrop-blur-sm flex items-start justify-center p-6 overflow-y-auto"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        data-testid="continuity-audit-modal"
        className="w-full max-w-3xl rounded-2xl border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] shadow-2xl my-6"
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-[#2A2442] flex items-center gap-3">
          <div
            className="h-10 w-10 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: `linear-gradient(135deg, ${cfg.accent}33, ${cfg.accent}11)` }}
          >
            <Icon size={18} style={{ color: cfg.accent }} strokeWidth={1.75} />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-bold text-gray-900 dark:text-white truncate inline-flex items-center gap-1.5">
              <Award size={13} style={{ color: cfg.accent }} />
              {cfg.title}
            </h2>
            <p className="text-[11px] text-gray-500 dark:text-[#A3A3B2]">{cfg.subtitle}</p>
          </div>
          <button
            onClick={onClose}
            data-testid="continuity-audit-close"
            className="p-2 rounded-lg text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-white/5 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        {loading ? (
          <div className="p-10 text-center">
            <Loader2 className="animate-spin mx-auto text-gray-400" size={20} />
            <p className="text-sm text-gray-500 dark:text-[#A3A3B2] mt-2">Carregando...</p>
          </div>
        ) : !report ? (
          <div className="p-10 text-center">
            <Shield size={40} className="mx-auto text-gray-300 dark:text-[#2A2442] mb-3" />
            <p className="text-sm text-gray-900 dark:text-white font-semibold">Nenhuma auditoria realizada ainda</p>
            <p className="text-xs text-gray-500 dark:text-[#A3A3B2] mt-1 mb-4">
              Clique abaixo para que {mode === 'book' ? 'Glen Keane' : 'Thelma Schoonmaker'} analise o projeto.
            </p>
            <button
              onClick={runAudit}
              disabled={running}
              data-testid="continuity-audit-run"
              className="h-10 px-5 rounded-lg bg-gradient-to-r from-violet-600 to-orange-500 text-white text-[13px] font-semibold inline-flex items-center gap-2 hover:brightness-110 transition disabled:opacity-50"
            >
              {running ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
              {running ? 'Auditando... (~15-30s)' : 'Executar Auditoria'}
            </button>
          </div>
        ) : (
          <div className="max-h-[70vh] overflow-y-auto">
            {/* Score banner */}
            <div className="px-6 py-5 border-b border-gray-200 dark:border-[#2A2442] flex items-center gap-4">
              <div className="shrink-0">
                <div
                  className="h-20 w-20 rounded-full flex flex-col items-center justify-center"
                  style={{
                    background: `conic-gradient(${scoreColor(report.score || 0)} ${(report.score || 0) * 3.6}deg, #e5e7eb 0deg)`,
                  }}
                >
                  <div className="h-16 w-16 rounded-full bg-white dark:bg-[#110A1F] flex flex-col items-center justify-center">
                    <span className="text-xl font-bold" style={{ color: scoreColor(report.score || 0) }}>
                      {report.score || 0}
                    </span>
                    <span className="text-[9px] font-mono uppercase text-gray-500 dark:text-[#A3A3B2]">score</span>
                  </div>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[13px] text-gray-900 dark:text-white leading-snug">
                  {report.summary || 'Auditoria concluída.'}
                </p>
                <p className="text-[10px] text-gray-500 dark:text-[#A3A3B2] mt-1">
                  {report.audited_at?.replace('T', ' ').replace('Z', '')} · {report.audited_by || 'agent'}
                </p>
              </div>
              <button
                onClick={runAudit}
                disabled={running}
                data-testid="continuity-audit-rerun"
                className="shrink-0 h-8 px-3 rounded-lg border border-gray-300 dark:border-[#2A2442] text-[11px] font-semibold text-gray-700 dark:text-[#A3A3B2] hover:border-violet-400 hover:text-violet-600 transition inline-flex items-center gap-1 disabled:opacity-50"
              >
                {running ? <Loader2 size={11} className="animate-spin" /> : <RefreshCw size={11} />}
                Re-auditar
              </button>
            </div>

            {/* Issues list */}
            {flatIssues.length === 0 ? (
              <div className="p-10 text-center">
                <Shield size={40} className="mx-auto text-emerald-500 mb-3" />
                <p className="text-sm text-gray-900 dark:text-white font-semibold">Nenhum problema detectado</p>
                <p className="text-xs text-gray-500 dark:text-[#A3A3B2] mt-1">
                  Projeto com alta integridade de continuidade.
                </p>
              </div>
            ) : (
              <div className="px-6 py-5 space-y-5">
                {['high', 'medium', 'low'].map((sev) => {
                  const list = groups[sev];
                  if (list.length === 0) return null;
                  const meta = SEV_META[sev];
                  const SevIcon = meta.Icon;
                  return (
                    <section key={sev}>
                      <header className="flex items-center gap-2 mb-2">
                        <SevIcon size={13} style={{ color: meta.color }} />
                        <h3 className="text-[11px] font-bold uppercase tracking-wider" style={{ color: meta.color }}>
                          {meta.label} ({list.length})
                        </h3>
                      </header>
                      <div className="space-y-2">
                        {list.map((it, i) => (
                          <div
                            key={i}
                            className={`rounded-lg border ${meta.border} ${meta.bg} p-3`}
                          >
                            <div className="flex items-start gap-2">
                              <span
                                className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded shrink-0"
                                style={{ color: meta.color, background: `${meta.color}22` }}
                              >
                                {TYPE_LABELS[it.type] || it.type}
                              </span>
                              {(it.scene_ids || it.spread_ids) && (
                                <span className="text-[10px] text-gray-600 dark:text-[#A3A3B2] shrink-0">
                                  {mode === 'book' ? 'spreads' : 'cenas'}:{' '}
                                  <b>{(it.scene_ids || it.spread_ids).join(', ')}</b>
                                </span>
                              )}
                            </div>
                            <p className="text-[12px] text-gray-900 dark:text-white mt-1.5">
                              {it.description}
                            </p>
                            {it.suggestion && (
                              <p className="text-[11px] text-gray-700 dark:text-[#A3A3B2] mt-1.5 flex items-start gap-1">
                                <ChevronRight size={11} className="mt-0.5 shrink-0" style={{ color: meta.color }} />
                                <span><b>Sugestão:</b> {it.suggestion || it.suggested_fix}</span>
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </section>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ContinuityAuditModal;
