import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Brain, Sparkles, Award } from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * ActiveAgentIndicator
 * Polls /api/studio/projects/{projectId}/active-agent every 2s and shows a
 * live "thinking" badge with the agent name + master reference + animated
 * dots. When there's no active agent, renders nothing.
 *
 * Props:
 *   projectId   (string, required)
 *   enabled     (bool, default true) — stop polling when false (e.g. project
 *               is idle / complete) to save requests
 *   compact     (bool, default false) — smaller variant for headers
 */
export function ActiveAgentIndicator({ projectId, enabled = true, compact = false }) {
  const [active, setActive] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const intervalRef = useRef(null);
  const tickRef = useRef(null);

  // Poll backend
  useEffect(() => {
    if (!projectId || !enabled) {
      setActive(null);
      return;
    }

    let alive = true;

    const poll = async () => {
      try {
        const res = await axios.get(`${API}/studio/projects/${projectId}/active-agent`);
        if (!alive) return;
        setActive(res.data?.active_agent || null);
      } catch {
        // Silent — indicator is optional UI
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);

    return () => {
      alive = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [projectId, enabled]);

  // Tick elapsed time
  useEffect(() => {
    if (!active?.started_at) {
      setElapsed(0);
      if (tickRef.current) clearInterval(tickRef.current);
      return;
    }
    const computeElapsed = () => {
      const started = new Date(active.started_at).getTime();
      setElapsed(Math.max(0, Math.floor((Date.now() - started) / 1000)));
    };
    computeElapsed();
    tickRef.current = setInterval(computeElapsed, 1000);
    return () => { if (tickRef.current) clearInterval(tickRef.current); };
  }, [active?.started_at]);

  if (!active) return null;

  const master = active.master_reference;
  const name = active.name || active.agent_id;
  const action = active.action || 'pensando…';

  if (compact) {
    return (
      <div
        data-testid="active-agent-indicator-compact"
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gradient-to-r from-violet-500/15 to-orange-500/15 border border-violet-400/40 text-[11px] font-semibold text-violet-700 dark:text-violet-200"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-violet-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-violet-500" />
        </span>
        <Brain size={11} className="shrink-0" />
        <span className="truncate max-w-[200px]">
          {master ? `${master} · ` : ''}{name}
        </span>
        <ThinkingDots />
      </div>
    );
  }

  return (
    <div
      data-testid="active-agent-indicator"
      className="relative rounded-xl border border-violet-400/40 dark:border-violet-500/40 bg-gradient-to-br from-violet-50 via-fuchsia-50 to-orange-50 dark:from-violet-500/15 dark:via-fuchsia-500/10 dark:to-orange-500/15 p-3 mb-2 overflow-hidden"
    >
      {/* Animated background sheen */}
      <div className="absolute inset-0 opacity-20 pointer-events-none">
        <div className="absolute -inset-[200%] bg-gradient-to-r from-transparent via-white/60 to-transparent animate-[sheen_3s_linear_infinite]" />
      </div>

      <div className="relative flex items-start gap-3">
        <div className="relative shrink-0">
          <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-violet-500 to-orange-500 flex items-center justify-center shadow-md">
            <Brain size={18} className="text-white" />
          </div>
          {/* Pulse ring */}
          <span className="absolute inset-0 rounded-lg ring-2 ring-violet-400 animate-ping opacity-40" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className="text-[13px] font-bold text-gray-900 dark:text-white"
              data-testid="active-agent-name"
            >
              {name}
            </span>
            {master && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-orange-700 dark:text-orange-300 bg-orange-500/10 px-1.5 py-0.5 rounded">
                <Award size={10} />
                {master}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <span className="text-[12px] text-gray-700 dark:text-[#A3A3B2] leading-snug flex items-center gap-1">
              <Sparkles size={11} className="text-violet-500 dark:text-violet-300 animate-pulse" />
              {action}
              <ThinkingDots />
            </span>
            {elapsed > 0 && (
              <span
                className="text-[10px] text-gray-500 dark:text-[#A3A3B2]/80 tabular-nums ml-auto"
                data-testid="active-agent-elapsed"
              >
                {formatElapsed(elapsed)}
              </span>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes sheen {
          0% { transform: translateX(-50%); }
          100% { transform: translateX(50%); }
        }
      `}</style>
    </div>
  );
}

function ThinkingDots() {
  return (
    <span className="inline-flex gap-[2px] ml-0.5" aria-hidden>
      <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1 h-1 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  );
}

function formatElapsed(seconds) {
  if (seconds < 60) return `${seconds}s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s.toString().padStart(2, '0')}s`;
}

export default ActiveAgentIndicator;
