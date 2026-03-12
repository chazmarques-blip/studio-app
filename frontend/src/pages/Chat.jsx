import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Search, Send, ArrowLeft, Phone, UserCheck, Bot, Sparkles } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const channelColors = { whatsapp: '#25D366', instagram: '#E4405F', facebook: '#1877F2', telegram: '#0088CC' };

export default function Chat() {
  const { t } = useTranslation();
  const [conversations, setConversations] = useState([]);
  const [selectedConvo, setSelectedConvo] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [aiLoading, setAiLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchConversations();
  }, [filter]);

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
    // Optimistic update
    const tempMsg = { id: Date.now(), sender: 'operator', content, message_type: 'text', created_at: new Date().toISOString() };
    setMessages(prev => [...prev, tempMsg]);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    try {
      await axios.post(`${API}/conversations/${selectedConvo.id}/messages`, { content, message_type: 'text' });
      fetchConversations(); // refresh list
    } catch (err) {
      console.error('Failed to send', err);
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

  // Mobile: show list or detail
  if (selectedConvo) {
    return (
      <div className="flex min-h-screen flex-col bg-[#0A0A0A]">
        {/* Header */}
        <div className="border-b border-[#2A2A2A] px-4 py-3">
          <div className="flex items-center gap-3">
            <button data-testid="chat-back-btn" onClick={() => setSelectedConvo(null)} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
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
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.sender === 'customer' ? 'justify-start' : 'justify-end'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                msg.sender === 'customer' ? 'bg-[#1A1A1A]' :
                msg.sender === 'agent' ? 'bg-[#1A1A1A] border-l-2 border-[#2196F3]' :
                'bg-[#1A1A1A] border-l-2 border-[#C9A84C]'
              }`}>
                {msg.sender === 'agent' && <p className="text-[10px] text-[#2196F3] mb-0.5"><Bot size={10} className="inline mr-1" />AI Agent</p>}
                {msg.sender === 'operator' && <p className="text-[10px] text-[#C9A84C] mb-0.5"><UserCheck size={10} className="inline mr-1" />You</p>}
                <p className="text-sm text-white whitespace-pre-wrap">{msg.content}</p>
                <p className="mt-1 text-right text-[9px] text-[#444]">{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-[#2A2A2A] px-4 py-3 flex gap-2">
          <button data-testid="chat-ai-reply-btn" onClick={triggerAiReply} disabled={aiLoading} title="AI Reply"
            className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] hover:border-[#C9A84C] disabled:opacity-50 transition">
            {aiLoading ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-[#C9A84C] border-t-transparent" /> : <Sparkles size={16} className="text-[#C9A84C]" />}
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
        {[{ key: 'all', label: t('chat.all') }, { key: 'whatsapp', label: 'WhatsApp' }, { key: 'instagram', label: 'Instagram' }, { key: 'facebook', label: 'Facebook' }, { key: 'telegram', label: 'Telegram' }].map((ch) => (
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
