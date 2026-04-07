import React from 'react';
import { 
  FileText, Users, Palette, Film, Music, Wand2, 
  CheckCircle2, Clock, AlertCircle, Loader2, Sparkles 
} from 'lucide-react';

/**
 * PipelineVisualTracker - Real-time visual timeline of all agents working
 * 
 * Shows:
 * - All agents (Screenwriter, Content Advisors, Director, etc.)
 * - Current status of each agent
 * - Progress bars with time estimates
 * - Visual indicators for: waiting, processing, completed, error
 */

const AGENT_DEFINITIONS = [
  {
    id: 'researcher_screenwriter',
    name: 'Redator & Pesquisador',
    icon: FileText,
    color: '#8B5CF6',
    description: 'Criando roteiro e pesquisando personagens',
    estimatedTime: 120, // 2 minutes
  },
  {
    id: 'character_library',
    name: 'Biblioteca de Personagens',
    icon: Users,
    color: '#3B82F6',
    description: 'Sincronizando personagens da pasta master',
    estimatedTime: 10,
  },
  {
    id: 'toddler_advisor',
    name: 'Toddler Content Advisor',
    icon: Sparkles,
    color: '#F59E0B',
    description: 'Adaptando linguagem para 2-5 anos',
    estimatedTime: 45,
  },
  {
    id: 'musical_advisor',
    name: 'Musical Composer',
    icon: Music,
    color: '#EC4899',
    description: 'Transformando história em música chiclete',
    estimatedTime: 60,
  },
  {
    id: 'narration_advisor',
    name: 'Narration Style Advisor',
    icon: Palette,
    color: '#10B981',
    description: 'Adicionando marcações de voz e entonação',
    estimatedTime: 30,
  },
  {
    id: 'director',
    name: 'Diretor de Cena',
    icon: Film,
    color: '#6366F1',
    description: 'Criando prompts visuais com Identity Cards',
    estimatedTime: 180, // 3 minutes
  },
  {
    id: 'music_generation',
    name: 'Geração de Música',
    icon: Music,
    color: '#8B5CF6',
    description: 'Gerando música com ElevenLabs',
    estimatedTime: 120,
  },
  {
    id: 'video_generation',
    name: 'Geração de Vídeo',
    icon: Film,
    color: '#DC2626',
    description: 'Gerando vídeos com Sora 2',
    estimatedTime: 600, // 10 minutes total
  },
];

const STATUS_CONFIG = {
  waiting: {
    label: 'Aguardando',
    icon: Clock,
    color: '#6B7280',
    bgColor: 'bg-gray-500/10',
    textColor: 'text-gray-400',
    borderColor: 'border-gray-500/20',
  },
  processing: {
    label: 'Processando',
    icon: Loader2,
    color: '#8B5CF6',
    bgColor: 'bg-purple-500/10',
    textColor: 'text-purple-400',
    borderColor: 'border-purple-500/30',
    animate: true,
  },
  completed: {
    label: 'Concluído',
    icon: CheckCircle2,
    color: '#10B981',
    bgColor: 'bg-green-500/10',
    textColor: 'text-green-400',
    borderColor: 'border-green-500/30',
  },
  error: {
    label: 'Erro',
    icon: AlertCircle,
    color: '#EF4444',
    bgColor: 'bg-red-500/10',
    textColor: 'text-red-400',
    borderColor: 'border-red-500/30',
  },
  skipped: {
    label: 'Desabilitado',
    icon: null,
    color: '#374151',
    bgColor: 'bg-gray-800/30',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-700/20',
  },
};

