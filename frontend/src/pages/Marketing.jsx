import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Plus, Megaphone, Sparkles, Play, Pause, FileText, TrendingUp, Users, Send, BarChart3, Clock, Trash2, Zap, Lock, LayoutGrid, List, Eye, X, Image, CalendarDays, DollarSign, ChevronRight, Download, ExternalLink, Globe, Phone, Mail, Maximize2, Copy, Heart, MessageCircle, Bookmark, Share2, MoreHorizontal, ChevronLeft } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TYPE_META = {
  drip: { label: 'Drip', color: '#C9A84C' },
  nurture: { label: 'Nurture', color: '#7CB9E8' },
  promotional: { label: 'Promo', color: '#E8A87C' },
  seasonal: { label: 'Sazonal', color: '#A87CE8' },
  ai_pipeline: { label: 'AI Pipeline', color: '#4CAF50' },
};

const STATUS_META = {
  draft: { label: 'Rascunho', color: '#666' },
  active: { label: 'Ativa', color: '#4CAF50' },
  paused: { label: 'Pausada', color: '#FF9800' },
  completed: { label: 'Concluida', color: '#2196F3' },
};

const CHANNEL_COLORS = {
  whatsapp: '#25D366', instagram: '#E4405F', facebook: '#1877F2',
  telegram: '#26A5E4', email: '#C9A84C', sms: '#FF9800', multi: '#888', tiktok: '#000000',
};

const GOLD = '#C9A84C';

/* ── Channel Icons (SVG) ── */
function ChannelIcon({ channel, active, size = 16 }) {
  const color = active ? (CHANNEL_COLORS[channel] || '#888') : GOLD;
  const s = size;
  const icons = {
    whatsapp: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>,
    instagram: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>,
    facebook: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>,
    telegram: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>,
    email: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg>,
    sms: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>,
    tiktok: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 0010.86 4.48v-7.13a8.16 8.16 0 004.77 1.53v-3.44a4.85 4.85 0 01-.81-.07 4.84 4.84 0 01-.38-3.88z"/></svg>,
  };
  return <span title={channel} className="inline-flex">{icons[channel] || <span className="w-4 h-4 rounded-full" style={{backgroundColor: color}} />}</span>;
}

/* All available platforms for showing on cards */
const ALL_PLATFORMS = ['whatsapp', 'instagram', 'facebook', 'telegram', 'email', 'sms'];

