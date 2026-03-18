import React from 'react';
import { useTranslation } from 'react-i18next';
import { Loader2, Trash2, Clock, Film, Image, Play, Check, AlertTriangle, RotateCcw, ArrowRight, Zap } from 'lucide-react';
import { STEP_META, STEP_ORDER } from './constants';

function HistoryCard({ pipeline, onSelect, onDelete }) {
  const { t } = useTranslation();
  const steps = pipeline.steps || {};
  const completedCount = STEP_ORDER.filter(s => steps[s]?.status === 'completed').length;
  const hasImages = steps.lucas_design?.image_urls?.some(u => u);
  const statusColors = { completed: 'text-green-400', failed: 'text-red-400', running: 'text-[#C9A84C]', waiting_approval: 'text-amber-400' };
  const statusLabels = { completed: t('studio.status_completed') || 'Completed', failed: t('studio.status_failed') || 'Failed', running: t('studio.status_running') || 'Running', waiting_approval: t('studio.status_waiting') || 'Waiting', requires_upgrade: 'Upgrade' };
  const createdAt = pipeline.created_at ? new Date(pipeline.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div data-testid={`history-card-${pipeline.id}`}
      className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 hover:border-[#2A2A2A] transition group cursor-pointer"
      onClick={() => onSelect(pipeline)}>
      <div className="flex items-start gap-2.5">
        {hasImages && steps.lucas_design.image_urls[0] ? (
          <img src={resolveImageUrl(steps.lucas_design.image_urls[0])}
            alt="" className="w-10 h-10 rounded-lg object-cover border border-[#1E1E1E] shrink-0" />
        ) : (
          <div className="w-10 h-10 rounded-lg bg-[#111] border border-[#1E1E1E] flex items-center justify-center shrink-0">
            <Zap size={14} className="text-[#333]" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-[11px] text-white font-medium truncate">{pipeline.briefing}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-[9px] font-semibold ${statusColors[pipeline.status] || 'text-[#555]'}`}>
              {statusLabels[pipeline.status] || pipeline.status}
            </span>
            <span className="text-[8px] text-[#444]">{completedCount}/{STEP_ORDER.length} etapas</span>
            <span className="text-[8px] text-[#333]">{createdAt}</span>
          </div>
          <div className="flex gap-0.5 mt-1">
            {(pipeline.platforms || []).map(p => (
              <span key={p} className="text-[7px] text-[#444] bg-[#111] px-1 py-0.5 rounded capitalize">{p}</span>
            ))}
          </div>
        </div>
        <button onClick={e => { e.stopPropagation(); onDelete(pipeline.id); }}
          className="text-[#222] hover:text-red-400 opacity-0 group-hover:opacity-100 transition p-1">
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  );
}

/* ── Asset Upload ── */

export { HistoryCard };
