import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Check, Wifi, WifiOff, RefreshCw, QrCode, MessageSquare, Phone } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CHANNELS = [
  { type: 'whatsapp', name: 'WhatsApp Business', color: '#25D366', icon: '📱', desc: { en: 'Connect via QR Code with Evolution API', pt: 'Conecte via QR Code com Evolution API', es: 'Conecta via QR Code con Evolution API' } },
  { type: 'instagram', name: 'Instagram DM', color: '#E4405F', icon: '📸', desc: { en: 'Connect your Instagram Business account', pt: 'Conecte sua conta Instagram Business', es: 'Conecta tu cuenta Instagram Business' } },
  { type: 'facebook', name: 'Messenger', color: '#1877F2', icon: '💬', desc: { en: 'Connect your Facebook Page', pt: 'Conecte sua Pagina do Facebook', es: 'Conecta tu Pagina de Facebook' } },
  { type: 'telegram', name: 'Telegram Bot', color: '#0088CC', icon: '✈️', desc: { en: 'Configure your bot token', pt: 'Configure o token do seu bot', es: 'Configura el token de tu bot' } },
  { type: 'sms', name: 'SMS (Twilio)', color: '#F22F46', icon: '📨', desc: { en: 'Send/receive SMS in the US and worldwide', pt: 'Envie/receba SMS nos EUA e no mundo', es: 'Envia/recibe SMS en EEUU y mundial' } },
];

