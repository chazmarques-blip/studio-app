import { PenTool, Palette, CheckCircle, CalendarClock, Award, Film, Headphones } from 'lucide-react';

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
  // Remove framework/direction tags from copy (ANTES:, DEPOIS:, A PONTE:, HOOK:, BUILD:, etc.)
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
  text = text.replace(/={3,}.*?={3,}/g, '');
  text = text.replace(/^-{3,}\s*$/gm, '');
  text = text.replace(/\n{3,}/g, '\n\n').trim();
  return text;
}

const STEP_META = {
  sofia_copy: { agent: 'David', role: 'Copywriter', icon: PenTool, color: '#8B5CF6', estimatedSec: 30 },
  ana_review_copy: { agent: 'Lee', role: 'Creative Director', icon: CheckCircle, color: '#4CAF50', estimatedSec: 20 },
  lucas_design: { agent: 'Stefan', role: 'Visual Designer', icon: Palette, color: '#7CB9E8', estimatedSec: 120 },
  rafael_review_design: { agent: 'George', role: 'Art Director', icon: Award, color: '#9B59B6', estimatedSec: 25 },
  dylan_sound: { agent: 'Dylan', role: 'Sound Director', icon: Headphones, color: '#E91E63', estimatedSec: 15 },
  marcos_video: { agent: 'Ridley', role: 'Video Director', icon: Film, color: '#E74C3C', estimatedSec: 500 },
  rafael_review_video: { agent: 'Roger', role: 'Video Reviewer', icon: Award, color: '#9B59B6', estimatedSec: 25 },
  pedro_publish: { agent: 'Gary', role: 'Campaign Validator', icon: CalendarClock, color: '#E8A87C', estimatedSec: 25 },
};

const STEP_ORDER = ['sofia_copy', 'ana_review_copy', 'lucas_design', 'rafael_review_design', 'dylan_sound', 'marcos_video', 'rafael_review_video', 'pedro_publish'];

const PLATFORMS = [
  { id: 'whatsapp', label: 'WhatsApp', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '1080x1920' },
  { id: 'instagram', label: 'Instagram Feed', imgRatio: '4:5', vidRatio: '4:5', imgSize: '864x1080', vidSize: '1080x1350', subFormats: ['instagram_reels'] },
  { id: 'instagram_reels', label: 'Instagram Reels', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '1080x1920', parent: 'instagram' },
  { id: 'facebook', label: 'Facebook Feed', imgRatio: '1:1', vidRatio: '16:9', imgSize: '1024x1024', vidSize: '1280x720', subFormats: ['facebook_stories'] },
  { id: 'facebook_stories', label: 'Facebook Stories', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '1080x1920', parent: 'facebook' },
  { id: 'tiktok', label: 'TikTok', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '1080x1920' },
  { id: 'youtube', label: 'YouTube', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1920x1080', subFormats: ['youtube_shorts'] },
  { id: 'youtube_shorts', label: 'YouTube Shorts', imgRatio: '9:16', vidRatio: '9:16', imgSize: '768x1344', vidSize: '1080x1920', parent: 'youtube' },
  { id: 'google_ads', label: 'Google Ads', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1920x1080' },
  { id: 'telegram', label: 'Telegram', imgRatio: '1:1', vidRatio: '16:9', imgSize: '1024x1024', vidSize: '1280x720' },
  { id: 'email', label: 'Email', imgRatio: '16:9', vidRatio: '16:9', imgSize: '1344x768', vidSize: '1280x720' },
  { id: 'sms', label: 'SMS', imgRatio: '1:1', vidRatio: '9:16', imgSize: '1024x1024', vidSize: '1080x1920' },
];

export { cleanDisplayText, STEP_META, STEP_ORDER, PLATFORMS };
