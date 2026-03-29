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
    <nav data-testid="bottom-nav" className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#2A2A2A] bg-[#111111]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-lg items-center justify-around px-1 py-2">
        {tabs.map(({ path, icon: Icon, label, exact, matchPath }) => {
          const checkPath = matchPath || path.split('?')[0];
          const isActive = exact 
            ? location.pathname === checkPath
            : location.pathname.startsWith(checkPath);
          return (
            <button key={path} data-testid={`nav-${label.toLowerCase().replace(/\s/g, '-')}`} onClick={() => navigate(path)}
              className={`flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${isActive ? 'text-[#8B5CF6]' : 'text-[#666666] hover:text-[#A0A0A0]'}`}>
              <Icon size={18} strokeWidth={isActive ? 2.2 : 1.8} />
              <span className="text-[9px] font-medium">{label}</span>
              {isActive && <div className="mt-0.5 h-1 w-1 rounded-full bg-[#8B5CF6]" />}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