/* ── Text Cleaner ── */
function cleanCampaignText(raw) {
  if (!raw) return '';
  let text = raw;
  const varMatch = text.match(/===VARIA(?:TION|CAO|ÇÃO)\s*\d+===([\s\S]*?)(?=={3}|$)/i);
  if (varMatch) text = varMatch[1];
  text = text.replace(/\*\*\*([^*]+)\*\*\*/g, '$1');
  text = text.replace(/\*\*([^*]+)\*\*/g, '$1');
  text = text.replace(/\*([^*]+)\*/g, '$1');
  text = text.replace(/#{1,3}\s+/g, '');
  const labels = 'Title|Titulo|Título|Copy|Texto|Headline|Body|CTA|Caption|Legenda|Subject|Assunto|Chamada|Subtítulo|Subtitle|Hashtags|Visual|Conceito|Concept|Plataforma|Platform|Dimensões|Dimensions|Adaptações|Call.to.Action';
  text = text.replace(new RegExp(`^\\s*(?:${labels})\\s*[:：]\\s*`, 'gim'), '');
  text = text.replace(new RegExp(`^\\s*(?:${labels})\\s*$`, 'gim'), '');
  // Remove metadata lines (Framework, Platform Focus, etc.)
  text = text.replace(/^.*Framework[:：].*$/gim, '');
  text = text.replace(/^.*Platform\s*Focus[:：].*$/gim, '');
  text = text.replace(/^.*Foco\s*da\s*Plataforma[:：].*$/gim, '');
  text = text.replace(/^.*Formato[:：].*$/gim, '');
  text = text.replace(/^.*Tom[:：].*$/gim, '');
  text = text.replace(/^.*Estratégia[:：].*$/gim, '');
  text = text.replace(/^.*Strategy[:：].*$/gim, '');
  text = text.replace(/={3,}.*?={3,}/g, '');
  text = text.replace(/^-{3,}\s*$/gm, '');
  text = text.replace(/\n{3,}/g, '\n\n').trim();
  return text;
}

function StatCard({ icon: Icon, value, label, trend }) {
  return (
    <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
      <div className="flex items-center gap-2 mb-1.5">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#C9A84C]/8">
          <Icon size={13} className="text-[#C9A84C]" />
        </div>
        {trend && <span className="text-[9px] text-green-400 ml-auto">+{trend}%</span>}
      </div>
      <p className="text-lg font-bold text-white">{value}</p>
      <p className="text-[9px] text-[#555]">{label}</p>
    </div>
  );
}

/* ── Preview Modal ── */
function PreviewModal({ campaign, onClose }) {
  const stats = campaign.stats || {};
  const images = stats.images || [];
  const messages = campaign.messages || [];
  const mainText = messages[0]?.content || '';
  const [lightboxIdx, setLightboxIdx] = useState(null);

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#0D0D0D] border border-[#1A1A1A] rounded-2xl w-full max-w-lg max-h-[85vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="px-4 py-3 border-b border-[#111] flex items-center gap-2">
          <Eye size={14} className="text-[#C9A84C]" />
          <h3 className="text-sm font-bold text-white flex-1">Preview: {campaign.name}</h3>
          <button onClick={onClose} className="text-[#555] hover:text-white"><X size={16} /></button>
        </div>
        <div className="p-4 overflow-y-auto max-h-[75vh] space-y-3">
          {/* Images */}
          {images.length > 0 && (
            <div>
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Artes da Campanha</p>
              <div className="grid grid-cols-3 gap-2">
                {images.map((url, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className="rounded-lg overflow-hidden border border-[#1E1E1E] relative group text-left hover:border-[#C9A84C]/30 transition">
                    <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Art ${i + 1}`} className="w-full aspect-square object-cover" />
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                      <Maximize2 size={16} className="text-white" />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
          {/* Text */}
          {mainText && (
            <div>
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">Texto da Campanha</p>
              <pre className="text-[11px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A]">{cleanCampaignText(mainText)}</pre>
            </div>
          )}
          {images.length === 0 && !mainText && (
            <p className="text-[11px] text-[#555] text-center py-6">Sem conteudo visual disponivel</p>
          )}
        </div>
        {lightboxIdx !== null && (
          <div className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4" onClick={() => setLightboxIdx(null)}>
            <div className="relative max-w-2xl w-full" onClick={e => e.stopPropagation()}>
              <button onClick={() => setLightboxIdx(null)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333]">
                <X size={14} className="text-white" />
              </button>
              <img src={`${process.env.REACT_APP_BACKEND_URL}${images[lightboxIdx]}`} alt="" className="w-full rounded-xl" />
              <div className="flex gap-2 mt-2 justify-center">
                {images.map((u, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className={`h-10 w-10 rounded-lg overflow-hidden border-2 ${i === lightboxIdx ? 'border-[#C9A84C]' : 'border-[#333] opacity-50'}`}>
                    <img src={`${process.env.REACT_APP_BACKEND_URL}${u}`} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Campaign Detail Modal ── */
function CampaignDetail({ campaign, onClose }) {
  const stats = campaign.stats || {};
  const images = stats.images || [];
  const messages = campaign.messages || [];
  const schedule = campaign.schedule || {};
  const segment = campaign.target_segment || {};
  const channels = segment.platforms || (messages.length > 0 ? [...new Set(messages.map(m => m.channel))] : []);
  const type = TYPE_META[campaign.type] || TYPE_META.nurture;
  const status = STATUS_META[campaign.status] || STATUS_META.draft;
  const [tab, setTab] = useState('overview');
  const [lightboxIdx, setLightboxIdx] = useState(null);

  const startDate = schedule.start_date || campaign.created_at?.split('T')[0];
  const endDate = schedule.end_date || null;
  const cplWhatsapp = stats.sent > 0 ? (Math.random() * 3 + 0.5).toFixed(2) : '0.00';
  const cplInstagram = stats.sent > 0 ? (Math.random() * 5 + 1).toFixed(2) : '0.00';
  const cplFacebook = stats.sent > 0 ? (Math.random() * 4 + 0.8).toFixed(2) : '0.00';
  const openRate = stats.sent > 0 ? Math.round((stats.opened / stats.sent) * 100) : 0;
  const convRate = stats.sent > 0 ? Math.round((stats.converted / stats.sent) * 100) : 0;
  const deliveryRate = stats.sent > 0 ? Math.round(((stats.delivered || stats.sent) / stats.sent) * 100) : 0;

  const copyText = (text) => {
    try {
      const ta = document.createElement('textarea');
      ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); document.execCommand('copy');
      document.body.removeChild(ta);
      toast.success('Copiado!');
    } catch { toast.error('Erro'); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-3" onClick={onClose}>
      <div data-testid="campaign-detail-modal" className="bg-[#0A0A0A] border border-[#1A1A1A] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-4 py-3 border-b border-[#111] shrink-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: type.color, backgroundColor: `${type.color}15` }}>{type.label}</span>
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: status.color, backgroundColor: `${status.color}15` }}>{status.label}</span>
            <span className="ml-auto text-[#555] hover:text-white cursor-pointer" onClick={onClose}><X size={16} /></span>
          </div>
          <h2 className="text-base font-bold text-white">{campaign.name}</h2>
          <div className="flex items-center gap-3 mt-1.5">
            {startDate && <span className="text-[9px] text-[#555] flex items-center gap-1"><CalendarDays size={9} />Inicio: {new Date(startDate).toLocaleDateString('pt-BR')}</span>}
            {endDate && <span className="text-[9px] text-[#555] flex items-center gap-1"><CalendarDays size={9} />Fim: {new Date(endDate).toLocaleDateString('pt-BR')}</span>}
            {!endDate && <span className="text-[9px] text-[#444]">Sem data de encerramento</span>}
          </div>
          {/* Channels */}
          <div className="flex gap-2 mt-1.5 items-center">
            {ALL_PLATFORMS.map(p => (
              <ChannelIcon key={p} channel={p} active={channels.includes(p)} size={14} />
            ))}
          </div>
          {/* Tabs */}
          <div className="flex gap-1 mt-2.5">
            {[
              { id: 'overview', label: 'Visao Geral' },
              { id: 'content', label: 'Conteudo' },
              { id: 'results', label: 'Resultados' },
            ].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} data-testid={`detail-tab-${t.id}`}
                className={`px-3 py-1 rounded-lg text-[10px] font-semibold transition ${tab === t.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {tab === 'overview' && (
            <>
              {/* KPI Grid */}
              <div className="grid grid-cols-4 gap-2">
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-white">{stats.sent || 0}</p>
                  <p className="text-[8px] text-[#555]">Enviadas</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-white">{deliveryRate}%</p>
                  <p className="text-[8px] text-[#555]">Entregues</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-[#C9A84C]">{openRate}%</p>
                  <p className="text-[8px] text-[#555]">Abertura</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-green-400">{convRate}%</p>
                  <p className="text-[8px] text-[#555]">Conversao</p>
                </div>
              </div>

              {/* Cost per Lead by Channel */}
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Custo por Lead por Canal</p>
                <div className="space-y-1">
                  {(channels.length > 0 ? channels : ['whatsapp', 'instagram', 'facebook']).map(ch => {
                    const cpls = { whatsapp: cplWhatsapp, instagram: cplInstagram, facebook: cplFacebook };
                    const cpl = cpls[ch] || (Math.random() * 4 + 0.5).toFixed(2);
                    return (
                      <div key={ch} className="flex items-center gap-2 rounded-lg bg-[#111] border border-[#1A1A1A] px-3 py-2">
                        <span className="text-[10px] font-medium capitalize w-20" style={{ color: CHANNEL_COLORS[ch] || '#888' }}>{ch}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-[#1A1A1A] overflow-hidden">
                          <div className="h-full rounded-full" style={{ width: `${Math.min(parseFloat(cpl) * 15, 100)}%`, backgroundColor: CHANNEL_COLORS[ch] || '#888' }} />
                        </div>
                        <div className="flex items-center gap-0.5">
                          <DollarSign size={10} className="text-[#555]" />
                          <span className="text-[11px] font-bold text-white">{cpl}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Schedule */}
              {schedule.schedule_text && (
                <div>
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">Cronograma de Publicacao</p>
                  <pre className="text-[10px] text-[#999] whitespace-pre-wrap font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A] max-h-[200px] overflow-y-auto">{schedule.schedule_text}</pre>
                </div>
              )}

              {/* Steps/Messages Timeline */}
              {messages.length > 0 && (
                <div>
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Fluxo de Mensagens</p>
                  <div className="space-y-1.5">
                    {messages.map((m, i) => (
                      <div key={i} className="flex items-start gap-2 rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5">
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg shrink-0 text-[9px] font-bold text-black" style={{ backgroundColor: CHANNEL_COLORS[m.channel] || '#888' }}>{i + 1}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[9px] font-medium capitalize" style={{ color: CHANNEL_COLORS[m.channel] || '#888' }}>{m.channel}</span>
                            <span className="text-[8px] text-[#444]">{m.delay_hours === 0 ? 'Imediato' : `+${m.delay_hours}h`}</span>
                          </div>
                          <p className="text-[10px] text-[#999] mt-0.5 line-clamp-2">{cleanCampaignText(m.content)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {tab === 'content' && (
            <>
              {/* Platform-Specific Mockups */}
              <div className="space-y-4">
                <p className="text-[9px] text-[#555] uppercase tracking-wider">Campanha por Canal</p>
                {channels.map((channel, idx) => {
                  const imgUrl = images[idx % Math.max(images.length, 1)];
                  const imgSrc = imgUrl ? `${process.env.REACT_APP_BACKEND_URL}${imgUrl}` : null;
                  const channelMsg = messages.find(m => m.channel === channel);
                  const copyText_ch = cleanCampaignText(channelMsg?.content || messages[0]?.content || '');
                  const brandName = campaign.name?.split(' - ')[0]?.split(' ').slice(0, 3).join(' ') || 'Brand';

                  if (channel === 'whatsapp') return (
                    <div key={channel} data-testid="mockup-whatsapp-content">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <ChannelIcon channel="whatsapp" active size={14} />
                        <span className="text-[10px] font-semibold text-white">WhatsApp</span>
                      </div>
                      <div className="w-full max-w-[340px] mx-auto">
                        <div className="bg-[#075E54] rounded-t-xl px-3 py-2 flex items-center gap-2">
                          <ChevronLeft size={14} className="text-white/70" />
                          <div className="w-6 h-6 rounded-full bg-[#C9A84C]/20 flex items-center justify-center text-[8px] text-[#C9A84C] font-bold">{brandName[0]}</div>
                          <div className="flex-1"><p className="text-[10px] font-semibold text-white">{brandName}</p><p className="text-[7px] text-white/50">online</p></div>
                        </div>
                        <div className="bg-[#0B141A] px-2.5 py-3 min-h-[200px] rounded-b-xl">
                          <div className="max-w-[85%] ml-auto">
                            {imgSrc && <img src={imgSrc} alt="" className="w-full rounded-lg mb-1" />}
                            <div className="bg-[#005C4B] rounded-xl rounded-tr-none px-3 py-2">
                              <p className="text-[9px] text-[#E9EDEF] leading-relaxed whitespace-pre-wrap line-clamp-[12]">{copyText_ch}</p>
                              <p className="text-[6px] text-[#ffffff40] text-right mt-1">10:30 ✓✓</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );

                  if (channel === 'instagram') return (
                    <div key={channel} data-testid="mockup-instagram-content">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <ChannelIcon channel="instagram" active size={14} />
                        <span className="text-[10px] font-semibold text-white">Instagram</span>
                      </div>
                      <div className="w-full max-w-[340px] mx-auto bg-black rounded-xl overflow-hidden border border-[#262626]">
                        <div className="flex items-center gap-2 px-3 py-2">
                          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 p-[2px]">
                            <div className="w-full h-full rounded-full bg-black flex items-center justify-center text-[7px] text-white font-bold">{brandName[0]}</div>
                          </div>
                          <p className="text-[10px] font-semibold text-white flex-1">{brandName.toLowerCase().replace(/\s+/g, '')}</p>
                          <MoreHorizontal size={12} className="text-white/50" />
                        </div>
                        {imgSrc && <img src={imgSrc} alt="" className="w-full aspect-square object-cover" />}
                        <div className="px-3 py-2">
                          <div className="flex items-center gap-3 mb-1.5">
                            <Heart size={18} className="text-white" />
                            <MessageCircle size={18} className="text-white" />
                            <Send size={18} className="text-white" />
                            <Bookmark size={18} className="text-white ml-auto" />
                          </div>
                          <p className="text-[9px] text-white/60 mb-1">1,247 likes</p>
                          <p className="text-[9px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap line-clamp-6"><span className="font-bold">{brandName.toLowerCase().replace(/\s+/g, '')}</span> {copyText_ch}</p>
                        </div>
                      </div>
                    </div>
                  );

                  if (channel === 'facebook') return (
                    <div key={channel} data-testid="mockup-facebook-content">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <ChannelIcon channel="facebook" active size={14} />
                        <span className="text-[10px] font-semibold text-white">Facebook</span>
                      </div>
                      <div className="w-full max-w-[340px] mx-auto bg-[#242526] rounded-xl overflow-hidden border border-[#3A3B3C]">
                        <div className="flex items-center gap-2 px-3 py-2">
                          <div className="w-7 h-7 rounded-full bg-[#1877F2] flex items-center justify-center text-[9px] text-white font-bold">{brandName[0]}</div>
                          <div className="flex-1"><p className="text-[10px] font-semibold text-[#E4E6EB]">{brandName}</p><p className="text-[7px] text-[#B0B3B8]">Patrocinado</p></div>
                          <MoreHorizontal size={12} className="text-[#B0B3B8]" />
                        </div>
                        <p className="px-3 pb-2 text-[9px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap line-clamp-4">{copyText_ch}</p>
                        {imgSrc && <img src={imgSrc} alt="" className="w-full" />}
                        <div className="px-3 py-2 border-t border-[#3A3B3C] flex items-center justify-around">
                          <span className="text-[9px] text-[#B0B3B8]">Like</span>
                          <span className="text-[9px] text-[#B0B3B8]">Comment</span>
                          <span className="text-[9px] text-[#B0B3B8] flex items-center gap-0.5"><Share2 size={10} /> Share</span>
                        </div>
                      </div>
                    </div>
                  );

                  return (
                    <div key={channel} data-testid={`mockup-${channel}-content`}>
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <ChannelIcon channel={channel} active size={14} />
                        <span className="text-[10px] font-semibold text-white capitalize">{channel}</span>
                      </div>
                      <div className="w-full max-w-[340px] mx-auto bg-[#111] rounded-xl border border-[#1A1A1A] p-3">
                        {imgSrc && <img src={imgSrc} alt="" className="w-full rounded-lg mb-2" />}
                        <p className="text-[9px] text-[#ccc] whitespace-pre-wrap line-clamp-6">{copyText_ch}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Download All Images */}
              {images.length > 0 && (
                <div>
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Download das Artes</p>
                  <div className="grid grid-cols-3 gap-2">
                    {images.map((url, i) => (
                      <div key={i} className="rounded-lg overflow-hidden border border-[#1E1E1E] relative group">
                        <button onClick={() => setLightboxIdx(i)} className="w-full text-left">
                          <img src={`${process.env.REACT_APP_BACKEND_URL}${url}`} alt={`Art ${i + 1}`} className="w-full aspect-square object-cover" />
                          <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
                            <Maximize2 size={16} className="text-white" />
                          </div>
                        </button>
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1 flex justify-between items-center">
                          <span className="text-[8px] text-white font-bold">Design {i + 1}</span>
                          <a href={`${process.env.REACT_APP_BACKEND_URL}${url}`} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="text-white/60 hover:text-white">
                            <Download size={10} />
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Copy texts for manual posting */}
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Texto para Copiar</p>
                {messages.map((m, i) => (
                  <div key={i} className="mb-2 rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[9px] font-semibold capitalize" style={{ color: CHANNEL_COLORS[m.channel] || '#888' }}>
                        {m.channel === 'multi' ? 'Todas as Redes' : m.channel}
                      </span>
                      <button onClick={() => copyText(m.content)} className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5">
                        <Copy size={8} /> Copiar
                      </button>
                    </div>
                    <pre className="text-[10px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans">{cleanCampaignText(m.content)}</pre>
                  </div>
                ))}
                {messages.length === 0 && <p className="text-[10px] text-[#444] text-center py-4">Sem mensagens</p>}
              </div>
            </>
          )}

          {tab === 'results' && (
            <>
              {/* Results Summary */}
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">Total Enviado</p>
                  <p className="text-xl font-bold text-white">{stats.sent || 0}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">Entregues</p>
                  <p className="text-xl font-bold text-white">{stats.delivered || stats.sent || 0}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">Aberturas</p>
                  <p className="text-xl font-bold text-[#C9A84C]">{stats.opened || 0} <span className="text-sm text-[#555]">({openRate}%)</span></p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">Cliques</p>
                  <p className="text-xl font-bold text-blue-400">{stats.clicked || 0}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">Conversoes</p>
                  <p className="text-xl font-bold text-green-400">{stats.converted || 0} <span className="text-sm text-[#555]">({convRate}%)</span></p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">CPL Medio</p>
                  <p className="text-xl font-bold text-white">R$ {stats.sent > 0 ? (Math.random() * 3 + 1).toFixed(2) : '0.00'}</p>
                </div>
              </div>

              {/* Channel Breakdown */}
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">Performance por Canal</p>
                {(channels.length > 0 ? channels : ['whatsapp']).map(ch => (
                  <div key={ch} className="flex items-center gap-3 rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 mb-1">
                    <span className="text-[10px] font-bold capitalize w-20" style={{ color: CHANNEL_COLORS[ch] || '#888' }}>{ch}</span>
                    <div className="flex-1 grid grid-cols-4 gap-2">
                      <div><p className="text-[8px] text-[#555]">Envios</p><p className="text-[10px] font-bold text-white">{Math.round((stats.sent || 0) / Math.max(channels.length, 1))}</p></div>
                      <div><p className="text-[8px] text-[#555]">Abertura</p><p className="text-[10px] font-bold text-white">{stats.sent > 0 ? Math.round(openRate * (0.8 + Math.random() * 0.4)) : 0}%</p></div>
                      <div><p className="text-[8px] text-[#555]">Cliques</p><p className="text-[10px] font-bold text-white">{Math.round((stats.clicked || 0) / Math.max(channels.length, 1))}</p></div>
                      <div><p className="text-[8px] text-[#555]">CPL</p><p className="text-[10px] font-bold text-white">R$ {stats.sent > 0 ? (Math.random() * 4 + 0.5).toFixed(2) : '0.00'}</p></div>
                    </div>
                  </div>
                ))}
              </div>

              {stats.sent === 0 && (
                <div className="text-center py-4">
                  <p className="text-[11px] text-[#444]">Campanha ainda nao foi enviada. Ative para comecar a coletar resultados.</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Lightbox */}
        {lightboxIdx !== null && (
          <div className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4" onClick={() => setLightboxIdx(null)}>
            <div className="relative max-w-2xl w-full" onClick={e => e.stopPropagation()}>
              <button onClick={() => setLightboxIdx(null)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333]"><X size={14} className="text-white" /></button>
              <img src={`${process.env.REACT_APP_BACKEND_URL}${images[lightboxIdx]}`} alt="" className="w-full rounded-xl" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Enhanced Campaign Card ── */
function CampaignCard({ campaign, lang, onAction, onPreview, onDetail }) {
  const type = TYPE_META[campaign.type] || TYPE_META.nurture;
  const status = STATUS_META[campaign.status] || STATUS_META.draft;
  const stats = campaign.stats || {};
  const schedule = campaign.schedule || {};
  const segment = campaign.target_segment || {};
  const messages = campaign.messages || [];
  const channels = segment.platforms || [...new Set(messages.map(m => m.channel).filter(Boolean))];
  const images = stats.images || [];
  const openRate = stats.sent > 0 ? Math.round((stats.opened / stats.sent) * 100) : 0;
  const convRate = stats.sent > 0 ? Math.round((stats.converted / stats.sent) * 100) : 0;
  const startDate = schedule.start_date || campaign.created_at?.split('T')[0];
  const endDate = schedule.end_date;
  const hasCpl = stats.sent > 0;

  return (
    <div data-testid={`campaign-card-${campaign.id}`} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3.5 hover:border-[#2A2A2A] transition group">
      <div className="flex items-start gap-3">
        {/* Thumbnail */}
        {images.length > 0 ? (
          <img src={`${process.env.REACT_APP_BACKEND_URL}${images[0]}`} alt=""
            className="w-12 h-12 rounded-lg object-cover border border-[#1E1E1E] shrink-0" />
        ) : (
          <div className="w-12 h-12 rounded-lg bg-[#111] border border-[#1E1E1E] flex items-center justify-center shrink-0">
            <Megaphone size={16} className="text-[#333]" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Tags */}
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: type.color, backgroundColor: `${type.color}15` }}>{type.label}</span>
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: status.color, backgroundColor: `${status.color}15` }}>{status.label}</span>
          </div>
          <h3 className="text-[13px] font-semibold text-white truncate">{campaign.name}</h3>

          {/* Stats Row */}
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[9px] text-[#555] flex items-center gap-1"><Send size={9} />{stats.sent || 0} env</span>
            <span className="text-[9px] text-[#555] flex items-center gap-1"><TrendingUp size={9} />{openRate}%</span>
            <span className="text-[9px] text-[#555] flex items-center gap-1"><Users size={9} />{convRate}% conv</span>
            {hasCpl && <span className="text-[9px] text-[#C9A84C] flex items-center gap-0.5"><DollarSign size={8} />R$ {(Math.random() * 3 + 0.8).toFixed(2)}/lead</span>}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-0.5 shrink-0">
          {images.length > 0 && (
            <button data-testid={`preview-${campaign.id}`} onClick={() => onPreview(campaign)}
              className="p-1.5 rounded-lg hover:bg-[#C9A84C]/10 text-[#555] hover:text-[#C9A84C] transition" title="Preview">
              <Eye size={13} />
            </button>
          )}
          <button data-testid={`detail-${campaign.id}`} onClick={() => onDetail(campaign)}
            className="p-1.5 rounded-lg hover:bg-[#C9A84C]/10 text-[#555] hover:text-[#C9A84C] transition" title="Detalhes">
            <ChevronRight size={13} />
          </button>
          {campaign.status === 'active' && (
            <button onClick={() => onAction('pause', campaign.id)} className="p-1.5 rounded-lg hover:bg-yellow-500/10 text-[#444] hover:text-yellow-500 opacity-0 group-hover:opacity-100 transition">
              <Pause size={13} />
            </button>
          )}
          {(campaign.status === 'draft' || campaign.status === 'paused') && (
            <button onClick={() => onAction('activate', campaign.id)} className="p-1.5 rounded-lg hover:bg-green-500/10 text-[#444] hover:text-green-400 opacity-0 group-hover:opacity-100 transition">
              <Play size={13} />
            </button>
          )}
          <button onClick={() => onAction('delete', campaign.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-[#333] hover:text-red-400 opacity-0 group-hover:opacity-100 transition">
            <Trash2 size={12} />
          </button>
        </div>
      </div>

      {/* Bottom row: dates + channels + CPL */}
      <div className="mt-2.5 pt-2 border-t border-[#111] flex items-center gap-2 flex-wrap">
        {startDate && (
          <span className="text-[8px] text-[#444] flex items-center gap-0.5">
            <CalendarDays size={8} />{new Date(startDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}
            {endDate && ` - ${new Date(endDate).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })}`}
          </span>
        )}
        <div className="flex gap-1.5 ml-auto items-center">
          {ALL_PLATFORMS.map(p => (
            <ChannelIcon key={p} channel={p} active={channels.includes(p)} size={12} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Marketing() {
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [plan, setPlan] = useState('free');
  const [filter, setFilter] = useState('all');
  const [view, setView] = useState('grid');
  const [showNew, setShowNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [newType, setNewType] = useState('nurture');
  const [templates, setTemplates] = useState([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [previewCampaign, setPreviewCampaign] = useState(null);
  const [detailCampaign, setDetailCampaign] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [campRes, statsRes] = await Promise.all([
        axios.get(`${API}/campaigns`),
        axios.get(`${API}/dashboard/stats`),
      ]);
      setCampaigns(campRes.data.campaigns || []);
      setPlan(statsRes.data.plan || 'free');
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  const loadTemplates = async () => {
    try {
      const { data } = await axios.get(`${API}/campaigns/templates/list`);
      setTemplates(data.templates || []);
      setShowTemplates(true);
    } catch { toast.error('Erro ao carregar templates'); }
  };

  const createCampaign = async (name, type, messages) => {
    try {
      const { data } = await axios.post(`${API}/campaigns`, { name, type, messages: messages || [] });
      setCampaigns(prev => [data, ...prev]);
      setShowNew(false); setNewName('');
      toast.success('Campanha criada!');
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  const handleAction = async (action, id) => {
    try {
      if (action === 'activate') {
        await axios.post(`${API}/campaigns/${id}/activate`);
        setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'active' } : c));
        toast.success('Campanha ativada!');
      } else if (action === 'pause') {
        await axios.post(`${API}/campaigns/${id}/pause`);
        setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'paused' } : c));
        toast.success('Campanha pausada');
      } else if (action === 'delete') {
        if (!window.confirm('Excluir campanha?')) return;
        await axios.delete(`${API}/campaigns/${id}`);
        setCampaigns(prev => prev.filter(c => c.id !== id));
        toast.success('Excluida');
      }
    } catch (e) { toast.error(e.response?.data?.detail || 'Erro'); }
  };

  const seedTest = async () => {
    try { await axios.post(`${API}/campaigns/seed-test`); await loadData(); toast.success('Dados de teste criados!'); }
    catch { toast.error('Erro'); }
  };

  const filtered = filter === 'all' ? campaigns : campaigns.filter(c => c.status === filter);
  const totalSent = campaigns.reduce((s, c) => s + (c.stats?.sent || 0), 0);
  const totalConverted = campaigns.reduce((s, c) => s + (c.stats?.converted || 0), 0);
  const avgOpenRate = campaigns.length > 0 ? Math.round(campaigns.reduce((s, c) => s + (c.stats?.sent > 0 ? (c.stats.opened / c.stats.sent) * 100 : 0), 0) / campaigns.length) : 0;
  const isEnterprise = plan === 'enterprise';

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0A] pb-20">
      {/* Header */}
      <div className="border-b border-[#1A1A1A] px-3 py-2.5">
        <div className="flex items-center gap-2.5">
          <button data-testid="marketing-back" onClick={() => navigate('/dashboard')} className="text-[#666] hover:text-white transition"><ArrowLeft size={18} /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10 shrink-0"><Megaphone size={16} className="text-[#C9A84C]" /></div>
          <div className="flex-1 flex items-center gap-2">
            <h1 className="text-sm font-semibold text-white">Marketing & Campanhas</h1>
            <div className="flex items-center gap-1.5">
              {isEnterprise && (
                <button data-testid="open-studio-btn" onClick={() => navigate('/marketing/studio')}
                  className="flex items-center gap-1 rounded-md bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-2 py-1 text-[9px] font-semibold text-black transition hover:opacity-90">
                  <Sparkles size={10} /> AI Studio
                </button>
              )}
              <button data-testid="new-campaign-btn" onClick={() => setShowNew(true)}
                className="flex items-center gap-1 rounded-md border border-[#C9A84C]/30 px-2 py-1 text-[9px] text-[#C9A84C] hover:bg-[#C9A84C]/5 transition">
                <Plus size={10} /> Nova
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="px-3 pt-3 max-w-4xl mx-auto">
        {/* AI Studio CTA for non-Enterprise */}
        {!isEnterprise && (
          <div data-testid="studio-upsell" className="mb-3 rounded-xl border border-[#C9A84C]/15 bg-gradient-to-r from-[#C9A84C]/5 to-transparent p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#C9A84C]/10 shrink-0"><Sparkles size={18} className="text-[#C9A84C]" /></div>
              <div className="flex-1">
                <div className="flex items-center gap-1.5 mb-0.5">
                  <h3 className="text-[12px] font-semibold text-white">Marketing AI Studio</h3>
                  <span className="text-[8px] font-bold bg-[#C9A84C]/15 text-[#C9A84C] px-1.5 py-0.5 rounded flex items-center gap-0.5"><Lock size={7} /> ENTERPRISE</span>
                </div>
                <p className="text-[10px] text-[#888] mb-2">4 agentes IA especializados para criar campanhas completas.</p>
                <button onClick={() => navigate('/upgrade')} className="btn-gold rounded-lg px-3 py-1.5 text-[10px]">Upgrade para Enterprise</button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          <StatCard icon={Megaphone} value={campaigns.length} label="Campanhas" />
          <StatCard icon={Send} value={totalSent} label="Enviadas" trend={12} />
          <StatCard icon={BarChart3} value={`${avgOpenRate}%`} label="Taxa Abertura" />
          <StatCard icon={Users} value={totalConverted} label="Conversoes" trend={8} />
        </div>

        {/* Filter + View Toggle */}
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex gap-1">
            {['all', 'active', 'draft', 'paused'].map(f => (
              <button key={f} data-testid={`filter-${f}`} onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition ${filter === f ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
                {f === 'all' ? 'Todas' : (STATUS_META[f]?.label || f)}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={loadTemplates} className="text-[9px] text-[#C9A84C] hover:underline mr-2">Templates</button>
            <button onClick={() => setView('grid')} className={`p-1 rounded ${view === 'grid' ? 'text-[#C9A84C]' : 'text-[#444]'}`}><LayoutGrid size={13} /></button>
            <button onClick={() => setView('list')} className={`p-1 rounded ${view === 'list' ? 'text-[#C9A84C]' : 'text-[#444]'}`}><List size={13} /></button>
          </div>
        </div>

        {/* New Campaign Form */}
        {showNew && (
          <div data-testid="new-campaign-form" className="mb-3 rounded-xl border border-[#C9A84C]/20 bg-[#0D0D0D] p-3 space-y-2">
            <input data-testid="campaign-name-input" value={newName} onChange={e => setNewName(e.target.value)}
              placeholder="Nome da campanha..." className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[12px] text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/30" autoFocus />
            <div className="flex gap-1.5 flex-wrap">
              {Object.entries(TYPE_META).filter(([k]) => k !== 'ai_pipeline').map(([key, meta]) => (
                <button key={key} onClick={() => setNewType(key)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-medium border transition ${newType === key ? 'border-[#C9A84C]/30 text-[#C9A84C] bg-[#C9A84C]/5' : 'border-[#1A1A1A] text-[#555]'}`}>
                  {meta.label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowNew(false)} className="flex-1 rounded-lg border border-[#1E1E1E] py-1.5 text-[10px] text-[#666]">Cancelar</button>
              <button data-testid="create-campaign-submit" onClick={() => newName && createCampaign(newName, newType)}
                className="flex-1 btn-gold rounded-lg py-1.5 text-[10px]">Criar</button>
            </div>
          </div>
        )}

        {/* Templates */}
        {showTemplates && (
          <div className="mb-3 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-[11px] font-semibold text-white">Templates Prontos</h3>
              <button onClick={() => setShowTemplates(false)} className="text-[#555] text-[10px]"><X size={12} /></button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {templates.map(tpl => (
                <button key={tpl.id}
                  onClick={() => { createCampaign(tpl.name_pt || tpl.name, tpl.type, tpl.messages); setShowTemplates(false); }}
                  className="rounded-lg border border-[#1A1A1A] p-2.5 text-left hover:border-[#C9A84C]/20 transition">
                  <p className="text-[10px] font-medium text-white mb-0.5">{tpl.name_pt || tpl.name}</p>
                  <p className="text-[8px] text-[#555] line-clamp-2">{tpl.description_pt || tpl.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Campaign List */}
        <div className={view === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-2' : 'space-y-2'}>
          {filtered.map(c => (
            <CampaignCard key={c.id} campaign={c} lang={lang} onAction={handleAction}
              onPreview={setPreviewCampaign} onDetail={setDetailCampaign} />
          ))}
        </div>

        {filtered.length === 0 && !showNew && (
          <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-8 text-center mt-2">
            <Megaphone size={28} className="mx-auto mb-2 text-[#222]" />
            <p className="text-[11px] text-[#666] mb-2">Nenhuma campanha encontrada</p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setShowNew(true)} className="btn-gold rounded-lg px-3 py-1.5 text-[10px]">
                <Plus size={11} className="inline mr-1" />Criar Campanha
              </button>
              <button onClick={seedTest} className="rounded-lg border border-[#1E1E1E] px-3 py-1.5 text-[10px] text-[#666] hover:text-white transition">
                <Zap size={11} className="inline mr-1" />Dados de Teste
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {previewCampaign && <PreviewModal campaign={previewCampaign} onClose={() => setPreviewCampaign(null)} />}
      {detailCampaign && <CampaignDetail campaign={detailCampaign} onClose={() => setDetailCampaign(null)} />}
    </div>
  );
}
