import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Check, Wifi, WifiOff, RefreshCw, QrCode, MessageSquare, Phone, Loader2, AlertCircle, CheckCircle2, Trash2, Link2 } from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CHANNELS = [
  { type: 'whatsapp', name: 'WhatsApp Business', color: '#25D366', icon: Phone, desc: { en: 'Connect via QR Code with Evolution API', pt: 'Conecte via QR Code com Evolution API', es: 'Conecta via QR Code con Evolution API' } },
  { type: 'instagram', name: 'Instagram DM', color: '#E4405F', icon: MessageSquare, desc: { en: 'Connect your Instagram Business account', pt: 'Conecte sua conta Instagram Business', es: 'Conecta tu cuenta Instagram Business' } },
  { type: 'facebook', name: 'Messenger', color: '#1877F2', icon: MessageSquare, desc: { en: 'Connect your Facebook Page', pt: 'Conecte sua Pagina do Facebook', es: 'Conecta tu Pagina de Facebook' } },
  { type: 'telegram', name: 'Telegram Bot', color: '#0088CC', icon: MessageSquare, desc: { en: 'Configure your bot token', pt: 'Configure o token do seu bot', es: 'Configura el token de tu bot' } },
  { type: 'sms', name: 'SMS (Twilio)', color: '#F22F46', icon: Phone, desc: { en: 'Send/receive SMS in the US and worldwide', pt: 'Envie/receba SMS nos EUA e no mundo', es: 'Envia/recibe SMS en EEUU y mundial' } },
];

