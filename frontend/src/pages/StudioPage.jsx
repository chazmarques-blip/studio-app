import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { v4 as uuidv4 } from 'uuid';
import { 
  Film, Plus, Trash2, Clock, Layers, Users, Play, Folder, 
  ChevronRight, MoreHorizontal, Search, ArrowLeft, Eye,
  FileText, Palette, Video, CheckCircle2, Circle, Sparkles, Pencil, Check, X, BookOpen, RefreshCw
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
function ProjectRow({ project, onSelect, onDelete, onRename, onSyncCharacters }) {
  const [showMenu, setShowMenu] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(project.name || '');
  const [videoThumbnail, setVideoThumbnail] = useState(null);
  const inputRef = useRef(null);
  const videoRef = useRef(null);
  
  // Corrigir: Buscar thumbnail do primeiro vídeo ou primeiro output
  const firstVideo = project.outputs?.find(o => o.type === 'video');
  const firstImage = project.outputs?.find(o => o.type === 'keyframe' || o.type === 'image');
  const thumbnail = project?.project_bible?.book_bible?.cover?.front_url || firstVideo?.url || firstImage?.url || project.book_cover_url;
  const progress = getProjectProgress(project);
  const updatedAt = project.updated_at ? new Date(project.updated_at) : null;
  const scenesCount = project.scenes?.length || 0;
  const charactersCount = project.characters?.length || 0;
  // BookFactory detection
  const bookBible = project?.project_bible?.book_bible || null;
  const isBookProject = project?.output_mode === 'book' || !!bookBible;
  const bookStatus = bookBible?.status || null;
  const bookPdfUrl = bookBible?.pdf_url || null;
  const bookCoverUrl = bookBible?.cover?.front_url || null;
  const bookSpreadsCount = (bookBible?.spreads || []).length;
  
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
      className="group relative flex items-center gap-3 rounded-xl border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#1A1430] hover:border-violet-300 dark:hover:border-violet-500/40 hover:shadow-sm cursor-pointer transition-all px-2 py-1"
      data-testid={`project-row-${project.id}`}
    >
      {/* Thumbnail — horizontal 16:9 */}
      <div className="relative w-28 h-16 shrink-0 rounded-md bg-gradient-to-br from-violet-50 to-gray-100 dark:from-[#221A3F] dark:to-[#0D0719] overflow-hidden flex items-center justify-center">
        {videoThumbnail ? (
          <img src={videoThumbnail} alt="" className="w-full h-full object-cover" />
        ) : thumbnail ? (
          <img src={resolveImageUrl(thumbnail)} alt="" className="w-full h-full object-cover" />
        ) : (
          <Film size={22} strokeWidth={1.25} className="text-violet-200 dark:text-[#4A3F6B]" />
        )}
      </div>

      {/* Name + meta */}
      <div className="flex-1 min-w-0" style={{ fontFamily: "'Manrope', system-ui" }}>
        <div className="flex items-center gap-2">
          {isEditing ? (
            <div className="flex items-center gap-1 flex-1" onClick={e => e.stopPropagation()}>
              <input
                ref={inputRef}
                type="text"
                value={editName}
                onChange={(e) => setEditName(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1 px-2 py-1 rounded bg-gray-100 dark:bg-[#0A0614] border border-violet-500 text-[13px] text-gray-900 dark:text-white outline-none"
              />
              <button onClick={handleSaveEdit} className="p-1 rounded hover:bg-white/10 text-emerald-500">
                <Check size={14} />
              </button>
              <button onClick={handleCancelEdit} className="p-1 rounded hover:bg-white/10 text-red-500">
                <X size={14} />
              </button>
            </div>
          ) : (
            <>
              <h3 className="text-[14px] font-semibold text-gray-900 dark:text-white truncate leading-tight">
                {project.name}
              </h3>
              <button
                onClick={handleStartEdit}
                className="p-1 rounded hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Renomear"
              >
                <Pencil size={11} className="text-gray-500 dark:text-[#A3A3B2]" />
              </button>
            </>
          )}
        </div>

        {/* Metadata row — compact */}
        <div className="flex items-center gap-2.5 text-[11px] text-gray-600 dark:text-[#A3A3B2] mt-1 flex-wrap">
          {isBookProject ? (
            <span className="inline-flex items-center gap-1 font-medium text-emerald-600 dark:text-emerald-400" data-testid={`book-badge-${project.id}`}>
              <BookOpen size={11} /> Livro
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 font-medium text-violet-600 dark:text-violet-400">
              <Video size={11} /> Vídeo
            </span>
          )}

          {isBookProject && bookSpreadsCount > 0 && (
            <span className="inline-flex items-center gap-1">
              <Layers size={11} className="text-gray-400 dark:text-[#6B647F]" /> {bookSpreadsCount} spreads
            </span>
          )}
          {!isBookProject && (
            <span className="inline-flex items-center gap-1">
              <Layers size={11} className="text-gray-400 dark:text-[#6B647F]" /> {scenesCount} cenas
            </span>
          )}

          <span className="inline-flex items-center gap-1">
            <Users size={11} className="text-gray-400 dark:text-[#6B647F]" /> {charactersCount} personagens
          </span>

          {isBookProject && bookPdfUrl && (
            <span className="inline-flex items-center gap-1 font-medium text-emerald-600 dark:text-emerald-400">
              <Check size={11} /> PDF pronto
            </span>
          )}
          {isBookProject && !bookPdfUrl && bookStatus && (
            <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
              {bookStatus.replace(/_/g, ' ')}
            </span>
          )}

          {updatedAt && (
            <span className="inline-flex items-center gap-1 text-gray-500 dark:text-[#6B647F]">
              <Clock size={11} /> {formatDate(updatedAt)}
            </span>
          )}
        </div>
      </div>

      {/* Status badge + actions — compact, fixed widths for alignment */}
      <div className="flex items-center gap-1 shrink-0">
        <div className={`h-6 w-6 rounded-full flex items-center justify-center ${
          (isBookProject ? bookPdfUrl : progress.percent === 100)
            ? 'bg-gradient-to-br from-violet-500 to-orange-500 shadow-[0_0_10px_rgba(139,92,246,0.3)]'
            : 'bg-gradient-to-br from-gray-200 to-gray-300 dark:from-[#2A2442] dark:to-[#1A1430] dark:border dark:border-[#3A3258]'
        }`} title={(isBookProject ? bookPdfUrl : progress.percent === 100) ? 'Pronto' : 'Em progresso'}>
          {isBookProject ? <BookOpen size={10} className="text-white" /> : <Video size={10} className="text-white" />}
        </div>

        <button
          onClick={(e) => { e.stopPropagation(); onSelect(project); }}
          data-testid={`open-project-${project.id}`}
          className="w-[88px] h-6 rounded-full bg-violet-50 dark:bg-violet-500/10 text-violet-700 dark:text-violet-300 hover:bg-violet-100 dark:hover:bg-violet-500/20 text-[10px] font-medium flex items-center justify-center gap-1 transition border border-violet-100 dark:border-violet-500/20"
        >
          {isBookProject ? <BookOpen size={10} /> : <Play size={10} />}
          {isBookProject ? 'Abrir livro' : 'Abrir vídeo'}
        </button>

        <button
          onClick={(e) => { e.stopPropagation(); onSyncCharacters(project); }}
          title={project.character_library ? `Atualizar biblioteca (${project.character_library.total_characters})` : 'Carregar personagens da pasta'}
          className="w-[80px] h-6 rounded-full bg-orange-50 dark:bg-orange-500/10 text-orange-700 dark:text-orange-300 hover:bg-orange-100 dark:hover:bg-orange-500/20 text-[10px] font-medium flex items-center justify-center gap-1 transition border border-orange-100 dark:border-orange-500/20"
        >
          {project.character_library ? <RefreshCw size={10} /> : <BookOpen size={10} />}
          Carregar
        </button>

        {/* Menu */}
        <div className="relative">
          <button
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
            className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-white/10 transition"
          >
            <MoreHorizontal size={12} className="text-gray-400 dark:text-[#6B647F]" />
          </button>

          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={(e) => { e.stopPropagation(); setShowMenu(false); }} />
              <div className="absolute right-0 top-full mt-1 z-20 rounded-lg border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] shadow-xl py-1.5 min-w-[160px]">
                {!project.v2_migrated && (
                  <button
                    onClick={(e) => { e.stopPropagation(); setShowMenu(false); if (window.onUpgradeToV2) window.onUpgradeToV2(project); }}
                    className="w-full px-4 py-2 text-left text-sm text-violet-600 dark:text-violet-300 hover:bg-violet-50 dark:hover:bg-violet-500/10 flex items-center gap-2 border-b border-gray-100 dark:border-[#2A2442] mb-1"
                  >
                    <Sparkles size={14} /> Upgrade to V2
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); handleStartEdit(e); setShowMenu(false); }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-[#A3A3B2] hover:bg-gray-50 dark:hover:bg-white/5 flex items-center gap-2"
                >
                  <Pencil size={14} /> Renomear
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); e.preventDefault(); setShowMenu(false); onDelete(project); }}
                  className="w-full px-4 py-2 text-left text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center gap-2"
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
  const [projectTypeFilter, setProjectTypeFilter] = useState('all'); // 'all' | 'video' | 'book' | 'both'
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  
  // Global Character Library
  const [showGlobalLibrary, setShowGlobalLibrary] = useState(false);

  // Open gallery automatically when navigated with ?gallery=1 (from Sidebar "Personagens")
  useEffect(() => {
    if (searchParams.get('gallery') === '1') {
      setShowGlobalLibrary(true);
      // Keep the param so the sidebar stays highlighted while modal is open
    }
  }, [searchParams]);
  
  // Company selection (duplicated from Marketing for Videos context)
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [showCompanySelector, setShowCompanySelector] = useState(false);
  
  // ═══════ AVATAR MODAL - COMPLETE STATES (copied from PipelineView) ═══════
  const [avatars, setAvatars] = useState([]);
  const [avatarsLoaded, setAvatarsLoaded] = useState(false);

  // Load avatars ONCE on mount (central cache)
  useEffect(() => {
    const loadAvatars = async () => {
      try {
        // Try cache first
        const cached = localStorage.getItem('studiox_avatars_cache');
        if (cached) {
          const { data, ts } = JSON.parse(cached);
          // Use cache if < 10 min old
          if (Date.now() - ts < 10 * 60 * 1000) {
            setAvatars(data);
            setAvatarsLoaded(true);
            console.log('✅ Loaded', data.length, 'avatars from cache');
            return;
          }
        }

        // Fetch from API
        console.log('🔄 Fetching avatars from API...');
        const { data } = await axios.get(`${API}/data/avatars`);
        setAvatars(data || []);
        setAvatarsLoaded(true);
        
        // Update cache
        localStorage.setItem('studiox_avatars_cache', JSON.stringify({ data: data || [], ts: Date.now() }));
        console.log('✅ Loaded', data?.length || 0, 'avatars from API');
      } catch (err) {
        console.error('Error loading avatars:', err);
        setAvatarsLoaded(true);
      }
    };

    loadAvatars();
  }, []);

  // Smart cache updaters (update ONLY the changed avatar)
  const updateAvatarInCache = useCallback((updatedAvatar) => {
    setAvatars(prev => {
      const idx = prev.findIndex(a => a.id === updatedAvatar.id);
      let updated;
      if (idx >= 0) {
        // Update existing
        updated = [...prev];
        updated[idx] = updatedAvatar;
        console.log('✅ Updated avatar in cache:', updatedAvatar.name);
      } else {
        // Add new
        updated = [...prev, updatedAvatar];
        console.log('✅ Added new avatar to cache:', updatedAvatar.name);
      }
      // Persist to localStorage
      localStorage.setItem('studiox_avatars_cache', JSON.stringify({ data: updated, ts: Date.now() }));
      return updated;
    });
  }, []);

  const removeAvatarFromCache = useCallback((avatarId) => {
    setAvatars(prev => {
      const updated = prev.filter(a => a.id !== avatarId);
      console.log('✅ Removed avatar from cache:', avatarId);
      // Persist to localStorage
      localStorage.setItem('studiox_avatars_cache', JSON.stringify({ data: updated, ts: Date.now() }));
      return updated;
    });
  }, []);
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
  
  // Auto-extract name from prompt
  useEffect(() => {
    if (avatarPromptText && !avatarName) {
      // Try to extract name from common patterns
      const patterns = [
        /(?:um|uma|o|a)\s+([A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+(?:\s+[A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+)?)\s+(?:feliz|alegre|triste|sorridente|bravo|que|está|com)/i,
        /^([A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+(?:\s+[A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+)?)\s+(?:é|está|tem|usa|veste)/i,
        /(?:chamado|chamada|conhecido|conhecida|nome|named|called)\s+([A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+(?:\s+[A-ZÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜ][a-zàáâãäåçèéêëìíîïñòóôõöùúûü]+)?)/i,
      ];
      
      for (const pattern of patterns) {
        const match = avatarPromptText.match(pattern);
        if (match && match[1]) {
          const extractedName = match[1].trim();
          console.log('✨ [AUTO-NAME] Extracted from prompt:', extractedName);
          setAvatarName(extractedName);
          break;
        }
      }
    }
  }, [avatarPromptText, avatarName]);
  
  const [avatarPromptGender, setAvatarPromptGender] = useState('female');
  const [avatarPromptStyle, setAvatarPromptStyle] = useState('custom');
  const [promptBatchMode, setPromptBatchMode] = useState(false); // false = individual, true = batch
  const [batchProgress, setBatchProgress] = useState(null); // { completed, total, currentPrompt }

  // Batch avatar generation function
  const generateAvatarBatch = async () => {
    console.log('🚀 generateAvatarBatch called (StudioPage)');
    
    if (!avatarPromptText.trim()) {
      toast.error('Cole os prompts separados por linha em branco');
      return;
    }

    // Split prompts by blank line
    const prompts = avatarPromptText
      .split(/\n\s*\n/)
      .map(p => p.trim())
      .filter(p => p.length > 0);

    console.log('Prompts parsed:', prompts.length, 'prompts');
    console.log('Prompt list:', prompts.map((p, i) => `${i+1}. ${p.substring(0, 50)}...`));

    if (prompts.length === 0) {
      toast.error('Nenhum prompt válido encontrado');
      return;
    }

    if (prompts.length > 20) {
      toast.error('Máximo de 20 personagens por lote');
      return;
    }

    setGeneratingAvatar(true);
    
    const created = [];
    const failed = [];

    // Process each prompt one by one with real-time progress
    for (let i = 0; i < prompts.length; i++) {
      const prompt = prompts[i];
      const currentNum = i + 1;
      
      // Update progress bar
      setBatchProgress({ 
        completed: i, 
        total: prompts.length, 
        currentPrompt: prompt.substring(0, 60) + '...',
        currentNum
      });

      try {
        console.log(`Creating ${currentNum}/${prompts.length}: ${prompt.substring(0, 50)}...`);
        
        // Call batch endpoint with single prompt
        const { data } = await axios.post(`${API}/data/avatars/batch`, {
          prompts: [prompt],
          style: avatarPromptStyle,
          gender: avatarPromptGender,
        }, {
          timeout: 60000, // 1 minute per avatar
        });

        if (data.created && data.created.length > 0) {
          created.push(...data.created);
          
          // Update progress to show completion
          setBatchProgress({ 
            completed: currentNum, 
            total: prompts.length, 
            currentPrompt: prompt.substring(0, 60) + '...',
            currentNum
          });
          
          console.log(`✅ Created ${currentNum}/${prompts.length}`);
        }
        
        if (data.failed && data.failed.length > 0) {
          failed.push(...data.failed);
        }

      } catch (e) {
        console.error(`Failed to create avatar ${currentNum}/${prompts.length}:`, e);
        failed.push({ prompt, error: e.message });
      }
    }

    try {
      // Refresh avatar list
      const freshAvatars = await axios.get(`${API}/data/avatars`);
      setAvatars(freshAvatars.data || []);
      localStorage.setItem('studiox_avatars', JSON.stringify(freshAvatars.data || []));

      // Show results
      if (created.length > 0) {
        toast.success(`${created.length} personagens criados com sucesso!`);
      }
      if (failed.length > 0) {
        toast.warning(`${failed.length} personagens falharam na criação`);
      }

      // Reset modal
      resetAvatarModal();

    } catch (e) {
      console.error('Error refreshing avatars:', e);
      toast.error('Personagens criados, mas erro ao atualizar lista');
    } finally {
      setGeneratingAvatar(false);
      setBatchProgress(null);
    }
  };



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
      prompt: av.prompt || '', // Incluir prompt para exibir botão de copiar
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

  // ═══════ EVENT LISTENER: Avatar Creation from DirectedStudio ═══════
  useEffect(() => {
    const handleOpenAvatarCreation = (e) => {
      console.log('🎯 [EVENT] openAvatarCreation received:', e.detail);
      console.log('🎯 [STATE] selectedProject:', selectedProject?.id);
      console.log('🎯 [STATE] showAvatarModal before:', showAvatarModal);
      
      resetAvatarModal();
      setShowAvatarModal(true);
      
      console.log('🎯 [ACTION] setShowAvatarModal(true) called');
    };
    
    window.addEventListener('openAvatarCreation', handleOpenAvatarCreation);
    
    return () => {
      window.removeEventListener('openAvatarCreation', handleOpenAvatarCreation);
    };
  }, [selectedProject, showAvatarModal]);

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

      // BookFactory: quando output_mode=book, ativa book/start e redireciona pro BookStudio
      if (projectData.output_mode === 'book' || projectData.output_mode === 'both') {
        try {
          await axios.post(`${API}/studio/projects/${data.id}/book/start`, {
            output_mode: projectData.output_mode,
            autoria_mode: 'user_author',
            format_preset: 'picturebook',
            trim_size: '6x9',
            target_spreads: 14,
            audience: projectData.target_audience === 'all' ? 'children_4_8' : 'children_4_8',
            illustration_track: 'storybook',
            title: projectData.name,
            author_name: '',
            briefing: projectData.briefing || '',
            language: projectData.language || 'pt',
            character_ids: [],
            source_project_id: null,
          });
        } catch (e) {
          console.warn('book/start failed (non-fatal):', e?.response?.data);
        }

        if (projectData.output_mode === 'book') {
          // Livro puro → abre BookStudio direto
          await fetchProjects();
          navigate(`/studio/book/${data.id}`);
          return;
        }
        // Both: segue para fluxo de vídeo mas já tem book_bible armado
      }

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

  // Sync Character Library
  const handleSyncCharacters = async (project) => {
    try {
      toast.loading('Carregando personagens...');
      const { data } = await axios.post(`${API}/studio/projects/${project.id}/sync-characters`);
      
      toast.dismiss();
      
      if (data.status === 'success') {
        toast.success(`✅ ${data.character_library.total_characters} personagens carregados da pasta "${data.character_library.folder_name}"!`);
        
        // Update project in state
        setProjects(prev => prev.map(p => 
          p.id === project.id 
            ? { ...p, character_library: data.character_library }
            : p
        ));
        
        // If this is the selected project, update it too
        if (selectedProject?.id === project.id) {
          setSelectedProject(prev => ({
            ...prev,
            character_library: data.character_library
          }));
        }
      } else if (data.status === 'warning') {
        toast.warning(data.message);
      }
    } catch (err) {
      toast.dismiss();
      toast.error('Erro ao carregar personagens: ' + (err.response?.data?.detail || err.message));
      console.error('Error syncing characters:', err);
    }
  };


  // Select project - CORRIGIDO
  // Projetos do tipo livro abrem na BookStudio (rota dedicada)
  const handleSelectProject = (project) => {
    const isBookProject = project?.output_mode === 'book' || !!project?.project_bible?.book_bible;
    if (isBookProject) {
      navigate(`/studio/book/${project.id}`);
      return;
    }
    setSelectedProject(project);
    setSearchParams({ project: project.id });
  };

  // Back to list
  const handleBackToList = () => {
    setSelectedProject(null);
    setSearchParams({});
  };

  // Filter projects — by search term AND by output type
  const projectKind = (p) => {
    // Infer the output type of a project
    const mode = p?.output_mode;
    if (mode === 'book' || mode === 'video' || mode === 'both') return mode;
    // Back-compat: older projects (no output_mode) → infer by presence of book_bible
    if (p?.project_bible?.book_bible) return 'book';
    return 'video';
  };

  const projectCounts = projects.reduce(
    (acc, p) => {
      const k = projectKind(p);
      acc.all += 1;
      acc[k] = (acc[k] || 0) + 1;
      return acc;
    },
    { all: 0, video: 0, book: 0, both: 0 },
  );

  const filteredProjects = projects.filter((p) => {
    if (!p.name?.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (projectTypeFilter === 'all') return true;
    return projectKind(p) === projectTypeFilter;
  });

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
            promptBatchMode,
            batchProgress,
            avatars,
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
            setApplyingClothing,
            setPromptBatchMode,
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
                    prompt: avatarPromptText, // Salvar prompt para exibir botão de copiar
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
            generateAvatarBatch,
            saveAvatarAndClose: async () => {
              console.log('💾 saveAvatarAndClose called (saving avatar...)');
              
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
                prompt: tempAvatar.prompt || '',  // Incluir prompt
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              };
              
              console.log('✅ New avatar created:', newAvatar);
              
              // 1. Save to GLOBAL gallery (tenant avatars)
              try {
                console.log('📡 [SAVE] Sending POST /data/avatars...', newAvatar);
                const response = await axios.post(`${API}/data/avatars`, newAvatar);
                console.log('✅ [SAVE] Response from /data/avatars:', response.data);
                console.log('✅ [SAVE] Avatar saved to global gallery');
                
                // 2. Add to local state (avatars cache)
                const updatedAvatars = [...avatars, newAvatar];
                console.log('📊 [CACHE] Updating avatars state. Before:', avatars.length, 'After:', updatedAvatars.length);
                setAvatars(updatedAvatars);
                setAvatarsLoaded(true);
                
                // 3. Update localStorage cache
                localStorage.setItem('studiox_avatars_cache', JSON.stringify(updatedAvatars));
                console.log('💾 [CACHE] localStorage updated');
                
                toast.success(`Personagem "${name}" criado com sucesso!`);
              } catch (err) {
                console.error('❌ [SAVE] Failed to save avatar to gallery:', err);
                console.error('❌ [SAVE] Error details:', err.response?.data);
                toast.error('Erro ao salvar personagem: ' + (err.response?.data?.detail || err.message));
                return; // Don't continue if gallery save failed
              }
              
              // 4. If there's a selected project, also add to project
              if (selectedProject?.id) {
                try {
                  console.log('📡 [PROJECT] Adding avatar to project:', selectedProject.id);
                  const response = await axios.post(`${API}/studio/projects/${selectedProject.id}/project-avatars/import`, {
                    avatar_ids: [newAvatar.id]
                  });
                  console.log('✅ [PROJECT] Response:', response.data);
                  console.log('✅ [PROJECT] Avatar added to project');
                  toast.success(`Personagem adicionado ao projeto!`);
                  
                  // Dispatch event to refresh DirectedStudio avatars
                  window.dispatchEvent(new CustomEvent('avatarCreated', { 
                    detail: { avatar: newAvatar, projectId: selectedProject.id } 
                  }));
                  console.log('📢 [EVENT] avatarCreated dispatched');
                } catch (err) {
                  console.error('❌ [PROJECT] Failed to add avatar to project:', err);
                  console.error('❌ [PROJECT] Error details:', err.response?.data);
                  // Don't show error - avatar is already in gallery
                }
              }
              
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
                prompt: tempAvatar.prompt || '',  // Incluir prompt
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              };
              
              console.log('✅ New avatar created:', newAvatar);
              
              // 1. Save to GLOBAL gallery (tenant avatars)
              try {
                const response = await axios.post(`${API}/data/avatars`, newAvatar);
                console.log('✅ Avatar saved to global gallery:', response.data);
                
                // 2. Add to local state (avatars cache)
                const updatedAvatars = [...avatars, newAvatar];
                setAvatars(updatedAvatars);
                setAvatarsLoaded(true);
                
                // 3. Update localStorage cache
                localStorage.setItem('studiox_avatars_cache', JSON.stringify(updatedAvatars));
                
                toast.success(`Personagem "${name}" criado com sucesso!`);
              } catch (err) {
                console.error('❌ Failed to save avatar to gallery:', err);
                toast.error('Erro ao salvar personagem: ' + (err.response?.data?.detail || err.message));
                return; // Don't continue if gallery save failed
              }
              
              // 4. If there's a selected project, also add to project
              if (selectedProject?.id) {
                try {
                  const response = await axios.post(`${API}/studio/projects/${selectedProject.id}/project-avatars/import`, {
                    avatar_ids: [newAvatar.id]
                  });
                  console.log('✅ Avatar added to project:', response.data);
                  toast.success(`Personagem adicionado ao projeto!`);
                } catch (err) {
                  console.error('❌ Failed to add avatar to project:', err);
                  // Don't show error - avatar is already in gallery
                }
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
  const isGalleryPage = searchParams.get('gallery') === '1';

  return (
    <div className="min-h-screen bg-[#FAFAFC] dark:bg-[#0A0614]" style={{ fontFamily: "'Outfit', system-ui" }}>
      {!isGalleryPage && (
      <>
      {/* ═══ CONTEXT BAR (pinned under global app header) ═══ */}
      <div className="sticky top-0 z-20 bg-white dark:bg-[#0A0614] border-b border-gray-200 dark:border-[#2A2442]">
        <div className="max-w-7xl mx-auto px-6 h-12 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <h1 className="text-[15px] font-semibold tracking-tight text-gray-900 dark:text-white">Projetos</h1>
            <span className="text-[10px] font-mono text-gray-400 dark:text-[#6B647F]">{projects.length}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => { setAvatarPreviewUrl(null); setShowGlobalLibrary(true); }}
              className="hidden sm:inline-flex items-center gap-1 h-7 px-2.5 rounded-md text-[11px] font-medium text-violet-700 dark:text-violet-300 bg-violet-50 dark:bg-violet-500/10 hover:bg-violet-100 dark:hover:bg-violet-500/20 border border-violet-100 dark:border-violet-500/20 transition"
              data-testid="btn-global-library"
            >
              <BookOpen size={12} /> Galeria
            </button>
            <button
              onClick={openNewProjectModal}
              disabled={creating}
              data-testid="btn-new-project"
              className="h-7 px-3 rounded-md bg-gradient-to-r from-orange-500 to-orange-600 text-white text-[11px] font-semibold hover:brightness-110 transition flex items-center gap-1 shadow-[0_0_12px_rgba(249,115,22,0.25)] disabled:opacity-50"
            >
              <Plus size={12} strokeWidth={2.5} /> Novo Projeto
            </button>
          </div>
        </div>
      </div>

      {/* ═══ CONTENT ═══ */}
      <div className="px-6 py-5 pb-28">
        <div className="max-w-7xl mx-auto">
          {/* Company Selector — compact chip (expandable) */}
          {!selectedProject && companies.length > 0 && (
            <div className="mb-4">
              <button
                onClick={() => setShowCompanySelector(!showCompanySelector)}
                data-testid="company-chip"
                className="inline-flex items-center gap-2 text-xs rounded-full border border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#1A1430] hover:border-violet-300 dark:hover:border-violet-500/40 px-3 py-1.5 transition group"
              >
                <Users size={13} className="text-violet-500" />
                <span className="text-gray-500 dark:text-[#A3A3B2]">Empresa:</span>
                <span className="font-semibold text-gray-900 dark:text-white truncate max-w-[240px]">
                  {selectedCompany ? selectedCompany.name : 'Nenhuma selecionada'}
                </span>
                <ChevronRight
                  size={12}
                  className={`text-gray-400 group-hover:text-violet-500 transition-transform ${showCompanySelector ? 'rotate-90' : ''}`}
                />
              </button>

              {/* Company List (collapsible) */}
              {showCompanySelector && (
                <div className="mt-3 grid gap-2 bg-gray-50 dark:bg-[#110A1F] rounded-xl p-3 border border-gray-200 dark:border-[#2A2442]" data-testid="company-list">
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
                          ? 'border-orange-500 bg-orange-50'
                          : 'border-gray-200 bg-white hover:border-orange-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{company.name}</p>
                          {company.phone && (
                            <p className="text-xs text-gray-500 mt-0.5">{company.phone}</p>
                          )}
                        </div>
                        {company.is_primary && (
                          <span className="text-[9px] bg-orange-100 text-orange-600 px-2 py-0.5 rounded-full font-semibold">
                            PRINCIPAL
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                  <button
                    onClick={() => navigate('/marketing')}
                    className="p-3 rounded-lg border border-dashed border-gray-300 hover:border-orange-400 text-gray-500 hover:text-orange-600 transition text-sm"
                  >
                    + Gerenciar Empresas
                  </button>
                </div>
              )}
            </div>
          )}
          
          {/* Search */}
          <div className="mb-4">
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

          {/* Type Filter Pills */}
          <div className="mb-6 flex items-center gap-2 flex-wrap" data-testid="project-type-filter">
            {[
              { key: 'all', label: 'Tudo', icon: Folder, count: projectCounts.all },
              { key: 'video', label: 'Vídeos', icon: Video, count: projectCounts.video },
              { key: 'book', label: 'Livros', icon: BookOpen, count: projectCounts.book },
              { key: 'both', label: 'Híbridos', icon: Layers, count: projectCounts.both },
            ].map(({ key, label, icon: Icon, count }) => {
              const active = projectTypeFilter === key;
              return (
                <button
                  key={key}
                  onClick={() => setProjectTypeFilter(key)}
                  data-testid={`filter-${key}`}
                  disabled={count === 0 && key !== 'all'}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                    active
                      ? 'bg-orange-500 text-white border-orange-500 shadow-sm'
                      : 'bg-white text-gray-700 border-gray-200 hover:border-orange-300 hover:bg-orange-50'
                  } ${count === 0 && key !== 'all' ? 'opacity-40 cursor-not-allowed' : ''}`}
                >
                  <Icon size={12} />
                  {label}
                  <span className={`ml-0.5 font-mono text-[10px] px-1.5 py-0.5 rounded-full ${
                    active ? 'bg-white/25 text-white' : 'bg-gray-100 text-gray-600'
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
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
          <div className="space-y-1.5" data-testid="project-list">
            {filteredProjects.map((project) => (
              <ProjectRow
                key={project.id}
                project={project}
                onSelect={handleSelectProject}
                onDelete={handleDeleteProject}
                onRename={handleRenameProject}
                onSyncCharacters={handleSyncCharacters}
              />
            ))}
          </div>
        )}
        </div>
      </div>
      </>
      )}
      
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

      {/* ═══════ GLOBAL CHARACTER LIBRARY MODAL (Must be BEFORE AvatarModal in DOM) ═══════ */}
      <AvatarLibraryModalV2
        open={showGlobalLibrary}
        embedded={isGalleryPage}
        onClose={() => {
          setShowGlobalLibrary(false);
          if (searchParams.get('gallery')) {
            const sp = new URLSearchParams(searchParams);
            sp.delete('gallery');
            setSearchParams(sp, { replace: true });
          }
        }}
        projectId={null}
        projectAvatarIds={new Set()}
        avatarsCache={avatars}
        avatarsCacheLoaded={avatarsLoaded}
        onCreateNew={() => {
          console.log('✅ Creating new character from global library');
          setShowGlobalLibrary(false); // Close gallery
          setShowAvatarModal(true); // Open creation modal
        }}
        onImported={(importedAvatars) => {
          console.log('✅ Avatars viewed in global library:', importedAvatars.length);
          toast.success(`Visualizando ${importedAvatars.length} personagens!`);
        }}
        onEditAvatar={(avatar) => {
          console.log('✅ Editing avatar from global library:', avatar.name);
          // Galeria permanece aberta, modal abre NA FRENTE com z-[99999]
          setEditingAvatarId(avatar.id);
          
          // Infer avatar_style from creation_mode for avatars saved before the fix
          let inferredStyle = avatar.avatar_style || 'realistic';
          if (!avatar.avatar_style && avatar.creation_mode === '3d') {
            inferredStyle = '3d_pixar';
          }
          const is3dAvatar = inferredStyle !== 'realistic';
          
          setTempAvatar({
            url: avatar.url,
            source_photo_url: avatar.source_photo_url || '',
            clothing: avatar.clothing || 'company_uniform',
            voice: avatar.voice || null,
            avatar_style: inferredStyle,
            creation_mode: avatar.creation_mode || 'photo',
            prompt: avatar.prompt || '', // Incluir prompt para exibir botão de copiar
          });
          
          setAvatarName(avatar.name || '');
          setPreviewVideoUrl(avatar.video_url || null);
          setAvatarMediaTab(avatar.video_url ? 'photo' : 'photo');
          
          // For 3D avatars, only load angles that were generated with 3D style
          const savedAngles = avatar.angles || {};
          if (is3dAvatar && savedAngles.front && savedAngles.front !== avatar.url) {
            setAngleImages({ front: avatar.url });
          } else {
            setAngleImages(savedAngles.front ? savedAngles : { front: avatar.url });
          }
          
          // Load saved language
          setPreviewLanguage(avatar.language || 'pt');
          
          // Restore audio from saved voice
          if (avatar.voice?.url) {
            setRecordedAudioUrl(avatar.voice.url);
            setVoiceTab('record');
          } else if (avatar.voice?.type === 'elevenlabs' && avatar.voice?.voice_id) {
            setVoiceTab('premium');
          } else if (avatar.voice?.voice_id) {
            setVoiceTab('bank');
          }
          
          // Rebuild clothing variants from angles if available
          const variants = {};
          if (avatar.clothing && avatar.url) variants[avatar.clothing] = avatar.url;
          setClothingVariants(variants);
          
          setAvatarStage('customize');
          setCustomizeTab('clothing');
          setShowAvatarModal(true);
          
          // ABRIR "Editar com IA" por padrão
          setAiEditAvatarId('temp');
          
          console.log('✅ Avatar modal OPENED for editing:', avatar.name);
          
          // Load saved edit history or initialize with current avatar as base
          const savedHistory = avatar.edit_history && avatar.edit_history.length > 0 ? avatar.edit_history : [];
          if (savedHistory.length > 0) {
            setAvatarEditHistory(savedHistory);
            const baseEntry = savedHistory.find(e => e.isBase);
            setAvatarBaseUrl(baseEntry ? baseEntry.url : avatar.url);
          } else {
            setAvatarBaseUrl(avatar.url);
            setAvatarEditHistory([{ 
              url: avatar.url, 
              instruction: 'Base original', 
              timestamp: new Date().toISOString(), 
              isBase: true 
            }]);
          }
        }}
        onDeleteAvatar={async (avatar, skipConfirm = false) => {
          console.log('🗑️ [DELETE] Callback chamado para:', avatar.name, avatar.id);
          try {
            console.log('🗑️ [DELETE] Enviando DELETE para API...');
            await axios.delete(`${API}/data/avatars/${avatar.id}`);
            console.log('✅ [DELETE] Resposta 200 OK');
            
            // Only show individual toast if not batch (batch shows summary)
            if (!skipConfirm) {
              toast.success(`"${avatar.name}" excluído com sucesso!`);
            }
            
            // Update cache (remove from list) - no need to reload entire gallery
            console.log('🗑️ [DELETE] Removendo do cache...');
            removeAvatarFromCache(avatar.id);
            
            // Invalidate localStorage cache
            localStorage.removeItem('studiox_avatar_library_v2');
            console.log('🗑️ [DELETE] Cache invalidado');
            
            console.log('✅ [DELETE] Completo!');
          } catch (err) {
            console.error('❌ [DELETE] Erro:', err);
            console.error('❌ [DELETE] Response:', err.response);
            
            // Always show error toast
            toast.error('Erro ao excluir personagem: ' + (err.response?.data?.detail || err.message));
            throw err; // Re-throw for batch delete error counting
          }
        }}
        onCreateNew={() => {
          console.log('🎨 Creating new character from gallery');
          
          // EXACT COPY from PipelineView.jsx resetAvatarModal (lines 709-730)
          setEditingAvatarId(null);
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
          setCustomizeTab('clothing');
          setAvatarEditHistory([]);
          setAvatarBaseUrl(null);
          setAngleImages({});
          setClothingVariants({});
          setAuto360Progress(null);
          setRecordedAudioUrl(null);
          setRecordedAudioBlob(null);
          setAvatarName('');
          setPreviewVideoUrl(null);
          setAvatarPreviewUrl(null);
          setPreviewLanguage('pt');
          setVoiceTab('bank');
          setAvatarMediaTab('photo');
          
          // Now open modal
          setShowAvatarModal(true);
        }}
        lang={lang}
      />

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
            promptBatchMode,
            batchProgress,
            avatars,
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
            setApplyingClothing,
            setPromptBatchMode,
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
            generateAvatarBatch,
            saveAvatarAndClose: async () => {
              console.log('💾 Global saveAvatarAndClose');
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para salvar');
                return;
              }
              
              try {
                const payload = {
                  ...(editingAvatarId && { id: editingAvatarId }), // Include ID when editing to update instead of creating duplicate
                  url: tempAvatar.url,
                  name: avatarName || 'Novo Personagem',
                  avatar_style: tempAvatar.style || avatarPromptStyle || 'realistic',
                  creation_mode: avatarCreationMode || 'prompt',
                  source_photo_url: avatarSourcePhoto || '',
                  clothing: 'keep_original',
                  voice: tempAvatar.voice || null,
                  angles: angleImages || {},
                  video_url: previewVideoUrl || null,
                  language: previewLanguage || 'pt',
                  edit_history: avatarEditHistory || [],
                  prompt: tempAvatar.prompt || ''  // Incluir prompt
                };
                
                console.log('📡 Salvando personagem global:', payload);
                const response = await axios.post(`${API}/data/avatars`, payload);
                console.log('✅ Resposta do backend:', response.data);
                
                toast.success('✅ Personagem salvo na galeria!');
                
                // Update cache with new/edited avatar
                updateAvatarInCache(response.data);
                
                // Invalidate localStorage cache
                localStorage.removeItem('studiox_avatar_library_v2');
                console.log('🗑️ [SAVE] Gallery cache invalidated');
                
                // Fecha modal de criação
                resetAvatarModal();
                setShowAvatarModal(false);
              } catch (err) {
                console.error('❌ Error saving avatar:', err);
                console.error('❌ Error response:', err.response?.data);
                toast.error('Erro ao salvar personagem: ' + (err.response?.data?.detail || err.message));
              }
            },
            saveAvatarAsNew: async () => {
              console.log('💾 Global saveAvatarAsNew');
              
              if (!tempAvatar?.url) {
                toast.error('Nenhum avatar para salvar');
                return;
              }
              
              try {
                const payload = {
                  // Never include ID for saveAsNew - always create new avatar
                  url: tempAvatar.url,
                  name: avatarName || 'Novo Personagem',
                  avatar_style: tempAvatar.style || avatarPromptStyle || 'realistic',
                  creation_mode: avatarCreationMode || 'prompt',
                  source_photo_url: avatarSourcePhoto || '',
                  clothing: 'keep_original',
                  voice: tempAvatar.voice || null,
                  angles: angleImages || {},
                  video_url: previewVideoUrl || null,
                  language: previewLanguage || 'pt',
                  edit_history: avatarEditHistory || [],
                  prompt: tempAvatar.prompt || ''  // Incluir prompt
                };
                
                console.log('📡 Salvando novo personagem:', payload);
                const response = await axios.post(`${API}/data/avatars`, payload);
                console.log('✅ Resposta do backend:', response.data);
                
                toast.success('✅ Personagem criado e salvo na galeria!');
                
                // Update cache with new avatar
                updateAvatarInCache(response.data);
                
                // Invalidate localStorage cache
                localStorage.removeItem('studiox_avatar_library_v2');
                console.log('🗑️ [CREATE] Gallery cache invalidated');
                
                // Fecha modal de criação
                resetAvatarModal();
                setShowAvatarModal(false);
              } catch (err) {
                console.error('❌ Error saving new avatar:', err);
                console.error('❌ Error response:', err.response?.data);
                toast.error('Erro ao salvar personagem: ' + (err.response?.data?.detail || err.message));
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
                  language: previewLanguage || 'pt',
                  prompt: tempAvatar.prompt || ''  // Incluir prompt
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
            // FORÇA z-index MÁXIMO para aparecer por cima da galeria (z-[10000])
            zIndexOverride: 'z-[99999]',
          }}
        />
      )}
    </div>
  );
}
