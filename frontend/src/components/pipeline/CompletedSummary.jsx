import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Check, Download, Eye, Maximize2, X, Play, Film, Loader2, RefreshCw, Send, Globe, Phone, Mail, MapPin, Building2, Image, FileText, Palette, Sparkles, CalendarClock } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { STEP_ORDER, cleanDisplayText } from './constants';
import FinalPreview from '../FinalPreview';
import { resolveImageUrl } from '../../utils/resolveImageUrl';
import { ImageLightbox } from './ImageLightbox';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STYLE_FILTERS = [
  { id: 'professional', label: 'Professional', icon: '💼', color: '#4A90D9' },
  { id: 'minimalist', label: 'Minimalist', icon: '◻️', color: '#A0A0A0' },
  { id: 'vibrant', label: 'Bold & Vibrant', icon: '🎨', color: '#FF6B6B' },
  { id: 'luxury', label: 'Luxury', icon: '✨', color: '#C9A84C' },
  { id: 'playful', label: 'Fun & Playful', icon: '🎉', color: '#FF9F43' },
  { id: 'bold', label: 'Bold Impact', icon: '⚡', color: '#E74C3C' },
  { id: 'organic', label: 'Natural & Organic', icon: '🌿', color: '#27AE60' },
  { id: 'tech', label: 'Tech & Modern', icon: '🔮', color: '#8E44AD' },
  { id: 'cartoon', label: 'Cartoon', icon: '🎭', color: '#F39C12' },
  { id: 'illustration', label: 'Illustration', icon: '🖌️', color: '#E67E22' },
  { id: 'watercolor', label: 'Watercolor', icon: '💧', color: '#3498DB' },
  { id: 'neon', label: 'Neon Glow', icon: '💜', color: '#9B59B6' },
  { id: 'retro', label: 'Retro & Vintage', icon: '📼', color: '#D35400' },
  { id: 'flat', label: 'Flat Design', icon: '📐', color: '#1ABC9C' },
  { id: 'corporate', label: 'Corporate', icon: '🏢', color: '#2C3E50' },
];

