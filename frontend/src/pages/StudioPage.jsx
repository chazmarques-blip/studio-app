import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Film, Plus, ChevronDown, Trash2, MoreHorizontal, Clock, Layers, Users, Play, Folder } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { DirectedStudio } from '../components/DirectedStudio';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── Project Card ── */
function ProjectCard({ project, isSelected, onSelect, onDelete }) {
  const [showMenu, setShowMenu] = useState(false);
  const thumbnail = project.scenes?.[0]?.panels?.[0]?.image_url;
  const progress = calculateProgress(project);
  const updatedAt = project.updated_at ? new Date(project.updated_at).toLocaleDateString() : '';
  
  return (
    <div 
      onClick={() => onSelect(project)}
      className={`group relative cursor-pointer rounded-xl border p-3 transition-all ${
        isSelected 
          ? 'border-[#8B5CF6]/50 bg-[#8B5CF6]/5' 
          : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#2A2A2A]'
      }`}
    >
      {/* Thumbnail */}
      <div className="relative h-20 rounded-lg bg-gradient-to-br from-[#1A1A1A] to-[#0A0A0A] overflow-hidden mb-2">
        {thumbnail ? (
          <img src={resolveImageUrl(thumbnail)} alt="" className="w-full h-full object-cover opacity-80" />
        ) : (
          <div className="flex items-center justify-center h-full">
            <Film size={20} className="text-[#333]" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        {/* Progress badge */}
        <div className="absolute top-1.5 right-1.5">
          <span className={`px-1.5 py-0.5 rounded text-[8px] font-semibold ${
            progress === 100 ? 'bg-emerald-500/20 text-emerald-400' :
            progress > 0 ? 'bg-[#8B5CF6]/20 text-[#8B5CF6]' :
            'bg-white/10 text-[#888]'
          }`}>
            {progress}%
          </span>
        </div>
      </div>
      
      {/* Info */}
      <h3 className="text-xs font-semibold text-white truncate mb-1">{project.name}</h3>
      <div className="flex items-center gap-2 text-[9px] text-[#666]">
        <span className="flex items-center gap-0.5">
          <Layers size={9} /> {project.scenes?.length || 0}
        </span>
        <span className="flex items-center gap-0.5">
          <Users size={9} /> {project.characters?.length || 0}
        </span>
        {updatedAt && (
          <span className="flex items-center gap-0.5 ml-auto">
            <Clock size={9} /> {updatedAt}
          </span>
        )}
      </div>
      
      {/* Progress bar */}
      <div className="mt-2 h-1 rounded-full bg-[#1A1A1A] overflow-hidden">
        <div 
          className="h-full rounded-full bg-gradient-to-r from-[#8B5CF6] to-[#A78BFA] transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Menu button */}
      <button 
        onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu); }}
        className="absolute top-2 left-2 p-1 rounded bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <MoreHorizontal size={12} className="text-white" />
      </button>
      
      {/* Dropdown menu */}
      {showMenu && (
        <div className="absolute top-8 left-2 z-10 rounded-lg border border-[#2A2A2A] bg-[#111] shadow-xl py-1 min-w-[120px]">
          <button 
            onClick={(e) => { e.stopPropagation(); onDelete(project); setShowMenu(false); }}
            className="w-full px-3 py-1.5 text-left text-xs text-red-400 hover:bg-red-500/10 flex items-center gap-2"
          >
            <Trash2 size={12} /> Excluir
          </button>
        </div>
      )}
    </div>
  );
}

function calculateProgress(project) {
  if (!project) return 0;
  let steps = 0, completed = 0;
  
  steps++; if (project.script || project.synopsis) completed++;
  steps++; if (project.characters?.length > 0) completed++;
  steps++; if (project.scenes?.some(s => s.dialogues?.length > 0)) completed++;
  steps++; if (project.scenes?.some(s => s.panels?.some(p => p.image_url))) completed++;
  steps++; if (project.scenes?.some(s => s.panels?.some(p => p.video_url))) completed++;
  
  return Math.round((completed / steps) * 100);
}

