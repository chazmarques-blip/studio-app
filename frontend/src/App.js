import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { StudioProductionProvider } from './contexts/StudioProductionContext';
import { StudioProductionBanner } from './components/StudioProductionBanner';
import { AppLayout } from './components/layout/AppLayout';
import React, { Suspense, useEffect } from 'react';

// ── Error Boundary (prevents white screen crashes) ──
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-[#0A0A0A] text-white p-8">
          <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mb-4">
            <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-lg font-semibold mb-2">Algo deu errado</h2>
          <p className="text-sm text-gray-400 mb-4 text-center max-w-md">{this.state.error?.message || 'Erro inesperado'}</p>
          <button
            onClick={() => { this.setState({ hasError: false, error: null }); window.location.reload(); }}
            className="px-4 py-2 bg-[#8B5CF6] text-black rounded-lg text-sm font-medium hover:bg-[#7C3AED] transition-colors"
            data-testid="error-boundary-reload"
          >
            Recarregar
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Loading Fallback ──
const PageLoader = () => (
  <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2A2A2A] border-t-[#8B5CF6]" />
  </div>
);

// ── Code Splitting: Heavy pages loaded on demand ──
const LandingV2 = React.lazy(() => import('./pages/LandingV2'));
const Login = React.lazy(() => import('./pages/Login'));
const Onboarding = React.lazy(() => import('./pages/Onboarding'));
const OnboardingAgentLang = React.lazy(() => import('./pages/OnboardingAgentLang'));
const Dashboard = React.lazy(() => import('./pages/DashboardStudio')); // StudioX Dashboard
const Chat = React.lazy(() => import('./pages/Chat'));
const Agents = React.lazy(() => import('./pages/Agents'));
const AgentBuilder = React.lazy(() => import('./pages/AgentBuilder'));
const AgentSandbox = React.lazy(() => import('./pages/AgentSandbox'));
const AgentConfig = React.lazy(() => import('./pages/AgentConfig'));
const CRM = React.lazy(() => import('./pages/CRM'));
const LeadDetail = React.lazy(() => import('./pages/LeadDetail'));
const CampaignBuilder = React.lazy(() => import('./pages/CampaignBuilder'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const SettingsPage = React.lazy(() => import('./pages/Settings'));
const ChannelConnection = React.lazy(() => import('./pages/ChannelConnection'));
const HandoffHuman = React.lazy(() => import('./pages/HandoffHuman'));
const UpsellScreen = React.lazy(() => import('./pages/UpsellScreen'));
const Pricing = React.lazy(() => import('./pages/Pricing'));
const GoogleIntegration = React.lazy(() => import('./pages/GoogleIntegration'));
const Marketing = React.lazy(() => import('./pages/Marketing'));
const MarketingStudio = React.lazy(() => import('./pages/MarketingStudio'));
const StudioPage = React.lazy(() => import('./pages/StudioPage')); // NEW: Exclusive Studio Page
const InteractiveBook = React.lazy(() => import('./pages/InteractiveBook'));
const TrafficHub = React.lazy(() => import('./pages/TrafficHub'));

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
  return user ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <PageLoader />;
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
        <StudioProductionProvider>
        <ErrorBoundary>
        <Toaster position="top-center" toastOptions={{ style: { background: '#1A1A1A', border: '1px solid #2A2A2A', color: '#FFFFFF', fontSize: '13px' } }} />
        <StudioProductionBanner />
        <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public */}
          <Route path="/" element={<PublicRoute><LandingV2 /></PublicRoute>} />
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
          <Route path="/studio" element={<ProtectedRoute><StudioPage /></ProtectedRoute>} />
          <Route path="/book/:projectId" element={<InteractiveBook />} />
          <Route path="/traffic-hub" element={<ProtectedRoute><TrafficHub /></ProtectedRoute>} />
          <Route path="/upgrade" element={<ProtectedRoute><UpsellScreen /></ProtectedRoute>} />
          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </Suspense>
        </ErrorBoundary>
        </StudioProductionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
