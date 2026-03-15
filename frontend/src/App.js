import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AppLayout } from './components/layout/AppLayout';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Onboarding from './pages/Onboarding';
import OnboardingAgentLang from './pages/OnboardingAgentLang';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import Agents from './pages/Agents';
import AgentBuilder from './pages/AgentBuilder';
import AgentSandbox from './pages/AgentSandbox';
import AgentConfig from './pages/AgentConfig';
import CRM from './pages/CRM';
import LeadDetail from './pages/LeadDetail';
import CampaignBuilder from './pages/CampaignBuilder';
import Analytics from './pages/Analytics';
import SettingsPage from './pages/Settings';
import ChannelConnection from './pages/ChannelConnection';
import HandoffHuman from './pages/HandoffHuman';
import UpsellScreen from './pages/UpsellScreen';
import Pricing from './pages/Pricing';
import GoogleIntegration from './pages/GoogleIntegration';
import Marketing from './pages/Marketing';
import MarketingStudio from './pages/MarketingStudio';
import TrafficHub from './pages/TrafficHub';

import { useEffect } from 'react';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
      </div>
    );
  }
  return user ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#C9A84C]" />
      </div>
    );
  }
  if (user) {
    return <Navigate to={user.onboarding_completed ? '/dashboard' : '/onboarding'} replace />;
  }
  return children;
}

function App() {
  useEffect(() => {
    const removeBadge = () => {
      const el = document.getElementById('emergent-badge');
      if (el) el.remove();
      document.querySelectorAll('a[href*="emergent.sh"]').forEach(a => a.remove());
    };
    removeBadge();
    const interval = setInterval(removeBadge, 500);
    return () => clearInterval(interval);
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster position="top-center" toastOptions={{ style: { background: '#1A1A1A', border: '1px solid #2A2A2A', color: '#FFFFFF', fontSize: '13px' } }} />
        <Routes>
          {/* Public */}
          <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          {/* Onboarding */}
          <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
          <Route path="/onboarding/agent-lang" element={<ProtectedRoute><OnboardingAgentLang /></ProtectedRoute>} />
          {/* App with bottom nav */}
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/crm" element={<CRM />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/marketing" element={<Marketing />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/pricing" element={<Pricing />} />
          </Route>
          {/* Full-screen pages (no bottom nav) */}
          <Route path="/agents/builder" element={<ProtectedRoute><AgentBuilder /></ProtectedRoute>} />
          <Route path="/agents/sandbox" element={<ProtectedRoute><AgentSandbox /></ProtectedRoute>} />
          <Route path="/agents/:agentId/config" element={<ProtectedRoute><AgentConfig /></ProtectedRoute>} />
          <Route path="/crm/lead/:id" element={<ProtectedRoute><LeadDetail /></ProtectedRoute>} />
          <Route path="/campaigns/new" element={<ProtectedRoute><CampaignBuilder /></ProtectedRoute>} />
          <Route path="/chat/handoff/:id" element={<ProtectedRoute><HandoffHuman /></ProtectedRoute>} />
          <Route path="/settings/channels" element={<ProtectedRoute><ChannelConnection /></ProtectedRoute>} />
          <Route path="/settings/google" element={<ProtectedRoute><GoogleIntegration /></ProtectedRoute>} />
          <Route path="/marketing/studio" element={<ProtectedRoute><MarketingStudio /></ProtectedRoute>} />
          <Route path="/traffic-hub" element={<ProtectedRoute><TrafficHub /></ProtectedRoute>} />
          <Route path="/upgrade" element={<ProtectedRoute><UpsellScreen /></ProtectedRoute>} />
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
