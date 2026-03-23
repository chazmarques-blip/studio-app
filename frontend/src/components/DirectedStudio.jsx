import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import { Upload, Mic, Music, Play, Pause, Image, Film, Users, Sparkles, Download, X, ChevronDown, Plus, Volume2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function DirectedStudio() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language?.substring(0, 2) || 'en';

  // State
  const [step, setStep] = useState(1); // 1=avatars, 2=assets+briefing, 3=voice+music, 4=generate
  const [avatarGallery, setAvatarGallery] = useState([]);
  const [selectedAvatars, setSelectedAvatars] = useState([]);
  const [assets, setAssets] = useState([]);
  const [briefing, setBriefing] = useState('');
  const [sceneType, setSceneType] = useState('single_image');
  const [voices, setVoices] = useState([]);
  const [musicTracks, setMusicTracks] = useState([]);
  const [avatarVoices, setAvatarVoices] = useState({});
  const [selectedMusic, setSelectedMusic] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [outputs, setOutputs] = useState([]);
  const [showVoiceDropdown, setShowVoiceDropdown] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(null);
  const [voiceTexts, setVoiceTexts] = useState({});
  const [generatingVoice, setGeneratingVoice] = useState(null);
  const [generatedAudios, setGeneratedAudios] = useState({});
  const audioRef = useRef(null);
  const fileInputRef = useRef(null);

  // Load data — presenter avatars from AI Studio, not profile avatars
  useEffect(() => {
    axios.get(`${API}/data/avatars`).then(r => {
      const avatars = Array.isArray(r.data) ? r.data : [];
      setAvatarGallery(avatars.map(a => ({ url: a.url, label: a.name || '', id: a.id })));
    }).catch(() => {});
    axios.get(`${API}/studio/voices`).then(r => setVoices(r.data.voices || [])).catch(() => {});
    axios.get(`${API}/studio/music-library`).then(r => setMusicTracks(r.data.tracks || [])).catch(() => {});
  }, []);

  const toggleAvatar = (url) => {
    setSelectedAvatars(prev =>
      prev.includes(url) ? prev.filter(u => u !== url) : [...prev, url]
    );
  };

  const handleAssetUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onload = () => setAssets(prev => [...prev, { url: reader.result, name: file.name }]);
      reader.readAsDataURL(file);
    });
  };

  const handleGenerate = async () => {
    if (!selectedAvatars.length) { toast.error('Select at least one avatar'); return; }
    if (!briefing.trim()) { toast.error('Add a scene description'); return; }
    setGenerating(true);
    try {
      const projRes = await axios.post(`${API}/studio/projects`, {
        name: `Studio ${new Date().toLocaleString()}`,
        scene_type: sceneType,
        briefing,
        avatar_urls: selectedAvatars,
        asset_urls: assets.map(a => a.url),
        voice_config: avatarVoices,
        music_config: selectedMusic ? { track_id: selectedMusic } : {},
        language: lang,
      });
      const project = projRes.data;

      const genRes = await axios.post(`${API}/studio/generate-image`, {
        project_id: project.id,
        scene_prompt: briefing,
      });
      setOutputs(prev => [genRes.data.output, ...prev]);
      toast.success(lang === 'pt' ? 'Cena gerada!' : 'Scene generated!');
      setStep(4);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateVoice = async (avatarIdx) => {
    const text = voiceTexts[avatarIdx];
    const voiceId = avatarVoices[avatarIdx]?.voice_id;
    if (!text || !voiceId) { toast.error('Select voice and enter text'); return; }
    setGeneratingVoice(avatarIdx);
    try {
      const res = await axios.post(`${API}/studio/generate-voice`, {
        text, voice_id: voiceId, language: lang,
      });
      setGeneratedAudios(prev => ({ ...prev, [avatarIdx]: res.data.audio_url }));
      toast.success(lang === 'pt' ? 'Voz gerada!' : 'Voice generated!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Voice generation failed');
    } finally {
      setGeneratingVoice(null);
    }
  };

  const playAudio = (url) => {
    if (playingAudio === url) {
      audioRef.current?.pause();
      setPlayingAudio(null);
    } else {
      if (audioRef.current) audioRef.current.pause();
      audioRef.current = new Audio(url);
      audioRef.current.play();
      audioRef.current.onended = () => setPlayingAudio(null);
      setPlayingAudio(url);
    }
  };

  const STEPS = [
    { n: 1, icon: Users, label: lang === 'pt' ? 'Avatares' : 'Avatars' },
    { n: 2, icon: Image, label: lang === 'pt' ? 'Cena' : 'Scene' },
    { n: 3, icon: Mic, label: lang === 'pt' ? 'Voz & Música' : 'Voice & Music' },
    { n: 4, icon: Sparkles, label: lang === 'pt' ? 'Resultado' : 'Result' },
  ];

  return (
    <div className="space-y-4" data-testid="directed-studio">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-1">
        {STEPS.map((s, i) => (
          <div key={s.n} className="flex items-center">
            <button onClick={() => setStep(s.n)} data-testid={`studio-step-${s.n}`}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-medium transition ${
                step === s.n ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#666] hover:text-[#999]'
              }`}>
              <s.icon size={12} />
              <span className="hidden sm:inline">{s.label}</span>
            </button>
            {i < STEPS.length - 1 && <div className="w-4 h-px bg-[#333] mx-1" />}
          </div>
        ))}
      </div>

      {/* Step 1: Avatar Selection */}
      {step === 1 && (
        <div className="glass-card p-4 space-y-3" data-testid="studio-step-avatars">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">
              {lang === 'pt' ? 'Selecione os Avatares' : 'Select Avatars'}
            </h3>
            <span className="text-[10px] text-[#C9A84C]">{selectedAvatars.length} {lang === 'pt' ? 'selecionado(s)' : 'selected'}</span>
          </div>
          <p className="text-[10px] text-[#666]">
            {lang === 'pt' ? 'Escolha 1 ou mais avatares para a cena. Para interação, selecione 2+' : 'Pick 1 or more avatars for the scene. For interaction, select 2+'}
          </p>

          {avatarGallery.length === 0 ? (
            <div className="text-center py-6">
              <Users size={24} className="mx-auto text-[#333] mb-2" />
              <p className="text-xs text-[#666]">{lang === 'pt' ? 'Nenhum avatar criado. Crie no AI Studio (modo auto).' : 'No avatars yet. Create one in AI Studio (auto mode).'}</p>
            </div>
          ) : (
            <div className="grid grid-cols-4 sm:grid-cols-6 gap-2">
              {avatarGallery.map((av, i) => {
                const selected = selectedAvatars.includes(av.url);
                return (
                  <button key={av.id || i} onClick={() => toggleAvatar(av.url)} data-testid={`studio-avatar-${i}`}
                    className={`relative rounded-xl overflow-hidden aspect-[3/4] transition-all ${
                      selected ? 'ring-2 ring-[#C9A84C] scale-95' : 'ring-1 ring-white/5 hover:ring-white/20'
                    }`}>
                    <img src={av.url} alt={av.label} className="w-full h-full object-cover" />
                    {selected && (
                      <div className="absolute top-1 right-1 h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center">
                        <span className="text-[8px] text-black font-bold">{selectedAvatars.indexOf(av.url) + 1}</span>
                      </div>
                    )}
                    {av.label && (
                      <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/80 to-transparent px-1 py-1">
                        <span className="text-[7px] text-white/80 truncate block">{av.label}</span>
                      </div>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          <button onClick={() => setStep(2)} disabled={!selectedAvatars.length}
            className="btn-gold w-full rounded-lg py-2 text-xs font-semibold disabled:opacity-30" data-testid="studio-next-1">
            {lang === 'pt' ? 'Próximo: Cena' : 'Next: Scene'} →
          </button>
        </div>
      )}

      {/* Step 2: Scene Setup */}
      {step === 2 && (
        <div className="glass-card p-4 space-y-3" data-testid="studio-step-scene">
          <h3 className="text-sm font-semibold text-white">
            {lang === 'pt' ? 'Configure a Cena' : 'Set Up Scene'}
          </h3>

          {/* Scene type */}
          <div className="flex gap-2">
            {[
              { id: 'single_image', icon: Image, label: lang === 'pt' ? 'Imagem' : 'Image' },
              { id: 'multi_avatar_image', icon: Users, label: lang === 'pt' ? 'Multi-Avatar' : 'Multi-Avatar' },
              { id: 'video_scene', icon: Film, label: lang === 'pt' ? 'Vídeo' : 'Video' },
            ].map(st => (
              <button key={st.id} onClick={() => setSceneType(st.id)} data-testid={`scene-type-${st.id}`}
                className={`flex-1 flex items-center justify-center gap-1.5 rounded-lg border py-2 text-[10px] font-medium transition ${
                  sceneType === st.id ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#222] bg-[#111] text-[#666] hover:border-[#333]'
                }`}>
                <st.icon size={12} /> {st.label}
              </button>
            ))}
          </div>

          {/* Briefing */}
          <div>
            <label className="mb-1 block text-[10px] font-semibold text-[#777] uppercase tracking-wider">
              {lang === 'pt' ? 'Descrição da Cena' : 'Scene Description'}
            </label>
            <textarea value={briefing} onChange={e => setBriefing(e.target.value)} rows={3} data-testid="studio-briefing"
              placeholder={lang === 'pt' ? 'Descreva a cena que deseja criar... Ex: "Meu avatar apresentando o novo produto em um cenário futurístico"' : 'Describe the scene you want to create...'}
              className="w-full rounded-lg border border-[#222] bg-[#111] px-3 py-2 text-xs text-white placeholder-[#555] outline-none resize-none transition focus:border-[#C9A84C]/40" />
          </div>

          {/* Asset upload */}
          <div>
            <label className="mb-1 block text-[10px] font-semibold text-[#777] uppercase tracking-wider">
              {lang === 'pt' ? 'Assets (Opcional)' : 'Assets (Optional)'}
            </label>
            <div className="flex gap-2 flex-wrap">
              {assets.map((a, i) => (
                <div key={i} className="relative h-14 w-14 rounded-lg overflow-hidden ring-1 ring-white/10">
                  <img src={a.url} alt="" className="w-full h-full object-cover" />
                  <button onClick={() => setAssets(prev => prev.filter((_, j) => j !== i))}
                    className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-black/60 flex items-center justify-center">
                    <X size={8} className="text-white" />
                  </button>
                </div>
              ))}
              <button onClick={() => fileInputRef.current?.click()} data-testid="studio-upload-asset"
                className="h-14 w-14 rounded-lg border border-dashed border-[#333] flex items-center justify-center text-[#555] hover:border-[#C9A84C]/30 hover:text-[#C9A84C] transition">
                <Plus size={16} />
              </button>
              <input ref={fileInputRef} type="file" accept="image/*" multiple className="hidden" onChange={handleAssetUpload} />
            </div>
          </div>

          {/* Selected avatars preview */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#666]">{lang === 'pt' ? 'Avatares:' : 'Avatars:'}</span>
            {selectedAvatars.map((url, i) => (
              <div key={i} className="h-8 w-8 rounded-full overflow-hidden ring-1 ring-[#C9A84C]/30">
                <img src={url} alt="" className="w-full h-full object-cover" />
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <button onClick={() => setStep(1)} className="flex-1 rounded-lg border border-[#333] py-2 text-xs text-[#999] hover:text-white transition">
              ← {lang === 'pt' ? 'Voltar' : 'Back'}
            </button>
            <button onClick={() => setStep(3)} disabled={!briefing.trim()}
              className="flex-1 btn-gold rounded-lg py-2 text-xs font-semibold disabled:opacity-30" data-testid="studio-next-2">
              {lang === 'pt' ? 'Próximo: Voz' : 'Next: Voice'} →
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Voice & Music */}
      {step === 3 && (
        <div className="glass-card p-4 space-y-3" data-testid="studio-step-voice">
          <h3 className="text-sm font-semibold text-white">
            {lang === 'pt' ? 'Voz & Música' : 'Voice & Music'}
          </h3>

          {/* Voice per avatar */}
          {selectedAvatars.map((url, idx) => (
            <div key={idx} className="rounded-lg border border-[#222] bg-[#0A0A0A] p-3 space-y-2">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-full overflow-hidden ring-1 ring-[#C9A84C]/30 shrink-0">
                  <img src={url} alt="" className="w-full h-full object-cover" />
                </div>
                <span className="text-[10px] text-[#999]">Avatar {idx + 1}</span>
                <div className="ml-auto relative">
                  <button onClick={() => setShowVoiceDropdown(showVoiceDropdown === idx ? null : idx)} data-testid={`voice-select-${idx}`}
                    className="flex items-center gap-1 rounded-lg border border-[#222] bg-[#111] px-2 py-1 text-[10px] text-white transition hover:border-[#333]">
                    <Mic size={10} />
                    <span>{avatarVoices[idx]?.voice_name || (lang === 'pt' ? 'Escolher voz' : 'Choose voice')}</span>
                    <ChevronDown size={10} className="text-[#555]" />
                  </button>
                  {showVoiceDropdown === idx && (
                    <div className="absolute right-0 top-full mt-1 z-50 max-h-48 w-56 overflow-y-auto rounded-lg border border-[#222] bg-[#111] shadow-xl">
                      {voices.map(v => (
                        <button key={v.id} onClick={() => {
                          setAvatarVoices(prev => ({ ...prev, [idx]: { voice_id: v.id, voice_name: v.name } }));
                          setShowVoiceDropdown(null);
                        }}
                          className="flex w-full items-center gap-2 px-3 py-1.5 text-[10px] transition hover:bg-white/5 text-white">
                          <span className={`text-[8px] px-1 rounded ${v.gender === 'male' ? 'bg-blue-500/20 text-blue-400' : 'bg-pink-500/20 text-pink-400'}`}>
                            {v.gender === 'male' ? 'M' : 'F'}
                          </span>
                          <span className="truncate">{v.name}</span>
                          {v.accent && <span className="text-[#666] ml-auto">{v.accent}</span>}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {avatarVoices[idx] && (
                <div className="space-y-1.5">
                  <textarea value={voiceTexts[idx] || ''} onChange={e => setVoiceTexts(prev => ({ ...prev, [idx]: e.target.value }))}
                    rows={2} placeholder={lang === 'pt' ? 'Texto para o avatar falar...' : 'Text for avatar to speak...'}
                    className="w-full rounded-lg border border-[#222] bg-[#111] px-2 py-1.5 text-[10px] text-white placeholder-[#555] outline-none resize-none" />
                  <div className="flex items-center gap-2">
                    <button onClick={() => handleGenerateVoice(idx)} disabled={generatingVoice === idx || !voiceTexts[idx]}
                      className="btn-gold rounded-lg px-3 py-1 text-[9px] font-semibold disabled:opacity-30" data-testid={`generate-voice-${idx}`}>
                      {generatingVoice === idx ? '...' : (lang === 'pt' ? 'Gerar Voz' : 'Generate Voice')}
                    </button>
                    {generatedAudios[idx] && (
                      <button onClick={() => playAudio(generatedAudios[idx])} className="flex items-center gap-1 text-[10px] text-[#C9A84C]">
                        {playingAudio === generatedAudios[idx] ? <Pause size={12} /> : <Play size={12} />}
                        {lang === 'pt' ? 'Ouvir' : 'Listen'}
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Background Music */}
          <div>
            <label className="mb-1 flex items-center gap-1 text-[10px] font-semibold text-[#777] uppercase tracking-wider">
              <Music size={10} /> {lang === 'pt' ? 'Música de Fundo' : 'Background Music'}
            </label>
            <div className="grid grid-cols-2 gap-1.5 max-h-32 overflow-y-auto">
              {musicTracks.map((track, i) => (
                <button key={typeof track === 'string' ? track : track.id || i}
                  onClick={() => setSelectedMusic(typeof track === 'string' ? track : track.id)}
                  className={`flex items-center gap-1.5 rounded-lg border px-2 py-1.5 text-[9px] transition ${
                    selectedMusic === (typeof track === 'string' ? track : track.id)
                      ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10 text-[#C9A84C]'
                      : 'border-[#222] bg-[#111] text-[#777] hover:border-[#333]'
                  }`}>
                  <Volume2 size={10} />
                  <span className="truncate">{typeof track === 'string' ? track : track.name || `Track ${i + 1}`}</span>
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <button onClick={() => setStep(2)} className="flex-1 rounded-lg border border-[#333] py-2 text-xs text-[#999] hover:text-white transition">
              ← {lang === 'pt' ? 'Voltar' : 'Back'}
            </button>
            <button onClick={handleGenerate} disabled={generating}
              className="flex-1 btn-gold rounded-lg py-2 text-xs font-semibold disabled:opacity-30 flex items-center justify-center gap-2" data-testid="studio-generate">
              <Sparkles size={14} /> {generating ? (lang === 'pt' ? 'Gerando...' : 'Generating...') : (lang === 'pt' ? 'Gerar Cena' : 'Generate Scene')}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Results */}
      {step === 4 && (
        <div className="glass-card p-4 space-y-3" data-testid="studio-step-results">
          <h3 className="text-sm font-semibold text-white">
            {lang === 'pt' ? 'Resultados' : 'Results'}
          </h3>

          {outputs.length === 0 ? (
            <div className="text-center py-8">
              <Sparkles size={24} className="mx-auto text-[#333] mb-2" />
              <p className="text-xs text-[#666]">{lang === 'pt' ? 'Nenhum resultado ainda' : 'No results yet'}</p>
            </div>
          ) : (
            <div className="space-y-3">
              {outputs.map((out, i) => (
                <div key={out.id || i} className="rounded-xl overflow-hidden border border-white/5">
                  {out.type === 'image' && (
                    <div className="relative">
                      <img src={out.url} alt="" className="w-full rounded-xl" />
                      <div className="absolute bottom-2 right-2 flex gap-1.5">
                        <a href={out.url} download className="btn-gold rounded-lg px-3 py-1.5 text-[10px] font-semibold flex items-center gap-1">
                          <Download size={12} /> Download
                        </a>
                      </div>
                    </div>
                  )}
                  <div className="p-2">
                    <p className="text-[9px] text-[#666] truncate">{out.prompt}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Audio results */}
          {Object.keys(generatedAudios).length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-[#999]">{lang === 'pt' ? 'Áudios Gerados' : 'Generated Audio'}</h4>
              {Object.entries(generatedAudios).map(([idx, url]) => (
                <div key={idx} className="flex items-center gap-2 rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                  <div className="h-6 w-6 rounded-full overflow-hidden ring-1 ring-[#C9A84C]/30">
                    <img src={selectedAvatars[idx]} alt="" className="w-full h-full object-cover" />
                  </div>
                  <span className="text-[10px] text-[#999]">Avatar {Number(idx) + 1}</span>
                  <button onClick={() => playAudio(url)} className="ml-auto flex items-center gap-1 text-[10px] text-[#C9A84C]">
                    {playingAudio === url ? <Pause size={12} /> : <Play size={12} />}
                  </button>
                  <a href={url} download className="text-[10px] text-[#666] hover:text-white">
                    <Download size={12} />
                  </a>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-2">
            <button onClick={() => setStep(2)} className="flex-1 rounded-lg border border-[#333] py-2 text-xs text-[#999] hover:text-white transition">
              ← {lang === 'pt' ? 'Nova Cena' : 'New Scene'}
            </button>
            <button onClick={handleGenerate} disabled={generating}
              className="flex-1 btn-gold rounded-lg py-2 text-xs font-semibold disabled:opacity-30 flex items-center justify-center gap-2">
              <Sparkles size={14} /> {lang === 'pt' ? 'Regenerar' : 'Regenerate'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
