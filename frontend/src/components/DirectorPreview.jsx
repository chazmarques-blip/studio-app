import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Eye, RefreshCw, ChevronLeft, ChevronRight, Check, X, AlertTriangle, Star, Sparkles, Film, BookOpen, Zap } from 'lucide-react';
import { getErrorMsg } from '../utils/getErrorMsg';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_COLORS = {
  EXCELLENT: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5',
  GOOD: 'text-sky-400 border-sky-500/20 bg-sky-500/5',
  NEEDS_WORK: 'text-amber-400 border-amber-500/20 bg-amber-500/5',
  CRITICAL: 'text-red-400 border-red-500/20 bg-red-500/5',
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
  
  // Poll progress during review/re-evaluation
  useEffect(() => {
    if (!applying && !reviewing) {
      setProgress(null);
      return;
    }
    
    const pollInterval = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/studio/projects/${projectId}/director/progress`);
        if (res.data.in_progress) {
          setProgress(res.data.progress);
        } else {
          setProgress(null);
        }
      } catch (err) {
        console.error('Poll progress failed:', err);
      }
    }, 2000); // Poll every 2 seconds
    
    return () => clearInterval(pollInterval);
  }, [applying, reviewing, projectId]);

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

      {/* Review Results */}
      {review && !reviewing && (
        <>
          {/* Score + Verdict */}
          <div className={`rounded-xl border p-4 ${isApproved ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-amber-500/30 bg-amber-500/5'}`}
            data-testid="director-verdict">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className={`text-3xl font-black ${scoreColor}`} data-testid="director-score">{score}</div>
                <div>
                  <p className={`text-xs font-bold ${isApproved ? 'text-emerald-400' : 'text-amber-400'}`} data-testid="director-verdict-text">
                    {isApproved
                      ? (lang === 'pt' ? 'APROVADO PELO DIRECTOR' : 'DIRECTOR APPROVED')
                      : (lang === 'pt' ? 'REVISÃO NECESSÁRIA' : 'REVISION NEEDED')
                    }
                  </p>
                  <p className="text-[10px] text-gray-600">
                    {needsWork > 0 && (lang === 'pt' ? `${needsWork} cena(s) precisam de ajustes` : `${needsWork} scene(s) need adjustments`)}
                    {needsWork === 0 && (lang === 'pt' ? 'Todas as cenas estão prontas' : 'All scenes are ready')}
                  </p>
                </div>
              </div>
              {hasRevisions && (
                <div className="flex flex-col gap-2">
                  <button onClick={applyFixes} disabled={applying}
                    data-testid="apply-director-fixes-btn"
                    className="text-xs px-3 py-2 rounded-lg bg-orange-500 text-black font-bold hover:bg-[#EA580C] transition disabled:opacity-50 flex items-center justify-center gap-1.5">
                    {applying ? <RefreshCw size={11} className="animate-spin" /> : <Zap size={11} />}
                    {applying
                      ? (lang === 'pt' ? 'Aplicando e re-avaliando...' : 'Applying & re-evaluating...')
                      : (lang === 'pt' ? 'Aplicar Correções + Re-avaliar' : 'Apply Fixes + Re-evaluate')
                    }
                  </button>
                  {score < 90 && (
                    <p className="text-[9px] text-amber-500 text-center">
                      {lang === 'pt' 
                        ? '⚡ Workflow automático: Aplica → Re-avalia → Aprovação >= 90%'
                        : '⚡ Auto workflow: Apply → Re-evaluate → Approval >= 90%'}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Director Notes */}
            {review.director_notes && (
              <div className="border-t border-[#222] pt-3">
                <p className="text-[10px] text-[#888] leading-relaxed whitespace-pre-line">{review.director_notes}</p>
              </div>
            )}
          </div>

          {/* Strengths & Improvements */}
          <div className="grid grid-cols-2 gap-2">
            {review.top_3_strengths?.length > 0 && (
              <div className="rounded-lg border border-emerald-500/15 bg-emerald-500/5 p-2.5">
                <p className="text-[10px] font-bold text-emerald-400 mb-1.5 flex items-center gap-1">
                  <Star size={9} /> {lang === 'pt' ? 'Pontos Fortes' : 'Strengths'}
                </p>
                {review.top_3_strengths.map((s, i) => (
                  <p key={i} className="text-[9px] text-[#888] leading-relaxed">+ {s}</p>
                ))}
              </div>
            )}
            {review.top_3_improvements?.length > 0 && (
              <div className="rounded-lg border border-amber-500/15 bg-amber-500/5 p-2.5">
                <p className="text-[10px] font-bold text-amber-400 mb-1.5 flex items-center gap-1">
                  <AlertTriangle size={9} /> {lang === 'pt' ? 'Melhorias' : 'Improvements'}
                </p>
                {review.top_3_improvements.map((s, i) => (
                  <p key={i} className="text-[9px] text-[#888] leading-relaxed">- {s}</p>
                ))}
              </div>
            )}
          </div>

          {/* Pacing & Emotional Arc */}
          {(review.pacing_notes || review.emotional_arc) && (
            <div className="grid grid-cols-2 gap-2">
              {review.pacing_notes && (
                <div className="rounded-lg border border-gray-200 bg-white p-2.5">
                  <p className="text-[10px] font-bold text-orange-600 mb-1 flex items-center gap-1">
                    <BookOpen size={9} /> {lang === 'pt' ? 'Ritmo Narrativo' : 'Pacing'}
                  </p>
                  <p className="text-[9px] text-[#777] leading-relaxed">{review.pacing_notes}</p>
                </div>
              )}
              {review.emotional_arc && (
                <div className="rounded-lg border border-gray-200 bg-white p-2.5">
                  <p className="text-[10px] font-bold text-orange-600 mb-1 flex items-center gap-1">
                    <Sparkles size={9} /> {lang === 'pt' ? 'Arco Emocional' : 'Emotional Arc'}
                  </p>
                  <p className="text-[9px] text-[#777] leading-relaxed">{review.emotional_arc}</p>
                </div>
              )}
            </div>
          )}

          {/* Scene-by-Scene Review */}
          <div className="space-y-1">
            <p className="text-[10px] font-bold text-gray-900 mb-1.5 flex items-center gap-1">
              <Film size={10} className="text-orange-600" />
              {lang === 'pt' ? 'Revisão Cena a Cena' : 'Scene-by-Scene Review'}
              <span className="text-gray-500 font-normal ml-1">({sceneReviews.length} cenas)</span>
            </p>
            <div className="space-y-1 max-h-[300px] overflow-y-auto hide-scrollbar">
              {sceneReviews.map(sr => {
                const isExpanded = expandedScene === sr.scene_number;
                const statusClass = STATUS_COLORS[sr.status] || STATUS_COLORS.GOOD;
                const scene = scenes.find(s => s.scene_number === sr.scene_number);

                return (
                  <div key={sr.scene_number}
                    className={`rounded-lg border ${statusClass} cursor-pointer transition-all`}
                    data-testid={`director-scene-${sr.scene_number}`}
                    onClick={() => setExpandedScene(isExpanded ? null : sr.scene_number)}>

                    {/* Scene header */}
                    <div className="flex items-center gap-2 px-2.5 py-1.5">
                      {STATUS_ICONS[sr.status]}
                      <span className="text-[10px] font-bold text-gray-900">
                        {lang === 'pt' ? 'Cena' : 'Scene'} {sr.scene_number}
                      </span>
                      <span className="text-[9px] text-gray-600 flex-1 truncate">{scene?.title || ''}</span>
                      <span className={`text-[9px] font-bold ${
                        sr.score >= 80 ? 'text-emerald-400' : sr.score >= 60 ? 'text-amber-400' : 'text-red-400'
                      }`}>{sr.score}/100</span>
                      <span className={`text-[8px] px-1.5 py-0.5 rounded ${statusClass}`}>
                        {sr.status}
                      </span>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="px-2.5 pb-2.5 space-y-1.5 border-t border-gray-200 pt-1.5">
                        {sr.issues?.length > 0 && (
                          <div>
                            <p className="text-[9px] text-red-300 font-medium mb-0.5">{lang === 'pt' ? 'Problemas:' : 'Issues:'}</p>
                            {sr.issues.map((issue, i) => (
                              <p key={i} className="text-[9px] text-[#888] pl-2 leading-relaxed">- {issue}</p>
                            ))}
                          </div>
                        )}
                        {sr.suggestions?.length > 0 && (
                          <div>
                            <p className="text-[9px] text-orange-600 font-medium mb-0.5">{lang === 'pt' ? 'Sugestões:' : 'Suggestions:'}</p>
                            {sr.suggestions.map((sug, i) => (
                              <p key={i} className="text-[9px] text-[#888] pl-2 leading-relaxed">+ {sug}</p>
                            ))}
                          </div>
                        )}
                        {sr.revised_dialogue && (
                          <div className="border border-emerald-500/20 rounded p-1.5 bg-emerald-500/5">
                            <p className="text-[9px] text-emerald-300 font-medium mb-0.5">{lang === 'pt' ? 'Diálogo Revisto:' : 'Revised Dialogue:'}</p>
                            <p className="text-[9px] text-[#ccc] whitespace-pre-line leading-relaxed">{sr.revised_dialogue}</p>
                          </div>
                        )}
                        {sr.revised_narration && (
                          <div className="border border-sky-500/20 rounded p-1.5 bg-sky-500/5">
                            <p className="text-[9px] text-sky-300 font-medium mb-0.5">{lang === 'pt' ? 'Narração Revista:' : 'Revised Narration:'}</p>
                            <p className="text-[9px] text-[#ccc] whitespace-pre-line leading-relaxed">{sr.revised_narration}</p>
                          </div>
                        )}
                        {sr.revised_description && (
                          <div className="border border-purple-500/20 rounded p-1.5 bg-purple-500/5">
                            <p className="text-[9px] text-purple-300 font-medium mb-0.5">{lang === 'pt' ? 'Descrição Enriquecida:' : 'Enriched Description:'}</p>
                            <p className="text-[9px] text-[#ccc] whitespace-pre-line leading-relaxed">{sr.revised_description}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
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
