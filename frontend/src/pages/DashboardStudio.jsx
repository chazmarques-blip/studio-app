import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
  Film, Play, Plus, Clock, Sparkles, ArrowRight, 
  FileText, Users, Mic, Video, Settings, Layers,
  ChevronRight, MoreHorizontal, Calendar, Eye,
  Clapperboard, Palette, Volume2, Wand2
} from 'lucide-react';
import axios from 'axios';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── Motion variants ── */
const fadeUp = {
  hidden: { opacity: 0, y: 14 },
  visible: (d = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.4, delay: d * 0.06, ease: [0.25, 0.46, 0.45, 0.94] } }),
};

/* ── Studio Agent Card ── */
const AgentCard = ({ icon: Icon, name, role, description, color, onClick }) => (
  <button 
    onClick={onClick}
    className="group glass-card p-4 text-left transition-all hover:border-[#8B5CF6]/30 hover:bg-white/[0.02]"
  >
    <div className="flex items-start gap-3">
      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${color} transition-all group-hover:scale-105`}>
        <Icon size={18} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-white truncate">{name}</p>
        <p className="text-[10px] text-[#8B5CF6] font-mono mb-1">{role}</p>
        <p className="text-[10px] text-[#888] leading-relaxed line-clamp-2">{description}</p>
      </div>
      <ChevronRight size={14} className="text-[#444] group-hover:text-[#8B5CF6] transition-colors mt-1" />
    </div>
  </button>
);

/* ── Project Card ── */
const ProjectCard = ({ project, onClick }) => {
  const thumbnail = project.scenes?.[0]?.panels?.[0]?.image_url;
  const progress = calculateProgress(project);
  
  return (
    <button 
      onClick={onClick}
      className="group glass-card overflow-hidden text-left transition-all hover:border-[#8B5CF6]/30"
    >
      {/* Thumbnail */}
      <div className="relative h-24 bg-gradient-to-br from-[#1A1A1A] to-[#0A0A0A] overflow-hidden">
        {thumbnail ? (
          <img src={resolveImageUrl(thumbnail)} alt="" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
        ) : (
          <div className="flex items-center justify-center h-full">
            <Film size={24} className="text-[#333]" />
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0A0A0A] to-transparent" />
        <div className="absolute bottom-2 left-2 right-2">
          <p className="text-xs font-semibold text-white truncate">{project.name}</p>
        </div>
        {/* Status badge */}
        <div className="absolute top-2 right-2">
          <span className={`px-1.5 py-0.5 rounded text-[8px] font-semibold ${
            progress === 100 ? 'bg-emerald-500/20 text-emerald-400' :
            progress > 0 ? 'bg-[#8B5CF6]/20 text-[#8B5CF6]' :
            'bg-white/10 text-[#888]'
          }`}>
            {progress === 100 ? 'Concluído' : progress > 0 ? `${progress}%` : 'Novo'}
          </span>
        </div>
      </div>
      {/* Info */}
      <div className="p-2.5">
        <div className="flex items-center gap-2 text-[9px] text-[#666]">
          <span className="flex items-center gap-1">
            <Layers size={10} /> {project.scenes?.length || 0} cenas
          </span>
          <span className="flex items-center gap-1">
            <Users size={10} /> {project.characters?.length || 0} personagens
          </span>
        </div>
        {/* Progress bar */}
        <div className="mt-2 h-1 rounded-full bg-[#1A1A1A] overflow-hidden">
          <div 
            className="h-full rounded-full bg-gradient-to-r from-[#8B5CF6] to-[#A78BFA] transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </button>
  );
};

function calculateProgress(project) {
  if (!project) return 0;
  let steps = 0;
  let completed = 0;
  
  // Script
  steps++;
  if (project.script || project.synopsis) completed++;
  
  // Characters
  steps++;
  if (project.characters?.length > 0) completed++;
  
  // Dialogues
  steps++;
  if (project.scenes?.some(s => s.dialogues?.length > 0)) completed++;
  
  // Storyboard
  steps++;
  if (project.scenes?.some(s => s.panels?.some(p => p.image_url))) completed++;
  
  // Production
  steps++;
  if (project.scenes?.some(s => s.panels?.some(p => p.video_url))) completed++;
  
  return Math.round((completed / steps) * 100);
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'Bom dia';
  if (h < 18) return 'Boa tarde';
  return 'Boa noite';
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language?.startsWith('pt') ? 'pt' : i18n.language?.startsWith('es') ? 'es' : 'en';
  
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/studio/projects`).catch(() => ({ data: [] })),
      axios.get(`${API}/dashboard/stats`).catch(() => ({ data: {} }))
    ]).then(([projectsRes, statsRes]) => {
      // Ensure projects is always an array
      const projectsData = projectsRes.data;
      setProjects(Array.isArray(projectsData) ? projectsData : projectsData?.projects || []);
      setStats(statsRes.data);
      setLoading(false);
    });
  }, []);

  const L = {
    pt: {
      greeting: getGreeting(),
      subtitle: 'O que vamos criar hoje?',
      newProject: 'Novo Projeto',
      recentProjects: 'Projetos Recentes',
      viewAll: 'Ver todos',
      noProjects: 'Nenhum projeto ainda',
      startFirst: 'Crie seu primeiro vídeo com IA',
      studioAgents: 'Agentes do Estúdio',
      agentsDesc: 'Configure e ajuste os agentes de IA do seu estúdio',
      quickActions: 'Ações Rápidas',
      settings: 'Configurações',
      plan: 'Plano Atual',
      upgrade: 'Upgrade',
      projects: 'Projetos',
      characters: 'Personagens',
      videos: 'Vídeos',
    },
    en: {
      greeting: getGreeting() === 'Bom dia' ? 'Good morning' : getGreeting() === 'Boa tarde' ? 'Good afternoon' : 'Good evening',
      subtitle: 'What shall we create today?',
      newProject: 'New Project',
      recentProjects: 'Recent Projects',
      viewAll: 'View all',
      noProjects: 'No projects yet',
      startFirst: 'Create your first AI video',
      studioAgents: 'Studio Agents',
      agentsDesc: 'Configure and adjust your studio AI agents',
      quickActions: 'Quick Actions',
      settings: 'Settings',
      plan: 'Current Plan',
      upgrade: 'Upgrade',
      projects: 'Projects',
      characters: 'Characters',
      videos: 'Videos',
    },
    es: {
      greeting: getGreeting() === 'Bom dia' ? 'Buenos días' : getGreeting() === 'Boa tarde' ? 'Buenas tardes' : 'Buenas noches',
      subtitle: '¿Qué vamos a crear hoy?',
      newProject: 'Nuevo Proyecto',
      recentProjects: 'Proyectos Recientes',
      viewAll: 'Ver todos',
      noProjects: 'Sin proyectos aún',
      startFirst: 'Crea tu primer video con IA',
      studioAgents: 'Agentes del Estudio',
      agentsDesc: 'Configura y ajusta los agentes IA de tu estudio',
      quickActions: 'Acciones Rápidas',
      settings: 'Configuración',
      plan: 'Plan Actual',
      upgrade: 'Upgrade',
      projects: 'Proyectos',
      characters: 'Personajes',
      videos: 'Videos',
    },
  };
  const l = L[lang] || L.en;

  const studioAgents = [
    { 
      icon: FileText, 
      name: 'Screenwriter', 
      role: 'Roteirista IA',
      description: 'Cria roteiros profissionais com cenas, diálogos e direções.',
      color: 'bg-gradient-to-br from-blue-500 to-blue-600'
    },
    { 
      icon: Clapperboard, 
      name: 'Shot Director', 
      role: 'Diretor de Cenas',
      description: 'Gera prompts visuais e dirige cada quadro do storyboard.',
      color: 'bg-gradient-to-br from-purple-500 to-purple-600'
    },
    { 
      icon: Palette, 
      name: 'Continuity', 
      role: 'Diretor de Continuidade',
      description: 'Mantém consistência visual de personagens entre cenas.',
      color: 'bg-gradient-to-br from-pink-500 to-pink-600'
    },
    { 
      icon: Mic, 
      name: 'Voice Designer', 
      role: 'Design de Voz',
      description: 'Cria vozes únicas e expressivas para cada personagem.',
      color: 'bg-gradient-to-br from-amber-500 to-amber-600'
    },
    { 
      icon: Volume2, 
      name: 'Sound Agent', 
      role: 'Sonoplastia IA',
      description: 'Projeta paisagem sonora e efeitos para cada cena.',
      color: 'bg-gradient-to-br from-emerald-500 to-emerald-600'
    },
    { 
      icon: Video, 
      name: 'Producer', 
      role: 'Produtor IA',
      description: 'Gerencia pipeline de produção e exportação de vídeos.',
      color: 'bg-gradient-to-br from-red-500 to-red-600'
    },
  ];

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#8B5CF6]" />
      </div>
    );
  }

  const recentProjects = Array.isArray(projects) ? projects.slice(0, 4) : [];
  const totalCharacters = (Array.isArray(projects) ? projects : []).reduce((acc, p) => acc + (p.characters?.length || 0), 0);
  const totalVideos = (Array.isArray(projects) ? projects : []).reduce((acc, p) => {
    return acc + (p.scenes?.reduce((a, s) => a + (s.panels?.filter(p => p.video_url)?.length || 0), 0) || 0);
  }, 0);

  return (
    <div className="min-h-screen px-4 pt-4 pb-6 max-w-6xl mx-auto">
      {/* ── Header ── */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={0} className="mb-6">
        <h1 className="text-2xl font-bold text-white mb-1">
          {l.greeting}, {user?.email?.split('@')[0] || 'Creator'}
        </h1>
        <p className="text-sm text-[#888]">{l.subtitle}</p>
      </motion.div>

      {/* ── Quick Stats ── */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={1} className="mb-6 grid grid-cols-3 gap-3">
        {[
          { label: l.projects, value: projects.length, icon: Film },
          { label: l.characters, value: totalCharacters, icon: Users },
          { label: l.videos, value: totalVideos, icon: Video },
        ].map((stat, i) => (
          <div key={i} className="glass-card p-3 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#8B5CF6]/10">
              <stat.icon size={16} className="text-[#8B5CF6]" />
            </div>
            <div>
              <p className="text-lg font-bold text-white">{stat.value}</p>
              <p className="text-[10px] text-[#888]">{stat.label}</p>
            </div>
          </div>
        ))}
      </motion.div>

      {/* ── New Project CTA ── */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={2} className="mb-6">
        <button 
          onClick={() => navigate('/studio')}
          className="w-full group glass-card p-4 flex items-center gap-4 border-[#8B5CF6]/20 hover:border-[#8B5CF6]/40 hover:bg-[#8B5CF6]/[0.03] transition-all"
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-[#8B5CF6] to-[#7C3AED] shadow-lg shadow-[#8B5CF6]/20 group-hover:shadow-[#8B5CF6]/30 transition-all">
            <Plus size={22} className="text-white" />
          </div>
          <div className="flex-1 text-left">
            <p className="text-sm font-semibold text-white">{l.newProject}</p>
            <p className="text-[11px] text-[#888]">Roteiro → Storyboard → Vídeo com IA</p>
          </div>
          <ArrowRight size={18} className="text-[#8B5CF6] group-hover:translate-x-1 transition-transform" />
        </button>
      </motion.div>

      {/* ── Recent Projects ── */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={3} className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white">{l.recentProjects}</h2>
          {projects.length > 4 && (
            <button onClick={() => navigate('/marketing')} className="text-[10px] text-[#8B5CF6] hover:underline">
              {l.viewAll}
            </button>
          )}
        </div>
        
        {recentProjects.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {recentProjects.map((project) => (
              <ProjectCard 
                key={project.id} 
                project={project} 
                onClick={() => navigate(`/studio?project=${project.id}`)}
              />
            ))}
          </div>
        ) : (
          <div className="glass-card p-8 text-center">
            <Film size={32} className="mx-auto mb-3 text-[#333]" />
            <p className="text-sm text-[#888] mb-3">{l.noProjects}</p>
            <button 
              onClick={() => navigate('/marketing')}
              className="btn-gold px-4 py-2 rounded-lg text-xs font-semibold"
            >
              {l.startFirst}
            </button>
          </div>
        )}
      </motion.div>

      {/* ── Studio Agents ── */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={4} className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-white">{l.studioAgents}</h2>
            <p className="text-[10px] text-[#666]">{l.agentsDesc}</p>
          </div>
          <button 
            onClick={() => navigate('/agents')}
            className="text-[10px] text-[#8B5CF6] hover:underline flex items-center gap-1"
          >
            <Settings size={10} /> Configurar
          </button>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {studioAgents.map((agent, i) => (
            <AgentCard 
              key={i} 
              {...agent} 
              onClick={() => navigate('/agents')}
            />
          ))}
        </div>
      </motion.div>

      {/* ── Plan & Settings ── */}
      <motion.div initial="hidden" animate="visible" variants={fadeUp} custom={5}>
        <div className="glass-card p-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#8B5CF6]/10">
              <Sparkles size={14} className="text-[#8B5CF6]" />
            </div>
            <div>
              <p className="text-[9px] text-[#666]">{l.plan}</p>
              <p className="text-xs font-semibold text-white capitalize">{stats?.plan || 'free'}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => navigate('/settings')}
              className="p-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] transition"
            >
              <Settings size={14} className="text-[#888]" />
            </button>
            <button 
              onClick={() => navigate('/pricing')}
              className="btn-gold px-3 py-1.5 rounded-lg text-[10px] font-semibold"
            >
              {l.upgrade}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
