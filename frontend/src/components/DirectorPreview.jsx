import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Eye, RefreshCw, ChevronLeft, ChevronRight, Check, X, AlertTriangle, Star, Sparkles, Film, BookOpen, Zap, ChevronDown } from 'lucide-react';
import { getErrorMsg } from '../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_COLORS = {
  EXCELLENT: { text: 'text-emerald-500', border: 'border-emerald-500/20', bg: 'bg-emerald-500/5' },
  GOOD: { text: 'text-blue-500', border: 'border-blue-500/20', bg: 'bg-blue-500/5' },
  NEEDS_WORK: { text: 'text-amber-500', border: 'border-amber-500/20', bg: 'bg-amber-500/5' },
  CRITICAL: { text: 'text-red-500', border: 'border-red-500/20', bg: 'bg-red-500/5' },
};

const STATUS_LABELS = {
  EXCELLENT: { pt: 'EXCELENTE', en: 'EXCELLENT' },
  GOOD: { pt: 'BOM', en: 'GOOD' },
  NEEDS_WORK: { pt: 'PRECISA MELHORAR', en: 'NEEDS WORK' },
  CRITICAL: { pt: 'CRÍTICO', en: 'CRITICAL' },
};

const STATUS_ICONS = {
  EXCELLENT: <Star size={10} className="text-emerald-400" />,
  GOOD: <Check size={10} className="text-sky-400" />,
  NEEDS_WORK: <AlertTriangle size={10} className="text-amber-400" />,
  CRITICAL: <X size={10} className="text-red-400" />,
};

