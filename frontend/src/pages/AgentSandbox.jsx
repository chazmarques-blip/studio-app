import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, ArrowLeft, Send, Trash2, Settings2, Activity, Globe, Clock, Zap } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AgentSandbox() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [debugInfo, setDebugInfo] = useState(null);
  const [agentConfig, setAgentConfig] = useState({ name: 'Carol', type: 'sales', prompt: '' });
  const [showConfig, setShowConfig] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
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
    } catch (err) {
      setMessages(prev => [...prev, { role: 'system', content: 'Error: Failed to get response. Try again.', time: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    if (sessionId) {
      try { await axios.delete(`${API}/sandbox/${sessionId}`); } catch {}
    }
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
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#C9A84C]/10"><Bot size={18} className="text-[#C9A84C]" /></div>
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
            <label className="mb-1 block text-xs text-[#666]">{t('agents.agent_name')}</label>
            <input data-testid="sandbox-agent-name" value={agentConfig.name} onChange={e => setAgentConfig(p => ({ ...p, name: e.target.value }))}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none focus:border-[#C9A84C]" />
          </div>
          <div>
            <label className="mb-1 block text-xs text-[#666]">{t('agents.agent_type')}</label>
            <select data-testid="sandbox-agent-type" value={agentConfig.type} onChange={e => setAgentConfig(p => ({ ...p, type: e.target.value }))}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white outline-none focus:border-[#C9A84C]">
              {['sales', 'support', 'scheduling', 'sac', 'onboarding'].map(tp => (
                <option key={tp} value={tp}>{t(`agents.type_${tp}`)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-[#666]">{t('agents.system_prompt')}</label>
            <textarea data-testid="sandbox-prompt" value={agentConfig.prompt} onChange={e => setAgentConfig(p => ({ ...p, prompt: e.target.value }))} rows={3}
              placeholder={t('agents.system_prompt_placeholder')}
              className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none resize-none focus:border-[#C9A84C] font-mono" />
          </div>
          <button onClick={() => { clearChat(); setShowConfig(false); }} className="btn-gold w-full rounded-lg py-2 text-xs">
            {t('agents.test_agent')}
          </button>
        </div>
      )}

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#C9A84C]/10"><Bot size={32} className="text-[#C9A84C]" /></div>
            <h3 className="mb-2 text-base font-semibold text-white">{t('agents.sandbox_title')}</h3>
            <p className="text-xs text-[#666] max-w-[280px]">{t('agents.send_test')}</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
              msg.role === 'user' ? 'bg-[#C9A84C]/15 border border-[#C9A84C]/20' :
              msg.role === 'agent' ? 'bg-[#1A1A1A] border border-[#2A2A2A]' :
              'bg-red-500/10 border border-red-500/20'
            }`}>
              {msg.role === 'agent' && (
                <p className="mb-1 text-[10px] font-medium text-[#C9A84C]"><Bot size={10} className="inline mr-1" />{agentConfig.name}</p>
              )}
              <p className="text-sm text-white whitespace-pre-wrap">{msg.content}</p>
              <p className="mt-1 text-right text-[9px] text-[#444]">{msg.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-[#1A1A1A] border border-[#2A2A2A] px-4 py-3">
              <div className="flex gap-1.5">
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#C9A84C]" style={{ animationDelay: '0ms' }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#C9A84C]" style={{ animationDelay: '150ms' }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-[#C9A84C]" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Debug Panel */}
      {debugInfo && (
        <div className="border-t border-[#2A2A2A] bg-[#111111] px-4 py-2.5">
          <div className="flex items-center gap-4 text-[10px]">
            <div className="flex items-center gap-1 text-[#666]"><Activity size={10} className="text-[#C9A84C]" /> {t('agents.debug_panel')}</div>
            <div className="flex items-center gap-1 text-[#A0A0A0]"><Clock size={10} />{debugInfo.response_time_ms}ms</div>
            <div className="flex items-center gap-1 text-[#A0A0A0]"><Zap size={10} />{debugInfo.tokens_estimate} tokens</div>
            <div className="flex items-center gap-1 text-[#A0A0A0]"><Globe size={10} />{debugInfo.language_detected?.toUpperCase()}</div>
            <div className="ml-auto text-[#444]">{debugInfo.model}</div>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-[#2A2A2A] px-4 py-3 pb-5 flex gap-2">
        <input data-testid="sandbox-input" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
          placeholder={t('agents.type_message')} disabled={loading}
          className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C] disabled:opacity-50" />
        <button data-testid="sandbox-send-btn" onClick={sendMessage} disabled={loading}
          className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C] disabled:opacity-50"><Send size={16} className="text-[#0A0A0A]" /></button>
      </div>
    </div>
  );
}
