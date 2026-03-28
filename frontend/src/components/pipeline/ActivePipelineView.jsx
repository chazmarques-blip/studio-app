import React from 'react';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Check, X, AlertTriangle, Crown, Phone, Image, RefreshCw, Eye } from 'lucide-react';
import FinalPreview from '../FinalPreview';
import { STEP_ORDER, STEP_META, StepCard, CompletedSummary } from './index';
import { getErrorMsg } from '../../utils/getErrorMsg';

/**
 * ActivePipelineView — Displays the monitoring UI for a running/completed pipeline.
 * Extracted from PipelineView to reduce file size.
 */
export function ActivePipelineView({
  activePipeline, expandedSteps, showFinalPreview, campaignLang,
  archivePipeline, approveStep, approveAudio, toggleStep, pollPipeline,
  retryPipeline, setShowFinalPreview, navigate,
}) {
  const { t } = useTranslation();
  const steps = activePipeline.steps || {};
  const completedCount = STEP_ORDER.filter(s => steps[s]?.status === 'completed').length;
  const progressPct = Math.round((completedCount / STEP_ORDER.length) * 100);
  const allStepsComplete = completedCount === STEP_ORDER.length;
  const statusConfig = {
    running: { label: t('studio.status_running') || 'Running', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
    waiting_approval: { label: t('studio.status_waiting') || 'Waiting Approval', color: 'text-amber-400', bg: 'bg-amber-400' },
    waiting_audio_approval: { label: t('studio.audio_preapproval') || 'Audio Pre-Approval', color: 'text-purple-400', bg: 'bg-purple-400' },
    completed: { label: t('studio.status_completed') || 'Completed!', color: 'text-green-400', bg: 'bg-green-400' },
    failed: { label: t('studio.status_failed') || 'Failed', color: 'text-red-400', bg: 'bg-red-400' },
    pending: { label: t('studio.status_pending') || 'Starting...', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
  };
  const sc = statusConfig[activePipeline.status] || statusConfig.pending;

  if (showFinalPreview) {
    return (
      <FinalPreview
        pipeline={activePipeline}
        campaignLang={campaignLang}
        onClose={() => setShowFinalPreview(false)}
        onPublish={async (editedCopy) => {
          try {
            const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
            const axios = (await import('axios')).default;
            await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/publish`, { edited_copy: editedCopy || null });
            const { toast } = await import('sonner');
            toast.success(t('studio.published') || 'Campaign published successfully!');
            navigate('/marketing');
          } catch (e) {
            const { toast } = await import('sonner');
            toast.error(getErrorMsg(e, t('studio.err_publish')) || 'Error publishing campaign');
          }
        }}
      />
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Pipeline Header */}
      <div className="border-b border-[#111] px-3 py-2.5 flex items-center gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold text-white">{activePipeline.result?.campaign_name || 'Pipeline'}</p>
            <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${sc.color}`}
              style={{ backgroundColor: `${sc.bg.replace('bg-', '')}10` }}>
              {['running', 'pending'].includes(activePipeline.status) && <span className={`w-1.5 h-1.5 rounded-full ${sc.bg} animate-pulse`} />}
              {sc.label}
            </span>
          </div>
          <div className="flex items-center gap-1.5 mt-1">
            {(activePipeline.platforms || []).map(p => (
              <span key={p} className="text-[11px] text-[#999] bg-[#111] px-1.5 py-0.5 rounded capitalize">{p}</span>
            ))}
          </div>
        </div>
        <div className="text-right">
          <span className="text-[10px] font-bold text-white">{progressPct}%</span>
          <span className="text-[11px] text-[#999] ml-1">completo</span>
        </div>
        <button onClick={() => archivePipeline(activePipeline.id)} className="text-[#888] hover:text-red-400 p-1.5 rounded-lg hover:bg-[#111] transition" title={t('studio.archive') || 'Archive and create new'}>
          <X size={14} />
        </button>
      </div>

      {/* Briefing */}
      <div className="px-3 py-2 bg-[#080808] border-b border-[#111]">
        <p className="text-[11px] text-[#999] uppercase tracking-wider mb-0.5">Briefing</p>
        <p className="text-[10px] text-[#999] line-clamp-2">{activePipeline.briefing}</p>
        {activePipeline.result?.uploaded_assets?.length > 0 && (
          <div className="flex items-center gap-1.5 mt-1">
            <Image size={9} className="text-[#888]" />
            <span className="text-[11px] text-[#888]">{activePipeline.result.uploaded_assets.length} arquivo(s) anexado(s)</span>
          </div>
        )}
        {activePipeline.result?.contact_info && Object.values(activePipeline.result.contact_info).some(v => v) && (
          <div className="flex items-center gap-1.5 mt-0.5">
            <Phone size={9} className="text-[#888]" />
            <span className="text-[11px] text-[#888]">{t('studio.contact_included') || 'Contact data included'}</span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="px-3 py-2">
        <div className="flex items-center gap-0.5">
          {STEP_ORDER.map((s, i) => {
            const st = steps[s]?.status || 'pending';
            const isRun = st === 'running' || st === 'generating_images';
            return (
              <div key={s} className="flex items-center flex-1 gap-0.5">
                <div className="relative h-2 rounded-full flex-1 bg-[#1A1A1A] overflow-hidden">
                  <div className={`absolute inset-y-0 left-0 rounded-full transition-all duration-700 ${
                    st === 'completed' ? 'w-full bg-green-500' : isRun ? 'w-1/2 bg-[#C9A84C]' : st === 'failed' ? 'w-full bg-red-500' : 'w-0'
                  }`} />
                  {isRun && <div className="absolute inset-0 bg-[#C9A84C]/20 animate-pulse rounded-full" />}
                </div>
                {i < STEP_ORDER.length - 1 && <ArrowRight size={8} className="text-[#777] shrink-0" />}
              </div>
            );
          })}
        </div>
      </div>

      {/* Completed Summary */}
      {(activePipeline.status === 'completed' || allStepsComplete) && <CompletedSummary pipeline={activePipeline} />}

      {/* Steps */}
      <div className="flex-1 overflow-y-auto px-3 py-1 space-y-2">
        {STEP_ORDER.map(s => (
          <StepCard key={s} step={s} data={steps[s]}
            isActive={s === activePipeline.current_step && activePipeline.status === 'running'}
            pipelineStatus={activePipeline.status} onApprove={approveStep} onApproveAudio={approveAudio}
            expanded={!!expandedSteps[s]} onToggle={() => toggleStep(s)}
            pipelineId={activePipeline.id} onRefresh={() => pollPipeline(activePipeline.id)} />
        ))}
      </div>

      {/* Bottom actions */}
      {(activePipeline.status === 'completed' || allStepsComplete) && (
        <div className="px-3 py-3 border-t border-[#111] bg-green-500/5">
          <div className="flex items-center gap-2 mb-2">
            <Check size={18} className="text-green-400" />
            <p className="text-xs font-bold text-green-400 flex-1">Pipeline concluido!</p>
          </div>
          <div className="flex gap-2">
            <button onClick={() => archivePipeline(activePipeline.id)}
              className="flex-1 rounded-lg border border-[#1E1E1E] py-2.5 text-[11px] text-[#888] hover:text-white transition">
              Novo Pipeline
            </button>
            <button data-testid="open-final-preview" onClick={() => setShowFinalPreview(true)}
              className="flex-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(201,168,76,0.15)]">
              <Eye size={14} /> Ver Preview Final
            </button>
          </div>
        </div>
      )}
      {activePipeline.status === 'failed' && (
        <div className="px-3 py-3 border-t border-[#111] bg-red-500/5">
          <div className="flex items-center gap-2">
            <AlertTriangle size={18} className="text-red-400" />
            <p className="text-xs font-semibold text-red-400 flex-1">A step has failed. Try again.</p>
            <button onClick={retryPipeline}
              className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition flex items-center gap-1.5">
              <RefreshCw size={12} /> Retry
            </button>
          </div>
        </div>
      )}
      {activePipeline.status === 'requires_upgrade' && (
        <div className="px-3 py-3 border-t border-[#111] bg-[#C9A84C]/5">
          <div className="flex items-center gap-2">
            <Crown size={18} className="text-[#C9A84C]" />
            <div className="flex-1">
              <p className="text-xs font-bold text-[#C9A84C]">Upgrade to Enterprise</p>
              <p className="text-xs text-[#888]">Your campaign is ready! Upgrade to publish.</p>
            </div>
            <button onClick={() => navigate('/upgrade')}
              className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(201,168,76,0.2)]">
              <Crown size={12} /> Fazer Upgrade
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
