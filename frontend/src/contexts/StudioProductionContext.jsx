import { createContext, useContext, useState, useRef, useCallback, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const StudioProductionContext = createContext(null);

export function StudioProductionProvider({ children }) {
  const [activeProduction, setActiveProduction] = useState(null);
  // { projectId, projectName, agentStatus, outputs, scenes, status, startedAt }
  const pollRef = useRef(null);
  const dismissed = useRef(false);

  const startTracking = useCallback((projectId, projectName, scenes) => {
    dismissed.current = false;
    setActiveProduction({
      projectId, projectName, scenes: scenes || [],
      agentStatus: {}, outputs: [], status: 'running_agents', startedAt: Date.now(),
    });
  }, []);

  const stopTracking = useCallback(() => {
    if (pollRef.current) { clearTimeout(pollRef.current); pollRef.current = null; }
    setActiveProduction(null);
  }, []);

  const dismiss = useCallback(() => { dismissed.current = true; }, []);

  // Poll when there's an active production
  useEffect(() => {
    if (!activeProduction?.projectId) return;
    if (['complete', 'error'].includes(activeProduction.status)) return;

    const poll = async () => {
      try {
        const token = localStorage.getItem('agentzz_token');
        if (!token) return;
        const res = await axios.get(`${API}/studio/projects/${activeProduction.projectId}/status`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const d = res.data;

        setActiveProduction(prev => {
          if (!prev || prev.projectId !== activeProduction.projectId) return prev;
          const updated = {
            ...prev,
            agentStatus: d.agent_status || {},
            outputs: d.outputs || [],
            scenes: d.scenes || prev.scenes,
            status: d.status,
            narrations: d.narrations || [],
          };
          if (d.status === 'complete') {
            toast.success('Produção concluída! Clique para ver o resultado.', { duration: 10000 });
            try { new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqF').play(); } catch {}
          }
          if (d.status === 'error') {
            toast.error(d.error || 'Erro na produção');
          }
          return updated;
        });
      } catch {}
      pollRef.current = setTimeout(poll, 4000);
    };

    pollRef.current = setTimeout(poll, 2000);
    return () => { if (pollRef.current) { clearTimeout(pollRef.current); pollRef.current = null; } };
  }, [activeProduction?.projectId, activeProduction?.status]);

  return (
    <StudioProductionContext.Provider value={{
      activeProduction, startTracking, stopTracking, dismiss, isDismissed: () => dismissed.current,
    }}>
      {children}
    </StudioProductionContext.Provider>
  );
}

export function useStudioProduction() {
  return useContext(StudioProductionContext);
}
