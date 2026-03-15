import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PenTool, Palette, CheckCircle, CalendarClock, Loader2, Check, ChevronDown, ChevronUp, ArrowRight, Zap, RotateCcw, Trash2, RefreshCw, AlertTriangle, Crown, Lock, Upload, X, Image, Phone, Globe, Mail, MapPin, FileText, Download, Eye, Clock, Maximize2, MessageSquare, Send, Award, Film, Play } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import FinalPreview from './FinalPreview';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── Text Cleaner ── */
function cleanDisplayText(raw) {
  if (!raw) return '';
  let text = raw;
  const varMatch = text.match(/===VARIA(?:TION|CAO|ÇÃO)\s*\d+===([\s\S]*?)(?=={3}|$)/i);
  if (varMatch) text = varMatch[1];
  text = text.replace(/\*\*\*([^*]+)\*\*\*/g, '$1');
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/#{1,3}\s+/g, '');
  const labels = 'Title|Titulo|Título|Copy|Texto|Headline|Body|CTA|Caption|Legenda|Subject|Assunto|Chamada|Subtítulo|Subtitle|Hashtags|Visual|Conceito|Concept|Plataforma|Platform|Dimensões|Dimensions|Adaptações|Call.to.Action';
  text = text.replace(new RegExp(`^\\s*(?:${labels})\\s*[:：]\\s*`, 'gim'), '');
  text = text.replace(new RegExp(`^\\s*(?:${labels})\\s*$`, 'gim'), '');
  text = text.replace(/={3,}.*?={3,}/g, '');
  text = text.replace(/^-{3,}\s*$/gm, '');
  text = text.replace(/\n{3,}/g, '\n\n').trim();
  return text;
}

const STEP_META = {
  sofia_copy: { agent: 'Sofia', role: 'Copywriter', icon: PenTool, color: '#C9A84C', estimatedSec: 30 },
  ana_review_copy: { agent: 'Ana', role: 'Revisora de Copy', icon: CheckCircle, color: '#4CAF50', estimatedSec: 20 },
  lucas_design: { agent: 'Lucas', role: 'Designer', icon: Palette, color: '#7CB9E8', estimatedSec: 120 },
  rafael_review_design: { agent: 'Rafael', role: 'Diretor de Arte', icon: Award, color: '#9B59B6', estimatedSec: 25 },
  marcos_video: { agent: 'Marcos', role: 'Videomaker', icon: Film, color: '#E74C3C', estimatedSec: 500 },
  rafael_review_video: { agent: 'Rafael', role: 'Revisor de Video', icon: Award, color: '#9B59B6', estimatedSec: 25 },
  pedro_publish: { agent: 'Pedro', role: 'Publisher', icon: CalendarClock, color: '#E8A87C', estimatedSec: 25 },
};

const STEP_ORDER = ['sofia_copy', 'ana_review_copy', 'lucas_design', 'rafael_review_design', 'marcos_video', 'rafael_review_video', 'pedro_publish'];

