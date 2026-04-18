import { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Image, MessageSquare, Send, RefreshCw, Check, X, Edit3, Save,
  Sparkles, ChevronRight, ChevronDown, ChevronUp, ChevronLeft, BookOpen, Wand2, Play, Download, Film, Mic, Paintbrush,
  Languages, ScanSearch, Zap, Globe, Shield, AlertTriangle, CheckCircle, PenTool, GripVertical, Clock, Copy
} from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import { getErrorMsg } from '../utils/getErrorMsg';
import { StoryboardPreview } from './StoryboardPreview';
import { VoiceInput } from './VoiceInput';
import { preloadImages, useImagePreloader } from '../hooks/useProjectCache';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  SortableContext,
  rectSortingStrategy,
  useSortable,
  arrayMove,
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* Film reel spinning animation component */
const FilmSpinner = ({ size = 10, className = '' }) => (
  <Film size={size} className={`animate-spin ${className}`} style={{ animationDuration: '1.5s' }} />
);

/* ══════════════════════════════════════════════════════════════
   SORTABLE PANEL WRAPPER - iPhone-style drag and drop
   ══════════════════════════════════════════════════════════════ */
function SortablePanel({ id, children }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div ref={setNodeRef} style={style}>
      {children({ dragHandleProps: { ...attributes, ...listeners } })}
    </div>
  );
}

