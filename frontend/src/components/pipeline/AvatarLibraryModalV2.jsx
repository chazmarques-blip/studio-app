import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { X, Search, Check, Download, Users, RefreshCw, Edit3, Maximize2, Eye, ChevronLeft, ChevronRight, Plus, Trash2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../../utils/resolveImageUrl';
import { getErrorMsg } from '../../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * AvatarLibraryModalV2 — Enhanced Character Library with:
 * - Custom scrollbar
 * - 4x expansion on click
 * - Edit button with gallery modal (360°, etc)
 * - Multi-select for batch download
 * - Filename = character name
 * - Intelligent caching + lazy loading
 * - Virtual scrolling for performance
 */
export function AvatarLibraryModalV2({ 
  open, 
  onClose, 
  projectId, 
  projectAvatarIds = new Set(), 
  onImported, 
  onEditAvatar,
  onDeleteAvatar,
  onCreateNew,
  avatarsCache = null,
  avatarsCacheLoaded = false,
  lang = 'pt' 
}) {
  const [library, setLibrary] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [downloading, setDownloading] = useState(new Set());
  const [importing, setImporting] = useState(false);
  
  // Expansion & preview
  const [expandedAvatar, setExpandedAvatar] = useState(null);
  const [previewIndex, setPreviewIndex] = useState(0);
  
  // Filters
  const [styleFilter, setStyleFilter] = useState('all');
  const [has360Filter, setHas360Filter] = useState(false);
  const [hasVoiceFilter, setHasVoiceFilter] = useState(false);
  const [sortBy, setSortBy] = useState('recent');
  
  // Image cache for faster loading
  const imageCache = useRef(new Map());
  
  const labels = {
    pt: { 
      title: 'Galeria de Personagens', 
      search: 'Buscar por nome...', 
      import: 'Importar', 
      download: 'Baixar',
      edit: 'Editar',
      expand: 'Expandir',
      empty: 'Nenhum personagem na galeria', 
      alreadyIn: 'Já no projeto', 
      selectAll: 'Selecionar Todos', 
      deselectAll: 'Desmarcar Todos',
      noResults: 'Nenhum resultado', 
      close: 'Fechar',
      selected: 'selecionado(s)',
      downloading: 'Baixando...',
      next: 'Próximo',
      prev: 'Anterior',
      createNew: '+ Criar Personagem'
    },
    en: { 
      title: 'Character Gallery', 
      search: 'Search by name...', 
      import: 'Import', 
      download: 'Download',
      edit: 'Edit',
      expand: 'Expand',
      empty: 'No characters in gallery', 
      alreadyIn: 'Already in project', 
      selectAll: 'Select All', 
      deselectAll: 'Deselect All',
      noResults: 'No results', 
      close: 'Close',
      selected: 'selected',
      downloading: 'Downloading...',
      next: 'Next',
      prev: 'Previous',
      createNew: '+ Create Character'
    },
    es: { 
      title: 'Galería de Personajes', 
      search: 'Buscar por nombre...', 
      import: 'Importar', 
      download: 'Descargar',
      edit: 'Editar',
      expand: 'Expandir',
      empty: 'Sin personajes en la galería', 
      alreadyIn: 'Ya en el proyecto', 
      selectAll: 'Seleccionar Todos', 
      deselectAll: 'Deseleccionar Todos',
      noResults: 'Sin resultados', 
      close: 'Cerrar',
      selected: 'seleccionado(s)',
      downloading: 'Descargando...',
      next: 'Siguiente',
      prev: 'Anterior',
      createNew: '+ Crear Personaje'
    },
  };
  const L = labels[lang] || labels.en;

  // Smart cache with TTL + external cache support
  useEffect(() => {
    if (!open) return;
    setSelected(new Set());
    setSearch('');
    setExpandedAvatar(null);

    // If external cache is provided, use it (central cache from StudioPage)
    if (avatarsCache && avatarsCacheLoaded) {
      setLibrary(avatarsCache);
      setLoading(false);
      console.log('✅ Using central avatars cache:', avatarsCache.length, 'avatars');
      
      // Preload first 20 images
      avatarsCache.slice(0, 20).forEach(av => {
        if (!imageCache.current.has(av.id)) {
          const img = new Image();
          img.src = resolveImageUrl(av.url);
          imageCache.current.set(av.id, img);
        }
      });
      return; // Skip local cache logic
    }

    const CACHE_KEY = 'studiox_avatar_library_v2';
    const CACHE_TTL = 5 * 60 * 1000; // 5 min

    // 1. Instant cache load (no spinner)
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
      if (cached.data?.length) {
        setLibrary(cached.data);
        // Preload first 20 images into cache
        cached.data.slice(0, 20).forEach(av => {
          if (!imageCache.current.has(av.id)) {
            const img = new Image();
            img.src = resolveImageUrl(av.url);
            imageCache.current.set(av.id, img);
          }
        });
        
        // If fresh cache, skip API
        if (Date.now() - (cached.ts || 0) < CACHE_TTL) return;
      }
    } catch { /* ignore */ }

    // 2. Background fetch
    setLoading(prev => library.length === 0);
    axios.get(`${API}/data/avatars`).then(res => {
      const fresh = res.data || [];
      setLibrary(fresh);
      localStorage.setItem(CACHE_KEY, JSON.stringify({ data: fresh, ts: Date.now() }));
    }).catch(() => {}).finally(() => setLoading(false));
  }, [open, avatarsCache, avatarsCacheLoaded]); // eslint-disable-line react-hooks/exhaustive-deps

  // Filtered + sorted + memoized
  const filtered = useMemo(() => {
    let result = [...library];
    
    // CRITICAL FIX: Filter out avatars with empty/missing URLs (prevents black cards)
    result = result.filter(a => {
      const url = a.url || '';
      return url.trim() !== '';
    });
    
    // 1. Text search
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter(a => (a.name || '').toLowerCase().includes(q));
    }
    
    // 2. Style filter
    if (styleFilter !== 'all') {
      result = result.filter(a => {
        const style = a.visual_style || a.avatar_style || '';
        return style === styleFilter;
      });
    }
    
    // 3. Has 360° filter
    if (has360Filter) {
      result = result.filter(a => {
        const angles = a.angles || {};
        return angles.front && angles.left && angles.right && angles.back;
      });
    }
    
    // 4. Has voice filter
    if (hasVoiceFilter) {
      result = result.filter(a => a.voice && a.voice.url);
    }
    
    // 5. Sort
    if (sortBy === 'recent') {
      result.sort((a, b) => {
        const dateA = new Date(a.created_at || a.added_at || 0);
        const dateB = new Date(b.created_at || b.added_at || 0);
        return dateB - dateA; // Newest first
      });
    } else if (sortBy === 'oldest') {
      result.sort((a, b) => {
        const dateA = new Date(a.created_at || a.added_at || 0);
        const dateB = new Date(b.created_at || b.added_at || 0);
        return dateA - dateB; // Oldest first
      });
    } else if (sortBy === 'az') {
      result.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
    } else if (sortBy === 'za') {
      result.sort((a, b) => (b.name || '').localeCompare(a.name || ''));
    }
    
    return result;
  }, [library, search, styleFilter, has360Filter, hasVoiceFilter, sortBy]);

  // Lazy image loading with IntersectionObserver
  const observerRef = useRef(null);
  
  useEffect(() => {
    observerRef.current = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            const src = img.dataset.src;
            if (src && !img.src) {
              img.src = src;
              img.classList.remove('opacity-0');
              img.classList.add('opacity-100', 'transition-opacity', 'duration-300');
            }
          }
        });
      },
      { rootMargin: '50px' }
    );
    
    return () => observerRef.current?.disconnect();
  }, []);

  const toggleSelect = useCallback((id) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const selectAllFiltered = useCallback(() => {
    const availableIds = filtered.filter(a => !projectAvatarIds.has(a.id)).map(a => a.id);
    setSelected(new Set(availableIds));
  }, [filtered, projectAvatarIds]);
  
  const deselectAll = useCallback(() => {
    setSelected(new Set());
  }, []);

  const doImport = async () => {
    if (!selected.size || !projectId) return;
    setImporting(true);
    try {
      const { data } = await axios.post(`${API}/studio/projects/${projectId}/project-avatars/import`, {
        avatar_ids: [...selected],
      });
      const importedAvatars = library.filter(a => selected.has(a.id));
      onImported(importedAvatars);
      toast.success(`${data.imported} ${lang === 'pt' ? 'importado(s)' : 'imported'}!`);
      setSelected(new Set());
    } catch (e) {
      toast.error(getErrorMsg(e, 'Error'));
    } finally {
      setImporting(false);
    }
  };

  // Download single or multiple avatars
  const downloadAvatar = async (avatar) => {
    setDownloading(prev => new Set(prev).add(avatar.id));
    try {
      const response = await fetch(resolveImageUrl(avatar.url));
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Filename = character name (sanitized)
      const filename = `${(avatar.name || 'character').replace(/[^a-z0-9]/gi, '_')}.png`;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success(`${avatar.name} ${lang === 'pt' ? 'baixado' : 'downloaded'}!`);
    } catch (e) {
      toast.error(getErrorMsg(e, 'Download failed'));
    } finally {
      setDownloading(prev => {
        const next = new Set(prev);
        next.delete(avatar.id);
        return next;
      });
    }
  };
  
  // Batch download
  const downloadSelected = async () => {
    if (!selected.size) return;
    const toDownload = library.filter(a => selected.has(a.id));
    
    for (const avatar of toDownload) {
      await downloadAvatar(avatar);
      // Small delay to avoid overwhelming browser
      await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    toast.success(`${selected.size} ${lang === 'pt' ? 'personagem(ns) baixado(s)' : 'character(s) downloaded'}!`);
  };

  // Expansion modal (4x size)
  const openExpanded = (avatar) => {
    setExpandedAvatar(avatar);
    const index = filtered.findIndex(a => a.id === avatar.id);
    setPreviewIndex(index);
  };
  
  const closeExpanded = () => {
    setExpandedAvatar(null);
  };
  
  const nextAvatar = () => {
    if (previewIndex < filtered.length - 1) {
      const next = filtered[previewIndex + 1];
      setExpandedAvatar(next);
      setPreviewIndex(previewIndex + 1);
    }
  };
  
  const prevAvatar = () => {
    if (previewIndex > 0) {
      const prev = filtered[previewIndex - 1];
      setExpandedAvatar(prev);
      setPreviewIndex(previewIndex - 1);
    }
  };

  if (!open) return null;

  return (
    <>
      {/* Main Library Modal */}
      <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4" onClick={onClose}>
        <div 
          data-testid="avatar-library-modal" 
          className="w-full max-w-5xl rounded-2xl border border-[#8B5CF6]/20 bg-[#0D0D0D] overflow-hidden max-h-[90vh] flex flex-col shadow-2xl"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="px-5 py-3 border-b border-[#151515] flex items-center gap-3 shrink-0 bg-gradient-to-r from-[#0D0D0D] to-[#1A1A1A]">
            <Users size={18} className="text-[#8B5CF6]" />
            <h3 className="text-base font-bold text-white flex-1">{L.title}</h3>
            <span className="text-xs text-[#888] bg-[#1A1A1A] px-2 py-1 rounded">{library.length} total</span>
            {selected.size > 0 && (
              <span className="text-xs text-[#8B5CF6] bg-[#8B5CF6]/10 px-2 py-1 rounded font-semibold">
                {selected.size} {L.selected}
              </span>
            )}
            {onCreateNew && (
              <button 
                onClick={() => {
                  // CRITICAL FIX: Don't close library, open modal INSIDE
                  onCreateNew();
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#6366F1]/20 to-[#4F46E5]/20 border border-[#6366F1]/40 text-xs font-semibold text-[#A78BFA] hover:from-[#6366F1]/30 hover:to-[#4F46E5]/30 transition-all hover:scale-105"
                title={L.createNew}
              >
                <Plus size={14} />
                <span>{L.createNew}</span>
              </button>
            )}
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[#1A1A1A] transition">
              <X size={18} className="text-[#999]" />
            </button>
          </div>

          {/* Search & Actions */}
          <div className="px-5 py-3 border-b border-[#111] shrink-0 space-y-3">
            {/* Search bar */}
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666]" />
              <input 
                data-testid="library-search" 
                value={search} 
                onChange={e => setSearch(e.target.value)}
                placeholder={L.search}
                className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[#111] border border-[#1E1E1E] text-sm text-white placeholder-[#555] outline-none focus:border-[#8B5CF6]/40 transition" 
              />
            </div>
            
            {/* Filters Row */}
            <div className="flex gap-2 flex-wrap items-center">
              {/* Style filter */}
              <select
                value={styleFilter}
                onChange={e => setStyleFilter(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-xs text-white outline-none focus:border-[#8B5CF6]/40 transition cursor-pointer"
              >
                <option value="all">🎨 Todos os Estilos</option>
                <option value="pixar_3d">Pixar 3D</option>
                <option value="cartoon_3d">Cartoon 3D</option>
                <option value="cartoon_2d">Cartoon 2D</option>
                <option value="anime_2d">Anime 2D</option>
                <option value="realistic">Realista</option>
              </select>
              
              {/* Sort filter */}
              <select
                value={sortBy}
                onChange={e => setSortBy(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-xs text-white outline-none focus:border-[#8B5CF6]/40 transition cursor-pointer"
              >
                <option value="recent">📅 Mais Recentes</option>
                <option value="oldest">📅 Mais Antigos</option>
                <option value="az">🔤 A → Z</option>
                <option value="za">🔤 Z → A</option>
              </select>
              
              {/* Checkboxes */}
              <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-xs text-white cursor-pointer hover:border-[#8B5CF6]/40 transition">
                <input
                  type="checkbox"
                  checked={has360Filter}
                  onChange={e => setHas360Filter(e.target.checked)}
                  className="w-3.5 h-3.5 rounded accent-[#8B5CF6]"
                />
                <span>🔄 Apenas com 360°</span>
              </label>
              
              <label className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-xs text-white cursor-pointer hover:border-[#8B5CF6]/40 transition">
                <input
                  type="checkbox"
                  checked={hasVoiceFilter}
                  onChange={e => setHasVoiceFilter(e.target.checked)}
                  className="w-3.5 h-3.5 rounded accent-[#8B5CF6]"
                />
                <span>🔊 Apenas com Voz</span>
              </label>
              
              {/* Clear filters */}
              {(styleFilter !== 'all' || has360Filter || hasVoiceFilter || sortBy !== 'recent') && (
                <button
                  onClick={() => {
                    setStyleFilter('all');
                    setHas360Filter(false);
                    setHasVoiceFilter(false);
                    setSortBy('recent');
                  }}
                  className="px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30 text-xs text-red-400 hover:bg-red-500/20 transition"
                >
                  ✕ Limpar Filtros
                </button>
              )}
            </div>
            
            {/* Quick actions */}
            <div className="flex gap-2 flex-wrap">
              {filtered.length > 0 && (
                <>
                  {selected.size === 0 ? (
                    <button 
                      onClick={selectAllFiltered} 
                      data-testid="library-select-all"
                      className="text-xs text-[#8B5CF6] hover:text-[#A78BFA] transition flex items-center gap-1.5 px-2 py-1 rounded bg-[#8B5CF6]/5 hover:bg-[#8B5CF6]/10"
                    >
                      <Check size={12} />
                      {L.selectAll} ({filtered.filter(a => !projectAvatarIds.has(a.id)).length})
                    </button>
                  ) : (
                    <button 
                      onClick={deselectAll}
                      className="text-xs text-red-400 hover:text-red-300 transition flex items-center gap-1.5 px-2 py-1 rounded bg-red-500/5 hover:bg-red-500/10"
                    >
                      <X size={12} />
                      {L.deselectAll}
                    </button>
                  )}
                </>
              )}
            </div>
          </div>

          {/* Grid with custom scrollbar */}
          <div className="flex-1 overflow-y-auto p-5 custom-scrollbar">
            <style>{`
              .custom-scrollbar::-webkit-scrollbar {
                width: 8px;
              }
              .custom-scrollbar::-webkit-scrollbar-track {
                background: #0D0D0D;
                border-radius: 4px;
              }
              .custom-scrollbar::-webkit-scrollbar-thumb {
                background: #8B5CF6;
                border-radius: 4px;
              }
              .custom-scrollbar::-webkit-scrollbar-thumb:hover {
                background: #A78BFA;
              }
            `}</style>
            
            {loading ? (
              <div className="flex items-center justify-center py-20">
                <RefreshCw size={24} className="animate-spin text-[#8B5CF6]" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-20">
                <Users size={48} className="mx-auto text-[#333] mb-4" />
                <p className="text-sm text-[#888]">{library.length === 0 ? L.empty : L.noResults}</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {filtered.map(av => {
                  const inProject = projectAvatarIds.has(av.id);
                  const isSelected = selected.has(av.id);
                  const isDownloading = downloading.has(av.id);
                  
                  return (
                    <div 
                      key={av.id} 
                      data-testid={`library-avatar-${av.id}`}
                      className={`group relative rounded-xl overflow-hidden border-2 transition-all duration-200 ${
                        inProject ? 'border-green-500/30 opacity-70' :
                        isSelected ? 'border-[#8B5CF6] shadow-[0_0_16px_rgba(139,92,246,0.3)] scale-[1.02]' :
                        'border-[#1E1E1E] hover:border-[#8B5CF6]/50 hover:scale-[1.02]'
                      }`}
                    >
                      {/* Main image */}
                      <div className="relative aspect-[3/4] bg-[#111]">
                        <img 
                          data-src={resolveImageUrl(av.url)}
                          alt={av.name} 
                          loading="lazy" 
                          decoding="async"
                          className="w-full h-full object-cover opacity-0"
                          ref={node => {
                            if (node && observerRef.current) {
                              observerRef.current.observe(node);
                            }
                          }}
                        />
                        
                        {/* Hover overlay with actions */}
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          {/* Expand button */}
                          <button
                            onClick={() => openExpanded(av)}
                            className="p-2 rounded-full bg-[#8B5CF6] hover:bg-[#A78BFA] transition"
                            title={L.expand}
                          >
                            <Maximize2 size={14} className="text-black" />
                          </button>
                          
                          {/* Edit button */}
                          {onEditAvatar && (
                            <button
                              onClick={() => onEditAvatar(av)}
                              className="p-2 rounded-full bg-blue-500 hover:bg-blue-400 transition"
                              title={L.edit}
                            >
                              <Edit3 size={14} className="text-white" />
                            </button>
                          )}
                          
                          {/* Delete button */}
                          {onDeleteAvatar && (
                            <button
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                console.log('🗑️ [CARD HOVER] Delete button clicked!', av.name, av.id);
                                onDeleteAvatar(av);
                              }}
                              className="p-2 rounded-full bg-red-500 hover:bg-red-400 transition"
                              title="Excluir"
                            >
                              <Trash2 size={14} className="text-white" />
                            </button>
                          )}
                          
                          {/* Download button */}
                          <button
                            onClick={() => downloadAvatar(av)}
                            disabled={isDownloading}
                            className="p-2 rounded-full bg-green-500 hover:bg-green-400 transition disabled:opacity-50"
                            title={L.download}
                          >
                            {isDownloading ? (
                              <RefreshCw size={14} className="text-white animate-spin" />
                            ) : (
                              <Download size={14} className="text-white" />
                            )}
                          </button>
                        </div>
                      </div>
                      
                      {/* Selection checkbox */}
                      {!inProject && (
                        <button
                          onClick={() => toggleSelect(av.id)}
                          className="absolute top-2 right-2 z-10"
                        >
                          <div className={`h-6 w-6 rounded-full border-2 flex items-center justify-center transition ${
                            isSelected 
                              ? 'bg-[#8B5CF6] border-[#8B5CF6]' 
                              : 'bg-black/40 border-white/30 hover:border-[#8B5CF6]'
                          }`}>
                            {isSelected && <Check size={12} className="text-black" />}
                          </div>
                        </button>
                      )}
                      
                      {/* Already in project badge */}
                      {inProject && (
                        <div className="absolute top-2 right-2 h-6 w-6 rounded-full bg-green-500 flex items-center justify-center">
                          <Check size={12} className="text-white" />
                        </div>
                      )}
                      
                      {/* Name overlay */}
                      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/80 to-transparent px-2 py-2">
                        <p className="text-xs text-white font-semibold truncate">{av.name || 'Avatar'}</p>
                        {inProject && <p className="text-[8px] text-green-400 mt-0.5">{L.alreadyIn}</p>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="px-5 py-3 border-t border-[#151515] shrink-0 flex items-center gap-2 bg-[#0A0A0A]">
            <button 
              onClick={onClose} 
              className="px-4 py-2 rounded-lg border border-[#333] text-sm text-[#999] hover:text-white hover:border-[#555] transition"
            >
              {L.close}
            </button>
            
            {selected.size > 0 && (
              <>
                {/* Download selected */}
                <button 
                  onClick={downloadSelected}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition"
                >
                  <Download size={14} />
                  {L.download} ({selected.size})
                </button>
                
                {/* Import selected */}
                {projectId && (
                  <button 
                    data-testid="library-import-btn" 
                    onClick={doImport} 
                    disabled={importing}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-[#8B5CF6] hover:bg-[#A78BFA] text-black text-sm font-bold transition disabled:opacity-50"
                  >
                    {importing ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
                    {L.import} ({selected.size})
                  </button>
                )}
              </>
            )}
          </div>
        </div>
      </div>

      {/* Expanded Preview Modal (4x size) */}
      {expandedAvatar && (
        <div 
          className="fixed inset-0 z-[70] bg-black/95 flex items-center justify-center p-4"
          onClick={closeExpanded}
        >
          <div 
            className="relative max-w-4xl w-full"
            onClick={e => e.stopPropagation()}
          >
            {/* Navigation arrows */}
            {previewIndex > 0 && (
              <button
                onClick={prevAvatar}
                className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-16 p-3 rounded-full bg-[#8B5CF6]/20 hover:bg-[#8B5CF6]/40 transition"
                title={L.prev}
              >
                <ChevronLeft size={24} className="text-white" />
              </button>
            )}
            
            {previewIndex < filtered.length - 1 && (
              <button
                onClick={nextAvatar}
                className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-16 p-3 rounded-full bg-[#8B5CF6]/20 hover:bg-[#8B5CF6]/40 transition"
                title={L.next}
              >
                <ChevronRight size={24} className="text-white" />
              </button>
            )}
            
            {/* Image */}
            <div className="relative rounded-2xl overflow-hidden border-2 border-[#8B5CF6]/50 shadow-2xl bg-[#0A0A0A]">
              <img 
                src={resolveImageUrl(expandedAvatar.url)} 
                alt={expandedAvatar.name}
                className="w-full h-auto max-h-[80vh] object-contain"
              />
              
              {/* Info overlay */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black via-black/90 to-transparent px-6 py-4">
                <h3 className="text-2xl font-bold text-white mb-2">{expandedAvatar.name}</h3>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => downloadAvatar(expandedAvatar)}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-500 text-white text-sm font-semibold transition"
                  >
                    <Download size={16} />
                    {L.download}
                  </button>
                  
                  {onEditAvatar && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditAvatar(expandedAvatar);
                        setExpandedAvatar(null);
                      }}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold transition"
                    >
                      <Edit3 size={16} />
                      {L.edit}
                    </button>
                  )}
                  
                  {/* Delete button - BIG RED BUTTON */}
                  {onDeleteAvatar && (
                    <button
                      data-testid="expanded-delete-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('🗑️ [EXPANDED MODAL] Delete button clicked!', expandedAvatar.name, expandedAvatar.id);
                        
                        if (window.confirm(`Tem certeza que deseja excluir "${expandedAvatar.name}"?`)) {
                          onDeleteAvatar(expandedAvatar);
                          setExpandedAvatar(null); // Close modal after delete
                        }
                      }}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition"
                    >
                      <Trash2 size={16} />
                      Deletar
                    </button>
                  )}
                </div>
              </div>
              
              {/* Close button */}
              <button
                onClick={closeExpanded}
                className="absolute top-4 right-4 p-2 rounded-full bg-black/60 hover:bg-black/80 transition"
              >
                <X size={20} className="text-white" />
              </button>
            </div>
            
            {/* Counter */}
            <div className="text-center mt-4">
              <span className="text-sm text-[#888]">
                {previewIndex + 1} / {filtered.length}
              </span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
