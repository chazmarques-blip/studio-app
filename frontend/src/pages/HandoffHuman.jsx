import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, UserCheck, Bot, ArrowRightLeft, Send } from 'lucide-react';
import { useState } from 'react';

const chatHistory = [
  { sender: 'customer', text: 'I have a problem with my order #12345', time: '14:22' },
  { sender: 'agent', text: 'I understand your concern. Let me check that order for you.', time: '14:22' },
  { sender: 'customer', text: 'I want to speak with a real person', time: '14:23' },
  { sender: 'system', text: 'Agent Carol escalated this conversation', time: '14:23' },
  { sender: 'human', text: 'Hi, this is Carlos from our support team. How can I help you?', time: '14:25' },
];

export default function HandoffHuman() {
  const [message, setMessage] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen flex-col bg-[#0A0A0A]">
      <div className="border-b border-[#2A2A2A] px-4 py-3">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/chat')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-white">Maria Silva</p>
              <div className="h-2 w-2 rounded-full bg-[#25D366]" />
            </div>
            <p className="text-xs text-[#666666]">WhatsApp - PT</p>
          </div>
          <div className="rounded-full bg-[#4CAF50]/15 px-2 py-1 text-[10px] font-medium text-[#4CAF50]">Live</div>
        </div>
      </div>

      <div className="rounded-lg bg-[#C9A84C]/10 border border-[#C9A84C]/30 mx-4 mt-3 px-4 py-2.5 flex items-center gap-2">
        <UserCheck size={16} className="text-[#C9A84C]" />
        <span className="text-xs text-[#C9A84C]">{t('handoff.handling')}</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {chatHistory.map((msg, i) => {
          if (msg.sender === 'system') {
            return <div key={i} className="text-center"><span className="rounded-full bg-[#C9A84C]/10 px-3 py-1 text-[10px] text-[#C9A84C]">{msg.text}</span></div>;
          }
          const isOutgoing = msg.sender === 'agent' || msg.sender === 'human';
          return (
            <div key={i} className={`flex ${isOutgoing ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 ${
                msg.sender === 'human' ? 'bg-[#1A1A1A] border-l-2 border-[#C9A84C]' :
                isOutgoing ? 'bg-[#1A1A1A] border-l-2 border-[#2196F3]' : 'bg-[#222222]'
              }`}>
                {msg.sender === 'human' && <p className="text-[10px] text-[#C9A84C] mb-1">You (Operator)</p>}
                {msg.sender === 'agent' && <p className="text-[10px] text-[#2196F3] mb-1">Agent Carol</p>}
                <p className="text-sm text-white">{msg.text}</p>
                <p className="mt-1 text-right text-[10px] text-[#666666]">{msg.time}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="border-t border-[#2A2A2A] px-4 py-3">
        <div className="mb-2 flex gap-2">
          <button className="rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] px-3 py-1.5 text-[10px] text-[#A0A0A0] hover:border-[#C9A84C]">{t('handoff.return_bot')}</button>
          <button className="rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] px-3 py-1.5 text-[10px] text-[#A0A0A0] hover:border-[#C9A84C]">{t('handoff.create_lead')}</button>
          <button className="rounded-lg bg-[#1A1A1A] border border-[#2A2A2A] px-3 py-1.5 text-[10px] text-[#A0A0A0] hover:border-[#C9A84C]">{t('handoff.transfer')}</button>
        </div>
        <div className="flex gap-2">
          <input value={message} onChange={e => setMessage(e.target.value)} placeholder={t('handoff.send_as_operator')}
            className="flex-1 rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
          <button className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#C9A84C]"><Send size={16} className="text-[#0A0A0A]" /></button>
        </div>
      </div>
    </div>
  );
}
