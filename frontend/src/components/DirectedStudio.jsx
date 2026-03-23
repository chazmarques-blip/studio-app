import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import { Send, Users, Film, Play, Pause, Sparkles, Download, X, ChevronDown, Plus, Volume2, PenTool, RefreshCw, Check, MessageSquare, Clapperboard, Eye, Camera, Copy, Edit3, Save, Wand2 } from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function DirectedStudio({
  avatars = [], onAddAvatar, onEditAvatar, onRemoveAvatar, onPreviewAvatar,
  onAiEditAvatar, aiEditAvatarId, setAiEditAvatarId, aiEditInstruction, setAiEditInstruction, aiEditLoading,
}) {
  const { i18n } = useTranslation();
  const lang = i18n.language?.substring(0, 2) || 'pt';

  const [step, setStep] = useState(0); // 0 = project list, 1-4 = workflow
  const [projectId, setProjectId] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [scenes, setScenes] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [characterAvatars, setCharacterAvatars] = useState({});
  const [generating, setGenerating] = useState(false);
  const [agentStatus, setAgentStatus] = useState({});
  const [outputs, setOutputs] = useState([]);
  const [allProjects, setAllProjects] = useState([]);
  const [viewingProject, setViewingProject] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [editingChar, setEditingChar] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', description: '', age: '', role: '' });
  const [showNewProject, setShowNewProject] = useState(false);
  const chatEndRef = useRef(null);

  const STEPS = [
    { n: 1, icon: MessageSquare, label: lang === 'pt' ? 'Roteiro' : 'Script' },
    { n: 2, icon: Users, label: lang === 'pt' ? 'Personagens' : 'Characters' },
    { n: 3, icon: Clapperboard, label: lang === 'pt' ? 'Produção' : 'Production' },
    { n: 4, icon: Eye, label: lang === 'pt' ? 'Resultado' : 'Result' },
  ];

  const STATUS_LABELS = {
    draft: { pt: 'Rascunho', en: 'Draft', color: 'text-[#888]' },
    scripting: { pt: 'Roteiro', en: 'Scripting', color: 'text-blue-400' },
    starting: { pt: 'Iniciando', en: 'Starting', color: 'text-yellow-400' },
    running_agents: { pt: 'Produzindo', en: 'Producing', color: 'text-orange-400' },
    complete: { pt: 'Concluído', en: 'Complete', color: 'text-emerald-400' },
    error: { pt: 'Erro', en: 'Error', color: 'text-red-400' },
  };

  // Load all projects
  const loadProjects = () => {
    axios.get(`${API}/studio/projects`).then(r => {
      setAllProjects(r.data.projects || []);
    }).catch(() => {});
  };

  useEffect(() => { loadProjects(); }, []);

  // Auto-resume in-progress project
  useEffect(() => {
    const inProgress = allProjects.find(p =>
      ['starting', 'running_agents', 'generating_video'].includes(p.status)
    );
    if (inProgress && !projectId) {
      resumeProject(inProgress);
    }
  }, [allProjects]);

  // Resume a project from its current step
  const resumeProject = (proj) => {
    setProjectId(proj.id);
    setProjectName(proj.name || '');
    setProjectDesc(proj.briefing || '');
    setScenes(proj.scenes || []);
    setCharacters(proj.characters || []);
    setChatMessages(proj.chat_history || []);
    setOutputs(proj.outputs || []);
    setCharacterAvatars({});
    setViewingProject(null);

    if (['starting', 'running_agents', 'generating_video'].includes(proj.status)) {
      setStep(3); setGenerating(true); startPolling(proj.id);
    } else if (proj.status === 'complete' && proj.outputs?.length > 0) {
      setStep(4); setOutputs(proj.outputs);
    } else if ((proj.scenes || []).length > 0) {
      setStep(2);
    } else {
      setStep(1);
    }
  };

  // Create a new project (name + description first)
  const createNewProject = async () => {
    if (!projectName.trim()) {
      toast.error(lang === 'pt' ? 'Dê um nome ao projecto' : 'Give the project a name');
      return;
    }
    try {
      const res = await axios.post(`${API}/studio/projects`, { name: projectName.trim(), briefing: projectDesc.trim() });
      setProjectId(res.data.id);
      setStep(1); setChatMessages([]); setScenes([]); setCharacters([]); setOutputs([]);
      setShowNewProject(false);
      loadProjects();
      toast.success(lang === 'pt' ? 'Projecto criado!' : 'Project created!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error');
    }
  };

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

  // Send message to Screenwriter (background + polling)
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
      }, { timeout: 15000 });
      const pid = res.data.project_id;
      setProjectId(pid);
      // Poll for screenwriter result
      pollChatResult(pid);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Screenwriter error');
      setChatMessages(prev => [...prev, { role: 'assistant', text: '❌ Erro ao processar. Tente novamente.' }]);
      setChatLoading(false);
    }
  };

  const pollChatResult = (pid) => {
    const poll = () => {
      axios.get(`${API}/studio/projects/${pid}/status`).then(res => {
        const d = res.data;
        if (d.chat_status === 'done') {
          // Get the last assistant message from chat_history
          const history = d.chat_history || [];
          const lastAssistant = [...history].reverse().find(m => m.role === 'assistant');
          if (lastAssistant) {
            setChatMessages(prev => {
              // Avoid duplicating if already added
              const lastMsg = prev[prev.length - 1];
              if (lastMsg?.role === 'assistant' && lastMsg?.text === lastAssistant.text) return prev;
              return [...prev, { role: 'assistant', text: lastAssistant.text }];
            });
          }
          setScenes(d.scenes || []);
          setCharacters(d.characters || []);
          setChatLoading(false);
          return;
        }
        if (d.chat_status === 'error') {
          toast.error(d.error || 'Erro ao processar');
          setChatMessages(prev => [...prev, { role: 'assistant', text: `❌ ${d.error || 'Erro ao processar. Tente novamente.'}` }]);
          setChatLoading(false);
          return;
        }
        // Still thinking
        setTimeout(poll, 3000);
      }).catch(() => setTimeout(poll, 5000));
    };
    setTimeout(poll, 2000);
  };

  // Copy character prompt to clipboard (with fallback for iframe/permissions)
  const copyPrompt = (char) => {
    const prompt = `${char.name}: ${char.description}. ${char.age || ''}, ${char.role || ''}`.trim();
    try {
      const ta = document.createElement('textarea');
      ta.value = prompt;
      ta.style.position = 'fixed';
      ta.style.left = '-9999px';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
      toast.success(lang === 'pt' ? 'Prompt copiado!' : 'Prompt copied!');
    } catch {
      toast.error(lang === 'pt' ? 'Erro ao copiar' : 'Copy failed');
    }
  };

  // Start editing a character
  const startEditChar = (idx) => {
    const c = characters[idx];
    setEditForm({ name: c.name || '', description: c.description || '', age: c.age || '', role: c.role || '' });
    setEditingChar(idx);
  };

  // Save edited character
  const saveEditChar = async () => {
    if (editingChar === null) return;
    const updated = [...characters];
    updated[editingChar] = { ...updated[editingChar], ...editForm };
    setCharacters(updated);
    setEditingChar(null);
    // Persist to backend
    if (projectId) {
      try {
        await axios.post(`${API}/studio/projects/${projectId}/update-characters`, { characters: updated });
      } catch { /* silent */ }
    }
    toast.success(lang === 'pt' ? 'Personagem atualizado!' : 'Character updated!');
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
        character_avatars: characterAvatars,
      });
      startPolling(projectId);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start');
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-3" data-testid="directed-studio">
      {/* Step Navigation — only when inside a project */}
      {step >= 1 && (
        <div className="flex items-center justify-between mb-1">
          <button onClick={() => { setStep(0); setViewingProject(null); }}
            className="text-[9px] text-[#C9A84C] hover:underline flex items-center gap-1">
            ← {lang === 'pt' ? 'Projectos' : 'Projects'}
          </button>
          <p className="text-[9px] text-[#666] truncate max-w-[200px]">{projectName}</p>
        </div>
      )}
      {step >= 1 && (
        <div className="flex items-center justify-center gap-1 my-1">
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
      )}

      {/* ═══ STEP 0: Project List ═══ */}
      {step === 0 && !viewingProject && (
        <div className="space-y-3" data-testid="studio-project-list">
          {!showNewProject ? (
            <button onClick={() => setShowNewProject(true)} data-testid="new-project-btn"
              className="w-full glass-card p-3 flex items-center gap-3 hover:border-[#C9A84C]/30 transition group border border-dashed border-[#333]">
              <div className="h-10 w-10 rounded-lg bg-[#C9A84C]/10 flex items-center justify-center group-hover:bg-[#C9A84C]/20 transition">
                <Plus size={18} className="text-[#C9A84C]" />
              </div>
              <div className="text-left">
                <p className="text-xs font-semibold text-white">{lang === 'pt' ? 'Novo Projecto' : 'New Project'}</p>
                <p className="text-[8px] text-[#666]">{lang === 'pt' ? 'Crie uma nova produção com IA' : 'Create a new AI production'}</p>
              </div>
            </button>
          ) : (
            <div className="glass-card p-3 space-y-2 border border-[#C9A84C]/20" data-testid="new-project-form">
              <h3 className="text-xs font-semibold text-white flex items-center gap-2">
                <Clapperboard size={12} className="text-[#C9A84C]" />
                {lang === 'pt' ? 'Novo Projecto' : 'New Project'}
              </h3>
              <input value={projectName} onChange={e => setProjectName(e.target.value)}
                placeholder={lang === 'pt' ? 'Nome do projecto (ex: A História de Abraão)' : 'Project name'}
                data-testid="new-project-name"
                className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-3 py-2 text-[11px] text-white outline-none focus:border-[#C9A84C]/50 placeholder-[#555]" />
              <textarea value={projectDesc} onChange={e => setProjectDesc(e.target.value)}
                placeholder={lang === 'pt' ? 'Descreva brevemente o projecto...' : 'Brief description...'}
                data-testid="new-project-desc"
                rows={2}
                className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-3 py-2 text-[10px] text-white outline-none focus:border-[#C9A84C]/50 placeholder-[#555] resize-none" />
              <div className="flex gap-2">
                <button onClick={() => { setShowNewProject(false); setProjectName(''); setProjectDesc(''); }}
                  className="flex-1 rounded-lg border border-[#333] py-2 text-[10px] text-[#999] hover:text-white transition">
                  {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                </button>
                <button onClick={createNewProject} disabled={!projectName.trim()} data-testid="create-project-btn"
                  className="flex-1 btn-gold rounded-lg py-2 text-[10px] font-semibold disabled:opacity-30 flex items-center justify-center gap-1">
                  <Sparkles size={10} /> {lang === 'pt' ? 'Criar Projecto' : 'Create Project'}
                </button>
              </div>
            </div>
          )}

          {allProjects.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-[9px] text-[#666] uppercase tracking-wider font-medium">
                {allProjects.length} {lang === 'pt' ? 'projectos' : 'projects'}
              </p>
              {allProjects.map(proj => {
                const sl = STATUS_LABELS[proj.status] || STATUS_LABELS.draft;
                const scenesCount = (proj.scenes || []).length;
                const videosCount = (proj.outputs || []).filter(o => o.type === 'video').length;
                const vid = proj.outputs?.find(o => o.type === 'video' && o.label === 'complete') || proj.outputs?.find(o => o.type === 'video');
                return (
                  <button key={proj.id} onClick={() => resumeProject(proj)} data-testid={`project-${proj.id}`}
                    className="w-full glass-card p-2.5 flex items-center gap-2.5 hover:border-[#C9A84C]/30 transition text-left group">
                    <div className="h-14 w-12 rounded-lg bg-[#111] flex-shrink-0 overflow-hidden border border-[#222] relative">
                      {vid ? (
                        <>
                          <video src={vid.url} className="w-full h-full object-cover" muted />
                          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                            <Play size={12} className="text-[#C9A84C]" />
                          </div>
                        </>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Film size={16} className="text-[#333]" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-semibold text-white truncate group-hover:text-[#C9A84C] transition">
                        {proj.name || proj.briefing?.slice(0, 40) || 'Sem nome'}
                      </p>
                      <p className="text-[8px] text-[#666] truncate mt-0.5">{proj.briefing?.slice(0, 60) || ''}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[7px] font-medium ${sl.color}`}>{sl[lang] || sl.en}</span>
                        {scenesCount > 0 && <span className="text-[7px] text-[#555]">{scenesCount} {lang === 'pt' ? 'cenas' : 'scenes'}</span>}
                        {videosCount > 0 && <span className="text-[7px] text-emerald-500">{videosCount} {lang === 'pt' ? 'vídeos' : 'videos'}</span>}
                      </div>
                    </div>
                    <div className="flex-shrink-0">
                      {['starting', 'running_agents'].includes(proj.status) ? (
                        <RefreshCw size={12} className="text-orange-400 animate-spin" />
                      ) : proj.status === 'complete' ? (
                        <Check size={12} className="text-emerald-400" />
                      ) : null}
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
            {lang === 'pt' ? 'Edite, vincule avatares ou copie o prompt de cada personagem' : 'Edit, link avatars or copy each character prompt'}
          </p>

          <div className="space-y-2">
            {characters.map((char, ci) => (
              <div key={ci} className="rounded-lg border border-[#222] bg-[#0A0A0A] p-2.5">
                {/* Character header */}
                {editingChar === ci ? (
                  /* ── Inline Edit Mode ── */
                  <div className="space-y-2 mb-2">
                    <div className="flex gap-2">
                      <input value={editForm.name} onChange={e => setEditForm(p => ({ ...p, name: e.target.value }))}
                        placeholder={lang === 'pt' ? 'Nome' : 'Name'}
                        data-testid={`edit-char-name-${ci}`}
                        className="flex-1 bg-[#111] border border-[#333] rounded px-2 py-1 text-[10px] text-white outline-none focus:border-[#C9A84C]/50" />
                      <input value={editForm.age} onChange={e => setEditForm(p => ({ ...p, age: e.target.value }))}
                        placeholder={lang === 'pt' ? 'Idade' : 'Age'}
                        className="w-16 bg-[#111] border border-[#333] rounded px-2 py-1 text-[10px] text-white outline-none focus:border-[#C9A84C]/50" />
                      <input value={editForm.role} onChange={e => setEditForm(p => ({ ...p, role: e.target.value }))}
                        placeholder={lang === 'pt' ? 'Papel' : 'Role'}
                        className="w-24 bg-[#111] border border-[#333] rounded px-2 py-1 text-[10px] text-white outline-none focus:border-[#C9A84C]/50" />
                    </div>
                    <textarea value={editForm.description} onChange={e => setEditForm(p => ({ ...p, description: e.target.value }))}
                      placeholder={lang === 'pt' ? 'Descrição visual do personagem...' : 'Visual description...'}
                      data-testid={`edit-char-desc-${ci}`}
                      rows={2}
                      className="w-full bg-[#111] border border-[#333] rounded px-2 py-1.5 text-[9px] text-white outline-none focus:border-[#C9A84C]/50 resize-none" />
                    <div className="flex gap-1.5">
                      <button onClick={saveEditChar} data-testid={`save-char-${ci}`}
                        className="flex items-center gap-1 bg-[#C9A84C]/15 border border-[#C9A84C]/30 text-[#C9A84C] rounded px-2 py-1 text-[8px] font-medium hover:bg-[#C9A84C]/25 transition">
                        <Save size={9} /> {lang === 'pt' ? 'Salvar' : 'Save'}
                      </button>
                      <button onClick={() => setEditingChar(null)}
                        className="flex items-center gap-1 border border-[#333] text-[#888] rounded px-2 py-1 text-[8px] hover:text-white transition">
                        <X size={9} /> {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                      </button>
                    </div>
                  </div>
                ) : (
                  /* ── View Mode ── */
                  <div className="flex items-start gap-2 mb-2">
                    {characterAvatars[char.name] ? (
                      <img src={resolveImageUrl(characterAvatars[char.name])} alt="" className="h-12 w-10 rounded-lg object-cover border border-[#C9A84C]/30 flex-shrink-0" />
                    ) : (
                      <div className="h-12 w-10 rounded-lg bg-[#1A1A1A] flex items-center justify-center border border-dashed border-[#333] flex-shrink-0">
                        <Users size={14} className="text-[#444]" />
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5">
                        <p className="text-[11px] font-bold text-white">{char.name}</p>
                        {!characterAvatars[char.name] && (
                          <span className="text-[6px] bg-red-500/10 text-red-400 border border-red-500/20 rounded px-1 py-0.5">
                            {lang === 'pt' ? 'Sem avatar' : 'No avatar'}
                          </span>
                        )}
                      </div>
                      <p className="text-[8px] text-[#888] leading-relaxed mt-0.5">{char.description}</p>
                      <p className="text-[7px] text-[#555] mt-0.5">{char.age} • {char.role}</p>
                    </div>
                    {/* Action buttons */}
                    <div className="flex flex-col gap-1 flex-shrink-0">
                      <button onClick={() => copyPrompt(char)} data-testid={`copy-prompt-${ci}`}
                        title={lang === 'pt' ? 'Copiar prompt' : 'Copy prompt'}
                        className="flex items-center gap-1 border border-[#333] text-[#888] rounded px-1.5 py-1 text-[7px] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
                        <Copy size={9} /> <span className="hidden sm:inline">{lang === 'pt' ? 'Copiar' : 'Copy'}</span>
                      </button>
                      <button onClick={() => startEditChar(ci)} data-testid={`edit-char-${ci}`}
                        title={lang === 'pt' ? 'Editar personagem' : 'Edit character'}
                        className="flex items-center gap-1 border border-[#333] text-[#888] rounded px-1.5 py-1 text-[7px] hover:text-[#C9A84C] hover:border-[#C9A84C]/30 transition">
                        <Edit3 size={9} /> <span className="hidden sm:inline">{lang === 'pt' ? 'Editar' : 'Edit'}</span>
                      </button>
                    </div>
                  </div>
                )}

                {/* Avatar selection with full controls */}
                <div className="flex gap-1.5 flex-wrap items-center">
                  {avatars.map((av, ai) => {
                    const isLinked = characterAvatars[char.name] === av.url;
                    const isEditing = aiEditAvatarId === av.id;
                    return (
                      <div key={ai} className={`relative rounded-lg overflow-hidden border-2 transition cursor-pointer group ${
                        isLinked ? 'border-[#C9A84C] shadow-[0_0_8px_rgba(201,168,76,0.25)]' : 'border-[#222] hover:border-[#444]'
                      }`} style={{ width: 52, height: 68 }}>
                        <img src={resolveImageUrl(av.url)} alt={av.name}
                          className="w-full h-full object-cover"
                          onClick={() => linkAvatar(char.name, av.url)} />
                        {isLinked && (
                          <div className="absolute top-0.5 right-0.5 h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center">
                            <Check size={8} className="text-black" />
                          </div>
                        )}
                        {/* Action bar — always visible on hover */}
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent px-0.5 py-0.5 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={e => { e.stopPropagation(); onPreviewAvatar(av.url); }}
                            className="h-5 w-5 rounded flex items-center justify-center text-white/70 hover:text-white transition" title={lang === 'pt' ? 'Ver zoom' : 'Preview'}>
                            <Eye size={9} />
                          </button>
                          <div className="flex items-center gap-0.5">
                            <button onClick={e => { e.stopPropagation(); setAiEditAvatarId(isEditing ? null : av.id); setAiEditInstruction(char.description || ''); }}
                              className="h-5 w-5 rounded flex items-center justify-center text-purple-400 hover:text-purple-300 transition" title={lang === 'pt' ? 'Editar com IA' : 'AI Edit'}>
                              <Sparkles size={9} />
                            </button>
                            <button onClick={e => { e.stopPropagation(); onEditAvatar(av); }}
                              className="h-5 w-5 rounded flex items-center justify-center text-[#C9A84C] hover:text-[#D4B85C] transition" title={lang === 'pt' ? 'Editar' : 'Edit'}>
                              <PenTool size={9} />
                            </button>
                          </div>
                        </div>
                        {/* AI Edit overlay */}
                        {isEditing && (
                          <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-1 z-10" onClick={e => e.stopPropagation()}>
                            <Sparkles size={10} className="text-purple-400 mb-0.5" />
                            <textarea value={aiEditInstruction} onChange={e => setAiEditInstruction(e.target.value)}
                              placeholder={lang === 'pt' ? 'Ex: mudar roupa...' : 'Ex: change outfit...'}
                              className="w-full text-[7px] bg-[#1A1A1A] border border-[#333] rounded p-1 text-white placeholder-[#666] resize-none outline-none focus:border-purple-500/40"
                              rows={2} />
                            <div className="flex gap-0.5 mt-0.5 w-full">
                              <button onClick={() => { setAiEditAvatarId(null); setAiEditInstruction(''); }}
                                className="flex-1 text-[6px] py-0.5 rounded border border-[#333] text-[#888] hover:text-white transition">
                                {lang === 'pt' ? 'Cancelar' : 'Cancel'}
                              </button>
                              <button onClick={() => onAiEditAvatar(av.id)} disabled={aiEditLoading || !aiEditInstruction.trim()}
                                className="flex-1 text-[6px] py-0.5 rounded bg-purple-600 text-white font-bold hover:bg-purple-500 transition disabled:opacity-40 flex items-center justify-center gap-0.5">
                                {aiEditLoading ? <RefreshCw size={7} className="animate-spin" /> : <Sparkles size={7} />}
                                {aiEditLoading ? '' : (lang === 'pt' ? 'Criar' : 'Create')}
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {/* Create new avatar button */}
                  <button onClick={onAddAvatar} data-testid={`add-avatar-${ci}`}
                    title={lang === 'pt' ? 'Criar novo avatar' : 'Create new avatar'}
                    className="rounded-lg border border-dashed border-[#444] flex flex-col items-center justify-center hover:border-[#C9A84C]/50 hover:bg-[#C9A84C]/5 transition group"
                    style={{ width: 52, height: 68 }}>
                    <Plus size={12} className="text-[#555] group-hover:text-[#C9A84C]" />
                    <span className="text-[6px] text-[#555] group-hover:text-[#C9A84C] mt-0.5">{lang === 'pt' ? 'Novo' : 'New'}</span>
                  </button>
                </div>

                {/* Selected avatar AI edit hint (when avatar is linked but overlay not open) */}
                {characterAvatars[char.name] && !avatars.find(a => a.url === characterAvatars[char.name] && aiEditAvatarId === a.id) && (
                  <p className="text-[7px] text-[#555] mt-1.5 italic">
                    {lang === 'pt' ? 'Passe o mouse sobre o avatar para ver, editar ou criar nova versão com IA' : 'Hover over avatar to preview, edit or create new AI version'}
                  </p>
                )}
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