function AgentCard({ agent, status, progress = 0, elapsedTime = 0, message = '' }) {
  const statusConfig = STATUS_CONFIG[status] || STATUS_CONFIG.waiting;
  const Icon = agent.icon;
  const StatusIcon = statusConfig.icon;
  
  // Calculate remaining time
  const remaining = Math.max(agent.estimatedTime - elapsedTime, 0);
  const remainingFormatted = remaining > 60 
    ? `~${Math.ceil(remaining / 60)}min` 
    : `~${remaining}s`;
  
  // Progress percentage (capped at 95% until completed)
  const progressPct = status === 'completed' 
    ? 100 
    : Math.min((elapsedTime / agent.estimatedTime) * 100, 95);

  return (
    <div 
      className={`relative rounded-xl border ${statusConfig.borderColor} ${statusConfig.bgColor} p-4 transition-all duration-300`}
      style={{
        opacity: status === 'skipped' ? 0.5 : 1,
      }}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        {/* Agent Icon */}
        <div 
          className="w-10 h-10 rounded-lg flex items-center justify-center shrink-0"
          style={{
            backgroundColor: `${agent.color}15`,
            color: agent.color,
          }}
        >
          <Icon size={20} />
        </div>
        
        {/* Agent Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h4 className="text-sm font-semibold text-white truncate">
              {agent.name}
            </h4>
            {/* Status Badge */}
            <span 
              className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${statusConfig.textColor}`}
              style={{ backgroundColor: `${statusConfig.color}15` }}
            >
              {StatusIcon && (
                <StatusIcon 
                  size={10} 
                  className={statusConfig.animate ? 'animate-spin' : ''} 
                />
              )}
              {statusConfig.label}
            </span>
          </div>
          
          <p className="text-xs text-gray-400 truncate">
            {message || agent.description}
          </p>
        </div>
      </div>

      {/* Progress Bar (only for processing/completed) */}
      {(status === 'processing' || status === 'completed') && (
        <div className="space-y-1.5">
          {/* Time Info */}
          {status === 'processing' && (
            <div className="flex items-center justify-between text-[10px]">
              <span className="text-gray-500">
                {elapsedTime}s decorrido
              </span>
              <span className="text-gray-500">
                {remainingFormatted} restante
              </span>
            </div>
          )}
          
          {/* Progress Bar */}
          <div className="h-1.5 rounded-full bg-gray-800/50 overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-1000 ease-linear relative"
              style={{ 
                width: `${progressPct}%`,
                backgroundColor: agent.color,
              }}
            >
              {status === 'processing' && (
                <div 
                  className="absolute inset-0 opacity-30 animate-pulse"
                  style={{ backgroundColor: agent.color }}
                />
              )}
            </div>
          </div>
          
          {/* Progress Percentage */}
          {status === 'processing' && (
            <div className="text-right">
              <span className="text-[10px] font-bold text-white">
                {Math.round(progressPct)}%
              </span>
            </div>
          )}
        </div>
      )}
      
      {/* Shimmer Effect for Processing */}
      {status === 'processing' && (
        <div 
          className="absolute inset-0 rounded-xl overflow-hidden pointer-events-none"
          style={{
            background: `linear-gradient(90deg, transparent, ${agent.color}10, transparent)`,
            animation: 'shimmer 2s infinite',
          }}
        />
      )}
    </div>
  );
}

export function PipelineVisualTracker({ 
  pipelineStatus = {}, 
  enabledAdvisors = [],
  currentAgent = null,
  projectConfig = {}
}) {
  /**
   * pipelineStatus format:
   * {
   *   researcher_screenwriter: { status: 'completed', progress: 100, elapsedTime: 95, message: '' },
   *   toddler_advisor: { status: 'processing', progress: 60, elapsedTime: 27, message: 'Simplificando vocabulário...' },
   *   musical_advisor: { status: 'waiting', progress: 0, elapsedTime: 0 },
   *   ...
   * }
   */

  // Filter agents based on enabled advisors
  const activeAgents = AGENT_DEFINITIONS.filter(agent => {
    // Core agents always shown
    if (['researcher_screenwriter', 'character_library', 'director'].includes(agent.id)) {
      return true;
    }
    
    // Content Advisors - only if enabled
    if (agent.id === 'toddler_advisor') {
      return enabledAdvisors.includes('toddler_content');
    }
    if (agent.id === 'musical_advisor') {
      return enabledAdvisors.includes('musical_composer');
    }
    if (agent.id === 'narration_advisor') {
      return enabledAdvisors.includes('narration_style');
    }
    
    // Music/Video generation - only if musical advisor is active
    if (agent.id === 'music_generation' || agent.id === 'video_generation') {
      return enabledAdvisors.includes('musical_composer');
    }
    
    return true;
  });

  // Calculate overall progress
  const completedCount = activeAgents.filter(
    agent => pipelineStatus[agent.id]?.status === 'completed'
  ).length;
  const totalAgents = activeAgents.length;
  const overallProgress = totalAgents > 0 
    ? Math.round((completedCount / totalAgents) * 100) 
    : 0;

  return (
    <div className="w-full h-full flex flex-col bg-[#0A0A0A] rounded-xl border border-gray-800/50">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800/50">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Wand2 size={16} className="text-purple-400" />
            Pipeline de Produção
          </h3>
          <div className="text-right">
            <span className="text-lg font-bold text-white">{overallProgress}%</span>
            <span className="text-xs text-gray-500 ml-1">completo</span>
          </div>
        </div>
        
        {/* Overall Progress Bar */}
        <div className="h-2 rounded-full bg-gray-800/50 overflow-hidden">
          <div 
            className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        
        {/* Agent Count */}
        <div className="flex items-center gap-4 mt-2 text-[10px] text-gray-500">
          <span>{completedCount} de {totalAgents} agentes concluídos</span>
          {currentAgent && (
            <span className="text-purple-400 flex items-center gap-1">
              <Loader2 size={10} className="animate-spin" />
              Atual: {AGENT_DEFINITIONS.find(a => a.id === currentAgent)?.name}
            </span>
          )}
        </div>
      </div>

      {/* Agent Cards */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {activeAgents.map(agent => {
          const agentStatus = pipelineStatus[agent.id] || { 
            status: 'waiting', 
            progress: 0, 
            elapsedTime: 0,
            message: '' 
          };
          
          return (
            <AgentCard
              key={agent.id}
              agent={agent}
              status={agentStatus.status}
              progress={agentStatus.progress}
              elapsedTime={agentStatus.elapsedTime}
              message={agentStatus.message}
            />
          );
        })}
      </div>

      {/* Add shimmer animation keyframes */}
      <style jsx>{`
        @keyframes shimmer {
          0% { transform: translateX(-100%); }
          100% { transform: translateX(100%); }
        }
      `}</style>
    </div>
  );
}

export default PipelineVisualTracker;
