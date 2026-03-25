import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Volume2, Music, Globe, Play, Download, RefreshCw, CheckCircle, AlertTriangle, Headphones, Languages } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const VOICES = [
  { id: "21m00Tcm4TlvDq8ikWAM", name: "Rachel", gender: "F", style: "Calm, warm" },
  { id: "29vD33N1CtxCmqQRPOHJ", name: "Drew", gender: "M", style: "Soft, narrative" },
  { id: "N2lVS1w4EtoT3dr4eOWO", name: "Callum", gender: "M", style: "Intense, dramatic" },
  { id: "EXAVITQu4vr4xnSDxMaL", name: "Sarah", gender: "F", style: "Soft, gentle" },
  { id: "CwhRBWXzGAHq8TQ4Fs17", name: "Roger", gender: "M", style: "Confident, commanding" },
  { id: "pFZP5JQG7iQjIQuC4Bku", name: "Lily", gender: "F", style: "Warm, elegant" },
  { id: "onwK4e9ZLuTAKqWW03F9", name: "Daniel", gender: "M", style: "Authoritative, deep" },
  { id: "pqHfZKP75CvOlQylNhV4", name: "Bill", gender: "M", style: "Trustworthy, wise" },
];

const MUSIC_TRACKS = [
  { id: "emotional", name: "Emotional & Inspiring", cat: "Orquestral" },
  { id: "cinematic", name: "Cinematic & Epic", cat: "Cinema" },
  { id: "gospel_uplifting", name: "Gospel Uplifting", cat: "Gospel" },
  { id: "classical_piano", name: "Classical Piano", cat: "Clássica" },
  { id: "ambient_dreamy", name: "Dreamy Ambient", cat: "Ambiente" },
  { id: "jazz_lofi", name: "Lo-Fi Chill", cat: "Jazz" },
  { id: "pop_acoustic", name: "Pop Acoustic", cat: "Pop" },
  { id: "corporate", name: "Corporate", cat: "Corporativo" },
];

const LANGUAGES = [
  { code: "pt", name: "Português", flag: "🇧🇷" },
  { code: "en", name: "English", flag: "🇺🇸" },
  { code: "es", name: "Español", flag: "🇪🇸" },
  { code: "fr", name: "Français", flag: "🇫🇷" },
  { code: "de", name: "Deutsch", flag: "🇩🇪" },
  { code: "it", name: "Italiano", flag: "🇮🇹" },
];

const phaseLabels = {
  starting: "Iniciando...",
  narration: "Gerando narrações",
  downloading: "Baixando vídeos",
  mixing: "Mixando áudio",
  uploading: "Enviando vídeo",
  complete: "Concluído",
  error: "Erro",
  translating: "Traduzindo",
  generating_audio: "Gerando áudio",
};

