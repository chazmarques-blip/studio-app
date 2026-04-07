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
          logo_position: editLogoPosition
        })
      });
      
      if (response.ok) {
        console.log('✅ [COMPANY] Updated');
        // Update local state
        setCompanies(prev => prev.map(c => 
          c.id === editingCompany.id 
            ? { ...c, name: editCompanyName.trim(), logo_url: editCompanyLogo || null, logo_position: editLogoPosition }
            : c
        ));
        // Update selected company if it's the one being edited
        if (selectedCompany?.id === editingCompany.id) {
          setSelectedCompany({ 
            ...selectedCompany, 
            name: editCompanyName.trim(), 
            logo_url: editCompanyLogo || null,
            logo_position: editLogoPosition
          });
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
              {/* Option: No company (standalone project) - Only show if no company selected */}
              {!selectedCompany && (
                <button
                  type="button"
                  onClick={() => setSelectedCompany(null)}
                  className="shrink-0 flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 border-dashed border-[#E0E0E0] bg-white/50 hover:border-[#8B5CF6] hover:bg-[#8B5CF6]/5 transition-all">
                  <div className="w-12 h-12 rounded-lg flex items-center justify-center border-2 border-dashed border-[#DDD]">
                    <Sparkles size={20} className="text-[#999]" />
                  </div>
                  <span className="text-xs font-medium text-center whitespace-nowrap text-[#666]">
                    {lang === 'pt' ? 'Sem Empresa' : 'No Company'}
                  </span>
                </button>
              )}

              {/* Existing companies */}
              {companies.map(company => (
                <div key={company.id} className="shrink-0 relative group">
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
                        
                        // Auto-select first folder if company has folders
                        if (company.folder_ids && company.folder_ids.length > 0) {
                          setSelectedFolder(company.folder_ids[0]);
                        }
                      }
                    }}
                    className={`w-full flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 transition-all ${
                      selectedCompany?.id === company.id
                        ? 'border-[#8B5CF6] bg-[#F3F0FF]'
                        : 'border-[#E0E0E0] bg-white/50 hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
                    }`}>
                    <div className="w-12 h-12 rounded-lg overflow-hidden">
                      {company.logo_url ? (
                        <img 
                          src={company.logo_url} 
                          alt={company.name} 
                          className="w-full h-full object-cover"
                          style={{ objectPosition: company.logo_position || 'center' }}
                        />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-[#F3F0FF] to-[#E8E3FF] flex items-center justify-center">
                          <Building2 size={20} className="text-[#8B5CF6]" />
                        </div>
                      )}
                    </div>
                    <span className="text-xs font-medium text-center max-w-[80px] truncate text-[#333]">
                      {company.name}
                    </span>
                    {company.is_primary && (
                      <span className="text-[9px] bg-green-500/20 text-green-600 px-1.5 py-0.5 rounded-full font-semibold">
                        PRINCIPAL
                      </span>
                    )}
                    {selectedCompany?.id === company.id && (
                      <Check size={14} strokeWidth={2.5} className="text-[#8B5CF6]" />
                    )}
                  </button>
                  
                  {/* Edit/Delete buttons - appear on hover */}
                  <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                    <button
                      type="button"
                      onClick={(e) => handleOpenEditCompany(company, e)}
                      className="p-1 rounded bg-[#8B5CF6] hover:bg-[#7C3AED] text-white transition"
                      title={lang === 'pt' ? 'Editar' : 'Edit'}>
                      <Edit2 size={12} />
                    </button>
                    <button
                      type="button"
                      onClick={(e) => handleDeleteCompany(company.id, e)}
                      className="p-1 rounded bg-red-500 hover:bg-red-600 text-white transition"
                      title={lang === 'pt' ? 'Excluir' : 'Delete'}>
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))}

              {/* Button: Create new company */}
              <button
                type="button"
                onClick={() => setShowCreateCompany(true)}
                className="shrink-0 flex flex-col items-center gap-1.5 p-3 rounded-lg border-2 border-dashed border-[#E0E0E0] hover:border-[#8B5CF6] bg-white/50 hover:bg-[#F9F7FF] transition-all">
                <div className="w-12 h-12 rounded-lg flex items-center justify-center border-2 border-dashed border-[#DDD]">
                  <Plus size={20} className="text-[#8B5CF6]" />
                </div>
                <span className="text-xs font-medium text-center whitespace-nowrap text-[#666]">
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
        
        {/* Modal: Create Company (inline) */}
        {showCreateCompany && (
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setShowCreateCompany(false)}>
            <div className="bg-white rounded-xl border-2 border-[#8B5CF6]/30 p-5 max-w-lg w-full space-y-4 shadow-2xl" onClick={e => e.stopPropagation()}>
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
                  {/* Preview - Logo ocupa TODO o espaço */}
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
                    
                    {/* Position controls - appear when logo is uploaded */}
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
                          // Only show: top, center, bottom, left, right (skip duplicate center)
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
                  
                  {/* Upload Button */}
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
          <div className="fixed inset-0 z-[70] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setShowEditCompany(false)}>
            <div className="bg-white rounded-xl border-2 border-[#8B5CF6]/30 p-5 max-w-lg w-full space-y-4 shadow-2xl" onClick={e => e.stopPropagation()}>
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
                <label className="text-xs font-medium text-[#666] mb-1.5 block">
                  {lang === 'pt' ? 'Nome da Empresa *' : 'Company Name *'}
                </label>
                <input
                  value={editCompanyName}
                  onChange={e => setEditCompanyName(e.target.value)}
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
                  {/* Preview - Logo ocupa TODO o espaço */}
                  <div className="shrink-0">
                    <div className="w-24 h-24 rounded-lg overflow-hidden">
                      {editCompanyLogo ? (
                        <img 
                          src={editCompanyLogo} 
                          alt="Logo preview" 
                          className="w-full h-full object-cover"
                          style={{ objectPosition: editLogoPosition }}
                        />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-[#F3F0FF] to-[#E8E3FF] flex items-center justify-center border-2 border-[#E0E0E0]">
                          <Building2 size={32} className="text-[#8B5CF6]/40" />
                        </div>
                      )}
                    </div>
                    
                    {/* Position controls - appear when logo is uploaded */}
                    {editCompanyLogo && (
                      <div className="mt-2 grid grid-cols-3 gap-0.5 bg-[#E0E0E0] rounded p-0.5">
                        {['top', 'center', 'bottom', 'left', 'right'].map((pos, idx) => {
                          const labels = ['↑', '●', '↓', '←', '→'];
                          return (
                            <button
                              key={pos}
                              type="button"
                              onClick={() => setEditLogoPosition(pos)}
                              className={`px-2 py-1 text-xs rounded transition ${
                                editLogoPosition === pos
                                  ? 'bg-[#8B5CF6] text-white'
                                  : 'bg-white text-[#666] hover:bg-[#F9F7FF]'
                              }`}
                              title={pos}>
                              {labels[idx]}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                  
                  {/* Upload Button */}
                  <label className="flex-1 cursor-pointer">
                    <div className="border-2 border-dashed border-[#E0E0E0] hover:border-[#8B5CF6] rounded-lg px-4 py-3 text-center transition-all bg-white/50 hover:bg-[#F9F7FF] h-24 flex flex-col items-center justify-center">
                      {uploadingEditLogo ? (
                        <span className="text-xs text-[#666]">
                          {lang === 'pt' ? 'Fazendo upload...' : 'Uploading...'}
                        </span>
                      ) : (
                        <>
                          <span className="text-xs text-[#666] block font-medium">
                            {lang === 'pt' ? 'Clique para alterar' : 'Click to change'}
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
                      onChange={handleEditLogoUpload}
                      disabled={uploadingEditLogo}
                      className="hidden"
                    />
                  </label>
                </div>
                
                {editCompanyLogo && (
                  <button
                    onClick={() => {
                      setEditCompanyLogo('');
                      setEditLogoPosition('center');
                    }}
                    className="mt-2 text-xs text-[#999] hover:text-red-500 transition">
                    {lang === 'pt' ? '✕ Remover logo' : '✕ Remove logo'}
                  </button>
                )}
              </div>
              
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => setShowEditCompany(false)}
                  className="flex-1 px-4 py-2.5 rounded-lg border-2 border-[#E0E0E0] text-xs font-medium text-[#666] hover:text-[#333] hover:border-[#8B5CF6] transition bg-white/80">
                  {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                </button>
                <button
                  onClick={handleUpdateCompany}
                  disabled={!editCompanyName.trim() || updatingCompany}
                  className="flex-1 px-4 py-2.5 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-sm font-bold text-white disabled:opacity-30 disabled:cursor-not-allowed transition-all hover:shadow-lg hover:shadow-[#8B5CF6]/30">
                  {updatingCompany 
                    ? (lang === 'pt' ? 'Salvando...' : 'Saving...') 
                    : (lang === 'pt' ? 'Salvar Alterações' : 'Save Changes')}
                </button>
              </div>
            </div>
          </div>
        )}

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
            className="w-full bg-white/80 border-2 border-[#E0E0E0] focus:border-[#8B5CF6] rounded-lg px-3 py-2 text-sm text-[#333] outline-none placeholder-[#999] transition" 
          />
        </div>

        {/* Step 2: Visual Style - UMA LINHA COMPACTA */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">2</span>
            {lang === 'pt' ? 'Estilo Visual' : 'Visual Style'}
            <span className="text-red-400">*</span>
          </label>
          <div className="flex gap-1 overflow-x-auto pb-1">
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
                  className={`shrink-0 px-2 py-1 rounded-md border-2 transition-all flex items-center gap-1 ${
                    animationSub === s.id
                      ? 'border-[#8B5CF6] bg-[#F3F0FF] text-[#8B5CF6]'
                      : 'border-[#E0E0E0] bg-white/80 text-[#666] hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
                  }`}>
                  <Icon size={12} strokeWidth={1.5} />
                  <span className="text-[11px] font-medium whitespace-nowrap">{s.label}</span>
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
          <div className="flex gap-1 overflow-x-auto pb-1">
            {/* Option: Create New Characters */}
            <button
              type="button"
              onClick={() => setSelectedFolder(null)}
              className={`shrink-0 px-2 py-1 rounded-md border-2 transition-all flex items-center gap-1 ${
                selectedFolder === null
                  ? 'border-[#8B5CF6] bg-[#F3F0FF] text-[#8B5CF6]'
                  : 'border-[#E0E0E0] bg-white/80 text-[#666] hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
              }`}>
              <Sparkles size={12} strokeWidth={1.5} />
              <span className="text-[11px] font-medium whitespace-nowrap">
                {lang === 'pt' ? 'Criar Novos' : 'Create New'}
              </span>
            </button>

            {/* Loading state */}
            {loadingFolders && (
              <div className="shrink-0 px-2 py-1 text-[11px] text-[#666]">
                {lang === 'pt' ? 'Carregando...' : 'Loading...'}
              </div>
            )}

            {/* Existing folders */}
            {!loadingFolders && folders.map(folder => (
              <button
                key={folder.id}
                type="button"
                onClick={() => setSelectedFolder(folder.id)}
                className={`shrink-0 px-2 py-1 rounded-md border-2 transition-all flex items-center gap-1 ${
                  selectedFolder === folder.id
                    ? 'border-[#8B5CF6] bg-[#F3F0FF] text-[#8B5CF6]'
                    : 'border-[#E0E0E0] bg-white/80 text-[#666] hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
                }`}>
                <Users size={12} strokeWidth={1.5} />
                <span className="text-[11px] font-medium whitespace-nowrap">{folder.name}</span>
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
          <div className="flex gap-1">
            {/* Safe Zone */}
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('safe_zone');
                setFormatsRequested(['16:9']);
              }}
              className={`flex-1 p-1.5 rounded-md border-2 text-left transition-all ${
                formatStrategy === 'safe_zone'
                  ? 'border-[#8B5CF6] bg-[#F3F0FF]'
                  : 'border-[#E0E0E0] bg-white/80 hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
              }`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[11px] font-semibold text-[#333]">Safe Zone</span>
                {formatStrategy === 'safe_zone' && (
                  <Check size={10} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </div>
              <div className="text-[9px] text-[#666]">16:9 → Crop 9:16</div>
            </button>

            {/* Dual Generation */}
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('dual_generation');
                setFormatsRequested(['16:9', '9:16']);
              }}
              className={`flex-1 p-1.5 rounded-md border-2 text-left transition-all ${
                formatStrategy === 'dual_generation'
                  ? 'border-[#8B5CF6] bg-[#F3F0FF]'
                  : 'border-[#E0E0E0] bg-white/80 hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
              }`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[11px] font-semibold text-[#333]">Dual</span>
                {formatStrategy === 'dual_generation' && (
                  <Check size={10} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </div>
              <div className="text-[9px] text-[#666]">16:9 + 9:16</div>
            </button>

            {/* Multi-Format */}
            <button
              type="button"
              onClick={() => {
                setFormatStrategy('multi_format');
                setFormatsRequested(['16:9', '9:16', '4:5', '1:1']);
              }}
              className={`flex-1 p-1.5 rounded-md border-2 text-left transition-all ${
                formatStrategy === 'multi_format'
                  ? 'border-[#8B5CF6] bg-[#F3F0FF]'
                  : 'border-[#E0E0E0] bg-white/80 hover:border-[#8B5CF6] hover:bg-[#F9F7FF]'
              }`}>
              <div className="flex items-center justify-between mb-0.5">
                <span className="text-[11px] font-semibold text-[#333]">Multi</span>
                {formatStrategy === 'multi_format' && (
                  <Check size={10} strokeWidth={2.5} className="text-[#8B5CF6]" />
                )}
              </div>
              <div className="text-[9px] text-[#666]">Todos</div>
            </button>
          </div>
        </div>

        {/* Step 5: Video Engine - NEW */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#999] flex items-center gap-1.5">
            <span className="text-[#8B5CF6] text-xs">5</span>
            {lang === 'pt' ? '🎬 Engine de Vídeo' : '🎬 Video Engine'}
          </label>
          <div className="grid grid-cols-2 gap-2">
            {/* Sora 2 */}
            <button
              type="button"
              onClick={() => setVideoEngine('sora')}
              className={`p-2 rounded-md border-2 text-left transition-all ${
                videoEngine === 'sora'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-[#E0E0E0] bg-white/80 hover:border-blue-300'
              }`}>
              <div className="flex items-center gap-1.5 mb-1">
                <div className={`w-5 h-5 rounded flex items-center justify-center ${
                  videoEngine === 'sora' ? 'bg-blue-500' : 'bg-gray-300'
                }`}>
                  <span className="text-white text-[10px] font-bold">S</span>
                </div>
                <span className={`text-[11px] font-semibold ${videoEngine === 'sora' ? 'text-blue-600' : 'text-gray-700'}`}>
                  Sora 2
                </span>
                {videoEngine === 'sora' && (
                  <Check size={10} strokeWidth={2.5} className="text-blue-500 ml-auto" />
                )}
              </div>
              <div className="text-[9px] text-gray-600 space-y-0.5 ml-6">
                <div>⏱️ 12s/cena</div>
                <div>🎨 Boa cont.</div>
                <div>💰 ~$0.12/s</div>
              </div>
            </button>

            {/* Kling AI */}
            <button
              type="button"
              onClick={() => setVideoEngine('kling')}
              className={`p-2 rounded-md border-2 text-left transition-all ${
                videoEngine === 'kling'
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-[#E0E0E0] bg-white/80 hover:border-purple-300'
              }`}>
              <div className="flex items-center gap-1.5 mb-1">
                <div className={`w-5 h-5 rounded flex items-center justify-center ${
                  videoEngine === 'kling' ? 'bg-purple-500' : 'bg-gray-300'
                }`}>
                  <span className="text-white text-[10px] font-bold">K</span>
                </div>
                <span className={`text-[11px] font-semibold ${videoEngine === 'kling' ? 'text-purple-600' : 'text-gray-700'}`}>
                  Kling AI
                </span>
                {videoEngine === 'kling' && (
                  <Check size={10} strokeWidth={2.5} className="text-purple-500 ml-auto" />
                )}
              </div>
              <div className="text-[9px] text-gray-600 space-y-0.5 ml-6">
                <div>⏱️ 5min</div>
                <div>🎨 Exc. cont.</div>
                <div>💰 ~$0.05/s</div>
              </div>
            </button>
          </div>
        </div>

        {/* Advanced Settings - Removido para compactar modal */}

        {/* Action Buttons - COMPACTO */}
        <div className="flex gap-2 pt-2">
          <button 
            onClick={onClose}
            className="px-4 py-2 rounded-lg border-2 border-[#E0E0E0] text-xs font-medium text-[#666] hover:text-[#333] hover:border-[#8B5CF6] transition bg-white/80">
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