export function StoryboardEditor({ projectId, scenes, characters, characterAvatars, lang, videoEngine, onApprove, onBack, onScenesReordered }) {
  const [panels, setPanels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generatingPanel, setGeneratingPanel] = useState(null);
  const [storyboardStatus, setStoryboardStatus] = useState({});
  const [editingPanel, setEditingPanel] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [approved, setApproved] = useState(false);
  
  // NOVO: Kling storyboards (30 frames)
  const [klingStoryboards, setKlingStoryboards] = useState(null);
  const [useKlingMode, setUseKlingMode] = useState(false);
  const [klingGenerating, setKlingGenerating] = useState(false);
  
  // NOVO: Zoom modal for frame details
  const [zoomFrame, setZoomFrame] = useState(null);
  const [zoomFrameIndex, setZoomFrameIndex] = useState(null);
  
  // NOVO: Inline editing state for zoom modal
  const [zoomEditing, setZoomEditing] = useState(false);
  const [zoomEditData, setZoomEditData] = useState({});
  const [zoomSaving, setZoomSaving] = useState(false);
  const [regenInstruction, setRegenInstruction] = useState('');
  
  // NOVO: Estado para travar regenerações simultâneas
  const [isRegenerating, setIsRegenerating] = useState(false);
  
  // NOVO: Confirmation state for 2-click confirmation (no popup)
  const [confirmRegenerateAll, setConfirmRegenerateAll] = useState(false);
  const [confirmRegenerateFrame, setConfirmRegenerateFrame] = useState(null); // frameNumber or null
  
  // NOVO: Progress tracking for regeneration
  const [regenerationProgress, setRegenerationProgress] = useState({}); // {frameNumber: percentage}
  
  // NOVO: Modal de confirmação customizado (necessário pois sandbox bloqueia window.confirm)
  const [confirmModal, setConfirmModal] = useState(null);
  
  // NOVO: Multi-select regeneration states
  const [selectedPanels, setSelectedPanels] = useState(new Set());
  const [regeneratingPanels, setRegeneratingPanels] = useState(new Map());
  const [isMultiSelectMode, setIsMultiSelectMode] = useState(false);
  
  // Flag to prevent reloading during drag operation
  const isDraggingRef = useRef(false);
  const [reorderedFrames, setReorderedFrames] = useState(null); // null = original order, array = reordered
  const [savingOrder, setSavingOrder] = useState(false);
  
  // Use Kling frames if available, otherwise regular panels. If reordered, use that.
  const rawFrames = useKlingMode && klingStoryboards 
    ? (klingStoryboards.scenes || []).flatMap(scene => scene.frames || [])
    : panels.map(p => ({ ...p, _original_scene: p.scene_number }));
  const displayFrames = reorderedFrames || rawFrames;
  
  // Reset reordered when raw data changes
  useEffect(() => { setReorderedFrames(null); }, [panels.length, klingStoryboards]);
  
  // DnD sensors
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );
  
  const handleDragEnd = (event) => {
    isDraggingRef.current = false;
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    
    const oldIdx = displayFrames.findIndex((_, i) => `frame-${i}` === active.id);
    const newIdx = displayFrames.findIndex((_, i) => `frame-${i}` === over.id);
    if (oldIdx < 0 || newIdx < 0) return;
    
    const newOrder = arrayMove([...displayFrames], oldIdx, newIdx);
    // Renumber scene_number / frame_number
    newOrder.forEach((frame, i) => {
      if (useKlingMode) {
        frame.frame_number = i + 1;
      } else {
        frame.scene_number = i + 1;
      }
    });
    setReorderedFrames(newOrder);
  };
  
  const saveReorderedScenes = async () => {
    if (!reorderedFrames) return;
    setSavingOrder(true);
    try {
      // Build the new order: list of original scene_numbers in their new positions
      const order = reorderedFrames.map(f => f._original_scene || f.scene_number);
      await axios.post(`${API}/studio/projects/${projectId}/reorder-scenes`, { order });
      // Update panels locally with new scene numbers
      setPanels(reorderedFrames.map((f, i) => ({ ...f, scene_number: i + 1 })));
      setReorderedFrames(null);
      if (onScenesReordered) onScenesReordered(reorderedFrames);
      toast.success(lang === 'pt' ? 'Ordem salva!' : 'Order saved!');
    } catch (err) {
      toast.error(`Erro: ${err.response?.data?.detail || err.message}`);
    } finally {
      setSavingOrder(false);
    }
  };
  
  console.log('📦 StoryboardEditor - panels:', panels.length, 'kling frames:', klingStoryboards?.total_frames || 0, 'useKlingMode:', useKlingMode, 'projectId:', projectId);

  // AI Facilitator
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Preview states
  const [showPreview, setShowPreview] = useState(false);
  const [syncingPanels, setSyncingPanels] = useState(false);
  const [exportingMp4, setExportingMp4] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewStatus, setPreviewStatus] = useState({});

  // Inpainting (Element Edit) states
  const [inpaintingPanel, setInpaintingPanel] = useState(null);
  const [inpaintPrompt, setInpaintPrompt] = useState('');
  const [inpaintLoading, setInpaintLoading] = useState(false);

  // Selected frame per panel (for gallery view)
  const [selectedFrames, setSelectedFrames] = useState({});
  // Book export states
  const [generatingCover, setGeneratingCover] = useState(false);
  const [bookCover, setBookCover] = useState(null);
  const [bookTitle, setBookTitle] = useState('');
  const [exportingPdf, setExportingPdf] = useState(false);
  // Language Agent states
  const [targetLang, setTargetLang] = useState('en');
  const [converting, setConverting] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [reviewResult, setReviewResult] = useState(null);
  // Smart Editor states
  const [smartMode, setSmartMode] = useState(true);
  const [analyzing, setAnalyzing] = useState(null);
  const [sceneAnalysis, setSceneAnalysis] = useState({});
  // Continuity Director states
  const [continuityRunning, setContinuityRunning] = useState(false);
  const [continuityStatus, setContinuityStatus] = useState({});
  const [continuityReport, setContinuityReport] = useState(null);
  const [correcting, setCorrecting] = useState(false);
  const [continuityNotes, setContinuityNotes] = useState('');
  // Expandable panels — collapsed by default for performance
  const [selectedPanelForView, setSelectedPanelForView] = useState(null); // For viewing expanded
  const [selectedFrameIndex, setSelectedFrameIndex] = useState(0); // For frame navigation
  
  const [expandedPanels, setExpandedPanels] = useState(new Set());
  const togglePanel = (sceneNum) => {
    setExpandedPanels(prev => {
      const next = new Set(prev);
      if (next.has(sceneNum)) next.delete(sceneNum);
      else next.add(sceneNum);
      return next;
    });
  };
  const expandAll = () => setExpandedPanels(new Set(panels.map(p => p.scene_number)));
  const collapseAll = () => setExpandedPanels(new Set());
  const getSelectedFrame = (panelNum, frames) => {
    const idx = selectedFrames[panelNum] || 0;
    return frames?.[idx] || null;
  };
  const selectFrame = (panelNum, frameIdx) => {
    setSelectedFrames(prev => ({ ...prev, [panelNum]: frameIdx }));
  };

  // ══════════════════════════════════════════════════════════════
  // DRAG AND DROP - iPhone style (long press to activate)
  // ══════════════════════════════════════════════════════════════
  const [reordering, setReordering] = useState(false);
  
  // Old DnD handlers removed — using new implementation above

  // Load existing storyboard on mount
  useEffect(() => {
    if (projectId && !isDraggingRef.current) {
      console.log('📥 Loading storyboard for project:', projectId);
      loadStoryboard();
    }
  }, [projectId]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Auto-poll when Kling generation is in progress (handles page refresh during generation)
  useEffect(() => {
    if (!klingGenerating || !projectId) return;
    
    console.log('⏳ Starting auto-poll for Kling generation...');
    setLoading(true);
    setIsRegenerating(true);
    
    const pollInterval = setInterval(async () => {
      try {
        const checkRes = await axios.get(`${API}/studio/projects/${projectId}/kling-storyboards`);
        const status = checkRes.data.generation_status || {};
        
        // ✅ Always update storyboard data during generation (show frames progressively)
        if (checkRes.data.has_storyboards && checkRes.data.total_frames > 0) {
          setKlingStoryboards({
            scenes: checkRes.data.scenes || [],
            total_frames: checkRes.data.total_frames,
            generated_at: checkRes.data.generated_at,
          });
          
          // Count frames with images
          const allFrames = (checkRes.data.scenes || []).flatMap(s => s.frames || []);
          const framesWithImage = allFrames.filter(f => f.image_url).length;
          console.log(`⏳ Kling progress: ${framesWithImage}/${allFrames.length} frames with images`);
        }
        
        if (checkRes.data.has_storyboards && checkRes.data.total_frames > 0 && status.phase !== 'generating') {
          clearInterval(pollInterval);
          setKlingGenerating(false);
          console.log(`✅ Kling generation complete: ${checkRes.data.total_frames} frames`);
          toast.success(lang === 'pt' ? `${checkRes.data.total_frames} frames gerados com sucesso!` : `${checkRes.data.total_frames} frames generated!`);
          await loadStoryboard();
          setLoading(false);
          setIsRegenerating(false);
        } else if (status.phase === 'error') {
          clearInterval(pollInterval);
          setKlingGenerating(false);
          toast.error(lang === 'pt' ? `Erro na geração: ${status.error}` : `Error: ${status.error}`);
          setLoading(false);
          setIsRegenerating(false);
        }
      } catch (err) {
        console.error('Auto-poll error:', err);
      }
    }, 5000); // Check every 5s for progressive loading
    
    return () => clearInterval(pollInterval);
  }, [klingGenerating, projectId]);

  // ✅ NEW: Continuous polling when panels are generating
  useEffect(() => {
    if (!projectId) return;
    
    const hasGeneratingPanels = panels.some(p => p.status === 'generating');
    if (!hasGeneratingPanels) return;
    
    // Poll every 2 seconds while generating
    const pollInterval = setInterval(async () => {
      try {
        const r = await axios.get(`${API}/studio/projects/${projectId}/storyboard/progress`);
        const { progress, panels: newPanels } = r.data;
        
        const sortedPanels = (newPanels || []).sort((a, b) => a.panel_number - b.panel_number);
        setPanels(sortedPanels);
        setStoryboardStatus(progress || {});
        
        console.log(`🎨 [Polling] ${sortedPanels.filter(p => p.status === 'done').length}/${sortedPanels.length} done`);
        
        // Stop polling if all done
        const allDone = sortedPanels.every(p => p.status === 'done' || p.status === 'error');
        if (allDone) {
          const doneCount = sortedPanels.filter(p => p.status === 'done').length;
          toast.success(lang === 'pt'
            ? `✅ Storyboard completo! ${doneCount}/${sortedPanels.length} painéis gerados.`
            : `✅ Storyboard complete! ${doneCount}/${sortedPanels.length} panels generated.`
          );
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000);
    
    return () => clearInterval(pollInterval);
  }, [projectId, panels, lang]);

  // Zoom modal functions
  const openZoomModal = (frame, index) => {
    setZoomFrame(frame);
    setZoomFrameIndex(index);
    setZoomEditing(false);
    setZoomEditData({});
  };

  const closeZoomModal = () => {
    setZoomFrame(null);
    setZoomFrameIndex(null);
    setZoomEditing(false);
    setZoomEditData({});
    setRegenInstruction('');
  };

  const navigateFrame = (direction) => {
    if (zoomFrameIndex === null) return;
    const newIndex = direction === 'next' 
      ? Math.min(zoomFrameIndex + 1, displayFrames.length - 1)
      : Math.max(zoomFrameIndex - 1, 0);
    setZoomFrame(displayFrames[newIndex]);
    setZoomFrameIndex(newIndex);
    setZoomEditing(false);
    setZoomEditData({});
  };

  const startZoomEdit = () => {
    setZoomEditing(true);
    if (useKlingMode) {
      setZoomEditData({
        image_prompt: zoomFrame.image_prompt || '',
        kling_prompt: zoomFrame.kling_prompt || '',
        dialogue_text: zoomFrame.dialogue_text || '',
      });
    } else {
      const matchedScene = scenes.find(s => s.scene_number === zoomFrame.scene_number) || {};
      setZoomEditData({
        dialogue: matchedScene.dubbed_text || matchedScene.dialogue || '',
        description: matchedScene.description || '',
        title: matchedScene.title || '',
      });
    }
  };

  const saveZoomEdit = async () => {
    if (!zoomFrame || !zoomEditData) return;
    setZoomSaving(true);
    try {
      if (useKlingMode) {
        await axios.patch(`${API}/studio/projects/${projectId}/kling-storyboards/update-frame`, {
          frame_number: zoomFrame.frame_number,
          ...zoomEditData,
        });
        const updatedFrame = { ...zoomFrame, ...zoomEditData };
        setZoomFrame(updatedFrame);
        setKlingStoryboards(prev => {
          if (!prev) return prev;
          return {
            ...prev,
            scenes: prev.scenes.map(scene => ({
              ...scene,
              frames: scene.frames.map(f =>
                f.frame_number === zoomFrame.frame_number ? { ...f, ...zoomEditData } : f
              )
            }))
          };
        });
      } else {
        await axios.patch(`${API}/studio/projects/${projectId}/scenes/${zoomFrame.scene_number}`, {
          dialogue: zoomEditData.dialogue,
          dubbed_text: zoomEditData.dialogue,
          description: zoomEditData.description,
          title: zoomEditData.title,
        });
        setScenes(prev => prev.map(s =>
          s.scene_number === zoomFrame.scene_number
            ? { ...s, dialogue: zoomEditData.dialogue, dubbed_text: zoomEditData.dialogue, description: zoomEditData.description, title: zoomEditData.title }
            : s
        ));
      }
      setZoomEditing(false);
      toast.success(lang === 'pt' ? 'Salvo!' : 'Saved!');
    } catch (err) {
      toast.error(getErrorMsg(err, lang === 'pt' ? 'Erro ao salvar' : 'Save failed'));
    } finally {
      setZoomSaving(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success(lang === 'pt' ? 'Prompt copiado!' : 'Prompt copied!');
  };

  // Keyboard navigation
  useEffect(() => {
    if (!zoomFrame) return;
    
    const handleKeyPress = (e) => {
      if (e.key === 'Escape') closeZoomModal();
      if (e.key === 'ArrowLeft') navigateFrame('prev');
      if (e.key === 'ArrowRight') navigateFrame('next');
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [zoomFrame, zoomFrameIndex]);

  const loadStoryboard = async () => {
    try {
      // PIPELINE SEPARATION: Kling uses 30-frame storyboards, Sora 2 uses scene panels
      if (videoEngine === 'kling') {
        // Try loading Kling storyboards (30 frames)
        try {
          const klingRes = await axios.get(`${API}/studio/projects/${projectId}/kling-storyboards`);
          const genStatus = klingRes.data.generation_status || {};
          
          if (genStatus.phase === 'generating') {
            setKlingGenerating(true);
            setUseKlingMode(true);
            console.log('⏳ Kling generation in progress, polling...');
            return;
          }
          
          setKlingGenerating(false);
          
          if (klingRes.data.has_storyboards && klingRes.data.total_frames > 0) {
            const timestamp = Date.now();
            const storyboardsWithCacheBusting = {
              ...klingRes.data,
              scenes: klingRes.data.scenes.map(scene => ({
                ...scene,
                frames: scene.frames.map(frame => ({
                  ...frame,
                  image_url: frame.image_url ? `${frame.image_url}?t=${timestamp}` : frame.image_url
                }))
              }))
            };
            
            setKlingStoryboards(storyboardsWithCacheBusting);
            setUseKlingMode(true);
            console.log('✅ Loaded Kling storyboards:', klingRes.data.total_frames, 'frames');
            return;
          }
        } catch (err) {
          console.log('No Kling storyboards yet');
        }
      }
      
      // Sora 2 mode OR fallback: load regular storyboard panels (scene-based)
      const r = await axios.get(`${API}/studio/projects/${projectId}/storyboard`);
      const loadedPanels = r.data.panels || [];
      setPanels(loadedPanels);
      setApproved(r.data.storyboard_approved || false);
      setChatMessages(r.data.storyboard_chat_history || []);
      setStoryboardStatus(r.data.storyboard_status || {});
      setUseKlingMode(false);
      
      const allUrls = loadedPanels.flatMap(p =>
        (p.frames || []).map(f => f.image_url).filter(Boolean).map(resolveImageUrl)
      );
      preloadImages(allUrls);
    } catch {
      // No storyboard yet
    }
  };

  const generateStoryboard = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/generate-storyboard`);
      toast.success(lang === 'pt' ? 'Criando estrutura de painéis...' : 'Creating panel structure...');
      
      // Start polling with new progress endpoint
      pollStoryboardProgress();
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao gerar storyboard'));
      setLoading(false);
    }
  };

  // Direct generation (no confirmation needed for initial generation)
  const generateAllFramesDirect = async () => {
    console.log('🔄 generateAllFramesDirect called (no confirmation)');
    if (isRegenerating) {
      toast.warning(lang === 'pt' ? 'Aguarde a regeneração atual terminar' : 'Wait for current regeneration to finish');
      return;
    }
    setLoading(true);
    setIsRegenerating(true);
    try {
      console.log('🔄 Generating new storyboards...');
      const generateResponse = await axios.post(`${API}/studio/projects/${projectId}/kling-storyboards/generate`, {
        scene_id: null
      });
      console.log('✅ Generate response:', generateResponse.status, generateResponse.data);
      toast.success(lang === 'pt' ? 'Gerando 30 frames... Isso pode levar 3-5 minutos. Aguarde.' : 'Generating 30 frames... This may take 3-5 minutes. Please wait.');
      _pollStoryboardCompletion();
    } catch (err) {
      console.error('❌ Error generating:', err);
      toast.error(getErrorMsg(err, 'Erro ao gerar storyboard'));
      setLoading(false);
      setIsRegenerating(false);
    }
  };

  // Shared polling logic for storyboard completion
  const _pollStoryboardCompletion = () => {
    let attempts = 0;
    const maxAttempts = 40;
    const checkCompletion = setInterval(async () => {
      attempts++;
      console.log(`🔍 Polling progress... attempt ${attempts}/${maxAttempts}`);
      try {
        const checkRes = await axios.get(`${API}/studio/projects/${projectId}/kling-storyboards`);
        const status = checkRes.data.generation_status || {};
        if (checkRes.data.has_storyboards && checkRes.data.total_frames > 0 && status.phase !== 'generating') {
          clearInterval(checkCompletion);
          console.log(`✅ Generation complete! ${checkRes.data.total_frames} frames`);
          toast.success(lang === 'pt' ? `${checkRes.data.total_frames} frames gerados com sucesso!` : `${checkRes.data.total_frames} frames generated successfully!`);
          await loadStoryboard();
          setLoading(false);
          setIsRegenerating(false);
        } else if (status.phase === 'error') {
          clearInterval(checkCompletion);
          toast.error(lang === 'pt' ? `Erro na geração: ${status.error || 'Unknown'}` : `Generation error: ${status.error || 'Unknown'}`);
          setLoading(false);
          setIsRegenerating(false);
        } else if (attempts >= maxAttempts) {
          clearInterval(checkCompletion);
          toast.warning(lang === 'pt' ? 'Geração está demorando. Recarregue a página em alguns minutos.' : 'Generation is taking longer. Reload page in a few minutes.');
          setLoading(false);
          setIsRegenerating(false);
        } else if (attempts % 2 === 0) {
          toast.info(lang === 'pt' ? `Gerando... (verificação ${attempts})` : `Generating... (check ${attempts})`, { duration: 3000 });
        }
      } catch (err) {
        console.error('Error checking completion:', err);
      }
    }, 15000);
  };

  const regenerateAllFrames = async () => {
    console.log('🔄 regenerateAllFrames called');
    
    // BLOQUEIO: Não permitir regeneração simultânea
    if (isRegenerating) {
      toast.warning(lang === 'pt' ? 'Aguarde a regeneração atual terminar' : 'Wait for current regeneration to finish');
      return;
    }
    
    // 2-CLICK INLINE CONFIRMATION
    if (confirmRegenerateAll) {
      console.log('🔄 2nd click - executing bulk regeneration');
      setConfirmRegenerateAll(false);
      setLoading(true);
      setIsRegenerating(true);
      
      try {
        console.log('🔄 Deleting existing storyboards...');
        const deleteResponse = await axios.delete(`${API}/studio/projects/${projectId}/kling-storyboards`);
        console.log('✅ Delete response:', deleteResponse.status, deleteResponse.data);
        
        console.log('🔄 Generating new storyboards...');
        const generateResponse = await axios.post(`${API}/studio/projects/${projectId}/kling-storyboards/generate`, {
          scene_id: null  // Generate for all scenes / create virtual 5-min scene
        });
        console.log('✅ Generate response:', generateResponse.status, generateResponse.data);
        
        // Backend runs generation in background — POST returns immediately
        // Now poll for completion
        toast.success(lang === 'pt' ? 'Gerando 30 frames... Isso pode levar 3-5 minutos. Aguarde.' : 'Generating 30 frames... This may take 3-5 minutes. Please wait.');
        _pollStoryboardCompletion();
        
      } catch (err) {
        console.error('❌ Error regenerating:', err);
        console.error('❌ Error details:', err.response?.data);
        console.error('❌ Error status:', err.response?.status);
        toast.error(getErrorMsg(err, 'Erro ao regenerar frames'));
        setLoading(false);
        setIsRegenerating(false);
      }
    } else {
      // 1º CLICK: Ativar confirmação
      console.log('🔄 1st click - asking for confirmation');
      setConfirmRegenerateAll(true);
      
      // Auto-cancelar após 4 segundos
      setTimeout(() => {
        setConfirmRegenerateAll(false);
      }, 4000);
    }
  };

  const regenerateKlingFrame = async (frameNumber) => {
    console.log('🔄 regenerateKlingFrame called for frame:', frameNumber);
    
    // BLOQUEIO: Não permitir regeneração se já estiver regenerando todos
    if (isRegenerating) {
      toast.warning(lang === 'pt' ? 'Aguarde a regeneração em andamento' : 'Wait for regeneration in progress');
      return;
    }
    
    // 2-CLICK INLINE CONFIRMATION: Se já está no estado de confirmação, executar
    if (confirmRegenerateFrame === frameNumber) {
      console.log('🔄 2nd click - executing regeneration for frame:', frameNumber);
      setConfirmRegenerateFrame(null); // Reset confirmation state
      
      try {
        console.log('🔄 Calling API to regenerate frame', frameNumber);
        toast.info(lang === 'pt' ? `Regenerando frame ${frameNumber}...` : `Regenerating frame ${frameNumber}...`);
        
        // Simular progresso: 0% → 100% em 30 segundos
        setRegenerationProgress(prev => ({ ...prev, [frameNumber]: 0 }));
        const progressInterval = setInterval(() => {
          setRegenerationProgress(prev => {
            const current = prev[frameNumber] || 0;
            if (current >= 100) {
              clearInterval(progressInterval);
              return prev;
            }
            return { ...prev, [frameNumber]: Math.min(current + 3, 100) }; // +3% a cada 1s = ~33s total
          });
        }, 1000);
        
        await axios.post(`${API}/studio/projects/${projectId}/kling-storyboards/regenerate-frame`, {
          frame_number: frameNumber
        });
        
        clearInterval(progressInterval);
        setRegenerationProgress(prev => ({ ...prev, [frameNumber]: 100 }));
        
        toast.success(lang === 'pt' ? 'Frame regenerado!' : 'Frame regenerated!');
        
        // Aguardar 1s e recarregar com cache-busting
        setTimeout(() => {
          setRegenerationProgress(prev => {
            const newProgress = { ...prev };
            delete newProgress[frameNumber];
            return newProgress;
          });
          loadStoryboard();
        }, 1000);
      } catch (err) {
        console.error('❌ Error regenerating frame:', err);
        setRegenerationProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[frameNumber];
          return newProgress;
        });
        toast.error(getErrorMsg(err, 'Erro ao regenerar frame'));
      }
    } else {
      // 1º CLICK: Ativar estado de confirmação
      console.log('🔄 1st click - asking for confirmation for frame:', frameNumber);
      setConfirmRegenerateFrame(frameNumber);
      
      // Auto-cancelar após 3 segundos se não clicar novamente
      setTimeout(() => {
        setConfirmRegenerateFrame(prev => prev === frameNumber ? null : prev);
      }, 3000);
    }
  };

  const pollStoryboardProgress = () => {
    let attempts = 0;
    const maxAttempts = 120; // 120 * 3s = 6 minutes max
    
    const poll = () => {
      attempts++;
      
      axios.get(`${API}/studio/projects/${projectId}/storyboard/progress`).then(r => {
        const { in_progress, progress, panels: newPanels } = r.data;
        
        // Sort panels by panel_number to ensure chronological order
        const sortedPanels = (newPanels || []).sort((a, b) => a.panel_number - b.panel_number);
        
        // 🐛 DEBUG: Log progress updates
        console.log(`🎨 [Storyboard Poll] Attempt ${attempts}:`, {
          status: progress?.status,
          phase: progress?.phase,
          completed: progress?.completed,
          total: progress?.total,
          panelsReady: sortedPanels.filter(p => p.status === 'done').length
        });
        
        setPanels(sortedPanels);
        setStoryboardStatus(progress || {});
        
        // Check if complete
        if (!in_progress || progress?.status === 'complete') {
          setLoading(false);
          const doneCount = sortedPanels.filter(p => p.status === 'done').length;
          toast.success(lang === 'pt'
            ? `✅ Storyboard completo! ${doneCount}/${progress?.total || sortedPanels.length} painéis gerados.`
            : `✅ Storyboard complete! ${doneCount}/${progress?.total || sortedPanels.length} panels generated.`
          );
          return;
        }
        
        // Check for errors or max attempts
        if (progress?.status === 'error' || attempts > maxAttempts) {
          setLoading(false);
          const doneCount = sortedPanels.filter(p => p.status === 'done').length;
          if (doneCount > 0) {
            toast.info(lang === 'pt' 
              ? `⚠️ Storyboard parcialmente gerado: ${doneCount}/${progress?.total || sortedPanels.length}` 
              : `⚠️ Storyboard partially generated: ${doneCount}/${progress?.total || sortedPanels.length}`
            );
          } else {
            toast.error(lang === 'pt' ? 'Erro ao gerar storyboard' : 'Storyboard generation failed');
          }
          return;
        }
        
        // Continue polling every 3 seconds
        setTimeout(poll, 3000);
      }).catch(err => {
        console.error('Storyboard polling error:', err);
        if (attempts > maxAttempts) {
          setLoading(false);
          toast.error(lang === 'pt' ? 'Timeout ao gerar storyboard' : 'Storyboard generation timeout');
        } else {
          setTimeout(poll, 3000);
        }
      });
    };
    
    poll();
  };

  const syncMissingPanels = async () => {
    setSyncingPanels(true);
    try {
      const { data } = await axios.post(`${API}/studio/projects/${projectId}/storyboard/sync-panels`);
      if (data.synced > 0) {
        toast.success(lang === 'pt' ? `Gerando ${data.synced} painéis faltantes...` : `Generating ${data.synced} missing panels...`);
        pollStoryboardProgress(); // Use new polling
      } else {
        toast.info(lang === 'pt' ? 'Todos os painéis já existem' : 'All panels already exist');
        setSyncingPanels(false);
      }
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao sincronizar painéis'));
      setSyncingPanels(false);
    }
  };


  const pollStoryboard = () => {
    let attempts = 0;
    const poll = () => {
      attempts++;
      axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r => {
        const d = r.data;
        const newPanels = d.panels || [];
        const newStatus = d.storyboard_status || {};
        
        // 🐛 DEBUG: Log progress updates
        console.log(`🎨 [Storyboard Poll] Attempt ${attempts}:`, {
          phase: newStatus.phase,
          current: newStatus.current,
          total: newStatus.total,
          panelsCount: newPanels.length,
          panelsDone: newPanels.filter(p => p.image_url).length
        });
        
        setPanels(newPanels);
        setStoryboardStatus(newStatus);

        if (newStatus.phase === 'complete') {
          setLoading(false);
          const doneCount = newPanels.filter(p => p.image_url).length;
          toast.success(lang === 'pt'
            ? `Storyboard pronto! ${doneCount} painéis gerados.`
            : `Storyboard ready! ${doneCount} panels generated.`);
          return;
        }
        if (newStatus.phase === 'error' || attempts > 60) {
          setLoading(false);
          if (newPanels.length > 0) {
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

  // ══════════════════════════════════════════════════════════════
  // MULTI-SELECT REGENERATION
  // ══════════════════════════════════════════════════════════════
  
  const togglePanelSelection = (panelNum) => {
    setSelectedPanels(prev => {
      const newSet = new Set(prev);
      if (newSet.has(panelNum)) {
        newSet.delete(panelNum);
      } else {
        newSet.add(panelNum);
      }
      // Auto-enable multi-select mode when selecting
      if (newSet.size > 0) setIsMultiSelectMode(true);
      if (newSet.size === 0) setIsMultiSelectMode(false);
      return newSet;
    });
  };
  
  const selectAllPanels = () => {
    const allPanelNums = panels.map(p => p.scene_number);
    setSelectedPanels(new Set(allPanelNums));
    setIsMultiSelectMode(true);
  };
  
  const deselectAllPanels = () => {
    setSelectedPanels(new Set());
    setIsMultiSelectMode(false);
  };
  
  const regenerateSelectedPanels = async () => {
    if (selectedPanels.size === 0) {
      toast.error(lang === 'pt' ? 'Selecione ao menos um painel' : 'Select at least one panel');
      return;
    }
    
    const panelsToRegen = Array.from(selectedPanels);
    toast.info(lang === 'pt' 
      ? `Regenerando ${panelsToRegen.length} painéis...`
      : `Regenerating ${panelsToRegen.length} panels...`
    );
    
    // Initialize progress tracking for each panel
    const newRegenerating = new Map();
    panelsToRegen.forEach(num => {
      newRegenerating.set(num, { status: 'queued', progress: 0 });
    });
    setRegeneratingPanels(newRegenerating);
    
    // Process panels sequentially to avoid overload (2 at a time)
    const BATCH_SIZE = 2;
    for (let i = 0; i < panelsToRegen.length; i += BATCH_SIZE) {
      const batch = panelsToRegen.slice(i, i + BATCH_SIZE);
      
      await Promise.all(
        batch.map(async (panelNum) => {
          try {
            // Update status: generating
            setRegeneratingPanels(prev => {
              const updated = new Map(prev);
              updated.set(panelNum, { status: 'generating', progress: 50 });
              return updated;
            });
            
            const panel = panels.find(p => p.scene_number === panelNum);
            await axios.post(`${API}/studio/projects/${projectId}/storyboard/regenerate-panel`, {
              panel_number: panelNum,
              description: panel?.description || '',
            });
            
            // Update status: success
            setRegeneratingPanels(prev => {
              const updated = new Map(prev);
              updated.set(panelNum, { status: 'success', progress: 100 });
              return updated;
            });
            
            toast.success(lang === 'pt' ? `Painel ${panelNum} regenerado!` : `Panel ${panelNum} regenerated!`);
            
          } catch (error) {
            console.error(`Panel ${panelNum} regeneration failed:`, error);
            setRegeneratingPanels(prev => {
              const updated = new Map(prev);
              updated.set(panelNum, { status: 'error', progress: 0, error: getErrorMsg(error) });
              return updated;
            });
            toast.error(lang === 'pt' ? `Painel ${panelNum} falhou` : `Panel ${panelNum} failed`);
          }
        })
      );
    }
    
    // Reload panels after all done
    setTimeout(() => {
      loadStoryboard();
      setRegeneratingPanels(new Map());
      setSelectedPanels(new Set());
      setIsMultiSelectMode(false);
    }, 2000);
  };

  // ══════════════════════════════════════════════════════════════
  // ORIGINAL REGENERATE PANEL (Single)
  // ══════════════════════════════════════════════════════════════
  
  const regeneratePanel = async (panelNum, customPrompt = '') => {
    setGeneratingPanel(panelNum);
    try {
      const panel = panels.find(p => p.scene_number === panelNum);
      await axios.post(`${API}/studio/projects/${projectId}/storyboard/regenerate-panel`, {
        panel_number: panelNum,
        description: panel?.description || '',
        custom_prompt: customPrompt || '',
      });
      const instruction = customPrompt ? ` (${customPrompt.slice(0, 40)}...)` : '';
      toast.success(lang === 'pt' ? `Regenerando painel ${panelNum}${instruction}` : `Regenerating panel ${panelNum}${instruction}`);
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
      toast.error(getErrorMsg(err, 'Erro'));
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
      toast.error(getErrorMsg(err, 'Erro ao exportar'));
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

  // Book Export — generate cover
  const generateBookCover = async () => {
    setGeneratingCover(true);
    try {
      const r = await axios.post(`${API}/studio/projects/${projectId}/book/generate-cover`);
      setBookCover(r.data.cover_url);
      setBookTitle(r.data.creative_title);
      toast.success(lang === 'pt' ? `Capa criada: "${r.data.creative_title}"` : `Cover created: "${r.data.creative_title}"`);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao gerar capa'));
    } finally {
      setGeneratingCover(false);
    }
  };

  // Book Export — download PDF
  const downloadPdf = async () => {
    setExportingPdf(true);
    try {
      const r = await axios.get(`${API}/studio/projects/${projectId}/book/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${bookTitle || 'storybook'}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      toast.success(lang === 'pt' ? 'PDF baixado!' : 'PDF downloaded!');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao exportar PDF'));
    } finally {
      setExportingPdf(false);
    }
  };

  // Book Export — open interactive book
  const openInteractiveBook = () => {
    const token = localStorage.getItem('studiox_token');
    const url = `/book/${projectId}?token=${encodeURIComponent(token)}`;
    window.open(url, '_blank');
  };

  // Inpainting — edit specific element in panel
  const editElement = async (panelNum) => {
    if (!inpaintPrompt.trim() || inpaintLoading) return;
    setInpaintLoading(true);
    const frameIdx = selectedFrames[panelNum] || 0;
    const currentPanel = panels.find(p => p.scene_number === panelNum);
    const currentFrameUrl = currentPanel?.frames?.[frameIdx]?.image_url || currentPanel?.image_url;

    const endpoint = smartMode ? 'smart-edit' : 'edit-element';
    const payload = {
      panel_number: panelNum,
      edit_instruction: inpaintPrompt.trim(),
      frame_index: frameIdx,
    };

    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/storyboard/${endpoint}`, payload);
      if (res.data.status === 'editing') {
        toast.success(smartMode
          ? (lang === 'pt' ? 'Analisando cena e editando...' : 'Analyzing scene and editing...')
          : (lang === 'pt' ? 'Editando elemento...' : 'Editing element...'));
        const pollInpaint = () => {
          axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r => {
            const updatedPanel = (r.data.panels || []).find(p => p.scene_number === panelNum);
            const updatedFrameUrl = updatedPanel?.frames?.[frameIdx]?.image_url || updatedPanel?.image_url;
            if (updatedPanel?.status === 'done' && updatedFrameUrl !== currentFrameUrl) {
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
      toast.error(getErrorMsg(err, 'Erro'));
      setInpaintLoading(false);
    }
  };

  // Smart Editor — analyze scene
  const analyzeScene = async (panelNum) => {
    const frameIdx = selectedFrames[panelNum] || 0;
    setAnalyzing(panelNum);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/storyboard/analyze-scene`, {
        panel_number: panelNum,
        frame_index: frameIdx,
      });
      setSceneAnalysis(prev => ({ ...prev, [`${panelNum}-${frameIdx}`]: res.data }));
      toast.success(lang === 'pt'
        ? `${(res.data.characters || []).length} personagens, ${(res.data.objects || []).length} objetos detectados`
        : `${(res.data.characters || []).length} characters, ${(res.data.objects || []).length} objects detected`);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro na analise'));
    } finally {
      setAnalyzing(null);
    }
  };

  // Language Agent — convert
  const convertLanguage = async () => {
    setConverting(true);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/language/convert`, { target_lang: targetLang });
      toast.success(lang === 'pt' ? 'Convertendo idioma...' : 'Converting language...');
      const pollLang = () => {
        axios.get(`${API}/studio/projects/${projectId}/language/status`).then(r => {
          const st = r.data.language_status;
          if (st?.phase === 'done') {
            setConverting(false);
            toast.success(lang === 'pt' ? `${st.count} cenas convertidas!` : `${st.count} scenes converted!`);
            axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r2 => setPanels(r2.data.panels || []));
          } else if (st?.phase === 'error') {
            setConverting(false);
            toast.error(typeof st.detail === 'string' ? st.detail : 'Erro');
          } else { setTimeout(pollLang, 4000); }
        }).catch(() => setTimeout(pollLang, 5000));
      };
      setTimeout(pollLang, 5000);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro na conversao'));
      setConverting(false);
    }
  };

  // Language Agent — review
  const reviewText = async () => {
    setReviewing(true);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/language/review`);
      toast.success(lang === 'pt' ? 'Revisando texto...' : 'Reviewing text...');
      const pollReview = () => {
        axios.get(`${API}/studio/projects/${projectId}/language/status`).then(r => {
          const st = r.data.review_status;
          if (st?.phase === 'done') {
            setReviewing(false);
            setReviewResult({ overall_quality: st.quality, revision_notes: st.notes });
            toast.success(lang === 'pt' ? `Revisao: ${st.quality}` : `Review: ${st.quality}`);
            axios.get(`${API}/studio/projects/${projectId}/storyboard`).then(r2 => setPanels(r2.data.panels || []));
          } else if (st?.phase === 'error') {
            setReviewing(false);
            toast.error(typeof st.detail === 'string' ? st.detail : 'Erro');
          } else { setTimeout(pollReview, 4000); }
        }).catch(() => setTimeout(pollReview, 5000));
      };
      setTimeout(pollReview, 5000);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro na revisao'));
      setReviewing(false);
    }
  };

  // Continuity Director — analyze
  const startContinuityAnalysis = async () => {
    setContinuityRunning(true);
    setContinuityReport(null);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/continuity/analyze`, {
        user_notes: continuityNotes.trim()
      });
      toast.success(lang === 'pt' ? 'Analisando continuidade do storyboard...' : 'Analyzing storyboard continuity...');
      pollContinuityStatus();
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro'));
      setContinuityRunning(false);
    }
  };

  const pollContinuityStatus = () => {
    const poll = () => {
      axios.get(`${API}/studio/projects/${projectId}/continuity/status`).then(r => {
        const st = r.data.continuity_status || {};
        setContinuityStatus(st);
        if (st.phase === 'done') {
          setContinuityRunning(false);
          setContinuityReport(r.data.continuity_report || {});
          const ic = r.data.continuity_report?.total_issues || 0;
          toast.success(lang === 'pt' ? `Analise completa! ${ic} problemas encontrados.` : `Analysis complete! ${ic} issues found.`);
        } else if (st.phase === 'corrected') {
          setCorrecting(false);
          setContinuityRunning(false);
          setContinuityReport(r.data.continuity_report || {});
          toast.success(lang === 'pt' ? `Correcoes aplicadas: ${st.corrected} OK, ${st.failed} falhas` : `Corrections applied: ${st.corrected} OK, ${st.failed} failed`);
          loadStoryboard();
        } else if (st.phase === 'error') {
          setContinuityRunning(false);
          setCorrecting(false);
          toast.error(typeof st.detail === 'string' ? st.detail : 'Erro na analise');
        } else {
          setTimeout(poll, 4000);
        }
      }).catch(() => setTimeout(poll, 5000));
    };
    setTimeout(poll, 3000);
  };

  // Continuity Director — auto-correct
  const startAutoCorrect = async () => {
    setCorrecting(true);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/continuity/auto-correct`);
      if (res.data.status === 'no_corrections_needed') {
        toast.info(lang === 'pt' ? 'Nenhuma correcao necessaria!' : 'No corrections needed!');
        setCorrecting(false);
        return;
      }
      toast.success(lang === 'pt' ? `Corrigindo ${res.data.total_corrections} problemas...` : `Correcting ${res.data.total_corrections} issues...`);
      pollContinuityStatus();
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro'));
      setCorrecting(false);
    }
  };

  const doneCount = useKlingMode && klingStoryboards
    ? (klingStoryboards.scenes || []).flatMap(s => s.frames || []).filter(f => f.image_url).length
    : panels.filter(p => p.image_url).length;
  const totalPanels = panels.length || scenes.length;

  return (
    <div className="space-y-3" data-testid="storyboard-editor">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-full bg-gradient-to-br from-[#8B5CF6] to-[#8B6914] flex items-center justify-center">
            <BookOpen size={12} className="text-black" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-white">
              {lang === 'pt' ? 'Storyboard Editável' : 'Editable Storyboard'}
            </h3>
            <p className="text-[11px] text-[#666]">
              {lang === 'pt'
                ? 'Revise e edite cada painel antes de produzir os vídeos'
                : 'Review and edit each panel before producing videos'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Multi-select toggle */}
          {panels.length > 0 && (
            <button
              onClick={() => {
                if (isMultiSelectMode) {
                  deselectAllPanels();
                } else {
                  setIsMultiSelectMode(true);
                }
              }}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition ${
                isMultiSelectMode
                  ? 'bg-orange-500/20 border border-orange-500/40 text-orange-300'
                  : 'bg-[#111] border border-[#333] text-[#888] hover:text-orange-300 hover:border-orange-500/30'
              }`}>
              <CheckCircle size={10} />
              {lang === 'pt' ? 'Seleção Múltipla' : 'Multi-Select'}
            </button>
          )}
          {panels.length > 0 && (
            <button onClick={() => setChatOpen(!chatOpen)} data-testid="toggle-facilitator-chat"
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition ${
                chatOpen
                  ? 'bg-purple-500/20 border border-purple-500/40 text-purple-300'
                  : 'bg-[#111] border border-[#333] text-[#888] hover:text-purple-300 hover:border-purple-500/30'
              }`}>
              <Wand2 size={10} />
              {lang === 'pt' ? 'Facilitador IA' : 'AI Facilitator'}
            </button>
          )}
        </div>
      </div>

      {/* Multi-select toolbar */}
      {isMultiSelectMode && panels.length > 0 && (
        <div className="rounded-xl border border-orange-500/30 bg-orange-500/5 p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-medium text-orange-300">
              {selectedPanels.size} {lang === 'pt' ? 'selecionado(s)' : 'selected'}
            </span>
            <div className="h-4 w-px bg-orange-500/30" />
            <button
              onClick={selectAllPanels}
              className="text-xs text-orange-400 hover:text-orange-300 transition">
              {lang === 'pt' ? 'Selecionar Todos' : 'Select All'}
            </button>
            <button
              onClick={deselectAllPanels}
              className="text-xs text-orange-400 hover:text-orange-300 transition">
              {lang === 'pt' ? 'Limpar' : 'Clear'}
            </button>
          </div>
          <button
            onClick={regenerateSelectedPanels}
            disabled={selectedPanels.size === 0 || regeneratingPanels.size > 0}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-orange-500 text-white text-xs font-medium hover:bg-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed">
            <RefreshCw size={12} className={regeneratingPanels.size > 0 ? 'animate-spin' : ''} />
            {lang === 'pt' ? `Regenerar ${selectedPanels.size || ''}` : `Regenerate ${selectedPanels.size || ''}`}
          </button>
        </div>
      )}
      
      {/* Regeneration Progress Timelines */}
      {regeneratingPanels.size > 0 && (
        <div className="space-y-2 rounded-xl border border-blue-500/30 bg-blue-500/5 p-3">
          <div className="flex items-center gap-2 mb-2">
            <RefreshCw size={12} className="text-blue-400 animate-spin" />
            <span className="text-xs font-semibold text-blue-300">
              {lang === 'pt' ? 'Regenerando Painéis' : 'Regenerating Panels'}
            </span>
          </div>
          {Array.from(regeneratingPanels.entries()).map(([panelNum, info]) => (
            <div key={panelNum} className="flex items-center gap-3">
              <span className="text-[10px] font-medium text-gray-400 w-16">
                {lang === 'pt' ? 'Painel' : 'Panel'} {panelNum}
              </span>
              <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    info.status === 'success' ? 'bg-green-500' :
                    info.status === 'error' ? 'bg-red-500' :
                    'bg-blue-500 animate-pulse'
                  }`}
                  style={{ width: `${info.progress}%` }}
                />
              </div>
              <span className="text-[10px] font-medium w-20 text-right">
                {info.status === 'queued' && (lang === 'pt' ? 'Na fila' : 'Queued')}
                {info.status === 'generating' && (lang === 'pt' ? 'Gerando...' : 'Generating...')}
                {info.status === 'success' && '✓ Pronto'}
                {info.status === 'error' && '✗ Erro'}
              </span>
            </div>
          ))}
        </div>
      )}


      {/* Generate button — show when no panels exist AND not generating */}
      {displayFrames.length === 0 && !loading && !panels.some(p => p.status === 'generating' || p.status === 'pending') && (
        <div className="space-y-4">
          {videoEngine === 'kling' ? (
            /* KLING: Generate 30 storyboard frames */
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center">
                <Film size={18} className="text-[#8B5CF6]" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-300 mb-3">
                  {lang === 'pt'
                    ? 'Gere automaticamente 30 frames detalhados (1 a cada 10s) para seu vídeo Kling de 5 minutos. Estilo Pixar 3D consistente com seus personagens selecionados.'
                    : 'Automatically generate 30 detailed frames (1 every 10s) for your 5-minute Kling video. Consistent Pixar 3D style with your selected characters.'}
                </p>
                <button onClick={generateAllFramesDirect} data-testid="generate-storyboard-btn"
                  className="btn-gold rounded-xl px-6 py-2.5 text-[11px] font-bold flex items-center gap-2">
                  <Sparkles size={14} />
                  {lang === 'pt' ? 'Gerar Storyboard (30 painéis)' : 'Generate Storyboard (30 panels)'}
                </button>
              </div>
            </div>
          ) : (
            /* SORA 2: Generate scene-based storyboard panels */
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                <Film size={18} className="text-blue-500" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-gray-300 mb-3">
                  {lang === 'pt'
                    ? `Gere painéis visuais para cada uma das ${scenes.length} cenas do seu roteiro. Cada painel terá 6 variações de imagem para escolher. Sora 2 usará esses painéis como referência visual.`
                    : `Generate visual panels for each of your ${scenes.length} script scenes. Each panel will have 6 image variations to choose from. Sora 2 will use these as visual reference.`}
                </p>
                <button onClick={generateStoryboard} data-testid="generate-storyboard-btn"
                  className="btn-gold rounded-xl px-6 py-2.5 text-[11px] font-bold flex items-center gap-2">
                  <Sparkles size={14} />
                  {lang === 'pt' ? `Gerar Storyboard (${scenes.length} cenas)` : `Generate Storyboard (${scenes.length} scenes)`}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Loading state with ordered generation progress */}
      {(loading || panels.some(p => p.status === 'generating' || p.status === 'pending')) && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-[#999] flex items-center gap-1.5">
              <FilmSpinner size={10} className="text-[#8B5CF6]" />
              {(() => {
                const completed = storyboardStatus.completed || 0;
                const total = storyboardStatus.total || scenes.length;
                const phase = storyboardStatus.phase || 'generating';
                
                if (phase === 'structure_created') {
                  return lang === 'pt' 
                    ? `📝 Estrutura criada! Gerando ${total} imagens...` 
                    : `📝 Structure created! Generating ${total} images...`;
                }
                
                // Show real-time progress
                return lang === 'pt' 
                  ? `Gerando painéis: ${completed}/${total}`
                  : `Generating panels: ${completed}/${total}`;
              })()}
            </span>
            <span className="text-[#8B5CF6] font-semibold">
              {Math.round((storyboardStatus.completed || 0) / (storyboardStatus.total || 1) * 100)}%
            </span>
          </div>
          <div className="w-full bg-[#111] rounded-full h-1.5">
            <div className="h-1.5 rounded-full bg-gradient-to-r from-[#8B5CF6] to-[#6D28D9] transition-all duration-500"
              style={{ 
                width: `${(() => {
                  const completed = storyboardStatus.completed || 0;
                  const total = storyboardStatus.total || 1;
                  return Math.min((completed / total) * 100, 100);
                })()}%`
              }}
            />
          </div>
          
          {/* Grid preview during generation - shows panels as they become ready */}
          {panels.length > 0 && panels.some(p => p.status === 'generating') && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] text-gray-400">
                  {lang === 'pt' ? '🤖 5 workers gerando em paralelo' : '🤖 5 workers generating in parallel'}
                </span>
                <span className="text-[10px] font-mono text-purple-400">
                  {panels.filter(p => p.status === 'generating').length} gerando | {panels.filter(p => p.status === 'done').length} prontos
                </span>
              </div>
              <div className="grid grid-cols-6 gap-2">{panels.map((panel) => (
                  <div 
                    key={panel.panel_number}
                    className="aspect-video rounded border overflow-hidden bg-[#0D0D0D] relative"
                  >
                    {panel.status === 'done' && panel.image_url ? (
                      <img 
                        src={resolveImageUrl(panel.image_url)} 
                        alt={`Painel ${panel.panel_number}`}
                        className="w-full h-full object-cover animate-fade-in"
                      />
                    ) : panel.status === 'generating' ? (
                      <div className="w-full h-full flex flex-col items-center justify-center gap-1 bg-purple-500/10 border border-purple-500/30 animate-pulse">
                        <FilmSpinner size={12} className="text-[#8B5CF6]" />
                        <span className="text-[8px] text-purple-400 font-semibold">Worker ativo</span>
                      </div>
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-[#111]">
                        <Clock size={10} className="text-gray-600" />
                      </div>
                    )}
                    {/* Panel number badge with status color */}
                    <div className={`absolute top-1 left-1 backdrop-blur-sm rounded px-1.5 py-0.5 text-[8px] font-mono ${
                      panel.status === 'done' ? 'bg-green-500/80 text-white' :
                      panel.status === 'generating' ? 'bg-purple-500/80 text-white animate-pulse' :
                      'bg-black/70 text-gray-400'
                    }`}>
                      {panel.panel_number}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Panels Grid - ALWAYS 6 COLUMNS COMPACT VIEW */}
      {displayFrames.length > 0 && !loading && (
        <div className="space-y-3">
          {/* Summary bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs text-[#666]">
                {doneCount}/{useKlingMode && klingStoryboards ? klingStoryboards.total_frames : panels.length} {lang === 'pt' ? 'painéis prontos' : 'panels ready'}
              </span>
              {useKlingMode && (
                <button
                  onClick={regenerateAllFrames}
                  disabled={isRegenerating}
                  className={`text-[10px] font-semibold flex items-center gap-1 px-2 py-1 rounded-lg border transition ${
                    isRegenerating
                      ? 'bg-gray-500/20 border-gray-500 text-gray-400 cursor-not-allowed'
                      : confirmRegenerateAll 
                        ? 'bg-red-500/20 border-red-500 text-red-400 animate-pulse' 
                        : 'text-[#8B5CF6] hover:text-[#7C4FD6] border-[#8B5CF6]/30 hover:bg-[#8B5CF6]/10'
                  }`}
                >
                  <RefreshCw size={11} className={isRegenerating ? 'animate-spin' : ''} />
                  {isRegenerating
                    ? (lang === 'pt' ? 'Regenerando...' : 'Regenerating...')
                    : confirmRegenerateAll 
                      ? (lang === 'pt' ? 'Confirmar?' : 'Confirm?')
                      : (lang === 'pt' ? 'Regenerar Todos (30)' : 'Regenerate All (30)')
                  }
                </button>
              )}
            </div>
            {approved && (
              <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                <Check size={10} /> {lang === 'pt' ? 'Aprovado' : 'Approved'}
              </span>
            )}
          </div>

          {/* Missing panels alert */}
          {!useKlingMode && scenes.length > panels.length && (
            <div className="rounded-lg border border-[#8B5CF6]/30 bg-[#8B5CF6]/5 p-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <RefreshCw size={14} className={`text-[#8B5CF6] ${syncingPanels ? 'animate-spin' : ''}`} />
                <span className="text-xs text-[#8B5CF6]">
                  {lang === 'pt'
                    ? `${scenes.length - panels.length} cena(s) sem storyboard`
                    : `${scenes.length - panels.length} scene(s) without storyboard`}
                </span>
              </div>
              <button onClick={syncMissingPanels} disabled={syncingPanels}
                className="text-[10px] font-semibold bg-[#8B5CF6] text-white px-3 py-1 rounded-full hover:bg-[#7C4FD6] transition disabled:opacity-50">
                {syncingPanels
                  ? <>{lang === 'pt' ? 'Gerando...' : 'Generating...'}</>
                  : <>{lang === 'pt' ? 'Gerar Faltantes' : 'Generate Missing'}</>}
              </button>
            </div>
          )}

          {/* Grid 6 colunas - Formato compacto permanente (only when no panels are generating) */}
          {!(panels.length > 0 && panels.some(p => p.status === 'generating')) && (
          <>
          {reorderedFrames && (
            <div className="flex items-center justify-between bg-[#8B5CF6]/10 border border-[#8B5CF6]/30 rounded-lg px-3 py-2 mb-2">
              <span className="text-xs text-[#8B5CF6] font-medium flex items-center gap-1.5">
                <GripVertical size={12} />
                {lang === 'pt' ? 'Ordem alterada — salve para aplicar' : 'Order changed — save to apply'}
              </span>
              <div className="flex items-center gap-2">
                <button onClick={() => setReorderedFrames(null)}
                  className="text-[9px] font-mono uppercase px-2 py-1 rounded text-gray-500 hover:text-white transition">
                  {lang === 'pt' ? 'Desfazer' : 'Undo'}
                </button>
                <button onClick={saveReorderedScenes} disabled={savingOrder}
                  className="text-[9px] font-mono uppercase px-3 py-1 rounded bg-[#8B5CF6] text-white hover:bg-[#7C3AED] transition disabled:opacity-50 flex items-center gap-1">
                  {savingOrder ? <RefreshCw size={9} className="animate-spin" /> : <Check size={9} />}
                  {lang === 'pt' ? 'Salvar Ordem' : 'Save Order'}
                </button>
              </div>
            </div>
          )}
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragStart={() => { isDraggingRef.current = true; }} onDragEnd={handleDragEnd}>
            <SortableContext items={displayFrames.map((_, i) => `frame-${i}`)} strategy={rectSortingStrategy}>
              <div className="grid grid-cols-6 gap-3">
                {displayFrames.map((item, idx) => {
              // Handle both Kling frames and regular panels
              const isKlingFrame = useKlingMode;
              const frameNumber = isKlingFrame ? item.frame_number : item.scene_number;
              const imageUrl = isKlingFrame ? item.image_url : (getSelectedFrame(item.scene_number, item.frames)?.image_url || item.image_url);
              const timeLabel = isKlingFrame ? `${item.time_start}-${item.time_end}` : null;
              const dialogueSnippet = isKlingFrame ? (item.dialogue_text || '') : '';
              const isRegeneratingThis = generatingPanel === frameNumber || regeneratingPanels.has(frameNumber) || item.status === 'generating';
              
              return (
                <SortablePanel key={isKlingFrame ? `kling-${frameNumber}` : `scene-${item.scene_number}`} id={`frame-${idx}`}>
                  {({ dragHandleProps }) => (
                <div
                  className="flex flex-col"
                  data-testid={`storyboard-frame-${frameNumber}`}
                >
                  <div 
                    className="group relative aspect-video rounded-lg border border-[#222] overflow-hidden bg-[#0D0D0D] hover:border-[#8B5CF6] transition-all cursor-pointer"
                    onClick={() => openZoomModal(item, idx)}
                  >
                    {/* Drag handle */}
                    <div {...dragHandleProps} className="absolute top-1 right-1 z-20 cursor-grab active:cursor-grabbing p-0.5 rounded bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={e => e.stopPropagation()}>
                      <GripVertical size={10} className="text-white/70" />
                    </div>
                    {/* Image or placeholder */}
                    {imageUrl ? (
                      <img 
                        src={resolveImageUrl(imageUrl)}
                        alt={`${isKlingFrame ? 'Frame' : 'Painel'} ${frameNumber}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-[#111]">
                        <Image size={20} className="text-[#333]" />
                      </div>
                    )}
                    
                    {/* Panel/Frame number badge */}
                    <div className="absolute top-1 left-1 bg-black/70 backdrop-blur-sm rounded px-1.5 py-0.5 text-[8px] text-white font-mono">
                      {frameNumber}
                    </div>
                    
                    {/* Regenerating overlay */}
                    {isRegeneratingThis && (
                      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm flex flex-col items-center justify-center z-10">
                        <RefreshCw size={16} className="text-[#8B5CF6] animate-spin mb-1" />
                        <span className="text-[9px] text-white font-medium">{lang === 'pt' ? 'Regenerando...' : 'Regenerating...'}</span>
                      </div>
                    )}
                    
                    {/* Time label for Kling frames */}
                    {isKlingFrame && timeLabel && (
                      <div className="absolute bottom-1 left-1 bg-black/70 backdrop-blur-sm rounded px-1.5 py-0.5 text-[8px] text-white/70 font-mono">
                        {timeLabel}
                      </div>
                    )}
                    
                    {/* Hover overlay with actions */}
                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1 pointer-events-none group-hover:pointer-events-auto">
                      <button
                        onClick={(e) => { 
                          e.stopPropagation(); 
                          isKlingFrame ? regenerateKlingFrame(item.frame_number) : regeneratePanel(item.scene_number);
                        }}
                        className={`px-2 py-1 rounded text-[9px] font-semibold flex items-center gap-1 pointer-events-auto transition ${
                          confirmRegenerateFrame === frameNumber
                            ? 'bg-red-500/90 text-white animate-pulse'
                            : 'bg-[#8B5CF6] text-white hover:bg-[#7C4FD6]'
                        }`}
                      >
                        <RefreshCw size={10} />
                        {confirmRegenerateFrame === frameNumber
                          ? (lang === 'pt' ? 'Confirmar?' : 'Confirm?')
                          : (lang === 'pt' ? 'Regerar' : 'Regenerate')
                        }
                      </button>
                      {!isKlingFrame && item.frames && item.frames.length > 1 && (
                        <span className="text-[8px] text-white/70">
                          {item.frames.length} frames
                        </span>
                      )}
                    </div>
                    
                    {/* Progress indicator overlay */}
                    {regenerationProgress[frameNumber] !== undefined && (
                      <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center gap-2 pointer-events-none">
                        <div className="bg-orange-500/20 border border-orange-500/50 rounded-lg px-3 py-2 backdrop-blur-sm">
                          <div className="flex items-center gap-2">
                            <RefreshCw size={12} className="text-orange-400 animate-spin" />
                            <span className="text-xs font-semibold text-orange-400">
                              {lang === 'pt' ? 'Regenerando' : 'Regenerating'}
                            </span>
                          </div>
                          <div className="mt-2 text-center text-lg font-bold text-orange-300">
                            {regenerationProgress[frameNumber]}%
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Expanded view indicator */}
                    {!isKlingFrame && expandedPanels.has(item.scene_number) && (
                      <div className="absolute bottom-1 right-1 bg-purple-500 rounded-full p-0.5">
                        <ChevronDown size={10} className="text-white" />
                      </div>
                    )}
                  </div>
                  
                  {/* Dialogue text snippet below the frame */}
                  {isKlingFrame && dialogueSnippet && (
                    <div className="mt-1 px-0.5" data-testid={`frame-dialogue-${frameNumber}`}>
                      <p className="text-[8px] leading-tight text-gray-400 line-clamp-2" title={dialogueSnippet}>
                        <MessageSquare size={8} className="inline mr-0.5 text-cyan-500/70" />
                        {dialogueSnippet.length > 60 ? dialogueSnippet.slice(0, 60) + '...' : dialogueSnippet}
                      </p>
                    </div>
                  )}
                </div>
                  )}
                </SortablePanel>
              );
            })}
              </div>
            </SortableContext>
          </DndContext>
          </>
          )}
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
                <p className="text-xs text-[#555]">
                  {lang === 'pt'
                    ? 'Diga o que quer mudar. Ex: "Mude o diálogo do painel 3" ou "Regenere a imagem da cena 5 com mais iluminação"'
                    : 'Tell me what to change. Ex: "Change panel 3 dialogue" or "Regenerate scene 5 image with more lighting"'}
                </p>
              </div>
            )}
            {chatMessages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg px-3 py-2 text-xs leading-relaxed ${
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
                  <span className="text-[11px] text-[#666]">{lang === 'pt' ? 'Analisando...' : 'Analyzing...'}</span>
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


      {/* Continuity Director moved to Step 7 (Final Results) */}

      {/* Action buttons */}
      <div className="flex gap-2">
        <button onClick={onBack}
          className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
          {lang === 'pt' ? '← Personagens' : '← Characters'}
        </button>
        {panels.length > 0 && !loading && (
          <>
            <button onClick={generateStoryboard} data-testid="regenerate-all-storyboard"
              className="rounded-lg border border-[#333] py-2 px-3 text-[10px] text-[#999] hover:text-[#8B5CF6] hover:border-[#8B5CF6]/30 transition flex items-center gap-1">
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
                {lang === 'pt' ? 'Ir para Produção' : 'Go to Production'} <ChevronRight size={12} />
              </button>
            )}
          </>
        )}
      </div>

      {/* Expanded Panel View Modal */}
      {selectedPanelForView && (
        <div 
          className="fixed inset-0 z-50 bg-black/90 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setSelectedPanelForView(null)}
        >
          <div 
            className="relative max-w-5xl w-full bg-[#0D0D0D] rounded-xl border border-[#8B5CF6]/30 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-[#222]">
              <div>
                <h3 className="text-base font-bold text-white">
                  {lang === 'pt' ? 'Painel' : 'Panel'} {selectedPanelForView.panel_number} - {selectedPanelForView.title || `Cena ${selectedPanelForView.scene_number}`}
                </h3>
                {selectedPanelForView.frames && selectedPanelForView.frames.length > 1 && (
                  <p className="text-xs text-gray-400 mt-1">
                    {selectedPanelForView.frames.length} frames • {lang === 'pt' ? 'Use as setas para navegar' : 'Use arrows to navigate'}
                  </p>
                )}
              </div>
              <button
                onClick={() => setSelectedPanelForView(null)}
                className="w-8 h-8 rounded-full bg-[#222] hover:bg-[#333] flex items-center justify-center transition"
              >
                <X size={16} className="text-white" />
              </button>
            </div>

            {/* Main Image Area */}
            <div className="relative bg-black">
              {(() => {
                const frames = selectedPanelForView.frames || [];
                const currentFrame = frames[selectedFrameIndex] || { image_url: selectedPanelForView.image_url };
                
                return (
                  <>
                    <img 
                      src={resolveImageUrl(currentFrame.image_url)}
                      alt={`Frame ${selectedFrameIndex + 1}`}
                      className="w-full max-h-[70vh] object-contain"
                    />
                    
                    {/* Navigation Arrows (if multiple frames) */}
                    {frames.length > 1 && (
                      <>
                        <button
                          onClick={() => setSelectedFrameIndex(prev => Math.max(0, prev - 1))}
                          disabled={selectedFrameIndex === 0}
                          className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/70 backdrop-blur-sm hover:bg-black/90 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition"
                        >
                          <ChevronLeft size={20} className="text-white" />
                        </button>
                        <button
                          onClick={() => setSelectedFrameIndex(prev => Math.min(frames.length - 1, prev + 1))}
                          disabled={selectedFrameIndex === frames.length - 1}
                          className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/70 backdrop-blur-sm hover:bg-black/90 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center transition"
                        >
                          <ChevronRight size={20} className="text-white" />
                        </button>
                      </>
                    )}
                  </>
                );
              })()}
            </div>

            {/* Frame Thumbnails (if multiple frames) */}
            {selectedPanelForView.frames && selectedPanelForView.frames.length > 1 && (
              <div className="p-4 border-t border-[#222]">
                <div className="flex items-center gap-2 mb-2">
                  <Film size={12} className="text-[#8B5CF6]" />
                  <span className="text-xs font-semibold text-gray-400">
                    {lang === 'pt' ? 'Frames desta cena' : 'Frames of this scene'}
                  </span>
                </div>
                <div className="grid grid-cols-6 gap-2">
                  {selectedPanelForView.frames.map((frame, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedFrameIndex(idx)}
                      className={`relative aspect-video rounded border-2 overflow-hidden cursor-pointer transition ${
                        idx === selectedFrameIndex 
                          ? 'border-[#8B5CF6] ring-2 ring-[#8B5CF6]/50' 
                          : 'border-[#333] hover:border-[#555]'
                      }`}
                    >
                      <img 
                        src={resolveImageUrl(frame.image_url)}
                        alt={frame.label}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute bottom-0 left-0 right-0 bg-black/70 backdrop-blur-sm px-1 py-0.5">
                        <span className="text-[8px] text-white font-mono">{frame.label || `Frame ${idx + 1}`}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Footer Info */}
            <div className="px-4 py-3 bg-[#111] border-t border-[#222] text-xs text-gray-400">
              <p className="mb-1"><strong className="text-white">{lang === 'pt' ? 'Descrição:' : 'Description:'}</strong> {selectedPanelForView.description || 'N/A'}</p>
              {selectedPanelForView.frames && selectedPanelForView.frames.length > 0 && (
                <p className="text-[#8B5CF6]">
                  ✓ {selectedPanelForView.frames.length} {lang === 'pt' ? 'frames gerados' : 'frames generated'}
                </p>
              )}
            </div>
          </div>
        </div>
      )}


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


      {/* Zoom Modal — Editable */}
      {zoomFrame && createPortal(
        <div className="fixed inset-0 z-[9999] bg-black/95 flex items-center justify-center p-4"
             onClick={closeZoomModal}>
          <div className="relative w-full max-w-5xl max-h-[90vh] overflow-y-auto"
               onClick={(e) => e.stopPropagation()}>
            
            {/* Close button removed from floating position - now in header */}

            {/* Navigation buttons */}
            {zoomFrameIndex > 0 && (
              <button
                onClick={() => navigateFrame('prev')}
                data-testid="zoom-prev-btn"
                className="absolute left-4 top-1/2 -translate-y-1/2 z-10 bg-black/80 hover:bg-black text-white rounded-full p-3 transition">
                <ChevronLeft size={24} />
              </button>
            )}
            {zoomFrameIndex < displayFrames.length - 1 && (
              <button
                onClick={() => navigateFrame('next')}
                data-testid="zoom-next-btn"
                className="absolute right-4 top-1/2 -translate-y-1/2 z-10 bg-black/80 hover:bg-black text-white rounded-full p-3 transition">
                <ChevronRight size={24} />
              </button>
            )}

            <div className="bg-[#0A0A0A] rounded-xl border border-[#222] overflow-hidden">
              {/* Header */}
              <div className="bg-[#111] border-b border-[#222] px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-white">
                      Frame {useKlingMode ? zoomFrame.frame_number : zoomFrame.scene_number}
                    </h3>
                    {useKlingMode && (
                      <p className="text-sm text-gray-400 mt-1">
                        {zoomFrame.time_start} - {zoomFrame.time_end} (10 segundos)
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-gray-500">
                      {zoomFrameIndex + 1} / {displayFrames.length}
                    </div>
                    {!zoomEditing && (
                      <button
                        onClick={startZoomEdit}
                        data-testid="zoom-edit-btn"
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 text-[#8B5CF6] hover:bg-[#8B5CF6]/25 transition">
                        <Edit3 size={12} />
                        {lang === 'pt' ? 'Editar' : 'Edit'}
                      </button>
                    )}
                    {zoomEditing && (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => { setZoomEditing(false); setZoomEditData({}); }}
                          className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-[#222] border border-[#333] text-gray-300 hover:bg-[#333] transition">
                          <X size={12} />
                          {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                        </button>
                        <button
                          onClick={saveZoomEdit}
                          disabled={zoomSaving}
                          data-testid="zoom-save-btn"
                          className="flex items-center gap-1 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/30 transition disabled:opacity-50">
                          {zoomSaving ? <FilmSpinner size={12} className="text-emerald-400" /> : <Save size={12} />}
                          {lang === 'pt' ? 'Salvar' : 'Save'}
                        </button>
                      </div>
                    )}
                    {/* Close button - inside header */}
                    <button
                      onClick={closeZoomModal}
                      data-testid="zoom-close-btn"
                      className="flex items-center justify-center w-8 h-8 rounded-full bg-[#222] hover:bg-red-600 text-gray-400 hover:text-white transition">
                      <X size={16} />
                    </button>
                  </div>
                </div>
              </div>

              {/* Image */}
              <div className="relative bg-black">
                {zoomFrame.image_url ? (
                  <img
                    src={resolveImageUrl(zoomFrame.image_url)}
                    alt={`Frame ${zoomFrame.frame_number}`}
                    className="w-full h-auto max-h-[50vh] object-contain mx-auto"
                  />
                ) : (
                  <div className="w-full h-64 flex items-center justify-center">
                    <Film size={48} className="text-gray-600 animate-pulse" />
                  </div>
                )}
              </div>

              {/* Editable Prompts Section — Kling Mode */}
              {useKlingMode && (
                <div className="p-6 space-y-4">
                  {/* Dialogue Text */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                        <MessageSquare size={14} />
                        {lang === 'pt' ? 'Texto / Diálogo' : 'Dialogue / Script Text'}
                      </h4>
                      {!zoomEditing && (
                        <button
                          onClick={() => copyToClipboard(zoomFrame.dialogue_text || '')}
                          className="text-xs text-gray-400 hover:text-white flex items-center gap-1 px-2 py-1 rounded bg-[#111] hover:bg-[#222] transition">
                          <Copy size={12} />
                          {lang === 'pt' ? 'Copiar' : 'Copy'}
                        </button>
                      )}
                    </div>
                    {zoomEditing ? (
                      <textarea
                        value={zoomEditData.dialogue_text || ''}
                        onChange={e => setZoomEditData(prev => ({ ...prev, dialogue_text: e.target.value }))}
                        data-testid="zoom-edit-dialogue"
                        rows={3}
                        className="w-full bg-[#0D0D0D] border border-cyan-500/30 rounded-lg p-3 text-xs text-gray-200 leading-relaxed resize-y outline-none focus:border-cyan-500/60 transition"
                        placeholder={lang === 'pt' ? 'Texto do diálogo ou narração...' : 'Dialogue or narration text...'}
                      />
                    ) : (
                      <div className="bg-[#0D0D0D] border border-[#222] rounded-lg p-3">
                        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {zoomFrame.dialogue_text || (lang === 'pt' ? '(Sem diálogo)' : '(No dialogue)')}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Image Prompt */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-purple-400 flex items-center gap-2">
                        <Paintbrush size={14} />
                        {lang === 'pt' ? 'Prompt de Imagem (Gemini)' : 'Image Prompt (Gemini)'}
                      </h4>
                      {!zoomEditing && (
                        <button
                          onClick={() => copyToClipboard(zoomFrame.image_prompt)}
                          className="text-xs text-gray-400 hover:text-white flex items-center gap-1 px-2 py-1 rounded bg-[#111] hover:bg-[#222] transition">
                          <Copy size={12} />
                          {lang === 'pt' ? 'Copiar' : 'Copy'}
                        </button>
                      )}
                    </div>
                    {zoomEditing ? (
                      <textarea
                        value={zoomEditData.image_prompt || ''}
                        onChange={e => setZoomEditData(prev => ({ ...prev, image_prompt: e.target.value }))}
                        data-testid="zoom-edit-image-prompt"
                        rows={4}
                        className="w-full bg-[#0D0D0D] border border-purple-500/30 rounded-lg p-3 text-xs text-gray-200 leading-relaxed resize-y outline-none focus:border-purple-500/60 transition"
                      />
                    ) : (
                      <div className="bg-[#0D0D0D] border border-[#222] rounded-lg p-3">
                        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {zoomFrame.image_prompt}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Kling Prompt */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-orange-400 flex items-center gap-2">
                        <Film size={14} />
                        {lang === 'pt' ? 'Prompt Kling (Para Vídeo)' : 'Kling Prompt (For Video)'}
                      </h4>
                      {!zoomEditing && (
                        <button
                          onClick={() => copyToClipboard(zoomFrame.kling_prompt)}
                          className="text-xs text-gray-400 hover:text-white flex items-center gap-1 px-2 py-1 rounded bg-[#111] hover:bg-[#222] transition">
                          <Copy size={12} />
                          {lang === 'pt' ? 'Copiar' : 'Copy'}
                        </button>
                      )}
                    </div>
                    {zoomEditing ? (
                      <textarea
                        value={zoomEditData.kling_prompt || ''}
                        onChange={e => setZoomEditData(prev => ({ ...prev, kling_prompt: e.target.value }))}
                        data-testid="zoom-edit-kling-prompt"
                        rows={4}
                        className="w-full bg-[#0D0D0D] border border-orange-500/30 rounded-lg p-3 text-xs text-gray-200 leading-relaxed resize-y outline-none focus:border-orange-500/60 transition"
                      />
                    ) : (
                      <div className="bg-[#0D0D0D] border border-[#222] rounded-lg p-3">
                        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {zoomFrame.kling_prompt}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Additional Details (read-only) */}
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[#222]">
                    {zoomFrame.characters_present && zoomFrame.characters_present.length > 0 && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-400 mb-1">
                          {lang === 'pt' ? 'Personagens' : 'Characters'}
                        </h5>
                        <p className="text-xs text-gray-300">{zoomFrame.characters_present.join(', ')}</p>
                      </div>
                    )}
                    {zoomFrame.camera_movement && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-400 mb-1">
                          {lang === 'pt' ? 'Movimento de Câmera' : 'Camera Movement'}
                        </h5>
                        <p className="text-xs text-gray-300">{zoomFrame.camera_movement}</p>
                      </div>
                    )}
                    {zoomFrame.emotion && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-400 mb-1">
                          {lang === 'pt' ? 'Emoção' : 'Emotion'}
                        </h5>
                        <p className="text-xs text-gray-300">{zoomFrame.emotion}</p>
                      </div>
                    )}
                    {zoomFrame.lighting && (
                      <div>
                        <h5 className="text-xs font-semibold text-gray-400 mb-1">
                          {lang === 'pt' ? 'Iluminação' : 'Lighting'}
                        </h5>
                        <p className="text-xs text-gray-300">{zoomFrame.lighting}</p>
                      </div>
                    )}
                  </div>

                  {/* Regenerate button inside zoom */}
                  {!zoomEditing && (
                    <div className="pt-4 border-t border-[#222] flex gap-3">
                      <button
                        onClick={() => {
                          regenerateKlingFrame(zoomFrame.frame_number);
                          closeZoomModal();
                        }}
                        data-testid="zoom-regenerate-btn"
                        className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 text-[#8B5CF6] hover:bg-[#8B5CF6]/25 transition">
                        <RefreshCw size={12} />
                        {lang === 'pt' ? 'Regenerar Imagem' : 'Regenerate Image'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Scene Details Section — Sora 2 Mode */}
              {!useKlingMode && (() => {
                // Cross-reference panel with scene data to get dialogue, sora_prompt, etc.
                const matchedScene = scenes.find(s => s.scene_number === zoomFrame.scene_number) || {};
                const sceneDialogue = matchedScene.dubbed_text || matchedScene.dialogue || zoomFrame.dialogue || '';
                const soraPrompt = matchedScene.sora_prompt || zoomFrame.sora_prompt || '';
                const sceneEmotion = matchedScene.emotion || zoomFrame.emotion || '';
                const sceneChars = matchedScene.characters_in_scene || zoomFrame.characters_in_scene || [];
                const sceneDescription = zoomFrame.description || matchedScene.description || '';
                
                return (
                <div className="p-6 space-y-4">
                  {/* Scene Title */}
                  <div className="space-y-1">
                    <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                      <Film size={14} className="text-[#8B5CF6]" />
                      {zoomEditing ? (
                        <input
                          value={zoomEditData.title || ''}
                          onChange={e => setZoomEditData(prev => ({ ...prev, title: e.target.value }))}
                          className="flex-1 bg-[#0D0D0D] border border-[#8B5CF6]/30 rounded px-2 py-1 text-sm text-white outline-none focus:border-[#8B5CF6]/60"
                          data-testid="zoom-edit-title"
                        />
                      ) : (
                        <span>{zoomFrame.title || matchedScene.title || `Cena ${zoomFrame.scene_number}`}</span>
                      )}
                    </h4>
                  </div>

                  {/* Scene Description */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold text-purple-400 flex items-center gap-2">
                      <Paintbrush size={14} />
                      {lang === 'pt' ? 'Descrição da Cena' : 'Scene Description'}
                    </h4>
                    {zoomEditing ? (
                      <textarea
                        value={zoomEditData.description || ''}
                        onChange={e => setZoomEditData(prev => ({ ...prev, description: e.target.value }))}
                        rows={4}
                        className="w-full bg-[#0D0D0D] border border-purple-500/30 rounded-lg p-3 text-xs text-gray-200 leading-relaxed resize-y outline-none focus:border-purple-500/60 transition"
                        data-testid="zoom-edit-description"
                      />
                    ) : (
                      <div className="bg-[#0D0D0D] border border-[#222] rounded-lg p-3">
                        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {sceneDescription || (lang === 'pt' ? '(Sem descrição)' : '(No description)')}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Dialogue */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                        <MessageSquare size={14} />
                        {lang === 'pt' ? 'Diálogo' : 'Dialogue'}
                      </h4>
                      {zoomEditing && (
                        <span className="text-[10px] text-gray-500">
                          {(zoomEditData.dialogue || '').split(/\s+/).filter(Boolean).length} palavras (~{((zoomEditData.dialogue || '').split(/\s+/).filter(Boolean).length / 2.5).toFixed(1)}s)
                        </span>
                      )}
                    </div>
                    {zoomEditing ? (
                      <textarea
                        value={zoomEditData.dialogue || ''}
                        onChange={e => setZoomEditData(prev => ({ ...prev, dialogue: e.target.value }))}
                        rows={3}
                        className="w-full bg-[#0D0D0D] border border-cyan-500/30 rounded-lg p-3 text-xs text-gray-200 leading-relaxed resize-y outline-none focus:border-cyan-500/60 transition"
                        placeholder={lang === 'pt' ? 'Diálogo da cena (max ~25 palavras para 12s)...' : 'Scene dialogue (max ~25 words for 12s)...'}
                        data-testid="zoom-edit-dialogue"
                      />
                    ) : (
                      <div className="bg-[#0D0D0D] border border-[#222] rounded-lg p-3">
                        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {sceneDialogue || (lang === 'pt' ? '(Sem diálogo)' : '(No dialogue)')}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Sora Prompt (if available from Director Preview) */}
                  {soraPrompt && (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-orange-400 flex items-center gap-2">
                          <Sparkles size={14} />
                          {lang === 'pt' ? 'Prompt Sora 2 (Director)' : 'Sora 2 Prompt (Director)'}
                        </h4>
                        <button
                          onClick={() => copyToClipboard(soraPrompt)}
                          className="text-xs text-gray-400 hover:text-white flex items-center gap-1 px-2 py-1 rounded bg-[#111] hover:bg-[#222] transition">
                          <Copy size={12} />
                          {lang === 'pt' ? 'Copiar' : 'Copy'}
                        </button>
                      </div>
                      <div className="bg-[#0D0D0D] border border-orange-500/20 rounded-lg p-3">
                        <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap">
                          {soraPrompt}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Characters */}
                  {sceneChars.length > 0 && (
                    <div className="space-y-1">
                      <h5 className="text-xs font-semibold text-gray-400">
                        {lang === 'pt' ? 'Personagens na Cena' : 'Characters in Scene'}
                      </h5>
                      <p className="text-xs text-gray-300">{sceneChars.join(', ')}</p>
                    </div>
                  )}

                  {/* Emotion */}
                  {sceneEmotion && (
                    <div className="space-y-1">
                      <h5 className="text-xs font-semibold text-gray-400">
                        {lang === 'pt' ? 'Emoção' : 'Emotion'}
                      </h5>
                      <p className="text-xs text-gray-300">{sceneEmotion}</p>
                    </div>
                  )}

                  {/* Instruction + Regenerate */}
                  <div className="pt-4 border-t border-[#222] space-y-2">
                    <textarea
                      value={regenInstruction}
                      onChange={(e) => setRegenInstruction(e.target.value)}
                      placeholder={lang === 'pt' 
                        ? 'Descreva o que ajustar nesta cena... (opcional)' 
                        : 'Describe what to adjust in this scene... (optional)'}
                      className="w-full bg-[#111] border border-[#333] rounded-lg px-3 py-2 text-xs text-white/80 placeholder-white/30 resize-none focus:outline-none focus:border-[#8B5CF6]/50"
                      rows={2}
                      data-testid="regen-instruction-input"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          regeneratePanel(zoomFrame.scene_number, regenInstruction);
                          setRegenInstruction('');
                          closeZoomModal();
                        }}
                        disabled={generatingPanel === zoomFrame.scene_number}
                        className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 text-[#8B5CF6] hover:bg-[#8B5CF6]/25 disabled:opacity-40 transition"
                        data-testid="regen-panel-btn"
                      >
                        <RefreshCw size={12} className={generatingPanel === zoomFrame.scene_number ? 'animate-spin' : ''} />
                        {regenInstruction.trim()
                          ? (lang === 'pt' ? 'Regenerar com Ajuste' : 'Regenerate with Instruction')
                          : (lang === 'pt' ? 'Regenerar Painel' : 'Regenerate Panel')
                        }
                      </button>
                    </div>
                  </div>
                </div>
                );
              })()}
            </div>
          </div>
        </div>,
        document.body
      )}


      {/* Confirmation Modal (replaces window.confirm which is blocked by sandbox) */}
      {confirmModal && createPortal(
        <div className="fixed inset-0 z-[9999] bg-black/80 flex items-center justify-center p-4"
             onClick={() => setConfirmModal(null)}>
          <div className="bg-[#0A0A0A] rounded-xl border border-[#333] p-6 max-w-md w-full"
               onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-bold text-white mb-4">
              {lang === 'pt' ? 'Confirmar Ação' : 'Confirm Action'}
            </h3>
            <p className="text-sm text-gray-300 mb-6 leading-relaxed">
              {confirmModal.message}
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => {
                  console.log('🔄 User cancelled');
                  setConfirmModal(null);
                }}
                className="px-4 py-2 text-sm font-semibold text-gray-300 bg-[#1A1A1A] hover:bg-[#222] rounded-lg transition">
                {lang === 'pt' ? 'Cancelar' : 'Cancel'}
              </button>
              <button
                onClick={confirmModal.onConfirm}
                className="px-4 py-2 text-sm font-semibold text-white bg-[#8B5CF6] hover:bg-[#7C4FD6] rounded-lg transition">
                {lang === 'pt' ? 'Confirmar' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>,
        document.body
      )}


    </div>
  );
}
