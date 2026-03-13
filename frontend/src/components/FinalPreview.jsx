import { useState } from 'react';
import { X, Download, Maximize2, Check, ChevronLeft, ThumbsUp, Heart, MessageCircle, Bookmark, Share2, Send, MoreHorizontal, Globe, Eye } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const LOGO_URL = '/brand/logo.png';

/* ── Text Cleaner ── */
function cleanText(raw) {
  if (!raw) return '';
  let text = raw;
  // Extract approved variation if markers present
  const varMatch = text.match(/===VARIA(?:TION|CAO|ÇÃO)\s*\d+===([\s\S]*?)(?=={3}|$)/i);
  if (varMatch) text = varMatch[1];
  // Strip all markdown bold/italic first
  text = text.replace(/\*\*\*([^*]+)\*\*\*/g, '$1');
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/#{1,3}\s+/g, '');
  // Remove ALL label prefixes (with or without preceding markdown/symbols)
  const labels = 'Title|Titulo|Título|Copy|Texto|Headline|Body|CTA|Caption|Legenda|Subject|Assunto|Chamada|Subtítulo|Subtitle|Hashtags|Visual|Conceito|Concept|Plataforma|Platform|Dimensões|Dimensions|Adaptações|Call.to.Action';
  const labelRegex = new RegExp(`^\\s*(?:${labels})\\s*[:：]\\s*`, 'gim');
  text = text.replace(labelRegex, '');
  // Remove lines that are ONLY a label with nothing after
  text = text.replace(new RegExp(`^\\s*(?:${labels})\\s*$`, 'gim'), '');
  // Remove variation markers
  text = text.replace(/={3,}.*?={3,}/g, '');
  // Remove --- separators
  text = text.replace(/^-{3,}\s*$/gm, '');
  // Clean up excessive whitespace
  text = text.replace(/\n{3,}/g, '\n\n').trim();
  const lines = text.split('\n').filter(l => l.trim());
  return lines.slice(0, 10).join('\n');
}

/* ── WhatsApp Mockup ── */
function WhatsAppMockup({ copy, image, contact }) {
  return (
    <div data-testid="mockup-whatsapp" className="w-full max-w-[320px] mx-auto">
      <div className="bg-[#075E54] rounded-t-xl px-3 py-2 flex items-center gap-2">
        <ChevronLeft size={16} className="text-white/70" />
        <img src={LOGO_URL} alt="AgentZZ" className="w-7 h-7 rounded-full object-contain bg-black" />
        <div className="flex-1">
          <p className="text-[11px] font-semibold text-white">AgentZZ</p>
          <p className="text-[8px] text-white/50">online</p>
        </div>
        <MoreHorizontal size={14} className="text-white/50" />
      </div>
      <div className="bg-[#0B141A] px-2.5 py-3 min-h-[280px] rounded-b-xl" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg width=\'100\' height=\'100\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cdefs%3E%3Cpattern id=\'p\' width=\'20\' height=\'20\' patternUnits=\'userSpaceOnUse\'%3E%3Ccircle cx=\'2\' cy=\'2\' r=\'0.5\' fill=\'%23ffffff06\'/%3E%3C/pattern%3E%3C/defs%3E%3Crect fill=\'url(%23p)\' width=\'100\' height=\'100\'/%3E%3C/svg%3E")' }}>
        <div className="max-w-[85%] ml-auto">
          <div className="bg-[#005C4B] rounded-xl rounded-tr-sm p-2 shadow">
            {image && <img src={`${BACKEND}${image}`} alt="" className="w-full rounded-lg mb-1.5" />}
            <p className="text-[10px] text-white/90 whitespace-pre-wrap leading-relaxed">{copy}</p>
            {contact?.website && <a href="#" className="mt-1 block text-[9px] text-[#53BDEB]">{contact.website}</a>}
            {contact?.phone && <p className="text-[8px] text-white/50 mt-0.5">{contact.phone}</p>}
            <p className="text-[7px] text-white/30 text-right mt-1">10:32 AM</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Instagram Mockup ── */
