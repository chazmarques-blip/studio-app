import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { 
  Film, Plus, Trash2, Clock, Layers, Users, Play, Folder, 
  ChevronRight, MoreHorizontal, Search, ArrowLeft, Eye,
  FileText, Palette, Video, CheckCircle2, Circle, Sparkles, Pencil, Check, X
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { DirectedStudio } from '../components/DirectedStudio';
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
      className="group relative flex items-center gap-5 p-4 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#8B5CF6]/30 hover:bg-[#0F0F0F] cursor-pointer transition-all"
    >
      {/* Thumbnail */}
      <div className="relative w-20 h-20 rounded-lg bg-gradient-to-br from-[#1A1A1A] to-[#0A0A0A] overflow-hidden shrink-0">
        {videoThumbnail ? (
          <img src={videoThumbnail} alt="" className="w-full h-full object-cover" />
        ) : thumbnail ? (
          <img src={resolveImageUrl(thumbnail)} alt="" className="w-full h-full object-cover" />
        ) : (
          <div className="flex items-center justify-center h-full">
            <Film size={24} className="text-[#555]" />
          </div>
        )}
        {firstVideo && (
          <div className="absolute bottom-1 right-1 bg-black/60 backdrop-blur-sm rounded px-1.5 py-0.5">
            <Video size={10} className="text-white" />
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
                className="flex-1 px-2 py-1 rounded bg-[#1A1A1A] border border-[#8B5CF6] text-sm text-white outline-none"
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
              <h3 className="text-sm font-semibold text-white truncate group-hover:text-[#A78BFA] transition-colors">
                {project.name}
              </h3>
              <button 
                onClick={handleStartEdit}
                className="p-1 rounded hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <Pencil size={12} className="text-white/70" />
              </button>
            </>
          )}
        </div>
        
        {/* Stats Row - CORES MAIS CLARAS */}
        <div className="flex items-center gap-4 text-xs text-white/70 mb-3">
          <span className="flex items-center gap-1.5">
            <Layers size={13} className="text-white/60" /> {scenesCount} cenas
          </span>
          <span className="flex items-center gap-1.5">
            <Users size={13} className="text-white/60" /> {charactersCount} personagens
          </span>
          {updatedAt && (
            <span className="flex items-center gap-1.5">
              <Clock size={13} className="text-white/60" /> {formatDate(updatedAt)}
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
                  : 'bg-[#1A1A1A] text-white/40'
              }`}
              title={step.label}
            >
              <step.icon size={12} />
            </div>
          ))}
          <span className="ml-2 text-xs text-white/60">
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
          <span className="absolute inset-0 flex items-center justify-center text-[11px] font-bold text-white">
            {progress.percent}%
          </span>
        </div>
        <span className={`text-[10px] font-medium ${
          progress.percent === 100 ? 'text-emerald-400' : 'text-white/60'
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
            <MoreHorizontal size={16} className="text-white/60" />
          </button>
          
          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={(e) => { e.stopPropagation(); setShowMenu(false); }} />
              <div className="absolute right-0 top-full mt-1 z-20 rounded-lg border border-[#2A2A2A] bg-[#111] shadow-xl py-1.5 min-w-[140px]">
                <button 
                  onClick={(e) => { e.stopPropagation(); handleStartEdit(e); setShowMenu(false); }}
                  className="w-full px-4 py-2 text-left text-sm text-white hover:bg-white/5 flex items-center gap-2"
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

  // Avatar management - dummy handlers for DirectedStudio
  const handleAddAvatar = (promptText) => {
    console.log('Add avatar:', promptText);
    // DirectedStudio will handle avatar creation internally via project avatars
  };
  
  const handleEditAvatar = (av) => {
    console.log('Edit avatar:', av);
    // DirectedStudio will handle editing internally
  };
  
  const handleRemoveAvatar = (av) => {
    console.log('Remove avatar:', av);
  };
  
  const handlePreviewAvatar = (url) => {
    console.log('Preview avatar:', url);
  };
  
  const handleAiEditAvatar = (id) => {
    console.log('AI edit avatar:', id);
  };

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
    const confirmDelete = window.confirm(l.deleteConfirm);
    if (!confirmDelete) return;
    
    try {
      console.log('🗑️ Deletando projeto:', project.id, project.name);
      await axios.delete(`${API}/studio/projects/${project.id}`);
      toast.success(l.deleted);
      
      // Se o projeto deletado está selecionado, voltar para lista
      if (selectedProject?.id === project.id) {
        setSelectedProject(null);
        setSearchParams({});
      }
      
      // Recarregar lista
      await fetchProjects();
      console.log('✅ Projeto deletado com sucesso');
    } catch (err) {
      console.error('❌ Erro ao excluir projeto:', err);
      toast.error('Erro ao excluir projeto: ' + (err.response?.data?.detail || err.message));
    }
  };

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
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#8B5CF6]" />
      </div>
    );
  }

  // If project is selected, show DirectedStudio
  if (selectedProject) {
    return (
      <div className="flex flex-col min-h-screen bg-[#0A0A0A]">
        {/* Back header */}
        <div className="shrink-0 border-b border-[#1A1A1A] bg-[#0A0A0A] px-6 sm:px-8 lg:px-12 py-4 flex items-center gap-4 sticky top-0 z-50">
          <button 
            onClick={handleBackToList}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#1A1A1A] hover:bg-[#222] text-sm text-white/80 hover:text-white transition"
          >
            <ArrowLeft size={18} /> {l.back}
          </button>
          <div className="h-6 w-px bg-[#2A2A2A]" />
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <Film size={18} className="text-[#8B5CF6] shrink-0" />
            <span className="text-base font-medium text-white truncate">{selectedProject.name}</span>
          </div>
        </div>
        
        {/* DirectedStudio */}
        <div className="flex-1 overflow-auto">
          <DirectedStudio 
            key={selectedProject.id} 
            projectId={selectedProject.id}
            onProjectUpdate={fetchProjects}
            onBack={handleBackToList}
            avatars={[]}
            onAddAvatar={handleAddAvatar}
            onEditAvatar={handleEditAvatar}
            onRemoveAvatar={handleRemoveAvatar}
            onPreviewAvatar={handlePreviewAvatar}
            onAiEditAvatar={handleAiEditAvatar}
            aiEditAvatarId={null}
            setAiEditAvatarId={() => {}}
            aiEditInstruction=""
            setAiEditInstruction={() => {}}
            aiEditLoading={false}
            lastCreatedAvatar={null}
          />
        </div>
      </div>
    );
  }

  // Project List View
  return (
    <div className="min-h-screen bg-[#0A0A0A] px-6 sm:px-8 lg:px-12 py-6 pb-28">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-[#8B5CF6] to-[#7C3AED] shadow-lg shadow-[#8B5CF6]/20">
                <Film size={22} className="text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">{l.title}</h1>
                <p className="text-sm text-white/60">{l.subtitle}</p>
              </div>
            </div>
            <span className="text-sm text-white/70 bg-[#1A1A1A] px-3 py-1.5 rounded-lg">
              {projects.length} {l.projects.toLowerCase()}
            </span>
          </div>
        </div>

        {/* Search + New Project */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 relative">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/50" />
            <input 
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={l.search}
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] text-sm text-white placeholder-white/40 outline-none focus:border-[#8B5CF6]/50 transition"
            />
          </div>
          <button 
            onClick={openNewProjectModal}
            disabled={creating}
            className="btn-gold flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold disabled:opacity-50"
          >
            <Plus size={18} /> {l.newProject}
          </button>
        </div>

        {/* Projects List */}
        {filteredProjects.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-[#1A1A1A] mb-6">
              <Folder size={36} className="text-white/30" />
            </div>
            <h2 className="text-lg font-semibold text-white mb-2">{l.noProjects}</h2>
            <p className="text-sm text-white/60 mb-6 max-w-sm">{l.createFirst}</p>
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
      
      {/* New Project Modal */}
      {showNewProjectModal && (
        <NewProjectModal
          lang={lang}
          onClose={() => setShowNewProjectModal(false)}
          onCreate={handleCreateProject}
        />
      )}
    </div>
  );
}