export function PostProduction({ project, onUpdate }) {
  const [voiceId, setVoiceId] = useState("21m00Tcm4TlvDq8ikWAM");
  const [musicTrack, setMusicTrack] = useState("");
  const [musicVolume, setMusicVolume] = useState(0.15);
  const [ppStatus, setPpStatus] = useState({});
  const [localizations, setLocalizations] = useState({});
  const [finalVideos, setFinalVideos] = useState({});
  const [locStatuses, setLocStatuses] = useState({});
  const [isProducing, setIsProducing] = useState(false);
  const [locTarget, setLocTarget] = useState("");
  const pollRef = useRef(null);

  const projectId = project?.id;
  const originalLang = project?.language || "pt";

  const sceneVideoCount = (project?.outputs || []).filter(
    o => o.type === "video" && (o.scene_number || 0) > 0 && o.url
  ).length;

  useEffect(() => {
    if (projectId) loadStatus();
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [projectId]);

  const loadStatus = async () => {
    try {
      const [ppRes, locRes] = await Promise.all([
        axios.get(`${API}/api/studio/projects/${projectId}/post-production-status`),
        axios.get(`${API}/api/studio/projects/${projectId}/localizations`),
      ]);
      setPpStatus(ppRes.data.status || {});
      setLocalizations(locRes.data.localizations || {});
      setFinalVideos(locRes.data.final_videos || {});
      setLocStatuses(locRes.data.statuses || {});

      const phase = ppRes.data.status?.phase;
      if (phase && !["complete", "error"].includes(phase)) {
        setIsProducing(true);
        startPolling();
      }
    } catch { /* ignore */ }
  };

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const [ppRes, locRes] = await Promise.all([
          axios.get(`${API}/api/studio/projects/${projectId}/post-production-status`),
          axios.get(`${API}/api/studio/projects/${projectId}/localizations`),
        ]);
        const st = ppRes.data.status || {};
        setPpStatus(st);
        setFinalVideos(locRes.data.final_videos || {});
        setLocStatuses(locRes.data.statuses || {});
        setLocalizations(locRes.data.localizations || {});

        if (st.phase === "complete") {
          setIsProducing(false);
          clearInterval(pollRef.current);
          toast.success("Pós-produção concluída!");
          if (onUpdate) onUpdate();
        } else if (st.phase === "error") {
          setIsProducing(false);
          clearInterval(pollRef.current);
          toast.error(`Erro: ${st.error || "desconhecido"}`);
        }

        // Check localization statuses
        for (const [lc, ls] of Object.entries(locRes.data.statuses || {})) {
          if (ls.phase === "complete" && locStatuses[lc]?.phase !== "complete") {
            toast.success(`Localização ${lc.toUpperCase()} concluída!`);
          }
        }
      } catch { /* ignore */ }
    }, 4000);
  };

  const startPostProduction = async () => {
    try {
      setIsProducing(true);
      await axios.post(`${API}/api/studio/projects/${projectId}/post-produce`, {
        voice_id: voiceId,
        stability: 0.30,
        similarity: 0.80,
        style_val: 0.55,
        music_track: musicTrack,
        music_volume: musicVolume,
        transition_type: "fade",
        transition_duration: 0.5,
      });
      toast.success("Pós-produção iniciada!");
      startPolling();
    } catch (e) {
      setIsProducing(false);
      toast.error(e.response?.data?.detail || "Erro ao iniciar");
    }
  };

  const startLocalization = async (targetLang) => {
    try {
      setLocTarget(targetLang);
      await axios.post(`${API}/api/studio/projects/${projectId}/localize`, {
        target_language: targetLang,
        voice_id: voiceId,
      });
      toast.success(`Localização para ${targetLang.toUpperCase()} iniciada!`);
      startPolling();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Erro");
      setLocTarget("");
    }
  };

  const ppPhase = ppStatus?.phase;
  const ppComplete = ppPhase === "complete";
  const ppRunning = ppPhase && !["complete", "error"].includes(ppPhase);
  const ppProgress = ppStatus?.done != null && ppStatus?.total ? Math.round((ppStatus.done / ppStatus.total) * 100) : 0;

  return (
    <div data-testid="post-production-panel" className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <Headphones size={16} className="text-[#C9A84C]" />
        <h3 className="text-sm font-semibold text-white">Pós-Produção</h3>
        {ppComplete && <CheckCircle size={14} className="text-green-500" />}
      </div>

      {/* Scene video count */}
      <div className="text-[10px] text-[#888] bg-[#0A0A0A] rounded-lg p-2 border border-[#222]">
        <span className="text-[#C9A84C] font-medium">{sceneVideoCount}</span> vídeos de cena disponíveis
        {ppComplete && ppStatus.final_url && (
          <span className="ml-2 text-green-400">• Vídeo final com áudio pronto</span>
        )}
      </div>

      {/* ── Configuration (only show if not complete) ── */}
      {!ppComplete && (
        <div className="space-y-3 bg-[#0F0F0F] rounded-xl border border-[#1E1E1E] p-3">
          {/* Voice Selection */}
          <div>
            <label className="text-[10px] text-[#888] uppercase tracking-wider mb-1 flex items-center gap-1">
              <Volume2 size={10} /> Narrador
            </label>
            <div className="grid grid-cols-2 gap-1.5">
              {VOICES.map(v => (
                <button
                  key={v.id}
                  data-testid={`voice-${v.id}`}
                  onClick={() => setVoiceId(v.id)}
                  className={`text-left p-2 rounded-lg border text-[9px] transition-all ${
                    voiceId === v.id
                      ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10'
                      : 'border-[#222] bg-[#0A0A0A] hover:border-[#444]'
                  }`}
                >
                  <span className={`font-medium ${voiceId === v.id ? 'text-[#C9A84C]' : 'text-white'}`}>
                    {v.name}
                  </span>
                  <span className="text-[#666] ml-1">({v.gender})</span>
                  <div className="text-[#555] mt-0.5">{v.style}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Music Selection */}
          <div>
            <label className="text-[10px] text-[#888] uppercase tracking-wider mb-1 flex items-center gap-1">
              <Music size={10} /> Trilha Sonora
            </label>
            <select
              data-testid="music-track-select"
              value={musicTrack}
              onChange={e => setMusicTrack(e.target.value)}
              className="w-full bg-[#0A0A0A] border border-[#333] rounded-lg px-2 py-1.5 text-[10px] text-white outline-none focus:border-[#C9A84C]/50"
            >
              <option value="">Auto (baseado no Production Design)</option>
              {MUSIC_TRACKS.map(m => (
                <option key={m.id} value={m.id}>{m.name} — {m.cat}</option>
              ))}
            </select>
          </div>

          {/* Music Volume */}
          <div>
            <label className="text-[10px] text-[#888] uppercase tracking-wider mb-1 flex items-center gap-1">
              Volume da Trilha: {Math.round(musicVolume * 100)}%
            </label>
            <input
              type="range"
              min="0" max="0.5" step="0.05"
              value={musicVolume}
              onChange={e => setMusicVolume(parseFloat(e.target.value))}
              className="w-full accent-[#C9A84C]"
              data-testid="music-volume-slider"
            />
          </div>

          {/* Start Button */}
          <button
            data-testid="start-post-production-btn"
            onClick={startPostProduction}
            disabled={isProducing || sceneVideoCount === 0}
            className="w-full py-2.5 rounded-lg font-medium text-xs transition-all disabled:opacity-40
              bg-gradient-to-r from-[#C9A84C] to-[#B8973F] text-black hover:brightness-110"
          >
            {isProducing ? (
              <span className="flex items-center justify-center gap-2">
                <RefreshCw size={12} className="animate-spin" />
                {phaseLabels[ppPhase] || ppPhase}
                {ppProgress > 0 && ` (${ppProgress}%)`}
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <Play size={12} /> Produzir Vídeo Final com Áudio
              </span>
            )}
          </button>

          {ppStatus.message && ppRunning && (
            <div className="text-[9px] text-[#888] text-center animate-pulse">{ppStatus.message}</div>
          )}
        </div>
      )}

      {/* ── Progress Bar (when running) ── */}
      {ppRunning && ppProgress > 0 && (
        <div className="w-full bg-[#1A1A1A] rounded-full h-1.5">
          <div
            className="bg-[#C9A84C] h-1.5 rounded-full transition-all duration-500"
            style={{ width: `${ppProgress}%` }}
          />
        </div>
      )}

      {/* ── Error ── */}
      {ppPhase === "error" && (
        <div className="flex items-start gap-2 p-2 bg-red-500/10 border border-red-500/30 rounded-lg">
          <AlertTriangle size={14} className="text-red-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-[10px] text-red-400 font-medium">Erro na pós-produção</p>
            <p className="text-[9px] text-red-300/70 mt-0.5">{ppStatus.error}</p>
            <button
              onClick={startPostProduction}
              className="text-[9px] text-[#C9A84C] mt-1 hover:underline"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      )}

      {/* ── Result: Final Video ── */}
      {ppComplete && ppStatus.final_url && (
        <div className="space-y-2 bg-[#0A0A0A] rounded-xl border border-green-500/20 p-3">
          <div className="flex items-center gap-2 text-[10px]">
            <CheckCircle size={12} className="text-green-500" />
            <span className="text-green-400 font-medium">Vídeo Final Pronto</span>
            <span className="text-[#666]">
              {ppStatus.duration ? `${Math.round(ppStatus.duration)}s` : ""} •
              {ppStatus.has_narration ? " Narração" : ""}{ppStatus.has_music ? " + Trilha" : ""}
            </span>
          </div>
          <video
            data-testid="final-video-player"
            src={ppStatus.final_url}
            controls
            className="w-full rounded-lg border border-[#222] max-h-48"
          />
          <a
            href={ppStatus.final_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1 text-[9px] text-[#C9A84C] hover:underline"
            data-testid="download-final-video"
          >
            <Download size={10} /> Baixar vídeo ({ppStatus.language?.toUpperCase()})
          </a>
        </div>
      )}

      {/* ── Localization Section ── */}
      {ppComplete && (
        <div className="space-y-2 bg-[#0F0F0F] rounded-xl border border-[#1E1E1E] p-3">
          <div className="flex items-center gap-2 mb-2">
            <Languages size={14} className="text-[#C9A84C]" />
            <span className="text-xs font-medium text-white">Localização Multi-Idioma</span>
          </div>
          <p className="text-[9px] text-[#666] mb-2">
            Mesmo vídeo, nova narração. A IA traduz e gera áudio no idioma selecionado.
          </p>

          <div className="grid grid-cols-3 gap-1.5">
            {LANGUAGES.filter(l => l.code !== originalLang).map(lang => {
              const locStatus = locStatuses[lang.code] || {};
              const fv = finalVideos[lang.code];
              const isRunning = locStatus.phase && !["complete", "error"].includes(locStatus.phase);
              const isDone = locStatus.phase === "complete" || fv;

              return (
                <div key={lang.code} className="relative">
                  <button
                    data-testid={`localize-${lang.code}-btn`}
                    onClick={() => !isRunning && startLocalization(lang.code)}
                    disabled={isRunning}
                    className={`w-full p-2 rounded-lg border text-[9px] transition-all ${
                      isDone
                        ? 'border-green-500/30 bg-green-500/5'
                        : isRunning
                        ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5'
                        : 'border-[#222] bg-[#0A0A0A] hover:border-[#C9A84C]/30'
                    }`}
                  >
                    <div className="text-center">
                      <span className="text-sm">{lang.flag}</span>
                      <div className={`font-medium mt-0.5 ${isDone ? 'text-green-400' : isRunning ? 'text-[#C9A84C]' : 'text-white'}`}>
                        {lang.name}
                      </div>
                      {isRunning && (
                        <div className="flex items-center justify-center gap-1 mt-0.5">
                          <RefreshCw size={8} className="animate-spin text-[#C9A84C]" />
                          <span className="text-[8px] text-[#C9A84C]">{phaseLabels[locStatus.phase] || locStatus.phase}</span>
                        </div>
                      )}
                      {isDone && <CheckCircle size={10} className="text-green-500 mx-auto mt-0.5" />}
                    </div>
                  </button>
                </div>
              );
            })}
          </div>

          {/* Localized videos */}
          {Object.entries(finalVideos).filter(([lc]) => lc !== originalLang).map(([lc, fv]) => (
            <div key={lc} className="mt-2 p-2 bg-[#0A0A0A] rounded-lg border border-[#222]">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[10px] text-white font-medium">
                  {LANGUAGES.find(l => l.code === lc)?.flag} {LANGUAGES.find(l => l.code === lc)?.name}
                </span>
                <span className="text-[8px] text-[#666]">
                  {fv.duration ? `${Math.round(fv.duration)}s` : ""} • {fv.file_size_mb}MB
                </span>
              </div>
              <video src={fv.url} controls className="w-full rounded-lg border border-[#222] max-h-36" />
              <a href={fv.url} target="_blank" rel="noopener noreferrer"
                className="flex items-center justify-center gap-1 mt-1 text-[9px] text-[#C9A84C] hover:underline"
                data-testid={`download-${lc}-video`}
              >
                <Download size={10} /> Baixar ({lc.toUpperCase()})
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
