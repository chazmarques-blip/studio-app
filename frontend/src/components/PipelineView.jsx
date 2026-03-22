import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PenTool, Palette, CheckCircle, CalendarClock, Loader2, Check, ChevronDown, ChevronUp, ArrowRight, Zap, RotateCcw, Trash2, RefreshCw, AlertTriangle, Crown, Lock, Upload, X, Image, Phone, Globe, Mail, MapPin, FileText, Download, Eye, Clock, Maximize2, MessageSquare, Send, Award, Film, Play, Building2, Plus, Star, Sparkles, Mic, MicOff, Volume2, Shirt, RotateCw, Square, Camera, Bot, ScanEye, ShieldCheck, Briefcase, User, History } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import FinalPreview from './FinalPreview';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import {
  cleanDisplayText, STEP_META, STEP_ORDER, PLATFORMS,
  ProgressTimer, ImageLightbox, StepCard,
  CopyApproval, DesignApproval, VideoApproval,
  CompletedSummary, HistoryCard, AssetUploader,
} from './pipeline';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;


/* ── Main PipelineView ── */
export default function PipelineView({ context }) {
  const navigate = useNavigate();
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
        localStorage.setItem('agentzz_companies', JSON.stringify(serverCompanies));
        localStorage.setItem('agentzz_avatars', JSON.stringify(serverAvatars));
        if (serverCompanies.length) {
          // Don't auto-select - let user choose or create generic campaign
        }
        if (serverAvatars.length) {
          setSelectedAvatarId(serverAvatars[0].id);
        }
      } catch {
        // Fallback to localStorage ONLY if API fails (e.g. not authenticated)
        try { const p = JSON.parse(localStorage.getItem('agentzz_companies') || '[]'); setCompanies(p); } catch {}
        try { const p = JSON.parse(localStorage.getItem('agentzz_avatars') || '[]'); setAvatars(p); if (p.length) setSelectedAvatarId(p[0].id); } catch {}
      }
    };
    loadUserData();
  }, []);

  const saveCompanies = (list) => {
    setCompanies(list);
    localStorage.setItem('agentzz_companies', JSON.stringify(list));
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
      toast.error(e.response?.data?.detail || 'Upload error');
    }
    setLogoUploading(false);
  };

  const setPrimaryCompany = async (id) => {
    const updated = companies.map(c => ({ ...c, is_primary: c.id === id }));
    setCompanies(updated);
    try { await axios.post(`${API}/data/companies/primary/${id}`); } catch {}
  };

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
    localStorage.setItem('agentzz_avatars', JSON.stringify(list));
  };

  const persistAvatarToServer = async (avatar) => {
    try {
      const { data } = await axios.post(`${API}/data/avatars`, avatar);
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
      toast.error(e.response?.data?.detail || t('studio.err_generic'));
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
      toast.error(e.response?.data?.detail || t('studio.err_generic'));
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
      toast.error(e.response?.data?.detail || t('studio.err_generic'));
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
      toast.error(e.response?.data?.detail || t('studio.err_generic'));
      setAccuracyProgress(null);
      setGeneratingAvatar(false);
    }
  };

  const saveAvatarAndClose = () => {
    if (!tempAvatar) return;
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
      };
      const updated = avatars.map(a => a.id === editingAvatarId ? { ...a, ...editedAvatar } : a);
      saveAvatars(updated);
      persistAvatarToServer(editedAvatar);
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
      };
      const updated = [...avatars, newAv];
      saveAvatars(updated);
      setSelectedAvatarId(newAv.id);
      persistAvatarToServer(newAv);
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
    };
    const updated = [...avatars, newAv];
    saveAvatars(updated);
    setSelectedAvatarId(newAv.id);
    persistAvatarToServer(newAv);
    resetAvatarModal();
    toast.success('Avatar saved as new!');
  };

  const openAvatarForEdit = (av) => {
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
    // Initialize edit history with current avatar as base
    setAvatarBaseUrl(av.url);
    setAvatarEditHistory([{ url: av.url, instruction: 'Base original', timestamp: new Date().toISOString(), isBase: true }]);
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
        try { await axios.post(`${API}/data/avatars`, { ...av, url: data.url }); } catch {}
        toast.success(t('studio.avatar_edited') || 'Avatar editado com IA!');
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Erro ao editar avatar');
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
      toast.error(e.response?.data?.detail || 'Error');
    }
    setApplyingClothing(false);
  };

  const generateAngle = async (angle, forceRegenerate = false) => {
    if (!tempAvatar || (angleImages[angle] && !forceRegenerate)) return;
    setGeneratingAngle(angle);
    const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
    const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
    try {
      const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-variant`, {
        source_image_url: sourceUrl,
        clothing: tempAvatar.clothing || 'company_uniform',
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
      });
      setActivePipeline(data);
      setBriefing(''); setCampaignName(''); setExpandedSteps({}); setUploadedAssets([]);
      setQuestionnaire({ product: '', goal: '', audience: '', tone: '', offer: '', differentials: '', cta: '', urgency: '' });
      setCampaignLang('');
      toast.success(t('studio.pipeline_started') || 'Pipeline started!');
    } catch (e) { toast.error(e.response?.data?.detail || t('studio.err_create') || 'Error creating pipeline'); }
    setCreating(false);
  };

  const approveStep = async (approvalData) => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/approve`, approvalData);
      toast.success(t('studio.approved') || 'Approved! Next step starting...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || t('studio.err_approve') || 'Error approving'); }
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
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); }
  };

  const retryPipeline = async () => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/retry`);
      toast.success(t('studio.retrying') || 'Retrying...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || t('studio.err_generic') || 'Error'); }
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
  if (activePipeline && showFinalPreview) {
    return (
      <FinalPreview
        pipeline={activePipeline}
        campaignLang={campaignLang}
        onClose={() => setShowFinalPreview(false)}
        onPublish={async (editedCopy) => {
          try {
            await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/publish`, {
              edited_copy: editedCopy || null
            });
            toast.success(t('studio.published') || 'Campaign published successfully!');
            navigate('/marketing');
          } catch (e) {
            toast.error(e.response?.data?.detail || t('studio.err_publish') || 'Error publishing campaign');
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
      running: { label: t('studio.status_running') || 'Running', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
      waiting_approval: { label: t('studio.status_waiting') || 'Waiting Approval', color: 'text-amber-400', bg: 'bg-amber-400' },
      waiting_audio_approval: { label: t('studio.audio_preapproval') || 'Audio Pre-Approval', color: 'text-purple-400', bg: 'bg-purple-400' },
      completed: { label: t('studio.status_completed') || 'Completed!', color: 'text-green-400', bg: 'bg-green-400' },
      failed: { label: t('studio.status_failed') || 'Failed', color: 'text-red-400', bg: 'bg-red-400' },
      pending: { label: t('studio.status_pending') || 'Starting...', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
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
                <span key={p} className="text-[8px] text-[#999] bg-[#111] px-1.5 py-0.5 rounded capitalize">{p}</span>
              ))}
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold text-white">{progressPct}%</span>
            <span className="text-[8px] text-[#999] ml-1">completo</span>
          </div>
          <button onClick={() => archivePipeline(activePipeline.id)} className="text-[#888] hover:text-red-400 p-1.5 rounded-lg hover:bg-[#111] transition" title={t('studio.archive') || 'Archive and create new'}>
            <X size={14} />
          </button>
        </div>

        {/* Briefing */}
        <div className="px-3 py-2 bg-[#080808] border-b border-[#111]">
          <p className="text-[8px] text-[#999] uppercase tracking-wider mb-0.5">Briefing</p>
          <p className="text-[10px] text-[#999] line-clamp-2">{activePipeline.briefing}</p>
          {/* Show uploaded assets info if present */}
          {activePipeline.result?.uploaded_assets?.length > 0 && (
            <div className="flex items-center gap-1.5 mt-1">
              <Image size={9} className="text-[#888]" />
              <span className="text-[8px] text-[#888]">{activePipeline.result.uploaded_assets.length} arquivo(s) anexado(s)</span>
            </div>
          )}
          {activePipeline.result?.contact_info && Object.values(activePipeline.result.contact_info).some(v => v) && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <Phone size={9} className="text-[#888]" />
              <span className="text-[8px] text-[#888]">{t('studio.contact_included') || 'Contact data included'}</span>
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
                  {i < STEP_ORDER.length - 1 && <ArrowRight size={8} className="text-[#777] shrink-0" />}
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
              pipelineStatus={activePipeline.status} onApprove={approveStep} onApproveAudio={approveAudio}
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
              <p className="text-xs font-semibold text-red-400 flex-1">A step has failed. Try again.</p>
              <button onClick={retryPipeline}
                className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition flex items-center gap-1.5">
                <RefreshCw size={12} /> Retry
              </button>
            </div>
          </div>
        )}
        {activePipeline.status === 'requires_upgrade' && (
          <div className="px-3 py-3 border-t border-[#111] bg-[#C9A84C]/5">
            <div className="flex items-center gap-2">
              <Crown size={18} className="text-[#C9A84C]" />
              <div className="flex-1">
                <p className="text-xs font-bold text-[#C9A84C]">Upgrade to Enterprise</p>
                <p className="text-[9px] text-[#888]">Your campaign is ready! Upgrade to publish.</p>
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
          <p className="text-[9px] text-[#999] mt-1.5">{STEP_ORDER.map(s => STEP_META[s].agent).join(' \u2192 ')}</p>
        </div>

        {/* Company / Advertiser — selectable list with "+" in header */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-[9px] text-[#999] uppercase tracking-wider flex items-center gap-1">
              <Building2 size={10} /> {t('studio.advertiser_company')}
            </label>
            <button data-testid="add-company-btn" onClick={() => { setEditingCompanyId(null); setNewCompany({ name: '', phone: '', is_whatsapp: true, website_url: '', logo_url: '', product_description: '', profile_type: 'company' }); setShowCompanyModal(true); }}
              className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-[#2A2A2A] text-[9px] text-[#999] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
              <Plus size={10} />
            </button>
          </div>
          {companies.length > 0 ? (
            <div className="space-y-1.5">
              {companies.map(co => (
                <div key={co.id} data-testid={`company-${co.id}`} role="button" tabIndex={0}
                  onClick={() => setActiveCompanyId(activeCompanyId === co.id ? null : co.id)}
                  className={`w-full text-left rounded-xl border px-3 py-2 transition group cursor-pointer ${activeCompanyId === co.id ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
                  <div className="flex items-center gap-2">
                    <div className={`h-6 w-6 rounded-lg flex items-center justify-center shrink-0 overflow-hidden ${activeCompanyId === co.id ? 'bg-[#C9A84C]/15' : 'bg-[#1A1A1A]'}`}>
                      {co.logo_url ? (
                        <img src={resolveImageUrl(co.logo_url)} alt="" className="h-full w-full object-cover" />
                      ) : (
                        <Building2 size={11} className={activeCompanyId === co.id ? 'text-[#C9A84C]' : 'text-[#999]'} />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] font-semibold text-white truncate">{co.name}</span>
                        {co.is_primary && <span className="text-[7px] text-[#C9A84C] bg-[#C9A84C]/10 px-1 py-0.5 rounded-full font-bold shrink-0">{t('studio.primary_label')}</span>}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {co.phone && <span className="text-[8px] text-[#999] flex items-center gap-0.5"><Phone size={7} />{co.phone}{co.is_whatsapp && <span className="text-[#25D366]">WA</span>}</span>}
                        {co.website_url && <span className="text-[8px] text-[#999] flex items-center gap-0.5 truncate max-w-[140px]"><Globe size={7} />{co.website_url.replace(/^https?:\/\//, '')}</span>}
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition">
                      <button onClick={e => { e.stopPropagation(); startEditCompany(co); }} title={t('studio.edit_company')} data-testid={`edit-company-${co.id}`} className="p-1 rounded hover:bg-[#1A1A1A]">
                        <PenTool size={10} className="text-[#999] hover:text-[#C9A84C]" />
                      </button>
                      {!co.is_primary && (
                        <button onClick={e => { e.stopPropagation(); setPrimaryCompany(co.id); }} title={t('studio.make_primary')} className="p-1 rounded hover:bg-[#1A1A1A]">
                          <Star size={10} className="text-[#999] hover:text-[#C9A84C]" />
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
            <p className="text-[9px] text-[#888] text-center py-2">{t('studio.register_company')}</p>
          )}
        </div>

        {/* Presenter Avatar — selectable gallery with "+" in header */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-[9px] text-[#999] uppercase tracking-wider flex items-center gap-1">
              <Sparkles size={10} className="text-[#C9A84C]" /> {t('studio.presenter_avatar')}
            </label>
            <div className="flex items-center gap-1">
              {avatars.length > 0 && (
                <button data-testid="clear-all-avatars-btn" onClick={async () => { saveAvatars([]); setSelectedAvatarId(null); try { await axios.delete(`${API}/data/avatars`); } catch {} toast.success(t('studio.avatars_cleared') || 'Avatars cleared'); }}
                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-[8px] text-red-400/70 hover:text-red-400 hover:bg-red-400/5 transition" title="Clear all">
                  <Trash2 size={9} />
                </button>
              )}
              <button data-testid="add-avatar-btn" onClick={() => { resetAvatarModal(); setShowAvatarModal(true); }}
                className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-[#2A2A2A] text-[9px] text-[#999] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
                <Plus size={10} />
              </button>
            </div>
          </div>
          {avatars.length > 0 ? (
            <div className="flex gap-2 flex-wrap">
              {avatars.map(av => (
                <div key={av.id} data-testid={`avatar-${av.id}`}
                  className={`relative rounded-xl overflow-hidden border-2 transition cursor-pointer ${selectedAvatarId === av.id ? 'border-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.2)]' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
                  <img src={resolveImageUrl(av.url)} alt={av.name} className="h-24 w-16 object-cover"
                    onClick={() => setSelectedAvatarId(av.id)} />
                  {selectedAvatarId === av.id && (
                    <div className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center">
                      <Check size={8} className="text-black" />
                    </div>
                  )}
                  {av.voice && (
                    <div className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full flex items-center justify-center ${av.voice.type === 'elevenlabs' ? 'bg-[#C9A84C]/90' : 'bg-black/70'}`}>
                      {av.voice.type === 'elevenlabs' ? <Crown size={7} className="text-black" /> : <Volume2 size={7} className="text-[#C9A84C]" />}
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
                        className="h-5 w-5 rounded flex items-center justify-center text-[#C9A84C] hover:text-[#D4B85C] transition" title="Editar">
                        <PenTool size={9} />
                      </button>
                    </div>
                  </div>
                  {av.creation_mode && av.creation_mode !== 'photo' && (
                    <div className="absolute top-0.5 left-0.5 rounded-md bg-black/70 px-1 py-0.5">
                      <span className="text-[6px] text-[#C9A84C] font-bold uppercase">{av.creation_mode === '3d' ? '3D' : 'AI'}</span>
                    </div>
                  )}
                  {/* AI Edit popover */}
                  {aiEditAvatarId === av.id && (
                    <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-1.5 z-10" onClick={e => e.stopPropagation()}>
                      <Sparkles size={12} className="text-purple-400 mb-1" />
                      <textarea data-testid={`ai-edit-input-${av.id}`}
                        value={aiEditInstruction} onChange={e => setAiEditInstruction(e.target.value)}
                        placeholder="Ex: mudar roupa para terno azul, adicionar oculos..."
                        className="w-full text-[8px] bg-[#1A1A1A] border border-[#333] rounded-lg p-1.5 text-white placeholder-[#666] resize-none outline-none focus:border-purple-500/40"
                        rows={2} />
                      <div className="flex gap-1 mt-1 w-full">
                        <button onClick={() => { setAiEditAvatarId(null); setAiEditInstruction(''); }}
                          className="flex-1 text-[7px] py-1 rounded-lg border border-[#333] text-[#888] hover:text-white transition">
                          {t('studio.cancel') || 'Cancelar'}
                        </button>
                        <button data-testid={`ai-edit-confirm-${av.id}`} onClick={() => aiEditAvatar(av.id)} disabled={aiEditLoading || !aiEditInstruction.trim()}
                          className="flex-1 text-[7px] py-1 rounded-lg bg-purple-600 text-white font-bold hover:bg-purple-500 transition disabled:opacity-40 flex items-center justify-center gap-1">
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
            <p className="text-[9px] text-[#888] text-center py-2">{t('studio.no_avatar_yet')}</p>
          )}
        </div>

        {/* Avatar Zoom Preview */}
        {avatarPreviewUrl && (
          <div className="fixed inset-0 z-[80] bg-black/90 flex items-center justify-center p-6" onClick={() => setAvatarPreviewUrl(null)}>
            <div className="relative max-w-lg w-full" onClick={e => e.stopPropagation()}>
              <img src={resolveImageUrl(avatarPreviewUrl)} alt="Avatar Preview" className="w-full rounded-2xl border border-[#C9A84C]/20 shadow-2xl" />
              <button onClick={() => setAvatarPreviewUrl(null)}
                className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-black border border-[#333] flex items-center justify-center hover:bg-[#1A1A1A] transition">
                <X size={14} className="text-white" />
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
                  className="h-8 w-8 rounded-lg bg-black/70 border border-white/15 flex items-center justify-center hover:bg-black transition">
                  <Download size={14} className="text-white" />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Company Modal */}
        {showCompanyModal && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={cancelCompanyForm}>
            <div data-testid="company-modal" className="w-full max-w-md rounded-2xl border border-[#C9A84C]/20 bg-[#0D0D0D] p-5 space-y-3" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between">
                <p className="text-sm text-white font-semibold">{editingCompanyId ? t('studio.edit_company') : t('studio.new_company')}</p>
                <button onClick={cancelCompanyForm} className="p-1 rounded hover:bg-[#1A1A1A]"><X size={16} className="text-[#999]" /></button>
              </div>
              {/* Profile Type Selector */}
              <div className="flex gap-1.5">
                {[
                  { id: 'company', label: 'Empresa', icon: Building2 },
                  { id: 'professional', label: 'Profissional', icon: Briefcase },
                  { id: 'personal', label: 'Pessoal', icon: User },
                ].map(pt => (
                  <button key={pt.id} data-testid={`profile-type-${pt.id}`}
                    onClick={() => setNewCompany(p => ({ ...p, profile_type: pt.id }))}
                    className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg border text-[10px] font-semibold transition ${newCompany.profile_type === pt.id
                      ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10 text-[#C9A84C]'
                      : 'border-[#1E1E1E] text-[#999] hover:text-[#888] hover:border-[#333]'}`}>
                    <pt.icon size={12} />
                    {pt.label}
                  </button>
                ))}
              </div>
              {/* Logo / Photo Upload */}
              <input ref={logoInputRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp,image/svg+xml"
                style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
                onChange={e => { uploadCompanyLogo(e.target.files); e.target.value = ''; }} />
              <div className="flex items-center gap-3">
                <button data-testid="company-logo-upload" type="button" onClick={() => logoInputRef.current?.click()}
                  disabled={logoUploading}
                  className={`relative shrink-0 h-14 w-14 rounded-xl border-2 border-dashed flex items-center justify-center overflow-hidden transition ${newCompany.logo_url ? 'border-[#C9A84C]/40' : 'border-[#2A2A2A] hover:border-[#C9A84C]/30'}`}>
                  {newCompany.logo_url ? (
                    <img src={resolveImageUrl(newCompany.logo_url)} alt="Logo" className="h-full w-full object-cover" />
                  ) : logoUploading ? (
                    <Loader2 size={16} className="animate-spin text-[#C9A84C]" />
                  ) : (
                    <Image size={18} className="text-[#888]" />
                  )}
                </button>
                <div className="flex-1">
                  <p className="text-[10px] text-white font-medium">{newCompany.profile_type === 'personal' ? 'Foto' : newCompany.profile_type === 'professional' ? 'Foto / Logo' : 'Logo'}</p>
                  <p className="text-[8px] text-[#999]">{newCompany.logo_url ? t('studio.click_to_change') || 'Click to change' : t('studio.upload_logo')}</p>
                  {newCompany.logo_url && (
                    <button onClick={() => setNewCompany(p => ({ ...p, logo_url: '' }))} className="text-[8px] text-red-400 hover:text-red-300 mt-0.5">{t('studio.remove')}</button>
                  )}
                </div>
              </div>
              <div>
                <label className="text-[9px] text-[#999] uppercase mb-1 block">{newCompany.profile_type === 'personal' ? 'Nome' : newCompany.profile_type === 'professional' ? 'Nome Profissional' : t('studio.company_name_label')} *</label>
                <input data-testid="new-company-name" value={newCompany.name} onChange={e => setNewCompany(p => ({ ...p, name: e.target.value }))}
                  placeholder="E.g.: AgentZZ, My Company..."
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div className="grid grid-cols-[1fr_auto] gap-3">
                <div>
                  <label className="text-[9px] text-[#999] uppercase mb-1 block">{t('studio.company_phone')}</label>
                  <input data-testid="new-company-phone" value={newCompany.phone} onChange={e => setNewCompany(p => ({ ...p, phone: e.target.value }))}
                    placeholder="+1 555 123-4567"
                    className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30" />
                </div>
                <div className="flex items-end pb-0.5">
                  <button data-testid="new-company-whatsapp-toggle" onClick={() => setNewCompany(p => ({ ...p, is_whatsapp: !p.is_whatsapp }))}
                    className={`flex items-center gap-1 rounded-lg border px-3 py-2 text-[10px] font-medium transition ${newCompany.is_whatsapp ? 'border-[#25D366]/40 bg-[#25D366]/10 text-[#25D366]' : 'border-[#1E1E1E] text-[#999]'}`}>
                    <MessageSquare size={10} /> WhatsApp
                  </button>
                </div>
              </div>
              <div>
                <label className="text-[9px] text-[#999] uppercase mb-1 flex items-center gap-1">
                  <Globe size={9} /> {t('studio.company_website')}
                </label>
                <input data-testid="new-company-website" value={newCompany.website_url} onChange={e => setNewCompany(p => ({ ...p, website_url: e.target.value }))}
                  placeholder="https://www.yourcompany.com"
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[9px] text-[#999] uppercase mb-1 block">{t('studio.product_service') || 'Produto / Servico'}</label>
                <textarea data-testid="new-company-product" value={newCompany.product_description} onChange={e => setNewCompany(p => ({ ...p, product_description: e.target.value }))}
                  placeholder="Ex: Plataforma de agentes IA para atendimento ao cliente, Loja de roupas femininas..."
                  rows={2}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 resize-none" />
              </div>
              {/* Social Links */}
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-[8px] text-[#999] uppercase mb-1 flex items-center gap-1"><span style={{color:'#1877F2'}}>f</span> Facebook</label>
                  <input data-testid="new-company-facebook" value={newCompany.facebook_url || ''} onChange={e => setNewCompany(p => ({ ...p, facebook_url: e.target.value }))}
                    placeholder="facebook.com/..."
                    className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#1877F2]/30" />
                </div>
                <div>
                  <label className="text-[8px] text-[#999] uppercase mb-1 flex items-center gap-1"><span style={{color:'#E4405F'}}>@</span> Instagram</label>
                  <input data-testid="new-company-instagram" value={newCompany.instagram_url || ''} onChange={e => setNewCompany(p => ({ ...p, instagram_url: e.target.value }))}
                    placeholder="instagram.com/..."
                    className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#E4405F]/30" />
                </div>
                <div>
                  <label className="text-[8px] text-[#999] uppercase mb-1 flex items-center gap-1"><span style={{color:'#fff'}}>T</span> TikTok</label>
                  <input data-testid="new-company-tiktok" value={newCompany.tiktok_url || ''} onChange={e => setNewCompany(p => ({ ...p, tiktok_url: e.target.value }))}
                    placeholder="tiktok.com/@..."
                    className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#fff]/20" />
                </div>
              </div>
              <div className="flex gap-2 pt-2">
                <button onClick={cancelCompanyForm}
                  className="flex-1 rounded-lg border border-[#1E1E1E] py-2 text-xs text-[#888] hover:text-white transition">
                  {t('studio.cancel')}
                </button>
                <button data-testid="save-company-btn" onClick={editingCompanyId ? saveEditCompany : addCompany} disabled={!newCompany.name.trim()}
                  className="flex-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2 text-xs font-bold text-black hover:opacity-90 disabled:opacity-30 transition">
                  {editingCompanyId ? t('studio.update_company') : t('studio.save_company')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Avatar Creation / Customization Modal */}
        {showAvatarModal && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={() => { if (!generatingAvatar && !applyingClothing) resetAvatarModal(); }}>
            <div data-testid="avatar-modal" className="w-full max-w-lg rounded-2xl border border-[#C9A84C]/20 bg-[#0D0D0D] overflow-hidden max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
              {/* Header */}
              <div className="px-5 py-3 border-b border-[#151515] flex items-center justify-between shrink-0">
                <p className="text-sm text-white font-semibold">
                  {avatarStage === 'customize' ? (editingAvatarId ? t('studio.edit_avatar') : t('studio.customize_avatar')) : t('studio.create_avatar')}
                </p>
                <button onClick={() => { if (!generatingAvatar && !applyingClothing) resetAvatarModal(); }} className="p-1 rounded hover:bg-[#1A1A1A]"><X size={16} className="text-[#999]" /></button>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {avatarStage === 'upload' ? (
                  <>
                    {/* Avatar Type Tabs */}
                    <div className="flex gap-1 mb-3">
                      {[
                        { id: 'photo', label: t('studio.photo_reference') || 'Photo', icon: Camera },
                        { id: 'prompt', label: t('studio.by_prompt') || 'By Prompt', icon: PenTool },
                        { id: '3d', label: '3D Animated', icon: Sparkles },
                      ].map(tab => (
                        <button key={tab.id} data-testid={`avatar-mode-${tab.id}`} onClick={() => setAvatarCreationMode(tab.id)}
                          className={`flex-1 rounded-lg py-2 text-[9px] font-semibold transition flex items-center justify-center gap-1.5 ${
                            avatarCreationMode === tab.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                          <tab.icon size={11} /> {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* MODE: Photo Reference (existing) */}
                    {avatarCreationMode === 'photo' && (
                      <>
                        <input ref={avatarInputRef} type="file" accept={avatarSourceType === 'video' ? 'video/mp4,video/quicktime,video/webm,video/*' : 'image/png,image/jpeg,image/jpg,image/webp'}
                          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
                          onChange={e => {
                            if (avatarSourceType === 'video') uploadAvatarVideo(e.target.files);
                            else uploadAvatarPhoto(e.target.files);
                            e.target.value = '';
                          }} />

                    {/* Photo Upload Section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Camera size={12} className="text-[#C9A84C]" />
                        <span className="text-[9px] text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.photo_reference') || 'Photo Reference'}</span>
                        {!avatarSourcePhoto && <span className="text-[7px] text-red-400/70 uppercase">*{t('studio.required') || 'Required'}</span>}
                      </div>
                      {avatarSourcePhoto ? (
                        <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0A0A0A] border border-[#1E1E1E]">
                          <div className="relative shrink-0">
                            <img src={avatarSourcePhoto.preview || resolveImageUrl(avatarSourcePhoto.url)} alt="Source"
                              onError={(e) => { if (avatarSourcePhoto.url) e.target.src = resolveImageUrl(avatarSourcePhoto.url); }}
                              className="h-16 w-16 rounded-lg object-cover border border-[#C9A84C]/30" />
                            <button onClick={() => { setAvatarSourcePhoto(null); }}
                              className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
                              <X size={8} className="text-white" />
                            </button>
                          </div>
                          <div>
                            <p className="text-[9px] text-[#888]">{t('studio.photo_uploaded') || 'Photo uploaded'}</p>
                            <p className="text-[7px] text-[#888]">{t('studio.photo_desc_detail') || 'High-resolution facial reference'}</p>
                          </div>
                          <Check size={14} className="text-green-400 ml-auto" />
                        </div>
                      ) : (
                        <button data-testid="upload-photo-btn" onClick={() => { setAvatarSourceType('photo'); setTimeout(() => avatarInputRef.current?.click(), 100); }}
                          disabled={avatarPhotoUploading}
                          className="w-full p-3 rounded-xl border border-dashed border-[#2A2A2A] hover:border-[#C9A84C]/30 text-center transition group">
                          {avatarPhotoUploading ? (
                            <div className="flex items-center justify-center gap-2"><Loader2 size={12} className="animate-spin text-[#C9A84C]" /><span className="text-[9px] text-[#999]">{t('studio.uploading')}</span></div>
                          ) : (
                            <div className="flex items-center justify-center gap-2">
                              <Upload size={14} className="text-[#888] group-hover:text-[#C9A84C] transition" />
                              <span className="text-[9px] text-[#999] group-hover:text-[#C9A84C] transition">{t('studio.select_photo') || 'Select photo'}</span>
                            </div>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Video Upload Section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Film size={12} className="text-[#C9A84C]" />
                        <span className="text-[9px] text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.video_reference') || 'Video Reference'}</span>
                        <span className="px-1.5 py-0.5 rounded-full bg-[#C9A84C]/15 text-[6px] text-[#C9A84C] font-bold uppercase">{t('studio.recommended') || 'Recommended'}</span>
                      </div>
                      {avatarExtractedAudio || avatarVideoFrames.length > 0 ? (
                        <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0A0A0A] border border-[#1E1E1E]">
                          {avatarVideoFrames.length > 0 && (
                            <div className="flex -space-x-2 shrink-0">
                              {avatarVideoFrames.slice(0, 3).map((url, i) => (
                                <img key={i} src={resolveImageUrl(url)} alt={`frame ${i}`}
                                  className="h-10 w-10 rounded-lg object-cover border-2 border-[#0A0A0A]" />
                              ))}
                            </div>
                          )}
                          <div className="flex-1 space-y-0.5">
                            <p className="text-[9px] text-[#888]">{t('studio.video_processed') || 'Video processed'}</p>
                            <div className="flex items-center gap-2">
                              {avatarVideoFrames.length > 0 && (
                                <span className="text-[7px] text-[#999]">{avatarVideoFrames.length} {t('studio.extra_frames') || 'frames'}</span>
                              )}
                              {avatarExtractedAudio && (
                                <span className="flex items-center gap-1 text-[7px] text-[#10B981]"><Volume2 size={8} /> {t('studio.voice_extracted')}</span>
                              )}
                            </div>
                          </div>
                          <button onClick={() => { setAvatarExtractedAudio(null); setAvatarVideoFrames([]); }}
                            className="p-1 rounded hover:bg-[#1A1A1A]"><X size={12} className="text-[#999]" /></button>
                        </div>
                      ) : (
                        <button data-testid="upload-video-btn" onClick={() => { setAvatarSourceType('video'); setTimeout(() => avatarInputRef.current?.click(), 100); }}
                          disabled={avatarVideoUploading}
                          className="w-full p-3 rounded-xl border border-dashed border-[#2A2A2A] hover:border-[#C9A84C]/30 text-center transition group">
                          {avatarVideoUploading ? (
                            <div className="flex items-center justify-center gap-2"><Loader2 size={12} className="animate-spin text-[#C9A84C]" /><span className="text-[9px] text-[#999]">{t('studio.extracting_video')}</span></div>
                          ) : (
                            <div className="space-y-1">
                              <div className="flex items-center justify-center gap-2">
                                <Upload size={14} className="text-[#888] group-hover:text-[#C9A84C] transition" />
                                <span className="text-[9px] text-[#999] group-hover:text-[#C9A84C] transition">{t('studio.select_video') || 'Select video'}</span>
                              </div>
                              <p className="text-[7px] text-[#777]">{t('studio.video_adds_accuracy') || 'Adds body, voice & expression data for higher accuracy'}</p>
                            </div>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Generate Button (requires photo) */}
                    {avatarSourcePhoto && (
                      <div className="space-y-2 pt-2">
                        {avatarVideoFrames.length > 0 && (
                          <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-green-500/5 border border-green-500/15">
                            <ShieldCheck size={10} className="text-green-400" />
                            <span className="text-[7px] text-green-400">{t('studio.enhanced_accuracy') || 'Enhanced accuracy: photo + video references active'}</span>
                          </div>
                        )}
                        <button data-testid="generate-avatar-btn" onClick={generateAvatarFromPhoto}
                          disabled={generatingAvatar}
                          className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-xs font-bold text-black hover:opacity-90 disabled:opacity-50 transition flex items-center justify-center gap-2">
                          {generatingAvatar ? (
                            <><Loader2 size={14} className="animate-spin" /> {t('studio.generating_avatar')}</>
                          ) : (
                            <><Sparkles size={14} /> {t('studio.generate_avatar_ai')}</>
                          )}
                        </button>
                        {generatingAvatar && (
                          <div className="rounded-xl bg-[#0A0A0A] border border-[#1E1E1E] p-4 space-y-3">
                            {/* Agent Timeline Header */}
                            <div className="flex items-center gap-2 pb-2 border-b border-[#1A1A1A]">
                              <div className="flex items-center gap-1.5">
                                {[
                                  { name: 'Scanner', icon: ScanEye, role: t('studio.agent_scanner') || 'Analyzing' },
                                  { name: 'Artist', icon: Bot, role: t('studio.agent_artist') || 'Generating' },
                                  { name: 'Critic', icon: ShieldCheck, role: t('studio.agent_critic') || 'Evaluating' },
                                ].map((agent, idx) => {
                                  const isActive = accuracyProgress?.active_agent === agent.name;
                                  const isDone = accuracyProgress?.iteration > 0 && (
                                    (agent.name === 'Scanner') ||
                                    (agent.name === 'Artist' && accuracyProgress?.iterations?.length > 0) ||
                                    (agent.name === 'Critic' && accuracyProgress?.iterations?.some(it => it.score > 0))
                                  );
                                  return (
                                    <React.Fragment key={agent.name}>
                                      {idx > 0 && <div className={`w-4 h-px ${isDone ? 'bg-[#C9A84C]' : 'bg-[#1E1E1E]'}`} />}
                                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg transition ${
                                        isActive ? 'bg-[#C9A84C]/15 border border-[#C9A84C]/30' :
                                        isDone ? 'bg-green-500/10 border border-green-500/20' :
                                        'bg-[#111] border border-[#1A1A1A]'}`}>
                                        <agent.icon size={10} className={isActive ? 'text-[#C9A84C] animate-pulse' : isDone ? 'text-green-400' : 'text-[#888]'} />
                                        <span className={`text-[7px] font-bold uppercase tracking-wider ${
                                          isActive ? 'text-[#C9A84C]' : isDone ? 'text-green-400' : 'text-[#888]'}`}>
                                          {agent.name}
                                        </span>
                                      </div>
                                    </React.Fragment>
                                  );
                                })}
                              </div>
                            </div>

                            {/* Progress info */}
                            <div className="flex items-center gap-2">
                              <Loader2 size={12} className="animate-spin text-[#C9A84C] shrink-0" />
                              <p className="text-[9px] text-[#888]">
                                {accuracyProgress?.progress || t('studio.avatar_gen_time')}
                              </p>
                            </div>

                            {/* Iteration progress bar */}
                            {accuracyProgress?.iteration > 0 && (
                              <div className="flex items-center gap-1.5">
                                <div className="flex-1 h-1.5 bg-[#1E1E1E] rounded-full overflow-hidden">
                                  <div className="h-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] transition-all duration-700 rounded-full"
                                    style={{width: `${(accuracyProgress.iteration / 3) * 100}%`}} />
                                </div>
                                <span className="text-[8px] text-[#999] font-mono">{accuracyProgress.iteration}/3</span>
                              </div>
                            )}

                            {/* Evolution thumbnails with scores */}
                            {accuracyProgress?.iterations?.length > 0 && (
                              <div className="space-y-1.5 pt-1 border-t border-[#1A1A1A]">
                                <p className="text-[7px] text-[#999] uppercase tracking-wider">{t('studio.accuracy_evolution') || 'Evolution'}</p>
                                <div className="flex gap-2">
                                  {accuracyProgress.iterations.map((it, idx) => (
                                    it.url && <div key={idx} className="relative group/evo">
                                      <img src={resolveImageUrl(it.url)} alt={`v${idx+1}`}
                                        className={`h-20 w-14 rounded-xl object-cover border-2 transition ${
                                          it.passed ? 'border-green-500/40' : 'border-red-500/30'}`} />
                                      <div className={`absolute -top-1.5 -right-1.5 h-5 min-w-5 px-0.5 rounded-full text-[8px] font-bold flex items-center justify-center shadow-lg ${
                                        it.passed ? 'bg-green-500 text-white' : 'bg-red-500/80 text-white'}`}>
                                        {it.score}
                                      </div>
                                      <div className={`absolute -bottom-0.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded text-[6px] font-bold ${
                                        it.passed ? 'bg-green-500/90 text-white' : 'bg-red-500/70 text-white'}`}>
                                        {it.passed ? 'OK' : 'REDO'}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                      </>
                    )}

                    {/* MODE: By Prompt */}
                    {avatarCreationMode === 'prompt' && (
                      <div className="space-y-3">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <PenTool size={12} className="text-[#C9A84C]" />
                            <span className="text-[9px] text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.describe_avatar') || 'Describe your avatar'}</span>
                          </div>
                          <textarea data-testid="avatar-prompt-input" value={avatarPromptText}
                            onChange={e => setAvatarPromptText(e.target.value)}
                            placeholder={t('studio.avatar_prompt_placeholder') || 'E.g.: Young professional woman, 28 years old, brown hair, confident smile, business attire'}
                            className="w-full bg-[#0A0A0A] border border-[#1E1E1E] rounded-xl px-3 py-2.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 resize-none h-20" />
                        </div>
                        <div className="flex gap-2">
                          <div className="flex-1 space-y-1">
                            <span className="text-[8px] text-[#999] uppercase tracking-wider">{t('studio.gender') || 'Gender'}</span>
                            <div className="flex gap-1">
                              {[{id:'female', label:'F'}, {id:'male', label:'M'}].map(g => (
                                <button key={g.id} onClick={() => setAvatarPromptGender(g.id)}
                                  className={`flex-1 rounded-lg py-1.5 text-[9px] font-semibold transition ${avatarPromptGender === g.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                  {g.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                        {/* Style selector - also for prompt mode */}
                        <div className="space-y-1">
                          <span className="text-[8px] text-[#999] uppercase tracking-wider">{t('studio.style') || 'Style'}</span>
                          <div className="flex gap-1">
                            {[{id:'custom', label:'Custom'}, {id:'realistic', label:'Realistic'}, {id:'3d_cartoon', label:'3D Cartoon'}, {id:'3d_pixar', label:'3D Pixar'}].map(s => (
                              <button key={s.id} onClick={() => setAvatarPromptStyle(s.id)}
                                data-testid={`prompt-style-${s.id}`}
                                className={`flex-1 rounded-lg py-1.5 text-[8px] font-semibold transition ${avatarPromptStyle === s.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                {s.label}
                              </button>
                            ))}
                          </div>
                        </div>
                        <button data-testid="generate-avatar-prompt-btn" onClick={generateAvatarFromPrompt}
                          disabled={generatingAvatar || !avatarPromptText.trim()}
                          className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-xs font-bold text-black hover:opacity-90 disabled:opacity-50 transition flex items-center justify-center gap-2">
                          {generatingAvatar ? (
                            <><Loader2 size={14} className="animate-spin" /> {accuracyProgress?.progress || t('studio.generating_avatar')}</>
                          ) : (
                            <><Sparkles size={14} /> {t('studio.generate_avatar_ai')}</>
                          )}
                        </button>
                      </div>
                    )}

                    {/* MODE: 3D Animated */}
                    {avatarCreationMode === '3d' && (
                      <div className="space-y-3">
                        {/* Hidden file input for 3D photo reference */}
                        <input ref={avatarInputRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp"
                          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
                          onChange={e => { uploadAvatarPhoto(e.target.files); e.target.value = ''; }} />

                        {/* Optional Photo Reference for 3D */}
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Camera size={12} className="text-[#C9A84C]" />
                            <span className="text-[9px] text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.photo_reference') || 'Photo Reference'}</span>
                            <span className="px-1.5 py-0.5 rounded-full bg-[#C9A84C]/10 text-[6px] text-[#C9A84C]/70 font-bold uppercase">{t('studio.optional') || 'Optional'}</span>
                          </div>
                          {avatarSourcePhoto ? (
                            <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0A0A0A] border border-[#1E1E1E]">
                              <div className="relative shrink-0">
                                <img src={avatarSourcePhoto.preview || resolveImageUrl(avatarSourcePhoto.url)} alt="Ref"
                                  onError={(e) => { if (avatarSourcePhoto.url) e.target.src = resolveImageUrl(avatarSourcePhoto.url); }}
                                  className="h-14 w-14 rounded-lg object-cover border border-[#C9A84C]/30" />
                                <button onClick={() => setAvatarSourcePhoto(null)}
                                  className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
                                  <X size={8} className="text-white" />
                                </button>
                              </div>
                              <div>
                                <p className="text-[9px] text-[#888]">{t('studio.photo_uploaded') || 'Photo uploaded'}</p>
                                <p className="text-[7px] text-[#888]">{t('studio.photo_3d_ref_desc') || '3D avatar will match this face'}</p>
                              </div>
                              <Check size={14} className="text-green-400 ml-auto" />
                            </div>
                          ) : (
                            <button data-testid="upload-3d-ref-photo-btn" onClick={() => { setAvatarSourceType('photo'); setTimeout(() => avatarInputRef.current?.click(), 100); }}
                              disabled={avatarPhotoUploading}
                              className="w-full p-2.5 rounded-xl border border-dashed border-[#2A2A2A] hover:border-[#C9A84C]/30 text-center transition group">
                              {avatarPhotoUploading ? (
                                <div className="flex items-center justify-center gap-2"><Loader2 size={12} className="animate-spin text-[#C9A84C]" /><span className="text-[9px] text-[#999]">{t('studio.uploading')}</span></div>
                              ) : (
                                <div className="space-y-0.5">
                                  <div className="flex items-center justify-center gap-2">
                                    <Upload size={12} className="text-[#888] group-hover:text-[#C9A84C] transition" />
                                    <span className="text-[9px] text-[#999] group-hover:text-[#C9A84C] transition">{t('studio.upload_ref_photo') || 'Upload reference photo'}</span>
                                  </div>
                                  <p className="text-[7px] text-[#777]">{t('studio.photo_3d_hint') || 'Upload a face photo to guide the 3D style'}</p>
                                </div>
                              )}
                            </button>
                          )}
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Sparkles size={12} className="text-[#C9A84C]" />
                            <span className="text-[9px] text-[#C9A84C] font-bold uppercase tracking-wider">3D Avatar Description</span>
                          </div>
                          <textarea data-testid="avatar-3d-prompt-input" value={avatarPromptText}
                            onChange={e => setAvatarPromptText(e.target.value)}
                            placeholder={t('studio.avatar_3d_placeholder') || 'E.g.: Friendly 3D character, young man with glasses, wearing casual clothes, vibrant colors'}
                            className="w-full bg-[#0A0A0A] border border-[#1E1E1E] rounded-xl px-3 py-2.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 resize-none h-20" />
                        </div>
                        <div className="flex gap-2">
                          <div className="flex-1 space-y-1">
                            <span className="text-[8px] text-[#999] uppercase tracking-wider">{t('studio.gender') || 'Gender'}</span>
                            <div className="flex gap-1">
                              {[{id:'female', label:'F'}, {id:'male', label:'M'}].map(g => (
                                <button key={g.id} onClick={() => setAvatarPromptGender(g.id)}
                                  className={`flex-1 rounded-lg py-1.5 text-[9px] font-semibold transition ${avatarPromptGender === g.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                  {g.label}
                                </button>
                              ))}
                            </div>
                          </div>
                          <div className="flex-1 space-y-1">
                            <span className="text-[8px] text-[#999] uppercase tracking-wider">{t('studio.style') || 'Style'}</span>
                            <div className="flex gap-1">
                              {[{id:'3d_cartoon', label:'Cartoon'}, {id:'3d_pixar', label:'Pixar'}].map(s => (
                                <button key={s.id} onClick={() => setAvatarPromptStyle(s.id)}
                                  className={`flex-1 rounded-lg py-1.5 text-[9px] font-semibold transition ${avatarPromptStyle === s.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                  {s.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                        <button data-testid="generate-avatar-3d-btn" onClick={generateAvatarFromPrompt}
                          disabled={generatingAvatar || !avatarPromptText.trim()}
                          className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-xs font-bold text-black hover:opacity-90 disabled:opacity-50 transition flex items-center justify-center gap-2">
                          {generatingAvatar ? (
                            <><Loader2 size={14} className="animate-spin" /> {accuracyProgress?.progress || t('studio.generating_avatar')}</>
                          ) : (
                            <><Sparkles size={14} /> Generate 3D Avatar</>
                          )}
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  /* CUSTOMIZE STAGE */
                  <>
                    {/* Avatar Name */}
                    <div className="flex items-center gap-2">
                      <input
                        data-testid="avatar-name-input"
                        type="text"
                        value={avatarName}
                        onChange={(e) => setAvatarName(e.target.value)}
                        placeholder={t('studio.avatar_name_placeholder') || 'Name your avatar...'}
                        className="flex-1 bg-[#0A0A0A] border border-[#1E1E1E] rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-[#888] focus:border-[#C9A84C]/50 focus:outline-none"
                      />
                    </div>

                    {/* Avatar Preview - Photo/Video selector */}
                    <div className="flex flex-col items-center gap-2">
                      {/* Photo / Video toggle */}
                      {(previewVideoUrl || generatingPreviewVideo) && (
                        <div className="flex rounded-md border border-[#1E1E1E] overflow-hidden">
                          <button data-testid="media-tab-photo" onClick={() => setAvatarMediaTab('photo')}
                            className={`px-4 py-1 text-[9px] font-semibold flex items-center gap-1 transition ${
                              avatarMediaTab === 'photo' ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'text-[#999] hover:text-[#888]'}`}>
                            <Camera size={10} /> {t('studio.photo_tab') || 'Photo'}
                          </button>
                          <button data-testid="media-tab-video" onClick={() => setAvatarMediaTab('video')}
                            className={`px-4 py-1 text-[9px] font-semibold flex items-center gap-1 transition ${
                              avatarMediaTab === 'video' ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'text-[#999] hover:text-[#888]'}`}>
                            <Film size={10} /> {t('studio.video_tab') || 'Video'}
                          </button>
                        </div>
                      )}

                      {/* Media Display + History (left) + AI Edit Side Panel (right) */}
                      <div className="flex gap-3 items-start">
                      {/* Edit History Panel (Left, vertical scroll, last 2 visible) */}
                      {avatarEditHistory.length > 1 && (
                        <div className="w-24 shrink-0 flex flex-col gap-1.5" data-testid="avatar-edit-history">
                          <div className="flex items-center gap-1">
                            <History size={9} className="text-[#999]" />
                            <span className="text-[7px] text-[#999] uppercase tracking-wider font-semibold">{t('studio.history') || 'Historico'}</span>
                          </div>
                          <div className="flex flex-col gap-1.5 overflow-y-auto pr-0.5" style={{maxHeight: '220px'}}>
                            {avatarEditHistory.map((entry, idx) => {
                              const isCurrent = tempAvatar?.url === entry.url;
                              return (
                                <div key={idx} data-testid={`history-entry-${idx}`}
                                  className={`relative shrink-0 rounded-xl overflow-hidden border-2 cursor-pointer transition group ${
                                    isCurrent ? 'border-[#C9A84C] shadow-[0_0_8px_rgba(201,168,76,0.15)]' : 'border-[#1E1E1E] hover:border-[#333]'
                                  }`}
                                  onClick={() => setTempAvatar(p => ({ ...p, url: entry.url }))}>
                                  <img src={resolveImageUrl(entry.url)} alt={`v${idx + 1}`}
                                    className="w-full aspect-[3/5] object-cover" />
                                  {entry.isBase && (
                                    <div className="absolute top-0.5 left-0.5 bg-[#C9A84C] rounded px-1 py-0.5">
                                      <span className="text-[5px] text-black font-bold uppercase">BASE</span>
                                    </div>
                                  )}
                                  <div className="absolute top-0.5 right-0.5 bg-black/70 rounded px-1 py-0.5">
                                    <span className="text-[6px] text-white font-bold">v{idx + 1}</span>
                                  </div>
                                  {isCurrent && (
                                    <div className="absolute bottom-0.5 right-0.5 h-3.5 w-3.5 rounded-full bg-[#C9A84C] flex items-center justify-center">
                                      <Check size={7} className="text-black" />
                                    </div>
                                  )}
                                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-1 opacity-0 group-hover:opacity-100 transition">
                                    <p className="text-[5px] text-white/80 line-clamp-2 leading-tight">{entry.instruction}</p>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      <div className="w-40 shrink-0">
                      <div className="relative aspect-[3/5]">
                        {avatarMediaTab === 'video' && previewVideoUrl ? (
                          <video
                            data-testid="avatar-preview-video"
                            src={previewVideoUrl}
                            controls autoPlay loop playsInline
                            className="w-full h-full rounded-2xl object-cover border-2 border-[#C9A84C]/30 shadow-lg bg-black"
                          />
                        ) : (
                          <div className="relative cursor-pointer group" onClick={() => setAvatarPreviewUrl(tempAvatar?.url)}>
                            <img src={resolveImageUrl(tempAvatar?.url)} alt="Avatar"
                              className="w-full h-full rounded-2xl object-cover border-2 border-[#C9A84C]/30 shadow-lg" />
                            <div className="absolute inset-0 rounded-2xl bg-black/0 group-hover:bg-black/30 transition flex items-center justify-center">
                              <Maximize2 size={16} className="text-white opacity-0 group-hover:opacity-100 transition" />
                            </div>
                            {applyingClothing && (
                              <div className="absolute inset-0 rounded-2xl bg-black/60 flex items-center justify-center">
                                <Loader2 size={24} className="animate-spin text-[#C9A84C]" />
                              </div>
                            )}
                          </div>
                        )}
                        {/* Generating video overlay */}
                        {avatarMediaTab === 'video' && generatingPreviewVideo && !previewVideoUrl && (
                          <div className="absolute inset-0 rounded-2xl bg-black/80 border-2 border-[#C9A84C]/30 flex flex-col items-center justify-center gap-2">
                            <Loader2 size={20} className="animate-spin text-[#C9A84C]" />
                            <p className="text-[8px] text-[#C9A84C]">{t('studio.generating_preview')}</p>
                          </div>
                        )}
                      </div>
                      {/* AI Edit button below avatar */}
                      {avatarMediaTab !== 'video' && (
                        <button data-testid="ai-edit-avatar-modal-btn" onClick={() => setAiEditAvatarId(aiEditAvatarId === 'temp' ? null : 'temp')}
                          className={`mt-1.5 w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg border border-dashed text-[9px] transition ${aiEditAvatarId === 'temp' ? 'border-purple-500/50 bg-purple-500/10 text-purple-300' : 'border-purple-500/30 text-purple-400 hover:bg-purple-500/10 hover:border-purple-500/50'}`}>
                          <Sparkles size={10} /> {t('studio.ai_edit') || 'Editar com IA'}
                        </button>
                      )}
                      </div>
                      {/* AI Edit Side Panel */}
                      {aiEditAvatarId === 'temp' && (
                        <div className="flex-1 min-w-[140px] bg-[#111] border border-[#1E1E1E] rounded-xl p-3 flex flex-col gap-2" onClick={e => e.stopPropagation()}>
                          <div className="flex items-center gap-1.5">
                            <Sparkles size={12} className="text-purple-400" />
                            <span className="text-[9px] text-purple-300 font-bold">{t('studio.ai_edit') || 'Editar com IA'}</span>
                          </div>
                          <textarea data-testid="ai-edit-modal-input"
                            value={aiEditInstruction} onChange={e => setAiEditInstruction(e.target.value)}
                            placeholder="Ex: mudar roupa para tunica bege, adicionar oculos, mudar fundo para praia..."
                            className="w-full text-[9px] bg-[#0A0A0A] border border-[#222] rounded-lg p-2 text-white placeholder-[#666] resize-none outline-none focus:border-purple-500/40"
                            rows={4} />
                          <div className="flex gap-1.5">
                            <button onClick={() => { setAiEditAvatarId(null); setAiEditInstruction(''); }}
                              className="flex-1 text-[8px] py-1.5 rounded-lg border border-[#333] text-[#888] hover:text-white transition">
                              {t('studio.cancel') || 'Cancelar'}
                            </button>
                            <button data-testid="ai-edit-modal-confirm" onClick={async () => {
                              if (!aiEditInstruction.trim() || aiEditLoading) return;
                              setAiEditLoading(true);
                              try {
                                const { data } = await axios.post(`${API}/campaigns/pipeline/edit-avatar`, {
                                  avatar_url: tempAvatar.url,
                                  instruction: aiEditInstruction,
                                  base_url: avatarBaseUrl || tempAvatar.url,
                                });
                                if (data.url) {
                                  setTempAvatar(p => ({ ...p, url: data.url }));
                                  setAvatarEditHistory(prev => [...prev, {
                                    url: data.url,
                                    instruction: aiEditInstruction,
                                    timestamp: new Date().toISOString(),
                                    isBase: false,
                                  }]);
                                  toast.success(t('studio.avatar_edited') || 'Avatar editado com IA!');
                                }
                              } catch (err) {
                                toast.error(err.response?.data?.detail || 'Erro ao editar avatar');
                              } finally {
                                setAiEditLoading(false);
                                setAiEditAvatarId(null);
                                setAiEditInstruction('');
                              }
                            }} disabled={aiEditLoading || !aiEditInstruction.trim()}
                              className="flex-1 text-[8px] py-1.5 rounded-lg bg-purple-600 text-white font-bold hover:bg-purple-500 transition disabled:opacity-40 flex items-center justify-center gap-1">
                              {aiEditLoading ? <RefreshCw size={10} className="animate-spin" /> : <Sparkles size={10} />}
                              {aiEditLoading ? (t('studio.editing') || 'Editando...') : (t('studio.apply') || 'Aplicar')}
                            </button>
                          </div>
                        </div>
                      )}
                      </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex rounded-lg border border-[#1A1A1A] bg-[#0A0A0A] p-0.5">
                      {[
                        { id: 'clothing', icon: Shirt, label: t('studio.clothing') },
                        { id: 'view360', icon: RotateCw, label: t('studio.view_360') },
                        { id: 'voice', icon: Volume2, label: t('studio.voice') },
                      ].map(tab => (
                        <button key={tab.id} data-testid={`avatar-tab-${tab.id}`}
                          onClick={() => {
                            setCustomizeTab(tab.id);
                            // Auto-trigger 360° generation when switching to the tab if missing angles
                            if (tab.id === 'view360' && tempAvatar?.url && !auto360Progress) {
                              const loadedAngles = Object.values(angleImages).filter(Boolean).length;
                              if (loadedAngles < 4) {
                                const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
                                const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
                                startAuto360(sourceUrl, tempAvatar.clothing || 'company_uniform', tempAvatar?.avatar_style || 'realistic');
                              }
                            }
                          }}
                          className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-2 text-[10px] font-semibold transition ${
                            customizeTab === tab.id ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'text-[#999] hover:text-[#888]'}`}>
                          <tab.icon size={12} /> {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* Clothing Tab */}
                    {customizeTab === 'clothing' && (
                      <div className="space-y-3">
                        {/* Clothing gallery of generated variants */}
                        {Object.keys(clothingVariants).length > 1 && (
                          <div>
                            <p className="text-[8px] text-[#999] uppercase tracking-wider mb-1.5">{t('studio.my_avatars')}</p>
                            <div className="flex gap-2 flex-wrap">
                              {Object.entries(clothingVariants).map(([style, url]) => (
                                <button key={style} onClick={() => setTempAvatar(p => ({ ...p, url, clothing: style }))}
                                  className={`relative rounded-xl overflow-hidden border-2 transition ${
                                    tempAvatar?.clothing === style ? 'border-[#C9A84C] shadow-[0_0_8px_rgba(201,168,76,0.2)]' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
                                  <img src={resolveImageUrl(url)} alt={style} className="w-14 h-20 object-cover" />
                                  {tempAvatar?.clothing === style && (
                                    <div className="absolute top-0.5 right-0.5 h-3.5 w-3.5 rounded-full bg-[#C9A84C] flex items-center justify-center">
                                      <Check size={7} className="text-black" />
                                    </div>
                                  )}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                        {/* Clothing style buttons */}
                        <div className="grid grid-cols-2 gap-2">
                          {[
                            { id: 'company_uniform', label: t('studio.clothing_uniform'), icon: '👕' },
                            { id: 'business_formal', label: t('studio.clothing_business'), icon: '👔' },
                            { id: 'casual', label: t('studio.clothing_casual'), icon: '🧥' },
                            { id: 'streetwear', label: t('studio.clothing_streetwear'), icon: '🏙' },
                            { id: 'creative', label: t('studio.clothing_creative'), icon: '🎨' },
                          ].map(style => (
                            <button key={style.id} data-testid={`clothing-${style.id}`}
                              onClick={() => applyClothing(style.id)}
                              disabled={applyingClothing}
                              className={`rounded-xl border p-3 text-left transition ${
                                tempAvatar?.clothing === style.id ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'} disabled:opacity-40`}>
                              <div className="flex items-center gap-2">
                                <p className="text-lg">{style.icon}</p>
                                <div>
                                  <p className="text-[10px] text-white font-medium">{style.label}</p>
                                  {clothingVariants[style.id] && (
                                    <p className="text-[7px] text-green-400">{t('studio.avatar_ready')}</p>
                                  )}
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                        {applyingClothing && (
                          <div className="text-center py-2">
                            <p className="text-[9px] text-[#C9A84C] flex items-center justify-center gap-1.5">
                              <Loader2 size={10} className="animate-spin" /> {t('studio.applying_style')}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* 360° View Tab */}
                    {customizeTab === 'view360' && (
                      <div className="space-y-2">
                        {auto360Progress && (
                          <div className="flex items-center gap-2 text-[9px] text-[#C9A84C] bg-[#C9A84C]/10 rounded-lg px-3 py-1.5">
                            <Loader2 size={10} className="animate-spin" />
                            <span>{t('studio.auto_generating_360') || 'Generating 360°...'} {auto360Progress.completed}/4</span>
                            <div className="flex-1 h-1 bg-[#1E1E1E] rounded-full overflow-hidden">
                              <div className="h-full bg-[#C9A84C] transition-all duration-500 rounded-full" style={{width: `${(auto360Progress.completed / 4) * 100}%`}} />
                            </div>
                          </div>
                        )}
                        <div className="grid grid-cols-4 gap-2">
                        {[
                          { id: 'front', label: t('studio.angle_front') },
                          { id: 'left_profile', label: t('studio.angle_left') },
                          { id: 'right_profile', label: t('studio.angle_right') },
                          { id: 'back', label: t('studio.angle_back') },
                        ].map(angle => (
                          <div key={angle.id} data-testid={`angle-${angle.id}`}
                            className={`relative rounded-xl border overflow-hidden transition group/angle ${
                              angleImages[angle.id] ? 'border-[#C9A84C]/30' : 'border-[#1E1E1E] border-dashed'}`}>
                            <button
                              onClick={() => { if (angleImages[angle.id]) setTempAvatar(p => ({ ...p, url: angleImages[angle.id] })); else generateAngle(angle.id); }}
                              disabled={generatingAngle === angle.id}
                              className="w-full">
                              {angleImages[angle.id] ? (
                                <img src={resolveImageUrl(angleImages[angle.id])} alt={angle.label} className="w-full aspect-[3/5] object-cover" />
                              ) : generatingAngle === angle.id ? (
                                <div className="w-full aspect-[3/5] flex items-center justify-center bg-[#111]">
                                  <Loader2 size={14} className="animate-spin text-[#C9A84C]" />
                                </div>
                              ) : (
                                <div className="w-full aspect-[3/5] flex items-center justify-center bg-[#0A0A0A]">
                                  <RotateCw size={14} className="text-[#777]" />
                                </div>
                              )}
                            </button>
                            {angleImages[angle.id] && generatingAngle !== angle.id && (
                              <button data-testid={`regen-angle-${angle.id}`}
                                onClick={(e) => { e.stopPropagation(); generateAngle(angle.id, true); }}
                                className="absolute top-1 right-1 h-5 w-5 rounded-full bg-black/70 border border-white/20 flex items-center justify-center opacity-0 group-hover/angle:opacity-100 transition"
                                title={t('studio.regenerate_angle')}>
                                <RefreshCw size={9} className="text-[#C9A84C]" />
                              </button>
                            )}
                            <p className="text-[8px] text-[#888] text-center py-1">{angle.label}</p>
                          </div>
                        ))}
                      </div>
                      {/* Regenerate All 360° button */}
                      {!auto360Progress && (
                        <button data-testid="regen-all-360-btn"
                          onClick={() => {
                            const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
                            const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
                            setAngleImages({ front: tempAvatar.url });
                            startAuto360(sourceUrl, tempAvatar?.clothing || 'company_uniform', tempAvatar?.avatar_style || 'realistic');
                          }}
                          className="w-full rounded-lg border border-dashed border-[#C9A84C]/20 py-2 text-[9px] text-[#C9A84C] hover:bg-[#C9A84C]/5 transition flex items-center justify-center gap-1.5">
                          <RefreshCw size={10} /> {t('studio.regenerate_all_360') || 'Regenerate All 360°'}
                        </button>
                      )}
                      </div>
                    )}

                    {/* Voice Tab */}
                    {customizeTab === 'voice' && (
                      <div className="space-y-3">
                        {/* Voice sub-tabs */}
                        <div className="flex gap-1">
                          <button onClick={() => setVoiceTab('bank')}
                            className={`flex-1 rounded-lg py-1.5 text-[9px] font-semibold transition ${voiceTab === 'bank' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                            {t('studio.voice_bank')}
                          </button>
                          <button onClick={() => setVoiceTab('premium')}
                            className={`flex-1 rounded-lg py-1.5 text-[9px] font-semibold transition flex items-center justify-center gap-1 ${voiceTab === 'premium' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                            <Crown size={9} /> {t('studio.premium_voices')}
                          </button>
                          <button onClick={() => setVoiceTab('record')}
                            className={`flex-1 rounded-lg py-1.5 text-[9px] font-semibold transition ${voiceTab === 'record' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                            {t('studio.custom_recording')}
                          </button>
                        </div>

                        {voiceTab === 'bank' ? (
                          <div className="space-y-1.5">
                            {[
                              { id: 'alloy', key: 'voice_alloy' },
                              { id: 'echo', key: 'voice_echo' },
                              { id: 'fable', key: 'voice_fable' },
                              { id: 'onyx', key: 'voice_onyx' },
                              { id: 'nova', key: 'voice_nova' },
                              { id: 'shimmer', key: 'voice_shimmer' },
                            ].map(v => (
                              <div key={v.id} data-testid={`voice-${v.id}`}
                                className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition ${
                                  tempAvatar?.voice?.type === 'openai' && tempAvatar?.voice?.voice_id === v.id
                                    ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}
                                onClick={() => setTempAvatar(p => ({ ...p, voice: { type: 'openai', voice_id: v.id } }))}>
                                <div className="flex-1">
                                  <p className="text-[10px] text-white font-medium capitalize">{v.id}</p>
                                  <p className="text-[8px] text-[#999]">{t(`studio.${v.key}`)}</p>
                                </div>
                                <button onClick={e => { e.stopPropagation(); previewVoice(v.id, 'openai'); }}
                                  disabled={loadingVoicePreview === v.id}
                                  className="h-7 w-7 rounded-lg border border-[#2A2A2A] flex items-center justify-center hover:bg-[#1A1A1A] transition disabled:opacity-40">
                                  {loadingVoicePreview === v.id ? (
                                    <Loader2 size={10} className="animate-spin text-[#C9A84C]" />
                                  ) : playingVoiceId === v.id ? (
                                    <Volume2 size={10} className="text-[#C9A84C]" />
                                  ) : (
                                    <Play size={10} className="text-[#999]" />
                                  )}
                                </button>
                                {tempAvatar?.voice?.type === 'openai' && tempAvatar?.voice?.voice_id === v.id && (
                                  <Check size={12} className="text-[#C9A84C] shrink-0" />
                                )}
                              </div>
                            ))}
                          </div>
                        ) : voiceTab === 'premium' ? (
                          <div className="space-y-1.5" data-testid="elevenlabs-voices-section">
                            {!elevenLabsAvailable && (
                              <div className="text-center py-3 border border-dashed border-[#2A2A2A] rounded-lg">
                                <Lock size={14} className="mx-auto text-[#999] mb-1" />
                                <p className="text-[9px] text-[#999]">ElevenLabs not configured</p>
                              </div>
                            )}
                            {elevenLabsAvailable && elevenLabsVoices.length === 0 && (
                              <div className="text-center py-3">
                                <Loader2 size={14} className="mx-auto text-[#C9A84C] animate-spin mb-1" />
                                <p className="text-[9px] text-[#999]">{t('studio.loading_voices')}</p>
                              </div>
                            )}
                            {elevenLabsVoices.map(v => (
                              <div key={v.id} data-testid={`voice-el-${v.name.toLowerCase()}`}
                                className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition ${
                                  tempAvatar?.voice?.type === 'elevenlabs' && tempAvatar?.voice?.voice_id === v.id
                                    ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}
                                onClick={() => setTempAvatar(p => ({ ...p, voice: { type: 'elevenlabs', voice_id: v.id } }))}>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <p className="text-[10px] text-white font-medium">{v.name}</p>
                                    <Crown size={8} className="text-[#C9A84C] shrink-0" />
                                  </div>
                                  <p className="text-[8px] text-[#999] truncate">{v.style} · {v.accent} · {v.gender === 'female' ? '♀' : '♂'}</p>
                                </div>
                                <button onClick={e => { e.stopPropagation(); previewVoice(v.id, 'elevenlabs'); }}
                                  disabled={loadingVoicePreview === v.id}
                                  className="h-7 w-7 rounded-lg border border-[#2A2A2A] flex items-center justify-center hover:bg-[#1A1A1A] transition disabled:opacity-40">
                                  {loadingVoicePreview === v.id ? (
                                    <Loader2 size={10} className="animate-spin text-[#C9A84C]" />
                                  ) : playingVoiceId === v.id ? (
                                    <Volume2 size={10} className="text-[#C9A84C]" />
                                  ) : (
                                    <Play size={10} className="text-[#999]" />
                                  )}
                                </button>
                                {tempAvatar?.voice?.type === 'elevenlabs' && tempAvatar?.voice?.voice_id === v.id && (
                                  <Check size={12} className="text-[#C9A84C] shrink-0" />
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="flex items-center justify-center gap-3 py-4">
                              {isRecording ? (
                                <button data-testid="stop-recording-btn" onClick={stopRecording}
                                  className="h-16 w-16 rounded-full bg-red-500 flex items-center justify-center animate-pulse hover:bg-red-600 transition">
                                  <Square size={20} className="text-white" />
                                </button>
                              ) : (
                                <button data-testid="start-recording-btn" onClick={startRecording}
                                  className="h-16 w-16 rounded-full border-2 border-[#C9A84C]/40 bg-[#C9A84C]/10 flex items-center justify-center hover:bg-[#C9A84C]/20 transition">
                                  <Mic size={24} className="text-[#C9A84C]" />
                                </button>
                              )}
                            </div>
                            <p className="text-[9px] text-center text-[#999]">
                              {isRecording ? t('studio.recording_in_progress') : recordedAudioUrl ? t('studio.play_preview') : t('studio.record')}
                            </p>
                            {recordedAudioUrl && (
                              <div className="space-y-2">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-[8px] text-[#C9A84C] font-medium uppercase tracking-wider">
                                    {avatarExtractedAudio ? t('studio.original_voice') : t('studio.recorded_voice')}
                                  </span>
                                </div>
                                <audio src={recordedAudioUrl} controls className="w-full h-8" style={{ filter: 'invert(1) hue-rotate(180deg)' }} />
                                <div className="flex gap-1.5">
                                  <button data-testid="master-voice-btn" onClick={async () => {
                                    let voiceUrl = tempAvatar?.voice?.url || recordedAudioUrl;
                                    if (!voiceUrl) return;
                                    setMasteringVoice(true);
                                    try {
                                      // If still a blob URL, upload first
                                      if (voiceUrl.startsWith('blob:') && recordedAudioBlob) {
                                        const ext = recordedAudioBlob.type.includes('mp4') ? 'mp4' : 'webm';
                                        const form = new FormData();
                                        form.append('file', recordedAudioBlob, `recording.${ext}`);
                                        const uploadRes = await axios.post(`${API}/campaigns/pipeline/upload-voice-recording`, form);
                                        if (uploadRes.data.audio_url) {
                                          voiceUrl = uploadRes.data.audio_url;
                                          setRecordedAudioUrl(voiceUrl);
                                          setTempAvatar(p => ({ ...p, voice: { type: 'custom', url: voiceUrl } }));
                                        } else { throw new Error('Upload failed'); }
                                      }
                                      const { data } = await axios.post(`${API}/campaigns/pipeline/master-voice`, { audio_url: voiceUrl });
                                      if (data.audio_url) {
                                        setRecordedAudioUrl(data.audio_url);
                                        setTempAvatar(p => ({ ...p, voice: { ...p?.voice, url: data.audio_url, mastered: true } }));
                                        toast.success(t('studio.voice_mastered'));
                                      }
                                    } catch (e) { toast.error(t('studio.err_generic')); }
                                    setMasteringVoice(false);
                                  }}
                                    disabled={masteringVoice || tempAvatar?.voice?.mastered}
                                    className={`flex-1 rounded-lg border py-2 text-[9px] font-bold flex items-center justify-center gap-1.5 transition disabled:opacity-40 ${
                                      tempAvatar?.voice?.mastered ? 'border-[#10B981]/30 text-[#10B981] bg-[#10B981]/5' : 'border-[#C9A84C]/30 text-[#C9A84C] hover:bg-[#C9A84C]/5'}`}>
                                    {masteringVoice ? <><Loader2 size={10} className="animate-spin" /> {t('studio.mastering')}</> :
                                     tempAvatar?.voice?.mastered ? <><Check size={10} /> {t('studio.mastered')}</> :
                                     <><Sparkles size={10} /> {t('studio.master_voice')}</>}
                                  </button>
                                  <button data-testid="save-recording-btn" onClick={saveRecordingAsVoice}
                                    disabled={uploadingRecording}
                                    className="flex-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2 text-[9px] font-bold text-black flex items-center justify-center gap-1.5 disabled:opacity-50">
                                    {uploadingRecording ? (
                                      <><Loader2 size={10} className="animate-spin" /> {t('studio.uploading_recording')}</>
                                    ) : (
                                      <><Check size={10} /> {t('studio.use') || 'Use'}</>
                                    )}
                                  </button>
                                </div>
                              </div>
                            )}
                            {tempAvatar?.voice?.type === 'custom' && (
                              <div className="flex items-center gap-1.5 text-[9px] text-green-400">
                                <Check size={10} /> {t('studio.recording_saved')}
                              </div>
                            )}
                          </div>
                        )}
                        {/* No voice option */}
                        <button onClick={() => setTempAvatar(p => ({ ...p, voice: null }))}
                          className={`w-full rounded-lg border px-3 py-2 text-[9px] text-center transition ${
                            !tempAvatar?.voice ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:border-[#2A2A2A]'}`}>
                          {t('studio.no_voice')}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Video Preview Controls */}
              {avatarStage === 'customize' && tempAvatar?.url && (
                <div className="px-5 py-2 border-t border-[#151515]/50 shrink-0 space-y-2">
                  {/* Language Selector + Generate/Regenerate */}
                  <div className="flex items-center gap-2">
                    <span className="text-[8px] text-[#999] uppercase tracking-wider">{t('studio.test_language') || 'Language'}:</span>
                    <div className="flex gap-1">
                      {[{id:'pt',label:'PT'},{id:'en',label:'EN'},{id:'es',label:'ES'}].map(lang => (
                        <button key={lang.id} onClick={() => setPreviewLanguage(lang.id)}
                          className={`px-2 py-0.5 rounded text-[8px] font-bold transition ${
                            previewLanguage === lang.id ? 'bg-[#C9A84C]/20 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#999] border border-[#1E1E1E] hover:border-[#333]'}`}>
                          {lang.label}
                        </button>
                      ))}
                    </div>
                    {previewVideoUrl && (
                      <button onClick={() => { setPreviewVideoUrl(null); setAvatarMediaTab('photo'); }}
                        className="ml-auto text-[8px] text-[#C9A84C] hover:underline">{t('studio.regenerate') || 'Regenerate'}</button>
                    )}
                  </div>
                  <button data-testid="generate-preview-video-btn"
                    onClick={async () => {
                      setGeneratingPreviewVideo(true);
                      setAvatarMediaTab('video');
                      try {
                        const voice = tempAvatar?.voice;
                        const { data } = await axios.post(`${API}/campaigns/pipeline/avatar-video-preview`, {
                          avatar_url: tempAvatar.url,
                          voice_url: voice?.url || '',
                          voice_id: voice?.voice_id || '',
                          language: previewLanguage,
                        });
                        if (data.job_id) {
                          const pollInterval = setInterval(async () => {
                            try {
                              const { data: status } = await axios.get(`${API}/campaigns/pipeline/avatar-video-preview/${data.job_id}`);
                              if (status.status === 'completed' && status.video_url) {
                                clearInterval(pollInterval);
                                setPreviewVideoUrl(status.video_url);
                                setGeneratingPreviewVideo(false);
                                setAvatarMediaTab('video');
                                toast.success(t('studio.preview_generated'));
                              } else if (status.status === 'failed') {
                                clearInterval(pollInterval);
                                setGeneratingPreviewVideo(false);
                                setAvatarMediaTab('photo');
                                toast.error(status.error || t('studio.err_generic'));
                              }
                            } catch { /* keep polling */ }
                          }, 5000);
                        }
                      } catch (e) {
                        toast.error(t('studio.err_generic'));
                        setGeneratingPreviewVideo(false);
                        setAvatarMediaTab('photo');
                      }
                    }}
                    disabled={generatingPreviewVideo}
                    className="w-full rounded-lg border border-dashed border-[#C9A84C]/20 py-2 text-[9px] text-[#C9A84C] hover:bg-[#C9A84C]/5 transition flex items-center justify-center gap-1.5 disabled:opacity-40">
                    {generatingPreviewVideo ? <><Loader2 size={10} className="animate-spin" /> {t('studio.generating_preview')}</> :
                     previewVideoUrl ? <><Play size={10} /> {t('studio.regenerate_preview') || 'Regenerate Preview'}</> :
                     <><Play size={10} /> {t('studio.generate_video_preview')}</>}
                  </button>
                </div>
              )}

              {/* Footer */}
              {avatarStage === 'customize' && (
                <div className="px-5 py-3 border-t border-[#151515] shrink-0 flex gap-2">
                  {editingAvatarId ? (
                    <>
                      <button data-testid="save-avatar-as-new-btn" onClick={saveAvatarAsNew}
                        className="flex-1 rounded-lg border border-[#C9A84C]/40 py-2.5 text-xs font-bold text-[#C9A84C] hover:bg-[#C9A84C]/10 transition flex items-center justify-center gap-2">
                        <Plus size={14} /> {t('studio.save_as_new')}
                      </button>
                      <button data-testid="save-avatar-final-btn" onClick={saveAvatarAndClose}
                        className="flex-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-xs font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2">
                        <Check size={14} /> {t('studio.update_avatar')}
                      </button>
                    </>
                  ) : (
                    <button data-testid="save-avatar-final-btn" onClick={saveAvatarAndClose}
                      className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-xs font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2">
                      <Check size={14} /> {t('studio.save_avatar')}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Campaign Name */}
        <div>
          <label className="text-[9px] text-[#999] uppercase tracking-wider block mb-1">{t('studio.campaign_name')}</label>
          <input data-testid="pipeline-campaign-name" value={campaignName} onChange={e => setCampaignName(e.target.value)}
            placeholder={t('studio.campaign_name_placeholder')}
            className="w-full rounded-xl border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-xs text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
        </div>

        {/* Briefing */}
        <div>
          <label className="text-[9px] text-[#999] uppercase tracking-wider block mb-2">{t('studio.briefing_label')}</label>
          <div className="flex gap-1 mb-3 p-0.5 bg-[#0A0A0A] rounded-lg border border-[#1A1A1A] w-fit">
            <button data-testid="briefing-mode-free" onClick={() => setBriefingMode('free')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition ${briefingMode === 'free' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#999] hover:text-white'}`}>
              <FileText size={10} className="inline mr-1" />{t('studio.briefing_free')}
            </button>
            <button data-testid="briefing-mode-guided" onClick={() => setBriefingMode('guided')}
              className={`px-3 py-1.5 rounded-md text-[10px] font-medium transition ${briefingMode === 'guided' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#999] hover:text-white'}`}>
              <CheckCircle size={10} className="inline mr-1" />{t('studio.briefing_guided')}
            </button>
          </div>

          {briefingMode === 'free' ? (
            <div>
              <textarea data-testid="pipeline-briefing" value={briefing} onChange={e => setBriefing(e.target.value)} rows={4}
                placeholder={t('studio.briefing_placeholder')}
                className="w-full rounded-xl border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-xs text-white placeholder-[#666] outline-none resize-none focus:border-[#C9A84C]/30 transition" />
              {savedBriefings.length > 0 && (
                <div className="mt-2">
                  <p className="text-[8px] text-[#999] uppercase tracking-wider mb-1.5">{t('studio.previous_briefings') || 'Previous Briefings'}</p>
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {savedBriefings.map((sb, i) => (
                      <button key={i} onClick={() => {
                        setBriefing(sb.briefing);
                        if (sb.campaign_name && !campaignName) setCampaignName(sb.campaign_name);
                        if (sb.campaign_language) setCampaignLang(sb.campaign_language);
                        if (sb.platforms?.length) setPlatforms(sb.platforms);
                        toast.success(t('studio.briefing_loaded') || 'Briefing loaded!');
                      }}
                        className="w-full text-left rounded-lg border border-[#1E1E1E] bg-[#0D0D0D] px-3 py-2 hover:border-[#C9A84C]/30 transition group">
                        <div className="flex items-center gap-2 mb-0.5">
                          {sb.campaign_name && <span className="text-[10px] font-semibold text-white">{sb.campaign_name}</span>}
                          {sb.campaign_language && <span className="text-[8px] text-[#C9A84C] uppercase">{sb.campaign_language}</span>}
                          <span className="text-[7px] text-[#777] ml-auto group-hover:text-[#C9A84C]">{t('studio.use') || 'Use'}</span>
                        </div>
                        <p className="text-[9px] text-[#999] line-clamp-2">{sb.briefing}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3 bg-[#0A0A0A] rounded-xl border border-[#1A1A1A] p-3">
              <p className="text-[9px] text-[#C9A84C] font-medium mb-1">{t('studio.guided_intro')}</p>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">1. {t('studio.q_product')}</label>
                <input data-testid="q-product" value={questionnaire.product} onChange={e => setQuestionnaire(p => ({...p, product: e.target.value}))}
                  placeholder={t('studio.q_product_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">2. {t('studio.q_goal')}</label>
                <div className="flex flex-wrap gap-1.5 mb-1.5">
                  {[{k:'goal_leads'},{k:'goal_sales'},{k:'goal_awareness'},{k:'goal_engagement'},{k:'goal_launch'},{k:'goal_promo'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, goal: p.goal === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.goal === t(`studio.${k}`) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
                <input value={questionnaire.goal} onChange={e => setQuestionnaire(p => ({...p, goal: e.target.value}))}
                  placeholder={t('studio.q_goal_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">3. {t('studio.q_audience')}</label>

                {/* Gender */}
                <p className="text-[8px] text-[#999] mb-1 mt-1">{t('studio.q_gender') || 'Gender'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['All', 'Male', 'Female', 'LGBTQ+', 'Non-binary'].map(g => (
                    <button key={g} onClick={() => setQuestionnaire(p => ({...p, gender: p.gender === g ? '' : g}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.gender === g ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {g}
                    </button>
                  ))}
                </div>

                {/* Age Range */}
                <p className="text-[8px] text-[#999] mb-1">{t('studio.q_age_range') || 'Age range'}</p>
                <div className="flex items-center gap-1.5 mb-2">
                  <input data-testid="q-age-min" value={questionnaire.ageMin} onChange={e => setQuestionnaire(p => ({...p, ageMin: e.target.value}))}
                    placeholder="18" type="number" min="13" max="99"
                    className="w-16 rounded-md border border-[#1E1E1E] bg-[#111] px-2 py-1 text-[10px] text-white text-center placeholder-[#666] outline-none focus:border-[#C9A84C]/30" />
                  <span className="text-[9px] text-[#888]">—</span>
                  <input data-testid="q-age-max" value={questionnaire.ageMax} onChange={e => setQuestionnaire(p => ({...p, ageMax: e.target.value}))}
                    placeholder="65+" type="text"
                    className="w-16 rounded-md border border-[#1E1E1E] bg-[#111] px-2 py-1 text-[10px] text-white text-center placeholder-[#666] outline-none focus:border-[#C9A84C]/30" />
                  <div className="flex gap-1 ml-2">
                    {['13-17', '18-24', '25-34', '35-44', '45-54', '55+'].map(r => (
                      <button key={r} onClick={() => { const [min, max] = r.split('-'); setQuestionnaire(p => ({...p, ageMin: min, ageMax: max || '65+'})); }}
                        className={`rounded-md px-1.5 py-0.5 text-[8px] border transition ${questionnaire.ageMin === r.split('-')[0] ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                        {r}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Social Class */}
                <p className="text-[8px] text-[#999] mb-1">{t('studio.q_social_class') || 'Social class'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['A (Luxury)', 'B (Upper-middle)', 'C (Middle)', 'D (Lower-middle)', 'E (Low income)', 'All classes'].map(c => (
                    <button key={c} onClick={() => setQuestionnaire(p => ({...p, socialClass: p.socialClass === c ? '' : c}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.socialClass === c ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {c}
                    </button>
                  ))}
                </div>

                {/* Lifestyle / Interests */}
                <p className="text-[8px] text-[#999] mb-1">{t('studio.q_lifestyle') || 'Lifestyle & Interests'}</p>
                <div className="flex flex-wrap gap-1 mb-2">
                  {['Fitness', 'Tech', 'Fashion', 'Gaming', 'Travel', 'Food', 'Music', 'Sports', 'Business', 'Eco-friendly', 'Luxury', 'Family'].map(l => (
                    <button key={l} onClick={() => setQuestionnaire(p => ({...p, lifestyle: p.lifestyle?.includes(l) ? p.lifestyle.replace(l, '').replace(/,\s*,/g, ',').replace(/^,\s*|,\s*$/g, '') : (p.lifestyle ? `${p.lifestyle}, ${l}` : l)}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.lifestyle?.includes(l) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {l}
                    </button>
                  ))}
                </div>

                {/* Free-text audience */}
                <input data-testid="q-audience" value={questionnaire.audience} onChange={e => setQuestionnaire(p => ({...p, audience: e.target.value}))}
                  placeholder={t('studio.q_audience_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">4. {t('studio.q_tone')}</label>
                <div className="flex flex-wrap gap-1.5">
                  {[{k:'tone_professional'},{k:'tone_casual'},{k:'tone_urgent'},{k:'tone_inspiring'},{k:'tone_fun'},{k:'tone_sophisticated'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, tone: p.tone === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.tone === t(`studio.${k}`) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">5. {t('studio.q_offer')}</label>
                <input data-testid="q-offer" value={questionnaire.offer} onChange={e => setQuestionnaire(p => ({...p, offer: e.target.value}))}
                  placeholder={t('studio.q_offer_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">6. {t('studio.q_differentials')}</label>
                <input data-testid="q-differentials" value={questionnaire.differentials} onChange={e => setQuestionnaire(p => ({...p, differentials: e.target.value}))}
                  placeholder={t('studio.q_differentials_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">7. {t('studio.q_pain_points') || 'What problems does your audience face?'}</label>
                <input data-testid="q-pain-points" value={questionnaire.painPoints} onChange={e => setQuestionnaire(p => ({...p, painPoints: e.target.value}))}
                  placeholder={t('studio.q_pain_points_placeholder') || 'E.g.: High costs, lack of time, complexity...'}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">8. {t('studio.q_visual_style') || 'Visual style preference'}</label>
                <div className="flex flex-wrap gap-1">
                  {['Minimalist', 'Bold & Vibrant', 'Luxury & Elegant', 'Natural & Organic', 'Tech & Modern', 'Retro & Vintage', 'Dark & Moody', 'Playful & Colorful'].map(s => (
                    <button key={s} onClick={() => setQuestionnaire(p => ({...p, visualStyle: p.visualStyle === s ? '' : s}))}
                      className={`rounded-md px-2 py-0.5 text-[9px] border transition ${questionnaire.visualStyle === s ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">9. {t('studio.q_cta')}</label>
                <div className="flex flex-wrap gap-1.5">
                  {[{k:'cta_signup'},{k:'cta_demo'},{k:'cta_buy'},{k:'cta_learn'},{k:'cta_download'},{k:'cta_whatsapp'}].map(({k}) => (
                    <button key={k} onClick={() => setQuestionnaire(p => ({...p, cta: p.cta === t(`studio.${k}`) ? '' : t(`studio.${k}`)}))}
                      className={`rounded-lg px-2.5 py-1 text-[10px] border transition ${questionnaire.cta === t(`studio.${k}`) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                      {t(`studio.${k}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-[9px] text-[#999] block mb-1">10. {t('studio.q_urgency')}</label>
                <input data-testid="q-urgency" value={questionnaire.urgency} onChange={e => setQuestionnaire(p => ({...p, urgency: e.target.value}))}
                  placeholder={t('studio.q_urgency_placeholder')}
                  className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[11px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition" />
              </div>

              {compileBriefing().trim() && (
                <div className="mt-2 p-2.5 rounded-lg bg-[#111] border border-[#1A1A1A]">
                  <p className="text-[8px] text-[#999] uppercase tracking-wider mb-1">{t('studio.briefing_preview')}</p>
                  <pre className="text-[10px] text-[#999] whitespace-pre-wrap font-sans leading-relaxed">{compileBriefing()}</pre>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Campaign Language */}
        <div>
          <label className="text-[9px] text-[#999] uppercase tracking-wider block mb-1">{t('studio.campaign_language')}</label>
          <p className="text-[8px] text-[#888] mb-1.5">{t('studio.campaign_language_desc')}</p>
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
                className={`rounded-lg px-3 py-1.5 text-[10px] font-medium border transition flex items-center gap-1.5 ${campaignLang === lang.code ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                <span className="text-sm">{lang.flag}</span> {lang.label}
              </button>
            ))}
            <input value={campaignLang && !['', 'pt', 'en', 'es', 'fr', 'ht'].includes(campaignLang) ? campaignLang : ''}
              onChange={e => setCampaignLang(e.target.value)}
              placeholder="Other language..."
              className="rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-1.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 transition w-32" />
          </div>
        </div>

        {/* Brand Data Toggle */}
        {activeCompany && (
          <div data-testid="brand-data-toggle">
            <button data-testid="brand-data-btn" onClick={() => setApplyBrandData(!applyBrandData)}
              className={`w-full rounded-xl border px-3 py-2.5 flex items-center gap-3 transition ${
                applyBrandData ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <div className={`h-4 w-4 rounded border flex items-center justify-center shrink-0 transition ${
                applyBrandData ? 'bg-[#C9A84C] border-[#C9A84C]' : 'border-[#555]'}`}>
                {applyBrandData && <Check size={10} className="text-black" />}
              </div>
              {activeCompany.logo_url ? (
                <img src={resolveImageUrl(activeCompany.logo_url)} alt="" className="h-8 w-8 rounded-lg object-cover border border-[#1E1E1E] shrink-0" />
              ) : (
                <div className="h-8 w-8 rounded-lg bg-[#1A1A1A] border border-[#1E1E1E] flex items-center justify-center shrink-0">
                  <Building2 size={12} className="text-[#999]" />
                </div>
              )}
              <div className="flex-1 min-w-0 text-left">
                <p className="text-[9px] text-white font-medium truncate">{activeCompany.name}</p>
                <p className="text-[7px] text-[#999] truncate">
                  {[activeCompany.phone, activeCompany.website_url].filter(Boolean).join(' · ') || t('studio.brand_no_extra_info')}
                </p>
              </div>
              <span className="text-[8px] text-[#999] uppercase tracking-wider shrink-0">{t('studio.apply_brand')}</span>
            </button>
            {applyBrandData && (
              <p className="text-[7px] text-[#C9A84C]/50 mt-1 px-1">{t('studio.brand_applied_hint')}</p>
            )}
          </div>
        )}

        {/* Product Images: Exact + Reference */}
        <AssetUploader assets={uploadedAssets} onAssetsChange={setUploadedAssets} />

        {/* Music Library - Compact with Genre Tabs */}
        {musicLibrary.length > 0 && (
          <div>
            <label className="text-[9px] text-[#999] uppercase tracking-wider block mb-1.5">{t('studio.music_library') || 'Background Music (Video)'}</label>
            {/* Genre Tabs */}
            <div className="flex gap-1 flex-wrap mb-1.5">
              {['All', ...new Set(musicLibrary.map(t => t.category || 'General'))].map(cat => (
                <button key={cat} onClick={() => setMusicGenre(cat)}
                  className={`rounded-md px-2 py-0.5 text-[8px] border transition ${musicGenre === cat ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C] font-semibold' : 'border-[#1A1A1A] text-[#999] hover:text-white'}`}>
                  {cat}
                </button>
              ))}
            </div>
            {/* Scrollable Track List */}
            <div className="max-h-[160px] overflow-y-auto space-y-0.5 pr-1" style={{scrollbarWidth:'thin', scrollbarColor:'#333 transparent'}}>
              {(musicGenre === 'All' ? musicLibrary : musicLibrary.filter(t => (t.category || 'General') === musicGenre)).map(track => (
                <div key={track.id} data-testid={`music-${track.id}`}
                  onClick={() => setSelectedMusic(selectedMusic === track.id ? '' : track.id)}
                  className={`flex items-center gap-1.5 rounded-md border px-2 py-1 cursor-pointer transition ${selectedMusic === track.id ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1A1A1A] hover:border-[#2A2A2A]'}`}>
                  <button
                    onClick={(e) => { e.stopPropagation(); togglePlayTrack(track.id); }}
                    className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 transition ${playingTrack === track.id ? 'bg-[#C9A84C] text-black' : 'bg-[#1A1A1A] text-[#888] hover:text-white'}`}>
                    {playingTrack === track.id ? <span className="text-[5px] font-bold">||</span> : <Play size={7} />}
                  </button>
                  <span className="text-[8px] font-medium text-white truncate flex-1">{track.name}</span>
                  <span className="text-[7px] text-[#888] truncate max-w-[100px] hidden sm:block">{track.description}</span>
                  {selectedMusic === track.id && <Check size={9} className="text-[#C9A84C] shrink-0" />}
                </div>
              ))}
            </div>
            {selectedMusic && (
              <p className="text-[8px] text-[#C9A84C] flex items-center gap-1 mt-0.5">
                <Check size={8} /> {t('studio.music_selected') || 'Music selected for video'}
              </p>
            )}
            {!selectedMusic && (
              <p className="text-[8px] text-[#888] mt-0.5">{t('studio.music_auto') || 'No selection = AI picks automatically based on campaign mood'}</p>
            )}
          </div>
        )}



        {/* Platforms */}
        <div>
          <label className="text-[9px] text-[#999] uppercase tracking-wider block mb-1.5">{t('studio.platforms')}</label>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.filter(p => !p.parent).map(p => (
              <button key={p.id} data-testid={`platform-${p.id}`} onClick={() => togglePlatform(p.id)}
                className={`rounded-lg px-3 py-1.5 text-[11px] font-medium border transition ${platforms.includes(p.id) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Video Mode */}
        <div>
          <label className="text-[9px] text-[#999] uppercase tracking-wider flex items-center gap-1 mb-1.5">
            <Film size={10} /> {t('studio.video_mode')}
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            <button data-testid="video-mode-none" onClick={() => { setSkipVideo(true); setVideoMode('none'); }}
              className={`rounded-xl border p-2 text-center transition ${skipVideo ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <X size={14} className={`mx-auto mb-1 ${skipVideo ? 'text-[#C9A84C]' : 'text-[#999]'}`} />
              <p className="text-[9px] font-semibold text-white">{t('studio.no_video')}</p>
              <p className="text-[7px] text-[#999]">{t('studio.faster')}</p>
            </button>
            <button data-testid="video-mode-narration" onClick={() => { setSkipVideo(false); setVideoMode('narration'); }}
              className={`rounded-xl border p-2 text-center transition ${!skipVideo && videoMode === 'narration' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <MessageSquare size={14} className={`mx-auto mb-1 ${!skipVideo && videoMode === 'narration' ? 'text-[#C9A84C]' : 'text-[#999]'}`} />
              <p className="text-[9px] font-semibold text-white">{t('studio.narration')}</p>
              <p className="text-[7px] text-[#999]">{t('studio.voice_scenes')}</p>
            </button>
            <button data-testid="video-mode-presenter" onClick={() => { setSkipVideo(false); setVideoMode('presenter'); }}
              className={`rounded-xl border p-2 text-center transition ${!skipVideo && videoMode === 'presenter' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <Eye size={14} className={`mx-auto mb-1 ${!skipVideo && videoMode === 'presenter' ? 'text-[#C9A84C]' : 'text-[#999]'}`} />
              <p className="text-[9px] font-semibold text-white">{t('studio.presenter')}</p>
              <p className="text-[7px] text-[#999]">{t('studio.talking_avatar')}</p>
            </button>
          </div>
          {!skipVideo && videoMode === 'presenter' && !selectedAvatar && (
            <p className="text-[8px] text-amber-400/80 mt-1.5 flex items-center gap-1">
              <AlertTriangle size={9} /> {t('studio.presenter_warning')}
            </p>
          )}
        </div>

        {/* Mode */}
        <div>
          <label className="text-[9px] text-[#999] uppercase tracking-wider block mb-1.5">{t('studio.execution_mode')}</label>
          <div className="grid grid-cols-2 gap-2">
            <button data-testid="mode-semi-auto" onClick={() => setMode('semi_auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'semi_auto' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <p className="text-xs font-semibold text-white mb-0.5">{t('studio.mode_semi')}</p>
              <p className="text-[9px] text-[#999]">{t('studio.mode_semi_desc')}</p>
            </button>
            <button data-testid="mode-auto" onClick={() => setMode('auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'auto' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <p className="text-xs font-semibold text-white mb-0.5">{t('studio.mode_auto')}</p>
              <p className="text-[9px] text-[#999]">{t('studio.mode_auto_desc')}</p>
            </button>
          </div>
        </div>

        {/* Previous Pipelines */}
        {pipelines.length > 0 && (
          <div>
            <button onClick={() => setShowHistory(!showHistory)} data-testid="toggle-history"
              className="text-[9px] text-[#C9A84C] hover:underline flex items-center gap-1">
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