function InstagramMockup({ copy, image, contact }) {
  return (
    <div data-testid="mockup-instagram" className="w-full max-w-[320px] mx-auto bg-black rounded-xl overflow-hidden border border-[#262626]">
      <div className="px-3 py-2 flex items-center gap-2 border-b border-[#262626]">
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#F58529] via-[#DD2A7B] to-[#8134AF] p-0.5">
          <img src={LOGO_URL} alt="AgentZZ" className="w-full h-full rounded-full object-contain bg-black" />
        </div>
        <div className="flex-1">
          <p className="text-[10px] font-semibold text-white">agentzz</p>
          <p className="text-[7px] text-[#A8A8A8]">Patrocinado</p>
        </div>
        <MoreHorizontal size={14} className="text-white/50" />
      </div>
      {image ? (
        <img src={`${BACKEND}${image}`} alt="" className="w-full aspect-square object-cover" />
      ) : (
        <div className="w-full aspect-square bg-[#1A1A1A] flex items-center justify-center">
          <img src={LOGO_URL} alt="" className="w-16 h-16 object-contain opacity-30" />
        </div>
      )}
      <div className="px-3 py-2">
        <div className="flex items-center gap-3 mb-1.5">
          <Heart size={18} className="text-white" />
          <MessageCircle size={18} className="text-white" />
          <Send size={18} className="text-white" />
          <Bookmark size={18} className="text-white ml-auto" />
        </div>
        <p className="text-[10px] text-white font-semibold mb-0.5">1,247 curtidas</p>
        <p className="text-[10px] text-white whitespace-pre-wrap leading-relaxed">
          <span className="font-semibold">agentzz </span>
          {copy?.split('\n').slice(0, 4).join('\n')}
        </p>
        {copy?.split('\n').length > 4 && <p className="text-[9px] text-[#A8A8A8] mt-0.5">... mais</p>}
        {contact?.website && <p className="text-[8px] text-[#E4405F] mt-0.5">{contact.website}</p>}
      </div>
    </div>
  );
}

/* ── Facebook Mockup ── */
function FacebookMockup({ copy, image, contact }) {
  return (
    <div data-testid="mockup-facebook" className="w-full max-w-[320px] mx-auto bg-[#242526] rounded-xl overflow-hidden border border-[#3E4042]">
      <div className="px-3 py-2 flex items-center gap-2">
        <img src={LOGO_URL} alt="AgentZZ" className="w-8 h-8 rounded-full object-contain bg-black" />
        <div className="flex-1">
          <p className="text-[11px] font-semibold text-white">AgentZZ</p>
          <div className="flex items-center gap-1">
            <p className="text-[8px] text-[#B0B3B8]">Patrocinado</p>
            <Globe size={8} className="text-[#B0B3B8]" />
          </div>
        </div>
        <MoreHorizontal size={14} className="text-[#B0B3B8]" />
      </div>
      <div className="px-3 pb-2">
        <p className="text-[10px] text-[#E4E6EB] whitespace-pre-wrap leading-relaxed line-clamp-4">{copy}</p>
        {contact?.website && <a href="#" className="text-[9px] text-[#1877F2] mt-0.5 block">{contact.website}</a>}
      </div>
      {image && <img src={`${BACKEND}${image}`} alt="" className="w-full" />}
      <div className="px-3 py-1.5 border-t border-[#3E4042]">
        <div className="flex items-center justify-between text-[10px] text-[#B0B3B8] mb-1.5">
          <span className="flex items-center gap-1"><ThumbsUp size={10} className="text-[#1877F2]" /> 328</span>
          <span>42 comentarios</span>
        </div>
        <div className="flex items-center justify-around border-t border-[#3E4042] pt-1.5">
          <button className="flex items-center gap-1.5 text-[10px] text-[#B0B3B8]"><ThumbsUp size={14} /> Curtir</button>
          <button className="flex items-center gap-1.5 text-[10px] text-[#B0B3B8]"><MessageCircle size={14} /> Comentar</button>
          <button className="flex items-center gap-1.5 text-[10px] text-[#B0B3B8]"><Share2 size={14} /> Compartilhar</button>
        </div>
      </div>
    </div>
  );
}

