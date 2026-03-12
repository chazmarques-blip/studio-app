import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Search, Send, ArrowLeft, Phone, UserCheck, Bot, Sparkles, Image, Mic, MicOff, FileAudio, X, Eye } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const channelColors = { whatsapp: '#25D366', instagram: '#E4405F', facebook: '#1877F2', telegram: '#0088CC', sms: '#F22F46' };

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
      toast.error(err.response?.data?.detail || 'Image analysis failed');
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
      toast.error(err.response?.data?.detail || 'Transcription failed');
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
    return (
      <div key={msg.id} className={`flex ${msg.sender === 'customer' ? 'justify-start' : 'justify-end'}`}>
        <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
          msg.sender === 'customer' ? 'bg-[#1A1A1A]' :
          msg.sender === 'agent' ? 'bg-[#1A1A1A] border-l-2 border-[#2196F3]' :
          'bg-[#1A1A1A] border-l-2 border-[#C9A84C]'
        }`}>
          {msg.sender === 'agent' && (
            <p className="text-[10px] text-[#2196F3] mb-0.5">
              {isVision ? <><Eye size={10} className="inline mr-1" />Vision</> :
               isTranscription ? <><FileAudio size={10} className="inline mr-1" />Whisper</> :
               <><Bot size={10} className="inline mr-1" />AI Agent</>}
            </p>
          )}
          {msg.sender === 'operator' && <p className="text-[10px] text-[#C9A84C] mb-0.5"><UserCheck size={10} className="inline mr-1" />You</p>}
          {msg.imageSrc && <img src={msg.imageSrc} alt="" className="mb-2 max-h-48 rounded-lg object-contain" />}
          <p className="text-sm text-white whitespace-pre-wrap">{msg.content}</p>
          <p className="mt-1 text-right text-[9px] text-[#444]">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
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
            <div className="flex h-9 w-9 items-center justify-center rounded-full" style={{ backgroundColor: `${channelColors[selectedConvo.channel_type] || '#666'}20` }}>
              <span className="text-sm font-bold" style={{ color: channelColors[selectedConvo.channel_type] }}>{(selectedConvo.contact_name || '?')[0].toUpperCase()}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="truncate text-sm font-semibold text-white">{selectedConvo.contact_name || selectedConvo.contact_phone}</p>
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: channelColors[selectedConvo.channel_type] }} />
                <span className="text-[10px] capitalize text-[#666666]">{selectedConvo.channel_type}</span>
                {selectedConvo.is_handoff && <span className="ml-1 rounded bg-[#C9A84C]/15 px-1.5 py-0.5 text-[9px] text-[#C9A84C]">Handoff</span>}
              </div>
            </div>
            <button className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]"><Phone size={14} className="text-[#A0A0A0]" /></button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map(renderMessage)}
          {(mediaLoading) && (
            <div className="flex justify-end">
              <div className="rounded-2xl bg-[#1A1A1A] border-l-2 border-[#2196F3] px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 animate-spin rounded-full border-2 border-[#2196F3] border-t-transparent" />
                  <span className="text-[10px] text-[#2196F3]">{lang === 'pt' ? 'Processando...' : 'Processing...'}</span>
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
                <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Enviar para analise Vision' : 'Send for Vision analysis'}</p>
              </div>
              <button onClick={() => setImagePreview(null)} className="text-[#666] hover:text-red-400"><X size={16} /></button>
              <button data-testid="chat-send-image-btn" onClick={sendImageAnalysis} disabled={mediaLoading}
                className="flex h-9 items-center gap-1.5 rounded-lg bg-[#C9A84C] px-3 text-xs font-semibold text-[#0A0A0A] disabled:opacity-50">
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
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#C9A84C] disabled:opacity-50 transition">
            {aiLoading ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" /> : <Sparkles size={16} className="text-[#C9A84C]" />}
          </button>

          <button data-testid="chat-image-btn" onClick={() => fileInputRef.current?.click()} disabled={mediaLoading}
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#C9A84C]/50 disabled:opacity-50 transition" title={lang === 'pt' ? 'Enviar imagem' : 'Send image'}>
            <Image size={16} className="text-[#A0A0A0]" />
          </button>

          <button data-testid="chat-mic-btn" onClick={toggleRecording} disabled={mediaLoading && !recording}
            className={`flex h-10 w-10 items-center justify-center rounded-lg border transition ${
              recording ? 'border-red-500 bg-red-500/10 animate-pulse' : 'border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#C9A84C]/50'
            } disabled:opacity-50`} title={lang === 'pt' ? 'Gravar audio' : 'Record audio'}>
            {recording ? <MicOff size={16} className="text-red-400" /> : <Mic size={16} className="text-[#A0A0A0]" />}
          </button>

          <input data-testid="chat-input" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder={t('handoff.send_as_operator')} className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
          <button data-testid="chat-send-btn" onClick={sendMessage} className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]"><Send size={16} className="text-[#0A0A0A]" /></button>
        </div>
      </div>
    );
  }

  // Conversation list view
  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('chat.inbox')}</h1>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]"><Search size={16} className="text-[#A0A0A0]" /></div>
      </div>

      {/* Channel filters */}
      <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
        {[{ key: 'all', label: t('chat.all') }, { key: 'whatsapp', label: 'WhatsApp' }, { key: 'instagram', label: 'Instagram' }, { key: 'facebook', label: 'Facebook' }, { key: 'telegram', label: 'Telegram' }, { key: 'sms', label: 'SMS' }].map((ch) => (
          <button key={ch.key} data-testid={`filter-${ch.key}`} onClick={() => setFilter(ch.key)}
            className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${filter === ch.key ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#A0A0A0] border border-[#2A2A2A] hover:border-[#3A3A3A]'}`}>{ch.label}</button>
        ))}
      </div>

      {/* Search */}
      {conversations.length > 0 && (
        <div className="relative mb-4">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#666666]" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder={t('common.search')}
            className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2 pl-9 pr-4 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
        </div>
      )}

      {/* Conversation list */}
      {filteredConvos.length > 0 ? (
        <div className="space-y-2">
          {filteredConvos.map((convo) => (
            <button key={convo.id} data-testid={`convo-${convo.id}`} onClick={() => openConversation(convo)}
              className="glass-card flex w-full items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
              <div className="relative flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-full" style={{ backgroundColor: `${channelColors[convo.channel_type] || '#666'}15` }}>
                <span className="text-sm font-bold" style={{ color: channelColors[convo.channel_type] }}>{(convo.contact_name || '?')[0].toUpperCase()}</span>
                <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-[#0A0A0A]" style={{ backgroundColor: channelColors[convo.channel_type] }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="truncate text-sm font-semibold text-white">{convo.contact_name || convo.contact_phone}</p>
                  <span className="ml-2 flex-shrink-0 text-[10px] text-[#666666]">{timeAgo(convo.last_message_at)}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="truncate text-xs text-[#666666]">{convo.channel_type}</span>
                  {convo.is_handoff && <span className="rounded bg-[#C9A84C]/15 px-1 py-0.5 text-[9px] text-[#C9A84C]">Handoff</span>}
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
