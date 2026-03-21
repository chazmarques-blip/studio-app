import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Sparkles } from 'lucide-react';
import axios from 'axios';
import PipelineView from '../components/PipelineView';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function MarketingStudio() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [context, setContext] = useState({ company: '', industry: '', audience: '', brand_voice: '' });
  const [showContext, setShowContext] = useState(false);
  const [plan, setPlan] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/dashboard/stats`).then(r => {
      setPlan(r.data.plan || 'free');
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] flex flex-col">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-3 py-2 shrink-0">
        <div className="flex items-center gap-2.5">
          <button data-testid="studio-back" onClick={() => navigate('/marketing')} className="text-[#666] hover:text-white transition"><ArrowLeft size={18} /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#C9A84C] to-[#D4B85A] shrink-0">
            <Sparkles size={14} className="text-black" />
          </div>
          <div className="flex-1">
            <h1 className="text-sm font-semibold text-white">Marketing AI Studio</h1>
          </div>
          <button onClick={() => setShowContext(!showContext)} className="text-[9px] text-[#C9A84C] hover:underline">
            {lang === 'pt' ? 'Contexto' : lang === 'es' ? 'Contexto' : 'Context'}
          </button>
        </div>
      </div>

      {/* Context Panel */}
      {showContext && (
        <div data-testid="context-panel" className="border-b border-[#1A1A1A] px-3 py-2 bg-[#0D0D0D]">
          <div className="grid grid-cols-2 gap-1.5 max-w-xl">
            {[
              { key: 'company', label: lang === 'pt' ? 'Empresa' : lang === 'es' ? 'Empresa' : 'Company' },
              { key: 'industry', label: lang === 'pt' ? 'Segmento' : lang === 'es' ? 'Segmento' : 'Industry' },
              { key: 'audience', label: lang === 'pt' ? 'Publico-alvo' : lang === 'es' ? 'Publico objetivo' : 'Audience' },
              { key: 'brand_voice', label: lang === 'pt' ? 'Tom da Marca' : lang === 'es' ? 'Tono de Marca' : 'Brand Voice' },
            ].map(f => (
              <div key={f.key}>
                <label className="text-[8px] text-[#777] uppercase">{f.label}</label>
                <input value={context[f.key] || ''} onChange={e => setContext(p => ({ ...p, [f.key]: e.target.value }))}
                  className="w-full rounded border border-[#1E1E1E] bg-[#111] px-2 py-1 text-[10px] text-white outline-none" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pipeline View - Direct */}
      <PipelineView context={context} />
    </div>
  );
}
