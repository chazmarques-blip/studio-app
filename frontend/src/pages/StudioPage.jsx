import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { v4 as uuidv4 } from 'uuid';
import { 
  Film, Plus, Trash2, Clock, Layers, Users, Play, Folder, 
  ChevronRight, MoreHorizontal, Search, ArrowLeft, Eye,
  FileText, Palette, Video, CheckCircle2, Circle, Sparkles, Pencil, Check, X, BookOpen
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { DirectedStudio } from '../components/DirectedStudio';
import { AvatarModal } from '../components/pipeline/AvatarModal';
import { AvatarLibraryModalV2 } from '../components/pipeline/AvatarLibraryModalV2';
import { NewProjectModal } from '../components/NewProjectModal';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── Progress Steps ── */
const STEPS = [
  { key: 'script', label: 'Roteiro', icon: FileText },
  { key: 'characters', label: 'Personagens', icon: Users },
  { key: 'dialogues', label: 'Diálogos', icon: Palette },
  { key: 'storyboard', label: 'Storyboard', icon: Layers },
  { key: 'production', label: 'Produção', icon: Video },
];

function getProjectProgress(project) {
  if (!project) return { completed: 0, total: 5, steps: [] };
  
  // Corrigir: Usar campos corretos do projeto
  const hasScript = !!(project.briefing || project.book_title || project.synopsis || project.script);
  const hasCharacters = (project.characters?.length || 0) > 0;
  const hasScenes = (project.scenes?.length || 0) > 0;
  const hasStoryboard = (project.storyboard_panels?.length || 0) > 0 || 
                        project.outputs?.some(o => o.type === 'keyframe' || o.type === 'image');
  const hasVideos = project.outputs?.some(o => o.type === 'video') || 
                    (project.scene_videos?.length || 0) > 0;
  
  const steps = [
    { ...STEPS[0], done: hasScript },
    { ...STEPS[1], done: hasCharacters },
    { ...STEPS[2], done: hasScenes }, // Diálogos estão nas cenas
    { ...STEPS[3], done: hasStoryboard },
    { ...STEPS[4], done: hasVideos },
  ];
  
  const completed = steps.filter(s => s.done).length;
  
  return {
    completed,
    total: steps.length,
    steps,
    percent: Math.round((completed / steps.length) * 100)
  };
}

/* ── Unified Project Row ── */
function ProjectRow({ project, onSelect, onDelete, onRename }) {
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(project.name || '');
  const [videoThumbnail, setVideoThumbnail] = useState(null);
  const inputRef = useRef(null);
  const videoRef = useRef(null);
  
  // Corrigir: Buscar thumbnail do primeiro vídeo ou primeiro output
  const firstVideo = project.outputs?.find(o => o.type === 'video');
  const firstImage = project.outputs?.find(o => o.type === 'keyframe' || o.type === 'image');
  const thumbnail = firstVideo?.url || firstImage?.url || project.book_cover_url;
  const progress = getProjectProgress(project);
  const updatedAt = project.updated_at ? new Date(project.updated_at) : null;
  const scenesCount = project.scenes?.length || 0;
  const charactersCount = project.characters?.length || 0;
  
  // Extrair thumbnail do vídeo (primeiro frame)
  useEffect(() => {
    if (firstVideo?.url && !firstImage && !videoThumbnail) {
      const video = document.createElement('video');
      video.crossOrigin = 'anonymous';
      video.src = resolveImageUrl(firstVideo.url);
      video.currentTime = 1; // Pegar frame em 1 segundo
      
      video.addEventListener('loadeddata', () => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);
        setVideoThumbnail(canvas.toDataURL('image/jpeg', 0.7));
      });
    }
  }, [firstVideo, firstImage, videoThumbnail]);
  
  const formatDate = (date) => {
    if (!date) return '';
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    if (days === 0) return 'Hoje';
    if (days === 1) return 'Ontem';
    if (days < 7) return `${days} dias atrás`;
    return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
  };

  const handleStartEdit = (e) => {
    e.stopPropagation();
    setEditName(project.name || '');
    setIsEditing(true);
    setTimeout(() => inputRef.current?.focus(), 50);
  };

  const handleSaveEdit = async (e) => {
    e?.stopPropagation();
    if (editName.trim() && editName !== project.name) {
      await onRename(project, editName.trim());
    }
    setIsEditing(false);
  };

  const handleCancelEdit = (e) => {
    e?.stopPropagation();
    setEditName(project.name || '');
    setIsEditing(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSaveEdit(e);
    if (e.key === 'Escape') handleCancelEdit(e);
  };

  return (
    <div 
      onClick={() => !isEditing && onSelect(project)}
      className="group relative flex items-center gap-5 p-4 rounded-xl border border-gray-200 bg-white hover:border-orange-500/30 hover:bg-[#0F0F0F] cursor-pointer transition-all"
    >
      {/* Thumbnail */}
      <div className="relative w-20 h-20 rounded-lg bg-gradient-to-br from-[#1A1A1A] to-[#0A0A0A] overflow-hidden shrink-0">
        {videoThumbnail ? (
          <img src={videoThumbnail} alt="" className="w-full h-full object-cover" />
        ) : thumbnail ? (
          <img src={resolveImageUrl(thumbnail)} alt="" className="w-full h-full object-cover" />
        ) : (
          <div className="flex items-center justify-center h-full">
            <Film size={24} className="text-gray-400" />
          </div>
        )}
        {firstVideo && (
          <div className="absolute bottom-1 right-1 bg-black/60 backdrop-blur-sm rounded px-1.5 py-0.5">
            <Video size={10} className="text-gray-900" />
          </div>
        )}
      </div>

      {/* Project Info */}
      <div className="flex-1 min-w-0">
        {/* Editable Name */}
        <div className="flex items-center gap-2 mb-1">
          {isEditing ? (
            <div className="flex items-center gap-1 flex-1" onClick={e => e.stopPropagation()}>
              <input
                ref={inputRef}
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 px-2 py-1 rounded bg-gray-100 border border-orange-500 text-sm text-gray-900 outline-none"
              />
              <button onClick={handleSaveEdit} className="p-1 rounded hover:bg-white/10 text-emerald-400">
                <Check size={14} />
              </button>
              <button onClick={handleCancelEdit} className="p-1 rounded hover:bg-white/10 text-red-400">
                <X size={14} />
              </button>
            </div>
          ) : (
            <>
              <h3 className="text-sm font-semibold text-gray-900 truncate group-hover:text-[#A78BFA] transition-colors">
                {project.name}
              </h3>
              <button 
                onClick={handleStartEdit}
                className="p-1 rounded hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Pencil size={12} className="text-gray-900/70" />
              </button>
            </>
          )}
        </div>
        
        {/* Stats Row - CORES MAIS CLARAS */}
        <div className="flex items-center gap-4 text-xs text-gray-900/70 mb-3">
          <span className="flex items-center gap-1.5">
            <Layers size={13} className="text-gray-900/60" /> {scenesCount} cenas
          </span>
          <span className="flex items-center gap-1.5">
            <Users size={13} className="text-gray-900/60" /> {charactersCount} personagens
          </span>
          {updatedAt && (
            <span className="flex items-center gap-1.5">
              <Clock size={13} className="text-gray-900/60" /> {formatDate(updatedAt)}
            </span>
          )}
        </div>

        {/* Progress Steps - Mini - CORES MAIS CLARAS */}
        <div className="flex items-center gap-1.5">
          {progress.steps.map((step, i) => (
            <div 
              key={step.key}
              className={`flex items-center justify-center w-6 h-6 rounded-md ${
                step.done 
                  ? 'bg-[#8B5CF6]/30 text-[#A78BFA]' 
                  : 'bg-gray-100 text-gray-900/40'
              }`}
              title={step.label}
            >
              <step.icon size={12} />
            </div>
          ))}
          <span className="ml-2 text-xs text-gray-900/60">
            {progress.completed}/{progress.total}
          </span>
        </div>
      </div>

      {/* Progress Circle */}
      <div className="shrink-0 flex flex-col items-center gap-1.5">
        <div className="relative w-12 h-12">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 48 48">
            <circle cx="24" cy="24" r="20" fill="none" stroke="#1A1A1A" strokeWidth="3" />
            <circle 
              cx="24" cy="24" r="20" fill="none" 
              stroke={progress.percent === 100 ? '#4ADE80' : '#8B5CF6'} 
              strokeWidth="3"
              strokeDasharray={`${progress.percent * 1.26} 126`}
              strokeLinecap="round"
            />
          </svg>
          <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-gray-900">
            {progress.percent}%
          </span>
        </div>
        <span className={`text-[10px] font-medium ${
          progress.percent === 100 ? 'text-emerald-400' : 'text-gray-900/60'
        }`}>
          {progress.percent === 100 ? 'Concluído' : 'Em progresso'}
        </span>
      </div>

      {/* Actions */}
      <div className="shrink-0 flex items-center gap-3">
        <button 
          onClick={(e) => { e.stopPropagation(); onSelect(project); }}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#8B5CF6]/20 text-[#A78BFA] text-xs font-semibold hover:bg-[#8B5CF6]/30 transition"
        >
          <Play size={13} /> Abrir
        </button>
        
        {/* Menu */}
        <div className="relative">
          <button 
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
            className="p-2 rounded-lg hover:bg-white/10 transition"
          >
            <MoreHorizontal size={16} className="text-gray-900/60" />
          </button>
          
          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={(e) => { e.stopPropagation(); setShowMenu(false); }} />
              <div className="absolute right-0 top-full mt-1 z-20 rounded-lg border border-[#2A2A2A] bg-gray-50 shadow-xl py-1.5 min-w-[160px]">
                {!project.v2_migrated && (
                  <button 
                    onClick={(e) => { 
                      e.stopPropagation(); 
                      setShowMenu(false);
                      // Will be handled in parent
                      if (window.onUpgradeToV2) window.onUpgradeToV2(project);
                    }}
                    className="w-full px-4 py-2 text-left text-sm text-[#8B5CF6] hover:bg-[#8B5CF6]/10 flex items-center gap-2 border-b border-[#2A2A2A] mb-1"
                  >
                    <Sparkles size={14} /> Upgrade to V2
                  </button>
                )}
                <button 
                  onClick={(e) => { e.stopPropagation(); handleStartEdit(e); setShowMenu(false); }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-900 hover:bg-white/5 flex items-center gap-2"
                >
                  <Pencil size={14} /> Renomear
                </button>
                <button 
                  onClick={(e) => { 
                    e.stopPropagation(); 
                    e.preventDefault();
                    setShowMenu(false); 
                    onDelete(project); 
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                >
                  <Trash2 size={14} /> Excluir
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function StudioPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { i18n } = useTranslation();
  const lang = i18n.language?.startsWith('pt') ? 'pt' : i18n.language?.startsWith('es') ? 'es' : 'en';

  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  
  // Global Character Library
  const [showGlobalLibrary, setShowGlobalLibrary] = useState(false);
  
  // Company selection (duplicated from Marketing for Videos context)
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [showCompanySelector, setShowCompanySelector] = useState(false);
  
  // ═══════ AVATAR MODAL - COMPLETE STATES (copied from PipelineView) ═══════
  const [avatars, setAvatars] = useState([]);
  const [selectedAvatarId, setSelectedAvatarId] = useState(null);
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [avatarSourcePhoto, setAvatarSourcePhoto] = useState(null);
  const [avatarSourceType, setAvatarSourceType] = useState('video');
  const [avatarVideoUploading, setAvatarVideoUploading] = useState(false);
  const [avatarExtractedAudio, setAvatarExtractedAudio] = useState(null);
  const [avatarVideoFrames, setAvatarVideoFrames] = useState([]);
  const [masteringVoice, setMasteringVoice] = useState(false);
  const [generatingPreviewVideo, setGeneratingPreviewVideo] = useState(false);
  const [previewVideoUrl, setPreviewVideoUrl] = useState(null);
  const [previewLanguage, setPreviewLanguage] = useState('pt');
  const [avatarName, setAvatarName] = useState('');
  const [avatarMediaTab, setAvatarMediaTab] = useState('photo');
  const [accuracyProgress, setAccuracyProgress] = useState(null);
  const [generatingAvatar, setGeneratingAvatar] = useState(false);
  const [avatarPhotoUploading, setAvatarPhotoUploading] = useState(false);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState(null);
  const [logoUploading, setLogoUploading] = useState(false);
  const [avatarStage, setAvatarStage] = useState('upload');
  const [avatarCreationMode, setAvatarCreationMode] = useState('photo');
  const [avatarPromptText, setAvatarPromptText] = useState('');
  const [avatarPromptGender, setAvatarPromptGender] = useState('female');
  const [avatarPromptStyle, setAvatarPromptStyle] = useState('custom');
  const [tempAvatar, setTempAvatar] = useState(null);
  const [editingAvatarId, setEditingAvatarId] = useState(null);
  const [customizeTab, setCustomizeTab] = useState('clothing');
  const [applyingClothing, setApplyingClothing] = useState(false);
  const [clothingVariants, setClothingVariants] = useState({});
  const [generatingAngle, setGeneratingAngle] = useState(null);
  const [angleImages, setAngleImages] = useState({});
  const [auto360Progress, setAuto360Progress] = useState(null);
  const [voiceTab, setVoiceTab] = useState('bank');
  const [loadingVoicePreview, setLoadingVoicePreview] = useState(null);
  const [playingVoiceId, setPlayingVoiceId] = useState(null);
  const [elevenLabsVoices, setElevenLabsVoices] = useState([]);
  const [elevenLabsAvailable, setElevenLabsAvailable] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState(null);
  const [recordedAudioBlob, setRecordedAudioBlob] = useState(null);
  const [uploadingRecording, setUploadingRecording] = useState(false);
  const [avatarEditHistory, setAvatarEditHistory] = useState([]);
  const [avatarBaseUrl, setAvatarBaseUrl] = useState(null);
  const [lastCreatedAvatar, setLastCreatedAvatar] = useState(null);
  
  // AI Avatar editing
  const [aiEditAvatarId, setAiEditAvatarId] = useState(null);
  const [aiEditInstruction, setAiEditInstruction] = useState('');
  const [aiEditLoading, setAiEditLoading] = useState(false);
  
  // Refs
  const avatarInputRef = useRef(null);
  const logoInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioPlayerRef = useRef(null);

  // ═══════ AVATAR MODAL - HELPER FUNCTIONS ═══════
  const resetAvatarModal = () => {
    setShowAvatarModal(false);
    setAvatarSourcePhoto(null);
    setAvatarVideoUploading(false);
    setAvatarExtractedAudio(null);
    setAvatarVideoFrames([]);
    setGeneratingAvatar(false);
    setAvatarPhotoUploading(false);
    setAvatarName('');
    setAvatarStage('upload');
    setTempAvatar(null);
    setEditingAvatarId(null);
    setAngleImages({});
    setClothingVariants({});
    setCustomizeTab('clothing');
    setAvatarCreationMode('photo');
    setAvatarPromptText('');
    setAvatarPromptGender('female');
    setAvatarPromptStyle('custom');
    setVoiceTab('bank');
    setRecordedAudioUrl(null);
    setRecordedAudioBlob(null);
    setPreviewVideoUrl(null);
    setMasteringVoice(false);
    setGeneratingPreviewVideo(false);
    setAvatarEditHistory([]);
    setAvatarBaseUrl(null);
  };
  
  const openAvatarForEdit = (av) => {
    setEditingAvatarId(av.id);
    let inferredStyle = av.avatar_style || 'realistic';
    if (!av.avatar_style && av.creation_mode === '3d') {
      inferredStyle = '3d_pixar';
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
    const savedAngles = av.angles || {};
    if (is3dAvatar && savedAngles.front && savedAngles.front !== av.url) {
      setAngleImages({ front: av.url });
    } else {
      setAngleImages(savedAngles.front ? savedAngles : { front: av.url });
    }
    setPreviewLanguage(av.language || 'pt');
    if (av.voice?.url) {
      setRecordedAudioUrl(av.voice.url);
      setVoiceTab('record');
    } else if (av.voice?.type === 'elevenlabs' && av.voice?.voice_id) {
      setVoiceTab('premium');
    } else if (av.voice?.voice_id) {
      setVoiceTab('bank');
    }
    const variants = {};
    if (av.clothing && av.url) variants[av.clothing] = av.url;
    setClothingVariants(variants);
    setAvatarStage('customize');
    setAvatarCreationMode(av.creation_mode || 'photo');
    setAvatarPromptStyle(inferredStyle);
    setAvatarEditHistory(av.edit_history || []);
    setAvatarBaseUrl(av.url);
    setShowAvatarModal(true);
  };
  
  const handleEditAvatar = useCallback((av) => {
    console.log('🔧 handleEditAvatar chamado:', av);
    openAvatarForEdit(av);
  }, []);
  
  const handleAddAvatar = useCallback(() => {
    console.log('➕ handleAddAvatar chamado');
    resetAvatarModal();
    setShowAvatarModal(true);
  }, []);
  
  const handleRemoveAvatar = useCallback((av) => {
    console.log('🗑️ handleRemoveAvatar chamado:', av);
  }, []);
  
  const handlePreviewAvatar = useCallback((url) => {
    console.log('🔍 handlePreviewAvatar chamado:', url);
    setAvatarPreviewUrl(url);
  }, []);
  
  const handleAiEditAvatar = useCallback((id) => {
    console.log('🤖 handleAiEditAvatar chamado:', id);
    setAiEditAvatarId(id);
  }, []);

  const L = {
    pt: {
      title: 'Estúdio',
      subtitle: 'Seus projetos de vídeo',
      projects: 'Projetos',
      newProject: 'Novo Projeto',
      noProjects: 'Nenhum projeto ainda',
      createFirst: 'Crie seu primeiro projeto de vídeo com IA',
      deleteConfirm: 'Tem certeza que deseja excluir este projeto?',
      deleted: 'Projeto excluído',
      created: 'Projeto criado',
      renamed: 'Projeto renomeado',
      search: 'Buscar projeto...',
      back: 'Voltar',
    },
    en: {
      title: 'Studio',
      subtitle: 'Your video projects',
      projects: 'Projects',
      newProject: 'New Project',
      noProjects: 'No projects yet',
      createFirst: 'Create your first AI video project',
      deleteConfirm: 'Are you sure you want to delete this project?',
      deleted: 'Project deleted',
      created: 'Project created',
      renamed: 'Project renamed',
      search: 'Search project...',
      back: 'Back',
    },
    es: {
      title: 'Estudio',
      subtitle: 'Tus proyectos de video',
      projects: 'Proyectos',
      newProject: 'Nuevo Proyecto',
      noProjects: 'Sin proyectos aún',
      createFirst: 'Crea tu primer proyecto de video con IA',
      deleteConfirm: '¿Estás seguro de que quieres eliminar este proyecto?',
      deleted: 'Proyecto eliminado',
      created: 'Proyecto creado',
      renamed: 'Proyecto renombrado',
      search: 'Buscar proyecto...',
      back: 'Volver',
    },
  };
  const l = L[lang] || L.en;

  // Fetch projects
  const fetchProjects = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/studio/projects`);
      const projectsList = Array.isArray(data) ? data : data?.projects || [];
      setProjects(projectsList);
      
      // Auto-select project from URL
      const projectId = searchParams.get('project');
      if (projectId) {
        const found = projectsList.find(p => p.id === projectId);
        if (found) setSelectedProject(found);
      }
    } catch (err) {
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Fetch companies (shared with Marketing context)
  const fetchCompanies = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/data/companies`);
      setCompanies(res.data || []);
      // Auto-select primary company
      const primary = (res.data || []).find(c => c.is_primary);
      if (primary) setSelectedCompany(primary);
    } catch (err) {
      console.error('Error fetching companies:', err);
    }
  }, []);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  // Create new project
  const handleCreateProject = async (projectData) => {
    setCreating(true);
    try {
      const { data } = await axios.post(`${API}/studio/projects`, projectData);
      toast.success(l.created);
      setShowNewProjectModal(false);
      await fetchProjects();
      setSelectedProject(data);
      setSearchParams({ project: data.id });
    } catch (err) {
      toast.error('Erro ao criar projeto');
    } finally {
      setCreating(false);
    }
  };
  
  // Open new project modal
  const openNewProjectModal = () => {
    setShowNewProjectModal(true);
  };

  // Delete project
  const handleDeleteProject = async (project) => {
    console.log('🗑️ handleDeleteProject called with:', project);
    
    const confirmDelete = window.confirm(l.deleteConfirm || `Tem certeza que deseja excluir "${project.name}"?`);
    if (!confirmDelete) {
      console.log('⚠️ Delete cancelled by user');
      return;
    }
    
    try {
      console.log('🗑️ Deletando projeto:', project.id, project.name);
      console.log('📡 DELETE request to:', `${API}/studio/projects/${project.id}`);
      
      const response = await axios.delete(`${API}/studio/projects/${project.id}`);
      console.log('✅ DELETE response:', response.data);
      
      toast.success(l.deleted || 'Projeto excluído com sucesso!');
      
      // Se o projeto deletado está selecionado, voltar para lista
      if (selectedProject?.id === project.id) {
        setSelectedProject(null);
        setSearchParams({});
      }
      
      // Recarregar lista
      await fetchProjects();
      console.log('✅ Projeto deletado e lista recarregada');
    } catch (err) {
      console.error('❌ Erro ao excluir projeto:', err);
      console.error('❌ Error details:', {
        status: err.response?.status,
        data: err.response?.data,
        message: err.message
      });
      toast.error('Erro ao excluir projeto: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Upgrade project to V2
  const handleUpgradeToV2 = async (project) => {
    if (!window.confirm(`Atualizar "${project.name}" para V2?\n\nIsso vai adicionar:\n✅ Dialogue Timeline (sincronização)\n✅ Camera Plan (DoP)\n✅ Multi-formato\n\nNão vai regenerar vídeos existentes.`)) {
      return;
    }
    
    try {
      toast.loading('Atualizando projeto...', { id: 'upgrade' });
      
      await axios.post(`${API}/studio/projects/${project.id}/migrate-to-v2`, {});
      
      toast.success('Projeto atualizado para V2! Dialogue timeline e camera plan em progresso.', { id: 'upgrade' });
      
      // Reload after 2 seconds
      setTimeout(() => fetchProjects(), 2000);
    } catch (error) {
      console.error('Erro ao atualizar projeto:', error);
      toast.error('Erro ao atualizar projeto', { id: 'upgrade' });
    }
  };
  
  // Set global handler for ProjectRow
  useEffect(() => {
    window.onUpgradeToV2 = handleUpgradeToV2;
    return () => {
      window.onUpgradeToV2 = null;
    };
  }, [handleUpgradeToV2]);

  // Rename project
  const handleRenameProject = async (project, newName) => {
    try {
      await axios.patch(`${API}/studio/projects/${project.id}`, { name: newName });
      toast.success(l.renamed);
      await fetchProjects();
    } catch (err) {
      toast.error('Erro ao renomear projeto');
    }
  };

  // Select project - CORRIGIDO
  const handleSelectProject = (project) => {
    setSelectedProject(project);
    setSearchParams({ project: project.id });
  };

  // Back to list
  const handleBackToList = () => {
    setSelectedProject(null);
    setSearchParams({});
  };

  // Filter projects
  const filteredProjects = projects.filter(p => 
    p.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#8B5CF6]" />
      </div>
    );
  }

  // If project is selected, show DirectedStudio
  if (selectedProject) {
    return (
      <>
      <div className="flex flex-col min-h-screen bg-gray-50">
        {/* ═══ NAVBAR ═══ */}
        <nav className="shrink-0 bg-gray-50/95 backdrop-blur-xl border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
            <div className="flex items-center justify-between h-16">
              {/* Left: Back + Project Info */}
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <button 
                  onClick={handleBackToList}
                  className="flex items-center gap-2 text-gray-900/70 hover:text-gray-900 transition group shrink-0"
                >
                  <ArrowLeft size={20} className="group-hover:-translate-x-1 transition" />
                  <span className="text-sm font-medium hidden sm:inline">Projetos</span>
                </button>
                
                <div className="h-8 w-px bg-gray-100 shrink-0" />
                
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#8B5CF6] to-[#7C3AED] shrink-0">
                    <Film size={18} className="text-gray-900" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h1 className="text-base font-bold text-gray-900 truncate">
                      {selectedProject.name || 'Sem título'}
                    </h1>
                    <p className="text-xs text-gray-900/50">
                      {selectedProject.scenes?.length || 0} cenas • {selectedProject.characters?.length || 0} personagens
                    </p>
                  </div>
                </div>
              </div>

              {/* Right: Quick Actions */}
              <div className="flex items-center gap-2 shrink-0 ml-4">
                <button 
                  className="p-2 rounded-lg hover:bg-gray-100 transition text-gray-900/70 hover:text-gray-900"
                  title="Visualizar"
                >
                  <Eye size={18} />
                </button>
                <button 
                  className="p-2 rounded-lg hover:bg-gray-100 transition text-gray-900/70 hover:text-gray-900"
                  title="Mais opções"
                >
                  <MoreHorizontal size={18} />
                </button>
              </div>
            </div>
          </div>
        </nav>
        
        {/* DirectedStudio */}
        <div className="flex-1 overflow-auto">
          <DirectedStudio 
            key={selectedProject.id} 
            projectId={selectedProject.id}
            onProjectUpdate={fetchProjects}
            onBack={handleBackToList}
            selectedCompany={selectedCompany}
            avatars={[]}
            onAddAvatar={handleAddAvatar}
            onEditAvatar={handleEditAvatar}
            onRemoveAvatar={handleRemoveAvatar}
            onPreviewAvatar={handlePreviewAvatar}
            onAiEditAvatar={handleAiEditAvatar}
            aiEditAvatarId={aiEditAvatarId}
            setAiEditAvatarId={setAiEditAvatarId}
            aiEditInstruction={aiEditInstruction}
            setAiEditInstruction={setAiEditInstruction}
            aiEditLoading={aiEditLoading}
            lastCreatedAvatar={lastCreatedAvatar}
          />
        </div>
      </div>

      {/* ═══════ PREVIEW MODAL (moved inside selectedProject block) ═══════ */}
      {avatarPreviewUrl && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[9999] flex items-center justify-center p-4"
          onClick={() => setAvatarPreviewUrl(null)}>
          <div className="relative">
            <button className="absolute -top-12 right-0 h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white"
              onClick={(e) => { e.stopPropagation(); setAvatarPreviewUrl(null); }}>
              <X size={20} />
            </button>
            <img src={resolveImageUrl(avatarPreviewUrl)} alt="Preview" className="max-w-full max-h-[85vh] rounded-lg shadow-2xl" onClick={(e) => e.stopPropagation()} />
          </div>
        </div>
      )}

      {/* ═══════ AVATAR MODAL (moved inside selectedProject block) ═══════ */}
      {showAvatarModal && selectedProject && (
        <AvatarModal
          ctx={{
            showAvatarModal,
            avatarStage,
            avatarCreationMode,
            avatarSourceType,
            avatarSourcePhoto,
            avatarVideoUploading,
            avatarExtractedAudio,
            avatarVideoFrames,
            masteringVoice,
            generatingPreviewVideo,
            previewVideoUrl,
            previewLanguage,
            avatarName,
            avatarMediaTab,
            accuracyProgress,
            generatingAvatar,
            avatarPhotoUploading,
            avatarPromptText,
            avatarPromptGender,
            avatarPromptStyle,
            aiEditAvatarId,
            aiEditInstruction,
            aiEditLoading,
            tempAvatar,
            clothingVariants,
            customizeTab,
            voiceTab,
            angleImages,
            generatingAngle,
            auto360Progress,
            editingAvatarId,
            avatarEditHistory,
            avatarBaseUrl,
            applyingClothing,
            isRecording,
            recordedAudioUrl,
            recordedAudioBlob,
            uploadingRecording,
            loadingVoicePreview,
            playingVoiceId,
            elevenLabsVoices,
            elevenLabsAvailable,
            avatarPreviewUrl,
            setAvatarCreationMode,
            setAvatarSourceType,
            setAvatarSourcePhoto,
            setAvatarExtractedAudio,
            setAvatarVideoFrames,
            setAvatarName,
            setAvatarMediaTab,
            setAvatarPromptText,
            setAvatarPromptGender,
            setAvatarPromptStyle,
            setAiEditAvatarId,
            setAiEditInstruction,
            setAiEditLoading,
            setTempAvatar,
            setCustomizeTab,
            setVoiceTab,
            setAngleImages,
            setPreviewLanguage,
            setAvatarPreviewUrl,
            setAvatarEditHistory,
            setPreviewVideoUrl,
            setGeneratingPreviewVideo,
            resetAvatarModal,
            generateAvatarFromPhoto: () => {
              console.log('⚠️ generateAvatarFromPhoto: Not implemented yet');
              toast.info('Função em desenvolvimento');
            },
            generateAvatarFromPrompt: async () => {
              console.log('🎨 generateAvatarFromPrompt called');
              
              if (!avatarPromptText.trim()) {
                toast.error('Descreva o personagem');
                return;
              }
              
              setGeneratingAvatar(true);
              setAccuracyProgress({ progress: 'Gerando personagem...' });
              
              try {
                const style = avatarPromptStyle;
                const payload = {
                  prompt: avatarPromptText,
                  gender: avatarPromptGender,
                  style,
                  company_name: '',
                  logo_url: '',
                };
                
                // Para modo 3D, incluir foto de referência se disponível
                if (avatarCreationMode === '3d' && avatarSourcePhoto?.url) {
                  payload.reference_photo_url = avatarSourcePhoto.url;
                }
                
                console.log('📡 Sending request to generate avatar:', payload);
                
                const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-from-prompt`, payload);
                
                if (data.avatar_url) {
                  console.log('✅ Avatar generated:', data.avatar_url);
                  
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
                  
                  // Inicializar histórico de edição
                  setAvatarBaseUrl(data.avatar_url);
                  setAvatarEditHistory([{
                    url: data.avatar_url,
                    instruction: 'Base original',
                    timestamp: new Date().toISOString(),
                    isBase: true
                  }]);
                  
                  toast.success('Personagem gerado com sucesso!');
                  
                  // Auto-gerar 360° (se função existir)
                  if (typeof startAuto360 === 'function') {
                    startAuto360(data.avatar_url, 'company_uniform', style);
                  }
                } else {
                  throw new Error('Avatar URL not returned');
                }
              } catch (e) {
                console.error('❌ Error generating avatar:', e);
                toast.error(e.response?.data?.detail || 'Erro ao gerar personagem');
                setAccuracyProgress(null);
                setGeneratingAvatar(false);
              }
            },
            uploadAvatarPhoto: () => {
              console.log('⚠️ uploadAvatarPhoto: Not implemented yet');
              toast.info('Função em desenvolvimento');
            },
            uploadAvatarVideo: () => {
              console.log('⚠️ uploadAvatarVideo: Not implemented yet');
              toast.info('Função em desenvolvimento');
            },
            applyClothing: () => {
              console.log('⚠️ applyClothing: Not implemented yet');
              toast.info('Função em desenvolvimento');
            },
            generateAngle: async (angle, forceRegenerate = false) => {
              console.log('🔄 generateAngle called:', angle, 'force:', forceRegenerate);
              
              if (!tempAvatar || (angleImages[angle] && !forceRegenerate)) {
                console.log('⏭️ Skipping (no tempAvatar or angle exists)');
                return;
              }
              
              setGeneratingAngle(angle);
              
              const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
              const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
              const clothing = 'keep_original';
              
              try {
                console.log('📡 Generating angle:', { angle, sourceUrl, style: tempAvatar.avatar_style });
                
                const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-variant`, {
                  source_image_url: sourceUrl,
                  clothing,
                  angle,
                  company_name: '',
                  logo_url: '',
                  avatar_style: tempAvatar?.avatar_style || 'realistic',
                });
                
                if (data.avatar_url) {
                  console.log(`✅ Angle ${angle} generated:`, data.avatar_url);
                  setAngleImages(prev => ({ ...prev, [angle]: data.avatar_url }));
                  toast.success(`Ângulo "${angle}" gerado!`);
                } else {
                  throw new Error('No avatar_url returned');
                }
              } catch (e) {
                console.error(`❌ Error generating angle ${angle}:`, e);
                toast.error(`Erro ao gerar ângulo "${angle}"`);
              } finally {
                setGeneratingAngle(null);
              }
            },
            startAuto360: async (sourceUrl, clothing = 'company_uniform', style = 'realistic') => {
              console.log('🔄 startAuto360 called:', { sourceUrl, clothing, style });
              
              setAuto360Progress({ completed: 0, total: 4 });
              
              try {
                console.log('📡 Starting 360° generation job...');
                
                const { data } = await axios.post(`${API}/campaigns/pipeline/generate-avatar-360`, {
                  source_image_url: sourceUrl,
                  clothing: 'keep_original',
                  logo_url: '',
                  avatar_style: style,
                });
                
                if (data.job_id) {
                  console.log('✅ 360° job started:', data.job_id);
                  toast.info('Gerando visão 360°... Aguarde ~30s');
                  
                  // Poll for progress
                  const pollInterval = setInterval(async () => {
                    try {
                      const { data: status } = await axios.get(`${API}/campaigns/pipeline/generate-avatar-360/${data.job_id}`);
                      
                      const completed = status.completed || Object.values(status.results || {}).filter(Boolean).length;
                      setAuto360Progress({ completed, total: 4 });
                      
                      console.log(`🔄 360° progress: ${completed}/4`, status.status);
                      
                      if (status.results) {
                        setAngleImages(prev => ({
                          ...prev,
                          ...Object.fromEntries(Object.entries(status.results).filter(([,v]) => v))
                        }));
                      }
                      
                      if (status.status === 'completed' || status.status === 'failed') {
                        clearInterval(pollInterval);
                        setAuto360Progress(null);
                        
                        if (status.status === 'completed') {
                          console.log('✅ 360° generation completed!');
                          toast.success('Visão 360° gerada com sucesso!');
                        } else {
                          console.error('❌ 360° generation failed');
                          toast.error('Erro ao gerar 360°');
                        }
                      }
                    } catch (pollErr) {
                      console.warn('⚠️ Poll error (will retry):', pollErr.message);
                      // Continue polling even on error
                    }
                  }, 6000); // Poll every 6 seconds
                  
                  // Auto-stop polling after 3 minutes (safety)
                  setTimeout(() => {
                    clearInterval(pollInterval);
                    setAuto360Progress(null);
                  }, 180000);
                  
                } else {
                  throw new Error('No job_id returned');
                }
              } catch (e) {
                console.error('❌ Error starting 360° generation:', e);
                setAuto360Progress(null);
                toast.error('Erro ao iniciar geração 360°');
              }
            },
            saveAvatarAndClose: () => {
              console.log('⚠️ saveAvatarAndClose: Not implemented in Directed Studio mode');
              toast.info('Use o botão "Salvar" no projeto para persistir mudanças');
              resetAvatarModal();
            },
            saveAvatarAsNew: async () => {
              console.log('💾 saveAvatarAsNew called');
              console.log('tempAvatar:', tempAvatar);
              console.log('avatarName:', avatarName);
              console.log('selectedProject:', selectedProject);
              
              if (!tempAvatar || !tempAvatar.url) {
                console.warn('⚠️ No tempAvatar or tempAvatar.url to save');
                toast.error('Nenhum personagem para salvar');
                return;
              }
              
              const name = avatarName.trim() || `Personagem ${avatars.length + 1}`;
              
              const newAvatar = {
                id: uuidv4(),
                url: tempAvatar.url,
                name,
                source_photo_url: tempAvatar.source_photo_url || '',
                clothing: tempAvatar.clothing || 'keep_original',
                voice: tempAvatar.voice || null,
                angles: angleImages || { front: tempAvatar.url },
                video_url: previewVideoUrl || null,
                language: previewLanguage || 'pt',
                creation_mode: tempAvatar.creation_mode || 'prompt',
                avatar_style: tempAvatar.avatar_style || 'custom',
                edit_history: avatarEditHistory || [],
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              };
              
              console.log('✅ New avatar created:', newAvatar);
              
              // Add to avatars list (local state)
              const updatedAvatars = [...avatars, newAvatar];
              setAvatars(updatedAvatars);
              
              // Persist to backend (if project exists)
              if (selectedProject?.id) {
                try {
                  const response = await axios.post(`${API}/studio/projects/${selectedProject.id}/project-avatars`, {
                    avatar: newAvatar
                  });
                  console.log('✅ Avatar persisted to backend:', response.data);
                  toast.success(`Personagem "${name}" salvo com sucesso!`);
                } catch (err) {
                  console.error('❌ Failed to persist avatar:', err);
                  toast.error('Erro ao salvar personagem no servidor: ' + (err.response?.data?.detail || err.message));
                }
              } else {
                console.log('⚠️ No selectedProject, saving locally only');
                toast.success(`Personagem "${name}" salvo localmente!`);
              }
              
              resetAvatarModal();
            },
            previewVoice: () => {}, // TODO
            startRecording: () => {}, // TODO
            stopRecording: () => {}, // TODO
            saveRecordingAsVoice: () => {}, // TODO
            persistAvatarToServer: () => {}, // TODO
            avatars: [],
            avatarInputRef,
            isDirectedMode: true,
          }}
        />
      )}
      </>
    );
  }

  // Project List View
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ═══ NAVBAR ═══ */}
      <nav className="sticky top-0 z-50 bg-gray-50/95 backdrop-blur-xl border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
          <div className="flex items-center justify-between h-16 gap-3 flex-wrap">
            {/* Left: Logo + Back */}
            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={() => navigate('/')}
                className="flex items-center gap-2 text-gray-900/70 hover:text-gray-900 transition group"
                title="Voltar ao Dashboard"
              >
                <ArrowLeft size={18} className="group-hover:-translate-x-1 transition" />
                <span className="text-sm font-medium">Dashboard</span>
              </button>
              
              <div className="h-8 w-px bg-gray-100" />
              
              <div className="flex items-center gap-2">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#8B5CF6] to-[#7C3AED] shadow-lg shadow-[#8B5CF6]/20 shrink-0">
                  <Film size={16} className="text-white" />
                </div>
                <div>
                  <h1 className="text-sm font-bold text-gray-900 whitespace-nowrap">Estúdio</h1>
                  <p className="text-[10px] text-gray-600 whitespace-nowrap">Seus projetos</p>
                </div>
              </div>
            </div>

            {/* Center: Mode Switcher */}
            <div className="flex items-center gap-1.5 bg-gray-100 rounded-lg p-1 shrink-0">
              <button
                onClick={() => navigate('/studio')}
                className="px-3 py-1.5 text-xs font-medium rounded-md transition bg-[#8B5CF6] text-white whitespace-nowrap"
              >
                Vídeos
              </button>
              <button
                onClick={() => navigate('/traffic-hub')}
                className="px-3 py-1.5 text-xs font-medium rounded-md transition text-gray-600 hover:text-gray-900 hover:bg-gray-200 whitespace-nowrap"
              >
                Marketing
              </button>
            </div>

            {/* Right: Project Count + Actions */}
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-gray-600 bg-gray-100 px-2.5 py-1.5 rounded-lg font-medium whitespace-nowrap">
                {projects.length} {projects.length === 1 ? 'projeto' : 'projetos'}
              </span>
              
              {/* Global Character Library Button */}
              <button
                onClick={() => setShowGlobalLibrary(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#8B5CF6]/10 to-[#7C3AED]/10 border border-[#8B5CF6]/30 text-xs font-semibold text-[#8B5CF6] hover:from-[#8B5CF6]/20 hover:to-[#7C3AED]/20 transition-all hover:scale-105 whitespace-nowrap"
                title="Galeria de Personagens"
              >
                <BookOpen size={14} className="shrink-0" />
                <span>Galeria</span>
              </button>
              
              <button 
                onClick={openNewProjectModal}
                disabled={creating}
                className="btn-gold flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold disabled:opacity-50 transition-all hover:scale-105 shadow-lg shadow-[#F59E0B]/20 whitespace-nowrap"
                title="Criar Novo Projeto"
              >
                <Plus size={14} className="shrink-0" />
                <span>Novo</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* ═══ CONTENT ═══ */}
      <div className="px-6 sm:px-8 lg:px-12 py-6 pb-28">
        <div className="max-w-5xl mx-auto">
          {/* Company Selector */}
          {!selectedProject && companies.length > 0 && (
            <div className="mb-6 bg-gradient-to-r from-[#8B5CF6]/10 to-transparent border border-orange-500/20 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#8B5CF6]/20">
                    <Users size={20} className="text-orange-600" />
                  </div>
                  <div>
                    <p className="text-xs text-gray-900/50 mb-0.5">Empresa do Projeto</p>
                    <p className="text-sm font-semibold text-gray-900">
                      {selectedCompany ? selectedCompany.name : 'Selecione uma empresa'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setShowCompanySelector(!showCompanySelector)}
                  className="text-xs text-orange-600 hover:text-[#9F7CF6] transition flex items-center gap-1"
                >
                  {showCompanySelector ? 'Fechar' : 'Trocar'}
                  <ChevronRight size={14} className={`transition-transform ${showCompanySelector ? 'rotate-90' : ''}`} />
                </button>
              </div>
              
              {/* Company List */}
              {showCompanySelector && (
                <div className="mt-4 pt-4 border-t border-white/5 grid gap-2">
                  {companies.map(company => (
                    <button
                      key={company.id}
                      onClick={() => {
                        setSelectedCompany(company);
                        setShowCompanySelector(false);
                        toast.success(`Empresa "${company.name}" selecionada`);
                      }}
                      className={`text-left p-3 rounded-lg border transition ${
                        selectedCompany?.id === company.id
                          ? 'border-orange-500 bg-[#8B5CF6]/10'
                          : 'border-white/5 bg-gray-100 hover:border-white/10'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{company.name}</p>
                          {company.phone && (
                            <p className="text-xs text-gray-900/50 mt-0.5">{company.phone}</p>
                          )}
                        </div>
                        {company.is_primary && (
                          <span className="text-[9px] bg-[#8B5CF6]/20 text-orange-600 px-2 py-0.5 rounded-full">
                            PRINCIPAL
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                  <button
                    onClick={() => navigate('/marketing')}
                    className="p-3 rounded-lg border border-dashed border-white/20 hover:border-orange-500/50 text-gray-900/50 hover:text-gray-900 transition text-sm"
                  >
                    + Gerenciar Empresas
                  </button>
                </div>
              )}
            </div>
          )}
          
          {/* Search */}
          <div className="mb-6">
            <div className="relative">
              <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-900/50" />
              <input 
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder={l.search}
                className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-200 bg-white text-sm text-gray-900 placeholder-white/40 outline-none focus:border-orange-500/50 transition"
              />
            </div>
          </div>

        {/* Projects List */}
        {filteredProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gray-100 mb-6">
              <Folder size={36} className="text-gray-900/30" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900 mb-2">{l.noProjects}</h2>
            <p className="text-sm text-gray-900/60 mb-6 max-w-sm">{l.createFirst}</p>
            <button 
              onClick={openNewProjectModal}
              disabled={creating}
              className="btn-gold flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold disabled:opacity-50"
            >
              <Sparkles size={18} /> {l.newProject}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredProjects.map((project) => (
              <ProjectRow
                key={project.id}
                project={project}
                onSelect={handleSelectProject}
                onDelete={handleDeleteProject}
                onRename={handleRenameProject}
              />
            ))}
          </div>
        )}
        </div>
      </div>
      
      {/* New Project Modal */}
      {showNewProjectModal && (
        <NewProjectModal
          lang={lang}
          onClose={() => setShowNewProjectModal(false)}
          onCreate={handleCreateProject}
        />
      )}

      {/* Avatar Zoom Modal */}
      {avatarPreviewUrl && (
        <div 
          className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/90 backdrop-blur-sm animate-fade-in"
          onClick={() => setAvatarPreviewUrl(null)}
        >
          <div className="relative max-w-2xl max-h-[90vh] p-4">
            <button 
              onClick={() => setAvatarPreviewUrl(null)}
              className="absolute -top-2 -right-2 z-10 p-2 rounded-full bg-white/10 hover:bg-white/20 text-gray-900 transition"
              aria-label="Fechar"
            >
              <X size={20} />
            </button>
            <img 
              src={resolveImageUrl(avatarPreviewUrl)} 
              alt="Preview" 
              className="max-w-full max-h-[85vh] rounded-lg shadow-2xl object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}

      {/* ═══════ AVATAR MODAL (Global - Outside Project Context) ═══════ */}
      {showAvatarModal && !selectedProject && (
        <AvatarModal
          ctx={{
            showAvatarModal,
            avatarStage,
            avatarCreationMode,
            avatarSourceType,
            avatarSourcePhoto,
            avatarVideoUploading,
            avatarExtractedAudio,
            avatarVideoFrames,
            masteringVoice,
            generatingPreviewVideo,
            previewVideoUrl,
            previewLanguage,
            avatarName,
            avatarMediaTab,
            accuracyProgress,
            generatingAvatar,
            avatarPhotoUploading,
            avatarPromptText,
            avatarPromptGender,
            avatarPromptStyle,
            aiEditAvatarId,
            aiEditInstruction,
            aiEditLoading,
            tempAvatar,
            clothingVariants,
            customizeTab,
            voiceTab,
            angleImages,
            generatingAngle,
            auto360Progress,
            editingAvatarId,
            avatarEditHistory,
            avatarBaseUrl,
            applyingClothing,
            isRecording,
            recordedAudioUrl,
            recordedAudioBlob,
            uploadingRecording,
            loadingVoicePreview,
            playingVoiceId,
            elevenLabsVoices,
            elevenLabsAvailable,
            avatarPreviewUrl,
            setAvatarCreationMode,
            setAvatarSourceType,
            setAvatarSourcePhoto,
            setAvatarExtractedAudio,
            setAvatarVideoFrames,
            setAvatarName,
            setAvatarMediaTab,
            setAvatarPromptText,
            setAvatarPromptGender,
            setAvatarPromptStyle,
            setAiEditAvatarId,
            setAiEditInstruction,
            setAiEditLoading,
            setTempAvatar,
            setCustomizeTab,
            setVoiceTab,
            setAngleImages,
            setPreviewLanguage,
            setAvatarPreviewUrl,
            setAvatarEditHistory,
            setPreviewVideoUrl,
            setGeneratingPreviewVideo,
            resetAvatarModal,
            generateAvatarFromPhoto: async () => {
              console.log('🎨 Global generateAvatarFromPhoto');
              
              if (!avatarSourcePhoto) {
                toast.error('Faça upload de uma foto primeiro');
                return;
              }
              
              setAvatarPhotoUploading(true);
              setGeneratingAvatar(true);
              
              try {
                const formData = new FormData();
                
                // Se avatarSourcePhoto é um blob/file
                if (avatarSourcePhoto instanceof Blob || avatarSourcePhoto instanceof File) {
                  formData.append('file', avatarSourcePhoto, 'avatar.jpg');
                } else if (avatarSourcePhoto.url) {
                  // Se é um objeto com URL
                  formData.append('image_url', avatarSourcePhoto.url);
                }
                
                formData.append('company_id', selectedCompany?.id || '');
                formData.append('style', avatarPromptStyle || 'custom');
                
                const response = await axios.post(`${API}/campaigns/pipeline/generate-avatar-from-photo`, formData, {
                  headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                const avatar = response.data.avatar;
                setTempAvatar(avatar);
                setAvatarName(avatar.name || '');
                setAvatarStage('customize');
                toast.success('Avatar criado com sucesso!');
              } catch (err) {
                console.error('❌ Error generating avatar:', err);
                toast.error('Erro ao gerar avatar: ' + (err.response?.data?.detail || err.message));
              } finally {
                setAvatarPhotoUploading(false);
                setGeneratingAvatar(false);
              }
            },
            generateAvatarFromPrompt: async () => {
              console.log('🎨 Global generateAvatarFromPrompt');
              
              if (!avatarPromptText.trim()) {
                toast.error('Descreva o personagem');
                return;
              }
              
              setGeneratingAvatar(true);
              setAccuracyProgress({ progress: 'Gerando personagem...' });
              
              try {
                const payload = {
                  prompt: avatarPromptText,
                  gender: avatarPromptGender,
                  style: avatarPromptStyle,
                  company_id: selectedCompany?.id || ''
                };
                
                const response = await axios.post(`${API}/campaigns/pipeline/generate-avatar-from-prompt`, payload);
                
                const avatar = response.data.avatar || { url: response.data.avatar_url };
                setTempAvatar(avatar);
                setAvatarName(avatar.name || '');
                setAvatarStage('customize');
                setAccuracyProgress(null);
                toast.success('Avatar gerado com sucesso!');
              } catch (err) {
                console.error('❌ Error generating avatar:', err);
                toast.error('Erro ao gerar avatar: ' + (err.response?.data?.detail || err.message));
                setAccuracyProgress(null);
              } finally {
                setGeneratingAvatar(false);
              }
            },
            uploadAvatarPhoto: () => avatarInputRef.current?.click(),
            uploadAvatarVideo: () => {
              console.log('⚠️ uploadAvatarVideo: Not implemented in global mode');
              toast.info('Upload de vídeo disponível apenas em projetos');
            },
            applyClothing: async (clothing) => {
              console.log('🎨 Global applyClothing:', clothing);
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para aplicar fundo');
                return;
              }
              
              setApplyingClothing(true);
              
              try {
                const response = await axios.post(`${API}/campaigns/pipeline/generate-avatar-variant`, {
                  source_image_url: tempAvatar.url,
                  clothing,
                  angle: 'front',
                  company_name: selectedCompany?.name || '',
                  logo_url: selectedCompany?.logo_url || '',
                  avatar_style: tempAvatar.style || 'custom'
                });
                
                if (response.data.avatar_url) {
                  setTempAvatar(prev => ({ ...prev, url: response.data.avatar_url }));
                  toast.success('Fundo aplicado com sucesso!');
                }
              } catch (err) {
                console.error('❌ Error applying background:', err);
                toast.error('Erro ao aplicar fundo');
              } finally {
                setApplyingClothing(false);
              }
            },
            generateAngle: async (angle, forceRegenerate = false) => {
              console.log('🔄 Global generateAngle:', angle);
              
              if (!tempAvatar?.url) return;
              if (angleImages[angle] && !forceRegenerate) return;
              
              setGeneratingAngle(angle);
              
              try {
                const response = await axios.post(`${API}/campaigns/pipeline/generate-avatar-variant`, {
                  source_image_url: tempAvatar.url,
                  clothing: 'keep_original',
                  angle,
                  company_name: '',
                  logo_url: '',
                  avatar_style: tempAvatar.style || 'custom'
                });
                
                if (response.data.avatar_url) {
                  setAngleImages(prev => ({ ...prev, [angle]: response.data.avatar_url }));
                  toast.success(`Ângulo "${angle}" gerado!`);
                }
              } catch (err) {
                console.error(`❌ Error generating angle ${angle}:`, err);
                toast.error(`Erro ao gerar ângulo "${angle}"`);
              } finally {
                setGeneratingAngle(null);
              }
            },
            startAuto360: async () => {
              console.log('🔄 Global startAuto360');
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para gerar 360°');
                return;
              }
              
              setAuto360Progress({ completed: 0, total: 4 });
              
              try {
                const response = await axios.post(`${API}/campaigns/pipeline/generate-avatar-360`, {
                  source_image_url: tempAvatar.url,
                  clothing: 'keep_original',
                  logo_url: '',
                  avatar_style: tempAvatar.style || 'custom'
                });
                
                if (response.data.job_id) {
                  toast.info('Gerando visão 360°... Aguarde ~30s');
                  
                  const pollInterval = setInterval(async () => {
                    try {
                      const { data: status } = await axios.get(`${API}/campaigns/pipeline/generate-avatar-360/${response.data.job_id}`);
                      
                      const completed = Object.values(status.results || {}).filter(Boolean).length;
                      setAuto360Progress({ completed, total: 4 });
                      
                      if (status.results) {
                        setAngleImages(prev => ({
                          ...prev,
                          ...Object.fromEntries(Object.entries(status.results).filter(([,v]) => v))
                        }));
                      }
                      
                      if (status.status === 'completed' || status.status === 'failed') {
                        clearInterval(pollInterval);
                        setAuto360Progress(null);
                        
                        if (status.status === 'completed') {
                          toast.success('Visão 360° gerada!');
                        } else {
                          toast.error('Erro ao gerar 360°');
                        }
                      }
                    } catch (pollErr) {
                      console.warn('⚠️ Poll error:', pollErr.message);
                    }
                  }, 6000);
                  
                  setTimeout(() => {
                    clearInterval(pollInterval);
                    setAuto360Progress(null);
                  }, 180000);
                }
              } catch (err) {
                console.error('❌ Error starting 360°:', err);
                setAuto360Progress(null);
                toast.error('Erro ao iniciar geração 360°');
              }
            },
            saveAvatarAndClose: async () => {
              console.log('💾 Global saveAvatarAndClose');
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para salvar');
                return;
              }
              
              try {
                const payload = {
                  name: avatarName || 'Novo Personagem',
                  image_url: tempAvatar.url,
                  style: tempAvatar.style || 'custom',
                  gender: tempAvatar.gender || 'male',
                  company_id: selectedCompany?.id || null,
                  angles: angleImages || {},
                  voice_id: tempAvatar.voice_id || null,
                  language: previewLanguage || 'pt'
                };
                
                await axios.post(`${API}/data/avatars`, payload);
                toast.success('Personagem salvo com sucesso!');
                resetAvatarModal();
                
                if (showGlobalLibrary) {
                  setShowGlobalLibrary(false);
                  setTimeout(() => setShowGlobalLibrary(true), 100);
                }
              } catch (err) {
                console.error('❌ Error saving avatar:', err);
                toast.error('Erro ao salvar personagem');
              }
            },
            saveAvatarAsNew: async () => {
              console.log('💾 Global saveAvatarAsNew (same as saveAvatarAndClose)');
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para salvar');
                return;
              }
              
              try {
                const payload = {
                  name: avatarName || 'Novo Personagem',
                  image_url: tempAvatar.url,
                  style: tempAvatar.style || 'custom',
                  gender: tempAvatar.gender || 'male',
                  company_id: selectedCompany?.id || null,
                  angles: angleImages || {},
                  voice_id: tempAvatar.voice_id || null,
                  language: previewLanguage || 'pt'
                };
                
                await axios.post(`${API}/data/avatars`, payload);
                toast.success('Personagem salvo!');
                resetAvatarModal();
                
                if (showGlobalLibrary) {
                  setShowGlobalLibrary(false);
                  setTimeout(() => setShowGlobalLibrary(true), 100);
                }
              } catch (err) {
                console.error('❌ Error saving avatar:', err);
                toast.error('Erro ao salvar personagem');
              }
            },
            previewVoice: async (voiceId, voiceType = 'elevenlabs') => {
              console.log('🔊 Global previewVoice:', voiceId);
              
              setLoadingVoicePreview(voiceId);
              setPlayingVoiceId(null);
              
              try {
                const sampleText = previewLanguage === 'pt' 
                  ? 'Olá! Esta é uma prévia da minha voz.'
                  : previewLanguage === 'es'
                  ? '¡Hola! Esta es una vista previa de mi voz.'
                  : 'Hello! This is a preview of my voice.';
                
                const response = await axios.post(`${API}/campaigns/pipeline/generate-voice-preview`, {
                  voice_id: voiceId,
                  text: sampleText,
                  language: previewLanguage || 'pt'
                });
                
                if (response.data.audio_url) {
                  const audio = new Audio(response.data.audio_url);
                  audio.onended = () => setPlayingVoiceId(null);
                  audio.play();
                  setPlayingVoiceId(voiceId);
                }
              } catch (err) {
                console.error('❌ Error previewing voice:', err);
                toast.error('Erro ao reproduzir voz');
              } finally {
                setLoadingVoicePreview(null);
              }
            },
            startRecording: () => {
              console.log('🎤 Global startRecording');
              toast.info('Gravação de voz disponível apenas em projetos');
            },
            stopRecording: () => {
              console.log('🛑 Global stopRecording');
            },
            saveRecordingAsVoice: () => {
              console.log('💾 Global saveRecordingAsVoice');
              toast.info('Gravação de voz disponível apenas em projetos');
            },
            persistAvatarToServer: async () => {
              console.log('💾 Global persistAvatarToServer (same as saveAvatarAndClose)');
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para salvar');
                return;
              }
              
              try {
                const payload = {
                  name: avatarName || 'Novo Personagem',
                  image_url: tempAvatar.url,
                  style: tempAvatar.style || 'custom',
                  gender: tempAvatar.gender || 'male',
                  company_id: selectedCompany?.id || null,
                  angles: angleImages || {},
                  voice_id: tempAvatar.voice_id || null,
                  language: previewLanguage || 'pt'
                };
                
                await axios.post(`${API}/data/avatars`, payload);
                toast.success('Personagem salvo!');
              } catch (err) {
                console.error('❌ Error persisting avatar:', err);
                toast.error('Erro ao salvar personagem');
              }
            },
            avatars,
            avatarInputRef,
            logoInputRef,
            isDirectedMode: true,
          }}
        />
      )}
      
      {/* Global Character Library Modal */}
      <AvatarLibraryModalV2
        open={showGlobalLibrary}
        onClose={() => setShowGlobalLibrary(false)}
        projectId={null}
        projectAvatarIds={new Set()}
        onImported={(importedAvatars) => {
          console.log('✅ Avatars viewed in global library:', importedAvatars.length);
          toast.success(`Visualizando ${importedAvatars.length} personagens!`);
        }}
        onEditAvatar={(avatar) => {
          console.log('✅ Editing avatar from global library:', avatar.name);
          // TODO: Implement global avatar editing
          toast.info('Edição de personagens globais em desenvolvimento');
        }}
        onCreateNew={() => {
          console.log('🎨 Creating new character from gallery');
          setEditingAvatarId(null);
          setTempAvatar(null);
          setShowAvatarModal(true);
        }}
        lang={lang}
      />
    </div>
  );
}
