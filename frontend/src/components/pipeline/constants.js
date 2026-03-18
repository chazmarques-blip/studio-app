import { PenTool, Palette, CheckCircle, CalendarClock, Award, Film } from 'lucide-react';

function cleanDisplayText(raw) {
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
  text = text.replace(/={3,}.*?={3,}/g, '');
  text = text.replace(/^-{3,}\s*$/gm, '');
  text = text.replace(/\n{3,}/g, '\n\n').trim();
  return text;
}

const STEP_META = {
  sofia_copy: { agent: 'David', role: 'Copywriter', icon: PenTool, color: '#C9A84C', estimatedSec: 30 },
  ana_review_copy: { agent: 'Lee', role: 'Creative Director', icon: CheckCircle, color: '#4CAF50', estimatedSec: 20 },
  lucas_design: { agent: 'Stefan', role: 'Visual Designer', icon: Palette, color: '#7CB9E8', estimatedSec: 120 },
  rafael_review_design: { agent: 'George', role: 'Art Director', icon: Award, color: '#9B59B6', estimatedSec: 25 },
  marcos_video: { agent: 'Ridley', role: 'Video Director', icon: Film, color: '#E74C3C', estimatedSec: 500 },
  rafael_review_video: { agent: 'Roger', role: 'Video Reviewer', icon: Award, color: '#9B59B6', estimatedSec: 25 },
  pedro_publish: { agent: 'Gary', role: 'Campaign Validator', icon: CalendarClock, color: '#E8A87C', estimatedSec: 25 },
};

const STEP_ORDER = ['sofia_copy', 'ana_review_copy', 'lucas_design', 'rafael_review_design', 'marcos_video', 'rafael_review_video', 'pedro_publish'];

const PLATFORMS = [
  { id: 'whatsapp', label: 'WhatsApp', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '768x1344' },
  { id: 'instagram', label: 'Instagram', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '768x1344' },
  { id: 'facebook', label: 'Facebook', imgRatio: '1:1', vidRatio: '16:9', imgSize: '1024x1024', vidSize: '1280x720' },
  { id: 'tiktok', label: 'TikTok', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '768x1344' },
  { id: 'google_ads', label: 'Google Ads', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1280x720' },
  { id: 'telegram', label: 'Telegram', imgRatio: '1:1', vidRatio: '16:9', imgSize: '1024x1024', vidSize: '1280x720' },
  { id: 'email', label: 'Email', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1280x720' },
  { id: 'sms', label: 'SMS', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '768x1344' },
];

export { cleanDisplayText, STEP_META, STEP_ORDER, PLATFORMS };
