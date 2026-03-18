import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Loader2, Check, ChevronDown, ChevronUp, RotateCcw, AlertTriangle, Crown, Lock, Play, RefreshCw, Maximize2, ArrowRight, X, Film, Eye, Download, Image } from 'lucide-react';
import { toast } from 'sonner';
import { STEP_META, STEP_ORDER, cleanDisplayText } from './constants';
import { ProgressTimer } from './ProgressTimer';
import { ImageLightbox } from './ImageLightbox';

function StepCard({ step, data, isActive, pipelineStatus, onApprove, expanded, onToggle, pipelineId, onRefresh }) {
  const { t } = useTranslation();
  const meta = STEP_META[step];
  const Icon = meta.icon;
  const status = data?.status || 'pending';
  const isGeneratingImages = status === 'generating_images';
  const isGeneratingVideo = status === 'generating_video';
  const isGenerating = isGeneratingImages || isGeneratingVideo;
  const needsApproval = pipelineStatus === 'waiting_approval' && (status === 'completed') &&
    ((step === 'ana_review_copy' && !data?.user_selection) ||
     (step === 'rafael_review_design' && !data?.user_selections));
  const isFailed = status === 'failed';
  const requiresUpgrade = status === 'requires_upgrade';
  const hasImages = data?.image_urls && data.image_urls.some(u => u);
  const hasVideo = !!data?.video_url;
  const revisionRound = data?.revision_round || 0;
  const revisionFeedback = data?.revision_feedback;
  const reviewerDecision = data?.decision;
  const reviewerRevisionCount = data?.revision_count || 0;

  return (
    <div data-testid={`step-card-${step}`} className={`rounded-xl border transition-all duration-300 ${
      isActive || isGenerating ? 'border-[#C9A84C]/50 bg-[#0D0D0D] shadow-[0_0_20px_rgba(201,168,76,0.1)]' :
      needsApproval ? 'border-amber-500/40 bg-[#0D0D0D] shadow-[0_0_15px_rgba(245,158,11,0.08)]' :
      isFailed ? 'border-red-500/30 bg-[#0D0D0D]' :
      requiresUpgrade ? 'border-[#C9A84C]/40 bg-[#0D0D0D]' :
      status === 'completed' ? 'border-green-500/20 bg-[#0D0D0D]' :
      'border-[#1A1A1A] bg-[#0A0A0A]'
    }`}>
      <button onClick={onToggle} className="w-full px-3 py-2.5 flex items-center gap-2.5">
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg shrink-0 transition-all ${isActive ? 'animate-pulse' : ''}`} style={{ backgroundColor: `${meta.color}15` }}>
          {status === 'running' || isGenerating ? (
            <div className="relative">
              <Loader2 size={16} className="animate-spin" style={{ color: meta.color }} />
              <div className="absolute inset-0 rounded-full animate-ping opacity-20" style={{ backgroundColor: meta.color }} />
            </div>
          ) : status === 'completed' ? (
            <Check size={16} className="text-green-400" />
          ) : isFailed ? (
            <AlertTriangle size={16} className="text-red-400" />
          ) : requiresUpgrade ? (
            <Lock size={16} className="text-[#C9A84C]" />
          ) : (
            <Icon size={16} style={{ color: `${meta.color}55` }} />
          )}
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-xs font-semibold text-white">{meta.agent} <span className="text-[#555] font-normal">- {meta.role}</span></p>
          <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
            {status === 'running' && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><span className="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse" />{revisionRound > 0 ? `${t('studio.revising')} (${revisionRound}/1)` : t('studio.processing')}</span>}
            {isGeneratingImages && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400"><Loader2 size={8} className="animate-spin" />{t('studio.generating_images') || 'Generating images...'}</span>}
            {isGeneratingVideo && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400"><Film size={8} className="animate-spin" />{t('studio.generating_video') || 'Generating commercial video...'}</span>}
            {status === 'completed' && !needsApproval && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">{t('studio.status_completed') || 'Completed'}</span>}
            {needsApproval && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 animate-pulse"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" />{t('studio.status_waiting') || 'Waiting Approval'}</span>}
            {status === 'pending' && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#222] text-[#555]">{t('studio.pending')}</span>}
            {isFailed && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">{t('studio.status_failed') || 'Failed'}</span>}
            {requiresUpgrade && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><Crown size={8} /> Upgrade Necessario</span>}
            {reviewerRevisionCount > 0 && (step === 'ana_review_copy' || step === 'rafael_review_design') && (
              <span className="inline-flex items-center gap-1 text-[8px] font-semibold px-1.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400">
                <RotateCcw size={7} />{reviewerRevisionCount} {t('studio.revision')}
              </span>
            )}
          </div>
        </div>
        {data?.elapsed_ms && <span className="text-[8px] text-[#444] shrink-0 bg-[#111] px-1.5 py-0.5 rounded">{(data.elapsed_ms / 1000).toFixed(1)}s</span>}
        {(data?.output || isFailed || requiresUpgrade) && (expanded ? <ChevronUp size={14} className="text-[#444]" /> : <ChevronDown size={14} className="text-[#444]" />)}
      </button>

      {/* Progress Timer for running steps */}
      {(status === 'running' || isGenerating) && data?.started_at && (
        <ProgressTimer startedAt={data.started_at} estimatedSec={isGeneratingVideo ? 300 : isGeneratingImages ? 90 : meta.estimatedSec} color={meta.color} />
      )}

      {/* Revision feedback banner */}
      {revisionFeedback && status === 'running' && (
        <div className="mx-3 mb-2 px-3 py-2 rounded-lg bg-purple-500/5 border border-purple-500/20">
          <p className="text-[8px] text-purple-400 uppercase tracking-wider font-semibold mb-0.5">{t('studio.reviewer_feedback')}</p>
          <p className="text-[9px] text-purple-300/80 line-clamp-3">{revisionFeedback}</p>
        </div>
      )}

      {expanded && (data?.output || isFailed || requiresUpgrade) && (
        <StepContent step={step} data={data} hasImages={hasImages} hasVideo={hasVideo} isFailed={isFailed}
          needsApproval={needsApproval} requiresUpgrade={requiresUpgrade}
          onApprove={onApprove} pipelineId={pipelineId} onRefresh={onRefresh} />
      )}
    </div>
  );
}

function StepContent({ step, data, hasImages, hasVideo, isFailed, needsApproval, requiresUpgrade, onApprove, pipelineId, onRefresh }) {
  const { t } = useTranslation();
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const [showStepVideoLightbox, setShowStepVideoLightbox] = useState(false);
  const images = (data?.image_urls || []).filter(u => u);

  return (
    <div className="px-3 pb-3 border-t border-[#151515]">
      {data?.output && (
        <div className="mt-2 rounded-lg bg-[#111] p-3 max-h-[300px] overflow-y-auto">
          <pre className="text-[10px] text-[#aaa] whitespace-pre-wrap leading-relaxed font-sans">{data.output}</pre>
        </div>
      )}
      {hasVideo && data.video_url && (
        <div className="mt-2">
          <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5 flex items-center gap-1"><Film size={10} className="text-red-400" /> {t('studio.video_commercial')}</p>
          <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black relative group cursor-pointer" onClick={() => setShowStepVideoLightbox(true)}>
            <video
              data-testid="pipeline-video-player"
              src={data.video_url}
              controls
              playsInline
              className="w-full max-h-[400px]"
              poster=""
              onClick={e => e.stopPropagation()}
            />
            <button data-testid="step-video-expand-btn" onClick={(e) => { e.stopPropagation(); setShowStepVideoLightbox(true); }}
              className="absolute top-2 right-2 h-8 w-8 rounded-lg bg-black/60 border border-white/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/80 z-10">
              <Maximize2 size={14} className="text-white" />
            </button>
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">{data.video_duration || 12}s</span>
            <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded capitalize">{data.video_format || 'vertical'}</span>
            <button onClick={() => setShowStepVideoLightbox(true)} data-testid="step-video-expand-text"
              className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5">
              <Maximize2 size={9} /> {t('studio.expand')}
            </button>
            <a href={data.video_url} target="_blank" rel="noopener noreferrer"
              className="ml-auto flex items-center gap-1 text-[9px] text-[#C9A84C] hover:underline">
              <Download size={10} /> {t('studio.download_video')}
            </a>
          </div>
          {showStepVideoLightbox && (
            <div data-testid="step-video-lightbox" className="fixed inset-0 z-[70] bg-black/95 flex items-center justify-center p-4" onClick={() => setShowStepVideoLightbox(false)}>
              <div className="relative w-full max-w-4xl" onClick={e => e.stopPropagation()}>
                <button onClick={() => setShowStepVideoLightbox(false)}
                  className="absolute -top-3 -right-3 z-10 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] transition">
                  <X size={16} className="text-white" />
                </button>
                <div className="rounded-xl overflow-hidden border border-[#333] bg-black shadow-2xl">
                  <video src={data.video_url} controls playsInline autoPlay className="w-full" style={{ maxHeight: '80vh' }} />
                </div>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-[9px] text-[#555] bg-[#111] px-2 py-1 rounded">Sora 2</span>
                  <a href={data.video_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1A1A1A] border border-[#333] text-[11px] text-white hover:bg-[#222] transition">
                    <Download size={12} /> {t('studio.download')} Video
                  </a>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      {hasImages && (
        <div className="mt-2">
          <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">{t('studio.images_generated')}</p>
          <div className="grid grid-cols-3 gap-2">
            {data.image_urls.map((url, i) => url && (
              <button key={i} onClick={() => setLightboxIndex(i)}
                className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] group relative text-left hover:border-[#C9A84C]/30 transition">
                <img src={resolveImageUrl(url)} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <Maximize2 size={18} className="text-white" />
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1">
                  <span className="text-[8px] text-white font-semibold">Design {i + 1}</span>
                </div>
              </button>
            ))}
          </div>
          {/* Platform variant badges */}
          {data.platform_variants && Object.keys(data.platform_variants).length > 0 && (
            <div className="mt-2 flex items-center gap-1.5 flex-wrap">
              <span className="text-[8px] text-[#555]">{t('studio.formats')}:</span>
              {Object.keys(data.platform_variants).map(p => {
                const AR_LABELS = { tiktok: '9:16', google_ads: '16:9', instagram: '1:1', facebook: '1:1', whatsapp: '1:1', email: '16:9' };
                return (
                  <span key={p} className="text-[7px] px-1.5 py-0.5 rounded bg-[#1A1A1A] text-[#C9A84C] border border-[#C9A84C]/20 capitalize">
                    {p === 'google_ads' ? 'Google Ads' : p} {AR_LABELS[p] || ''}
                  </span>
                );
              })}
            </div>
          )}
          {lightboxIndex !== null && (
            <ImageLightbox images={images} initialIndex={lightboxIndex}
              onClose={() => setLightboxIndex(null)} pipelineId={pipelineId} onRegenerate={onRefresh} />
          )}
        </div>
      )}
      {isFailed && data?.error && (
        <div className="mt-2 rounded-lg bg-red-500/5 border border-red-500/20 p-3">
          <p className="text-[10px] text-red-400">{data.error}</p>
        </div>
      )}
      {needsApproval && step === 'ana_review_copy' && <CopyApproval data={data} onApprove={onApprove} />}
      {needsApproval && step === 'rafael_review_design' && <DesignApproval data={data} onApprove={onApprove} images={images} pipelineId={pipelineId} onRefresh={onRefresh} />}
      {needsApproval && step === 'rafael_review_video' && <VideoApproval data={data} onApprove={onApprove} pipelineId={pipelineId} />}
    </div>
  );
}


export { StepCard, StepContent };
