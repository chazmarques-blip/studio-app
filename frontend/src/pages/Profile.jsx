import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Save, Crown, MessageSquare, Bot, ChevronRight, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Profile() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user, signOut, setUser } = useAuth();
  const [form, setForm] = useState({ full_name: '', company_name: '', ui_language: 'en' });
  const [saving, setSaving] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (user) {
      setForm({ full_name: user.full_name || '', company_name: user.company_name || '', ui_language: user.ui_language || 'en' });
    }
    axios.get(`${API}/dashboard/stats`).then(r => setStats(r.data)).catch(() => {});
  }, [user]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/auth/profile`, form);
      if (setUser) setUser(prev => ({ ...prev, ...form }));
      toast.success('Profile updated!');
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Error');
    } finally { setSaving(false); }
  };

  const handleLogout = async () => {
    await signOut();
    navigate('/');
  };

  const plan = stats?.plan || 'free';
  const msgsUsed = stats?.messages_used || 0;
  const msgsLimit = stats?.messages_limit || 200;
  const msgsPct = msgsLimit > 0 ? Math.min(100, Math.round((msgsUsed / msgsLimit) * 100)) : 0;

  return (
    <div className="min-h-screen bg-[#0A0A0A] px-4 pt-5 pb-24">
      <div className="mb-5 flex items-center gap-3">
        <button onClick={() => navigate('/settings')} className="text-[#999] hover:text-white transition"><ArrowLeft size={20} /></button>
        <h1 className="text-lg font-bold text-white">Profile</h1>
      </div>

      {/* Avatar + Name */}
      <div className="flex flex-col items-center mb-6">
        <div className="h-16 w-16 rounded-full bg-gradient-to-br from-[#C9A84C] to-[#A88B3D] flex items-center justify-center mb-3">
          <span className="text-2xl font-bold text-[#0A0A0A]">{(form.full_name || user?.email || 'U')[0].toUpperCase()}</span>
        </div>
        <p className="text-sm font-semibold text-white">{form.full_name || 'User'}</p>
        <p className="text-xs text-[#B0B0B0]">{user?.email}</p>
      </div>

      {/* Plan quick card */}
      {stats && (
        <button data-testid="plan-quick-card" onClick={() => navigate('/pricing')} className="w-full mb-5 rounded-xl border border-[#C9A84C]/15 bg-[#C9A84C]/5 p-4 text-left">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Crown size={14} className="text-[#C9A84C]" />
              <span className="text-xs font-semibold text-white capitalize">{plan} Plan</span>
            </div>
            <ChevronRight size={14} className="text-[#C9A84C]" />
          </div>
          <div className="flex items-center gap-3 text-[11px]">
            <div className="flex items-center gap-1.5 text-[#888]">
              <MessageSquare size={10} />{msgsUsed}/{msgsLimit.toLocaleString()} msgs
            </div>
            <div className="flex items-center gap-1.5 text-[#888]">
              <Bot size={10} />{stats.agents_count}/{stats.agents_limit} agents
            </div>
          </div>
          <div className="mt-2 h-1.5 rounded-full bg-[#1A1A1A] overflow-hidden">
            <div className="h-full rounded-full bg-[#C9A84C] transition-all" style={{ width: `${msgsPct}%` }} />
          </div>
          <p className="mt-1 text-[10px] text-[#C9A84C]">Manage plan & billing</p>
        </button>
      )}

      {/* Edit Profile */}
      <div className="space-y-3 mb-6">
        <div>
          <label className="mb-1 block text-xs text-[#999]">Full Name</label>
          <input data-testid="profile-name" value={form.full_name} onChange={e => setForm(p => ({...p, full_name: e.target.value}))}
            className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#C9A84C]/40" />
        </div>
        <div>
          <label className="mb-1 block text-xs text-[#999]">Company</label>
          <input data-testid="profile-company" value={form.company_name} onChange={e => setForm(p => ({...p, company_name: e.target.value}))}
            className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#C9A84C]/40" />
        </div>
        <div>
          <label className="mb-1 block text-xs text-[#999]">Language</label>
          <select data-testid="profile-lang" value={form.ui_language} onChange={e => setForm(p => ({...p, ui_language: e.target.value}))}
            className="w-full rounded-lg border border-[#1E1E1E] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#C9A84C]/40">
            <option value="en">English</option>
            <option value="pt">Portugues</option>
            <option value="es">Espanol</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-[#999]">Email</label>
          <input value={user?.email || ''} disabled className="w-full rounded-lg border border-[#1E1E1E] bg-[#0A0A0A] px-3 py-2.5 text-sm text-[#B0B0B0] outline-none" />
        </div>
      </div>

      <button data-testid="save-profile-btn" onClick={handleSave} disabled={saving}
        className="btn-gold w-full flex items-center justify-center gap-2 rounded-lg py-2.5 text-sm font-semibold disabled:opacity-50 mb-4">
        <Save size={14} /> {saving ? 'Saving...' : 'Save Changes'}
      </button>

      <button data-testid="logout-btn" onClick={handleLogout}
        className="w-full flex items-center justify-center gap-2 rounded-lg border border-red-500/20 py-2.5 text-sm text-red-400 hover:bg-red-500/5 transition">
        <LogOut size={14} /> Sign Out
      </button>
    </div>
  );
}
