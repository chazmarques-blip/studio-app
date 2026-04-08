import { X, Sparkles, Check, ChevronRight, Clapperboard, Film, Palette, Pencil, CircleDot, Camera, Brush, Users, Building2, Plus, Trash2, Edit2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

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
  const { token } = useAuth(); // Get token from AuthContext
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [projectLang, setProjectLang] = useState('pt');
  const [audioMode, setAudioMode] = useState('narrated');
  const [animationSub, setAnimationSub] = useState('');
  const [visualStyle, setVisualStyle] = useState('animation');
  const [continuityMode, setContinuityMode] = useState(true);
  const [formatStrategy, setFormatStrategy] = useState('safe_zone');
  const [formatsRequested, setFormatsRequested] = useState(['16:9']);
  const [videoEngine, setVideoEngine] = useState('sora'); // NEW: Sora 2 or Kling AI
  const [targetDuration, setTargetDuration] = useState(5); // NEW: Duration in minutes (5, 10, 15, 20, 25)
  const [targetAudience, setTargetAudience] = useState('all'); // NEW: Target audience age range
  
  // NEW: Character folder selection for continuity
  const [selectedFolder, setSelectedFolder] = useState(null); // null = criar novos personagens
  const [folders, setFolders] = useState([]);
  const [loadingFolders, setLoadingFolders] = useState(true);
  
  // NEW: Company selection
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loadingCompanies, setLoadingCompanies] = useState(true);
  
  // NEW: Company creation modal
  const [showCreateCompany, setShowCreateCompany] = useState(false);
  const [newCompanyName, setNewCompanyName] = useState('');
  const [newCompanyLogo, setNewCompanyLogo] = useState('');
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [creatingCompany, setCreatingCompany] = useState(false);
  
  // NEW: Company editing
  const [editingCompany, setEditingCompany] = useState(null);
  const [showEditCompany, setShowEditCompany] = useState(false);
  const [editCompanyName, setEditCompanyName] = useState('');
  const [editCompanyLogo, setEditCompanyLogo] = useState('');
  // NEW: Company defaults editing
  const [editCompanyDefaults, setEditCompanyDefaults] = useState({
    default_visual_style: '',
    default_animation_sub: '',
    default_target_audience: '',
    default_character_folder_id: '',
    default_format_strategy: '',
    default_video_engine: '',
    default_target_duration: 5
  });
  const [uploadingEditLogo, setUploadingEditLogo] = useState(false);
  const [updatingCompany, setUpdatingCompany] = useState(false);
  const [editLogoPosition, setEditLogoPosition] = useState('center'); // 'center', 'top', 'bottom', 'left', 'right'
  
  // NEW: Company creation logo position
  const [newLogoPosition, setNewLogoPosition] = useState('center');

  // Fetch folders on mount
  useEffect(() => {
    const fetchFolders = async () => {
      if (!token) {
        console.warn('⚠️ [NewProjectModal] No token available - User may not be logged in');
        setLoadingFolders(false);
        setLoadingCompanies(false);
        return;
      }

      try {
        console.log('🔍 [NewProjectModal] Fetching folders and companies...');
        
        const headers = {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        };
        
        // Fetch folders
        const foldersResponse = await fetch(`${API}/api/folders`, { headers });
        console.log('📡 [FOLDERS] Response status:', foldersResponse.status);
        
        if (foldersResponse.ok) {
          const data = await foldersResponse.json();
          console.log('✅ [FOLDERS] Received:', data.folders?.length || 0);
          setFolders(data.folders || []);
        } else {
          console.error('❌ [FOLDERS] Fetch failed:', foldersResponse.status);
        }
        
        // Fetch companies
        const companiesResponse = await fetch(`${API}/api/companies`, { headers });
        console.log('📡 [COMPANIES] Response status:', companiesResponse.status);
        
        if (companiesResponse.ok) {
          const data = await companiesResponse.json();
          console.log('✅ [COMPANIES] Received:', data.companies?.length || 0);
          setCompanies(data.companies || []);
        } else {
          console.error('❌ [COMPANIES] Fetch failed:', companiesResponse.status);
        }
        
      } catch (err) {
        console.error('❌ [NewProjectModal] Error fetching data:', err);
      } finally {
        setLoadingFolders(false);
        setLoadingCompanies(false);
      }
    };
    
    fetchFolders();
  }, [token]);

  // ═══════════════════════════════════════════════════════════════════════════
  // NEW: Apply company defaults when company is selected
  // ═══════════════════════════════════════════════════════════════════════════
  useEffect(() => {
    if (selectedCompany) {
      console.log('🏢 [NewProjectModal] Company selected:', selectedCompany.name);
      console.log('📊 [NewProjectModal] Company defaults:', {
        visual_style: selectedCompany.default_visual_style,
        target_audience: selectedCompany.default_target_audience,
        format: selectedCompany.default_format_strategy,
        engine: selectedCompany.default_video_engine,
        duration: selectedCompany.default_target_duration,
        folder: selectedCompany.default_character_folder_id
      });
      
      // Apply defaults if they exist
      if (selectedCompany.default_visual_style) {
        setVisualStyle(selectedCompany.default_visual_style);
        console.log('  ✅ Visual Style:', selectedCompany.default_visual_style);
      }
      
      if (selectedCompany.default_animation_sub) {
        setAnimationSub(selectedCompany.default_animation_sub);
        console.log('  ✅ Animation Sub:', selectedCompany.default_animation_sub);
      }
      
      if (selectedCompany.default_target_audience) {
        setTargetAudience(selectedCompany.default_target_audience);
        console.log('  ✅ Target Audience:', selectedCompany.default_target_audience);
      }
      
      if (selectedCompany.default_format_strategy) {
        setFormatStrategy(selectedCompany.default_format_strategy);
        console.log('  ✅ Format Strategy:', selectedCompany.default_format_strategy);
      }
      
      if (selectedCompany.default_video_engine) {
        setVideoEngine(selectedCompany.default_video_engine);
        console.log('  ✅ Video Engine:', selectedCompany.default_video_engine);
      }
      
      if (selectedCompany.default_target_duration) {
        setTargetDuration(selectedCompany.default_target_duration);
        console.log('  ✅ Target Duration:', selectedCompany.default_target_duration);
      }
      
      // Auto-select company's character folder if it exists
      if (selectedCompany.default_character_folder_id) {
        const folder = folders.find(f => f.id === selectedCompany.default_character_folder_id);
        if (folder) {
          setSelectedFolder(folder.id);
          console.log('  ✅ Character Folder:', folder.name);
        } else {
          console.log('  ⚠️ Character Folder ID exists but folder not found:', selectedCompany.default_character_folder_id);
        }
      }
    } else {
      console.log('🏢 [NewProjectModal] No company selected');
    }
  }, [selectedCompany, folders]);
  
  // Auto-select company if only one exists
  useEffect(() => {
    if (companies.length === 1 && !selectedCompany) {
      console.log('📍 [NewProjectModal] Only 1 company, auto-selecting:', companies[0].name);
      setSelectedCompany(companies[0]);
    }
  }, [companies, selectedCompany]);


  const handleEditLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      alert(lang === 'pt' ? 'Apenas PNG ou JPEG são aceitos' : 'Only PNG or JPEG are accepted');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      alert(lang === 'pt' ? 'Tamanho máximo: 5MB' : 'Max size: 5MB');
      return;
    }
    
    setUploadingEditLogo(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', 'company_logo');
      
      const response = await fetch(`${API}/api/campaigns/pipeline/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setEditCompanyLogo(data.url);
        console.log('✅ [LOGO] Uploaded for edit:', data.url);
      } else {
        alert(lang === 'pt' ? 'Erro ao fazer upload' : 'Upload failed');
      }
    } catch (err) {
      console.error('❌ [LOGO] Upload error:', err);
      alert(lang === 'pt' ? 'Erro ao fazer upload' : 'Upload failed');
    } finally {
      setUploadingEditLogo(false);
    }
  };

  const handleOpenEditCompany = (company, e) => {
    e.stopPropagation(); // Prevent company selection
    setEditingCompany(company);
    setEditCompanyName(company.name);
    setEditCompanyLogo(company.logo_url || '');
    setEditLogoPosition(company.logo_position || 'center');
    
    // Load company defaults with detailed logging
    console.log('📝 [EDIT] Opening edit modal for company:', company.name);
    console.log('📝 [EDIT] Raw company data:', company);
    console.log('📝 [EDIT] Default visual style:', company.default_visual_style);
    console.log('📝 [EDIT] Default target audience:', company.default_target_audience);
    console.log('📝 [EDIT] Default engine:', company.default_video_engine);
    
    setEditCompanyDefaults({
      default_visual_style: company.default_visual_style || '',
      default_animation_sub: company.default_animation_sub || '',
      default_target_audience: company.default_target_audience || '',
      default_character_folder_id: company.default_character_folder_id || '',
      default_format_strategy: company.default_format_strategy || '',
      default_video_engine: company.default_video_engine || '',
      default_target_duration: company.default_target_duration || 5
    });
    
    console.log('📝 [EDIT] Set editCompanyDefaults to:', {
      default_visual_style: company.default_visual_style || '',
      default_target_audience: company.default_target_audience || '',
      default_video_engine: company.default_video_engine || ''
    });
    
    setShowEditCompany(true);
  };

  const handleUpdateCompany = async () => {
    if (!editCompanyName.trim() || !editingCompany || updatingCompany || !token) return;
    
    setUpdatingCompany(true);
    try {
      const response = await fetch(`${API}/api/companies/${editingCompany.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: editCompanyName.trim(),
          logo_url: editCompanyLogo || null,
          logo_position: editLogoPosition,
          // Include defaults
          ...editCompanyDefaults
        })
      });
      
      if (response.ok) {
        console.log('✅ [COMPANY] Updated with defaults:', editCompanyDefaults);
        
        // Refetch companies from backend to get updated data
        try {
          const refetchResponse = await fetch(`${API}/api/companies`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });
          
          if (refetchResponse.ok) {
            const data = await refetchResponse.json();
            console.log('🔄 [COMPANY] Refetched from backend:', data.companies?.length || 0);
            setCompanies(data.companies || []);
            
            // Update selected company with fresh data
            if (selectedCompany?.id === editingCompany.id) {
              const freshCompany = data.companies.find(c => c.id === editingCompany.id);
              if (freshCompany) {
                console.log('🔄 [COMPANY] Updated selectedCompany with fresh data:', freshCompany);
                setSelectedCompany(freshCompany);
              }
            }
          }
        } catch (refetchErr) {
          console.error('❌ [COMPANY] Refetch failed:', refetchErr);
        }
        
        setShowEditCompany(false);
        setEditingCompany(null);
      } else {
        alert(lang === 'pt' ? 'Erro ao atualizar empresa' : 'Failed to update company');
      }
    } catch (err) {
      console.error('❌ [COMPANY] Update error:', err);
      alert(lang === 'pt' ? 'Erro ao atualizar empresa' : 'Failed to update company');
    } finally {
      setUpdatingCompany(false);
    }
  };

  const handleDeleteCompany = async (companyId, e) => {
    e.stopPropagation();
    
    if (!confirm(lang === 'pt' ? 'Tem certeza que deseja excluir esta empresa?' : 'Are you sure you want to delete this company?')) {
      return;
    }
    
    try {
      const response = await fetch(`${API}/api/companies/${companyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        console.log('✅ [COMPANY] Deleted');
        setCompanies(prev => prev.filter(c => c.id !== companyId));
        if (selectedCompany?.id === companyId) {
          setSelectedCompany(null);
        }
      } else {
        alert(lang === 'pt' ? 'Erro ao excluir empresa' : 'Failed to delete company');
      }
    } catch (err) {
      console.error('❌ [COMPANY] Delete error:', err);
      alert(lang === 'pt' ? 'Erro ao excluir empresa' : 'Failed to delete company');
    }
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg'];
    if (!validTypes.includes(file.type)) {
      alert(lang === 'pt' ? 'Apenas PNG ou JPEG são aceitos' : 'Only PNG or JPEG are accepted');
      return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert(lang === 'pt' ? 'Tamanho máximo: 5MB' : 'Max size: 5MB');
      return;
    }
    
    setUploadingLogo(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('asset_type', 'company_logo');
      
      const response = await fetch(`${API}/api/campaigns/pipeline/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        setNewCompanyLogo(data.url);
        console.log('✅ [LOGO] Uploaded:', data.url);
      } else {
        console.error('❌ [LOGO] Upload failed:', response.status);
        alert(lang === 'pt' ? 'Erro ao fazer upload' : 'Upload failed');
      }
    } catch (err) {
      console.error('❌ [LOGO] Upload error:', err);
      alert(lang === 'pt' ? 'Erro ao fazer upload' : 'Upload failed');
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleCreateCompany = async () => {
    if (!newCompanyName.trim() || creatingCompany || !token) return;
    
    setCreatingCompany(true);
    try {
      const response = await fetch(`${API}/api/companies`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: newCompanyName.trim(),
          logo_url: newCompanyLogo || null,
          logo_position: newLogoPosition,
          default_visual_style: visualStyle,
          default_animation_sub: animationSub,
          default_format_strategy: formatStrategy,
          default_language: projectLang
        })
      });
      
      if (response.ok) {
        const company = await response.json(); // Backend returns company directly, not wrapped
        console.log('✅ [COMPANY] Created:', company);
        setCompanies(prev => [...prev, company]);
        setSelectedCompany(company);
        setShowCreateCompany(false);
        setNewCompanyName('');
        setNewCompanyLogo('');
        setNewLogoPosition('center');
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('❌ [COMPANY] Creation failed:', response.status, errorData);
        alert(lang === 'pt' ? 'Erro ao criar empresa' : 'Failed to create company');
      }
    } catch (err) {
      console.error('❌ [COMPANY] Error:', err);
      alert(lang === 'pt' ? 'Erro ao criar empresa' : 'Failed to create company');
    } finally {
      setCreatingCompany(false);
    }
  };

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
      company_id: selectedCompany?.id || null,
      video_engine: videoEngine, // NEW: Pass selected video engine
      target_duration_minutes: targetDuration, // NEW: Pass target duration
      target_audience: targetAudience, // NEW: Pass target audience
    });
  };

  const isValid = projectName.trim() && animationSub;

  return (
    <>
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-white rounded-lg p-4 max-w-md w-full max-h-[90vh] overflow-y-auto space-y-3 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h4 className="text-base font-semibold text-[#333] flex items-center gap-2">
            <Clapperboard size={18} className="text-[#8B5CF6]" />
            {lang === 'pt' ? 'Novo Projeto' : 'New Project'}
          </h4>
          <button onClick={onClose} className="text-[#999] hover:text-[#333] transition">
            <X size={18} />
          </button>
        </div>

        {/* Step 0: Empresa/Projeto Master - COMPACTO */}
        <div className="mb-1">
          <label className="text-xs font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Empresa / Projeto Master' : 'Company / Master Project'}
          </label>
          
          {loadingCompanies ? (
            <div className="text-xs text-[#666] py-1">
              {lang === 'pt' ? 'Carregando empresas...' : 'Loading companies...'}
            </div>
          ) : (
            <div className="flex gap-3 overflow-x-auto pb-1 items-start">
              {/* Existing companies - Filtrar Test Company */}
              {companies.filter(c => !c.name.toLowerCase().includes('test')).map(company => (
                <div key={company.id} className="shrink-0 flex flex-col items-center gap-1 relative group">
                  {/* Logo dentro do quadro HORIZONTAL (mais largo que alto) */}
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedCompany(company);
                      // Auto-fill settings from company defaults
                      if (company.default_settings) {
                        setAnimationSub(company.default_settings.animation_sub || animationSub);
                        setVisualStyle(company.default_settings.visual_style || visualStyle);
                        setFormatStrategy(company.default_settings.format_strategy || formatStrategy);
                        setProjectLang(company.default_settings.language || projectLang);
                        
                        if (company.folder_ids && company.folder_ids.length > 0) {
                          setSelectedFolder(company.folder_ids[0]);
                        }
                      }
                    }}
                    className={`w-24 h-14 rounded-lg overflow-hidden transition-all relative bg-white ${
                      selectedCompany?.id === company.id
                        ? 'ring-2 ring-[#8B5CF6] ring-offset-2'
                        : 'hover:ring-2 hover:ring-[#8B5CF6]/30'
                    }`}>
                    {company.logo_url ? (
                      <img 
                        src={company.logo_url} 
                        alt={company.name} 
                        className="w-full h-full object-contain p-1"
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-to-br from-[#F3F0FF] to-[#E8E3FF] flex items-center justify-center">
                        <Building2 size={24} className="text-[#8B5CF6]" />
                      </div>
                    )}
                    {selectedCompany?.id === company.id && (
                      <div className="absolute top-1 right-1 w-4 h-4 rounded-full bg-[#8B5CF6] flex items-center justify-center">
                        <Check size={10} strokeWidth={3} className="text-white" />
                      </div>
                    )}
                  </button>
                  
                  {/* Nome FORA do quadro, abaixo */}
                  <span className="text-[8px] font-medium text-center text-[#333] leading-tight w-24 line-clamp-2">
                    {company.name}
                  </span>
                  
                  {/* Edit button - canto superior esquerdo do quadro */}
                  <button
                    type="button"
                    onClick={(e) => handleOpenEditCompany(company, e)}
                    className="absolute top-0 left-0 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded-full bg-[#8B5CF6] hover:bg-[#7C3AED] text-white shadow-md z-10"
                    title={lang === 'pt' ? 'Editar' : 'Edit'}>
                    <Edit2 size={9} />
                  </button>
                </div>
              ))}

              {/* Button: Create new company - Apenas ícone + circular */}
              <div className="shrink-0 flex flex-col items-center gap-1 mt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateCompany(true)}
                  className="w-10 h-10 flex items-center justify-center rounded-full bg-[#8B5CF6] hover:bg-[#7C3AED] text-white transition-all shadow-md"
                  title={lang === 'pt' ? 'Nova Empresa' : 'New Company'}>
                  <Plus size={18} strokeWidth={2.5} />
                </button>
              </div>
            </div>
          )}
          
          <p className="text-[9px] text-[#999] mt-0.5">
            {selectedCompany 
              ? (lang === 'pt' 
                  ? `Configurações de "${selectedCompany.name}" serão aplicadas` 
                  : `"${selectedCompany.name}" settings will be applied`)
              : (lang === 'pt' 
                  ? 'Configure manualmente abaixo' 
                  : 'Configure manually below')
            }
          </p>
        </div>
        
        {/* Step 1: Project Name */}
        <div className="mb-1">
          <label className="text-xs font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Nome do Projeto' : 'Project Name'}
            <span className="text-red-400 ml-1">*</span>
          </label>
          <input 
            value={projectName} 
            onChange={e => setProjectName(e.target.value)}
            placeholder={lang === 'pt' ? 'Ex: A Jornada de Abraão' : 'Ex: The Journey of Abraham'}
            className="w-full bg-white border-2 border-[#E0E0E0] focus:border-[#8B5CF6] rounded-xl px-3 py-1.5 text-sm text-[#333] outline-none placeholder-[#999] transition" 
          />
        </div>

        {/* Step 2: Visual Style */}
        <div className="mb-1">
          <label className="text-[10px] font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Estilo Visual Padrão' : 'Default Visual Style'}
            <span className="text-red-400 ml-1">*</span>
          </label>
          <div className="grid grid-cols-3 gap-0.5">
            {[
              { id: 'pixar_3d', label: 'Pixar 3D' },
              { id: 'cartoon_3d', label: 'Cartoon 3D' },
              { id: 'cartoon_2d', label: 'Cartoon 2D' },
              { id: 'anime_2d', label: 'Anime 2D' },
              { id: 'realistic', label: 'Realista' },
              { id: 'watercolor', label: 'Aquarela' },
            ].map(s => (
              <button 
                key={s.id} 
                type="button"
                onClick={() => { 
                  setAnimationSub(s.id); 
                  setVisualStyle(s.id.includes('3d') ? 'animation' : s.id.includes('2d') ? (s.id === 'anime_2d' ? 'anime' : 'cartoon') : s.id === 'realistic' ? 'realistic' : 'watercolor'); 
                }}
                className={`px-1.5 py-0.5 rounded-lg border-2 transition-all text-[10px] font-medium ${
                  animationSub === s.id
                    ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                    : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                }`}>
                {s.label}
              </button>
            ))}
          </div>
        </div>

        {/* Step 3: Character Folder Selection */}
        <div className="mb-1">
          <label className="text-[10px] font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Pasta de Personagens Padrão' : 'Default Character Folder'}
          </label>
          <div className="grid grid-cols-2 gap-0.5 max-h-20 overflow-y-auto p-0.5 bg-gray-50 rounded-lg">
            <button
              type="button"
              onClick={() => setSelectedFolder(null)}
              className={`px-1.5 py-0.5 rounded-lg border-2 transition-all flex items-center gap-1 text-[10px] font-medium text-left ${
                selectedFolder === null
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                  : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-white'
              }`}>
              <Sparkles size={12} />
              <span>{lang === 'pt' ? 'Criar Novos' : 'Create New'}</span>
            </button>

            {!loadingFolders && folders.map(folder => (
              <button
                key={folder.id}
                type="button"
                onClick={() => setSelectedFolder(folder.id)}
                className={`px-1.5 py-0.5 rounded-lg border-2 transition-all flex items-center gap-1 text-[10px] font-medium text-left ${
                  selectedFolder === folder.id
                    ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                    : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-white'
                }`}>
                <Users size={12} />
                <span className="truncate">{folder.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Step 4: Target Audience */}
        <div className="mb-1">
          <label className="text-[10px] font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Público-Alvo Padrão' : 'Default Target Audience'}
            <span className="text-red-400 ml-1">*</span>
          </label>
          <div className="grid grid-cols-4 gap-0.5">
            {[
              { id: '3-6', label: '3-6' },
              { id: '6-9', label: '6-9' },
              { id: '10-13', label: '10-13' },
              { id: '14-17', label: '14-17' },
            ].map(age => (
              <button
                key={age.id}
                type="button"
                onClick={() => setTargetAudience(age.id)}
                className={`px-1.5 py-0.5 rounded-lg border-2 transition text-[10px] font-medium ${
                  targetAudience === age.id
                    ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                    : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                }`}>
                {age.label}
              </button>
            ))}
          </div>
          <div className="grid grid-cols-3 gap-0.5 mt-0.5">
            {[
              { id: '18-25', label: '18-25' },
              { id: '25+', label: '25+' },
              { id: 'all', label: lang === 'pt' ? 'Todas' : 'All' },
            ].map(age => (
              <button
                key={age.id}
                type="button"
                onClick={() => setTargetAudience(age.id)}
                className={`px-1.5 py-0.5 rounded-lg border-2 transition text-[10px] font-medium ${
                  targetAudience === age.id
                    ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                    : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                }`}>
                {age.label}
              </button>
            ))}
          </div>
        </div>

        {/* Step 5: Multi-Format Strategy */}
        <div className="mb-1">
          <label className="text-[10px] font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Formato Padrão' : 'Default Format'}
          </label>
          <div className="grid grid-cols-3 gap-0.5">
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('safe_zone');
                setFormatsRequested(['16:9']);
              }}
              className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                formatStrategy === 'safe_zone'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                  : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
              }`}>
              Safe Zone
            </button>

            <button
              type="button"
              onClick={() => {
                setFormatStrategy('dual_generation');
                setFormatsRequested(['16:9', '9:16']);
              }}
              className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                formatStrategy === 'dual_generation'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                  : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
              }`}>
              Dual
            </button>

            <button
              type="button"
              onClick={() => {
                setFormatStrategy('multi_format');
                setFormatsRequested(['16:9', '9:16', '4:5', '1:1']);
              }}
              className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                formatStrategy === 'multi_format'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                  : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
              }`}>
              Multi
            </button>
          </div>
        </div>

        {/* Step 6: Video Engine */}
        <div className="mb-1">
          <label className="text-[10px] font-medium text-[#666] mb-0.5 block">
            {lang === 'pt' ? 'Engine de Vídeo Padrão' : 'Default Video Engine'}
          </label>
          <div className="grid grid-cols-2 gap-0.5">
            <button
              type="button"
              onClick={() => setVideoEngine('sora')}
              className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                videoEngine === 'sora'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                  : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
              }`}>
              Sora 2 (12s)
            </button>

            <button
              type="button"
              onClick={() => setVideoEngine('kling')}
              className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                videoEngine === 'kling'
                  ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                  : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
              }`}>
              Kling AI (5min)
            </button>
          </div>
        </div>

        {/* Step 7: Target Duration (only for Kling) */}
        {videoEngine === 'kling' && (
          <div className="mb-1">
            <label className="text-[10px] font-medium text-[#666] mb-0.5 block">
              {lang === 'pt' ? 'Duração Padrão (min)' : 'Default Duration (min)'}
            </label>
            <div className="grid grid-cols-5 gap-0.5">
              {[5, 10, 15, 20, 25].map(duration => (
                <button
                  key={duration}
                  type="button"
                  onClick={() => setTargetDuration(duration)}
                  className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                    targetDuration === duration
                      ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                      : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                  }`}>
                  {duration}min
                </button>
              ))}
            </div>
          </div>
        )}

        <p className="text-[9px] text-[#999] italic mt-2">
          💡 {lang === 'pt' 
            ? 'Esses valores serão aplicados automaticamente ao criar novos projetos' 
            : 'These values will be applied automatically when creating new projects'}
        </p>

        {/* Action Buttons */}
        <div className="flex gap-2 pt-0.5">
          <button 
            onClick={onClose}
            className="flex-1 px-4 py-1.5 rounded-lg border-2 border-[#E0E0E0] text-xs font-medium text-[#666] hover:text-[#333] hover:border-[#8B5CF6] transition bg-white/80">
            {lang === 'pt' ? 'Cancelar' : 'Cancel'}
          </button>
          <button 
            onClick={handleCreate} 
            disabled={!isValid}
            className="flex-1 bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] hover:from-[#7C3AED] hover:to-[#6D28D9] rounded-lg py-1.5 text-xs font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-1.5 shadow-lg shadow-[#8B5CF6]/40 transition-all">
            {lang === 'pt' ? 'Salvar' : 'Save'}
          </button>
        </div>
      </div>
    </div>
    
    {/* Modals de Empresa - Renderizados FORA do modal principal */}
    {/* Modal: Create Company (inline) */}
    {showCreateCompany && (
      <div className="fixed inset-0 z-[80] bg-black/85 backdrop-blur-sm flex items-center justify-center p-0" onClick={() => setShowCreateCompany(false)}>
        <div className="bg-white rounded-lg p-4 max-w-md w-[90%] space-y-3 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between">
            <h4 className="text-base font-semibold text-[#333] flex items-center gap-2">
              <Building2 size={18} className="text-[#8B5CF6]" />
              {lang === 'pt' ? 'Nova Empresa' : 'New Company'}
            </h4>
            <button onClick={() => setShowCreateCompany(false)} className="text-[#999] hover:text-[#333] transition">
              <X size={18} />
            </button>
          </div>
          
          {/* Company Name */}
          <div>
            <label className="text-xs font-medium text-[#666] mb-1.5 block">
              {lang === 'pt' ? 'Nome da Empresa *' : 'Company Name *'}
            </label>
            <input
              value={newCompanyName}
              onChange={e => setNewCompanyName(e.target.value)}
              placeholder={lang === 'pt' ? 'Ex: Biblizoo, Agent22...' : 'Ex: Biblizoo, Agent22...'}
              autoFocus
              className="w-full bg-white/80 border-2 border-[#E0E0E0] rounded-lg px-3 py-2.5 text-sm text-[#333] placeholder-[#999] outline-none focus:border-[#8B5CF6] transition"
            />
          </div>
          
          {/* Logo Upload */}
          <div>
            <label className="text-xs font-medium text-[#666] mb-1.5 block">
              {lang === 'pt' ? 'Logo (PNG ou JPEG)' : 'Logo (PNG or JPEG)'}
            </label>
            
            <div className="flex items-start gap-3">
              <div className="shrink-0">
                <div className="w-24 h-24 rounded-lg overflow-hidden">
                  {newCompanyLogo ? (
                    <img 
                      src={newCompanyLogo} 
                      alt="Logo preview" 
                      className="w-full h-full object-cover"
                      style={{ objectPosition: newLogoPosition }}
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-[#F3F0FF] to-[#E8E3FF] flex items-center justify-center border-2 border-[#E0E0E0]">
                      <Building2 size={32} className="text-[#8B5CF6]/40" />
                    </div>
                  )}
                </div>
                
                {newCompanyLogo && (
                  <div className="mt-2 grid grid-cols-3 gap-0.5 bg-[#E0E0E0] rounded p-0.5">
                    {[
                      { id: 'top', label: '↑' },
                      { id: 'center', label: '●' },
                      { id: 'bottom', label: '↓' },
                      { id: 'left', label: '←' },
                      { id: 'center', label: '●' },
                      { id: 'right', label: '→' },
                    ].slice(0, 5).map((pos, idx) => {
                      const positions = ['top', 'center', 'bottom', 'left', 'right'];
                      const labels = ['↑', '●', '↓', '←', '→'];
                      return (
                        <button
                          key={positions[idx]}
                          type="button"
                          onClick={() => setNewLogoPosition(positions[idx])}
                          className={`px-2 py-1 text-xs rounded transition ${
                            newLogoPosition === positions[idx]
                              ? 'bg-[#8B5CF6] text-white'
                              : 'bg-white text-[#666] hover:bg-[#F9F7FF]'
                          }`}
                          title={positions[idx]}>
                          {labels[idx]}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
              
              <label className="flex-1 cursor-pointer">
                <div className="border-2 border-dashed border-[#E0E0E0] hover:border-[#8B5CF6] rounded-lg px-4 py-3 text-center transition-all bg-white/50 hover:bg-[#F9F7FF] h-24 flex flex-col items-center justify-center">
                  {uploadingLogo ? (
                    <span className="text-xs text-[#666]">
                      {lang === 'pt' ? 'Fazendo upload...' : 'Uploading...'}
                    </span>
                  ) : (
                    <>
                      <span className="text-xs text-[#666] block font-medium">
                        {lang === 'pt' ? 'Clique para fazer upload' : 'Click to upload'}
                      </span>
                      <span className="text-[10px] text-[#999] mt-0.5 block">
                        PNG, JPEG • Max 5MB
                      </span>
                    </>
                  )}
                </div>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  onChange={handleLogoUpload}
                  disabled={uploadingLogo}
                  className="hidden"
                />
              </label>
            </div>
            
            {newCompanyLogo && (
              <button
                onClick={() => {
                  setNewCompanyLogo('');
                  setNewLogoPosition('center');
                }}
                className="mt-2 text-xs text-[#999] hover:text-red-500 transition">
                {lang === 'pt' ? '✕ Remover logo' : '✕ Remove logo'}
              </button>
            )}
          </div>
          
          <p className="text-[10px] text-[#666] bg-[#F9F7FF] rounded px-2 py-1.5 border border-[#E8E3FF]">
            💡 {lang === 'pt' 
              ? 'As configurações atuais do projeto serão salvas como padrão para esta empresa.' 
              : 'Current project settings will be saved as defaults for this company.'}
          </p>
          
          <div className="flex gap-2 pt-1">
            <button
              onClick={() => setShowCreateCompany(false)}
              className="flex-1 px-4 py-2.5 rounded-lg border-2 border-[#E0E0E0] text-xs font-medium text-[#666] hover:text-[#333] hover:border-[#8B5CF6] transition bg-white/80">
              {lang === 'pt' ? 'Cancelar' : 'Cancel'}
            </button>
            <button
              onClick={handleCreateCompany}
              disabled={!newCompanyName.trim() || creatingCompany}
              className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-sm font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:shadow-[#8B5CF6]/30">
              {creatingCompany 
                ? (lang === 'pt' ? 'Criando...' : 'Creating...') 
                : (lang === 'pt' ? 'Criar Empresa' : 'Create Company')}
            </button>
          </div>
        </div>
      </div>
    )}
    
    {/* Modal: Edit Company */}
    {showEditCompany && editingCompany && (
      <div className="fixed inset-0 z-[80] bg-black/85 backdrop-blur-sm flex items-center justify-center p-0" onClick={() => setShowEditCompany(false)}>
        <div className="bg-white rounded-lg p-4 max-w-md w-[90%] max-h-[90vh] overflow-y-auto space-y-3 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between">
            <h4 className="text-base font-semibold text-[#333] flex items-center gap-2">
              <Edit2 size={18} className="text-[#8B5CF6]" />
              {lang === 'pt' ? 'Editar Empresa' : 'Edit Company'}
            </h4>
            <button onClick={() => setShowEditCompany(false)} className="text-[#999] hover:text-[#333] transition">
              <X size={18} />
            </button>
          </div>
          
          {/* Company Name */}
          <div>
            <label className="text-xs font-medium text-[#666] mb-0.5 block">
              {lang === 'pt' ? 'Nome da Empresa *' : 'Company Name *'}
            </label>
            <input
              value={editCompanyName}
              onChange={e => setEditCompanyName(e.target.value)}
              placeholder={lang === 'pt' ? 'Ex: Biblizoo, Agent22...' : 'Ex: Biblizoo, Agent22...'}
              autoFocus
              className="w-full bg-white/80 border-2 border-[#E0E0E0] rounded-lg px-3 py-1.5 text-sm text-[#333] placeholder-[#999] outline-none focus:border-[#8B5CF6] transition"
            />
          </div>
          
          {/* Logo Upload - SIMPLIFICADO */}
          <div>
            <label className="text-xs font-medium text-[#666] mb-0.5 block">
              {lang === 'pt' ? 'Logo (PNG ou JPEG)' : 'Logo (PNG or JPEG)'}
            </label>
            
            <div className="flex items-center gap-2">
              <div className="shrink-0 w-16 h-12 rounded-lg overflow-hidden bg-white border border-[#E0E0E0] flex items-center justify-center">
                {editCompanyLogo ? (
                  <img 
                    src={editCompanyLogo} 
                    alt="Logo" 
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <Building2 size={16} className="text-gray-300" />
                )}
              </div>
              
              <label className="flex-1 cursor-pointer">
                <div className="border-2 border-dashed border-[#E0E0E0] hover:border-[#8B5CF6] rounded-lg px-2 py-1.5 text-center transition bg-white/50 hover:bg-[#F9F7FF]">
                  <span className="text-[9px] text-[#666] font-medium block">
                    {uploadingEditLogo 
                      ? (lang === 'pt' ? 'Enviando...' : 'Uploading...') 
                      : (editCompanyLogo 
                          ? (lang === 'pt' ? 'Alterar logo' : 'Change')
                          : (lang === 'pt' ? 'Adicionar logo' : 'Add logo'))}
                  </span>
                  <span className="text-[7px] text-[#999]">PNG/JPEG • 5MB</span>
                </div>
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  onChange={handleEditLogoUpload}
                  disabled={uploadingEditLogo}
                  className="hidden"
                />
              </label>
              
              {editCompanyLogo && (
                <button
                  type="button"
                  onClick={() => {
                    setEditCompanyLogo('');
                  }}
                  className="text-[9px] text-red-500 hover:text-red-600 transition whitespace-nowrap">
                  ✕ Remover
                </button>
              )}
            </div>
          </div>
          
          {/* PROJECT DEFAULTS SECTION - COMPACTO */}
          <div className="border-t-2 border-[#E0E0E0] pt-2 mt-1">
            <h5 className="text-sm font-semibold text-[#333] mb-0.5 flex items-center gap-1.5">
              ⚙️ Padrões de Projeto
            </h5>
            <p className="text-[9px] text-[#999] mb-1.5">
              Configure valores padrão que serão aplicados automaticamente ao criar novos projetos
            </p>
            
            {/* Default Visual Style - COMPLETO */}
            <div className="mb-1">
              <label className="text-[10px] font-medium text-[#666] mb-0.5 block">Estilo Visual Padrão</label>
              <div className="grid grid-cols-3 gap-0.5">
                {[
                  { id: 'pixar_3d', label: 'Pixar 3D' },
                  { id: 'cartoon_3d', label: 'Cartoon 3D' },
                  { id: 'cartoon_2d', label: 'Cartoon 2D' },
                  { id: 'anime_2d', label: 'Anime 2D' },
                  { id: 'realistic', label: 'Realista' },
                  { id: 'watercolor', label: 'Aquarela' },
                ].map(style => (
                  <button key={style.id} type="button"
                    onClick={() => setEditCompanyDefaults(p => ({ ...p, default_visual_style: style.id, default_animation_sub: style.id }))}
                    className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                      editCompanyDefaults.default_visual_style === style.id
                        ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                        : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                    }`}>
                    {style.label}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Default Character Folder */}
            <div className="mb-1">
              <label className="text-[10px] font-medium text-[#666] mb-0.5 block">Pasta de Personagens Padrão</label>
              <div className="grid grid-cols-2 gap-0.5 max-h-20 overflow-y-auto p-0.5 bg-gray-50 rounded-lg">
                {folders.length > 0 ? folders.map(folder => (
                  <button key={folder.id} type="button"
                    onClick={() => setEditCompanyDefaults(p => ({ ...p, default_character_folder_id: folder.id }))}
                    className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition text-left ${
                      editCompanyDefaults.default_character_folder_id === folder.id
                        ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                        : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-white'
                    }`}>
                    📁 {folder.name}
                  </button>
                )) : (
                  <p className="text-[10px] text-[#999] col-span-2 py-0.5 text-center">
                    Nenhuma pasta
                  </p>
                )}
              </div>
            </div>

            {/* Default Target Audience */}
            <div className="mb-1">
              <label className="text-[10px] font-medium text-[#666] mb-0.5 block">Público-Alvo Padrão</label>
              <div className="grid grid-cols-4 gap-0.5">
                {[
                  { id: '3-6', label: '3-6' },
                  { id: '6-9', label: '6-9' },
                  { id: '10-13', label: '10-13' },
                  { id: '14-17', label: '14-17' },
                  { id: '18-25', label: '18-25' },
                  { id: '25+', label: '25+' },
                  { id: 'all', label: 'Todas' },
                ].map(age => (
                  <button key={age.id} type="button"
                    onClick={() => setEditCompanyDefaults(p => ({ ...p, default_target_audience: age.id }))}
                    className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                      editCompanyDefaults.default_target_audience === age.id
                        ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                        : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                    }`}>
                    {age.label}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Default Format */}
            <div className="mb-1">
              <label className="text-[10px] font-medium text-[#666] mb-0.5 block">Formato Padrão</label>
              <div className="grid grid-cols-3 gap-0.5">
                {[
                  { id: 'safe_zone', label: 'Safe Zone' },
                  { id: 'dual', label: 'Dual' },
                  { id: 'multi', label: 'Multi' },
                ].map(format => (
                  <button key={format.id} type="button"
                    onClick={() => setEditCompanyDefaults(p => ({ ...p, default_format_strategy: format.id }))}
                    className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                      editCompanyDefaults.default_format_strategy === format.id
                        ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                        : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                    }`}>
                    {format.label}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Default Video Engine */}
            <div className="mb-1">
              <label className="text-[10px] font-medium text-[#666] mb-0.5 block">Engine de Vídeo Padrão</label>
              <div className="grid grid-cols-2 gap-0.5">
                {[
                  { id: 'sora', label: 'Sora 2 (12s)' },
                  { id: 'kling', label: 'Kling AI (5min)' },
                ].map(engine => (
                  <button key={engine.id} type="button"
                    onClick={() => setEditCompanyDefaults(p => ({ ...p, default_video_engine: engine.id }))}
                    className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                      editCompanyDefaults.default_video_engine === engine.id
                        ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                        : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                    }`}>
                    {engine.label}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Default Duration (only for Kling) */}
            {editCompanyDefaults.default_video_engine === 'kling' && (
              <div className="mb-1">
                <label className="text-[10px] font-medium text-[#666] mb-0.5 block">Duração Padrão (min)</label>
                <div className="grid grid-cols-5 gap-0.5">
                  {[5, 10, 15, 20, 25].map(duration => (
                    <button key={duration} type="button"
                      onClick={() => setEditCompanyDefaults(p => ({ ...p, default_target_duration: duration }))}
                      className={`px-1.5 py-0.5 rounded-lg border-2 text-[10px] font-medium transition ${
                        editCompanyDefaults.default_target_duration === duration
                          ? 'border-[#8B5CF6] bg-[#8B5CF6]/5 text-[#8B5CF6]'
                          : 'border-[#E0E0E0] text-[#666] hover:border-[#8B5CF6]/30 hover:bg-[#F9F7FF]'
                      }`}>
                      {duration}min
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            <p className="text-[9px] text-[#999] italic mt-2">
              💡 Esses valores serão aplicados automaticamente ao criar novos projetos
            </p>
          </div>
          
          <div className="flex gap-2 pt-0.5">
            <button
              onClick={() => setShowEditCompany(false)}
              className="flex-1 px-4 py-1.5 rounded-lg border-2 border-[#E0E0E0] text-xs font-medium text-[#666] hover:text-[#333] hover:border-[#8B5CF6] transition bg-white/80">
              {lang === 'pt' ? 'Cancelar' : 'Cancel'}
            </button>
            <button
              onClick={handleUpdateCompany}
              disabled={!editCompanyName.trim() || updatingCompany}
              className="flex-1 px-4 py-1.5 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-xs font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:shadow-[#8B5CF6]/30">
              {updatingCompany 
                ? (lang === 'pt' ? 'Salvando...' : 'Saving...') 
                : (lang === 'pt' ? 'Salvar' : 'Save')}
            </button>
          </div>
        </div>
      </div>
    )}
    </>
  );
}

