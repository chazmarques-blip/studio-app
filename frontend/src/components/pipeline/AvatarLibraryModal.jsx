import { useState, useEffect, useMemo } from 'react';
import { X, Search, Check, Download, Plus, BookOpen, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * AvatarLibraryModal — Browse global avatar library and import into the current project.
 * Props:
 *   open: boolean
 *   onClose: () => void
 *   projectId: string
 *   projectAvatarIds: Set<string> — IDs already in the project
 *   onImported: (importedAvatars[]) => void — callback after import
 *   lang: 'pt' | 'en' | 'es'
 */
export function AvatarLibraryModal({ open, onClose, projectId, projectAvatarIds = new Set(), onImported, lang = 'pt' }) {
  const [library, setLibrary] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(new Set());
  const [importing, setImporting] = useState(false);

  const labels = {
    pt: { title: 'Biblioteca de Personagens', search: 'Buscar por nome...', import: 'Importar Selecionados', empty: 'Nenhum personagem na biblioteca', alreadyIn: 'Ja no projeto', selectAll: 'Selecionar Todos', noResults: 'Nenhum resultado', close: 'Fechar' },
    en: { title: 'Character Library', search: 'Search by name...', import: 'Import Selected', empty: 'No characters in library', alreadyIn: 'Already in project', selectAll: 'Select All', noResults: 'No results', close: 'Close' },
    es: { title: 'Biblioteca de Personajes', search: 'Buscar por nombre...', import: 'Importar Seleccionados', empty: 'Sin personajes en la biblioteca', alreadyIn: 'Ya en el proyecto', selectAll: 'Seleccionar Todos', noResults: 'Sin resultados', close: 'Cerrar' },
  };
  const L = labels[lang] || labels.en;

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setSelected(new Set());
    setSearch('');
    axios.get(`${API}/data/avatars`).then(res => {
      setLibrary(res.data || []);
    }).catch(() => {
      // Fallback to localStorage
      try { setLibrary(JSON.parse(localStorage.getItem('agentzz_avatars') || '[]')); } catch { setLibrary([]); }
    }).finally(() => setLoading(false));
  }, [open]);

  const filtered = useMemo(() => {
    if (!search.trim()) return library;
    const q = search.toLowerCase();
    return library.filter(a => (a.name || '').toLowerCase().includes(q));
  }, [library, search]);

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const selectAllFiltered = () => {
    const availableIds = filtered.filter(a => !projectAvatarIds.has(a.id)).map(a => a.id);
    setSelected(new Set(availableIds));
  };

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
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    } finally {
      setImporting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4" onClick={onClose}>
      <div data-testid="avatar-library-modal" className="w-full max-w-lg rounded-2xl border border-[#C9A84C]/20 bg-[#0D0D0D] overflow-hidden max-h-[85vh] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-4 py-3 border-b border-[#151515] flex items-center gap-2 shrink-0">
          <BookOpen size={14} className="text-[#C9A84C]" />
          <h3 className="text-sm font-bold text-white flex-1">{L.title}</h3>
          <span className="text-[9px] text-[#888]">{library.length} total</span>
          <button onClick={onClose} className="p-1 rounded hover:bg-[#1A1A1A]"><X size={16} className="text-[#999]" /></button>
        </div>

        {/* Search */}
        <div className="px-4 py-2 border-b border-[#111] shrink-0">
          <div className="relative">
            <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#666]" />
            <input data-testid="library-search" value={search} onChange={e => setSearch(e.target.value)}
              placeholder={L.search}
              className="w-full pl-8 pr-3 py-2 rounded-lg bg-[#111] border border-[#1E1E1E] text-xs text-white placeholder-[#555] outline-none focus:border-[#C9A84C]/30" />
          </div>
          {filtered.length > 0 && (
            <button onClick={selectAllFiltered} data-testid="library-select-all"
              className="mt-1.5 text-[9px] text-[#C9A84C] hover:underline">
              {L.selectAll} ({filtered.filter(a => !projectAvatarIds.has(a.id)).length})
            </button>
          )}
        </div>

        {/* Grid */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw size={18} className="animate-spin text-[#C9A84C]" />
            </div>
          ) : filtered.length === 0 ? (
            <p className="text-xs text-[#888] text-center py-12">{library.length === 0 ? L.empty : L.noResults}</p>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-2.5">
              {filtered.map(av => {
                const inProject = projectAvatarIds.has(av.id);
                const isSelected = selected.has(av.id);
                return (
                  <button key={av.id} data-testid={`library-avatar-${av.id}`}
                    onClick={() => !inProject && toggleSelect(av.id)}
                    disabled={inProject}
                    className={`relative rounded-xl overflow-hidden border-2 transition text-left ${
                      inProject ? 'border-green-500/30 opacity-60 cursor-default' :
                      isSelected ? 'border-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.2)]' :
                      'border-[#1E1E1E] hover:border-[#333] cursor-pointer'
                    }`}>
                    <img src={resolveImageUrl(av.url)} alt={av.name} loading="lazy" decoding="async"
                      className="w-full aspect-[3/4] object-cover" />
                    {/* Selection check */}
                    {isSelected && (
                      <div className="absolute top-1 right-1 h-5 w-5 rounded-full bg-[#C9A84C] flex items-center justify-center">
                        <Check size={10} className="text-black" />
                      </div>
                    )}
                    {/* Already in project badge */}
                    {inProject && (
                      <div className="absolute top-1 right-1 h-5 w-5 rounded-full bg-green-500/80 flex items-center justify-center">
                        <Check size={10} className="text-white" />
                      </div>
                    )}
                    {/* Name overlay */}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-1.5 py-1">
                      <p className="text-[9px] text-white font-medium truncate">{av.name || 'Avatar'}</p>
                      {inProject && <p className="text-[7px] text-green-400">{L.alreadyIn}</p>}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {selected.size > 0 && (
          <div className="px-4 py-3 border-t border-[#151515] shrink-0 flex items-center gap-2">
            <button onClick={onClose} className="px-3 py-2 rounded-lg border border-[#333] text-xs text-[#999] hover:text-white transition">
              {L.close}
            </button>
            <button data-testid="library-import-btn" onClick={doImport} disabled={importing}
              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-[#C9A84C] text-black text-xs font-bold hover:bg-[#D4B85A] transition disabled:opacity-50">
              {importing ? <RefreshCw size={12} className="animate-spin" /> : <Download size={12} />}
              {L.import} ({selected.size})
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
