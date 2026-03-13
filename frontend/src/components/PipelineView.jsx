import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { PenTool, Palette, CheckCircle, CalendarClock, Loader2, Check, ChevronDown, ChevronUp, ArrowRight, Zap, RotateCcw, Trash2, RefreshCw, AlertTriangle, Crown, Lock, Upload, X, Image, Phone, Globe, Mail, FileText, Download, Eye, Clock } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STEP_META = {
  sofia_copy: { agent: 'Sofia', role: 'Copywriter', icon: PenTool, color: '#C9A84C' },
  ana_review_copy: { agent: 'Ana', role: 'Revisora de Copy', icon: CheckCircle, color: '#4CAF50' },
  lucas_design: { agent: 'Lucas', role: 'Designer', icon: Palette, color: '#7CB9E8' },
  ana_review_design: { agent: 'Ana', role: 'Revisora de Design', icon: CheckCircle, color: '#4CAF50' },
  pedro_publish: { agent: 'Pedro', role: 'Publisher', icon: CalendarClock, color: '#E8A87C' },
};

const STEP_ORDER = ['sofia_copy', 'ana_review_copy', 'lucas_design', 'ana_review_design', 'pedro_publish'];

const PLATFORMS = [
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'facebook', label: 'Facebook' },
  { id: 'telegram', label: 'Telegram' },
  { id: 'email', label: 'Email' },
  { id: 'sms', label: 'SMS' },
];

