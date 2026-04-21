import { useState, useEffect } from 'react';
import { Users, Search, FileText, Film, Sparkles, CheckCircle2, Clock, RefreshCw, Minus, X, ChevronRight } from 'lucide-react';

// ── Enhanced Pipeline Visual Tracker ──
// Define phases OUTSIDE component to avoid re-creation on every render
export const PIPELINE_PHASES = {
  pt: [
    { id: 'library_sync', icon: Users, name: 'Biblioteca de Personagens', message: 'Sincronizando personagens da pasta "Biblizoo Baby"...', duration: 10, color: '#3B82F6' },
    { id: 'researcher', icon: Search, name: 'Pesquisador', message: '71 personagens encontrados! Pesquisando contexto histórico...', duration: 30, color: '#8B5CF6' },
    { id: 'screenwriter', icon: FileText, name: 'Redator', message: 'Criando roteiro usando personagens existentes...', duration: 60, color: '#EC4899' },
    { id: 'director', icon: Film, name: 'Diretor', message: 'Preparando prompts visuais e cenas...', duration: 20, color: '#10B981' }
  ],
  en: [
    { id: 'library_sync', icon: Users, name: 'Character Library', message: 'Syncing characters from "Biblizoo Baby" folder...', duration: 10, color: '#3B82F6' },
    { id: 'researcher', icon: Search, name: 'Researcher', message: '71 characters found! Researching historical context...', duration: 30, color: '#8B5CF6' },
    { id: 'screenwriter', icon: FileText, name: 'Screenwriter', message: 'Creating screenplay using existing characters...', duration: 60, color: '#EC4899' },
    { id: 'director', icon: Film, name: 'Director', message: 'Preparing visual prompts and scenes...', duration: 20, color: '#10B981' }
  ]
};

/**
 * PipelineTrackerInline — expanded/minimized/closed floating progress tracker.
 * Extracted from DirectedStudio.jsx to reduce monolithic size.
 */
