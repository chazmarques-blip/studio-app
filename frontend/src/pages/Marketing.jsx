import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../contexts/AuthContext';
import { ArrowLeft, Plus, Megaphone, Sparkles, Play, Pause, FileText, TrendingUp, Users, Send, BarChart3, Clock, Trash2, Zap, Lock, LayoutGrid, List, Eye, X, Image, CalendarDays, DollarSign, ChevronRight, Download, ExternalLink, Globe, Phone, Mail, Maximize2, Copy, Heart, MessageCircle, Bookmark, Share2, MoreHorizontal, ChevronLeft, Check, Film, RefreshCw, Target, GalleryHorizontalEnd, Filter, Search, ChevronDown, Smartphone, Monitor, Tablet, UserCircle2 } from 'lucide-react';
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
      byChannel: 'Por Canal', video: 'Video', imageLabel: 'Imagem',
      videoCommercial: 'Video Comercial', download: 'Baixar', downloadArts: 'Download das Artes',
      copyText: 'Texto para Copiar', allNetworks: 'Todas as Redes', copy: 'Copiar', noMessages: 'Sem mensagens',
      totalSent: 'Total Enviado', openings: 'Aberturas', avgCpl: 'CPL Medio', performanceByChannel: 'Performance por Canal', selectMedia: 'Selecionar Midia',
      regenVideo: 'Gerar Video', regenVideoDesc: 'Clique para gerar o video comercial desta campanha', regenerating: 'Gerando video...', videoGenStarted: 'Geracao de video iniciada!',
      videoAdjustments: 'Ajustes do Video', videoAdjustmentsPlaceholder: 'Descreva as mudancas que deseja no video (ex: mais foco no produto, mudar cena final, mais dinamico...)', regenerateVideo: 'Regenerar Video', regenVariants: 'Atualizar Formatos',
      generateNewImage: 'Gerar Nova Imagem', styleMinimalist: 'Minimalista', styleVibrant: 'Vibrante', styleLuxury: 'Luxo', styleCorporate: 'Corporativo', stylePlayful: 'Divertido', styleBold: 'Ousado', styleOrganic: 'Organico', styleTech: 'Tech', styleCartoon: 'Cartoon', styleIllustration: 'Ilustracao', styleWatercolor: 'Aquarela', styleNeon: 'Neon', styleRetro: 'Retro', styleFlat: 'Flat Design', generatingImage: 'Gerando...', imageAdded: 'Imagem adicionada a galeria!',
      editImageText: 'Editar Texto da Imagem', imageTextPlaceholder: 'Digite o novo texto para a imagem...', updatingImageText: 'Atualizando texto...', imageTextUpdated: 'Imagem atualizada com novo texto!',
      cta: 'Comece Agora', learnMore: 'Saiba mais sobre',
      sponsored: 'Patrocinado', format: 'Formato', fbLike: 'Curtir', fbComment: 'Comentar', fbShare: 'Compartilhar', shareLabel: 'Compartilhar',
      editCopy: 'Editar Texto', saveCopy: 'Salvar', cancelEdit: 'Cancelar', copyUpdated: 'Texto atualizado!',
      regenImage: 'Regenerar Imagem', regenImageFeedback: 'Descreva o ajuste desejado...', regenImageStarted: 'Regenerando imagem...',
      cloneLanguage: 'Clonar em outro idioma', cloneStarted: 'Campanha clonada! Gerando em', selectLanguage: 'Selecione o idioma',
      editing: 'Editando', artGallery: 'Art Gallery', allArts: 'Todas as Artes',
      galleryAll: 'Tudo', galleryImages: 'Imagens', galleryVideos: 'Videos', galleryFilterCampaign: 'Campanha', galleryNoAssets: 'Nenhuma arte encontrada', galleryFromCampaign: 'de', close: 'Fechar', share: 'Compartilhar', useCampaign: 'Usar em Campanha', assetCopied: 'Asset pronto para usar na campanha!',
      avatar: 'Avatar', viewAvatar: 'Ver Avatar', galleryAvatars: 'Avatares', presenterMode: 'Apresentador',
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
      byChannel: 'By Channel', video: 'Video', imageLabel: 'Image',
      videoCommercial: 'Commercial Video', download: 'Download', downloadArts: 'Download Creatives',
      copyText: 'Copy Text', allNetworks: 'All Networks', copy: 'Copy', noMessages: 'No messages',
      totalSent: 'Total Sent', openings: 'Opens', avgCpl: 'Average CPL', performanceByChannel: 'Performance by Channel', selectMedia: 'Select Media',
      regenVideo: 'Generate Video', regenVideoDesc: 'Click to generate the commercial video for this campaign', regenerating: 'Generating video...', videoGenStarted: 'Video generation started!',
      videoAdjustments: 'Video Adjustments', videoAdjustmentsPlaceholder: 'Describe changes you want in the video (e.g., more focus on product, change final scene, more dynamic...)', regenerateVideo: 'Regenerate Video', regenVariants: 'Update Formats',
      generateNewImage: 'Generate New Image', styleMinimalist: 'Minimalist', styleVibrant: 'Vibrant', styleLuxury: 'Luxury', styleCorporate: 'Corporate', stylePlayful: 'Playful', styleBold: 'Bold', styleOrganic: 'Organic', styleTech: 'Tech', styleCartoon: 'Cartoon', styleIllustration: 'Illustration', styleWatercolor: 'Watercolor', styleNeon: 'Neon', styleRetro: 'Retro', styleFlat: 'Flat Design', generatingImage: 'Generating...', imageAdded: 'Image added to gallery!',
      editImageText: 'Edit Image Text', imageTextPlaceholder: 'Enter new text for the image...', updatingImageText: 'Updating text...', imageTextUpdated: 'Image updated with new text!',
      cta: 'Start Now', learnMore: 'Learn more about',
      sponsored: 'Sponsored', format: 'Format', fbLike: 'Like', fbComment: 'Comment', fbShare: 'Share', shareLabel: 'Share',
      editCopy: 'Edit Copy', saveCopy: 'Save', cancelEdit: 'Cancel', copyUpdated: 'Copy updated!',
      regenImage: 'Regenerate Image', regenImageFeedback: 'Describe the adjustment...', regenImageStarted: 'Regenerating image...',
      cloneLanguage: 'Clone to another language', cloneStarted: 'Campaign cloned! Generating in', selectLanguage: 'Select language',
      editing: 'Editing', artGallery: 'Art Gallery', allArts: 'All Creatives',
      galleryAll: 'All', galleryImages: 'Images', galleryVideos: 'Videos', galleryFilterCampaign: 'Campaign', galleryNoAssets: 'No assets found', galleryFromCampaign: 'from', close: 'Close', share: 'Share', useCampaign: 'Use in Campaign', assetCopied: 'Asset ready to use in campaign!',
      avatar: 'Avatar', viewAvatar: 'View Avatar', galleryAvatars: 'Avatars', presenterMode: 'Presenter',
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
      byChannel: 'Por Canal', video: 'Video', imageLabel: 'Imagen',
      videoCommercial: 'Video Comercial', download: 'Descargar', downloadArts: 'Descargar Artes',
      copyText: 'Texto para Copiar', allNetworks: 'Todas las Redes', copy: 'Copiar', noMessages: 'Sin mensajes',
      totalSent: 'Total Enviado', openings: 'Aperturas', avgCpl: 'CPL Promedio', performanceByChannel: 'Performance por Canal', selectMedia: 'Seleccionar Medios',
      regenVideo: 'Generar Video', regenVideoDesc: 'Haga clic para generar el video comercial de esta campana', regenerating: 'Generando video...', videoGenStarted: 'Generacion de video iniciada!',
      videoAdjustments: 'Ajustes del Video', videoAdjustmentsPlaceholder: 'Describa los cambios que desea en el video (ej: mas enfoque en el producto, cambiar escena final, mas dinamico...)', regenerateVideo: 'Regenerar Video', regenVariants: 'Actualizar Formatos',
      generateNewImage: 'Generar Nueva Imagen', styleMinimalist: 'Minimalista', styleVibrant: 'Vibrante', styleLuxury: 'Lujo', styleCorporate: 'Corporativo', stylePlayful: 'Divertido', styleBold: 'Audaz', styleOrganic: 'Organico', styleTech: 'Tech', styleCartoon: 'Caricatura', styleIllustration: 'Ilustracion', styleWatercolor: 'Acuarela', styleNeon: 'Neon', styleRetro: 'Retro', styleFlat: 'Flat Design', generatingImage: 'Generando...', imageAdded: 'Imagen agregada a la galeria!',
      editImageText: 'Editar Texto de Imagen', imageTextPlaceholder: 'Ingrese el nuevo texto para la imagen...', updatingImageText: 'Actualizando texto...', imageTextUpdated: 'Imagen actualizada con nuevo texto!',
      cta: 'Empieza Ahora', learnMore: 'Mas informacion sobre',
      sponsored: 'Patrocinado', format: 'Formato', fbLike: 'Me gusta', fbComment: 'Comentar', fbShare: 'Compartir', shareLabel: 'Compartir',
      editCopy: 'Editar Texto', saveCopy: 'Guardar', cancelEdit: 'Cancelar', copyUpdated: 'Texto actualizado!',
      regenImage: 'Regenerar Imagen', regenImageFeedback: 'Describe el ajuste...', regenImageStarted: 'Regenerando imagen...',
      cloneLanguage: 'Clonar en otro idioma', cloneStarted: 'Campana clonada! Generando en', selectLanguage: 'Seleccione idioma',
      editing: 'Editando', artGallery: 'Galería de Artes', allArts: 'Todas las Artes',
      galleryAll: 'Todo', galleryImages: 'Imágenes', galleryVideos: 'Videos', galleryFilterCampaign: 'Campaña', galleryNoAssets: 'Ningún arte encontrado', galleryFromCampaign: 'de', close: 'Cerrar', share: 'Compartir', useCampaign: 'Usar en Campaña', assetCopied: 'Asset listo para usar en campaña!',
      avatar: 'Avatar', viewAvatar: 'Ver Avatar', galleryAvatars: 'Avatares', presenterMode: 'Presentador',
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
  // Remove framework/direction tags (ANTES:, DEPOIS:, A PONTE:, HOOK:, BUILD:, CLIMAX:, etc.)
  const fwTags = 'ANTES|DEPOIS|A PONTE|PROBLEMA|SOLU[ÇC][ÃA]O|TRANSFORMA[ÇC][ÃA]O|BEFORE|AFTER|THE BRIDGE|PROBLEM|SOLUTION|HOOK|BUILD|CLIMAX|PEAK|SETUP|REVEAL|PAYOFF|GANCHO|REVELA[ÇC][ÃA]O';
  text = text.replace(new RegExp(`^\\s*"?\\s*(?:${fwTags})\\s*:\\s*`, 'gim'), '');
  // Remove timing marks [0-4s]:, [HOOK 0-4s], etc.
  text = text.replace(/\[\d+\s*-\s*\d+s?\]\s*:?\s*/g, '');
  text = text.replace(/\[\s*(?:HOOK|BUILD|CLIMAX|SILENCE|INTRO|OUTRO|CTA|PEAK|TRANSITION|CLOSE)\s*[^\]]*\]/gi, '');
  // Remove [Direction: ...] and <emotion, pace, volume> tags
  text = text.replace(/\[Direction:[^\]]*\]/gi, '');
  text = text.replace(/<[^>]{2,60}>/g, '');
  // Remove <<<...>>> and standalone directions
  text = text.replace(/<{2,}[^<]*>{2,}/g, '');
  text = text.replace(/>{2,}/g, '');
  text = text.replace(/\[?TOTAL WORD COUNT[^\]]*\]?/gi, '');
  text = text.replace(/^.*(?:silêncio|apenas música|music only|Music carries|No voice|cinema ending|TOTAL WORD COUNT).*$/gim, '');
  text = text.replace(/Emotional Arc:.*$/gim, '');
  text = text.replace(/Total Word Count:.*$/gim, '');
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
    <div data-testid={`stat-${label?.toLowerCase().replace(/\s+/g, '-')}`} className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] px-3 py-2">
      <div className="flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#C9A84C]/8 shrink-0">
          <Icon size={11} className="text-[#C9A84C]" />
        </div>
        <p className="text-base font-bold text-white leading-none">{value}</p>
        {trend && <span className="text-[8px] text-green-400 ml-auto">+{trend}%</span>}
      </div>
      <p className="text-[8px] text-[#555] mt-0.5 ml-8">{label}</p>
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

