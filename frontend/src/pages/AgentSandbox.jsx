import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, ArrowLeft, Send, Trash2, Settings2, Activity, Globe, Clock, Zap, Image, Mic, MicOff, X, FileAudio, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AgentSandbox() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);
  const [agentConfig, setAgentConfig] = useState({ name: 'Carol', type: 'sales', prompt: '' });
  const [showConfig, setShowConfig] = useState(false);
  const [recording, setRecording] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async () => {
    if ((!input.trim() && !imagePreview) || loading) return;
    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg, time: new Date() }]);
    setLoading(true);

    try {
      const { data } = await axios.post(`${API}/sandbox/chat`, {
        content: userMsg,
        agent_name: agentConfig.name,
        agent_type: agentConfig.type,
        system_prompt: agentConfig.prompt,
        session_id: sessionId,
      });
      setSessionId(data.session_id);
      setDebugInfo(data.debug);
      setMessages(prev => [...prev, { role: 'agent', content: data.response, time: new Date() }]);
    } catch {
      setMessages(prev => [...prev, { role: 'system', content: 'Error: Failed to get response.', time: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleImageUpload = async (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImagePreview({ name: file.name, src: reader.result, file });
    reader.readAsDataURL(file);
  };

  const sendImage = async () => {
    if (!imagePreview || loading) return;
    setLoading(true);
    const preview = imagePreview;
    setImagePreview(null);

    setMessages(prev => [...prev, {
      role: 'user', content: `[${lang === 'pt' ? 'Imagem enviada' : 'Image sent'}: ${preview.name}]`,
      time: new Date(), type: 'image', imageSrc: preview.src,
    }]);

    try {
      const formData = new FormData();
      formData.append('image', preview.file);
      formData.append('language', lang);
      const { data } = await axios.post(`${API}/ai/analyze-image`, formData);
      setDebugInfo(data.debug);
      setMessages(prev => [...prev, { role: 'agent', content: data.analysis, time: new Date(), type: 'vision' }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: `Error: ${err.response?.data?.detail || 'Image analysis failed'}`, time: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const handleAudioFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setMessages(prev => [...prev, {
      role: 'user', content: `[${lang === 'pt' ? 'Audio enviado' : 'Audio sent'}: ${file.name}]`,
      time: new Date(), type: 'audio',
    }]);

    try {
      const formData = new FormData();
      formData.append('audio', file);
      formData.append('language', lang);
      const { data } = await axios.post(`${API}/ai/transcribe`, formData);
      setDebugInfo(data.debug);
      setMessages(prev => [...prev, {
        role: 'agent',
        content: `**${lang === 'pt' ? 'Transcricao' : 'Transcription'}:**\n${data.text}${data.duration ? `\n\n_${lang === 'pt' ? 'Duracao' : 'Duration'}: ${Math.round(data.duration)}s | ${lang === 'pt' ? 'Idioma' : 'Language'}: ${data.language}_` : ''}`,
        time: new Date(), type: 'transcription',
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: `Error: ${err.response?.data?.detail || 'Transcription failed'}`, time: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (recording) {
      mediaRecorderRef.current?.stop();
      setRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorder.onstop = () => {
        stream.getTracks().forEach(track => track.stop());
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const file = new File([blob], 'recording.webm', { type: 'audio/webm' });
        handleAudioFile(file);
      };

      mediaRecorder.start();
      setRecording(true);
      toast.info(lang === 'pt' ? 'Gravando... clique novamente para parar' : 'Recording... click again to stop');
    } catch {
      toast.error(lang === 'pt' ? 'Microfone nao disponivel' : 'Microphone not available');
    }
  };

  const clearChat = async () => {
    if (sessionId) { try { await axios.delete(`${API}/sandbox/${sessionId}`); } catch {} }
    setMessages([]);
    setSessionId(null);
    setDebugInfo(null);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#0A0A0A]">
      {/* Header */}
      <div className="border-b border-[#2A2A2A] px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/agents')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#8B5CF6]/10"><Bot size={18} className="text-[#8B5CF6]" /></div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-white">{t('agents.sandbox_title')}</p>
            <p className="text-[10px] text-[#666666]">{agentConfig.name} ({agentConfig.type})</p>
          </div>
          <button data-testid="sandbox-config-btn" onClick={() => setShowConfig(!showConfig)} className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]">
            <Settings2 size={14} className="text-[#A0A0A0]" />
          </button>
          <button data-testid="sandbox-clear-btn" onClick={clearChat} className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]">
            <Trash2 size={14} className="text-[#A0A0A0]" />
          </button>
        </div>
      </div>

      {/* Config Panel */}
      {showConfig && (
        <div className="border-b border-[#2A2A2A] bg-[#111111] px-4 py-4 space-y-3">
          <div>
            <label className="mb-1 block text-xs text-[#999]">{t('agents.agent_name')}</label>
            <input data-testid="sandbox-agent-name" value={agentConfig.name} onChange={e => setAgentConfig(p => ({ ...p, name: e.target.value }))}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none focus:border-[#8B5CF6]" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-[#999]">{t('agents.agent_type')}</label>
            <select data-testid="sandbox-agent-type" value={agentConfig.type} onChange={e => setAgentConfig(p => ({ ...p, type: e.target.value }))}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none focus:border-[#8B5CF6]">
              {['sales', 'support', 'scheduling', 'sac', 'onboarding'].map(tp => (
                <option key={tp} value={tp}>{t(`agents.type_${tp}`)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-[#999]">{t('agents.system_prompt')}</label>
            <textarea data-testid="sandbox-prompt" value={agentConfig.prompt} onChange={e => setAgentConfig(p => ({ ...p, prompt: e.target.value }))} rows={3}
              placeholder={t('agents.system_prompt_placeholder')}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#666] outline-none resize-none focus:border-[#8B5CF6] font-mono" />
          </div>
          <button onClick={() => { clearChat(); setShowConfig(false); }} className="btn-gold w-full rounded-lg py-2 text-xs">
            {t('agents.test_agent')}
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#8B5CF6]/10"><Bot size={32} className="text-[#8B5CF6]" /></div>
            <h3 className="mb-2 text-base font-semibold text-white">{t('agents.sandbox_title')}</h3>
            <p className="text-xs text-[#999] max-w-[280px]">{t('agents.send_test')}</p>
            <div className="mt-4 flex gap-2">
              <div className="flex items-center gap-1.5 rounded-full bg-[#1A1A1A] border border-[#2A2A2A] px-3 py-1.5">
                <Image size={12} className="text-[#8B5CF6]" />
                <span className="text-[10px] text-[#999]">{lang === 'pt' ? 'Envie imagens' : 'Send images'}</span>
              </div>
              <div className="flex items-center gap-1.5 rounded-full bg-[#1A1A1A] border border-[#2A2A2A] px-3 py-1.5">
                <Mic size={12} className="text-[#8B5CF6]" />
                <span className="text-[10px] text-[#999]">{lang === 'pt' ? 'Grave audio' : 'Record audio'}</span>
              </div>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
              msg.role === 'user' ? 'bg-[#8B5CF6]/15 border border-[#8B5CF6]/20' :
              msg.role === 'agent' ? 'bg-[#1A1A1A] border border-[#2A2A2A]' :
              'bg-red-500/10 border border-red-500/20'
            }`}>
              {msg.role === 'agent' && (
                <p className="mb-1 text-[10px] font-medium text-[#8B5CF6]">
                  {msg.type === 'vision' ? <><Eye size={10} className="inline mr-1" />Vision</> :
                   msg.type === 'transcription' ? <><FileAudio size={10} className="inline mr-1" />Whisper</> :
                   <><Bot size={10} className="inline mr-1" />{agentConfig.name}</>}
                </p>
              )}
              {msg.imageSrc && (
                <img src={msg.imageSrc} alt="Upload" className="mb-2 max-h-48 rounded-lg object-contain" />
              )}
              <p className="text-sm text-white whitespace-pre-wrap">{msg.content}</p>
              <p className="mt-1 text-right text-[9px] text-[#999]">{msg.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-[#1A1A1A] border border-[#2A2A2A] px-4 py-3">
              <div className="flex gap-1.5">
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#8B5CF6]" style={{ animationDelay: '0ms' }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#8B5CF6]" style={{ animationDelay: '150ms' }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#8B5CF6]" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Image Preview */}
      {imagePreview && (
        <div className="border-t border-[#2A2A2A] bg-[#111] px-4 py-3">
          <div className="flex items-center gap-3">
            <img src={imagePreview.src} alt="Preview" className="h-16 w-16 rounded-lg object-cover border border-[#2A2A2A]" />
            <div className="flex-1">
              <p className="text-xs text-white truncate">{imagePreview.name}</p>
              <p className="text-[10px] text-[#999]">{lang === 'pt' ? 'Clique enviar para analisar' : 'Click send to analyze'}</p>
            </div>
            <button onClick={() => setImagePreview(null)} className="text-[#999] hover:text-red-400"><X size={16} /></button>
            <button data-testid="sandbox-send-image-btn" onClick={sendImage} disabled={loading}
              className="flex h-9 items-center gap-1.5 rounded-lg bg-[#8B5CF6] px-4 text-xs font-semibold text-[#0A0A0A] disabled:opacity-50">
              <Eye size={14} /> {lang === 'pt' ? 'Analisar' : 'Analyze'}
            </button>
          </div>
        </div>
      )}

      {/* Debug Panel */}
      {debugInfo && (
        <div className="border-t border-[#2A2A2A] bg-[#111111] px-4 py-2.5">
          <div className="flex items-center gap-4 text-[10px]">
            <div className="flex items-center gap-1 text-[#999]"><Activity size={10} className="text-[#8B5CF6]" /> {t('agents.debug_panel')}</div>
            <div className="flex items-center gap-1 text-[#A0A0A0]"><Clock size={10} />{debugInfo.response_time_ms}ms</div>
            {debugInfo.tokens_estimate && <div className="flex items-center gap-1 text-[#A0A0A0]"><Zap size={10} />{debugInfo.tokens_estimate} tokens</div>}
            {debugInfo.language_detected && <div className="flex items-center gap-1 text-[#A0A0A0]"><Globe size={10} />{debugInfo.language_detected?.toUpperCase()}</div>}
            <div className="ml-auto text-[#999]">{debugInfo.model}</div>
          </div>
        </div>
      )}

      {/* Input Bar */}
      <div className="border-t border-[#2A2A2A] px-4 py-3 pb-5 flex gap-2">
        <input type="file" ref={fileInputRef} accept="image/*" className="hidden" onChange={e => { if (e.target.files[0]) handleImageUpload(e.target.files[0]); e.target.value = ''; }} />
        <input type="file" ref={audioInputRef} accept="audio/*,.webm,.ogg,.mp3,.wav,.m4a" className="hidden" onChange={e => { if (e.target.files[0]) handleAudioFile(e.target.files[0]); e.target.value = ''; }} />

        <button data-testid="sandbox-image-btn" onClick={() => fileInputRef.current?.click()} disabled={loading}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#8B5CF6]/50 disabled:opacity-50 transition" title={lang === 'pt' ? 'Enviar imagem' : 'Send image'}>
          <Image size={16} className="text-[#A0A0A0]" />
        </button>

        <button data-testid="sandbox-mic-btn" onClick={toggleRecording} disabled={loading && !recording}
          className={`flex h-10 w-10 items-center justify-center rounded-lg border transition ${
            recording ? 'border-red-500 bg-red-500/10 animate-pulse' : 'border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#8B5CF6]/50'
          } disabled:opacity-50`} title={lang === 'pt' ? 'Gravar audio' : 'Record audio'}>
          {recording ? <MicOff size={16} className="text-red-400" /> : <Mic size={16} className="text-[#A0A0A0]" />}
        </button>

        <button data-testid="sandbox-audio-file-btn" onClick={() => audioInputRef.current?.click()} disabled={loading}
          className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#8B5CF6]/50 disabled:opacity-50 transition" title={lang === 'pt' ? 'Enviar arquivo de audio' : 'Upload audio file'}>
          <FileAudio size={16} className="text-[#A0A0A0]" />
        </button>

        <input data-testid="sandbox-input" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder={t('agents.type_message')} disabled={loading}
          className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#8B5CF6] disabled:opacity-50" />
        <button data-testid="sandbox-send-btn" onClick={sendMessage} disabled={loading}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#8B5CF6] disabled:opacity-50"><Send size={16} className="text-[#0A0A0A]" /></button>
      </div>
    </div>
  );
}
