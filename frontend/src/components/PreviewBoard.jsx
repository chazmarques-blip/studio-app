import { useState } from 'react';
import { Eye, Palette, MapPin, Film, Music, Volume2, Sparkles, RefreshCw, Clapperboard, ChevronDown, ChevronUp, Clock } from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';

/**
 * PreviewBoard — Shows the Production Design Document visually before starting production.
 * Allows users to review character appearance, locations, style, music plan, and scene flow.
 */
export function PreviewBoard({ productionDesign, avatarDescriptions, characters, characterAvatars, scenes, lang = 'pt', previewTime, onApprove, onRegenerate, regenerating }) {
  const [expandedSection, setExpandedSection] = useState('characters');

  if (!productionDesign) return null;

  const pd = productionDesign;
  const charBible = pd.character_bible || {};
  const locBible = pd.location_bible || {};
  const sceneDirs = pd.scene_directions || [];
  const musicPlan = pd.music_plan || [];
  const voicePlan = pd.voice_plan || [];
  const colorPalette = pd.color_palette || {};

  const toggle = (key) => setExpandedSection(prev => prev === key ? null : key);

  const SectionHeader = ({ id, icon: Icon, title, count }) => (
    <button onClick={() => toggle(id)} data-testid={`preview-section-${id}`}
      className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-[#0A0A0A] border border-[#1A1A1A] hover:border-[#8B5CF6]/20 transition group">
      <div className="flex items-center gap-2">
        <Icon size={12} className="text-[#8B5CF6]" />
        <span className="text-[10px] font-semibold text-white">{title}</span>
        {count !== undefined && <span className="text-[8px] text-[#555] bg-[#1A1A1A] rounded-full px-1.5 py-0.5">{count}</span>}
      </div>
      {expandedSection === id ? <ChevronUp size={12} className="text-[#555]" /> : <ChevronDown size={12} className="text-[#555]" />}
    </button>
  );

  const TIME_COLORS = { morning: '#F59E0B', afternoon: '#F97316', sunset: '#EF4444', night: '#6366F1' };
  const TIME_LABELS = { morning: lang === 'pt' ? 'Manhã' : 'Morning', afternoon: lang === 'pt' ? 'Tarde' : 'Afternoon', sunset: lang === 'pt' ? 'Pôr-do-sol' : 'Sunset', night: lang === 'pt' ? 'Noite' : 'Night' };

  return (
    <div className="space-y-2" data-testid="preview-board">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Eye size={14} className="text-[#8B5CF6]" />
          <h3 className="text-xs font-bold text-white">{lang === 'pt' ? 'Design de Produção' : 'Production Design'}</h3>
          {previewTime && (
            <span className="text-[7px] text-[#555] flex items-center gap-0.5"><Clock size={8} /> {previewTime}s</span>
          )}
        </div>
        <span className="text-[7px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-2 py-0.5">
          {lang === 'pt' ? 'Pronto para revisão' : 'Ready for review'}
        </span>
      </div>

      {/* Style Anchors */}
      {pd.style_anchors && (
        <div className="rounded-lg border border-[#8B5CF6]/20 bg-[#8B5CF6]/5 p-2.5" data-testid="preview-style-anchors">
          <div className="flex items-center gap-1.5 mb-1">
            <Sparkles size={10} className="text-[#8B5CF6]" />
            <span className="text-[9px] font-semibold text-[#8B5CF6]">{lang === 'pt' ? 'Estilo Visual (em cada cena)' : 'Visual Style (every scene)'}</span>
          </div>
          <p className="text-[9px] text-[#CCC] leading-relaxed italic">"{pd.style_anchors}"</p>
        </div>
      )}

      {/* Color Palette */}
      {Object.keys(colorPalette).length > 0 && (
        <div className="rounded-lg border border-[#1A1A1A] bg-[#0A0A0A] p-2.5" data-testid="preview-color-palette">
          <div className="flex items-center gap-1.5 mb-2">
            <Palette size={10} className="text-[#8B5CF6]" />
            <span className="text-[9px] font-semibold text-white">{lang === 'pt' ? 'Paleta de Cores & Iluminação' : 'Color Palette & Lighting'}</span>
          </div>
          {colorPalette.global && (
            <p className="text-[8px] text-[#888] mb-1.5">{colorPalette.global}</p>
          )}
          <div className="grid grid-cols-4 gap-1.5">
            {['morning', 'afternoon', 'sunset', 'night'].map(time => colorPalette[time] && (
              <div key={time} className="rounded-md p-1.5 text-center" style={{ backgroundColor: `${TIME_COLORS[time]}10`, border: `1px solid ${TIME_COLORS[time]}30` }}>
                <div className="w-4 h-4 rounded-full mx-auto mb-1" style={{ backgroundColor: TIME_COLORS[time], opacity: 0.7 }} />
                <p className="text-[7px] font-bold" style={{ color: TIME_COLORS[time] }}>{TIME_LABELS[time]}</p>
                <p className="text-[6px] text-[#888] mt-0.5 leading-tight">{colorPalette[time]}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Character Bible */}
      <SectionHeader id="characters" icon={Eye} title={lang === 'pt' ? 'Bíblia de Personagens' : 'Character Bible'} count={Object.keys(charBible).length} />
      {expandedSection === 'characters' && (
        <div className="space-y-1.5 pl-1" data-testid="preview-characters">
          {Object.entries(charBible).map(([name, desc]) => {
            const char = characters.find(c => c.name === name);
            const avatarUrl = characterAvatars[name];
            const origDesc = char?.description || '';
            return (
              <div key={name} className="flex gap-2.5 rounded-lg border border-[#1A1A1A] bg-[#0A0A0A] p-2">
                {/* Avatar */}
                {avatarUrl ? (
                  <img src={resolveImageUrl(avatarUrl)} alt={name} className="h-16 w-14 rounded-lg object-cover border border-[#8B5CF6]/30 flex-shrink-0" />
                ) : (
                  <div className="h-16 w-14 rounded-lg bg-[#111] flex items-center justify-center border border-dashed border-[#333] flex-shrink-0">
                    <span className="text-[14px] text-[#444]">?</span>
                  </div>
                )}
                {/* Details */}
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] font-bold text-white">{name}</p>
                  <div className="mt-1 rounded bg-[#8B5CF6]/5 border border-[#8B5CF6]/15 px-2 py-1">
                    <p className="text-[7px] text-[#8B5CF6] font-semibold mb-0.5">{lang === 'pt' ? 'DESCRIÇÃO CANÔNICA (Sora 2 usará)' : 'CANONICAL (Sora 2 will use)'}</p>
                    <p className="text-[8px] text-[#CCC] leading-relaxed">{desc}</p>
                  </div>
                  {origDesc && origDesc !== desc && (
                    <div className="mt-1 rounded bg-[#111] px-2 py-1">
                      <p className="text-[7px] text-[#555] font-semibold mb-0.5">{lang === 'pt' ? 'Original (roteirista)' : 'Original (screenwriter)'}</p>
                      <p className="text-[7px] text-[#666] leading-relaxed">{origDesc}</p>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Locations */}
      {Object.keys(locBible).length > 0 && (
        <>
          <SectionHeader id="locations" icon={MapPin} title={lang === 'pt' ? 'Locações' : 'Locations'} count={Object.keys(locBible).length} />
          {expandedSection === 'locations' && (
            <div className="grid grid-cols-2 gap-1.5 pl-1" data-testid="preview-locations">
              {Object.entries(locBible).map(([key, desc]) => (
                <div key={key} className="rounded-lg border border-[#1A1A1A] bg-[#0A0A0A] p-2">
                  <p className="text-[9px] font-bold text-[#8B5CF6] mb-0.5">{key}</p>
                  <p className="text-[8px] text-[#999] leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Scene Flow */}
      {sceneDirs.length > 0 && (
        <>
          <SectionHeader id="scenes" icon={Film} title={lang === 'pt' ? 'Fluxo de Cenas' : 'Scene Flow'} count={sceneDirs.length} />
          {expandedSection === 'scenes' && (
            <div className="space-y-1 pl-1 max-h-[250px] overflow-y-auto hide-scrollbar" data-testid="preview-scene-flow">
              {sceneDirs.map((sd, i) => {
                const scene = scenes.find(s => s.scene_number === sd.scene) || scenes[i] || {};
                const timeColor = TIME_COLORS[sd.time_of_day] || '#888';
                return (
                  <div key={i} className="flex items-start gap-2 rounded-md border border-[#1A1A1A] bg-[#0A0A0A] p-2">
                    {/* Scene number */}
                    <div className="flex flex-col items-center flex-shrink-0">
                      <span className="text-[10px] font-bold text-[#8B5CF6]">{sd.scene}</span>
                      <div className="w-3 h-3 rounded-full mt-0.5" style={{ backgroundColor: timeColor, opacity: 0.6 }} />
                    </div>
                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <p className="text-[9px] font-semibold text-white truncate">{scene.title || `Scene ${sd.scene}`}</p>
                        <span className="text-[6px] rounded-full px-1.5 py-0.5 font-bold" style={{ color: timeColor, backgroundColor: `${timeColor}15`, border: `1px solid ${timeColor}30` }}>
                          {TIME_LABELS[sd.time_of_day] || sd.time_of_day}
                        </span>
                      </div>
                      {sd.camera_flow && <p className="text-[7px] text-[#777] mt-0.5">📷 {sd.camera_flow}</p>}
                      {sd.transition_note && <p className="text-[7px] text-[#555] mt-0.5 italic">↔ {sd.transition_note}</p>}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}

      {/* Music Plan */}
      {musicPlan.length > 0 && (
        <>
          <SectionHeader id="music" icon={Music} title={lang === 'pt' ? 'Plano Musical' : 'Music Plan'} count={musicPlan.length} />
          {expandedSection === 'music' && (
            <div className="space-y-1 pl-1" data-testid="preview-music-plan">
              {musicPlan.map((mp, i) => (
                <div key={i} className="flex items-center gap-2 rounded-md border border-[#1A1A1A] bg-[#0A0A0A] p-2">
                  <Music size={10} className="text-[#8B5CF6] flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[8px] font-bold text-white">
                        {lang === 'pt' ? 'Cenas' : 'Scenes'} {(mp.scenes || []).join(', ')}
                      </span>
                      <span className="text-[7px] text-[#8B5CF6] bg-[#8B5CF6]/10 rounded px-1 py-0.5">{mp.category || mp.mood}</span>
                      <span className={`text-[6px] rounded px-1 py-0.5 ${mp.intensity === 'high' ? 'text-red-400 bg-red-500/10' : mp.intensity === 'medium' ? 'text-yellow-400 bg-yellow-500/10' : 'text-emerald-400 bg-emerald-500/10'}`}>
                        {mp.intensity}
                      </span>
                    </div>
                    <p className="text-[7px] text-[#888] mt-0.5">{mp.mood}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Voice Plan */}
      {voicePlan.length > 0 && (
        <>
          <SectionHeader id="voice" icon={Volume2} title={lang === 'pt' ? 'Direção de Voz' : 'Voice Direction'} count={voicePlan.length} />
          {expandedSection === 'voice' && (
            <div className="flex flex-wrap gap-1 pl-1" data-testid="preview-voice-plan">
              {voicePlan.map((vp, i) => (
                <div key={i} className="rounded-md border border-[#1A1A1A] bg-[#0A0A0A] px-2 py-1 text-center">
                  <span className="text-[8px] font-bold text-[#8B5CF6]">C{vp.scene}</span>
                  <p className="text-[7px] text-[#999]">{vp.tone}</p>
                  <p className="text-[6px] text-[#555]">{vp.pace}</p>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* Action Buttons */}
      <div className="flex gap-2 pt-1" data-testid="preview-actions">
        <button onClick={onRegenerate} disabled={regenerating}
          data-testid="preview-regenerate-btn"
          className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white hover:border-[#555] transition flex items-center justify-center gap-1 disabled:opacity-30">
          {regenerating ? <RefreshCw size={10} className="animate-spin" /> : <RefreshCw size={10} />}
          {lang === 'pt' ? 'Regenerar Preview' : 'Regenerate Preview'}
        </button>
        <button onClick={onApprove} disabled={regenerating}
          data-testid="preview-approve-btn"
          className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-semibold flex items-center justify-center gap-1 disabled:opacity-30">
          <Clapperboard size={12} /> {lang === 'pt' ? 'Aprovar & Produzir' : 'Approve & Produce'}
        </button>
      </div>
    </div>
  );
}
