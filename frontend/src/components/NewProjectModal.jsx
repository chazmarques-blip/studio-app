import { X, Sparkles, Check, ChevronRight, Clapperboard } from 'lucide-react';
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
    });
  };

  const isValid = projectName.trim() && animationSub;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="glass-card p-6 space-y-5 border border-[#8B5CF6]/20 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-2xl font-bold text-white flex items-center gap-3">
              <Clapperboard size={24} className="text-[#8B5CF6]" />
              {lang === 'pt' ? 'Novo Projeto' : 'New Project'}
            </h3>
            <p className="text-sm text-[#888] mt-1">
              {new Date().toLocaleDateString(lang === 'pt' ? 'pt-BR' : 'en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="text-[#666] hover:text-white transition p-2 hover:bg-white/5 rounded-lg">
            <X size={24} />
          </button>
        </div>

        {/* Step 1: Project Name */}
        <div className="space-y-3">
          <label className="text-base font-bold text-white flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-[#8B5CF6] flex items-center justify-center text-sm">1</span>
            {lang === 'pt' ? 'Nome do Projeto' : 'Project Name'}
            <span className="text-red-400 text-xl">*</span>
          </label>
          <input 
            value={projectName} 
            onChange={e => setProjectName(e.target.value)}
            placeholder={lang === 'pt' ? 'Ex: A Jornada de Abraão' : 'Ex: The Journey of Abraham'}
            autoFocus
            className="w-full bg-[#0A0A0A] border-2 border-[#333] focus:border-[#8B5CF6] rounded-xl px-5 py-4 text-lg text-white font-semibold outline-none placeholder-[#555] transition" 
          />
        </div>

        {/* Step 2: Visual Style */}
        <div className="space-y-3">
          <label className="text-base font-bold text-white flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-[#8B5CF6] flex items-center justify-center text-sm">2</span>
            {lang === 'pt' ? 'Estilo Visual' : 'Visual Style'}
            <span className="text-red-400 text-xl">*</span>
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { id: 'pixar_3d', label: 'Pixar 3D', desc: 'Estilo DreamWorks/Pixar', icon: '🎬', gradient: 'from-blue-500/20 to-purple-500/20' },
              { id: 'cartoon_3d', label: 'Cartoon 3D', desc: 'Cores vivas, estilizado', icon: '🎨', gradient: 'from-pink-500/20 to-orange-500/20' },
              { id: 'cartoon_2d', label: 'Cartoon 2D', desc: 'Clássico Disney', icon: '✏️', gradient: 'from-yellow-500/20 to-red-500/20' },
              { id: 'anime_2d', label: 'Anime 2D', desc: 'Estilo japonês', icon: '⛩️', gradient: 'from-purple-500/20 to-pink-500/20' },
              { id: 'realistic', label: 'Realista', desc: 'Cinematográfico', icon: '📽️', gradient: 'from-slate-500/20 to-zinc-500/20' },
              { id: 'watercolor', label: 'Aquarela', desc: 'Artístico', icon: '🖌️', gradient: 'from-teal-500/20 to-cyan-500/20' },
            ].map(s => (
              <button 
                key={s.id} 
                type="button"
                onClick={() => { 
                  setAnimationSub(s.id); 
                  setVisualStyle(s.id.includes('3d') ? 'animation' : s.id.includes('2d') ? (s.id === 'anime_2d' ? 'anime' : 'cartoon') : s.id === 'realistic' ? 'realistic' : 'watercolor'); 
                }}
                className={`relative p-5 rounded-2xl border-2 text-left transition-all hover:scale-105 ${
                  animationSub === s.id
                    ? 'border-[#8B5CF6] bg-gradient-to-br shadow-xl shadow-[#8B5CF6]/30'
                    : 'border-[#222] bg-[#0A0A0A] hover:border-[#444]'
                } ${s.gradient}`}>
                {animationSub === s.id && (
                  <div className="absolute top-3 right-3 w-7 h-7 bg-[#8B5CF6] rounded-full flex items-center justify-center shadow-lg">
                    <Check size={16} strokeWidth={3} className="text-black" />
                  </div>
                )}
                
                <div className="text-3xl mb-3">{s.icon}</div>
                <div className={`font-bold text-base mb-1 ${animationSub === s.id ? 'text-[#8B5CF6]' : 'text-white'}`}>
                  {s.label}
                </div>
                <div className="text-xs text-[#666]">{s.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Description (optional) */}
        <div className="space-y-3">
          <label className="text-base font-bold text-white flex items-center gap-2">
            <span className="w-7 h-7 rounded-full bg-[#555] flex items-center justify-center text-sm">3</span>
            {lang === 'pt' ? 'Descrição' : 'Description'}
            <span className="text-xs text-[#666] font-normal ml-1">({lang === 'pt' ? 'opcional' : 'optional'})</span>
          </label>
          <textarea 
            value={projectDesc} 
            onChange={e => setProjectDesc(e.target.value)}
            placeholder={lang === 'pt' ? 'Descreva brevemente o tema ou objetivo do projeto...' : 'Briefly describe the theme or goal...'}
            rows={3}
            className="w-full bg-[#0A0A0A] border border-[#333] focus:border-[#8B5CF6]/50 rounded-xl px-5 py-3 text-sm text-white outline-none placeholder-[#555] resize-none transition" 
          />
        </div>

        {/* Advanced Settings - Collapsible */}
        <details className="group">
          <summary className="cursor-pointer text-base font-semibold text-[#8B5CF6] hover:text-[#A78BFA] flex items-center gap-2 py-2">
            <ChevronRight size={18} className="transition-transform group-open:rotate-90" />
            {lang === 'pt' ? 'Configurações Avançadas' : 'Advanced Settings'}
          </summary>
          <div className="mt-4 space-y-4 pl-2">
            {/* Language + Audio */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-[#888] uppercase tracking-wider mb-2 block font-medium">
                  {lang === 'pt' ? 'Idioma' : 'Language'}
                </label>
                <select 
                  value={projectLang} 
                  onChange={e => setProjectLang(e.target.value)}
                  className="w-full bg-[#0A0A0A] border border-[#333] focus:border-[#8B5CF6]/50 rounded-xl px-4 py-3 text-sm text-white outline-none transition">
                  <option value="pt">🇧🇷 Português</option>
                  <option value="en">🇺🇸 English</option>
                  <option value="es">🇪🇸 Español</option>
                </select>
              </div>
              <div>
                <label className="text-sm text-[#888] uppercase tracking-wider mb-2 block font-medium">
                  {lang === 'pt' ? 'Tipo de Áudio' : 'Audio Type'}
                </label>
                <select 
                  value={audioMode} 
                  onChange={e => setAudioMode(e.target.value)}
                  className="w-full bg-[#0A0A0A] border border-[#333] focus:border-[#8B5CF6]/50 rounded-xl px-4 py-3 text-sm text-white outline-none transition">
                  <option value="narrated">🎙️ {lang === 'pt' ? 'Narrado' : 'Narrated'}</option>
                  <option value="dubbed">🗣️ {lang === 'pt' ? 'Dublado' : 'Dubbed'}</option>
                </select>
              </div>
            </div>

            {/* Continuity Engine */}
            <div className="flex items-center justify-between p-4 rounded-xl border border-[#222] bg-[#0A0A0A]">
              <div className="flex-1">
                <div className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[#8B5CF6]"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
                  {lang === 'pt' ? 'Motor de Continuidade' : 'Continuity Engine'}
                </div>
                <div className="text-xs text-[#666]">
                  {lang === 'pt' ? 'Consistência visual entre cenas' : 'Visual consistency across scenes'}
                </div>
              </div>
              <button
                type="button"
                onClick={() => setContinuityMode(!continuityMode)}
                className={`relative w-14 h-7 rounded-full transition-colors ${
                  continuityMode ? 'bg-[#8B5CF6]' : 'bg-[#333]'
                }`}>
                <div className={`absolute top-0.5 w-6 h-6 rounded-full bg-white transition-all shadow-lg ${
                  continuityMode ? 'right-0.5' : 'left-0.5'
                }`} />
              </button>
            </div>
          </div>
        </details>

        {/* Action Buttons */}
        <div className="flex gap-4 pt-4">
          <button 
            onClick={onClose}
            className="flex-1 rounded-xl border-2 border-[#333] py-4 text-base font-semibold text-[#999] hover:text-white hover:border-[#555] transition">
            {lang === 'pt' ? 'Cancelar' : 'Cancel'}
          </button>
          <button 
            onClick={handleCreate} 
            disabled={!isValid}
            className="flex-1 bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] hover:from-[#7C3AED] hover:to-[#6D28D9] rounded-xl py-4 text-base font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-xl shadow-[#8B5CF6]/40 transition-all hover:scale-[1.02]">
            <Sparkles size={20} /> 
            {lang === 'pt' ? 'Criar Projeto' : 'Create Project'}
          </button>
        </div>
      </div>
    </div>
  );
}
