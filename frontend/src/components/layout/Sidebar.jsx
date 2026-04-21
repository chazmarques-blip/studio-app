import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Home, Users, Bot, Settings, Zap } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

/**
 * Unified left sidebar — replaces BottomNav + per-page nav
 * - Collapsed state for future (64px) — for now always expanded (240px)
 * - Items: Projetos / Personagens / Agentes / Configurações
 * - Bottom: avatar + credits (click → profile menu)
 */
export default function Sidebar({ counts = {} }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, tenant } = useAuth();

  const ITEMS = [
    { path: '/studio', key: 'projetos', label: 'Projetos', Icon: Home, count: counts.projects ?? null, activeRegex: /^\/(studio|dashboard|projetos)(?!\?gallery)/, isActive: (loc) => /^\/(studio|dashboard|projetos)/.test(loc.pathname) && !loc.search.includes('gallery=') },
    { path: '/studio?gallery=1', key: 'personagens', label: 'Personagens', Icon: Users, count: counts.characters ?? null, activeRegex: /gallery=1/, isActive: (loc) => loc.search.includes('gallery=') },
    { path: '/studio/agents', key: 'agentes', label: 'Agentes', Icon: Bot, count: counts.agents ?? null, activeRegex: /^\/(agents|studio\/agents)/, isActive: (loc) => /^\/(agents|studio\/agents)/.test(loc.pathname) },
    { path: '/settings/channels', key: 'config', label: 'Configurações', Icon: Settings, count: null, activeRegex: /^\/settings/, isActive: (loc) => /^\/settings/.test(loc.pathname) },
  ];

  const initials = (user?.full_name || user?.email || 'U').split(' ').map(s => s[0]).slice(0, 2).join('').toUpperCase();
  const creditsLeft = Math.max(0, (tenant?.limits?.messages_limit || 0) - (tenant?.usage?.messages_sent_this_period || 0));
  const creditsTotal = tenant?.limits?.messages_limit || 0;

  return (
    <aside
      data-testid="app-sidebar"
      className="hidden md:flex fixed inset-y-0 left-0 z-40 w-60 shrink-0 flex-col border-r border-gray-200 bg-[#FAF8FD] dark:bg-[#110A1F] dark:border-[#2A2442]"
      style={{ fontFamily: "'Outfit', system-ui" }}
    >
      {/* Logo */}
      <Link to="/studio" className="h-12 px-4 flex items-center gap-2 border-b border-gray-200 dark:border-[#2A2442]">
        <div className="h-7 w-7 rounded-lg bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center text-xs font-black text-white shadow-sm dark:shadow-[0_0_20px_rgba(139,92,246,0.4)]">X</div>
        <span className="text-[15px] font-semibold tracking-tight text-gray-900 dark:text-white">StudioX</span>
      </Link>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {ITEMS.map(({ path, key, label, Icon, count, isActive }) => {
          const active = isActive(location);
          return (
            <button
              key={key}
              onClick={() => navigate(path)}
              data-testid={`sidebar-${key}`}
              className={`relative w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition ${
                active
                  ? 'bg-violet-50 text-violet-800 dark:bg-violet-500/15 dark:text-violet-200'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-[#A3A3B2] dark:hover:bg-white/5 dark:hover:text-white'
              }`}
            >
              {active && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full bg-violet-500" />}
              <Icon size={16} strokeWidth={1.75} />
              <span className="flex-1 text-left">{label}</span>
              {count != null && (
                <span className={`text-[10px] font-mono ${active ? 'text-violet-600 dark:text-violet-300/80' : 'text-gray-400 dark:text-[#6B647F]'}`}>{count}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer — avatar + credits */}
      <div className="px-3 pb-3 border-t border-gray-200 dark:border-[#2A2442] pt-3">
        <button
          onClick={() => navigate('/pricing')}
          data-testid="sidebar-credits"
          className="w-full flex items-center gap-2 p-2 rounded-lg hover:bg-white dark:hover:bg-white/5 cursor-pointer transition"
        >
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-orange-500 flex items-center justify-center text-[11px] font-bold text-white">
            {initials}
          </div>
          <div className="flex-1 min-w-0 text-left">
            <p className="text-[12px] font-medium text-gray-900 dark:text-white truncate">{user?.full_name || user?.email || 'Usuário'}</p>
            <p className="text-[10px] text-gray-500 dark:text-[#6B647F] flex items-center gap-1 font-mono">
              <Zap size={9} className="text-orange-500" />
              {creditsLeft.toLocaleString()} / {creditsTotal >= 1000 ? `${Math.round(creditsTotal / 1000)}k` : creditsTotal}
            </p>
          </div>
        </button>
      </div>
    </aside>
  );
}
