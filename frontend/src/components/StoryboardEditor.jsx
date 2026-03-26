import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Image, MessageSquare, Send, RefreshCw, Check, X, Edit3, Save,
  Sparkles, ChevronRight, Maximize2, BookOpen, Wand2, Play, Download, Film, Mic, Paintbrush
} from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import { StoryboardPreview } from './StoryboardPreview';
import { VoiceInput } from './VoiceInput';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* Film reel spinning animation component */
const FilmSpinner = ({ size = 10, className = '' }) => (
  <Film size={size} className={`animate-spin ${className}`} style={{ animationDuration: '1.5s' }} />
);

export function StoryboardEditor({ projectId, scenes, characters, characterAvatars, lang, onApprove, onBack }) {
  const [panels, setPanels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generatingPanel, setGeneratingPanel] = useState(null);
  const [storyboardStatus, setStoryboardStatus] = useState({});
  const [editingPanel, setEditingPanel] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [approved, setApproved] = useState(false);
  const [expandedPanel, setExpandedPanel] = useState(null);

  // AI Facilitator
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Preview states
  const [showPreview, setShowPreview] = useState(false);
  const [exportingMp4, setExportingMp4] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewStatus, setPreviewStatus] = useState({});

  // Inpainting (Element Edit) states
  const [inpaintingPanel, setInpaintingPanel] = useState(null);
  const [inpaintPrompt, setInpaintPrompt] = useState('');
  const [inpaintLoading, setInpaintLoading] = useState(false);

  // Selected frame per panel (for gallery view)
  const [selectedFrames, setSelectedFrames] = useState({});
  const getSelectedFrame = (panelNum, frames) => {
    const idx = selectedFrames[panelNum] || 0;
    return frames?.[idx] || null;
  };
  const selectFrame = (panelNum, frameIdx) => {
    setSelectedFrames(prev => ({ ...prev, [panelNum]: frameIdx }));
  };

  // Load existing storyboard on mount
  useEffect(() => {
    if (projectId) loadStoryboard();
  }, [projectId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const loadStoryboard = async () => {
    try {
      const r = await axios.get(`${API}/studio/projects/${projectId}/storyboard`);
      setPanels(r.data.panels || []);
      setApproved(r.data.storyboard_approved || false);
      setChatMessages(r.data.storyboard_chat_history || []);
      setStoryboardStatus(r.data.storyboard_status || {});
    } catch {
      // No storyboard yet
    }
  };

  const generateStoryboard = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/generate-storyboard`);
      toast.success(lang === 'pt' ? 'Gerando storyboard...' : 'Generating storyboard...');
      pollStoryboard();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao gerar storyboard');
      setLoading(false);
    }
  };

  const pollStoryboard = () => {
    let attempts = 0;
    const poll = () => {
      attempts++;
      axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r => {
        const d = r.data;
        setPanels(d.panels || []);
        setStoryboardStatus(d.storyboard_status || {});

        if (d.storyboard_status?.phase === 'complete') {
          setLoading(false);
          const doneCount = (d.panels || []).filter(p => p.image_url).length;
          toast.success(lang === 'pt'
            ? `Storyboard pronto! ${doneCount} painéis gerados.`
            : `Storyboard ready! ${doneCount} panels generated.`);
          return;
        }
        if (d.storyboard_status?.phase === 'error' || attempts > 60) {
          setLoading(false);
          if ((d.panels || []).length > 0) {
            toast.info(lang === 'pt' ? 'Storyboard parcialmente gerado.' : 'Storyboard partially generated.');
          } else {
            toast.error(lang === 'pt' ? 'Erro ao gerar storyboard' : 'Storyboard generation failed');
          }
          return;
        }
        setTimeout(poll, 4000);
      }).catch(() => {
        if (attempts > 10) { setLoading(false); return; }
        setTimeout(poll, 5000);
      });
    };
    setTimeout(poll, 3000);
  };

  const regeneratePanel = async (panelNum) => {
    setGeneratingPanel(panelNum);
    try {
      const panel = panels.find(p => p.scene_number === panelNum);
      await axios.post(`${API}/studio/projects/${projectId}/storyboard/regenerate-panel`, {
        panel_number: panelNum,
        description: panel?.description || '',
      });
      toast.success(lang === 'pt' ? `Regenerando painel ${panelNum}...` : `Regenerating panel ${panelNum}...`);
      // Poll for this panel specifically
      const pollPanel = () => {
        axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r => {
          const updatedPanel = (r.data.panels || []).find(p => p.scene_number === panelNum);
          if (updatedPanel?.status === 'done' && updatedPanel?.image_url) {
            setPanels(r.data.panels);
            setGeneratingPanel(null);
            toast.success(lang === 'pt' ? `Painel ${panelNum} atualizado!` : `Panel ${panelNum} updated!`);
          } else if (updatedPanel?.status === 'error') {
            setPanels(r.data.panels);
            setGeneratingPanel(null);
            toast.error(lang === 'pt' ? `Erro no painel ${panelNum}` : `Panel ${panelNum} error`);
          } else {
            setTimeout(pollPanel, 3000);
          }
        }).catch(() => setTimeout(pollPanel, 4000));
      };
      setTimeout(pollPanel, 3000);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro');
      setGeneratingPanel(null);
    }
  };

  const saveEditPanel = async (panelNum) => {
    try {
      await axios.patch(`${API}/studio/projects/${projectId}/storyboard/edit-panel`, {
        panel_number: panelNum,
        ...editForm,
      });
      setPanels(prev => prev.map(p =>
        p.scene_number === panelNum ? { ...p, ...editForm } : p
      ));
      setEditingPanel(null);
      setEditForm({});
      toast.success(lang === 'pt' ? 'Painel atualizado!' : 'Panel updated!');
    } catch (err) {
      toast.error('Erro ao salvar');
    }
  };

  const approveStoryboard = async () => {
    try {
      await axios.patch(`${API}/studio/projects/${projectId}/storyboard/approve`, { approved: true });
      setApproved(true);
      toast.success(lang === 'pt' ? 'Storyboard aprovado!' : 'Storyboard approved!');
    } catch (err) {
      toast.error('Erro ao aprovar');
    }
  };

  // AI Facilitator chat
  const sendFacilitatorMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: msg }]);
    setChatLoading(true);
    try {
      const r = await axios.post(`${API}/studio/projects/${projectId}/storyboard/chat`, {
        message: msg,
      });
      const data = r.data;
      setChatMessages(prev => [...prev, { role: 'assistant', text: data.response }]);

      // Process actions
      if (data.actions?.length > 0) {
        for (const action of data.actions) {
          if (action.action === 'edit_text' && action.panel_number) {
            setPanels(prev => prev.map(p =>
              p.scene_number === action.panel_number
                ? { ...p, [action.field]: action.value }
                : p
            ));
          }
          if (action.action === 'regenerate_image' && action.panel_number) {
            regeneratePanel(action.panel_number);
          }
        }
      }

      // Refresh panels
      loadStoryboard();
    } catch (err) {
      setChatMessages(prev => [...prev, {
        role: 'assistant',
        text: lang === 'pt' ? 'Erro ao processar. Tente novamente.' : 'Error processing. Try again.'
      }]);
    }
    setChatLoading(false);
  };

  // Export MP4 with narration
  const exportMp4 = async () => {
    setExportingMp4(true);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/storyboard/generate-preview`, {
        voice_id: 'onwK4e9ZLuTAKqWW03F9', // Daniel
        music_track: 'cinematic',
      });
      toast.success(lang === 'pt' ? 'Gerando preview MP4 com narração...' : 'Generating MP4 preview with narration...');
      pollPreviewStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao exportar');
      setExportingMp4(false);
    }
  };

  const pollPreviewStatus = () => {
    let attempts = 0;
    const poll = () => {
      attempts++;
      axios.get(`${API}/studio/projects/${projectId}/storyboard/preview-status`).then(r => {
        const st = r.data.preview_status || {};
        setPreviewStatus(st);
        if (st.phase === 'complete' && r.data.preview_url) {
          setPreviewUrl(r.data.preview_url);
          setExportingMp4(false);
          toast.success(lang === 'pt' ? 'Preview MP4 pronto!' : 'MP4 Preview ready!');
          return;
        }
        if (st.phase === 'error' || attempts > 120) {
          setExportingMp4(false);
          toast.error(lang === 'pt' ? 'Erro ao gerar preview' : 'Preview generation failed');
          return;
        }
        setTimeout(poll, 4000);
      }).catch(() => {
        if (attempts > 10) { setExportingMp4(false); return; }
        setTimeout(poll, 5000);
      });
    };
    setTimeout(poll, 3000);
  };

  // Inpainting — edit specific element in panel
  const editElement = async (panelNum) => {
    if (!inpaintPrompt.trim() || inpaintLoading) return;
    setInpaintLoading(true);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/storyboard/edit-element`, {
        panel_number: panelNum,
        edit_instruction: inpaintPrompt.trim(),
      });
      if (res.data.status === 'editing') {
        toast.success(lang === 'pt' ? 'Editando elemento...' : 'Editing element...');
        // Poll for the updated panel
        const pollInpaint = () => {
          axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r => {
            const updatedPanel = (r.data.panels || []).find(p => p.scene_number === panelNum);
            if (updatedPanel?.status === 'done' && updatedPanel?.image_url !== panels.find(p => p.scene_number === panelNum)?.image_url) {
              setPanels(r.data.panels);
              setInpaintLoading(false);
              setInpaintingPanel(null);
              setInpaintPrompt('');
              toast.success(lang === 'pt' ? 'Elemento editado!' : 'Element edited!');
            } else if (updatedPanel?.status === 'error') {
              setPanels(r.data.panels);
              setInpaintLoading(false);
              toast.error(lang === 'pt' ? 'Erro ao editar' : 'Edit failed');
            } else {
              setTimeout(pollInpaint, 3000);
            }
          }).catch(() => setTimeout(pollInpaint, 4000));
        };
        setTimeout(pollInpaint, 3000);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro');
      setInpaintLoading(false);
    }
  };

  const doneCount = panels.filter(p => p.image_url).length;
  const totalPanels = panels.length || scenes.length;

  return (
    <div className="space-y-3" data-testid="storyboard-editor">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#8B6914] flex items-center justify-center">
            <BookOpen size={12} className="text-black" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-white">
              {lang === 'pt' ? 'Storyboard Editável' : 'Editable Storyboard'}
            </h3>
            <p className="text-[8px] text-[#666]">
              {lang === 'pt'
                ? 'Revise e edite cada painel antes de produzir os vídeos'
                : 'Review and edit each panel before producing videos'}
            </p>
          </div>
        </div>
        {panels.length > 0 && (
          <button onClick={() => setChatOpen(!chatOpen)} data-testid="toggle-facilitator-chat"
            className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[9px] font-medium transition ${
              chatOpen
                ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300'
                : 'bg-[#111] border border-[#333] text-[#888] hover:text-purple-300 hover:border-purple-500/30'
            }`}>
            <Wand2 size={10} />
            {lang === 'pt' ? 'Facilitador IA' : 'AI Facilitator'}
          </button>
        )}
      </div>

      {/* Generate button — show when no panels exist */}
      {panels.length === 0 && !loading && (
        <div className="text-center py-8 space-y-3">
          <div className="h-16 w-16 rounded-2xl bg-[#C9A84C]/10 border border-[#C9A84C]/20 flex items-center justify-center mx-auto">
            <Image size={24} className="text-[#C9A84C]" />
          </div>
          <p className="text-[10px] text-[#666] max-w-[280px] mx-auto">
            {lang === 'pt'
              ? 'Gere ilustrações para cada cena do roteiro. Você poderá editar textos, regenerar imagens e usar o Facilitador IA antes de produzir os vídeos.'
              : 'Generate illustrations for each scene. You can edit text, regenerate images and use the AI Facilitator before producing videos.'}
          </p>
          <button onClick={generateStoryboard} data-testid="generate-storyboard-btn"
            className="btn-gold rounded-xl px-6 py-2.5 text-[11px] font-bold flex items-center gap-2 mx-auto">
            <Sparkles size={14} />
            {lang === 'pt' ? `Gerar Storyboard (${scenes.length} painéis)` : `Generate Storyboard (${scenes.length} panels)`}
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-[9px]">
            <span className="text-[#999] flex items-center gap-1.5">
              <FilmSpinner size={10} className="text-[#C9A84C]" />
              {lang === 'pt'
                ? `Gerando painel ${storyboardStatus.current || '...'}/${storyboardStatus.total || totalPanels}`
                : `Generating panel ${storyboardStatus.current || '...'}/${storyboardStatus.total || totalPanels}`}
            </span>
            <span className="text-[#C9A84C] font-semibold">{doneCount}/{totalPanels}</span>
          </div>
          <div className="w-full bg-[#111] rounded-full h-1.5">
            <div className="h-1.5 rounded-full bg-[#C9A84C] transition-all duration-500"
              style={{ width: `${totalPanels > 0 ? (doneCount / totalPanels) * 100 : 0}%` }} />
          </div>
        </div>
      )}

      {/* Panels Grid */}
      {panels.length > 0 && (
        <div className="space-y-2">
          {/* Summary bar */}
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-[#666]">
              {doneCount}/{panels.length} {lang === 'pt' ? 'painéis prontos' : 'panels ready'}
            </span>
            {approved && (
              <span className="text-[8px] text-emerald-400 flex items-center gap-1">
                <Check size={10} /> {lang === 'pt' ? 'Aprovado' : 'Approved'}
              </span>
            )}
          </div>

          <div className="grid grid-cols-2 gap-2">
            {panels.map((panel) => {
              const isEditing = editingPanel === panel.scene_number;
              const isGenerating = generatingPanel === panel.scene_number;
              const isExpanded = expandedPanel === panel.scene_number;

              return (
                <div key={panel.scene_number}
                  data-testid={`storyboard-panel-${panel.scene_number}`}
                  className={`rounded-xl border overflow-hidden transition-all ${
                    isExpanded ? 'col-span-2' : ''
                  } ${
                    panel.status === 'error'
                      ? 'border-red-500/30 bg-red-500/5'
                      : panel.image_url
                        ? 'border-[#222] bg-[#0A0A0A] hover:border-[#C9A84C]/30'
                        : 'border-[#1A1A1A] bg-[#0A0A0A]'
                  }`}>
                  {/* Image area — Gallery view with filmstrip */}
                  <div className="relative bg-[#0A0A0A] overflow-hidden">
                    {/* Main display image */}
                    {panel.frames?.length > 1 && !isGenerating ? (() => {
                      const activeFrame = getSelectedFrame(panel.scene_number, panel.frames);
                      const activeIdx = selectedFrames[panel.scene_number] || 0;
                      return (
                        <div>
                          {/* Large main frame */}
                          <div className="relative aspect-video overflow-hidden bg-black">
                            <img
                              src={resolveImageUrl(activeFrame?.image_url || panel.image_url)}
                              alt={activeFrame?.label || panel.title}
                              className="w-full h-full object-cover"
                              data-testid={`panel-main-frame-${panel.scene_number}`}
                            />
                            {/* Scene number badge */}
                            <span className="absolute top-1 left-1 bg-black/80 text-[7px] text-[#C9A84C] font-bold px-1.5 py-0.5 rounded">
                              {panel.scene_number}
                            </span>
                            {/* Frame label badge */}
                            {activeFrame?.label && (
                              <span className="absolute top-1.5 right-1.5 bg-black/70 backdrop-blur-sm text-[7px] text-[#C9A84C] font-medium px-2 py-0.5 rounded-full">
                                {activeFrame.label}
                              </span>
                            )}
                          </div>

                          {/* Filmstrip — horizontal thumbnails */}
                          <div className="flex gap-[2px] bg-[#111] p-[2px]" data-testid={`panel-filmstrip-${panel.scene_number}`}>
                            {panel.frames.map((frame, fi) => (
                              <button
                                key={frame.frame_number}
                                onClick={() => selectFrame(panel.scene_number, fi)}
                                data-testid={`frame-thumb-${panel.scene_number}-${fi}`}
                                className={`relative flex-1 aspect-[16/10] overflow-hidden rounded-sm transition-all ${
                                  fi === activeIdx
                                    ? 'ring-1 ring-[#C9A84C] brightness-100'
                                    : 'brightness-50 hover:brightness-75'
                                }`}
                              >
                                <img
                                  src={resolveImageUrl(frame.image_url)}
                                  alt={frame.label}
                                  className="w-full h-full object-cover"
                                />
                                {fi === activeIdx && (
                                  <div className="absolute inset-x-0 bottom-0 h-[2px] bg-[#C9A84C]" />
                                )}
                              </button>
                            ))}
                          </div>

                          {/* Action toolbar — below filmstrip, always visible */}
                          <div className="flex items-center justify-between px-2 py-1 bg-[#0D0D0D] border-t border-[#1A1A1A]">
                            <div className="flex items-center gap-1">
                              <button onClick={() => setExpandedPanel(isExpanded ? null : panel.scene_number)}
                                data-testid={`expand-panel-${panel.scene_number}`}
                                className="h-6 w-6 rounded bg-[#1A1A1A] flex items-center justify-center text-[#888] hover:text-white hover:bg-[#222] transition" title={lang === 'pt' ? 'Expandir' : 'Expand'}>
                                <Maximize2 size={10} />
                              </button>
                              <button onClick={() => { setInpaintingPanel(inpaintingPanel === panel.scene_number ? null : panel.scene_number); setInpaintPrompt(''); }}
                                data-testid={`inpaint-panel-${panel.scene_number}`}
                                className={`h-6 w-6 rounded flex items-center justify-center transition ${
                                  inpaintingPanel === panel.scene_number
                                    ? 'bg-orange-500/20 text-orange-400'
                                    : 'bg-[#1A1A1A] text-orange-400/60 hover:text-orange-400 hover:bg-[#222]'
                                }`} title={lang === 'pt' ? 'Editar Elemento' : 'Edit Element'}>
                                <Paintbrush size={10} />
                              </button>
                              <button onClick={() => regeneratePanel(panel.scene_number)}
                                data-testid={`regen-panel-${panel.scene_number}`}
                                className="h-6 w-6 rounded bg-[#1A1A1A] flex items-center justify-center text-[#C9A84C]/60 hover:text-[#C9A84C] hover:bg-[#222] transition" title={lang === 'pt' ? 'Regenerar' : 'Regenerate'}>
                                <Film size={10} />
                              </button>
                            </div>
                            <span className="text-[7px] text-[#555]">
                              {panel.frames.length} frames
                            </span>
                          </div>
                        </div>
                      );
                    })() : panel.image_url && !isGenerating ? (
                      <div>
                        <div className="relative aspect-video">
                          <img src={resolveImageUrl(panel.image_url)} alt={panel.title}
                            className="w-full h-full object-cover" />
                          <span className="absolute top-1 left-1 bg-black/80 text-[7px] text-[#C9A84C] font-bold px-1.5 py-0.5 rounded">
                            {panel.scene_number}
                          </span>
                        </div>
                        {/* Action toolbar for single image */}
                        <div className="flex items-center gap-1 px-2 py-1 bg-[#0D0D0D] border-t border-[#1A1A1A]">
                          <button onClick={() => setExpandedPanel(isExpanded ? null : panel.scene_number)}
                            className="h-6 w-6 rounded bg-[#1A1A1A] flex items-center justify-center text-[#888] hover:text-white hover:bg-[#222] transition">
                            <Maximize2 size={10} />
                          </button>
                          <button onClick={() => { setInpaintingPanel(inpaintingPanel === panel.scene_number ? null : panel.scene_number); setInpaintPrompt(''); }}
                            data-testid={`inpaint-panel-single-${panel.scene_number}`}
                            className="h-6 w-6 rounded bg-[#1A1A1A] flex items-center justify-center text-orange-400/60 hover:text-orange-400 hover:bg-[#222] transition">
                            <Paintbrush size={10} />
                          </button>
                          <button onClick={() => regeneratePanel(panel.scene_number)}
                            className="h-6 w-6 rounded bg-[#1A1A1A] flex items-center justify-center text-[#C9A84C]/60 hover:text-[#C9A84C] hover:bg-[#222] transition">
                            <Film size={10} />
                          </button>
                        </div>
                      </div>
                    ) : isGenerating ? (
                      <div className="aspect-video flex flex-col items-center justify-center gap-2">
                        <FilmSpinner size={20} className="text-[#C9A84C]" />
                        <span className="text-[7px] text-[#666]">{lang === 'pt' ? 'Gerando 6 frames...' : 'Generating 6 frames...'}</span>
                      </div>
                    ) : (
                      <div className="aspect-video flex items-center justify-center">
                        <Image size={20} className="text-[#333]" />
                      </div>
                    )}
                  </div>

                  {/* Inpainting — Element edit UI */}
                  {inpaintingPanel === panel.scene_number && (
                    <div className="px-2 py-1.5 bg-orange-500/5 border-t border-orange-500/20 space-y-1.5">
                      <div className="flex items-center gap-1.5">
                        <Paintbrush size={10} className="text-orange-400 flex-shrink-0" />
                        <span className="text-[8px] text-orange-300 font-medium">
                          {lang === 'pt' ? 'Editar Elemento' : 'Edit Element'}
                        </span>
                      </div>
                      <div className="flex gap-1 items-center">
                        <input
                          value={inpaintPrompt}
                          onChange={e => setInpaintPrompt(e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && editElement(panel.scene_number)}
                          placeholder={lang === 'pt' ? 'Ex: Remover a corcova do Isaque' : 'Ex: Remove the hump from Isaac'}
                          data-testid={`inpaint-input-${panel.scene_number}`}
                          className="flex-1 bg-[#111] border border-orange-500/30 rounded px-2 py-1.5 text-[8px] text-white placeholder-[#555] outline-none focus:border-orange-500/50"
                          disabled={inpaintLoading}
                        />
                        <VoiceInput
                          onResult={text => setInpaintPrompt(prev => prev ? `${prev} ${text}` : text)}
                          lang={lang}
                          size={14}
                          className="h-7 w-7 rounded bg-orange-500/10 border border-orange-500/30 flex items-center justify-center text-orange-400 hover:bg-orange-500/20 transition flex-shrink-0"
                        />
                        <button
                          onClick={() => editElement(panel.scene_number)}
                          disabled={inpaintLoading || !inpaintPrompt.trim()}
                          data-testid={`inpaint-submit-${panel.scene_number}`}
                          className="rounded px-2.5 py-1.5 text-[8px] font-semibold bg-orange-500/20 border border-orange-500/30 text-orange-400 hover:bg-orange-500/30 transition disabled:opacity-30 flex items-center gap-1 flex-shrink-0"
                        >
                          {inpaintLoading ? <FilmSpinner size={8} className="text-orange-400" /> : <Paintbrush size={8} />}
                          {lang === 'pt' ? 'Editar' : 'Edit'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Text area */}
                  <div className="p-2 space-y-1">
                    {isEditing ? (
                      <div className="space-y-1.5">
                        <input value={editForm.title || ''} onChange={e => setEditForm(p => ({ ...p, title: e.target.value }))}
                          placeholder={lang === 'pt' ? 'Título' : 'Title'}
                          className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-[9px] text-white outline-none focus:border-[#C9A84C]" />
                        <textarea value={editForm.description || ''} onChange={e => setEditForm(p => ({ ...p, description: e.target.value }))}
                          placeholder={lang === 'pt' ? 'Descrição visual' : 'Visual description'}
                          rows={2} className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-[8px] text-white outline-none focus:border-[#C9A84C] resize-none" />
                        <textarea value={editForm.dialogue || ''} onChange={e => setEditForm(p => ({ ...p, dialogue: e.target.value }))}
                          placeholder={lang === 'pt' ? 'Diálogo/Narração' : 'Dialogue/Narration'}
                          rows={2} className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-[8px] text-white outline-none focus:border-[#C9A84C] resize-none" />
                        <div className="flex gap-1">
                          <button onClick={() => { setEditingPanel(null); setEditForm({}); }}
                            className="flex-1 rounded border border-[#333] py-1 text-[8px] text-[#999] hover:text-white transition">
                            {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                          </button>
                          <button onClick={() => saveEditPanel(panel.scene_number)}
                            className="flex-1 btn-gold rounded py-1 text-[8px] font-semibold">
                            {lang === 'pt' ? 'Salvar' : 'Save'}
                          </button>
                          <button onClick={() => { saveEditPanel(panel.scene_number); setTimeout(() => regeneratePanel(panel.scene_number), 500); }}
                            className="flex-1 rounded py-1 text-[8px] font-semibold bg-[#C9A84C]/20 border border-[#C9A84C]/30 text-[#C9A84C]">
                            {lang === 'pt' ? 'Salvar & Reger.' : 'Save & Regen'}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between">
                          <p className="text-[9px] font-semibold text-white truncate flex-1">{panel.title}</p>
                          <button onClick={() => {
                            setEditingPanel(panel.scene_number);
                            setEditForm({ title: panel.title, description: panel.description, dialogue: panel.dialogue });
                          }}
                            data-testid={`edit-panel-${panel.scene_number}`}
                            className="text-[#555] hover:text-[#C9A84C] transition ml-1">
                            <Edit3 size={10} />
                          </button>
                        </div>
                        {panel.dialogue && (
                          <p className="text-[8px] text-[#AAA] italic leading-relaxed line-clamp-3">
                            {panel.dialogue}
                          </p>
                        )}
                        {panel.characters_in_scene?.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-0.5">
                            {panel.characters_in_scene.map((c, ci) => (
                              <span key={ci} className="text-[6px] bg-[#C9A84C]/10 text-[#C9A84C] rounded px-1 py-0.5">{c}</span>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* AI Facilitator Chat */}
      {chatOpen && panels.length > 0 && (
        <div className="rounded-xl border border-purple-500/30 bg-[#0A0A0A] overflow-hidden" data-testid="facilitator-chat">
          <div className="px-3 py-2 bg-purple-500/10 border-b border-purple-500/20 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Wand2 size={12} className="text-purple-400" />
              <span className="text-[10px] font-semibold text-purple-300">
                {lang === 'pt' ? 'Facilitador IA' : 'AI Facilitator'}
              </span>
            </div>
            <button onClick={() => setChatOpen(false)} className="text-[#666] hover:text-white">
              <X size={12} />
            </button>
          </div>

          {/* Messages */}
          <div className="max-h-[200px] overflow-y-auto p-3 space-y-2 hide-scrollbar">
            {chatMessages.length === 0 && (
              <div className="text-center py-4">
                <p className="text-[9px] text-[#555]">
                  {lang === 'pt'
                    ? 'Diga o que quer mudar. Ex: "Mude o diálogo do painel 3" ou "Regenere a imagem da cena 5 com mais iluminação"'
                    : 'Tell me what to change. Ex: "Change panel 3 dialogue" or "Regenerate scene 5 image with more lighting"'}
                </p>
              </div>
            )}
            {chatMessages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[9px] leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-purple-500/15 text-purple-200 border border-purple-500/20'
                    : 'bg-[#111] text-[#ccc] border border-[#222]'
                }`}>
                  <pre className="whitespace-pre-wrap font-sans">{m.text}</pre>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-[#111] border border-[#222] rounded-lg px-3 py-2 flex items-center gap-2">
                  <FilmSpinner size={10} className="text-purple-400" />
                  <span className="text-[8px] text-[#666]">{lang === 'pt' ? 'Analisando...' : 'Analyzing...'}</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="p-2 border-t border-[#222] flex gap-2">
            <input value={chatInput} onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendFacilitatorMessage()}
              placeholder={lang === 'pt' ? 'Ex: Mude o diálogo do painel 3...' : 'Ex: Change panel 3 dialogue...'}
              data-testid="facilitator-chat-input"
              className="flex-1 bg-[#111] border border-[#333] rounded-lg px-3 py-1.5 text-[10px] text-white placeholder-[#555] outline-none focus:border-purple-500/40"
              disabled={chatLoading} />
            <VoiceInput
              onResult={text => setChatInput(prev => prev ? `${prev} ${text}` : text)}
              lang={lang}
              size={12}
              className="h-8 w-8"
            />
            <button onClick={sendFacilitatorMessage} disabled={chatLoading || !chatInput.trim()}
              data-testid="facilitator-send-btn"
              className="rounded-lg px-3 py-1.5 bg-purple-500/20 border border-purple-500/40 text-purple-300 hover:bg-purple-500/30 transition disabled:opacity-30">
              <Send size={12} />
            </button>
          </div>
        </div>
      )}

      {/* Preview & Export buttons */}
      {panels.length > 0 && doneCount > 0 && !loading && (
        <div className="flex gap-2">
          <button onClick={() => setShowPreview(true)} data-testid="open-preview-btn"
            className="flex-1 rounded-lg py-2 text-[10px] font-semibold transition-all
              bg-blue-500/10 border border-blue-500/30 text-blue-400 hover:bg-blue-500/20
              flex items-center justify-center gap-1.5">
            <Play size={12} />
            {lang === 'pt' ? 'Preview Animado' : 'Animated Preview'}
          </button>
          <button onClick={exportMp4} disabled={exportingMp4} data-testid="export-mp4-btn"
            className="flex-1 rounded-lg py-2 text-[10px] font-semibold transition-all
              bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20
              flex items-center justify-center gap-1.5 disabled:opacity-40">
            {exportingMp4 ? (
              <>
                <FilmSpinner size={10} className="text-purple-400" />
                {previewStatus.phase === 'narrating'
                  ? `${lang === 'pt' ? 'Narrando' : 'Narrating'} ${previewStatus.current || ''}/${previewStatus.total || ''}`
                  : previewStatus.phase === 'rendering'
                    ? `${lang === 'pt' ? 'Renderizando' : 'Rendering'} ${previewStatus.current || ''}/${previewStatus.total || ''}`
                    : previewStatus.phase === 'concatenating' || previewStatus.phase === 'mixing_music'
                      ? (lang === 'pt' ? 'Mixando...' : 'Mixing...')
                      : (lang === 'pt' ? 'Exportando...' : 'Exporting...')
                }
              </>
            ) : (
              <>
                <Film size={12} />
                {lang === 'pt' ? 'Exportar MP4 + Narração' : 'Export MP4 + Narration'}
              </>
            )}
          </button>
          {previewUrl && !exportingMp4 && (
            <a href={resolveImageUrl(previewUrl)} target="_blank" rel="noopener noreferrer"
              data-testid="download-preview-btn"
              className="rounded-lg py-2 px-3 text-[10px] font-semibold transition-all
                bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20
                flex items-center justify-center gap-1.5">
              <Download size={12} />
              MP4
            </a>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        <button onClick={onBack}
          className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
          {lang === 'pt' ? '← Personagens' : '← Characters'}
        </button>
        {panels.length > 0 && !loading && (
          <>
            <button onClick={generateStoryboard} data-testid="regenerate-all-storyboard"
              className="rounded-lg border border-[#333] py-2 px-3 text-[10px] text-[#999] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition flex items-center gap-1">
              <RefreshCw size={10} />
              {lang === 'pt' ? 'Reger. Tudo' : 'Regen All'}
            </button>
            {!approved ? (
              <button onClick={approveStoryboard} data-testid="approve-storyboard-btn"
                disabled={doneCount === 0}
                className="flex-1 rounded-lg py-2 text-[10px] font-bold transition-all
                  bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20
                  flex items-center justify-center gap-1.5 disabled:opacity-30">
                <Check size={12} />
                {lang === 'pt' ? 'Aprovar Storyboard' : 'Approve Storyboard'}
              </button>
            ) : (
              <button onClick={onApprove} data-testid="proceed-to-production-btn"
                className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-bold flex items-center justify-center gap-1.5">
                {lang === 'pt' ? 'Produzir Vídeos' : 'Produce Videos'} <ChevronRight size={12} />
              </button>
            )}
          </>
        )}
      </div>

      {/* Fullscreen Preview Overlay — Portal to body */}
      {showPreview && createPortal(
        <div className="fixed inset-0 z-[9999] bg-black flex items-center justify-center p-4" data-testid="preview-overlay">
          <div className="w-full max-w-4xl">
            <StoryboardPreview
              panels={panels}
              lang={lang}
              onClose={() => setShowPreview(false)}
            />
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}
