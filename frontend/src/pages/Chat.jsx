import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Search, Send, ArrowLeft, Phone, UserCheck, Bot, Sparkles, Image, Mic, MicOff, FileAudio, X, Eye, RefreshCw } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';
import { getErrorMsg } from '../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ChannelIcon = ({ type, size = 14 }) => {
  const s = { width: size, height: size };
  switch (type) {
    case 'whatsapp': return <svg {...s} viewBox="0 0 24 24" fill="#8B5CF6"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>;
    case 'instagram': return <svg {...s} viewBox="0 0 24 24" fill="#8B5CF6"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z"/></svg>;
    case 'telegram': return <svg {...s} viewBox="0 0 24 24" fill="#8B5CF6"><path d="M11.944 0A12 12 0 000 12a12 12 0 0012 12 12 12 0 0012-12A12 12 0 0012 0 12 12 0 0011.944 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 01.171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.479.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
    case 'facebook': return <svg {...s} viewBox="0 0 24 24" fill="#8B5CF6"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>;
    case 'sms': return <svg {...s} viewBox="0 0 24 24" fill="#8B5CF6"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/><path d="M7 9h2v2H7zm4 0h2v2h-2zm4 0h2v2h-2z"/></svg>;
    default: return <svg {...s} viewBox="0 0 24 24" fill="#8B5CF6"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/></svg>;
  }
};

