import { useState, useRef, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import {
  Play, Pause, SkipBack, SkipForward, Maximize2, Minimize2,
  X, Volume2, VolumeX, Download, RefreshCw
} from 'lucide-react';
import { resolveImageUrl } from '../utils/resolveImageUrl';

const PANEL_DURATION = 6000; // 6s default per panel
const TRANSITION_DURATION = 800; // 0.8s fade

export function StoryboardPreview({ panels, lang, onClose }) {
  const [playing, setPlaying] = useState(false);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [progress, setProgress] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);
  const [showSubtitles, setShowSubtitles] = useState(true);
  const [transitioning, setTransitioning] = useState(false);
  const containerRef = useRef(null);
  const timerRef = useRef(null);
  const progressRef = useRef(null);
  const startTimeRef = useRef(null);

  const validPanels = panels.filter(p => p.image_url);
  const current = validPanels[currentIdx];
  const total = validPanels.length;

  // Animate progress bar
  const animateProgress = useCallback(() => {
    if (!startTimeRef.current) return;
    const elapsed = Date.now() - startTimeRef.current;
    const pct = Math.min((elapsed / PANEL_DURATION) * 100, 100);
    setProgress(pct);
    if (pct < 100) {
      progressRef.current = requestAnimationFrame(animateProgress);
    }
  }, []);

  // Auto-advance
  useEffect(() => {
    if (!playing) {
      if (progressRef.current) cancelAnimationFrame(progressRef.current);
      return;
    }

    startTimeRef.current = Date.now();
    progressRef.current = requestAnimationFrame(animateProgress);

    timerRef.current = setTimeout(() => {
      if (currentIdx < total - 1) {
        setTransitioning(true);
        setTimeout(() => {
          setCurrentIdx(prev => prev + 1);
          setProgress(0);
          setTransitioning(false);
        }, TRANSITION_DURATION);
      } else {
        setPlaying(false);
        setProgress(100);
      }
    }, PANEL_DURATION);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (progressRef.current) cancelAnimationFrame(progressRef.current);
    };
  }, [playing, currentIdx, total, animateProgress]);

  const goTo = (idx) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (progressRef.current) cancelAnimationFrame(progressRef.current);
    setTransitioning(true);
    setTimeout(() => {
      setCurrentIdx(Math.max(0, Math.min(idx, total - 1)));
      setProgress(0);
      setTransitioning(false);
      if (playing) {
        startTimeRef.current = Date.now();
        progressRef.current = requestAnimationFrame(animateProgress);
      }
    }, TRANSITION_DURATION / 2);
  };

  const togglePlay = () => {
    if (!playing && currentIdx >= total - 1 && progress >= 100) {
      setCurrentIdx(0);
      setProgress(0);
    }
    setPlaying(p => !p);
  };

  const toggleFullscreen = () => {
    if (!fullscreen) {
      containerRef.current?.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setFullscreen(f => !f);
  };

  // Keyboard controls
  useEffect(() => {
    const handler = (e) => {
      if (e.key === ' ' || e.key === 'k') { e.preventDefault(); togglePlay(); }
      if (e.key === 'ArrowRight' || e.key === 'l') goTo(currentIdx + 1);
      if (e.key === 'ArrowLeft' || e.key === 'j') goTo(currentIdx - 1);
      if (e.key === 'f') toggleFullscreen();
      if (e.key === 'Escape') { if (fullscreen) toggleFullscreen(); else onClose?.(); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [currentIdx, playing, fullscreen]);

  // Ken Burns animation class — alternate between effects
  const kenBurnsClass = currentIdx % 3 === 0
    ? 'animate-ken-burns-in'
    : currentIdx % 3 === 1
      ? 'animate-ken-burns-pan'
      : 'animate-ken-burns-out';

  if (!current) return null;

  return (
    <div ref={containerRef} data-testid="storyboard-preview"
      className={`relative bg-black overflow-hidden ${
        fullscreen ? 'fixed inset-0 z-[9999]' : 'rounded-xl border border-[#222]'
      }`}>

      {/* Image with Ken Burns */}
      <div className={`relative w-full ${fullscreen ? 'h-screen' : 'aspect-video'} overflow-hidden bg-black`}>
        <img
          key={current.scene_number}
          src={resolveImageUrl(current.image_url)}
          alt={current.title}
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-[800ms] ${
            transitioning ? 'opacity-0' : 'opacity-100'
          } ${kenBurnsClass}`}
        />

        {/* Gradient overlay for subtitles */}
        <div className="absolute inset-x-0 bottom-0 h-1/3 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />

        {/* Scene number badge */}
        <div className="absolute top-3 left-3 flex items-center gap-2">
          <span className="bg-black/70 backdrop-blur-sm text-[#C9A84C] text-[10px] font-bold px-2.5 py-1 rounded-full">
            {current.scene_number}/{total}
          </span>
          <span className="bg-black/50 backdrop-blur-sm text-white/80 text-[10px] px-2.5 py-1 rounded-full">
            {current.title}
          </span>
        </div>

        {/* Close button */}
        <button onClick={onClose} data-testid="close-preview-btn"
          className="absolute top-3 right-3 h-8 w-8 rounded-full bg-black/60 backdrop-blur-sm flex items-center justify-center text-white/70 hover:text-white transition">
          <X size={14} />
        </button>

        {/* Subtitles */}
        {showSubtitles && current.dialogue && (
          <div className="absolute bottom-16 inset-x-0 flex justify-center px-4">
            <div className={`max-w-[80%] bg-black/70 backdrop-blur-sm rounded-xl px-5 py-3 transition-all duration-500 ${
              transitioning ? 'opacity-0 translate-y-4' : 'opacity-100 translate-y-0'
            }`}>
              <p className="text-white text-sm sm:text-base text-center leading-relaxed font-medium">
                {current.dialogue}
              </p>
              {current.characters_in_scene?.length > 0 && (
                <p className="text-[#C9A84C] text-[10px] text-center mt-1 opacity-70">
                  {current.characters_in_scene.join(' & ')}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Click to play/pause (center area) */}
        <div className="absolute inset-0 flex items-center justify-center cursor-pointer group"
          onClick={togglePlay}>
          <div className={`h-16 w-16 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center transition-all ${
            playing ? 'opacity-0 group-hover:opacity-100 scale-90 group-hover:scale-100' : 'opacity-100 scale-100'
          }`}>
            {playing ? <Pause size={24} className="text-white" /> : <Play size={24} className="text-white ml-1" />}
          </div>
        </div>
      </div>

      {/* Controls bar */}
      <div className="bg-[#0A0A0A] border-t border-[#1A1A1A] px-3 py-2 space-y-1.5">
        {/* Progress bar */}
        <div className="flex items-center gap-2">
          {/* Mini panel dots */}
          <div className="flex-1 flex items-center gap-0.5">
            {validPanels.map((p, i) => (
              <button key={p.scene_number} onClick={() => goTo(i)}
                data-testid={`preview-dot-${p.scene_number}`}
                className={`flex-1 h-1 rounded-full transition-all cursor-pointer ${
                  i < currentIdx ? 'bg-[#C9A84C]'
                    : i === currentIdx ? 'bg-[#C9A84C]/70'
                    : 'bg-[#333] hover:bg-[#444]'
                }`}>
                {i === currentIdx && (
                  <div className="h-full rounded-full bg-[#C9A84C] transition-all"
                    style={{ width: `${progress}%` }} />
                )}
              </button>
            ))}
          </div>
          <span className="text-[9px] text-[#666] font-mono w-10 text-right">
            {currentIdx + 1}/{total}
          </span>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button onClick={() => goTo(currentIdx - 1)} disabled={currentIdx === 0}
              data-testid="preview-prev-btn"
              className="h-7 w-7 rounded-full bg-[#111] border border-[#222] flex items-center justify-center text-[#999] hover:text-white transition disabled:opacity-30">
              <SkipBack size={12} />
            </button>
            <button onClick={togglePlay} data-testid="preview-play-btn"
              className="h-9 w-9 rounded-full bg-[#C9A84C]/10 border border-[#C9A84C]/30 flex items-center justify-center text-[#C9A84C] hover:bg-[#C9A84C]/20 transition">
              {playing ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
            </button>
            <button onClick={() => goTo(currentIdx + 1)} disabled={currentIdx >= total - 1}
              data-testid="preview-next-btn"
              className="h-7 w-7 rounded-full bg-[#111] border border-[#222] flex items-center justify-center text-[#999] hover:text-white transition disabled:opacity-30">
              <SkipForward size={12} />
            </button>
          </div>

          <div className="flex items-center gap-1">
            <button onClick={() => setShowSubtitles(s => !s)} data-testid="toggle-subtitles-btn"
              className={`h-7 px-2 rounded-full text-[9px] font-medium flex items-center gap-1 transition ${
                showSubtitles
                  ? 'bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[#C9A84C]'
                  : 'bg-[#111] border border-[#222] text-[#666]'
              }`}>
              {showSubtitles ? <Volume2 size={10} /> : <VolumeX size={10} />}
              {lang === 'pt' ? 'Legendas' : 'Subs'}
            </button>
            <button onClick={toggleFullscreen} data-testid="preview-fullscreen-btn"
              className="h-7 w-7 rounded-full bg-[#111] border border-[#222] flex items-center justify-center text-[#999] hover:text-white transition">
              {fullscreen ? <Minimize2 size={12} /> : <Maximize2 size={12} />}
            </button>
          </div>
        </div>
      </div>

      {/* Ken Burns CSS animations */}
      <style>{`
        @keyframes kenBurnsIn {
          from { transform: scale(1) translate(0, 0); }
          to { transform: scale(1.15) translate(-1%, -1%); }
        }
        @keyframes kenBurnsPan {
          from { transform: scale(1.1) translate(-2%, 0); }
          to { transform: scale(1.1) translate(2%, 0); }
        }
        @keyframes kenBurnsOut {
          from { transform: scale(1.15) translate(1%, 1%); }
          to { transform: scale(1) translate(0, 0); }
        }
        .animate-ken-burns-in { animation: kenBurnsIn ${PANEL_DURATION}ms ease-out forwards; }
        .animate-ken-burns-pan { animation: kenBurnsPan ${PANEL_DURATION}ms ease-in-out forwards; }
        .animate-ken-burns-out { animation: kenBurnsOut ${PANEL_DURATION}ms ease-out forwards; }
      `}</style>
    </div>
  );
}
