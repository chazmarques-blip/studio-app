import { Outlet } from 'react-router-dom';
import { BottomNav } from './BottomNav';

function TechGridBg() {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0" aria-hidden="true">
      <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="app-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(201,168,76,0.025)" strokeWidth="0.5" />
          </pattern>
          <radialGradient id="app-grid-fade" cx="50%" cy="30%" r="55%">
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="app-grid-mask"><rect width="100%" height="100%" fill="url(#app-grid-fade)" /></mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#app-grid)" mask="url(#app-grid-mask)" />
      </svg>
      <div className="absolute left-1/4 top-0 h-[350px] w-[450px] rounded-full bg-[#C9A84C]/[0.02] blur-[140px]" />
      <div className="absolute right-0 top-1/3 h-[250px] w-[300px] rounded-full bg-[#C9A84C]/[0.015] blur-[120px]" />
    </div>
  );
}

export function AppLayout() {
  return (
    <div className="relative min-h-screen bg-[#0A0A0A]">
      <TechGridBg />
      <main className="relative z-10 pb-20">
        <Outlet />
      </main>
      <BottomNav />
    </div>
  );
}
