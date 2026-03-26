import { useState, useRef, useCallback } from 'react';
import axios from 'axios';
import { Mic, MicOff, Loader2 } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * VoiceInput — Universal voice command button.
 * Records audio, transcribes with Whisper, calls onResult with text.
 *
 * Props:
 *   onResult(text: string) — called with transcribed text
 *   lang — 'pt' | 'en' | 'es'
 *   className — optional extra classes
 *   size — icon size (default 12)
 */
export function VoiceInput({ onResult, lang = 'pt', className = '', size = 12 }) {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach(t => t.stop());
        streamRef.current = null;

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        if (blob.size < 100) return; // Too small, ignore

        setTranscribing(true);
        try {
          const formData = new FormData();
          formData.append('audio', blob, 'voice.webm');
          formData.append('language', lang);

          // Get auth token from localStorage
          const token = localStorage.getItem('agentzz_token');
          const headers = { 'Content-Type': 'multipart/form-data' };
          if (token) headers['Authorization'] = `Bearer ${token}`;

          const res = await axios.post(`${API}/ai/transcribe`, formData, {
            headers,
            timeout: 30000,
          });

          const text = res.data?.text?.trim();
          if (text && onResult) {
            onResult(text);
          }
        } catch (err) {
          console.error('Transcription error:', err);
        }
        setTranscribing(false);
      };

      mediaRecorder.start(250); // Collect in 250ms chunks
      setRecording(true);
    } catch (err) {
      console.error('Mic access error:', err);
    }
  }, [lang, onResult]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setRecording(false);
  }, []);

  const toggle = () => {
    if (recording) stopRecording();
    else startRecording();
  };

  return (
    <button
      onClick={toggle}
      disabled={transcribing}
      data-testid="voice-input-btn"
      className={`rounded-full flex items-center justify-center transition-all ${
        recording
          ? 'bg-red-500/20 border border-red-500/50 text-red-400 animate-pulse'
          : transcribing
            ? 'bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[#C9A84C]'
            : 'bg-[#111] border border-[#333] text-[#666] hover:text-[#C9A84C] hover:border-[#C9A84C]/30'
      } ${className}`}
      title={recording ? (lang === 'pt' ? 'Parar gravação' : 'Stop recording') : (lang === 'pt' ? 'Comando de voz' : 'Voice command')}
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
