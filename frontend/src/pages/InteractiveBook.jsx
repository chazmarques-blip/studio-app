import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { ChevronLeft, ChevronRight, Volume2, VolumeX, BookOpen, X } from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function InteractiveBook() {
  const { projectId } = useParams();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || localStorage.getItem('studiox_token');

  const [bookData, setBookData] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [autoNarrate, setAutoNarrate] = useState(true);
  const [loadingAudio, setLoadingAudio] = useState(false);
  const [isFlipping, setIsFlipping] = useState(false);
  const [flipDir, setFlipDir] = useState('next');
  const [error, setError] = useState(null);
  const audioRef = useRef(null);
  const touchStartX = useRef(0);
  const containerRef = useRef(null);

  useEffect(() => {
    loadBook();
  }, [projectId]);

  const loadBook = async () => {
    try {
      const r = await axios.get(`${API}/api/studio/projects/${projectId}/book/interactive-data`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setBookData(r.data);
    } catch (e) {
      setError('Erro ao carregar livro');
    }
  };

  const resolveUrl = (url) => {
    if (!url) return '';
    if (url.startsWith('http')) return url;
    const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
    return `${supabaseUrl}/storage/v1/object/public${url}`;
  };

  const goToPage = useCallback((newPage) => {
    if (!bookData || isFlipping) return;
    if (newPage < 0 || newPage >= bookData.pages.length) return;
    const dir = newPage > currentPage ? 'next' : 'prev';
    setFlipDir(dir);
    setIsFlipping(true);
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    setIsPlaying(false);

    setTimeout(() => {
      setCurrentPage(newPage);
      setIsFlipping(false);
    }, 400);
  }, [bookData, currentPage, isFlipping]);

  useEffect(() => {
    if (autoNarrate && bookData && !isFlipping) {
      const page = bookData.pages[currentPage];
      if (page?.narration) narratePage(page.narration);
    }
  }, [currentPage, autoNarrate, isFlipping]);

  const narratePage = async (text) => {
    if (!text || !token) return;
    setLoadingAudio(true);
    try {
      const r = await axios.post(
        `${API}/api/studio/projects/${projectId}/book/tts-page`,
        { text, voice_id: 'onwK4e9ZLuTAKqWW03F9' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (r.data.audio_url) {
        const url = resolveUrl(r.data.audio_url);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onplay = () => setIsPlaying(true);
        audio.onended = () => { setIsPlaying(false); audioRef.current = null; };
        audio.play().catch(() => {});
      }
    } catch {
    } finally {
      setLoadingAudio(false);
    }
  };

  const toggleNarration = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }
    setAutoNarrate(!autoNarrate);
  };

  // Keyboard navigation
  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ') goToPage(currentPage + 1);
      if (e.key === 'ArrowLeft') goToPage(currentPage - 1);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [goToPage, currentPage]);

  // Touch/swipe
  const onTouchStart = (e) => { touchStartX.current = e.touches[0].clientX; };
  const onTouchEnd = (e) => {
    const delta = touchStartX.current - e.changedTouches[0].clientX;
    if (Math.abs(delta) > 60) {
      delta > 0 ? goToPage(currentPage + 1) : goToPage(currentPage - 1);
    }
  };

  if (error) return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center text-red-400">{error}</div>
  );
  if (!bookData) return (
    <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
      <BookOpen className="text-[#8B5CF6] animate-pulse" size={48} />
    </div>
  );

  const page = bookData.pages[currentPage];
  const isFirst = currentPage === 0;
  const isLast = currentPage === bookData.pages.length - 1;
  const progress = ((currentPage + 1) / bookData.pages.length) * 100;

  return (
    <div
      ref={containerRef}
      className="min-h-screen bg-[#0A0A0A] flex flex-col select-none overflow-hidden"
      onTouchStart={onTouchStart}
      onTouchEnd={onTouchEnd}
      data-testid="interactive-book"
    >
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#0D0D0D] border-b border-[#1A1A1A] z-20">
        <span className="text-xs text-[#8B5CF6] font-semibold truncate max-w-[60%]">{bookData.title}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleNarration}
            data-testid="toggle-narration"
            className={`h-8 w-8 rounded-full flex items-center justify-center transition ${
              autoNarrate ? 'bg-[#8B5CF6]/20 text-[#8B5CF6]' : 'bg-[#1A1A1A] text-[#555]'
            }`}
          >
            {autoNarrate ? <Volume2 size={16} /> : <VolumeX size={16} />}
          </button>
          <span className="text-[10px] text-[#555]">{currentPage + 1}/{bookData.pages.length}</span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-[2px] bg-[#1A1A1A]">
        <div
          className="h-full bg-[#8B5CF6] transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Page content */}
      <div className="flex-1 relative flex items-center justify-center p-2 md:p-4">
        {/* Page flip animation wrapper */}
        <div className={`w-full max-w-4xl aspect-[4/3] relative rounded-xl overflow-hidden shadow-2xl transition-all duration-400 ${
          isFlipping ? (flipDir === 'next'
            ? 'animate-[flipOut_0.4s_ease-in-out]'
            : 'animate-[flipIn_0.4s_ease-in-out]')
          : 'animate-[fadeIn_0.3s_ease-out]'
        }`}>
          {page.type === 'cover' ? (
            /* Cover page */
            <div className="w-full h-full relative bg-black" data-testid="book-cover-page">
              {page.image_url && (
                <img src={resolveUrl(page.image_url)} alt="Cover"
                  className="w-full h-full object-cover" />
              )}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-6 md:p-10 text-center">
                <h1 className="text-2xl md:text-4xl lg:text-5xl font-bold text-white mb-2 leading-tight"
                    style={{ textShadow: '2px 2px 8px rgba(0,0,0,0.8)' }}>
                  {page.title}
                </h1>
                <p className="text-sm md:text-base text-[#8B5CF6]">{page.subtitle}</p>
              </div>
            </div>
          ) : page.type === 'end' ? (
            /* End page */
            <div className="w-full h-full relative bg-black" data-testid="book-end-page">
              {page.image_url && (
                <img src={resolveUrl(page.image_url)} alt="End"
                  className="w-full h-full object-cover opacity-40" />
              )}
              <div className="absolute inset-0 flex items-center justify-center">
                <h1 className="text-5xl md:text-7xl font-bold text-[#8B5CF6]"
                    style={{ textShadow: '2px 2px 12px rgba(0,0,0,0.9)' }}>
                  {page.title}
                </h1>
              </div>
            </div>
          ) : (
            /* Story page */
            <div className="w-full h-full flex flex-col bg-[#0A0A0A]" data-testid={`book-page-${page.page_number}`}>
              {/* Illustration — takes most space */}
              <div className="flex-1 relative overflow-hidden">
                {page.image_url && (
                  <img
                    src={resolveUrl(page.image_url)}
                    alt={page.title}
                    className="w-full h-full object-cover"
                  />
                )}
                {/* Subtle label */}
                <span className="absolute top-2 right-2 text-[9px] text-white/40 bg-black/40 px-2 py-0.5 rounded-full">
                  {page.label}
                </span>
              </div>
              {/* Narration text strip */}
              <div className="px-4 py-3 md:px-6 md:py-4 bg-[#0D0D0D] border-t border-[#1A1A1A]">
                <p className="text-xs md:text-sm text-[#ccc] leading-relaxed text-center italic">
                  {page.narration}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Nav arrows — desktop */}
        {!isFirst && (
          <button
            onClick={() => goToPage(currentPage - 1)}
            data-testid="prev-page-btn"
            className="hidden md:flex absolute left-2 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full bg-black/50 backdrop-blur items-center justify-center text-white/60 hover:text-white hover:bg-black/70 transition"
          >
            <ChevronLeft size={24} />
          </button>
        )}
        {!isLast && (
          <button
            onClick={() => goToPage(currentPage + 1)}
            data-testid="next-page-btn"
            className="hidden md:flex absolute right-2 top-1/2 -translate-y-1/2 h-12 w-12 rounded-full bg-black/50 backdrop-blur items-center justify-center text-white/60 hover:text-white hover:bg-black/70 transition"
          >
            <ChevronRight size={24} />
          </button>
        )}

        {/* Audio indicator */}
        {(isPlaying || loadingAudio) && (
          <div className="absolute bottom-4 right-4 flex items-center gap-1.5 bg-black/70 backdrop-blur px-3 py-1.5 rounded-full">
            {loadingAudio ? (
              <div className="w-3 h-3 border-2 border-[#8B5CF6] border-t-transparent rounded-full animate-spin" />
            ) : (
              <div className="flex items-center gap-0.5">
                {[1,2,3].map(i => (
                  <div key={i} className="w-1 bg-[#8B5CF6] rounded-full animate-pulse"
                    style={{ height: `${8 + i * 3}px`, animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            )}
            <span className="text-[9px] text-[#8B5CF6]">
              {loadingAudio ? 'Carregando...' : 'Narrando'}
            </span>
          </div>
        )}
      </div>

      {/* Bottom tap zones for mobile */}
      <div className="md:hidden flex">
        <button onClick={() => goToPage(currentPage - 1)} disabled={isFirst}
          className="flex-1 py-3 text-center text-[10px] text-[#555] disabled:opacity-20">
          <ChevronLeft size={16} className="inline" /> Anterior
        </button>
        <button onClick={() => goToPage(currentPage + 1)} disabled={isLast}
          className="flex-1 py-3 text-center text-[10px] text-[#8B5CF6] disabled:opacity-20">
          Proximo <ChevronRight size={16} className="inline" />
        </button>
      </div>

      {/* CSS animations */}
      <style>{`
        @keyframes flipOut {
          0% { transform: perspective(1200px) rotateY(0); opacity: 1; }
          100% { transform: perspective(1200px) rotateY(-90deg); opacity: 0; }
        }
        @keyframes flipIn {
          0% { transform: perspective(1200px) rotateY(90deg); opacity: 0; }
          100% { transform: perspective(1200px) rotateY(0); opacity: 1; }
        }
        @keyframes fadeIn {
          from { opacity: 0.3; transform: scale(0.98); }
          to { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
