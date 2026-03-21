import { useState, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Check, ChevronLeft, Heart, MessageCircle, Bookmark, Share2, Send, MoreHorizontal, Loader2, Pencil, Image as ImageIcon, RefreshCw, Film, Download } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND}/api`;
const DEFAULT_LOGO = '/brand/logo.png';

/* ── Text Cleaner ── */
function cleanText(raw) {
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
  const lines = text.split('\n').filter(l => l.trim());
  return lines.slice(0, 10).join('\n');
}

function resolveImageSrc(url) {
  if (!url) return '';
  if (url.startsWith('http') || url.startsWith('blob:') || url.startsWith('data:')) return url;
  return `${BACKEND}${url}`;
}

/* ── WhatsApp Mockup ── */
function WhatsAppMockup({ copy, image, contact, brandName, brandLogo }) {
  return (
    <div data-testid="mockup-whatsapp" className="w-full max-w-[320px] mx-auto">
      <div className="bg-[#075E54] rounded-t-xl px-3 py-2 flex items-center gap-2">
        <ChevronLeft size={16} className="text-white/70" />
        <img src={brandLogo} alt="" className="w-7 h-7 rounded-full object-contain bg-black" onError={e => { e.target.src = DEFAULT_LOGO; }} />
        <div className="flex-1">
          <p className="text-[11px] font-semibold text-white">{brandName}</p>
          <p className="text-[8px] text-white/50">online</p>
        </div>
        <MoreHorizontal size={14} className="text-white/50" />
      </div>
      <div className="bg-[#0B141A] px-2.5 py-3 min-h-[280px] rounded-b-xl" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cdefs%3E%3Cpattern id=\'p\' width=\'20\' height=\'20\' patternUnits=\'userSpaceOnUse\'%3E%3Ccircle cx=\'2\' cy=\'2\' r=\'0.5\' fill=\'%23ffffff06\'/%3E%3C/pattern%3E%3C/defs%3E%3Crect fill=\'url(%23p)\' width=\'100\' height=\'100\'/%3E%3C/svg%3E")' }}>
        <div className="max-w-[85%] ml-auto">
          {image && <img src={resolveImageSrc(image)} alt="" className="w-full rounded-lg mb-1" />}
          <div className="bg-[#005C4B] rounded-xl rounded-tr-none px-3 py-2">
            <p className="text-[10px] text-[#E9EDEF] leading-relaxed whitespace-pre-wrap">{copy}</p>
            {contact?.phone && <p className="text-[9px] text-[#53BDEB] mt-1.5">{contact.phone}</p>}
            {contact?.website && <p className="text-[9px] text-[#53BDEB]">{contact.website}</p>}
            <p className="text-[7px] text-[#ffffff40] text-right mt-1">10:30 ✓✓</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Instagram Mockup ── */
function InstagramMockup({ copy, image, brandName, brandLogo }) {
  const handle = brandName.toLowerCase().replace(/\s+/g, '');
  return (
    <div data-testid="mockup-instagram" className="w-full max-w-[320px] mx-auto bg-black rounded-xl overflow-hidden border border-[#262626]">
      <div className="flex items-center gap-2.5 px-3 py-2">
        <img src={brandLogo} alt="" className="w-7 h-7 rounded-full object-contain bg-black border border-[#333]" onError={e => { e.target.src = DEFAULT_LOGO; }} />
        <p className="text-[11px] font-semibold text-white flex-1">{handle}</p>
        <MoreHorizontal size={14} className="text-white/50" />
      </div>
      {image && <img src={resolveImageSrc(image)} alt="" className="w-full aspect-square object-cover" />}
      <div className="px-3 py-2">
        <div className="flex items-center gap-3 mb-2">
          <Heart size={20} className="text-white" />
          <MessageCircle size={20} className="text-white" />
          <Send size={20} className="text-white" />
          <Bookmark size={20} className="text-white ml-auto" />
        </div>
        <p className="text-[10px] text-white/60 mb-1">1,247 likes</p>
        <p className="text-[10px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap"><span className="font-bold">{handle}</span> {copy}</p>
      </div>
    </div>
  );
}

/* ── Facebook Mockup ── */
function FacebookMockup({ copy, image, brandName, brandLogo }) {
  return (
    <div data-testid="mockup-facebook" className="w-full max-w-[320px] mx-auto bg-[#242526] rounded-xl overflow-hidden border border-[#3A3B3C]">
      <div className="flex items-center gap-2 px-3 py-2.5">
        <img src={brandLogo} alt="" className="w-8 h-8 rounded-full object-contain bg-black" onError={e => { e.target.src = DEFAULT_LOGO; }} />
        <div className="flex-1">
          <p className="text-[11px] font-semibold text-[#E4E6EB]">{brandName}</p>
          <p className="text-[8px] text-[#B0B3B8]">Patrocinado</p>
        </div>
        <MoreHorizontal size={14} className="text-[#B0B3B8]" />
      </div>
      <p className="px-3 pb-2 text-[10px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap">{copy}</p>
      {image && <img src={resolveImageSrc(image)} alt="" className="w-full" />}
      <div className="px-3 py-2 border-t border-[#3A3B3C]">
        <div className="flex items-center justify-around">
          <span className="text-[10px] text-[#B0B3B8]">👍 Like</span>
          <span className="text-[10px] text-[#B0B3B8]">💬 Comment</span>
          <span className="text-[10px] text-[#B0B3B8] flex items-center gap-1"><Share2 size={12} /> Share</span>
        </div>
      </div>
    </div>
  );
}

/* ── TikTok Mockup ── */
function TikTokMockup({ copy, image, brandName, brandLogo }) {
  return (
    <div data-testid="mockup-tiktok" className="w-full max-w-[260px] mx-auto bg-black rounded-xl overflow-hidden border border-[#333] relative" style={{aspectRatio: '9/16', maxHeight: 480}}>
      {image && <img src={resolveImageSrc(image)} alt="" className="w-full h-full object-cover absolute inset-0" />}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
      <div className="absolute bottom-0 left-0 right-10 p-3">
        <p className="text-[10px] font-bold text-white mb-1">@{brandName.toLowerCase().replace(/\s+/g, '')}</p>
        <p className="text-[9px] text-white/90 leading-relaxed line-clamp-4 whitespace-pre-wrap">{copy}</p>
      </div>
      <div className="absolute right-2 bottom-16 flex flex-col items-center gap-3">
        <img src={brandLogo} alt="" className="w-8 h-8 rounded-full border-2 border-white object-contain bg-black" onError={e => { e.target.src = DEFAULT_LOGO; }} />
        <div className="flex flex-col items-center"><Heart size={22} className="text-white" /><span className="text-[7px] text-white">24.5K</span></div>
        <div className="flex flex-col items-center"><MessageCircle size={22} className="text-white" /><span className="text-[7px] text-white">1.2K</span></div>
        <div className="flex flex-col items-center"><Share2 size={22} className="text-white" /><span className="text-[7px] text-white">892</span></div>
      </div>
    </div>
  );
}

/* ── Google Ads Mockup ── */
function GoogleAdsMockup({ copy, image, brandName }) {
  const headline = copy?.split('\n')[0]?.substring(0, 60) || brandName;
  const description = copy?.substring(0, 120) || '';
  const domain = `${brandName.toLowerCase().replace(/\s+/g, '')}.com`;
  return (
    <div data-testid="mockup-google-ads" className="w-full max-w-[320px] mx-auto space-y-3">
      {/* Search Ad */}
      <div className="bg-white rounded-xl overflow-hidden border border-[#dadce0] p-3">
        <div className="flex items-center gap-1.5 mb-1">
          <span className="text-[8px] font-bold text-[#202124] bg-[#f1f3f4] px-1.5 py-0.5 rounded">Ad</span>
          <span className="text-[9px] text-[#202124]">{domain}</span>
        </div>
        <p className="text-[13px] font-medium text-[#1a0dab] leading-tight mb-0.5">{headline} | Comece Agora</p>
        <p className="text-[10px] text-[#4d5156] leading-relaxed line-clamp-2">{description}...</p>
      </div>
      {/* Display Ad */}
      {image && (
        <div className="bg-white rounded-xl overflow-hidden border border-[#dadce0]">
          <img src={resolveImageSrc(image)} alt="" className="w-full aspect-[1.91/1] object-cover" />
          <div className="p-2.5 border-t border-[#eee]">
            <div className="flex items-center gap-1.5 mb-0.5">
              <span className="text-[7px] font-bold text-white bg-[#FBBC04] px-1 py-0.5 rounded">Ad</span>
              <span className="text-[8px] text-[#70757a]">{domain}</span>
            </div>
            <p className="text-[11px] font-medium text-[#202124] line-clamp-1">{headline}</p>
            <p className="text-[8px] text-[#70757a]">Saiba mais sobre {brandName}</p>
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Main Final Preview Component ── */
export default function FinalPreview({ pipeline, campaignLang, onClose, onPublish }) {
  const { t, i18n } = useTranslation();
  const steps = pipeline?.steps || {};
  const approvedCopy = steps.ana_review_copy?.approved_content || steps.sofia_copy?.output || '';
  const images = steps.lucas_design?.image_urls?.filter(u => u) || [];
  const schedule = steps.pedro_publish?.output || '';
  const platforms = pipeline?.platforms || [];
  const contact = pipeline?.result?.contact_info || {};
  const campaignName = pipeline?.result?.campaign_name || (t('studio.campaign_default') || 'Campaign');
  const assets = pipeline?.result?.uploaded_assets || [];
  const contextData = pipeline?.result?.context || {};
  const videoUrl = steps.marcos_video?.video_url || '';

  // Derive brand name from campaign name first, then context
  const brandName = campaignName || contextData.company || t('studio.campaign_default') || 'Campaign';

  // Derive brand logo from uploaded assets
  const logoAsset = assets.find(a => a.type === 'logo');
  const brandLogo = logoAsset ? resolveImageSrc(logoAsset.url) : DEFAULT_LOGO;

  const [publishing, setPublishing] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editedCopy, setEditedCopy] = useState(null); // null = not edited yet
  const [customImages, setCustomImages] = useState([]);
  const [selectedStyle, setSelectedStyle] = useState('');
  const [regenerating, setRegenerating] = useState(false);
  const fileInputRef = useRef(null);

  const anaDesignSelections = steps.rafael_review_design?.result?.auto_selections || {};
  const [selectedChannel, setSelectedChannel] = useState(platforms[0] || 'whatsapp');

  const getSelectedImageIndex = (channel) => {
    const sel = anaDesignSelections[channel] || anaDesignSelections.default || 1;
    return Math.max(0, Math.min(sel - 1, images.length - 1));
  };

  const [selectedImage, setSelectedImage] = useState(() => getSelectedImageIndex(platforms[0] || 'whatsapp'));

  const handleChannelChange = (ch) => {
    setSelectedChannel(ch);
    setSelectedImage(getSelectedImageIndex(ch));
  };

  // Use edited copy if available, otherwise clean the original
  const displayCopy = editedCopy !== null ? editedCopy : cleanText(approvedCopy);

  const handleStartEdit = () => { setEditedCopy(displayCopy); setIsEditing(true); };
  const handleSaveEdit = () => { setIsEditing(false); toast.success(t('studio.text_updated') || 'Text updated!'); };
  const handleCancelEdit = () => { setIsEditing(false); };

  // Custom image upload
  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach(file => {
      if (!file.type.startsWith('image/')) { toast.error(t('studio.only_images') || 'Only images accepted'); return; }
      const blobUrl = URL.createObjectURL(file);
      setCustomImages(prev => [...prev, { url: blobUrl, name: file.name }]);
    });
    e.target.value = '';
  };

  // Regenerate image with style
  const handleRegenerateImage = async (style) => {
    setRegenerating(true);
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/regenerate-single-image`, {
        style,
        campaign_name: campaignName,
        campaign_copy: displayCopy || '',
        product_description: brandName || campaignName || '',
        language: campaignLang || i18n?.language || 'pt',
        pipeline_id: pipeline?.id || '',
      });
      if (data.image_url) {
        setCustomImages(prev => [...prev, { url: data.image_url, name: `${style}-${Date.now()}` }]);
        setSelectedImage(allImages.length);
        toast.success(`${style} ${t('studio.image_generated')}`);
      }
    } catch (e) { toast.error(t('studio.err_generate_image') || 'Error generating image'); }
    setRegenerating(false);
  };

  const allImages = [...images, ...customImages.map(c => c.url)];
  const currentImage = allImages[selectedImage] || null;

  const CHANNEL_MAP = {
    whatsapp: { label: 'WhatsApp', color: '#25D366', Component: WhatsAppMockup },
    instagram: { label: 'Instagram', color: '#E4405F', Component: InstagramMockup },
    facebook: { label: 'Facebook', color: '#1877F2', Component: FacebookMockup },
    tiktok: { label: 'TikTok', color: '#000000', Component: TikTokMockup },
    google_ads: { label: 'Google Ads', color: '#4285F4', Component: GoogleAdsMockup },
  };

  const channel = CHANNEL_MAP[selectedChannel] || CHANNEL_MAP.whatsapp;
  const MockupComponent = channel.Component;

  return (
    <div data-testid="final-preview" className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 py-2.5 border-b border-[#111] shrink-0">
        <div className="flex items-center gap-2">
          <img src={brandLogo} alt="" className="h-8 w-8 rounded-lg object-contain bg-black border border-[#1A1A1A]" onError={e => { e.target.src = DEFAULT_LOGO; }} />
          <div className="flex-1">
            <p className="text-xs font-bold text-white">{campaignName}</p>
            <p className="text-[9px] text-[#777]">Visualize como sua campanha aparece em cada canal</p>
          </div>
          {onClose && (
            <button onClick={onClose} className="text-[#666] hover:text-white p-1.5 rounded-lg hover:bg-[#111] transition">
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Channel Selector */}
      <div className="px-3 py-2 border-b border-[#111] flex items-center gap-2 shrink-0 overflow-x-auto">
        {platforms.filter(p => CHANNEL_MAP[p]).map(p => {
          const ch = CHANNEL_MAP[p];
          return (
            <button key={p} data-testid={`preview-channel-${p}`} onClick={() => handleChannelChange(p)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-semibold transition whitespace-nowrap ${
                selectedChannel === p ? 'border-2 shadow-lg' : 'border border-[#1E1E1E] text-[#777] hover:text-white'
              }`}
              style={selectedChannel === p ? { borderColor: ch.color, color: ch.color, backgroundColor: `${ch.color}10` } : {}}>
              {ch.label}
            </button>
          );
        })}
      </div>

      {/* Mockup Area */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <div className="flex flex-col items-center gap-3">
          <MockupComponent
            copy={isEditing ? editedCopy : displayCopy}
            image={currentImage}
            contact={contact}
            brandName={brandName}
            brandLogo={brandLogo}
          />

          {/* Image Selector + Upload */}
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-[8px] text-[#777] uppercase tracking-wider">{t('studio.image_label')}</p>
            {allImages.map((url, i) => {
              const isCustom = i >= images.length;
              return (
                <div key={i} className="relative">
                  <button onClick={() => setSelectedImage(i)}
                    className={`h-10 w-10 rounded-lg overflow-hidden border-2 transition ${
                      i === selectedImage ? 'border-[#C9A84C] shadow-lg' : 'border-[#333] opacity-50 hover:opacity-80'
                    }`}>
                    <img src={resolveImageSrc(url)} alt="" className="w-full h-full object-cover" />
                  </button>
                  {isCustom && (
                    <div className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-blue-500 flex items-center justify-center text-[6px] text-white font-bold">+</div>
                  )}
                </div>
              );
            })}
            <button data-testid="upload-custom-image" onClick={() => fileInputRef.current?.click()}
              className="h-10 w-10 rounded-lg border-2 border-dashed border-[#333] hover:border-[#C9A84C]/40 flex items-center justify-center transition group">
              <ImageIcon size={14} className="text-[#666] group-hover:text-[#C9A84C]" />
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" multiple onChange={handleFileUpload} className="hidden" />
          </div>

          {/* Style Selector for Image Regeneration */}
          <div className="w-full max-w-[320px]">
            <div className="flex items-center gap-1.5 mb-1.5">
              <RefreshCw size={10} className="text-[#777]" />
              <p className="text-[8px] text-[#777] uppercase tracking-wider">{t('studio.generate_new_style')}</p>
              {regenerating && <Loader2 size={10} className="text-[#C9A84C] animate-spin" />}
            </div>
            <div className="flex flex-wrap gap-1">
              {[
                { key: 'professional', label: 'Professional' },
                { key: 'minimalist', label: 'Minimalist' },
                { key: 'vibrant', label: 'Bold & Vibrant' },
                { key: 'luxury', label: 'Luxury' },
                { key: 'playful', label: 'Fun & Playful' },
                { key: 'bold', label: 'Bold Impact' },
                { key: 'organic', label: 'Natural & Organic' },
                { key: 'tech', label: 'Tech & Modern' },
                { key: 'cartoon', label: 'Cartoon' },
                { key: 'illustration', label: 'Illustration' },
                { key: 'watercolor', label: 'Watercolor' },
                { key: 'neon', label: 'Neon Glow' },
                { key: 'retro', label: 'Retro & Vintage' },
                { key: 'flat', label: 'Flat Design' },
                { key: 'corporate', label: 'Corporate' },
              ].map(s => (
                <button key={s.key} disabled={regenerating}
                  onClick={() => { setSelectedStyle(s.key); handleRegenerateImage(s.key); }}
                  className={`rounded-md px-2 py-1 text-[9px] border transition disabled:opacity-30 ${selectedStyle === s.key && regenerating ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#777] hover:text-white hover:border-[#333]'}`}>
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Text Editing */}
          <div className="w-full max-w-[320px]">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[8px] text-[#777] uppercase tracking-wider">{t('studio.campaign_text') || 'Campaign Copy'}</p>
              {isEditing ? (
                <div className="flex gap-1">
                  <button onClick={handleCancelEdit} className="text-[9px] px-2 py-0.5 rounded bg-[#111] text-[#888] hover:text-white transition">{t('studio.cancel') || 'Cancel'}</button>
                  <button data-testid="save-copy-btn" onClick={handleSaveEdit}
                    className="flex items-center gap-1 text-[9px] px-2 py-0.5 rounded bg-green-500/10 text-green-400 hover:bg-green-500/20 transition">
                    <Check size={9} /> Salvar
                  </button>
                </div>
              ) : (
                <button data-testid="edit-copy-btn" onClick={handleStartEdit}
                  className="flex items-center gap-1 text-[9px] px-2 py-0.5 rounded bg-[#111] text-[#C9A84C] hover:bg-[#1A1A1A] transition">
                  <Pencil size={9} /> {t('studio.edit') || 'Edit'}
                </button>
              )}
            </div>
            {isEditing ? (
              <textarea data-testid="edit-copy-textarea" value={editedCopy} onChange={e => setEditedCopy(e.target.value)} rows={6}
                className="w-full rounded-xl border border-[#C9A84C]/30 bg-[#0D0D0D] px-3 py-2.5 text-[11px] text-white outline-none resize-none focus:border-[#C9A84C]/50 transition" />
            ) : (
              <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-3 py-2.5">
                <p className="text-[10px] text-[#999] whitespace-pre-wrap leading-relaxed">{displayCopy}</p>
              </div>
            )}
          </div>

          {/* Schedule Summary */}
          {schedule && (
            <div className="w-full max-w-[320px] rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
              <p className="text-[9px] text-[#777] uppercase tracking-wider mb-1">Cronograma (Pedro)</p>
              <pre className="text-[9px] text-[#999] whitespace-pre-wrap font-sans leading-relaxed line-clamp-6">{cleanText(schedule)}</pre>
            </div>
          )}

          {/* Video Commercial */}
          {videoUrl && (
            <div className="w-full max-w-[320px]">
              <p className="text-[8px] text-[#777] uppercase tracking-wider mb-1.5 flex items-center gap-1">Video Comercial (Marcos)</p>
              <div className="rounded-xl overflow-hidden border border-[#1E1E1E] bg-black">
                <video src={videoUrl} controls playsInline className="w-full" data-testid="final-preview-video" />
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-[7px] text-[#777] bg-[#111] px-1.5 py-0.5 rounded">12s Sora 2</span>
                <a href={videoUrl} target="_blank" rel="noopener noreferrer"
                  className="ml-auto text-[8px] text-[#C9A84C] hover:underline">Baixar</a>
              </div>
            </div>
          )}
          {!videoUrl && pipeline?.id && (
            <div className="w-full max-w-[320px]">
              <p className="text-[8px] text-[#777] uppercase tracking-wider mb-1.5 flex items-center gap-1">Video Comercial</p>
              <div className="rounded-xl border border-dashed border-[#C9A84C]/30 bg-[#C9A84C]/5 p-4 text-center">
                <Film size={18} className="mx-auto mb-1 text-[#C9A84C]/60" />
                <p className="text-[9px] text-[#666]">{t('studio.generating_video') || 'Video will appear here once generated'}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="px-3 py-3 border-t border-[#1A1A1A] shrink-0 bg-[#0A0A0A]">
        <div className="flex gap-2">
          {onClose && (
            <button onClick={onClose}
              className="flex-1 rounded-xl border border-[#1E1E1E] py-2.5 text-[11px] text-[#888] hover:text-white transition">
              {t('studio.back') || 'Back'}
            </button>
          )}
          <button data-testid="publish-campaign-btn"
            disabled={publishing || isEditing}
            onClick={async () => {
              if (onPublish) {
                setPublishing(true);
                try { await onPublish(editedCopy); } catch {}
                setPublishing(false);
              }
            }}
            className="flex-1 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(201,168,76,0.15)] disabled:opacity-50">
            {publishing ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
            {publishing ? (t('studio.publishing') || 'Publishing...') : (t('studio.publish_campaign') || 'Publish Campaign')}
          </button>
        </div>
      </div>
    </div>
  );
}
