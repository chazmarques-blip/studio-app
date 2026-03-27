import { LayoutDashboard, MessageSquare, Bot, Target, BarChart3, Settings, Megaphone, Film } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const tabs = [
    { path: '/dashboard', icon: LayoutDashboard, label: t('nav.dashboard') },
    { path: '/chat', icon: MessageSquare, label: t('nav.chat') },
    { path: '/agents', icon: Bot, label: t('nav.agents') },
    { path: '/marketing', icon: Megaphone, label: 'Marketing', exact: true },
    { path: '/marketing/studio?mode=directed', icon: Film, label: 'Movie', matchPath: '/marketing/studio' },
    { path: '/crm', icon: Target, label: t('nav.crm') },
    { path: '/analytics', icon: BarChart3, label: t('nav.analytics') },
    { path: '/settings', icon: Settings, label: t('nav.settings') },
  ];

  return (
    <nav data-testid="bottom-nav" className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#2A2A2A] bg-[#111111]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-lg items-center justify-around px-1 py-2">
        {tabs.map(({ path, icon: Icon, label, exact, matchPath }) => {
          const checkPath = matchPath || path.split('?')[0];
          const isActive = exact
            ? location.pathname === checkPath
            : location.pathname.startsWith(checkPath) && (!exact || location.pathname === checkPath);
          return (
            <button key={path} data-testid={`nav-${label.toLowerCase().replace(/\s/g, '-')}`} onClick={() => navigate(path)}
              className={`flex flex-col items-center gap-0.5 rounded-lg px-2 py-1.5 transition-all duration-200 ${isActive ? 'text-[#C9A84C]' : 'text-[#666666] hover:text-[#A0A0A0]'}`}>
              <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
              <span className="text-[9px] font-medium">{label}</span>
              {isActive && <div className="mt-0.5 h-1 w-1 rounded-full bg-[#C9A84C]" />}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