function CompletedSummary({ pipeline }) {
  const { t } = useTranslation();
  const steps = pipeline.steps || {};
  const rawCopy = steps.ana_review_copy?.approved_content || steps.sofia_copy?.output || '';
  const approvedCopy = cleanDisplayText(rawCopy);
  const images = steps.lucas_design?.image_urls?.filter(u => u) || [];
  const videoUrl = steps.marcos_video?.video_url || '';
  const rawSchedule = steps.pedro_publish?.output || '';
  const schedule = cleanDisplayText(rawSchedule);
  const validationLabel = 'Validation Report';
  const [activeTab, setActiveTab] = useState('preview');
  const [lightboxIdx, setLightboxIdx] = useState(null);
  const [showVideoLightbox, setShowVideoLightbox] = useState(false);
  const [generatingStyle, setGeneratingStyle] = useState(null);
  const [styleVariations, setStyleVariations] = useState([]);

  const generateStyleVariation = async (styleId) => {
    setGeneratingStyle(styleId);
    try {
      const token = localStorage.getItem('token');
      const campName = pipeline.name || pipeline.campaign_name || '';
      const productDesc = pipeline.product_description || pipeline.company_description || '';
      const res = await axios.post(`${API}/campaigns/pipeline/regenerate-single-image`, {
        style: styleId,
        pipeline_id: pipeline.id,
        campaign_name: campName,
        campaign_copy: approvedCopy.slice(0, 500),
        product_description: productDesc,
        prompt_override: '',
        language: pipeline.result?.campaign_language || 'pt',
      }, { headers: { Authorization: `Bearer ${token}` } });
      if (res.data?.url) {
        setStyleVariations(prev => [{ style: styleId, url: res.data.url, label: STYLE_FILTERS.find(s => s.id === styleId)?.label || styleId }, ...prev]);
        toast.success(t('studio.variation_created') || 'New variation created!');
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Failed to generate variation');
    }
    setGeneratingStyle(null);
  };

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
            { id: 'variations', label: 'Create Art', icon: Palette },
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
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1 flex items-center gap-1"><Film size={9} className="text-red-400" /> {t('studio.video_commercial')}</p>
                <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black relative group cursor-pointer" onClick={() => setShowVideoLightbox(true)}>
                  <video src={videoUrl} controls playsInline className="w-full max-h-[250px]" data-testid="summary-video-player" onClick={e => e.stopPropagation()} />
                  <button data-testid="summary-video-expand-btn" onClick={(e) => { e.stopPropagation(); setShowVideoLightbox(true); }}
                    className="absolute top-2 right-2 h-8 w-8 rounded-lg bg-black/60 border border-white/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/80 z-10">
                    <Maximize2 size={14} className="text-white" />
                  </button>
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
            <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5 flex items-center gap-1"><Film size={9} className="text-red-400" /> {t('studio.video_commercial')}</p>
            <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black relative group cursor-pointer" onClick={() => setShowVideoLightbox(true)}>
              <video src={videoUrl} controls playsInline autoPlay muted className="w-full max-h-[400px]" data-testid="summary-video-tab-player" onClick={e => e.stopPropagation()} />
              <button data-testid="video-tab-expand-btn" onClick={(e) => { e.stopPropagation(); setShowVideoLightbox(true); }}
                className="absolute top-2 right-2 h-8 w-8 rounded-lg bg-black/60 border border-white/20 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/80 z-10">
                <Maximize2 size={14} className="text-white" />
              </button>
            </div>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">12 segundos</span>
              <span className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">Sora 2</span>
              <button onClick={() => setShowVideoLightbox(true)} data-testid="video-tab-expand-text"
                className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5">
                <Maximize2 size={9} /> {t('studio.expand')}
              </button>
              <a href={videoUrl} target="_blank" rel="noopener noreferrer"
                className="ml-auto flex items-center gap-1 text-[9px] text-[#C9A84C] hover:underline">
                <Download size={10} /> {t('studio.download_video')}
              </a>
            </div>
          </div>
        )}
        {activeTab === 'variations' && (
          <div data-testid="style-variations-tab">
            <p className="text-[9px] text-[#555] uppercase tracking-wider mb-2">Choose a visual style to create new art</p>
            <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5 mb-4">
              {STYLE_FILTERS.map(sf => (
                <button key={sf.id} data-testid={`style-${sf.id}`}
                  onClick={() => generateStyleVariation(sf.id)}
                  disabled={generatingStyle !== null}
                  className={`rounded-lg border p-2 text-center transition-all hover:scale-[1.02] ${
                    generatingStyle === sf.id
                      ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10'
                      : 'border-[#1E1E1E] bg-[#0D0D0D] hover:border-white/[0.15] hover:bg-[#111]'
                  } disabled:opacity-40`}>
                  {generatingStyle === sf.id ? (
                    <Loader2 size={16} className="animate-spin text-[#C9A84C] mx-auto mb-1" />
                  ) : (
                    <span className="text-sm block mb-0.5">{sf.icon}</span>
                  )}
                  <span className="text-[8px] font-semibold text-[#ccc] block leading-tight">{sf.label}</span>
                </button>
              ))}
            </div>

            {/* Generated variations gallery */}
            {styleVariations.length > 0 && (
              <div>
                <p className="text-[9px] text-[#C9A84C] uppercase tracking-wider mb-1.5 flex items-center gap-1">
                  <Sparkles size={9} /> Generated Variations ({styleVariations.length})
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {styleVariations.map((sv, i) => (
                    <div key={i} className="relative rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] group hover:border-[#C9A84C]/30 transition">
                      <img src={resolveImageUrl(sv.url)} alt={sv.label} className="w-full aspect-square object-cover" loading="lazy" />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                        <a href={resolveImageUrl(sv.url)} target="_blank" rel="noopener noreferrer"
                          className="h-8 w-8 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center">
                          <Download size={14} className="text-white" />
                        </a>
                      </div>
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-2 py-1.5">
                        <span className="text-[8px] font-semibold text-white">{sv.label}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {styleVariations.length === 0 && !generatingStyle && (
              <div className="text-center py-6 rounded-lg border border-dashed border-[#1E1E1E]">
                <Palette size={24} className="text-[#333] mx-auto mb-2" />
                <p className="text-[10px] text-[#555]">Click a style above to generate a new art variation</p>
                <p className="text-[8px] text-[#333] mt-1">Uses the same campaign prompt with a different visual style</p>
              </div>
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
      {showVideoLightbox && videoUrl && (
        <div data-testid="video-lightbox" className="fixed inset-0 z-[70] bg-black/95 flex items-center justify-center p-4" onClick={() => setShowVideoLightbox(false)}>
          <div className="relative w-full max-w-4xl" onClick={e => e.stopPropagation()}>
            <button onClick={() => setShowVideoLightbox(false)} data-testid="video-lightbox-close"
              className="absolute -top-3 -right-3 z-10 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] transition">
              <X size={16} className="text-white" />
            </button>
            <div className="rounded-xl overflow-hidden border border-[#333] bg-black shadow-2xl">
              <video src={videoUrl} controls playsInline autoPlay className="w-full" style={{ maxHeight: '80vh' }} />
            </div>
            <div className="flex items-center justify-between mt-3">
              <span className="text-[9px] text-[#555] bg-[#111] px-2 py-1 rounded">Sora 2</span>
              <a href={videoUrl} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1A1A1A] border border-[#333] text-[11px] text-white hover:bg-[#222] transition">
                <Download size={12} /> {t('studio.download')} Video
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── History Card ── */

export { CompletedSummary };
