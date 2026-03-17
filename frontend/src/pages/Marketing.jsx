import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Plus, Megaphone, Sparkles, Play, Pause, FileText, TrendingUp, Users, Send, BarChart3, Clock, Trash2, Zap, Lock, LayoutGrid, List, Eye, X, Image, CalendarDays, DollarSign, ChevronRight, Download, ExternalLink, Globe, Phone, Mail, Maximize2, Copy, Heart, MessageCircle, Bookmark, Share2, MoreHorizontal, ChevronLeft, Check, Film, RefreshCw, Target } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/* ── i18n labels ── */
const L = (lang) => {
  const t = {
    pt: {
      seasonal: 'Sazonal', draft: 'Rascunho', active: 'Ativa', paused: 'Pausada', completed: 'Concluida',
      campaigns: 'Campanhas', sent: 'Enviadas', openRate: 'Taxa Abertura', conversions: 'Conversoes',
      createWithStudio: 'Criar com AI Studio', newBtn: 'Nova', cancel: 'Cancelar', create: 'Criar',
      createCampaign: 'Criar Campanha', testData: 'Dados de Teste', noCampaigns: 'Nenhuma campanha encontrada',
      campaignName: 'Nome da campanha...', title: 'Marketing & Campanhas',
      templates: 'Templates', readyTemplates: 'Templates Prontos',
      upgradeEnterprise: 'Upgrade para Enterprise', studioDesc: '4 agentes IA especializados para criar campanhas completas.',
      all: 'Todas', overview: 'Visao Geral', content: 'Conteudo', results: 'Resultados',
      campaignArts: 'Artes da Campanha', campaignText: 'Texto da Campanha', noVisual: 'Sem conteudo visual disponivel',
      selectChannel: 'Selecione o Canal', delivered: 'Entregues', opens: 'Abertura', conversion: 'Conversao',
      cplByChannel: 'Custo por Lead por Canal', schedule: 'Cronograma de Publicacao', messageFlow: 'Fluxo de Mensagens',
      immediate: 'Imediato', start: 'Inicio', end: 'Fim', noEndDate: 'Sem data de encerramento',
      sends: 'Envios', clicks: 'Cliques', notSent: 'Campanha ainda nao foi enviada. Ative para comecar a coletar resultados.',
      copied: 'Copiado!', deleteCampaign: 'Excluir campanha', details: 'Detalhes',
      created: 'Campanha criada!', activated: 'Campanha ativada!', paused_toast: 'Campanha pausada',
      deleted: 'Campanha excluida!', loadError: 'Erro ao carregar templates', error: 'Erro',
      testCreated: 'Dados de teste criados!', env: 'env', conv: 'conv',
      byChannel: 'Por Canal', video: 'Video',
      videoCommercial: 'Video Comercial', download: 'Baixar', downloadArts: 'Download das Artes',
      copyText: 'Texto para Copiar', allNetworks: 'Todas as Redes', copy: 'Copiar', noMessages: 'Sem mensagens',
      totalSent: 'Total Enviado', openings: 'Aberturas', avgCpl: 'CPL Medio', performanceByChannel: 'Performance por Canal',
      regenVideo: 'Gerar Video', regenVideoDesc: 'Clique para gerar o video comercial desta campanha', regenerating: 'Gerando video...', videoGenStarted: 'Geracao de video iniciada!',
      cta: 'Comece Agora', learnMore: 'Saiba mais sobre',
      sponsored: 'Patrocinado', format: 'Formato',
      editCopy: 'Editar Texto', saveCopy: 'Salvar', cancelEdit: 'Cancelar', copyUpdated: 'Texto atualizado!',
      regenImage: 'Regenerar Imagem', regenImageFeedback: 'Descreva o ajuste desejado...', regenImageStarted: 'Regenerando imagem...',
      cloneLanguage: 'Clonar em outro idioma', cloneStarted: 'Campanha clonada! Gerando em', selectLanguage: 'Selecione o idioma',
      editing: 'Editando',
    },
    en: {
      seasonal: 'Seasonal', draft: 'Draft', active: 'Active', paused: 'Paused', completed: 'Completed',
      campaigns: 'Campaigns', sent: 'Sent', openRate: 'Open Rate', conversions: 'Conversions',
      createWithStudio: 'Create with AI Studio', newBtn: 'New', cancel: 'Cancel', create: 'Create',
      createCampaign: 'Create Campaign', testData: 'Test Data', noCampaigns: 'No campaigns found',
      campaignName: 'Campaign name...', title: 'Marketing & Campaigns',
      templates: 'Templates', readyTemplates: 'Ready Templates',
      upgradeEnterprise: 'Upgrade to Enterprise', studioDesc: '4 specialized AI agents to create complete campaigns.',
      all: 'All', overview: 'Overview', content: 'Content', results: 'Results',
      campaignArts: 'Campaign Creatives', campaignText: 'Campaign Copy', noVisual: 'No visual content available',
      selectChannel: 'Select Channel', delivered: 'Delivered', opens: 'Opens', conversion: 'Conversion',
      cplByChannel: 'Cost per Lead by Channel', schedule: 'Publishing Schedule', messageFlow: 'Message Flow',
      immediate: 'Immediate', start: 'Start', end: 'End', noEndDate: 'No end date',
      sends: 'Sends', clicks: 'Clicks', notSent: 'Campaign not yet sent. Activate to start collecting results.',
      copied: 'Copied!', deleteCampaign: 'Delete campaign', details: 'Details',
      created: 'Campaign created!', activated: 'Campaign activated!', paused_toast: 'Campaign paused',
      deleted: 'Campaign deleted!', loadError: 'Error loading templates', error: 'Error',
      testCreated: 'Test data created!', env: 'sent', conv: 'conv',
      byChannel: 'By Channel', video: 'Video',
      videoCommercial: 'Commercial Video', download: 'Download', downloadArts: 'Download Creatives',
      copyText: 'Copy Text', allNetworks: 'All Networks', copy: 'Copy', noMessages: 'No messages',
      totalSent: 'Total Sent', openings: 'Opens', avgCpl: 'Average CPL', performanceByChannel: 'Performance by Channel',
      regenVideo: 'Generate Video', regenVideoDesc: 'Click to generate the commercial video for this campaign', regenerating: 'Generating video...', videoGenStarted: 'Video generation started!',
      cta: 'Start Now', learnMore: 'Learn more about',
      sponsored: 'Sponsored', format: 'Format',
      editCopy: 'Edit Copy', saveCopy: 'Save', cancelEdit: 'Cancel', copyUpdated: 'Copy updated!',
      regenImage: 'Regenerate Image', regenImageFeedback: 'Describe the adjustment...', regenImageStarted: 'Regenerating image...',
      cloneLanguage: 'Clone to another language', cloneStarted: 'Campaign cloned! Generating in', selectLanguage: 'Select language',
      editing: 'Editing',
    },
    es: {
      seasonal: 'Estacional', draft: 'Borrador', active: 'Activa', paused: 'Pausada', completed: 'Completada',
      campaigns: 'Campanas', sent: 'Enviadas', openRate: 'Tasa Apertura', conversions: 'Conversiones',
      createWithStudio: 'Crear con AI Studio', newBtn: 'Nueva', cancel: 'Cancelar', create: 'Crear',
      createCampaign: 'Crear Campana', testData: 'Datos de Prueba', noCampaigns: 'No se encontraron campanas',
      campaignName: 'Nombre de campana...', title: 'Marketing & Campanas',
      templates: 'Plantillas', readyTemplates: 'Plantillas Listas',
      upgradeEnterprise: 'Upgrade a Enterprise', studioDesc: '4 agentes IA especializados para crear campanas completas.',
      all: 'Todas', overview: 'General', content: 'Contenido', results: 'Resultados',
      campaignArts: 'Artes de Campana', campaignText: 'Texto de Campana', noVisual: 'Sin contenido visual disponible',
      selectChannel: 'Seleccionar Canal', delivered: 'Entregadas', opens: 'Apertura', conversion: 'Conversion',
      cplByChannel: 'Costo por Lead por Canal', schedule: 'Cronograma de Publicacion', messageFlow: 'Flujo de Mensajes',
      immediate: 'Inmediato', start: 'Inicio', end: 'Fin', noEndDate: 'Sin fecha de cierre',
      sends: 'Envios', clicks: 'Clics', notSent: 'Campana aun no fue enviada. Active para empezar a recolectar resultados.',
      copied: 'Copiado!', deleteCampaign: 'Eliminar campana', details: 'Detalles',
      created: 'Campana creada!', activated: 'Campana activada!', paused_toast: 'Campana pausada',
      deleted: 'Campana eliminada!', loadError: 'Error al cargar plantillas', error: 'Error',
      testCreated: 'Datos de prueba creados!', env: 'env', conv: 'conv',
      byChannel: 'Por Canal', video: 'Video',
      videoCommercial: 'Video Comercial', download: 'Descargar', downloadArts: 'Descargar Artes',
      copyText: 'Texto para Copiar', allNetworks: 'Todas las Redes', copy: 'Copiar', noMessages: 'Sin mensajes',
      totalSent: 'Total Enviado', openings: 'Aperturas', avgCpl: 'CPL Promedio', performanceByChannel: 'Performance por Canal',
      regenVideo: 'Generar Video', regenVideoDesc: 'Haga clic para generar el video comercial de esta campana', regenerating: 'Generando video...', videoGenStarted: 'Generacion de video iniciada!',
      cta: 'Empieza Ahora', learnMore: 'Mas informacion sobre',
      sponsored: 'Patrocinado', format: 'Formato',
      editCopy: 'Editar Texto', saveCopy: 'Guardar', cancelEdit: 'Cancelar', copyUpdated: 'Texto actualizado!',
      regenImage: 'Regenerar Imagen', regenImageFeedback: 'Describe el ajuste...', regenImageStarted: 'Regenerando imagen...',
      cloneLanguage: 'Clonar en otro idioma', cloneStarted: 'Campana clonada! Generando en', selectLanguage: 'Seleccione idioma',
      editing: 'Editando',
    },
  };
  const base = lang?.startsWith('pt') ? 'pt' : lang?.startsWith('es') ? 'es' : 'en';
  return t[base] || t.en;
};

