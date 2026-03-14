import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PenTool, Palette, CheckCircle, CalendarClock, Loader2, Check, ChevronDown, ChevronUp, ArrowRight, Zap, RotateCcw, Trash2, RefreshCw, AlertTriangle, Crown, Lock, Upload, X, Image, Phone, Globe, Mail, FileText, Download, Eye, Clock, Maximize2, MessageSquare, Send } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import FinalPreview from './FinalPreview';

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
  ana_review_design: { agent: 'Ana', role: 'Revisora de Design', icon: CheckCircle, color: '#4CAF50', estimatedSec: 20 },
  pedro_publish: { agent: 'Pedro', role: 'Publisher', icon: CalendarClock, color: '#E8A87C', estimatedSec: 25 },
};

const STEP_ORDER = ['sofia_copy', 'ana_review_copy', 'lucas_design', 'ana_review_design', 'pedro_publish'];

const PLATFORMS = [
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'facebook', label: 'Facebook' },
  { id: 'telegram', label: 'Telegram' },
  { id: 'email', label: 'Email' },
  { id: 'sms', label: 'SMS' },
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
      toast.success('Ajuste solicitado! Gerando nova imagem...');
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
        <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${index + 1}`}
          className="w-full rounded-xl border border-[#333] shadow-2xl" />
        <div className="flex items-center justify-between mt-3">
          <div className="flex gap-2">
            {images.map((u, i) => u && (
              <button key={i} onClick={() => setIndex(i)}
                className={`h-12 w-12 rounded-lg overflow-hidden border-2 transition ${i === index ? 'border-[#C9A84C]' : 'border-[#333] opacity-60 hover:opacity-100'}`}>
                <img src={`${process.env.REACT_APP_BACKEND_URL}${u}`} alt="" className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
          <div className="flex gap-2">
            <a href={`${process.env.REACT_APP_BACKEND_URL}${url}`} target="_blank" rel="noopener noreferrer"
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
            <p className="text-[10px] text-[#888] mb-1.5">Descreva o ajuste que deseja no Design {index + 1}:</p>
            <textarea value={feedback} onChange={e => setFeedback(e.target.value)} rows={2}
              placeholder="Ex: Aumentar o logo, mudar a cor de fundo para azul, adicionar o telefone..."
              className="w-full rounded-lg border border-[#1E1E1E] bg-[#0A0A0A] px-3 py-2 text-xs text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/30" />
            <button onClick={requestAdjust} disabled={submitting || !feedback.trim()}
              className="mt-2 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] text-[11px] font-bold text-black hover:opacity-90 disabled:opacity-30 transition">
              {submitting ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
              {submitting ? 'Gerando...' : 'Enviar Ajuste'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function StepCard({ step, data, isActive, pipelineStatus, onApprove, expanded, onToggle, pipelineId, onRefresh }) {
  const meta = STEP_META[step];
  const Icon = meta.icon;
  const status = data?.status || 'pending';
  const isGeneratingImages = status === 'generating_images';
  const needsApproval = pipelineStatus === 'waiting_approval' && (status === 'completed') &&
    ((step === 'ana_review_copy' && !data?.user_selection) ||
     (step === 'ana_review_design' && !data?.user_selections));
  const isFailed = status === 'failed';
  const requiresUpgrade = status === 'requires_upgrade';
  const hasImages = data?.image_urls && data.image_urls.some(u => u);

  return (
    <div data-testid={`step-card-${step}`} className={`rounded-xl border transition-all duration-300 ${
      isActive || isGeneratingImages ? 'border-[#C9A84C]/50 bg-[#0D0D0D] shadow-[0_0_20px_rgba(201,168,76,0.1)]' :
      needsApproval ? 'border-amber-500/40 bg-[#0D0D0D] shadow-[0_0_15px_rgba(245,158,11,0.08)]' :
      isFailed ? 'border-red-500/30 bg-[#0D0D0D]' :
      requiresUpgrade ? 'border-[#C9A84C]/40 bg-[#0D0D0D]' :
      status === 'completed' ? 'border-green-500/20 bg-[#0D0D0D]' :
      'border-[#1A1A1A] bg-[#0A0A0A]'
    }`}>
      <button onClick={onToggle} className="w-full px-3 py-2.5 flex items-center gap-2.5">
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg shrink-0 transition-all ${isActive ? 'animate-pulse' : ''}`} style={{ backgroundColor: `${meta.color}15` }}>
          {status === 'running' || isGeneratingImages ? (
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
          <div className="flex items-center gap-1.5 mt-0.5">
            {status === 'running' && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><span className="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse" />Processando...</span>}
            {isGeneratingImages && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400"><Loader2 size={8} className="animate-spin" />Gerando imagens...</span>}
            {status === 'completed' && !needsApproval && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">Concluido</span>}
            {needsApproval && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 animate-pulse"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" />Aguardando sua aprovacao</span>}
            {status === 'pending' && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#222] text-[#555]">Pendente</span>}
            {isFailed && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">Falhou</span>}
            {requiresUpgrade && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><Crown size={8} /> Upgrade Necessario</span>}
          </div>
        </div>
        {data?.elapsed_ms && <span className="text-[8px] text-[#444] shrink-0 bg-[#111] px-1.5 py-0.5 rounded">{(data.elapsed_ms / 1000).toFixed(1)}s</span>}
        {(data?.output || isFailed || requiresUpgrade) && (expanded ? <ChevronUp size={14} className="text-[#444]" /> : <ChevronDown size={14} className="text-[#444]" />)}
      </button>

      {/* Progress Timer for running steps */}
      {(status === 'running' || isGeneratingImages) && data?.started_at && (
        <ProgressTimer startedAt={data.started_at} estimatedSec={isGeneratingImages ? 90 : meta.estimatedSec} color={meta.color} />
      )}

      {expanded && (data?.output || isFailed || requiresUpgrade) && (
        <StepContent step={step} data={data} hasImages={hasImages} isFailed={isFailed}
          needsApproval={needsApproval} requiresUpgrade={requiresUpgrade}
          onApprove={onApprove} pipelineId={pipelineId} onRefresh={onRefresh} />
      )}
    </div>
  );
}

function StepContent({ step, data, hasImages, isFailed, needsApproval, requiresUpgrade, onApprove, pipelineId, onRefresh }) {
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const images = (data?.image_urls || []).filter(u => u);

  return (
    <div className="px-3 pb-3 border-t border-[#151515]">
      {data?.output && (
        <div className="mt-2 rounded-lg bg-[#111] p-3 max-h-[300px] overflow-y-auto">
          <pre className="text-[10px] text-[#aaa] whitespace-pre-wrap leading-relaxed font-sans">{data.output}</pre>
        </div>
      )}
      {hasImages && (
        <div className="mt-2">
          <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Imagens Geradas — clique para ver em tamanho completo</p>
          <div className="grid grid-cols-3 gap-2">
            {data.image_urls.map((url, i) => url && (
              <button key={i} onClick={() => setLightboxIndex(i)}
                className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] group relative text-left hover:border-[#C9A84C]/30 transition">
                <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <Maximize2 size={18} className="text-white" />
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1">
                  <span className="text-[8px] text-white font-semibold">Design {i + 1}</span>
                </div>
              </button>
            ))}
          </div>
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
      {needsApproval && step === 'ana_review_design' && <DesignApproval data={data} onApprove={onApprove} images={images} pipelineId={pipelineId} onRefresh={onRefresh} />}
    </div>
  );
}

function CopyApproval({ data, onApprove }) {
  const [selected, setSelected] = useState(data?.auto_selection || 1);
  const [submitting, setSubmitting] = useState(false);
  const autoSel = data?.auto_selection || 1;
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selection: selected }); setSubmitting(false); };
  return (
    <div data-testid="copy-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">Escolha a variacao para continuar:</p>
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
              <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" />
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
        <p className="text-[9px] text-[#888]">Ana avaliou os designs. Clique para aprovar e publicar.</p>
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
  const steps = pipeline.steps || {};
  const rawCopy = steps.ana_review_copy?.approved_content || steps.sofia_copy?.output || '';
  const approvedCopy = cleanDisplayText(rawCopy);
  const images = steps.lucas_design?.image_urls?.filter(u => u) || [];
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
            <p className="text-xs font-bold text-white">Campanha Finalizada</p>
            <p className="text-[9px] text-[#666]">{(pipeline.platforms || []).join(' / ')}</p>
          </div>
        </div>
        <div className="flex gap-1">
          {[
            { id: 'preview', label: 'Preview Completo', icon: Eye },
            { id: 'copy', label: 'Copy Final', icon: FileText },
            { id: 'images', label: `Imagens (${images.length})`, icon: Image },
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
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">Texto da Campanha</p>
              <div className="rounded-lg bg-[#111] p-3 border border-[#1A1A1A]">
                <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans">{approvedCopy}</pre>
              </div>
            </div>
            {images.length > 0 && (
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">Imagens da Campanha</p>
                <div className="grid grid-cols-3 gap-2">
                  {images.map((url, i) => (
                    <button key={i} onClick={() => setLightboxIdx(i)}
                      className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] relative group text-left hover:border-[#C9A84C]/30 transition">
                      <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
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
            <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Clique para ver em tamanho completo</p>
            {images.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {images.map((url, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] relative group text-left hover:border-[#C9A84C]/30 transition">
                    <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
                      <Maximize2 size={16} className="text-white" />
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1 flex items-center justify-between">
                      <span className="text-[8px] text-white font-semibold">Design {i + 1}</span>
                      <a href={`${process.env.REACT_APP_BACKEND_URL}${url}`} target="_blank" rel="noopener noreferrer"
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
  const steps = pipeline.steps || {};
  const completedCount = STEP_ORDER.filter(s => steps[s]?.status === 'completed').length;
  const hasImages = steps.lucas_design?.image_urls?.some(u => u);
  const statusColors = { completed: 'text-green-400', failed: 'text-red-400', running: 'text-[#C9A84C]', waiting_approval: 'text-amber-400' };
  const statusLabels = { completed: 'Concluido', failed: 'Falhou', running: 'Em andamento', waiting_approval: 'Aguardando', requires_upgrade: 'Upgrade' };
  const createdAt = pipeline.created_at ? new Date(pipeline.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div data-testid={`history-card-${pipeline.id}`}
      className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 hover:border-[#2A2A2A] transition group cursor-pointer"
      onClick={() => onSelect(pipeline)}>
      <div className="flex items-start gap-2.5">
        {hasImages && steps.lucas_design.image_urls[0] ? (
          <img src={`${process.env.REACT_APP_BACKEND_URL}${steps.lucas_design.image_urls[0]}`}
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
      <label className="text-[9px] text-[#555] uppercase tracking-wider block">Marca & Imagens de Referencia</label>

      {/* Logo Upload */}
      <div>
        <p className="text-[10px] text-[#888] mb-1.5">Logo da marca</p>
        <input ref={logoRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp,image/svg+xml"
          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
          onChange={e => { handleUpload(e.target.files, 'logo'); e.target.value = ''; }} />

        {logos.length > 0 ? (
          <div className="flex gap-2 flex-wrap items-center">
            {logos.map((a, i) => (
              <div key={i} className="relative group">
                <img src={a.preview || `${process.env.REACT_APP_BACKEND_URL}${a.url}`} alt="Logo"
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
            <span className="text-[11px] text-[#C9A84C] font-medium">Clique para enviar o logo</span>
            <span className="text-[8px] text-[#444]">PNG, JPG, SVG, WEBP (max 10MB)</span>
          </button>
        )}
      </div>

      {/* Reference Images Upload */}
      <div>
        <p className="text-[10px] text-[#888] mb-1.5">Imagens de referencia</p>
        <input ref={refRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp" multiple
          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
          onChange={e => { handleUpload(e.target.files, 'reference'); e.target.value = ''; }} />

        {refs.length > 0 && (
          <div className="flex gap-2 flex-wrap items-center mb-2">
            {refs.map((a, i) => (
              <div key={i} className="relative group">
                <img src={a.preview || `${process.env.REACT_APP_BACKEND_URL}${a.url}`} alt="Ref"
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
          <span className="text-[10px] text-[#7CB9E8] font-medium">{refs.length > 0 ? 'Adicionar mais imagens' : 'Clique para enviar imagens de referencia'}</span>
          <span className="text-[8px] text-[#444]">Selecione uma ou varias imagens</span>
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
    product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: ''
  });
  const [campaignLang, setCampaignLang] = useState('');
  const [mode, setMode] = useState('semi_auto');
  const [platforms, setPlatforms] = useState(['whatsapp', 'instagram', 'facebook']);
  const [creating, setCreating] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [showHistory, setShowHistory] = useState(false);
  const [contactInfo, setContactInfo] = useState({ phone: '', website: '', email: '' });
  const [showContact, setShowContact] = useState(false);
  const [uploadedAssets, setUploadedAssets] = useState([]);
  const [showFinalPreview, setShowFinalPreview] = useState(false);
  const pollRef = useRef(null);

  useEffect(() => {
    loadPipelines();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  useEffect(() => {
    if (!activePipeline) return;
    const steps = activePipeline.steps || {};
    const newExpanded = { ...expandedSteps };
    let changed = false;
    STEP_ORDER.forEach(s => {
      const st = steps[s];
      if (!st) return;
      if (activePipeline.status === 'waiting_approval' && st.status === 'completed' && (s === 'ana_review_copy' || s === 'ana_review_design') && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
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
    if (q.audience) parts.push(`${t('studio.q_audience')} ${q.audience}`);
    if (q.tone) parts.push(`${t('studio.q_tone')} ${q.tone}`);
    if (q.offer) parts.push(`${t('studio.q_offer')} ${q.offer}`);
    if (q.differentials) parts.push(`${t('studio.q_differentials')} ${q.differentials}`);
    if (q.cta) parts.push(`${t('studio.q_cta')} ${q.cta}`);
    if (q.urgency) parts.push(`${t('studio.q_urgency')} ${q.urgency}`);
    return parts.join('\n');
  };

  const getEffectiveBriefing = () => briefingMode === 'guided' ? compileBriefing() : briefing;

  const createPipeline = async () => {
    const effectiveBriefing = getEffectiveBriefing();
    if (!campaignName.trim()) { toast.error('Defina o nome da campanha'); return; }
    if (!effectiveBriefing.trim() || platforms.length === 0) { toast.error('Preencha o briefing e selecione ao menos uma plataforma'); return; }
    setCreating(true);
    try {
      const assetPayload = uploadedAssets.map(a => ({ url: a.url, type: a.type, filename: a.filename }));
      const { data } = await axios.post(`${API}/campaigns/pipeline`, {
        briefing: effectiveBriefing.trim(), campaign_name: campaignName.trim(), mode, platforms,
        campaign_language: campaignLang || '',
        context: context || {},
        contact_info: contactInfo,
        uploaded_assets: assetPayload,
      });
      setActivePipeline(data);
      setBriefing(''); setCampaignName(''); setExpandedSteps({}); setUploadedAssets([]);
      setQuestionnaire({ product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: '' });
      setCampaignLang('');
      toast.success('Pipeline iniciado!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao criar pipeline'); }
    setCreating(false);
  };

  const approveStep = async (approvalData) => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/approve`, approvalData);
      toast.success('Aprovado! Proxima etapa iniciando...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao aprovar'); }
  };

  const retryPipeline = async () => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/retry`);
      toast.success('Tentando novamente...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  const deletePipeline = async (id) => {
    try {
      await axios.delete(`${API}/campaigns/pipeline/${id}`);
      if (activePipeline?.id === id) setActivePipeline(null);
      setPipelines(prev => prev.filter(p => p.id !== id));
      toast.success('Pipeline removido');
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
      toast.success('Pipeline arquivado');
    } catch { toast.error('Erro ao arquivar pipeline'); }
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
            toast.success('Campanha publicada com sucesso!');
            navigate('/marketing');
          } catch (e) {
            toast.error(e.response?.data?.detail || 'Erro ao publicar campanha');
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
      running: { label: 'Executando', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
      waiting_approval: { label: 'Aguardando Aprovacao', color: 'text-amber-400', bg: 'bg-amber-400' },
      completed: { label: 'Concluido!', color: 'text-green-400', bg: 'bg-green-400' },
      failed: { label: 'Falhou', color: 'text-red-400', bg: 'bg-red-400' },
      pending: { label: 'Iniciando...', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
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
          <button onClick={() => archivePipeline(activePipeline.id)} className="text-[#666] hover:text-red-400 p-1.5 rounded-lg hover:bg-[#111] transition" title="Arquivar e criar novo">
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
              <span className="text-[8px] text-[#444]">Dados de contato incluidos</span>
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
            {[PenTool, CheckCircle, Palette, CheckCircle, CalendarClock].map((Icon, i) => (
              <div key={i} className="flex items-center gap-1">
                {i > 0 && <ArrowRight size={8} className="text-[#333]" />}
                <Icon size={12} style={{ color: Object.values(STEP_META)[i].color }} />
              </div>
            ))}
          </div>
          <p className="text-[9px] text-[#555] mt-1.5">Sofia &rarr; Ana &rarr; Lucas &rarr; Ana &rarr; Pedro</p>
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
            <textarea data-testid="pipeline-briefing" value={briefing} onChange={e => setBriefing(e.target.value)} rows={4}
              placeholder={t('studio.briefing_placeholder')}
              className="w-full rounded-xl border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-xs text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/30 transition" />
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
                <input data-testid="q-audience" value={questionnaire.audience} onChange={e => setQuestionnaire(p => ({...p, audience: e.target.value}))}
                  placeholder={t('studio.q_audience_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition" />
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
                <label className="text-[9px] text-[#777] block mb-1">7. {t('studio.q_cta')}</label>
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
                <label className="text-[9px] text-[#777] block mb-1">8. {t('studio.q_urgency')}</label>
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
              placeholder="Outro idioma..."
              className="rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30 transition w-32" />
          </div>
        </div>

        {/* Asset Upload */}
        <AssetUploader assets={uploadedAssets} onAssetsChange={setUploadedAssets} />

        {/* Contact Info */}
        <div>
          <button onClick={() => setShowContact(!showContact)} className="flex items-center gap-1.5 text-[9px] text-[#555] uppercase tracking-wider mb-1.5 hover:text-[#888] transition">
            {showContact ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            <Phone size={10} /> Dados de Contato (opcional)
          </button>
          {showContact && (
            <div data-testid="contact-info-section" className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-[#0D0D0D] rounded-xl border border-[#1A1A1A] p-3">
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Phone size={8} /> Telefone</label>
                <input data-testid="contact-phone" value={contactInfo.phone} onChange={e => setContactInfo(p => ({ ...p, phone: e.target.value }))}
                  placeholder="+55 11 99999-9999" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Globe size={8} /> Website</label>
                <input data-testid="contact-website" value={contactInfo.website} onChange={e => setContactInfo(p => ({ ...p, website: e.target.value }))}
                  placeholder="www.suaempresa.com" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Mail size={8} /> Email</label>
                <input data-testid="contact-email" value={contactInfo.email} onChange={e => setContactInfo(p => ({ ...p, email: e.target.value }))}
                  placeholder="contato@empresa.com" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
            </div>
          )}
        </div>

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