export default function ChannelConnection() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [channels, setChannels] = useState([]);
  const [connecting, setConnecting] = useState(null);
  const [whatsappConfig, setWhatsappConfig] = useState({ instance_name: '', api_url: '', api_key: '' });
  const [smsConfig, setSmsConfig] = useState({ account_sid: '', auth_token: '', phone_number: '' });
  const [telegramConfig, setTelegramConfig] = useState({ bot_token: '' });
  const [showConfig, setShowConfig] = useState(null);

  useEffect(() => {
    axios.get(`${API}/channels`).then(r => setChannels(r.data.channels)).catch(() => {});
  }, []);

  const getChannelStatus = (type) => channels.find(c => c.type === type);

  const connectChannel = async (type) => {
    setConnecting(type);
    try {
      let config = {};
      if (type === 'whatsapp') config = whatsappConfig;
      else if (type === 'sms') config = smsConfig;
      else if (type === 'telegram') config = telegramConfig;

      const { data } = await axios.post(`${API}/channels`, { type, config });
      setChannels(prev => {
        const filtered = prev.filter(c => c.type !== type);
        return [...filtered, data];
      });
      toast.success(lang === 'pt' ? 'Canal conectando...' : 'Channel connecting...');
      setShowConfig(null);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error connecting');
    } finally {
      setConnecting(null);
    }
  };

  const disconnectChannel = async (channelId) => {
    await axios.delete(`${API}/channels/${channelId}`);
    setChannels(prev => prev.filter(c => c.id !== channelId));
    toast.success(lang === 'pt' ? 'Canal desconectado' : 'Channel disconnected');
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate('/settings')} className="text-[#A0A0A0] hover:text-white"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold text-white">{t('channels.title')}</h1>
      </div>

      <div className="space-y-3">
        {CHANNELS.map(ch => {
          const connected = getChannelStatus(ch.type);
          const isConnected = connected?.status === 'connected';
          const isConnecting = connected?.status === 'connecting';

          return (
            <div key={ch.type} data-testid={`channel-${ch.type}`} className="glass-card overflow-hidden">
              <div className="flex items-center gap-3 p-4">
                <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl" style={{ backgroundColor: `${ch.color}15` }}>
                  <span className="text-xl">{ch.icon}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-white">{ch.name}</h3>
                  <p className="text-[10px] text-[#666]">{ch.desc[lang] || ch.desc.en}</p>
                </div>
                <div className="flex items-center gap-2">
                  {isConnected ? (
                    <>
                      <div className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-1">
                        <Wifi size={10} className="text-green-400" />
                        <span className="text-[10px] text-green-400">{t('settings.connected')}</span>
                      </div>
                      <button onClick={() => disconnectChannel(connected.id)} className="text-xs text-[#666] hover:text-red-400">{t('channels.disconnect')}</button>
                    </>
                  ) : isConnecting ? (
                    <div className="flex items-center gap-1 rounded-full bg-[#C9A84C]/10 px-2.5 py-1">
                      <RefreshCw size={10} className="animate-spin text-[#C9A84C]" />
                      <span className="text-[10px] text-[#C9A84C]">{lang === 'pt' ? 'Conectando...' : 'Connecting...'}</span>
                    </div>
                  ) : (
                    <button data-testid={`connect-${ch.type}`} onClick={() => setShowConfig(showConfig === ch.type ? null : ch.type)}
                      className="btn-gold rounded-lg px-4 py-1.5 text-xs">{t('settings.connect')}</button>
                  )}
                </div>
              </div>

              {/* WhatsApp Config */}
              {showConfig === 'whatsapp' && ch.type === 'whatsapp' && (
                <div className="border-t border-[#1A1A1A] bg-[#111] px-4 py-4 space-y-3">
                  <p className="text-xs text-[#C9A84C] font-medium">Evolution API</p>
                  <input data-testid="wa-api-url" value={whatsappConfig.api_url} onChange={e => setWhatsappConfig(p => ({ ...p, api_url: e.target.value }))}
                    placeholder={lang === 'pt' ? 'URL da API (ex: https://evo.seuservidor.com)' : 'API URL (e.g., https://evo.yourserver.com)'}
                    className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                  <input data-testid="wa-api-key" value={whatsappConfig.api_key} onChange={e => setWhatsappConfig(p => ({ ...p, api_key: e.target.value }))}
                    placeholder={lang === 'pt' ? 'Chave da API' : 'API Key'} type="password"
                    className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                  <input data-testid="wa-instance" value={whatsappConfig.instance_name} onChange={e => setWhatsappConfig(p => ({ ...p, instance_name: e.target.value }))}
                    placeholder={lang === 'pt' ? 'Nome da instancia (ex: meu-negocio)' : 'Instance name (e.g., my-business)'}
                    className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                  <div className="glass-card flex items-center justify-center p-8">
                    <div className="text-center">
                      <QrCode size={48} className="mx-auto mb-2 text-[#2A2A2A]" />
                      <p className="text-xs text-[#666]">{t('agents.qr_hint')}</p>
                    </div>
                  </div>
                  <button onClick={() => connectChannel('whatsapp')} disabled={connecting === 'whatsapp'}
                    className="btn-gold w-full rounded-lg py-2.5 text-xs disabled:opacity-50">
                    {connecting === 'whatsapp' ? '...' : (lang === 'pt' ? 'Conectar WhatsApp' : 'Connect WhatsApp')}
                  </button>
                </div>
              )}

              {/* SMS Config */}
              {showConfig === 'sms' && ch.type === 'sms' && (
                <div className="border-t border-[#1A1A1A] bg-[#111] px-4 py-4 space-y-3">
                  <p className="text-xs text-[#F22F46] font-medium">Twilio</p>
                  <input value={smsConfig.account_sid} onChange={e => setSmsConfig(p => ({ ...p, account_sid: e.target.value }))}
                    placeholder="Account SID" className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                  <input value={smsConfig.auth_token} onChange={e => setSmsConfig(p => ({ ...p, auth_token: e.target.value }))}
                    placeholder="Auth Token" type="password" className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                  <input value={smsConfig.phone_number} onChange={e => setSmsConfig(p => ({ ...p, phone_number: e.target.value }))}
                    placeholder={lang === 'pt' ? 'Numero Twilio (ex: +15551234567)' : 'Twilio Number (e.g., +15551234567)'}
                    className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none" />
                  <button onClick={() => connectChannel('sms')} disabled={connecting === 'sms'}
                    className="btn-gold w-full rounded-lg py-2.5 text-xs disabled:opacity-50">
                    {connecting === 'sms' ? '...' : (lang === 'pt' ? 'Conectar SMS' : 'Connect SMS')}
                  </button>
                </div>
              )}

              {/* Telegram Config */}
              {showConfig === 'telegram' && ch.type === 'telegram' && (
                <div className="border-t border-[#1A1A1A] bg-[#111] px-4 py-4 space-y-3">
                  <p className="text-xs text-[#0088CC] font-medium">BotFather Token</p>
                  <input value={telegramConfig.bot_token} onChange={e => setTelegramConfig(p => ({ ...p, bot_token: e.target.value }))}
                    placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz" className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2 text-sm text-white placeholder-[#444] outline-none font-mono" />
                  <button onClick={() => connectChannel('telegram')} disabled={connecting === 'telegram'}
                    className="btn-gold w-full rounded-lg py-2.5 text-xs disabled:opacity-50">
                    {connecting === 'telegram' ? '...' : (lang === 'pt' ? 'Conectar Telegram' : 'Connect Telegram')}
                  </button>
                </div>
              )}

              {/* Instagram / Facebook - OAuth flow */}
              {(showConfig === 'instagram' || showConfig === 'facebook') && ch.type === showConfig && (
                <div className="border-t border-[#1A1A1A] bg-[#111] px-4 py-4 text-center">
                  <p className="text-xs text-[#666] mb-3">{lang === 'pt' ? 'Conecte via Facebook Business Manager' : 'Connect via Facebook Business Manager'}</p>
                  <button onClick={() => connectChannel(ch.type)} disabled={connecting === ch.type}
                    className="btn-gold rounded-lg px-6 py-2.5 text-xs disabled:opacity-50">
                    {connecting === ch.type ? '...' : (lang === 'pt' ? 'Conectar com Facebook' : 'Connect with Facebook')}
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