const TYPE_META = {
  drip: { label: 'Drip', color: '#C9A84C' },
  nurture: { label: 'Nurture', color: '#7CB9E8' },
  promotional: { label: 'Promo', color: '#E8A87C' },
  seasonal: { label_key: 'seasonal', color: '#A87CE8' },
  ai_pipeline: { label: 'AI Pipeline', color: '#4CAF50' },
};

const STATUS_META = {
  draft: { label_key: 'draft', color: '#666' },
  active: { label_key: 'active', color: '#4CAF50' },
  paused: { label_key: 'paused', color: '#FF9800' },
  completed: { label_key: 'completed', color: '#2196F3' },
};

const CHANNEL_COLORS = {
  whatsapp: '#25D366', instagram: '#E4405F', facebook: '#1877F2',
  telegram: '#26A5E4', email: '#C9A84C', sms: '#FF9800', multi: '#888', tiktok: '#000000',
  google_ads: '#4285F4',
};

const GOLD = '#C9A84C';

/* ── Channel Icons (SVG) ── */
function ChannelIcon({ channel, active, size = 16 }) {
  const color = active ? (CHANNEL_COLORS[channel] || '#888') : '#555';
  const s = size;
  const icons = {
    whatsapp: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>,
    instagram: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>,
    facebook: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>,
    telegram: <svg width={s} height={s} viewBox="0 0 24 24" fill={color}><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0a12 12 0 00-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>,
    email: <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>,
    sms: <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>,
    tiktok: <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5"/></svg>,
    google_ads: <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>,
  };
  return <span title={channel} className="inline-flex">{icons[channel] || <span className="w-3 h-3 rounded-full" style={{backgroundColor: color}} />}</span>;
}

/* All available platforms for showing on cards */
const ALL_PLATFORMS = ['whatsapp', 'instagram', 'facebook', 'tiktok', 'google_ads', 'telegram', 'email', 'sms'];

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

/* Helper to resolve meta label */
function metaLabel(meta, labels) {
  if (meta.label_key) return labels[meta.label_key] || meta.label_key;
  return meta.label || '';
}

