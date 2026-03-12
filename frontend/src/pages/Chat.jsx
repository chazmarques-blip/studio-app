import { useTranslation } from 'react-i18next';
import { MessageSquare, Search } from 'lucide-react';

export default function Chat() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">{t('chat.inbox')}</h1>
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1A1A1A] border border-[#2A2A2A]"><Search size={16} className="text-[#A0A0A0]" /></div>
      </div>
      <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
        {[t('chat.all'), 'WhatsApp', 'Instagram', 'Facebook', 'Telegram'].map((ch, i) => (
          <button key={ch} data-testid={`filter-${ch.toLowerCase()}`}
            className={`whitespace-nowrap rounded-full px-4 py-1.5 text-xs font-medium transition ${i === 0 ? 'bg-[#C9A84C] text-[#0A0A0A]' : 'bg-[#1A1A1A] text-[#A0A0A0] border border-[#2A2A2A] hover:border-[#3A3A3A]'}`}>{ch}</button>
        ))}
      </div>
      <div data-testid="chat-empty-state" className="glass-card mt-12 p-8 text-center">
        <MessageSquare size={40} className="mx-auto mb-4 text-[#2A2A2A]" />
        <h3 className="mb-2 text-base font-semibold text-white">{t('chat.no_conversations')}</h3>
        <p className="text-sm text-[#666666]">{t('chat.no_conversations_desc')}</p>
      </div>
    </div>
  );
}
