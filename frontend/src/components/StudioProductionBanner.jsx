import { useStudioProduction } from '../contexts/StudioProductionContext';
import { useNavigate } from 'react-router-dom';
import { Film, Check, X, ChevronRight, Minimize2 } from 'lucide-react';
import { useState } from 'react';

export function StudioProductionBanner() {
  const ctx = useStudioProduction();
  const navigate = useNavigate();
  const [minimized, setMinimized] = useState(false);

  if (!ctx?.activeProduction) return null;

  const { projectId, projectName, agentStatus, outputs, scenes, status, startedAt } = ctx.activeProduction;
  const isComplete = status === 'complete';
  const isError = status === 'error';
  const isRunning = !isComplete && !isError;

  if (ctx.isDismissed() && !isComplete) return null;

  const totalScenes = agentStatus?.total_scenes || scenes?.length || 0;
  const videosDone = agentStatus?.videos_done || outputs?.filter(o => o.type === 'video' && o.url && o.scene_number)?.length || 0;
  const phase = agentStatus?.phase || '';
  const elapsed = Math.round((Date.now() - startedAt) / 60000);

  // Progress calc
  let progress = 0;
  if (isComplete) progress = 100;
  else if (phase === 'concatenating') progress = 95;
  else if (phase?.startsWith('generating_video')) progress = 50 + (videosDone / Math.max(totalScenes, 1)) * 45;
  else if (phase) progress = Math.min(30, 5 + (agentStatus?.current_scene || 0) / Math.max(totalScenes, 1) * 25);

  const phaseLabel = isComplete ? 'Concluído!'
    : isError ? 'Erro na produção'
    : phase === 'concatenating' ? 'Montando filme...'
    : phase === 'generating_video' ? `Sora 2 — ${videosDone}/${totalScenes} vídeos`
    : phase === 'directing' ? `Dirigindo cenas...`
    : phase === 'waiting_sora' ? 'Aguardando Sora 2...'
    : phase === 'starting_teams' ? 'Iniciando equipas...'
    : 'Produzindo...';

  if (minimized && isRunning) {
    return (
      <button onClick={() => setMinimized(false)} data-testid="studio-banner-minimized"
        className="fixed bottom-20 right-3 z-50 h-10 w-10 rounded-full bg-[#C9A84C] text-black flex items-center justify-center shadow-lg shadow-[#C9A84C]/20 animate-pulse">
        <Film size={16} />
        {videosDone > 0 && (
          <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-emerald-500 text-[7px] text-white font-bold flex items-center justify-center">
            {videosDone}
          </span>
        )}
      </button>
    );
  }

  return (
    <div data-testid="studio-production-banner"
      className={`fixed bottom-20 left-3 right-3 z-50 rounded-xl border shadow-xl backdrop-blur-xl transition-all ${
        isComplete ? 'border-emerald-500/30 bg-emerald-500/10 shadow-emerald-500/10'
        : isError ? 'border-red-500/30 bg-red-500/10 shadow-red-500/10'
        : 'border-[#C9A84C]/30 bg-[#0A0A0A]/95 shadow-[#C9A84C]/10'
      }`} style={{ maxWidth: '420px', margin: '0 auto' }}>

      <div className="p-2.5">
        {/* Header */}
        <div className="flex items-center gap-2 mb-1.5">
          <div className={`h-6 w-6 rounded-lg flex items-center justify-center ${
            isComplete ? 'bg-emerald-500' : isError ? 'bg-red-500' : 'bg-[#C9A84C]'
          }`}>
            {isComplete ? <Check size={12} className="text-black" /> : isError ? <X size={12} className="text-white" /> : <Film size={12} className="text-black" />}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[9px] font-semibold text-white truncate">{projectName || 'Produção'}</p>
            <p className={`text-[7px] font-medium ${isComplete ? 'text-emerald-400' : isError ? 'text-red-400' : 'text-[#C9A84C]'}`}>
              {phaseLabel} {isRunning && elapsed > 0 ? `• ${elapsed}min` : ''}
            </p>
          </div>
          <div className="flex items-center gap-1">
            {isRunning && (
              <button onClick={() => setMinimized(true)} className="h-5 w-5 rounded flex items-center justify-center text-[#666] hover:text-white transition">
                <Minimize2 size={10} />
              </button>
            )}
            <button onClick={() => { navigate('/marketing/studio'); if (isComplete || isError) ctx.stopTracking(); }}
              data-testid="studio-banner-go"
              className={`rounded-lg px-2 py-1 text-[8px] font-semibold flex items-center gap-0.5 ${
                isComplete ? 'bg-emerald-500 text-black' : 'bg-[#C9A84C]/20 text-[#C9A84C] hover:bg-[#C9A84C]/30'
              }`}>
              {isComplete ? 'Ver Filme' : 'Ver'} <ChevronRight size={8} />
            </button>
          </div>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-[#111] rounded-full h-1.5 overflow-hidden">
          <div className={`h-full rounded-full transition-all duration-1000 ${
            isComplete ? 'bg-emerald-500' : isError ? 'bg-red-500' : 'bg-[#C9A84C]'
          } ${isRunning ? 'animate-pulse' : ''}`} style={{ width: `${progress}%` }} />
        </div>

        {/* Scene mini-indicators */}
        {totalScenes > 0 && isRunning && (
          <div className="flex gap-0.5 mt-1.5">
            {Array.from({ length: totalScenes }, (_, i) => {
              const sn = String(i + 1);
              const ss = agentStatus?.scene_status || {};
              const done = ss[sn] === 'done';
              const agentsDone = ss[sn] === 'agents_done';
              const err = ss[sn] === 'error';
              return (
                <div key={i} className={`flex-1 h-1 rounded-sm ${
                  done ? 'bg-emerald-500' : err ? 'bg-red-500' : agentsDone ? 'bg-blue-500' : 'bg-[#222]'
                }`} />
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