export function DirectorPreview({ projectId, lang, scenes, onApprove, onBack }) {
  const [review, setReview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [expandedScene, setExpandedScene] = useState(null);
  const [progress, setProgress] = useState(null);

  // Load existing review
  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/studio/projects/${projectId}/director/review`);
        if (res.data.has_review) setReview(res.data.review);
      } catch { /* no review yet */ }
      setLoading(false);
    };
    load();
  }, [projectId]);
  
  // Poll progress during review/re-evaluation WITH WATCHDOG
  useEffect(() => {
    if (!applying && !reviewing) {
      setProgress(null);
      return;
    }
    
    let lastProgressUpdate = Date.now();
    let watchdogTriggered = false;
    
    const pollInterval = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/studio/projects/${projectId}/director/progress`);
        
        if (res.data.in_progress) {
          const currentProgress = res.data.progress;
          setProgress(currentProgress);
          
          // Update watchdog timestamp if progress changed
          const currentBatch = currentProgress?.current_batch || 0;
          const scenesProcessed = currentProgress?.scenes_processed || 0;
          
          // Check if progress actually moved
          if (currentBatch !== (window.lastBatch || 0) || scenesProcessed !== (window.lastScenes || 0)) {
            lastProgressUpdate = Date.now();
            window.lastBatch = currentBatch;
            window.lastScenes = scenesProcessed;
            watchdogTriggered = false;
          }
          
          // WATCHDOG: If no progress for 90 seconds, auto-resume
          const timeSinceUpdate = (Date.now() - lastProgressUpdate) / 1000;
          if (timeSinceUpdate > 90 && !watchdogTriggered) {
            watchdogTriggered = true;
            console.warn('🐕 WATCHDOG: Progress stuck for 90s, auto-resuming...');
            toast.warning(
              lang === 'pt' 
                ? '⚠️ Revisão travada detectada. Retomando automaticamente...' 
                : '⚠️ Stuck review detected. Auto-resuming...'
            );
            
            // Call resume endpoint
            try {
              const resumeRes = await axios.post(`${API}/studio/projects/${projectId}/director/resume`);
              if (resumeRes.data.scene_reviews || resumeRes.data.verdict) {
                // Resume completed successfully!
                setReview(resumeRes.data);
                setReviewing(false);
                setApplying(false);
                toast.success(
                  lang === 'pt' 
                    ? '✅ Revisão retomada e concluída!' 
                    : '✅ Review resumed and completed!'
                );
              }
            } catch (resumeErr) {
              console.error('Resume failed:', resumeErr);
              // Will retry on next watchdog cycle
            }
          }
        } else {
          setProgress(null);
          
          // Check if review completed
          try {
            const reviewRes = await axios.get(`${API}/studio/projects/${projectId}/director/review`);
            if (reviewRes.data.has_review && reviewing) {
              setReview(reviewRes.data.review);
              setReviewing(false);
              setApplying(false);
              toast.success(lang === 'pt' ? 'Revisão do Director concluída!' : 'Director review complete!');
            }
          } catch {
            // No review yet
          }
        }
      } catch (err) {
        console.error('Poll progress failed:', err);
      }
    }, 5000); // Poll every 5 seconds (increased from 2s to reduce server load)
    
    return () => {
      clearInterval(pollInterval);
      window.lastBatch = undefined;
      window.lastScenes = undefined;
    };
  }, [applying, reviewing, projectId, lang]);

  const runReview = async () => {
    setReviewing(true);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/director/review`, { focus: 'full' }, { timeout: 120000 });
      setReview(res.data);
      toast.success(lang === 'pt' ? 'Revisão do Director concluída!' : 'Director review complete!');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Review failed'));
    } finally {
      setReviewing(false);
    }
  };

  const resumeReview = async () => {
    setReviewing(true);
    toast.info(lang === 'pt' ? '🔄 Retomando revisão travada...' : '🔄 Resuming stuck review...');
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/director/resume`);
      setReview(res.data);
      toast.success(lang === 'pt' ? '✅ Revisão retomada e concluída!' : '✅ Review resumed and completed!');
    } catch (err) {
      toast.error(getErrorMsg(err, 'Resume failed'));
    } finally {
      setReviewing(false);
    }
  };

  const applyFixes = async () => {
    setApplying(true);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/director/apply-fixes`, { re_evaluate: true });
      const applied = res.data.applied;
      
      toast.success(lang === 'pt'
        ? `${applied} cena(s) corrigida(s) pelo Director!`
        : `${applied} scene(s) fixed by Director!`);
      
      // If re-evaluation was performed, update the review
      if (res.data.re_evaluated && res.data.new_review) {
        const newReview = res.data.new_review;
        setReview(newReview);
        
        const newScore = newReview.overall_score || 0;
        const needsWork = (newReview.scene_reviews || []).filter(s => s.score < 80).length;
        
        if (newScore >= 90 && needsWork === 0) {
          toast.success(lang === 'pt' 
            ? `🎉 EXCELENTE! Score: ${newScore}% - Aprovado para produção!`
            : `🎉 EXCELLENT! Score: ${newScore}% - Approved for production!`, { duration: 5000 });
        } else if (newScore >= 80 && needsWork === 0) {
          toast.success(lang === 'pt'
            ? `✅ BOM! Score: ${newScore}% - Pode prosseguir (pequenos ajustes recomendados)`
            : `✅ GOOD! Score: ${newScore}% - Can proceed (minor polishing recommended)`, { duration: 5000 });
        } else {
          toast.warning(lang === 'pt'
            ? `⚠️ Score: ${newScore}% - ${needsWork} cena(s) ainda abaixo de 80%. Clique "Aplicar Correções" novamente.`
            : `⚠️ Score: ${newScore}% - ${needsWork} scene(s) still below 80%. Click "Apply Fixes" again.`, { duration: 7000 });
        }
      } else {
        // Fallback if no re-evaluation
        setTimeout(() => {
          toast.info(lang === 'pt' 
            ? 'Correções aplicadas! Volte aos Diálogos para ver as mudanças ou clique "Re-analisar" para verificar o novo score.' 
            : 'Fixes applied! Go back to Dialogues to see changes or click "Re-analyze" to check new score.');
        }, 1000);
      }
      
    } catch (err) {
      toast.error(getErrorMsg(err, 'Apply fixes failed'));
    } finally {
      setApplying(false);
    }
  };

  const score = review?.overall_score || 0;
  const scoreColor = score >= 80 ? 'text-emerald-400' : score >= 60 ? 'text-amber-400' : 'text-red-400';
  const isApproved = review?.verdict === 'APPROVED';
  const sceneReviews = review?.scene_reviews || [];
  const needsWork = sceneReviews.filter(s => s.status === 'NEEDS_WORK' || s.status === 'CRITICAL').length;
  const hasRevisions = sceneReviews.some(s => s.revised_dialogue || s.revised_narration || s.revised_description);

  if (loading) return (
    <div className="flex items-center justify-center py-12">
      <RefreshCw size={16} className="animate-spin text-orange-600" />
    </div>
  );

  return (
    <div className="glass-card p-4 space-y-4" data-testid="director-preview">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Film size={16} className="text-orange-600" />
          <h3 className="text-sm font-bold text-gray-900">
            {lang === 'pt' ? "Director's Preview" : "Director's Preview"}
          </h3>
          <span className="text-[10px] text-gray-500 font-normal">
            {lang === 'pt' ? 'Revisão profissional antes do Storyboard' : 'Professional review before Storyboard'}
          </span>
        </div>
        <div className="flex gap-2">
          {progress && progress.status && progress.status !== 'complete' && !reviewing && (
            <button onClick={resumeReview}
              className="text-xs px-3 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/5 text-amber-600 hover:bg-amber-500/15 transition flex items-center gap-1.5">
              <RefreshCw size={11} />
              {lang === 'pt' ? 'Retomar' : 'Resume'}
            </button>
          )}
          <button onClick={runReview} disabled={reviewing}
            data-testid="run-director-review-btn"
            className="text-xs px-3 py-1.5 rounded-lg border border-orange-500/40 bg-orange-500/5 text-orange-600 hover:bg-orange-500/15 transition disabled:opacity-30 flex items-center gap-1.5">
            {reviewing ? <RefreshCw size={11} className="animate-spin" /> : <Eye size={11} />}
            {reviewing
              ? (lang === 'pt' ? 'Director analisando...' : 'Director analyzing...')
              : (lang === 'pt' ? (review ? 'Re-analisar' : 'Iniciar Revisão') : (review ? 'Re-analyze' : 'Start Review'))
            }
          </button>
        </div>
      </div>

      {/* Reviewing state with real-time progress */}
      {(reviewing || applying) && progress && (
        <div className="border border-orange-500/20 rounded-xl bg-orange-500/5 p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <RefreshCw size={16} className="animate-spin text-orange-600" />
              <p className="text-xs text-orange-600 font-bold">
                {lang === 'pt' 
                  ? (applying ? 'Re-avaliando Qualidade...' : 'Director Analisando...')
                  : (applying ? 'Re-evaluating Quality...' : 'Director Analyzing...')}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm font-bold text-orange-600">{Math.round(progress.current_score || 0)}%</p>
              <p className="text-[9px] text-gray-500">score médio</p>
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="space-y-1">
            <div className="flex justify-between text-[10px] text-gray-600">
              <span>
                {lang === 'pt' ? 'Progresso' : 'Progress'}: Batch {progress.current_batch}/{progress.total_batches}
              </span>
              <span>{progress.scenes_processed}/{progress.total_scenes} cenas</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-orange-500 to-orange-600 transition-all duration-500"
                style={{ width: `${(progress.scenes_processed / progress.total_scenes) * 100}%` }}
              />
            </div>
          </div>
          
          {/* Batch scores */}
          {progress.batch_scores && progress.batch_scores.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {progress.batch_scores.map((bs, i) => (
                <div key={i} className={`px-2 py-0.5 rounded text-[9px] font-medium ${
                  bs.score >= 90 ? 'bg-emerald-500/20 text-emerald-600' :
                  bs.score >= 80 ? 'bg-blue-500/20 text-blue-600' :
                  bs.score >= 60 ? 'bg-amber-500/20 text-amber-600' :
                  'bg-red-500/20 text-red-600'
                }`}>
                  Batch {bs.batch}: {Math.round(bs.score)}%
                </div>
              ))}
            </div>
          )}
          
          <p className="text-[10px] text-gray-500 text-center">
            {lang === 'pt' 
              ? 'Equipe de diretores trabalhando em paralelo...'
              : 'Team of directors working in parallel...'}
          </p>
        </div>
      )}
      
      {/* Reviewing state (fallback when no progress) */}
      {(reviewing || applying) && !progress && (
        <div className="text-center py-8 border border-orange-500/20 rounded-xl bg-orange-500/5">
          <RefreshCw size={20} className="animate-spin text-orange-600 mx-auto mb-2" />
          <p className="text-xs text-orange-600 font-medium">
            {lang === 'pt'
              ? 'O Director está analisando cada cena com os padrões dos melhores cineastas do mundo...'
              : 'The Director is analyzing each scene with world-class filmmaking standards...'}
          </p>
          <p className="text-[10px] text-gray-600 mt-1">Spielberg + Miyazaki + Pixar + Nolan</p>
        </div>
      )}

      {/* No review yet */}
      {!review && !reviewing && (
        <div className="text-center py-8 border border-dashed border-[#333] rounded-xl">
          <Film size={24} className="text-[#333] mx-auto mb-2" />
          <p className="text-xs text-gray-500">
            {lang === 'pt'
              ? 'Clique "Iniciar Revisão" para o Director IA analisar todo o projecto'
              : 'Click "Start Review" for the AI Director to analyze the entire project'}
          </p>
          <p className="text-[10px] text-[#444] mt-1">
            {lang === 'pt'
              ? 'Diálogos, ritmo, arco emocional, consistência e storytelling visual'
              : 'Dialogues, pacing, emotional arc, consistency and visual storytelling'}
          </p>
        </div>
      )}

      {/* Compact Review Summary */}
      {review && !reviewing && !applying && (
        <div className="border-l-4 border-orange-500 bg-orange-500/5 px-3 py-2 rounded-r-md flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className={`text-xl font-bold ${scoreColor}`}>{score}</span>
            <div className="text-[10px]">
              <p className={`font-bold ${isApproved ? 'text-emerald-500' : 'text-amber-500'}`}>
                {isApproved ? (lang === 'pt' ? 'APROVADO' : 'APPROVED') : (lang === 'pt' ? 'REVISÃO NECESSÁRIA' : 'NEEDS REVISION')}
              </p>
              <p className="text-gray-600">
                {needsWork > 0 ? `${needsWork} ${lang === 'pt' ? 'cenas < 80%' : 'scenes < 80%'}` : (lang === 'pt' ? 'Tudo pronto!' : 'All ready!')}
              </p>
            </div>
          </div>
          
          {hasRevisions && (
            <button onClick={applyFixes} disabled={applying}
              className="text-[10px] px-2.5 py-1.5 rounded-md bg-orange-500 text-black font-bold hover:bg-[#EA580C] transition disabled:opacity-50 flex items-center gap-1">
              <Zap size={9} />
              {lang === 'pt' ? 'Aplicar Correções' : 'Apply Fixes'}
            </button>
          )}
        </div>
      )}

      {/* Scene-by-Scene Review with Progress */}
      {review && sceneReviews.length > 0 && (
        <div className="space-y-1">
          <p className="text-[10px] font-semibold text-gray-700 mb-2 flex items-center gap-1.5">
            <Film size={10} className="text-orange-600" />
            {lang === 'pt' ? 'Cenas' : 'Scenes'} ({sceneReviews.length})
          </p>
          <div className="space-y-1 max-h-[400px] overflow-y-auto hide-scrollbar">
            {sceneReviews.map(sr => {
              const isExpanded = expandedScene === sr.scene_number;
              const statusClass = STATUS_COLORS[sr.status] || STATUS_COLORS.GOOD;
              
              // Check if this scene is being processed (from progress)
              const isProcessing = applying && progress?.status?.includes(`scene_${sr.scene_number}`);
              const wasJustFixed = applying && sr.revised_dialogue || sr.revised_narration || sr.revised_description;

              return (
                <div key={sr.scene_number} className={`rounded-md border text-[10px] overflow-hidden transition-all ${statusClass.border} ${statusClass.bg}`}>
                  <div className="p-2 flex items-center justify-between cursor-pointer hover:bg-black/5 transition"
                    onClick={() => setExpandedScene(isExpanded ? null : sr.scene_number)}>
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <span className={`font-bold ${statusClass.text} shrink-0`}>{sr.score}</span>
                      <p className="font-medium text-gray-900 truncate">
                        Cena {sr.scene_number}: {scenes?.find(s => s.scene_number === sr.scene_number)?.title || 'Sem título'}
                      </p>
                    </div>
                    
                    <div className="flex items-center gap-2 shrink-0">
                      {/* Real-time processing indicator */}
                      {isProcessing && (
                        <div className="flex items-center gap-1 text-orange-600">
                          <RefreshCw size={9} className="animate-spin" />
                          <span className="text-[9px] font-medium">
                            {lang === 'pt' ? 'Corrigindo...' : 'Fixing...'}
                          </span>
                        </div>
                      )}
                      
                      {/* Just fixed indicator */}
                      {wasJustFixed && !isProcessing && (
                        <div className="flex items-center gap-1 text-emerald-600">
                          <Check size={9} />
                          <span className="text-[9px] font-medium">
                            {lang === 'pt' ? 'Corrigido' : 'Fixed'}
                          </span>
                        </div>
                      )}
                      
                      <span className={`text-[9px] font-medium ${statusClass.text}`}>
                        {STATUS_LABELS[sr.status]?.[lang] || sr.status}
                      </span>
                      <ChevronDown size={12} className={`text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-200 p-2 space-y-1.5 bg-white/50">
                      {sr.issues?.length > 0 && (
                        <div>
                          <p className="text-[9px] font-semibold text-red-600 mb-0.5">
                            {lang === 'pt' ? 'Problemas:' : 'Issues:'}
                          </p>
                          <ul className="space-y-0.5 pl-2">
                            {sr.issues.map((issue, i) => (
                              <li key={i} className="text-[9px] text-gray-600">• {issue}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {sr.suggestions?.length > 0 && (
                        <div>
                          <p className="text-[9px] font-semibold text-blue-600 mb-0.5">
                            {lang === 'pt' ? 'Sugestões:' : 'Suggestions:'}
                          </p>
                          <ul className="space-y-0.5 pl-2">
                            {sr.suggestions.map((sug, i) => (
                              <li key={i} className="text-[9px] text-gray-600">• {sug}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between items-center border-t border-[#222] pt-3">
        <button onClick={onBack} className="text-xs text-gray-600 hover:text-gray-900 transition flex items-center gap-1" data-testid="director-back-btn">
          <ChevronLeft size={12} />
          {lang === 'pt' ? 'Voltar aos Diálogos' : 'Back to Dialogues'}
        </button>
        <button onClick={onApprove} disabled={!review}
          data-testid="director-approve-btn"
          className={`px-4 py-2 text-xs rounded-lg font-bold flex items-center gap-1.5 transition ${
            isApproved
              ? 'bg-emerald-500 text-gray-900 hover:bg-emerald-600'
              : review
                ? 'bg-orange-500 text-black hover:bg-[#EA580C]'
                : 'bg-gray-300 text-gray-600 cursor-not-allowed'
          }`}>
          <ChevronRight size={12} />
          {isApproved
            ? (lang === 'pt' ? 'Aprovado — Avançar para Storyboard' : 'Approved — Continue to Storyboard')
            : (lang === 'pt' ? 'Avançar para Storyboard' : 'Continue to Storyboard')
          }
        </button>
      </div>
    </div>
  );
}
