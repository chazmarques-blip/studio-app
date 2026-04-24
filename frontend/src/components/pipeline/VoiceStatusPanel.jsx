import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Mic, Lock, Unlock, AlertTriangle, RefreshCw, Volume2, Loader2,
  CheckCircle2, XCircle, ShieldAlert,
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Friendly error messages for Sora Character Lock failures.
 */
const ERROR_LABELS = {
  moderation_rejected: {
    label: 'Rejeitado por moderação',
    hint: 'A OpenAI recusa rostos humanos realistas. Funciona melhor com estilo animado/estilizado.',
    emoji: '🛡',
  },
  face_detected: {
    label: 'Rosto real detectado',
    hint: 'A API rejeitou porque detectou um rosto humano real no vídeo.',
    emoji: '👤',
  },
  duration_invalid: {
    label: 'Duração inválida',
    hint: 'O vídeo precisa ter 2 a 4 segundos.',
    emoji: '⏱',
  },
  openai_key_missing: {
    label: 'OpenAI key faltando',
    hint: 'Configure a variável OPENAI_API_KEY no servidor.',
    emoji: '🔑',
  },
  download_failed_404: {
    label: 'Vídeo não baixado',
    hint: 'Não foi possível baixar o vídeo da cena âncora.',
    emoji: '📥',
  },
  network_error: { label: 'Erro de rede', hint: 'Tente de novo em alguns segundos.', emoji: '📡' },
};

function statusStyle(s) {
  if (s === 'locked') return { emoji: '🔒', color: 'emerald', label: 'Travada (Sora nativa)' };
  if (s === 'fallback_only')
    return { emoji: '🎙', color: 'amber', label: 'Dublada (ElevenLabs)' };
  return { emoji: '❌', color: 'gray', label: 'Sem voz atribuída' };
}

/**
 * VoiceStatusPanel — shows, for a project:
 *   - Summary: X travadas / Y fallback / Z sem voz
 *   - Per-character row: status badge, Sora character_id, ElevenLabs backup voice
 *   - Actions: preview voice / auto-register all / retry failed / remove lock
 *
 * Props:
 *   - projectId: string
 *   - refreshKey?: any (bump to force reload)
 */
