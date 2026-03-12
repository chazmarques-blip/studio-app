import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Plus, Trash2, Clock } from 'lucide-react';

const types = [
  { id: 'abandoned_cart', icon: '🛒' },
  { id: 'inactive_lead', icon: '💤' },
  { id: 'follow_up', icon: '🔄' },
  { id: 'birthday', icon: '🎂' },
];

export default function CampaignBuilder() {
  const [name, setName] = useState('');
  const [selectedType, setSelectedType] = useState('follow_up');
  const [messages, setMessages] = useState([{ delay: '1h', text: 'Hi {{name}}, just checking in!' }]);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const addMessage = () => setMessages(prev => [...prev, { delay: '24h', text: '' }]);
  const removeMessage = (idx) => setMessages(prev => prev.filter((_, i) => i !== idx));

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold text-white">{t('campaigns.title')}</h1>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('campaigns.name')}</label>
          <input data-testid="campaign-name" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Abandoned Cart Recovery"
            className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
        </div>

        <div>
          <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('campaigns.type')}</label>
          <div className="grid grid-cols-2 gap-2">
            {types.map(tp => (
              <button key={tp.id} onClick={() => setSelectedType(tp.id)}
                className={`glass-card flex items-center gap-2 p-3 text-sm ${selectedType === tp.id ? 'border-[#C9A84C] text-[#C9A84C]' : 'text-[#A0A0A0]'}`}>
                <span className="text-lg">{tp.icon}</span> {t(`campaigns.${tp.id}`)}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="mb-3 block text-xs font-medium text-[#A0A0A0]">{t('campaigns.message_sequence')}</label>
          <div className="relative space-y-3">
            {messages.map((msg, i) => (
              <div key={i} className="relative">
                {i > 0 && (
                  <div className="mb-2 flex items-center gap-2 ml-4">
                    <div className="h-6 border-l border-dashed border-[#C9A84C]/50" />
                    <div className="flex items-center gap-1 rounded-full bg-[#C9A84C]/10 px-2 py-0.5">
                      <Clock size={10} className="text-[#C9A84C]" />
                      <span className="text-[10px] text-[#C9A84C]">After {msg.delay}</span>
                    </div>
                  </div>
                )}
                <div className="glass-card p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#A0A0A0]">Message {i + 1}</span>
                    {i > 0 && <button onClick={() => removeMessage(i)} className="text-red-400 hover:text-red-300"><Trash2 size={14} /></button>}
                  </div>
                  <textarea value={msg.text} onChange={e => { const newMsgs = [...messages]; newMsgs[i].text = e.target.value; setMessages(newMsgs); }}
                    rows={2} placeholder="Write your message... Use {{name}} for variables"
                    className="w-full rounded border border-[#2A2A2A] bg-[#111111] px-3 py-2 text-sm text-white placeholder-[#666666] outline-none resize-none focus:border-[#C9A84C]" />
                </div>
              </div>
            ))}
          </div>
          <button onClick={addMessage} className="mt-3 flex items-center gap-1.5 text-xs text-[#C9A84C] hover:text-[#D4B85A]"><Plus size={14} /> {t('campaigns.add_message')}</button>
        </div>
      </div>

      <div className="fixed bottom-20 left-0 right-0 border-t border-[#2A2A2A] bg-[#0A0A0A] px-4 py-3">
        <div className="mx-auto flex max-w-lg gap-3">
          <button className="btn-gold-outline flex-1 rounded-lg py-2.5 text-sm">{t('campaigns.save_draft')}</button>
          <button className="btn-gold flex-1 rounded-lg py-2.5 text-sm">{t('campaigns.activate')}</button>
        </div>
      </div>
    </div>
  );
}