const PLATFORMS = [
  { id: 'whatsapp', label: 'WhatsApp', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '768x1344' },
  { id: 'instagram', label: 'Instagram', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '768x1344' },
  { id: 'facebook', label: 'Facebook', imgRatio: '1:1', vidRatio: '16:9', imgSize: '1024x1024', vidSize: '1280x720' },
  { id: 'tiktok', label: 'TikTok', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '768x1344' },
  { id: 'google_ads', label: 'Google Ads', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1280x720' },
  { id: 'telegram', label: 'Telegram', imgRatio: '1:1', vidRatio: '16:9', imgSize: '1024x1024', vidSize: '1280x720' },
  { id: 'email', label: 'Email', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1280x720' },
  { id: 'sms', label: 'SMS', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '768x1344' },
];

/* ── Progress Timer ── */
function ProgressTimer({ startedAt, estimatedSec, color }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!startedAt) return;
    const start = new Date(startedAt).getTime();
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);
  const pct = Math.min((elapsed / estimatedSec) * 100, 95);
  const remaining = Math.max(estimatedSec - elapsed, 0);
  const fmt = remaining > 60 ? `~${Math.ceil(remaining / 60)}min` : `~${remaining}s`;
  return (
    <div className="mt-1.5 px-1">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[8px] text-[#555]">{elapsed}s decorridos</span>
        <span className="text-[8px] text-[#555]">{fmt} restante</span>
      </div>
      <div className="h-1 rounded-full bg-[#1A1A1A] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-1000 ease-linear" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

/* ── Image Lightbox ── */
function ImageLightbox({ images, initialIndex, onClose, pipelineId, onRegenerate }) {
  const { t } = useTranslation();
  const [index, setIndex] = useState(initialIndex || 0);
  const [showAdjust, setShowAdjust] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const url = images[index];
  if (!url) return null;

  const requestAdjust = async () => {
    if (!feedback.trim()) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/campaigns/pipeline/${pipelineId}/regenerate-design`, {
        design_index: index, feedback: feedback.trim()
      });
      toast.success(t('studio.adjustment_requested') || 'Adjustment requested! Generating new image...');
      setShowAdjust(false);
      setFeedback('');
      if (onRegenerate) onRegenerate();
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao solicitar ajuste');
    }
    setSubmitting(false);
  };

  return (
    <div data-testid="image-lightbox" className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4" onClick={onClose}>
      <div className="relative max-w-3xl w-full" onClick={e => e.stopPropagation()}>
        <button onClick={onClose} className="absolute -top-3 -right-3 z-10 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] transition">
          <X size={16} className="text-white" />
        </button>
        <img src={resolveImageUrl(url)} alt={`Design ${index + 1}`}
          className="w-full rounded-xl border border-[#333] shadow-2xl" />
        <div className="flex items-center justify-between mt-3">
          <div className="flex gap-2">
            {images.map((u, i) => u && (
              <button key={i} onClick={() => setIndex(i)}
                className={`h-12 w-12 rounded-lg overflow-hidden border-2 transition ${i === index ? 'border-[#C9A84C]' : 'border-[#333] opacity-60 hover:opacity-100'}`}>
                <img src={resolveImageUrl(u)} alt="" className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <a href={resolveImageUrl(url)} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1A1A1A] border border-[#333] text-[11px] text-white hover:bg-[#222] transition">
              <Download size={12} /> Baixar
            </a>
            <button onClick={() => setShowAdjust(!showAdjust)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[11px] text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
              <MessageSquare size={12} /> Pedir Ajuste
            </button>
          </div>
        </div>
        {showAdjust && (
          <div className="mt-3 p-3 rounded-xl bg-[#111] border border-[#C9A84C]/20">
            <p className="text-[10px] text-[#888] mb-1.5">{t('studio.describe_adjustment') || 'Describe the adjustment you want'} {index + 1}:</p>
            <textarea value={feedback} onChange={e => setFeedback(e.target.value)} rows={2}
              placeholder="Ex: Aumentar o logo, mudar a cor de fundo para azul, adicionar o telefone..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#0A0A0A] px-3 py-2 text-xs text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/30" />
            <button onClick={requestAdjust} disabled={submitting || !feedback.trim()}
              className="mt-2 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] text-[11px] font-bold text-black hover:opacity-90 disabled:opacity-30 transition">
              {submitting ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
              {submitting ? (t('studio.generating') || 'Generating...') : (t('studio.send_adjustment') || 'Send Adjustment')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

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
            {status === 'running' && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><span className="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse" />{revisionRound > 0 ? `Revisando (${revisionRound}/1)` : 'Processando...'}</span>}
            {isGeneratingImages && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400"><Loader2 size={8} className="animate-spin" />{t('studio.generating_images') || 'Generating images...'}</span>}
            {isGeneratingVideo && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/15 text-red-400"><Film size={8} className="animate-spin" />{t('studio.generating_video') || 'Generating commercial video...'}</span>}
            {status === 'completed' && !needsApproval && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">{t('studio.status_completed') || 'Completed'}</span>}
            {needsApproval && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 animate-pulse"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" />{t('studio.status_waiting') || 'Waiting Approval'}</span>}
            {status === 'pending' && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#222] text-[#555]">Pendente</span>}
            {isFailed && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">{t('studio.status_failed') || 'Failed'}</span>}
            {requiresUpgrade && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><Crown size={8} /> Upgrade Necessario</span>}
            {reviewerRevisionCount > 0 && (step === 'ana_review_copy' || step === 'rafael_review_design') && (
              <span className="inline-flex items-center gap-1 text-[8px] font-semibold px-1.5 py-0.5 rounded-full bg-purple-500/10 text-purple-400">
                <RotateCcw size={7} />{reviewerRevisionCount} revisao(oes)
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
          <p className="text-[8px] text-purple-400 uppercase tracking-wider font-semibold mb-0.5">Feedback do Revisor</p>
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
  const [lightboxIndex, setLightboxIndex] = useState(null);
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
          <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5 flex items-center gap-1"><Film size={10} className="text-red-400" /> Video Comercial Gerado</p>
          <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black">
            <video
              data-testid="pipeline-video-player"
              src={data.video_url}
              controls
              playsInline
              className="w-full max-h-[400px]"
              poster=""
            />
          </div>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">{data.video_duration || 12}s</span>
            <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded capitalize">{data.video_format || 'vertical'}</span>
            <a href={data.video_url} target="_blank" rel="noopener noreferrer"
              className="ml-auto flex items-center gap-1 text-[9px] text-[#C9A84C] hover:underline">
              <Download size={10} /> Baixar Video
            </a>
          </div>
        </div>
      )}
      {hasImages && (
        <div className="mt-2">
          <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Imagens Geradas — clique para ver em tamanho completo</p>
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
              <span className="text-[8px] text-[#555]">Formatos:</span>
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
    </div>
  );
}

function CopyApproval({ data, onApprove }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState(data?.auto_selection || 1);
  const [submitting, setSubmitting] = useState(false);
  const autoSel = data?.auto_selection || 1;
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selection: selected }); setSubmitting(false); };
  return (
    <div data-testid="copy-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">{t('studio.choose_variation') || 'Choose the variation to continue'}:</p>
      <p className="text-[9px] text-[#888]">Ana recomendou a <span className="text-[#C9A84C] font-bold">Variacao {autoSel}</span></p>
      <div className="flex gap-2">
        {[1, 2, 3].map(n => (
          <button key={n} data-testid={`select-copy-${n}`} onClick={() => setSelected(n)}
            className={`flex-1 rounded-lg py-2.5 text-[11px] font-semibold border-2 transition-all ${selected === n ? 'border-[#C9A84C] bg-[#C9A84C]/15 text-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.15)]' : 'border-[#222] text-[#666] hover:text-white hover:border-[#333]'}`}>
            {n === autoSel ? `Var ${n} *` : `Variacao ${n}`}
          </button>
        ))}
      </div>
      <button data-testid="approve-copy-btn" onClick={handleApprove} disabled={submitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-[0_0_20px_rgba(201,168,76,0.2)]">
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        {submitting ? 'Enviando...' : 'Aprovar e Continuar'}
      </button>
    </div>
  );
}

function DesignApproval({ data, onApprove, images, pipelineId, onRefresh }) {
  const autoSels = data?.auto_selections || {};
  const [selections, setSelections] = useState(autoSels);
  const [submitting, setSubmitting] = useState(false);
  const [lightboxIdx, setLightboxIdx] = useState(null);
  const platforms = Object.keys(autoSels);
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selections: Object.keys(selections).length > 0 ? selections : { default: 1 } }); setSubmitting(false); };
  return (
    <div data-testid="design-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">Revise os designs e escolha por plataforma:</p>

      {/* Image preview thumbnails with click to enlarge */}
      {images && images.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {images.map((url, i) => (
            <button key={i} onClick={() => setLightboxIdx(i)}
              className="rounded-lg overflow-hidden border-2 border-[#222] hover:border-[#C9A84C]/50 transition relative group">
              <img src={resolveImageUrl(url)} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" />
              <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                <Maximize2 size={16} className="text-white" />
              </div>
              <div className="absolute bottom-0 left-0 right-0 bg-black/80 px-2 py-1 text-center">
                <span className="text-[9px] text-white font-bold">Design {i + 1}</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {lightboxIdx !== null && (
        <ImageLightbox images={images} initialIndex={lightboxIdx}
          onClose={() => setLightboxIdx(null)} pipelineId={pipelineId} onRegenerate={onRefresh} />
      )}

      {platforms.length > 0 ? platforms.map(p => (
        <div key={p} className="flex items-center gap-2">
          <span className="text-[11px] text-white font-medium capitalize w-24">{p}</span>
          <div className="flex gap-1.5 flex-1">
            {[1, 2, 3].map(n => (
              <button key={n} onClick={() => setSelections(prev => ({ ...prev, [p]: n }))}
                className={`flex-1 rounded-lg py-2 text-[10px] font-semibold border-2 transition-all ${(selections[p] || 1) === n ? 'border-[#C9A84C] bg-[#C9A84C]/15 text-[#C9A84C]' : 'border-[#222] text-[#666] hover:text-white'}`}>
                {n === autoSels[p] ? `D${n} *` : `Design ${n}`}
              </button>
            ))}
          </div>
        </div>
      )) : (
        <p className="text-[9px] text-[#888]">Rafael reviewed the designs. Click to approve and publish.</p>
      )}
      <button data-testid="approve-design-btn" onClick={handleApprove} disabled={submitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-[0_0_20px_rgba(201,168,76,0.2)]">
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        {submitting ? 'Enviando...' : 'Aprovar e Continuar'}
      </button>
    </div>
  );
}

/* ── Completed Pipeline Summary ── */
function CompletedSummary({ pipeline }) {
  const { t } = useTranslation();
  const steps = pipeline.steps || {};
  const rawCopy = steps.ana_review_copy?.approved_content || steps.sofia_copy?.output || '';
  const approvedCopy = cleanDisplayText(rawCopy);
  const images = steps.lucas_design?.image_urls?.filter(u => u) || [];
  const videoUrl = steps.marcos_video?.video_url || '';
  const rawSchedule = steps.pedro_publish?.output || '';
  const schedule = cleanDisplayText(rawSchedule);
  const [activeTab, setActiveTab] = useState('preview');
  const [lightboxIdx, setLightboxIdx] = useState(null);

  const copyToClipboard = (text) => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy');
      document.body.removeChild(ta);
      toast.success('Copiado!');
    } catch { toast.error('Erro ao copiar'); }
  };

  return (
    <div data-testid="completed-summary" className="mx-3 mb-3 rounded-xl border border-green-500/20 bg-gradient-to-b from-green-500/5 to-transparent overflow-hidden">
      <div className="px-3 py-2.5 border-b border-[#151515]">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-7 w-7 rounded-lg bg-green-500/10 flex items-center justify-center"><Check size={14} className="text-green-400" /></div>
          <div>
            <p className="text-xs font-bold text-white">{t('studio.campaign_finished') || 'Campaign Finished'}</p>
            <p className="text-[9px] text-[#666]">{(pipeline.platforms || []).join(' / ')}</p>
          </div>
        </div>
        <div className="flex gap-1">
          {[
            { id: 'preview', label: 'Preview Completo', icon: Eye },
            { id: 'copy', label: 'Copy Final', icon: FileText },
            { id: 'images', label: `Imagens (${images.length})`, icon: Image },
            ...(videoUrl ? [{ id: 'video', label: 'Video', icon: Film }] : []),
            { id: 'schedule', label: 'Cronograma', icon: CalendarClock },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} data-testid={`summary-tab-${tab.id}`}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[9px] font-semibold transition ${
                activeTab === tab.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'
              }`}>
              <tab.icon size={10} />{tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-3 max-h-[450px] overflow-y-auto">
        {activeTab === 'preview' && (
          <div className="space-y-3">
            {/* Preview: Copy + Images side by side */}
            <div>
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">{t('studio.campaign_text') || 'Campaign Copy'}</p>
              <div className="rounded-lg bg-[#111] p-3 border border-[#1A1A1A]">
                <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans">{approvedCopy}</pre>
              </div>
            </div>
            {images.length > 0 && (
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">{t('studio.campaign_images') || 'Campaign Images'}</p>
                <div className="grid grid-cols-3 gap-2">
                  {images.map((url, i) => (
                    <button key={i} onClick={() => setLightboxIdx(i)}
                      className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] relative group text-left hover:border-[#C9A84C]/30 transition">
                      <img src={resolveImageUrl(url)} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                        <Maximize2 size={18} className="text-white" />
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {schedule && (
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">Cronograma</p>
                <div className="rounded-lg bg-[#111] p-2 border border-[#1A1A1A]">
                  <pre className="text-[9px] text-[#999] whitespace-pre-wrap leading-relaxed font-sans line-clamp-6">{schedule}</pre>
                </div>
              </div>
            )}
            {videoUrl && (
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1 flex items-center gap-1"><Film size={9} className="text-red-400" /> Video Comercial</p>
                <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black">
                  <video src={videoUrl} controls playsInline className="w-full max-h-[250px]" data-testid="summary-video-player" />
                </div>
              </div>
            )}
          </div>
        )}
        {activeTab === 'copy' && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[9px] text-[#555] uppercase tracking-wider">Copy Aprovada</p>
              <button onClick={() => copyToClipboard(approvedCopy)} className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5"><FileText size={8} />Copiar</button>
            </div>
            <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A]">{approvedCopy}</pre>
          </div>
        )}
        {activeTab === 'images' && (
          <div>
            <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Click to view full size</p>
            {images.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {images.map((url, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] relative group text-left hover:border-[#C9A84C]/30 transition">
                    <img src={resolveImageUrl(url)} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
                      <Maximize2 size={16} className="text-white" />
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1 flex items-center justify-between">
                      <span className="text-[8px] text-white font-semibold">Design {i + 1}</span>
                      <a href={resolveImageUrl(url)} target="_blank" rel="noopener noreferrer"
                        onClick={e => e.stopPropagation()} className="text-white/70 hover:text-white">
                        <Download size={10} />
                      </a>
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <p className="text-[10px] text-[#555] text-center py-4">Nenhuma imagem gerada</p>
            )}
          </div>
        )}
        {activeTab === 'video' && videoUrl && (
          <div>
            <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5 flex items-center gap-1"><Film size={9} className="text-red-400" /> Video Comercial (12s)</p>
            <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black">
              <video src={videoUrl} controls playsInline autoPlay muted className="w-full max-h-[400px]" data-testid="summary-video-tab-player" />
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">12 segundos</span>
              <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">Sora 2</span>
              <a href={videoUrl} target="_blank" rel="noopener noreferrer"
                className="ml-auto flex items-center gap-1 text-[9px] text-[#C9A84C] hover:underline">
                <Download size={10} /> Baixar Video
              </a>
            </div>
          </div>
        )}
        {activeTab === 'schedule' && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[9px] text-[#555] uppercase tracking-wider">Cronograma de Publicacao</p>
              <button onClick={() => copyToClipboard(schedule)} className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5"><FileText size={8} />Copiar</button>
            </div>
            <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A]">{schedule}</pre>
          </div>
        )}
      </div>

      {lightboxIdx !== null && (
        <ImageLightbox images={images} initialIndex={lightboxIdx}
          onClose={() => setLightboxIdx(null)} pipelineId={pipeline.id} />
      )}
    </div>
  );
}

/* ── History Card ── */
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
function AssetUploader({ assets, onAssetsChange }) {
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(null);
  const logoRef = useRef(null);
  const refRef = useRef(null);

  const handleUpload = async (files, type) => {
    if (!files?.length) return;
    setUploading(true);
    const newAssets = [...assets];
    for (const file of Array.from(files)) {
      if (!file.type || !file.type.startsWith('image/')) { toast.error(`"${file.name}" nao e uma imagem valida`); continue; }
      if (file.size > 10 * 1024 * 1024) { toast.error(`"${file.name}" excede 10MB`); continue; }
      try {
        const form = new FormData();
        form.append('file', file);
        form.append('asset_type', type);
        const { data } = await axios.post(`${API}/campaigns/pipeline/upload`, form);
        newAssets.push({ url: data.url, filename: data.filename, type, name: file.name, preview: URL.createObjectURL(file) });
        toast.success(`${file.name} enviado com sucesso!`);
      } catch (e) {
        console.error('Upload error:', e?.response?.status, e?.response?.data, e?.message);
        const msg = e.response?.data?.detail || e.message || 'Erro de conexao';
        toast.error(`Falha ao enviar "${file.name}": ${msg}`);
      }
    }
    onAssetsChange(newAssets);
    setUploading(false);
  };

  const handleDrop = (e, type) => {
    e.preventDefault();
    setDragOver(null);
    const files = e.dataTransfer?.files;
    if (files?.length) handleUpload(files, type);
  };

  const handleDragOver = (e, type) => { e.preventDefault(); setDragOver(type); };
  const handleDragLeave = () => setDragOver(null);

  const removeAsset = (idx) => {
    onAssetsChange(assets.filter((_, i) => i !== idx));
  };

  const logos = assets.filter(a => a.type === 'logo');
  const refs = assets.filter(a => a.type === 'reference');

  return (
    <div data-testid="asset-uploader" className="space-y-3">
      <label className="text-[9px] text-[#555] uppercase tracking-wider block">Brand & Reference Images</label>

      {/* Logo Upload */}
      <div>
        <p className="text-[10px] text-[#888] mb-1.5">Brand logo</p>
        <input ref={logoRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp,image/svg+xml"
          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
          onChange={e => { handleUpload(e.target.files, 'logo'); e.target.value = ''; }} />

        {logos.length > 0 ? (
          <div className="flex gap-2 flex-wrap items-center">
            {logos.map((a, i) => (
              <div key={i} className="relative group">
                <img src={a.preview || resolveImageUrl(a.url)} alt="Logo"
                  className="h-14 w-14 rounded-lg object-cover border-2 border-[#C9A84C]/30" />
                <button onClick={() => removeAsset(assets.indexOf(a))}
                  className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-red-500 flex items-center justify-center shadow-lg">
                  <X size={10} className="text-white" />
                </button>
              </div>
            ))}
            <button onClick={() => logoRef.current?.click()} disabled={uploading}
              className="h-14 w-14 rounded-lg border-2 border-dashed border-[#2A2A2A] flex items-center justify-center hover:border-[#C9A84C]/40 transition disabled:opacity-40">
              <Upload size={14} className="text-[#555]" />
            </button>
          </div>
        ) : (
          <button data-testid="upload-logo-btn"
            onClick={() => logoRef.current?.click()}
            onDrop={e => handleDrop(e, 'logo')}
            onDragOver={e => handleDragOver(e, 'logo')}
            onDragLeave={handleDragLeave}
            disabled={uploading}
            className={`w-full rounded-xl border-2 border-dashed py-4 flex flex-col items-center gap-1.5 transition disabled:opacity-40 cursor-pointer ${
              dragOver === 'logo' ? 'border-[#C9A84C] bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#C9A84C]/30 hover:bg-[#0D0D0D]'
            }`}>
            <div className="h-10 w-10 rounded-xl bg-[#C9A84C]/10 flex items-center justify-center">
              <Upload size={18} className="text-[#C9A84C]" />
            </div>
            <span className="text-[11px] text-[#C9A84C] font-medium">Click to upload logo</span>
            <span className="text-[8px] text-[#444]">PNG, JPG, SVG, WEBP (max 10MB)</span>
          </button>
        )}
      </div>

      {/* Reference Images Upload */}
      <div>
        <p className="text-[10px] text-[#888] mb-1.5">Reference images</p>
        <input ref={refRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp" multiple
          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
          onChange={e => { handleUpload(e.target.files, 'reference'); e.target.value = ''; }} />

        {refs.length > 0 && (
          <div className="flex gap-2 flex-wrap items-center mb-2">
            {refs.map((a, i) => (
              <div key={i} className="relative group">
                <img src={a.preview || resolveImageUrl(a.url)} alt="Ref"
                  className="h-14 w-14 rounded-lg object-cover border border-[#1E1E1E]" />
                <button onClick={() => removeAsset(assets.indexOf(a))}
                  className="absolute -top-1.5 -right-1.5 h-5 w-5 rounded-full bg-red-500 flex items-center justify-center shadow-lg">
                  <X size={10} className="text-white" />
                </button>
                <p className="text-[7px] text-[#555] mt-0.5 truncate max-w-[56px] text-center">{a.name}</p>
              </div>
            ))}
          </div>
        )}
        <button data-testid="upload-ref-btn"
          onClick={() => refRef.current?.click()}
          onDrop={e => handleDrop(e, 'reference')}
          onDragOver={e => handleDragOver(e, 'reference')}
          onDragLeave={handleDragLeave}
          disabled={uploading}
          className={`w-full rounded-xl border-2 border-dashed py-3 flex flex-col items-center gap-1 transition disabled:opacity-40 cursor-pointer ${
            dragOver === 'reference' ? 'border-[#7CB9E8] bg-[#7CB9E8]/5' : 'border-[#1E1E1E] hover:border-[#7CB9E8]/30 hover:bg-[#0D0D0D]'
          }`}>
          <div className="h-8 w-8 rounded-lg bg-[#7CB9E8]/10 flex items-center justify-center">
            <Image size={14} className="text-[#7CB9E8]" />
          </div>
          <span className="text-[10px] text-[#7CB9E8] font-medium">{refs.length > 0 ? 'Add more images' : 'Click to upload reference images'}</span>
          <span className="text-[8px] text-[#444]">Select one or more images</span>
        </button>
      </div>

      {uploading && (
        <div className="flex items-center gap-2 p-2 rounded-lg bg-[#C9A84C]/5 border border-[#C9A84C]/20">
          <Loader2 size={12} className="animate-spin text-[#C9A84C]" />
          <span className="text-[10px] text-[#C9A84C]">Enviando arquivo...</span>
        </div>
      )}
    </div>
  );
}

/* ── Main PipelineView ── */
export default function PipelineView({ context }) {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [pipelines, setPipelines] = useState([]);
  const [activePipeline, setActivePipeline] = useState(null);
  const [campaignName, setCampaignName] = useState('');
  const [briefing, setBriefing] = useState('');
  const [briefingMode, setBriefingMode] = useState('free'); // 'free' | 'guided'
  const [questionnaire, setQuestionnaire] = useState({
    product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: '',
    gender: '', ageMin: '', ageMax: '', socialClass: '', lifestyle: '', painPoints: '', visualStyle: ''
  });
  const [campaignLang, setCampaignLang] = useState('');
  const [mode, setMode] = useState('semi_auto');
  const [platforms, setPlatforms] = useState(['whatsapp', 'instagram', 'facebook']);
  const [creating, setCreating] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [showHistory, setShowHistory] = useState(false);
  const [contactInfo, setContactInfo] = useState({ phone: '', website: '', email: '', address: '' });
  const [showContact, setShowContact] = useState(false);
  const [uploadedAssets, setUploadedAssets] = useState([]);
  const [showFinalPreview, setShowFinalPreview] = useState(false);
  const [savedLogos, setSavedLogos] = useState([]);
  const [savedBriefings, setSavedBriefings] = useState([]);
  const [musicLibrary, setMusicLibrary] = useState([]);
  const [selectedMusic, setSelectedMusic] = useState('');
  const [musicGenre, setMusicGenre] = useState('All');
  const [playingTrack, setPlayingTrack] = useState(null);
  const audioRef = useRef(null);
  const pollRef = useRef(null);

  useEffect(() => {
    loadPipelines();
    loadSavedHistory();
    loadMusicLibrary();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    };
  }, []);

  const loadMusicLibrary = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/music-library`);
      setMusicLibrary(data.tracks || []);
    } catch { /* ignore */ }
  };

  const togglePlayTrack = (trackId) => {
    if (playingTrack === trackId) {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      setPlayingTrack(null);
    } else {
      if (audioRef.current) { audioRef.current.pause(); }
      const audio = new Audio(`${API}/campaigns/pipeline/music-preview/${trackId}`);
      audio.volume = 0.5;
      audio.play().catch(() => {});
      audio.onended = () => setPlayingTrack(null);
      audioRef.current = audio;
      setPlayingTrack(trackId);
    }
  };


  const deleteSavedLogo = async (url) => {
    try {
      await axios.delete(`${API}/campaigns/pipeline/saved/logo?url=${encodeURIComponent(url)}`);
      setSavedLogos(prev => prev.filter(l => l.url !== url));
      setUploadedAssets(prev => prev.filter(a => !(a.url === url && a.type === 'logo')));
      toast.success('Logo removed');
    } catch { toast.error('Erro ao remover logo'); }
  };

  const loadSavedHistory = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/saved/history`);
      setSavedLogos(data.logos || []);
      setSavedBriefings(data.briefings || []);
    } catch (err) {
      console.error('Failed to load saved history:', err?.response?.status, err?.response?.data, err?.message);
    }
  };

  useEffect(() => {
    if (!activePipeline) return;
    const steps = activePipeline.steps || {};
    const newExpanded = { ...expandedSteps };
    let changed = false;
    STEP_ORDER.forEach(s => {
      const st = steps[s];
      if (!st) return;
      if (activePipeline.status === 'waiting_approval' && st.status === 'completed' && (s === 'ana_review_copy' || s === 'rafael_review_design') && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
      if (st.status === 'failed' && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
      if (st.status === 'requires_upgrade' && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
    });
    if (changed) setExpandedSteps(newExpanded);
  }, [activePipeline?.status, activePipeline?.current_step]);

  const startPolling = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => pollPipeline(id), 3000);
  }, []);

  useEffect(() => {
    if (activePipeline && ['running', 'pending'].includes(activePipeline.status)) {
      startPolling(activePipeline.id);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [activePipeline?.id, activePipeline?.status, startPolling]);

  const loadPipelines = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/list`);
      const list = data.pipelines || [];
      setPipelines(list);
      const active = list.find(p => ['running', 'pending', 'waiting_approval'].includes(p.status));
      if (active) {
        setActivePipeline(active);
        const exp = {};
        STEP_ORDER.forEach(s => { if (active.steps?.[s]?.status === 'completed') exp[s] = true; if (active.steps?.[s]?.status === 'failed') exp[s] = true; });
        setExpandedSteps(exp);
      }
    } catch {}
  };

  const pollPipeline = async (id) => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/${id}`);
      setActivePipeline(data);
      if (['completed', 'failed', 'waiting_approval', 'requires_upgrade'].includes(data.status)) {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    } catch {}
  };

  const compileBriefing = () => {
    const q = questionnaire;
    const parts = [];
    if (q.product) parts.push(`${t('studio.q_product')} ${q.product}`);
    if (q.goal) parts.push(`${t('studio.q_goal')} ${q.goal}`);
    // Build audience string from selectable fields
    const audienceParts = [];
    if (q.gender) audienceParts.push(`Gender: ${q.gender}`);
    if (q.ageMin || q.ageMax) audienceParts.push(`Age: ${q.ageMin || '18'}–${q.ageMax || '65+'}`);
    if (q.socialClass) audienceParts.push(`Social class: ${q.socialClass}`);
    if (q.lifestyle) audienceParts.push(`Lifestyle: ${q.lifestyle}`);
    if (q.audience) audienceParts.push(q.audience);
    if (audienceParts.length) parts.push(`${t('studio.q_audience')} ${audienceParts.join(', ')}`);
    if (q.painPoints) parts.push(`${t('studio.q_pain_points') || 'Pain points:'} ${q.painPoints}`);
    if (q.tone) parts.push(`${t('studio.q_tone')} ${q.tone}`);
    if (q.visualStyle) parts.push(`${t('studio.q_visual_style') || 'Visual style:'} ${q.visualStyle}`);
    if (q.offer) parts.push(`${t('studio.q_offer')} ${q.offer}`);
    if (q.differentials) parts.push(`${t('studio.q_differentials')} ${q.differentials}`);
    if (q.cta) parts.push(`${t('studio.q_cta')} ${q.cta}`);
    if (q.urgency) parts.push(`${t('studio.q_urgency')} ${q.urgency}`);
    return parts.join('\n');
  };

  const getEffectiveBriefing = () => briefingMode === 'guided' ? compileBriefing() : briefing;

  const createPipeline = async () => {
    const effectiveBriefing = getEffectiveBriefing();
    if (!campaignName.trim()) { toast.error(t('studio.err_name') || 'Define the campaign name'); return; }
    if (!effectiveBriefing.trim() || platforms.length === 0) { toast.error(t('studio.err_briefing') || 'Fill in the briefing and select at least one platform'); return; }
    setCreating(true);
    try {
      const assetPayload = uploadedAssets.map(a => ({ url: a.url, type: a.type, filename: a.filename }));
      // Build adaptive media format specs from selected platforms
      const selectedPlatforms = PLATFORMS.filter(p => platforms.includes(p.id));
      const mediaFormats = {};
      selectedPlatforms.forEach(p => {
        mediaFormats[p.id] = { imgRatio: p.imgRatio, vidRatio: p.vidRatio, imgSize: p.imgSize, vidSize: p.vidSize };
      });
      const { data } = await axios.post(`${API}/campaigns/pipeline`, {
        briefing: effectiveBriefing.trim(), campaign_name: campaignName.trim(), mode, platforms,
        campaign_language: campaignLang || '',
        context: context || {},
        contact_info: contactInfo,
        uploaded_assets: assetPayload,
        media_formats: mediaFormats,
        selected_music: selectedMusic || '',
      });
      setActivePipeline(data);
      setBriefing(''); setCampaignName(''); setExpandedSteps({}); setUploadedAssets([]);
      setQuestionnaire({ product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: '' });
      setCampaignLang('');
      toast.success(t('studio.pipeline_started') || 'Pipeline started!');
    } catch (e) { toast.error(e.response?.data?.detail || t('studio.err_create') || 'Error creating pipeline'); }
    setCreating(false);
  };

  const approveStep = async (approvalData) => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/approve`, approvalData);
      toast.success(t('studio.approved') || 'Approved! Next step starting...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || t('studio.err_approve') || 'Error approving'); }
  };

  const retryPipeline = async () => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/retry`);
      toast.success(t('studio.retrying') || 'Retrying...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || t('studio.err_generic') || 'Error'); }
  };

  const deletePipeline = async (id) => {
    try {
      await axios.delete(`${API}/campaigns/pipeline/${id}`);
      if (activePipeline?.id === id) setActivePipeline(null);
      setPipelines(prev => prev.filter(p => p.id !== id));
      toast.success(t('studio.pipeline_removed') || 'Pipeline removed');
    } catch {}
  };

  const toggleStep = (step) => setExpandedSteps(prev => ({ ...prev, [step]: !prev[step] }));
  const togglePlatform = (pid) => setPlatforms(prev => prev.includes(pid) ? prev.filter(p => p !== pid) : [...prev, pid]);
  const resetView = () => { setActivePipeline(null); setExpandedSteps({}); setShowFinalPreview(false); };

  const archivePipeline = async (pid) => {
    try {
      await axios.post(`${API}/campaigns/pipeline/${pid}/archive`);
      setActivePipeline(null);
      setExpandedSteps({});
      setShowFinalPreview(false);
      loadPipelines();
      toast.success(t('studio.pipeline_archived') || 'Pipeline archived');
    } catch { toast.error(t('studio.err_archive') || 'Error archiving pipeline'); }
  };

  // ── Final Preview Mode ──
  if (activePipeline && showFinalPreview) {
    return (
      <FinalPreview
        pipeline={activePipeline}
        onClose={() => setShowFinalPreview(false)}
        onPublish={async (editedCopy) => {
          try {
            await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/publish`, {
              edited_copy: editedCopy || null
            });
            toast.success(t('studio.published') || 'Campaign published successfully!');
            navigate('/marketing');
          } catch (e) {
            toast.error(e.response?.data?.detail || t('studio.err_publish') || 'Error publishing campaign');
          }
        }}
      />
    );
  }

  // ── Active Pipeline View ──
  if (activePipeline) {
    const steps = activePipeline.steps || {};
    const completedCount = STEP_ORDER.filter(s => steps[s]?.status === 'completed').length;
    const progressPct = Math.round((completedCount / STEP_ORDER.length) * 100);
    const allStepsComplete = completedCount === STEP_ORDER.length;
    const statusConfig = {
      running: { label: t('studio.status_running') || 'Running', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
      waiting_approval: { label: t('studio.status_waiting') || 'Waiting Approval', color: 'text-amber-400', bg: 'bg-amber-400' },
      completed: { label: t('studio.status_completed') || 'Completed!', color: 'text-green-400', bg: 'bg-green-400' },
      failed: { label: t('studio.status_failed') || 'Failed', color: 'text-red-400', bg: 'bg-red-400' },
      pending: { label: t('studio.status_pending') || 'Starting...', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
    };
    const sc = statusConfig[activePipeline.status] || statusConfig.pending;

    return (
      <div className="flex flex-col h-full">
        {/* Pipeline Header */}
        <div className="border-b border-[#111] px-3 py-2.5 flex items-center gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold text-white">{activePipeline.result?.campaign_name || 'Pipeline'}</p>
              <span className={`inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full ${sc.color}`}
                style={{ backgroundColor: `${sc.bg.replace('bg-', '')}10` }}>
                {['running', 'pending'].includes(activePipeline.status) && <span className={`w-1.5 h-1.5 rounded-full ${sc.bg} animate-pulse`} />}
                {sc.label}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              {(activePipeline.platforms || []).map(p => (
                <span key={p} className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded capitalize">{p}</span>
              ))}
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold text-white">{progressPct}%</span>
            <span className="text-[8px] text-[#555] ml-1">completo</span>
          </div>
          <button onClick={() => archivePipeline(activePipeline.id)} className="text-[#666] hover:text-red-400 p-1.5 rounded-lg hover:bg-[#111] transition" title={t('studio.archive') || 'Archive and create new'}>
            <X size={14} />
          </button>
        </div>

        {/* Briefing */}
        <div className="px-3 py-2 bg-[#080808] border-b border-[#111]">
          <p className="text-[8px] text-[#555] uppercase tracking-wider mb-0.5">Briefing</p>
          <p className="text-[10px] text-[#999] line-clamp-2">{activePipeline.briefing}</p>
          {/* Show uploaded assets info if present */}
          {activePipeline.result?.uploaded_assets?.length > 0 && (
            <div className="flex items-center gap-1.5 mt-1">
              <Image size={9} className="text-[#444]" />
              <span className="text-[8px] text-[#444]">{activePipeline.result.uploaded_assets.length} arquivo(s) anexado(s)</span>
            </div>
          )}
          {activePipeline.result?.contact_info && Object.values(activePipeline.result.contact_info).some(v => v) && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <Phone size={9} className="text-[#444]" />
              <span className="text-[8px] text-[#444]">{t('studio.contact_included') || 'Contact data included'}</span>
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
                  {i < STEP_ORDER.length - 1 && <ArrowRight size={8} className="text-[#333] shrink-0" />}
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
              pipelineStatus={activePipeline.status} onApprove={approveStep}
              expanded={!!expandedSteps[s]} onToggle={() => toggleStep(s)}
              pipelineId={activePipeline.id} onRefresh={() => pollPipeline(activePipeline.id)} />
          ))}
        </div>

        {/* Bottom actions - Show preview when all steps are done */}
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
              <p className="text-xs font-semibold text-red-400 flex-1">Uma etapa falhou. Tente novamente.</p>
              <button onClick={retryPipeline}
                className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition flex items-center gap-1.5">
                <RefreshCw size={12} /> Tentar Novamente
              </button>
            </div>
          </div>
        )}
        {activePipeline.status === 'requires_upgrade' && (
          <div className="px-3 py-3 border-t border-[#111] bg-[#C9A84C]/5">
            <div className="flex items-center gap-2">
              <Crown size={18} className="text-[#C9A84C]" />
              <div className="flex-1">
                <p className="text-xs font-bold text-[#C9A84C]">Upgrade para Enterprise</p>
                <p className="text-[9px] text-[#888]">Sua campanha esta pronta! Faca upgrade para publicar.</p>
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

  // ── Creation Form ──
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Pipeline Intro */}
        <div className="text-center py-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#C9A84C]/5 border border-[#C9A84C]/15">
            {[PenTool, CheckCircle, Palette, Award, Film, CalendarClock].map((Icon, i) => (
              <div key={i} className="flex items-center gap-1">
                {i > 0 && <ArrowRight size={8} className="text-[#333]" />}
                <Icon size={12} style={{ color: Object.values(STEP_META)[i].color }} />
              </div>
            ))}
          </div>
          <p className="text-[9px] text-[#555] mt-1.5">Sofia &rarr; Ana &rarr; Lucas &rarr; Rafael &rarr; Marcos &rarr; Pedro</p>
        </div>

        {/* Campaign Name */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1">{t('studio.campaign_name')}</label>
          <input data-testid="pipeline-campaign-name" value={campaignName} onChange={e => setCampaignName(e.target.value)}
            placeholder={t('studio.campaign_name_placeholder')}
            className="w-full rounded-xl border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-xs text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/30 transition" />
        </div>

        {/* Briefing */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-2">{t('studio.briefing_label')}</label>
          <div className="flex gap-1 mb-3 p-0.5 bg-[#0A0A0A] rounded-lg border border-[#1A1A1A] w-fit">
            <button data-testid="briefing-mode-free" onClick={() => setBriefingMode('free')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition ${briefingMode === 'free' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#555] hover:text-white'}`}>
              <FileText size={10} className="inline mr-1" />{t('studio.briefing_free')}
            </button>
            <button data-testid="briefing-mode-guided" onClick={() => setBriefingMode('guided')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition ${briefingMode === 'guided' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#555] hover:text-white'}`}>
              <CheckCircle size={10} className="inline mr-1" />{t('studio.briefing_guided')}
            </button>
          </div>

          {briefingMode === 'free' ? (
            <div>
              <textarea data-testid="pipeline-briefing" value={briefing} onChange={e => setBriefing(e.target.value)} rows={4}
                placeholder={t('studio.briefing_placeholder')}
                className="w-full rounded-xl border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-xs text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/30 transition" />
              {savedBriefings.length > 0 && (
                <div className="mt-2">
                  <p className="text-[8px] text-[#555] uppercase tracking-wider mb-1.5">{t('studio.previous_briefings') || 'Previous Briefings'}</p>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {savedBriefings.map((sb, i) => (
                      <button key={i} onClick={() => {
                        setBriefing(sb.briefing);
                        if (sb.campaign_name && !campaignName) setCampaignName(sb.campaign_name);
                        if (sb.campaign_language) setCampaignLang(sb.campaign_language);
                        if (sb.platforms?.length) setPlatforms(sb.platforms);
                        toast.success(t('studio.briefing_loaded') || 'Briefing loaded!');
                      }}
                        className="w-full text-left rounded-lg border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2 hover:border-[#C9A84C]/30 transition group">
                        <div className="flex items-center gap-2 mb-0.5">
                          {sb.campaign_name && <span className="text-[10px] font-semibold text-white">{sb.campaign_name}</span>}
                          {sb.campaign_language && <span className="text-[8px] text-[#C9A84C] uppercase">{sb.campaign_language}</span>}
                          <span className="text-[7px] text-[#333] ml-auto group-hover:text-[#C9A84C]">{t('studio.use') || 'Use'}</span>
                        </div>
                        <p className="text-[9px] text-[#555] line-clamp-2">{sb.briefing}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3 bg-[#0A0A0A] rounded-xl border border-[#1A1A1A] p-3">
              <p className="text-[9px] text-[#C9A84C] font-medium mb-1">{t('studio.guided_intro')}</p>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">1. {t('studio.q_product')}</label>
                <input data-testid="q-product" value={questionnaire.product} onChange={e => setQuestionnaire(p => ({...p, product: e.target.value}))}
                  placeholder={t('studio.q_product_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">2. {t('studio.q_goal')}</label>
                <div className="flex flex-wrap gap-1.5 mb-1.5">
                  {[{k:'goal_leads'},{k:'goal_sales'},{k:'goal_awareness'},{k:'goal_engagement'},{k:'goal_launch'},{k:'goal_promo'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, goal: p.goal === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.goal === t(`studio.${k}`) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
                <input value={questionnaire.goal} onChange={e => setQuestionnaire(p => ({...p, goal: e.target.value}))}
                  placeholder={t('studio.q_goal_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">3. {t('studio.q_audience')}</label>

                {/* Gender */}
                <p className="text-[8px] text-[#555] mb-1 mt-1">{t('studio.q_gender') || 'Gender'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['All', 'Male', 'Female', 'LGBTQ+', 'Non-binary'].map(g => (
                    <button key={g} onClick={() => setQuestionnaire(p => ({...p, gender: p.gender === g ? '' : g}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.gender === g ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {g}
                    </button>
                  ))}
                </div>

                {/* Age Range */}
                <p className="text-[8px] text-[#555] mb-1">{t('studio.q_age_range') || 'Age range'}</p>
                <div className="flex items-center gap-1.5 mb-2">
                  <input data-testid="q-age-min" value={questionnaire.ageMin} onChange={e => setQuestionnaire(p => ({...p, ageMin: e.target.value}))}
                    placeholder="18" type="number" min="13" max="99"
                    className="w-16 rounded-md border border-[#1E1E1E] bg-[#111] px-2 py-1 text-[10px] text-white text-center placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
                  <span className="text-[9px] text-[#444]">—</span>
                  <input data-testid="q-age-max" value={questionnaire.ageMax} onChange={e => setQuestionnaire(p => ({...p, ageMax: e.target.value}))}
                    placeholder="65+" type="text"
                    className="w-16 rounded-md border border-[#1E1E1E] bg-[#111] px-2 py-1 text-[10px] text-white text-center placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
                  <div className="flex gap-1 ml-2">
                    {['13-17', '18-24', '25-34', '35-44', '45-54', '55+'].map(r => (
                      <button key={r} onClick={() => { const [min, max] = r.split('-'); setQuestionnaire(p => ({...p, ageMin: min, ageMax: max || '65+'})); }}
                        className={`rounded-md px-1.5 py-0.5 text-[8px] border transition ${questionnaire.ageMin === r.split('-')[0] ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Social Class */}
                <p className="text-[8px] text-[#555] mb-1">{t('studio.q_social_class') || 'Social class'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['A (Luxury)', 'B (Upper-middle)', 'C (Middle)', 'D (Lower-middle)', 'E (Low income)', 'All classes'].map(c => (
                    <button key={c} onClick={() => setQuestionnaire(p => ({...p, socialClass: p.socialClass === c ? '' : c}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.socialClass === c ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {c}
                    </button>
                  ))}
                </div>

                {/* Lifestyle / Interests */}
                <p className="text-[8px] text-[#555] mb-1">{t('studio.q_lifestyle') || 'Lifestyle & Interests'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['Fitness', 'Tech', 'Fashion', 'Gaming', 'Travel', 'Food', 'Music', 'Sports', 'Business', 'Eco-friendly', 'Luxury', 'Family'].map(l => (
                    <button key={l} onClick={() => setQuestionnaire(p => ({...p, lifestyle: p.lifestyle?.includes(l) ? p.lifestyle.replace(l, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '') : (p.lifestyle ? `${p.lifestyle}, ${l}` : l)}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.lifestyle?.includes(l) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {l}
                    </button>
                  ))}
                </div>

                {/* Free-text audience */}
                <input data-testid="q-audience" value={questionnaire.audience} onChange={e => setQuestionnaire(p => ({...p, audience: e.target.value}))}
                  placeholder={t('studio.q_audience_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">4. {t('studio.q_tone')}</label>
                <div className="flex flex-wrap gap-1.5">
                  {[{k:'tone_professional'},{k:'tone_casual'},{k:'tone_urgent'},{k:'tone_inspiring'},{k:'tone_fun'},{k:'tone_sophisticated'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, tone: p.tone === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.tone === t(`studio.${k}`) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">5. {t('studio.q_offer')}</label>
                <input data-testid="q-offer" value={questionnaire.offer} onChange={e => setQuestionnaire(p => ({...p, offer: e.target.value}))}
                  placeholder={t('studio.q_offer_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">6. {t('studio.q_differentials')}</label>
                <input data-testid="q-differentials" value={questionnaire.differentials} onChange={e => setQuestionnaire(p => ({...p, differentials: e.target.value}))}
                  placeholder={t('studio.q_differentials_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">7. {t('studio.q_pain_points') || 'What problems does your audience face?'}</label>
                <input data-testid="q-pain-points" value={questionnaire.painPoints} onChange={e => setQuestionnaire(p => ({...p, painPoints: e.target.value}))}
                  placeholder={t('studio.q_pain_points_placeholder') || 'E.g.: High costs, lack of time, complexity...'}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">8. {t('studio.q_visual_style') || 'Visual style preference'}</label>
                <div className="flex flex-wrap gap-1">
                  {['Minimalist', 'Bold & Vibrant', 'Luxury & Elegant', 'Natural & Organic', 'Tech & Modern', 'Retro & Vintage', 'Dark & Moody', 'Playful & Colorful'].map(s => (
                    <button key={s} onClick={() => setQuestionnaire(p => ({...p, visualStyle: p.visualStyle === s ? '' : s}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.visualStyle === s ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">9. {t('studio.q_cta')}</label>
                <div className="flex flex-wrap gap-1.5">
                  {[{k:'cta_signup'},{k:'cta_demo'},{k:'cta_buy'},{k:'cta_learn'},{k:'cta_download'},{k:'cta_whatsapp'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, cta: p.cta === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.cta === t(`studio.${k}`) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] text-[#777] block mb-1">10. {t('studio.q_urgency')}</label>
                <input data-testid="q-urgency" value={questionnaire.urgency} onChange={e => setQuestionnaire(p => ({...p, urgency: e.target.value}))}
                  placeholder={t('studio.q_urgency_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              {compileBriefing().trim() && (
                <div className="mt-2 p-2.5 rounded-lg bg-[#111] border border-[#1A1A1A]">
                  <p className="text-[8px] text-[#555] uppercase tracking-wider mb-1">{t('studio.briefing_preview')}</p>
                  <pre className="text-[10px] text-[#999] whitespace-pre-wrap font-sans leading-relaxed">{compileBriefing()}</pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Campaign Language */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1">{t('studio.campaign_language')}</label>
          <p className="text-[8px] text-[#444] mb-1.5">{t('studio.campaign_language_desc')}</p>
          <div className="flex flex-wrap gap-1.5">
            {[
              { code: '', label: 'Auto', flag: '🌐' },
              { code: 'pt', label: 'Portugues', flag: '🇧🇷' },
              { code: 'en', label: 'English', flag: '🇺🇸' },
              { code: 'es', label: 'Espanol', flag: '🇪🇸' },
              { code: 'fr', label: 'Francais', flag: '🇫🇷' },
              { code: 'ht', label: 'Kreyol Ayisyen', flag: '🇭🇹' },
            ].map(lang => (
              <button key={lang.code} data-testid={`lang-${lang.code || 'auto'}`}
                onClick={() => setCampaignLang(lang.code)}
                className={`rounded-lg px-3 py-1.5 text-[10px] font-medium border transition flex items-center gap-1.5 ${campaignLang === lang.code ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                <span className="text-sm">{lang.flag}</span> {lang.label}
              </button>
            ))}
            <input value={campaignLang && !['', 'pt', 'en', 'es', 'fr', 'ht'].includes(campaignLang) ? campaignLang : ''}
              onChange={e => setCampaignLang(e.target.value)}
              placeholder="Other language..."
              className="rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition w-32" />
          </div>
        </div>

        {/* Saved Logos + Asset Upload */}
        <div>
          {savedLogos.length > 0 && (
            <div className="mb-2">
              <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1.5">{t('studio.saved_logos') || 'Saved Logos'}</label>
              <div className="flex gap-2 flex-wrap">
                {savedLogos.map((logo, i) => {
                  const isSelected = uploadedAssets.some(a => a.url === logo.url && a.type === 'logo');
                  return (
                    <div key={i} className="relative group">
                      <button onClick={() => {
                        if (isSelected) {
                          setUploadedAssets(prev => prev.filter(a => !(a.url === logo.url && a.type === 'logo')));
                        } else {
                          setUploadedAssets(prev => [...prev.filter(a => a.type !== 'logo'), { url: logo.url, type: 'logo', filename: logo.filename }]);
                        }
                      }}
                        className={`h-12 w-12 rounded-lg overflow-hidden border-2 transition ${isSelected ? 'border-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.3)]' : 'border-[#1E1E1E] opacity-60 hover:opacity-100'}`}>
                        <img src={resolveImageUrl(logo.url)} alt={logo.filename} className="w-full h-full object-contain bg-black" />
                      </button>
                      <button onClick={(e) => { e.stopPropagation(); deleteSavedLogo(logo.url); }}
                        className="absolute -top-1.5 -right-1.5 h-4 w-4 rounded-full bg-red-500/80 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition text-[8px] font-bold hover:bg-red-500">
                        X
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          <AssetUploader assets={uploadedAssets} onAssetsChange={setUploadedAssets} />
        </div>

        {/* Contact Info */}
        <div>
          <button onClick={() => setShowContact(!showContact)} className="flex items-center gap-1.5 text-[9px] text-[#555] uppercase tracking-wider mb-1.5 hover:text-[#888] transition">
            {showContact ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            <Phone size={10} /> {t('studio.contact_data') || 'Contact Data (optional)'}
          </button>
          {showContact && (
            <div data-testid="contact-info-section" className="grid grid-cols-1 sm:grid-cols-2 gap-2 bg-[#0D0D0D] rounded-xl border border-[#1A1A1A] p-3">
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Phone size={8} /> {t('studio.phone') || 'Phone'}</label>
                <input data-testid="contact-phone" value={contactInfo.phone} onChange={e => setContactInfo(p => ({ ...p, phone: e.target.value }))}
                  placeholder="+1 (555) 123-4567" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Globe size={8} /> Website</label>
                <input data-testid="contact-website" value={contactInfo.website} onChange={e => setContactInfo(p => ({ ...p, website: e.target.value }))}
                  placeholder="www.yourcompany.com" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Mail size={8} /> Email</label>
                <input data-testid="contact-email" value={contactInfo.email} onChange={e => setContactInfo(p => ({ ...p, email: e.target.value }))}
                  placeholder="contact@company.com" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><MapPin size={8} /> {t('studio.address') || 'Address'}</label>
                <input data-testid="contact-address" value={contactInfo.address} onChange={e => setContactInfo(p => ({ ...p, address: e.target.value }))}
                  placeholder="123 Main St, City, State" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
            </div>
          )}
        </div>

        {/* Music Library - Compact with Genre Tabs */}
        {musicLibrary.length > 0 && (
          <div>
            <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1.5">{t('studio.music_library') || 'Background Music (Video)'}</label>
            {/* Genre Tabs */}
            <div className="flex gap-1 flex-wrap mb-1.5">
              {['All', ...new Set(musicLibrary.map(t => t.category || 'General'))].map(cat => (
                <button key={cat} onClick={() => setMusicGenre(cat)}
                  className={`rounded-md px-2 py-0.5 text-[8px] border transition ${musicGenre === cat ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C] font-semibold' : 'border-[#1A1A1A] text-[#555] hover:text-white'}`}>
                  {cat}
                </button>
              ))}
            </div>
            {/* Scrollable Track List */}
            <div className="max-h-[160px] overflow-y-auto space-y-0.5 pr-1" style={{scrollbarWidth:'thin', scrollbarColor:'#333 transparent'}}>
              {(musicGenre === 'All' ? musicLibrary : musicLibrary.filter(t => (t.category || 'General') === musicGenre)).map(track => (
                <div key={track.id} data-testid={`music-${track.id}`}
                  onClick={() => setSelectedMusic(selectedMusic === track.id ? '' : track.id)}
                  className={`flex items-center gap-1.5 rounded-md border px-2 py-1 cursor-pointer transition ${selectedMusic === track.id ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1A1A1A] hover:border-[#2A2A2A]'}`}>
                  <button
                    onClick={(e) => { e.stopPropagation(); togglePlayTrack(track.id); }}
                    className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 transition ${playingTrack === track.id ? 'bg-[#C9A84C] text-black' : 'bg-[#1A1A1A] text-[#666] hover:text-white'}`}>
                    {playingTrack === track.id ? <span className="text-[5px] font-bold">||</span> : <Play size={7} />}
                  </button>
                  <span className="text-[8px] font-medium text-white truncate flex-1">{track.name}</span>
                  <span className="text-[7px] text-[#444] truncate max-w-[100px] hidden sm:block">{track.description}</span>
                  {selectedMusic === track.id && <Check size={9} className="text-[#C9A84C] shrink-0" />}
                </div>
              ))}
            </div>
            {selectedMusic && (
              <p className="text-[8px] text-[#C9A84C] flex items-center gap-1 mt-0.5">
                <Check size={8} /> {t('studio.music_selected') || 'Music selected for video'}
              </p>
            )}
            {!selectedMusic && (
              <p className="text-[8px] text-[#444] mt-0.5">{t('studio.music_auto') || 'No selection = AI picks automatically based on campaign mood'}</p>
            )}
          </div>
        )}



        {/* Platforms */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1.5">{t('studio.platforms')}</label>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.map(p => (
              <button key={p.id} data-testid={`platform-${p.id}`} onClick={() => togglePlatform(p.id)}
                className={`rounded-lg px-3 py-1.5 text-[11px] font-medium border transition ${platforms.includes(p.id) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mode */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1.5">{t('studio.execution_mode')}</label>
          <div className="grid grid-cols-2 gap-2">
            <button data-testid="mode-semi-auto" onClick={() => setMode('semi_auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'semi_auto' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <p className="text-xs font-semibold text-white mb-0.5">{t('studio.mode_semi')}</p>
              <p className="text-[9px] text-[#555]">{t('studio.mode_semi_desc')}</p>
            </button>
            <button data-testid="mode-auto" onClick={() => setMode('auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'auto' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <p className="text-xs font-semibold text-white mb-0.5">{t('studio.mode_auto')}</p>
              <p className="text-[9px] text-[#555]">{t('studio.mode_auto_desc')}</p>
            </button>
          </div>
        </div>

        {/* Previous Pipelines */}
        {pipelines.length > 0 && (
          <div>
            <button onClick={() => setShowHistory(!showHistory)} data-testid="toggle-history"
              className="text-[9px] text-[#C9A84C] hover:underline flex items-center gap-1">
              {showHistory ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
              {pipelines.length} pipeline{pipelines.length > 1 ? 's' : ''} anterior{pipelines.length > 1 ? 'es' : ''}
            </button>
            {showHistory && (
              <div className="mt-1.5 space-y-1.5">
                {pipelines.map(p => (
                  <HistoryCard key={p.id} pipeline={p}
                    onSelect={pl => { setActivePipeline(pl); setExpandedSteps({}); }}
                    onDelete={deletePipeline} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Start Button */}
      <div className="px-4 py-3 border-t border-[#1A1A1A]">
        <button data-testid="start-pipeline-btn" onClick={createPipeline}
          disabled={creating || !campaignName.trim() || !(briefingMode === 'guided' ? compileBriefing().trim() : briefing.trim()) || platforms.length === 0}
          className="w-full rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-[13px] font-bold text-black transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(201,168,76,0.15)]">
          {creating ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
          {creating ? t('studio.starting') : `${mode === 'auto' ? t('studio.start_pipeline_auto') : t('studio.start_pipeline_semi')}`}
        </button>
      </div>
    </div>
  );
}
