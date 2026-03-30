import { LayoutDashboard, Bot, Film, Settings, Clapperboard, Megaphone } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();
  const { i18n } = useTranslation();
  const lang = i18n.language?.startsWith('pt') ? 'pt' : i18n.language?.startsWith('es') ? 'es' : 'en';

  const L = {
    pt: { dashboard: 'Início', studio: 'Estúdio', marketing: 'Marketing', agents: 'Agentes', settings: 'Config' },
    en: { dashboard: 'Home', studio: 'Studio', marketing: 'Marketing', agents: 'Agents', settings: 'Settings' },
    es: { dashboard: 'Inicio', studio: 'Estudio', marketing: 'Marketing', agents: 'Agentes', settings: 'Config' },
  };
  const l = L[lang] || L.en;

  const tabs = [
    { path: '/dashboard', icon: LayoutDashboard, label: l.dashboard },
    { path: '/studio', icon: Film, label: l.studio },
    { path: '/marketing', icon: Megaphone, label: l.marketing, exact: true },
    { path: '/agents', icon: Bot, label: l.agents },
    { path: '/settings', icon: Settings, label: l.settings },
  ];

  return (
    <nav data-testid="bottom-nav" className="fixed bottom-0 left-0 right-0 z-50 border-t border-gray-200 bg-white/95 backdrop-blur-md shadow-lg">
      <div className="mx-auto flex max-w-lg items-center justify-around px-1 py-2.5">
        {tabs.map(({ path, icon: Icon, label, exact, matchPath }) => {
          const checkPath = matchPath || path.split('?')[0];
          const isActive = exact 
            ? location.pathname === checkPath
            : location.pathname.startsWith(checkPath);
          return (
            <button key={path} data-testid={`nav-${label.toLowerCase().replace(/\s/g, '-')}`} onClick={() => navigate(path)}
              className={`flex flex-col items-center gap-1 rounded-xl px-3 py-2 transition-all duration-200 ${isActive ? 'text-orange-600 bg-orange-50' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'}`}>
              <Icon size={20} strokeWidth={isActive ? 2.5 : 2} />
              <span className="text-[10px] font-semibold">{label}</span>
              {isActive && <div className="h-1 w-1 rounded-full bg-orange-500" />}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
