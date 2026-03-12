import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Bot, Send, Clock, Cpu, Globe, Zap } from 'lucide-react';

const sampleConvo = [
  { role: 'user', text: 'Hi, I want to buy a dress' },
  { role: 'agent', text: 'Hello! Welcome to our store. We have beautiful summer dresses. What style are you looking for?' },
  { role: 'user', text: 'Something casual for the weekend' },
  { role: 'agent', text: 'Great choice! I recommend our Linen Breeze collection. Sizes S-XL available. Would you like to see some options?' },
];

export default function AgentSandbox() {
  const [messages, setMessages] = useState(sampleConvo);
  const [input, setInput] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  const sendMessage = () => {
    if (!input.trim()) return;
    setMessages(prev => [...prev, { role: 'user', text: input }, { role: 'agent', text: 'This is a simulated response. Connect AI to enable real responses.' }]);
    setInput('');
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#0A0A0A]">
      <div className="border-b border-[#2A2A2A] px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/agents')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#C9A84C]/10"><Bot size={16} className="text-[#C9A84C]" /></div>
          <div><p className="text-sm font-semibold text-white">{t('agents.sandbox_title')}</p><p className="text-[10px] text-[#666666]">Carol - Sales Agent</p></div>
        </div>
      </div>

      <div className="flex flex-1 flex-col lg:flex-row">
        {/* Chat area */}
        <div className="flex flex-1 flex-col">
          <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${msg.role === 'user' ? 'bg-[#222222]' : 'bg-[#1A1A1A] border-l-2 border-[#C9A84C]'}`}>
                  {msg.role === 'agent' && <p className="text-[10px] text-[#C9A84C] mb-1">Agent Carol</p>}
                  <p className="text-sm text-white">{msg.text}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="border-t border-[#2A2A2A] px-4 py-3 flex gap-2">
            <input data-testid="sandbox-input" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
              placeholder={t('agents.type_message')} className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
            <button onClick={sendMessage} className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]"><Send size={16} className="text-[#0A0A0A]" /></button>
          </div>
        </div>

        {/* Debug panel */}
        <div className="w-full lg:w-72 border-t lg:border-t-0 lg:border-l border-[#2A2A2A] bg-[#111111] p-4">
          <h3 className="mb-4 text-xs font-semibold text-[#A0A0A0]">{t('agents.debug_panel')}</h3>
          <div className="space-y-3">
            <div className="glass-card p-3 flex items-center gap-3">
              <Clock size={14} className="text-[#C9A84C]" />
              <div><p className="text-[10px] text-[#666666]">{t('agents.response_time')}</p><p className="text-sm font-semibold text-white">1.2s</p></div>
            </div>
            <div className="glass-card p-3 flex items-center gap-3">
              <Cpu size={14} className="text-[#2196F3]" />
              <div><p className="text-[10px] text-[#666666]">{t('agents.tokens_used')}</p><p className="text-sm font-semibold text-white">142</p></div>
            </div>
            <div className="glass-card p-3 flex items-center gap-3">
              <Globe size={14} className="text-[#4CAF50]" />
              <div><p className="text-[10px] text-[#666666]">{t('agents.language_detected')}</p><p className="text-sm font-semibold text-white">EN</p></div>
            </div>
            <div className="glass-card p-3 flex items-center gap-3">
              <Zap size={14} className="text-[#FF9800]" />
              <div><p className="text-[10px] text-[#666666]">Model</p><p className="text-sm font-semibold text-white">Claude Sonnet</p></div>
            </div>
          </div>
          <div className="mt-4 space-y-2">
            <button className="btn-gold w-full rounded-lg py-2 text-xs">{t('agents.publish')}</button>
            <button onClick={() => navigate('/agents/builder')} className="btn-gold-outline w-full rounded-lg py-2 text-xs">{t('agents.edit')}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
