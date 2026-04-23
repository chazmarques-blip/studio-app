import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Smartphone, Square, Monitor, Download, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const FORMAT_UI = {
  '9:16': { Icon: Smartphone, label: 'Reels/Shorts', sub: '1080×1920', color: '#EC4899' },
  '1:1':  { Icon: Square, label: 'Square', sub: '1080×1080', color: '#8B5CF6' },
  '4:5':  { Icon: Square, label: 'Feed', sub: '1080×1350', color: '#F97316' },
  '16:9': { Icon: Monitor, label: 'Landscape', sub: '1920×1080', color: '#10B981' },
};

/**
 * MultiFormatExport
 * Panel on the Results tab that lets the user request reformatted exports
 * (9:16, 1:1, 4:5, 16:9) of the final video for different platforms.
 * Polls /exports every 5s while any format is "processing".
 */
export function MultiFormatExport({ projectId, lang = 'pt' }) {
  const [exports, setExports] = useState({});
  const pollRef = useRef(null);

  const refresh = async () => {
    try {
      const { data } = await axios.get(`${API}/studio/projects/${projectId}/exports`);
      setExports(data.exports || {});
      return data.exports || {};
    } catch {
      return {};
    }
  };

  useEffect(() => {
    refresh();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [projectId]);

  // Poll while any export is processing
  useEffect(() => {
    const anyProcessing = Object.values(exports).some((e) => e?.status === 'processing');
    if (anyProcessing && !pollRef.current) {
      pollRef.current = setInterval(refresh, 5000);
    } else if (!anyProcessing && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, [exports]);

  const requestExport = async (fmt) => {
    try {
      setExports((prev) => ({ ...prev, [fmt]: { status: 'processing', requested_at: new Date().toISOString() } }));
      await axios.post(`${API}/studio/projects/${projectId}/export-format`, { format: fmt });
      toast.success(lang === 'pt' ? `Exportando em ${fmt}…` : `Exporting ${fmt}…`);
    } catch (e) {
      toast.error(e.response?.data?.detail || (lang === 'pt' ? 'Erro ao exportar' : 'Export failed'));
      setExports((prev) => ({ ...prev, [fmt]: { error: 'Failed', failed_at: new Date().toISOString() } }));
    }
  };

  return (
    <div className="mt-3 rounded-xl border border-gray-200 bg-white p-4" data-testid="multi-format-export">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-[13px] font-bold text-gray-900 flex items-center gap-2">
            <Smartphone size={14} className="text-violet-600" />
            {lang === 'pt' ? 'Exportar para redes sociais' : 'Export for social media'}
          </h3>
          <p className="text-[10px] text-gray-500 mt-0.5">
            {lang === 'pt'
              ? 'Gera uma versão reformatada para cada plataforma (leva ~1 min).'
              : 'Generates a reformatted version for each platform (~1 min).'}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {Object.entries(FORMAT_UI).map(([fmt, ui]) => {
          const ex = exports[fmt] || null;
          const { Icon } = ui;
          const isProcessing = ex?.status === 'processing';
          const isReady = !!ex?.url;
          const isError = !!ex?.error;

          return (
            <div
              key={fmt}
              data-testid={`export-format-${fmt.replace(':','x')}`}
              className={`rounded-lg border p-2.5 transition ${
                isReady ? 'border-emerald-300 bg-emerald-50/50'
                : isError ? 'border-red-300 bg-red-50/50'
                : isProcessing ? 'border-violet-300 bg-violet-50/40'
                : 'border-gray-200 bg-gray-50 hover:border-violet-300'
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <div
                    className="h-6 w-6 rounded-md flex items-center justify-center"
                    style={{ backgroundColor: `${ui.color}20`, color: ui.color }}
                  >
                    <Icon size={12} />
                  </div>
                  <div>
                    <div className="text-[11px] font-bold text-gray-900">{fmt}</div>
                    <div className="text-[9px] text-gray-500">{ui.sub}</div>
                  </div>
                </div>
                {isReady && <CheckCircle2 size={12} className="text-emerald-600" />}
                {isProcessing && <Loader2 size={12} className="text-violet-600 animate-spin" />}
                {isError && <AlertCircle size={12} className="text-red-600" />}
              </div>

              <div className="text-[9px] text-gray-600 mb-2">{ui.label}</div>

              {isReady ? (
                <a
                  href={ex.url}
                  download
                  data-testid={`export-download-${fmt.replace(':','x')}`}
                  className="flex items-center justify-center gap-1 w-full py-1.5 rounded bg-emerald-600 hover:bg-emerald-700 text-white text-[10px] font-semibold transition"
                >
                  <Download size={10} /> {lang === 'pt' ? 'Baixar' : 'Download'}
                </a>
              ) : isProcessing ? (
                <div className="text-center text-[10px] text-violet-700 font-medium py-1.5">
                  {lang === 'pt' ? 'Processando…' : 'Processing…'}
                </div>
              ) : isError ? (
                <button
                  onClick={() => requestExport(fmt)}
                  className="w-full py-1.5 rounded bg-red-100 hover:bg-red-200 text-red-700 text-[10px] font-semibold transition"
                >
                  {lang === 'pt' ? 'Tentar novamente' : 'Retry'}
                </button>
              ) : (
                <button
                  onClick={() => requestExport(fmt)}
                  data-testid={`export-request-${fmt.replace(':','x')}`}
                  className="w-full py-1.5 rounded bg-white border border-gray-300 hover:border-violet-400 hover:bg-violet-50 text-gray-700 hover:text-violet-700 text-[10px] font-semibold transition"
                >
                  {lang === 'pt' ? 'Gerar' : 'Generate'}
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default MultiFormatExport;
