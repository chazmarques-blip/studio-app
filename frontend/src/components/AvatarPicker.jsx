import { useState, useRef, useCallback } from 'react';
import { Camera, Upload, Sparkles, RotateCcw, Check, X, ZoomIn } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DEFAULT_AVATAR = 'https://static.prod-images.emergentagent.com/jobs/84603ad5-04da-484d-beef-13c6455d5e93/images/e9e9c643eda7783e1e8eebf5e075b6cae5fbdd49181a39682085dd90fe69f0b9.png';
const MAX_GENERATIONS = 5;

export function AvatarPicker({ currentAvatar, onSave, onSkip, lang = 'en', compact = false }) {
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoBase64, setPhotoBase64] = useState(null);
  const [generated, setGenerated] = useState([]); // [{url, variation}]
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const [generating, setGenerating] = useState(false);
  const [genCount, setGenCount] = useState(0);
  const [cameraActive, setCameraActive] = useState(false);
  const [stream, setStream] = useState(null);
  const [zoomed, setZoomed] = useState(null);
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const L = {
    en: { selfie: 'Selfie', upload: 'Upload', generate: 'Generate AI Avatar', regen: 'Regenerate', save: 'Save Avatar', skip: 'Skip for now', creating: 'Creating...', left: 'left', zoom: 'Tap to zoom' },
    pt: { selfie: 'Selfie', upload: 'Upload', generate: 'Gerar Avatar IA', regen: 'Regenerar', save: 'Salvar Avatar', skip: 'Pular por agora', creating: 'Criando...', left: 'restantes', zoom: 'Toque p/ ampliar' },
    es: { selfie: 'Selfie', upload: 'Upload', generate: 'Generar Avatar IA', regen: 'Regenerar', save: 'Guardar Avatar', skip: 'Saltar por ahora', creating: 'Creando...', left: 'restantes', zoom: 'Toca p/ ampliar' },
  };
  const t = L[lang] || L.en;

  const handleFile = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { toast.error('Max 10MB'); return; }
    const reader = new FileReader();
    reader.onload = (ev) => {
      setPhotoPreview(ev.target.result);
      setPhotoBase64(ev.target.result);
      setGenerated([]);
      setSelectedIdx(-1);
      setGenCount(0);
    };
    reader.readAsDataURL(file);
  }, []);

  const startCamera = async () => {
    try {
      const ms = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user', width: 512, height: 512 } });
      setStream(ms);
      setCameraActive(true);
      setTimeout(() => { if (videoRef.current) videoRef.current.srcObject = ms; }, 100);
    } catch { toast.error('Camera denied'); }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const c = canvasRef.current, v = videoRef.current;
    c.width = v.videoWidth; c.height = v.videoHeight;
    c.getContext('2d').drawImage(v, 0, 0);
    const d = c.toDataURL('image/jpeg', 0.85);
    setPhotoPreview(d); setPhotoBase64(d);
    setGenerated([]); setSelectedIdx(-1); setGenCount(0);
    stopCamera();
  };

  const stopCamera = () => {
    if (stream) { stream.getTracks().forEach(t => t.stop()); setStream(null); }
    setCameraActive(false);
  };

  const generate = async () => {
    if (!photoBase64 || genCount >= MAX_GENERATIONS) return;
    setGenerating(true);
    try {
      const { data } = await axios.post(`${API}/avatar/generate`, {
        photo_base64: photoBase64,
        variation_index: genCount
      });
      const newGen = [...generated, { url: data.avatar_url, variation: data.variation }];
      setGenerated(newGen);
      setSelectedIdx(newGen.length - 1);
      setGenCount(prev => prev + 1);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Generation failed');
    } finally { setGenerating(false); }
  };

  const handleSave = async () => {
    const chosen = selectedIdx >= 0 ? generated[selectedIdx]?.url : null;
    if (!chosen) return;
    try {
      const cleanupUrls = generated.filter((_, i) => i !== selectedIdx).map(g => g.url);
      const { data } = await axios.post(`${API}/avatar/save`, { avatar_url: chosen, cleanup_urls: cleanupUrls });
      if (onSave) onSave(data.avatar_url);
    } catch { toast.error('Save failed'); }
  };

  const selectedUrl = selectedIdx >= 0 ? generated[selectedIdx]?.url : null;
  const displayUrl = selectedUrl || photoPreview || currentAvatar || DEFAULT_AVATAR;
  const canGenerate = photoBase64 && genCount < MAX_GENERATIONS && !generating;
  const showingPhoto = !selectedUrl && photoPreview;

  return (
    <div className="flex flex-col items-center" data-testid="avatar-picker">
      {/* Zoom modal */}
      {zoomed && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm" onClick={() => setZoomed(null)} data-testid="avatar-zoom-modal">
          <div className="relative max-w-[85vw] max-h-[85vh]">
            <img src={zoomed} alt="Zoom" className="rounded-2xl max-w-full max-h-[85vh] object-contain" />
            <button onClick={() => setZoomed(null)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#1A1A1A] border border-white/10 flex items-center justify-center text-white">
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Avatar display area */}
      <div className="flex items-center justify-center gap-2 mb-3">
        {/* Left side thumbnails */}
        <div className="flex flex-col gap-1.5 items-center w-10">
          {generated.slice(0, 2).map((g, i) => (
            <button key={i} onClick={() => setSelectedIdx(i)} data-testid={`avatar-thumb-${i}`}
              className={`h-9 w-9 rounded-full overflow-hidden ring-2 transition-all shrink-0 ${selectedIdx === i ? 'ring-[#C9A84C] scale-110' : 'ring-white/10 opacity-50 hover:opacity-80'}`}>
              <img src={g.url} alt="" className="h-full w-full object-cover" />
            </button>
          ))}
        </div>

        {/* Main avatar */}
        <div className="relative group cursor-pointer" onClick={() => setZoomed(displayUrl)}>
          <div className={`${compact ? 'h-24 w-24' : 'h-32 w-32'} rounded-full overflow-hidden ring-2 ${showingPhoto ? 'ring-white/20' : 'ring-[#C9A84C]/30'} transition-all group-hover:ring-[#C9A84C]/60`} data-testid="avatar-main-preview">
            {generating ? (
              <div className="h-full w-full flex flex-col items-center justify-center bg-[#111] gap-1">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
                <span className="text-[8px] text-[#888]">{t.creating}</span>
              </div>
            ) : (
              <img src={displayUrl} alt="Avatar" className="h-full w-full object-cover" />
            )}
          </div>
          {!generating && (
            <div className="absolute inset-0 rounded-full flex items-center justify-center bg-black/0 group-hover:bg-black/30 transition-all">
              <ZoomIn size={16} className="text-white opacity-0 group-hover:opacity-70 transition-all" />
            </div>
          )}
          {selectedIdx >= 0 && (
            <div className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-emerald-500 flex items-center justify-center ring-2 ring-[#0A0A0A]">
              <Check size={10} className="text-white" />
            </div>
          )}
        </div>

        {/* Right side thumbnails */}
        <div className="flex flex-col gap-1.5 items-center w-10">
          {generated.slice(2, 4).map((g, i) => {
            const realIdx = i + 2;
            return (
              <button key={realIdx} onClick={() => setSelectedIdx(realIdx)} data-testid={`avatar-thumb-${realIdx}`}
                className={`h-9 w-9 rounded-full overflow-hidden ring-2 transition-all shrink-0 ${selectedIdx === realIdx ? 'ring-[#C9A84C] scale-110' : 'ring-white/10 opacity-50 hover:opacity-80'}`}>
                <img src={g.url} alt="" className="h-full w-full object-cover" />
              </button>
            );
          })}
        </div>
      </div>

      {/* Generation counter */}
      {genCount > 0 && (
        <p className="text-[9px] text-[#888] font-mono mb-2" data-testid="gen-counter">
          {genCount}/{MAX_GENERATIONS} {t.left}
        </p>
      )}

      {/* Camera view */}
      {cameraActive && (
        <div className="mb-3 w-full relative rounded-xl overflow-hidden border border-white/[0.06]">
          <video ref={videoRef} autoPlay playsInline muted className="w-full aspect-square object-cover" />
          <div className="absolute bottom-3 left-0 right-0 flex justify-center gap-3">
            <button onClick={capturePhoto} data-testid="capture-btn"
              className="h-14 w-14 rounded-full bg-white/90 flex items-center justify-center shadow-lg active:scale-95">
              <div className="h-12 w-12 rounded-full border-2 border-[#0A0A0A]" />
            </button>
            <button onClick={stopCamera} className="h-10 w-10 rounded-full bg-red-500/20 flex items-center justify-center text-red-400 self-end text-xs">X</button>
          </div>
        </div>
      )}
      <canvas ref={canvasRef} className="hidden" />

      {/* Action buttons */}
      {!cameraActive && (
        <div className="w-full space-y-2">
          {/* Selfie + Upload row */}
          {!photoPreview && (
            <div className="flex gap-2">
              <button onClick={startCamera} data-testid="camera-btn"
                className="flex-1 glass-card flex items-center justify-center gap-1.5 py-2.5 text-[11px] text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition">
                <Camera size={14} className="text-[#C9A84C]" /> {t.selfie}
              </button>
              <button onClick={() => fileInputRef.current?.click()} data-testid="upload-btn"
                className="flex-1 glass-card flex items-center justify-center gap-1.5 py-2.5 text-[11px] text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition">
                <Upload size={14} className="text-[#C9A84C]" /> {t.upload}
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleFile} />
            </div>
          )}

          {/* Photo loaded - Generate / Regenerate */}
          {photoPreview && (
            <>
              <div className="flex gap-2">
                {generated.length === 0 ? (
                  <button onClick={generate} disabled={!canGenerate} data-testid="generate-avatar-btn"
                    className="flex-1 btn-gold rounded-xl py-2.5 text-[11px] font-semibold flex items-center justify-center gap-1.5 disabled:opacity-40">
                    <Sparkles size={14} /> {t.generate}
                  </button>
                ) : (
                  <>
                    <button onClick={generate} disabled={!canGenerate} data-testid="regenerate-btn"
                      className="flex-1 glass-card flex items-center justify-center gap-1.5 py-2.5 text-[11px] text-[#B0B0B0] hover:text-white hover:border-[#C9A84C]/25 transition disabled:opacity-30">
                      <RotateCcw size={13} className="text-[#C9A84C]" /> {t.regen} ({MAX_GENERATIONS - genCount})
                    </button>
                    <button onClick={handleSave} disabled={selectedIdx < 0} data-testid="save-avatar-btn"
                      className="flex-1 btn-gold rounded-xl py-2.5 text-[11px] font-semibold flex items-center justify-center gap-1.5 disabled:opacity-40">
                      <Check size={14} /> {t.save}
                    </button>
                  </>
                )}
              </div>
              {/* Change photo */}
              <div className="flex gap-2">
                <button onClick={() => { setPhotoPreview(null); setPhotoBase64(null); setGenerated([]); setSelectedIdx(-1); setGenCount(0); }}
                  className="flex-1 text-[10px] text-[#666] hover:text-[#999] transition text-center py-1">
                  Change photo
                </button>
              </div>
            </>
          )}

          {/* Skip */}
          {onSkip && (
            <button onClick={onSkip} data-testid="skip-avatar-btn"
              className="w-full text-[10px] text-[#666] hover:text-[#C9A84C] transition text-center py-1">
              {t.skip}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
