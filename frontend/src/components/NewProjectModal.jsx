import { X, Sparkles, Check, ChevronRight, Clapperboard, Film, Palette, Pencil, CircleDot, Camera, Brush, Users, Building2, Plus } from 'lucide-react';
import { useState, useEffect } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

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
  const [formatStrategy, setFormatStrategy] = useState('safe_zone');
  const [formatsRequested, setFormatsRequested] = useState(['16:9']);
  
  // NEW: Character folder selection for continuity
  const [selectedFolder, setSelectedFolder] = useState(null); // null = criar novos personagens
  const [folders, setFolders] = useState([]);
  const [loadingFolders, setLoadingFolders] = useState(true);
  
  // NEW: Company selection
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);

  // Fetch folders on mount
  useEffect(() => {
    const fetchFolders = async () => {
      try {
        const token = localStorage.getItem('token');
        console.log('🔍 [FOLDERS] Fetching folders...', { hasToken: !!token });
        
        if (!token) {
          console.warn('⚠️ [FOLDERS] No token found, skipping fetch');
          setLoadingFolders(false);
          return;
        }
        
        const response = await fetch(`${API}/api/folders`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log('📡 [FOLDERS] Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('✅ [FOLDERS] Folders received:', data.folders?.length || 0, data.folders);
          setFolders(data.folders || []);
        } else {
          const errorText = await response.text();
          console.error('❌ [FOLDERS] Fetch failed:', response.status, errorText);
        }
      } catch (err) {
        console.error('❌ [FOLDERS] Error fetching folders:', err);
      } finally {
        setLoadingFolders(false);
      }
    };
    
    fetchFolders();
  }, []);

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
      format_strategy: formatStrategy,
      formats_requested: formatsRequested,
      character_folder_id: selectedFolder,
      company_id: selectedCompany?.id || null, // NEW: Pass selected company
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

        {/* Step 0: Empresa/Projeto Master - NOVO */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">0</span>
            <Building2 size={12} className="text-[#8B5CF6]" />
            {lang === 'pt' ? 'Empresa / Projeto Master' : 'Company / Master Project'}
          </label>
          
          {loadingCompanies ? (
            <div className="text-xs text-[#666] py-2">
              {lang === 'pt' ? 'Carregando empresas...' : 'Loading companies...'}
            </div>
          ) : (
            <div className="flex gap-2 overflow-x-auto pb-1">
              {/* Option: No company (standalone project) */}
              <button
                type="button"
                onClick={() => setSelectedCompany(null)}
                className={`shrink-0 flex flex-col items-center gap-1.5 p-3 rounded-lg border transition-all ${
                  selectedCompany === null
                    ? 'border-[#8B5CF6] bg-[#8B5CF6]/10'
                    : 'border-[#333] bg-[#0A0A0A] hover:border-[#555]'
                }`}>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center border-2 border-dashed ${
                  selectedCompany === null ? 'border-[#8B5CF6]' : 'border-[#444]'
                }`}>
                  <Sparkles size={20} className={selectedCompany === null ? 'text-[#8B5CF6]' : 'text-[#666]'} />
                </div>
                <span className="text-xs font-medium text-center whitespace-nowrap text-white">
                  {lang === 'pt' ? 'Sem Empresa' : 'No Company'}
                </span>
                {selectedCompany === null && (
                  <Check size={14} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </button>

              {/* Existing companies */}
              {companies.map(company => (
                <button
                  key={company.id}
                  type="button"
                  onClick={() => {
                    setSelectedCompany(company);
                    // Auto-fill settings from company defaults
                    if (company.default_settings) {
                      setAnimationSub(company.default_settings.animation_sub || animationSub);
                      setVisualStyle(company.default_settings.visual_style || visualStyle);
                      setFormatStrategy(company.default_settings.format_strategy || formatStrategy);
                      setProjectLang(company.default_settings.language || projectLang);
                      
                      // Auto-select first folder if company has folders
                      if (company.folder_ids && company.folder_ids.length > 0) {
                        setSelectedFolder(company.folder_ids[0]);
                      }
                    }
                  }}
                  className={`shrink-0 flex flex-col items-center gap-1.5 p-3 rounded-lg border transition-all ${
                    selectedCompany?.id === company.id
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/10'
                      : 'border-[#333] bg-[#0A0A0A] hover:border-[#555]'
                  }`}>
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center overflow-hidden ${
                    company.logo_url ? 'bg-white' : 'bg-[#1A1A1A]'
                  }`}>
                    {company.logo_url ? (
                      <img src={company.logo_url} alt={company.name} className="w-full h-full object-contain" />
                    ) : (
                      <Building2 size={20} className="text-[#666]" />
                    )}
                  </div>
                  <span className="text-xs font-medium text-center max-w-[80px] truncate text-white">
                    {company.name}
                  </span>
                  {company.is_primary && (
                    <span className="text-[9px] bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded-full">
                      PRINCIPAL
                    </span>
                  )}
                  {selectedCompany?.id === company.id && (
                    <Check size={14} strokeWidth={2.5} className="text-[#8B5CF6]" />
                  )}
                </button>
              ))}

              {/* Button: Create new company */}
              <button
                type="button"
                onClick={() => {
                  // TODO: Open company creation modal
                  alert('Abrir modal de criação de empresa');
                }}
                className="shrink-0 flex flex-col items-center gap-1.5 p-3 rounded-lg border border-dashed border-[#555] hover:border-[#8B5CF6] bg-[#0A0A0A] hover:bg-[#8B5CF6]/5 transition-all">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center border-2 border-dashed border-[#555]">
                  <Plus size={20} className="text-[#666]" />
                </div>
                <span className="text-xs font-medium text-center whitespace-nowrap text-[#888]">
                  {lang === 'pt' ? '+ Nova Empresa' : '+ New Company'}
                </span>
              </button>
            </div>
          )}
          
          <p className="text-[10px] text-[#666]">
            {selectedCompany 
              ? (lang === 'pt' 
                  ? `Configurações e personagens de "${selectedCompany.name}" serão aplicados automaticamente` 
                  : `Settings and characters from "${selectedCompany.name}" will be applied automatically`)
              : (lang === 'pt' 
                  ? 'Projeto independente - configure manualmente abaixo' 
                  : 'Standalone project - configure manually below')
            }
          </p>
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

        {/* Step 3: Character Folder Selection - NOVO PARA CONTINUIDADE */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">3</span>
            <Users size={12} className="text-[#8B5CF6]" />
            {lang === 'pt' ? 'Personagens' : 'Characters'}
          </label>
          <div className="flex gap-1.5 overflow-x-auto pb-1">
            {/* Option: Create New Characters */}
            <button
              type="button"
              onClick={() => setSelectedFolder(null)}
              className={`shrink-0 px-3 py-1.5 rounded-md border transition-all flex items-center gap-1.5 ${
                selectedFolder === null
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                  : 'border-[#333] bg-[#0A0A0A] text-[#888] hover:border-[#555] hover:text-white'
              }`}>
              <Sparkles size={14} strokeWidth={1.5} />
              <span className="text-xs font-medium whitespace-nowrap">
                {lang === 'pt' ? 'Criar Novos' : 'Create New'}
              </span>
              {selectedFolder === null && (
                <Check size={12} strokeWidth={2.5} className="text-[#8B5CF6]" />
              )}
            </button>

            {/* Loading state */}
            {loadingFolders && (
              <div className="shrink-0 px-3 py-1.5 text-xs text-[#666]">
                {lang === 'pt' ? 'Carregando...' : 'Loading...'}
              </div>
            )}

            {/* Existing folders */}
            {!loadingFolders && folders.map(folder => (
              <button
                key={folder.id}
                type="button"
                onClick={() => setSelectedFolder(folder.id)}
                className={`shrink-0 px-3 py-1.5 rounded-md border transition-all flex items-center gap-1.5 ${
                  selectedFolder === folder.id
                    ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6]'
                    : 'border-[#333] bg-[#0A0A0A] text-[#888] hover:border-[#555] hover:text-white'
                }`}>
                <Users size={14} strokeWidth={1.5} />
                <span className="text-xs font-medium whitespace-nowrap">{folder.name}</span>
                {selectedFolder === folder.id && (
                  <Check size={12} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </button>
            ))}

            {/* Empty state */}
            {!loadingFolders && folders.length === 0 && (
              <div className="shrink-0 px-3 py-1.5 text-xs text-[#666]">
                {lang === 'pt' ? 'Nenhuma pasta criada ainda' : 'No folders created yet'}
              </div>
            )}
          </div>
          <p className="text-[10px] text-[#666]">
            {selectedFolder === null 
              ? (lang === 'pt' ? 'Novos personagens serão criados para este projeto' : 'New characters will be created for this project')
              : (lang === 'pt' ? 'Personagens existentes serão reutilizados (continuidade garantida)' : 'Existing characters will be reused (continuity guaranteed)')
            }
          </p>
        </div>

        {/* Step 4: Multi-Format Strategy - ULTRA COMPACTO (renumerado) */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">4</span>
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