export default function VoiceStatusPanel({ projectId, refreshKey }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);
  const [previewingVoice, setPreviewingVoice] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get(`${API}/studio/projects/${projectId}/voice-status`);
      setData(data);
    } catch (e) {
      toast.error('Falha ao carregar status de voz');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshKey]);

  const autoRegisterAll = async () => {
    setProcessing('auto_register_all');
    try {
      const { data: res } = await axios.post(
        `${API}/studio/projects/${projectId}/auto-register-sora-characters`
      );
      const reg = res.total_registered || 0;
      const failed = (res.failed || []).length;
      if (reg > 0) toast.success(`🔒 ${reg} personagem(ns) travado(s) com sucesso!`);
      if (failed > 0 && reg === 0)
        toast.warning(
          `${failed} rejeitado(s). Veja detalhes abaixo — personagens realistas são bloqueados por moderação.`
        );
      await load();
    } catch (e) {
      toast.error(`Erro: ${e.response?.data?.detail || e.message}`);
    } finally {
      setProcessing(null);
    }
  };

  const retryCharacter = async (name) => {
    setProcessing(`retry_${name}`);
    try {
      // Clear the sticky error first by unregistering, then re-attempt
      await axios.delete(
        `${API}/studio/projects/${projectId}/sora-characters/${encodeURIComponent(name)}`
      );
      await axios.post(
        `${API}/studio/projects/${projectId}/auto-register-sora-characters`
      );
      await load();
    } catch (e) {
      toast.error(`Erro: ${e.response?.data?.detail || e.message}`);
    } finally {
      setProcessing(null);
    }
  };

  const unlockCharacter = async (name) => {
    if (!window.confirm(`Desvincular "${name}" do Sora Character Lock?\n\nA voz voltará a usar o fallback ElevenLabs.`))
      return;
    setProcessing(`unlock_${name}`);
    try {
      await axios.delete(
        `${API}/studio/projects/${projectId}/sora-characters/${encodeURIComponent(name)}`
      );
      toast.success(`🔓 ${name} desvinculado`);
      await load();
    } catch (e) {
      toast.error(`Erro: ${e.response?.data?.detail || e.message}`);
    } finally {
      setProcessing(null);
    }
  };

  const previewVoice = async (voiceId, characterName) => {
    if (!voiceId) return;
    setPreviewingVoice(voiceId);
    try {
      const res = await axios.post(
        `${API}/studio/voice-preview`,
        { voice_id: voiceId, text: `Olá, eu sou ${characterName}.` },
        { responseType: 'blob' }
      );
      const url = URL.createObjectURL(res.data);
      const audio = new Audio(url);
      audio.play();
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setPreviewingVoice(null);
      };
    } catch (e) {
      toast.error('Falha ao reproduzir voz');
      setPreviewingVoice(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12" data-testid="voice-status-loading">
        <Loader2 size={24} className="text-violet-500 animate-spin" />
      </div>
    );
  }

  if (!data || !data.characters?.length) {
    return (
      <div className="text-center py-10 text-sm text-gray-500" data-testid="voice-status-empty">
        Nenhum personagem cadastrado no projeto.
      </div>
    );
  }

  const { counts = {}, characters = [], total = 0 } = data;

  return (
    <div className="space-y-4" data-testid="voice-status-panel">
      {/* Header / Summary */}
      <div className="flex items-center justify-between gap-3 pb-3 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
            <Mic size={16} className="text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-gray-900">Vozes dos Personagens</h3>
            <p className="text-[11px] text-gray-500">
              {counts.locked || 0} travadas · {counts.fallback_only || 0} dubladas · {counts.unassigned || 0} sem voz
              <span className="mx-1.5 text-gray-300">·</span>
              Total: {total}
            </p>
          </div>
        </div>
        <button
          onClick={autoRegisterAll}
          disabled={processing === 'auto_register_all'}
          data-testid="btn-auto-register-all"
          className="h-8 inline-flex items-center gap-1.5 px-3 rounded-md bg-violet-500 hover:bg-violet-600 text-white text-xs font-semibold disabled:opacity-60"
        >
          {processing === 'auto_register_all' ? (
            <>
              <Loader2 size={12} className="animate-spin" /> Registrando…
            </>
          ) : (
            <>
              <Lock size={12} /> Travar Vozes do Sora
            </>
          )}
        </button>
      </div>

      {/* Explanation banner (sticky) */}
      <div className="rounded-lg bg-violet-50 border border-violet-200 p-3 text-[11px] text-violet-900 leading-relaxed">
        <div className="flex items-start gap-2">
          <ShieldAlert size={14} className="text-violet-600 shrink-0 mt-0.5" />
          <div>
            <strong>Como funciona:</strong> A primeira cena renderizada de cada personagem é enviada para a
            OpenAI, que retorna um <code className="px-1 py-0.5 rounded bg-white/70 text-[10px]">character_id</code>{' '}
            permanente. As cenas seguintes usam esse ID para preservar a voz e aparência nativas do Sora 2.
            <br />
            <strong>Fallback:</strong> Se a OpenAI rejeitar (rostos realistas / moderação), o ElevenLabs assume
            como voz dublada — também consistente, pois o voice_id é travado.
          </div>
        </div>
      </div>

      {/* Characters list */}
      <div className="space-y-2">
        {characters.map((c) => {
          const st = statusStyle(c.status);
          const errInfo = c.lock_error ? ERROR_LABELS[c.lock_error] : null;
          return (
            <div
              key={c.name}
              data-testid={`voice-row-${c.name}`}
              className={`flex items-center gap-3 rounded-lg border p-3 bg-white ${
                c.status === 'locked'
                  ? 'border-emerald-200'
                  : c.status === 'fallback_only'
                  ? 'border-amber-200'
                  : 'border-gray-200'
              }`}
            >
              {/* Status emoji */}
              <div className="text-xl leading-none shrink-0 w-8 text-center">{st.emoji}</div>

              {/* Name + info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-semibold text-sm text-gray-900 truncate">{c.name}</span>
                  <span
                    className={`text-[10px] font-medium uppercase tracking-wider px-1.5 py-0.5 rounded ${
                      st.color === 'emerald'
                        ? 'bg-emerald-100 text-emerald-700'
                        : st.color === 'amber'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                  >
                    {st.label}
                  </span>
                  {c.anchor_scene && (
                    <span className="text-[10px] text-gray-500">
                      âncora: cena #{c.anchor_scene}
                    </span>
                  )}
                </div>
                <div className="text-[11px] text-gray-500 flex items-center gap-3 flex-wrap">
                  {c.sora_character_id && (
                    <span>
                      <Lock size={10} className="inline" />{' '}
                      <code className="text-[10px]">{c.sora_character_id.slice(0, 20)}…</code>
                    </span>
                  )}
                  {c.elevenlabs_voice_name && (
                    <span className="flex items-center gap-1">
                      <Volume2 size={10} /> ElevenLabs: <strong>{c.elevenlabs_voice_name}</strong>
                    </span>
                  )}
                  {errInfo && (
                    <span className="flex items-center gap-1 text-red-600">
                      <AlertTriangle size={10} />{' '}
                      <span title={errInfo.hint}>
                        {errInfo.emoji} {errInfo.label}
                      </span>
                    </span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-1.5 shrink-0">
                {c.elevenlabs_voice_id && (
                  <button
                    onClick={() => previewVoice(c.elevenlabs_voice_id, c.name)}
                    disabled={previewingVoice === c.elevenlabs_voice_id}
                    data-testid={`btn-preview-${c.name}`}
                    className="h-7 w-7 inline-flex items-center justify-center rounded-md hover:bg-violet-50 text-violet-600 border border-violet-200 disabled:opacity-50"
                    title="Ouvir voz fallback"
                  >
                    {previewingVoice === c.elevenlabs_voice_id ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Volume2 size={12} />
                    )}
                  </button>
                )}
                {c.lock_error && (
                  <button
                    onClick={() => retryCharacter(c.name)}
                    disabled={processing === `retry_${c.name}`}
                    data-testid={`btn-retry-${c.name}`}
                    className="h-7 inline-flex items-center gap-1 px-2 rounded-md hover:bg-amber-50 text-amber-700 border border-amber-200 text-[10px] font-medium disabled:opacity-50"
                    title="Tentar novamente (o erro ficou memorizado)"
                  >
                    {processing === `retry_${c.name}` ? (
                      <Loader2 size={10} className="animate-spin" />
                    ) : (
                      <RefreshCw size={10} />
                    )}
                    Retry
                  </button>
                )}
                {c.status === 'locked' && (
                  <button
                    onClick={() => unlockCharacter(c.name)}
                    disabled={processing === `unlock_${c.name}`}
                    data-testid={`btn-unlock-${c.name}`}
                    className="h-7 w-7 inline-flex items-center justify-center rounded-md hover:bg-red-50 text-red-600 border border-red-200 disabled:opacity-50"
                    title="Desvincular do Sora Character"
                  >
                    {processing === `unlock_${c.name}` ? (
                      <Loader2 size={12} className="animate-spin" />
                    ) : (
                      <Unlock size={12} />
                    )}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
