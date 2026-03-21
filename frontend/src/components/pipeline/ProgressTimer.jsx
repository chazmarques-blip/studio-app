import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';

function ProgressTimer({ startedAt, estimatedSec, color }) {
  const { t } = useTranslation();
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!startedAt) return;
    const start = new Date(startedAt).getTime();
    const tick = () => setElapsed(Math.floor((Date.now() - start) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);
  const pct = Math.min((elapsed / estimatedSec) * 100, 95);
  const remaining = Math.max(estimatedSec - elapsed, 0);
  const fmt = remaining > 60 ? `~${Math.ceil(remaining / 60)}min` : `~${remaining}s`;
  return (
    <div className="mt-1.5 px-1">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-[8px] text-[#999]">{elapsed}s {t('studio.elapsed')}</span>
        <span className="text-[8px] text-[#999]">{fmt} {t('studio.remaining')}</span>
      </div>
      <div className="h-1 rounded-full bg-[#1A1A1A] overflow-hidden">
        <div className="h-full rounded-full transition-all duration-1000 ease-linear" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
    </div>
  );
}

/* ── Image Lightbox ── */

export { ProgressTimer };
