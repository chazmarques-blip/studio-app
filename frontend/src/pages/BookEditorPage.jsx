import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import {
  ArrowLeft, Save, Image as ImageIcon, Type, RefreshCw, Download,
  Loader2, Eye, X, ChevronLeft, ChevronRight, Shield, AlertTriangle,
  Check, Award, Palette, Move, Maximize2, Trash2, Plus, Wand2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FONT_OPTIONS = [
  { value: "'Source Serif Pro', Georgia, serif", label: 'Source Serif' },
  { value: "'EB Garamond', Garamond, serif", label: 'EB Garamond' },
  { value: "'Baskerville', serif", label: 'Baskerville' },
  { value: "'Futura', 'Helvetica Neue', sans-serif", label: 'Futura' },
  { value: "'Playfair Display', serif", label: 'Playfair' },
  { value: "'Merriweather', serif", label: 'Merriweather' },
];

const GRADIENT_PRESETS = [
  { label: 'Nenhum', config: null },
  { label: 'Preto ↑', config: { direction: 'to top',    from: 'rgba(0,0,0,0.85)', to: 'rgba(0,0,0,0)',   opacity: 1 } },
  { label: 'Preto ↓', config: { direction: 'to bottom', from: 'rgba(0,0,0,0.85)', to: 'rgba(0,0,0,0)',   opacity: 1 } },
  { label: 'Branco',  config: { direction: 'to top',    from: 'rgba(255,255,255,0.9)', to: 'rgba(255,255,255,0)', opacity: 1 } },
  { label: 'Azul',    config: { direction: 'to top',    from: 'rgba(15,30,80,0.9)', to: 'rgba(15,30,80,0)', opacity: 1 } },
];

// ═════════════════════════════════════════════════════════
// Spread Canvas — visual editor for one page
// ═════════════════════════════════════════════════════════
function SpreadCanvas({ spread, onUpdate, editing }) {
  const canvasRef = useRef(null);
  const [selectedId, setSelectedId] = useState(null);

  const img = spread.image || {};
  const textOverlays = spread.text_overlays || [];

  return (
    <div
      ref={canvasRef}
      data-testid="spread-canvas"
      className="relative w-full aspect-[3/4] bg-white dark:bg-[#1A1430] rounded-xl shadow-2xl overflow-hidden border border-gray-200 dark:border-[#2A2442]"
      style={{ backgroundColor: spread.background_color || '#FFFFFF' }}
      onClick={() => setSelectedId(null)}
    >
      {/* Image layer */}
      {img.url ? (
        <img
          src={img.url}
          alt=""
          className={`absolute ${selectedId === 'image' ? 'ring-4 ring-violet-500 ring-offset-0' : ''}`}
          style={{
            left: `${img.x_pct ?? 0}%`,
            top: `${img.y_pct ?? 0}%`,
            width: `${img.width_pct ?? 100}%`,
            height: `${img.height_pct ?? 100}%`,
            objectFit: img.fit || 'cover',
            cursor: editing ? 'pointer' : 'default',
          }}
          onClick={(e) => { e.stopPropagation(); if (editing) setSelectedId('image'); }}
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 dark:bg-[#2A2442] text-gray-400 dark:text-[#6B647F]">
          <ImageIcon size={40} />
        </div>
      )}

      {/* Text overlays */}
      {textOverlays.map((t) => {
        const grad = t.gradient;
        const gradBg = grad
          ? `linear-gradient(${grad.direction || 'to top'}, ${grad.from}, ${grad.to})`
          : 'transparent';
        const isSel = selectedId === t.id;
        return (
          <div
            key={t.id}
            data-testid={`text-overlay-${t.id}`}
            className={`absolute flex items-end p-4 ${isSel ? 'ring-4 ring-violet-500 ring-offset-0' : ''}`}
            style={{
              left: `${t.x_pct ?? 10}%`,
              top: `${t.y_pct ?? 65}%`,
              width: `${t.width_pct ?? 80}%`,
              height: `${t.height_pct ?? 25}%`,
              background: gradBg,
              color: t.color || '#FFFFFF',
              fontFamily: t.font_family || "'Source Serif Pro', serif",
              fontSize: `${(t.font_size_pt || 16) * 1.1}px`,
              textAlign: t.alignment || 'left',
              lineHeight: 1.35,
              cursor: editing ? 'pointer' : 'default',
            }}
            onClick={(e) => { e.stopPropagation(); if (editing) setSelectedId(t.id); }}
          >
            <p className="m-0 w-full" style={{ textShadow: t.color === '#FFFFFF' ? '0 1px 3px rgba(0,0,0,0.5)' : 'none' }}>
              {t.content}
            </p>
          </div>
        );
      })}

      {/* Page number badge */}
      <div className="absolute bottom-2 right-3 text-[10px] font-mono text-white/70 bg-black/30 px-1.5 py-0.5 rounded">
        p.{spread.id}
      </div>
    </div>
  );
}

// ═════════════════════════════════════════════════════════
// Right-side property panel
// ═════════════════════════════════════════════════════════
function PropertyPanel({ spread, onUpdate, onRegenerateImage, saving }) {
  const [editedSpread, setEditedSpread] = useState(spread);
  const [regenPrompt, setRegenPrompt] = useState('');
  const [regenLoading, setRegenLoading] = useState(false);
  const [selectedOverlayId, setSelectedOverlayId] = useState(
    spread?.text_overlays?.[0]?.id || null
  );

  useEffect(() => {
    setEditedSpread(spread);
    setSelectedOverlayId(spread?.text_overlays?.[0]?.id || null);
    setRegenPrompt(spread?.image?.regen_prompt || '');
  }, [spread?.id]);

  const updateImage = (patch) => {
    const next = { ...editedSpread, image: { ...editedSpread.image, ...patch } };
    setEditedSpread(next);
    onUpdate(next);
  };

  const updateOverlay = (id, patch) => {
    const next = {
      ...editedSpread,
      text_overlays: (editedSpread.text_overlays || []).map(t =>
        t.id === id ? { ...t, ...patch } : t
      ),
    };
    setEditedSpread(next);
    onUpdate(next);
  };

  const addOverlay = () => {
    const newId = `text_${spread.id}_${Date.now()}`;
    const newOverlay = {
      id: newId, content: 'Novo texto',
      x_pct: 15, y_pct: 40, width_pct: 70, height_pct: 20,
      font_size_pt: 16,
      font_family: "'Source Serif Pro', Georgia, serif",
      color: '#FFFFFF',
      gradient: GRADIENT_PRESETS[1].config,
      alignment: 'center',
      editable: true,
    };
    const next = { ...editedSpread, text_overlays: [...(editedSpread.text_overlays || []), newOverlay] };
    setEditedSpread(next);
    onUpdate(next);
    setSelectedOverlayId(newId);
  };

  const deleteOverlay = (id) => {
    if (!window.confirm('Remover este bloco de texto?')) return;
    const next = {
      ...editedSpread,
      text_overlays: (editedSpread.text_overlays || []).filter(t => t.id !== id),
    };
    setEditedSpread(next);
    onUpdate(next);
    setSelectedOverlayId(null);
  };

  const regenerateImage = async () => {
    setRegenLoading(true);
    try {
      await onRegenerateImage(spread.id, regenPrompt);
    } finally {
      setRegenLoading(false);
    }
  };

  const currentOverlay = (editedSpread.text_overlays || []).find(t => t.id === selectedOverlayId);

  return (
    <aside className="w-80 shrink-0 border-l border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] overflow-y-auto h-full">
      <div className="p-4 space-y-5">
        {/* Image section */}
        <section>
          <h3 className="text-[11px] font-bold uppercase tracking-wider text-gray-700 dark:text-white mb-2 flex items-center gap-1.5">
            <ImageIcon size={12} /> Imagem
          </h3>
          <div className="space-y-2">
            <label className="block">
              <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Encaixe</span>
              <select
                value={editedSpread.image?.fit || 'cover'}
                onChange={(e) => updateImage({ fit: e.target.value })}
                className="mt-0.5 w-full h-8 px-2 rounded bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500"
              >
                <option value="cover">Full-bleed (cover)</option>
                <option value="contain">Contain (margens)</option>
                <option value="fill">Esticar (fill)</option>
              </select>
            </label>

            <div className="grid grid-cols-2 gap-2">
              <label>
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">X %</span>
                <input type="number" value={editedSpread.image?.x_pct ?? 0}
                  onChange={(e) => updateImage({ x_pct: +e.target.value })}
                  className="w-full h-8 px-2 rounded bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500" />
              </label>
              <label>
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Y %</span>
                <input type="number" value={editedSpread.image?.y_pct ?? 0}
                  onChange={(e) => updateImage({ y_pct: +e.target.value })}
                  className="w-full h-8 px-2 rounded bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500" />
              </label>
              <label>
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Largura %</span>
                <input type="number" value={editedSpread.image?.width_pct ?? 100}
                  onChange={(e) => updateImage({ width_pct: +e.target.value })}
                  className="w-full h-8 px-2 rounded bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500" />
              </label>
              <label>
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Altura %</span>
                <input type="number" value={editedSpread.image?.height_pct ?? 100}
                  onChange={(e) => updateImage({ height_pct: +e.target.value })}
                  className="w-full h-8 px-2 rounded bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500" />
              </label>
            </div>

            {/* Regenerate */}
            <div className="pt-2 border-t border-gray-100 dark:border-[#2A2442]">
              <label className="block">
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Prompt para regenerar</span>
                <textarea
                  value={regenPrompt}
                  onChange={(e) => setRegenPrompt(e.target.value)}
                  rows={3}
                  className="mt-0.5 w-full p-2 rounded bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white outline-none focus:border-violet-500 resize-none"
                  placeholder="Descreva a cena..."
                />
              </label>
              <button
                onClick={regenerateImage}
                disabled={regenLoading || !regenPrompt.trim()}
                data-testid="regen-image-btn"
                className="mt-2 w-full h-9 rounded-lg bg-gradient-to-r from-orange-500 to-orange-600 text-white text-[12px] font-semibold inline-flex items-center justify-center gap-1.5 hover:brightness-110 transition disabled:opacity-50"
              >
                {regenLoading ? <Loader2 size={12} className="animate-spin" /> : <Wand2 size={12} />}
                {regenLoading ? 'Regenerando...' : 'Regenerar Imagem'}
              </button>
            </div>
          </div>
        </section>

        {/* Text overlays section */}
        <section>
          <header className="flex items-center justify-between mb-2">
            <h3 className="text-[11px] font-bold uppercase tracking-wider text-gray-700 dark:text-white flex items-center gap-1.5">
              <Type size={12} /> Textos ({(editedSpread.text_overlays || []).length})
            </h3>
            <button
              onClick={addOverlay}
              data-testid="add-overlay-btn"
              className="h-6 w-6 rounded-md bg-violet-100 dark:bg-violet-500/20 text-violet-600 dark:text-violet-300 hover:bg-violet-200 dark:hover:bg-violet-500/30 flex items-center justify-center transition"
            >
              <Plus size={12} />
            </button>
          </header>

          {(editedSpread.text_overlays || []).length === 0 ? (
            <p className="text-[11px] text-gray-500 dark:text-[#A3A3B2]">Nenhum texto nesta página.</p>
          ) : (
            <div className="space-y-1 mb-3">
              {editedSpread.text_overlays.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedOverlayId(t.id)}
                  className={`w-full flex items-center gap-2 px-2 h-8 rounded text-[11px] text-left transition ${
                    selectedOverlayId === t.id
                      ? 'bg-violet-100 dark:bg-violet-500/20 text-violet-700 dark:text-violet-300'
                      : 'bg-gray-50 dark:bg-[#1A1430] text-gray-700 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-[#2A2442]'
                  }`}
                >
                  <Type size={10} />
                  <span className="flex-1 truncate">{t.content?.slice(0, 30) || '(vazio)'}</span>
                </button>
              ))}
            </div>
          )}

          {currentOverlay && (
            <div className="space-y-2 p-3 rounded-lg bg-gray-50 dark:bg-[#1A1430] border border-gray-200 dark:border-[#2A2442]">
              <label className="block">
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Conteúdo</span>
                <textarea
                  value={currentOverlay.content}
                  onChange={(e) => updateOverlay(currentOverlay.id, { content: e.target.value })}
                  data-testid="overlay-content"
                  rows={4}
                  className="mt-0.5 w-full p-2 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500 resize-y"
                />
              </label>

              <div className="grid grid-cols-2 gap-2">
                <label>
                  <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Tamanho (pt)</span>
                  <input type="number" value={currentOverlay.font_size_pt || 16} min={6} max={96}
                    onChange={(e) => updateOverlay(currentOverlay.id, { font_size_pt: +e.target.value })}
                    data-testid="overlay-size"
                    className="w-full h-8 px-2 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500" />
                </label>
                <label>
                  <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Cor</span>
                  <input type="color" value={currentOverlay.color || '#FFFFFF'}
                    onChange={(e) => updateOverlay(currentOverlay.id, { color: e.target.value })}
                    className="w-full h-8 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] cursor-pointer" />
                </label>
              </div>

              <label className="block">
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Fonte</span>
                <select
                  value={currentOverlay.font_family}
                  onChange={(e) => updateOverlay(currentOverlay.id, { font_family: e.target.value })}
                  className="mt-0.5 w-full h-8 px-2 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500"
                >
                  {FONT_OPTIONS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                </select>
              </label>

              <label className="block">
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2]">Alinhamento</span>
                <select
                  value={currentOverlay.alignment || 'left'}
                  onChange={(e) => updateOverlay(currentOverlay.id, { alignment: e.target.value })}
                  className="mt-0.5 w-full h-8 px-2 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[12px] text-gray-900 dark:text-white outline-none focus:border-violet-500"
                >
                  <option value="left">Esquerda</option>
                  <option value="center">Centro</option>
                  <option value="right">Direita</option>
                  <option value="justify">Justificado</option>
                </select>
              </label>

              <div>
                <span className="text-[10px] text-gray-500 dark:text-[#A3A3B2] block">Gradient (overlay)</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {GRADIENT_PRESETS.map((g, i) => (
                    <button
                      key={i}
                      onClick={() => updateOverlay(currentOverlay.id, { gradient: g.config })}
                      className={`h-7 px-2 rounded text-[10px] font-semibold border transition ${
                        JSON.stringify(currentOverlay.gradient) === JSON.stringify(g.config)
                          ? 'border-violet-500 bg-violet-50 dark:bg-violet-500/20 text-violet-700 dark:text-violet-300'
                          : 'border-gray-200 dark:border-[#2A2442] text-gray-700 dark:text-[#A3A3B2] hover:border-violet-300'
                      }`}
                    >
                      {g.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-4 gap-1 pt-2 border-t border-gray-100 dark:border-[#2A2442]">
                <label><span className="text-[9px] text-gray-500 dark:text-[#6B647F]">X</span>
                  <input type="number" value={currentOverlay.x_pct ?? 10}
                    onChange={(e) => updateOverlay(currentOverlay.id, { x_pct: +e.target.value })}
                    className="w-full h-7 px-1 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white outline-none" /></label>
                <label><span className="text-[9px] text-gray-500 dark:text-[#6B647F]">Y</span>
                  <input type="number" value={currentOverlay.y_pct ?? 65}
                    onChange={(e) => updateOverlay(currentOverlay.id, { y_pct: +e.target.value })}
                    className="w-full h-7 px-1 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white outline-none" /></label>
                <label><span className="text-[9px] text-gray-500 dark:text-[#6B647F]">W</span>
                  <input type="number" value={currentOverlay.width_pct ?? 80}
                    onChange={(e) => updateOverlay(currentOverlay.id, { width_pct: +e.target.value })}
                    className="w-full h-7 px-1 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white outline-none" /></label>
                <label><span className="text-[9px] text-gray-500 dark:text-[#6B647F]">H</span>
                  <input type="number" value={currentOverlay.height_pct ?? 25}
                    onChange={(e) => updateOverlay(currentOverlay.id, { height_pct: +e.target.value })}
                    className="w-full h-7 px-1 rounded bg-white dark:bg-[#0A0614] border border-gray-200 dark:border-[#2A2442] text-[11px] text-gray-900 dark:text-white outline-none" /></label>
              </div>

              <button
                onClick={() => deleteOverlay(currentOverlay.id)}
                className="w-full mt-2 h-7 px-2 rounded text-[10px] text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition inline-flex items-center justify-center gap-1"
              >
                <Trash2 size={10} /> Remover bloco
              </button>
            </div>
          )}
        </section>
      </div>
    </aside>
  );
}

// ═════════════════════════════════════════════════════════
// Main editor page
// ═════════════════════════════════════════════════════════
export default function BookEditorPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();

  const [spreads, setSpreads] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [gate, setGate] = useState(null);
  const [exporting, setExporting] = useState(false);

  const saveTimeoutRef = useRef(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sRes, gRes] = await Promise.all([
        axios.get(`${API}/studio/book/projects/${projectId}/editable-spreads`),
        axios.get(`${API}/studio/book/projects/${projectId}/quality-gate`).catch(() => ({ data: null })),
      ]);
      setSpreads(sRes.data.spreads || []);
      setGate(gRes.data);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Erro ao carregar livro');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  const current = spreads[currentIdx];

  // Debounced auto-save
  const updateSpread = (next) => {
    setSpreads(prev => prev.map((s, i) => (i === currentIdx ? next : s)));
    if (saveTimeoutRef.current) clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(async () => {
      setSaving(true);
      try {
        await axios.put(`${API}/studio/book/projects/${projectId}/editable-spreads/${next.id}`, {
          image: next.image,
          text_overlays: next.text_overlays,
          background_color: next.background_color,
        });
      } catch (e) {
        toast.error('Erro ao salvar edições');
      } finally {
        setSaving(false);
      }
    }, 800);
  };

  const regenerateImage = async (spreadId, prompt) => {
    try {
      const { data } = await axios.post(
        `${API}/studio/book/projects/${projectId}/editable-spreads/${spreadId}/regenerate-image`,
        { prompt }
      );
      setSpreads(prev => prev.map(s => s.id === spreadId
        ? { ...s, image: { ...s.image, url: data.image_url, regen_prompt: prompt } }
        : s
      ));
      toast.success('Imagem regenerada');
    } catch (e) {
      toast.error('Erro ao regenerar imagem');
    }
  };

  const exportPDF = async () => {
    setExporting(true);
    try {
      // Backend block if Glen score < 90
      const { data } = await axios.post(`${API}/studio/book/${projectId}/render-pdf`);
      if (data?.pdf_url) {
        window.open(data.pdf_url, '_blank');
        toast.success('PDF gerado!');
      }
    } catch (e) {
      const err = e.response?.data?.detail;
      if (err?.error === 'quality_gate_failed') {
        toast.error(`Quality gate: ${err.message}`);
      } else {
        toast.error(typeof err === 'string' ? err : 'Erro ao gerar PDF');
      }
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-[#FAFAFC] dark:bg-[#0A0614]">
        <Loader2 className="animate-spin text-violet-600" size={32} />
      </div>
    );
  }

  if (spreads.length === 0) {
    return (
      <div className="h-screen flex flex-col items-center justify-center bg-[#FAFAFC] dark:bg-[#0A0614] p-6 text-center">
        <ImageIcon size={48} className="text-gray-300 dark:text-[#2A2442] mb-4" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Nenhuma página para editar</h2>
        <p className="text-sm text-gray-500 dark:text-[#A3A3B2] mt-2 mb-4">
          Este livro ainda não tem ilustrações geradas. Volte ao StudioX Books e gere as ilustrações primeiro.
        </p>
        <Link to={`/studio/book/${projectId}`} className="h-10 px-5 rounded-lg bg-violet-600 text-white text-sm font-semibold inline-flex items-center gap-2">
          <ArrowLeft size={14} /> Voltar ao BookStudio
        </Link>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-[#FAFAFC] dark:bg-[#0A0614]" style={{ fontFamily: "'Outfit', system-ui" }}>
      {/* Top bar */}
      <header className="shrink-0 h-14 border-b border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] flex items-center px-4 gap-3">
        <button
          onClick={() => navigate(`/studio/book/${projectId}`)}
          data-testid="book-editor-back"
          className="h-9 w-9 rounded-lg flex items-center justify-center text-gray-500 dark:text-[#A3A3B2] hover:bg-gray-100 dark:hover:bg-white/5"
        >
          <ArrowLeft size={16} />
        </button>
        <div className="flex-1 min-w-0">
          <h1 className="text-[14px] font-bold text-gray-900 dark:text-white truncate">Editor Visual do Livro</h1>
          <p className="text-[11px] text-gray-500 dark:text-[#A3A3B2]">
            Página {currentIdx + 1} de {spreads.length} · p.{current?.id}
          </p>
        </div>

        {/* Gate status */}
        {gate && (
          <div
            className={`inline-flex items-center gap-1.5 px-3 h-8 rounded-full text-[11px] font-semibold ${
              gate.passed
                ? 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300'
                : gate.score == null
                ? 'bg-gray-100 dark:bg-[#1A1430] text-gray-600 dark:text-[#A3A3B2]'
                : 'bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-300'
            }`}
            title={gate.message}
          >
            <Shield size={11} />
            {gate.passed
              ? <>Gate OK · {gate.score}</>
              : gate.score == null
              ? <>Gate não auditado</>
              : <>Gate {gate.score} / {gate.min_required}</>}
          </div>
        )}

        {/* Save indicator */}
        <span className="text-[10px] text-gray-400 dark:text-[#6B647F] w-20 text-right">
          {saving ? <><Loader2 size={10} className="inline animate-spin mr-1" />Salvando</> : <>Auto-salvo</>}
        </span>

        <button
          onClick={exportPDF}
          disabled={exporting}
          data-testid="export-pdf-btn"
          className="h-9 px-4 rounded-lg bg-gradient-to-r from-violet-600 to-orange-500 text-white text-[12px] font-semibold inline-flex items-center gap-1.5 hover:brightness-110 transition disabled:opacity-50"
        >
          {exporting ? <Loader2 size={12} className="animate-spin" /> : <Download size={12} />}
          {exporting ? 'Gerando...' : 'Gerar PDF'}
        </button>
      </header>

      {/* Main — thumbs | canvas | properties */}
      <div className="flex-1 flex min-h-0">
        {/* Left thumbnails */}
        <aside className="w-44 shrink-0 border-r border-gray-200 dark:border-[#2A2442] bg-white dark:bg-[#110A1F] overflow-y-auto p-2 space-y-1">
          {spreads.map((sp, i) => (
            <button
              key={sp.id}
              onClick={() => setCurrentIdx(i)}
              data-testid={`thumb-${sp.id}`}
              className={`w-full aspect-[3/4] rounded-md border-2 overflow-hidden transition relative ${
                i === currentIdx
                  ? 'border-violet-500'
                  : 'border-gray-200 dark:border-[#2A2442] hover:border-violet-300'
              }`}
            >
              {sp.image?.url ? (
                <img src={sp.image.url} alt="" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full bg-gray-100 dark:bg-[#1A1430] flex items-center justify-center text-gray-400">
                  <ImageIcon size={16} />
                </div>
              )}
              <span className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-[9px] font-mono text-center py-0.5">
                p.{sp.id}
              </span>
            </button>
          ))}
        </aside>

        {/* Canvas center */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 overflow-y-auto">
          <div className="w-full max-w-[560px]">
            {current && (
              <SpreadCanvas
                spread={current}
                onUpdate={updateSpread}
                editing
              />
            )}
            {/* Nav buttons */}
            <div className="mt-4 flex items-center justify-center gap-2">
              <button
                onClick={() => setCurrentIdx(Math.max(0, currentIdx - 1))}
                disabled={currentIdx === 0}
                className="h-8 w-8 rounded-lg border border-gray-200 dark:border-[#2A2442] text-gray-500 dark:text-[#A3A3B2] hover:border-violet-400 hover:text-violet-600 disabled:opacity-40 flex items-center justify-center transition"
              >
                <ChevronLeft size={14} />
              </button>
              <span className="text-[11px] font-mono text-gray-500 dark:text-[#A3A3B2] px-3">
                {currentIdx + 1} / {spreads.length}
              </span>
              <button
                onClick={() => setCurrentIdx(Math.min(spreads.length - 1, currentIdx + 1))}
                disabled={currentIdx === spreads.length - 1}
                className="h-8 w-8 rounded-lg border border-gray-200 dark:border-[#2A2442] text-gray-500 dark:text-[#A3A3B2] hover:border-violet-400 hover:text-violet-600 disabled:opacity-40 flex items-center justify-center transition"
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>

        {/* Right properties */}
        {current && (
          <PropertyPanel
            spread={current}
            onUpdate={updateSpread}
            onRegenerateImage={regenerateImage}
            saving={saving}
          />
        )}
      </div>
    </div>
  );
}
