import { X, Sparkles, Check, ChevronRight, Clapperboard, Film, Palette, Pencil, CircleDot, Camera, Brush } from 'lucide-react';
import { useState } from 'react';

/**
 * New Project Modal - Optimized UX
 * Clear step-by-step project creation flow
 */
export function NewProjectModal({ 
  lang = 'pt',
  onClose, 
  onCreate 
}) {
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [projectLang, setProjectLang] = useState('pt');
  const [audioMode, setAudioMode] = useState('narrated');
  const [animationSub, setAnimationSub] = useState('');
  const [visualStyle, setVisualStyle] = useState('animation');
  const [continuityMode, setContinuityMode] = useState(true);
  const [formatStrategy, setFormatStrategy] = useState('safe_zone'); // NEW
  const [formatsRequested, setFormatsRequested] = useState(['16:9']); // NEW

  const handleCreate = () => {
    if (!projectName.trim() || !animationSub) return;
    
    onCreate({
      name: projectName.trim(),
      briefing: projectDesc.trim(),
      language: projectLang,
      visual_style: visualStyle,
      audio_mode: audioMode,
      animation_sub: animationSub,
      continuity_mode: continuityMode,
      format_strategy: formatStrategy, // NEW
      formats_requested: formatsRequested, // NEW
    });
  };

  const isValid = projectName.trim() && animationSub;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-card p-4 space-y-3 border border-[#8B5CF6]/20 max-w-2xl w-full max-h-[95vh] overflow-y-auto">
        {/* Header - COMPACTO */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clapperboard size={18} className="text-[#8B5CF6]" />
            <h3 className="text-lg font-bold text-white">
              {lang === 'pt' ? 'Novo Projeto' : 'New Project'}
            </h3>
          </div>
          <button 
            onClick={onClose}
            className="text-[#666] hover:text-white transition p-1 hover:bg-white/5 rounded">
            <X size={20} />
          </button>
        </div>

        {/* Step 1: Project Name - ULTRA COMPACTO */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">1</span>
            {lang === 'pt' ? 'Nome do Projeto' : 'Project Name'}
            <span className="text-red-400">*</span>
          </label>
          <input 
            value={projectName} 
            onChange={e => setProjectName(e.target.value)}
            placeholder={lang === 'pt' ? 'Ex: A Jornada de Abraão' : 'Ex: The Journey of Abraham'}
            autoFocus
            className="w-full bg-[#0A0A0A] border border-[#333] focus:border-[#8B5CF6] rounded-lg px-3 py-2 text-sm text-white outline-none placeholder-[#555] transition" 
          />
        </div>

        {/* Step 2: Visual Style - UMA LINHA COMPACTA */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">2</span>
            {lang === 'pt' ? 'Estilo Visual' : 'Visual Style'}
            <span className="text-red-400">*</span>
          </label>
          <div className="flex gap-1.5 overflow-x-auto pb-1">
            {[
              { id: 'pixar_3d', label: 'Pixar 3D', icon: Film },
              { id: 'cartoon_3d', label: 'Cartoon 3D', icon: Palette },
              { id: 'cartoon_2d', label: 'Cartoon 2D', icon: Pencil },
              { id: 'anime_2d', label: 'Anime 2D', icon: CircleDot },
              { id: 'realistic', label: 'Realista', icon: Camera },
              { id: 'watercolor', label: 'Aquarela', icon: Brush },
            ].map(s => {
              const Icon = s.icon;
              return (
                <button 
                  key={s.id} 
                  type="button"
                  onClick={() => { 
                    setAnimationSub(s.id); 
                    setVisualStyle(s.id.includes('3d') ? 'animation' : s.id.includes('2d') ? (s.id === 'anime_2d' ? 'anime' : 'cartoon') : s.id === 'realistic' ? 'realistic' : 'watercolor'); 
                  }}
                  className={`shrink-0 px-3 py-1.5 rounded-md border transition-all flex items-center gap-1.5 ${
                    animationSub === s.id
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                      : 'border-[#333] bg-[#0A0A0A] text-[#888] hover:border-[#555] hover:text-white'
                  }`}>
                  <Icon size={14} strokeWidth={1.5} />
                  <span className="text-xs font-medium whitespace-nowrap">{s.label}</span>
                  {animationSub === s.id && (
                    <Check size={12} strokeWidth={2.5} className="text-[#8B5CF6]" />
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Step 3: Multi-Format Strategy - ULTRA COMPACTO (renumerado) */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">3</span>
            {lang === 'pt' ? 'Formato' : 'Format'}
          </label>
          <div className="flex gap-1.5">
            {/* Safe Zone */}
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('safe_zone');
                setFormatsRequested(['16:9']);
              }}
              className={`flex-1 p-2 rounded-md border text-left transition-all ${
                formatStrategy === 'safe_zone'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/10'
                  : 'border-[#333] bg-[#0A0A0A] hover:border-[#555]'
              }`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs font-semibold text-white">Safe Zone</span>
                {formatStrategy === 'safe_zone' && (
                  <Check size={12} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </div>
              <div className="text-[10px] text-[#888]">16:9 → Crop 9:16</div>
            </button>

            {/* Dual Generation */}
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('dual_generation');
                setFormatsRequested(['16:9', '9:16']);
              }}
              className={`flex-1 p-2 rounded-md border text-left transition-all ${
                formatStrategy === 'dual_generation'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/10'
                  : 'border-[#333] bg-[#0A0A0A] hover:border-[#555]'
              }`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs font-semibold text-white">Dual</span>
                {formatStrategy === 'dual_generation' && (
                  <Check size={12} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </div>
              <div className="text-[10px] text-[#888]">16:9 + 9:16</div>
            </button>

            {/* Multi-Format */}
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('multi_format');
                setFormatsRequested(['16:9', '9:16', '4:5', '1:1']);
              }}
              className={`flex-1 p-2 rounded-md border text-left transition-all ${
                formatStrategy === 'multi_format'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/10'
                  : 'border-[#333] bg-[#0A0A0A] hover:border-[#555]'
              }`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-xs font-semibold text-white">Multi</span>
                {formatStrategy === 'multi_format' && (
                  <Check size={12} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </div>
              <div className="text-[10px] text-[#888]">Todos</div>
            </button>
          </div>
        </div>

        {/* Advanced Settings - Removido para compactar modal */}

        {/* Action Buttons - COMPACTO */}
        <div className="flex gap-2 pt-2">
          <button 
            onClick={onClose}
            className="px-4 py-2 rounded-lg border border-[#333] text-xs font-medium text-[#999] hover:text-white hover:border-[#555] transition">
            {lang === 'pt' ? 'Cancelar' : 'Cancel'}
          </button>
          <button 
            onClick={handleCreate} 
            disabled={!isValid}
            className="flex-1 bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] hover:from-[#7C3AED] hover:to-[#6D28D9] rounded-lg py-2 text-sm font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 shadow-lg shadow-[#8B5CF6]/40 transition-all">
            <Sparkles size={16} /> 
            {lang === 'pt' ? 'Criar Projeto' : 'Create Project'}
          </button>
        </div>
      </div>
    </div>
  );
}
