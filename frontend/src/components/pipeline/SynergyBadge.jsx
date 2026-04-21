import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Award, Brain, ChevronRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * SynergyBadge — shows which registered masters/mindsets are ACTIVE
 * for the current project's category (video / book / hybrid).
 *
 * Shows only when at least one agent or mindset is active, so projects
 * in default mode don't see clutter.
 */
export function SynergyBadge({ category = 'video', compact = false }) {
  const [agents, setAgents] = useState([]);
  const [mindset, setMindset] = useState(null);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [ag, mi] = await Promise.all([
          axios.get(`${API}/studio/agents/registry`),
          axios.get(`${API}/studio/agents/mindsets`),
        ]);
        if (!alive) return;
        setAgents(ag.data.agents || []);
        setMindset((mi.data.mindsets || {})[category] || null);
      } catch (e) {
        // Silent — synergy is optional UI
      }
    })();
    return () => { alive = false; };
  }, [category]);

  const activeMasters = useMemo(() => {
    return agents.filter(a => a.active === true && a.category === category && a.master_reference);
  }, [agents, category]);

  const mindsetActive = mindset?.active === true;

  if (!mindsetActive && activeMasters.length === 0) return null;

  if (compact) {
    return (
      <Link
        to="/studio/agents"
        data-testid="synergy-badge-compact"
        className="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-gradient-to-r from-violet-50 to-orange-50 dark:from-violet-500/15 dark:to-orange-500/15 border border-violet-200 dark:border-violet-500/30 text-[10px] font-semibold text-violet-700 dark:text-violet-300 hover:brightness-105 transition"
        title="Dream Team ativo — clique para ver/editar"
      >
        <Award size={10} />
        {mindsetActive && <Brain size={10} />}
        <span>Dream Team · {activeMasters.length}</span>
      </Link>
    );
  }

  return (
    <div
      data-testid="synergy-badge"
      className="rounded-xl border border-violet-200 dark:border-violet-500/30 bg-gradient-to-br from-violet-50/60 to-orange-50/40 dark:from-violet-500/10 dark:to-orange-500/10 px-4 py-3"
    >
      <div className="flex items-start gap-3">
        <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-violet-500/20 to-orange-500/20 flex items-center justify-center shrink-0">
          <Award size={14} className="text-violet-600 dark:text-violet-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[12px] font-bold text-gray-900 dark:text-white mb-1">
            Dream Team ativo neste projeto
          </p>
          {mindsetActive && (
            <p className="text-[11px] text-gray-700 dark:text-[#A3A3B2] leading-snug">
              <Brain size={10} className="inline mr-1 text-violet-600 dark:text-violet-400" />
              <strong>Mentalidade:</strong> {mindset.title}
            </p>
          )}
          {activeMasters.length > 0 && (
            <p className="text-[11px] text-gray-700 dark:text-[#A3A3B2] leading-snug mt-0.5">
              <Award size={10} className="inline mr-1 text-orange-600 dark:text-orange-400" />
              <strong>Mestres:</strong>{' '}
              {activeMasters.map(a => a.master_reference).join(' · ')}
            </p>
          )}
        </div>
        <Link
          to="/studio/agents"
          className="shrink-0 inline-flex items-center gap-0.5 text-[10px] font-semibold text-violet-600 dark:text-violet-400 hover:underline"
        >
          Editar <ChevronRight size={11} />
        </Link>
      </div>
    </div>
  );
}

export default SynergyBadge;
