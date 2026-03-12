import { MessageSquare, Bot, Target, BarChart3, Settings } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

const tabs = [
  { path: '/chat', icon: MessageSquare, label: 'Chat' },
  { path: '/agents', icon: Bot, label: 'Agents' },
  { path: '/crm', icon: Target, label: 'CRM' },
  { path: '/analytics', icon: BarChart3, label: 'Analytics' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <nav data-testid="bottom-nav" className="fixed bottom-0 left-0 right-0 z-50 border-t border-[#2A2A2A] bg-[#111111]/95 backdrop-blur-md">
      <div className="mx-auto flex max-w-lg items-center justify-around px-2 py-2">
        {tabs.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname.startsWith(path);
          return (
            <button
              key={path}
              data-testid={`nav-${label.toLowerCase()}`}
              onClick={() => navigate(path)}
              className={`flex flex-col items-center gap-0.5 rounded-lg px-3 py-1.5 transition-all duration-200 ${
                isActive
                  ? 'text-[#C9A84C]'
                  : 'text-[#666666] hover:text-[#A0A0A0]'
              }`}
            >
              <Icon size={20} strokeWidth={isActive ? 2.2 : 1.8} />
              <span className="text-[10px] font-medium">{label}</span>
              {isActive && (
                <div className="mt-0.5 h-1 w-1 rounded-full bg-[#C9A84C]" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
