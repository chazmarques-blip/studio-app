import { useState, useRef, useEffect, useCallback } from 'react';
import { Calendar, ChevronUp, ChevronDown } from 'lucide-react';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const ITEM_H = 28;

function getDaysInMonth(month, year) {
  if (!month || !year) return 31;
  return new Date(year, month, 0).getDate();
}

function ScrollColumn({ items, value, onChange, testId }) {
  const ref = useRef(null);
  const isScrolling = useRef(false);

  useEffect(() => {
    if (ref.current && !isScrolling.current) {
      const idx = items.indexOf(value);
      if (idx >= 0) ref.current.scrollTop = idx * ITEM_H;
    }
  }, [value, items]);

  const handleScroll = useCallback(() => {
    if (!ref.current) return;
    isScrolling.current = true;
    clearTimeout(ref.current._t);
    ref.current._t = setTimeout(() => {
      const idx = Math.round(ref.current.scrollTop / ITEM_H);
      const clamped = Math.max(0, Math.min(idx, items.length - 1));
      ref.current.scrollTo({ top: clamped * ITEM_H, behavior: 'smooth' });
      if (items[clamped] !== value) onChange(items[clamped]);
      isScrolling.current = false;
    }, 80);
  }, [items, value, onChange]);

  const nudge = (dir) => {
    const idx = items.indexOf(value);
    const next = Math.max(0, Math.min(idx + dir, items.length - 1));
    onChange(items[next]);
  };

  return (
    <div className="flex flex-col items-center gap-0.5" data-testid={testId}>
      <button type="button" onClick={() => nudge(-1)} className="text-[#555] hover:text-[#C9A84C] transition p-0.5">
        <ChevronUp size={12} />
      </button>
      <div
        ref={ref}
        onScroll={handleScroll}
        className="h-[84px] w-full overflow-y-auto scrollbar-hide snap-y snap-mandatory"
        style={{ scrollSnapType: 'y mandatory' }}
      >
        {items.map((item) => (
          <div
            key={item}
            className={`flex items-center justify-center snap-center cursor-pointer transition-all ${
              item === value
                ? 'text-white font-semibold text-[13px]'
                : 'text-[#555] text-[11px] hover:text-[#888]'
            }`}
            style={{ height: ITEM_H, scrollSnapAlign: 'center' }}
            onClick={() => onChange(item)}
          >
            {item}
          </div>
        ))}
      </div>
      <button type="button" onClick={() => nudge(1)} className="text-[#555] hover:text-[#C9A84C] transition p-0.5">
        <ChevronDown size={12} />
      </button>
    </div>
  );
}

export function DateScrollPicker({ value, onChange, compact }) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(null);
  const [day, setDay] = useState(null);
  const [year, setYear] = useState(null);
  const wrapRef = useRef(null);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 80 }, (_, i) => currentYear - i);
  const maxDay = getDaysInMonth(month, year);
  const days = Array.from({ length: maxDay }, (_, i) => i + 1);

  useEffect(() => {
    if (value) {
      const [y, m, d] = value.split('-').map(Number);
      if (y && m && d) { setYear(y); setMonth(m); setDay(d); }
    }
  }, [value]);

  useEffect(() => {
    if (day && day > maxDay) setDay(maxDay);
  }, [month, year, day, maxDay]);

  useEffect(() => {
    const handleClick = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleConfirm = () => {
    if (month && day && year) {
      const iso = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      onChange(iso);
    }
    setOpen(false);
  };

  const displayText = (month && day && year)
    ? `${MONTHS[month - 1]} ${day}, ${year}`
    : '';

  const inputCls = compact
    ? 'w-full rounded-lg border border-[#2A2A2A] bg-[#1A1A1A] px-3 py-2 text-sm text-white outline-none transition focus:border-[#C9A84C]/50 cursor-pointer'
    : 'w-full rounded-lg border border-[#222] bg-[#111] px-3 py-1.5 text-[12px] text-white placeholder-[#555] outline-none transition focus:border-[#C9A84C]/40 focus:ring-1 focus:ring-[#C9A84C]/20 cursor-pointer';

  return (
    <div className="relative" ref={wrapRef}>
      <div
        data-testid="date-picker-trigger"
        className={`${inputCls} flex items-center gap-2`}
        onClick={() => setOpen(!open)}
      >
        <Calendar size={12} className="text-[#555] shrink-0" />
        <span className={displayText ? 'text-white' : 'text-[#555]'}>
          {displayText || 'Select date'}
        </span>
      </div>

      {open && (
        <div
          data-testid="date-picker-dropdown"
          className="absolute top-full left-0 mt-1 z-50 w-full rounded-xl border border-[#C9A84C]/20 bg-[#111] shadow-2xl shadow-black/40 p-3 animate-in fade-in slide-in-from-top-1 duration-150"
        >
          <div className="grid grid-cols-3 gap-1 text-center mb-1">
            <span className="text-[8px] font-semibold text-[#666] uppercase tracking-wider">Month</span>
            <span className="text-[8px] font-semibold text-[#666] uppercase tracking-wider">Day</span>
            <span className="text-[8px] font-semibold text-[#666] uppercase tracking-wider">Year</span>
          </div>

          <div className="relative">
            <div className="absolute left-0 right-0 top-[28px] h-[28px] rounded-md bg-[#C9A84C]/8 border border-[#C9A84C]/15 pointer-events-none z-0" />
            <div className="grid grid-cols-3 gap-1 relative z-10">
              <ScrollColumn
                items={MONTHS.map((_, i) => i + 1)}
                value={month}
                onChange={setMonth}
                testId="date-scroll-month"
              />
              <ScrollColumn
                items={days}
                value={day}
                onChange={setDay}
                testId="date-scroll-day"
              />
              <ScrollColumn
                items={years}
                value={year}
                onChange={setYear}
                testId="date-scroll-year"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-1 text-center mt-0.5 mb-2">
            <span className="text-[9px] text-[#C9A84C] font-medium">{month ? MONTHS[month - 1] : '-'}</span>
            <span className="text-[9px] text-[#C9A84C] font-medium">{day || '-'}</span>
            <span className="text-[9px] text-[#C9A84C] font-medium">{year || '-'}</span>
          </div>

          <button
            type="button"
            data-testid="date-picker-confirm"
            onClick={handleConfirm}
            disabled={!month || !day || !year}
            className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#A88B3D] py-1.5 text-[10px] font-semibold text-[#0A0A0A] transition hover:opacity-90 disabled:opacity-30"
          >
            Confirm
          </button>
        </div>
      )}
    </div>
  );
}