/* ── Main Final Preview Component ── */
export default function FinalPreview({ pipeline, onClose, onPublish }) {
  const steps = pipeline?.steps || {};
  const approvedCopy = steps.ana_review_copy?.approved_content || steps.sofia_copy?.output || '';
  const images = steps.lucas_design?.image_urls?.filter(u => u) || [];
  const schedule = steps.pedro_publish?.output || '';
  const platforms = pipeline?.platforms || [];
  const contact = pipeline?.result?.contact_info || {};

  // Get Ana's design selections to determine the default image per channel
  const anaDesignSelections = steps.ana_review_design?.user_selections || steps.ana_review_design?.auto_selections || {};

  const [selectedChannel, setSelectedChannel] = useState(platforms[0] || 'whatsapp');

  // Determine the correct image for the current channel based on Ana's selection
  const getSelectedImageIndex = (channel) => {
    const sel = anaDesignSelections[channel] || anaDesignSelections.default || 1;
    return Math.max(0, Math.min(sel - 1, images.length - 1)); // Convert 1-based to 0-based
  };

  const [selectedImage, setSelectedImage] = useState(() => getSelectedImageIndex(platforms[0] || 'whatsapp'));

  // Update selected image when channel changes
  const handleChannelChange = (ch) => {
    setSelectedChannel(ch);
    setSelectedImage(getSelectedImageIndex(ch));
  };

  const cleanCopy = cleanText(approvedCopy);
  const currentImage = images[selectedImage] || null;

  const CHANNEL_MAP = {
    whatsapp: { label: 'WhatsApp', color: '#25D366', Component: WhatsAppMockup },
    instagram: { label: 'Instagram', color: '#E4405F', Component: InstagramMockup },
    facebook: { label: 'Facebook', color: '#1877F2', Component: FacebookMockup },
  };

  const channel = CHANNEL_MAP[selectedChannel] || CHANNEL_MAP.whatsapp;
  const MockupComponent = channel.Component;

  return (
    <div data-testid="final-preview" className="flex flex-col h-full">
      {/* Header */}
      <div className="px-3 py-2.5 border-b border-[#111] shrink-0">
        <div className="flex items-center gap-2">
          <img src={LOGO_URL} alt="AgentZZ" className="h-8 w-8 rounded-lg object-contain bg-black border border-[#1A1A1A]" />
          <div className="flex-1">
            <p className="text-xs font-bold text-white">Preview Final da Campanha</p>
            <p className="text-[9px] text-[#555]">Visualize como sua campanha aparece em cada canal</p>
          </div>
          {onClose && (
            <button onClick={onClose} className="text-[#444] hover:text-white p-1.5 rounded-lg hover:bg-[#111] transition">
              <X size={14} />
            </button>
          )}
        </div>
        {/* Show which image Ana selected */}
        {Object.keys(anaDesignSelections).length > 0 && (
          <div className="mt-1.5 flex items-center gap-1.5">
            <span className="text-[8px] text-[#555]">Ana selecionou:</span>
            {Object.entries(anaDesignSelections).map(([ch, idx]) => (
              <span key={ch} className="text-[8px] font-semibold px-1.5 py-0.5 rounded bg-[#111] capitalize" style={{ color: CHANNEL_MAP[ch]?.color || '#888' }}>
                {ch}: Design {idx}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Channel Selector */}
      <div className="px-3 py-2 border-b border-[#111] flex items-center gap-2 shrink-0 overflow-x-auto">
        {platforms.filter(p => CHANNEL_MAP[p]).map(p => {
          const ch = CHANNEL_MAP[p];
          const selIdx = anaDesignSelections[p];
          return (
            <button key={p} data-testid={`preview-channel-${p}`} onClick={() => handleChannelChange(p)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-semibold transition whitespace-nowrap ${
                selectedChannel === p ? 'border-2 shadow-lg' : 'border border-[#1E1E1E] text-[#555] hover:text-white'
              }`}
              style={selectedChannel === p ? { borderColor: ch.color, color: ch.color, backgroundColor: `${ch.color}10` } : {}}>
              {ch.label}
              {selIdx && <span className="text-[7px] opacity-60">(D{selIdx})</span>}
            </button>
          );
        })}
        {platforms.filter(p => !CHANNEL_MAP[p]).map(p => (
          <span key={p} className="px-3 py-1.5 rounded-lg text-[10px] text-[#333] border border-[#1A1A1A] capitalize">{p}</span>
        ))}
      </div>

      {/* Mockup Area */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <div className="flex flex-col items-center gap-3">
          <MockupComponent copy={cleanCopy} image={currentImage} contact={contact} />

          {/* Image Selector */}
          {images.length > 1 && (
            <div className="flex items-center gap-2">
              <p className="text-[8px] text-[#555] uppercase tracking-wider">Imagem:</p>
              {images.map((url, i) => {
                const isAnaChoice = (getSelectedImageIndex(selectedChannel) === i);
                return (
                  <div key={i} className="relative">
                    <button onClick={() => setSelectedImage(i)}
                      className={`h-10 w-10 rounded-lg overflow-hidden border-2 transition ${
                        i === selectedImage ? 'border-[#C9A84C] shadow-lg' : 'border-[#333] opacity-50 hover:opacity-80'
                      }`}>
                      <img src={`${BACKEND}${url}`} alt="" className="w-full h-full object-cover" />
                    </button>
                    {isAnaChoice && (
                      <div className="absolute -top-1 -right-1 h-3.5 w-3.5 rounded-full bg-green-500 flex items-center justify-center">
                        <Check size={8} className="text-white" />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Schedule Summary */}
          {schedule && (
            <div className="w-full max-w-[320px] rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">Cronograma (Pedro)</p>
              <pre className="text-[9px] text-[#999] whitespace-pre-wrap font-sans leading-relaxed line-clamp-6">{cleanText(schedule)}</pre>
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
              Voltar ao Pipeline
            </button>
          )}
          <button data-testid="publish-campaign-btn"
            onClick={() => { if (onPublish) onPublish(); else toast.success('Campanha publicada com sucesso!'); }}
            className="flex-1 rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(201,168,76,0.15)]">
            <Check size={14} /> Publicar Campanha
          </button>
        </div>
      </div>
    </div>
  );
}
