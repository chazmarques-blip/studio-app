import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Check, Loader2, CheckCircle, AlertTriangle, ArrowRight, Maximize2, X, Film, Image } from 'lucide-react';
import { cleanDisplayText } from './constants';
import { resolveImageUrl } from '../../utils/resolveImageUrl';

function CopyApproval({ data, onApprove }) {
  const { t } = useTranslation();
  const [selected, setSelected] = useState(data?.auto_selection || 1);
  const [submitting, setSubmitting] = useState(false);
  const autoSel = data?.auto_selection || 1;
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selection: selected }); setSubmitting(false); };
  return (
    <div data-testid="copy-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">{t('studio.choose_variation') || 'Choose the variation to continue'}:</p>
      <p className="text-[9px] text-[#888]">Lee recomendou a <span className="text-[#C9A84C] font-bold">Variacao {autoSel}</span></p>
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
        {submitting ? t('studio.sending') : t('studio.approve_continue')}
      </button>
    </div>
  );
}

function DesignApproval({ data, onApprove, images, pipelineId, onRefresh }) {
  const { t } = useTranslation();
  const autoSels = data?.auto_selections || {};
  const [selections, setSelections] = useState(autoSels);
  const [submitting, setSubmitting] = useState(false);
  const [lightboxIdx, setLightboxIdx] = useState(null);
  const platforms = Object.keys(autoSels);
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selections: Object.keys(selections).length > 0 ? selections : { default: 1 } }); setSubmitting(false); };
  return (
    <div data-testid="design-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">{t('studio.review_designs')}</p>

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
        <p className="text-[9px] text-[#888]">George reviewed the designs. Click to approve and publish.</p>
      )}
      <button data-testid="approve-design-btn" onClick={handleApprove} disabled={submitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-[0_0_20px_rgba(201,168,76,0.2)]">
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        {submitting ? t('studio.sending') : t('studio.approve_continue')}
      </button>
    </div>
  );
}

function VideoApproval({ data, onApprove, pipelineId }) {
  const [submitting, setSubmitting] = useState(false);
  const decision = data?.decision || 'approved';
  const output = data?.output || '';

  const handleApprove = async () => {
    setSubmitting(true);
    await onApprove({ step: 'rafael_review_video' });
    setSubmitting(false);
  };

  // Extract key points from Roger's review
  const lines = output.split('\n').filter(l => l.trim());
  const summaryLines = lines.slice(0, 8);

  return (
    <div data-testid="video-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold flex items-center gap-1.5">
        <Film size={13} /> Roger reviewed the video concept
      </p>
      <div className="text-[9px] text-[#888] bg-[#0A0A0A] rounded-lg p-2 max-h-32 overflow-y-auto">
        {summaryLines.map((line, i) => <p key={i} className="mb-0.5">{line}</p>)}
        {lines.length > 8 && <p className="text-[#555]">... ({lines.length - 8} more lines)</p>}
      </div>
      <div className="flex items-center gap-2 text-[9px]">
        <span className={`px-2 py-0.5 rounded-full font-bold ${decision === 'approved' ? 'bg-green-500/15 text-green-400' : 'bg-yellow-500/15 text-yellow-400'}`}>
          {decision === 'approved' ? 'APPROVED' : 'NEEDS REVISION'}
        </span>
      </div>
      <button data-testid="approve-video-btn" onClick={handleApprove} disabled={submitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-[0_0_20px_rgba(201,168,76,0.2)]">
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        {submitting ? 'Processing...' : 'Approve & Continue to Validation'}
      </button>
    </div>
  );
}


/* ── Completed Pipeline Summary ── */

export { CopyApproval, DesignApproval, VideoApproval };