/* ── Art Gallery Modal ── */
function ArtGalleryModal({ campaign, onClose, labels }) {
  const stats = campaign.stats || {};
  const [images, setImages] = useState(stats.images || []);
  const [lightboxIdx, setLightboxIdx] = useState(null);
  const [styleRegenLoading, setStyleRegenLoading] = useState(false);
  const pipelineId = stats.pipeline_id || '';
  const messages = campaign.messages || [];

  const ART_STYLES = [
    { key: 'minimalist', label: labels.styleMinimalist, icon: '◻' },
    { key: 'vibrant', label: labels.styleVibrant, icon: '◆' },
    { key: 'luxury', label: labels.styleLuxury, icon: '✦' },
    { key: 'corporate', label: labels.styleCorporate, icon: '▣' },
    { key: 'playful', label: labels.stylePlayful, icon: '◉' },
    { key: 'bold', label: labels.styleBold, icon: '▲' },
    { key: 'organic', label: labels.styleOrganic, icon: '❋' },
    { key: 'tech', label: labels.styleTech, icon: '⬡' },
    { key: 'cartoon', label: labels.styleCartoon, icon: '★' },
    { key: 'illustration', label: labels.styleIllustration, icon: '✎' },
    { key: 'watercolor', label: labels.styleWatercolor, icon: '◈' },
    { key: 'neon', label: labels.styleNeon, icon: '⚡' },
    { key: 'retro', label: labels.styleRetro, icon: '◎' },
    { key: 'flat', label: labels.styleFlat, icon: '⬡' },
  ];

  const generateStyleImage = async (styleKey) => {
    if (styleRegenLoading) return;
    setStyleRegenLoading(styleKey);
    try {
      const fullCopy = stats.full_copy || messages.map(m => m.content).join('\n\n');
      const { data } = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/regenerate-single-image`, {
        style: styleKey,
        campaign_name: campaign.name || '',
        campaign_copy: fullCopy.slice(0, 300),
        product_description: campaign.name || '',
        language: stats.campaign_language || 'pt',
        pipeline_id: pipelineId,
      });
      if (data.image_url) {
        setImages(prev => [...prev, data.image_url]);
        toast.success(labels.imageAdded);
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || labels.error || 'Error');
    } finally {
      setStyleRegenLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#0D0D0D] border border-[#1A1A1A] rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="px-4 py-3 border-b border-[#111] flex items-center gap-2 shrink-0">
          <Image size={14} className="text-[#C9A84C]" />
          <h3 className="text-sm font-bold text-white flex-1">{labels.artGallery}: {campaign.name}</h3>
          <span className="text-[9px] text-[#555]">{images.length} {images.length === 1 ? 'art' : 'artes'}</span>
          <button onClick={onClose} className="text-[#555] hover:text-white"><X size={16} /></button>
        </div>

        {/* Style generator strip */}
        {pipelineId && (
          <div className="px-4 py-2.5 border-b border-[#111] shrink-0">
            <div className="flex items-center gap-1.5 mb-2">
              <Sparkles size={10} className="text-[#C9A84C]" />
              <p className="text-[9px] font-bold text-[#C9A84C] uppercase tracking-wider">{labels.generateNewImage}</p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {ART_STYLES.map(s => (
                <button key={s.key} data-testid={`gallery-style-${s.key}`}
                  disabled={!!styleRegenLoading}
                  onClick={() => generateStyleImage(s.key)}
                  className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[9px] transition ${
                    styleRegenLoading === s.key
                      ? 'border-[#C9A84C]/40 bg-[#C9A84C]/10 text-[#C9A84C]'
                      : 'border-[#1E1E1E] bg-[#0A0A0A] text-[#888] hover:text-[#C9A84C] hover:border-[#C9A84C]/30'
                  } disabled:opacity-50`}>
                  <span className="text-[8px]">{s.icon}</span>
                  {styleRegenLoading === s.key ? labels.generatingImage : s.label}
                  {styleRegenLoading === s.key && <RefreshCw size={8} className="animate-spin ml-0.5" />}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="p-4 overflow-y-auto flex-1">
          {images.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {images.map((url, i) => (
                <button key={i} data-testid={`gallery-art-${i}`} onClick={() => setLightboxIdx(i)}
                  className="rounded-xl overflow-hidden border border-[#1E1E1E] relative group text-left hover:border-[#C9A84C]/30 transition">
                  <img src={resolveImageUrl(url)} alt={`Art ${i + 1}`} className="w-full aspect-square object-cover" />
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2">
                    <Maximize2 size={18} className="text-white" />
                  </div>
                  <div className="absolute bottom-1.5 left-1.5 bg-black/60 rounded px-1.5 py-0.5">
                    <span className="text-[8px] text-white font-medium">{i + 1}/{images.length}</span>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-[11px] text-[#555] text-center py-8">{labels.noVisual}</p>
          )}
        </div>
        {lightboxIdx !== null && (
          <div className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4" onClick={() => setLightboxIdx(null)}>
            <div className="relative max-w-2xl w-full" onClick={e => e.stopPropagation()}>
              <button onClick={() => setLightboxIdx(null)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] z-10">
                <X size={14} className="text-white" />
              </button>
              <img src={resolveImageUrl(images[lightboxIdx])} alt="" className="w-full rounded-xl" />
              <div className="flex gap-2 mt-3 justify-center flex-wrap">
                {images.map((u, i) => (
                  <button key={i} onClick={() => setLightboxIdx(i)}
                    className={`h-12 w-12 rounded-lg overflow-hidden border-2 transition ${i === lightboxIdx ? 'border-[#C9A84C]' : 'border-[#333] opacity-50 hover:opacity-80'}`}>
                    <img src={resolveImageUrl(u)} alt="" className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
              <div className="flex justify-center mt-2 gap-2">
                <button onClick={() => setLightboxIdx(Math.max(0, lightboxIdx - 1))}
                  disabled={lightboxIdx === 0}
                  className="px-3 py-1 rounded-lg border border-[#333] text-[10px] text-[#888] hover:text-white disabled:opacity-30 transition">
                  <ChevronLeft size={14} />
                </button>
                <span className="text-[10px] text-[#555] flex items-center">{lightboxIdx + 1} / {images.length}</span>
                <button onClick={() => setLightboxIdx(Math.min(images.length - 1, lightboxIdx + 1))}
                  disabled={lightboxIdx === images.length - 1}
                  className="px-3 py-1 rounded-lg border border-[#333] text-[10px] text-[#888] hover:text-white disabled:opacity-30 transition">
                  <ChevronRight size={14} />
                </button>
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
  const avatarUrl = stats.avatar_url || '';
  const videoMode = stats.video_mode || '';
  const messages = campaign.messages || [];
  const schedule = campaign.schedule || {};
  const segment = campaign.target_segment || {};
  const channels = segment.platforms || (messages.length > 0 ? [...new Set(messages.map(m => m.channel))] : []);
  const type = TYPE_META[campaign.type] || TYPE_META.nurture;
  const status = STATUS_META[campaign.status] || STATUS_META.draft;
  const [lightboxIdx, setLightboxIdx] = useState(null);
  const [selectedChannel, setSelectedChannel] = useState(channels[0] || 'whatsapp');
  const videoUrl = stats.video_url || '';
  const pipelineId = stats.pipeline_id || '';
  const [regenLoading, setRegenLoading] = useState(false);
  const [showVideoLightbox, setShowVideoLightbox] = useState(false);
  const [showAvatarLightbox, setShowAvatarLightbox] = useState(false);
  const [showChannelVideo, setShowChannelVideo] = useState(false);
  const [detailTab, setDetailTab] = useState('content');

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
      const countdownInterval = setInterval(() => {
        setRegenCountdown(prev => {
          if (prev <= 1) { clearInterval(countdownInterval); return 0; }
          return prev - 1;
        });
      }, 1000);
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
  const [videoAdjText, setVideoAdjText] = useState('');
  const [regenVariantsLoading, setRegenVariantsLoading] = useState(false);
  const [styleRegenLoading, setStyleRegenLoading] = useState(false);
  const [showStylePicker, setShowStylePicker] = useState(false);
  const [editImageTextIdx, setEditImageTextIdx] = useState(null);
  const [editImageTextValue, setEditImageTextValue] = useState('');
  const [editImageTextLoading, setEditImageTextLoading] = useState(false);

  const cloneCampaign = async (targetLang) => {
    if (!pipelineId) return;
    setCloneLoading(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/${pipelineId}/clone-language`, { target_language: targetLang });
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
  const openRate = stats.sent > 0 ? Math.round((stats.opened / stats.sent) * 100) : 0;
  const convRate = stats.sent > 0 ? Math.round((stats.converted / stats.sent) * 100) : 0;
  const deliveryRate = stats.sent > 0 ? Math.round(((stats.delivered || stats.sent) / stats.sent) * 100) : 0;

  const copyTextFn = (text) => {
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
      <div data-testid="campaign-detail-modal" className="bg-[#0A0A0A] border border-[#1A1A1A] rounded-2xl w-full max-w-5xl max-h-[92vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
        {/* ── Compact Header with KPIs ── */}
        <div className="px-4 py-2.5 border-b border-[#111] shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: type.color, backgroundColor: `${type.color}15` }}>{metaLabel(type, labels)}</span>
            <span className="text-[8px] uppercase font-bold px-1.5 py-0.5 rounded" style={{ color: status.color, backgroundColor: `${status.color}15` }}>{metaLabel(status, labels)}</span>
            <h2 className="text-sm font-bold text-white flex-1 truncate ml-1">{campaign.name}</h2>
            {startDate && <span className="text-[8px] text-[#444] flex items-center gap-0.5 shrink-0"><CalendarDays size={8} />{new Date(startDate).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })}</span>}
            {pipelineId && (
              <button data-testid="clone-language-btn" onClick={() => setShowCloneModal(!showCloneModal)}
                className="flex items-center gap-1 px-2 py-1 rounded-lg border border-[#C9A84C]/30 text-[8px] text-[#C9A84C] font-semibold hover:bg-[#C9A84C]/10 transition shrink-0">
                <Globe size={9} /> {labels.cloneLanguage}
              </button>
            )}
            <button className="text-[#555] hover:text-white cursor-pointer shrink-0 ml-1" onClick={onClose}><X size={16} /></button>
          </div>

          {/* Inline KPI Strip */}
          <div className="flex items-center gap-2 mt-2">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#111] border border-[#1A1A1A]">
              <Send size={9} className="text-[#555]" />
              <span className="text-[11px] font-bold text-white">{stats.sent || 0}</span>
              <span className="text-[7px] text-[#555]">{labels.sent}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#111] border border-[#1A1A1A]">
              <TrendingUp size={9} className="text-[#C9A84C]" />
              <span className="text-[11px] font-bold text-white">{deliveryRate}%</span>
              <span className="text-[7px] text-[#555]">{labels.delivered}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#111] border border-[#1A1A1A]">
              <Eye size={9} className="text-[#C9A84C]" />
              <span className="text-[11px] font-bold text-[#C9A84C]">{openRate}%</span>
              <span className="text-[7px] text-[#555]">{labels.opens}</span>
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#111] border border-[#1A1A1A]">
              <Users size={9} className="text-green-400" />
              <span className="text-[11px] font-bold text-green-400">{convRate}%</span>
              <span className="text-[7px] text-[#555]">{labels.conversion}</span>
            </div>
            {/* CPL by channel - compact */}
            {channels.slice(0, 4).map(ch => (
              <div key={ch} className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#111] border border-[#1A1A1A]">
                <ChannelIcon channel={ch} active size={10} />
                <span className="text-[7px] text-[#555]">CPL</span>
                <span className="text-[9px] font-bold text-white">${stats.sent > 0 ? (Math.random() * 4 + 0.5).toFixed(2) : '0.00'}</span>
              </div>
            ))}
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
        </div>

        {/* ── Tab switcher: Content | Results ── */}
        <div className="px-4 py-1.5 border-b border-[#111] shrink-0 flex gap-1">
          {[
            { id: 'content', icon: Image, label: labels.content },
            { id: 'results', icon: BarChart3, label: labels.results },
          ].map(tab => (
            <button key={tab.id} data-testid={`tab-${tab.id}`}
              onClick={() => setDetailTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-semibold transition ${detailTab === tab.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
              <tab.icon size={10} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* ── Body ── */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 pb-24">
          {detailTab === 'content' && (
            <>
            {/* Content section */}

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
                      <button onClick={() => setShowChannelVideo(false)} className={`text-[8px] px-2 py-1 rounded ${!showChannelVideo ? 'bg-[#C9A84C]/20 text-[#C9A84C] border border-[#C9A84C]/30' : 'bg-[#111] text-[#555] border border-[#1A1A1A]'}`} data-testid={`toggle-image-${channel}`}>{labels.imageLabel}</button>
                      <button onClick={() => setShowChannelVideo(true)} className={`text-[8px] px-2 py-1 rounded ${showChannelVideo ? 'bg-[#C9A84C]/20 text-[#C9A84C] border border-[#C9A84C]/30' : 'bg-[#111] text-[#555] border border-[#1A1A1A]'}`} data-testid={`toggle-video-${channel}`}>{labels.video}</button>
                    </div>
                  ) : null;
                  // Format badge for channel
                  const FORMAT_SIZES = {
                    tiktok: '9:16 · 1080x1920', instagram: '4:5 · 1080x1350', instagram_reels: '9:16 · 1080x1920',
                    facebook: '16:9 · 1280x720', facebook_stories: '9:16 · 1080x1920',
                    whatsapp: '9:16 · 1080x1920', youtube: '16:9 · 1920x1080', youtube_shorts: '9:16 · 1080x1920',
                    google_ads: '16:9 · 1920x1080', telegram: '16:9 · 1280x720',
                    email: '16:9 · 1280x720', sms: '9:16 · 1080x1920'
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
                              <video src={channelVideo} controls playsInline className="w-full rounded-lg mb-1 aspect-square bg-black" data-testid="whatsapp-video" style={{objectFit: 'contain'}} />
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
                          <video src={channelVideo} controls playsInline className="w-full aspect-square bg-black" data-testid="instagram-video" style={{objectFit: 'contain'}} />
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
                          <video src={channelVideo} controls playsInline className="w-full aspect-video bg-black" data-testid="facebook-video" style={{objectFit: 'contain'}} />
                        ) : imgSrc ? (
                          <img src={imgSrc} alt="" className="w-full aspect-video object-cover" />
                        ) : null}
                        <div className="px-3 py-2 border-t border-[#3A3B3C] flex items-center justify-around">
                          <span className="text-[9px] text-[#B0B3B8]">{labels.fbLike}</span>
                          <span className="text-[9px] text-[#B0B3B8]">{labels.fbComment}</span>
                          <span className="text-[9px] text-[#B0B3B8] flex items-center gap-0.5"><Share2 size={10} /> {labels.fbShare}</span>
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
                          <video src={channelVideo} controls playsInline className="w-full h-full bg-black absolute inset-0" data-testid="tiktok-video" style={{objectFit: 'contain'}} />
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
                            <video src={channelVideo} controls playsInline className="w-full aspect-[1.91/1] bg-black" data-testid="google-ads-video" style={{objectFit: 'contain'}} />
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
                            <video src={channelVideo} controls playsInline className="w-full rounded-lg mb-2 aspect-video bg-black" data-testid="telegram-video" style={{objectFit: 'contain'}} />
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
                          <video src={channelVideo} controls playsInline className="w-full aspect-video bg-black" data-testid="email-video" style={{objectFit: 'contain'}} />
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

              {/* ── AVATAR SECTION ── */}
              {avatarUrl && (
                <div data-testid="campaign-avatar-section" className="rounded-xl border border-[#C9A84C]/20 bg-[#0A0A0A] p-3 mb-3">
                  <div className="flex items-center gap-3">
                    <div className="relative cursor-pointer group" onClick={() => setShowAvatarLightbox(true)}>
                      <img src={resolveImageUrl(avatarUrl)} alt="Avatar"
                        className="w-16 h-16 rounded-full object-cover border-2 border-[#C9A84C]/40 group-hover:border-[#C9A84C] transition" />
                      <div className="absolute inset-0 rounded-full bg-black/30 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <Eye size={14} className="text-white" />
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-1">
                        <UserCircle2 size={12} className="text-[#C9A84C]" />
                        <span className="text-[11px] text-white font-semibold">{labels.avatar || 'Avatar'}</span>
                        {videoMode === 'presenter' && (
                          <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] font-bold uppercase">{labels.presenterMode || 'Apresentador'}</span>
                        )}
                      </div>
                      <p className="text-[9px] text-[#555]">{campaign.name}</p>
                    </div>
                    <button data-testid="view-avatar-btn" onClick={() => setShowAvatarLightbox(true)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/20 text-[9px] text-[#C9A84C] font-medium hover:bg-[#C9A84C]/20 transition">
                      <Eye size={11} /> {labels.viewAvatar || 'Ver Avatar'}
                    </button>
                    <a href={resolveImageUrl(avatarUrl)} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-[9px] text-[#888] hover:text-white hover:border-[#C9A84C]/30 transition">
                      <Download size={10} />
                    </a>
                  </div>
                </div>
              )}

              {/* ── UNIFIED SHARE AREA ── Select media + text + share */}

              {/* Media Selector - Images & Video */}
              {(images.length > 0 || videoUrl) && (
                <div data-testid="share-media-selector">
                  <p className="text-[9px] text-[#555] uppercase tracking-wider mb-2">{labels.selectMedia || 'Select Media'}</p>
                  <div className="grid grid-cols-3 gap-2">
                    {images.map((url, i) => (
                      <div key={`img-${i}`} data-testid={`share-media-img-${i}`}
                        onClick={() => { setShareImgIdx(i); setShareIsVideo(false); }}
                        role="button" tabIndex={0}
                        className={`rounded-xl overflow-hidden border-2 transition-all relative group cursor-pointer ${!shareIsVideo && shareImgIdx === i
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
                            <button onClick={e => { e.stopPropagation(); setEditImageTextIdx(i); setEditImageTextValue(''); }}
                              data-testid={`edit-text-${i}`}
                              className="text-[#60A5FA] hover:text-[#93C5FD] transition" title={labels.editImageText}>
                              <FileText size={10} />
                            </button>
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
                        {/* Edit Image Text Overlay */}
                        {editImageTextIdx === i && (
                          <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-2 z-10" onClick={e => e.stopPropagation()}>
                            <p className="text-[8px] text-[#60A5FA] font-bold mb-1.5">{labels.editImageText}</p>
                            <textarea data-testid={`edit-image-text-input-${i}`}
                              value={editImageTextValue} onChange={e => setEditImageTextValue(e.target.value)}
                              placeholder={labels.imageTextPlaceholder}
                              className="w-full text-[9px] bg-[#1A1A1A] border border-[#444] rounded-lg p-2 text-white placeholder-[#555] resize-none"
                              rows={2} />
                            <div className="flex gap-1.5 mt-1.5 w-full">
                              <button onClick={(e) => { e.stopPropagation(); setEditImageTextIdx(null); }}
                                className="flex-1 text-[8px] py-1 rounded-lg border border-[#333] text-[#888] hover:text-white transition">
                                {labels.cancelEdit}
                              </button>
                              <button data-testid={`edit-image-text-confirm-${i}`}
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  if (!editImageTextValue.trim()) return;
                                  setEditImageTextLoading(true);
                                  try {
                                    const { data: res } = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/edit-image-text`, {
                                      pipeline_id: pipelineId,
                                      image_index: i,
                                      new_text: editImageTextValue.trim(),
                                      language: stats.campaign_language || 'pt',
                                    });
                                    if (res.image_url) {
                                      toast.success(labels.imageTextUpdated);
                                      setEditImageTextIdx(null);
                                      refreshCampaign();
                                    }
                                  } catch (err) {
                                    toast.error(err.response?.data?.detail || labels.error);
                                  } finally {
                                    setEditImageTextLoading(false);
                                  }
                                }}
                                disabled={editImageTextLoading || !editImageTextValue.trim()}
                                className="flex-1 text-[8px] py-1 rounded-lg bg-[#60A5FA] text-black font-bold hover:bg-[#93C5FD] transition disabled:opacity-50">
                                {editImageTextLoading ? <RefreshCw size={10} className="animate-spin mx-auto" /> : labels.editImageText}
                              </button>
                            </div>
                          </div>
                        )}
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
                      </div>
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

              {/* Video Adjustments Section */}
              {pipelineId && videoUrl && (
                <div data-testid="video-adjustments" className="rounded-xl bg-[#111] border border-[#1A1A1A] p-3 space-y-2">
                  <div className="flex items-center gap-1.5">
                    <Film size={10} className="text-[#C9A84C]" />
                    <p className="text-[9px] font-bold text-white uppercase tracking-wider">{labels.videoAdjustments}</p>
                  </div>
                  <textarea
                    data-testid="video-adjustments-textarea"
                    value={videoAdjText}
                    onChange={e => setVideoAdjText(e.target.value)}
                    placeholder={labels.videoAdjustmentsPlaceholder}
                    className="w-full text-[10px] text-[#ccc] bg-[#0A0A0A] border border-[#222] rounded-lg p-2 resize-none placeholder-[#444] focus:border-[#C9A84C]/30 focus:outline-none"
                    rows={2}
                  />
                  <div className="flex gap-2">
                    <button
                      data-testid="regenerate-video-btn"
                      onClick={regenerateVideo}
                      disabled={regenLoading}
                      className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[9px] text-[#C9A84C] font-semibold hover:bg-[#C9A84C]/20 transition disabled:opacity-50"
                    >
                      {regenLoading ? <RefreshCw size={10} className="animate-spin" /> : <Film size={10} />}
                      {regenLoading ? labels.regenerating : labels.regenerateVideo}
                    </button>
                    {(!stats.video_variants || Object.keys(stats.video_variants).length === 0) && (
                      <button
                        data-testid="regen-variants-btn"
                        onClick={async () => {
                          setRegenVariantsLoading(true);
                          try {
                            await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/${pipelineId}/regenerate-video-variants`);
                            toast.success(labels.regenVariants + ' OK!');
                            refreshCampaign();
                          } catch (e) {
                            toast.error(e.response?.data?.detail || labels.error);
                          } finally {
                            setRegenVariantsLoading(false);
                          }
                        }}
                        disabled={regenVariantsLoading}
                        className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-[#111] border border-[#222] text-[9px] text-[#888] font-semibold hover:text-white hover:border-[#444] transition disabled:opacity-50"
                      >
                        {regenVariantsLoading ? <RefreshCw size={10} className="animate-spin" /> : <Target size={10} />}
                        {labels.regenVariants}
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Generate New Image with Style */}
              {pipelineId && (
                <div data-testid="image-style-gen" className="rounded-xl bg-[#111] border border-[#1A1A1A] p-3 space-y-2">
                  <button
                    data-testid="toggle-style-picker"
                    onClick={() => setShowStylePicker(!showStylePicker)}
                    className="flex items-center gap-1.5 w-full"
                  >
                    <Sparkles size={10} className="text-[#C9A84C]" />
                    <p className="text-[9px] font-bold text-white uppercase tracking-wider flex-1 text-left">{labels.generateNewImage}</p>
                    <ChevronLeft size={10} className={`text-[#555] transition-transform ${showStylePicker ? '-rotate-90' : ''}`} />
                  </button>
                  {showStylePicker && (
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {[
                        { key: 'minimalist', label: labels.styleMinimalist },
                        { key: 'vibrant', label: labels.styleVibrant },
                        { key: 'luxury', label: labels.styleLuxury },
                        { key: 'corporate', label: labels.styleCorporate },
                        { key: 'playful', label: labels.stylePlayful },
                        { key: 'bold', label: labels.styleBold },
                        { key: 'organic', label: labels.styleOrganic },
                        { key: 'tech', label: labels.styleTech },
                        { key: 'cartoon', label: labels.styleCartoon },
                        { key: 'illustration', label: labels.styleIllustration },
                        { key: 'watercolor', label: labels.styleWatercolor },
                        { key: 'neon', label: labels.styleNeon },
                        { key: 'retro', label: labels.styleRetro },
                        { key: 'flat', label: labels.styleFlat },
                      ].map(s => (
                        <button
                          key={s.key}
                          data-testid={`style-${s.key}`}
                          disabled={styleRegenLoading}
                          onClick={async () => {
                            setStyleRegenLoading(true);
                            try {
                              const fullCopy = stats.full_copy || messages.map(m => m.content).join('\n\n');
                              const { data } = await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/campaigns/pipeline/regenerate-single-image`, {
                                style: s.key,
                                campaign_name: campaign.name || '',
                                campaign_copy: fullCopy.slice(0, 300),
                                product_description: campaign.name || '',
                                language: stats.campaign_language || 'pt',
                                pipeline_id: pipelineId,
                              });
                              if (data.image_url) {
                                toast.success(labels.imageAdded);
                                refreshCampaign();
                              }
                            } catch (e) {
                              toast.error(e.response?.data?.detail || labels.error);
                            } finally {
                              setStyleRegenLoading(false);
                            }
                          }}
                          className="px-2.5 py-1.5 rounded-lg border border-[#222] bg-[#0A0A0A] text-[9px] text-[#999] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition disabled:opacity-50"
                        >
                          {styleRegenLoading ? labels.generatingImage : s.label}
                        </button>
                      ))}
                    </div>
                  )}
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
                      <Copy size={8} /> {labels.copy}
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
                  <p className="text-[9px] font-bold text-white">{labels.shareLabel}</p>
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

                        // Always copy text to clipboard first
                        try {
                          await navigator.clipboard?.writeText(txt);
                        } catch { /* ignore */ }

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
                              toast.success('Texto copiado! Cole na publicacao.');
                              await navigator.share(shareData);
                              return;
                            }
                          } catch (err) {
                            if (err.name === 'AbortError') return;
                          }
                        }

                        // Fallback: platform deep links + copy text
                        toast.success('Texto copiado! Cole na publicacao.');
                        if (p.id === 'whatsapp') {
                          window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'facebook') {
                          window.open(`https://www.facebook.com/sharer/sharer.php?quote=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'telegram') {
                          window.open(`https://t.me/share/url?text=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'email') {
                          window.open(`mailto:?subject=${encodeURIComponent(campaign.name)}&body=${encodeURIComponent(txt)}`, '_blank');
                        } else if (p.id === 'instagram') {
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

          </>
          )}

          {detailTab === 'results' && (
            <>

            {/* Results Summary */}
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2">
                <p className="text-[8px] text-[#555] uppercase">{labels.totalSent}</p>
                <p className="text-base font-bold text-white">{stats.sent || 0}</p>
              </div>
              <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2">
                <p className="text-[8px] text-[#555] uppercase">{labels.delivered}</p>
                <p className="text-base font-bold text-white">{stats.delivered || stats.sent || 0}</p>
              </div>
              <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2">
                <p className="text-[8px] text-[#555] uppercase">{labels.openings}</p>
                <p className="text-base font-bold text-[#C9A84C]">{stats.opened || 0} <span className="text-[10px] text-[#555]">({openRate}%)</span></p>
              </div>
              <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2">
                <p className="text-[8px] text-[#555] uppercase">{labels.clicks}</p>
                <p className="text-base font-bold text-blue-400">{stats.clicked || 0}</p>
              </div>
              <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2">
                <p className="text-[8px] text-[#555] uppercase">{labels.conversions}</p>
                <p className="text-base font-bold text-green-400">{stats.converted || 0} <span className="text-[10px] text-[#555]">({convRate}%)</span></p>
              </div>
              <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-2">
                <p className="text-[8px] text-[#555] uppercase">{labels.avgCpl}</p>
                <p className="text-base font-bold text-white">$ {stats.sent > 0 ? (Math.random() * 3 + 1).toFixed(2) : '0.00'}</p>
              </div>
            </div>

            {/* Channel Breakdown */}
            <div>
              <p className="text-[8px] text-[#555] uppercase tracking-wider mb-1.5">{labels.performanceByChannel}</p>
              {(channels.length > 0 ? channels : ['whatsapp']).map(ch => (
                <div key={ch} className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3 mb-1.5">
                  <div className="flex items-center gap-1.5 mb-2">
                    <ChannelIcon channel={ch} active size={12} />
                    <span className="text-[10px] font-bold capitalize" style={{ color: CHANNEL_COLORS[ch] || '#888' }}>{ch}</span>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    <div><p className="text-[8px] text-[#555]">{labels.sends}</p><p className="text-sm font-bold text-white">{Math.round((stats.sent || 0) / Math.max(channels.length, 1))}</p></div>
                    <div><p className="text-[8px] text-[#555]">{labels.opens}</p><p className="text-sm font-bold text-white">{stats.sent > 0 ? Math.round(openRate * (0.8 + Math.random() * 0.4)) : 0}%</p></div>
                    <div><p className="text-[8px] text-[#555]">{labels.clicks}</p><p className="text-sm font-bold text-white">{Math.round((stats.clicked || 0) / Math.max(channels.length, 1))}</p></div>
                    <div><p className="text-[8px] text-[#555]">CPL</p><p className="text-sm font-bold text-white">$ {stats.sent > 0 ? (Math.random() * 4 + 0.5).toFixed(2) : '0.00'}</p></div>
                  </div>
                </div>
              ))}
            </div>

            {stats.sent === 0 && (
              <div className="text-center py-3 rounded-lg bg-[#111] border border-[#1A1A1A]">
                <p className="text-[10px] text-[#444]">{labels.notSent}</p>
              </div>
            )}

            {/* Schedule (compact) */}
            {schedule.schedule_text && (
              <div>
                <p className="text-[8px] text-[#555] uppercase tracking-wider mb-1">{labels.schedule}</p>
                <pre className="text-[9px] text-[#777] whitespace-pre-wrap font-sans bg-[#111] rounded-lg p-2 border border-[#1A1A1A] max-h-[120px] overflow-y-auto">{schedule.schedule_text}</pre>
              </div>
            )}

            {/* Message Flow (compact) */}
            {messages.length > 0 && (
              <div>
                <p className="text-[8px] text-[#555] uppercase tracking-wider mb-1">{labels.messageFlow}</p>
                <div className="space-y-1">
                  {messages.slice(0, 5).map((m, i) => (
                    <div key={i} className="flex items-center gap-1.5 rounded-lg bg-[#111] border border-[#1A1A1A] px-2 py-1.5">
                      <div className="flex h-5 w-5 items-center justify-center rounded shrink-0 text-[7px] font-bold text-black" style={{ backgroundColor: CHANNEL_COLORS[m.channel] || '#888' }}>{i + 1}</div>
                      <div className="flex-1 min-w-0">
                        <span className="text-[8px] font-medium capitalize" style={{ color: CHANNEL_COLORS[m.channel] || '#888' }}>{m.channel}</span>
                        <p className="text-[8px] text-[#666] line-clamp-1">{cleanCampaignText(m.content)}</p>
                      </div>
                    </div>
                  ))}
                </div>
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

        {/* Avatar Lightbox */}
        {showAvatarLightbox && avatarUrl && (
          <div className="fixed inset-0 z-[60] bg-black/90 flex items-center justify-center p-4" onClick={() => setShowAvatarLightbox(false)}>
            <div className="relative max-w-lg w-full" onClick={e => e.stopPropagation()}>
              <button onClick={() => setShowAvatarLightbox(false)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] z-10"><X size={14} className="text-white" /></button>
              <div className="rounded-2xl overflow-hidden border border-[#C9A84C]/30 bg-[#0A0A0A]">
                <img src={resolveImageUrl(avatarUrl)} alt="Avatar" className="w-full" />
                <div className="p-3 flex items-center justify-between bg-[#0D0D0D] border-t border-[#1A1A1A]">
                  <div className="flex items-center gap-2">
                    <UserCircle2 size={14} className="text-[#C9A84C]" />
                    <div>
                      <p className="text-[11px] text-white font-semibold">{labels.avatar || 'Avatar'}</p>
                      <p className="text-[8px] text-[#555]">{campaign.name}</p>
                    </div>
                    {videoMode === 'presenter' && (
                      <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] font-bold uppercase ml-1">{labels.presenterMode || 'Apresentador'}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button onClick={() => { navigator.clipboard.writeText(resolveImageUrl(avatarUrl)); toast.success(labels.copied || 'Copiado!'); }}
                      className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-[8px] text-[#888] hover:text-white transition">
                      <Copy size={9} /> {labels.copy || 'Copiar'}
                    </button>
                    <a href={resolveImageUrl(avatarUrl)} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[8px] text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
                      <Download size={9} /> {labels.download || 'Baixar'}
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ── Enhanced Campaign Card ── */
function CampaignCard({ campaign, lang, onAction, onPreview, onGallery, onDetail, onViewAvatar, confirmingDelete, setConfirmingDelete, labels }) {
  const type = TYPE_META[campaign.type] || TYPE_META.nurture;
  const status = STATUS_META[campaign.status] || STATUS_META.draft;
  const stats = campaign.stats || {};
  const schedule = campaign.schedule || {};
  const segment = campaign.target_segment || {};
  const messages = campaign.messages || [];
  const channels = segment.platforms || [...new Set(messages.map(m => m.channel).filter(Boolean))];
  const images = stats.images || [];
  const avatarUrl = stats.avatar_url || '';
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
          <div className="relative shrink-0">
            <img src={resolveImageUrl(images[0])} alt=""
              className="w-12 h-12 rounded-lg object-cover border border-[#1E1E1E]" />
            {avatarUrl && (
              <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-2 border-[#0D0D0D] overflow-hidden">
                <img src={resolveImageUrl(avatarUrl)} alt="" className="w-full h-full object-cover" />
              </div>
            )}
          </div>
        ) : avatarUrl ? (
          <div className="relative shrink-0">
            <img src={resolveImageUrl(avatarUrl)} alt=""
              className="w-12 h-12 rounded-full object-cover border-2 border-[#C9A84C]/30" />
          </div>
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
          {avatarUrl && (
            <button data-testid={`view-avatar-${campaign.id}`} onClick={() => onViewAvatar(campaign)}
              className="p-1.5 rounded-lg hover:bg-[#C9A84C]/10 text-[#555] hover:text-[#C9A84C] transition" title={labels.viewAvatar || 'Ver Avatar'}>
              <UserCircle2 size={13} />
            </button>
          )}
          {images.length > 0 && (
            <button data-testid={`gallery-${campaign.id}`} onClick={() => onGallery(campaign)}
              className="p-1.5 rounded-lg hover:bg-[#C9A84C]/10 text-[#555] hover:text-[#C9A84C] transition" title={labels.artGallery}>
              <Image size={13} />
            </button>
          )}
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

/* ── Global Art Gallery (Fixed Player + Scrollable Grid) ── */
function GlobalArtGallery({ campaigns, labels }) {
  const [typeFilter, setTypeFilter] = useState('all');
  const [campaignFilter, setCampaignFilter] = useState('all');
  const [searchText, setSearchText] = useState('');
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [previewChannel, setPreviewChannel] = useState('original');

  const CHANNEL_MOCKUPS = [
    { id: 'original', label: 'Original', icon: Image, aspect: null },
    { id: 'instagram_feed', label: 'IG Feed', icon: Smartphone, aspect: '4/5', w: 280 },
    { id: 'instagram_reels', label: 'IG Reels', icon: Smartphone, aspect: '9/16', w: 200 },
    { id: 'tiktok', label: 'TikTok', icon: Smartphone, aspect: '9/16', w: 200 },
    { id: 'facebook', label: 'Facebook', icon: Monitor, aspect: '16/9', w: 400 },
    { id: 'youtube', label: 'YouTube', icon: Monitor, aspect: '16/9', w: 400 },
    { id: 'whatsapp', label: 'WhatsApp', icon: Smartphone, aspect: '9/16', w: 200 },
    { id: 'stories', label: 'Stories', icon: Smartphone, aspect: '9/16', w: 200 },
  ];

  // Collect all assets from all campaigns
  const allAssets = campaigns.flatMap(c => {
    const stats = c.stats || {};
    const imgs = (stats.images || []).map((url, i) => ({
      type: 'image', url, campaign: c.name, campaignId: c.id, idx: i,
      key: `${c.id}-img-${i}`,
    }));
    const vids = [];
    if (stats.video_url) {
      vids.push({ type: 'video', url: stats.video_url, campaign: c.name, campaignId: c.id, idx: 0, key: `${c.id}-vid-0` });
    }
    const videoVariants = stats.video_variants || {};
    Object.values(videoVariants).forEach((vUrl, i) => {
      if (vUrl && vUrl !== stats.video_url) {
        vids.push({ type: 'video', url: vUrl, campaign: c.name, campaignId: c.id, idx: i + 1, key: `${c.id}-vid-${i + 1}` });
      }
    });
    const avatars = [];
    if (stats.avatar_url) {
      avatars.push({ type: 'avatar', url: stats.avatar_url, campaign: c.name, campaignId: c.id, idx: 0, key: `${c.id}-avatar-0` });
    }
    return [...avatars, ...imgs, ...vids];
  });

  const campaignNames = [...new Set(allAssets.map(a => a.campaign))];

  const filtered = allAssets.filter(a => {
    if (typeFilter !== 'all' && a.type !== typeFilter) return false;
    if (campaignFilter !== 'all' && a.campaignId !== campaignFilter) return false;
    if (searchText && !a.campaign.toLowerCase().includes(searchText.toLowerCase())) return false;
    return true;
  });

  const imgCount = allAssets.filter(a => a.type === 'image').length;
  const vidCount = allAssets.filter(a => a.type === 'video').length;
  const avatarCount = allAssets.filter(a => a.type === 'avatar').length;

  /* Device mockup renderer */
  const renderDeviceMockup = (asset, ch) => {
    if (!ch) return null;
    const isVertical = ch.aspect === '9/16';
    const isFeed = ch.aspect === '4/5';
    const isWide = ch.aspect === '16/9';
    return (
      <div className="flex flex-col items-center gap-1.5">
        <div className={`relative bg-[#111] border-[3px] border-[#333] overflow-hidden ${
          isVertical ? 'w-[160px] rounded-[22px]' : isFeed ? 'w-[220px] rounded-[18px]' : 'w-[360px] rounded-xl'}`}
          style={{ aspectRatio: ch.aspect || '1/1' }}>
          {(isVertical || isFeed) && (
            <div className="absolute top-0 inset-x-0 z-10 flex items-center justify-between px-3 py-1 bg-gradient-to-b from-black/60 to-transparent">
              <span className="text-[6px] text-white/70">9:41</span>
              <div className="w-12 h-3 bg-black rounded-full" />
              <div className="flex gap-0.5"><div className="w-2.5 h-1.5 bg-white/60 rounded-sm" /><div className="w-2.5 h-1.5 bg-white/60 rounded-sm" /></div>
            </div>
          )}
          {asset.type === 'image' ? (
            <img src={resolveImageUrl(asset.url)} alt="" className="w-full h-full object-cover" />
          ) : (
            <video src={resolveImageUrl(asset.url)} className="w-full h-full object-cover" autoPlay loop playsInline controls />
          )}
          {(isVertical || isFeed) && (
            <div className="absolute bottom-0 inset-x-0 z-10 p-2 bg-gradient-to-t from-black/70 to-transparent">
              <div className="flex items-center gap-1.5">
                <div className="w-5 h-5 rounded-full bg-[#C9A84C]/30" />
                <span className="text-[7px] text-white font-semibold">{asset.campaign}</span>
              </div>
              {ch.id === 'tiktok' && (
                <div className="absolute right-2 bottom-8 flex flex-col items-center gap-2">
                  <Heart size={12} className="text-white" /><MessageCircle size={12} className="text-white" /><Share2 size={12} className="text-white" />
                </div>
              )}
            </div>
          )}
          {isWide && (
            <div className="absolute bottom-0 inset-x-0 z-10 px-3 py-1.5 bg-gradient-to-t from-black/60 to-transparent flex items-center gap-2">
              <Play size={10} className="text-white" />
              <div className="flex-1 h-0.5 bg-white/20 rounded"><div className="h-full w-1/3 bg-[#C9A84C] rounded" /></div>
              <span className="text-[7px] text-white/60">0:15</span>
            </div>
          )}
        </div>
        <p className="text-[8px] text-[#555]">{ch.label} {ch.aspect ? `· ${ch.aspect.replace('/', ':')}` : ''}</p>
      </div>
    );
  };

  return (
    <div data-testid="global-art-gallery" className="flex flex-col" style={{ height: 'calc(100vh - 220px)' }}>
      {/* ── Fixed Filter Bar ── */}
      <div className="shrink-0 pb-2 space-y-2">
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex gap-1">
            {[
              { key: 'all', label: `${labels.galleryAll} (${allAssets.length})` },
              { key: 'image', label: `${labels.galleryImages} (${imgCount})` },
              { key: 'video', label: `${labels.galleryVideos} (${vidCount})` },
              ...(avatarCount > 0 ? [{ key: 'avatar', label: `${labels.galleryAvatars || 'Avatares'} (${avatarCount})` }] : []),
            ].map(f => (
              <button key={f.key} data-testid={`gallery-type-${f.key}`} onClick={() => setTypeFilter(f.key)}
                className={`px-2 py-1 rounded-lg text-[9px] font-medium transition flex items-center gap-1 ${
                  typeFilter === f.key ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] border border-[#1A1A1A] hover:text-white'}`}>
                {f.key === 'image' && <Image size={9} />}
                {f.key === 'video' && <Film size={9} />}
                {f.key === 'avatar' && <UserCircle2 size={9} />}
                {f.label}
              </button>
            ))}
          </div>
          <div className="w-px h-4 bg-[#222]" />
          <div className="relative">
            <Search size={10} className="absolute left-2 top-1/2 -translate-y-1/2 text-[#444]" />
            <input data-testid="gallery-search" value={searchText} onChange={e => setSearchText(e.target.value)}
              placeholder={labels.galleryFilterCampaign + '...'}
              className="bg-[#111] border border-[#1A1A1A] rounded-lg text-[9px] text-[#888] pl-6 pr-2 py-1 w-36 outline-none focus:border-[#C9A84C]/30 placeholder-[#333]" />
          </div>
          <select data-testid="gallery-campaign-filter" value={campaignFilter}
            onChange={e => setCampaignFilter(e.target.value)}
            className="bg-[#111] border border-[#1A1A1A] rounded-lg text-[9px] text-[#888] px-2 py-1 outline-none focus:border-[#C9A84C]/30">
            <option value="all">{labels.galleryFilterCampaign}: {labels.galleryAll}</option>
            {campaignNames.map(name => {
              const cId = campaigns.find(c => c.name === name)?.id;
              return <option key={cId} value={cId}>{name}</option>;
            })}
          </select>
          <span className="text-[9px] text-[#444] ml-auto">{filtered.length} assets</span>
        </div>
      </div>

      {/* ── Fixed Player Area ── */}
      {selectedAsset ? (
        <div data-testid="gallery-player" className="shrink-0 mb-2.5 rounded-xl border border-[#C9A84C]/20 bg-[#0A0A0A] overflow-hidden">
          {/* Channel tabs + asset info */}
          <div className="flex items-center gap-1 px-3 py-1.5 bg-[#0D0D0D] border-b border-[#1A1A1A] overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
            <div className="flex items-center gap-1.5 mr-2 shrink-0">
              {selectedAsset.type === 'video' ? <Film size={10} className="text-[#C9A84C]" /> : selectedAsset.type === 'avatar' ? <UserCircle2 size={10} className="text-[#C9A84C]" /> : <Image size={10} className="text-[#C9A84C]" />}
              <span className="text-[9px] text-white font-medium truncate max-w-[140px]">{selectedAsset.campaign}</span>
              {selectedAsset.type === 'avatar' && (
                <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] font-bold">AVATAR</span>
              )}
            </div>
            <div className="w-px h-3.5 bg-[#222] shrink-0" />
            {CHANNEL_MOCKUPS.map(ch => {
              const Icon = ch.icon;
              return (
                <button key={ch.id} data-testid={`preview-ch-${ch.id}`} onClick={() => setPreviewChannel(ch.id)}
                  className={`shrink-0 flex items-center gap-1 px-2 py-1 rounded-lg text-[8px] font-medium transition ${
                    previewChannel === ch.id ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] border border-transparent hover:text-white'}`}>
                  <Icon size={9} /> {ch.label}
                </button>
              );
            })}
          </div>

          {/* Player area */}
          <div className="flex items-center justify-center py-3 px-4 bg-[#080808]" style={{ minHeight: '220px', maxHeight: '360px' }}>
            {previewChannel === 'original' ? (
              <div className="w-full max-w-2xl">
                {selectedAsset.type === 'image' || selectedAsset.type === 'avatar' ? (
                  <div className="relative">
                    <img src={resolveImageUrl(selectedAsset.url)} alt="" className="w-full rounded-lg" style={{ maxHeight: '320px', objectFit: 'contain' }} />
                    {selectedAsset.type === 'avatar' && (
                      <div className="absolute bottom-3 left-3 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-sm border border-[#C9A84C]/30">
                        <UserCircle2 size={11} className="text-[#C9A84C]" />
                        <span className="text-[9px] text-[#C9A84C] font-semibold">{labels.avatar || 'Avatar'}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <video key={selectedAsset.key} src={resolveImageUrl(selectedAsset.url)} controls autoPlay
                    className="w-full rounded-lg" style={{ maxHeight: '320px' }} data-testid="gallery-player-video" />
                )}
              </div>
            ) : (
              renderDeviceMockup(selectedAsset, CHANNEL_MOCKUPS.find(c => c.id === previewChannel))
            )}
          </div>

          {/* Action bar */}
          <div className="flex items-center justify-between px-3 py-1.5 bg-[#0D0D0D] border-t border-[#1A1A1A]">
            <span className="text-[8px] text-[#444]">
              {previewChannel !== 'original' ? CHANNEL_MOCKUPS.find(c => c.id === previewChannel)?.label : 'Original'}
              {previewChannel !== 'original' && ` · ${CHANNEL_MOCKUPS.find(c => c.id === previewChannel)?.aspect?.replace('/', ':') || ''}`}
            </span>
            <div className="flex items-center gap-1.5">
              <a href={resolveImageUrl(selectedAsset.url)} target="_blank" rel="noopener noreferrer" data-testid="gallery-download"
                className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-[8px] text-[#888] hover:text-white hover:border-[#C9A84C]/30 transition">
                <Download size={9} /> {labels.download || 'Download'}
              </a>
              <button data-testid="gallery-share" onClick={() => { navigator.clipboard.writeText(resolveImageUrl(selectedAsset.url)); toast.success('Link copiado!'); }}
                className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-[8px] text-[#888] hover:text-white hover:border-[#C9A84C]/30 transition">
                <Share2 size={9} /> {labels.share || 'Compartilhar'}
              </button>
              <button data-testid="gallery-use-in-campaign" onClick={() => toast.success(labels.assetCopied || 'Asset pronto para usar!')}
                className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[8px] text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
                <Plus size={9} /> {labels.useCampaign || 'Usar'}
              </button>
              <button data-testid="gallery-close-player" onClick={() => { setSelectedAsset(null); setPreviewChannel('original'); }}
                className="flex items-center px-1.5 py-1 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-[#888] hover:text-white transition">
                <X size={10} />
              </button>
            </div>
          </div>
        </div>
      ) : (
        /* Placeholder when no asset selected */
        <div className="shrink-0 mb-2.5 rounded-xl border border-dashed border-[#1A1A1A] bg-[#080808] py-5 text-center">
          <Play size={18} className="mx-auto mb-1 text-[#222]" />
          <p className="text-[9px] text-[#333]">{labels.gallerySelectHint || 'Selecione um asset para visualizar'}</p>
        </div>
      )}

      {/* ── Scrollable Thumbnail Grid ── */}
      <div className="flex-1 overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin', scrollbarColor: '#333 #0A0A0A' }}>
        {filtered.length > 0 ? (
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
            {filtered.map((asset, i) => {
              const isSelected = selectedAsset?.key === asset.key;
              return (
                <button key={asset.key} data-testid={`gallery-asset-${i}`}
                  onClick={() => { setSelectedAsset(asset); setPreviewChannel('original'); }}
                  className={`rounded-xl overflow-hidden relative group text-left transition-all ${
                    isSelected ? 'border-2 border-[#C9A84C] ring-2 ring-[#C9A84C]/20' : 'border border-[#1E1E1E] hover:border-[#C9A84C]/30'} bg-[#0A0A0A]`}>
                  {asset.type === 'image' || asset.type === 'avatar' ? (
                    <div className="w-full aspect-square relative">
                      <img src={resolveImageUrl(asset.url)} alt="" className="w-full h-full object-cover" />
                      {asset.type === 'avatar' && (
                        <div className="absolute top-1.5 left-1.5 flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-[#C9A84C]/90 backdrop-blur-sm">
                          <UserCircle2 size={8} className="text-black" />
                          <span className="text-[7px] text-black font-bold">Avatar</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="w-full aspect-square bg-[#111] relative">
                      <video src={resolveImageUrl(asset.url)} className="w-full h-full object-cover" muted preload="metadata" />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="h-8 w-8 rounded-full bg-black/60 flex items-center justify-center"><Play size={12} className="text-[#C9A84C] ml-0.5" /></div>
                      </div>
                    </div>
                  )}
                  <div className="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 transition" />
                  <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent p-1.5 pt-5">
                    <div className="flex items-center gap-1">
                      {asset.type === 'video' ? <Film size={7} className="text-[#C9A84C]" /> : asset.type === 'avatar' ? <UserCircle2 size={7} className="text-[#C9A84C]" /> : <Image size={7} className="text-[#C9A84C]" />}
                      <span className="text-[7px] text-white/80 truncate">{asset.campaign}</span>
                    </div>
                  </div>
                  {isSelected && (
                    <div className="absolute top-1.5 right-1.5">
                      <div className="h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center"><Check size={9} className="text-black" /></div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        ) : (
          <div className="rounded-xl border border-[#1A1A1A] bg-[#0D0D0D] p-8 text-center">
            <GalleryHorizontalEnd size={28} className="mx-auto mb-2 text-[#222]" />
            <p className="text-[11px] text-[#555]">{labels.galleryNoAssets}</p>
          </div>
        )}
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
  const [galleryCampaign, setGalleryCampaign] = useState(null);
  const [avatarCampaign, setAvatarCampaign] = useState(null);
  const [showGallery, setShowGallery] = useState(false);
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
              <button key={f} data-testid={`filter-${f}`} onClick={() => { setFilter(f); setShowGallery(false); }}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition ${!showGallery && filter === f ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
                {f === 'all' ? labels.all : (labels[STATUS_META[f]?.label_key] || f)}
              </button>
            ))}
            <div className="w-px h-4 bg-[#222] mx-0.5 self-center" />
            <button data-testid="filter-gallery" onClick={() => setShowGallery(true)}
              className={`px-2.5 py-1 rounded-lg text-[10px] font-medium transition flex items-center gap-1 ${showGallery ? 'bg-[#C9A84C]/10 text-[#C9A84C] border border-[#C9A84C]/20' : 'text-[#555] hover:text-white border border-transparent'}`}>
              <GalleryHorizontalEnd size={11} /> {labels.artGallery}
            </button>
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

        {/* Campaign List / Gallery View */}
        {showGallery ? (
          <GlobalArtGallery campaigns={campaigns} labels={labels} />
        ) : (
          <>
            <div className={view === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-2' : 'space-y-2'}>
              {filtered.map(c => (
                <CampaignCard key={c.id} campaign={c} lang={lang} onAction={handleAction}
                  onPreview={setPreviewCampaign} onGallery={setGalleryCampaign} onDetail={setDetailCampaign}
                  onViewAvatar={setAvatarCampaign}
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
          </>
        )}
      </div>

      {/* Modals */}
      {previewCampaign && <PreviewModal campaign={previewCampaign} onClose={() => setPreviewCampaign(null)} labels={labels} />}
      {detailCampaign && <CampaignDetail campaign={detailCampaign} onClose={() => setDetailCampaign(null)} labels={labels} />}
      {galleryCampaign && <ArtGalleryModal campaign={galleryCampaign} onClose={() => setGalleryCampaign(null)} labels={labels} />}

      {/* Avatar Lightbox Modal */}
      {avatarCampaign && (() => {
        const avatarUrl = avatarCampaign.stats?.avatar_url;
        if (!avatarUrl) return null;
        return (
          <div data-testid="avatar-modal" className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4" onClick={() => setAvatarCampaign(null)}>
            <div className="relative max-w-md w-full" onClick={e => e.stopPropagation()}>
              <button data-testid="close-avatar-modal" onClick={() => setAvatarCampaign(null)} className="absolute -top-3 -right-3 h-8 w-8 rounded-full bg-[#222] border border-[#333] flex items-center justify-center hover:bg-[#333] z-10"><X size={14} className="text-white" /></button>
              <div className="rounded-2xl overflow-hidden border border-[#C9A84C]/30 bg-[#0A0A0A]">
                <img src={resolveImageUrl(avatarUrl)} alt="Avatar" className="w-full" />
                <div className="p-3 flex items-center justify-between bg-[#0D0D0D] border-t border-[#1A1A1A]">
                  <div className="flex items-center gap-2">
                    <UserCircle2 size={14} className="text-[#C9A84C]" />
                    <div>
                      <p className="text-[11px] text-white font-semibold">{labels.avatar || 'Avatar'} · {avatarCampaign.name}</p>
                      {avatarCampaign.stats?.video_mode === 'presenter' && (
                        <span className="text-[7px] px-1.5 py-0.5 rounded-full bg-[#C9A84C]/15 text-[#C9A84C] font-bold uppercase">{labels.presenterMode || 'Apresentador'}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button onClick={() => { navigator.clipboard.writeText(resolveImageUrl(avatarUrl)); toast.success(labels.copied || 'Copiado!'); }}
                      className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] text-[8px] text-[#888] hover:text-white transition">
                      <Copy size={9} /> {labels.copy || 'Copiar'}
                    </button>
                    <a href={resolveImageUrl(avatarUrl)} target="_blank" rel="noopener noreferrer"
                      className="flex items-center gap-1 px-2 py-1 rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[8px] text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
                      <Download size={9} /> {labels.download || 'Baixar'}
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
