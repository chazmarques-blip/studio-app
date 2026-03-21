import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, ChevronDown, ChevronUp, RefreshCw, Loader2, Maximize2, Download, MessageSquare, Send } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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
              <Download size={12} /> {t('studio.download')}
            </a>
            <button onClick={() => setShowAdjust(!showAdjust)}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[11px] text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
              <MessageSquare size={12} /> {t('studio.request_adjust')}
            </button>
          </div>
        </div>
        {showAdjust && (
          <div className="mt-3 p-3 rounded-xl bg-[#111] border border-[#C9A84C]/20">
            <p className="text-[10px] text-[#888] mb-1.5">{t('studio.describe_adjustment') || 'Describe the adjustment you want'} {index + 1}:</p>
            <textarea value={feedback} onChange={e => setFeedback(e.target.value)} rows={2}
              placeholder="Ex: Aumentar o logo, mudar a cor de fundo para azul, adicionar o telefone..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#0A0A0A] px-3 py-2 text-xs text-white placeholder-[#555] outline-none resize-none focus:border-[#C9A84C]/30" />
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


export { ImageLightbox };
