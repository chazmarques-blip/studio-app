import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { User, Globe, CreditCard, Link2, LogOut, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';

const channelStatus = [
  { name: 'WhatsApp', color: '#25D366', connected: false },
  { name: 'Instagram', color: '#E4405F', connected: false },
  { name: 'Facebook', color: '#1877F2', connected: false },
  { name: 'Telegram', color: '#0088CC', connected: false },
];

export default function SettingsPage() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await signOut();
    toast.success('Signed out');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-6">
      <h1 className="mb-6 text-xl font-bold text-white">Settings</h1>

      {/* Profile Card */}
      <div data-testid="profile-card" className="glass-card mb-4 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D]">
            <span className="text-lg font-bold text-[#0A0A0A]">
              {(user?.full_name || user?.user_metadata?.full_name || user?.email || 'U')[0].toUpperCase()}
            </span>
          </div>
          <div>
            <p className="text-sm font-semibold text-white">{user?.full_name || user?.user_metadata?.full_name || 'User'}</p>
            <p className="text-xs text-[#666666]">{user?.email}</p>
          </div>
          <ChevronRight size={16} className="ml-auto text-[#3A3A3A]" />
        </div>
      </div>

      {/* Menu Items */}
      <div className="mb-4 space-y-1">
        {[
          { icon: User, label: 'Account', desc: 'Edit profile and company info' },
          { icon: Globe, label: 'Language', desc: 'Change interface language' },
          { icon: CreditCard, label: 'Billing', desc: 'Manage your subscription' },
          { icon: Link2, label: 'Integrations', desc: 'Google Calendar, Sheets & more' },
        ].map((item, i) => (
          <button key={i} className="glass-card flex w-full items-center gap-3 p-4 text-left transition-all hover:border-[rgba(201,168,76,0.3)]">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#1E1E1E]">
              <item.icon size={16} className="text-[#A0A0A0]" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-medium text-white">{item.label}</p>
              <p className="text-xs text-[#666666]">{item.desc}</p>
            </div>
            <ChevronRight size={16} className="text-[#3A3A3A]" />
          </button>
        ))}
      </div>

      {/* Channels */}
      <div className="mb-4">
        <h2 className="mb-3 text-sm font-semibold text-[#A0A0A0]">Connected Channels</h2>
        <div className="space-y-1">
          {channelStatus.map(ch => (
            <div key={ch.name} data-testid={`channel-${ch.name.toLowerCase()}`} className="glass-card flex items-center gap-3 p-3">
              <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: ch.color }} />
              <span className="flex-1 text-sm text-white">{ch.name}</span>
              <span className={`text-xs ${ch.connected ? 'text-[#4CAF50]' : 'text-[#666666]'}`}>
                {ch.connected ? 'Connected' : 'Not connected'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Logout */}
      <button
        data-testid="logout-btn"
        onClick={handleLogout}
        className="flex w-full items-center gap-3 rounded-xl bg-[#1A1A1A] border border-[#2A2A2A] p-4 text-left transition hover:border-red-500/30"
      >
        <LogOut size={16} className="text-red-400" />
        <span className="text-sm font-medium text-red-400">Sign Out</span>
      </button>
    </div>
  );
}
