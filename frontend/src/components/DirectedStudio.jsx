import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import { Upload, Mic, Music, Play, Pause, Image, Film, Users, Sparkles, Download, X, ChevronDown, Plus, Volume2, PenTool, Trash2, RefreshCw, Check, Crown } from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function DirectedStudio({
  avatars = [],
  onAddAvatar,
  onEditAvatar,
  onRemoveAvatar,
  onPreviewAvatar,
  onAiEditAvatar,
  aiEditAvatarId,
  setAiEditAvatarId,
  aiEditInstruction,
  setAiEditInstruction,
  aiEditLoading,
}) {
  const { t, i18n } = useTranslation();
  const lang = i18n.language?.substring(0, 2) || 'en';

  // State
  const [step, setStep] = useState(1); // 1=avatars, 2=assets+briefing, 3=voice+music, 4=generate
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
  const [agentStatus, setAgentStatus] = useState({});
  const [agentsOutput, setAgentsOutput] = useState(null);
  const [videoDuration, setVideoDuration] = useState(8);
  const [pastProjects, setPastProjects] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [viewingProject, setViewingProject] = useState(null);
  const audioRef = useRef(null);
  const fileInputRef = useRef(null);

  // Load voices, music, and past projects — resume in-progress projects
  useEffect(() => {
    axios.get(`${API}/studio/voices`).then(r => setVoices(r.data.voices || [])).catch(() => {});
    axios.get(`${API}/studio/music-library`).then(r => setMusicTracks(r.data.tracks || [])).catch(() => {});
    axios.get(`${API}/studio/projects`).then(r => {
      const allProjs = r.data.projects || [];
      setPastProjects(allProjs.filter(p => p.outputs?.length > 0));

      // Check for in-progress projects — resume polling
      const inProgress = allProjs.find(p =>
        ['starting', 'running_agents', 'generating_video'].includes(p.status)
      );
      if (inProgress) {
        setStep(4);
        setGenerating(true);
        setBriefing(inProgress.briefing || '');
        setAgentStatus(inProgress.agent_status || {});
        if (inProgress.agents_output && Object.keys(inProgress.agents_output).length > 0) {
          setAgentsOutput(inProgress.agents_output);
        }
        // Resume polling
        const poll = () => {
          axios.get(`${API}/studio/projects/${inProgress.id}/status`).then(res => {
            const data = res.data;
            setAgentStatus(data.agent_status || {});
            if (data.agents_output && Object.keys(data.agents_output).length > 0) {
              setAgentsOutput(data.agents_output);
            }
            if (data.status === 'complete') {
              const videoOut = (data.outputs || []).find(o => o.type === 'video');
              if (videoOut) setOutputs([videoOut]);
              setGenerating(false);
              toast.success(lang === 'pt' ? 'Vídeo gerado com sucesso!' : 'Video generated!');
              // Refresh history
              axios.get(`${API}/studio/projects`).then(r2 => {
                setPastProjects((r2.data.projects || []).filter(p => p.outputs?.length > 0));
              }).catch(() => {});
              return;
            }
            if (data.status === 'error') {
              setGenerating(false);
              toast.error(data.error || (lang === 'pt' ? 'Erro na produção' : 'Production error'));
              return;
            }
            setTimeout(poll, 5000);
          }).catch(() => setTimeout(poll, 8000));
        };
        setTimeout(poll, 2000);
        return;
      }

      // If most recent project just completed, show it
      const justCompleted = allProjs.find(p => p.status === 'complete' && p.outputs?.length > 0);
      if (justCompleted) {
        const createdAt = new Date(justCompleted.created_at);
        const now = new Date();
        const diffMin = (now - createdAt) / 60000;
        if (diffMin < 10) {
          // Show the recently completed project
          setViewingProject(justCompleted);
        }
      }
    }).catch(() => {});
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
    if (!selectedAvatars.length) { toast.error(lang === 'pt' ? 'Selecione ao menos um avatar' : 'Select at least one avatar'); return; }
    if (!briefing.trim()) { toast.error(lang === 'pt' ? 'Adicione uma descrição' : 'Add a scene description'); return; }
    setGenerating(true);
    setAgentStatus({ photography: 'pending', screenwriter: 'pending', music: 'pending', audio: 'pending', video: 'pending' });
    setAgentsOutput(null);
    setOutputs([]);
    setStep(4);

    try {
      // Step 1: Create project
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
      const projectId = projRes.data.id;

      // Step 2: Start background production pipeline
      await axios.post(`${API}/studio/start-production`, {
        project_id: projectId,
        scene_prompt: briefing,
        video_duration: videoDuration,
      });

      // Step 3: Poll for status every 5 seconds
      const poll = async () => {
        try {
          const statusRes = await axios.get(`${API}/studio/projects/${projectId}/status`);
          const data = statusRes.data;
          setAgentStatus(data.agent_status || {});
          if (data.agents_output && Object.keys(data.agents_output).length > 0) {
            setAgentsOutput(data.agents_output);
          }

          if (data.status === 'complete') {
            const videoOut = (data.outputs || []).find(o => o.type === 'video');
            if (videoOut) {
              setOutputs([videoOut]);
            }
            setGenerating(false);
            toast.success(lang === 'pt' ? 'Vídeo gerado com sucesso!' : 'Video generated!');
            return;
          }

          if (data.status === 'error') {
            setGenerating(false);
            toast.error(data.error || (lang === 'pt' ? 'Erro na produção' : 'Production error'));
            return;
          }

          // Keep polling
          setTimeout(poll, 5000);
        } catch {
          setTimeout(poll, 8000);
        }
      };

      // Start polling after 3 seconds
      setTimeout(poll, 3000);

    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Generation failed';
      toast.error(detail);
      setGenerating(false);
    }
  };

  const handleGenerateImageFallback = async () => {
    setGenerating(true);
    try {
      const projList = await axios.get(`${API}/studio/projects`);
      const lastProj = projList.data.projects?.[0];
      if (!lastProj) return;

      const imgRes = await axios.post(`${API}/studio/generate-image`, {
        project_id: lastProj.id,
        scene_prompt: briefing,
      }, { timeout: 120000 });

      setOutputs(prev => [{
        id: Date.now().toString(),
        type: 'image',
        url: imgRes.data.image_url,
        prompt: briefing,
      }, ...prev]);
      toast.success(lang === 'pt' ? 'Imagem gerada!' : 'Image generated!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Image generation failed');
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
            <button onClick={() => { setViewingProject(null); setStep(s.n); }} data-testid={`studio-step-${s.n}`}
              className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[10px] font-medium transition ${
                step === s.n && !viewingProject ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#666] hover:text-[#999]'
              }`}>
              <s.icon size={12} />
              <span className="hidden sm:inline">{s.label}</span>
            </button>
            {i < STEPS.length - 1 && <div className="w-4 h-px bg-[#333] mx-1" />}
          </div>
        ))}
      </div>

      {/* Project History — always visible */}
      {pastProjects.length > 0 && !viewingProject && step !== 4 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <button onClick={() => setShowHistory(!showHistory)} data-testid="toggle-studio-history"
              className="text-[10px] text-[#C9A84C] hover:underline flex items-center gap-1">
              <Film size={10} />
              {pastProjects.length} {lang === 'pt' ? 'produções' : 'productions'}
              <ChevronDown size={10} className={`transition ${showHistory ? 'rotate-180' : ''}`} />
            </button>
          </div>
          {showHistory && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {pastProjects.slice(0, 6).map(proj => {
                const vid = proj.outputs?.find(o => o.type === 'video');
                const img = proj.outputs?.find(o => o.type === 'image');
                const thumb = vid || img;
                return (
                  <button key={proj.id} onClick={() => { setViewingProject(proj); }}
                    data-testid={`history-project-${proj.id}`}
                    className="rounded-xl border border-[#222] bg-[#0A0A0A] overflow-hidden text-left hover:border-[#C9A84C]/30 transition group">
                    <div className="aspect-video bg-[#111] relative flex items-center justify-center">
                      {thumb?.type === 'video' ? (
                        <>
                          <video src={thumb.url} className="w-full h-full object-cover" muted />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                            <Play size={20} className="text-[#C9A84C] group-hover:scale-110 transition" />
                          </div>
                          <span className="absolute top-1 left-1 bg-[#C9A84C]/90 text-[6px] font-bold text-black px-1 rounded">SORA 2</span>
                        </>
                      ) : thumb?.type === 'image' ? (
                        <img src={thumb.url} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <Film size={16} className="text-[#333]" />
                      )}
                    </div>
                    <div className="p-1.5">
                      <p className="text-[8px] text-[#999] truncate">{proj.briefing || proj.name}</p>
                      <p className="text-[7px] text-[#555]">{new Date(proj.created_at).toLocaleDateString()}</p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Viewing Past Project */}
      {viewingProject && (
        <div className="glass-card p-4 space-y-3" data-testid="viewing-past-project">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <Film size={14} className="text-[#C9A84C]" />
              {viewingProject.name || viewingProject.briefing?.slice(0, 40)}
            </h3>
            <button onClick={() => setViewingProject(null)} className="text-[#666] hover:text-white">
              <X size={14} />
            </button>
          </div>

          {/* Agents Analysis */}
          {viewingProject.agents_output && Object.keys(viewingProject.agents_output).length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[9px] font-bold text-[#C9A84C] uppercase">{lang === 'pt' ? 'Análise dos Agentes' : 'Agents Analysis'}</p>
              {viewingProject.agents_output.photography_director?.visual_direction && (
                <div className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                  <p className="text-[7px] font-bold text-[#C9A84C] uppercase">📸 {lang === 'pt' ? 'Dir. Fotografia' : 'Photography'}</p>
                  <p className="text-[8px] text-[#999] line-clamp-2">{viewingProject.agents_output.photography_director.visual_direction}</p>
                </div>
              )}
              {viewingProject.agents_output.screenwriter?.narration && (
                <div className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                  <p className="text-[7px] font-bold text-[#C9A84C] uppercase">✍️ {lang === 'pt' ? 'Redator' : 'Screenwriter'}</p>
                  <p className="text-[8px] text-[#999] line-clamp-2">{viewingProject.agents_output.screenwriter.narration}</p>
                  {viewingProject.agents_output.screenwriter.dialogues?.slice(0, 3).map((d, i) => (
                    <p key={i} className="text-[7px] text-[#777] italic mt-0.5">"{d.line}" — {d.character}</p>
                  ))}
                </div>
              )}
              {viewingProject.agents_output.music_director?.mood && (
                <div className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                  <p className="text-[7px] font-bold text-[#C9A84C] uppercase">🎵 {lang === 'pt' ? 'Dir. Musical' : 'Music'}</p>
                  <p className="text-[8px] text-[#999]">{viewingProject.agents_output.music_director.mood}</p>
                </div>
              )}
            </div>
          )}

          {/* Outputs */}
          {viewingProject.outputs?.map((out, i) => (
            <div key={out.id || i} className="rounded-xl overflow-hidden border border-white/5">
              {out.type === 'video' && (
                <div className="relative bg-black">
                  <video controls autoPlay className="w-full rounded-xl" data-testid="history-video-player" src={out.url} />
                  <span className="absolute top-2 left-2 bg-black/70 text-[8px] text-[#C9A84C] font-bold px-2 py-0.5 rounded">SORA 2</span>
                </div>
              )}
              {out.type === 'image' && (
                <img src={out.url} alt="" className="w-full rounded-xl" />
              )}
              <div className="p-2 flex items-center justify-between">
                <p className="text-[9px] text-[#666] truncate flex-1">{out.prompt}</p>
                <a href={out.url} download className="btn-gold rounded-lg px-3 py-1.5 text-[10px] font-semibold flex items-center gap-1 ml-2 shrink-0">
                  <Download size={12} /> Download
                </a>
              </div>
            </div>
          ))}

          <button onClick={() => setViewingProject(null)}
            className="w-full rounded-lg border border-[#333] py-2 text-xs text-[#999] hover:text-white transition">
            ← {lang === 'pt' ? 'Voltar' : 'Back'}
          </button>
        </div>
      )}

      {/* Step 1: Avatar Selection */}
      {step === 1 && !viewingProject && (
        <div className="glass-card p-4 space-y-3" data-testid="studio-step-avatars">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">
              {lang === 'pt' ? 'Selecione os Avatares' : 'Select Avatars'}
            </h3>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-[#C9A84C]">{selectedAvatars.length} {lang === 'pt' ? 'selecionado(s)' : 'selected'}</span>
              {onAddAvatar && (
                <button onClick={onAddAvatar} data-testid="studio-add-avatar-btn"
                  className="flex items-center gap-1 px-2 py-1 rounded-lg border border-dashed border-[#2A2A2A] text-[9px] text-[#999] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
                  <Plus size={10} /> {lang === 'pt' ? 'Criar' : 'Create'}
                </button>
              )}
            </div>
          </div>
          <p className="text-[10px] text-[#666]">
            {lang === 'pt' ? 'Escolha 1 ou mais avatares para a cena. Para interação, selecione 2+' : 'Pick 1 or more avatars for the scene. For interaction, select 2+'}
          </p>

          {avatars.length === 0 ? (
            <div className="text-center py-6">
              <Users size={24} className="mx-auto text-[#333] mb-2" />
              <p className="text-xs text-[#666]">{lang === 'pt' ? 'Nenhum avatar criado ainda.' : 'No avatars yet.'}</p>
              {onAddAvatar && (
                <button onClick={onAddAvatar} className="mt-2 btn-gold rounded-lg px-4 py-1.5 text-[10px] font-semibold">
                  <Plus size={10} className="inline mr-1" /> {lang === 'pt' ? 'Criar Avatar' : 'Create Avatar'}
                </button>
              )}
            </div>
          ) : (
            <div className="flex gap-2 flex-wrap">
              {avatars.map((av, i) => {
                const selected = selectedAvatars.includes(av.url);
                return (
                  <div key={av.id || i} data-testid={`studio-avatar-${i}`}
                    className={`relative rounded-xl overflow-hidden border-2 transition cursor-pointer ${
                      selected ? 'border-[#C9A84C] shadow-[0_0_10px_rgba(201,168,76,0.2)]' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'
                    }`}>
                    <img src={resolveImageUrl(av.url)} alt={av.name} className="h-24 w-16 object-cover"
                      onClick={() => toggleAvatar(av.url)} />
                    {selected && (
                      <div className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center">
                        <span className="text-[8px] text-black font-bold">{selectedAvatars.indexOf(av.url) + 1}</span>
                      </div>
                    )}
                    {av.voice && (
                      <div className={`absolute top-0.5 left-0.5 h-4 w-4 rounded-full flex items-center justify-center ${av.voice.type === 'elevenlabs' ? 'bg-[#C9A84C]/90' : 'bg-black/70'}`}>
                        {av.voice.type === 'elevenlabs' ? <Crown size={7} className="text-black" /> : <Volume2 size={7} className="text-[#C9A84C]" />}
                      </div>
                    )}
                    {/* Action bar */}
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent px-1 py-0.5 flex items-center justify-between">
                      <button onClick={e => { e.stopPropagation(); onRemoveAvatar?.(av.id); }}
                        className="h-5 w-5 rounded flex items-center justify-center text-red-400/70 hover:text-red-400 transition">
                        <X size={9} />
                      </button>
                      <div className="flex items-center gap-0.5">
                        <button onClick={e => { e.stopPropagation(); setAiEditAvatarId?.(aiEditAvatarId === av.id ? null : av.id); setAiEditInstruction?.(''); }}
                          className="h-5 w-5 rounded flex items-center justify-center text-purple-400 hover:text-purple-300 transition" title="Editar com IA">
                          <Sparkles size={9} />
                        </button>
                        <button onClick={e => { e.stopPropagation(); onEditAvatar?.(av); }}
                          className="h-5 w-5 rounded flex items-center justify-center text-[#C9A84C] hover:text-[#D4B85C] transition" title="Editar">
                          <PenTool size={9} />
                        </button>
                      </div>
                    </div>
                    {av.creation_mode && av.creation_mode !== 'photo' && (
                      <div className="absolute top-0.5 left-0.5 rounded-md bg-black/70 px-1 py-0.5">
                        <span className="text-[6px] text-[#C9A84C] font-bold uppercase">{av.creation_mode === '3d' ? '3D' : 'AI'}</span>
                      </div>
                    )}
                    {/* AI Edit popover */}
                    {aiEditAvatarId === av.id && (
                      <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-1.5 z-10" onClick={e => e.stopPropagation()}>
                        <Sparkles size={12} className="text-purple-400 mb-1" />
                        <textarea data-testid={`studio-ai-edit-input-${av.id}`}
                          value={aiEditInstruction || ''} onChange={e => setAiEditInstruction?.(e.target.value)}
                          placeholder="Ex: mudar roupa para terno azul, adicionar oculos..."
                          className="w-full text-[8px] bg-[#1A1A1A] border border-[#333] rounded-lg p-1.5 text-white placeholder-[#666] resize-none outline-none focus:border-purple-500/40"
                          rows={2} />
                        <div className="flex gap-1 mt-1 w-full">
                          <button onClick={() => { setAiEditAvatarId?.(null); setAiEditInstruction?.(''); }}
                            className="flex-1 text-[7px] py-1 rounded-lg border border-[#333] text-[#888] hover:text-white transition">
                            {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                          </button>
                          <button onClick={() => onAiEditAvatar?.(av.id)} disabled={aiEditLoading || !(aiEditInstruction || '').trim()}
                            className="flex-1 text-[7px] py-1 rounded-lg bg-purple-600 text-white font-bold hover:bg-purple-500 transition disabled:opacity-40 flex items-center justify-center gap-1">
                            {aiEditLoading ? <RefreshCw size={8} className="animate-spin" /> : <Sparkles size={8} />}
                            {aiEditLoading ? '' : 'Editar'}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
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

          {/* Video Duration */}
          <div>
            <label className="mb-1 flex items-center gap-1 text-[10px] font-semibold text-[#777] uppercase tracking-wider">
              <Film size={10} /> {lang === 'pt' ? 'Duração do Vídeo' : 'Video Duration'}
            </label>
            <div className="flex gap-2">
              {[4, 8, 12].map(d => (
                <button key={d} onClick={() => setVideoDuration(d)}
                  className={`flex-1 rounded-lg border px-3 py-2 text-xs font-semibold transition ${
                    videoDuration === d ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10 text-[#C9A84C]' : 'border-[#222] bg-[#111] text-[#555] hover:border-[#333]'
                  }`} data-testid={`video-duration-${d}`}>
                  {d}s
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

      {/* Step 4: Production & Results */}
      {step === 4 && (
        <div className="glass-card p-4 space-y-4" data-testid="studio-step-results">
          {/* Agents Status Panel */}
          {generating && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Film size={14} className="text-[#C9A84C]" />
                {lang === 'pt' ? 'Produção em Andamento' : 'Production in Progress'}
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { key: 'photography', icon: '📸', label: lang === 'pt' ? 'Dir. Fotografia' : 'Photography Dir.' },
                  { key: 'screenwriter', icon: '✍️', label: lang === 'pt' ? 'Redator/Autor' : 'Screenwriter' },
                  { key: 'music', icon: '🎵', label: lang === 'pt' ? 'Dir. Musical' : 'Music Director' },
                  { key: 'audio', icon: '🎙️', label: lang === 'pt' ? 'Dir. Áudio' : 'Audio Director' },
                ].map(agent => (
                  <div key={agent.key}
                    className={`rounded-lg border px-3 py-2 text-[10px] flex items-center gap-2 transition-all ${
                      agentStatus[agent.key] === 'done' ? 'border-green-500/30 bg-green-500/5 text-green-400' :
                      agentStatus[agent.key] === 'running' ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5 text-[#C9A84C] animate-pulse' :
                      'border-[#222] bg-[#111] text-[#555]'
                    }`}>
                    <span>{agent.icon}</span>
                    <span className="flex-1">{agent.label}</span>
                    {agentStatus[agent.key] === 'done' && <Check size={10} className="text-green-400" />}
                    {agentStatus[agent.key] === 'running' && <RefreshCw size={10} className="animate-spin" />}
                  </div>
                ))}
              </div>
              {agentStatus.video === 'running' && (
                <div className="rounded-lg border border-[#C9A84C]/30 bg-[#C9A84C]/5 px-3 py-3 flex items-center gap-3 animate-pulse">
                  <Film size={16} className="text-[#C9A84C]" />
                  <div>
                    <p className="text-[11px] font-semibold text-[#C9A84C]">Sora 2 — {lang === 'pt' ? 'Gerando Vídeo' : 'Generating Video'}...</p>
                    <p className="text-[9px] text-[#666]">{lang === 'pt' ? 'Isto pode levar 2-5 minutos' : 'This may take 2-5 minutes'}</p>
                  </div>
                </div>
              )}
              {agentStatus.error && (
                <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-3 py-2 text-[10px] text-red-400">
                  {agentStatus.error}
                </div>
              )}
            </div>
          )}

          {/* Agents Output Summary */}
          {agentsOutput && !generating && (
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-white">{lang === 'pt' ? 'Análise dos Agentes' : 'Agents Analysis'}</h3>
              <div className="grid grid-cols-1 gap-2">
                {agentsOutput.photography_director?.visual_direction && (
                  <div className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                    <p className="text-[8px] font-bold text-[#C9A84C] uppercase mb-0.5">📸 {lang === 'pt' ? 'Dir. Fotografia' : 'Photography'}</p>
                    <p className="text-[9px] text-[#999] line-clamp-2">{agentsOutput.photography_director.visual_direction}</p>
                  </div>
                )}
                {agentsOutput.screenwriter?.narration && (
                  <div className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                    <p className="text-[8px] font-bold text-[#C9A84C] uppercase mb-0.5">✍️ {lang === 'pt' ? 'Redator' : 'Screenwriter'}</p>
                    <p className="text-[9px] text-[#999] line-clamp-2">{agentsOutput.screenwriter.narration}</p>
                    {agentsOutput.screenwriter.dialogues?.length > 0 && (
                      <div className="mt-1 space-y-0.5">
                        {agentsOutput.screenwriter.dialogues.slice(0, 3).map((d, i) => (
                          <p key={i} className="text-[8px] text-[#777] italic">"{d.line}" — {d.character}</p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {agentsOutput.music_director?.mood && (
                  <div className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                    <p className="text-[8px] font-bold text-[#C9A84C] uppercase mb-0.5">🎵 {lang === 'pt' ? 'Dir. Musical' : 'Music'}</p>
                    <p className="text-[9px] text-[#999]">{agentsOutput.music_director.mood} — {agentsOutput.music_director.recommended_genre}</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Results Title */}
          {!generating && outputs.length > 0 && (
            <h3 className="text-sm font-semibold text-white">
              {lang === 'pt' ? 'Resultados' : 'Results'}
            </h3>
          )}

          {/* Video/Image Results */}
          {outputs.length > 0 && (
            <div className="space-y-3">
              {outputs.map((out, i) => (
                <div key={out.id || i} className="rounded-xl overflow-hidden border border-white/5">
                  {out.type === 'video' && (
                    <div className="relative bg-black">
                      <video
                        controls
                        autoPlay
                        className="w-full rounded-xl"
                        data-testid="studio-video-player"
                        src={out.url}
                      />
                      <div className="absolute top-2 left-2 rounded-md bg-black/70 px-2 py-0.5">
                        <span className="text-[8px] text-[#C9A84C] font-bold">SORA 2</span>
                      </div>
                    </div>
                  )}
                  {out.type === 'image' && (
                    <div className="relative">
                      <img src={out.url} alt="" className="w-full rounded-xl" />
                    </div>
                  )}
                  <div className="p-2 flex items-center justify-between">
                    <p className="text-[9px] text-[#666] truncate flex-1">{out.prompt}</p>
                    <a href={out.url} download className="btn-gold rounded-lg px-3 py-1.5 text-[10px] font-semibold flex items-center gap-1 ml-2 shrink-0">
                      <Download size={12} /> Download
                    </a>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error fallback: offer image generation */}
          {!generating && agentStatus.video === 'error' && outputs.length === 0 && (
            <div className="text-center py-4 space-y-2">
              <p className="text-xs text-[#999]">{lang === 'pt' ? 'O vídeo falhou. Deseja gerar uma imagem da cena?' : 'Video failed. Generate image instead?'}</p>
              <button onClick={handleGenerateImageFallback}
                className="btn-gold rounded-lg px-4 py-2 text-xs font-semibold flex items-center justify-center gap-2 mx-auto">
                <Image size={12} /> {lang === 'pt' ? 'Gerar Imagem' : 'Generate Image'}
              </button>
            </div>
          )}

          {/* No results yet */}
          {!generating && outputs.length === 0 && !agentStatus.error && (
            <div className="text-center py-8">
              <Sparkles size={24} className="mx-auto text-[#333] mb-2" />
              <p className="text-xs text-[#666]">{lang === 'pt' ? 'Nenhum resultado ainda' : 'No results yet'}</p>
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
            <button onClick={() => {
              setStep(1); setOutputs([]); setAgentsOutput(null); setAgentStatus({});
              axios.get(`${API}/studio/projects`).then(r => {
                setPastProjects((r.data.projects || []).filter(p => p.outputs?.length > 0));
              }).catch(() => {});
            }}
              className="flex-1 rounded-lg border border-[#333] py-2 text-xs text-[#999] hover:text-white transition">
              ← {lang === 'pt' ? 'Nova Cena' : 'New Scene'}
            </button>
            <button onClick={handleGenerate} disabled={generating}
              className="flex-1 btn-gold rounded-lg py-2 text-xs font-semibold disabled:opacity-30 flex items-center justify-center gap-2">
              <Sparkles size={14} /> {generating ? '...' : (lang === 'pt' ? 'Regenerar' : 'Regenerate')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
