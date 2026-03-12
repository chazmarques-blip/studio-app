import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, QrCode, ExternalLink } from 'lucide-react';

const channelsList = [
  { id: 'whatsapp', name: 'WhatsApp Business', color: '#25D366', connected: false, connectType: 'qr' },
  { id: 'instagram', name: 'Instagram DM', color: '#E4405F', connected: false, connectType: 'oauth' },
  { id: 'facebook', name: 'Messenger', color: '#1877F2', connected: false, connectType: 'oauth' },
  { id: 'telegram', name: 'Telegram Bot', color: '#0088CC', connected: false, connectType: 'token' },
];

export default function ChannelConnection() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate('/settings')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold text-white">{t('channels.title')}</h1>
      </div>

      <div className="space-y-4">
        {channelsList.map(ch => (
          <div key={ch.id} data-testid={`connect-${ch.id}`} className={`glass-card p-5 transition-all ${ch.connected ? 'border-[rgba(201,168,76,0.3)]' : ''}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl" style={{ backgroundColor: `${ch.color}15` }}>
                <div className="h-5 w-5 rounded-full" style={{ backgroundColor: ch.color }} />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-white">{ch.name}</h3>
                <p className="text-xs text-[#666666]">{t(`channels.${ch.id}_desc`)}</p>
              </div>
              <span className={`rounded-full px-2.5 py-1 text-[10px] font-medium ${ch.connected ? 'bg-[#4CAF50]/15 text-[#4CAF50]' : 'bg-[#1E1E1E] text-[#666666]'}`}>
                {ch.connected ? t('settings.connected') : t('settings.not_connected')}
              </span>
            </div>

            {ch.connectType === 'qr' && !ch.connected && (
              <div className="rounded-xl bg-[#111111] border border-[#1A1A1A] p-6 text-center">
                <div className="mx-auto mb-3 flex h-32 w-32 items-center justify-center rounded-xl bg-white/5 border border-dashed border-[#2A2A2A]">
                  <QrCode size={48} className="text-[#2A2A2A]" />
                </div>
                <p className="text-xs text-[#666666]">{t('agents.qr_hint')}</p>
                <button className="btn-gold mt-3 rounded-lg px-6 py-2 text-xs">{t('settings.connect')}</button>
              </div>
            )}
            {ch.connectType === 'oauth' && !ch.connected && (
              <button className="btn-gold flex w-full items-center justify-center gap-2 rounded-lg py-2.5 text-xs">
                <ExternalLink size={14} /> {t('settings.connect')} {ch.name}
              </button>
            )}
            {ch.connectType === 'token' && !ch.connected && (
              <div>
                <input placeholder="Enter your bot token: 123456:ABC-DEF1234..."
                  className="mb-2 w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-4 py-2.5 text-sm text-white placeholder-[#666666] outline-none focus:border-[#C9A84C]" />
                <button className="btn-gold w-full rounded-lg py-2.5 text-xs">{t('settings.connect')}</button>
              </div>
            )}
            {ch.connected && (
              <button className="btn-gold-outline w-full rounded-lg py-2 text-xs">{t('channels.disconnect')}</button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
