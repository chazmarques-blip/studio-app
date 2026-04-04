import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PenTool, Palette, CheckCircle, CalendarClock, Loader2, Check, ChevronDown, ChevronUp, ArrowRight, Zap, RotateCcw, Trash2, RefreshCw, AlertTriangle, Crown, Lock, Upload, X, Image, Phone, Globe, Mail, MapPin, FileText, Download, Eye, Clock, Maximize2, MessageSquare, Send, Award, Film, Play, Building2, Plus, Star, Sparkles, Mic, MicOff, Volume2, Shirt, RotateCw, Square, Camera, Bot, ScanEye, ShieldCheck, Briefcase, User, History, Sun, Layers } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import FinalPreview from './FinalPreview';
import { DirectedStudio } from './DirectedStudio';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import { getErrorMsg } from '../utils/getErrorMsg';
import {
  cleanDisplayText, STEP_META, STEP_ORDER, PLATFORMS,
  ProgressTimer, ImageLightbox, StepCard,
  CopyApproval, DesignApproval, VideoApproval,
  CompletedSummary, HistoryCard, AssetUploader,
  ActivePipelineView, CompanyModal, AvatarModal,
} from './pipeline';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;


/* ── Main PipelineView ── */
export default function PipelineView({ context }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, i18n } = useTranslation();
  const [pipelines, setPipelines] = useState([]);
  const [activePipeline, setActivePipeline] = useState(null);
  const [campaignName, setCampaignName] = useState('');
  const [briefing, setBriefing] = useState('');
  const [briefingMode, setBriefingMode] = useState('guided'); // 'free' | 'guided'
  const [questionnaire, setQuestionnaire] = useState({
    product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: '',
    gender: '', ageMin: '', ageMax: '', socialClass: '', lifestyle: '', painPoints: '', visualStyle: ''
  });
  const [campaignLang, setCampaignLang] = useState('');
  const [mode, setMode] = useState('semi_auto');
  const [platforms, setPlatforms] = useState(['whatsapp', 'instagram', 'facebook', 'tiktok', 'google_ads', 'telegram', 'email', 'sms']);
  const [creating, setCreating] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [showHistory, setShowHistory] = useState(false);
  const [contactInfo, setContactInfo] = useState({ phone: '', website: '', email: '', address: '' });
  const [applyBrandData, setApplyBrandData] = useState(true);
  const [uploadedAssets, setUploadedAssets] = useState([]);
  const [showFinalPreview, setShowFinalPreview] = useState(false);
  const [skipVideo, setSkipVideo] = useState(false);
  const [videoMode, setVideoMode] = useState('narration'); // 'narration' | 'presenter'
  const [savedBriefings, setSavedBriefings] = useState([]);
  const [musicLibrary, setMusicLibrary] = useState([]);
  const [selectedMusic, setSelectedMusic] = useState('');
  const [musicGenre, setMusicGenre] = useState('All');
  const [playingTrack, setPlayingTrack] = useState(null);
  const audioRef = useRef(null);
  const pollRef = useRef(null);

  // Company management
  const [companies, setCompanies] = useState([]);
  const [activeCompanyId, setActiveCompanyId] = useState(null);
  const [showCompanyModal, setShowCompanyModal] = useState(false);
  const [editingCompanyId, setEditingCompanyId] = useState(null);
  const [newCompany, setNewCompany] = useState({ name: '', phone: '', is_whatsapp: true, website_url: '', logo_url: '', product_description: '', profile_type: 'company' });

  // Campaign Type Selector
  const [campaignTypes, setCampaignTypes] = useState(['image_post']);
  const isDirectedMode = campaignTypes.includes('directed_studio');

  // Auto-select directed studio mode from URL param
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    if (params.get('mode') === 'directed') {
      setCampaignTypes(['directed_studio']);
    }
  }, [location.search]);

  const toggleCampaignType = (typeId) => {
    if (typeId === 'directed_studio') {
      // Directed is exclusive — toggle it and clear others
      setCampaignTypes(prev => prev.includes('directed_studio') ? ['image_post'] : ['directed_studio']);
    } else {
      // Auto types — multi-select, but clear directed if active
      setCampaignTypes(prev => {
        const without = prev.filter(t => t !== 'directed_studio');
        if (without.includes(typeId)) {
          const removed = without.filter(t => t !== typeId);
          return removed.length === 0 ? ['image_post'] : removed;
        }
        return [...without, typeId];
      });
    }
  };
  // Avatar Gallery (standalone, multiple avatars)
  const [avatars, setAvatars] = useState([]); // [{ id, url, name, source_photo_url }]
  const [selectedAvatarId, setSelectedAvatarId] = useState(null);
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [avatarSourcePhoto, setAvatarSourcePhoto] = useState(null);
  const [avatarSourceType, setAvatarSourceType] = useState('video'); // 'photo' | 'video' (current upload mode)
  const [avatarVideoUploading, setAvatarVideoUploading] = useState(false);
  const [avatarExtractedAudio, setAvatarExtractedAudio] = useState(null); // { url }
  const [avatarVideoFrames, setAvatarVideoFrames] = useState([]); // extra frame URLs from video
  const [masteringVoice, setMasteringVoice] = useState(false);
  const [generatingPreviewVideo, setGeneratingPreviewVideo] = useState(false);
  const [previewVideoUrl, setPreviewVideoUrl] = useState(null);
  const [previewLanguage, setPreviewLanguage] = useState('pt');
  const [avatarName, setAvatarName] = useState('');
  const [avatarMediaTab, setAvatarMediaTab] = useState('photo'); // 'photo' | 'video'
  const [accuracyProgress, setAccuracyProgress] = useState(null); // { iteration, progress, iterations }
  const [generatingAvatar, setGeneratingAvatar] = useState(false);
  const [avatarPhotoUploading, setAvatarPhotoUploading] = useState(false);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState(null);
  const [logoUploading, setLogoUploading] = useState(false);
  // Avatar customization stage
  const [avatarStage, setAvatarStage] = useState('upload'); // 'upload' | 'customize'
  const [avatarCreationMode, setAvatarCreationMode] = useState('photo'); // 'photo' | 'prompt' | '3d'
  const [avatarPromptText, setAvatarPromptText] = useState('');
  const [avatarPromptGender, setAvatarPromptGender] = useState('female');
  const [avatarPromptStyle, setAvatarPromptStyle] = useState('custom'); // 'custom' | 'realistic' | '3d_cartoon' | '3d_pixar'
  const [tempAvatar, setTempAvatar] = useState(null); // { url, source_photo_url, clothing, voice }
  const [editingAvatarId, setEditingAvatarId] = useState(null); // null = new, string = editing existing
  const [customizeTab, setCustomizeTab] = useState('clothing');
  const [applyingClothing, setApplyingClothing] = useState(false);
  const [clothingVariants, setClothingVariants] = useState({}); // { company_uniform: url, casual: url, ... }
  const [generatingAngle, setGeneratingAngle] = useState(null);
  const [angleImages, setAngleImages] = useState({});
  const [auto360Progress, setAuto360Progress] = useState(null); // null | { completed: number, total: 4 }
  const [voiceTab, setVoiceTab] = useState('bank'); // 'bank' | 'premium' | 'record'
  const [loadingVoicePreview, setLoadingVoicePreview] = useState(null);
  const [playingVoiceId, setPlayingVoiceId] = useState(null);
  const [elevenLabsVoices, setElevenLabsVoices] = useState([]);
  const [elevenLabsAvailable, setElevenLabsAvailable] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState(null);
  const [recordedAudioBlob, setRecordedAudioBlob] = useState(null);
  const [uploadingRecording, setUploadingRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioPlayerRef = useRef(null);
  const avatarInputRef = useRef(null);
  const logoInputRef = useRef(null);

  // AI Avatar Editing
  const [aiEditAvatarId, setAiEditAvatarId] = useState(null);
  const [aiEditInstruction, setAiEditInstruction] = useState('');
  const [aiEditLoading, setAiEditLoading] = useState(false);

  // Avatar Edit History (for customize modal)
  const [avatarEditHistory, setAvatarEditHistory] = useState([]); // [{url, instruction, timestamp, isBase}]
  const [avatarBaseUrl, setAvatarBaseUrl] = useState(null); // Original base character URL
  const [lastCreatedAvatar, setLastCreatedAvatar] = useState(null); // Track last created/edited avatar for DirectedStudio

  useEffect(() => {
    // Load companies and avatars from Supabase (source of truth)
    const loadUserData = async () => {
      try {
        const [companiesRes, avatarsRes] = await Promise.all([
          axios.get(`${API}/data/companies`),
          axios.get(`${API}/data/avatars`),
        ]);
        // API is source of truth — always use server data, clear stale localStorage
        const serverCompanies = companiesRes.data || [];
        const serverAvatars = avatarsRes.data || [];
        setCompanies(serverCompanies);
        setAvatars(serverAvatars);
        localStorage.setItem('studiox_companies', JSON.stringify(serverCompanies));
        localStorage.setItem('studiox_avatars', JSON.stringify(serverAvatars));
        if (serverCompanies.length) {
          // Don't auto-select - let user choose or create generic campaign
        }
        if (serverAvatars.length) {
          setSelectedAvatarId(serverAvatars[0].id);
        }
      } catch {
        // Fallback to localStorage ONLY if API fails (e.g. not authenticated)
        try { const p = JSON.parse(localStorage.getItem('studiox_companies') || '[]'); setCompanies(p); } catch {}
        try { const p = JSON.parse(localStorage.getItem('studiox_avatars') || '[]'); setAvatars(p); if (p.length) setSelectedAvatarId(p[0].id); } catch {}
      }
    };
    loadUserData();
  }, []);

  const saveCompanies = (list) => {
    setCompanies(list);
    localStorage.setItem('studiox_companies', JSON.stringify(list));
  };

  const addCompany = async () => {
    if (!newCompany.name.trim()) return;
    const co = { ...newCompany, id: Date.now().toString(), is_primary: companies.length === 0 };
    try {
      const { data } = await axios.post(`${API}/data/companies`, co);
      const updated = [...companies, data || co];
      setCompanies(updated);
      setActiveCompanyId((data || co).id);
    } catch {
      const updated = [...companies, co];
      saveCompanies(updated);
      setActiveCompanyId(co.id);
    }
    setNewCompany({ name: '', phone: '', is_whatsapp: true, website_url: '', logo_url: '', product_description: '', profile_type: 'company' });
    setShowCompanyModal(false);
    setEditingCompanyId(null);
    toast.success(t('studio.company_saved'));
  };

  const removeCompany = async (id) => {
    const updated = companies.filter(c => c.id !== id);
    if (updated.length && !updated.some(c => c.is_primary)) updated[0].is_primary = true;
    setCompanies(updated);
    if (activeCompanyId === id) setActiveCompanyId(updated[0]?.id || null);
    try { await axios.delete(`${API}/data/companies/${id}`); } catch {}
  };

  const startEditCompany = (co) => {
    setEditingCompanyId(co.id);
    setNewCompany({ name: co.name, phone: co.phone || '', is_whatsapp: co.is_whatsapp !== false, website_url: co.website_url || '', logo_url: co.logo_url || '', product_description: co.product_description || '', profile_type: co.profile_type || 'company' });
    setShowCompanyModal(true);
  };

  const saveEditCompany = async () => {
    if (!newCompany.name.trim()) return;
    const updatedCo = { ...newCompany, id: editingCompanyId };
    try {
      await axios.post(`${API}/data/companies`, updatedCo);
    } catch {}
    const updated = companies.map(c => c.id === editingCompanyId ? { ...c, ...newCompany } : c);
    setCompanies(updated);
    setEditingCompanyId(null);
    setNewCompany({ name: '', phone: '', is_whatsapp: true, website_url: '', logo_url: '', product_description: '', profile_type: 'company' });
    setShowCompanyModal(false);
    toast.success(t('studio.company_updated'));
  };

  const cancelCompanyForm = () => {
    setShowCompanyModal(false);
    setEditingCompanyId(null);
    setNewCompany({ name: '', phone: '', is_whatsapp: true, website_url: '', logo_url: '', product_description: '', profile_type: 'company' });
  };

  const uploadCompanyLogo = async (files) => {
    if (!files?.length) return;
    const file = files[0];
    if (!file.type?.startsWith('image/')) return;
    setLogoUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('asset_type', 'company_logo');
      const { data } = await axios.post(`${API}/campaigns/pipeline/upload`, form);
      setNewCompany(p => ({ ...p, logo_url: data.url }));
    } catch (e) {
      toast.error(getErrorMsg(e, 'Upload error'));
    }
    setLogoUploading(false);
  };

  const setPrimaryCompany = async (id) => {
    const updated = companies.map(c => ({ ...c, is_primary: c.id === id }));
    setCompanies(updated);
    try { await axios.post(`${API}/data/companies/primary/${id}`); } catch {}
  };

  // Stable callbacks for DirectedStudio (avoid re-renders)
  const handleAddAvatarDirected = useCallback((promptText) => {
    resetAvatarModal();
    if (promptText) { setAvatarPromptText(promptText); setAvatarCreationMode('prompt'); }
    setShowAvatarModal(true);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleEditAvatarDirected = useCallback((av) => {
    console.log('🔧 handleEditAvatarDirected called with avatar:', av);
    // CRITICAL FIX: Ensure avatar from library has required fields
    const avatarToEdit = {
      id: av.id,
      url: av.url,
      name: av.name || 'Personagem sem nome',
      source_photo_url: av.source_photo_url || '',
      clothing: av.clothing || 'company_uniform',
      voice: av.voice || null,
      angles: av.angles || {},
      video_url: av.video_url || null,
      language: av.language || 'pt',
      creation_mode: av.creation_mode || 'photo',
      avatar_style: av.avatar_style || 'realistic',
      edit_history: av.edit_history || [],
    };
    console.log('📝 Opening avatar for edit:', avatarToEdit);
    openAvatarForEdit(avatarToEdit);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleRemoveAvatarDirected = useCallback((av) => {
    removeAvatar(av);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handlePreviewAvatarDirected = useCallback((url) => {
    setAvatarPreviewUrl(url);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAiEditAvatarDirected = useCallback((id) => {
    aiEditAvatar(id);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const activeCompany = companies.find(c => c.id === activeCompanyId) || null;
  const selectedAvatar = avatars.find(a => a.id === selectedAvatarId) || null;

  // Auto-fill campaign name and briefing product when company changes
  useEffect(() => {
    if (activeCompany) {
      setCampaignName(activeCompany.name || '');
      setQuestionnaire(q => ({ ...q, product: activeCompany.product_description || activeCompany.name || '' }));
    } else {
      setCampaignName('');
      setQuestionnaire(q => ({ ...q, product: '' }));
    }
  }, [activeCompanyId]); // eslint-disable-line react-hooks/exhaustive-deps


  const saveAvatars = (list) => {
    setAvatars(list);
    localStorage.setItem('studiox_avatars', JSON.stringify(list));
  };

  const persistAvatarToServer = async (avatar) => {
    try {
      const { data } = await axios.post(`${API}/data/avatars`, avatar);
      // CRITICAL FIX: Invalidate library cache so new avatar appears in gallery
      localStorage.removeItem('studiox_avatar_library_v2');
      return data;
    } catch {
      return null;
    }
  };

  const uploadAvatarPhoto = async (files) => {
    if (!files?.length) return;
    const file = files[0];
    if (!file.type?.startsWith('image/')) { toast.error(t('studio.err_generic')); return; }
    if (file.size > 10 * 1024 * 1024) { toast.error('File exceeds 10MB'); return; }
    setAvatarPhotoUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('asset_type', 'avatar_source');
      const { data } = await axios.post(`${API}/campaigns/pipeline/upload`, form);
      setAvatarSourcePhoto({ url: data.url, preview: URL.createObjectURL(file) });
      toast.success(t('studio.photo_uploaded_toast'));
    } catch (e) {
      toast.error(getErrorMsg(e, t('studio.err_generic')));
    }
    setAvatarPhotoUploading(false);
  };

  const uploadAvatarVideo = async (files) => {
    if (!files?.length) return;
    const file = files[0];
    if (!file.type?.startsWith('video/')) { toast.error('Selecione um arquivo de vídeo'); return; }
    if (file.size > 50 * 1024 * 1024) { toast.error('Vídeo excede 50MB'); return; }
    setAvatarVideoUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await axios.post(`${API}/campaigns/pipeline/extract-from-video`, form, { timeout: 120000 });
      if (data.frame_url) {
        setAvatarSourcePhoto({ url: data.frame_url, preview: data.frame_url });
        // Store extra frames for enhanced identity matching
        if (data.extra_frame_urls?.length) {
          setAvatarVideoFrames(data.extra_frame_urls);
        }
        if (data.audio_url) {
          setAvatarExtractedAudio({ url: data.audio_url });
          toast.success(t('studio.video_extracted'));
        } else {
          toast.success(t('studio.frame_extracted'));
        }
      }
    } catch (e) {
      toast.error(getErrorMsg(e, t('studio.err_generic')));
    }
    setAvatarVideoUploading(false);
  };

  const startAuto360 = async (sourceUrl, clothing = 'company_uniform', style = 'realistic') => {
    setAuto360Progress({ completed: 0, total: 4 });
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-360`, {
        source_image_url: sourceUrl,
        clothing,
        logo_url: activeCompany?.logo_url || '',
        avatar_style: style,
      });
      if (data.job_id) {
        const pollInterval = setInterval(async () => {
          try {
            const { data: status } = await axios.get(`${API}/campaigns/pipeline/generate-avatar-360/${data.job_id}`);
            const completed = status.completed || Object.values(status.results || {}).filter(Boolean).length;
            setAuto360Progress({ completed, total: 4 });
            if (status.results) {
              setAngleImages(prev => ({ ...prev, ...Object.fromEntries(Object.entries(status.results).filter(([,v]) => v)) }));
            }
            if (status.status === 'completed' || status.status === 'failed') {
              clearInterval(pollInterval);
              setAuto360Progress(null);
              if (status.status === 'completed') {
                toast.success(t('studio.angles_generated') || '360° generated!');
              }
            }
          } catch { /* keep polling */ }
        }, 6000);
      }
    } catch (e) {
      setAuto360Progress(null);
      toast.error('Error starting 360° generation');
    }
  };

  const generateAvatarFromPhoto = async () => {
    setGeneratingAvatar(true);
    setAccuracyProgress(null);
    try {
      // Use accuracy agent endpoint with polling
      const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-with-accuracy`, {
        source_image_url: avatarSourcePhoto?.url || '',
        video_frame_urls: avatarVideoFrames || [],
        company_name: activeCompany?.name || '',
        logo_url: activeCompany?.logo_url || '',
        max_iterations: 3,
      });
      if (data.job_id) {
        const pollInterval = setInterval(async () => {
          try {
            const { data: status } = await axios.get(`${API}/campaigns/pipeline/generate-avatar-with-accuracy/${data.job_id}`);
            // Update progress for UI
            if (status.iteration || status.iterations) {
              setAccuracyProgress({
                iteration: status.iteration || 0,
                progress: status.progress || '',
                iterations: status.iterations || [],
                active_agent: status.active_agent || null,
                agents: status.agents || [],
              });
            }
            if (status.status === 'completed' && status.avatar_url) {
              clearInterval(pollInterval);
              const autoVoice = avatarExtractedAudio ? { type: 'custom', url: avatarExtractedAudio.url } : null;
              setTempAvatar({
                url: status.avatar_url,
                source_photo_url: avatarSourcePhoto?.url || '',
                clothing: 'company_uniform',
                voice: autoVoice,
                accuracy_iterations: status.iterations || [],
                avatar_style: 'realistic',
              });
              setAvatarStage('customize');
              setAngleImages({});
              setClothingVariants({});
              if (autoVoice) {
                setRecordedAudioUrl(avatarExtractedAudio.url);
                setVoiceTab('record');
              }
              setAccuracyProgress(null);
              setGeneratingAvatar(false);
              // Initialize edit history with generated avatar as base
              const genUrl = status.url;
              setAvatarBaseUrl(genUrl);
              setAvatarEditHistory([{ url: genUrl, instruction: 'Base original', timestamp: new Date().toISOString(), isBase: true }]);
              toast.success(`${t('studio.avatar_generated')} (Score: ${status.final_score || '?'}/10)`);
              // Auto-generate 360° angles
              startAuto360(avatarSourcePhoto?.url || status.avatar_url, 'company_uniform', 'realistic');
            } else if (status.status === 'failed') {
              clearInterval(pollInterval);
              setAccuracyProgress(null);
              setGeneratingAvatar(false);
              toast.error(status.error || t('studio.err_generic'));
            }
          } catch { /* keep polling */ }
        }, 4000);
      }
    } catch (e) {
      toast.error(getErrorMsg(e, t('studio.err_generic')));
      setAccuracyProgress(null);
      setGeneratingAvatar(false);
    }
  };

  const generateAvatarFromPrompt = async () => {
    if (!avatarPromptText.trim()) { toast.error(t('studio.prompt_required') || 'Describe the avatar'); return; }
    setGeneratingAvatar(true);
    setAccuracyProgress({ progress: t('studio.generating_avatar') || 'Generating avatar from description...' });
    try {
      const style = avatarPromptStyle;
      const payload = {
        prompt: avatarPromptText,
        gender: avatarPromptGender,
        style,
        company_name: activeCompany?.name || '',
        logo_url: activeCompany?.logo_url || '',
      };
      // Pass photo reference for 3D mode if available
      if (avatarCreationMode === '3d' && avatarSourcePhoto?.url) {
        payload.reference_photo_url = avatarSourcePhoto.url;
      }
      const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-from-prompt`, payload);
      if (data.avatar_url) {
        setTempAvatar({
          url: data.avatar_url,
          source_photo_url: '',
          clothing: 'company_uniform',
          voice: null,
          creation_mode: avatarCreationMode,
          avatar_style: style,
        });
        setAvatarStage('customize');
        setAngleImages({});
        setClothingVariants({});
        setAccuracyProgress(null);
        setGeneratingAvatar(false);
        // Initialize edit history with generated avatar as base
        setAvatarBaseUrl(data.avatar_url);
        setAvatarEditHistory([{ url: data.avatar_url, instruction: 'Base original', timestamp: new Date().toISOString(), isBase: true }]);
        toast.success(t('studio.avatar_generated') || 'Avatar generated!');
        startAuto360(data.avatar_url, 'company_uniform', style);
      }
    } catch (e) {
      toast.error(getErrorMsg(e, t('studio.err_generic')));
      setAccuracyProgress(null);
      setGeneratingAvatar(false);
    }
  };

  const saveAvatarAndClose = () => {
    if (!tempAvatar) return;
    
    // CRITICAL FIX: Don't save if avatar has no URL (still generating)
    if (!tempAvatar.url || !tempAvatar.url.trim()) {
      toast.error('Aguarde a geração do personagem finalizar antes de salvar!');
      return;
    }
    
    const name = avatarName.trim() || `Avatar ${avatars.length + 1}`;
    if (editingAvatarId) {
      const editedAvatar = {
        id: editingAvatarId, url: tempAvatar.url, clothing: tempAvatar.clothing,
        voice: tempAvatar.voice, angles: angleImages, name,
        source_photo_url: tempAvatar.source_photo_url || '',
        video_url: previewVideoUrl || null,
        language: previewLanguage,
        avatar_style: tempAvatar.avatar_style || 'realistic',
        creation_mode: tempAvatar.creation_mode || 'photo',
        edit_history: avatarEditHistory,
      };
      const updated = avatars.map(a => a.id === editingAvatarId ? { ...a, ...editedAvatar } : a);
      saveAvatars(updated);
      persistAvatarToServer(editedAvatar);
      setLastCreatedAvatar({ ...editedAvatar, _ts: Date.now() });
    } else {
      const newAv = {
        id: Date.now().toString(),
        url: tempAvatar.url,
        name,
        source_photo_url: tempAvatar.source_photo_url,
        clothing: tempAvatar.clothing,
        voice: tempAvatar.voice,
        angles: angleImages,
        video_url: previewVideoUrl || null,
        language: previewLanguage,
        avatar_style: tempAvatar.avatar_style || 'realistic',
        creation_mode: tempAvatar.creation_mode || 'photo',
        edit_history: avatarEditHistory,
      };
      const updated = [...avatars, newAv];
      saveAvatars(updated);
      setSelectedAvatarId(newAv.id);
      persistAvatarToServer(newAv);
      setLastCreatedAvatar({ ...newAv, _ts: Date.now() });
    }
    resetAvatarModal();
  };

  const saveAvatarAsNew = () => {
    if (!tempAvatar) return;
    const name = avatarName.trim() || `Avatar ${avatars.length + 1}`;
    const newAv = {
      id: Date.now().toString(),
      url: tempAvatar.url,
      name,
      source_photo_url: tempAvatar.source_photo_url,
      clothing: tempAvatar.clothing,
      voice: tempAvatar.voice,
      angles: angleImages,
      video_url: previewVideoUrl || null,
      language: previewLanguage,
      creation_mode: tempAvatar.creation_mode || 'photo',
      avatar_style: tempAvatar.avatar_style || 'realistic',
      edit_history: avatarEditHistory,
    };
    const updated = [...avatars, newAv];
    saveAvatars(updated);
    setSelectedAvatarId(newAv.id);
    persistAvatarToServer(newAv);
    setLastCreatedAvatar({ ...newAv, _ts: Date.now() });
    resetAvatarModal();
    toast.success('Avatar saved as new!');
  };

  const openAvatarForEdit = (av) => {
    console.log('🎨 openAvatarForEdit - Starting edit for:', av.name, av.id);
    console.log('🎨 Avatar data:', av);
    
    setEditingAvatarId(av.id);
    // Infer avatar_style from creation_mode for avatars saved before the fix
    let inferredStyle = av.avatar_style || 'realistic';
    if (!av.avatar_style && av.creation_mode === '3d') {
      inferredStyle = '3d_pixar'; // Default 3D mode to pixar if not specified
    }
    const is3dAvatar = inferredStyle !== 'realistic';
    setTempAvatar({
      url: av.url,
      source_photo_url: av.source_photo_url || '',
      clothing: av.clothing || 'company_uniform',
      voice: av.voice || null,
      avatar_style: inferredStyle,
      creation_mode: av.creation_mode || 'photo',
    });
    setAvatarName(av.name || '');
    setPreviewVideoUrl(av.video_url || null);
    setAvatarMediaTab(av.video_url ? 'photo' : 'photo');
    // For 3D avatars, only load angles that were generated with 3D style
    // If the avatar is 3D but angles were saved from a previous realistic generation, clear them
    const savedAngles = av.angles || {};
    if (is3dAvatar && savedAngles.front && savedAngles.front !== av.url) {
      // Angles from before the fix — clear them and set front to the 3D avatar itself
      setAngleImages({ front: av.url });
    } else {
      setAngleImages(savedAngles.front ? savedAngles : { front: av.url });
    }
    // Load saved language
    setPreviewLanguage(av.language || 'pt');
    // Restore audio from saved voice
    if (av.voice?.url) {
      setRecordedAudioUrl(av.voice.url);
      setVoiceTab('record');
    } else if (av.voice?.type === 'elevenlabs' && av.voice?.voice_id) {
      setVoiceTab('premium');
    } else if (av.voice?.voice_id) {
      setVoiceTab('bank');
    }
    // Rebuild clothing variants from angles if available
    const variants = {};
    if (av.clothing && av.url) variants[av.clothing] = av.url;
    setClothingVariants(variants);
    setAvatarStage('customize');
    setCustomizeTab('clothing');
    setShowAvatarModal(true);
    console.log('✅ Avatar modal OPENED for editing:', av.name);
    // Load saved edit history or initialize with current avatar as base
    const savedHistory = av.edit_history && av.edit_history.length > 0 ? av.edit_history : [];
    if (savedHistory.length > 0) {
      setAvatarEditHistory(savedHistory);
      const baseEntry = savedHistory.find(e => e.isBase);
      setAvatarBaseUrl(baseEntry ? baseEntry.url : av.url);
    } else {
      setAvatarBaseUrl(av.url);
      setAvatarEditHistory([{ url: av.url, instruction: 'Base original', timestamp: new Date().toISOString(), isBase: true }]);
    }
  };

  const resetAvatarModal = () => {
    setShowAvatarModal(false);
    setAvatarSourcePhoto(null);
    setAvatarSourceType('video');
    setAvatarVideoUploading(false);
    setAvatarExtractedAudio(null);
    setAvatarVideoFrames([]);
    setAvatarStage('upload');
    setAvatarCreationMode('photo');
    setAvatarPromptText('');
    setAvatarPromptGender('female');
    setAvatarPromptStyle('custom');
    setTempAvatar(null);
    setEditingAvatarId(null);
    setCustomizeTab('clothing');
    setAvatarEditHistory([]);
    setAvatarBaseUrl(null);
    setAngleImages({});
    setClothingVariants({});
    setAuto360Progress(null);
    setRecordedAudioUrl(null);
    setRecordedAudioBlob(null);
    setPreviewVideoUrl(null);
    setPreviewLanguage('pt');
    setAvatarName('');
    setAvatarMediaTab('photo');
    setAccuracyProgress(null);
  };

  const aiEditAvatar = async (avatarId) => {
    if (!aiEditInstruction.trim() || aiEditLoading) return;
    const av = avatars.find(a => a.id === avatarId);
    if (!av) return;
    setAiEditLoading(true);
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/edit-avatar`, {
        avatar_url: av.url,
        instruction: aiEditInstruction,
        base_url: av.url, // For gallery edits, base is the avatar itself
      });
      if (data.url) {
        const updated = avatars.map(a => a.id === avatarId ? { ...a, url: data.url } : a);
        saveAvatars(updated);
        try { 
          await axios.post(`${API}/data/avatars`, { ...av, url: data.url }); 
          // CRITICAL FIX: Invalidate library cache so new avatar appears in gallery
          localStorage.removeItem('studiox_avatar_library_v2');
        } catch {}
        setLastCreatedAvatar({ ...av, url: data.url, _ts: Date.now() });
        toast.success(t('studio.avatar_edited') || 'Avatar editado com IA!');
      }
    } catch (err) {
      toast.error(getErrorMsg(err, 'Erro ao editar avatar'));
    } finally {
      setAiEditLoading(false);
      setAiEditAvatarId(null);
      setAiEditInstruction('');
    }
  };

  const applyClothing = async (style) => {
    if (!tempAvatar) return;
    // If already generated this style, just select it
    if (clothingVariants[style]) {
      setTempAvatar(p => ({ ...p, url: clothingVariants[style], clothing: style }));
      return;
    }
    setApplyingClothing(true);
    const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
    // For 3D avatars, always use the generated avatar URL (not the original photo)
    const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-variant`, {
        source_image_url: sourceUrl,
        clothing: style,
        angle: 'front',
        company_name: activeCompany?.name || '',
        logo_url: activeCompany?.logo_url || '',
        avatar_style: tempAvatar?.avatar_style || 'realistic',
      });
      if (data.avatar_url) {
        setClothingVariants(p => ({ ...p, [style]: data.avatar_url }));
        setTempAvatar(p => ({ ...p, url: data.avatar_url, clothing: style }));
        setAngleImages({ front: data.avatar_url });
        // Auto-generate remaining 360° angles for this style
        startAuto360(sourceUrl, style, tempAvatar?.avatar_style || 'realistic');
      }
    } catch (e) {
      toast.error(getErrorMsg(e, 'Error'));
    }
    setApplyingClothing(false);
  };

  const generateAngle = async (angle, forceRegenerate = false) => {
    if (!tempAvatar || (angleImages[angle] && !forceRegenerate)) return;
    setGeneratingAngle(angle);
    const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
    const sourceUrl = isDirectedMode ? tempAvatar.url : (is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url));
    const clothing = isDirectedMode ? 'keep_original' : (tempAvatar.clothing || 'company_uniform');
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-variant`, {
        source_image_url: sourceUrl,
        clothing,
        angle,
        company_name: activeCompany?.name || '',
        logo_url: activeCompany?.logo_url || '',
        avatar_style: tempAvatar?.avatar_style || 'realistic',
      });
      if (data.avatar_url) {
        setAngleImages(p => ({ ...p, [angle]: data.avatar_url }));
      }
    } catch (e) {
      toast.error('Error generating angle');
    }
    setGeneratingAngle(null);
  };

  const previewVoice = async (voiceId, voiceType = 'openai') => {
    setLoadingVoicePreview(voiceId);
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/voice-preview`, {
        voice_id: voiceId,
        voice_type: voiceType,
        text: t('studio.voice_preview_text') || 'Hello! This is a preview of my voice. I can be the presenter for your marketing campaigns.',
      });
      if (data.audio_url) {
        if (audioPlayerRef.current) { audioPlayerRef.current.pause(); }
        const audio = new Audio(data.audio_url);
        audioPlayerRef.current = audio;
        setPlayingVoiceId(voiceId);
        audio.onended = () => setPlayingVoiceId(null);
        audio.play();
      }
    } catch (e) {
      toast.error('Error loading preview');
    }
    setLoadingVoicePreview(null);
  };

  const startRecording = async () => {
    try {
      // Check if running in iframe (mic blocked by feature policy)
      if (window.self !== window.top) {
        const appUrl = window.location.href;
        toast.error(`Open the app in a new tab to use the microphone`, { duration: 6000 });
        window.open(appUrl, '_blank');
        return;
      }
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        toast.error('Your browser does not support audio recording');
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm'
        : MediaRecorder.isTypeSupported('audio/mp4') ? 'audio/mp4' : '';
      const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        setRecordedAudioBlob(blob);
        setRecordedAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(track => track.stop());
      };
      recorder.start(100);
      setIsRecording(true);
      setRecordedAudioUrl(null);
      setRecordedAudioBlob(null);
    } catch (e) {
      console.error('Recording error:', e);
      toast.error(
        e.name === 'NotAllowedError'
          ? 'Microphone blocked. Open the app in a new tab to use the microphone.'
          : e.name === 'NotFoundError' ? 'No microphone found.' : `Error: ${e.message}`
      );
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const saveRecordingAsVoice = async () => {
    if (!recordedAudioBlob) return;
    setUploadingRecording(true);
    try {
      const ext = recordedAudioBlob.type.includes('mp4') ? 'mp4' : 'webm';
      const form = new FormData();
      form.append('file', recordedAudioBlob, `recording.${ext}`);
      const { data } = await axios.post(`${API}/campaigns/pipeline/upload-voice-recording`, form);
      if (data.audio_url) {
        setRecordedAudioUrl(data.audio_url);
        setTempAvatar(p => ({ ...p, voice: { type: 'custom', url: data.audio_url } }));
        toast.success(t('studio.recording_saved'));
      }
    } catch (e) {
      toast.error('Upload error');
    }
    setUploadingRecording(false);
  };

  const removeAvatar = async (id) => {
    const updated = avatars.filter(a => a.id !== id);
    saveAvatars(updated);
    if (selectedAvatarId === id) setSelectedAvatarId(updated[0]?.id || null);
    try { await axios.delete(`${API}/data/avatars/${id}`); } catch {}
  };

  useEffect(() => {
    loadPipelines();
    loadSavedHistory();
    loadMusicLibrary();
    loadElevenLabsVoices();
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    };
  }, []);

  const loadMusicLibrary = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/music-library`);
      setMusicLibrary(data.tracks || []);
    } catch { /* ignore */ }
  };

  const loadElevenLabsVoices = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/elevenlabs-voices`);
      setElevenLabsVoices(data.voices || []);
      setElevenLabsAvailable(data.available || false);
    } catch { /* ignore */ }
  };

  const togglePlayTrack = (trackId) => {
    if (playingTrack === trackId) {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      setPlayingTrack(null);
    } else {
      if (audioRef.current) { audioRef.current.pause(); }
      const audio = new Audio(`${API}/campaigns/pipeline/music-preview/${trackId}`);
      audio.volume = 0.5;
      audio.play().catch(() => {});
      audio.onended = () => setPlayingTrack(null);
      audioRef.current = audio;
      setPlayingTrack(trackId);
    }
  };


  const loadSavedHistory = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/saved/history`);
      setSavedBriefings(data.briefings || []);
    } catch (err) {
      console.error('Failed to load saved history:', err?.response?.status, err?.response?.data, err?.message);
    }
  };

  useEffect(() => {
    if (!activePipeline) return;
    const steps = activePipeline.steps || {};
    const newExpanded = { ...expandedSteps };
    let changed = false;
    STEP_ORDER.forEach(s => {
      const st = steps[s];
      if (!st) return;
      if (activePipeline.status === 'waiting_approval' && st.status === 'completed' && (s === 'ana_review_copy' || s === 'rafael_review_design' || s === 'rafael_review_video') && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
          if (activePipeline.status === 'waiting_audio_approval' && s === 'marcos_video' && st.status === 'waiting_audio_approval' && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
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
    if (activePipeline && ['running', 'pending'].includes(activePipeline.status) && !isDirectedMode) {
      startPolling(activePipeline.id);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [activePipeline?.id, activePipeline?.status, startPolling, isDirectedMode]);

  const loadPipelines = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/list`);
      const list = data.pipelines || [];
      setPipelines(list);
      const active = list.find(p => ['running', 'pending', 'waiting_approval', 'waiting_audio_approval'].includes(p.status));
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
      if (['completed', 'failed', 'waiting_approval', 'waiting_audio_approval', 'requires_upgrade'].includes(data.status)) {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    } catch {}
  };

  const compileBriefing = () => {
    const q = questionnaire;
    const parts = [];
    if (q.product) parts.push(`${t('studio.q_product')} ${q.product}`);
    if (q.goal) parts.push(`${t('studio.q_goal')} ${q.goal}`);
    // Build audience string from selectable fields
    const audienceParts = [];
    if (q.gender) audienceParts.push(`Gender: ${q.gender}`);
    if (q.ageMin || q.ageMax) audienceParts.push(`Age: ${q.ageMin || '18'}–${q.ageMax || '65+'}`);
    if (q.socialClass) audienceParts.push(`Social class: ${q.socialClass}`);
    if (q.lifestyle) audienceParts.push(`Lifestyle: ${q.lifestyle}`);
    if (q.audience) audienceParts.push(q.audience);
    if (audienceParts.length) parts.push(`${t('studio.q_audience')} ${audienceParts.join(', ')}`);
    if (q.painPoints) parts.push(`${t('studio.q_pain_points') || 'Pain points:'} ${q.painPoints}`);
    if (q.tone) parts.push(`${t('studio.q_tone')} ${q.tone}`);
    if (q.visualStyle) parts.push(`${t('studio.q_visual_style') || 'Visual style:'} ${q.visualStyle}`);
    if (q.offer) parts.push(`${t('studio.q_offer')} ${q.offer}`);
    if (q.differentials) parts.push(`${t('studio.q_differentials')} ${q.differentials}`);
    if (q.cta) parts.push(`${t('studio.q_cta')} ${q.cta}`);
    if (q.urgency) parts.push(`${t('studio.q_urgency')} ${q.urgency}`);
    return parts.join('\n');
  };

  const getEffectiveBriefing = () => briefingMode === 'guided' ? compileBriefing() : briefing;

  const createPipeline = async () => {
    const effectiveBriefing = getEffectiveBriefing();
    if (!campaignName.trim()) { toast.error(t('studio.err_name') || 'Define the campaign name'); return; }
    if (!effectiveBriefing.trim() || platforms.length === 0) { toast.error(t('studio.err_briefing') || 'Fill in the briefing and select at least one platform'); return; }
    setCreating(true);
    try {
      const assetPayload = uploadedAssets.map(a => ({ url: a.url, type: a.type, filename: a.filename }));
      // Build adaptive media format specs from selected platforms
      const selectedPlatforms = PLATFORMS.filter(p => platforms.includes(p.id));
      const mediaFormats = {};
      selectedPlatforms.forEach(p => {
        mediaFormats[p.id] = { imgRatio: p.imgRatio, vidRatio: p.vidRatio, imgSize: p.imgSize, vidSize: p.vidSize };
      });
      const { data } = await axios.post(`${API}/campaigns/pipeline`, {
        briefing: effectiveBriefing.trim(), campaign_name: campaignName.trim(), mode, platforms,
        campaign_language: campaignLang || '',
        apply_brand: applyBrandData,
        brand_data: applyBrandData && activeCompany ? {
          company_name: activeCompany.name,
          logo_url: activeCompany.logo_url || '',
          phone: activeCompany.phone || '',
          website_url: activeCompany.website_url || '',
          is_whatsapp: activeCompany.is_whatsapp,
          product_description: activeCompany.product_description || '',
        } : null,
        context: {
          ...(context || {}),
          ...(activeCompany ? { company: activeCompany.name, website_url: activeCompany.website_url } : {}),
        },
        contact_info: applyBrandData && activeCompany ? {
          phone: activeCompany.phone || '',
          website: activeCompany.website_url || '',
          is_whatsapp: activeCompany.is_whatsapp,
        } : contactInfo,
        uploaded_assets: assetPayload,
        media_formats: mediaFormats,
        selected_music: selectedMusic || '',
        skip_video: skipVideo,
        video_mode: skipVideo ? 'none' : videoMode,
        avatar_url: selectedAvatar?.url || '',
        avatar_voice: selectedAvatar?.voice || null,
        campaign_type: campaignTypes,
      });
      setActivePipeline(data);
      setBriefing(''); setCampaignName(''); setExpandedSteps({}); setUploadedAssets([]);
      setQuestionnaire({ product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: '' });
      setCampaignLang('');
      toast.success(t('studio.pipeline_started') || 'Pipeline started!');
    } catch (e) { toast.error(getErrorMsg(e, t('studio.err_create') || 'Error creating pipeline')); }
    setCreating(false);
  };

  const approveStep = async (approvalData) => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/approve`, approvalData);
      toast.success(t('studio.approved') || 'Approved! Next step starting...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(getErrorMsg(e, t('studio.err_approve') || 'Error approving')); }
  };

  const approveAudio = async (approvalData) => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/approve-audio`, {
        feedback: approvalData.feedback || '',
        selection: approvalData.approved ? 1 : 0,
        selected_voice_id: approvalData.selectedVoiceId || '',
      });
      if (approvalData.approved) {
        toast.success(t('studio.audio_approved') || 'Audio approved! Generating video...');
      } else {
        toast.success(t('studio.script_revision') || 'Script revision requested...');
      }
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(getErrorMsg(e, 'Error')); }
  };

  const retryPipeline = async () => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/retry`);
      toast.success(t('studio.retrying') || 'Retrying...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(getErrorMsg(e, t('studio.err_generic') || 'Error')); }
  };

  const deletePipeline = async (id) => {
    try {
      await axios.delete(`${API}/campaigns/pipeline/${id}`);
      if (activePipeline?.id === id) setActivePipeline(null);
      setPipelines(prev => prev.filter(p => p.id !== id));
      toast.success(t('studio.pipeline_removed') || 'Pipeline removed');
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
      toast.success(t('studio.pipeline_archived') || 'Pipeline archived');
    } catch { toast.error(t('studio.err_archive') || 'Error archiving pipeline'); }
  };

  // ── Final Preview Mode ──
  // ── Active Pipeline View ──
  if (activePipeline) {
    return (
      <ActivePipelineView
        activePipeline={activePipeline} expandedSteps={expandedSteps}
        showFinalPreview={showFinalPreview} campaignLang={campaignLang}
        archivePipeline={archivePipeline} approveStep={approveStep}
        approveAudio={approveAudio} toggleStep={toggleStep}
        pollPipeline={pollPipeline} retryPipeline={retryPipeline}
        setShowFinalPreview={setShowFinalPreview} navigate={navigate}
      />
    );
  }

  // ── Creation Form ──
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Pipeline Intro */}
        <div className="text-center py-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#8B5CF6]/5 border border-orange-500/15">
            {STEP_ORDER.map((s, i) => {
              const meta = STEP_META[s];
              const Icon = meta.icon;
              return (
                <div key={s} className="flex items-center gap-1">
                  {i > 0 && <ArrowRight size={8} className="text-[#777]" />}
                  <Icon size={12} style={{ color: meta.color }} />
                </div>
              );
            })}
          </div>
          <p className="text-xs text-[#999] mt-1.5">{STEP_ORDER.map(s => STEP_META[s].agent).join(' \u2192 ')}</p>
        </div>

        {/* Company / Advertiser — selectable list with "+" in header */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs text-[#999] uppercase tracking-wider flex items-center gap-1">
              <Building2 size={10} /> {t('studio.advertiser_company')}
            </label>
            <button data-testid="add-company-btn" onClick={() => { setEditingCompanyId(null); setNewCompany({ name: '', phone: '', is_whatsapp: true, website_url: '', logo_url: '', product_description: '', profile_type: 'company' }); setShowCompanyModal(true); }}
              className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-gray-300 text-xs text-[#999] hover:text-orange-600 hover:border-orange-500/30 transition">
              <Plus size={10} />
            </button>
          </div>
          {companies.length > 0 ? (
            <div className="space-y-1.5">
              {companies.map(co => (
                <div key={co.id} data-testid={`company-${co.id}`} role="button" tabIndex={0}
                  onClick={() => setActiveCompanyId(activeCompanyId === co.id ? null : co.id)}
                  className={`w-full text-left rounded-xl border px-3 py-2 transition group cursor-pointer ${activeCompanyId === co.id ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
                  <div className="flex items-center gap-2">
                    <div className={`h-6 w-6 rounded-lg flex items-center justify-center shrink-0 overflow-hidden ${activeCompanyId === co.id ? 'bg-[#8B5CF6]/15' : 'bg-gray-100'}`}>
                      {co.logo_url ? (
                        <img src={resolveImageUrl(co.logo_url)} alt="" loading="lazy" decoding="async" className="h-full w-full object-cover" />
                      ) : (
                        <Building2 size={11} className={activeCompanyId === co.id ? 'text-orange-600' : 'text-[#999]'} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-gray-900 truncate">{co.name}</span>
                        {co.is_primary && <span className="text-[10px] text-orange-600 bg-[#8B5CF6]/10 px-1 py-0.5 rounded-full font-bold shrink-0">{t('studio.primary_label')}</span>}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {co.phone && <span className="text-[11px] text-[#999] flex items-center gap-0.5"><Phone size={7} />{co.phone}{co.is_whatsapp && <span className="text-[#25D366]">WA</span>}</span>}
                        {co.website_url && <span className="text-[11px] text-[#999] flex items-center gap-0.5 truncate max-w-[140px]"><Globe size={7} />{co.website_url.replace(/^https?:\/\//, '')}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition">
                      <button onClick={e => { e.stopPropagation(); startEditCompany(co); }} title={t('studio.edit_company')} data-testid={`edit-company-${co.id}`} className="p-1 rounded hover:bg-gray-100">
                        <PenTool size={10} className="text-[#999] hover:text-orange-600" />
                      </button>
                      {!co.is_primary && (
                        <button onClick={e => { e.stopPropagation(); setPrimaryCompany(co.id); }} title={t('studio.make_primary')} className="p-1 rounded hover:bg-gray-100">
                          <Star size={10} className="text-[#999] hover:text-orange-600" />
                        </button>
                      )}
                      <button onClick={e => { e.stopPropagation(); removeCompany(co.id); }} title={t('studio.remove')} className="p-1 rounded hover:bg-red-500/10">
                        <X size={10} className="text-[#999] hover:text-red-400" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-600 text-center py-2">{t('studio.register_company')}</p>
          )}
        </div>

        {/* Campaign Type Selector */}
        <div data-testid="campaign-type-selector">
          <label className="text-xs text-[#999] uppercase tracking-wider flex items-center gap-1 mb-2">
            <Sparkles size={10} className="text-orange-600" /> {t('studio.campaign_type') || 'Campaign Type'}
          </label>
          <div className="flex items-start gap-3 sm:gap-5">
            {/* Auto mode icons (multi-select) */}
            {[
              { id: 'image_post', label: t('studio.type_image_post') || 'Image Post', icon: '/icons/campaign-types/image-post.png' },
              { id: 'video_post', label: t('studio.type_video_post') || 'Video Post', icon: '/icons/campaign-types/video-post.png' },
              { id: 'image_avatar', label: t('studio.type_image_avatar') || 'Image + Avatar', icon: '/icons/campaign-types/image-avatar.png' },
              { id: 'video_avatar', label: t('studio.type_video_avatar') || 'Video + Avatar', icon: '/icons/campaign-types/video-avatar.png' },
              { id: 'carousel', label: t('studio.type_carousel') || 'Carousel', icon: '/icons/campaign-types/carousel.png' },
            ].map(type => {
              const active = campaignTypes.includes(type.id);
              return (
                <button key={type.id} data-testid={`campaign-type-${type.id}`}
                  onClick={() => toggleCampaignType(type.id)}
                  className="flex flex-col items-center gap-1 group cursor-pointer w-[50px]">
                  <div className={`h-10 w-10 rounded-lg overflow-hidden transition-all shrink-0 ${
                    active ? 'ring-2 ring-[#8B5CF6]' : ''
                  }`}>
                    <img src={type.icon} alt={type.label} loading="lazy" decoding="async" className="h-full w-full object-cover" />
                  </div>
                  <span className={`text-[10px] font-semibold text-center leading-tight w-full ${
                    active ? 'text-orange-600' : 'text-[#999]'
                  }`}>{type.label}</span>
                </button>
              );
            })}

            {/* Divider */}
            <div className="h-12 w-px bg-white/[0.06] mx-1 shrink-0" />

            {/* Directed Studio (exclusive) */}
            {(() => {
              const active = isDirectedMode;
              return (
                <button data-testid="campaign-type-directed_studio"
                  onClick={() => toggleCampaignType('directed_studio')}
                  className="flex flex-col items-center gap-1 group cursor-pointer w-[50px]">
                  <div className={`h-10 w-10 rounded-lg overflow-hidden transition-all shrink-0 ${
                    active ? 'ring-2 ring-[#8B5CF6]' : ''
                  }`}>
                    <img src="/icons/campaign-types/directed-video.png" alt="Directed Studio" loading="lazy" decoding="async" className="h-full w-full object-cover" />
                  </div>
                  <span className={`text-[10px] font-semibold text-center leading-tight w-full ${
                    active ? 'text-orange-600' : 'text-[#999]'
                  }`}>{t('studio.type_directed_studio') || 'Studio'}</span>
                </button>
              );
            })()}
          </div>
          {/* Mode indicator */}
          <div className="mt-2">
            <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded ${
              isDirectedMode
                ? 'text-orange-600 bg-[#8B5CF6]/[0.06]'
                : 'text-gray-600 bg-white/[0.02]'
            }`}>
              {isDirectedMode
                ? (t('studio.mode_directed') || 'Directed Studio Mode')
                : (t('studio.mode_auto') || `Auto Mode — ${campaignTypes.length} output${campaignTypes.length > 1 ? 's' : ''}`)}
            </span>
          </div>
        </div>

        {/* DIRECTED STUDIO MODE */}
        {isDirectedMode ? (
          <DirectedStudio
            avatars={avatars}
            onAddAvatar={handleAddAvatarDirected}
            onEditAvatar={handleEditAvatarDirected}
            onRemoveAvatar={handleRemoveAvatarDirected}
            onPreviewAvatar={handlePreviewAvatarDirected}
            onAiEditAvatar={handleAiEditAvatarDirected}
            aiEditAvatarId={aiEditAvatarId}
            setAiEditAvatarId={setAiEditAvatarId}
            aiEditInstruction={aiEditInstruction}
            setAiEditInstruction={setAiEditInstruction}
            aiEditLoading={aiEditLoading}
            lastCreatedAvatar={lastCreatedAvatar}
          />
        ) : (
        <>
        {/* Presenter Avatar — selectable gallery with "+" in header */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs text-[#999] uppercase tracking-wider flex items-center gap-1">
              <Sparkles size={10} className="text-orange-600" /> {t('studio.presenter_avatar')}
            </label>
            <div className="flex items-center gap-1">
              {avatars.length > 0 && (
                <button data-testid="clear-all-avatars-btn" onClick={async () => { saveAvatars([]); setSelectedAvatarId(null); try { await axios.delete(`${API}/data/avatars`); } catch {} toast.success(t('studio.avatars_cleared') || 'Avatars cleared'); }}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-[11px] text-red-400/70 hover:text-red-400 hover:bg-red-400/5 transition" title="Clear all">
                  <Trash2 size={9} />
                </button>
              )}
              <button data-testid="add-avatar-btn" onClick={() => { resetAvatarModal(); setShowAvatarModal(true); }}
                className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-gray-300 text-xs text-[#999] hover:text-orange-600 hover:border-orange-500/30 transition">
                <Plus size={10} />
              </button>
            </div>
          </div>
          {avatars.length > 0 ? (
            <div className="flex gap-2 flex-wrap">
              {avatars.map(av => (
                <div key={av.id} data-testid={`avatar-${av.id}`}
                  className={`relative rounded-xl overflow-hidden border-2 transition cursor-pointer ${selectedAvatarId === av.id ? 'border-orange-500 shadow-[0_0_10px_rgba(201,168,76,0.2)]' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
                  <img src={resolveImageUrl(av.url)} alt={av.name} loading="lazy" decoding="async" className="h-24 w-16 object-cover"
                    onClick={() => setSelectedAvatarId(av.id)} />
                  {selectedAvatarId === av.id && (
                    <div className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-[#8B5CF6] flex items-center justify-center">
                      <Check size={8} className="text-black" />
                    </div>
                  )}
                  {av.voice && (
                    <div className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full flex items-center justify-center ${av.voice.type === 'elevenlabs' ? 'bg-[#8B5CF6]/90' : 'bg-white/70'}`}>
                      {av.voice.type === 'elevenlabs' ? <Crown size={7} className="text-black" /> : <Volume2 size={7} className="text-orange-600" />}
                    </div>
                  )}
                  {/* Always visible action bar */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-1 py-0.5 flex items-center justify-between">
                    <button data-testid={`delete-avatar-${av.id}`} onClick={e => { e.stopPropagation(); removeAvatar(av.id); }}
                      className="h-5 w-5 rounded flex items-center justify-center text-red-400/70 hover:text-red-400 transition">
                      <X size={9} />
                    </button>
                    <div className="flex items-center gap-0.5">
                      <button data-testid={`ai-edit-avatar-${av.id}`} onClick={e => { e.stopPropagation(); setAiEditAvatarId(aiEditAvatarId === av.id ? null : av.id); setAiEditInstruction(''); }}
                        className="h-5 w-5 rounded flex items-center justify-center text-purple-400 hover:text-purple-300 transition" title="Editar com IA">
                        <Sparkles size={9} />
                      </button>
                      <button data-testid={`edit-avatar-${av.id}`} onClick={e => { e.stopPropagation(); openAvatarForEdit(av); }}
                        className="h-5 w-5 rounded flex items-center justify-center text-orange-600 hover:text-[#D4B85C] transition" title="Editar">
                        <PenTool size={9} />
                      </button>
                    </div>
                  </div>
                  {av.creation_mode && av.creation_mode !== 'photo' && (
                    <div className="absolute top-0.5 left-0.5 rounded-md bg-white/70 px-1 py-0.5">
                      <span className="text-xs text-orange-600 font-bold uppercase">{av.creation_mode === '3d' ? '3D' : 'AI'}</span>
                    </div>
                  )}
                  {/* AI Edit popover */}
                  {aiEditAvatarId === av.id && (
                    <div className="absolute inset-0 bg-white/90 flex flex-col items-center justify-center p-1.5 z-10" onClick={e => e.stopPropagation()}>
                      <Sparkles size={12} className="text-purple-400 mb-1" />
                      <textarea data-testid={`ai-edit-input-${av.id}`}
                        value={aiEditInstruction} onChange={e => setAiEditInstruction(e.target.value)}
                        placeholder="Ex: mudar roupa para terno azul, adicionar oculos..."
                        className="w-full text-[11px] bg-gray-100 border border-[#333] rounded-lg p-1.5 text-gray-900 placeholder-[#666] resize-none outline-none focus:border-purple-500/40"
                        rows={2} />
                      <div className="flex gap-1 mt-1 w-full">
                        <button onClick={() => { setAiEditAvatarId(null); setAiEditInstruction(''); }}
                          className="flex-1 text-[10px] py-1 rounded-lg border border-[#333] text-gray-600 hover:text-gray-900 transition">
                          {t('studio.cancel') || 'Cancelar'}
                        </button>
                        <button data-testid={`ai-edit-confirm-${av.id}`} onClick={() => aiEditAvatar(av.id)} disabled={aiEditLoading || !aiEditInstruction.trim()}
                          className="flex-1 text-[10px] py-1 rounded-lg bg-purple-600 text-gray-900 font-bold hover:bg-purple-500 transition disabled:opacity-40 flex items-center justify-center gap-1">
                          {aiEditLoading ? <RefreshCw size={8} className="animate-spin" /> : <Sparkles size={8} />}
                          {aiEditLoading ? '' : 'Editar'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-600 text-center py-2">{t('studio.no_avatar_yet')}</p>
          )}
        </div>

        {/* Campaign Name */}
        <div>
          <label className="text-xs text-[#999] uppercase tracking-wider block mb-1">{t('studio.campaign_name')}</label>
          <input data-testid="pipeline-campaign-name" value={campaignName} onChange={e => setCampaignName(e.target.value)}
            placeholder={t('studio.campaign_name_placeholder')}
            className="w-full rounded-xl border border-[#1E1E1E] bg-gray-50 px-3 py-2.5 text-xs text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
        </div>

        {/* Briefing */}
        <div>
          <label className="text-xs text-[#999] uppercase tracking-wider block mb-2">{t('studio.briefing_label')}</label>
          <div className="flex gap-1 mb-3 p-0.5 bg-gray-50 rounded-lg border border-gray-200 w-fit">
            <button data-testid="briefing-mode-free" onClick={() => setBriefingMode('free')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition ${briefingMode === 'free' ? 'bg-[#8B5CF6]/15 text-orange-600 border border-orange-500/30' : 'text-[#999] hover:text-gray-900'}`}>
              <FileText size={10} className="inline mr-1" />{t('studio.briefing_free')}
            </button>
            <button data-testid="briefing-mode-guided" onClick={() => setBriefingMode('guided')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition ${briefingMode === 'guided' ? 'bg-[#8B5CF6]/15 text-orange-600 border border-orange-500/30' : 'text-[#999] hover:text-gray-900'}`}>
              <CheckCircle size={10} className="inline mr-1" />{t('studio.briefing_guided')}
            </button>
          </div>

          {briefingMode === 'free' ? (
            <div>
              <textarea data-testid="pipeline-briefing" value={briefing} onChange={e => setBriefing(e.target.value)} rows={4}
                placeholder={t('studio.briefing_placeholder')}
                className="w-full rounded-xl border border-[#1E1E1E] bg-gray-50 px-3 py-2.5 text-xs text-gray-900 placeholder-[#666] outline-none resize-none focus:border-orange-500/30 transition" />
              {savedBriefings.length > 0 && (
                <div className="mt-2">
                  <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1.5">{t('studio.previous_briefings') || 'Previous Briefings'}</p>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {savedBriefings.map((sb, i) => (
                      <button key={i} onClick={() => {
                        setBriefing(sb.briefing);
                        if (sb.campaign_name && !campaignName) setCampaignName(sb.campaign_name);
                        if (sb.campaign_language) setCampaignLang(sb.campaign_language);
                        if (sb.platforms?.length) setPlatforms(sb.platforms);
                        toast.success(t('studio.briefing_loaded') || 'Briefing loaded!');
                      }}
                        className="w-full text-left rounded-lg border border-[#1E1E1E] bg-white px-3 py-2 hover:border-orange-500/30 transition group">
                        <div className="flex items-center gap-2 mb-0.5">
                          {sb.campaign_name && <span className="text-[10px] font-semibold text-gray-900">{sb.campaign_name}</span>}
                          {sb.campaign_language && <span className="text-[11px] text-orange-600 uppercase">{sb.campaign_language}</span>}
                          <span className="text-[10px] text-[#777] ml-auto group-hover:text-orange-600">{t('studio.use') || 'Use'}</span>
                        </div>
                        <p className="text-xs text-[#999] line-clamp-2">{sb.briefing}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3 bg-gray-50 rounded-xl border border-gray-200 p-3">
              <p className="text-xs text-orange-600 font-medium mb-1">{t('studio.guided_intro')}</p>

              <div>
                <label className="text-xs text-[#999] block mb-1">1. {t('studio.q_product')}</label>
                <input data-testid="q-product" value={questionnaire.product} onChange={e => setQuestionnaire(p => ({...p, product: e.target.value}))}
                  placeholder={t('studio.q_product_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-2 text-[11px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">2. {t('studio.q_goal')}</label>
                <div className="flex flex-wrap gap-1.5 mb-1.5">
                  {[{k:'goal_leads'},{k:'goal_sales'},{k:'goal_awareness'},{k:'goal_engagement'},{k:'goal_launch'},{k:'goal_promo'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, goal: p.goal === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.goal === t(`studio.${k}`) ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
                <input value={questionnaire.goal} onChange={e => setQuestionnaire(p => ({...p, goal: e.target.value}))}
                  placeholder={t('studio.q_goal_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-1.5 text-[10px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">3. {t('studio.q_audience')}</label>

                {/* Gender */}
                <p className="text-[11px] text-[#999] mb-1 mt-1">{t('studio.q_gender') || 'Gender'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['All', 'Male', 'Female', 'LGBTQ+', 'Non-binary'].map(g => (
                    <button key={g} onClick={() => setQuestionnaire(p => ({...p, gender: p.gender === g ? '' : g}))}
                      className={`rounded-md px-2 py-0.5 text-xs border transition ${questionnaire.gender === g ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {g}
                    </button>
                  ))}
                </div>

                {/* Age Range */}
                <p className="text-[11px] text-[#999] mb-1">{t('studio.q_age_range') || 'Age range'}</p>
                <div className="flex items-center gap-1.5 mb-2">
                  <input data-testid="q-age-min" value={questionnaire.ageMin} onChange={e => setQuestionnaire(p => ({...p, ageMin: e.target.value}))}
                    placeholder="18" type="number" min="13" max="99"
                    className="w-16 rounded-md border border-[#1E1E1E] bg-gray-50 px-2 py-1 text-[10px] text-gray-900 text-center placeholder-[#666] outline-none focus:border-orange-500/30" />
                  <span className="text-xs text-gray-600">—</span>
                  <input data-testid="q-age-max" value={questionnaire.ageMax} onChange={e => setQuestionnaire(p => ({...p, ageMax: e.target.value}))}
                    placeholder="65+" type="text"
                    className="w-16 rounded-md border border-[#1E1E1E] bg-gray-50 px-2 py-1 text-[10px] text-gray-900 text-center placeholder-[#666] outline-none focus:border-orange-500/30" />
                  <div className="flex gap-1 ml-2">
                    {['13-17', '18-24', '25-34', '35-44', '45-54', '55+'].map(r => (
                      <button key={r} onClick={() => { const [min, max] = r.split('-'); setQuestionnaire(p => ({...p, ageMin: min, ageMax: max || '65+'})); }}
                        className={`rounded-md px-1.5 py-0.5 text-[11px] border transition ${questionnaire.ageMin === r.split('-')[0] ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Social Class */}
                <p className="text-[11px] text-[#999] mb-1">{t('studio.q_social_class') || 'Social class'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['A (Luxury)', 'B (Upper-middle)', 'C (Middle)', 'D (Lower-middle)', 'E (Low income)', 'All classes'].map(c => (
                    <button key={c} onClick={() => setQuestionnaire(p => ({...p, socialClass: p.socialClass === c ? '' : c}))}
                      className={`rounded-md px-2 py-0.5 text-xs border transition ${questionnaire.socialClass === c ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {c}
                    </button>
                  ))}
                </div>

                {/* Lifestyle / Interests */}
                <p className="text-[11px] text-[#999] mb-1">{t('studio.q_lifestyle') || 'Lifestyle & Interests'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['Fitness', 'Tech', 'Fashion', 'Gaming', 'Travel', 'Food', 'Music', 'Sports', 'Business', 'Eco-friendly', 'Luxury', 'Family'].map(l => (
                    <button key={l} onClick={() => setQuestionnaire(p => ({...p, lifestyle: p.lifestyle?.includes(l) ? p.lifestyle.replace(l, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '') : (p.lifestyle ? `${p.lifestyle}, ${l}` : l)}))}
                      className={`rounded-md px-2 py-0.5 text-xs border transition ${questionnaire.lifestyle?.includes(l) ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {l}
                    </button>
                  ))}
                </div>

                {/* Free-text audience */}
                <input data-testid="q-audience" value={questionnaire.audience} onChange={e => setQuestionnaire(p => ({...p, audience: e.target.value}))}
                  placeholder={t('studio.q_audience_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-1.5 text-[10px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">4. {t('studio.q_tone')}</label>
                <div className="flex flex-wrap gap-1.5">
                  {[{k:'tone_professional'},{k:'tone_casual'},{k:'tone_urgent'},{k:'tone_inspiring'},{k:'tone_fun'},{k:'tone_sophisticated'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, tone: p.tone === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.tone === t(`studio.${k}`) ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">5. {t('studio.q_offer')}</label>
                <input data-testid="q-offer" value={questionnaire.offer} onChange={e => setQuestionnaire(p => ({...p, offer: e.target.value}))}
                  placeholder={t('studio.q_offer_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-2 text-[11px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">6. {t('studio.q_differentials')}</label>
                <input data-testid="q-differentials" value={questionnaire.differentials} onChange={e => setQuestionnaire(p => ({...p, differentials: e.target.value}))}
                  placeholder={t('studio.q_differentials_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-2 text-[11px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">7. {t('studio.q_pain_points') || 'What problems does your audience face?'}</label>
                <input data-testid="q-pain-points" value={questionnaire.painPoints} onChange={e => setQuestionnaire(p => ({...p, painPoints: e.target.value}))}
                  placeholder={t('studio.q_pain_points_placeholder') || 'E.g.: High costs, lack of time, complexity...'}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-2 text-[11px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">8. {t('studio.q_visual_style') || 'Visual style preference'}</label>
                <div className="flex flex-wrap gap-1">
                  {['Minimalist', 'Bold & Vibrant', 'Luxury & Elegant', 'Natural & Organic', 'Tech & Modern', 'Retro & Vintage', 'Dark & Moody', 'Playful & Colorful'].map(s => (
                    <button key={s} onClick={() => setQuestionnaire(p => ({...p, visualStyle: p.visualStyle === s ? '' : s}))}
                      className={`rounded-md px-2 py-0.5 text-xs border transition ${questionnaire.visualStyle === s ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">9. {t('studio.q_cta')}</label>
                <div className="flex flex-wrap gap-1.5">
                  {[{k:'cta_signup'},{k:'cta_demo'},{k:'cta_buy'},{k:'cta_learn'},{k:'cta_download'},{k:'cta_whatsapp'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, cta: p.cta === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.cta === t(`studio.${k}`) ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs text-[#999] block mb-1">10. {t('studio.q_urgency')}</label>
                <input data-testid="q-urgency" value={questionnaire.urgency} onChange={e => setQuestionnaire(p => ({...p, urgency: e.target.value}))}
                  placeholder={t('studio.q_urgency_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-2 text-[11px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition" />
              </div>

              {compileBriefing().trim() && (
                <div className="mt-2 p-2.5 rounded-lg bg-gray-50 border border-gray-200">
                  <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1">{t('studio.briefing_preview')}</p>
                  <pre className="text-[10px] text-[#999] whitespace-pre-wrap font-sans leading-relaxed">{compileBriefing()}</pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Campaign Language */}
        <div>
          <label className="text-xs text-[#999] uppercase tracking-wider block mb-1">{t('studio.campaign_language')}</label>
          <p className="text-[11px] text-gray-600 mb-1.5">{t('studio.campaign_language_desc')}</p>
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
                className={`rounded-lg px-3 py-1.5 text-[10px] font-medium border transition flex items-center gap-1.5 ${campaignLang === lang.code ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                <span className="text-sm">{lang.flag}</span> {lang.label}
              </button>
            ))}
            <input value={campaignLang && !['', 'pt', 'en', 'es', 'fr', 'ht'].includes(campaignLang) ? campaignLang : ''}
              onChange={e => setCampaignLang(e.target.value)}
              placeholder="Other language..."
              className="rounded-lg border border-[#1E1E1E] bg-gray-50 px-3 py-1.5 text-[10px] text-gray-900 placeholder-[#666] outline-none focus:border-orange-500/30 transition w-32" />
          </div>
        </div>

        {/* Brand Data Toggle */}
        {activeCompany && (
          <div data-testid="brand-data-toggle">
            <button data-testid="brand-data-btn" onClick={() => setApplyBrandData(!applyBrandData)}
              className={`w-full rounded-xl border px-3 py-2.5 flex items-center gap-3 transition ${
                applyBrandData ? 'border-orange-500/30 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
              <div className={`h-4 w-4 rounded border flex items-center justify-center shrink-0 transition ${
                applyBrandData ? 'bg-[#8B5CF6] border-orange-500' : 'border-[#555]'}`}>
                {applyBrandData && <Check size={10} className="text-black" />}
              </div>
              {activeCompany.logo_url ? (
                <img src={resolveImageUrl(activeCompany.logo_url)} alt="" loading="lazy" decoding="async" className="h-8 w-8 rounded-lg object-cover border border-[#1E1E1E] shrink-0" />
              ) : (
                <div className="h-8 w-8 rounded-lg bg-gray-100 border border-[#1E1E1E] flex items-center justify-center shrink-0">
                  <Building2 size={12} className="text-[#999]" />
                </div>
              )}
              <div className="flex-1 min-w-0 text-left">
                <p className="text-xs text-gray-900 font-medium truncate">{activeCompany.name}</p>
                <p className="text-[10px] text-[#999] truncate">
                  {[activeCompany.phone, activeCompany.website_url].filter(Boolean).join(' · ') || t('studio.brand_no_extra_info')}
                </p>
              </div>
              <span className="text-[11px] text-[#999] uppercase tracking-wider shrink-0">{t('studio.apply_brand')}</span>
            </button>
            {applyBrandData && (
              <p className="text-[10px] text-orange-600/50 mt-1 px-1">{t('studio.brand_applied_hint')}</p>
            )}
          </div>
        )}

        {/* Product Images: Exact + Reference */}
        <AssetUploader assets={uploadedAssets} onAssetsChange={setUploadedAssets} />

        {/* Music Library - Compact with Genre Tabs */}
        {musicLibrary.length > 0 && (
          <div>
            <label className="text-xs text-[#999] uppercase tracking-wider block mb-1.5">{t('studio.music_library') || 'Background Music (Video)'}</label>
            {/* Genre Tabs */}
            <div className="flex gap-1 flex-wrap mb-1.5">
              {['All', ...new Set(musicLibrary.map(t => t.category || 'General'))].map(cat => (
                <button key={cat} onClick={() => setMusicGenre(cat)}
                  className={`rounded-md px-2 py-0.5 text-[11px] border transition ${musicGenre === cat ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600 font-semibold' : 'border-gray-200 text-[#999] hover:text-gray-900'}`}>
                  {cat}
                </button>
              ))}
            </div>
            {/* Scrollable Track List */}
            <div className="max-h-[160px] overflow-y-auto space-y-0.5 pr-1" style={{scrollbarWidth:'thin', scrollbarColor:'#333 transparent'}}>
              {(musicGenre === 'All' ? musicLibrary : musicLibrary.filter(t => (t.category || 'General') === musicGenre)).map(track => (
                <div key={track.id} data-testid={`music-${track.id}`}
                  onClick={() => setSelectedMusic(selectedMusic === track.id ? '' : track.id)}
                  className={`flex items-center gap-1.5 rounded-md border px-2 py-1 cursor-pointer transition ${selectedMusic === track.id ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-gray-200 hover:border-gray-300'}`}>
                  <button
                    onClick={(e) => { e.stopPropagation(); togglePlayTrack(track.id); }}
                    className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 transition ${playingTrack === track.id ? 'bg-[#8B5CF6] text-black' : 'bg-gray-100 text-gray-600 hover:text-gray-900'}`}>
                    {playingTrack === track.id ? <span className="text-[5px] font-bold">||</span> : <Play size={7} />}
                  </button>
                  <span className="text-[11px] font-medium text-gray-900 truncate flex-1">{track.name}</span>
                  <span className="text-[10px] text-gray-600 truncate max-w-[100px] hidden sm:block">{track.description}</span>
                  {selectedMusic === track.id && <Check size={9} className="text-orange-600 shrink-0" />}
                </div>
              ))}
            </div>
            {selectedMusic && (
              <p className="text-[11px] text-orange-600 flex items-center gap-1 mt-0.5">
                <Check size={8} /> {t('studio.music_selected') || 'Music selected for video'}
              </p>
            )}
            {!selectedMusic && (
              <p className="text-[11px] text-gray-600 mt-0.5">{t('studio.music_auto') || 'No selection = AI picks automatically based on campaign mood'}</p>
            )}
          </div>
        )}



        {/* Platforms */}
        <div>
          <label className="text-xs text-[#999] uppercase tracking-wider block mb-1.5">{t('studio.platforms')}</label>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.filter(p => !p.parent).map(p => (
              <button key={p.id} data-testid={`platform-${p.id}`} onClick={() => togglePlatform(p.id)}
                className={`rounded-lg px-3 py-1.5 text-[11px] font-medium border transition ${platforms.includes(p.id) ? 'border-orange-500/40 bg-[#8B5CF6]/10 text-orange-600' : 'border-[#1E1E1E] text-[#999] hover:text-gray-900'}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Video Mode */}
        <div>
          <label className="text-xs text-[#999] uppercase tracking-wider flex items-center gap-1 mb-1.5">
            <Film size={10} /> {t('studio.video_mode')}
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            <button data-testid="video-mode-none" onClick={() => { setSkipVideo(true); setVideoMode('none'); }}
              className={`rounded-xl border p-2 text-center transition ${skipVideo ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
              <X size={14} className={`mx-auto mb-1 ${skipVideo ? 'text-orange-600' : 'text-[#999]'}`} />
              <p className="text-xs font-semibold text-gray-900">{t('studio.no_video')}</p>
              <p className="text-[10px] text-[#999]">{t('studio.faster')}</p>
            </button>
            <button data-testid="video-mode-narration" onClick={() => { setSkipVideo(false); setVideoMode('narration'); }}
              className={`rounded-xl border p-2 text-center transition ${!skipVideo && videoMode === 'narration' ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
              <MessageSquare size={14} className={`mx-auto mb-1 ${!skipVideo && videoMode === 'narration' ? 'text-orange-600' : 'text-[#999]'}`} />
              <p className="text-xs font-semibold text-gray-900">{t('studio.narration')}</p>
              <p className="text-[10px] text-[#999]">{t('studio.voice_scenes')}</p>
            </button>
            <button data-testid="video-mode-presenter" onClick={() => { setSkipVideo(false); setVideoMode('presenter'); }}
              className={`rounded-xl border p-2 text-center transition ${!skipVideo && videoMode === 'presenter' ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
              <Eye size={14} className={`mx-auto mb-1 ${!skipVideo && videoMode === 'presenter' ? 'text-orange-600' : 'text-[#999]'}`} />
              <p className="text-xs font-semibold text-gray-900">{t('studio.presenter')}</p>
              <p className="text-[10px] text-[#999]">{t('studio.talking_avatar')}</p>
            </button>
          </div>
          {!skipVideo && videoMode === 'presenter' && !selectedAvatar && (
            <p className="text-[11px] text-amber-400/80 mt-1.5 flex items-center gap-1">
              <AlertTriangle size={9} /> {t('studio.presenter_warning')}
            </p>
          )}
        </div>

        {/* Mode */}
        <div>
          <label className="text-xs text-[#999] uppercase tracking-wider block mb-1.5">{t('studio.execution_mode')}</label>
          <div className="grid grid-cols-2 gap-2">
            <button data-testid="mode-semi-auto" onClick={() => setMode('semi_auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'semi_auto' ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
              <p className="text-xs font-semibold text-gray-900 mb-0.5">{t('studio.mode_semi')}</p>
              <p className="text-xs text-[#999]">{t('studio.mode_semi_desc')}</p>
            </button>
            <button data-testid="mode-auto" onClick={() => setMode('auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'auto' ? 'border-orange-500/40 bg-[#8B5CF6]/5' : 'border-[#1E1E1E] hover:border-gray-300'}`}>
              <p className="text-xs font-semibold text-gray-900 mb-0.5">{t('studio.mode_auto')}</p>
              <p className="text-xs text-[#999]">{t('studio.mode_auto_desc')}</p>
            </button>
          </div>
        </div>

        {/* Previous Pipelines */}
        {pipelines.length > 0 && (
          <div>
            <button onClick={() => setShowHistory(!showHistory)} data-testid="toggle-history"
              className="text-xs text-orange-600 hover:underline flex items-center gap-1">
              {showHistory ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
              {pipelines.length} {t('studio.previous_pipelines')}
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
        </>
        )}
      </div>

      {/* Start Button — only in auto mode */}
      {!isDirectedMode && (
      <div className="px-4 py-3 border-t border-gray-200">
        <button data-testid="start-pipeline-btn" onClick={createPipeline}
          disabled={creating || !campaignName.trim() || !(briefingMode === 'guided' ? compileBriefing().trim() : briefing.trim()) || platforms.length === 0}
          className="w-full rounded-xl bg-gradient-to-r from-[#8B5CF6] to-[#D4B85A] py-3 text-[13px] font-bold text-black transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(201,168,76,0.15)]">
          {creating ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
          {creating ? t('studio.starting') : `${mode === 'auto' ? t('studio.start_pipeline_auto') : t('studio.start_pipeline_semi')}`}
        </button>
      </div>
      )}

        {/* Avatar Zoom Preview */}
        {avatarPreviewUrl && (
          <div className="fixed inset-0 z-[80] bg-white/95 flex items-center justify-center p-4" onClick={() => setAvatarPreviewUrl(null)}>
            <div className="relative max-w-3xl w-full max-h-[90vh] flex items-center justify-center" onClick={e => e.stopPropagation()}>
              <img src={resolveImageUrl(avatarPreviewUrl)} alt="Avatar Preview" loading="lazy" decoding="async" className="max-w-full max-h-[85vh] rounded-2xl border border-orange-500/20 shadow-2xl object-contain" />
              <button onClick={() => setAvatarPreviewUrl(null)}
                className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-white border border-[#333] flex items-center justify-center hover:bg-gray-100 transition">
                <X size={14} className="text-gray-900" />
              </button>
              <div className="absolute bottom-3 right-3 flex gap-2">
                <button data-testid="download-avatar-btn" onClick={async () => {
                    try {
                      const response = await fetch(resolveImageUrl(avatarPreviewUrl));
                      const blob = await response.blob();
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `avatar_${Date.now()}.png`;
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(url);
                    } catch { toast.error('Download failed'); }
                  }}
                  className="h-8 w-8 rounded-lg bg-white/70 border border-white/15 flex items-center justify-center hover:bg-white transition">
                  <Download size={14} className="text-gray-900" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Company Modal */}
        {showCompanyModal && (
          <CompanyModal
            editingCompanyId={editingCompanyId} newCompany={newCompany}
            setNewCompany={setNewCompany} logoUploading={logoUploading}
            cancelCompanyForm={cancelCompanyForm} addCompany={addCompany}
            saveEditCompany={saveEditCompany} uploadCompanyLogo={uploadCompanyLogo}
            logoInputRef={logoInputRef}
          />
        )}

        {/* Avatar Creation / Customization Modal */}
        <AvatarModal ctx={{
          showAvatarModal, avatarStage, avatarCreationMode, avatarSourceType,
          avatarSourcePhoto, avatarVideoUploading, avatarExtractedAudio,
          avatarVideoFrames, masteringVoice, generatingPreviewVideo, previewVideoUrl,
          previewLanguage, avatarName, avatarMediaTab, accuracyProgress,
          generatingAvatar, avatarPhotoUploading, avatarPromptText,
          avatarPromptGender, avatarPromptStyle, aiEditAvatarId, aiEditInstruction,
          aiEditLoading, tempAvatar, clothingVariants, customizeTab, voiceTab,
          angleImages, generatingAngle, auto360Progress, editingAvatarId,
          avatarEditHistory, avatarBaseUrl, applyingClothing, isRecording,
          recordedAudioUrl, recordedAudioBlob, uploadingRecording, loadingVoicePreview,
          playingVoiceId, elevenLabsVoices, elevenLabsAvailable, avatarPreviewUrl, avatars,
          setAvatarCreationMode, setAvatarSourceType, setAvatarSourcePhoto,
          setAvatarExtractedAudio, setAvatarVideoFrames, setAvatarName,
          setAvatarMediaTab, setAvatarPromptText, setAvatarPromptGender,
          setAvatarPromptStyle, setAiEditAvatarId, setAiEditInstruction, setAiEditLoading,
          setTempAvatar, setCustomizeTab, setVoiceTab, setAngleImages,
          setPreviewLanguage, setAvatarPreviewUrl, setAvatarEditHistory,
          setPreviewVideoUrl, setGeneratingPreviewVideo,
          resetAvatarModal, generateAvatarFromPhoto, generateAvatarFromPrompt,
          uploadAvatarPhoto, uploadAvatarVideo, applyClothing, generateAngle,
          startAuto360, saveAvatarAndClose, saveAvatarAsNew, previewVoice,
          startRecording, stopRecording, saveRecordingAsVoice, persistAvatarToServer,
          avatarInputRef,
          isDirectedMode,
        }} />

    </div>
  );
}