export default function Chat() {
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [conversations, setConversations] = useState([]);
  const [selectedConvo, setSelectedConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [imagePreview, setImagePreview] = useState(null);
  const [routingAgent, setRoutingAgent] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => { fetchConversations(); }, [filter]);

  const fetchConversations = async () => {
    try {
      const params = filter !== 'all' ? { channel_type: filter } : {};
      const { data } = await axios.get(`${API}/conversations`, { params });
      setConversations(data.conversations);
    } catch (err) {
      console.error('Failed to fetch conversations', err);
    } finally {
      setLoading(false);
    }
  };

  const openConversation = async (convo) => {
    setSelectedConvo(convo);
    try {
      const { data } = await axios.get(`${API}/conversations/${convo.id}/messages`);
      setMessages(data.messages);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
    } catch (err) {
      console.error('Failed to fetch messages', err);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !selectedConvo) return;
    const content = input;
    setInput('');
    const tempMsg = { id: Date.now(), sender: 'operator', content, message_type: 'text', created_at: new Date().toISOString() };
    setMessages(prev => [...prev, tempMsg]);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    try {
      await axios.post(`${API}/conversations/${selectedConvo.id}/messages`, { content, message_type: 'text' });
      fetchConversations();
    } catch (err) {
      console.error('Failed to send', err);
    }
  };

  const triggerAiReply = async () => {
    if (!selectedConvo || aiLoading) return;
    setAiLoading(true);
    try {
      const { data } = await axios.post(`${API}/conversations/${selectedConvo.id}/ai-reply`);
      setMessages(prev => [...prev, { id: Date.now(), sender: 'agent', content: data.response, message_type: 'text', created_at: new Date().toISOString(), metadata: { model: 'claude-sonnet-4-5' } }]);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (err) {
      console.error('AI reply failed', err);
    } finally {
      setAiLoading(false);
    }
  };

  const routeAgent = async () => {
    if (!selectedConvo || routingAgent) return;
    setRoutingAgent(true);
    try {
      const { data } = await axios.post(`${API}/conversations/${selectedConvo.id}/route-agent`);
      setMessages(prev => [...prev, {
        id: Date.now(), sender: 'system',
        content: `${lang === 'pt' ? 'Agente roteado para' : 'Agent routed to'}: **${data.agent_name}** — ${data.reason}`,
        message_type: 'text', created_at: new Date().toISOString(), metadata: { type: 'routing' },
      }]);
      toast.success(`${lang === 'pt' ? 'Roteado para' : 'Routed to'} ${data.agent_name}`);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (err) {
      const detail = err.response?.data?.detail || 'Routing failed';
      toast.error(detail);
    } finally {
      setRoutingAgent(false);
    }
  };

  const handleImageUpload = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setImagePreview({ name: file.name, src: reader.result, file });
    reader.readAsDataURL(file);
  };

  const sendImageAnalysis = async () => {
    if (!imagePreview || mediaLoading) return;
    setMediaLoading(true);
    const preview = imagePreview;
    setImagePreview(null);

    setMessages(prev => [...prev, {
      id: Date.now(), sender: 'operator', content: `[${lang === 'pt' ? 'Imagem enviada para analise' : 'Image sent for analysis'}]`,
      message_type: 'image', created_at: new Date().toISOString(), imageSrc: preview.src,
    }]);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);

    try {
      const formData = new FormData();
      formData.append('image', preview.file);
      formData.append('language', lang);
      const { data } = await axios.post(`${API}/ai/analyze-image`, formData);
      setMessages(prev => [...prev, {
        id: Date.now() + 1, sender: 'agent', content: data.analysis,
        message_type: 'text', created_at: new Date().toISOString(), metadata: { model: 'claude-vision', type: 'vision' },
      }]);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Image analysis failed'));
    } finally {
      setMediaLoading(false);
    }
  };

  const handleAudioFile = async (file) => {
    if (!file || mediaLoading) return;
    setMediaLoading(true);

    setMessages(prev => [...prev, {
      id: Date.now(), sender: 'operator', content: `[${lang === 'pt' ? 'Audio enviado para transcricao' : 'Audio sent for transcription'}: ${file.name}]`,
      message_type: 'audio', created_at: new Date().toISOString(),
    }]);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);

    try {
      const formData = new FormData();
      formData.append('audio', file);
      formData.append('language', lang);
      const { data } = await axios.post(`${API}/ai/transcribe`, formData);
      setMessages(prev => [...prev, {
        id: Date.now() + 1, sender: 'agent',
        content: `**${lang === 'pt' ? 'Transcricao' : 'Transcription'}:**\n${data.text}${data.duration ? `\n\n_${lang === 'pt' ? 'Duracao' : 'Duration'}: ${Math.round(data.duration)}s_` : ''}`,
        message_type: 'text', created_at: new Date().toISOString(), metadata: { model: 'whisper', type: 'transcription' },
      }]);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    } catch (err) {
      toast.error(getErrorMsg(err, 'Transcription failed'));
    } finally {
      setMediaLoading(false);
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
        handleAudioFile(new File([blob], 'recording.webm', { type: 'audio/webm' }));
      };
      mediaRecorder.start();
      setRecording(true);
      toast.info(lang === 'pt' ? 'Gravando...' : 'Recording...');
    } catch {
      toast.error(lang === 'pt' ? 'Microfone nao disponivel' : 'Microphone not available');
    }
  };

  const timeAgo = (dateStr) => {
    if (!dateStr) return '';
    const diff = (Date.now() - new Date(dateStr).getTime()) / 1000;
    if (diff < 60) return `${Math.floor(diff)}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  };

  const filteredConvos = conversations.filter(c =>
    !search || c.contact_name?.toLowerCase().includes(search.toLowerCase()) || c.contact_phone?.includes(search)
  );

  const renderMessage = (msg) => {
    const isVision = msg.metadata?.type === 'vision';
    const isTranscription = msg.metadata?.type === 'transcription';
    const isRouting = msg.metadata?.type === 'routing' || msg.sender === 'system';
    if (isRouting) {
      return (
        <div key={msg.id} className="flex justify-center">
          <div className="rounded-full bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 px-4 py-1.5 flex items-center gap-2">
            <RefreshCw size={12} className="text-[#8B5CF6]" />
            <span className="text-[11px] text-[#8B5CF6]">{msg.content}</span>
          </div>
        </div>
      );
    }
    return (
      <div key={msg.id} className={`flex ${msg.sender === 'customer' ? 'justify-start' : 'justify-end'}`}>
        <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
          msg.sender === 'customer' ? 'bg-[#1A1A1A]' :
          msg.sender === 'agent' ? 'bg-[#1A1A1A] border-l-2 border-[#8B5CF6]/50' :
          'bg-[#1A1A1A] border-l-2 border-[#8B5CF6]'
        }`}>
          {msg.sender === 'agent' && (
            <p className="text-[10px] text-[#8B5CF6] mb-0.5">
              {isVision ? <><Eye size={10} className="inline mr-1" />Vision</> :
               isTranscription ? <><FileAudio size={10} className="inline mr-1" />Whisper</> :
               <><Bot size={10} className="inline mr-1" />AI Agent</>}
            </p>
          )}
          {msg.sender === 'operator' && <p className="text-[10px] text-[#8B5CF6] mb-0.5"><UserCheck size={10} className="inline mr-1" />You</p>}
          {msg.imageSrc && <img src={msg.imageSrc} alt="" className="mb-2 max-h-48 rounded-lg object-contain" />}
          <p className="text-sm text-white whitespace-pre-wrap">{msg.content}</p>
          <p className="mt-1 text-right text-[9px] text-[#999]">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
        </div>
      </div>
    );
  };

  // Conversation detail view
  if (selectedConvo) {
    return (
      <div className="flex min-h-screen flex-col bg-[#0A0A0A]">
        {/* Header */}
        <div className="border-b border-[#2A2A2A] px-4 py-3">
          <div className="flex items-center gap-3">
            <button data-testid="chat-back-btn" onClick={() => { setSelectedConvo(null); setImagePreview(null); }} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#1A1A1A] border border-[#2A2A2A]">
              <ChannelIcon type={selectedConvo.channel_type} size={16} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-semibold text-white">{selectedConvo.contact_name || selectedConvo.contact_phone}</p>
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full bg-[#8B5CF6]" />
                <span className="text-[10px] capitalize text-[#666666]">{selectedConvo.channel_type}</span>
                {selectedConvo.is_handoff && <span className="ml-1 rounded bg-[#8B5CF6]/15 px-1.5 py-0.5 text-[9px] text-[#8B5CF6]">Handoff</span>}
              </div>
            </div>
            <button data-testid="chat-route-btn" onClick={routeAgent} disabled={routingAgent} title={lang === 'pt' ? 'Rotear para melhor agente' : 'Route to best agent'}
              className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] hover:border-[#8B5CF6] disabled:opacity-50 transition">
              {routingAgent ? <div className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-[#8B5CF6] border-t-transparent" /> : <RefreshCw size={14} className="text-[#8B5CF6]" />}
            </button>
            <button className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]"><Phone size={14} className="text-[#A0A0A0]" /></button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map(renderMessage)}
          {(mediaLoading) && (
            <div className="flex justify-end">
              <div className="rounded-2xl bg-[#1A1A1A] border-l-2 border-[#8B5CF6]/50 px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#8B5CF6] border-t-transparent" />
                  <span className="text-[10px] text-[#8B5CF6]">{lang === 'pt' ? 'Processando...' : 'Processing...'}</span>
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
              <img src={imagePreview.src} alt="Preview" className="h-14 w-14 rounded-lg object-cover border border-[#2A2A2A]" />
              <div className="flex-1 min-w-0">
                <p className="text-xs text-white truncate">{imagePreview.name}</p>
                <p className="text-[10px] text-[#999]">{lang === 'pt' ? 'Enviar para analise Vision' : 'Send for Vision analysis'}</p>
              </div>
              <button onClick={() => setImagePreview(null)} className="text-[#999] hover:text-red-400"><X size={16} /></button>
              <button data-testid="chat-send-image-btn" onClick={sendImageAnalysis} disabled={mediaLoading}
                className="flex h-9 items-center gap-1.5 rounded-lg bg-[#8B5CF6] px-3 text-xs font-semibold text-[#0A0A0A] disabled:opacity-50">
                <Eye size={14} /> {lang === 'pt' ? 'Analisar' : 'Analyze'}
              </button>
            </div>
          </div>
        )}

        {/* Input */}
        <div className="border-t border-[#2A2A2A] px-4 py-3 flex gap-2">
          <input type="file" ref={fileInputRef} accept="image/*" className="hidden" onChange={e => { if (e.target.files[0]) handleImageUpload(e.target.files[0]); e.target.value = ''; }} />
          <input type="file" ref={audioInputRef} accept="audio/*,.webm,.ogg,.mp3,.wav,.m4a" className="hidden" onChange={e => { if (e.target.files[0]) handleAudioFile(e.target.files[0]); e.target.value = ''; }} />

          <button data-testid="chat-ai-reply-btn" onClick={triggerAiReply} disabled={aiLoading} title="AI Reply"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#8B5CF6] disabled:opacity-50 transition">
            {aiLoading ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#8B5CF6] border-t-transparent" /> : <Sparkles size={16} className="text-[#8B5CF6]" />}
          </button>

          <button data-testid="chat-image-btn" onClick={() => fileInputRef.current?.click()} disabled={mediaLoading}
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#8B5CF6]/50 disabled:opacity-50 transition" title={lang === 'pt' ? 'Enviar imagem' : 'Send image'}>
            <Image size={16} className="text-[#A0A0A0]" />
          </button>

          <button data-testid="chat-mic-btn" onClick={toggleRecording} disabled={mediaLoading && !recording}
            className={`flex h-10 w-10 items-center justify-center rounded-lg border transition ${
              recording ? 'border-red-500 bg-red-500/10 animate-pulse' : 'border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#8B5CF6]/50'
            } disabled:opacity-50`} title={lang === 'pt' ? 'Gravar audio' : 'Record audio'}>
            {recording ? <MicOff size={16} className="text-red-400" /> : <Mic size={16} className="text-[#A0A0A0]" />}
          </button>

          <input data-testid="chat-input" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder={t('handoff.send_as_operator')} className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#8B5CF6]" />
          <button data-testid="chat-send-btn" onClick={sendMessage} className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#8B5CF6]"><Send size={16} className="text-[#0A0A0A]" /></button>
        </div>
      </div>
    );
  }

  // Conversation list view
  return (
    <div className="min-h-screen px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('chat.inbox')}</h1>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]"><Search size={16} className="text-[#A0A0A0]" /></div>
      </div>

      {/* Channel filters */}
      <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
        {[{ key: 'all', label: t('chat.all') }, { key: 'whatsapp', label: 'WhatsApp' }, { key: 'instagram', label: 'Instagram' }, { key: 'facebook', label: 'Facebook' }, { key: 'telegram', label: 'Telegram' }, { key: 'sms', label: 'SMS' }].map((ch) => (
          <button key={ch.key} data-testid={`filter-${ch.key}`} onClick={() => setFilter(ch.key)}
            className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${filter === ch.key ? 'bg-[#8B5CF6] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#A0A0A0] border border-[#2A2A2A] hover:border-[#3A3A3A]'}`}>{ch.label}</button>
        ))}
      </div>

      {/* Search */}
      {conversations.length > 0 && (
        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder={t('common.search')}
            className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2 pl-9 pr-4 text-sm text-white placeholder-[#666666] outline-none focus:border-[#8B5CF6]" />
        </div>
      )}

      {/* Conversation list */}
      {filteredConvos.length > 0 ? (
        <div className="space-y-2">
          {filteredConvos.map((convo) => (
            <button key={convo.id} data-testid={`convo-${convo.id}`} onClick={() => openConversation(convo)}
              className="glass-card flex w-full items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
              <div className="relative flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full bg-[#1A1A1A] border border-[#2A2A2A]">
                <ChannelIcon type={convo.channel_type} size={18} />
                <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#0A0A0A] bg-[#8B5CF6]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="truncate text-sm font-semibold text-white">{convo.contact_name || convo.contact_phone}</p>
                  <span className="ml-2 flex-shrink-0 text-[10px] text-[#666666]">{timeAgo(convo.last_message_at)}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="truncate text-xs text-[#666666]">{convo.channel_type}</span>
                  {convo.is_handoff && <span className="rounded bg-[#8B5CF6]/15 px-1 py-0.5 text-[9px] text-[#8B5CF6]">Handoff</span>}
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : (
        <div data-testid="chat-empty-state" className="glass-card mt-12 p-8 text-center">
          <MessageSquare size={40} className="mx-auto mb-4 text-[#2A2A2A]" />
          <h3 className="mb-2 text-base font-semibold text-white">{t('chat.no_conversations')}</h3>
          <p className="text-sm text-[#666666]">{t('chat.no_conversations_desc')}</p>
        </div>
      )}
    </div>
  );
}
