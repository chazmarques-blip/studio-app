import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import { Send, Users, Film, Play, Pause, Sparkles, Download, X, ChevronDown, Plus, Volume2, PenTool, RefreshCw, Check, MessageSquare, Clapperboard, Eye, Camera } from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function DirectedStudio({
  avatars = [], onAddAvatar, onEditAvatar, onRemoveAvatar, onPreviewAvatar,
  onAiEditAvatar, aiEditAvatarId, setAiEditAvatarId, aiEditInstruction, setAiEditInstruction, aiEditLoading,
}) {
  const { i18n } = useTranslation();
  const lang = i18n.language?.substring(0, 2) || 'pt';

  const [step, setStep] = useState(1);
  const [projectId, setProjectId] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [scenes, setScenes] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [characterAvatars, setCharacterAvatars] = useState({});
  const [generating, setGenerating] = useState(false);
  const [agentStatus, setAgentStatus] = useState({});
  const [outputs, setOutputs] = useState([]);
  const [pastProjects, setPastProjects] = useState([]);
  const [viewingProject, setViewingProject] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const chatEndRef = useRef(null);

  const STEPS = [
    { n: 1, icon: MessageSquare, label: lang === 'pt' ? 'Roteiro' : 'Script' },
    { n: 2, icon: Users, label: lang === 'pt' ? 'Personagens' : 'Characters' },
    { n: 3, icon: Clapperboard, label: lang === 'pt' ? 'Produção' : 'Production' },
    { n: 4, icon: Eye, label: lang === 'pt' ? 'Resultado' : 'Result' },
  ];

  // Load past projects & resume in-progress
  useEffect(() => {
    axios.get(`${API}/studio/projects`).then(r => {
      const allProjs = r.data.projects || [];
      setPastProjects(allProjs.filter(p => p.outputs?.length > 0));
      const inProgress = allProjs.find(p =>
        ['starting', 'running_agents', 'generating_video'].includes(p.status)
      );
      if (inProgress) {
        setProjectId(inProgress.id);
        setScenes(inProgress.scenes || []);
        setCharacters(inProgress.characters || []);
        setStep(3);
        setGenerating(true);
        startPolling(inProgress.id);
        return;
      }
      const recent = allProjs.find(p => p.status === 'complete' && p.outputs?.length > 0);
      if (recent) {
        const diffMin = (Date.now() - new Date(recent.created_at).getTime()) / 60000;
        if (diffMin < 15) setViewingProject(recent);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Polling for production status
  const startPolling = (pid) => {
    const poll = () => {
      axios.get(`${API}/studio/projects/${pid}/status`).then(res => {
        const d = res.data;
        setAgentStatus(d.agent_status || {});
        setScenes(d.scenes || []);
        if (d.status === 'complete') {
          setOutputs(d.outputs || []);
          setGenerating(false);
          setStep(4);
          toast.success(lang === 'pt' ? 'Produção concluída!' : 'Production complete!');
          axios.get(`${API}/studio/projects`).then(r2 => {
            setPastProjects((r2.data.projects || []).filter(p => p.outputs?.length > 0));
          }).catch(() => {});
          return;
        }
        if (d.status === 'error') {
          setGenerating(false);
          toast.error(d.error || 'Production error');
          return;
        }
        setTimeout(poll, 4000);
      }).catch(() => setTimeout(poll, 6000));
    };
    setTimeout(poll, 3000);
  };

  // Send message to Screenwriter
  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', text: msg }]);
    setChatLoading(true);
    try {
      const res = await axios.post(`${API}/studio/chat`, {
        project_id: projectId,
        message: msg,
        language: lang,
      }, { timeout: 120000 });
      setProjectId(res.data.project_id);
      setScenes(res.data.scenes || []);
      setCharacters(res.data.characters || []);
      setChatMessages(prev => [...prev, { role: 'assistant', text: res.data.message }]);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Screenwriter error');
      setChatMessages(prev => [...prev, { role: 'assistant', text: '❌ Erro ao processar. Tente novamente.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Link existing avatars to characters
  const linkAvatar = (charName, avatarUrl) => {
    setCharacterAvatars(prev => ({ ...prev, [charName]: avatarUrl }));
  };

  // Start multi-scene production
  const startProduction = async () => {
    if (!projectId || scenes.length === 0) return;
    setGenerating(true);
    setStep(3);
    setOutputs([]);
    try {
      await axios.post(`${API}/studio/start-production`, {
        project_id: projectId,
        video_duration: 12,
      });
      startPolling(projectId);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start');
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-3" data-testid="directed-studio">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-0.5">
        {STEPS.map((s, i) => (
          <div key={s.n} className="flex items-center">
            <button onClick={() => { if (!generating) { setViewingProject(null); setStep(s.n); }}}
              data-testid={`studio-step-${s.n}`}
              className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-[9px] font-medium transition ${
                step === s.n && !viewingProject ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#555] hover:text-[#888]'
              }`}>
              <s.icon size={11} />
              <span className="hidden sm:inline">{s.label}</span>
            </button>
            {i < STEPS.length - 1 && <div className="w-3 h-px bg-[#333] mx-0.5" />}
          </div>
        ))}
      </div>

      {/* History */}
      {pastProjects.length > 0 && !viewingProject && step === 1 && !chatMessages.length && (
        <div>
          <button onClick={() => setShowHistory(!showHistory)} data-testid="toggle-studio-history"
            className="text-[10px] text-[#C9A84C] hover:underline flex items-center gap-1 mb-1">
            <Film size={10} /> {pastProjects.length} {lang === 'pt' ? 'produções' : 'productions'}
            <ChevronDown size={10} className={`transition ${showHistory ? 'rotate-180' : ''}`} />
          </button>
          {showHistory && (
            <div className="grid grid-cols-3 gap-1.5">
              {pastProjects.slice(0, 6).map(proj => {
                const vid = proj.outputs?.find(o => o.type === 'video');
                return (
                  <button key={proj.id} onClick={() => setViewingProject(proj)} data-testid={`history-project-${proj.id}`}
                    className="rounded-lg border border-[#222] bg-[#0A0A0A] overflow-hidden text-left hover:border-[#C9A84C]/30 transition group">
                    <div className="aspect-video bg-[#111] relative flex items-center justify-center">
                      {vid ? (
                        <>
                          <video src={vid.url} className="w-full h-full object-cover" muted />
                          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                            <Play size={14} className="text-[#C9A84C]" />
                          </div>
                          <span className="absolute top-0.5 left-0.5 bg-[#C9A84C] text-[5px] font-bold text-black px-1 rounded">SORA 2</span>
                        </>
                      ) : <Film size={12} className="text-[#333]" />}
                    </div>
                    <div className="p-1">
                      <p className="text-[7px] text-[#999] truncate">{proj.briefing || proj.name}</p>
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
        <div className="glass-card p-3 space-y-2" data-testid="viewing-past-project">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-white flex items-center gap-1.5">
              <Film size={12} className="text-[#C9A84C]" />
              {viewingProject.name || viewingProject.briefing?.slice(0, 40)}
            </h3>
            <button onClick={() => setViewingProject(null)} className="text-[#666] hover:text-white"><X size={12} /></button>
          </div>
          {viewingProject.outputs?.map((out, i) => (
            <div key={out.id || i} className="rounded-lg overflow-hidden border border-white/5">
              {out.type === 'video' && (
                <div className="relative bg-black">
                  <video controls autoPlay={i === 0} className="w-full rounded-lg" src={out.url} />
                  <span className="absolute top-1 left-1 bg-black/70 text-[7px] text-[#C9A84C] font-bold px-1.5 py-0.5 rounded">
                    {out.label === 'complete' ? 'FILME COMPLETO' : `CENA ${out.scene_number}`}
                  </span>
                </div>
              )}
              <div className="p-1.5 flex items-center justify-between">
                <span className="text-[8px] text-[#666]">{out.label === 'complete' ? `${out.duration}s total` : `Cena ${out.scene_number} • 12s`}</span>
                <a href={out.url} download className="btn-gold rounded px-2 py-1 text-[8px] font-semibold flex items-center gap-1">
                  <Download size={10} /> Download
                </a>
              </div>
            </div>
          ))}
          <button onClick={() => setViewingProject(null)} className="w-full rounded-lg border border-[#333] py-1.5 text-[10px] text-[#999] hover:text-white transition">
            ← {lang === 'pt' ? 'Voltar' : 'Back'}
          </button>
        </div>
      )}

      {/* ═══ STEP 1: Screenwriter Chat ═══ */}
      {step === 1 && !viewingProject && (
        <div className="glass-card p-3 space-y-2" data-testid="studio-step-script">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#8B6914] flex items-center justify-center">
              <MessageSquare size={12} className="text-black" />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-white">{lang === 'pt' ? 'Redator & Pesquisador' : 'Screenwriter'}</h3>
              <p className="text-[8px] text-[#666]">{lang === 'pt' ? 'Descreva a história que quer criar' : 'Describe the story you want to create'}</p>
            </div>
          </div>

          {/* Chat messages */}
          <div className="max-h-[350px] overflow-y-auto space-y-2 hide-scrollbar" data-testid="screenwriter-chat">
            {chatMessages.length === 0 && (
              <div className="text-center py-6 space-y-2">
                <Sparkles size={20} className="mx-auto text-[#333]" />
                <p className="text-[10px] text-[#555]">{lang === 'pt'
                  ? 'Ex: "Crie a história completa de Isaque e Jacó da Bíblia, com todas as cenas importantes"'
                  : 'Ex: "Create the complete story of Isaac and Jacob from the Bible"'
                }</p>
              </div>
            )}
            {chatMessages.map((m, i) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-lg px-3 py-2 text-[10px] leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/20'
                    : 'bg-[#111] text-[#ccc] border border-[#222]'
                }`}>
                  <pre className="whitespace-pre-wrap font-sans">{m.text}</pre>
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-[#111] border border-[#222] rounded-lg px-3 py-2 flex items-center gap-2">
                  <RefreshCw size={10} className="animate-spin text-[#C9A84C]" />
                  <span className="text-[9px] text-[#666]">{lang === 'pt' ? 'Pesquisando e escrevendo...' : 'Researching and writing...'}</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat input */}
          <div className="flex gap-2">
            <input data-testid="screenwriter-input" value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendChat()}
              placeholder={lang === 'pt' ? 'Descreva a história...' : 'Describe the story...'}
              className="flex-1 bg-[#0A0A0A] border border-[#222] rounded-lg px-3 py-2 text-xs text-white placeholder-[#555] outline-none focus:border-[#C9A84C]/40"
              disabled={chatLoading}
            />
            <button onClick={sendChat} disabled={chatLoading || !chatInput.trim()} data-testid="send-chat-btn"
              className="btn-gold rounded-lg px-3 py-2 disabled:opacity-30">
              <Send size={14} />
            </button>
          </div>

          {/* Scene summary */}
          {scenes.length > 0 && (
            <div className="space-y-1.5 border-t border-[#222] pt-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-semibold text-[#C9A84C]">{scenes.length} {lang === 'pt' ? 'cenas planejadas' : 'scenes planned'} ({scenes.length * 12}s)</span>
                <button onClick={() => setStep(2)} data-testid="go-to-characters"
                  className="btn-gold rounded-lg px-3 py-1.5 text-[10px] font-semibold flex items-center gap-1">
                  {lang === 'pt' ? 'Personagens' : 'Characters'} →
                </button>
              </div>
              <div className="grid grid-cols-2 gap-1">
                {scenes.slice(0, 4).map((s, i) => (
                  <div key={i} className="rounded-md border border-[#1A1A1A] bg-[#0A0A0A] p-1.5">
                    <p className="text-[7px] font-bold text-[#C9A84C]">CENA {s.scene_number} ({s.time_start}-{s.time_end})</p>
                    <p className="text-[7px] text-[#888] truncate">{s.title}</p>
                  </div>
                ))}
                {scenes.length > 4 && (
                  <div className="rounded-md border border-[#1A1A1A] bg-[#0A0A0A] p-1.5 flex items-center justify-center">
                    <p className="text-[8px] text-[#555]">+{scenes.length - 4} {lang === 'pt' ? 'cenas' : 'scenes'}</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ STEP 2: Characters / Avatars ═══ */}
      {step === 2 && !viewingProject && (
        <div className="glass-card p-3 space-y-3" data-testid="studio-step-characters">
          <h3 className="text-xs font-semibold text-white flex items-center gap-2">
            <Users size={12} className="text-[#C9A84C]" />
            {lang === 'pt' ? 'Personagens & Avatares' : 'Characters & Avatars'}
          </h3>
          <p className="text-[9px] text-[#666]">
            {lang === 'pt' ? 'Vincule avatares existentes ou crie novos para cada personagem' : 'Link existing avatars or create new ones'}
          </p>

          <div className="space-y-2">
            {characters.map((char, ci) => (
              <div key={ci} className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2">
                <div className="flex items-center gap-2 mb-1.5">
                  {characterAvatars[char.name] ? (
                    <img src={resolveImageUrl(characterAvatars[char.name])} alt="" className="h-10 w-8 rounded-lg object-cover border border-[#C9A84C]/30" />
                  ) : (
                    <div className="h-10 w-8 rounded-lg bg-[#1A1A1A] flex items-center justify-center border border-dashed border-[#333]">
                      <Users size={12} className="text-[#444]" />
                    </div>
                  )}
                  <div className="flex-1">
                    <p className="text-[10px] font-semibold text-white">{char.name}</p>
                    <p className="text-[8px] text-[#666]">{char.description}</p>
                    <p className="text-[7px] text-[#555]">{char.age} • {char.role}</p>
                  </div>
                  {!characterAvatars[char.name] && (
                    <span className="text-[7px] bg-red-500/10 text-red-400 border border-red-500/20 rounded px-1.5 py-0.5">
                      {lang === 'pt' ? 'Sem avatar' : 'No avatar'}
                    </span>
                  )}
                </div>

                {/* Avatar selection */}
                <div className="flex gap-1 flex-wrap">
                  {avatars.map((av, ai) => (
                    <button key={ai} onClick={() => linkAvatar(char.name, av.url)}
                      className={`h-10 w-8 rounded overflow-hidden border-2 transition ${
                        characterAvatars[char.name] === av.url ? 'border-[#C9A84C]' : 'border-[#222] hover:border-[#444]'
                      }`}>
                      <img src={resolveImageUrl(av.url)} alt={av.name} className="w-full h-full object-cover" />
                    </button>
                  ))}
                  <button onClick={onAddAvatar} className="h-10 w-8 rounded border border-dashed border-[#333] flex items-center justify-center hover:border-[#C9A84C]/40 transition">
                    <Plus size={10} className="text-[#555]" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex gap-2">
            <button onClick={() => setStep(1)} className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
              ← {lang === 'pt' ? 'Roteiro' : 'Script'}
            </button>
            <button onClick={startProduction} disabled={generating || scenes.length === 0}
              data-testid="start-production-btn"
              className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-semibold disabled:opacity-30 flex items-center justify-center gap-1">
              <Clapperboard size={12} /> {lang === 'pt' ? `Produzir ${scenes.length} Cenas` : `Produce ${scenes.length} Scenes`}
            </button>
          </div>
        </div>
      )}

      {/* ═══ STEP 3: Production Progress ═══ */}
      {step === 3 && !viewingProject && (
        <div className="glass-card p-3 space-y-3" data-testid="studio-step-production">
          <h3 className="text-xs font-semibold text-white flex items-center gap-2">
            <Clapperboard size={12} className="text-[#C9A84C]" />
            {lang === 'pt' ? 'Produção em Andamento' : 'Production in Progress'}
          </h3>

          {/* Overall progress */}
          {agentStatus.total_scenes > 0 && (
            <div>
              <div className="flex items-center justify-between text-[9px] mb-1">
                <span className="text-[#999]">
                  {agentStatus.phase === 'photography' && `📸 Dir. Fotografia — Cena ${agentStatus.current_scene}/${agentStatus.total_scenes}`}
                  {agentStatus.phase === 'music' && `🎵 Dir. Musical`}
                  {agentStatus.phase === 'audio' && `🎙️ Dir. Áudio — Cena ${agentStatus.current_scene}/${agentStatus.total_scenes}`}
                  {agentStatus.phase === 'generating_video' && `🎬 Aguardando geração de vídeos...`}
                  {agentStatus.phase === 'generating_videos' && `🎬 Aguardando geração de vídeos...`}
                  {agentStatus.phase === 'concatenating' && `🔗 Concatenando vídeos...`}
                  {agentStatus.phase === 'complete' && `✅ Produção concluída!`}
                  {agentStatus.phase === 'starting' && `⏳ Iniciando produção...`}
                </span>
                <span className="text-[#C9A84C] font-semibold">
                  {agentStatus.videos_done !== undefined ? `${agentStatus.videos_done}/${agentStatus.total_scenes} vídeos` : ''}
                </span>
              </div>
              <div className="w-full bg-[#1A1A1A] rounded-full h-1.5">
                <div className="bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${_calcProgress(agentStatus)}%` }} />
              </div>
            </div>
          )}

          {/* Scene-by-scene status */}
          <div className="space-y-1">
            {scenes.map((s, i) => {
              const sceneNum = s.scene_number || i + 1;
              const currentScene = agentStatus.current_scene || 0;
              const videosGenerated = agentStatus.videos_done || 0;
              const isAgentProcessing = ['photography', 'music', 'audio'].includes(agentStatus.phase) && currentScene === sceneNum;
              const agentsDone = currentScene > sceneNum || ['generating_video', 'generating_videos', 'concatenating', 'complete'].includes(agentStatus.phase);
              const videoGenerated = videosGenerated >= sceneNum;
              const isVideoGenerating = agentStatus.phase?.startsWith('generating_video') && !videoGenerated && agentsDone;

              return (
                <div key={i} className={`rounded-lg border px-2.5 py-1.5 flex items-center gap-2 transition-all ${
                  isAgentProcessing ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5 animate-pulse' :
                  videoGenerated ? 'border-green-500/20 bg-green-500/5' :
                  agentsDone ? 'border-blue-500/20 bg-blue-500/5' :
                  'border-[#1A1A1A] bg-[#0A0A0A]'
                }`}>
                  <div className={`h-5 w-5 rounded-full flex items-center justify-center text-[8px] font-bold ${
                    videoGenerated ? 'bg-green-500 text-black' :
                    isAgentProcessing ? 'bg-[#C9A84C] text-black' :
                    agentsDone ? 'bg-blue-500 text-white' :
                    'bg-[#222] text-[#666]'
                  }`}>
                    {videoGenerated ? <Check size={8} /> : sceneNum}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[8px] font-semibold text-white truncate">{s.title || `Cena ${sceneNum}`}</p>
                    <p className="text-[7px] text-[#666] truncate">{s.time_start}-{s.time_end} • {s.emotion}</p>
                  </div>
                  <div className="text-[7px] shrink-0">
                    {videoGenerated && <span className="text-green-400">✓ Vídeo</span>}
                    {isVideoGenerating && <span className="text-[#C9A84C]">Sora 2...</span>}
                    {isAgentProcessing && <RefreshCw size={8} className="animate-spin text-[#C9A84C]" />}
                    {!agentsDone && !isAgentProcessing && <span className="text-[#444]">—</span>}
                    {agentsDone && !videoGenerated && !isVideoGenerating && <span className="text-blue-400">Pronto</span>}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Phase indicator */}
          {generating && agentStatus.phase?.startsWith('generating_video') && (
            <div className="rounded-lg border border-[#C9A84C]/20 bg-[#C9A84C]/5 p-2 flex items-center gap-2">
              <Film size={14} className="text-[#C9A84C] animate-pulse" />
              <div>
                <p className="text-[10px] font-semibold text-[#C9A84C]">Sora 2 — {lang === 'pt' ? 'Gerando Vídeos' : 'Generating Videos'}</p>
                <p className="text-[8px] text-[#666]">{lang === 'pt' ? 'Cada cena leva 2-5 minutos' : 'Each scene takes 2-5 minutes'}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ═══ STEP 4: Results ═══ */}
      {step === 4 && !viewingProject && (
        <div className="glass-card p-3 space-y-3" data-testid="studio-step-results">
          <h3 className="text-xs font-semibold text-white flex items-center gap-2">
            <Eye size={12} className="text-[#C9A84C]" />
            {lang === 'pt' ? 'Resultado Final' : 'Final Result'}
          </h3>

          {outputs.length === 0 && !generating && (
            <div className="text-center py-6">
              <Sparkles size={20} className="mx-auto text-[#333] mb-2" />
              <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Aguardando produção...' : 'Waiting for production...'}</p>
            </div>
          )}

          {outputs.map((out, i) => (
            <div key={out.id || i} className="rounded-lg overflow-hidden border border-white/5">
              {out.type === 'video' && out.url && (
                <div className="relative bg-black">
                  <video controls autoPlay={i === 0} className="w-full rounded-lg" data-testid={`result-video-${i}`} src={out.url} />
                  <span className="absolute top-1.5 left-1.5 bg-black/80 text-[7px] text-[#C9A84C] font-bold px-1.5 py-0.5 rounded">
                    {out.label === 'complete' ? `🎬 FILME COMPLETO (${out.duration}s)` : `CENA ${out.scene_number}`}
                  </span>
                </div>
              )}
              <div className="p-1.5 flex items-center justify-between">
                <span className="text-[8px] text-[#666]">{out.label === 'complete' ? 'Todas as cenas' : `Cena ${out.scene_number} • 12s`}</span>
                <a href={out.url} download className="btn-gold rounded px-2 py-1 text-[8px] font-semibold flex items-center gap-1">
                  <Download size={10} /> Download
                </a>
              </div>
            </div>
          ))}

          <div className="flex gap-2">
            <button onClick={() => {
              setStep(1); setChatMessages([]); setScenes([]); setCharacters([]);
              setProjectId(null); setOutputs([]); setAgentStatus({});
              axios.get(`${API}/studio/projects`).then(r => {
                setPastProjects((r.data.projects || []).filter(p => p.outputs?.length > 0));
              }).catch(() => {});
            }} className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
              ← {lang === 'pt' ? 'Nova Produção' : 'New Production'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function _calcProgress(status) {
  if (!status.total_scenes) return 0;
  const { current_scene = 0, total_scenes = 1, phase = '', videos_done = 0 } = status;
  if (phase === 'complete') return 100;
  if (phase === 'concatenating') return 95;
  if (phase?.startsWith('generating_video')) {
    const agentPct = 50;
    const videoPct = (videos_done / total_scenes) * 45;
    return Math.min(agentPct + videoPct, 95);
  }
  // Agent phases: photography, music, audio (50% of progress for agents)
  const sceneProgress = ((current_scene - 1) / total_scenes);
  const phaseMultiplier = phase === 'photography' ? 0.3 : phase === 'music' ? 0.6 : phase === 'audio' ? 0.9 : 1;
  return Math.min(sceneProgress * 50 * phaseMultiplier + 5, 50);
}
