import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import {
  BookOpen, Sparkles, Palette, Image as ImageIcon, Edit3, Eye, Download, Check,
  ChevronRight, ChevronLeft, RefreshCw, Loader2, AlertCircle, FileCheck, Users, Wand2,
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const STEPS = [
  { id: 'brief', label: 'Briefing', icon: BookOpen },
  { id: 'outline', label: 'Outline', icon: Sparkles },
  { id: 'art', label: 'Arte', icon: Palette },
  { id: 'review', label: 'Revisão', icon: FileCheck },
  { id: 'illustrate', label: 'Ilustrações', icon: ImageIcon },
  { id: 'cover', label: 'Capa', icon: Users },
  { id: 'render', label: 'PDF', icon: Eye },
];

const TOKEN_KEY = 'studiox_token';
const authHeaders = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ''}` } });

export default function BookStudio() {
  const { projectId: projectIdParam } = useParams();
  const navigate = useNavigate();

  const [projectId, setProjectId] = useState(projectIdParam || '');
  const [step, setStep] = useState('brief');
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState(null);

  // brief form
  const [brief, setBrief] = useState({
    name: '',
    title: '',
    author_name: '',
    briefing: '',
    format_preset: 'picturebook',
    trim_size: '6x9',
    target_spreads: 14,
    audience: 'children_4_8',
    illustration_track: 'storybook',
    autoria_mode: 'user_author',
    language: 'pt',
    reference_work: '',
    source_project_id: '',
  });

  // state fetched from backend
  const [bookState, setBookState] = useState(null);
  const [projects, setProjects] = useState([]);
  const [autoRunning, setAutoRunning] = useState(false);
  // Per-page regeneration state: Set of page numbers currently regenerating
  const [regeneratingPages, setRegeneratingPages] = useState(new Set());
  // Per-spread regeneration state
  const [regeneratingSpreads, setRegeneratingSpreads] = useState(new Set());

  const loadProjects = useCallback(async () => {
    try {
      const { data } = await axios.get(`${API}/api/studio/projects`, authHeaders());
      const list = Array.isArray(data) ? data : (data?.projects || []);
      setProjects(list.filter((p) => (p?.characters || []).length > 0));
    } catch (e) { /* noop */ }
  }, []);

  const loadState = useCallback(async (pid, opts = {}) => {
    if (!pid) return;
    const { inferStep = true } = opts;
    try {
      const { data } = await axios.get(`${API}/api/studio/projects/${pid}/book/state`, authHeaders());
      setBookState(data || {});
      if (!inferStep) return;
      // infer step — works for both picturebook (spreads) and chapter flow (chapters/plan)
      const hasIllus = (data?.spreads || []).some((s) => s.illustration_url)
        || (data?.illustration_plan || []).some((p) => p.illustration_url);
      if (data?.pdf_url) setStep('render');
      else if ((data?.cover || {}).front_url) setStep('cover');
      else if (hasIllus) setStep('illustrate');
      else if (data?.meeting_room_review) setStep('review');
      else if (data?.theme) setStep('art');
      else if (data?.outline) setStep('outline');
      else if (data?.brief) setStep('ready');
      else setStep('brief');
    } catch (e) { /* noop */ }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);
  useEffect(() => { if (projectId) loadState(projectId); }, [projectId, loadState]);

  // Polling ativo quando pipeline está rodando
  useEffect(() => {
    if (!projectId || !bookState?.pipeline_running) return;
    setAutoRunning(true);
    // Polling refresha o state mas não muda o step atual — respeita a navegação do usuário
    const iv = setInterval(() => { loadState(projectId, { inferStep: false }); }, 3000);
    return () => clearInterval(iv);
  }, [projectId, bookState?.pipeline_running, loadState]);

  useEffect(() => {
    // Quando pipeline termina, desliga o autoRunning
    if (bookState && !bookState.pipeline_running && autoRunning) {
      setAutoRunning(false);
      if (bookState.pipeline_step === 'done') {
        toast.success('🎉 Livro pronto!');
      } else if (bookState.pipeline_step === 'error') {
        toast.error(`Pipeline falhou: ${bookState.pipeline_error || 'erro'}`);
      }
    }
  }, [bookState?.pipeline_running, bookState?.pipeline_step, autoRunning, bookState]);

  const runFullPipeline = async () => {
    if (!projectId) return;
    try {
      await axios.post(`${API}/api/studio/projects/${projectId}/book/run-pipeline`, {}, authHeaders());
      setAutoRunning(true);
      toast.success('🚀 Pipeline iniciada! Acompanhe o progresso abaixo.');
      // Imediatamente atualiza pra pegar status running
      setTimeout(() => loadState(projectId), 800);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Erro ao iniciar pipeline');
    }
  };

  // ── actions ─────────────────────────────────────────────────────
  const callApi = async (method, path, body, okMsg) => {
    setBusyAction(path);
    try {
      const { data } = await axios({ method, url: `${API}${path}`, data: body, ...authHeaders() });
      if (okMsg) toast.success(okMsg);
      return data;
    } catch (e) {
      toast.error(e?.response?.data?.detail || `Erro em ${path}`);
      throw e;
    } finally {
      setBusyAction(null);
    }
  };

  const createBook = async () => {
    if (!brief.name || !brief.briefing) { toast.error('Preencha nome e briefing'); return; }
    setLoading(true);
    try {
      const { data: proj } = await axios.post(`${API}/api/studio/projects`, {
        name: brief.name, briefing: brief.briefing, language: brief.language,
      }, authHeaders());
      const pid = proj.id;
      await axios.post(`${API}/api/studio/projects/${pid}/book/start`, brief, authHeaders());
      toast.success('Projeto criado!');
      setProjectId(pid);
      navigate(`/studio/book/${pid}`);
      await loadState(pid);
    } catch (e) {
      toast.error(e?.response?.data?.detail || 'Erro ao criar');
    } finally { setLoading(false); }
  };

  const genOutline = async () => {
    const d = await callApi('post', `/api/studio/projects/${projectId}/book/generate-outline`, null, 'Outline gerado');
    await callApi('post', `/api/studio/projects/${projectId}/book/approve-outline`);
    await loadState(projectId);
    setStep('outline');
    return d;
  };

  const genArt = async (extra) => {
    await callApi('post', `/api/studio/projects/${projectId}/book/art-direct`, { extra_instructions: extra || '' }, 'Direção de arte definida');
    await loadState(projectId); setStep('art');
  };

  const genReview = async () => {
    await callApi('post', `/api/studio/projects/${projectId}/book/meeting-room-review`, null, 'Meeting Room concluída');
    await loadState(projectId); setStep('review');
  };

  const applyFixes = async () => {
    await callApi('post', `/api/studio/projects/${projectId}/book/apply-review-fixes`, null, 'Ajustes aplicados');
    await loadState(projectId, { inferStep: false });
  };

  const illustrateOne = async (idx) => {
    setRegeneratingSpreads((s) => new Set(s).add(idx));
    try {
      await callApi('post', `/api/studio/projects/${projectId}/book/illustrate-spread`, { spread_index: idx }, `Spread ${idx} ilustrado`);
      await loadState(projectId, { inferStep: false });
    } finally {
      setRegeneratingSpreads((s) => { const n = new Set(s); n.delete(idx); return n; });
    }
  };

  const illustrateAll = async () => {
    const spreads = bookState?.spreads || [];
    for (const s of spreads) {
      if (s.illustration_url) continue;
      setRegeneratingSpreads((p) => new Set(p).add(s.index));
      try { await axios.post(`${API}/api/studio/projects/${projectId}/book/illustrate-spread`, { spread_index: s.index }, authHeaders()); }
      catch (e) { toast.error(`Spread ${s.index} falhou`); }
      setRegeneratingSpreads((p) => { const n = new Set(p); n.delete(s.index); return n; });
      await loadState(projectId, { inferStep: false });
    }
    toast.success('Todas as ilustrações geradas!');
  };

  // Chapter-flow: regenerate a single page illustration (with optional style override)
  const regeneratePageIllus = async (pageNumber, withOverride = false) => {
    const body = { page_number: pageNumber };
    if (withOverride) {
      const extra = window.prompt(
        `Instruções extras para a pg.${pageNumber} (estilo, personagens, cena). Ex: "Pixar 3D, Ash cinza e Snow branco, SEM cachorros extras":`,
        'Manter estilo Pixar 3D consistente com as outras páginas. Personagens principais: Ash (pomerânia cinza-azulado, olhos azuis) e Snow (pomerânia branca, olhos castanhos). NÃO incluir outros cachorros.'
      );
      if (extra === null) return;
      if (extra.trim()) body.override_prompt = extra;
    }
    setRegeneratingPages((s) => new Set(s).add(pageNumber));
    try {
      await callApi('post', `/api/studio/projects/${projectId}/book/generate-illustration`, body, `Página ${pageNumber} regerada`);
      await loadState(projectId, { inferStep: false });
    } finally {
      setRegeneratingPages((s) => { const n = new Set(s); n.delete(pageNumber); return n; });
    }
  };

  // Chapter-flow: regenerate ALL missing/failed pages
  const regenerateAllPages = async () => {
    const plan = (bookState?.illustration_plan || []).filter((p) => p.type !== 'none');
    for (const p of plan) {
      setRegeneratingPages((s) => new Set(s).add(p.page_number));
      try {
        await axios.post(`${API}/api/studio/projects/${projectId}/book/generate-illustration`, { page_number: p.page_number }, authHeaders());
      } catch (e) { toast.error(`Pg ${p.page_number} falhou`); }
      setRegeneratingPages((s) => { const n = new Set(s); n.delete(p.page_number); return n; });
      await loadState(projectId, { inferStep: false });
    }
    toast.success('Ilustrações regeradas!');
  };

  const genCover = async () => {
    await callApi('post', `/api/studio/projects/${projectId}/book/generate-cover-v2`, null, 'Capa gerada');
    await loadState(projectId); setStep('cover');
  };

  const [renderingPdf, setRenderingPdf] = useState(false);

  const renderPDF = async () => {
    if (renderingPdf) return;
    const fmt = bookState?.brief?.format_preset || 'picturebook';
    const endpoint = fmt === 'picturebook' ? 'render-picturebook' : 'render-pdf';
    setRenderingPdf(true);
    const t = toast.loading('Renderizando PDF... (pode levar ~20s)');
    try {
      await axios.post(`${API}/api/studio/projects/${projectId}/book/${endpoint}`, null, authHeaders());
      toast.loading('Validando pré-impressão...', { id: t });
      await axios.post(`${API}/api/studio/projects/${projectId}/book/preflight`, null, authHeaders());
      toast.success('PDF renderizado!', { id: t });
      await loadState(projectId);
      setStep('render');
    } catch (e) {
      toast.error(`Render falhou: ${e?.response?.data?.detail || e.message}`, { id: t });
    } finally {
      setRenderingPdf(false);
    }
  };

  const rewriteSpread = async (idx) => {
    const instr = window.prompt(`Instruções para reescrever spread ${idx}:`, 'encurtar e deixar mais alegre');
    if (!instr) return;
    await callApi('post', `/api/studio/projects/${projectId}/book/rewrite-spread`, { spread_index: idx, instructions: instr }, `Spread ${idx} reescrito`);
    await loadState(projectId, { inferStep: false });
  };

  const updateTheme = async (patch) => {
    await callApi('patch', `/api/studio/projects/${projectId}/book/theme`, patch, 'Tema atualizado');
    await loadState(projectId, { inferStep: false });
  };

  // ── render ──────────────────────────────────────────────────────
  const currentStepIdx = STEPS.findIndex((s) => s.id === step);
  const spreads = bookState?.spreads || [];
  const chapters = Object.values(bookState?.chapters || {}).sort((a, b) => (a.index || 0) - (b.index || 0));
  const illustrationPlan = bookState?.illustration_plan || [];
  const outlineChapters = bookState?.outline?.chapters || [];
  const formatPreset = bookState?.brief?.format_preset || 'picturebook';
  const isPicturebook = formatPreset === 'picturebook';
  const theme = bookState?.theme_applied || bookState?.theme || {};
  const cover = bookState?.cover || {};
  const review = bookState?.meeting_room_review || null;

  // Cache-bust: appends ?v=<generated_at> (or now) to force browser to refetch.
  // Backend overwrites the same storage path so URL alone doesn't change.
  const cacheBust = (url, stamp) => {
    if (!url) return url;
    const v = stamp ? new Date(stamp).getTime() : Date.now();
    return url + (url.includes('?') ? '&' : '?') + 'v=' + v;
  };

  const [downloadingPdf, setDownloadingPdf] = useState(false);

  // Download PDF via backend proxy (avoids ad-blocker blocking Supabase domain)
  const downloadPdf = async () => {
    if (!projectId) return;
    const token = localStorage.getItem(TOKEN_KEY) || '';
    setDownloadingPdf(true);
    const t = toast.loading('Baixando PDF... (pode levar alguns segundos)');
    try {
      const r = await fetch(`${API}/api/studio/projects/${projectId}/book/download-pdf`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}: ${await r.text().catch(() => '')}`);
      const blob = await r.blob();
      const url = window.URL.createObjectURL(blob);
      const filename = `${(bookState?.outline?.title || bookState?.brief?.title || 'livro').replace(/[^\w\-\. ]+/g, '_')}.pdf`;
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      toast.dismiss(t);
      // Persistent toast with fallback link — some browsers (Safari, custom "Save As" setup)
      // silently fail the programmatic download. Give the user a clickable escape hatch.
      toast.success(
        (tid) => (
          <div className="text-xs" data-testid="download-success-toast">
            <div className="font-bold mb-1">✓ Download iniciado!</div>
            <div className="mb-1">Arquivo: <span className="font-mono">{filename}</span></div>
            <div className="text-gray-600 mb-2">Verifique sua pasta <strong>Downloads</strong>.</div>
            <div className="flex gap-2">
              <a
                href={url}
                download={filename}
                className="text-amber-700 underline hover:text-amber-900"
                onClick={() => setTimeout(() => toast.dismiss(tid), 500)}
              >
                Não apareceu? Clique aqui
              </a>
            </div>
          </div>
        ),
        { duration: 30000 }
      );
      // Keep the blob URL alive for 2 min so the fallback link still works
      setTimeout(() => window.URL.revokeObjectURL(url), 120000);
    } catch (e) {
      toast.error(`Download falhou: ${e.message || e}`, { id: t });
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Open PDF inline in a new tab via proxy (blob URL bypasses ad-blocker + supabase block)
  const openPdfInTab = async () => {
    if (!projectId) return;
    const token = localStorage.getItem(TOKEN_KEY) || '';
    setDownloadingPdf(true);
    const t = toast.loading('Abrindo PDF...');
    try {
      const r = await fetch(`${API}/api/studio/projects/${projectId}/book/download-pdf?inline=1`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const blob = await r.blob();
      const url = window.URL.createObjectURL(blob);
      const w = window.open(url, '_blank');
      if (!w) throw new Error('Pop-up bloqueado. Libere pop-ups para este site.');
      toast.success('PDF aberto em nova aba', { id: t });
      // Revoke later; tab needs it alive
      setTimeout(() => window.URL.revokeObjectURL(url), 60000);
    } catch (e) {
      toast.error(`Falha ao abrir: ${e.message || e}`, { id: t });
    } finally {
      setDownloadingPdf(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 via-white to-orange-50" data-testid="book-studio-page">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-white/80 backdrop-blur-md border-b border-amber-100">
        <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/studio')} data-testid="back-to-studio" className="p-1.5 hover:bg-amber-100 rounded-md">
              <ChevronLeft size={18} />
            </button>
            <BookOpen className="text-amber-700" size={22} />
            <h1 className="text-lg font-bold text-amber-900">BookFactory</h1>
            {projectId && <span className="text-xs text-amber-600 font-mono">#{projectId.slice(0, 8)}</span>}
            {projectId && bookState?.brief && !bookState?.pipeline_running && !bookState?.pdf_url && (
              <button
                onClick={runFullPipeline}
                data-testid="btn-run-full-pipeline"
                className="ml-2 flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gradient-to-r from-amber-500 to-orange-600 text-white text-xs font-bold hover:from-amber-600 hover:to-orange-700 shadow-sm transition"
                title="Gera outline → arte → revisão → ilustrações → capa → PDF automaticamente"
              >
                <Sparkles size={13} /> 🚀 Gerar tudo
              </button>
            )}
            {bookState?.pipeline_running && (
              <span className="ml-2 flex items-center gap-1 px-2 py-1 rounded-md bg-amber-100 text-amber-700 text-[10px] font-mono" data-testid="pipeline-running-pill">
                <Loader2 className="animate-spin" size={10} /> {bookState.pipeline_step || 'running'}
              </span>
            )}
          </div>

          {/* Stepper */}
          <div className="hidden md:flex items-center gap-1">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const active = s.id === step;
              const done = i < currentStepIdx;
              // Any step can be accessed if it has data available (PDF done, outline exists, etc.)
              // This gives the user "free navigation" once content exists — no gray blocked look.
              const hasData = (
                (s.id === 'brief' && (bookState?.brief)) ||
                (s.id === 'ready' && bookState?.brief) ||
                (s.id === 'outline' && bookState?.outline) ||
                (s.id === 'art' && bookState?.theme) ||
                (s.id === 'review' && bookState?.meeting_room_review) ||
                (s.id === 'illustrate' && ((bookState?.spreads || []).some((sp) => sp.illustration_url) || (bookState?.illustration_plan || []).some((p) => p.illustration_url))) ||
                (s.id === 'cover' && (bookState?.cover || {}).front_url) ||
                (s.id === 'render' && bookState?.pdf_url)
              );
              const accessible = active || done || hasData;
              return (
                <button
                  key={s.id}
                  onClick={() => {
                    if (!projectId) return;
                    setStep(s.id);
                    // Smooth scroll to top so the panel change is obvious
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                  }}
                  disabled={!projectId && s.id !== 'brief'}
                  data-testid={`step-${s.id}`}
                  title={hasData ? `Ir para ${s.label}` : `${s.label} (ainda não disponível)`}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition cursor-pointer ${
                    active
                      ? 'bg-amber-600 text-white shadow-sm'
                      : accessible
                        ? 'text-amber-700 hover:bg-amber-100 border border-amber-200'
                        : 'text-gray-400 hover:bg-gray-50'
                  }`}
                >
                  <Icon size={13} /> {s.label}
                  {hasData && !active && <Check size={10} className="text-emerald-600" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Auto-pipeline progress banner */}
        {bookState?.pipeline_running && (
          <div className="mb-6 bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-2xl p-5 shadow-lg" data-testid="pipeline-banner">
            <div className="flex items-center gap-3 mb-3">
              <Loader2 className="animate-spin" size={20} />
              <div className="flex-1">
                <h3 className="font-bold">Pipeline rodando automaticamente...</h3>
                <p className="text-xs opacity-90">Passo atual: <strong>{bookState.pipeline_step || '...'}</strong></p>
              </div>
            </div>
            {(bookState.pipeline_log || []).length > 0 && (
              <div className="bg-white/10 rounded-lg p-3 max-h-32 overflow-y-auto font-mono text-[10px] space-y-0.5">
                {(bookState.pipeline_log || []).slice(-8).map((entry, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="opacity-60">{(entry.ts || '').slice(11, 19)}</span>
                    <span className="opacity-80">[{entry.step || '—'}]</span>
                    <span>{entry.msg}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {bookState?.pipeline_step === 'done' && !bookState?.pipeline_running && bookState?.pdf_url && (
          <div className="mb-6 bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex items-center gap-3" data-testid="pipeline-done-banner">
            <Check className="text-emerald-600" size={20} />
            <div className="flex-1">
              <p className="font-semibold text-emerald-900">Livro pronto! Pipeline completa.</p>
              <p className="text-xs text-emerald-700">Baixe o PDF abaixo ou navegue pelos passos.</p>
            </div>
            <button
              onClick={downloadPdf}
              disabled={downloadingPdf}
              data-testid="btn-download-pdf-banner"
              className="px-3 py-1.5 bg-emerald-600 text-white text-xs rounded-lg flex items-center gap-1 hover:bg-emerald-700 disabled:opacity-60">
              {downloadingPdf ? <Loader2 className="animate-spin" size={12} /> : <Download size={12} />}
              {downloadingPdf ? 'Baixando...' : 'Baixar'}
            </button>
          </div>
        )}
        {/* STEP: READY (brief recebido, pipeline ainda não rodou) */}
        {step === 'ready' && bookState?.brief && (
          <div className="bg-white rounded-2xl shadow-lg p-10 max-w-3xl mx-auto text-center" data-testid="ready-panel">
            <div className="w-20 h-20 mx-auto bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center mb-6">
              <BookOpen className="text-white" size={36} />
            </div>
            <h2 className="text-3xl font-bold text-amber-900 mb-2">
              {bookState.brief.title || 'Seu livro'}
            </h2>
            <p className="text-sm text-gray-600 mb-1">Briefing recebido ✅</p>
            <p className="text-xs text-gray-500 mb-8 max-w-md mx-auto">{bookState.brief.briefing}</p>

            <div className="grid md:grid-cols-2 gap-4 max-w-2xl mx-auto">
              <button
                onClick={runFullPipeline}
                disabled={bookState?.pipeline_running}
                data-testid="btn-start-pipeline-auto"
                className="group p-6 rounded-2xl border-2 border-amber-400 bg-gradient-to-br from-amber-50 to-orange-50 hover:border-amber-500 transition text-left relative overflow-hidden"
              >
                <div className="absolute top-2 right-2 text-[9px] font-bold bg-amber-500 text-white px-2 py-0.5 rounded-full">
                  RECOMENDADO
                </div>
                <Sparkles className="text-amber-600 mb-2" size={28} />
                <h3 className="font-bold text-amber-900 mb-1">🚀 Gerar tudo automaticamente</h3>
                <p className="text-xs text-amber-800">
                  Executa outline → arte → revisão → ilustrações → capa → PDF sem intervenção.
                </p>
                <p className="text-[10px] text-amber-700 mt-2 font-mono">~5-8 minutos</p>
              </button>

              <button
                onClick={genOutline}
                disabled={busyAction}
                data-testid="btn-start-pipeline-manual"
                className="p-6 rounded-2xl border-2 border-gray-200 hover:border-amber-300 transition text-left"
              >
                <Edit3 className="text-gray-500 mb-2" size={28} />
                <h3 className="font-bold text-gray-800 mb-1">Modo manual</h3>
                <p className="text-xs text-gray-600">
                  Gere e aprove cada passo individualmente. Ideal pra ter controle total.
                </p>
                <p className="text-[10px] text-gray-500 mt-2 font-mono">Passo a passo</p>
              </button>
            </div>

            <div className="mt-6 pt-6 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-2">Detalhes do projeto</p>
              <div className="flex flex-wrap justify-center gap-2 text-[11px]">
                <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded-full">📖 {bookState.brief.format_preset}</span>
                <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded-full">{bookState.brief.trim_size}</span>
                <span className="px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded-full">{bookState.brief.target_spreads || '?'} spreads</span>
                <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded-full">{bookState.brief.audience}</span>
                <span className="px-2 py-0.5 bg-orange-100 text-orange-800 rounded-full">{bookState.brief.illustration_track}</span>
              </div>
            </div>
          </div>
        )}

        {/* STEP: BRIEF */}
        {step === 'brief' && (
          <div className="bg-white rounded-2xl shadow-lg p-8 max-w-3xl mx-auto" data-testid="brief-form">
            <h2 className="text-2xl font-bold text-amber-900 mb-2">Novo Livro</h2>
            <p className="text-sm text-gray-600 mb-6">Preencha o briefing e escolha o formato. Você pode herdar personagens de outro projeto.</p>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Nome do projeto *</label>
                <input data-testid="brief-name" value={brief.name} onChange={(e) => setBrief({ ...brief, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="Ex: A História de Davi" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Título público (opcional)</label>
                <input data-testid="brief-title" value={brief.title} onChange={(e) => setBrief({ ...brief, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="(deixa em branco pra IA criar)" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Autor</label>
                <input data-testid="brief-author" value={brief.author_name} onChange={(e) => setBrief({ ...brief, author_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="Nome do autor" />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Idioma</label>
                <select data-testid="brief-lang" value={brief.language} onChange={(e) => setBrief({ ...brief, language: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="pt">Português</option>
                  <option value="en">English</option>
                  <option value="es">Español</option>
                </select>
              </div>
              <div className="md:col-span-2">
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Briefing / Sinopse *</label>
                <textarea data-testid="brief-briefing" value={brief.briefing} onChange={(e) => setBrief({ ...brief, briefing: e.target.value })}
                  rows={5} className="w-full px-3 py-2 border rounded-lg text-sm"
                  placeholder="Ex: História bíblica de Abraão e Isaque adaptada para crianças de 4-8 anos, com foco em fé e obediência..." />
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Formato</label>
                <select data-testid="brief-format" value={brief.format_preset} onChange={(e) => setBrief({ ...brief, format_preset: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="picturebook">📖 Picturebook infantil (spreads curtos)</option>
                  <option value="infantil_ilustrado">🖍️ Infantil ilustrado (capítulos)</option>
                  <option value="romance_adulto">📚 Romance adulto</option>
                  <option value="tecnico_historico">📜 Técnico / Histórico</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Tamanho</label>
                <select data-testid="brief-trim" value={brief.trim_size} onChange={(e) => setBrief({ ...brief, trim_size: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="6x9">6×9 in (Royal)</option>
                  <option value="5x8">5×8 in (Digest)</option>
                  <option value="A4">A4</option>
                  <option value="A5">A5</option>
                </select>
              </div>
              {brief.format_preset === 'picturebook' && (
                <div>
                  <label className="text-xs font-semibold text-gray-700 mb-1 block">Nº de spreads</label>
                  <input data-testid="brief-spreads" type="number" min={6} max={32}
                    value={brief.target_spreads} onChange={(e) => setBrief({ ...brief, target_spreads: parseInt(e.target.value) || 14 })}
                    className="w-full px-3 py-2 border rounded-lg text-sm" />
                </div>
              )}
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Público-alvo</label>
                <select data-testid="brief-audience" value={brief.audience} onChange={(e) => setBrief({ ...brief, audience: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="children_0_3">Bebês 0-3</option>
                  <option value="children_4_8">Crianças 4-8</option>
                  <option value="children_9_12">Crianças 9-12</option>
                  <option value="ya">Jovem Adulto</option>
                  <option value="adult">Adulto</option>
                  <option value="technical">Técnico</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Trilha visual</label>
                <select data-testid="brief-track" value={brief.illustration_track} onChange={(e) => setBrief({ ...brief, illustration_track: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="storybook">Storybook</option>
                  <option value="aquarela">Aquarela</option>
                  <option value="cartoon">Cartoon</option>
                  <option value="flat">Flat moderno</option>
                  <option value="realismo_editorial">Realismo editorial</option>
                  <option value="fotorrealismo">Fotorrealismo</option>
                  <option value="none">Sem ilustrações</option>
                </select>
              </div>
              <div>
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Modo de autoria</label>
                <select data-testid="brief-autoria" value={brief.autoria_mode} onChange={(e) => setBrief({ ...brief, autoria_mode: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="user_author">Usuário como autor</option>
                  <option value="public_domain">Domínio público (Bíblia, clássicos)</option>
                  <option value="free">Tema livre (IA cria)</option>
                </select>
              </div>
              {brief.autoria_mode === 'public_domain' && (
                <div className="md:col-span-2">
                  <label className="text-xs font-semibold text-gray-700 mb-1 block">Referência (usa Bible RAG / clássicos)</label>
                  <input data-testid="brief-ref" value={brief.reference_work} onChange={(e) => setBrief({ ...brief, reference_work: e.target.value })}
                    className="w-full px-3 py-2 border rounded-lg text-sm" placeholder="Ex: biblia_genesis_22, biblia_davi_golias, dom_casmurro" />
                </div>
              )}
              <div className="md:col-span-2">
                <label className="text-xs font-semibold text-gray-700 mb-1 block">Herdar personagens de outro projeto</label>
                <select data-testid="brief-source-project" value={brief.source_project_id} onChange={(e) => setBrief({ ...brief, source_project_id: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm">
                  <option value="">— Nenhum (criar personagens novos) —</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.name} — {(p.characters || []).length} personagens</option>
                  ))}
                </select>
                {brief.source_project_id && (
                  <p className="text-[11px] text-amber-700 mt-1">✨ Character Universe: todas as ilustrações usarão esses personagens.</p>
                )}
              </div>
            </div>

            <button onClick={createBook} disabled={loading}
              data-testid="btn-create-book"
              className="mt-6 w-full py-3 bg-gradient-to-r from-amber-600 to-orange-600 text-white font-semibold rounded-lg hover:from-amber-700 hover:to-orange-700 disabled:opacity-50 flex items-center justify-center gap-2">
              {loading ? <Loader2 className="animate-spin" size={16} /> : <Sparkles size={16} />}
              Criar livro e gerar outline
            </button>
          </div>
        )}

        {/* STEP: OUTLINE */}
        {step === 'outline' && bookState?.outline && (
          <div className="bg-white rounded-2xl shadow-lg p-8" data-testid="outline-panel">
            <div className="flex items-start justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-amber-900">{bookState.outline.title}</h2>
                <p className="text-sm text-gray-600 italic mt-1">{bookState.outline.subtitle}</p>
                <p className="text-sm text-gray-700 mt-3 max-w-2xl">{bookState.outline.blurb}</p>
                {(bookState.rag_sources || []).length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {bookState.rag_sources.map((s, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">📖 {s.reference}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-2">
                <button onClick={genOutline} disabled={busyAction} data-testid="btn-regenerate-outline"
                  className="px-3 py-2 text-xs border rounded-lg hover:bg-amber-50 flex items-center gap-1">
                  <RefreshCw size={12} /> Regerar
                </button>
                <button onClick={runFullPipeline} disabled={busyAction || bookState?.pipeline_running} data-testid="btn-run-pipeline-from-outline"
                  className="px-4 py-2 text-xs bg-gradient-to-r from-amber-500 to-orange-600 text-white rounded-lg font-bold hover:from-amber-600 hover:to-orange-700 flex items-center gap-1 shadow-sm">
                  <Sparkles size={12} /> 🚀 Gerar tudo automaticamente
                </button>
                <button onClick={() => genArt()} disabled={busyAction} data-testid="btn-go-art"
                  className="px-3 py-2 text-xs border border-amber-200 text-amber-700 rounded-lg hover:bg-amber-50 flex items-center gap-1">
                  Manual <ChevronRight size={12} />
                </button>
              </div>
            </div>

            <div className="space-y-3">
              {isPicturebook ? (
                spreads.length > 0 ? spreads.map((s) => (
                  <div key={s.index} data-testid={`spread-${s.index}`} className="border rounded-lg p-4 hover:border-amber-300">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-[10px] font-mono bg-amber-100 text-amber-800 px-2 py-0.5 rounded">Spread {s.index}</span>
                          {(s.characters_in_scene || []).map((c, i) => (
                            <span key={i} className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{c}</span>
                          ))}
                        </div>
                        <p className="text-sm text-gray-900 mb-2">"{s.text}"</p>
                        <p className="text-xs text-gray-500 italic">🎨 {s.scene_description}</p>
                      </div>
                      <button onClick={() => rewriteSpread(s.index)} data-testid={`btn-rewrite-${s.index}`}
                        className="p-2 text-amber-600 hover:bg-amber-50 rounded">
                        <Edit3 size={14} />
                      </button>
                    </div>
                  </div>
                )) : <p className="text-sm text-gray-500">Nenhum spread ainda. Clique em "🚀 Gerar tudo" pra começar.</p>
              ) : (
                // CHAPTER FLOW (infantil_ilustrado / romance / técnico)
                <div>
                  <p className="text-xs text-gray-500 mb-3">
                    📖 Formato: <strong>{formatPreset}</strong> — {outlineChapters.length} capítulos planeados, {chapters.length} escritos
                  </p>
                  {outlineChapters.map((ch) => {
                    const written = chapters.find((w) => w.index === ch.index);
                    return (
                      <div key={ch.index} data-testid={`chapter-${ch.index}`} className="border rounded-lg p-4 mb-2 hover:border-amber-300">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-[10px] font-mono bg-amber-100 text-amber-800 px-2 py-0.5 rounded">Cap {ch.index}</span>
                              <span className="text-sm font-semibold text-gray-900">{ch.title}</span>
                              {written ? (
                                <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">✓ {written.word_count || 0} palavras</span>
                              ) : (
                                <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded">pendente</span>
                              )}
                            </div>
                            <p className="text-xs text-gray-600 italic">{ch.synopsis}</p>
                            {written && (
                              <details className="mt-2">
                                <summary className="text-[11px] text-amber-700 cursor-pointer hover:underline">Ver prosa escrita</summary>
                                <pre className="text-xs text-gray-700 whitespace-pre-wrap mt-2 p-3 bg-amber-50 rounded max-h-64 overflow-y-auto font-sans">{written.prose}</pre>
                              </details>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* STEP: ART */}
        {step === 'art' && (
          <div className="bg-white rounded-2xl shadow-lg p-8" data-testid="art-panel">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-amber-900">Direção de Arte</h2>
              <div className="flex gap-2">
                <button onClick={() => genArt(window.prompt('Instruções extras para o Art Director:', '') || '')}
                  disabled={busyAction} data-testid="btn-regenerate-art"
                  className="px-3 py-2 text-xs border rounded-lg hover:bg-amber-50 flex items-center gap-1">
                  <RefreshCw size={12} /> Regerar
                </button>
                <button onClick={genReview} disabled={busyAction} data-testid="btn-go-review"
                  className="px-4 py-2 text-xs bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-1">
                  Revisar no Meeting Room <ChevronRight size={12} />
                </button>
              </div>
            </div>

            {theme ? (
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Tipografia</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs text-gray-500">Fonte do título</label>
                      <input data-testid="theme-title-font" value={theme.title_font || ''}
                        onChange={(e) => updateTheme({ theme: { title_font: e.target.value } })}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Fonte do corpo</label>
                      <input data-testid="theme-body-font" value={theme.body_font || ''}
                        onChange={(e) => updateTheme({ theme: { body_font: e.target.value } })}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                    <div>
                      <label className="text-xs text-gray-500">Tamanho do corpo (pt)</label>
                      <input data-testid="theme-body-size" type="number"
                        value={theme.body_size || 14}
                        onChange={(e) => updateTheme({ theme: { body_size: parseFloat(e.target.value) || 14 } })}
                        className="w-full px-3 py-2 border rounded-lg text-sm" />
                    </div>
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">Paleta</h3>
                  <div className="space-y-3">
                    {['page_bg', 'text_box_bg', 'title_color', 'body_color', 'accent'].map((k) => (
                      <div key={k} className="flex items-center gap-3">
                        <label className="text-xs text-gray-500 w-28">{k}</label>
                        <input data-testid={`theme-${k}`} type="color" value={theme[k] || '#ffffff'}
                          onChange={(e) => updateTheme({ theme: { [k]: e.target.value } })}
                          className="w-10 h-9 border rounded cursor-pointer" />
                        <input value={theme[k] || ''}
                          onChange={(e) => updateTheme({ theme: { [k]: e.target.value } })}
                          className="flex-1 px-2 py-1.5 border rounded text-xs font-mono" />
                      </div>
                    ))}
                  </div>
                </div>
                <div className="md:col-span-2 p-4 rounded-lg" style={{ background: theme.page_bg || '#fff' }}>
                  <h3 className="text-lg font-bold mb-2" style={{ fontFamily: theme.title_font, color: theme.title_color }}>
                    Preview do livro
                  </h3>
                  <p className="text-sm" style={{ fontFamily: theme.body_font, color: theme.body_color, fontSize: `${theme.body_size}px` }}>
                    Este é um preview de como o texto vai aparecer nas páginas do seu livro. Edite as fontes e cores acima.
                  </p>
                </div>
                {bookState?.style_rules && (
                  <div className="md:col-span-2 text-xs text-gray-600 bg-gray-50 rounded-lg p-3">
                    <strong>Regras visuais do Art Director:</strong><br />
                    {bookState.style_rules}
                  </div>
                )}
              </div>
            ) : (
              <button onClick={() => genArt()} disabled={busyAction} data-testid="btn-start-art"
                className="px-4 py-2 bg-amber-600 text-white rounded-lg">
                Gerar direção de arte
              </button>
            )}
          </div>
        )}

        {/* STEP: REVIEW */}
        {step === 'review' && (
          <div className="bg-white rounded-2xl shadow-lg p-8" data-testid="review-panel">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-amber-900">Meeting Room</h2>
              <div className="flex gap-2">
                <button onClick={genReview} disabled={busyAction} data-testid="btn-regenerate-review"
                  className="px-3 py-2 text-xs border rounded-lg hover:bg-amber-50 flex items-center gap-1">
                  <RefreshCw size={12} /> Rodar de novo
                </button>
                {review && (
                  <button onClick={applyFixes} disabled={busyAction} data-testid="btn-apply-fixes"
                    className="px-3 py-2 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1">
                    <Wand2 size={12} /> Aplicar fixes críticos
                  </button>
                )}
                <button onClick={() => setStep('illustrate')} data-testid="btn-go-illustrate"
                  className="px-4 py-2 text-xs bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-1">
                  Ilustrar <ChevronRight size={12} />
                </button>
              </div>
            </div>
            {review ? (
              <div>
                <div className="flex items-center gap-4 mb-6 p-4 bg-amber-50 rounded-lg">
                  <div className="text-4xl font-bold text-amber-700">{review.consistency_score}</div>
                  <div>
                    <div className="text-xs font-semibold text-amber-900 uppercase">Consistência</div>
                    <div className="text-sm text-amber-800">{review.overall_assessment}</div>
                  </div>
                </div>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Issues encontradas ({(review.issues || []).length})</h3>
                <div className="space-y-2">
                  {(review.issues || []).map((iss, i) => (
                    <div key={i} className={`p-3 rounded-lg border-l-4 ${
                      iss.severity === 'critical' ? 'bg-red-50 border-red-400' :
                      iss.severity === 'major' ? 'bg-amber-50 border-amber-400' :
                      'bg-gray-50 border-gray-300'
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <AlertCircle size={12} className={
                          iss.severity === 'critical' ? 'text-red-600' :
                          iss.severity === 'major' ? 'text-amber-600' : 'text-gray-500'
                        } />
                        <span className="text-xs font-bold uppercase">{iss.severity}</span>
                        {iss.spread && <span className="text-[10px] bg-white px-2 py-0.5 rounded">Spread {iss.spread}</span>}
                        <span className="text-[10px] text-gray-500">{iss.type}</span>
                      </div>
                      <p className="text-xs text-gray-800 mb-1">{iss.description}</p>
                      <p className="text-[11px] text-gray-600 italic">💡 {iss.suggested_fix}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <button onClick={genReview} disabled={busyAction} data-testid="btn-start-review"
                className="px-4 py-2 bg-amber-600 text-white rounded-lg">Rodar Meeting Room</button>
            )}
          </div>
        )}

        {/* STEP: ILLUSTRATE */}
        {step === 'illustrate' && (
          <div className="bg-white rounded-2xl shadow-lg p-8" data-testid="illustrate-panel">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-amber-900">Ilustrações</h2>
              <div className="flex gap-2">
                {isPicturebook ? (
                  <button onClick={illustrateAll} disabled={busyAction} data-testid="btn-illustrate-all"
                    className="px-4 py-2 text-xs bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-1 disabled:opacity-50">
                    {busyAction ? <Loader2 className="animate-spin" size={12} /> : <ImageIcon size={12} />}
                    Gerar todas faltantes
                  </button>
                ) : (
                  <button onClick={regenerateAllPages} disabled={busyAction} data-testid="btn-regen-all-pages"
                    className="px-4 py-2 text-xs bg-amber-600 text-white rounded-lg hover:bg-amber-700 flex items-center gap-1 disabled:opacity-50"
                    title="Regera todas as ilustrações deste livro usando os personagens de referência"
                  >
                    {busyAction ? <Loader2 className="animate-spin" size={12} /> : <RefreshCw size={12} />}
                    Regerar todas
                  </button>
                )}
                <button onClick={() => setStep('cover')} data-testid="btn-go-cover"
                  className="px-4 py-2 text-xs border rounded-lg hover:bg-amber-50 flex items-center gap-1">
                  Capa <ChevronRight size={12} />
                </button>
              </div>
            </div>
            {!isPicturebook && (
              <div className="mb-4 bg-purple-50 border border-purple-200 rounded-lg p-3 text-xs text-purple-900">
                💡 <strong>Dica:</strong> clique em <strong>Custom</strong> numa página pra regerar com instruções específicas (ex: "mesmo estilo Pixar 3D", "sem outros cachorros", "personagens Ash cinza + Snow branco"). Útil quando uma ilustração saiu fora do padrão visual.
              </div>
            )}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {isPicturebook ? spreads.map((s) => {
                const isRegenSpread = regeneratingSpreads.has(s.index);
                return (
                <div key={s.index} data-testid={`illus-${s.index}`} className={`border rounded-lg overflow-hidden group relative ${isRegenSpread ? 'ring-2 ring-amber-400' : ''}`}>
                  {s.illustration_url ? (
                    <img src={cacheBust(s.illustration_url, s.generated_at)} alt=""
                      className={`w-full aspect-[4/3] object-cover transition-opacity duration-300 ${isRegenSpread ? 'opacity-40' : 'opacity-100'}`} />
                  ) : (
                    <div className="w-full aspect-[4/3] bg-gray-100 flex items-center justify-center">
                      <ImageIcon size={32} className="text-gray-300" />
                    </div>
                  )}
                  {isRegenSpread && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="bg-white/85 rounded-full p-3 shadow-lg">
                        <Loader2 className="animate-spin text-amber-600" size={24} />
                      </div>
                    </div>
                  )}
                  <div className="p-2">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-mono bg-amber-100 text-amber-800 px-1.5 rounded">#{s.index}</span>
                      <button onClick={() => illustrateOne(s.index)} disabled={isRegenSpread}
                        data-testid={`btn-regen-illus-${s.index}`}
                        className="text-[10px] text-amber-700 hover:bg-amber-50 px-1.5 py-0.5 rounded flex items-center gap-1 disabled:opacity-60">
                        {isRegenSpread ? <Loader2 className="animate-spin" size={10} /> : <RefreshCw size={10} />}
                        {isRegenSpread ? 'Regerando...' : (s.illustration_url ? 'Regerar' : 'Gerar')}
                      </button>
                    </div>
                    <p className="text-[11px] text-gray-700 line-clamp-2">"{s.text}"</p>
                  </div>
                </div>
                );
              }) : illustrationPlan.filter((p) => p.type !== 'none').map((p) => {
                const isRegenPage = regeneratingPages.has(p.page_number);
                return (
                <div key={p.page_number} data-testid={`illus-page-${p.page_number}`} className={`border rounded-lg overflow-hidden group relative ${isRegenPage ? 'ring-2 ring-amber-400' : ''}`}>
                  {p.illustration_url ? (
                    <img src={cacheBust(p.illustration_url, p.generated_at)} alt=""
                      className={`w-full aspect-[4/3] object-cover transition-opacity duration-300 ${isRegenPage ? 'opacity-40' : 'opacity-100'}`} />
                  ) : (
                    <div className="w-full aspect-[4/3] bg-gray-100 flex items-center justify-center">
                      <ImageIcon size={32} className="text-gray-300" />
                    </div>
                  )}
                  {isRegenPage && (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                      <div className="bg-white/85 rounded-full p-3 shadow-lg">
                        <Loader2 className="animate-spin text-amber-600" size={24} />
                      </div>
                    </div>
                  )}
                  <div className="p-2">
                    <div className="flex items-center justify-between mb-1 gap-1">
                      <span className="text-[10px] font-mono bg-amber-100 text-amber-800 px-1.5 rounded">pg.{p.page_number}</span>
                      <span className="text-[9px] text-gray-500">Cap {p.chapter} • {p.type}</span>
                    </div>
                    <p className="text-[11px] text-gray-700 line-clamp-2 mb-2">{p.description}</p>
                    <div className="flex gap-1">
                      <button
                        onClick={() => regeneratePageIllus(p.page_number, false)}
                        disabled={isRegenPage}
                        data-testid={`btn-regen-page-${p.page_number}`}
                        className="flex-1 text-[10px] text-amber-700 hover:bg-amber-50 border border-amber-200 px-1.5 py-1 rounded flex items-center justify-center gap-1 disabled:opacity-60"
                        title="Regerar mantendo o plano original"
                      >
                        {isRegenPage ? <Loader2 className="animate-spin" size={10} /> : <RefreshCw size={10} />}
                        {isRegenPage ? 'Regerando...' : 'Regerar'}
                      </button>
                      <button
                        onClick={() => regeneratePageIllus(p.page_number, true)}
                        disabled={isRegenPage}
                        data-testid={`btn-regen-page-custom-${p.page_number}`}
                        className="flex-1 text-[10px] text-purple-700 hover:bg-purple-50 border border-purple-200 px-1.5 py-1 rounded flex items-center justify-center gap-1 disabled:opacity-60"
                        title="Regerar com instruções customizadas (estilo, personagens)"
                      >
                        {isRegenPage ? <Loader2 className="animate-spin" size={10} /> : <Wand2 size={10} />}
                        Custom
                      </button>
                    </div>
                  </div>
                </div>
                );
              })}
              {!isPicturebook && illustrationPlan.length === 0 && (
                <div className="col-span-full text-center text-sm text-gray-500 py-8">
                  Nenhum plano de ilustração ainda. O Art Director cria durante a pipeline.
                </div>
              )}
            </div>
          </div>
        )}

        {/* STEP: COVER */}
        {step === 'cover' && (
          <div className="bg-white rounded-2xl shadow-lg p-8" data-testid="cover-panel">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-amber-900">Capa</h2>
              <div className="flex gap-2">
                <button onClick={genCover} disabled={busyAction} data-testid="btn-regenerate-cover"
                  className="px-3 py-2 text-xs border rounded-lg hover:bg-amber-50 flex items-center gap-1">
                  <RefreshCw size={12} /> {cover.front_url ? 'Regerar' : 'Gerar'}
                </button>
                <button onClick={renderPDF} disabled={renderingPdf} data-testid="btn-render-pdf"
                  className="px-4 py-2 text-xs bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-lg flex items-center gap-1 disabled:opacity-60">
                  {renderingPdf ? <Loader2 className="animate-spin" size={12} /> : <FileCheck size={12} />}
                  {renderingPdf ? 'Renderizando...' : 'Renderizar PDF final'}
                </button>
              </div>
            </div>
            <div className="max-w-md mx-auto">
              {cover.front_url ? (
                <div className="aspect-[6/9] rounded-lg overflow-hidden shadow-2xl relative" style={{ backgroundImage: `url(${cacheBust(cover.front_url, bookState?.cover_generated_at)})`, backgroundSize: 'cover' }}>
                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/20" />
                  <div className="absolute bottom-6 inset-x-0 text-center text-white p-4">
                    <h3 className="text-2xl font-black drop-shadow-lg">{cover.title || bookState?.outline?.title}</h3>
                    {cover.subtitle && <p className="text-sm italic mt-2">{cover.subtitle}</p>}
                    {cover.author_name && <p className="text-xs mt-3 tracking-widest uppercase opacity-90">{cover.author_name}</p>}
                  </div>
                </div>
              ) : (
                <div className="aspect-[6/9] rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center">
                  <button onClick={genCover} disabled={busyAction} className="px-6 py-3 bg-amber-600 text-white rounded-lg">
                    Gerar capa
                  </button>
                </div>
              )}
              {cover.spine_width_mm && (
                <p className="text-center text-xs text-gray-500 mt-2">Lombada: {cover.spine_width_mm}mm</p>
              )}
            </div>
          </div>
        )}

        {/* STEP: RENDER */}
        {step === 'render' && (
          <div className="bg-white rounded-2xl shadow-lg p-8 text-center" data-testid="render-panel">
            <div className="w-20 h-20 mx-auto bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center mb-6">
              <Check className="text-white" size={40} />
            </div>
            <h2 className="text-3xl font-bold text-amber-900 mb-2">Livro Pronto!</h2>
            {bookState?.page_count && <p className="text-gray-600 mb-1">{bookState.page_count} páginas</p>}
            {bookState?.pdf_size_bytes && <p className="text-xs text-gray-400 mb-6">{Math.round(bookState.pdf_size_bytes / 1024)} KB</p>}

            {bookState?.preflight_report && (
              <div className={`max-w-md mx-auto mb-6 p-4 rounded-lg text-left ${
                bookState.preflight_report.passed ? 'bg-green-50 border border-green-200' : 'bg-amber-50 border border-amber-200'
              }`}>
                <div className="flex items-center gap-2 mb-2">
                  {bookState.preflight_report.passed ?
                    <Check className="text-green-600" size={16} /> :
                    <AlertCircle className="text-amber-600" size={16} />
                  }
                  <span className="text-sm font-semibold">
                    Preflight: {bookState.preflight_report.passed ? 'PASSED' : 'Com avisos'}
                  </span>
                </div>
                {(bookState.preflight_report.warnings || []).map((w, i) => (
                  <p key={i} className="text-xs text-amber-800">⚠️ {w}</p>
                ))}
                {(bookState.preflight_report.blockers || []).map((b, i) => (
                  <p key={i} className="text-xs text-red-700">❌ {b}</p>
                ))}
              </div>
            )}

            {bookState?.pdf_url && (
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={downloadPdf}
                  disabled={downloadingPdf}
                  data-testid="btn-download-pdf"
                  className="px-6 py-3 bg-gradient-to-r from-amber-600 to-orange-600 text-white rounded-lg font-semibold flex items-center justify-center gap-2 hover:from-amber-700 hover:to-orange-700 disabled:opacity-60">
                  {downloadingPdf ? <Loader2 className="animate-spin" size={16} /> : <Download size={16} />}
                  {downloadingPdf ? 'Baixando...' : 'Baixar PDF'}
                </button>
                <button
                  onClick={openPdfInTab}
                  disabled={downloadingPdf}
                  data-testid="btn-open-pdf"
                  className="px-6 py-3 border rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2 disabled:opacity-60">
                  {downloadingPdf ? <Loader2 className="animate-spin" size={16} /> : <Eye size={16} />}
                  Abrir em nova aba
                </button>
                <button onClick={renderPDF} disabled={renderingPdf} data-testid="btn-rerender"
                  className="px-6 py-3 border rounded-lg hover:bg-gray-50 flex items-center justify-center gap-2 disabled:opacity-60">
                  {renderingPdf ? <Loader2 className="animate-spin" size={16} /> : <RefreshCw size={16} />}
                  {renderingPdf ? 'Renderizando...' : 'Renderizar de novo'}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Busy indicator */}
        {busyAction && (
          <div className="fixed bottom-6 right-6 bg-amber-600 text-white px-4 py-2 rounded-lg shadow-lg text-xs font-mono flex items-center gap-2" data-testid="busy-indicator">
            <Loader2 className="animate-spin" size={14} /> {busyAction.split('/').pop()}...
          </div>
        )}
      </div>
    </div>
  );
}
