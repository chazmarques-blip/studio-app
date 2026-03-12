import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Bot, ArrowLeft, ArrowRight, Check } from 'lucide-react';

const agentTypes = [
  { value: 'sales', label: 'Sales', color: '#C9A84C' },
  { value: 'support', label: 'Support', color: '#2196F3' },
  { value: 'scheduling', label: 'Scheduling', color: '#4CAF50' },
  { value: 'sac', label: 'SAC', color: '#FF9800' },
  { value: 'onboarding', label: 'Onboarding', color: '#9C27B0' },
  { value: 'custom', label: 'Custom', color: '#666666' },
];

const channels = [
  { id: 'whatsapp', name: 'WhatsApp', color: '#25D366' },
  { id: 'instagram', name: 'Instagram', color: '#E4405F' },
  { id: 'facebook', name: 'Facebook', color: '#1877F2' },
  { id: 'telegram', name: 'Telegram', color: '#0088CC' },
];

const steps = ['Identity', 'Personality', 'Knowledge', 'Deploy'];

export default function AgentBuilder() {
  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [type, setType] = useState('sales');
  const [description, setDescription] = useState('');
  const [selectedChannels, setSelectedChannels] = useState([]);
  const [tone, setTone] = useState(0.6);
  const [verbosity, setVerbosity] = useState(0.4);
  const [systemPrompt, setSystemPrompt] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();

  const toggleChannel = (id) => setSelectedChannels(prev => prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]);

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate('/agents')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold text-white">{t('agents.builder_title')}</h1>
      </div>
      {/* Step indicator */}
      <div className="mb-8 flex items-center justify-center gap-1">
        {steps.map((s, i) => (
          <div key={s} className="flex items-center">
            <div className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold ${i <= step ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#666666]'}`}>{i < step ? <Check size={14} /> : i + 1}</div>
            <span className={`ml-1.5 mr-3 text-xs ${i <= step ? 'text-[#C9A84C]' : 'text-[#666666]'}`}>{s}</span>
            {i < steps.length - 1 && <div className={`h-px w-8 ${i < step ? 'bg-[#C9A84C]' : 'bg-[#2A2A2A]'}`} />}
          </div>
        ))}
      </div>

      {step === 0 && (
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('agents.agent_name')}</label>
            <input data-testid="builder-name" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Carol" className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('agents.agent_type')}</label>
            <div className="grid grid-cols-3 gap-2">
              {agentTypes.map(at => (
                <button key={at.value} onClick={() => setType(at.value)} className={`glass-card p-3 text-center text-xs font-medium transition ${type === at.value ? 'border-[#C9A84C] text-[#C9A84C]' : 'text-[#A0A0A0]'}`}>{at.label}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">{t('agents.description')}</label>
            <textarea data-testid="builder-desc" value={description} onChange={e => setDescription(e.target.value)} rows={3} placeholder="Describe what this agent does..." className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none resize-none focus:border-[#C9A84C]" />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">Channels</label>
            <div className="grid grid-cols-2 gap-2">
              {channels.map(ch => (
                <button key={ch.id} onClick={() => toggleChannel(ch.id)} className={`glass-card flex items-center gap-2 p-3 text-sm ${selectedChannels.includes(ch.id) ? 'border-[#C9A84C]' : ''}`}>
                  <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ch.color }} />
                  <span className="text-[#A0A0A0]">{ch.name}</span>
                  {selectedChannels.includes(ch.id) && <Check size={14} className="ml-auto text-[#C9A84C]" />}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
      {step === 1 && (
        <div className="space-y-6">
          <div>
            <div className="mb-2 flex items-center justify-between"><label className="text-xs font-medium text-[#A0A0A0]">Tone (Formal → Casual)</label><span className="text-xs text-[#C9A84C]">{Math.round(tone * 100)}%</span></div>
            <input type="range" min="0" max="1" step="0.1" value={tone} onChange={e => setTone(parseFloat(e.target.value))} className="w-full accent-[#C9A84C]" />
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between"><label className="text-xs font-medium text-[#A0A0A0]">Verbosity (Concise → Detailed)</label><span className="text-xs text-[#C9A84C]">{Math.round(verbosity * 100)}%</span></div>
            <input type="range" min="0" max="1" step="0.1" value={verbosity} onChange={e => setVerbosity(parseFloat(e.target.value))} className="w-full accent-[#C9A84C]" />
          </div>
          <div className="glass-card p-4">
            <p className="text-xs text-[#666666] mb-2">Preview</p>
            <p className="text-sm text-[#A0A0A0]">{tone > 0.5 ? 'Hey there! How can I help you today? 😊' : 'Good day. How may I assist you?'}</p>
          </div>
        </div>
      )}
      {step === 2 && (
        <div>
          <label className="mb-1.5 block text-xs font-medium text-[#A0A0A0]">System Prompt</label>
          <textarea data-testid="builder-prompt" value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)} rows={10}
            placeholder="You are a helpful assistant that..." className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-3 text-sm text-white placeholder-[#666666] outline-none resize-none focus:border-[#C9A84C] font-mono" />
        </div>
      )}
      {step === 3 && (
        <div className="glass-card p-6 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-[#C9A84C]/10"><Bot size={32} className="text-[#C9A84C]" /></div>
          <h3 className="mb-1 text-lg font-bold text-white">{name || 'Your Agent'}</h3>
          <p className="mb-2 text-xs capitalize text-[#A0A0A0]">{type}</p>
          <p className="mb-4 text-sm text-[#666666]">{description || 'No description'}</p>
          <div className="flex flex-wrap justify-center gap-2 mb-4">
            {selectedChannels.map(ch => {
              const c = channels.find(x => x.id === ch);
              return <span key={ch} className="rounded-full bg-[#1A1A1A] px-3 py-1 text-xs text-[#A0A0A0]">{c?.name}</span>;
            })}
          </div>
          <button className="btn-gold w-full rounded-lg py-2.5 text-sm">{t('agents.publish')}</button>
          <button onClick={() => navigate('/agents/sandbox')} className="btn-gold-outline mt-2 w-full rounded-lg py-2.5 text-sm">{t('agents.test_agent')}</button>
        </div>
      )}

      <div className="fixed bottom-20 left-0 right-0 border-t border-[#2A2A2A] bg-[#0A0A0A] px-4 py-3">
        <div className="mx-auto flex max-w-lg gap-3">
          {step > 0 && <button onClick={() => setStep(s => s - 1)} className="btn-gold-outline flex-1 rounded-lg py-2.5 text-sm">{t('agents.previous')}</button>}
          {step < 3 && <button onClick={() => setStep(s => s + 1)} className="btn-gold flex-1 rounded-lg py-2.5 text-sm flex items-center justify-center gap-2">{t('agents.next_step')} <ArrowRight size={16} /></button>}
        </div>
      </div>
    </div>
  );
}
