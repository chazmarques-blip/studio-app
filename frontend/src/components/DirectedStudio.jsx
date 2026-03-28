import { useState, useEffect, useRef, memo, Fragment } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import { Send, Users, Film, Play, Pause, Sparkles, Download, X, ChevronDown, ChevronLeft, ChevronRight, Plus, Volume2, PenTool, RefreshCw, Check, MessageSquare, Clapperboard, Eye, Camera, Copy, Edit3, Save, Wand2, Clock, Trash2, BarChart3, BookOpen, Globe, Maximize2, FileText, Image as ImageIcon, Mic, Music } from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import { getErrorMsg } from '../utils/getErrorMsg';
import { useStudioProduction } from '../contexts/StudioProductionContext';
import { PreviewBoard } from './PreviewBoard';
import { PostProduction } from './PostProduction';
import { StoryboardEditor } from './StoryboardEditor';
import { DialogueEditor } from './DialogueEditor';
import { AvatarLibraryModal } from './pipeline/AvatarLibraryModal';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const DirectedStudio = memo(function DirectedStudio({
  avatars = [], onAddAvatar, onEditAvatar, onRemoveAvatar, onPreviewAvatar,
  onAiEditAvatar, aiEditAvatarId, setAiEditAvatarId, aiEditInstruction, setAiEditInstruction, aiEditLoading,
  lastCreatedAvatar,
}) {
  const { i18n } = useTranslation();
  const lang = i18n.language?.substring(0, 2) || 'pt';
  const studioCtx = useStudioProduction();

  const [step, setStep] = useState(0); // 0 = project list, 1-4 = workflow
  const [projectId, setProjectId] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [scenes, setScenes] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [characterAvatars, setCharacterAvatars] = useState({});
  const [generating, setGenerating] = useState(false);
  const [agentStatus, setAgentStatus] = useState({});
  const [outputs, setOutputs] = useState([]);
  const [allProjects, setAllProjects] = useState([]);
  const [viewingProject, setViewingProject] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [editingChar, setEditingChar] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', description: '', age: '', role: '' });
  const [showNewProject, setShowNewProject] = useState(false);
  const [visualStyle, setVisualStyle] = useState('animation');
  const [projectLang, setProjectLang] = useState('pt');
  const [audioMode, setAudioMode] = useState('narrated');
  const [animationSub, setAnimationSub] = useState('pixar_3d');
  const [continuityMode, setContinuityMode] = useState(true);
  const [regenScene, setRegenScene] = useState(null);
  const [editingScene, setEditingScene] = useState(null);
  const [editSceneForm, setEditSceneForm] = useState({});
  const [screenplayApproved, setScreenplayApproved] = useState(false);  const [voices, setVoices] = useState([]);
  const [selectedVoice, setSelectedVoice] = useState('21m00Tcm4TlvDq8ikWAM');
  const [narrations, setNarrations] = useState([]);
  const [narrationStatus, setNarrationStatus] = useState({});
  const [narrationGenerating, setNarrationGenerating] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [addingSceneAt, setAddingSceneAt] = useState(null); // position to insert new scene
  const [newSceneForm, setNewSceneForm] = useState({ title: '', description: '', dialogue: '', emotion: '', camera: '', characters_in_scene: [] });
  const [newSceneMode, setNewSceneMode] = useState('manual'); // 'manual' or 'ai'
  const [aiSceneHint, setAiSceneHint] = useState('');
  const [aiSceneLoading, setAiSceneLoading] = useState(false);
  const [addingSceneLoading, setAddingSceneLoading] = useState(false);
  const [projectSearch, setProjectSearch] = useState('');
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [showPostProd, setShowPostProd] = useState(false);
  const [storyboardThumbs, setStoryboardThumbs] = useState([]);
  const [projectAvatars, setProjectAvatars] = useState([]); // Avatars scoped to current project
  const [showLibrary, setShowLibrary] = useState(false); // Avatar library modal
  const [previewModal, setPreviewModal] = useState(null); // { type: 'video'|'gallery'|'book'|'pdf', data: any }
  const [allPanelFrames, setAllPanelFrames] = useState([]); // All storyboard frames for gallery
  const skipAutoResume = useRef(false);
  const chatEndRef = useRef(null);

  // Keyboard handler for preview modal
  useEffect(() => {
    if (!previewModal) return;
    const handler = (e) => {
      if (e.key === 'Escape') setPreviewModal(null);
      if (previewModal.type === 'gallery' && e.key === 'ArrowRight') {
        setPreviewModal(prev => prev?.data?.currentIndex < prev?.data?.images?.length - 1
          ? { ...prev, data: { ...prev.data, currentIndex: prev.data.currentIndex + 1 } } : prev);
      }
      if (previewModal.type === 'gallery' && e.key === 'ArrowLeft') {
        setPreviewModal(prev => prev?.data?.currentIndex > 0
          ? { ...prev, data: { ...prev.data, currentIndex: prev.data.currentIndex - 1 } } : prev);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [previewModal]);

  const loadAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const r = await axios.get(`${API}/studio/analytics/performance`);
      setAnalyticsData(r.data);
      setShowAnalytics(true);
    } catch { toast.error('Erro ao carregar analytics'); }
    setAnalyticsLoading(false);
  };

  // Auto-add newly created avatars (from PipelineView modal) to the current project
  useEffect(() => {
    if (lastCreatedAvatar && projectId) {
      addAvatarToProject(lastCreatedAvatar);
    }
  }, [lastCreatedAvatar]); // eslint-disable-line react-hooks/exhaustive-deps

  const STEPS = [
    { n: 1, icon: MessageSquare, label: lang === 'pt' ? 'Roteiro' : 'Script' },
    { n: 2, icon: Users, label: lang === 'pt' ? 'Personagens' : 'Characters' },
    { n: 3, icon: Camera, label: 'Storyboard' },
    { n: 4, icon: Mic, label: lang === 'pt' ? 'Diálogos' : 'Dialogues' },
    { n: 5, icon: Clapperboard, label: lang === 'pt' ? 'Produção' : 'Production' },
    { n: 6, icon: Eye, label: lang === 'pt' ? 'Resultado' : 'Result' },
  ];

  const STATUS_LABELS = {
    draft: { pt: 'Rascunho', en: 'Draft', color: 'text-[#888]' },
    scripting: { pt: 'Roteiro', en: 'Scripting', color: 'text-blue-400' },
    starting: { pt: 'Iniciando', en: 'Starting', color: 'text-yellow-400' },
    running_agents: { pt: 'Produzindo', en: 'Producing', color: 'text-orange-400' },
    complete: { pt: 'Concluído', en: 'Complete', color: 'text-emerald-400' },
    error: { pt: 'Erro', en: 'Error', color: 'text-red-400' },
  };

  // Load all projects
  const loadingRef = useRef(false);
  const loadProjects = async () => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setProjectsLoading(true);
    try {
      const r = await axios.get(`${API}/studio/projects`);
      setAllProjects(r.data.projects || []);
    } catch {
      try {
        await new Promise(res => setTimeout(res, 1500));
        const r = await axios.get(`${API}/studio/projects`);
        setAllProjects(r.data.projects || []);
      } catch { /* silent */ }
    } finally {
      setProjectsLoading(false);
      loadingRef.current = false;
    }
  };

  useEffect(() => { loadProjects(); loadVoices(); }, []);

  // Sync with global production context when returning from another page
  useEffect(() => {
    if (studioCtx?.activeProduction?.projectId && !projectId) {
      const ap = studioCtx.activeProduction;
      setProjectId(ap.projectId);
      setProjectName(ap.projectName || '');
      setScenes(ap.scenes || []);
      setOutputs(ap.outputs || []);
      setAgentStatus(ap.agentStatus || {});
      setNarrations(ap.narrations || []);
      if (ap.status === 'complete') {
        setStep(6); setGenerating(false);
      } else if (['running_agents', 'starting'].includes(ap.status)) {
        setStep(5); setGenerating(true); startPolling(ap.projectId);
      }
    }
  }, []);

  const loadVoices = () => {
    axios.get(`${API}/studio/voices`).then(r => setVoices(r.data.voices || [])).catch(() => {});
  };

  // Reload projects when going back to step 0
  useEffect(() => {
    if (step === 0) loadProjects();
  }, [step]);

  // Load storyboard thumbnails and project data when entering Step 5
  useEffect(() => {
    if (step === 6 && projectId) {
      // Always fetch full status for Step 5 to ensure we have all data
      axios.get(`${API}/studio/projects/${projectId}/status`).then(r => {
        const full = r.data;
        if (full.scenes?.length > 0 && scenes.length === 0) setScenes(full.scenes);
        if (full.outputs?.length > 0 && outputs.length === 0) setOutputs(full.outputs);
        const panels = full.storyboard_panels || [];
        if (panels.length > 0) {
          const thumbs = panels.slice(0, 6).map(p => {
            const f = (p.frames || [])[0];
            return f?.image_url || p?.image_url || '';
          }).filter(Boolean);
          setStoryboardThumbs(thumbs);
          // Collect ALL frames for gallery view
          const allFrames = [];
          panels.forEach((p, pi) => {
            (p.frames || []).forEach((f, fi) => {
              if (f?.image_url) {
                allFrames.push({ url: f.image_url, scene: pi + 1, frame: fi + 1, description: p.description || p.narration || '' });
              }
            });
          });
          setAllPanelFrames(allFrames);
        }
      }).catch(() => {});
    }
  }, [step, projectId]);


  // Auto-resume in-progress project (only truly running, within last 10 min, and ONLY on first mount)
  const hasAutoResumed = useRef(false);
  useEffect(() => {
    if (skipAutoResume.current || hasAutoResumed.current || projectsLoading) return;
    if (allProjects.length === 0) return;
    hasAutoResumed.current = true;
    const now = Date.now();
    const inProgress = allProjects.find(p => {
      if (!['starting', 'running_agents'].includes(p.status)) return false;
      const updated = new Date(p.updated_at).getTime();
      return (now - updated) < 10 * 60 * 1000; // last 10 minutes only
    });
    if (inProgress && !projectId) {
      resumeProject(inProgress);
    }
  }, [allProjects, projectsLoading]);

  // Resume a project from its current step
  const resumeProject = async (proj) => {
    setProjectId(proj.id);
    setProjectName(proj.name || '');
    setProjectDesc(proj.briefing || '');
    setCharacterAvatars(proj.character_avatars || {});
    setProjectAvatars(proj.project_avatars || []);
    setVisualStyle(proj.visual_style || 'animation');
    setProjectLang(proj.language || 'pt');
    setViewingProject(null);

    // Load full project data from /status for complete info
    try {
      const r = await axios.get(`${API}/studio/projects/${proj.id}/status`);
      const full = r.data;
      setScenes(full.scenes || []);
      setCharacters(full.characters || []);
      setChatMessages(full.storyboard_chat_history || []);
      setOutputs(full.outputs || []);
      setNarrations(full.narrations || []);
      setNarrationStatus(full.narration_status || {});
      setScreenplayApproved(full.screenplay_approved || false);
      if (full.project_avatars?.length) setProjectAvatars(full.project_avatars);

      // Load storyboard thumbnails
      const panels = full.storyboard_panels || [];
      if (panels.length > 0) {
        const thumbs = panels.slice(0, 6).map(p => {
          const f = (p.frames || [])[0];
          return f?.image_url || p?.image_url || '';
        }).filter(Boolean);
        setStoryboardThumbs(thumbs);
        // Collect ALL frames for gallery view
        const allFrames = [];
        panels.forEach((p, pi) => {
          (p.frames || []).forEach((f, fi) => {
            if (f?.image_url) {
              allFrames.push({ url: f.image_url, scene: pi + 1, frame: fi + 1, description: p.description || p.narration || '' });
            }
          });
        });
        setAllPanelFrames(allFrames);
      }

      const status = full.status || proj.status;
      const outs = full.outputs || [];
      if (['starting', 'running_agents', 'generating_video'].includes(status)) {
        setStep(5); setGenerating(true); startPolling(proj.id);
      } else if (status === 'complete' && outs.length > 0) {
        setStep(6); setOutputs(outs);
      } else {
        setGenerating(false);
        setAgentStatus({});
        if (studioCtx?.stopTracking) studioCtx.stopTracking();
        const sc = full.scenes || [];
        if (sc.length > 0) {
          if (panels.length > 0) {
            setStep(3);
          } else {
            setStep(2);
          }
          const existingPD = (full.agents_output || proj.agents_output)?.production_design;
          if (existingPD && existingPD.character_bible) {
            setPreviewData({
              production_design: existingPD,
              avatar_descriptions: (full.agents_output || proj.agents_output)?.avatar_descriptions,
              preview_time: full.preview_time || proj.preview_time,
            });
          }
        } else {
          setStep(1);
        }
      }
    } catch {
      // Fallback to lightweight proj data
      setScenes(proj.scenes || []);
      setCharacters(proj.characters || []);
      setChatMessages(proj.chat_history || []);
      setOutputs(proj.outputs || []);
      setNarrations(proj.narrations || []);
      setNarrationStatus(proj.narration_status || {});
      setScreenplayApproved(proj.screenplay_approved || false);
      if (['starting', 'running_agents', 'generating_video'].includes(proj.status)) {
        setStep(5); setGenerating(true); startPolling(proj.id);
      } else if (proj.status === 'complete' && proj.outputs?.length > 0) {
        setStep(6);
      } else {
        setStep(1);
      }
    }
  };

  // Create a new project (name + description first)
  const createNewProject = async () => {
    if (!projectName.trim()) {
      toast.error(lang === 'pt' ? 'Dê um nome ao projecto' : 'Give the project a name');
      return;
    }
    try {
      const res = await axios.post(`${API}/studio/projects`, {
        name: projectName.trim(),
        briefing: projectDesc.trim(),
        language: projectLang,
        visual_style: visualStyle,
        audio_mode: audioMode,
        animation_sub: animationSub,
        continuity_mode: continuityMode,
      });
      setProjectId(res.data.id);
      setStep(1); setChatMessages([]); setScenes([]); setCharacters([]); setOutputs([]);
      setShowNewProject(false);
      loadProjects();
      toast.success(lang === 'pt' ? 'Projecto criado!' : 'Project created!');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Error'));
    }
  };

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Auto-recover: if stuck on step 3 with generating=false, check if outputs exist
  useEffect(() => {
    if (step === 5 && !generating && projectId) {
      const check = setTimeout(() => {
        axios.get(`${API}/studio/projects/${projectId}/status`).then(res => {
          const d = res.data;
          if (d.status === 'complete' && d.outputs?.length > 0) {
            setOutputs(d.outputs);
            setStep(6);
            toast.success(lang === 'pt' ? 'Produção concluída!' : 'Production complete!');
          } else if (d.outputs?.length > 0) {
            setOutputs(d.outputs);
            setStep(6);
          }
        }).catch(() => {});
      }, 2000);
      return () => clearTimeout(check);
    }
  }, [step, generating, projectId]);

  // Polling for production status
  const startPolling = (pid) => {
    // Register in global context so banner shows on other pages
    studioCtx?.startTracking(pid, projectName, scenes);

    const poll = () => {
      axios.get(`${API}/studio/projects/${pid}/status`).then(res => {
        const d = res.data;
        setAgentStatus(d.agent_status || {});
        setScenes(d.scenes || []);
        // Update outputs in real-time (partial videos as they complete)
        if (d.outputs?.length > 0) setOutputs(d.outputs);
        if (d.narrations?.length > 0) setNarrations(d.narrations);
        // Restore persisted data
        if (d.character_avatars && Object.keys(d.character_avatars).length > 0) setCharacterAvatars(d.character_avatars);
        if (d.visual_style) setVisualStyle(d.visual_style);
        if (d.language) setProjectLang(d.language);

        if (d.status === 'complete') {
          setOutputs(d.outputs || []);
          setGenerating(false);
          setStep(6);
          toast.success(lang === 'pt' ? 'Produção concluída!' : 'Production complete!');
          loadProjects();
          return;
        }
        if (d.status === 'error') {
          setGenerating(false);
          // If outputs exist despite error, go to results (partial/recovered success)
          if (d.outputs?.length > 0) {
            setOutputs(d.outputs);
            setStep(6);
            toast.success(lang === 'pt' ? `Produção finalizada — ${d.outputs.length} vídeos prontos` : `Production finished — ${d.outputs.length} videos ready`);
          } else {
            toast.error(d.error || 'Production error');
          }
          return;
        }
        // Also handle: status reverted to scripting/draft (fix-stuck was called)
        if (!['starting', 'running_agents', 'generating_video'].includes(d.status)) {
          setGenerating(false);
          if (d.outputs?.length > 0) {
            setOutputs(d.outputs);
            setStep(6);
          }
          return;
        }
        setTimeout(poll, 4000);
      }).catch(() => setTimeout(poll, 6000));
    };
    setTimeout(poll, 3000);
  };

  // Send message to Screenwriter (background + polling)
  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: msg }]);
    setChatLoading(true);
    try {
      const res = await axios.post(`${API}/studio/chat`, {
        project_id: projectId,
        message: msg,
        language: lang,
      }, { timeout: 15000 });
      const pid = res.data.project_id;
      setProjectId(pid);
      // Poll for screenwriter result
      pollChatResult(pid);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Screenwriter error'));
      setChatMessages(prev => [...prev, { role: 'assistant', text: '❌ Erro ao processar. Tente novamente.' }]);
      setChatLoading(false);
    }
  };

  const pollChatResult = (pid) => {
    let pollCount = 0;
    const MAX_POLLS = 40; // ~2 min (3s each)
    const poll = () => {
      pollCount++;
      axios.get(`${API}/studio/projects/${pid}/status`).then(res => {
        const d = res.data;
        if (d.chat_status === 'done') {
          const history = d.chat_history || [];
          const lastAssistant = [...history].reverse().find(m => m.role === 'assistant');
          if (lastAssistant) {
            setChatMessages(prev => {
              const lastMsg = prev[prev.length - 1];
              if (lastMsg?.role === 'assistant' && lastMsg?.text === lastAssistant.text) return prev;
              return [...prev, { role: 'assistant', text: lastAssistant.text }];
            });
          }
          setScenes(d.scenes || []);
          setCharacters(d.characters || []);
          setChatLoading(false);
          return;
        }
        if (d.chat_status === 'error') {
          toast.error(d.error || 'Erro ao processar');
          setChatMessages(prev => [...prev, { role: 'assistant', text: `Erro: ${d.error || 'Erro ao processar. Clique "Tentar Novamente"'}` }]);
          setChatLoading(false);
          return;
        }
        // Still thinking — check if stuck too long
        if (pollCount >= MAX_POLLS) {
          setChatMessages(prev => [...prev, { role: 'assistant', text: 'O redator está demorando mais que o esperado. Use o botão "Tentar Novamente" abaixo.' }]);
          setChatLoading(false);
          return;
        }
        setTimeout(poll, 3000);
      }).catch(() => setTimeout(poll, 5000));
    };
    setTimeout(poll, 2000);
  };

  // Retry a stuck screenwriter
  const retryChat = async () => {
    setChatLoading(true);
    // Remove last error/timeout message
    setChatMessages(prev => prev.filter(m => !(m.role === 'assistant' && (m.text.includes('demorando') || m.text.includes('Erro')))));
    try {
      await axios.post(`${API}/studio/projects/${projectId}/retry-chat`);
      toast.success(lang === 'pt' ? 'Reenviando ao Redator...' : 'Retrying Screenwriter...');
      pollChatResult(projectId);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao reenviar'));
      setChatLoading(false);
    }
  };

  // Copy character prompt to clipboard (with fallback for iframe/permissions)
  const copyPrompt = (char) => {
    const prompt = `${char.name}: ${char.description}. ${char.age || ''}, ${char.role || ''}`.trim();
    try {
      const ta = document.createElement('textarea');
      ta.value = prompt;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      toast.success(lang === 'pt' ? 'Prompt copiado!' : 'Prompt copied!');
    } catch {
      toast.error(lang === 'pt' ? 'Erro ao copiar' : 'Copy failed');
    }
  };

  // Start editing a character
  const startEditChar = (idx) => {
    const c = characters[idx];
    setEditForm({ name: c.name || '', description: c.description || '', age: c.age || '', role: c.role || '' });
    setEditingChar(idx);
  };

  // Save edited character
  const saveEditChar = async () => {
    if (editingChar === null) return;
    const updated = [...characters];
    updated[editingChar] = { ...updated[editingChar], ...editForm };
    setCharacters(updated);
    setEditingChar(null);
    // Persist to backend
    if (projectId) {
      try {
        await axios.post(`${API}/studio/projects/${projectId}/update-characters`, { characters: updated });
      } catch { /* silent */ }
    }
    toast.success(lang === 'pt' ? 'Personagem atualizado!' : 'Character updated!');
  };

  // Delete a project
  const deleteProject = async (e, projId) => {
    e.stopPropagation();
    if (!window.confirm(lang === 'pt' ? 'Eliminar este projecto?' : 'Delete this project?')) return;
    try {
      await axios.delete(`${API}/studio/projects/${projId}`);
      setAllProjects(prev => prev.filter(p => p.id !== projId));
      toast.success(lang === 'pt' ? 'Projecto eliminado' : 'Project deleted');
    } catch {
      toast.error(lang === 'pt' ? 'Erro ao eliminar' : 'Delete failed');
    }
  };

  // Resume production for error/incomplete projects
  const resumeProduction = async (e, proj) => {
    e.stopPropagation();
    setProjectId(proj.id);
    setProjectName(proj.name || '');
    setScenes(proj.scenes || []);
    setCharacters(proj.characters || []);
    setOutputs(proj.outputs || []);
    setCharacterAvatars(proj.character_avatars || {});
    setProjectAvatars(proj.project_avatars || []);
    setGenerating(true);
    setStep(5);
    try {
      await axios.post(`${API}/studio/start-production`, {
        project_id: proj.id,
        video_duration: 12,
        character_avatars: proj.character_avatars || {},
      });
      startPolling(proj.id);
      toast.success(lang === 'pt' ? 'Retomando produção...' : 'Resuming production...');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Failed'));
      setGenerating(false);
    }
  };

  // Generate narration with ElevenLabs
  const generateNarration = async () => {
    if (!projectId || scenes.length === 0) return;
    setNarrationGenerating(true);
    setNarrationStatus({ phase: 'starting' });
    try {
      await axios.post(`${API}/studio/projects/${projectId}/generate-narration`, {
        project_id: projectId,
        voice_id: selectedVoice,
        stability: 0.30,
        similarity: 0.80,
        style_val: 0.55,
      });
      toast.success(lang === 'pt' ? 'Gerando narração...' : 'Generating narration...');
      pollNarrationStatus(projectId);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Narration failed'));
      setNarrationGenerating(false);
    }
  };

  const pollNarrationStatus = (pid) => {
    const poll = () => {
      axios.get(`${API}/studio/projects/${pid}/narrations`).then(res => {
        const d = res.data;
        setNarrationStatus(d.narration_status || {});
        setNarrations(d.narrations || []);
        if (d.narration_status?.phase === 'complete') {
          setNarrationGenerating(false);
          toast.success(lang === 'pt' ? 'Narração completa!' : 'Narration complete!');
          return;
        }
        if (d.narration_status?.phase === 'error') {
          setNarrationGenerating(false);
          toast.error(d.narration_status?.error || 'Narration error');
          return;
        }
        setTimeout(poll, 3000);
      }).catch(() => setTimeout(poll, 5000));
    };
    setTimeout(poll, 2000);
  };

  // Link existing avatars to characters and persist to backend
  const linkAvatar = async (charName, avatarUrl) => {
    const newAvatars = { ...characterAvatars, [charName]: avatarUrl };
    setCharacterAvatars(newAvatars);
    // Persist to backend
    if (projectId) {
      try {
        await axios.post(`${API}/studio/projects/${projectId}/save-character-avatars`, { character_avatars: newAvatars });
      } catch (e) { /* silent */ }
    }
  };

  // Add avatar to current project's local pool + global library
  const addAvatarToProject = async (avatar) => {
    if (!projectId) return;
    setProjectAvatars(prev => {
      const exists = prev.some(a => a.id === avatar.id);
      return exists ? prev.map(a => a.id === avatar.id ? { ...a, ...avatar } : a) : [...prev, avatar];
    });
    try {
      await axios.post(`${API}/studio/projects/${projectId}/project-avatars`, { avatar, save_to_library: true });
      // Invalidate library cache so next open shows the new avatar
      localStorage.removeItem('agentzz_avatar_library');
    } catch { /* silent */ }
  };

  // Remove avatar from current project (keeps in global library)
  const removeAvatarFromProject = async (avatarId) => {
    setProjectAvatars(prev => prev.filter(a => a.id !== avatarId));
    // Unlink from characters if linked
    const av = projectAvatars.find(a => a.id === avatarId);
    if (av) {
      const newCharAvatars = { ...characterAvatars };
      for (const [k, v] of Object.entries(newCharAvatars)) {
        if (v === av.url) delete newCharAvatars[k];
      }
      setCharacterAvatars(newCharAvatars);
    }
    if (projectId) {
      try { await axios.delete(`${API}/studio/projects/${projectId}/project-avatars/${avatarId}`); } catch { /* silent */ }
    }
  };

  // Handle import from library
  const handleLibraryImport = (importedAvatars) => {
    setProjectAvatars(prev => {
      const existingIds = new Set(prev.map(a => a.id));
      const newOnes = importedAvatars.filter(a => !existingIds.has(a.id));
      return [...prev, ...newOnes];
    });
  };

  // Regenerate a single scene
  const regenerateScene = async (sceneNum, customPrompt = null) => {
    setRegenScene(sceneNum);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/regenerate-scene`, {
        scene_number: sceneNum,
        custom_prompt: customPrompt,
      });
      toast.success(`Regenerando cena ${sceneNum}...`);
      startPolling(projectId);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao regenerar'));
    } finally {
      setRegenScene(null);
    }
  };

  // Update a scene's description
  const saveSceneEdit = async (sceneNum) => {
    try {
      await axios.post(`${API}/studio/projects/${projectId}/update-scene`, {
        scene_number: sceneNum,
        ...editSceneForm,
      });
      setScenes(prev => prev.map(s =>
        s.scene_number === sceneNum ? { ...s, ...editSceneForm } : s
      ));
      setEditingScene(null);
      setEditSceneForm({});
      toast.success('Cena atualizada!');
    } catch (err) {
      toast.error('Erro ao salvar cena');
    }
  };

  // ── Scene Management: Add, Delete, Reorder ──
  const addScene = async (position) => {
    setAddingSceneLoading(true);
    try {
      const { data } = await axios.post(`${API}/studio/projects/${projectId}/add-scene`, {
        position,
        scene: newSceneForm,
      });
      // Refresh scenes from server
      const status = await axios.get(`${API}/studio/projects/${projectId}/status`);
      setScenes(status.data.scenes || []);
      setAddingSceneAt(null);
      setNewSceneForm({ title: '', description: '', dialogue: '', emotion: '', camera: '', characters_in_scene: [] });
      setNewSceneMode('manual');
      setAiSceneHint('');
      toast.success(lang === 'pt' ? 'Cena adicionada!' : 'Scene added!');
      // Auto-generate storyboard for the new scene if storyboard exists
      if (data.auto_storyboard) {
        try {
          await axios.post(`${API}/studio/projects/${projectId}/storyboard/regenerate-panel`, { panel_number: position });
        } catch { /* Storyboard gen will happen later if it fails */ }
      }
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao adicionar cena'));
    }
    setAddingSceneLoading(false);
  };

  const deleteScene = async (sceneNum) => {
    if (!window.confirm(lang === 'pt' ? `Eliminar cena ${sceneNum}? Isso também remove o storyboard e áudio associados.` : `Delete scene ${sceneNum}?`)) return;
    try {
      await axios.post(`${API}/studio/projects/${projectId}/delete-scene`, { scene_number: sceneNum });
      const status = await axios.get(`${API}/studio/projects/${projectId}/status`);
      setScenes(status.data.scenes || []);
      toast.success(lang === 'pt' ? 'Cena eliminada!' : 'Scene deleted!');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao eliminar cena'));
    }
  };

  const moveScene = async (sceneNum, direction) => {
    const idx = scenes.findIndex(s => s.scene_number === sceneNum);
    if (idx < 0) return;
    const newIdx = direction === 'up' ? idx - 1 : idx + 1;
    if (newIdx < 0 || newIdx >= scenes.length) return;
    const order = scenes.map(s => s.scene_number);
    [order[idx], order[newIdx]] = [order[newIdx], order[idx]];
    try {
      await axios.post(`${API}/studio/projects/${projectId}/reorder-scenes`, { order });
      const status = await axios.get(`${API}/studio/projects/${projectId}/status`);
      setScenes(status.data.scenes || []);
      toast.success(lang === 'pt' ? 'Ordem atualizada!' : 'Order updated!');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao reordenar'));
    }
  };

  const generateSceneAI = async (position) => {
    setAiSceneLoading(true);
    try {
      const { data } = await axios.post(`${API}/studio/projects/${projectId}/generate-scene-ai`, {
        hint: aiSceneHint,
        position,
      });
      if (data.scene) {
        setNewSceneForm({
          title: data.scene.title || '',
          description: data.scene.description || '',
          dialogue: data.scene.dialogue || '',
          emotion: data.scene.emotion || '',
          camera: data.scene.camera || '',
          characters_in_scene: data.scene.characters_in_scene || [],
        });
        toast.success(lang === 'pt' ? 'Cena gerada! Revise e salve.' : 'Scene generated! Review and save.');
      }
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao gerar cena'));
    }
    setAiSceneLoading(false);
  };


  const approveScreenplay = async () => {
    try {
      await axios.patch(`${API}/studio/projects/${projectId}/settings`, {
        screenplay_approved: true,
      });
      setScreenplayApproved(true);
      toast.success(lang === 'pt' ? 'Roteiro aprovado! Avance para Personagens.' : 'Screenplay approved!');
    } catch (err) {
      toast.error('Erro ao aprovar roteiro');
    }
  };

  const unapproveScreenplay = async () => {
    try {
      await axios.patch(`${API}/studio/projects/${projectId}/settings`, {
        screenplay_approved: false,
      });
      setScreenplayApproved(false);
      toast.success(lang === 'pt' ? 'Roteiro reaberto para edição.' : 'Screenplay reopened for editing.');
    } catch (err) {
      toast.error('Erro');
    }
  };

  // Merge scenes from chat history (recover lost scenes)
  const mergeChatScenes = async () => {
    if (!projectId) return;
    try {
      const r = await axios.post(`${API}/studio/projects/${projectId}/merge-chat-scenes`);
      if (r.data.recovered > 0) {
        // Reload project to get merged scenes
        const status = await axios.get(`${API}/studio/projects/${projectId}/status`);
        setScenes(status.data.scenes || []);
        setCharacters(status.data.characters || []);
        toast.success(lang === 'pt'
          ? `${r.data.recovered} cenas recuperadas! Total: ${r.data.total_scenes} cenas`
          : `${r.data.recovered} scenes recovered! Total: ${r.data.total_scenes} scenes`);
      } else {
        toast.info(lang === 'pt' ? 'Todas as cenas já estão no roteiro.' : 'All scenes already in screenplay.');
      }
    } catch (err) {
      toast.error(lang === 'pt' ? 'Erro ao unificar cenas' : 'Error merging scenes');
    }
  };

  // Detect if chat history mentions more scenes than currently in the editor
  const chatMentionsMoreScenes = (() => {
    if (!chatMessages.length || !scenes.length) return false;
    const sceneNums = new Set(scenes.map(s => s.scene_number));
    for (const m of chatMessages) {
      if (m.role !== 'assistant') continue;
      const matches = m.text.matchAll(/\*\*CENA\s+(\d+)\*\*/g);
      for (const match of matches) {
        if (!sceneNums.has(parseInt(match[1]))) return true;
      }
    }
    return false;
  })();

  // Generate production preview (pre-production only)
  const generatePreview = async () => {
    if (!projectId || scenes.length === 0) return;
    setPreviewLoading(true);
    setPreviewData(null);
    try {
      await axios.post(`${API}/studio/projects/${projectId}/generate-preview`);
      // Poll for preview completion
      const pollPreview = () => {
        axios.get(`${API}/studio/projects/${projectId}/preview`).then(r => {
          const d = r.data;
          if (d.preview_status === 'complete') {
            setPreviewData(d);
            setPreviewLoading(false);
            setShowPreview(true);
            toast.success(lang === 'pt' ? 'Design de produção pronto!' : 'Production design ready!');
          } else if (d.preview_status === 'error') {
            setPreviewLoading(false);
            toast.error(lang === 'pt' ? 'Erro ao gerar preview' : 'Preview generation failed');
          } else {
            setTimeout(pollPreview, 2000);
          }
        }).catch(() => {
          setPreviewLoading(false);
          toast.error(lang === 'pt' ? 'Erro ao verificar preview' : 'Preview check failed');
        });
      };
      setTimeout(pollPreview, 3000);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Preview failed'));
      setPreviewLoading(false);
    }
  };

  // Approve preview and start production
  const approveAndProduce = async () => {
    setShowPreview(false);
    startProduction();
  };

  // Start multi-scene production
  const startProduction = async () => {
    if (!projectId || scenes.length === 0) return;
    setGenerating(true);
    setStep(5);
    try {
      await axios.post(`${API}/studio/start-production`, {
        project_id: projectId,
        video_duration: 12,
        character_avatars: characterAvatars,
        visual_style: visualStyle,
      });
      startPolling(projectId);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Failed to start'));
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-3" data-testid="directed-studio">
      {/* Step Navigation — only when inside a project */}
      {step >= 1 && (
        <div className="flex items-center justify-between mb-1">
          <button onClick={() => { skipAutoResume.current = true; setStep(0); setProjectId(null); setViewingProject(null); loadProjects(); }}
            className="text-xs text-[#C9A84C] hover:underline flex items-center gap-1">
            ← {lang === 'pt' ? 'Projectos' : 'Projects'}
          </button>
          <p className="text-xs text-[#666] truncate max-w-[200px]">{projectName}</p>
        </div>
      )}
      {step >= 1 && (
        <div className="flex items-center justify-center gap-0 my-2 relative">
          {/* Timeline track */}
          <div className="absolute top-1/2 left-8 right-8 h-px bg-[#1A1A1A] -translate-y-1/2 z-0" />
          {STEPS.map((s, i) => {
            const isActive = step === s.n && !viewingProject;
            const isDone = step > s.n;
            return (
              <div key={s.n} className="flex-1 flex flex-col items-center relative z-10">
                <button onClick={() => { if (!generating) { setViewingProject(null); setStep(s.n); }}}
                  data-testid={`studio-step-${s.n}`}
                  className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-300 ${
                    isActive ? 'bg-[#C9A84C] text-black shadow-[0_0_16px_rgba(201,168,76,0.3)]' :
                    isDone ? 'bg-white text-black' :
                    'bg-[#111] text-[#555] border border-[#222] hover:border-[#444]'
                  }`}>
                  {isDone ? <Check size={12} strokeWidth={2.5} /> : <s.icon size={12} strokeWidth={1.5} />}
                </button>
                <span className={`mt-1 text-[11px] font-mono tracking-wider uppercase transition-colors ${
                  isActive ? 'text-[#C9A84C]' : isDone ? 'text-white/60' : 'text-[#333]'
                }`}>
                  {isActive ? s.label : <span className="hidden sm:inline">{s.label}</span>}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* ═══ STEP 0: Project List ═══ */}
      {step === 0 && !viewingProject && (
        <div className="space-y-3" data-testid="studio-project-list">

          {/* Analytics Panel */}
          {showAnalytics && analyticsData && (
            <div className="glass-card border border-[#C9A84C]/20 p-3 space-y-3" data-testid="studio-analytics-panel">
              <div className="flex items-center justify-between">
                <h3 className="text-[11px] font-bold text-white flex items-center gap-1.5">
                  <BarChart3 size={12} className="text-[#C9A84C]" />
                  {lang === 'pt' ? 'Relatório de Performance' : 'Performance Report'}
                </h3>
                <button onClick={() => setShowAnalytics(false)} className="text-[#666] hover:text-white">
                  <X size={12} />
                </button>
              </div>

              {/* Summary cards */}
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { label: lang === 'pt' ? 'Produções' : 'Productions', value: analyticsData.summary?.completed || 0, color: 'text-emerald-400' },
                  { label: lang === 'pt' ? 'Cenas' : 'Scenes', value: analyticsData.summary?.total_scenes_produced || 0, color: 'text-blue-400' },
                  { label: lang === 'pt' ? 'Vídeos' : 'Videos', value: analyticsData.summary?.total_videos_generated || 0, color: 'text-[#C9A84C]' },
                  { label: lang === 'pt' ? 'Erros' : 'Errors', value: analyticsData.summary?.errored || 0, color: 'text-red-400' },
                ].map((s, i) => (
                  <div key={i} className="rounded-lg bg-[#0A0A0A] border border-[#1A1A1A] p-2 text-center">
                    <p className={`text-sm font-bold ${s.color}`}>{s.value}</p>
                    <p className="text-[10px] text-[#666]">{s.label}</p>
                  </div>
                ))}
              </div>

              {/* Timing */}
              <div className="rounded-lg bg-[#0A0A0A] border border-[#1A1A1A] p-2 space-y-1.5">
                <p className="text-[11px] font-semibold text-[#999]">{lang === 'pt' ? 'TEMPOS MÉDIOS' : 'AVG TIMING'}</p>
                {[
                  { label: 'Agentes (Claude)', value: analyticsData.timing?.avg_agent_seconds, color: 'bg-purple-500' },
                  { label: 'Vídeos (Sora 2)', value: analyticsData.timing?.avg_video_seconds, color: 'bg-[#C9A84C]' },
                  { label: 'TOTAL', value: analyticsData.timing?.avg_total_seconds, color: 'bg-emerald-500' },
                ].map((t, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className={`h-1.5 w-1.5 rounded-full ${t.color}`} />
                    <span className="text-[11px] text-[#999] w-24">{t.label}</span>
                    <div className="flex-1 bg-[#111] rounded-full h-1.5">
                      <div className={`h-1.5 rounded-full ${t.color} transition-all`}
                        style={{ width: `${Math.min((t.value || 0) / Math.max(analyticsData.timing?.avg_total_seconds || 1, 1) * 100, 100)}%` }} />
                    </div>
                    <span className="text-[11px] font-mono text-white w-12 text-right">
                      {t.value ? (t.value > 60 ? `${(t.value/60).toFixed(1)}m` : `${t.value}s`) : '—'}
                    </span>
                  </div>
                ))}
              </div>

              {/* Pipeline versions */}
              <div className="flex gap-1.5">
                {[
                  { label: 'v1 seq', count: analyticsData.pipeline_versions?.v1_sequential || 0, color: 'border-red-500/30 text-red-400' },
                  { label: 'v2 batch', count: analyticsData.pipeline_versions?.v2_batched || 0, color: 'border-orange-500/30 text-orange-400' },
                  { label: 'v3 parallel', count: analyticsData.pipeline_versions?.v3_parallel_teams || 0, color: 'border-emerald-500/30 text-emerald-400' },
                ].map((v, i) => (
                  <div key={i} className={`flex-1 rounded-lg border bg-[#0A0A0A] p-1.5 text-center ${v.color}`}>
                    <p className="text-xs font-bold">{v.count}</p>
                    <p className="text-[10px]">{v.label}</p>
                  </div>
                ))}
              </div>

              {/* Cost savings */}
              {analyticsData.cost_estimate && (
                <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-2">
                  <p className="text-[11px] font-semibold text-emerald-400">{lang === 'pt' ? 'ECONOMIA' : 'SAVINGS'}</p>
                  <p className="text-[10px] text-[#999] mt-0.5">{analyticsData.cost_estimate.optimization_note}</p>
                </div>
              )}

              {/* Recommendations */}
              {analyticsData.recommendations?.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold text-[#999]">{lang === 'pt' ? 'RECOMENDAÇÕES' : 'RECOMMENDATIONS'}</p>
                  {analyticsData.recommendations.map((r, i) => (
                    <div key={i} className={`rounded-md px-2 py-1.5 text-[11px] border ${
                      r.type === 'critical' ? 'border-red-500/30 bg-red-500/5 text-red-300' :
                      r.type === 'warning' ? 'border-orange-500/30 bg-orange-500/5 text-orange-300' :
                      r.type === 'success' ? 'border-emerald-500/30 bg-emerald-500/5 text-emerald-300' :
                      'border-blue-500/30 bg-blue-500/5 text-blue-300'
                    }`}>{r.text}</div>
                  ))}
                </div>
              )}

              {/* Per-production breakdown */}
              {analyticsData.productions?.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold text-[#999]">{lang === 'pt' ? 'PRODUÇÕES (por velocidade)' : 'PRODUCTIONS (by speed)'}</p>
                  <div className="max-h-[120px] overflow-y-auto hide-scrollbar space-y-0.5">
                    {analyticsData.productions.map((p, i) => (
                      <div key={i} className="flex items-center gap-2 rounded-md bg-[#0A0A0A] px-2 py-1 border border-[#1A1A1A]">
                        <span className={`text-[10px] font-mono px-1 rounded ${
                          p.pipeline_version === 'v3' ? 'bg-emerald-500/20 text-emerald-400' :
                          p.pipeline_version === 'v2' ? 'bg-orange-500/20 text-orange-400' :
                          'bg-red-500/20 text-red-400'
                        }`}>{p.pipeline_version}</span>
                        <span className="text-[11px] text-white flex-1 truncate">{p.name}</span>
                        <span className="text-[10px] text-[#666]">{p.scenes}c</span>
                        <span className="text-[11px] font-mono text-[#C9A84C]">
                          {p.total_seconds ? (p.total_seconds > 60 ? `${(p.total_seconds/60).toFixed(1)}m` : `${p.total_seconds}s`) : '—'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* New Project + Analytics buttons */}
          {!showNewProject ? (
            <div className="flex gap-2">
              <button onClick={() => setShowNewProject(true)} data-testid="new-project-btn"
                className="flex-1 glass-card p-3 flex items-center gap-3 hover:border-[#C9A84C]/30 transition group border border-dashed border-[#333]">
                <div className="h-10 w-10 rounded-lg bg-[#C9A84C]/10 flex items-center justify-center group-hover:bg-[#C9A84C]/20 transition">
                  <Plus size={18} className="text-[#C9A84C]" />
                </div>
                <div className="text-left">
                  <p className="text-xs font-semibold text-white">{lang === 'pt' ? 'Novo Projecto' : 'New Project'}</p>
                  <p className="text-[11px] text-[#666]">{lang === 'pt' ? 'Crie uma nova produção com IA' : 'Create a new AI production'}</p>
                </div>
              </button>
              <button onClick={loadAnalytics} disabled={analyticsLoading} data-testid="analytics-btn"
                className="glass-card p-3 flex flex-col items-center justify-center gap-1 hover:border-[#C9A84C]/30 transition border border-[#333] w-16">
                {analyticsLoading ? <RefreshCw size={14} className="text-[#C9A84C] animate-spin" /> : <BarChart3 size={14} className="text-[#C9A84C]" />}
                <span className="text-[10px] text-[#666]">Analytics</span>
              </button>
            </div>
          ) : (
            <div className="glass-card p-3 space-y-2 border border-[#C9A84C]/20" data-testid="new-project-form">
              <h3 className="text-xs font-semibold text-white flex items-center gap-2">
                <Clapperboard size={12} className="text-[#C9A84C]" />
                {lang === 'pt' ? 'Novo Projecto' : 'New Project'}
              </h3>
              <input value={projectName} onChange={e => setProjectName(e.target.value)}
                placeholder={lang === 'pt' ? 'Nome do projecto (ex: A História de Abraão)' : 'Project name'}
                data-testid="new-project-name"
                className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-3 py-2 text-[11px] text-white outline-none focus:border-[#C9A84C]/50 placeholder-[#555]" />
              <textarea value={projectDesc} onChange={e => setProjectDesc(e.target.value)}
                placeholder={lang === 'pt' ? 'Descreva brevemente o projecto...' : 'Brief description...'}
                data-testid="new-project-desc"
                rows={2}
                className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-3 py-2 text-[10px] text-white outline-none focus:border-[#C9A84C]/50 placeholder-[#555] resize-none" />
              {/* Language + Audio Mode */}
              <div className="flex gap-2">
                <div className="flex-1">
                  <label className="text-[11px] text-[#666] uppercase tracking-wider mb-1 block">
                    {lang === 'pt' ? 'Idioma' : 'Language'}
                  </label>
                  <select value={projectLang} onChange={e => setProjectLang(e.target.value)}
                    data-testid="project-language-select"
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-2 py-1.5 text-[10px] text-white outline-none focus:border-[#C9A84C]/50">
                    <option value="pt">Portugu&ecirc;s</option>
                    <option value="en">English</option>
                    <option value="es">Espa&ntilde;ol</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="text-[11px] text-[#666] uppercase tracking-wider mb-1 block">
                    {lang === 'pt' ? 'Tipo de Áudio' : 'Audio Type'}
                  </label>
                  <select value={audioMode} onChange={e => setAudioMode(e.target.value)}
                    data-testid="project-audio-mode-select"
                    className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-2 py-1.5 text-[10px] text-white outline-none focus:border-[#C9A84C]/50">
                    <option value="narrated">{lang === 'pt' ? 'Narrado (voz em off)' : 'Narrated (voice-over)'}</option>
                    <option value="dubbed">{lang === 'pt' ? 'Dublado (vozes por personagem)' : 'Dubbed (per-character voices)'}</option>
                  </select>
                </div>
              </div>
              {/* Animation Style */}
              <div>
                <label className="text-[11px] text-[#666] uppercase tracking-wider mb-1 block">
                  {lang === 'pt' ? 'Estilo de Animação' : 'Animation Style'}
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { id: 'pixar_3d', label: '3D Pixar', desc: 'DreamWorks / Pixar', icon: '🎬' },
                    { id: 'cartoon_3d', label: '3D Cartoon', desc: 'Estilizado, cores vivas', icon: '🎨' },
                    { id: 'cartoon_2d', label: '2D Clássico', desc: 'Disney / Cartoon', icon: '✏️' },
                    { id: 'anime_2d', label: '2D Anime', desc: 'Estilo japonês', icon: '⛩️' },
                    { id: 'realistic', label: 'Cinematográfico', desc: 'Live action realista', icon: '📽️' },
                    { id: 'watercolor', label: 'Aquarela', desc: 'Pintura artística', icon: '🖌️' },
                  ].map(s => (
                    <button key={s.id} type="button"
                      data-testid={`animation-style-${s.id}`}
                      onClick={() => { setAnimationSub(s.id); setVisualStyle(s.id.includes('3d') ? 'animation' : s.id.includes('2d') ? (s.id === 'anime_2d' ? 'anime' : 'cartoon') : s.id === 'realistic' ? 'realistic' : 'watercolor'); }}
                      className={`p-2 rounded-lg border text-left text-xs transition-all ${
                        animationSub === s.id
                          ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10'
                          : 'border-[#222] bg-[#0A0A0A] hover:border-[#444]'
                      }`}>
                      <span className="text-sm">{s.icon}</span>
                      <div className={`font-medium mt-0.5 ${animationSub === s.id ? 'text-[#C9A84C]' : 'text-white'}`}>{s.label}</div>
                      <div className="text-[11px] text-[#555]">{s.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
              {/* Continuity Engine Toggle */}
              <div className="flex items-center justify-between p-2.5 rounded-lg border border-[#222] bg-[#0A0A0A]">
                <div>
                  <div className="text-[10px] font-medium text-white flex items-center gap-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#C9A84C]"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
                    {lang === 'pt' ? 'Motor de Continuidade' : 'Continuity Engine'}
                  </div>
                  <div className="text-[11px] text-[#666] mt-0.5">
                    {lang === 'pt'
                      ? 'Renderização sequencial com âncora visual, DNA de estilo, validação IA e color grading'
                      : 'Sequential rendering with visual anchoring, style DNA, AI validation & color grading'}
                  </div>
                </div>
                <button
                  type="button"
                  data-testid="continuity-mode-toggle"
                  onClick={() => setContinuityMode(!continuityMode)}
                  className={`w-10 h-5 rounded-full transition-all relative ${
                    continuityMode ? 'bg-[#C9A84C]' : 'bg-[#333]'
                  }`}
                >
                  <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-0.5 transition-all ${
                    continuityMode ? 'right-0.5' : 'left-0.5'
                  }`} />
                </button>
              </div>
              <div className="flex gap-2">
                <button onClick={() => { setShowNewProject(false); setProjectName(''); setProjectDesc(''); }}
                  className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
                  {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                </button>
                <button onClick={createNewProject} disabled={!projectName.trim()} data-testid="create-project-btn"
                  className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-semibold disabled:opacity-30 flex items-center justify-center gap-1">
                  <Sparkles size={10} /> {lang === 'pt' ? 'Criar Projecto' : 'Create Project'}
                </button>
              </div>
            </div>
          )}

          {allProjects.length > 0 && (
            <div className="space-y-1.5">
              {/* Search bar */}
              <div className="relative">
                <input
                  value={projectSearch}
                  onChange={e => setProjectSearch(e.target.value)}
                  placeholder={lang === 'pt' ? 'Buscar projecto...' : 'Search project...'}
                  data-testid="project-search-input"
                  className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg pl-3 pr-8 py-1.5 text-[10px] text-white outline-none focus:border-[#C9A84C]/50 placeholder-[#555]"
                />
                {projectSearch && (
                  <button onClick={() => setProjectSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-[#555] hover:text-white">
                    <X size={10} />
                  </button>
                )}
              </div>
              <p className="text-xs text-[#666] uppercase tracking-wider font-medium">
                {(() => {
                  const filtered = allProjects.filter(p => {
                    if (!projectSearch.trim()) return true;
                    const q = projectSearch.toLowerCase();
                    return (p.name || '').toLowerCase().includes(q) || (p.briefing || '').toLowerCase().includes(q);
                  });
                  return `${filtered.length} ${lang === 'pt' ? 'projectos' : 'projects'}${projectSearch ? ` (${allProjects.length} total)` : ''}`;
                })()}
              </p>
              {allProjects.filter(p => {
                if (!projectSearch.trim()) return true;
                const q = projectSearch.toLowerCase();
                return (p.name || '').toLowerCase().includes(q) || (p.briefing || '').toLowerCase().includes(q);
              }).map(proj => {
                const sl = STATUS_LABELS[proj.status] || STATUS_LABELS.draft;
                const scenesCount = (proj.scenes || []).length;
                const videosCount = (proj.outputs || []).filter(o => o.type === 'video').length;
                const vid = proj.outputs?.find(o => o.type === 'video' && o.label === 'complete') || proj.outputs?.find(o => o.type === 'video');
                const milestones = proj.milestones || [];
                return (
                  <div key={proj.id} onClick={() => resumeProject(proj)} data-testid={`project-${proj.id}`}
                    className="w-full glass-card p-2.5 hover:border-[#C9A84C]/30 transition text-left group relative cursor-pointer">
                    <div className="flex items-center gap-2.5">
                      <div className="h-14 w-12 rounded-lg bg-[#111] flex-shrink-0 overflow-hidden border border-[#222] relative">
                        {vid ? (
                          <>
                            <video src={vid.url} className="w-full h-full object-cover" muted />
                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                              <Play size={12} className="text-[#C9A84C]" />
                            </div>
                          </>
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <Film size={16} className="text-[#333]" />
                          </div>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[11px] font-semibold text-white truncate group-hover:text-[#C9A84C] transition">
                          {proj.name || proj.briefing?.slice(0, 40) || 'Sem nome'}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className={`text-[10px] font-medium ${sl.color}`}>{sl[lang] || sl.en}</span>
                          {scenesCount > 0 && <span className="text-[10px] text-[#555]">{scenesCount} {lang === 'pt' ? 'cenas' : 'scenes'}</span>}
                          {videosCount > 0 && <span className="text-[10px] text-emerald-500">{videosCount} {lang === 'pt' ? 'vídeos' : 'videos'}</span>}
                        </div>
                      </div>
                      <div className="flex flex-col items-center gap-1 flex-shrink-0">
                        {['starting', 'running_agents'].includes(proj.status) ? (
                          <RefreshCw size={12} className="text-orange-400 animate-spin" />
                        ) : proj.status === 'complete' ? (
                          <Check size={12} className="text-emerald-400" />
                        ) : null}
                        {/* Action buttons */}
                        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          {proj.status === 'error' && (proj.scenes || []).length > 0 && (
                            <button onClick={e => resumeProduction(e, proj)} data-testid={`resume-project-${proj.id}`}
                              title={lang === 'pt' ? 'Retomar produção' : 'Resume production'}
                              className="h-5 w-5 rounded flex items-center justify-center text-orange-400 hover:text-orange-300 hover:bg-orange-500/10 transition">
                              <RefreshCw size={10} />
                            </button>
                          )}
                          <button onClick={e => deleteProject(e, proj.id)} data-testid={`delete-project-${proj.id}`}
                            title={lang === 'pt' ? 'Eliminar projecto' : 'Delete project'}
                            className="h-5 w-5 rounded flex items-center justify-center text-red-500/50 hover:text-red-400 hover:bg-red-500/10 transition">
                            <Trash2 size={10} />
                          </button>
                        </div>
                      </div>
                    </div>
                    {/* Milestones */}
                    {milestones.length > 0 && (
                      <div className="mt-1.5 pt-1.5 border-t border-[#1A1A1A] flex flex-wrap gap-x-3 gap-y-0.5">
                        {milestones.map((ms, mi) => (
                          <span key={mi} className="flex items-center gap-1 text-[10px] text-[#666]">
                            <Check size={7} className="text-emerald-500 flex-shrink-0" />
                            {ms.label?.split('—')[0]?.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Loading state */}
          {projectsLoading && allProjects.length === 0 && (
            <div className="flex items-center justify-center gap-2 py-6">
              <RefreshCw size={14} className="text-[#C9A84C] animate-spin" />
              <span className="text-[10px] text-[#666]">{lang === 'pt' ? 'Carregando projectos...' : 'Loading projects...'}</span>
            </div>
          )}

          {/* Empty state */}
          {!projectsLoading && allProjects.length === 0 && (
            <div className="text-center py-6">
              <Film size={24} className="text-[#333] mx-auto mb-2" />
              <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Nenhum projecto ainda. Crie o primeiro!' : 'No projects yet. Create your first!'}</p>
            </div>
          )}
        </div>
      )}

      {/* Viewing Past Project */}
      {viewingProject && (
        <div className="glass-card p-3 space-y-2" data-testid="viewing-past-project">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
              <Film size={12} className="text-[#C9A84C]" />
              {viewingProject.name || viewingProject.briefing?.slice(0, 40)}
            </h3>
            <button onClick={() => setViewingProject(null)} className="text-[#666] hover:text-white"><X size={12} /></button>
          </div>
          {viewingProject.outputs?.map((out, i) => (
            <div key={out.id || i} className="rounded-lg overflow-hidden border border-white/5">
              {out.type === 'video' && (
                <div className="relative bg-black">
                  <video controls autoPlay={i === 0} className="w-full rounded-lg" src={out.url} />
                  <span className="absolute top-1 left-1 bg-black/70 text-[10px] text-[#C9A84C] font-bold px-1.5 py-0.5 rounded">
                    {out.label === 'complete' ? 'FILME COMPLETO' : `CENA ${out.scene_number}`}
                  </span>
                </div>
              )}
              <div className="p-1.5 flex items-center justify-between">
                <span className="text-[11px] text-[#666]">{out.label === 'complete' ? `${out.duration}s total` : `Cena ${out.scene_number} • 12s`}</span>
                <a href={out.url} download className="btn-gold rounded px-2 py-1 text-[11px] font-semibold flex items-center gap-1">
                  <Download size={10} /> Download
                </a>
              </div>
            </div>
          ))}
          <button onClick={() => setViewingProject(null)} className="w-full rounded-lg border border-[#333] py-1.5 text-[10px] text-[#999] hover:text-white transition">
            ← {lang === 'pt' ? 'Voltar' : 'Back'}
          </button>
        </div>
      )}

      {/* ═══ STEP 1: Screenwriter Chat ═══ */}
      {step === 1 && !viewingProject && (
        <div className="glass-card p-3 space-y-2" data-testid="studio-step-script">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#8B6914] flex items-center justify-center">
              <MessageSquare size={12} className="text-black" />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-white">{lang === 'pt' ? 'Redator & Pesquisador' : 'Screenwriter'}</h3>
              <p className="text-[11px] text-[#666]">{lang === 'pt' ? 'Descreva a história que quer criar' : 'Describe the story you want to create'}</p>
            </div>
          </div>

          {/* Chat messages */}
          <div className="max-h-[350px] overflow-y-auto space-y-2 hide-scrollbar" data-testid="screenwriter-chat">
            {chatMessages.length === 0 && (
              <div className="text-center py-6 space-y-2">
                <Sparkles size={20} className="mx-auto text-[#333]" />
                <p className="text-[10px] text-[#555]">{lang === 'pt'
                  ? 'Ex: "Crie a história completa de Isaque e Jacó da Bíblia, com todas as cenas importantes"'
                  : 'Ex: "Create the complete story of Isaac and Jacob from the Bible"'
                }</p>
              </div>
            )}
            {chatMessages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[10px] leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20'
                    : 'bg-[#111] text-[#ccc] border border-[#222]'
                }`}>
                  <pre className="whitespace-pre-wrap font-sans">{m.text}</pre>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-[#111] border border-[#222] rounded-lg px-3 py-2 flex items-center gap-2">
                  <RefreshCw size={10} className="animate-spin text-[#C9A84C]" />
                  <span className="text-xs text-[#666]">{lang === 'pt' ? 'Pesquisando e escrevendo...' : 'Researching and writing...'}</span>
                </div>
              </div>
            )}
            {/* Retry button when stuck or error */}
            {!chatLoading && chatMessages.length > 0 && projectId && (
              chatMessages[chatMessages.length - 1]?.text?.includes('demorando') ||
              chatMessages[chatMessages.length - 1]?.text?.includes('Erro')
            ) && (
              <div className="flex justify-center">
                <button onClick={retryChat} data-testid="retry-chat-btn"
                  className="flex items-center gap-1.5 rounded-lg px-4 py-2 text-[10px] font-medium bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
                  <RefreshCw size={10} />
                  {lang === 'pt' ? 'Tentar Novamente' : 'Try Again'}
                </button>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat input */}
          <div className="flex gap-2">
            <input data-testid="screenwriter-input" value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendChat()}
              placeholder={lang === 'pt' ? 'Descreva a história...' : 'Describe the story...'}
              className="flex-1 bg-[#0A0A0A] border border-[#222] rounded-lg px-3 py-2 text-xs text-white placeholder-[#555] outline-none focus:border-[#C9A84C]/40"
              disabled={chatLoading}
            />
            <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()} data-testid="send-chat-btn"
              className="btn-gold rounded-lg px-3 py-2 disabled:opacity-30">
              <Send size={14} />
            </button>
          </div>

          {/* Scene Editor - Full editable list */}
          {scenes.length > 0 && (
            <div className="space-y-2 border-t border-[#222] pt-2">
              {/* Merge alert banner */}
              {chatMentionsMoreScenes && !screenplayApproved && (
                <button onClick={mergeChatScenes} data-testid="merge-chat-scenes-btn"
                  className="w-full rounded-lg py-2 px-3 text-xs font-medium transition-all
                    bg-amber-500/10 border border-amber-500/30 text-amber-400 hover:bg-amber-500/20
                    flex items-center justify-center gap-2">
                  <RefreshCw size={12} />
                  {lang === 'pt'
                    ? 'Cenas faltando! Clique para unificar todas as cenas do roteiro'
                    : 'Missing scenes! Click to merge all scenes from screenplay'}
                </button>
              )}
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-[#C9A84C]">{scenes.length} {lang === 'pt' ? 'cenas planejadas' : 'scenes planned'} ({scenes.length * 12}s)</span>
                {screenplayApproved ? (
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] text-emerald-400 flex items-center gap-1">
                      <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
                      {lang === 'pt' ? 'Aprovado' : 'Approved'}
                    </span>
                    <button onClick={unapproveScreenplay} className="text-[10px] text-[#555] hover:text-[#888] underline">
                      {lang === 'pt' ? 'Reabrir' : 'Reopen'}
                    </button>
                  </div>
                ) : (
                  <span className="text-[11px] text-[#666]">{lang === 'pt' ? 'Revise e aprove para continuar' : 'Review and approve to continue'}</span>
                )}
              </div>
              <div className="space-y-1.5 max-h-[400px] overflow-y-auto pr-1">
                {/* Add scene at the beginning */}
                {!screenplayApproved && (
                  <div className="flex justify-center">
                    <button onClick={() => { setAddingSceneAt(1); setNewSceneForm({ title: '', description: '', dialogue: '', emotion: '', camera: '', characters_in_scene: [] }); setNewSceneMode('manual'); setAiSceneHint(''); }}
                      data-testid="add-scene-top"
                      className="text-[10px] text-[#555] hover:text-[#C9A84C] transition-colors flex items-center gap-1 px-2 py-0.5 rounded border border-dashed border-[#333] hover:border-[#C9A84C]/40">
                      <Plus size={10} /> {lang === 'pt' ? 'Inserir cena aqui' : 'Insert scene here'}
                    </button>
                  </div>
                )}

                {scenes.map((s, sceneIdx) => {
                  const isEditing = editingScene === s.scene_number;
                  return (
                    <Fragment key={s.scene_number}>
                      {/* Add Scene Form (shown when addingSceneAt matches this position) */}
                      {addingSceneAt === s.scene_number && (
                        <div className="rounded-lg border-2 border-dashed border-[#C9A84C]/40 bg-[#0D0D0A] p-3 space-y-2" data-testid={`new-scene-form-${s.scene_number}`}>
                          <div className="flex items-center justify-between">
                            <p className="text-[11px] font-bold text-[#C9A84C]">{lang === 'pt' ? 'Nova Cena' : 'New Scene'}</p>
                            <div className="flex gap-1">
                              <button onClick={() => setNewSceneMode('manual')} className={`text-[9px] px-2 py-0.5 rounded ${newSceneMode === 'manual' ? 'bg-[#C9A84C]/20 text-[#C9A84C]' : 'text-[#555] hover:text-[#888]'}`}>Manual</button>
                              <button onClick={() => setNewSceneMode('ai')} className={`text-[9px] px-2 py-0.5 rounded flex items-center gap-0.5 ${newSceneMode === 'ai' ? 'bg-[#C9A84C]/20 text-[#C9A84C]' : 'text-[#555] hover:text-[#888]'}`}><Sparkles size={8} /> IA</button>
                              <button onClick={() => setAddingSceneAt(null)} className="text-[9px] text-[#555] hover:text-red-400 ml-1"><X size={12} /></button>
                            </div>
                          </div>

                          {newSceneMode === 'ai' && (
                            <div className="space-y-1.5">
                              <textarea value={aiSceneHint} onChange={e => setAiSceneHint(e.target.value)} placeholder={lang === 'pt' ? 'Descreva a ideia da cena (opcional)...' : 'Describe the scene idea (optional)...'} rows={2}
                                className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" data-testid="ai-scene-hint" />
                              <button onClick={() => generateSceneAI(s.scene_number)} disabled={aiSceneLoading}
                                data-testid="generate-scene-ai-btn"
                                className="w-full btn-gold rounded py-1 text-[10px] font-semibold flex items-center justify-center gap-1 disabled:opacity-50">
                                {aiSceneLoading ? <><RefreshCw size={10} className="animate-spin" /> {lang === 'pt' ? 'Gerando...' : 'Generating...'}</> : <><Sparkles size={10} /> {lang === 'pt' ? 'Gerar com IA' : 'Generate with AI'}</>}
                              </button>
                            </div>
                          )}

                          <div>
                            <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Título' : 'Title'}</label>
                            <input value={newSceneForm.title} onChange={e => setNewSceneForm(p => ({ ...p, title: e.target.value }))}
                              className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" data-testid="new-scene-title" />
                          </div>
                          <div>
                            <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Descrição' : 'Description'}</label>
                            <textarea value={newSceneForm.description} onChange={e => setNewSceneForm(p => ({ ...p, description: e.target.value }))} rows={2}
                              className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" data-testid="new-scene-desc" />
                          </div>
                          <div>
                            <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Narração/Diálogo' : 'Narration/Dialogue'}</label>
                            <textarea value={newSceneForm.dialogue} onChange={e => setNewSceneForm(p => ({ ...p, dialogue: e.target.value }))} rows={2}
                              className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" data-testid="new-scene-dialogue" />
                          </div>
                          <div className="grid grid-cols-2 gap-1.5">
                            <div>
                              <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Emoção' : 'Emotion'}</label>
                              <input value={newSceneForm.emotion} onChange={e => setNewSceneForm(p => ({ ...p, emotion: e.target.value }))}
                                className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" data-testid="new-scene-emotion" />
                            </div>
                            <div>
                              <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Câmera' : 'Camera'}</label>
                              <input value={newSceneForm.camera} onChange={e => setNewSceneForm(p => ({ ...p, camera: e.target.value }))}
                                className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" data-testid="new-scene-camera" />
                            </div>
                          </div>
                          {/* Characters selection for new scene */}
                          {characters.length > 0 && (
                            <div>
                              <label className="text-[10px] text-[#666] block mb-1">{lang === 'pt' ? 'Personagens' : 'Characters'}</label>
                              <div className="flex flex-wrap gap-1">
                                {characters.map((char) => {
                                  const sel = newSceneForm.characters_in_scene.includes(char.name);
                                  return (
                                    <button key={char.name} type="button"
                                      onClick={() => setNewSceneForm(p => ({
                                        ...p,
                                        characters_in_scene: sel ? p.characters_in_scene.filter(c => c !== char.name) : [...p.characters_in_scene, char.name]
                                      }))}
                                      className={`flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[9px] font-medium border ${sel ? 'bg-[#C9A84C]/15 border-[#C9A84C]/40 text-[#C9A84C]' : 'bg-[#111] border-[#333] text-[#555]'}`}>
                                      {sel ? <Check size={7} /> : <Plus size={7} />} {char.name}
                                    </button>
                                  );
                                })}
                              </div>
                            </div>
                          )}
                          <button onClick={() => addScene(s.scene_number)} disabled={addingSceneLoading || !newSceneForm.title.trim()}
                            data-testid="save-new-scene-btn"
                            className="w-full btn-gold rounded-lg py-1.5 text-xs font-semibold disabled:opacity-50 flex items-center justify-center gap-1">
                            {addingSceneLoading ? <><RefreshCw size={10} className="animate-spin" /> {lang === 'pt' ? 'Salvando...' : 'Saving...'}</> : <><Plus size={10} /> {lang === 'pt' ? 'Adicionar Cena' : 'Add Scene'}</>}
                          </button>
                        </div>
                      )}

                    <div className="rounded-lg border border-[#1A1A1A] bg-[#0A0A0A] p-2 space-y-1" data-testid={`scene-card-${s.scene_number}`}>
                      <div className="flex items-center justify-between">
                        <p className="text-[11px] font-bold text-[#C9A84C]">CENA {s.scene_number} — {s.time_start}-{s.time_end}</p>
                        <div className="flex items-center gap-0.5">
                          {!screenplayApproved && (
                            <>
                              <button onClick={() => moveScene(s.scene_number, 'up')} disabled={sceneIdx === 0}
                                data-testid={`move-scene-up-${s.scene_number}`}
                                className="text-[#555] hover:text-[#C9A84C] disabled:opacity-20 disabled:hover:text-[#555] p-0.5 transition-colors" title={lang === 'pt' ? 'Mover acima' : 'Move up'}>
                                <ChevronDown size={12} className="rotate-180" />
                              </button>
                              <button onClick={() => moveScene(s.scene_number, 'down')} disabled={sceneIdx === scenes.length - 1}
                                data-testid={`move-scene-down-${s.scene_number}`}
                                className="text-[#555] hover:text-[#C9A84C] disabled:opacity-20 disabled:hover:text-[#555] p-0.5 transition-colors" title={lang === 'pt' ? 'Mover abaixo' : 'Move down'}>
                                <ChevronDown size={12} />
                              </button>
                              <button onClick={() => deleteScene(s.scene_number)}
                                data-testid={`delete-scene-${s.scene_number}`}
                                className="text-[#555] hover:text-red-400 p-0.5 transition-colors" title={lang === 'pt' ? 'Eliminar cena' : 'Delete scene'}>
                                <X size={12} />
                              </button>
                            </>
                          )}
                          <button
                            data-testid={`edit-scene-${s.scene_number}`}
                            onClick={() => {
                              if (isEditing) { setEditingScene(null); setEditSceneForm({}); }
                              else { setEditingScene(s.scene_number); setEditSceneForm({ title: s.title, description: s.description, dialogue: s.dialogue, emotion: s.emotion, camera: s.camera, characters_in_scene: s.characters_in_scene || [] }); }
                            }}
                            className="text-[11px] text-[#C9A84C] hover:text-white transition-colors px-1.5 py-0.5 rounded border border-[#333] hover:border-[#C9A84C]/40"
                          >
                            {isEditing ? (lang === 'pt' ? 'Cancelar' : 'Cancel') : (lang === 'pt' ? 'Editar' : 'Edit')}
                          </button>
                        </div>
                      </div>

                      {isEditing ? (
                        <div className="space-y-1.5">
                          <div>
                            <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Título' : 'Title'}</label>
                            <input value={editSceneForm.title || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, title: e.target.value }))}
                              className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" data-testid={`edit-title-${s.scene_number}`} />
                          </div>
                          <div>
                            <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Descrição da Cena' : 'Scene Description'}</label>
                            <textarea value={editSceneForm.description || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, description: e.target.value }))}
                              rows={2} className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" data-testid={`edit-desc-${s.scene_number}`} />
                          </div>
                          <div>
                            <label className="text-[10px] text-[#666] block mb-0.5">{audioMode === 'dubbed' ? (lang === 'pt' ? 'Diálogos dos Personagens' : 'Character Dialogues') : (lang === 'pt' ? 'Narração' : 'Narration')}</label>
                            <textarea value={editSceneForm.dialogue || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, dialogue: e.target.value }))}
                              rows={3} className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" data-testid={`edit-dialogue-${s.scene_number}`} />
                          </div>
                          <div className="grid grid-cols-2 gap-1.5">
                            <div>
                              <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Emoção' : 'Emotion'}</label>
                              <input value={editSceneForm.emotion || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, emotion: e.target.value }))}
                                className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" data-testid={`edit-emotion-${s.scene_number}`} />
                            </div>
                            <div>
                              <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Câmera' : 'Camera'}</label>
                              <input value={editSceneForm.camera || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, camera: e.target.value }))}
                                className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" data-testid={`edit-camera-${s.scene_number}`} />
                            </div>
                          </div>
                          {/* Characters in scene selector */}
                          <div>
                            <label className="text-[10px] text-[#666] block mb-1">{lang === 'pt' ? 'Personagens na Cena' : 'Characters in Scene'}</label>
                            <div className="flex flex-wrap gap-1.5">
                              {characters.map((char) => {
                                const isSelected = (editSceneForm.characters_in_scene || []).includes(char.name);
                                return (
                                  <button key={char.name} type="button"
                                    data-testid={`scene-char-toggle-${s.scene_number}-${char.name}`}
                                    onClick={() => {
                                      setEditSceneForm(prev => {
                                        const current = prev.characters_in_scene || [];
                                        return {
                                          ...prev,
                                          characters_in_scene: isSelected
                                            ? current.filter(c => c !== char.name)
                                            : [...current, char.name]
                                        };
                                      });
                                    }}
                                    className={`flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-medium transition-all border ${
                                      isSelected
                                        ? 'bg-[#C9A84C]/15 border-[#C9A84C]/40 text-[#C9A84C]'
                                        : 'bg-[#111] border-[#333] text-[#666] hover:border-[#555] hover:text-[#999]'
                                    }`}>
                                    {isSelected ? <Check size={8} /> : <Plus size={8} />}
                                    {char.name}
                                  </button>
                                );
                              })}
                              {characters.length === 0 && (
                                <span className="text-[10px] text-[#555] italic">
                                  {lang === 'pt' ? 'Nenhum personagem definido ainda' : 'No characters defined yet'}
                                </span>
                              )}
                            </div>
                          </div>
                          <button onClick={() => saveSceneEdit(s.scene_number)} data-testid={`save-scene-${s.scene_number}`}
                            className="w-full btn-gold rounded-lg py-1 text-xs font-semibold">
                            {lang === 'pt' ? 'Salvar Alterações' : 'Save Changes'}
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-0.5">
                          <p className="text-xs text-white font-medium">{s.title}</p>
                          <p className="text-[11px] text-[#888]">{s.description}</p>
                          <p className="text-[11px] text-[#AAA] italic mt-0.5">{s.dialogue}</p>
                          <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                            {s.emotion && <span className="text-[10px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">{s.emotion}</span>}
                            {s.camera && <span className="text-[10px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded">{s.camera}</span>}
                          </div>
                          {s.characters_in_scene?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {s.characters_in_scene.map((charName) => (
                                <span key={charName} className="inline-flex items-center gap-0.5 text-[10px] bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20 rounded-full px-1.5 py-0.5">
                                  <Users size={8} />
                                  {charName}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Insert scene button after this scene */}
                    {!screenplayApproved && (
                      <div className="flex justify-center py-0.5">
                        <button onClick={() => { setAddingSceneAt(s.scene_number + 1); setNewSceneForm({ title: '', description: '', dialogue: '', emotion: '', camera: '', characters_in_scene: [] }); setNewSceneMode('manual'); setAiSceneHint(''); }}
                          data-testid={`add-scene-after-${s.scene_number}`}
                          className="text-[10px] text-[#555] hover:text-[#C9A84C] transition-colors flex items-center gap-1 px-2 py-0.5 rounded border border-dashed border-[#333] hover:border-[#C9A84C]/40">
                          <Plus size={10} /> {lang === 'pt' ? 'Inserir cena aqui' : 'Insert scene here'}
                        </button>
                      </div>
                    )}
                    </Fragment>
                  );
                })}

                {/* Add scene form at the END of the list */}
                {addingSceneAt === scenes.length + 1 && (
                  <div className="rounded-lg border-2 border-dashed border-[#C9A84C]/40 bg-[#0D0D0A] p-3 space-y-2" data-testid="new-scene-form-end">
                    <div className="flex items-center justify-between">
                      <p className="text-[11px] font-bold text-[#C9A84C]">{lang === 'pt' ? 'Nova Cena' : 'New Scene'}</p>
                      <div className="flex gap-1">
                        <button onClick={() => setNewSceneMode('manual')} className={`text-[9px] px-2 py-0.5 rounded ${newSceneMode === 'manual' ? 'bg-[#C9A84C]/20 text-[#C9A84C]' : 'text-[#555] hover:text-[#888]'}`}>Manual</button>
                        <button onClick={() => setNewSceneMode('ai')} className={`text-[9px] px-2 py-0.5 rounded flex items-center gap-0.5 ${newSceneMode === 'ai' ? 'bg-[#C9A84C]/20 text-[#C9A84C]' : 'text-[#555] hover:text-[#888]'}`}><Sparkles size={8} /> IA</button>
                        <button onClick={() => setAddingSceneAt(null)} className="text-[9px] text-[#555] hover:text-red-400 ml-1"><X size={12} /></button>
                      </div>
                    </div>
                    {newSceneMode === 'ai' && (
                      <div className="space-y-1.5">
                        <textarea value={aiSceneHint} onChange={e => setAiSceneHint(e.target.value)} placeholder={lang === 'pt' ? 'Descreva a ideia da cena (opcional)...' : 'Describe the scene idea (optional)...'} rows={2}
                          className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" />
                        <button onClick={() => generateSceneAI(scenes.length + 1)} disabled={aiSceneLoading}
                          className="w-full btn-gold rounded py-1 text-[10px] font-semibold flex items-center justify-center gap-1 disabled:opacity-50">
                          {aiSceneLoading ? <><RefreshCw size={10} className="animate-spin" /> {lang === 'pt' ? 'Gerando...' : 'Generating...'}</> : <><Sparkles size={10} /> {lang === 'pt' ? 'Gerar com IA' : 'Generate with AI'}</>}
                        </button>
                      </div>
                    )}
                    <div>
                      <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Título' : 'Title'}</label>
                      <input value={newSceneForm.title} onChange={e => setNewSceneForm(p => ({ ...p, title: e.target.value }))}
                        className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" />
                    </div>
                    <div>
                      <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Descrição' : 'Description'}</label>
                      <textarea value={newSceneForm.description} onChange={e => setNewSceneForm(p => ({ ...p, description: e.target.value }))} rows={2}
                        className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" />
                    </div>
                    <div>
                      <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Narração/Diálogo' : 'Narration/Dialogue'}</label>
                      <textarea value={newSceneForm.dialogue} onChange={e => setNewSceneForm(p => ({ ...p, dialogue: e.target.value }))} rows={2}
                        className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none resize-none" />
                    </div>
                    <div className="grid grid-cols-2 gap-1.5">
                      <div>
                        <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Emoção' : 'Emotion'}</label>
                        <input value={newSceneForm.emotion} onChange={e => setNewSceneForm(p => ({ ...p, emotion: e.target.value }))}
                          className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" />
                      </div>
                      <div>
                        <label className="text-[10px] text-[#666] block mb-0.5">{lang === 'pt' ? 'Câmera' : 'Camera'}</label>
                        <input value={newSceneForm.camera} onChange={e => setNewSceneForm(p => ({ ...p, camera: e.target.value }))}
                          className="w-full bg-[#111] border border-[#333] rounded px-2 py-1 text-xs text-white focus:border-[#C9A84C] outline-none" />
                      </div>
                    </div>
                    {characters.length > 0 && (
                      <div>
                        <label className="text-[10px] text-[#666] block mb-1">{lang === 'pt' ? 'Personagens' : 'Characters'}</label>
                        <div className="flex flex-wrap gap-1">
                          {characters.map((char) => {
                            const sel = newSceneForm.characters_in_scene.includes(char.name);
                            return (
                              <button key={char.name} type="button"
                                onClick={() => setNewSceneForm(p => ({
                                  ...p, characters_in_scene: sel ? p.characters_in_scene.filter(c => c !== char.name) : [...p.characters_in_scene, char.name]
                                }))}
                                className={`flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[9px] font-medium border ${sel ? 'bg-[#C9A84C]/15 border-[#C9A84C]/40 text-[#C9A84C]' : 'bg-[#111] border-[#333] text-[#555]'}`}>
                                {sel ? <Check size={7} /> : <Plus size={7} />} {char.name}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    <button onClick={() => addScene(scenes.length + 1)} disabled={addingSceneLoading || !newSceneForm.title.trim()}
                      className="w-full btn-gold rounded-lg py-1.5 text-xs font-semibold disabled:opacity-50 flex items-center justify-center gap-1">
                      {addingSceneLoading ? <><RefreshCw size={10} className="animate-spin" /> {lang === 'pt' ? 'Salvando...' : 'Saving...'}</> : <><Plus size={10} /> {lang === 'pt' ? 'Adicionar Cena' : 'Add Scene'}</>}
                    </button>
                  </div>
                )}
              </div>
              <div className="flex gap-2 pt-1">
                {!screenplayApproved ? (
                  <button onClick={approveScreenplay} data-testid="approve-screenplay-btn"
                    className="flex-1 rounded-lg py-2 text-[10px] font-bold transition-all
                      bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20
                      flex items-center justify-center gap-1.5">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
                    {lang === 'pt' ? 'Aprovar Roteiro' : 'Approve Screenplay'}
                  </button>
                ) : (
                  <button onClick={() => setStep(2)} data-testid="go-to-characters"
                    className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-bold flex items-center justify-center gap-1.5">
                    {lang === 'pt' ? 'Personagens' : 'Characters'} →
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ STEP 2: Characters / Avatars ═══ */}
      {step === 2 && !viewingProject && (
        <div className="glass-card p-3 space-y-3" data-testid="studio-step-characters">
          <h3 className="text-xs font-semibold text-white flex items-center gap-2">
            <Users size={12} className="text-[#C9A84C]" />
            {lang === 'pt' ? 'Personagens' : 'Characters'}
          </h3>
          <p className="text-xs text-[#666]">
            {lang === 'pt' ? 'Crie, edite ou importe personagens da biblioteca' : 'Create, edit or import characters from library'}
          </p>

          <div className="space-y-2">
            {characters.map((char, ci) => (
              <div key={char.name || ci} className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2.5">
                {/* Character header */}
                {editingChar === ci ? (
                  /* ── Inline Edit Mode ── */
                  <div className="space-y-2 mb-2">
                    <div className="flex gap-2">
                      <input value={editForm.name} onChange={e => setEditForm(p => ({ ...p, name: e.target.value }))}
                        placeholder={lang === 'pt' ? 'Nome' : 'Name'}
                        data-testid={`edit-char-name-${ci}`}
                        className="flex-1 bg-[#111] border border-[#333] rounded px-2 py-1 text-[10px] text-white outline-none focus:border-[#C9A84C]/50" />
                      <input value={editForm.age} onChange={e => setEditForm(p => ({ ...p, age: e.target.value }))}
                        placeholder={lang === 'pt' ? 'Idade' : 'Age'}
                        className="w-16 bg-[#111] border border-[#333] rounded px-2 py-1 text-[10px] text-white outline-none focus:border-[#C9A84C]/50" />
                      <input value={editForm.role} onChange={e => setEditForm(p => ({ ...p, role: e.target.value }))}
                        placeholder={lang === 'pt' ? 'Papel' : 'Role'}
                        className="w-24 bg-[#111] border border-[#333] rounded px-2 py-1 text-[10px] text-white outline-none focus:border-[#C9A84C]/50" />
                    </div>
                    <textarea value={editForm.description} onChange={e => setEditForm(p => ({ ...p, description: e.target.value }))}
                      placeholder={lang === 'pt' ? 'Descrição visual do personagem...' : 'Visual description...'}
                      data-testid={`edit-char-desc-${ci}`}
                      rows={2}
                      className="w-full bg-[#111] border border-[#333] rounded px-2 py-1.5 text-xs text-white outline-none focus:border-[#C9A84C]/50 resize-none" />
                    <div className="flex gap-1.5">
                      <button onClick={saveEditChar} data-testid={`save-char-${ci}`}
                        className="flex items-center gap-1 bg-[#C9A84C]/15 border border-[#C9A84C]/30 text-[#C9A84C] rounded px-2 py-1 text-[11px] font-medium hover:bg-[#C9A84C]/25 transition">
                        <Save size={9} /> {lang === 'pt' ? 'Salvar' : 'Save'}
                      </button>
                      <button onClick={() => setEditingChar(null)}
                        className="flex items-center gap-1 border border-[#333] text-[#888] rounded px-2 py-1 text-[11px] hover:text-white transition">
                        <X size={9} /> {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                      </button>
                    </div>
                  </div>
                ) : (
                  /* ── View Mode ── */
                  <div className="flex items-start gap-2 mb-2">
                    {characterAvatars[char.name] ? (
                      <img src={resolveImageUrl(characterAvatars[char.name])} alt="" loading="lazy" decoding="async" className="h-12 w-10 rounded-lg object-cover border border-[#C9A84C]/30 flex-shrink-0" />
                    ) : (
                      <div className="h-12 w-10 rounded-lg bg-[#1A1A1A] flex items-center justify-center border border-dashed border-[#333] flex-shrink-0">
                        <Users size={14} className="text-[#444]" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <p className="text-[11px] font-bold text-white">{char.name}</p>
                        {!characterAvatars[char.name] && (
                          <span className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 rounded px-1 py-0.5">
                            {lang === 'pt' ? 'Sem personagem' : 'No character'}
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#888] leading-relaxed mt-0.5">{char.description}</p>
                      <p className="text-[10px] text-[#555] mt-0.5">{char.age} • {char.role}</p>
                    </div>
                    {/* Action buttons */}
                    <div className="flex flex-col gap-1 flex-shrink-0">
                      <button onClick={() => copyPrompt(char)} data-testid={`copy-prompt-${ci}`}
                        title={lang === 'pt' ? 'Copiar prompt' : 'Copy prompt'}
                        className="flex items-center gap-1 border border-[#333] text-[#888] rounded px-1.5 py-1 text-[10px] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
                        <Copy size={9} /> <span className="hidden sm:inline">{lang === 'pt' ? 'Copiar' : 'Copy'}</span>
                      </button>
                      <button onClick={() => {
                        // If character has a linked avatar, open edit mode; otherwise create mode
                        const linkedUrl = characterAvatars[char.name];
                        const linkedAv = linkedUrl && projectAvatars.find(a => a.url === linkedUrl);
                        if (linkedAv) {
                          onEditAvatar(linkedAv);
                        } else {
                          onAddAvatar(char.description || char.name || '');
                        }
                      }} data-testid={`edit-char-${ci}`}
                        title={lang === 'pt' ? 'Editar personagem' : 'Edit character'}
                        className="flex items-center gap-1 border border-[#333] text-[#888] rounded px-1.5 py-1 text-[10px] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
                        <Edit3 size={9} /> <span className="hidden sm:inline">{lang === 'pt' ? 'Editar' : 'Edit'}</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Avatar selection with full controls — PROJECT-SCOPED */}
                <div className="flex gap-1.5 flex-wrap items-center">
                  {projectAvatars.map((av, ai) => {
                    const isLinked = characterAvatars[char.name] === av.url;
                    const isEditing = aiEditAvatarId === av.id;
                    return (
                      <div key={av.id || ai} className={`relative rounded-lg overflow-hidden border-2 transition cursor-pointer group ${
                        isLinked ? 'border-[#C9A84C] shadow-[0_0_8px_rgba(201,168,76,0.25)]' : 'border-[#222] hover:border-[#444]'
                      }`} style={{ width: 52, height: 68 }}>
                        <img loading="lazy" decoding="async" src={resolveImageUrl(av.url)} alt={av.name}
                          className="w-full h-full object-cover"
                          onClick={() => linkAvatar(char.name, av.url)} />
                        {isLinked && (
                          <div className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center">
                            <Check size={8} className="text-black" />
                          </div>
                        )}
                        {/* Action bar — always visible on hover */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent px-0.5 py-0.5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={e => { e.stopPropagation(); removeAvatarFromProject(av.id); }}
                            className="h-5 w-5 rounded flex items-center justify-center text-red-400/70 hover:text-red-400 transition" title={lang === 'pt' ? 'Remover' : 'Remove'}>
                            <X size={9} />
                          </button>
                          <div className="flex items-center gap-0.5">
                            <button onClick={e => { e.stopPropagation(); onPreviewAvatar(av.url); }}
                              className="h-5 w-5 rounded flex items-center justify-center text-white/70 hover:text-white transition" title={lang === 'pt' ? 'Ver zoom' : 'Preview'}>
                              <Eye size={9} />
                            </button>
                            <button onClick={e => { e.stopPropagation(); onEditAvatar(av); }}
                              className="h-5 w-5 rounded flex items-center justify-center text-[#C9A84C] hover:text-[#D4B85C] transition" title={lang === 'pt' ? 'Editar' : 'Edit'}>
                              <PenTool size={9} />
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {/* Create new avatar button */}
                  <button onClick={() => onAddAvatar(char.description || char.name || '')} data-testid={`add-avatar-${ci}`}
                    title={lang === 'pt' ? 'Criar novo personagem' : 'Create new character'}
                    className="rounded-lg border border-dashed border-[#444] flex flex-col items-center justify-center hover:border-[#C9A84C]/50 hover:bg-[#C9A84C]/5 transition group"
                    style={{ width: 52, height: 68 }}>
                    <Plus size={12} className="text-[#555] group-hover:text-[#C9A84C]" />
                    <span className="text-[8px] text-[#555] group-hover:text-[#C9A84C] mt-0.5">{lang === 'pt' ? 'Criar' : 'New'}</span>
                  </button>
                  {/* Import from library button */}
                  <button onClick={() => setShowLibrary(true)} data-testid={`import-library-${ci}`}
                    title={lang === 'pt' ? 'Importar da Biblioteca' : 'Import from Library'}
                    className="rounded-lg border border-dashed border-[#C9A84C]/30 flex flex-col items-center justify-center hover:border-[#C9A84C]/60 hover:bg-[#C9A84C]/5 transition group"
                    style={{ width: 52, height: 68 }}>
                    <BookOpen size={12} className="text-[#C9A84C]/50 group-hover:text-[#C9A84C]" />
                    <span className="text-[8px] text-[#C9A84C]/50 group-hover:text-[#C9A84C] mt-0.5">{lang === 'pt' ? 'Acervo' : 'Library'}</span>
                  </button>
                </div>

                {/* Selected avatar AI edit hint (when avatar is linked but overlay not open) */}
                {characterAvatars[char.name] && !projectAvatars.find(a => a.url === characterAvatars[char.name] && aiEditAvatarId === a.id) && (
                  <p className="text-[10px] text-[#555] mt-1.5 italic">
                    {lang === 'pt' ? 'Passe o mouse para ver, editar ou criar nova versão com IA' : 'Hover to preview, edit or create new AI version'}
                  </p>
                )}
              </div>
            ))}
          </div>

          {/* ── Voice Narration (ElevenLabs) ── */}
          <div className="border-t border-[#222] pt-3 space-y-2" data-testid="studio-narration-section">
            <h4 className="text-[10px] font-semibold text-white flex items-center gap-1.5">
              <Volume2 size={11} className="text-[#C9A84C]" />
              {lang === 'pt' ? 'Narração por Voz' : 'Voice Narration'}
              <span className="text-[10px] text-[#555] font-normal ml-1">ElevenLabs</span>
            </h4>

            {/* Voice selector */}
            <div className="flex gap-2 items-end">
              <div className="flex-1">
                <label className="text-[11px] text-[#666] mb-0.5 block">{lang === 'pt' ? 'Voz' : 'Voice'}</label>
                <select value={selectedVoice} onChange={e => setSelectedVoice(e.target.value)}
                  data-testid="voice-selector"
                  className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-2 py-1.5 text-[10px] text-white outline-none focus:border-[#C9A84C]/50">
                  {voices.map(v => (
                    <option key={v.id} value={v.id}>{v.name} — {v.gender} • {v.accent} • {v.style}</option>
                  ))}
                </select>
              </div>
              <button onClick={generateNarration} disabled={narrationGenerating || scenes.length === 0}
                data-testid="generate-narration-btn"
                className="btn-gold rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-30 flex items-center gap-1 whitespace-nowrap">
                {narrationGenerating ? <RefreshCw size={10} className="animate-spin" /> : <Volume2 size={10} />}
                {narrationGenerating
                  ? `${narrationStatus.done || 0}/${narrationStatus.total || '?'}`
                  : (lang === 'pt' ? 'Gerar Narração' : 'Generate Narration')
                }
              </button>
            </div>

            {/* Narration results */}
            {narrations.length > 0 && (
              <div className="space-y-1 max-h-[150px] overflow-y-auto hide-scrollbar">
                {narrations.map((n, i) => (
                  <div key={i} className={`rounded-md border px-2 py-1.5 flex items-center gap-2 ${
                    n.audio_url ? 'border-emerald-500/20 bg-emerald-500/5' : 'border-[#222] bg-[#0A0A0A]'
                  }`}>
                    <span className="text-[11px] font-bold text-[#C9A84C] shrink-0">C{n.scene_number}</span>
                    <p className="text-[11px] text-[#999] flex-1 truncate">{n.text || '—'}</p>
                    {n.audio_url && (
                      <audio src={n.audio_url} controls className="h-6 w-24 shrink-0" style={{maxHeight: '24px'}} />
                    )}
                    {n.error && <span className="text-[10px] text-red-400 shrink-0">Erro</span>}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* ── Preview Board (when preview is generated) ── */}
          {showPreview && previewData?.production_design && (
            <div className="border-t border-[#222] pt-3">
              <PreviewBoard
                productionDesign={previewData.production_design}
                avatarDescriptions={previewData.avatar_descriptions}
                characters={characters}
                characterAvatars={characterAvatars}
                scenes={scenes}
                lang={lang}
                previewTime={previewData.preview_time}
                onApprove={approveAndProduce}
                onRegenerate={generatePreview}
                regenerating={previewLoading}
              />
            </div>
          )}

          {/* Action buttons — only show when preview is NOT open */}
          {!showPreview && (
            <div className="flex gap-2">
              <button onClick={() => setStep(1)} className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
                ← {lang === 'pt' ? 'Roteiro' : 'Script'}
              </button>
              <button onClick={generatePreview} disabled={generating || previewLoading || scenes.length === 0}
                data-testid="preview-production-btn"
                className="flex-1 rounded-lg border border-[#C9A84C]/30 bg-[#C9A84C]/5 py-2 text-[10px] font-semibold text-[#C9A84C] hover:bg-[#C9A84C]/10 transition disabled:opacity-30 flex items-center justify-center gap-1">
                {previewLoading ? <RefreshCw size={10} className="animate-spin" /> : <Eye size={12} />}
                {previewLoading
                  ? (lang === 'pt' ? 'Gerando preview...' : 'Generating preview...')
                  : (lang === 'pt' ? 'Preview Design' : 'Preview Design')
                }
              </button>
              <button onClick={() => setStep(3)} disabled={scenes.length === 0}
                data-testid="go-to-storyboard-btn"
                className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-semibold disabled:opacity-30 flex items-center justify-center gap-1">
                <Camera size={12} /> Storyboard →
              </button>
            </div>
          )}
        </div>
      )}

      {/* ═══ STEP 3: Storyboard ═══ */}
      {step === 3 && !viewingProject && (
        <div className="glass-card p-3" data-testid="studio-step-storyboard">
          <StoryboardEditor
            projectId={projectId}
            scenes={scenes}
            characters={characters}
            characterAvatars={characterAvatars}
            lang={lang}
            onApprove={() => {
              // After approving storyboard, go to Dialogues step
              setStep(4);
            }}
            onBack={() => setStep(2)}
          />
        </div>
      )}


      {/* ═══ STEP 4: Dialogues & Script Polish ═══ */}
      {step === 4 && !viewingProject && (
        <div data-testid="studio-step-dialogues">
          <DialogueEditor
            projectId={projectId}
            lang={lang}
            scenes={scenes}
            onComplete={() => setStep(5)}
            onBack={() => setStep(3)}
          />
        </div>
      )}


      {/* ═══ STEP 5: Production Progress ═══ */}
      {step === 5 && !viewingProject && (
        <div className="glass-card p-3 space-y-3" data-testid="studio-step-production">
          <h3 className="text-xs font-semibold text-white flex items-center gap-2">
            <Clapperboard size={12} className="text-[#C9A84C]" />
            {lang === 'pt' ? 'Produção em Andamento' : 'Production in Progress'}
          </h3>

          {/* Segmented progress bar */}
          {scenes.length > 0 && (
            <div>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-[#999]">
                  {agentStatus.phase === 'pre_production' && `Pré-produção inteligente — Analisando avatares e design...`}
                  {agentStatus.phase === 'pre_production_done' && `Design de produção pronto — Iniciando direção...`}
                  {agentStatus.phase === 'photography' && `Dir. Fotografia — Cena ${agentStatus.current_scene || 0}/${agentStatus.total_scenes || scenes.length}`}
                  {agentStatus.phase === 'generating_keyframes' && `Gemini — Gerando keyframes de referência (${agentStatus.total_scenes || scenes.length} cenas)`}
                  {agentStatus.phase === 'music' && `Dir. Musical`}
                  {agentStatus.phase === 'audio' && `Dir. Áudio — Cena ${agentStatus.current_scene || 0}/${agentStatus.total_scenes || scenes.length}`}
                  {agentStatus.phase?.startsWith('generating_video') && `Sora 2 — Gerando vídeos`}
                  {agentStatus.phase === 'concatenating' && `Concatenando filme final...`}
                  {agentStatus.phase === 'complete' && `Produção concluída!`}
                  {agentStatus.phase === 'starting' && `Iniciando produção...`}
                  {agentStatus.phase === 'starting_teams' && `Iniciando equipas de direção...`}
                </span>
                <span className="text-[#C9A84C] font-semibold">
                  {agentStatus.videos_done !== undefined ? `${agentStatus.videos_done}/${agentStatus.total_scenes || scenes.length} vídeos` : ''}
                </span>
              </div>
              {/* Main segmented bar — one segment per scene */}
              <div className="flex gap-0.5 w-full">
                {scenes.map((s, i) => {
                  const sn = String(s.scene_number || i + 1);
                  const ss = agentStatus.scene_status || {};
                  const videoDone = ss[sn] === 'done';
                  const agentsDone = ss[sn] === 'agents_done';
                  const videoError = ss[sn] === 'error';
                  const isCurrentScene = agentStatus.current_scene === (s.scene_number || i + 1);
                  const phase = agentStatus.phase || '';

                  let segColor = 'bg-[#1A1A1A]'; // pending
                  if (videoDone) segColor = 'bg-emerald-500';
                  else if (videoError) segColor = 'bg-red-500';
                  else if (agentsDone && phase.startsWith('generating_video')) segColor = 'bg-blue-500';
                  else if (agentsDone) segColor = 'bg-blue-500/60';
                  else if (isCurrentScene) segColor = 'bg-[#C9A84C] animate-pulse';

                  return (
                    <div key={i} className="flex-1 flex flex-col items-center gap-0.5" title={`Cena ${sn}: ${s.title || ''}`}>
                      <div className={`w-full h-2 rounded-sm transition-all duration-500 ${segColor}`} />
                      <span className="text-xs text-[#555]">{sn}</span>
                    </div>
                  );
                })}
              </div>
              {/* Legend */}
              <div className="flex items-center gap-3 mt-1.5">
                <span className="flex items-center gap-1 text-xs text-[#666]"><span className="inline-block w-2 h-2 rounded-sm bg-emerald-500" /> {lang === 'pt' ? 'Vídeo pronto' : 'Video done'}</span>
                <span className="flex items-center gap-1 text-xs text-[#666]"><span className="inline-block w-2 h-2 rounded-sm bg-blue-500" /> {lang === 'pt' ? 'Agentes prontos' : 'Agents done'}</span>
                <span className="flex items-center gap-1 text-xs text-[#666]"><span className="inline-block w-2 h-2 rounded-sm bg-[#C9A84C]" /> {lang === 'pt' ? 'Processando' : 'Processing'}</span>
                <span className="flex items-center gap-1 text-xs text-[#666]"><span className="inline-block w-2 h-2 rounded-sm bg-red-500" /> {lang === 'pt' ? 'Erro' : 'Error'}</span>
              </div>
            </div>
          )}

          {/* Scene-by-scene detail */}
          <div className="space-y-1">
            {scenes.map((s, i) => {
              const sceneNum = s.scene_number || i + 1;
              const ss = agentStatus.scene_status || {};
              const sceneState = ss[String(sceneNum)] || 'queued';
              const videoDone = sceneState === 'done';
              const videoError = sceneState === 'error';
              const isDirecting = sceneState === 'directing';
              const isWaiting = sceneState === 'waiting_sora';
              const isVideoGen = sceneState === 'generating_video';
              const isActive = isDirecting || isWaiting || isVideoGen;

              // Find the video output for this scene
              const sceneVideo = outputs.find(o => o.scene_number === sceneNum && o.type === 'video' && o.url);

              // Progress per state
              const sceneProgress = videoDone ? 100 : videoError ? 100 : isVideoGen ? 65 : isWaiting ? 40 : isDirecting ? 20 : 0;
              const barColor = videoDone ? 'bg-emerald-500' : videoError ? 'bg-red-500' : isVideoGen ? 'bg-[#C9A84C]' : isWaiting ? 'bg-blue-400' : isDirecting ? 'bg-purple-400' : 'bg-[#222]';

              return (
                <div key={i} className={`rounded-lg border px-2.5 py-1.5 transition-all ${
                  isVideoGen ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5' :
                  isDirecting ? 'border-purple-500/20 bg-purple-500/5' :
                  isWaiting ? 'border-blue-500/20 bg-blue-500/5' :
                  videoDone ? 'border-emerald-500/20 bg-emerald-500/5' :
                  videoError ? 'border-red-500/20 bg-red-500/5' :
                  'border-[#1A1A1A] bg-[#0A0A0A]'
                }`}>
                  <div className="flex items-center gap-2">
                    <div className={`h-5 w-5 rounded-full flex items-center justify-center text-[11px] font-bold ${
                      videoDone ? 'bg-emerald-500 text-black' :
                      videoError ? 'bg-red-500 text-white' :
                      isVideoGen ? 'bg-[#C9A84C] text-black' :
                      isDirecting ? 'bg-purple-500 text-white' :
                      isWaiting ? 'bg-blue-500 text-white' :
                      'bg-[#222] text-[#666]'
                    }`}>
                      {videoDone ? <Check size={8} /> : videoError ? <X size={8} /> : isActive ? <RefreshCw size={8} className="animate-spin" /> : sceneNum}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-semibold text-white truncate">{s.title || `Cena ${sceneNum}`}</p>
                      <p className="text-[10px] text-[#666] truncate">{s.time_start}-{s.time_end} • {s.emotion}</p>
                    </div>
                    <div className="text-[10px] shrink-0">
                      {videoDone && <span className="text-emerald-400 font-medium">{lang === 'pt' ? 'Pronto' : 'Done'}</span>}
                      {videoError && <span className="text-red-400">Erro</span>}
                      {isVideoGen && <span className="text-[#C9A84C]">Sora 2...</span>}
                      {isWaiting && <span className="text-blue-400">{lang === 'pt' ? 'Fila Sora' : 'Sora Queue'}</span>}
                      {isDirecting && <span className="text-purple-400">{lang === 'pt' ? 'Dirigindo' : 'Directing'}</span>}
                      {sceneState === 'queued' && <span className="text-[#444]">—</span>}
                    </div>
                  </div>
                  {/* Per-scene progress bar */}
                  <div className="mt-1 w-full bg-[#111] rounded-full h-1">
                    <div className={`h-1 rounded-full transition-all duration-700 ${barColor} ${isActive ? 'animate-pulse' : ''}`}
                      style={{ width: `${sceneProgress}%` }} />
                  </div>
                  {/* Real-time video preview when scene is done */}
                  {sceneVideo && (
                    <div className="mt-1.5 rounded-lg overflow-hidden border border-emerald-500/20 bg-black">
                      <video src={sceneVideo.url} controls preload="metadata" data-testid={`scene-preview-${sceneNum}`}
                        className="w-full max-h-[120px] object-contain" />
                    </div>
                  )}
                  {/* Per-scene action buttons: Retry + Edit */}
                  {(videoError || videoDone) && !generating && (
                    <div className="mt-1.5 flex gap-1">
                      <button
                        onClick={() => regenerateScene(sceneNum)}
                        disabled={regenScene === sceneNum}
                        data-testid={`regen-scene-${sceneNum}`}
                        className={`flex-1 flex items-center justify-center gap-1 rounded-md py-1 text-[11px] font-medium transition ${
                          videoError
                            ? 'bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20'
                            : 'bg-[#111] border border-[#333] text-[#888] hover:text-white hover:border-[#C9A84C]/30'
                        } ${regenScene === sceneNum ? 'opacity-50' : ''}`}>
                        <RefreshCw size={8} className={regenScene === sceneNum ? 'animate-spin' : ''} />
                        {regenScene === sceneNum ? (lang === 'pt' ? 'Regenerando...' : 'Regenerating...') : (lang === 'pt' ? 'Regenerar' : 'Retry')}
                      </button>
                      <button
                        onClick={() => { setEditingScene(sceneNum); setEditSceneForm({ title: s.title, description: s.description, dialogue: s.dialogue, emotion: s.emotion, camera: s.camera }); }}
                        data-testid={`edit-scene-${sceneNum}`}
                        className="flex items-center gap-1 rounded-md py-1 px-2 text-[11px] bg-[#111] border border-[#333] text-[#888] hover:text-white hover:border-[#C9A84C]/30 transition">
                        <Edit3 size={8} />
                        {lang === 'pt' ? 'Editar' : 'Edit'}
                      </button>
                    </div>
                  )}
                  {/* Scene edit form (inline) */}
                  {editingScene === sceneNum && (
                    <div className="mt-2 space-y-1.5 p-2 rounded-lg bg-[#0A0A0A] border border-[#C9A84C]/20">
                      <input value={editSceneForm.title || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, title: e.target.value }))}
                        placeholder="Título da cena" className="w-full bg-[#111] border border-[#222] rounded px-2 py-1 text-xs text-white outline-none" />
                      <textarea value={editSceneForm.description || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Descrição visual da cena" rows={2}
                        className="w-full bg-[#111] border border-[#222] rounded px-2 py-1 text-xs text-white outline-none resize-none" />
                      <textarea value={editSceneForm.dialogue || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, dialogue: e.target.value }))}
                        placeholder="Diálogo/Narração" rows={2}
                        className="w-full bg-[#111] border border-[#222] rounded px-2 py-1 text-xs text-white outline-none resize-none" />
                      <div className="flex gap-1">
                        <input value={editSceneForm.emotion || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, emotion: e.target.value }))}
                          placeholder="Emoção" className="flex-1 bg-[#111] border border-[#222] rounded px-2 py-1 text-xs text-white outline-none" />
                        <input value={editSceneForm.camera || ''} onChange={e => setEditSceneForm(prev => ({ ...prev, camera: e.target.value }))}
                          placeholder="Câmera" className="flex-1 bg-[#111] border border-[#222] rounded px-2 py-1 text-xs text-white outline-none" />
                      </div>
                      <div className="flex gap-1">
                        <button onClick={() => setEditingScene(null)} className="flex-1 rounded border border-[#333] py-1 text-[11px] text-[#999] hover:text-white">
                          {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                        </button>
                        <button onClick={() => saveSceneEdit(sceneNum)}
                          className="flex-1 btn-gold rounded py-1 text-[11px] font-semibold">
                          {lang === 'pt' ? 'Salvar' : 'Save'}
                        </button>
                        <button onClick={() => { saveSceneEdit(sceneNum); setTimeout(() => regenerateScene(sceneNum), 500); }}
                          className="flex-1 rounded py-1 text-[11px] font-semibold bg-[#C9A84C]/20 border border-[#C9A84C]/30 text-[#C9A84C] hover:bg-[#C9A84C]/30">
                          {lang === 'pt' ? 'Salvar & Regenerar' : 'Save & Regen'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Phase indicator with time estimate */}
          {generating && agentStatus.phase?.startsWith('generating_video') && (
            <div className="rounded-lg border border-[#C9A84C]/20 bg-[#C9A84C]/5 p-2 flex items-center gap-2">
              <Film size={14} className="text-[#C9A84C] animate-pulse" />
              <div className="flex-1">
                <p className="text-[10px] font-semibold text-[#C9A84C]">Sora 2 — {lang === 'pt' ? 'Gerando Vídeos' : 'Generating Videos'}</p>
                <p className="text-[11px] text-[#666]">
                  {agentStatus.videos_done || 0}/{agentStatus.total_scenes || '?'} {lang === 'pt' ? 'prontos' : 'done'}.
                  {' '}{lang === 'pt' ? 'Pode navegar — avisaremos quando terminar.' : 'You can navigate away.'}
                </p>
              </div>
            </div>
          )}
          {/* Budget exhausted warning */}
          {generating && Object.values(agentStatus.scene_status || {}).some(s => s === 'error') &&
           agentStatus.videos_done > 0 && agentStatus.videos_done < (agentStatus.total_scenes || 0) && (
            <div className="rounded-lg border border-orange-500/30 bg-orange-500/5 p-2 flex items-center gap-2">
              <Clock size={12} className="text-orange-400" />
              <p className="text-[11px] text-orange-300">
                {lang === 'pt'
                  ? `${agentStatus.videos_done} cenas geradas, restantes falharam. Possivelmente budget Sora 2 esgotado. Adicione saldo em Profile → Universal Key → Add Balance e retome a produção.`
                  : `${agentStatus.videos_done} scenes generated, others failed. Likely Sora 2 budget exceeded. Top up balance and resume.`
                }
              </p>
            </div>
          )}
        </div>
      )}

      {/* ═══ MEDIA PREVIEW MODAL ═══ */}
      {previewModal && (
        <div className="fixed inset-0 z-[60] bg-black/95 backdrop-blur-sm flex items-center justify-center" data-testid="media-preview-modal"
          onClick={() => setPreviewModal(null)}>
          <div className="relative w-full h-full flex flex-col" onClick={e => e.stopPropagation()}>
            {/* Close button */}
            <button onClick={() => setPreviewModal(null)} data-testid="close-preview-modal"
              className="absolute top-3 right-3 z-20 w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition">
              <X size={18} className="text-white" />
            </button>

            {/* === VIDEO PREVIEW === */}
            {previewModal.type === 'video' && (
              <div className="flex-1 flex flex-col items-center justify-center p-4">
                <div className="w-full max-w-3xl">
                  <video src={previewModal.data.url} controls autoPlay className="w-full rounded-xl shadow-2xl" data-testid="preview-video-player" />
                  <div className="flex items-center justify-between mt-3 px-1">
                    <p className="text-sm font-medium text-white">
                      {lang === 'pt' ? 'Cena' : 'Scene'} {previewModal.data.scene_number}
                    </p>
                    <a href={previewModal.data.url} download data-testid="preview-video-download"
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#C9A84C] text-black text-xs font-semibold hover:bg-white transition">
                      <Download size={14} /> Download
                    </a>
                  </div>
                </div>
                {/* Navigation between scene videos */}
                {previewModal.data.allVideos && previewModal.data.allVideos.length > 1 && (
                  <div className="flex gap-2 mt-4 overflow-x-auto pb-2 max-w-3xl">
                    {previewModal.data.allVideos.map((v, i) => (
                      <button key={i} onClick={() => setPreviewModal({
                        type: 'video',
                        data: { ...v, allVideos: previewModal.data.allVideos }
                      })}
                        className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-[10px] font-mono uppercase tracking-wider transition ${
                          v.scene_number === previewModal.data.scene_number
                            ? 'bg-[#C9A84C] text-black font-bold'
                            : 'bg-white/5 text-white/60 hover:bg-white/10'
                        }`}>
                        {lang === 'pt' ? 'Cena' : 'Scene'} {v.scene_number}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* === IMAGE GALLERY === */}
            {previewModal.type === 'gallery' && (
              <div className="flex-1 flex flex-col items-center justify-center p-4">
                <div className="w-full max-w-4xl">
                  {/* Main image */}
                  <div className="relative">
                    <img loading="lazy" decoding="async"
                      src={previewModal.data.images[previewModal.data.currentIndex]?.url || previewModal.data.images[previewModal.data.currentIndex]}
                      alt=""
                      className="w-full max-h-[65vh] object-contain rounded-xl shadow-2xl"
                      data-testid="preview-gallery-image"
                    />
                    {/* Left/Right arrows */}
                    {previewModal.data.currentIndex > 0 && (
                      <button onClick={() => setPreviewModal(prev => ({
                        ...prev, data: { ...prev.data, currentIndex: prev.data.currentIndex - 1 }
                      }))}
                        className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 hover:bg-black/80 flex items-center justify-center transition">
                        <ChevronLeft size={20} className="text-white" />
                      </button>
                    )}
                    {previewModal.data.currentIndex < previewModal.data.images.length - 1 && (
                      <button onClick={() => setPreviewModal(prev => ({
                        ...prev, data: { ...prev.data, currentIndex: prev.data.currentIndex + 1 }
                      }))}
                        className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-black/50 hover:bg-black/80 flex items-center justify-center transition">
                        <ChevronRight size={20} className="text-white" />
                      </button>
                    )}
                  </div>
                  {/* Info bar */}
                  <div className="flex items-center justify-between mt-3 px-1">
                    <div>
                      <p className="text-sm font-medium text-white">{previewModal.data.title || 'Storyboard'}</p>
                      <p className="text-[10px] font-mono text-[#555]">
                        {previewModal.data.currentIndex + 1} / {previewModal.data.images.length}
                        {previewModal.data.images[previewModal.data.currentIndex]?.scene && (
                          <> &bull; {lang === 'pt' ? 'Cena' : 'Scene'} {previewModal.data.images[previewModal.data.currentIndex].scene}</>
                        )}
                      </p>
                    </div>
                    <a href={previewModal.data.images[previewModal.data.currentIndex]?.url || previewModal.data.images[previewModal.data.currentIndex]}
                      download data-testid="preview-gallery-download"
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#C9A84C] text-black text-xs font-semibold hover:bg-white transition">
                      <Download size={14} /> Download
                    </a>
                  </div>
                  {/* Thumbnail strip */}
                  <div className="flex gap-1.5 mt-3 overflow-x-auto pb-2 scrollbar-hide">
                    {previewModal.data.images.map((img, i) => (
                      <button key={i} onClick={() => setPreviewModal(prev => ({
                        ...prev, data: { ...prev.data, currentIndex: i }
                      }))}
                        className={`flex-shrink-0 w-14 h-10 rounded-lg overflow-hidden border-2 transition ${
                          i === previewModal.data.currentIndex ? 'border-[#C9A84C] opacity-100' : 'border-transparent opacity-40 hover:opacity-70'
                        }`}>
                        <img src={img?.url || img} alt="" loading="lazy" decoding="async" className="w-full h-full object-cover" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* === BOOK PREVIEW (embedded) === */}
            {previewModal.type === 'book' && (
              <div className="flex-1 flex flex-col">
                <div className="flex items-center justify-between px-4 py-2 bg-[#0A0A0A] border-b border-white/5">
                  <div className="flex items-center gap-2">
                    <BookOpen size={16} className="text-[#C9A84C]" />
                    <span className="text-sm font-medium text-white">{lang === 'pt' ? 'Livro Animado' : 'Animated Book'}</span>
                  </div>
                  <a href={`/book/${projectId}`} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-[10px] font-mono text-[#C9A84C] hover:underline">
                    <Maximize2 size={10} /> {lang === 'pt' ? 'Tela cheia' : 'Full screen'}
                  </a>
                </div>
                <div className="flex-1">
                  <iframe src={`/book/${projectId}`} className="w-full h-full border-0" title="Interactive Book" data-testid="preview-book-iframe" />
                </div>
              </div>
            )}

            {/* === PDF PREVIEW (image gallery from storyboard frames) === */}
            {previewModal.type === 'pdf' && (
              <div className="flex-1 flex flex-col items-center justify-center p-4">
                <div className="w-full max-w-4xl">
                  <div className="flex items-center gap-2 mb-4">
                    <FileText size={18} className="text-purple-400" />
                    <h3 className="text-sm font-medium text-white">Storyboard PDF</h3>
                    <span className="text-[10px] font-mono text-[#555]">{allPanelFrames.length} {lang === 'pt' ? 'ilustrações' : 'illustrations'}</span>
                  </div>
                  {/* Grid preview of all frames */}
                  <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 max-h-[60vh] overflow-y-auto pr-1 scrollbar-hide">
                    {allPanelFrames.map((frame, i) => (
                      <button key={i} onClick={() => setPreviewModal({
                        type: 'gallery',
                        data: { images: allPanelFrames, currentIndex: i, title: `Storyboard — ${lang === 'pt' ? 'Cena' : 'Scene'} ${frame.scene}` }
                      })}
                        className="relative rounded-lg overflow-hidden border border-white/5 hover:border-[#C9A84C]/30 transition group aspect-[4/3]"
                        data-testid={`pdf-preview-frame-${i}`}>
                        <img src={frame.url} alt="" loading="lazy" decoding="async" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition" />
                        <span className="absolute bottom-1 left-1.5 text-[10px] font-mono text-white/80 opacity-0 group-hover:opacity-100 transition">
                          C{frame.scene} F{frame.frame}
                        </span>
                        <Maximize2 size={10} className="absolute top-1 right-1 text-white/60 opacity-0 group-hover:opacity-100 transition" />
                      </button>
                    ))}
                  </div>
                  {/* Download PDF button */}
                  <div className="flex justify-center mt-4">
                    <button onClick={async () => {
                      try {
                        const r = await axios.get(`${API}/studio/projects/${projectId}/book/pdf`, { responseType: 'blob' });
                        const url = URL.createObjectURL(r.data);
                        const a = document.createElement('a'); a.href = url; a.download = `${projectName || 'storyboard'}.pdf`; a.click();
                        toast.success('PDF baixado!');
                      } catch { toast.error('Erro ao baixar PDF'); }
                    }} data-testid="preview-pdf-download"
                      className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-purple-500/20 border border-purple-500/30 text-purple-300 text-xs font-semibold hover:bg-purple-500/30 transition">
                      <Download size={14} /> {lang === 'pt' ? 'Baixar PDF Completo' : 'Download Full PDF'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ═══ STEP 5: Resultado — Deliverables Showcase ═══ */}
      {step === 6 && !viewingProject && (
        <div className="space-y-4" data-testid="studio-step-results">
          {/* Section Header */}
          <div className="text-center py-2">
            <p className="text-[10px] font-mono tracking-[0.3em] uppercase text-[#C9A84C]/60 mb-1">
              {lang === 'pt' ? 'Entrega Final' : 'Final Delivery'}
            </p>
            <h2 className="text-xl sm:text-2xl font-medium text-white tracking-tight">
              {lang === 'pt' ? 'Seus Produtos' : 'Your Products'}
            </h2>
          </div>

          {outputs.length === 0 && !generating && scenes.length === 0 && storyboardThumbs.length === 0 && (() => {
            const proj = allProjects.find(p => p.id === projectId);
            const hasPanels = (proj?.storyboard_panels || []).length > 0;
            if (!hasPanels) return (
              <div className="text-center py-10 border border-[#111] rounded-xl">
                <Film size={28} className="mx-auto text-[#222] mb-3" strokeWidth={1} />
                <p className="text-sm text-[#444] font-sans">{lang === 'pt' ? 'Comece criando o roteiro e storyboard' : 'Start by creating the script and storyboard'}</p>
                <button onClick={() => setStep(1)} className="mt-3 text-[10px] font-mono tracking-wider uppercase text-[#C9A84C] hover:underline">
                  {lang === 'pt' ? 'Criar Roteiro' : 'Create Script'}
                </button>
              </div>
            );
            return null;
          })()}

          {/* ── HERO: Vídeo Final Pós-Produzido ── */}
          {(() => {
            const finalVideo = outputs.find(o => o.type === 'final_video' && o.url);
            const heroVideo = outputs.find(o => o.label === 'complete' && o.url);
            const heroOut = finalVideo || heroVideo;
            if (!heroOut) return null;
            return (
              <div className="relative rounded-xl overflow-hidden border border-[#C9A84C]/20 group" data-testid="deliverable-filme-completo">
                <div className="relative bg-black aspect-video cursor-pointer"
                  onClick={() => setPreviewModal({ type: 'video', data: { url: heroOut.url, scene_number: 0, allVideos: [] } })}>
                  <video className="w-full h-full object-contain" data-testid="result-video-complete" src={heroOut.url} poster="" preload="metadata" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />
                  <div className="absolute top-3 left-3 flex items-center gap-2">
                    <span className="text-[11px] font-mono tracking-[0.2em] uppercase bg-[#C9A84C] text-black px-2 py-0.5 rounded-sm font-semibold">
                      {lang === 'pt' ? 'Filme Final' : 'Final Film'}
                    </span>
                    {heroOut.has_narration && (
                      <span className="text-[10px] font-mono tracking-wider uppercase bg-white/10 backdrop-blur-sm text-white/80 px-1.5 py-0.5 rounded-sm">
                        {lang === 'pt' ? 'Dublado' : 'Dubbed'}
                      </span>
                    )}
                    {heroOut.has_music && (
                      <span className="text-[10px] font-mono tracking-wider uppercase bg-white/10 backdrop-blur-sm text-white/80 px-1.5 py-0.5 rounded-sm">
                        {lang === 'pt' ? 'Trilha Sonora' : 'Soundtrack'}
                      </span>
                    )}
                  </div>
                  {/* Play overlay */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-16 h-16 rounded-full bg-black/60 backdrop-blur-sm border border-[#C9A84C]/40 flex items-center justify-center">
                      <Play size={24} className="text-[#C9A84C] ml-1" fill="#C9A84C" />
                    </div>
                  </div>
                </div>
                <div className="p-3 flex items-center justify-between bg-[#0A0A0A]">
                  <div>
                    <p className="text-xs font-medium text-white">{projectName}</p>
                    <p className="text-xs font-mono text-[#555]">
                      {scenes.length} {lang === 'pt' ? 'cenas' : 'scenes'}
                      {heroOut.duration ? ` \u2022 ${Math.round(heroOut.duration)}s` : ''}
                      {heroOut.file_size_mb ? ` \u2022 ${heroOut.file_size_mb}MB` : ''}
                      {heroOut.language ? ` \u2022 ${heroOut.language.toUpperCase()}` : ''}
                    </p>
                  </div>
                  <a href={heroOut.url} download data-testid="download-filme-completo"
                    className="bg-[#C9A84C] text-black font-semibold text-[10px] tracking-wide uppercase px-4 py-2 rounded-sm hover:bg-white transition-colors duration-300 flex items-center gap-1.5">
                    <Download size={12} strokeWidth={1.5} /> Download
                  </a>
                </div>
              </div>
            );
          })()}

          {/* ── BENTO GRID: Produtos Secundários ── */}
          {(() => {
            const thumbs = storyboardThumbs;
            const sceneCount = scenes.length;
            const frameCount = sceneCount * 6;
            const sceneVideos = outputs.filter(o => o.label !== 'complete' && o.url);

            return (
            <div className="grid grid-cols-2 gap-2" data-testid="deliverables-grid">
              {/* Card: Livro Interativo — with cover thumbnail */}
              <button
                onClick={() => setPreviewModal({ type: 'book' })}
                data-testid="deliverable-livro-interativo"
                className="relative bg-[#0A0A0A] border border-white/5 rounded-xl overflow-hidden text-left group hover:-translate-y-0.5 hover:border-[#C9A84C]/20 transition-all duration-500"
              >
                {/* Thumbnail background */}
                {thumbs[0] && (
                  <div className="relative h-24 overflow-hidden">
                    <img src={thumbs[0]} alt="" loading="lazy" decoding="async" className="w-full h-full object-cover opacity-40 group-hover:opacity-60 group-hover:scale-105 transition-all duration-700" />
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A]/60 to-transparent" />
                    <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center">
                      <Check size={10} className="text-emerald-400" />
                    </div>
                    <div className="absolute bottom-2 left-2.5 flex items-center gap-1.5">
                      <BookOpen size={14} className="text-[#C9A84C]" strokeWidth={1.5} />
                      <span className="text-xs font-medium text-white drop-shadow-lg">
                        {lang === 'pt' ? 'Livro Animado' : 'Animated Book'}
                      </span>
                    </div>
                  </div>
                )}
                <div className="p-2.5">
                  {!thumbs[0] && (
                    <>
                      <BookOpen size={18} className="text-[#C9A84C] mb-1.5" strokeWidth={1.2} />
                      <p className="text-xs font-medium text-white mb-0.5">{lang === 'pt' ? 'Livro Animado' : 'Animated Book'}</p>
                    </>
                  )}
                  <p className="text-[11px] font-mono text-[#555] tracking-wider uppercase">
                    {sceneCount} {lang === 'pt' ? 'paginas' : 'pages'} • {lang === 'pt' ? 'interativo' : 'interactive'}
                  </p>
                  <span className="inline-block mt-1.5 text-[11px] font-mono tracking-wider uppercase text-[#C9A84C] group-hover:underline">
                    <Eye size={8} className="inline mr-1" />{lang === 'pt' ? 'Visualizar' : 'Preview'}
                  </span>
                </div>
              </button>

              {/* Card: Storyboard PDF — with collage */}
              <button
                onClick={() => {
                  if (allPanelFrames.length > 0) {
                    setPreviewModal({ type: 'pdf' });
                  } else {
                    // Fallback: direct download if no frames available
                    (async () => {
                      try {
                        const r = await axios.get(`${API}/studio/projects/${projectId}/book/pdf`, { responseType: 'blob' });
                        const url = URL.createObjectURL(r.data);
                        const a = document.createElement('a'); a.href = url; a.download = `${projectName || 'storyboard'}.pdf`; a.click();
                        toast.success('PDF baixado!');
                      } catch { toast.error('Erro ao baixar PDF'); }
                    })();
                  }
                }}
                data-testid="deliverable-storyboard-pdf"
                className="relative bg-[#0A0A0A] border border-white/5 rounded-xl overflow-hidden text-left group hover:-translate-y-0.5 hover:border-[#C9A84C]/20 transition-all duration-500"
              >
                {/* Collage of 4 thumbnails */}
                {thumbs.length >= 2 && (
                  <div className="relative h-24 overflow-hidden">
                    <div className="grid grid-cols-2 gap-px h-full">
                      {thumbs.slice(0, 4).map((t, ti) => (
                        <img key={ti} src={t} alt="" loading="lazy" decoding="async" className="w-full h-full object-cover opacity-30 group-hover:opacity-50 transition-opacity duration-500" />
                      ))}
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A]/50 to-transparent" />
                    <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center">
                      <Check size={10} className="text-emerald-400" />
                    </div>
                    <div className="absolute bottom-2 left-2.5 flex items-center gap-1.5">
                      <Download size={14} className="text-purple-400" strokeWidth={1.5} />
                      <span className="text-xs font-medium text-white drop-shadow-lg">Storyboard PDF</span>
                    </div>
                  </div>
                )}
                <div className="p-2.5">
                  {thumbs.length < 2 && (
                    <>
                      <Download size={18} className="text-purple-400 mb-1.5" strokeWidth={1.2} />
                      <p className="text-xs font-medium text-white mb-0.5">Storyboard PDF</p>
                    </>
                  )}
                  <p className="text-[11px] font-mono text-[#555] tracking-wider uppercase">
                    {frameCount} {lang === 'pt' ? 'ilustracoes' : 'illustrations'} • PDF
                  </p>
                  <span className="inline-block mt-1.5 text-[11px] font-mono tracking-wider uppercase text-purple-400 group-hover:underline">
                    <Eye size={8} className="inline mr-1" />{lang === 'pt' ? 'Visualizar' : 'Preview'}
                  </span>
                </div>
              </button>

              {/* Card: Vídeos por Cena — with scene count and mini thumbnails */}
              {sceneVideos.length > 0 && (
                <button
                  onClick={() => {
                    if (sceneVideos.length > 0) {
                      setPreviewModal({
                        type: 'video',
                        data: { ...sceneVideos[0], allVideos: sceneVideos }
                      });
                    }
                  }}
                  data-testid="deliverable-cenas-card"
                  className="relative bg-[#0A0A0A] border border-white/5 rounded-xl overflow-hidden text-left group hover:-translate-y-0.5 hover:border-[#C9A84C]/20 transition-all duration-500"
                >
                  {/* Film strip preview */}
                  <div className="relative h-24 overflow-hidden">
                    <div className="flex h-full">
                      {thumbs.slice(0, 3).map((t, ti) => (
                        <div key={ti} className="flex-1 relative">
                          <img src={t} alt="" loading="lazy" decoding="async" className="w-full h-full object-cover opacity-30 group-hover:opacity-50 transition-opacity duration-500" />
                        </div>
                      ))}
                    </div>
                    <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] via-[#0A0A0A]/50 to-transparent" />
                    <div className="absolute bottom-2 left-2.5 flex items-center gap-1.5">
                      <Film size={14} className="text-emerald-400" strokeWidth={1.5} />
                      <span className="text-xs font-medium text-white drop-shadow-lg">
                        {lang === 'pt' ? 'Videos por Cena' : 'Scene Videos'}
                      </span>
                    </div>
                    <div className="absolute top-2 right-2 bg-black/60 rounded-sm px-1.5 py-0.5">
                      <span className="text-[11px] font-mono text-emerald-400">{sceneVideos.length}</span>
                    </div>
                  </div>
                  <div className="p-2.5">
                    <p className="text-[11px] font-mono text-[#555] tracking-wider uppercase">
                      {sceneVideos.length} {lang === 'pt' ? 'videos individuais' : 'individual videos'}
                    </p>
                    <span className="inline-block mt-1.5 text-[11px] font-mono tracking-wider uppercase text-emerald-400 group-hover:underline">
                      <Play size={8} className="inline mr-1" />{lang === 'pt' ? 'Assistir' : 'Watch'}
                    </span>
                  </div>
                </button>
              )}

              {/* Card: Pós-Produção */}
              {(() => {
                const hasFinal = outputs.some(o => o.type === 'final_video' && o.url);
                return (
              <button
                onClick={() => setShowPostProd(true)}
                data-testid="deliverable-pos-producao"
                className={`relative bg-[#0A0A0A] border rounded-xl overflow-hidden text-left group hover:-translate-y-0.5 transition-all duration-500 ${
                  hasFinal ? 'border-green-500/20 hover:border-green-500/40' : 'border-white/5 hover:border-[#C9A84C]/20'
                }`}
              >
                <div className="relative h-24 overflow-hidden bg-gradient-to-br from-blue-900/20 to-[#0A0A0A]">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex gap-3">
                      <div className="w-7 h-7 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                        <Mic size={12} className="text-blue-400" />
                      </div>
                      <div className="w-7 h-7 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                        <Music size={12} className="text-blue-400" />
                      </div>
                      <div className="w-7 h-7 rounded-full bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                        <Globe size={12} className="text-blue-400" />
                      </div>
                    </div>
                  </div>
                  {hasFinal && (
                    <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-green-500/10 flex items-center justify-center">
                      <Check size={10} className="text-green-400" />
                    </div>
                  )}
                  <div className="absolute bottom-2 left-2.5 flex items-center gap-1.5">
                    <Clapperboard size={14} className="text-blue-400" strokeWidth={1.5} />
                    <span className="text-xs font-medium text-white drop-shadow-lg">
                      {lang === 'pt' ? 'Pós-Produção' : 'Post-Production'}
                    </span>
                  </div>
                </div>
                <div className="p-2.5">
                  <p className="text-[11px] font-mono text-[#555] tracking-wider uppercase">
                    {hasFinal
                      ? (lang === 'pt' ? 'Narração + Trilha Sonora + Transições' : 'Narration + Soundtrack + Transitions')
                      : (lang === 'pt' ? 'Narração IA ou Manual, Trilha, Legendas' : 'AI or Manual Narration, Music, Subtitles')
                    }
                  </p>
                  <span className={`inline-block mt-1.5 text-[11px] font-mono tracking-wider uppercase group-hover:underline ${hasFinal ? 'text-green-400' : 'text-blue-400'}`}>
                    {hasFinal
                      ? (lang === 'pt' ? 'Concluído — Reconfigurar' : 'Complete — Reconfigure')
                      : (lang === 'pt' ? 'Configurar >' : 'Configure >')}
                  </span>
                </div>
              </button>
                );
              })()}

              {/* Card: Analytics */}
              <button
                onClick={loadAnalytics}
                disabled={analyticsLoading}
                data-testid="deliverable-analytics"
                className="relative bg-[#0A0A0A] border border-white/5 rounded-xl overflow-hidden text-left group hover:-translate-y-0.5 hover:border-[#C9A84C]/20 transition-all duration-500 col-span-2"
              >
                <div className="p-3 flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
                    <BarChart3 size={20} className="text-amber-400" strokeWidth={1.2} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-white">{lang === 'pt' ? 'Analytics do Projeto' : 'Project Analytics'}</p>
                    <p className="text-[11px] font-mono text-[#555] tracking-wider uppercase">
                      {sceneCount} {lang === 'pt' ? 'cenas' : 'scenes'} • {frameCount} frames • {sceneVideos.length} {lang === 'pt' ? 'videos' : 'videos'}
                    </p>
                  </div>
                  <span className="text-[11px] font-mono tracking-wider uppercase text-amber-400 flex-shrink-0 group-hover:underline">
                    {lang === 'pt' ? 'Ver >' : 'View >'}
                  </span>
                </div>
              </button>
            </div>
            );
          })()}

          {/* ── HORIZONTAL SCROLL: Cenas Individuais ── */}
          {outputs.filter(o => o.label !== 'complete' && o.url).length > 0 && (
            <div data-testid="deliverables-cenas">
              <p className="text-[10px] font-mono tracking-[0.2em] uppercase text-[#555] mb-2">
                {lang === 'pt' ? 'Cenas Individuais' : 'Individual Scenes'} ({outputs.filter(o => o.label !== 'complete').length})
              </p>
              <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-hide">
                {outputs.filter(o => o.label !== 'complete').map((out, i) => {
                  const sceneState = (agentStatus.scene_status || {})[String(out.scene_number)] || '';
                  const isRegenerating = regenScene === out.scene_number;
                  const allSceneVids = outputs.filter(o => o.label !== 'complete' && o.url);
                  return (
                    <div key={out.id || i} className="flex-shrink-0 w-[200px] rounded-xl overflow-hidden border border-white/5 bg-[#0A0A0A] group hover:border-[#C9A84C]/20 transition-all duration-300 cursor-pointer"
                      data-testid={`deliverable-cena-${out.scene_number}`}
                      onClick={() => setPreviewModal({ type: 'video', data: { ...out, allVideos: allSceneVids } })}>
                      <div className="relative aspect-video bg-black">
                        <video src={out.url} preload="metadata" className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                          data-testid={`result-video-${i}`}
                          onMouseEnter={e => { e.target.play().catch(() => {}); }} onMouseLeave={e => { e.target.pause(); e.target.currentTime = 0; }} muted />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent pointer-events-none" />
                        <span className="absolute bottom-1.5 left-1.5 text-[11px] font-mono text-white/80 tracking-wider">
                          {lang === 'pt' ? 'CENA' : 'SCENE'} {out.scene_number}
                        </span>
                        {/* Play overlay */}
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                          <div className="w-8 h-8 rounded-full bg-black/60 backdrop-blur-sm border border-white/20 flex items-center justify-center">
                            <Play size={12} className="text-white ml-0.5" fill="white" />
                          </div>
                        </div>
                      </div>
                      <div className="p-2 flex items-center gap-1.5">
                        <a href={out.url} download onClick={e => e.stopPropagation()} className="flex-1 text-center text-[11px] font-mono tracking-wider uppercase text-[#888] hover:text-[#C9A84C] transition py-1">
                          <Download size={10} className="inline mr-1" />Download
                        </a>
                        <button onClick={e => { e.stopPropagation(); regenerateScene(out.scene_number); }} disabled={isRegenerating}
                          data-testid={`result-regen-${out.scene_number}`}
                          className="text-[11px] text-[#555] hover:text-[#C9A84C] transition p-1 disabled:opacity-40">
                          <RefreshCw size={10} className={isRegenerating ? 'animate-spin' : ''} />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Failed scenes */}
          {scenes.filter(s => !outputs.find(o => o.scene_number === s.scene_number && o.url)).length > 0 && (
            <div className="rounded-xl border border-red-500/10 bg-red-500/5 p-3 space-y-2">
              <p className="text-[10px] font-mono tracking-wider uppercase text-red-400">
                {lang === 'pt' ? 'Cenas Pendentes' : 'Pending Scenes'}
              </p>
              {scenes.filter(s => !outputs.find(o => o.scene_number === s.scene_number && o.url)).map(s => (
                <div key={s.scene_number} className="flex items-center gap-2">
                  <span className="text-xs text-red-300/70 flex-1 font-sans">Cena {s.scene_number}: {s.title}</span>
                  <button onClick={() => regenerateScene(s.scene_number)} disabled={regenScene === s.scene_number}
                    data-testid={`failed-regen-${s.scene_number}`}
                    className="rounded-sm px-2.5 py-1 text-[11px] font-mono tracking-wider uppercase bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 flex items-center gap-1 disabled:opacity-50 transition">
                    <RefreshCw size={8} className={regenScene === s.scene_number ? 'animate-spin' : ''} />
                    Retry
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Post-Production Sheet (Drawer) */}
          {showPostProd && outputs.length > 0 && (
            <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-end sm:items-center justify-center" onClick={() => setShowPostProd(false)}>
              <div className="w-full sm:max-w-lg max-h-[85vh] bg-[#0A0A0A] border border-white/5 rounded-t-2xl sm:rounded-xl overflow-y-auto" onClick={e => e.stopPropagation()}>
                <div className="sticky top-0 bg-[#0A0A0A] border-b border-white/5 p-3 flex items-center justify-between z-10">
                  <h3 className="text-sm font-medium text-white">{lang === 'pt' ? 'Pós-Produção' : 'Post-Production'}</h3>
                  <button onClick={() => setShowPostProd(false)} data-testid="close-post-production" className="text-[#555] hover:text-white transition">
                    <X size={16} />
                  </button>
                </div>
                <div className="p-3">
                  <PostProduction
                    project={{
                      id: projectId,
                      language: projectLang || lang,
                      scenes,
                      outputs,
                      ...(() => {
                        const proj = allProjects.find(p => p.id === projectId);
                        return proj ? {
                          agents_output: proj.agents_output,
                          narrations: proj.narrations,
                          voice_config: proj.voice_config,
                          post_production_status: proj.post_production_status,
                        } : {};
                      })(),
                    }}
                    onUpdate={loadProjects}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Bottom navigation */}
          <div className="flex gap-2 pt-2">
            <button onClick={() => {
              skipAutoResume.current = true;
              setStep(0); setProjectId(null); setChatMessages([]); setScenes([]);
              setCharacters([]); setOutputs([]); setAgentStatus({});
              loadProjects();
            }} data-testid="back-to-projects"
              className="flex-1 rounded-sm border border-[#222] py-2.5 text-[10px] font-mono tracking-wider uppercase text-[#666] hover:text-white hover:border-[#444] transition">
              {lang === 'pt' ? 'Projectos' : 'Projects'}
            </button>
            <button onClick={() => setStep(3)} data-testid="go-to-storyboard"
              className="flex-1 rounded-sm border border-[#C9A84C]/20 bg-[#C9A84C]/5 py-2.5 text-[10px] font-mono tracking-wider uppercase text-[#C9A84C] hover:bg-[#C9A84C]/10 transition flex items-center justify-center gap-1.5">
              <Camera size={10} /> Storyboard
            </button>
            <button onClick={() => setStep(5)} data-testid="go-to-config-btn"
              className="flex-1 bg-[#C9A84C] text-black rounded-sm py-2.5 text-[10px] font-mono tracking-wider uppercase font-semibold hover:bg-white transition-colors duration-300 flex items-center justify-center gap-1.5">
              <RefreshCw size={10} /> {lang === 'pt' ? 'Re-produzir' : 'Re-produce'}
            </button>
          </div>
        </div>
      )}

      {/* Avatar Library Modal */}
      <AvatarLibraryModal
        open={showLibrary}
        onClose={() => setShowLibrary(false)}
        projectId={projectId}
        projectAvatarIds={new Set(projectAvatars.map(a => a.id))}
        onImported={handleLibraryImport}
        lang={lang}
      />
    </div>
  );
});

function _calcProgress(status) {
  if (!status.total_scenes) return 0;
  const { current_scene = 0, total_scenes = 1, phase = '', videos_done = 0 } = status;
  if (phase === 'complete') return 100;
  if (phase === 'concatenating') return 95;
  if (phase?.startsWith('generating_video')) {
    const agentPct = 50;
    const videoPct = (videos_done / total_scenes) * 45;
    return Math.min(agentPct + videoPct, 95);
  }
  // Agent phases: photography, music, audio (50% of progress for agents)
  const sceneProgress = ((current_scene - 1) / total_scenes);
  const phaseMultiplier = phase === 'photography' ? 0.3 : phase === 'generating_keyframes' ? 0.5 : phase === 'music' ? 0.6 : phase === 'audio' ? 0.9 : 1;
  return Math.min(sceneProgress * 50 * phaseMultiplier + 5, 50);
}