export default function StudioPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { i18n } = useTranslation();
  const lang = i18n.language?.startsWith('pt') ? 'pt' : i18n.language?.startsWith('es') ? 'es' : 'en';

  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSidebar, setShowSidebar] = useState(true);
  const [creating, setCreating] = useState(false);

  const L = {
    pt: {
      title: 'Estúdio',
      projects: 'Projetos',
      newProject: 'Novo Projeto',
      noProjects: 'Nenhum projeto',
      createFirst: 'Crie seu primeiro projeto',
      deleteConfirm: 'Tem certeza que deseja excluir este projeto?',
      deleted: 'Projeto excluído',
      created: 'Projeto criado',
    },
    en: {
      title: 'Studio',
      projects: 'Projects',
      newProject: 'New Project',
      noProjects: 'No projects',
      createFirst: 'Create your first project',
      deleteConfirm: 'Are you sure you want to delete this project?',
      deleted: 'Project deleted',
      created: 'Project created',
    },
    es: {
      title: 'Estudio',
      projects: 'Proyectos',
      newProject: 'Nuevo Proyecto',
      noProjects: 'Sin proyectos',
      createFirst: 'Crea tu primer proyecto',
      deleteConfirm: '¿Estás seguro de que quieres eliminar este proyecto?',
      deleted: 'Proyecto eliminado',
      created: 'Proyecto creado',
    },
  };
  const l = L[lang] || L.en;

  // Fetch projects
  const fetchProjects = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/studio/projects`);
      const projectsList = Array.isArray(data) ? data : data?.projects || [];
      setProjects(projectsList);
      
      // Auto-select project from URL or first one
      const projectId = searchParams.get('project');
      if (projectId) {
        const found = projectsList.find(p => p.id === projectId);
        if (found) setSelectedProject(found);
      } else if (projectsList.length > 0 && !selectedProject) {
        setSelectedProject(projectsList[0]);
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
  const handleCreateProject = async () => {
    setCreating(true);
    try {
      const { data } = await axios.post(`${API}/studio/projects`, {
        name: `Novo Projeto ${projects.length + 1}`,
        genre: 'drama',
        duration_minutes: 5,
        mode: 'film'
      });
      toast.success(l.created);
      await fetchProjects();
      setSelectedProject(data);
      setSearchParams({ project: data.id });
    } catch (err) {
      toast.error('Erro ao criar projeto');
    } finally {
      setCreating(false);
    }
  };

  // Delete project
  const handleDeleteProject = async (project) => {
    if (!confirm(l.deleteConfirm)) return;
    try {
      await axios.delete(`${API}/studio/projects/${project.id}`);
      toast.success(l.deleted);
      if (selectedProject?.id === project.id) {
        setSelectedProject(null);
        setSearchParams({});
      }
      await fetchProjects();
    } catch (err) {
      toast.error('Erro ao excluir projeto');
    }
  };

  // Select project
  const handleSelectProject = (project) => {
    setSelectedProject(project);
    setSearchParams({ project: project.id });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#8B5CF6]" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#0A0A0A]">
      {/* Sidebar - Project List */}
      <div className={`${showSidebar ? 'w-64' : 'w-0'} shrink-0 border-r border-[#1A1A1A] bg-[#0A0A0A] transition-all overflow-hidden`}>
        <div className="h-full flex flex-col p-3">
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#8B5CF6] to-[#7C3AED]">
                <Film size={14} className="text-white" />
              </div>
              <span className="text-sm font-semibold text-white">{l.projects}</span>
            </div>
            <span className="text-[10px] text-[#666] bg-[#1A1A1A] px-1.5 py-0.5 rounded">{projects.length}</span>
          </div>

          {/* New Project Button */}
          <button 
            onClick={handleCreateProject}
            disabled={creating}
            className="mb-3 flex items-center justify-center gap-2 rounded-lg border border-dashed border-[#2A2A2A] py-2.5 text-xs text-[#888] hover:border-[#8B5CF6]/50 hover:text-[#8B5CF6] transition-all disabled:opacity-50"
          >
            {creating ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#8B5CF6] border-t-transparent" />
            ) : (
              <>
                <Plus size={14} /> {l.newProject}
              </>
            )}
          </button>

          {/* Project List */}
          <div className="flex-1 overflow-y-auto space-y-2 scrollbar-hide">
            {projects.length === 0 ? (
              <div className="text-center py-8">
                <Folder size={32} className="mx-auto mb-2 text-[#333]" />
                <p className="text-xs text-[#666]">{l.noProjects}</p>
                <p className="text-[10px] text-[#444]">{l.createFirst}</p>
              </div>
            ) : (
              projects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  isSelected={selectedProject?.id === project.id}
                  onSelect={handleSelectProject}
                  onDelete={handleDeleteProject}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Main Content - Directed Studio */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Toggle sidebar button */}
        <button 
          onClick={() => setShowSidebar(!showSidebar)}
          className="absolute top-3 left-3 z-20 p-1.5 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] hover:bg-[#222] transition lg:hidden"
        >
          <ChevronDown size={14} className={`text-white transition-transform ${showSidebar ? 'rotate-90' : '-rotate-90'}`} />
        </button>

        {selectedProject ? (
          <DirectedStudio 
            key={selectedProject.id} 
            projectId={selectedProject.id}
            onProjectUpdate={fetchProjects}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <Film size={48} className="mx-auto mb-4 text-[#333]" />
              <h2 className="text-lg font-semibold text-white mb-2">
                {lang === 'pt' ? 'Selecione um projeto' : lang === 'es' ? 'Selecciona un proyecto' : 'Select a project'}
              </h2>
              <p className="text-sm text-[#666] mb-4">
                {lang === 'pt' ? 'Ou crie um novo para começar' : lang === 'es' ? 'O crea uno nuevo para empezar' : 'Or create a new one to get started'}
              </p>
              <button 
                onClick={handleCreateProject}
                disabled={creating}
                className="btn-gold px-4 py-2 rounded-lg text-sm font-semibold disabled:opacity-50"
              >
                {creating ? 'Criando...' : l.newProject}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