/* ── Video Lightbox ── */
function VideoLightbox({ videoUrl, onClose, labels }) {
  useEffect(() => {
    document.querySelectorAll('video').forEach(v => {
      if (!v.dataset.testid?.includes('lightbox')) v.pause();
    });
  }, []);
  return (
    <div data-testid="video-lightbox" className="fixed inset-0 z-[70] bg-black/95 flex items-center justify-center p-4" onClick={onClose}>
      <div className="relative w-full max-w-4xl" onClick={e => e.stopPropagation()}>
        <button onClick={onClose} data-testid="video-lightbox-close"
          className="absolute -top-3 -right-3 z-10 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] transition">
          <X size={16} className="text-white" />
        </button>
        <div className="rounded-xl overflow-hidden border border-[#333] bg-black shadow-2xl">
          <video src={videoUrl} controls playsInline autoPlay className="w-full" data-testid="video-lightbox-player" style={{ maxHeight: '80vh' }} />
        </div>
        <div className="flex items-center justify-between mt-3">
          <span className="text-[9px] text-[#555] bg-[#111] px-2 py-1 rounded">Sora 2</span>
          <a href={videoUrl} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-[#1A1A1A] border border-[#333] text-[11px] text-white hover:bg-[#222] transition">
            <Download size={12} /> {labels?.download || 'Baixar'}
          </a>
        </div>
      </div>
    </div>
  );
}

/* ── Preview Modal ── */
function PreviewModal({ campaign, onClose, labels }) {
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
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">{labels.campaignArts}</p>
              <div className="grid grid-cols-3 gap-2">
                {images.map((url, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className="rounded-lg overflow-hidden border border-[#1E1E1E] relative group text-left hover:border-[#C9A84C]/30 transition">
                    <img src={resolveImageUrl(url)} alt={`Art ${i + 1}`} className="w-full aspect-square object-cover" />
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
              <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">{labels.campaignText}</p>
              <pre className="text-[11px] text-[#ccc] whitespace-pre-wrap leading-relaxed font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A]">{cleanCampaignText(mainText)}</pre>
            </div>
          )}
          {images.length === 0 && !mainText && (
            <p className="text-[11px] text-[#555] text-center py-6">{labels.noVisual}</p>
          )}
        </div>
        {lightboxIdx !== null && (
          <div className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4" onClick={() => setLightboxIdx(null)}>
            <div className="relative max-w-2xl w-full" onClick={e => e.stopPropagation()}>
              <button onClick={() => setLightboxIdx(null)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333]">
                <X size={14} className="text-white" />
              </button>
              <img src={resolveImageUrl(images[lightboxIdx])} alt="" className="w-full rounded-xl" />
              <div className="flex gap-2 mt-2 justify-center">
                {images.map((u, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className={`h-10 w-10 rounded-lg overflow-hidden border-2 ${i === lightboxIdx ? 'border-[#C9A84C]' : 'border-[#333] opacity-50'}`}>
                    <img src={resolveImageUrl(u)} alt="" className="w-full h-full object-cover" />
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
function CampaignDetail({ campaign: initialCampaign, onClose, labels }) {
  const [campaign, setCampaign] = useState(initialCampaign);
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
  const [selectedChannel, setSelectedChannel] = useState(channels[0] || 'whatsapp');
  const videoUrl = stats.video_url || '';
  const pipelineId = stats.pipeline_id || '';
  const [regenLoading, setRegenLoading] = useState(false);
  const [showVideoLightbox, setShowVideoLightbox] = useState(false);
  const [showChannelVideo, setShowChannelVideo] = useState(false);

  const refreshCampaign = () => {
    axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/${initialCampaign.id}`)
      .then(res => setCampaign(res.data))
      .catch(() => {});
  };

  useEffect(() => {
    refreshCampaign();
  }, [initialCampaign.id]);

  // Poll for video when regenerating
  useEffect(() => {
    if (!regenLoading) return;
    const interval = setInterval(() => {
      axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/${initialCampaign.id}`)
        .then(res => {
          setCampaign(res.data);
          if (res.data?.stats?.video_url) {
            setRegenLoading(false);
            toast.success(labels.videoCommercial + ' OK!');
          }
        }).catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, [regenLoading, initialCampaign.id]);

  const regenerateVideo = async () => {
    if (!pipelineId) return;
    setRegenLoading(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/${pipelineId}/regenerate-video`);
      toast.success(labels.videoGenStarted);
    } catch (e) {
      toast.error(e.response?.data?.detail || labels.error);
      setRegenLoading(false);
    }
  };

  // Edit copy state
  const [editingCopy, setEditingCopy] = useState(false);
  const [editCopyText, setEditCopyText] = useState('');
  const [savingCopy, setSavingCopy] = useState(false);

  const startEditCopy = () => {
    const fullCopy = stats.full_copy || messages.map(m => m.content).join('\n\n---\n\n');
    setEditCopyText(fullCopy);
    setEditingCopy(true);
  };

  const saveCopy = async () => {
    if (!pipelineId) return;
    setSavingCopy(true);
    try {
      await axios.put(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/${pipelineId}/update-copy`, { copy_text: editCopyText });
      toast.success(labels.copyUpdated);
      setEditingCopy(false);
      refreshCampaign();
    } catch (e) {
      toast.error(e.response?.data?.detail || labels.error);
    } finally {
      setSavingCopy(false);
    }
  };

  // Regenerate image state
  const [regenImageIdx, setRegenImageIdx] = useState(null);
  const [regenImageFeedback, setRegenImageFeedback] = useState('');
  const [regenImageLoading, setRegenImageLoading] = useState(false);
  const [regenCountdown, setRegenCountdown] = useState(0);

  const regenerateImage = async (idx) => {
    if (!pipelineId) return;
    setRegenImageLoading(true);
    setRegenCountdown(30);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/${pipelineId}/regenerate-image`, {
        image_index: idx,
        feedback: regenImageFeedback,
      });
      toast.success(labels.regenImageStarted);
      setRegenImageIdx(null);
      setRegenImageFeedback('');
      // Countdown timer
      const countdownInterval = setInterval(() => {
        setRegenCountdown(prev => {
          if (prev <= 1) { clearInterval(countdownInterval); return 0; }
          return prev - 1;
        });
      }, 1000);
      // Poll for updated image
      const pollInterval = setInterval(() => {
        refreshCampaign();
      }, 5000);
      setTimeout(() => { clearInterval(pollInterval); setRegenImageLoading(false); setRegenCountdown(0); }, 60000);
    } catch (e) {
      toast.error(e.response?.data?.detail || labels.error);
      setRegenImageLoading(false);
      setRegenCountdown(0);
    }
  };

  // Clone language state
  const [showCloneModal, setShowCloneModal] = useState(false);
  const [cloneLoading, setCloneLoading] = useState(false);
  const [shareImgIdx, setShareImgIdx] = useState(0);
  const [shareText, setShareText] = useState('');
  const [shareIsVideo, setShareIsVideo] = useState(false);

  const cloneCampaign = async (targetLang) => {
    if (!pipelineId) return;
    setCloneLoading(true);
    try {
      const res = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/${pipelineId}/clone-language`, { target_language: targetLang });
      const langLabel = { pt: 'Portugues', en: 'English', es: 'Espanol', fr: 'Francais', de: 'Deutsch' }[targetLang] || targetLang;
      toast.success(`${labels.cloneStarted} ${langLabel}!`);
      setShowCloneModal(false);
      onClose();
    } catch (e) {
      toast.error(e.response?.data?.detail || labels.error);
    } finally {
      setCloneLoading(false);
    }
  };

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
      toast.success(labels.copied);
    } catch { toast.error(labels.error); }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-3" onClick={onClose}>
      <div data-testid="campaign-detail-modal" className="bg-[#0A0A0A] border border-[#1A1A1A] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="px-4 py-3 border-b border-[#111] shrink-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: type.color, backgroundColor: `${type.color}15` }}>{metaLabel(type, labels)}</span>
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: status.color, backgroundColor: `${status.color}15` }}>{metaLabel(status, labels)}</span>
            <span className="ml-auto text-[#555] hover:text-white cursor-pointer" onClick={onClose}><X size={16} /></span>
          </div>
          <h2 className="text-base font-bold text-white">{campaign.name}</h2>
          <div className="flex items-center gap-3 mt-1.5">
            {startDate && <span className="text-[9px] text-[#555] flex items-center gap-1"><CalendarDays size={9} />{labels.start}: {new Date(startDate).toLocaleDateString()}</span>}
            {endDate && <span className="text-[9px] text-[#555] flex items-center gap-1"><CalendarDays size={9} />{labels.end}: {new Date(endDate).toLocaleDateString()}</span>}
            {!endDate && <span className="text-[9px] text-[#444]">{labels.noEndDate}</span>}
            {pipelineId && (
              <button data-testid="clone-language-btn" onClick={() => setShowCloneModal(!showCloneModal)}
                className="ml-auto flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[#C9A84C]/30 text-[8px] text-[#C9A84C] font-semibold hover:bg-[#C9A84C]/10 transition">
                <Globe size={10} /> {labels.cloneLanguage}
              </button>
            )}
          </div>
          {/* Clone Language Modal */}
          {showCloneModal && (
            <div data-testid="clone-language-modal" className="mt-2 p-3 rounded-xl bg-[#111] border border-[#C9A84C]/20">
              <p className="text-[9px] text-[#C9A84C] font-bold mb-2">{labels.selectLanguage}</p>
              <div className="flex gap-2 flex-wrap">
                {[
                  { code: 'pt', label: 'Portugues', flag: 'BR' },
                  { code: 'en', label: 'English', flag: 'US' },
                  { code: 'es', label: 'Espanol', flag: 'ES' },
                  { code: 'fr', label: 'Francais', flag: 'FR' },
                  { code: 'de', label: 'Deutsch', flag: 'DE' },
                  { code: 'it', label: 'Italiano', flag: 'IT' },
                ].map(l => (
                  <button key={l.code} data-testid={`clone-lang-${l.code}`}
                    onClick={() => cloneCampaign(l.code)} disabled={cloneLoading}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#1E1E1E] bg-[#0A0A0A] text-[10px] text-white hover:border-[#C9A84C]/40 hover:bg-[#C9A84C]/5 transition disabled:opacity-50">
                    <span className="text-[8px] text-[#555] font-bold">{l.flag}</span>
                    {l.label}
                    {cloneLoading && <RefreshCw size={9} className="animate-spin ml-1" />}
                  </button>
                ))}
              </div>
            </div>
          )}
          {/* Tabs */}
          <div className="flex gap-1 mt-2.5">
            {[
              { id: 'overview', label: labels.overview },
              { id: 'content', label: labels.content },
              { id: 'results', label: labels.results },
            ].map(t => (
              <button key={t.id} onClick={() => setTab(t.id)} data-testid={`detail-tab-${t.id}`}
                className={`px-3 py-1 rounded-lg text-[10px] font-semibold transition ${tab === t.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
          {tab === 'overview' && (
            <>
              {/* KPI Grid */}
              <div className="grid grid-cols-4 gap-2">
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-white">{stats.sent || 0}</p>
                  <p className="text-[8px] text-[#555]">{labels.sent}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-white">{deliveryRate}%</p>
                  <p className="text-[8px] text-[#555]">{labels.delivered}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-[#C9A84C]">{openRate}%</p>
                  <p className="text-[8px] text-[#555]">{labels.opens}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 text-center">
                  <p className="text-lg font-bold text-green-400">{convRate}%</p>
                  <p className="text-[8px] text-[#555]">{labels.conversion}</p>
                </div>
              </div>

              {/* Cost per Lead by Channel */}
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">{labels.cplByChannel}</p>
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
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1">{labels.schedule}</p>
                  <pre className="text-[10px] text-[#999] whitespace-pre-wrap font-sans bg-[#111] rounded-lg p-3 border border-[#1A1A1A] max-h-[200px] overflow-y-auto">{schedule.schedule_text}</pre>
                </div>
              )}

              {/* Steps/Messages Timeline */}
              {messages.length > 0 && (
                <div>
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">{labels.messageFlow}</p>
                  <div className="space-y-1.5">
                    {messages.map((m, i) => (
                      <div key={i} className="flex items-start gap-2 rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5">
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg shrink-0 text-[9px] font-bold text-black" style={{ backgroundColor: CHANNEL_COLORS[m.channel] || '#888' }}>{i + 1}</div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="text-[9px] font-medium capitalize" style={{ color: CHANNEL_COLORS[m.channel] || '#888' }}>{m.channel}</span>
                            <span className="text-[8px] text-[#444]">{m.delay_hours === 0 ? labels.immediate : `+${m.delay_hours}h`}</span>
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
              {/* Channel Selector Header with Format Badges */}
              <div data-testid="channel-selector-header">
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-2">{labels.selectChannel}</p>
                <div className="flex gap-1.5 flex-wrap">
                  {channels.map(ch => {
                    const FORMAT_BADGE = {
                      whatsapp: '1:1', instagram: '1:1', facebook: '16:9',
                      tiktok: '9:16', google_ads: '1.91:1', telegram: '16:9', sms: '-'
                    };
                    return (
                    <button key={ch} onClick={() => setSelectedChannel(ch)} data-testid={`channel-select-${ch}`}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border transition-all ${
                        selectedChannel === ch
                          ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10 shadow-[0_0_10px_rgba(201,168,76,0.1)]'
                          : 'border-[#1A1A1A] bg-[#111] hover:border-[#333]'
                      }`}>
                      <ChannelIcon channel={ch} active={selectedChannel === ch} size={14} />
                      <span className={`text-[9px] font-semibold capitalize ${selectedChannel === ch ? 'text-[#C9A84C]' : 'text-[#555]'}`}>
                        {ch === 'google_ads' ? 'Google Ads' : ch}
                      </span>
                      <span className="text-[7px] px-1 py-0.5 rounded bg-[#1A1A1A] text-[#666]">{FORMAT_BADGE[ch] || '1:1'}</span>
                    </button>
                    );
                  })}
                </div>
              </div>

              {/* Selected Channel Mockup */}
              <div className="space-y-3" data-testid={`mockup-${selectedChannel}-content`}>
                {(() => {
                  const channel = selectedChannel;
                  // Use platform-specific variant if available
                  const platformVariants = stats.platform_variants || {};
                  const channelImages = platformVariants[channel] || images;
                  const imgUrl = channelImages[0] || images[0];
                  const imgSrc = imgUrl ? resolveImageUrl(imgUrl) : null;
                  const channelMsg = messages.find(m => m.channel === channel);
                  const copyText_ch = cleanCampaignText(channelMsg?.content || messages[0]?.content || '');
                  const brandName = campaign.name?.split(' - ')[0]?.split(' ').slice(0, 3).join(' ') || 'Brand';
                  const handle = brandName.toLowerCase().replace(/\s+/g, '');
                  // Per-channel video
                  const videoVariants = stats.video_variants || {};
                  const channelVideo = videoVariants[channel] || videoUrl;
                  // Toggle for image/video
                  const MediaToggle = () => (channelVideo && imgSrc) ? (
                    <div className="flex gap-1 mb-2 max-w-[340px] mx-auto">
                      <button onClick={() => setShowChannelVideo(false)} className={`text-[8px] px-2 py-1 rounded ${!showChannelVideo ? 'bg-[#C9A84C]/20 text-[#C9A84C] border border-[#C9A84C]/30' : 'bg-[#111] text-[#555] border border-[#1A1A1A]'}`} data-testid={`toggle-image-${channel}`}>Imagem</button>
                      <button onClick={() => setShowChannelVideo(true)} className={`text-[8px] px-2 py-1 rounded ${showChannelVideo ? 'bg-[#C9A84C]/20 text-[#C9A84C] border border-[#C9A84C]/30' : 'bg-[#111] text-[#555] border border-[#1A1A1A]'}`} data-testid={`toggle-video-${channel}`}>Video</button>
                    </div>
                  ) : null;
                  // Format badge for channel
                  const FORMAT_SIZES = {
                    whatsapp: '1:1 · 720x720', instagram: '1:1 · 1080x1080', facebook: '16:9 · 1280x720',
                    tiktok: '9:16 · 720x1280', google_ads: '16:9 · 1344x768', telegram: '16:9 · 1280x720',
                    email: '16:9 · 1280x720', sms: '9:16 · 720x1280'
                  };

                  if (channel === 'whatsapp') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[340px] mx-auto">
                        <div className="bg-[#075E54] rounded-t-xl px-3 py-2 flex items-center gap-2">
                          <ChevronLeft size={14} className="text-white/70" />
                          <div className="w-6 h-6 rounded-full bg-[#C9A84C]/20 flex items-center justify-center text-[8px] text-[#C9A84C] font-bold">{brandName[0]}</div>
                          <div className="flex-1"><p className="text-[10px] font-semibold text-white">{brandName}</p><p className="text-[7px] text-white/50">online</p></div>
                        </div>
                        <div className="bg-[#0B141A] px-2.5 py-3 min-h-[200px] rounded-b-xl">
                          <div className="max-w-[85%] ml-auto">
                            {showChannelVideo && channelVideo ? (
                              <video src={channelVideo} controls playsInline className="w-full rounded-lg mb-1 aspect-square object-cover" data-testid="whatsapp-video" />
                            ) : imgSrc ? (
                              <img src={imgSrc} alt="" className="w-full rounded-lg mb-1 aspect-square object-cover" />
                            ) : null}
                            <div className="bg-[#005C4B] rounded-xl rounded-tr-none px-3 py-2">
                              <p className="text-[9px] text-[#E9EDEF] leading-relaxed whitespace-pre-wrap line-clamp-[12]">{copyText_ch}</p>
                              <p className="text-[6px] text-[#ffffff40] text-right mt-1">10:30 ✓✓</p>
                            </div>
                          </div>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.whatsapp}</p>
                    </div>
                  );

                  if (channel === 'instagram') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[340px] mx-auto bg-black rounded-xl overflow-hidden border border-[#262626]">
                        <div className="flex items-center gap-2 px-3 py-2">
                          <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 p-[2px]">
                            <div className="w-full h-full rounded-full bg-black flex items-center justify-center text-[7px] text-white font-bold">{brandName[0]}</div>
                          </div>
                          <p className="text-[10px] font-semibold text-white flex-1">{handle}</p>
                          <MoreHorizontal size={12} className="text-white/50" />
                        </div>
                        {showChannelVideo && channelVideo ? (
                          <video src={channelVideo} controls playsInline className="w-full aspect-square object-cover" data-testid="instagram-video" />
                        ) : imgSrc ? (
                          <img src={imgSrc} alt="" className="w-full aspect-square object-cover" />
                        ) : null}
                        <div className="px-3 py-2">
                          <div className="flex items-center gap-3 mb-1.5">
                            <Heart size={18} className="text-white" /><MessageCircle size={18} className="text-white" /><Send size={18} className="text-white" /><Bookmark size={18} className="text-white ml-auto" />
                          </div>
                          <p className="text-[9px] text-white/60 mb-1">1,247 likes</p>
                          <p className="text-[9px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap line-clamp-6"><span className="font-bold">{handle}</span> {copyText_ch}</p>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.instagram}</p>
                    </div>
                  );

                  if (channel === 'facebook') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[340px] mx-auto bg-[#242526] rounded-xl overflow-hidden border border-[#3A3B3C]">
                        <div className="flex items-center gap-2 px-3 py-2">
                          <div className="w-7 h-7 rounded-full bg-[#1877F2] flex items-center justify-center text-[9px] text-white font-bold">{brandName[0]}</div>
                          <div className="flex-1"><p className="text-[10px] font-semibold text-[#E4E6EB]">{brandName}</p><p className="text-[7px] text-[#B0B3B8]">{labels.sponsored || 'Patrocinado'}</p></div>
                          <MoreHorizontal size={12} className="text-[#B0B3B8]" />
                        </div>
                        <p className="px-3 pb-2 text-[9px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap line-clamp-4">{copyText_ch}</p>
                        {showChannelVideo && channelVideo ? (
                          <video src={channelVideo} controls playsInline className="w-full aspect-video object-cover" data-testid="facebook-video" />
                        ) : imgSrc ? (
                          <img src={imgSrc} alt="" className="w-full aspect-video object-cover" />
                        ) : null}
                        <div className="px-3 py-2 border-t border-[#3A3B3C] flex items-center justify-around">
                          <span className="text-[9px] text-[#B0B3B8]">Curtir</span>
                          <span className="text-[9px] text-[#B0B3B8]">Comentar</span>
                          <span className="text-[9px] text-[#B0B3B8] flex items-center gap-0.5"><Share2 size={10} /> Compartilhar</span>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.facebook}</p>
                    </div>
                  );

                  if (channel === 'tiktok') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[240px] mx-auto bg-black rounded-2xl overflow-hidden border border-[#333] relative" style={{aspectRatio: '9/16'}}>
                        {showChannelVideo && channelVideo ? (
                          <video src={channelVideo} controls playsInline className="w-full h-full object-cover absolute inset-0" data-testid="tiktok-video" />
                        ) : imgSrc ? (
                          <img src={imgSrc} alt="" className="w-full h-full object-cover absolute inset-0" />
                        ) : null}
                        {!showChannelVideo && <>
                          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
                          <div className="absolute bottom-0 left-0 right-10 p-3">
                            <p className="text-[10px] font-bold text-white mb-1">@{handle}</p>
                            <p className="text-[8px] text-white/90 leading-relaxed line-clamp-3">{copyText_ch.substring(0, 150)}</p>
                            <p className="text-[7px] text-white/50 mt-1">#marketing #ia #agentZZ</p>
                          </div>
                          <div className="absolute right-2 bottom-20 flex flex-col items-center gap-3">
                            <div className="flex flex-col items-center"><Heart size={18} className="text-white" /><span className="text-[6px] text-white">24.5K</span></div>
                            <div className="flex flex-col items-center"><MessageCircle size={18} className="text-white" /><span className="text-[6px] text-white">1,234</span></div>
                            <div className="flex flex-col items-center"><Share2 size={18} className="text-white" /><span className="text-[6px] text-white">892</span></div>
                          </div>
                        </>}
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.tiktok}</p>
                    </div>
                  );

                  if (channel === 'google_ads') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[340px] mx-auto space-y-2">
                        <div className="bg-white rounded-xl overflow-hidden border border-[#ddd] p-3">
                          <div className="flex items-center gap-1 mb-1">
                            <span className="text-[8px] font-bold text-[#202124] bg-[#f1f3f4] px-1.5 py-0.5 rounded">Ad</span>
                            <span className="text-[9px] text-[#202124]">·</span>
                            <span className="text-[9px] text-[#202124]">{handle}.com</span>
                          </div>
                          <p className="text-[12px] font-medium text-[#1a0dab] leading-tight mb-0.5">{copyText_ch.split('\n')[0]?.substring(0, 60) || brandName}</p>
                          <p className="text-[9px] text-[#4d5156] leading-relaxed line-clamp-2">{copyText_ch.substring(0, 120)}...</p>
                        </div>
                        <div className="bg-white rounded-xl overflow-hidden border border-[#ddd]">
                          {showChannelVideo && channelVideo ? (
                            <video src={channelVideo} controls playsInline className="w-full aspect-[1.91/1] object-cover" data-testid="google-ads-video" />
                          ) : imgSrc ? (
                            <img src={imgSrc} alt="" className="w-full aspect-[1.91/1] object-cover" />
                          ) : null}
                          <div className="p-2.5 border-t border-[#eee]">
                            <div className="flex items-center gap-1 mb-0.5">
                              <span className="text-[7px] font-bold text-white bg-[#FBBC04] px-1 py-0.5 rounded">Ad</span>
                              <span className="text-[8px] text-[#70757a]">{handle}.com</span>
                            </div>
                            <p className="text-[10px] font-medium text-[#202124] line-clamp-1">{copyText_ch.split('\n')[0]?.substring(0, 50) || brandName}</p>
                          </div>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.google_ads}</p>
                    </div>
                  );

                  if (channel === 'telegram') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[340px] mx-auto">
                        <div className="bg-[#17212B] rounded-t-xl px-3 py-2 flex items-center gap-2">
                          <ChevronLeft size={14} className="text-[#6AB2F2]" />
                          <div className="w-6 h-6 rounded-full bg-[#6AB2F2] flex items-center justify-center text-[8px] text-white font-bold">{brandName[0]}</div>
                          <div className="flex-1"><p className="text-[10px] font-semibold text-white">{brandName}</p><p className="text-[7px] text-[#6AB2F2]">canal</p></div>
                        </div>
                        <div className="bg-[#0E1621] px-2.5 py-3 rounded-b-xl">
                          {showChannelVideo && channelVideo ? (
                            <video src={channelVideo} controls playsInline className="w-full rounded-lg mb-2 aspect-video object-cover" data-testid="telegram-video" />
                          ) : imgSrc ? (
                            <img src={imgSrc} alt="" className="w-full rounded-lg mb-2 aspect-video object-cover" />
                          ) : null}
                          <div className="bg-[#182533] rounded-xl px-3 py-2">
                            <p className="text-[9px] text-[#E4E6EB] leading-relaxed whitespace-pre-wrap line-clamp-[8]">{copyText_ch}</p>
                            <p className="text-[6px] text-[#6AB2F2] text-right mt-1">10:30</p>
                          </div>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.telegram}</p>
                    </div>
                  );

                  if (channel === 'email') return (
                    <div>
                      <MediaToggle />
                      <div className="w-full max-w-[340px] mx-auto bg-white rounded-xl overflow-hidden border border-[#ddd]">
                        <div className="bg-[#f8f9fa] px-3 py-2 border-b border-[#eee]">
                          <p className="text-[8px] text-[#5f6368]">De: {brandName} &lt;contato@{handle}.com&gt;</p>
                          <p className="text-[10px] font-semibold text-[#202124] mt-0.5">{copyText_ch.split('\n')[0]?.substring(0, 50) || brandName}</p>
                        </div>
                        {showChannelVideo && channelVideo ? (
                          <video src={channelVideo} controls playsInline className="w-full aspect-video object-cover" data-testid="email-video" />
                        ) : imgSrc ? (
                          <img src={imgSrc} alt="" className="w-full aspect-video object-cover" />
                        ) : null}
                        <div className="px-3 py-3">
                          <p className="text-[9px] text-[#202124] leading-relaxed whitespace-pre-wrap line-clamp-6">{copyText_ch}</p>
                          <button className="mt-2 px-4 py-1.5 bg-[#C9A84C] text-white text-[9px] font-semibold rounded-lg">{labels.cta || 'Saiba Mais'}</button>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.email}</p>
                    </div>
                  );

                  if (channel === 'sms') return (
                    <div>
                      <div className="w-full max-w-[260px] mx-auto bg-[#1C1C1E] rounded-2xl overflow-hidden border border-[#333]">
                        <div className="bg-[#2C2C2E] px-3 py-2 text-center">
                          <p className="text-[10px] font-semibold text-white">{brandName}</p>
                          <p className="text-[7px] text-[#8E8E93]">SMS</p>
                        </div>
                        <div className="px-3 py-3 min-h-[150px]">
                          <div className="max-w-[85%] bg-[#3A3A3C] rounded-2xl rounded-tl-none px-3 py-2">
                            <p className="text-[9px] text-white leading-relaxed whitespace-pre-wrap line-clamp-[10]">{copyText_ch}</p>
                            <p className="text-[6px] text-[#8E8E93] text-right mt-1">10:30</p>
                          </div>
                        </div>
                      </div>
                      <p className="text-center text-[7px] text-[#444] mt-1">{FORMAT_SIZES.sms}</p>
                    </div>
                  );

                  return (
                    <div>
                      <div className="w-full max-w-[340px] mx-auto bg-[#111] rounded-xl border border-[#1A1A1A] p-3">
                        {imgSrc && <img src={imgSrc} alt="" className="w-full rounded-lg mb-2" />}
                        <p className="text-[9px] text-[#ccc] whitespace-pre-wrap line-clamp-6">{copyText_ch}</p>
                      </div>
                    </div>
                  );
                })()}
              </div>

              {/* ── UNIFIED SHARE AREA ── Select media + text + share */}

              {/* Media Selector - Images & Video */}
              {(images.length > 0 || videoUrl) && (
                <div data-testid="share-media-selector">
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-2">Selecionar Midia</p>
                  <div className="grid grid-cols-3 gap-2">
                    {images.map((url, i) => (
                      <button key={`img-${i}`} data-testid={`share-media-img-${i}`}
                        onClick={() => { setShareImgIdx(i); setShareIsVideo(false); }}
                        className={`rounded-xl overflow-hidden border-2 transition-all relative group ${!shareIsVideo && shareImgIdx === i
                          ? 'border-[#C9A84C] shadow-[0_0_12px_rgba(201,168,76,0.25)] scale-[1.02]'
                          : 'border-[#1A1A1A] opacity-70 hover:opacity-100 hover:border-[#333]'}`}>
                        <img src={resolveImageUrl(url)} alt={`Design ${i + 1}`} className="w-full aspect-square object-cover" />
                        {/* Selection indicator */}
                        {!shareIsVideo && shareImgIdx === i && (
                          <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-[#C9A84C] flex items-center justify-center">
                            <Check size={10} className="text-black" />
                          </div>
                        )}
                        {/* Regen button */}
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1 flex justify-between items-center">
                          <span className="text-[8px] text-white font-bold">Design {i + 1}</span>
                          <div className="flex items-center gap-1.5">
                            <button onClick={e => { e.stopPropagation(); setRegenImageIdx(i); setRegenImageFeedback(''); }}
                              data-testid={`regen-image-${i}`}
                              className="text-[#C9A84C] hover:text-[#D4B85C] transition" title={labels.regenImage}>
                              <RefreshCw size={10} />
                            </button>
                            <a href={resolveImageUrl(url)} target="_blank" rel="noopener noreferrer" onClick={e => e.stopPropagation()} className="text-white/60 hover:text-white">
                              <Download size={10} />
                            </a>
                          </div>
                        </div>
                        {regenImageIdx === i && (
                          <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-2 z-10" onClick={e => e.stopPropagation()}>
                            <p className="text-[8px] text-[#C9A84C] font-bold mb-1.5">{labels.regenImage}</p>
                            <textarea data-testid={`regen-feedback-${i}`}
                              value={regenImageFeedback} onChange={e => setRegenImageFeedback(e.target.value)}
                              placeholder={labels.regenImageFeedback}
                              className="w-full text-[9px] bg-[#1A1A1A] border border-[#333] rounded-lg p-2 text-white placeholder-[#555] resize-none"
                              rows={2} />
                            <div className="flex gap-1.5 mt-1.5 w-full">
                              <button onClick={(e) => { e.stopPropagation(); setRegenImageIdx(null); }}
                                className="flex-1 text-[8px] py-1 rounded-lg border border-[#333] text-[#888] hover:text-white transition">
                                {labels.cancelEdit}
                              </button>
                              <button data-testid={`regen-image-confirm-${i}`} onClick={(e) => { e.stopPropagation(); regenerateImage(i); }} disabled={regenImageLoading}
                                className="flex-1 text-[8px] py-1 rounded-lg bg-[#C9A84C] text-black font-bold hover:bg-[#D4B85C] transition disabled:opacity-50">
                                {regenImageLoading ? <RefreshCw size={10} className="animate-spin mx-auto" /> : labels.regenImage}
                              </button>
                            </div>
                          </div>
                        )}
                        {regenImageLoading && regenImageIdx === null && (
                          <div className="absolute inset-0 bg-black/70 flex flex-col items-center justify-center z-10">
                            <RefreshCw size={16} className="text-[#C9A84C] animate-spin mb-1" />
                            {regenCountdown > 0 && <span className="text-[10px] text-[#C9A84C] font-bold">{regenCountdown}s</span>}
                          </div>
                        )}
                      </button>
                    ))}
                    {/* Video thumbnail */}
                    {videoUrl && (
                      <button data-testid="share-media-video"
                        onClick={() => setShareIsVideo(true)}
                        className={`rounded-xl overflow-hidden border-2 transition-all relative ${shareIsVideo
                          ? 'border-[#C9A84C] shadow-[0_0_12px_rgba(201,168,76,0.25)] scale-[1.02]'
                          : 'border-[#1A1A1A] opacity-70 hover:opacity-100 hover:border-[#333]'}`}>
                        <video src={videoUrl} className="w-full aspect-square object-cover" muted />
                        <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                          <div className="w-8 h-8 rounded-full bg-black/60 flex items-center justify-center">
                            <Play size={14} className="text-white ml-0.5" fill="white" />
                          </div>
                        </div>
                        {shareIsVideo && (
                          <div className="absolute top-1.5 right-1.5 w-5 h-5 rounded-full bg-[#C9A84C] flex items-center justify-center">
                            <Check size={10} className="text-black" />
                          </div>
                        )}
                        <div className="absolute bottom-0 left-0 right-0 bg-black/70 px-2 py-1">
                          <span className="text-[8px] text-white font-bold flex items-center gap-1"><Film size={8} /> Video</span>
                        </div>
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Text Area - Editable */}
              <div data-testid="share-text-area">
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[9px] text-[#555] uppercase tracking-wider">{labels.copyText}</p>
                  <div className="flex items-center gap-2">
                    {pipelineId && !editingCopy && (
                      <button data-testid="edit-copy-btn" onClick={startEditCopy}
                        className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-1">
                        <FileText size={9} /> {labels.editCopy}
                      </button>
                    )}
                    <button data-testid="share-copy-text" onClick={() => {
                      const t = shareText || cleanCampaignText(messages.find(m => m.channel === selectedChannel)?.content || messages[0]?.content || '');
                      navigator.clipboard?.writeText(t).then(() => toast.success(labels.copied)).catch(() => {
                        const ta = document.createElement('textarea'); ta.value = t; ta.style.position = 'fixed'; ta.style.opacity = '0';
                        document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
                        toast.success(labels.copied);
                      });
                    }} className="text-[8px] text-[#C9A84C] hover:underline flex items-center gap-0.5">
                      <Copy size={8} /> Copiar
                    </button>
                  </div>
                </div>
                {editingCopy ? (
                  <div data-testid="copy-editor" className="rounded-lg bg-[#111] border border-[#C9A84C]/30 p-3">
                    <div className="flex items-center gap-1.5 mb-2">
                      <FileText size={10} className="text-[#C9A84C]" />
                      <span className="text-[9px] text-[#C9A84C] font-bold">{labels.editing}</span>
                    </div>
                    <textarea data-testid="copy-editor-textarea"
                      value={editCopyText} onChange={e => setEditCopyText(e.target.value)}
                      className="w-full bg-[#0A0A0A] border border-[#1E1E1E] rounded-lg p-3 text-[10px] text-[#ccc] font-sans leading-relaxed resize-none focus:border-[#C9A84C]/50 focus:outline-none"
                      rows={12} />
                    <div className="flex gap-2 mt-2 justify-end">
                      <button data-testid="copy-cancel-btn" onClick={() => setEditingCopy(false)}
                        className="px-3 py-1.5 rounded-lg border border-[#333] text-[9px] text-[#888] hover:text-white transition">
                        {labels.cancelEdit}
                      </button>
                      <button data-testid="copy-save-btn" onClick={saveCopy} disabled={savingCopy}
                        className="px-4 py-1.5 rounded-lg bg-[#C9A84C] text-[9px] text-black font-bold hover:bg-[#D4B85C] transition disabled:opacity-50 flex items-center gap-1">
                        {savingCopy ? <RefreshCw size={10} className="animate-spin" /> : <Check size={10} />}
                        {labels.saveCopy}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[8px] font-semibold text-[#888]">
                        {messages.find(m => m.channel === selectedChannel)?.channel === 'multi' ? labels.allNetworks : selectedChannel}
                      </span>
                    </div>
                    <textarea data-testid="share-text-editor"
                      value={shareText || cleanCampaignText(messages.find(m => m.channel === selectedChannel)?.content || messages[0]?.content || '')}
                      onChange={e => setShareText(e.target.value)}
                      className="w-full bg-transparent text-[9px] text-[#ccc] leading-relaxed font-sans resize-none focus:outline-none"
                      rows={5} />
                  </div>
                )}
              </div>

              {/* ── SHARE BUTTONS ── */}
              <div data-testid="share-bar" className="rounded-xl border border-[#C9A84C]/20 bg-[#0D0D0D] p-2.5 -mt-1">
                <div className="flex items-center gap-2 mb-2">
                  <Send size={10} className="text-[#C9A84C]" />
                  <p className="text-[9px] font-bold text-white">Compartilhar</p>
                  <span className="text-[7px] text-[#555] ml-auto">
                    {shareIsVideo ? 'Video' : `Design ${shareImgIdx + 1}`}
                  </span>
                </div>
                <div className="flex gap-1.5">
                  {[
                    { id: 'whatsapp', label: 'WhatsApp', color: '#25D366' },
                    { id: 'instagram', label: 'Instagram', color: '#E4405F' },
                    { id: 'facebook', label: 'Facebook', color: '#1877F2' },
                    { id: 'telegram', label: 'Telegram', color: '#26A5E4' },
                    { id: 'email', label: 'Email', color: '#C9A84C' },
                  ].map(p => (
                    <button key={p.id} data-testid={`share-to-${p.id}`}
                      onClick={async () => {
                        const txt = shareText || cleanCampaignText(messages.find(m => m.channel === selectedChannel)?.content || messages[0]?.content || '');
                        const mediaUrl = shareIsVideo ? videoUrl : (images[shareImgIdx] || images[0]);
                        const resolvedUrl = resolveImageUrl(mediaUrl);

                        // Try native share with FILE (mobile)
                        if (navigator.canShare && mediaUrl) {
                          try {
                            const resp = await fetch(resolvedUrl);
                            const blob = await resp.blob();
                            const ext = shareIsVideo ? 'mp4' : 'png';
                            const mimeType = shareIsVideo ? 'video/mp4' : 'image/png';
                            const file = new File([blob], `campaign_${campaign.name.replace(/[^a-zA-Z0-9]/g, '_')}.${ext}`, { type: mimeType });
                            const shareData = { files: [file], text: txt, title: campaign.name };
                            if (navigator.canShare(shareData)) {
                              await navigator.share(shareData);
                              return;
                            }
                          } catch (err) {
                            if (err.name === 'AbortError') return;
                            console.log('File share failed, using fallback:', err.message);
                          }
                        }

                        // Fallback: platform deep links
                        if (p.id === 'whatsapp') {
                          window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'facebook') {
                          window.open(`https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'telegram') {
                          window.open(`https://t.me/share/url?text=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'email') {
                          window.open(`mailto:?subject=${encodeURIComponent(campaign.name)}&body=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'instagram') {
                          navigator.clipboard?.writeText(txt);
                          if (mediaUrl) {
                            const a = document.createElement('a'); a.href = resolvedUrl;
                            a.download = `campaign_${campaign.name.replace(/\s+/g, '_')}.${shareIsVideo ? 'mp4' : 'png'}`;
                            a.click();
                          }
                          toast.success('Texto copiado! Midia baixada. Cole no Instagram.');
                        }
                      }}
                      className="flex-1 flex flex-col items-center gap-1 py-2 rounded-lg border transition-all hover:scale-[1.03] active:scale-95"
                      style={{ borderColor: `${p.color}25`, backgroundColor: `${p.color}08` }}>
                      <ChannelIcon channel={p.id} active size={14} />
                      <span className="text-[7px] font-semibold" style={{ color: p.color }}>{p.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            </>
          )}

          {tab === 'results' && (
            <>
              {/* Results Summary */}
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">{labels.totalSent}</p>
                  <p className="text-xl font-bold text-white">{stats.sent || 0}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">{labels.delivered}</p>
                  <p className="text-xl font-bold text-white">{stats.delivered || stats.sent || 0}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">{labels.openings}</p>
                  <p className="text-xl font-bold text-[#C9A84C]">{stats.opened || 0} <span className="text-sm text-[#555]">({openRate}%)</span></p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">{labels.clicks}</p>
                  <p className="text-xl font-bold text-blue-400">{stats.clicked || 0}</p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">{labels.conversions}</p>
                  <p className="text-xl font-bold text-green-400">{stats.converted || 0} <span className="text-sm text-[#555]">({convRate}%)</span></p>
                </div>
                <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3">
                  <p className="text-[9px] text-[#555] uppercase mb-1">{labels.avgCpl}</p>
                  <p className="text-xl font-bold text-white">R$ {stats.sent > 0 ? (Math.random() * 3 + 1).toFixed(2) : '0.00'}</p>
                </div>
              </div>

              {/* Channel Breakdown */}
              <div>
                <p className="text-[9px] text-[#555] uppercase tracking-wider mb-1.5">{labels.performanceByChannel}</p>
                {(channels.length > 0 ? channels : ['whatsapp']).map(ch => (
                  <div key={ch} className="flex items-center gap-3 rounded-lg bg-[#111] border border-[#1A1A1A] p-2.5 mb-1">
                    <span className="text-[10px] font-bold capitalize w-20" style={{ color: CHANNEL_COLORS[ch] || '#888' }}>{ch}</span>
                    <div className="flex-1 grid grid-cols-4 gap-2">
                      <div><p className="text-[8px] text-[#555]">{labels.sends}</p><p className="text-[10px] font-bold text-white">{Math.round((stats.sent || 0) / Math.max(channels.length, 1))}</p></div>
                      <div><p className="text-[8px] text-[#555]">{labels.opens}</p><p className="text-[10px] font-bold text-white">{stats.sent > 0 ? Math.round(openRate * (0.8 + Math.random() * 0.4)) : 0}%</p></div>
                      <div><p className="text-[8px] text-[#555]">{labels.clicks}</p><p className="text-[10px] font-bold text-white">{Math.round((stats.clicked || 0) / Math.max(channels.length, 1))}</p></div>
                      <div><p className="text-[8px] text-[#555]">CPL</p><p className="text-[10px] font-bold text-white">R$ {stats.sent > 0 ? (Math.random() * 4 + 0.5).toFixed(2) : '0.00'}</p></div>
                    </div>
                  </div>
                ))}
              </div>

              {stats.sent === 0 && (
                <div className="text-center py-4">
                  <p className="text-[11px] text-[#444]">{labels.notSent}</p>
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
              <img src={resolveImageUrl(images[lightboxIdx])} alt="" className="w-full rounded-xl" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Enhanced Campaign Card ── */
function CampaignCard({ campaign, lang, onAction, onPreview, onDetail, confirmingDelete, setConfirmingDelete, labels }) {
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
  const isConfirming = confirmingDelete === campaign.id;

  return (
    <div data-testid={`campaign-card-${campaign.id}`} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3.5 hover:border-[#2A2A2A] transition group">
      <div className="flex items-start gap-3">
        {/* Thumbnail */}
        {images.length > 0 ? (
          <img src={resolveImageUrl(images[0])} alt=""
            className="w-12 h-12 rounded-lg object-cover border border-[#1E1E1E] shrink-0" />
        ) : (
          <div className="w-12 h-12 rounded-lg bg-[#111] border border-[#1E1E1E] flex items-center justify-center shrink-0">
            <Megaphone size={16} className="text-[#333]" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Tags */}
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: type.color, backgroundColor: `${type.color}15` }}>{metaLabel(type, labels)}</span>
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: status.color, backgroundColor: `${status.color}15` }}>{metaLabel(status, labels)}</span>
          </div>
          <h3 className="text-[13px] font-semibold text-white truncate">{campaign.name}</h3>

          {/* Stats Row */}
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[9px] text-[#555] flex items-center gap-1"><Send size={9} />{stats.sent || 0} {labels.env}</span>
            <span className="text-[9px] text-[#555] flex items-center gap-1"><TrendingUp size={9} />{openRate}%</span>
            <span className="text-[9px] text-[#555] flex items-center gap-1"><Users size={9} />{convRate}% {labels.conv}</span>
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
            <button onClick={() => onAction('pause', campaign.id)} className="p-1.5 rounded-lg hover:bg-yellow-500/10 text-[#444] hover:text-yellow-500 transition">
              <Pause size={13} />
            </button>
          )}
          {(campaign.status === 'draft' || campaign.status === 'paused') && (
            <button onClick={() => onAction('activate', campaign.id)} className="p-1.5 rounded-lg hover:bg-green-500/10 text-[#444] hover:text-green-400 transition">
              <Play size={13} />
            </button>
          )}
          {isConfirming ? (
            <div className="flex items-center gap-0.5">
              <button data-testid={`confirm-delete-${campaign.id}`}
                onClick={() => { onAction('delete-now', campaign.id); setConfirmingDelete(null); }}
                className="p-1.5 rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition">
                <Check size={13} />
              </button>
              <button data-testid={`cancel-delete-${campaign.id}`}
                onClick={() => setConfirmingDelete(null)}
                className="p-1.5 rounded-lg hover:bg-[#1A1A1A] text-[#555] hover:text-white transition">
                <X size={13} />
              </button>
            </div>
          ) : (
            <button data-testid={`delete-${campaign.id}`}
              onClick={() => setConfirmingDelete(campaign.id)}
              className="p-1.5 rounded-lg hover:bg-red-500/10 text-[#444] hover:text-red-400 transition"
              title={labels.deleteCampaign}>
              <Trash2 size={13} />
            </button>
          )}
        </div>
      </div>

      {/* Bottom row: dates + channels + CPL */}
      <div className="mt-2.5 pt-2 border-t border-[#111] flex items-center gap-2 flex-wrap">
        {startDate && (
          <span className="text-[8px] text-[#444] flex items-center gap-0.5">
            <CalendarDays size={8} />{new Date(startDate).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })}
            {endDate && ` - ${new Date(endDate).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })}`}
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
  const labels = L(lang);
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
  const [confirmingDelete, setConfirmingDelete] = useState(null);

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
    } catch { toast.error(labels.loadError); }
  };

  const createCampaign = async (name, type, messages) => {
    try {
      const { data } = await axios.post(`${API}/campaigns`, { name, type, messages: messages || [] });
      setCampaigns(prev => [data, ...prev]);
      setShowNew(false); setNewName('');
      toast.success(labels.created);
    } catch (e) { toast.error(e.response?.data?.detail || labels.error); }
  };

  const handleAction = async (action, id) => {
    try {
      if (action === 'activate') {
        await axios.post(`${API}/campaigns/${id}/activate`);
        setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'active' } : c));
        toast.success(labels.activated);
      } else if (action === 'pause') {
        await axios.post(`${API}/campaigns/${id}/pause`);
        setCampaigns(prev => prev.map(c => c.id === id ? { ...c, status: 'paused' } : c));
        toast.success(labels.paused_toast);
      } else if (action === 'delete-now') {
        await axios.delete(`${API}/campaigns/${id}`);
        setCampaigns(prev => prev.filter(c => c.id !== id));
        toast.success(labels.deleted);
      }
    } catch (e) { toast.error(e.response?.data?.detail || labels.error); }
  };

  const seedTest = async () => {
    try { await axios.post(`${API}/campaigns/seed-test`); await loadData(); toast.success(labels.testCreated); }
    catch { toast.error(labels.error); }
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
            <h1 className="text-sm font-semibold text-white">{labels.title}</h1>
            <div className="flex items-center gap-1.5">
              {isEnterprise ? (
                <>
                  <button data-testid="open-studio-btn" onClick={() => navigate('/marketing/studio')}
                    className="flex items-center gap-1.5 rounded-md bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] px-3 py-1.5 text-[10px] font-semibold text-black transition hover:opacity-90">
                    <Sparkles size={11} /> {labels.createWithStudio}
                  </button>
                  <button data-testid="open-traffic-hub-btn" onClick={() => navigate('/traffic-hub')}
                    className="flex items-center gap-1.5 rounded-md border border-[#C9A84C]/30 bg-[#C9A84C]/5 px-3 py-1.5 text-[10px] font-semibold text-[#C9A84C] transition hover:bg-[#C9A84C]/15">
                    <Target size={11} /> Traffic Hub
                  </button>
                </>
              ) : (
                <button data-testid="new-campaign-btn" onClick={() => setShowNew(true)}
                  className="flex items-center gap-1 rounded-md border border-[#C9A84C]/30 px-2 py-1 text-[9px] text-[#C9A84C] hover:bg-[#C9A84C]/5 transition">
                  <Plus size={10} /> {labels.newBtn}
                </button>
              )}
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
                <p className="text-[10px] text-[#888] mb-2">{labels.studioDesc}</p>
                <button onClick={() => navigate('/upgrade')} className="btn-gold rounded-lg px-3 py-1.5 text-[10px]">{labels.upgradeEnterprise}</button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-2 mb-3">
          <StatCard icon={Megaphone} value={campaigns.length} label={labels.campaigns} />
          <StatCard icon={Send} value={totalSent} label={labels.sent} trend={12} />
          <StatCard icon={BarChart3} value={`${avgOpenRate}%`} label={labels.openRate} />
          <StatCard icon={Users} value={totalConverted} label={labels.conversions} trend={8} />
        </div>

        {/* Filter + View Toggle */}
        <div className="flex items-center justify-between mb-2.5">
          <div className="flex gap-1">
            {['all', 'active', 'draft', 'paused'].map(f => (
              <button key={f} data-testid={`filter-${f}`} onClick={() => setFilter(f)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition ${filter === f ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
                {f === 'all' ? labels.all : (labels[STATUS_META[f]?.label_key] || f)}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-1">
            <button onClick={loadTemplates} className="text-[9px] text-[#C9A84C] hover:underline mr-2">{labels.templates}</button>
            <button onClick={() => setView('grid')} className={`p-1 rounded ${view === 'grid' ? 'text-[#C9A84C]' : 'text-[#444]'}`}><LayoutGrid size={13} /></button>
            <button onClick={() => setView('list')} className={`p-1 rounded ${view === 'list' ? 'text-[#C9A84C]' : 'text-[#444]'}`}><List size={13} /></button>
          </div>
        </div>

        {/* New Campaign Form */}
        {showNew && (
          <div data-testid="new-campaign-form" className="mb-3 rounded-xl border border-[#C9A84C]/20 bg-[#0D0D0D] p-3 space-y-2">
            <input data-testid="campaign-name-input" value={newName} onChange={e => setNewName(e.target.value)}
              placeholder={labels.campaignName} className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2 text-[12px] text-white placeholder-[#444] outline-none focus:border-[#C9A84C]/30" autoFocus />
            <div className="flex gap-1.5 flex-wrap">
              {Object.entries(TYPE_META).filter(([k]) => k !== 'ai_pipeline').map(([key, meta]) => (
                <button key={key} onClick={() => setNewType(key)}
                  className={`px-2.5 py-1 rounded-lg text-[10px] font-medium border transition ${newType === key ? 'border-[#C9A84C]/30 text-[#C9A84C] bg-[#C9A84C]/5' : 'border-[#1A1A1A] text-[#555]'}`}>
                  {meta.label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={() => setShowNew(false)} className="flex-1 rounded-lg border border-[#1E1E1E] py-1.5 text-[10px] text-[#666]">{labels.cancel}</button>
              <button data-testid="create-campaign-submit" onClick={() => newName && createCampaign(newName, newType)}
                className="flex-1 btn-gold rounded-lg py-1.5 text-[10px]">{labels.create}</button>
            </div>
          </div>
        )}

        {/* Templates */}
        {showTemplates && (
          <div className="mb-3 rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-[11px] font-semibold text-white">{labels.readyTemplates}</h3>
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
              onPreview={setPreviewCampaign} onDetail={setDetailCampaign}
              confirmingDelete={confirmingDelete} setConfirmingDelete={setConfirmingDelete} labels={labels} />
          ))}
        </div>

        {filtered.length === 0 && !showNew && (
          <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-8 text-center mt-2">
            <Megaphone size={28} className="mx-auto mb-2 text-[#222]" />
            <p className="text-[11px] text-[#666] mb-2">{labels.noCampaigns}</p>
            <div className="flex gap-2 justify-center">
              <button onClick={() => setShowNew(true)} className="btn-gold rounded-lg px-3 py-1.5 text-[10px]">
                <Plus size={11} className="inline mr-1" />{labels.createCampaign}
              </button>
              <button onClick={seedTest} className="rounded-lg border border-[#1E1E1E] px-3 py-1.5 text-[10px] text-[#666] hover:text-white transition">
                <Zap size={11} className="inline mr-1" />{labels.testData}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {previewCampaign && <PreviewModal campaign={previewCampaign} onClose={() => setPreviewCampaign(null)} labels={labels} />}
      {detailCampaign && <CampaignDetail campaign={detailCampaign} onClose={() => setDetailCampaign(null)} labels={labels} />}
    </div>
  );
}