function StepCard({ step, data, isActive, pipelineStatus, onApprove, expanded, onToggle }) {
  const meta = STEP_META[step];
  const Icon = meta.icon;
  const status = data?.status || 'pending';
  const isGeneratingImages = status === 'generating_images';
  const needsApproval = pipelineStatus === 'waiting_approval' && (status === 'completed') &&
    ((step === 'ana_review_copy' && !data?.user_selection) ||
     (step === 'ana_review_design' && !data?.user_selections));
  const isFailed = status === 'failed';
  const requiresUpgrade = status === 'requires_upgrade';
  const hasImages = data?.image_urls && data.image_urls.some(u => u);

  return (
    <div data-testid={`step-card-${step}`} className={`rounded-xl border transition-all duration-300 ${
      isActive || isGeneratingImages ? 'border-[#C9A84C]/50 bg-[#0D0D0D] shadow-[0_0_20px_rgba(201,168,76,0.1)]' :
      needsApproval ? 'border-amber-500/40 bg-[#0D0D0D] shadow-[0_0_15px_rgba(245,158,11,0.08)]' :
      isFailed ? 'border-red-500/30 bg-[#0D0D0D]' :
      requiresUpgrade ? 'border-[#C9A84C]/40 bg-[#0D0D0D]' :
      status === 'completed' ? 'border-green-500/20 bg-[#0D0D0D]' :
      'border-[#1A1A1A] bg-[#0A0A0A]'
    }`}>
      <button onClick={onToggle} className="w-full px-3 py-2.5 flex items-center gap-2.5">
        <div className={`flex h-9 w-9 items-center justify-center rounded-lg shrink-0 transition-all ${isActive ? 'animate-pulse' : ''}`} style={{ backgroundColor: `${meta.color}15` }}>
          {status === 'running' || isGeneratingImages ? (
            <div className="relative">
              <Loader2 size={16} className="animate-spin" style={{ color: meta.color }} />
              <div className="absolute inset-0 rounded-full animate-ping opacity-20" style={{ backgroundColor: meta.color }} />
            </div>
          ) : status === 'completed' ? (
            <Check size={16} className="text-green-400" />
          ) : isFailed ? (
            <AlertTriangle size={16} className="text-red-400" />
          ) : requiresUpgrade ? (
            <Lock size={16} className="text-[#C9A84C]" />
          ) : (
            <Icon size={16} style={{ color: `${meta.color}55` }} />
          )}
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-xs font-semibold text-white">{meta.agent} <span className="text-[#555] font-normal">- {meta.role}</span></p>
          <div className="flex items-center gap-1.5 mt-0.5">
            {status === 'running' && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><span className="w-1.5 h-1.5 rounded-full bg-[#C9A84C] animate-pulse" />Processando...</span>}
            {isGeneratingImages && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400"><Loader2 size={8} className="animate-spin" />Gerando imagens...</span>}
            {status === 'completed' && !needsApproval && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-green-500/10 text-green-400">Concluido</span>}
            {needsApproval && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 animate-pulse"><span className="w-1.5 h-1.5 rounded-full bg-amber-400" />Aguardando sua aprovacao</span>}
            {status === 'pending' && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#222] text-[#555]">Pendente</span>}
            {isFailed && <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full bg-red-500/10 text-red-400">Falhou</span>}
            {requiresUpgrade && <span className="inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C]"><Crown size={8} /> Upgrade Necessario</span>}
          </div>
        </div>
        {data?.elapsed_ms && <span className="text-[8px] text-[#444] shrink-0 bg-[#111] px-1.5 py-0.5 rounded">{(data.elapsed_ms / 1000).toFixed(1)}s</span>}
        {(data?.output || isFailed || requiresUpgrade) && (expanded ? <ChevronUp size={14} className="text-[#444]" /> : <ChevronDown size={14} className="text-[#444]" />)}
      </button>

      {expanded && (data?.output || isFailed || requiresUpgrade) && (
        <div className="px-3 pb-3 border-t border-[#151515]">
          {data?.output && (
            <div className="mt-2 rounded-lg bg-[#111] p-3 max-h-[300px] overflow-y-auto">
              <pre className="text-[10px] text-[#aaa] whitespace-pre-wrap leading-relaxed font-sans">{data.output}</pre>
            </div>
          )}
          {hasImages && (
            <div className="mt-2">
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Imagens Geradas</p>
              <div className="grid grid-cols-3 gap-2">
                {data.image_urls.map((url, i) => url && (
                  <div key={i} className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] group relative">
                    <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1">
                      <span className="text-[8px] text-white font-semibold">Design {i + 1}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          {isFailed && data?.error && (
            <div className="mt-2 rounded-lg bg-red-500/5 border border-red-500/20 p-3">
              <p className="text-[10px] text-red-400">{data.error}</p>
            </div>
          )}
          {needsApproval && step === 'ana_review_copy' && <CopyApproval data={data} onApprove={onApprove} />}
          {needsApproval && step === 'ana_review_design' && <DesignApproval data={data} onApprove={onApprove} />}
        </div>
      )}
    </div>
  );
}

function CopyApproval({ data, onApprove }) {
  const [selected, setSelected] = useState(data?.auto_selection || 1);
  const [submitting, setSubmitting] = useState(false);
  const autoSel = data?.auto_selection || 1;
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selection: selected }); setSubmitting(false); };
  return (
    <div data-testid="copy-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">Escolha a variacao para continuar:</p>
      <p className="text-[9px] text-[#888]">Ana recomendou a <span className="text-[#C9A84C] font-bold">Variacao {autoSel}</span></p>
      <div className="flex gap-2">
        {[1, 2, 3].map(n => (
          <button key={n} data-testid={`select-copy-${n}`} onClick={() => setSelected(n)}
            className={`flex-1 rounded-lg py-2.5 text-[11px] font-semibold border-2 transition-all ${selected === n ? 'border-[#C9A84C] bg-[#C9A84C]/15 text-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.15)]' : 'border-[#222] text-[#666] hover:text-white hover:border-[#333]'}`}>
            {n === autoSel ? `Var ${n} *` : `Variacao ${n}`}
          </button>
        ))}
      </div>
      <button data-testid="approve-copy-btn" onClick={handleApprove} disabled={submitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-[0_0_20px_rgba(201,168,76,0.2)]">
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        {submitting ? 'Enviando...' : 'Aprovar e Continuar'}
      </button>
    </div>
  );
}

function DesignApproval({ data, onApprove }) {
  const autoSels = data?.auto_selections || {};
  const [selections, setSelections] = useState(autoSels);
  const [submitting, setSubmitting] = useState(false);
  const platforms = Object.keys(autoSels);
  const handleApprove = async () => { setSubmitting(true); await onApprove({ selections: Object.keys(selections).length > 0 ? selections : { default: 1 } }); setSubmitting(false); };
  return (
    <div data-testid="design-approval" className="mt-3 space-y-2.5 bg-amber-500/5 rounded-lg p-3 border border-amber-500/20">
      <p className="text-[11px] text-amber-200 font-semibold">Escolha o design por plataforma:</p>
      {platforms.length > 0 ? platforms.map(p => (
        <div key={p} className="flex items-center gap-2">
          <span className="text-[11px] text-white font-medium capitalize w-24">{p}</span>
          <div className="flex gap-1.5 flex-1">
            {[1, 2, 3].map(n => (
              <button key={n} onClick={() => setSelections(prev => ({ ...prev, [p]: n }))}
                className={`flex-1 rounded-lg py-2 text-[10px] font-semibold border-2 transition-all ${(selections[p] || 1) === n ? 'border-[#C9A84C] bg-[#C9A84C]/15 text-[#C9A84C]' : 'border-[#222] text-[#666] hover:text-white'}`}>
                {n === autoSels[p] ? `D${n} *` : `Design ${n}`}
              </button>
            ))}
          </div>
        </div>
      )) : (
        <p className="text-[9px] text-[#888]">Ana avaliou os designs. Clique para aprovar e publicar.</p>
      )}
      <button data-testid="approve-design-btn" onClick={handleApprove} disabled={submitting}
        className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-[12px] font-bold text-black hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50 shadow-[0_0_20px_rgba(201,168,76,0.2)]">
        {submitting ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
        {submitting ? 'Enviando...' : 'Aprovar e Continuar'}
      </button>
    </div>
  );
}

/* ── Completed Pipeline Summary ── */
function CompletedSummary({ pipeline }) {
  const steps = pipeline.steps || {};
  const approvedCopy = steps.ana_review_copy?.approved_content || steps.sofia_copy?.output || '';
  const images = steps.lucas_design?.image_urls?.filter(u => u) || [];
  const schedule = steps.pedro_publish?.output || '';
  const [activeTab, setActiveTab] = useState('copy');

  const copyToClipboard = (text) => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy');
      document.body.removeChild(ta);
      toast.success('Copiado!');
    } catch { toast.error('Erro ao copiar'); }
  };

  return (
    <div data-testid="completed-summary" className="mx-3 mb-3 rounded-xl border border-green-500/20 bg-gradient-to-b from-green-500/5 to-transparent overflow-hidden">
      <div className="px-3 py-2.5 border-b border-[#151515]">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-7 w-7 rounded-lg bg-green-500/10 flex items-center justify-center"><Check size={14} className="text-green-400" /></div>
          <div>
            <p className="text-xs font-bold text-white">Campanha Finalizada</p>
            <p className="text-[9px] text-[#666]">{(pipeline.platforms || []).join(' / ')}</p>
          </div>
        </div>
        <div className="flex gap-1">
          {[
            { id: 'copy', label: 'Copy Final', icon: FileText },
            { id: 'images', label: `Imagens (${images.length})`, icon: Image },
            { id: 'schedule', label: 'Cronograma', icon: CalendarClock },
          ].map(tab => (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)} data-testid={`summary-tab-${tab.id}`}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[9px] font-semibold transition ${
                activeTab === tab.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'
              }`}>
              <tab.icon size={10} />{tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-3 max-h-[350px] overflow-y-auto">
        {activeTab === 'copy' && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[9px] text-[#555] uppercase tracking-wider">Copy Aprovada</p>
              <button onClick={() => copyToClipboard(approvedCopy)} className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5"><FileText size={8} />Copiar</button>
            </div>
            <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A]">{approvedCopy}</pre>
          </div>
        )}
        {activeTab === 'images' && (
          <div>
            <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Imagens da Campanha</p>
            {images.length > 0 ? (
              <div className="grid grid-cols-3 gap-2">
                {images.map((url, i) => (
                  <div key={i} className="rounded-lg overflow-hidden border border-[#1E1E1E] bg-[#111] relative group">
                    <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" loading="lazy" />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
                      <a href={`${process.env.REACT_APP_BACKEND_URL}${url}`} target="_blank" rel="noopener noreferrer"
                        className="h-7 w-7 rounded-lg bg-white/10 flex items-center justify-center hover:bg-white/20 transition">
                        <Download size={12} className="text-white" />
                      </a>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1">
                      <span className="text-[8px] text-white font-semibold">Design {i + 1}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-[10px] text-[#555] text-center py-4">Nenhuma imagem gerada</p>
            )}
          </div>
        )}
        {activeTab === 'schedule' && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <p className="text-[9px] text-[#555] uppercase tracking-wider">Cronograma de Publicacao</p>
              <button onClick={() => copyToClipboard(schedule)} className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5"><FileText size={8} />Copiar</button>
            </div>
            <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A]">{schedule}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── History Card ── */
function HistoryCard({ pipeline, onSelect, onDelete }) {
  const steps = pipeline.steps || {};
  const completedCount = STEP_ORDER.filter(s => steps[s]?.status === 'completed').length;
  const hasImages = steps.lucas_design?.image_urls?.some(u => u);
  const statusColors = { completed: 'text-green-400', failed: 'text-red-400', running: 'text-[#C9A84C]', waiting_approval: 'text-amber-400' };
  const statusLabels = { completed: 'Concluido', failed: 'Falhou', running: 'Em andamento', waiting_approval: 'Aguardando', requires_upgrade: 'Upgrade' };
  const createdAt = pipeline.created_at ? new Date(pipeline.created_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div data-testid={`history-card-${pipeline.id}`}
      className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3 hover:border-[#2A2A2A] transition group cursor-pointer"
      onClick={() => onSelect(pipeline)}>
      <div className="flex items-start gap-2.5">
        {hasImages && steps.lucas_design.image_urls[0] ? (
          <img src={`${process.env.REACT_APP_BACKEND_URL}${steps.lucas_design.image_urls[0]}`}
            alt="" className="w-10 h-10 rounded-lg object-cover border border-[#1E1E1E] shrink-0" />
        ) : (
          <div className="w-10 h-10 rounded-lg bg-[#111] border border-[#1E1E1E] flex items-center justify-center shrink-0">
            <Zap size={14} className="text-[#333]" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-[11px] text-white font-medium truncate">{pipeline.briefing}</p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-[9px] font-semibold ${statusColors[pipeline.status] || 'text-[#555]'}`}>
              {statusLabels[pipeline.status] || pipeline.status}
            </span>
            <span className="text-[8px] text-[#444]">{completedCount}/{STEP_ORDER.length} etapas</span>
            <span className="text-[8px] text-[#333]">{createdAt}</span>
          </div>
          <div className="flex gap-0.5 mt-1">
            {(pipeline.platforms || []).map(p => (
              <span key={p} className="text-[7px] text-[#444] bg-[#111] px-1 py-0.5 rounded capitalize">{p}</span>
            ))}
          </div>
        </div>
        <button onClick={e => { e.stopPropagation(); onDelete(pipeline.id); }}
          className="text-[#222] hover:text-red-400 opacity-0 group-hover:opacity-100 transition p-1">
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  );
}

/* ── Asset Upload ── */
function AssetUploader({ assets, onAssetsChange }) {
  const [uploading, setUploading] = useState(false);
  const logoRef = useRef(null);
  const refRef = useRef(null);

  const handleUpload = async (files, type) => {
    if (!files?.length) return;
    setUploading(true);
    const newAssets = [...assets];
    for (const file of files) {
      if (!file.type.startsWith('image/')) { toast.error('Apenas imagens'); continue; }
      if (file.size > 10 * 1024 * 1024) { toast.error('Maximo 10MB por arquivo'); continue; }
      try {
        const form = new FormData();
        form.append('file', file);
        form.append('asset_type', type);
        const { data } = await axios.post(`${API}/campaigns/pipeline/upload`, form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        newAssets.push({ url: data.url, filename: data.filename, type, name: file.name, preview: URL.createObjectURL(file) });
      } catch (e) {
        toast.error('Erro no upload: ' + (e.response?.data?.detail || 'Tente novamente'));
      }
    }
    onAssetsChange(newAssets);
    setUploading(false);
  };

  const removeAsset = (idx) => {
    onAssetsChange(assets.filter((_, i) => i !== idx));
  };

  const logos = assets.filter(a => a.type === 'logo');
  const refs = assets.filter(a => a.type === 'reference');

  return (
    <div data-testid="asset-uploader" className="space-y-2.5">
      <label className="text-[9px] text-[#555] uppercase tracking-wider block">Marca & Imagens de Referencia</label>

      {/* Logo Upload */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] text-[#888]">Logo da marca</span>
          {logos.length === 0 && (
            <button onClick={() => logoRef.current?.click()} disabled={uploading}
              className="text-[9px] text-[#C9A84C] hover:underline flex items-center gap-0.5 disabled:opacity-40">
              <Upload size={9} /> Upload
            </button>
          )}
          <input ref={logoRef} type="file" accept="image/*" className="hidden" onChange={e => handleUpload(e.target.files, 'logo')} />
        </div>
        {logos.length > 0 && (
          <div className="flex gap-1.5 flex-wrap">
            {logos.map((a, i) => (
              <div key={i} className="relative group">
                <img src={a.preview || `${process.env.REACT_APP_BACKEND_URL}${a.url}`} alt="Logo" className="h-12 w-12 rounded-lg object-cover border border-[#1E1E1E]" />
                <button onClick={() => removeAsset(assets.indexOf(a))}
                  className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <X size={8} className="text-white" />
                </button>
              </div>
            ))}
            <button onClick={() => logoRef.current?.click()} className="h-12 w-12 rounded-lg border border-dashed border-[#2A2A2A] flex items-center justify-center hover:border-[#C9A84C]/30 transition">
              <Upload size={12} className="text-[#444]" />
            </button>
          </div>
        )}
      </div>

      {/* Reference Images Upload */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] text-[#888]">Imagens de referencia</span>
          <button onClick={() => refRef.current?.click()} disabled={uploading}
            className="text-[9px] text-[#C9A84C] hover:underline flex items-center gap-0.5 disabled:opacity-40">
            <Upload size={9} /> Upload
          </button>
          <input ref={refRef} type="file" accept="image/*" multiple className="hidden" onChange={e => handleUpload(e.target.files, 'reference')} />
        </div>
        {refs.length > 0 && (
          <div className="flex gap-1.5 flex-wrap">
            {refs.map((a, i) => (
              <div key={i} className="relative group">
                <img src={a.preview || `${process.env.REACT_APP_BACKEND_URL}${a.url}`} alt="Ref" className="h-12 w-12 rounded-lg object-cover border border-[#1E1E1E]" />
                <button onClick={() => removeAsset(assets.indexOf(a))}
                  className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                  <X size={8} className="text-white" />
                </button>
                <p className="text-[7px] text-[#555] mt-0.5 truncate max-w-[48px]">{a.name}</p>
              </div>
            ))}
          </div>
        )}
        {refs.length === 0 && (
          <button onClick={() => refRef.current?.click()} disabled={uploading}
            className="w-full rounded-lg border border-dashed border-[#1E1E1E] py-3 flex flex-col items-center gap-1 hover:border-[#C9A84C]/20 transition disabled:opacity-40">
            <Image size={16} className="text-[#333]" />
            <span className="text-[9px] text-[#444]">Arraste ou clique para adicionar</span>
          </button>
        )}
      </div>
      {uploading && <p className="text-[9px] text-[#C9A84C] flex items-center gap-1"><Loader2 size={10} className="animate-spin" /> Enviando...</p>}
    </div>
  );
}

/* ── Main PipelineView ── */
export default function PipelineView({ context }) {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const [pipelines, setPipelines] = useState([]);
  const [activePipeline, setActivePipeline] = useState(null);
  const [briefing, setBriefing] = useState('');
  const [mode, setMode] = useState('semi_auto');
  const [platforms, setPlatforms] = useState(['whatsapp', 'instagram', 'facebook']);
  const [creating, setCreating] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [showHistory, setShowHistory] = useState(false);
  const [contactInfo, setContactInfo] = useState({ phone: '', website: '', email: '' });
  const [showContact, setShowContact] = useState(false);
  const [uploadedAssets, setUploadedAssets] = useState([]);
  const pollRef = useRef(null);

  useEffect(() => {
    loadPipelines();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  useEffect(() => {
    if (!activePipeline) return;
    const steps = activePipeline.steps || {};
    const newExpanded = { ...expandedSteps };
    let changed = false;
    STEP_ORDER.forEach(s => {
      const st = steps[s];
      if (!st) return;
      if (activePipeline.status === 'waiting_approval' && st.status === 'completed' && (s === 'ana_review_copy' || s === 'ana_review_design') && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
      if (st.status === 'failed' && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
      if (st.status === 'requires_upgrade' && !newExpanded[s]) { newExpanded[s] = true; changed = true; }
    });
    if (changed) setExpandedSteps(newExpanded);
  }, [activePipeline?.status, activePipeline?.current_step]);

  const startPolling = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => pollPipeline(id), 3000);
  }, []);

  useEffect(() => {
    if (activePipeline && ['running', 'pending'].includes(activePipeline.status)) {
      startPolling(activePipeline.id);
    } else {
      if (pollRef.current) clearInterval(pollRef.current);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [activePipeline?.id, activePipeline?.status, startPolling]);

  const loadPipelines = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/list`);
      const list = data.pipelines || [];
      setPipelines(list);
      const active = list.find(p => ['running', 'pending', 'waiting_approval'].includes(p.status));
      if (active) {
        setActivePipeline(active);
        const exp = {};
        STEP_ORDER.forEach(s => { if (active.steps?.[s]?.status === 'completed') exp[s] = true; if (active.steps?.[s]?.status === 'failed') exp[s] = true; });
        setExpandedSteps(exp);
      }
    } catch {}
  };

  const pollPipeline = async (id) => {
    try {
      const { data } = await axios.get(`${API}/campaigns/pipeline/${id}`);
      setActivePipeline(data);
      if (['completed', 'failed', 'waiting_approval', 'requires_upgrade'].includes(data.status)) {
        if (pollRef.current) clearInterval(pollRef.current);
      }
    } catch {}
  };

  const createPipeline = async () => {
    if (!briefing.trim() || platforms.length === 0) { toast.error('Preencha o briefing e selecione ao menos uma plataforma'); return; }
    setCreating(true);
    try {
      const assetPayload = uploadedAssets.map(a => ({ url: a.url, type: a.type, filename: a.filename }));
      const { data } = await axios.post(`${API}/campaigns/pipeline`, {
        briefing: briefing.trim(), mode, platforms,
        context: context || {},
        contact_info: contactInfo,
        uploaded_assets: assetPayload,
      });
      setActivePipeline(data);
      setBriefing(''); setExpandedSteps({}); setUploadedAssets([]);
      toast.success('Pipeline iniciado!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao criar pipeline'); }
    setCreating(false);
  };

  const approveStep = async (approvalData) => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/approve`, approvalData);
      toast.success('Aprovado! Proxima etapa iniciando...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro ao aprovar'); }
  };

  const retryPipeline = async () => {
    if (!activePipeline) return;
    try {
      await axios.post(`${API}/campaigns/pipeline/${activePipeline.id}/retry`);
      toast.success('Tentando novamente...');
      setTimeout(() => { pollPipeline(activePipeline.id); startPolling(activePipeline.id); }, 1000);
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  const deletePipeline = async (id) => {
    try {
      await axios.delete(`${API}/campaigns/pipeline/${id}`);
      if (activePipeline?.id === id) setActivePipeline(null);
      setPipelines(prev => prev.filter(p => p.id !== id));
      toast.success('Pipeline removido');
    } catch {}
  };

  const toggleStep = (step) => setExpandedSteps(prev => ({ ...prev, [step]: !prev[step] }));
  const togglePlatform = (pid) => setPlatforms(prev => prev.includes(pid) ? prev.filter(p => p !== pid) : [...prev, pid]);
  const resetView = () => { setActivePipeline(null); setExpandedSteps({}); loadPipelines(); };

  // ── Active Pipeline View ──
  if (activePipeline) {
    const steps = activePipeline.steps || {};
    const completedCount = STEP_ORDER.filter(s => steps[s]?.status === 'completed').length;
    const progressPct = Math.round((completedCount / STEP_ORDER.length) * 100);
    const statusConfig = {
      running: { label: 'Executando', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
      waiting_approval: { label: 'Aguardando Aprovacao', color: 'text-amber-400', bg: 'bg-amber-400' },
      completed: { label: 'Concluido!', color: 'text-green-400', bg: 'bg-green-400' },
      failed: { label: 'Falhou', color: 'text-red-400', bg: 'bg-red-400' },
      pending: { label: 'Iniciando...', color: 'text-[#C9A84C]', bg: 'bg-[#C9A84C]' },
    };
    const sc = statusConfig[activePipeline.status] || statusConfig.pending;

    return (
      <div className="flex flex-col h-full">
        {/* Pipeline Header */}
        <div className="border-b border-[#111] px-3 py-2.5 flex items-center gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="text-xs font-semibold text-white">Pipeline {activePipeline.mode === 'auto' ? 'Automatico' : 'Semi-Automatico'}</p>
              <span className={`inline-flex items-center gap-1 text-[9px] font-semibold px-2 py-0.5 rounded-full ${sc.color}`}
                style={{ backgroundColor: `${sc.bg.replace('bg-', '')}10` }}>
                {['running', 'pending'].includes(activePipeline.status) && <span className={`w-1.5 h-1.5 rounded-full ${sc.bg} animate-pulse`} />}
                {sc.label}
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              {(activePipeline.platforms || []).map(p => (
                <span key={p} className="text-[8px] text-[#555] bg-[#111] px-1.5 py-0.5 rounded capitalize">{p}</span>
              ))}
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] font-bold text-white">{progressPct}%</span>
            <span className="text-[8px] text-[#555] ml-1">completo</span>
          </div>
          <button onClick={resetView} className="text-[#444] hover:text-white p-1.5 rounded-lg hover:bg-[#111] transition" title="Novo">
            <RotateCcw size={14} />
          </button>
        </div>

        {/* Briefing */}
        <div className="px-3 py-2 bg-[#080808] border-b border-[#111]">
          <p className="text-[8px] text-[#555] uppercase tracking-wider mb-0.5">Briefing</p>
          <p className="text-[10px] text-[#999] line-clamp-2">{activePipeline.briefing}</p>
          {/* Show uploaded assets info if present */}
          {activePipeline.result?.uploaded_assets?.length > 0 && (
            <div className="flex items-center gap-1.5 mt-1">
              <Image size={9} className="text-[#444]" />
              <span className="text-[8px] text-[#444]">{activePipeline.result.uploaded_assets.length} arquivo(s) anexado(s)</span>
            </div>
          )}
          {activePipeline.result?.contact_info && Object.values(activePipeline.result.contact_info).some(v => v) && (
            <div className="flex items-center gap-1.5 mt-0.5">
              <Phone size={9} className="text-[#444]" />
              <span className="text-[8px] text-[#444]">Dados de contato incluidos</span>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="px-3 py-2">
          <div className="flex items-center gap-0.5">
            {STEP_ORDER.map((s, i) => {
              const st = steps[s]?.status || 'pending';
              const isRun = st === 'running' || st === 'generating_images';
              return (
                <div key={s} className="flex items-center flex-1 gap-0.5">
                  <div className="relative h-2 rounded-full flex-1 bg-[#1A1A1A] overflow-hidden">
                    <div className={`absolute inset-y-0 left-0 rounded-full transition-all duration-700 ${
                      st === 'completed' ? 'w-full bg-green-500' : isRun ? 'w-1/2 bg-[#C9A84C]' : st === 'failed' ? 'w-full bg-red-500' : 'w-0'
                    }`} />
                    {isRun && <div className="absolute inset-0 bg-[#C9A84C]/20 animate-pulse rounded-full" />}
                  </div>
                  {i < STEP_ORDER.length - 1 && <ArrowRight size={8} className="text-[#333] shrink-0" />}
                </div>
              );
            })}
          </div>
        </div>

        {/* Completed Summary */}
        {activePipeline.status === 'completed' && <CompletedSummary pipeline={activePipeline} />}

        {/* Steps */}
        <div className="flex-1 overflow-y-auto px-3 py-1 space-y-2">
          {STEP_ORDER.map(s => (
            <StepCard key={s} step={s} data={steps[s]}
              isActive={s === activePipeline.current_step && activePipeline.status === 'running'}
              pipelineStatus={activePipeline.status} onApprove={approveStep}
              expanded={!!expandedSteps[s]} onToggle={() => toggleStep(s)} />
          ))}
        </div>

        {/* Bottom actions */}
        {activePipeline.status === 'completed' && (
          <div className="px-3 py-3 border-t border-[#111] bg-green-500/5">
            <div className="flex items-center gap-2">
              <Check size={18} className="text-green-400" />
              <p className="text-xs font-bold text-green-400 flex-1">Pipeline concluido com sucesso!</p>
              <button onClick={resetView}
                className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition">
                Novo Pipeline
              </button>
            </div>
          </div>
        )}
        {activePipeline.status === 'failed' && (
          <div className="px-3 py-3 border-t border-[#111] bg-red-500/5">
            <div className="flex items-center gap-2">
              <AlertTriangle size={18} className="text-red-400" />
              <p className="text-xs font-semibold text-red-400 flex-1">Uma etapa falhou. Tente novamente.</p>
              <button onClick={retryPipeline}
                className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition flex items-center gap-1.5">
                <RefreshCw size={12} /> Tentar Novamente
              </button>
            </div>
          </div>
        )}
        {activePipeline.status === 'requires_upgrade' && (
          <div className="px-3 py-3 border-t border-[#111] bg-[#C9A84C]/5">
            <div className="flex items-center gap-2">
              <Crown size={18} className="text-[#C9A84C]" />
              <div className="flex-1">
                <p className="text-xs font-bold text-[#C9A84C]">Upgrade para Enterprise</p>
                <p className="text-[9px] text-[#888]">Sua campanha esta pronta! Faca upgrade para publicar.</p>
              </div>
              <button onClick={() => navigate('/upgrade')}
                className="rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-4 py-2 text-[11px] font-bold text-black hover:opacity-90 transition flex items-center gap-1.5 shadow-[0_0_15px_rgba(201,168,76,0.2)]">
                <Crown size={12} /> Fazer Upgrade
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // ── Creation Form ──
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {/* Pipeline Intro */}
        <div className="text-center py-3">
          <div className="flex items-center justify-center gap-1.5 mb-2">
            {[PenTool, CheckCircle, Palette, CheckCircle, CalendarClock].map((Icon, i) => (
              <div key={i} className="flex items-center gap-1">
                {i > 0 && <ArrowRight size={10} className="text-[#333]" />}
                <div className="h-8 w-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${Object.values(STEP_META)[i].color}15` }}>
                  <Icon size={14} style={{ color: Object.values(STEP_META)[i].color }} />
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-[#888]">{"Sofia cria \u2192 Ana aprova \u2192 Lucas desenha \u2192 Ana aprova \u2192 Pedro publica"}</p>
        </div>

        {/* Briefing */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1">Briefing da Campanha</label>
          <textarea data-testid="pipeline-briefing" value={briefing} onChange={e => setBriefing(e.target.value)} rows={4}
            placeholder="Descreva o que voce quer: tipo de campanha, objetivo, publico-alvo, tom de voz..."
            className="w-full rounded-xl border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-xs text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C]/30 transition" />
        </div>

        {/* Asset Upload */}
        <AssetUploader assets={uploadedAssets} onAssetsChange={setUploadedAssets} />

        {/* Contact Info */}
        <div>
          <button onClick={() => setShowContact(!showContact)} className="flex items-center gap-1.5 text-[9px] text-[#555] uppercase tracking-wider mb-1.5 hover:text-[#888] transition">
            {showContact ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            <Phone size={10} /> Dados de Contato (opcional)
          </button>
          {showContact && (
            <div data-testid="contact-info-section" className="grid grid-cols-1 sm:grid-cols-3 gap-2 bg-[#0D0D0D] rounded-xl border border-[#1A1A1A] p-3">
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Phone size={8} /> Telefone</label>
                <input data-testid="contact-phone" value={contactInfo.phone} onChange={e => setContactInfo(p => ({ ...p, phone: e.target.value }))}
                  placeholder="+55 11 99999-9999" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Globe size={8} /> Website</label>
                <input data-testid="contact-website" value={contactInfo.website} onChange={e => setContactInfo(p => ({ ...p, website: e.target.value }))}
                  placeholder="www.suaempresa.com" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
              <div>
                <label className="text-[8px] text-[#555] uppercase flex items-center gap-1 mb-0.5"><Mail size={8} /> Email</label>
                <input data-testid="contact-email" value={contactInfo.email} onChange={e => setContactInfo(p => ({ ...p, email: e.target.value }))}
                  placeholder="contato@empresa.com" className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#333] outline-none focus:border-[#C9A84C]/30" />
              </div>
            </div>
          )}
        </div>

        {/* Platforms */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1.5">Plataformas</label>
          <div className="flex flex-wrap gap-1.5">
            {PLATFORMS.map(p => (
              <button key={p.id} data-testid={`platform-${p.id}`} onClick={() => togglePlatform(p.id)}
                className={`rounded-lg px-3 py-1.5 text-[11px] font-medium border transition ${platforms.includes(p.id) ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#555] hover:text-white'}`}>
                {p.label}
              </button>
            ))}
          </div>
        </div>

        {/* Mode */}
        <div>
          <label className="text-[9px] text-[#555] uppercase tracking-wider block mb-1.5">Modo de Execucao</label>
          <div className="grid grid-cols-2 gap-2">
            <button data-testid="mode-semi-auto" onClick={() => setMode('semi_auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'semi_auto' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <p className="text-xs font-semibold text-white mb-0.5">Semi-Automatico</p>
              <p className="text-[9px] text-[#555]">Pausa para voce aprovar cada etapa antes de continuar</p>
            </button>
            <button data-testid="mode-auto" onClick={() => setMode('auto')}
              className={`rounded-xl border p-3 text-left transition ${mode === 'auto' ? 'border-[#C9A84C]/40 bg-[#C9A84C]/5' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
              <p className="text-xs font-semibold text-white mb-0.5">Automatico</p>
              <p className="text-[9px] text-[#555]">Ana decide sozinha e o pipeline roda ate o final</p>
            </button>
          </div>
        </div>

        {/* Previous Pipelines */}
        {pipelines.length > 0 && (
          <div>
            <button onClick={() => setShowHistory(!showHistory)} data-testid="toggle-history"
              className="text-[9px] text-[#C9A84C] hover:underline flex items-center gap-1">
              {showHistory ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
              {pipelines.length} pipeline{pipelines.length > 1 ? 's' : ''} anterior{pipelines.length > 1 ? 'es' : ''}
            </button>
            {showHistory && (
              <div className="mt-1.5 space-y-1.5">
                {pipelines.map(p => (
                  <HistoryCard key={p.id} pipeline={p}
                    onSelect={pl => { setActivePipeline(pl); setExpandedSteps({}); }}
                    onDelete={deletePipeline} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Start Button */}
      <div className="px-4 py-3 border-t border-[#1A1A1A]">
        <button data-testid="start-pipeline-btn" onClick={createPipeline}
          disabled={creating || !briefing.trim() || platforms.length === 0}
          className="w-full rounded-xl bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-[13px] font-bold text-black transition hover:opacity-90 disabled:opacity-30 flex items-center justify-center gap-2 shadow-[0_0_25px_rgba(201,168,76,0.15)]">
          {creating ? <Loader2 size={16} className="animate-spin" /> : <Zap size={16} />}
          {creating ? 'Iniciando Pipeline...' : `Iniciar Pipeline ${mode === 'auto' ? 'Automatico' : 'Semi-Automatico'}`}
        </button>
      </div>
    </div>
  );
}
