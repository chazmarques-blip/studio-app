import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Calendar, Table2, HardDrive, Link2, Check, ExternalLink, Download, RefreshCw, Trash2, FileSpreadsheet } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function GoogleIntegration() {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState({ connected: false });
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [events, setEvents] = useState([]);
  const [sheets, setSheets] = useState([]);
  const [tab, setTab] = useState('calendar');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (searchParams.get('google_connected')) {
      toast.success(lang === 'pt' ? 'Google conectado!' : 'Google connected!');
    }
    if (searchParams.get('google_error')) {
      toast.error(searchParams.get('google_error'));
    }
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const { data } = await axios.get(`${API}/google/status`);
      setStatus(data);
      if (data.connected) {
        loadCalendarEvents();
        loadSheets();
      }
    } catch {} finally { setLoading(false); }
  };

  const connect = async () => {
    setConnecting(true);
    try {
      const { data } = await axios.get(`${API}/google/connect?origin=${encodeURIComponent(window.location.origin)}`);
      window.location.href = data.authorization_url;
    } catch { toast.error('Error'); setConnecting(false); }
  };

  const disconnect = async () => {
    if (!window.confirm(lang === 'pt' ? 'Desconectar Google?' : 'Disconnect Google?')) return;
    await axios.post(`${API}/google/disconnect`);
    setStatus({ connected: false });
    setEvents([]);
    setSheets([]);
    toast.success(lang === 'pt' ? 'Desconectado' : 'Disconnected');
  };

  const loadCalendarEvents = async () => {
    try { const { data } = await axios.get(`${API}/google/calendar/events`); setEvents(data.events || []); } catch {}
  };

  const loadSheets = async () => {
    try { const { data } = await axios.get(`${API}/google/sheets/list`); setSheets(data.sheets || []); } catch {}
  };

  const exportLeads = async () => {
    setExporting(true);
    try {
      const { data } = await axios.post(`${API}/google/sheets/export-leads`);
      toast.success(lang === 'pt' ? `${data.leads_exported} leads exportados!` : `${data.leads_exported} leads exported!`);
      window.open(data.url, '_blank');
      loadSheets();
    } catch (e) {
      toast.error(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Error');
    } finally { setExporting(false); }
  };

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]"><div className="h-8 w-8 animate-spin rounded-full border-2 border-[#8B5CF6] border-t-transparent" /></div>;

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-5 pb-24">
      {/* Header */}
      <div className="mb-5 flex items-center gap-3">
        <button onClick={() => navigate('/settings')} className="text-[#999] hover:text-white transition"><ArrowLeft size={18} /></button>
        <h1 className="text-lg font-bold text-white">Google</h1>
      </div>

      {/* Connection Status */}
      <div className={`mb-5 glass-card p-4 ${status.connected ? 'border-[#8B5CF6]/20' : ''}`}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#8B5CF6]/10">
            <Link2 size={18} className="text-[#8B5CF6]" />
          </div>
          <div className="flex-1">
            {status.connected ? (
              <>
                <div className="flex items-center gap-1.5">
                  <Check size={12} className="text-[#8B5CF6]" />
                  <p className="text-xs font-semibold text-white">{lang === 'pt' ? 'Conectado' : 'Connected'}</p>
                </div>
                <p className="text-[10px] text-[#999]">{status.email}</p>
              </>
            ) : (
              <>
                <p className="text-xs font-semibold text-white">{lang === 'pt' ? 'Nao conectado' : 'Not connected'}</p>
                <p className="text-[10px] text-[#999]">Calendar, Sheets, Drive</p>
              </>
            )}
          </div>
          {status.connected ? (
            <button onClick={disconnect} className="rounded-lg border border-[#2A2A2A] px-3 py-1.5 text-[10px] text-[#888] hover:border-red-500/30 hover:text-red-400 transition">
              {lang === 'pt' ? 'Desconectar' : 'Disconnect'}
            </button>
          ) : (
            <button data-testid="google-connect-btn" onClick={connect} disabled={connecting}
              className="btn-gold flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs disabled:opacity-50">
              {connecting ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#0A0A0A] border-t-transparent" /> : <Link2 size={13} />}
              {lang === 'pt' ? 'Conectar Google' : 'Connect Google'}
            </button>
          )}
        </div>
      </div>

      {!status.connected && (
        <div className="space-y-2">
          {[
            { icon: Calendar, name: 'Google Calendar', desc: lang === 'pt' ? 'Agentes agendam e consultam eventos automaticamente' : 'Agents schedule and query events automatically' },
            { icon: Table2, name: 'Google Sheets', desc: lang === 'pt' ? 'Exportar leads, ler dados de planilhas' : 'Export leads, read spreadsheet data' },
            { icon: HardDrive, name: 'Google Drive', desc: lang === 'pt' ? 'Usar documentos como base de conhecimento' : 'Use documents as knowledge base' },
          ].map((s, i) => (
            <div key={i} className="glass-card flex items-center gap-3 p-3.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#8B5CF6]/8"><s.icon size={16} className="text-[#8B5CF6]" /></div>
              <div className="flex-1"><p className="text-xs font-medium text-white">{s.name}</p><p className="text-[10px] text-[#B0B0B0]">{s.desc}</p></div>
            </div>
          ))}
        </div>
      )}

      {status.connected && (
        <>
          {/* Tabs */}
          <div className="mb-4 flex rounded-lg bg-[#111] border border-[#1A1A1A] p-1">
            {[
              { key: 'calendar', icon: Calendar, label: 'Calendar' },
              { key: 'sheets', icon: Table2, label: 'Sheets' },
            ].map(tb => (
              <button key={tb.key} onClick={() => setTab(tb.key)}
                className={`flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-xs font-medium transition ${tab === tb.key ? 'bg-[#8B5CF6] text-[#0A0A0A]' : 'text-[#999]'}`}>
                <tb.icon size={13} /> {tb.label}
              </button>
            ))}
          </div>

          {/* Calendar */}
          {tab === 'calendar' && (
            <div>
              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs font-semibold text-white">{lang === 'pt' ? 'Proximos Eventos' : 'Upcoming Events'}</p>
                <button onClick={loadCalendarEvents} className="text-[#999] hover:text-[#8B5CF6] transition"><RefreshCw size={13} /></button>
              </div>
              {events.length > 0 ? (
                <div className="space-y-1.5">
                  {events.map(e => (
                    <div key={e.id} className="glass-card flex items-center gap-2.5 p-3">
                      <Calendar size={14} className="text-[#8B5CF6] shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{e.summary}</p>
                        <p className="text-[9px] text-[#B0B0B0]">
                          {new Date(e.start).toLocaleDateString(lang, { weekday: 'short', day: 'numeric', month: 'short' })}
                          {' '}{new Date(e.start).toLocaleTimeString(lang, { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="glass-card p-6 text-center">
                  <Calendar size={24} className="mx-auto mb-2 text-[#555]" />
                  <p className="text-[10px] text-[#B0B0B0]">{lang === 'pt' ? 'Nenhum evento proximo' : 'No upcoming events'}</p>
                </div>
              )}
            </div>
          )}

          {/* Sheets */}
          {tab === 'sheets' && (
            <div>
              <button data-testid="export-leads-btn" onClick={exportLeads} disabled={exporting}
                className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl border border-[#8B5CF6]/20 bg-[#8B5CF6]/5 py-3 text-xs font-semibold text-[#8B5CF6] transition hover:bg-[#8B5CF6]/10 disabled:opacity-50">
                {exporting ? <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#8B5CF6] border-t-transparent" /> : <Download size={14} />}
                {lang === 'pt' ? 'Exportar Leads para Google Sheets' : 'Export Leads to Google Sheets'}
              </button>

              <div className="mb-3 flex items-center justify-between">
                <p className="text-xs font-semibold text-white">{lang === 'pt' ? 'Suas Planilhas' : 'Your Sheets'}</p>
                <button onClick={loadSheets} className="text-[#999] hover:text-[#8B5CF6] transition"><RefreshCw size={13} /></button>
              </div>
              {sheets.length > 0 ? (
                <div className="space-y-1.5">
                  {sheets.map(s => (
                    <a key={s.id} href={`https://docs.google.com/spreadsheets/d/${s.id}`} target="_blank" rel="noreferrer"
                      className="glass-card flex items-center gap-2.5 p-3 transition hover:border-[#8B5CF6]/20">
                      <FileSpreadsheet size={14} className="text-[#8B5CF6] shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium text-white truncate">{s.name}</p>
                        <p className="text-[9px] text-[#B0B0B0]">{new Date(s.modified).toLocaleDateString(lang)}</p>
                      </div>
                      <ExternalLink size={12} className="text-[#B0B0B0]" />
                    </a>
                  ))}
                </div>
              ) : (
                <div className="glass-card p-6 text-center">
                  <Table2 size={24} className="mx-auto mb-2 text-[#555]" />
                  <p className="text-[10px] text-[#B0B0B0]">{lang === 'pt' ? 'Nenhuma planilha' : 'No spreadsheets'}</p>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
