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
  
  // Download preview modal
  const [downloadPreview, setDownloadPreview] = useState(null);
  
  // Folders system
  const [folders, setFolders] = useState([]);
  const [currentFolder, setCurrentFolder] = useState(null); // null = all avatars
  const [folderModalOpen, setFolderModalOpen] = useState(false);
  const [editingFolder, setEditingFolder] = useState(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFolderColor, setNewFolderColor] = useState('#8B5CF6');
  const [newFolderParent, setNewFolderParent] = useState(null);
  const [moveToFolderMenuOpen, setMoveToFolderMenuOpen] = useState(false);
  
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
    const CACHE_VERSION = '1.0'; // Increment to invalidate cache

    // IMPROVED: Load cache (no expiration - only invalidate on edit/create/delete)
    try {
      const cached = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
      if (cached.data?.length && cached.version === CACHE_VERSION) {
        console.log('✅ [Gallery] Cache hit:', cached.data.length, 'avatars');
        setLibrary(cached.data);
        
        // Preload first 20 images
        cached.data.slice(0, 20).forEach(av => {
          if (!imageCache.current.has(av.id)) {
            const img = new Image();
            img.src = resolveImageUrl(av.url);
            imageCache.current.set(av.id, img);
          }
        });
        
        // Don't fetch - cache is permanent until invalidated
        return;
      }
    } catch { /* ignore */ }

    // Only fetch if no cache
    console.log('⏳ [Gallery] Cache miss - fetching from API...');
    setLoading(true);
    axios.get(`${API}/data/avatars`).then(res => {
      const fresh = res.data || [];
      console.log('✅ [Gallery] Loaded', fresh.length, 'from API');
      setLibrary(fresh);
      localStorage.setItem(CACHE_KEY, JSON.stringify({ 
        data: fresh, 
        ts: Date.now(),
        version: CACHE_VERSION 
      }));
    }).catch(() => {}).finally(() => setLoading(false));
  }, [open, avatarsCache, avatarsCacheLoaded]); // eslint-disable-line react-hooks/exhaustive-deps

  // Load folders
  useEffect(() => {
    if (!open) return;
    
    axios.get(`${API}/folders`)
      .then(({ data }) => {
        setFolders(data.folders || []);
      })
      .catch(err => console.error('Error loading folders:', err));
  }, [open]);

  // Folder management functions
  const createFolder = async () => {
    if (!newFolderName.trim()) {
      toast.error('Nome da pasta é obrigatório');
      return;
    }
    
    try {
      const { data } = await axios.post(`${API}/folders`, {
        name: newFolderName.trim(),
        parent_id: newFolderParent,
        color: newFolderColor
      });
      
      setFolders(prev => [...prev, data]);
      setFolderModalOpen(false);
      setNewFolderName('');
      setNewFolderColor('#8B5CF6');
      setNewFolderParent(null);
      toast.success(`Pasta "${data.name}" criada!`);
    } catch (err) {
      toast.error('Erro ao criar pasta');
    }
  };

  const deleteFolder = async (folderId) => {
    if (!window.confirm('Deletar esta pasta? Os personagens não serão deletados.')) return;
    
    try {
      await axios.delete(`${API}/folders/${folderId}`);
      setFolders(prev => prev.filter(f => f.id !== folderId));
      if (currentFolder === folderId) setCurrentFolder(null);
      toast.success('Pasta deletada');
    } catch (err) {
      toast.error('Erro ao deletar pasta');
    }
  };

  const moveAvatarsToFolder = async (folderId) => {
    if (selected.size === 0) return;
    
    try {
      await axios.post(`${API}/folders/assign-avatars`, {
        folder_id: folderId,
        avatar_ids: Array.from(selected)
      });
      
      // Update folder's avatar_ids locally
      setFolders(prev => prev.map(f => {
        if (f.id === folderId) {
          const newIds = new Set([...f.avatar_ids || [], ...Array.from(selected)]);
          return { ...f, avatar_ids: Array.from(newIds) };
        }
        return f;
      }));
      
      const folder = folders.find(f => f.id === folderId);
      toast.success(`${selected.size} personagens movidos para "${folder?.name}"`);
      setSelected(new Set());
      setMoveToFolderMenuOpen(false);
    } catch (err) {
      toast.error('Erro ao mover personagens');
    }
  };

  const downloadSelected = async () => {
    if (selected.size === 0) return;
    
    const toDownload = library.filter(a => selected.has(a.id));
    toast.info(`Baixando ${toDownload.length} personagens...`);
    
    for (const av of toDownload) {
      const filename = `${(av.name || 'character').replace(/[^a-z0-9]/gi, '_')}.png`;
      const link = document.createElement('a');
      link.href = `${API}/download-image?url=${encodeURIComponent(resolveImageUrl(av.url))}&filename=${encodeURIComponent(filename)}`;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      await new Promise(resolve => setTimeout(resolve, 500)); // Delay between downloads
    }
    
    toast.success(`${toDownload.length} personagens baixados!`);
    setSelected(new Set());
  };

  const deleteSelected = async () => {
    if (selected.size === 0) return;
    if (!window.confirm(`Deletar ${selected.size} personagens? Esta ação não pode ser desfeita.`)) return;
    
    const toDelete = Array.from(selected);
    let deleted = 0;
    
    for (const avatarId of toDelete) {
      try {
        await axios.delete(`${API}/data/avatars/${avatarId}`);
        deleted++;
      } catch (err) {
        console.error('Error deleting avatar:', avatarId, err);
      }
    }
    
    setLibrary(prev => prev.filter(a => !toDelete.includes(a.id)));
    setSelected(new Set());
    toast.success(`${deleted} personagens deletados`);
  };

  // Filtered + sorted + memoized
  const filtered = useMemo(() => {
    let result = [...library];
    
    // CRITICAL FIX: Filter out avatars with empty/missing URLs (prevents black cards)
    result = result.filter(a => {
      const url = a.url || '';
      return url.trim() !== '';
    });
    
    // 0. Folder filter (if a folder is selected)
    if (currentFolder) {
      const folder = folders.find(f => f.id === currentFolder);
      if (folder && folder.avatar_ids) {
        result = result.filter(a => folder.avatar_ids.includes(a.id));
      } else {
        result = []; // Folder not found or empty
      }
    }
    
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
  }, [library, search, styleFilter, has360Filter, hasVoiceFilter, sortBy, currentFolder, folders]);

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
    console.log('🎯 [DOWNLOAD] Função chamada para:', avatar.name, avatar.id);
    setDownloading(prev => new Set(prev).add(avatar.id));
    
    try {
      const imageUrl = resolveImageUrl(avatar.url);
      const filename = `${(avatar.name || 'character').replace(/[^a-z0-9]/gi, '_')}.png`;
      
      console.log('📥 [DOWNLOAD] Método 1: Tentando download via fetch + blob');
      console.log('📥 [DOWNLOAD] URL:', imageUrl);
      
      // Method 1: Try fetch + blob (works for CORS-enabled resources)
      try {
        const response = await fetch(imageUrl, {
          mode: 'cors',
          credentials: 'omit'
        });
        
        console.log('📡 [DOWNLOAD] Response status:', response.status, response.statusText);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const blob = await response.blob();
        console.log('✅ [DOWNLOAD] Blob criado:', blob.size, 'bytes, tipo:', blob.type);
        
        // Create download link
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        
        // Force click in a way that bypasses popup blockers
        document.body.appendChild(a);
        console.log('🔗 [DOWNLOAD] Iniciando download (método 1):', filename);
        
        // Try multiple click methods
        a.click();
        
        // Fallback: dispatch click event
        const clickEvent = new MouseEvent('click', {
          view: window,
          bubbles: true,
          cancelable: true
        });
        a.dispatchEvent(clickEvent);
        
        // Cleanup after delay
        setTimeout(() => {
          document.body.removeChild(a);
          window.URL.revokeObjectURL(blobUrl);
          console.log('🧹 [DOWNLOAD] Cleanup concluído (método 1)');
        }, 500);
        
        toast.success(`✅ ${avatar.name} baixado!`);
        
      } catch (fetchError) {
        console.warn('⚠️ [DOWNLOAD] Método 1 falhou, tentando método 2 (download direto)');
        console.error('⚠️ [DOWNLOAD] Erro método 1:', fetchError);
        
        // Method 2: Direct download link (fallback for non-CORS resources)
        const a = document.createElement('a');
        a.href = imageUrl;
        a.download = filename;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        
        document.body.appendChild(a);
        console.log('🔗 [DOWNLOAD] Iniciando download (método 2 - direto):', filename);
        a.click();
        
        setTimeout(() => {
          document.body.removeChild(a);
          console.log('🧹 [DOWNLOAD] Cleanup concluído (método 2)');
        }, 500);
        
        toast.success(`✅ ${avatar.name} - download iniciado!`);
      }
      
    } catch (e) {
      console.error('❌ [DOWNLOAD] Erro fatal ao baixar:', e);
      console.error('❌ [DOWNLOAD] Stack:', e.stack);
      toast.error(`Erro ao baixar ${avatar.name}. Tente abrir em nova aba.`);
    } finally {
      console.log('🏁 [DOWNLOAD] Finally block - removendo do estado downloading');
      setDownloading(prev => {
        const next = new Set(prev);
        next.delete(avatar.id);
        return next;
      });
    }
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
      <div className="fixed inset-0 z-[10000] bg-black/80 flex items-center justify-center p-4">
        <div 
          data-testid="avatar-library-modal" 
          className="w-full max-w-5xl rounded-2xl border border-[#8B5CF6]/20 bg-[#0D0D0D] overflow-hidden max-h-[90vh] flex flex-col shadow-2xl"
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
            <button 
              onClick={() => {
                setEditingFolder(null);
                setNewFolderName('');
                setNewFolderColor('#8B5CF6');
                setNewFolderParent(null);
                setFolderModalOpen(true);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-[#8B5CF6]/20 to-[#7C3AED]/20 border border-[#8B5CF6]/40 text-xs font-semibold text-[#A78BFA] hover:from-[#8B5CF6]/30 hover:to-[#7C3AED]/30 transition-all hover:scale-105"
              title="Nova Pasta"
            >
              <Plus size={14} />
              <span>Nova Pasta</span>
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[#1A1A1A] transition">
              <X size={18} className="text-[#999]" />
            </button>
          </div>

          {/* Search & Actions */}
          <div className="px-5 py-3 border-b border-[#111] shrink-0 space-y-3">
            {/* Breadcrumb & Folder Navigation */}
            {currentFolder && (
              <div className="flex items-center gap-2 text-xs">
                <button
                  onClick={() => setCurrentFolder(null)}
                  className="text-[#8B5CF6] hover:text-[#A78BFA] transition"
                >
                  Todas as Pastas
                </button>
                <ChevronRight size={12} className="text-[#666]" />
                <span className="text-white font-semibold">
                  {folders.find(f => f.id === currentFolder)?.name || 'Pasta'}
                </span>
              </div>
            )}
            
            {/* Action Bar - Shows when avatars are selected */}
            {selected.size > 0 && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-gradient-to-r from-[#8B5CF6]/10 to-[#7C3AED]/10 border border-[#8B5CF6]/30">
                <span className="text-xs font-semibold text-white">{selected.size} selecionado(s)</span>
                <div className="flex-1" />
                <button
                  onClick={downloadSelected}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-green-500/20 border border-green-500/40 text-xs font-semibold text-green-400 hover:bg-green-500/30 transition"
                >
                  <Download size={12} />
                  Baixar Todos
                </button>
                <div className="relative">
                  <button
                    onClick={() => setMoveToFolderMenuOpen(!moveToFolderMenuOpen)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/40 text-xs font-semibold text-blue-400 hover:bg-blue-500/30 transition"
                  >
                    <Plus size={12} />
                    Mover para Pasta
                  </button>
                  {moveToFolderMenuOpen && (
                    <div className="absolute top-full mt-1 right-0 bg-[#1A1A1A] border border-[#333] rounded-lg shadow-xl z-50 min-w-[200px] max-h-[300px] overflow-y-auto">
                      {folders.length === 0 ? (
                        <div className="px-4 py-3 text-xs text-[#666]">Nenhuma pasta criada</div>
                      ) : (
                        folders.map(folder => (
                          <button
                            key={folder.id}
                            onClick={() => moveAvatarsToFolder(folder.id)}
                            className="w-full px-4 py-2 text-left text-xs text-white hover:bg-[#2A2A2A] transition flex items-center gap-2"
                          >
                            <div 
                              className="w-3 h-3 rounded-full" 
                              style={{ backgroundColor: folder.color || '#8B5CF6' }}
                            />
                            {folder.name}
                          </button>
                        ))
                      )}
                      <button
                        onClick={() => {
                          setMoveToFolderMenuOpen(false);
                          setFolderModalOpen(true);
                        }}
                        className="w-full px-4 py-2 text-left text-xs text-[#8B5CF6] hover:bg-[#2A2A2A] transition border-t border-[#333]"
                      >
                        + Criar Nova Pasta
                      </button>
                    </div>
                  )}
                </div>
                <button
                  onClick={deleteSelected}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/20 border border-red-500/40 text-xs font-semibold text-red-400 hover:bg-red-500/30 transition"
                >
                  <Trash2 size={12} />
                  Deletar
                </button>
              </div>
            )}
            
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

          {/* Main Content Area with Sidebar */}
          <div className="flex-1 flex overflow-hidden">
            {/* Folders Sidebar */}
            <div className="w-56 border-r border-[#151515] bg-[#0A0A0A] overflow-y-auto p-4 space-y-2">
              <div className="text-xs font-bold text-[#666] uppercase mb-2">Pastas</div>
              
              {/* All Avatars (default view) */}
              <button
                onClick={() => setCurrentFolder(null)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs transition flex items-center gap-2 ${
                  currentFolder === null 
                    ? 'bg-[#8B5CF6]/20 text-[#8B5CF6] font-semibold border border-[#8B5CF6]/40' 
                    : 'text-[#999] hover:bg-[#1A1A1A] hover:text-white'
                }`}
              >
                <Users size={14} />
                <span className="flex-1">Todos ({library.length})</span>
              </button>
              
              {/* Folder List */}
              {folders.map(folder => {
                const count = folder.avatar_ids?.length || 0;
                const isActive = currentFolder === folder.id;
                
                return (
                  <div key={folder.id} className="relative group">
                    <button
                      onClick={() => setCurrentFolder(folder.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs transition flex items-center gap-2 ${
                        isActive 
                          ? 'bg-[#8B5CF6]/20 text-white font-semibold border border-[#8B5CF6]/40' 
                          : 'text-[#999] hover:bg-[#1A1A1A] hover:text-white'
                      }`}
                    >
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: folder.color || '#8B5CF6' }}
                      />
                      <span className="flex-1 truncate">{folder.name}</span>
                      <span className="text-[10px] text-[#666]">({count})</span>
                    </button>
                    
                    {/* Delete folder button (on hover) */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteFolder(folder.id);
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition p-1 rounded hover:bg-red-500/20"
                      title="Deletar pasta"
                    >
                      <Trash2 size={10} className="text-red-400" />
                    </button>
                  </div>
                );
              })}
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
                        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2 pointer-events-none">
                          {/* Expand button */}
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              openExpanded(av);
                            }}
                            className="p-2 rounded-full bg-[#8B5CF6] hover:bg-[#A78BFA] transition pointer-events-auto"
                            title={L.expand}
                          >
                            <Maximize2 size={14} className="text-black" />
                          </button>
                          
                          {/* Edit button */}
                          {onEditAvatar && (
                            <button
                              onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                console.log('✏️ [HOVER] Edit clicked!', av.name);
                                onEditAvatar(av);
                              }}
                              className="p-2 rounded-full bg-blue-500 hover:bg-blue-400 transition pointer-events-auto"
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
                              className="p-2 rounded-full bg-red-500 hover:bg-red-400 transition pointer-events-auto"
                              title="Excluir"
                            >
                              <Trash2 size={14} className="text-white" />
                            </button>
                          )}
                          
                          {/* Download button - Opens compact download modal */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              e.preventDefault();
                              console.log('📥 [DOWNLOAD] Abrindo modal de download');
                              setDownloadPreview(av);
                            }}
                            className="p-2 rounded-full bg-green-500 hover:bg-green-400 transition pointer-events-auto flex items-center justify-center"
                            title="Baixar personagem"
                          >
                            <Download size={14} className="text-white" />
                          </button>
                        </div>
                      </div>
                      
                      {/* Selection checkbox */}
                      {!inProject && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            e.preventDefault();
                            console.log('🔘 [CHECKBOX] Clicado!', av.id, av.name);
                            toggleSelect(av.id);
                          }}
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
                
                {/* Delete selected - BIG RED BUTTON */}
                {onDeleteAvatar && (
                  <button 
                    data-testid="library-delete-selected-btn"
                    type="button"
                    onClick={async (e) => {
                      e.stopPropagation();
                      const count = selected.size;
                      const selectedAvatars = library.filter(a => selected.has(a.id));
                      
                      console.log('🗑️ [BATCH DELETE] Iniciando deleção de', count, 'personagens...');
                      
                      let successCount = 0;
                      let errorCount = 0;
                      
                      for (const avatar of selectedAvatars) {
                        try {
                          console.log('🗑️ Deletando:', avatar.name);
                          await onDeleteAvatar(avatar, true); // skipConfirm = true
                          successCount++;
                        } catch (err) {
                          console.error('❌ Erro ao deletar', avatar.name, err);
                          errorCount++;
                        }
                      }
                      
                      // Clear selection
                      setSelected(new Set());
                      
                      // Show summary toast
                      if (errorCount === 0) {
                        toast.success(`✅ ${successCount} personagem(ns) excluído(s) com sucesso!`);
                      } else {
                        toast.warning(`⚠️ ${successCount} excluído(s), ${errorCount} com erro`);
                      }
                      
                      console.log('✅ [BATCH DELETE] Completo:', successCount, 'sucesso,', errorCount, 'erros');
                    }}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-500 text-white text-sm font-semibold transition"
                  >
                    <Trash2 size={14} />
                    Deletar ({selected.size})
                  </button>
                )}
                
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
          className="fixed inset-0 z-[10002] bg-black/95 flex items-center justify-center p-4"
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
                        console.log('✏️ [EXPANDED] Edit button clicked!', expandedAvatar.name);
                        const avatarToEdit = expandedAvatar; // Save before closing
                        setExpandedAvatar(null); // Close expanded modal first
                        onEditAvatar(avatarToEdit); // Then open edit modal
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
                        onDeleteAvatar(expandedAvatar);
                        setExpandedAvatar(null); // Close modal after delete
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
      
      {/* Folder Create/Edit Modal */}
      {folderModalOpen && (
        <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4" onClick={() => setFolderModalOpen(false)}>
          <div className="bg-[#0D0D0D] rounded-2xl border border-[#8B5CF6]/20 overflow-hidden max-w-md w-full" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] px-4 py-3 flex items-center justify-between">
              <h3 className="text-white font-bold text-sm flex items-center gap-2">
                <Plus size={16} />
                {editingFolder ? 'Editar Pasta' : 'Nova Pasta'}
              </h3>
              <button onClick={() => setFolderModalOpen(false)} className="text-white/80 hover:text-white transition">
                <X size={18} />
              </button>
            </div>
            
            {/* Form */}
            <div className="p-4 space-y-4">
              {/* Folder Name */}
              <div>
                <label className="text-xs text-[#999] mb-1 block">Nome da Pasta</label>
                <input
                  type="text"
                  value={newFolderName}
                  onChange={e => setNewFolderName(e.target.value)}
                  placeholder="Ex: Projeto A"
                  className="w-full px-3 py-2 rounded-lg bg-[#1A1A1A] border border-[#333] text-white text-sm outline-none focus:border-[#8B5CF6] transition"
                  autoFocus
                />
              </div>
              
              {/* Folder Color */}
              <div>
                <label className="text-xs text-[#999] mb-1 block">Cor</label>
                <div className="flex gap-2">
                  {['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#EC4899'].map(color => (
                    <button
                      key={color}
                      onClick={() => setNewFolderColor(color)}
                      className={`w-10 h-10 rounded-lg transition ${
                        newFolderColor === color ? 'ring-2 ring-white ring-offset-2 ring-offset-[#0D0D0D]' : ''
                      }`}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
              </div>
              
              {/* Parent Folder (optional) */}
              <div>
                <label className="text-xs text-[#999] mb-1 block">Pasta Pai (opcional)</label>
                <select
                  value={newFolderParent || ''}
                  onChange={e => setNewFolderParent(e.target.value || null)}
                  className="w-full px-3 py-2 rounded-lg bg-[#1A1A1A] border border-[#333] text-white text-sm outline-none focus:border-[#8B5CF6] transition"
                >
                  <option value="">Nenhuma (raiz)</option>
                  {folders.map(f => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>
            </div>
            
            {/* Actions */}
            <div className="px-4 pb-4 flex gap-2">
              <button
                onClick={() => setFolderModalOpen(false)}
                className="flex-1 py-2.5 rounded-lg border border-[#333] text-[#999] hover:text-white hover:border-[#666] transition text-sm font-medium"
              >
                Cancelar
              </button>
              <button
                onClick={createFolder}
                className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] text-white font-bold hover:from-[#7C3AED] hover:to-[#6D28D9] transition text-sm flex items-center justify-center gap-2"
              >
                <Plus size={16} />
                {editingFolder ? 'Salvar' : 'Criar Pasta'}
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Download Preview Modal - Compact popup over gallery */}
      {downloadPreview && (
        <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4" onClick={() => setDownloadPreview(null)}>
          <div className="bg-[#0D0D0D] rounded-2xl border border-[#8B5CF6]/20 overflow-hidden max-w-md w-full" onClick={e => e.stopPropagation()}>
            {/* Header */}
            <div className="bg-gradient-to-r from-[#8B5CF6] to-[#7C3AED] px-4 py-3 flex items-center justify-between">
              <h3 className="text-white font-bold text-sm flex items-center gap-2">
                <Download size={16} />
                Baixar Personagem
              </h3>
              <button onClick={() => setDownloadPreview(null)} className="text-white/80 hover:text-white transition">
                <X size={18} />
              </button>
            </div>
            
            {/* Image Preview */}
            <div className="p-4">
              <img 
                src={resolveImageUrl(downloadPreview.url)} 
                alt={downloadPreview.name}
                className="w-full aspect-[3/4] object-cover rounded-lg border border-[#333]"
              />
              <p className="text-white text-center mt-2 font-semibold">{downloadPreview.name}</p>
            </div>
            
            {/* Download Button */}
            <div className="px-4 pb-4 flex gap-2">
              <button
                onClick={() => setDownloadPreview(null)}
                className="flex-1 py-2.5 rounded-lg border border-[#333] text-[#999] hover:text-white hover:border-[#666] transition text-sm font-medium"
              >
                Cancelar
              </button>
              <a
                href={`${API}/download-image?url=${encodeURIComponent(resolveImageUrl(downloadPreview.url))}&filename=${encodeURIComponent(`${(downloadPreview.name || 'character').replace(/[^a-z0-9]/gi, '_')}.png`)}`}
                onClick={() => {
                  toast.success(`Download iniciado: ${downloadPreview.name}`);
                  setDownloadPreview(null);
                }}
                className="flex-1 py-2.5 rounded-lg bg-gradient-to-r from-green-500 to-green-600 text-white font-bold hover:from-green-600 hover:to-green-700 transition text-sm flex items-center justify-center gap-2"
              >
                <Download size={16} />
                Baixar Agora
              </a>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
