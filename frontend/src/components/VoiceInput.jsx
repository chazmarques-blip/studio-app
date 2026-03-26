import { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * VoiceInput — Universal voice command button.
 * Records audio, transcribes with Whisper, calls onResult with text.
 */
export function VoiceInput({ onResult, lang = 'pt', className = '', size = 12 }) {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    setRecording(false);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        toast.error(lang === 'pt' ? 'Microfone nao suportado neste navegador' : 'Microphone not supported');
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Try preferred format, fallback to default
      let options = {};
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options = { mimeType: 'audio/webm;codecs=opus' };
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        options = { mimeType: 'audio/webm' };
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        options = { mimeType: 'audio/mp4' };
      }

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;

        const mimeType = options.mimeType || 'audio/webm';
        const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
        const blob = new Blob(chunksRef.current, { type: mimeType });

        if (blob.size < 100) {
          toast.error(lang === 'pt' ? 'Audio muito curto' : 'Audio too short');
          return;
        }

        setTranscribing(true);
        toast.info(lang === 'pt' ? 'Transcrevendo...' : 'Transcribing...');

        try {
          const formData = new FormData();
          formData.append('audio', blob, `voice.${ext}`);
          formData.append('language', lang);

          const token = localStorage.getItem('agentzz_token');
          const headers = {};
          if (token) headers['Authorization'] = `Bearer ${token}`;

          const res = await axios.post(`${API}/ai/transcribe`, formData, {
            headers,
            timeout: 30000,
          });

          const text = res.data?.text?.trim();
          if (text && onResult) {
            onResult(text);
            toast.success(lang === 'pt' ? `"${text.substring(0, 50)}..."` : `"${text.substring(0, 50)}..."`);
          } else {
            toast.warning(lang === 'pt' ? 'Nenhum texto detectado' : 'No text detected');
          }
        } catch (err) {
          const msg = err.response?.data?.detail || err.message || 'Erro';
          toast.error(lang === 'pt' ? `Erro na transcricao: ${msg}` : `Transcription error: ${msg}`);
        }
        setTranscribing(false);
      };

      mediaRecorder.start(250);
      setRecording(true);
      toast.info(lang === 'pt' ? 'Gravando... clique novamente para parar' : 'Recording... click again to stop');
    } catch (err) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        toast.error(lang === 'pt' ? 'Permissao do microfone negada. Habilite nas configuracoes do navegador.' : 'Microphone permission denied. Enable in browser settings.');
      } else if (err.name === 'NotFoundError') {
        toast.error(lang === 'pt' ? 'Nenhum microfone encontrado' : 'No microphone found');
      } else {
        toast.error(lang === 'pt' ? `Erro ao acessar microfone: ${err.message}` : `Mic error: ${err.message}`);
      }
    }
  }, [lang, onResult]);

  const toggle = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    if (transcribing) return;
    if (recording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [recording, transcribing, startRecording, stopRecording]);

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={transcribing}
      data-testid="voice-input-btn"
      className={`rounded-full flex items-center justify-center transition-all cursor-pointer ${
        recording
          ? 'bg-red-500/20 border border-red-500/50 text-red-400 animate-pulse'
          : transcribing
            ? 'bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[#C9A84C]'
            : 'bg-[#111] border border-[#333] text-[#666] hover:text-[#C9A84C] hover:border-[#C9A84C]/30'
      } ${className}`}
      title={recording ? (lang === 'pt' ? 'Parar gravacao' : 'Stop recording') : (lang === 'pt' ? 'Comando de voz' : 'Voice command')}
    >
      {transcribing ? (
        <Loader2 size={size} className="animate-spin" />
      ) : recording ? (
        <MicOff size={size} />
      ) : (
        <Mic size={size} />
      )}
    </button>
  );
}