export const PipelineTrackerInline = ({ lang, projectId, project, onRetryPhase, onNextStep }) => {
  const [trackerState, setTrackerState] = useState(() => {
    const saved = localStorage.getItem(`pipeline_tracker_${projectId}`);
    return saved || 'expanded';
  });

  const phases = PIPELINE_PHASES[lang] || PIPELINE_PHASES.pt;

  useEffect(() => {
    if (projectId) {
      localStorage.setItem(`pipeline_tracker_${projectId}`, trackerState);
    }
  }, [trackerState, projectId]);

  const getRealPhaseProgress = (phaseId) => {
    if (!project) return 0;
    const currentPhase = project.pipeline_phase || '';

    switch (phaseId) {
      case 'library_sync': {
        const library = project.character_library;
        if (library && library.total_characters > 0) return 100;
        if (currentPhase === 'library_sync') return 50;
        if (['researcher_screenwriter', 'researcher', 'screenwriter', 'director'].includes(currentPhase)) return 100;
        return 0;
      }
      case 'researcher': {
        const research = project.agents_output?.screenwriter?.research_notes;
        if (research) return 100;
        if (currentPhase === 'researcher_screenwriter') return 60;
        if (['screenwriter', 'director', 'screenwriter_done'].includes(currentPhase)) return 100;
        if (project.chat_status === 'done' && project.scenes?.length > 0) return 100;
        return 0;
      }
      case 'screenwriter': {
        const scenes = project.scenes || [];
        if (scenes.length > 0) return 100;
        if (currentPhase === 'researcher_screenwriter') return 40;
        if (currentPhase === 'screenwriter_done') return 100;
        if (project.chat_status === 'thinking') return 30;
        return 0;
      }
      case 'director': {
        const directorReview = project.director_review;
        const directorProgress = project.director_progress;
        if (directorReview) return 100;
        if (directorProgress) {
          const { scenes_processed = 0, total_scenes = 1 } = directorProgress;
          return Math.min(Math.round((scenes_processed / total_scenes) * 100), 98);
        }
        if (project.scenes?.length > 0 && project.chat_status === 'done') return 10;
        return 0;
      }
      default:
        return 0;
    }
  };

  const getPhaseStatus = (phaseId) => {
    const progress = getRealPhaseProgress(phaseId);
    if (progress === 100) return 'completed';
    if (progress > 0) return 'processing';
    return 'waiting';
  };

  const overallProgress = Math.round(
    phases.reduce((sum, phase) => sum + getRealPhaseProgress(phase.id), 0) / phases.length
  );
  const allPhasesComplete = phases.every(phase => getRealPhaseProgress(phase.id) === 100);

  if (trackerState === 'closed') return null;

  if (trackerState === 'minimized') {
    return (
      <div
        onClick={() => setTrackerState('expanded')}
        className="fixed bottom-4 right-4 z-50 cursor-pointer hover:scale-105 transition-transform"
        data-testid="pipeline-tracker-minimized"
      >
        <div className="relative">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg flex flex-col items-center justify-center text-white animate-pulse">
            <Sparkles size={16} className="mb-0.5" />
            <span className="text-[10px] font-bold">{overallProgress}%</span>
          </div>
          <svg className="absolute inset-0 w-14 h-14 -rotate-90">
            <circle cx="28" cy="28" r="26" stroke="rgba(255,255,255,0.3)" strokeWidth="2" fill="none" />
            <circle
              cx="28" cy="28" r="26" stroke="white" strokeWidth="2" fill="none"
              strokeDasharray={`${2 * Math.PI * 26}`}
              strokeDashoffset={`${2 * Math.PI * 26 * (1 - (overallProgress / 100))}`}
              className="transition-all duration-300"
            />
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 p-1.5 mb-1.5 shadow-sm" data-testid="pipeline-tracker-expanded">
      <div className="flex items-center justify-between mb-1 px-1">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 rounded-full bg-purple-500 flex items-center justify-center">
            <Sparkles size={8} className="text-white" />
          </div>
          <h3 className="text-[9px] font-bold text-gray-800">
            {lang === 'pt' ? 'Pipeline de Produção' : 'Production Pipeline'}
          </h3>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`text-xs font-bold ${allPhasesComplete ? 'text-green-600' : 'text-purple-600'}`}>{overallProgress}%</span>
          {allPhasesComplete && (<span className="text-[8px] font-bold text-green-600">✓ COMPLETO</span>)}
          <div className="flex items-center gap-0.5 ml-1">
            <button
              onClick={() => setTrackerState('minimized')}
              className="w-4 h-4 rounded flex items-center justify-center hover:bg-purple-200 transition-colors"
              title={lang === 'pt' ? 'Minimizar' : 'Minimize'}
              data-testid="pipeline-tracker-minimize-btn"
            >
              <Minus size={10} className="text-gray-600" />
            </button>
            <button
              onClick={() => setTrackerState('closed')}
              className="w-4 h-4 rounded flex items-center justify-center hover:bg-red-200 transition-colors"
              title={lang === 'pt' ? 'Fechar' : 'Close'}
              data-testid="pipeline-tracker-close-btn"
            >
              <X size={10} className="text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      <div className="space-y-0.5 px-1">
        {phases.map((phase) => {
          const Icon = phase.icon;
          const status = getPhaseStatus(phase.id);
          const progress = getRealPhaseProgress(phase.id);

          return (
            <div
              key={phase.id}
              className={`rounded px-1.5 py-0.5 transition-all duration-300 ${
                status === 'completed' ? 'bg-green-50 border border-green-200'
                : status === 'processing' ? 'bg-white border border-purple-300'
                : 'bg-gray-50 border border-gray-200 opacity-50'
              }`}
            >
              <div className="flex items-center gap-1">
                <div className={`w-4 h-4 rounded flex items-center justify-center shrink-0 ${
                  status === 'completed' ? 'bg-green-500'
                  : status === 'processing' ? 'bg-purple-500 animate-pulse'
                  : 'bg-gray-300'
                }`}>
                  {status === 'completed' ? (<CheckCircle2 size={8} className="text-white" />)
                    : status === 'processing' ? (<Icon size={8} className="text-white" />)
                    : (<Clock size={8} className="text-white" />)}
                </div>

                <span className="text-[9px] font-semibold text-gray-800 truncate flex-1">{phase.name}</span>

                {(status === 'completed' || status === 'processing') && onRetryPhase && (
                  <button
                    onClick={() => onRetryPhase(phase.id)}
                    className="w-4 h-4 rounded flex items-center justify-center hover:bg-purple-200 transition-colors shrink-0"
                    title={lang === 'pt' ? `Refazer ${phase.name}` : `Retry ${phase.name}`}
                    data-testid={`pipeline-retry-${phase.id}`}
                  >
                    <RefreshCw size={7} className="text-gray-600" />
                  </button>
                )}

                {status === 'processing' && progress < 100 && (<RefreshCw size={7} className="text-purple-500 animate-spin shrink-0" />)}
                {status === 'completed' && (<span className="text-[8px] font-semibold text-green-600 shrink-0">✓ 100%</span>)}
                {status === 'processing' && progress < 100 && (
                  <span className="text-[8px] font-medium text-gray-600 shrink-0 w-6 text-right">{progress}%</span>
                )}
              </div>

              {status === 'processing' && progress < 100 && (
                <div className="mt-0.5 ml-5">
                  <div className="h-px rounded-full bg-gray-200 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-1000 ease-linear"
                      style={{ width: `${progress}%`, backgroundColor: phase.color }}
                    />
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {allPhasesComplete && onNextStep && (
        <div className="mt-2 px-1">
          <button
            onClick={onNextStep}
            className="w-full py-1.5 px-3 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white text-xs font-bold shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-1"
            data-testid="pipeline-next-step-btn"
          >
            <ChevronRight size={14} />
            {lang === 'pt' ? 'Próxima Etapa' : 'Next Step'}
          </button>
        </div>
      )}
    </div>
  );
};

export default PipelineTrackerInline;
