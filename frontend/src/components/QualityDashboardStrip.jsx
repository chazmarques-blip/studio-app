import { useState, useEffect } from 'react';
import axios from 'axios';
import { Film, BookOpen, Zap, DollarSign, AlertTriangle, RefreshCw } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * QualityDashboardStrip — tenant-wide KPIs at the top of StudioPage.
 * Polls /api/studio/quality-dashboard every 30s.
 * Note: Uses axios with default headers (Authorization set by AuthContext)
 */
export function QualityDashboardStrip() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    let retryTimeout = null;
    let pollInterval = null;
    
    const fetchData = async (retryCount = 0) => {
      // Check if auth header is set (AuthContext sets it)
      const hasAuth = !!axios.defaults.headers.common['Authorization'];
      
      if (!hasAuth && retryCount < 10) {
        retryTimeout = setTimeout(() => fetchData(retryCount + 1), 300);
        return;
      }
      
      if (!hasAuth) {
        if (isMounted) setLoading(false);
        return;
      }
      
      try {
        const response = await axios.get(`${API}/studio/quality-dashboard`);
        if (isMounted) {
          setData(response.data);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) setLoading(false);
      }
    };
    
    // Initial fetch with delay to allow AuthContext to set headers
    retryTimeout = setTimeout(() => fetchData(0), 500);
    
    // Poll every 30 seconds
    pollInterval = setInterval(() => fetchData(0), 30000);
    
    return () => {
      isMounted = false;
      if (retryTimeout) clearTimeout(retryTimeout);
      if (pollInterval) clearInterval(pollInterval);
    };
  }, []);

  if (loading || !data) return null;

  const hasHotIssues = (data.hot_issues || []).length > 0;
  const v = data.videos || {};
  const af = data.auto_fix || {};
  const cost = data.cost || {};

  // Hide if there's nothing meaningful
  if (v.total === 0) return null;

  const avgScoreColor =
    v.avg_continuity_score >= 85 ? 'text-emerald-600' :
    v.avg_continuity_score >= 70 ? 'text-amber-600' :
    v.avg_continuity_score > 0 ? 'text-red-600' : 'text-gray-400';

  return (
    <div className="mb-4" data-testid="quality-dashboard-strip">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <StatCard
          Icon={Film}
          label="Vídeos"
          value={`${v.complete}/${v.total}`}
          sub="completos"
          color="#8B5CF6"
          testId="kpi-videos"
        />
        <StatCard
          Icon={Zap}
          label="Continuidade média"
          value={v.avg_continuity_score > 0 ? v.avg_continuity_score.toFixed(1) : '—'}
          sub={v.audited > 0 ? `${v.audited} auditados (🟢${v.green} 🟡${v.yellow} 🔴${v.red})` : 'sem auditoria'}
          color={v.avg_continuity_score >= 85 ? '#10B981' : v.avg_continuity_score >= 70 ? '#F59E0B' : '#EF4444'}
          valueClass={avgScoreColor}
          testId="kpi-continuity"
        />
        <StatCard
          Icon={RefreshCw}
          label="Auto-Fix"
          value={af.runs || 0}
          sub={af.scenes_regenerated ? `${af.scenes_regenerated} cenas regenadas` : 'nenhum executado'}
          color="#EC4899"
          testId="kpi-autofix"
        />
        <StatCard
          Icon={DollarSign}
          label="Custo estimado"
          value={`$${(cost.total_usd || 0).toFixed(4)}`}
          sub={`${cost.total_activations || 0} ativações LLM`}
          color="#F97316"
          testId="kpi-cost"
        />
      </div>

      {/* Hot issues banner */}
      {hasHotIssues && (
        <div className="mt-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 flex items-start gap-2" data-testid="hot-issues-banner">
          <AlertTriangle size={14} className="text-red-600 mt-0.5 shrink-0" />
          <div className="flex-1">
            <div className="text-[11px] font-bold text-red-700 mb-0.5">
              {data.hot_issues.length} projeto{data.hot_issues.length > 1 ? 's' : ''} com score de continuidade abaixo de 70
            </div>
            <div className="flex flex-wrap gap-1.5">
              {data.hot_issues.slice(0, 5).map((p) => (
                <span
                  key={p.id}
                  className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-white border border-red-200 text-[10px] text-red-700"
                  title={`${p.issues_count} issues · Auto-Fix: ${p.auto_fix_status || 'não executado'}`}
                >
                  🔴 {(p.name || p.id).slice(0, 30)}{(p.name || '').length > 30 ? '…' : ''}
                  <span className="font-bold">{p.score}</span>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="mt-1 text-[9px] text-gray-400 text-right">
        Atualiza a cada 30s · Thelma Schoonmaker (vídeo) · Glen Keane (livro)
      </div>
    </div>
  );
}

function StatCard({ Icon, label, value, sub, color, valueClass = '', testId }) {
  return (
    <div
      data-testid={testId}
      className="rounded-lg border border-gray-200 bg-white p-2.5 hover:border-gray-300 transition"
    >
      <div className="flex items-center gap-1.5 mb-0.5">
        <div
          className="h-5 w-5 rounded flex items-center justify-center"
          style={{ backgroundColor: `${color}18`, color }}
        >
          <Icon size={10} />
        </div>
        <span className="text-[9px] uppercase tracking-wider text-gray-500 font-semibold">{label}</span>
      </div>
      <div className={`text-base font-bold tabular-nums leading-tight ${valueClass || 'text-gray-900'}`}>{value}</div>
      <div className="text-[9px] text-gray-500 mt-0.5 truncate">{sub}</div>
    </div>
  );
}

export default QualityDashboardStrip;