function WhatsAppSetup({ channel, lang, onConnect, onDisconnect }) {
  const [step, setStep] = useState('config'); // config | connecting | qr | connected
  const [config, setConfig] = useState({ api_url: '', api_key: '', instance_name: '' });
  const [qrCode, setQrCode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const pollRef = useRef(null);

  useEffect(() => {
    if (channel?.status === 'connected') {
      setStep('connected');
      setConfig(channel.config || {});
    } else if (channel?.status === 'waiting_qr') {
      setConfig(channel.config || {});
      setStep('qr');
      startPolling(channel.config);
    } else if (channel?.config?.api_url) {
      setConfig(channel.config);
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [channel]);

  const startPolling = useCallback((cfg) => {
    if (pollRef.current) clearInterval(pollRef.current);
    const instance = cfg?.instance_name;
    if (!instance) return;

    // Fetch QR immediately
    fetchQR(instance);

    pollRef.current = setInterval(async () => {
      try {
        const { data } = await axios.get(`${API}/whatsapp/status/${instance}`);
        if (data.connected) {
          clearInterval(pollRef.current);
          pollRef.current = null;
          setStep('connected');
          setQrCode(null);
          onConnect();
          toast.success(lang === 'pt' ? 'WhatsApp conectado!' : lang === 'es' ? 'WhatsApp conectado!' : 'WhatsApp connected!');
        } else {
          // Refresh QR
          fetchQR(instance);
        }
      } catch {}
    }, 4000);
  }, [lang, onConnect]);

  const fetchQR = async (instance) => {
    try {
      const { data } = await axios.get(`${API}/whatsapp/qr/${instance}`);
      if (data.qr_code) {
        setQrCode(data.qr_code);
      }
    } catch {}
  };

  const handleCreateInstance = async () => {
    if (!config.api_url || !config.api_key || !config.instance_name) {
      setError(lang === 'pt' ? 'Preencha todos os campos' : 'Fill in all fields');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const { data } = await axios.post(`${API}/whatsapp/create-instance`, config);
      if (data.qr_code) {
        setQrCode(data.qr_code);
      }
      setStep('qr');
      startPolling(config);
      toast.success(lang === 'pt' ? 'Instancia criada! Escaneie o QR Code' : 'Instance created! Scan the QR Code');
    } catch (err) {
      const detail = err.response?.data?.detail || 'Error creating instance';
      setError(detail);
      toast.error(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
    try {
      await axios.delete(`${API}/whatsapp/instance/${config.instance_name}`);
      toast.success(lang === 'pt' ? 'WhatsApp desconectado' : 'WhatsApp disconnected');
    } catch {}
    setStep('config');
    setQrCode(null);
    setConfig({ api_url: '', api_key: '', instance_name: '' });
    onDisconnect();
  };

  if (step === 'connected') {
    return (
      <div className="border-t border-[#1A1A1A] bg-[#0D0D0D] px-4 py-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#25D366]/10">
            <CheckCircle2 size={20} className="text-[#25D366]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{lang === 'pt' ? 'WhatsApp Conectado' : 'WhatsApp Connected'}</p>
            <p className="text-[10px] text-[#666]">{config.instance_name} @ {config.api_url?.replace('https://', '')?.replace('http://', '')}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-[#25D366]/5 border border-[#25D366]/15 p-3 mb-3">
          <Wifi size={14} className="text-[#25D366]" />
          <p className="text-xs text-[#25D366]">{lang === 'pt' ? 'Recebendo e enviando mensagens automaticamente' : 'Receiving and sending messages automatically'}</p>
        </div>
        <button data-testid="wa-disconnect-btn" onClick={handleDisconnect}
          className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2 text-xs text-red-400 hover:bg-red-500/10 hover:border-red-500/20 transition">
          <Trash2 size={12} className="inline mr-1.5" />
          {lang === 'pt' ? 'Desconectar WhatsApp' : 'Disconnect WhatsApp'}
        </button>
      </div>
    );
  }

  if (step === 'qr') {
    return (
      <div className="border-t border-[#1A1A1A] bg-[#0D0D0D] px-4 py-5">
        <div className="text-center mb-4">
          <p className="text-sm font-semibold text-white mb-1">{lang === 'pt' ? 'Escaneie o QR Code' : 'Scan the QR Code'}</p>
          <p className="text-[10px] text-[#666]">{lang === 'pt' ? 'Abra o WhatsApp > Aparelhos Conectados > Conectar Aparelho' : 'Open WhatsApp > Linked Devices > Link a Device'}</p>
        </div>
        <div className="flex justify-center mb-4">
          {qrCode ? (
            <div className="rounded-xl bg-white p-3">
              <img
                data-testid="wa-qr-image"
                src={qrCode.startsWith('data:') ? qrCode : `data:image/png;base64,${qrCode}`}
                alt="WhatsApp QR Code"
                className="h-48 w-48 object-contain"
              />
            </div>
          ) : (
            <div className="flex h-48 w-48 items-center justify-center rounded-xl border border-[#2A2A2A] bg-[#111]">
              <Loader2 size={24} className="animate-spin text-[#C9A84C]" />
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-[#C9A84C]/5 border border-[#C9A84C]/15 p-2.5 mb-3">
          <RefreshCw size={12} className="animate-spin text-[#C9A84C]" />
          <p className="text-[10px] text-[#C9A84C]">{lang === 'pt' ? 'Aguardando conexao... QR atualiza automaticamente' : 'Waiting for connection... QR refreshes automatically'}</p>
        </div>
        <button onClick={() => { if (pollRef.current) clearInterval(pollRef.current); setStep('config'); setQrCode(null); }}
          className="w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] py-2 text-xs text-[#A0A0A0] hover:text-white transition">
          {lang === 'pt' ? 'Voltar' : 'Back'}
        </button>
      </div>
    );
  }

  // Config step
  return (
    <div className="border-t border-[#1A1A1A] bg-[#0D0D0D] px-4 py-4 space-y-3">
      <div className="flex items-center gap-2 mb-1">
        <Link2 size={14} className="text-[#25D366]" />
        <p className="text-xs text-[#25D366] font-medium">Evolution API</p>
      </div>
      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 border border-red-500/20 p-2.5">
          <AlertCircle size={12} className="text-red-400 flex-shrink-0" />
          <p className="text-[10px] text-red-400">{error}</p>
        </div>
      )}
      <div>
        <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">{lang === 'pt' ? 'URL da API' : 'API URL'}</label>
        <input data-testid="wa-api-url" value={config.api_url} onChange={e => setConfig(p => ({ ...p, api_url: e.target.value }))}
          placeholder="https://evo.seuservidor.com"
          className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#25D366]/50 transition" />
      </div>
      <div>
        <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">{lang === 'pt' ? 'Chave da API' : 'API Key'}</label>
        <input data-testid="wa-api-key" value={config.api_key} onChange={e => setConfig(p => ({ ...p, api_key: e.target.value }))}
          placeholder="B6D711FCDE4D4FD5936544120E713976" type="password"
          className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#25D366]/50 transition" />
      </div>
      <div>
        <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">{lang === 'pt' ? 'Nome da Instancia' : 'Instance Name'}</label>
        <input data-testid="wa-instance" value={config.instance_name} onChange={e => setConfig(p => ({ ...p, instance_name: e.target.value }))}
          placeholder={lang === 'pt' ? 'meu-negocio' : 'my-business'}
          className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#25D366]/50 transition" />
      </div>
      <button data-testid="wa-connect-btn" onClick={handleCreateInstance} disabled={loading}
        className="w-full rounded-lg bg-[#25D366] py-2.5 text-xs font-semibold text-white hover:bg-[#20BD5A] disabled:opacity-50 transition flex items-center justify-center gap-2">
        {loading ? <Loader2 size={14} className="animate-spin" /> : <QrCode size={14} />}
        {loading ? (lang === 'pt' ? 'Criando instancia...' : 'Creating instance...') : (lang === 'pt' ? 'Gerar QR Code' : 'Generate QR Code')}
      </button>
      <div className="rounded-lg bg-[#111] border border-[#1A1A1A] p-3 space-y-2">
        <p className="text-[10px] text-[#666] font-medium uppercase tracking-wider">{lang === 'pt' ? 'Como conectar' : 'How to connect'}</p>
        <div className="space-y-1.5">
          {[
            lang === 'pt' ? '1. Instale a Evolution API no seu servidor' : '1. Install Evolution API on your server',
            lang === 'pt' ? '2. Copie a URL e a chave da API' : '2. Copy the URL and API key',
            lang === 'pt' ? '3. Escolha um nome para a instancia' : '3. Choose an instance name',
            lang === 'pt' ? '4. Clique em Gerar QR Code e escaneie' : '4. Click Generate QR Code and scan',
          ].map((text, i) => (
            <p key={i} className="text-[10px] text-[#555]">{text}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function ChannelConnection() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const lang = i18n.language || 'en';
  const [channels, setChannels] = useState([]);
  const [smsConfig, setSmsConfig] = useState({ account_sid: '', auth_token: '', phone_number: '' });
  const [telegramConfig, setTelegramConfig] = useState({ bot_token: '' });
  const [showConfig, setShowConfig] = useState(null);
  const [connecting, setConnecting] = useState(null);

  useEffect(() => {
    fetchChannels();
  }, []);

  const fetchChannels = async () => {
    try {
      const { data } = await axios.get(`${API}/channels`);
      setChannels(data.channels || []);
    } catch {}
  };

  const getChannelStatus = (type) => channels.find(c => c.type === type);

  const connectChannel = async (type) => {
    setConnecting(type);
    try {
      let config = {};
      if (type === 'sms') config = smsConfig;
      else if (type === 'telegram') config = telegramConfig;

      await axios.post(`${API}/channels`, { type, config });
      await fetchChannels();
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
    await fetchChannels();
    toast.success(lang === 'pt' ? 'Canal desconectado' : 'Channel disconnected');
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6 pb-24">
      <div className="mb-6 flex items-center gap-3">
        <button onClick={() => navigate('/settings')} className="text-[#A0A0A0] hover:text-white transition"><ArrowLeft size={20} /></button>
        <h1 className="text-xl font-bold text-white">{t('channels.title')}</h1>
      </div>

      <div className="space-y-3">
        {CHANNELS.map(ch => {
          const connected = getChannelStatus(ch.type);
          const isConnected = connected?.status === 'connected';
          const isConnecting = connected?.status === 'connecting' || connected?.status === 'waiting_qr';
          const IconComponent = ch.icon;

          return (
            <div key={ch.type} data-testid={`channel-${ch.type}`} className="rounded-xl border border-[#1A1A1A] bg-[#111] overflow-hidden">
              <div className="flex items-center gap-3 p-4">
                <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl" style={{ backgroundColor: `${ch.color}12` }}>
                  <IconComponent size={20} style={{ color: ch.color }} />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-semibold text-white">{ch.name}</h3>
                  <p className="text-[10px] text-[#555]">{ch.desc[lang] || ch.desc.en}</p>
                </div>
                <div className="flex items-center gap-2">
                  {ch.type === 'whatsapp' ? (
                    // WhatsApp has its own connect/status UI
                    isConnected ? (
                      <div className="flex items-center gap-1 rounded-full bg-[#25D366]/10 px-2.5 py-1">
                        <Wifi size={10} className="text-[#25D366]" />
                        <span className="text-[10px] text-[#25D366] font-medium">{t('settings.connected')}</span>
                      </div>
                    ) : isConnecting ? (
                      <div className="flex items-center gap-1 rounded-full bg-[#C9A84C]/10 px-2.5 py-1">
                        <RefreshCw size={10} className="animate-spin text-[#C9A84C]" />
                        <span className="text-[10px] text-[#C9A84C]">{lang === 'pt' ? 'Conectando...' : 'Connecting...'}</span>
                      </div>
                    ) : (
                      <button data-testid="connect-whatsapp" onClick={() => setShowConfig(showConfig === 'whatsapp' ? null : 'whatsapp')}
                        className="rounded-lg bg-[#25D366] px-4 py-1.5 text-xs font-semibold text-white hover:bg-[#20BD5A] transition">
                        {t('settings.connect')}
                      </button>
                    )
                  ) : isConnected ? (
                    <>
                      <div className="flex items-center gap-1 rounded-full bg-green-500/10 px-2.5 py-1">
                        <Wifi size={10} className="text-green-400" />
                        <span className="text-[10px] text-green-400">{t('settings.connected')}</span>
                      </div>
                      <button onClick={() => disconnectChannel(connected.id)} className="text-xs text-[#666] hover:text-red-400 transition">{t('channels.disconnect')}</button>
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

              {/* WhatsApp - Full Integration */}
              {showConfig === 'whatsapp' && ch.type === 'whatsapp' && (
                <WhatsAppSetup
                  channel={connected}
                  lang={lang}
                  onConnect={fetchChannels}
                  onDisconnect={fetchChannels}
                />
              )}

              {/* Always show WhatsApp setup if waiting_qr or connected */}
              {ch.type === 'whatsapp' && (isConnected || isConnecting) && showConfig !== 'whatsapp' && (
                <div className="border-t border-[#1A1A1A]">
                  <button onClick={() => setShowConfig('whatsapp')} className="w-full px-4 py-2 text-[10px] text-[#666] hover:text-[#C9A84C] transition text-center">
                    {lang === 'pt' ? 'Ver detalhes' : 'View details'}
                  </button>
                </div>
              )}

              {/* SMS Config */}
              {showConfig === 'sms' && ch.type === 'sms' && (
                <div className="border-t border-[#1A1A1A] bg-[#0D0D0D] px-4 py-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <Link2 size={14} className="text-[#F22F46]" />
                    <p className="text-xs text-[#F22F46] font-medium">Twilio</p>
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">Account SID</label>
                    <input data-testid="sms-account-sid" value={smsConfig.account_sid} onChange={e => setSmsConfig(p => ({ ...p, account_sid: e.target.value }))}
                      placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                      className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#F22F46]/50 transition font-mono" />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">Auth Token</label>
                    <input data-testid="sms-auth-token" value={smsConfig.auth_token} onChange={e => setSmsConfig(p => ({ ...p, auth_token: e.target.value }))}
                      placeholder="your_auth_token" type="password"
                      className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#F22F46]/50 transition" />
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">{lang === 'pt' ? 'Numero Twilio' : 'Twilio Number'}</label>
                    <input data-testid="sms-phone" value={smsConfig.phone_number} onChange={e => setSmsConfig(p => ({ ...p, phone_number: e.target.value }))}
                      placeholder="+15551234567"
                      className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#F22F46]/50 transition font-mono" />
                  </div>
                  <button data-testid="sms-connect-btn" onClick={() => connectChannel('sms')} disabled={connecting === 'sms'}
                    className="w-full rounded-lg bg-[#F22F46] py-2.5 text-xs font-semibold text-white hover:bg-[#D92340] disabled:opacity-50 transition">
                    {connecting === 'sms' ? '...' : (lang === 'pt' ? 'Conectar SMS' : 'Connect SMS')}
                  </button>
                </div>
              )}

              {/* Telegram Config */}
              {showConfig === 'telegram' && ch.type === 'telegram' && (
                <div className="border-t border-[#1A1A1A] bg-[#0D0D0D] px-4 py-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <Link2 size={14} className="text-[#0088CC]" />
                    <p className="text-xs text-[#0088CC] font-medium">BotFather Token</p>
                  </div>
                  <div>
                    <label className="mb-1 block text-[10px] text-[#666] uppercase tracking-wider">Bot Token</label>
                    <input data-testid="telegram-token" value={telegramConfig.bot_token} onChange={e => setTelegramConfig(p => ({ ...p, bot_token: e.target.value }))}
                      placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                      className="w-full rounded-lg border border-[#2A2A2A] bg-[#1E1E1E] px-3 py-2.5 text-sm text-white placeholder-[#444] outline-none focus:border-[#0088CC]/50 transition font-mono" />
                  </div>
                  <button data-testid="telegram-connect-btn" onClick={() => connectChannel('telegram')} disabled={connecting === 'telegram'}
                    className="w-full rounded-lg bg-[#0088CC] py-2.5 text-xs font-semibold text-white hover:bg-[#0077B5] disabled:opacity-50 transition">
                    {connecting === 'telegram' ? '...' : (lang === 'pt' ? 'Conectar Telegram' : 'Connect Telegram')}
                  </button>
                </div>
              )}

              {/* Instagram / Facebook */}
              {(showConfig === 'instagram' || showConfig === 'facebook') && ch.type === showConfig && (
                <div className="border-t border-[#1A1A1A] bg-[#0D0D0D] px-4 py-5 text-center">
                  <p className="text-xs text-[#666] mb-3">{lang === 'pt' ? 'Conecte via Facebook Business Manager' : 'Connect via Facebook Business Manager'}</p>
                  <button onClick={() => connectChannel(ch.type)} disabled={connecting === ch.type}
                    className="btn-gold rounded-lg px-6 py-2.5 text-xs disabled:opacity-50">
                    {connecting === ch.type ? '...' : (lang === 'pt' ? 'Conectar com Facebook' : 'Connect with Facebook')}
                  </button>
                  <p className="mt-3 text-[10px] text-[#444]">{lang === 'pt' ? 'Integracao em breve' : 'Integration coming soon'}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
