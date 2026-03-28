import React from 'react';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { toast } from 'sonner';
import {
  X, Loader2, Camera, PenTool, Sparkles, Upload, Check, Film, Volume2,
  ShieldCheck, ScanEye, Bot, Maximize2, Shirt, RotateCw, Sun, Layers,
  Briefcase, Palette, History, Download, Trash2, Plus, Play, Crown,
  Mic, MicOff, Square, RefreshCw, Lock,
} from 'lucide-react';
import { resolveImageUrl } from '../../utils/resolveImageUrl';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * AvatarModal — Full avatar creation/customization modal.
 * Extracted from PipelineView (~1050 lines) to reduce file size.
 * All state is passed via the `ctx` prop object.
 */
export function AvatarModal({ ctx }) {
  const { t } = useTranslation();
  const {
    showAvatarModal, avatarStage, avatarCreationMode, avatarSourceType,
    avatarSourcePhoto, avatarVideoUploading, avatarExtractedAudio,
    avatarVideoFrames, masteringVoice, generatingPreviewVideo, previewVideoUrl,
    previewLanguage, avatarName, avatarMediaTab, accuracyProgress,
    generatingAvatar, avatarPhotoUploading, avatarPromptText,
    avatarPromptGender, avatarPromptStyle, aiEditAvatarId, aiEditInstruction,
    aiEditLoading, tempAvatar, clothingVariants, customizeTab, voiceTab,
    angleImages, generatingAngle, auto360Progress, editingAvatarId,
    avatarEditHistory, avatarBaseUrl, applyingClothing, isRecording,
    recordedAudioUrl, recordedAudioBlob, uploadingRecording, loadingVoicePreview,
    playingVoiceId, elevenLabsVoices, elevenLabsAvailable, avatarPreviewUrl,
    // Setters
    setAvatarCreationMode, setAvatarSourceType, setAvatarSourcePhoto,
    setAvatarExtractedAudio, setAvatarVideoFrames, setAvatarName,
    setAvatarMediaTab, setAvatarPromptText, setAvatarPromptGender,
    setAvatarPromptStyle, setAiEditAvatarId, setAiEditInstruction, setAiEditLoading: _setAiEditLoading,
    setTempAvatar, setCustomizeTab, setVoiceTab, setAngleImages,
    setPreviewLanguage, setAvatarPreviewUrl, setAvatarEditHistory,
    setPreviewVideoUrl, setGeneratingPreviewVideo,
    // Handlers
    resetAvatarModal, generateAvatarFromPhoto, generateAvatarFromPrompt,
    uploadAvatarPhoto, uploadAvatarVideo, applyClothing, generateAngle,
    startAuto360, saveAvatarAndClose, saveAvatarAsNew, previewVoice,
    startRecording, stopRecording, saveRecordingAsVoice, persistAvatarToServer,
    avatars,
    // Refs
    avatarInputRef,
    isDirectedMode,
  } = ctx;

  const setAiEditLoading = _setAiEditLoading || (() => {});

  // Labels adapt based on context (Directed Studio = "Personagem", Campaign = "Avatar")
  const entityLabel = isDirectedMode ? 'Personagem' : 'Avatar';

  // In directed mode, skip clothing tab — default to view360
  const effectiveTab = (isDirectedMode && customizeTab === 'clothing') ? 'view360' : customizeTab;

  if (!showAvatarModal) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4" onClick={() => { if (!generatingAvatar && !applyingClothing) resetAvatarModal(); }}>
      <div data-testid="avatar-modal" className="w-full max-w-lg rounded-2xl border border-[#C9A84C]/20 bg-[#0D0D0D] overflow-hidden max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
              {/* Header */}
              <div className="px-5 py-3 border-b border-[#151515] flex items-center justify-between shrink-0">
                <p className="text-sm text-white font-semibold">
                  {avatarStage === 'customize'
                    ? (editingAvatarId
                        ? (isDirectedMode ? `Editar ${entityLabel}` : t('studio.edit_avatar'))
                        : (isDirectedMode ? `Personalizar ${entityLabel}` : t('studio.customize_avatar')))
                    : (isDirectedMode ? `Criar ${entityLabel}` : t('studio.create_avatar'))}
                </p>
                <button onClick={() => { if (!generatingAvatar && !applyingClothing) resetAvatarModal(); }} className="p-1 rounded hover:bg-[#1A1A1A]"><X size={16} className="text-[#999]" /></button>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-4">
                {avatarStage === 'upload' ? (
                  <>
                    {/* Avatar Type Tabs */}
                    <div className="flex gap-1 mb-3">
                      {[
                        { id: 'photo', label: t('studio.photo_reference') || 'Photo', icon: Camera },
                        { id: 'prompt', label: t('studio.by_prompt') || 'By Prompt', icon: PenTool },
                        { id: '3d', label: '3D Animated', icon: Sparkles },
                      ].map(tab => (
                        <button key={tab.id} data-testid={`avatar-mode-${tab.id}`} onClick={() => setAvatarCreationMode(tab.id)}
                          className={`flex-1 rounded-lg py-2 text-xs font-semibold transition flex items-center justify-center gap-1.5 ${
                            avatarCreationMode === tab.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999] hover:text-white'}`}>
                          <tab.icon size={11} /> {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* MODE: Photo Reference (existing) */}
                    {avatarCreationMode === 'photo' && (
                      <>
                        <input ref={avatarInputRef} type="file" accept={avatarSourceType === 'video' ? 'video/mp4,video/quicktime,video/webm,video/*' : 'image/png,image/jpeg,image/jpg,image/webp'}
                          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
                          onChange={e => {
                            if (avatarSourceType === 'video') uploadAvatarVideo(e.target.files);
                            else uploadAvatarPhoto(e.target.files);
                            e.target.value = '';
                          }} />

                    {/* Photo Upload Section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Camera size={12} className="text-[#C9A84C]" />
                        <span className="text-xs text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.photo_reference') || 'Photo Reference'}</span>
                        {!avatarSourcePhoto && <span className="text-[10px] text-red-400/70 uppercase">*{t('studio.required') || 'Required'}</span>}
                      </div>
                      {avatarSourcePhoto ? (
                        <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0A0A0A] border border-[#1E1E1E]">
                          <div className="relative shrink-0">
                            <img loading="lazy" decoding="async" src={avatarSourcePhoto.preview || resolveImageUrl(avatarSourcePhoto.url)} alt="Source"
                              onError={(e) => { if (avatarSourcePhoto.url) e.target.src = resolveImageUrl(avatarSourcePhoto.url); }}
                              className="h-16 w-16 rounded-lg object-cover border border-[#C9A84C]/30" />
                            <button onClick={() => { setAvatarSourcePhoto(null); }}
                              className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
                              <X size={8} className="text-white" />
                            </button>
                          </div>
                          <div>
                            <p className="text-xs text-[#888]">{t('studio.photo_uploaded') || 'Photo uploaded'}</p>
                            <p className="text-[10px] text-[#888]">{t('studio.photo_desc_detail') || 'High-resolution facial reference'}</p>
                          </div>
                          <Check size={14} className="text-green-400 ml-auto" />
                        </div>
                      ) : (
                        <button data-testid="upload-photo-btn" onClick={() => { setAvatarSourceType('photo'); setTimeout(() => avatarInputRef.current?.click(), 100); }}
                          disabled={avatarPhotoUploading}
                          className="w-full p-3 rounded-xl border border-dashed border-[#2A2A2A] hover:border-[#C9A84C]/30 text-center transition group">
                          {avatarPhotoUploading ? (
                            <div className="flex items-center justify-center gap-2"><Loader2 size={12} className="animate-spin text-[#C9A84C]" /><span className="text-xs text-[#999]">{t('studio.uploading')}</span></div>
                          ) : (
                            <div className="flex items-center justify-center gap-2">
                              <Upload size={14} className="text-[#888] group-hover:text-[#C9A84C] transition" />
                              <span className="text-xs text-[#999] group-hover:text-[#C9A84C] transition">{t('studio.select_photo') || 'Select photo'}</span>
                            </div>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Video Upload Section */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Film size={12} className="text-[#C9A84C]" />
                        <span className="text-xs text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.video_reference') || 'Video Reference'}</span>
                        <span className="px-1.5 py-0.5 rounded-full bg-[#C9A84C]/15 text-xs text-[#C9A84C] font-bold uppercase">{t('studio.recommended') || 'Recommended'}</span>
                      </div>
                      {avatarExtractedAudio || avatarVideoFrames.length > 0 ? (
                        <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0A0A0A] border border-[#1E1E1E]">
                          {avatarVideoFrames.length > 0 && (
                            <div className="flex -space-x-2 shrink-0">
                              {avatarVideoFrames.slice(0, 3).map((url, i) => (
                                <img loading="lazy" decoding="async" key={i} src={resolveImageUrl(url)} alt={`frame ${i}`}
                                  className="h-10 w-10 rounded-lg object-cover border-2 border-[#0A0A0A]" />
                              ))}
                            </div>
                          )}
                          <div className="flex-1 space-y-0.5">
                            <p className="text-xs text-[#888]">{t('studio.video_processed') || 'Video processed'}</p>
                            <div className="flex items-center gap-2">
                              {avatarVideoFrames.length > 0 && (
                                <span className="text-[10px] text-[#999]">{avatarVideoFrames.length} {t('studio.extra_frames') || 'frames'}</span>
                              )}
                              {avatarExtractedAudio && (
                                <span className="flex items-center gap-1 text-[10px] text-[#10B981]"><Volume2 size={8} /> {t('studio.voice_extracted')}</span>
                              )}
                            </div>
                          </div>
                          <button onClick={() => { setAvatarExtractedAudio(null); setAvatarVideoFrames([]); }}
                            className="p-1 rounded hover:bg-[#1A1A1A]"><X size={12} className="text-[#999]" /></button>
                        </div>
                      ) : (
                        <button data-testid="upload-video-btn" onClick={() => { setAvatarSourceType('video'); setTimeout(() => avatarInputRef.current?.click(), 100); }}
                          disabled={avatarVideoUploading}
                          className="w-full p-3 rounded-xl border border-dashed border-[#2A2A2A] hover:border-[#C9A84C]/30 text-center transition group">
                          {avatarVideoUploading ? (
                            <div className="flex items-center justify-center gap-2"><Loader2 size={12} className="animate-spin text-[#C9A84C]" /><span className="text-xs text-[#999]">{t('studio.extracting_video')}</span></div>
                          ) : (
                            <div className="space-y-1">
                              <div className="flex items-center justify-center gap-2">
                                <Upload size={14} className="text-[#888] group-hover:text-[#C9A84C] transition" />
                                <span className="text-xs text-[#999] group-hover:text-[#C9A84C] transition">{t('studio.select_video') || 'Select video'}</span>
                              </div>
                              <p className="text-[10px] text-[#777]">{t('studio.video_adds_accuracy') || 'Adds body, voice & expression data for higher accuracy'}</p>
                            </div>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Generate Button (requires photo) */}
                    {avatarSourcePhoto && (
                      <div className="space-y-2 pt-2">
                        {avatarVideoFrames.length > 0 && (
                          <div className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-green-500/5 border border-green-500/15">
                            <ShieldCheck size={10} className="text-green-400" />
                            <span className="text-[10px] text-green-400">{t('studio.enhanced_accuracy') || 'Enhanced accuracy: photo + video references active'}</span>
                          </div>
                        )}
                        <button data-testid="generate-avatar-btn" onClick={generateAvatarFromPhoto}
                          disabled={generatingAvatar}
                          className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-xs font-bold text-black hover:opacity-90 disabled:opacity-50 transition flex items-center justify-center gap-2">
                          {generatingAvatar ? (
                            <><Loader2 size={14} className="animate-spin" /> {t('studio.generating_avatar')}</>
                          ) : (
                            <><Sparkles size={14} /> {t('studio.generate_avatar_ai')}</>
                          )}
                        </button>
                        {generatingAvatar && (
                          <div className="rounded-xl bg-[#0A0A0A] border border-[#1E1E1E] p-4 space-y-3">
                            {/* Agent Timeline Header */}
                            <div className="flex items-center gap-2 pb-2 border-b border-[#1A1A1A]">
                              <div className="flex items-center gap-1.5">
                                {[
                                  { name: 'Scanner', icon: ScanEye, role: t('studio.agent_scanner') || 'Analyzing' },
                                  { name: 'Artist', icon: Bot, role: t('studio.agent_artist') || 'Generating' },
                                  { name: 'Critic', icon: ShieldCheck, role: t('studio.agent_critic') || 'Evaluating' },
                                ].map((agent, idx) => {
                                  const isActive = accuracyProgress?.active_agent === agent.name;
                                  const isDone = accuracyProgress?.iteration > 0 && (
                                    (agent.name === 'Scanner') ||
                                    (agent.name === 'Artist' && accuracyProgress?.iterations?.length > 0) ||
                                    (agent.name === 'Critic' && accuracyProgress?.iterations?.some(it => it.score > 0))
                                  );
                                  return (
                                    <React.Fragment key={agent.name}>
                                      {idx > 0 && <div className={`w-4 h-px ${isDone ? 'bg-[#C9A84C]' : 'bg-[#1E1E1E]'}`} />}
                                      <div className={`flex items-center gap-1 px-2 py-1 rounded-lg transition ${
                                        isActive ? 'bg-[#C9A84C]/15 border border-[#C9A84C]/30' :
                                        isDone ? 'bg-green-500/10 border border-green-500/20' :
                                        'bg-[#111] border border-[#1A1A1A]'}`}>
                                        <agent.icon size={10} className={isActive ? 'text-[#C9A84C] animate-pulse' : isDone ? 'text-green-400' : 'text-[#888]'} />
                                        <span className={`text-[10px] font-bold uppercase tracking-wider ${
                                          isActive ? 'text-[#C9A84C]' : isDone ? 'text-green-400' : 'text-[#888]'}`}>
                                          {agent.name}
                                        </span>
                                      </div>
                                    </React.Fragment>
                                  );
                                })}
                              </div>
                            </div>

                            {/* Progress info */}
                            <div className="flex items-center gap-2">
                              <Loader2 size={12} className="animate-spin text-[#C9A84C] shrink-0" />
                              <p className="text-xs text-[#888]">
                                {accuracyProgress?.progress || t('studio.avatar_gen_time')}
                              </p>
                            </div>

                            {/* Iteration progress bar */}
                            {accuracyProgress?.iteration > 0 && (
                              <div className="flex items-center gap-1.5">
                                <div className="flex-1 h-1.5 bg-[#1E1E1E] rounded-full overflow-hidden">
                                  <div className="h-full bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] transition-all duration-700 rounded-full"
                                    style={{width: `${(accuracyProgress.iteration / 3) * 100}%`}} />
                                </div>
                                <span className="text-[11px] text-[#999] font-mono">{accuracyProgress.iteration}/3</span>
                              </div>
                            )}

                            {/* Evolution thumbnails with scores */}
                            {accuracyProgress?.iterations?.length > 0 && (
                              <div className="space-y-1.5 pt-1 border-t border-[#1A1A1A]">
                                <p className="text-[10px] text-[#999] uppercase tracking-wider">{t('studio.accuracy_evolution') || 'Evolution'}</p>
                                <div className="flex gap-2">
                                  {accuracyProgress.iterations.map((it, idx) => (
                                    it.url && <div key={idx} className="relative group/evo">
                                      <img loading="lazy" decoding="async" src={resolveImageUrl(it.url)} alt={`v${idx+1}`}
                                        className={`h-20 w-14 rounded-xl object-cover border-2 transition ${
                                          it.passed ? 'border-green-500/40' : 'border-red-500/30'}`} />
                                      <div className={`absolute -top-1.5 -right-1.5 h-5 min-w-5 px-0.5 rounded-full text-[11px] font-bold flex items-center justify-center shadow-lg ${
                                        it.passed ? 'bg-green-500 text-white' : 'bg-red-500/80 text-white'}`}>
                                        {it.score}
                                      </div>
                                      <div className={`absolute -bottom-0.5 left-1/2 -translate-x-1/2 px-1.5 py-0.5 rounded text-xs font-bold ${
                                        it.passed ? 'bg-green-500/90 text-white' : 'bg-red-500/70 text-white'}`}>
                                        {it.passed ? 'OK' : 'REDO'}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                      </>
                    )}

                    {/* MODE: By Prompt */}
                    {avatarCreationMode === 'prompt' && (
                      <div className="space-y-3">
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <PenTool size={12} className="text-[#C9A84C]" />
                            <span className="text-xs text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.describe_avatar') || 'Describe your avatar'}</span>
                          </div>
                          <textarea data-testid="avatar-prompt-input" value={avatarPromptText}
                            onChange={e => setAvatarPromptText(e.target.value)}
                            placeholder={t('studio.avatar_prompt_placeholder') || 'E.g.: Young professional woman, 28 years old, brown hair, confident smile, business attire'}
                            className="w-full bg-[#0A0A0A] border border-[#1E1E1E] rounded-xl px-3 py-2.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 resize-none h-20" />
                        </div>
                        <div className="flex gap-2">
                          <div className="flex-1 space-y-1">
                            <span className="text-[11px] text-[#999] uppercase tracking-wider">{t('studio.gender') || 'Gender'}</span>
                            <div className="flex gap-1">
                              {[{id:'female', label:'F'}, {id:'male', label:'M'}].map(g => (
                                <button key={g.id} onClick={() => setAvatarPromptGender(g.id)}
                                  className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition ${avatarPromptGender === g.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                  {g.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                        {/* Style selector - also for prompt mode */}
                        <div className="space-y-1">
                          <span className="text-[11px] text-[#999] uppercase tracking-wider">{t('studio.style') || 'Style'}</span>
                          <div className="flex gap-1">
                            {[{id:'custom', label:'Custom'}, {id:'realistic', label:'Realistic'}, {id:'3d_cartoon', label:'3D Cartoon'}, {id:'3d_pixar', label:'3D Pixar'}].map(s => (
                              <button key={s.id} onClick={() => setAvatarPromptStyle(s.id)}
                                data-testid={`prompt-style-${s.id}`}
                                className={`flex-1 rounded-lg py-1.5 text-[11px] font-semibold transition ${avatarPromptStyle === s.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                {s.label}
                              </button>
                            ))}
                          </div>
                        </div>
                        <button data-testid="generate-avatar-prompt-btn" onClick={generateAvatarFromPrompt}
                          disabled={generatingAvatar || !avatarPromptText.trim()}
                          className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-xs font-bold text-black hover:opacity-90 disabled:opacity-50 transition flex items-center justify-center gap-2">
                          {generatingAvatar ? (
                            <><Loader2 size={14} className="animate-spin" /> {accuracyProgress?.progress || t('studio.generating_avatar')}</>
                          ) : (
                            <><Sparkles size={14} /> {t('studio.generate_avatar_ai')}</>
                          )}
                        </button>
                      </div>
                    )}

                    {/* MODE: 3D Animated */}
                    {avatarCreationMode === '3d' && (
                      <div className="space-y-3">
                        {/* Hidden file input for 3D photo reference */}
                        <input ref={avatarInputRef} type="file" accept="image/png,image/jpeg,image/jpg,image/webp"
                          style={{ position: 'absolute', width: 1, height: 1, opacity: 0, overflow: 'hidden' }}
                          onChange={e => { uploadAvatarPhoto(e.target.files); e.target.value = ''; }} />

                        {/* Optional Photo Reference for 3D */}
                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Camera size={12} className="text-[#C9A84C]" />
                            <span className="text-xs text-[#C9A84C] font-bold uppercase tracking-wider">{t('studio.photo_reference') || 'Photo Reference'}</span>
                            <span className="px-1.5 py-0.5 rounded-full bg-[#C9A84C]/10 text-xs text-[#C9A84C]/70 font-bold uppercase">{t('studio.optional') || 'Optional'}</span>
                          </div>
                          {avatarSourcePhoto ? (
                            <div className="flex items-center gap-3 p-2 rounded-xl bg-[#0A0A0A] border border-[#1E1E1E]">
                              <div className="relative shrink-0">
                                <img loading="lazy" decoding="async" src={avatarSourcePhoto.preview || resolveImageUrl(avatarSourcePhoto.url)} alt="Ref"
                                  onError={(e) => { if (avatarSourcePhoto.url) e.target.src = resolveImageUrl(avatarSourcePhoto.url); }}
                                  className="h-14 w-14 rounded-lg object-cover border border-[#C9A84C]/30" />
                                <button onClick={() => setAvatarSourcePhoto(null)}
                                  className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 flex items-center justify-center">
                                  <X size={8} className="text-white" />
                                </button>
                              </div>
                              <div>
                                <p className="text-xs text-[#888]">{t('studio.photo_uploaded') || 'Photo uploaded'}</p>
                                <p className="text-[10px] text-[#888]">{t('studio.photo_3d_ref_desc') || '3D avatar will match this face'}</p>
                              </div>
                              <Check size={14} className="text-green-400 ml-auto" />
                            </div>
                          ) : (
                            <button data-testid="upload-3d-ref-photo-btn" onClick={() => { setAvatarSourceType('photo'); setTimeout(() => avatarInputRef.current?.click(), 100); }}
                              disabled={avatarPhotoUploading}
                              className="w-full p-2.5 rounded-xl border border-dashed border-[#2A2A2A] hover:border-[#C9A84C]/30 text-center transition group">
                              {avatarPhotoUploading ? (
                                <div className="flex items-center justify-center gap-2"><Loader2 size={12} className="animate-spin text-[#C9A84C]" /><span className="text-xs text-[#999]">{t('studio.uploading')}</span></div>
                              ) : (
                                <div className="space-y-0.5">
                                  <div className="flex items-center justify-center gap-2">
                                    <Upload size={12} className="text-[#888] group-hover:text-[#C9A84C] transition" />
                                    <span className="text-xs text-[#999] group-hover:text-[#C9A84C] transition">{t('studio.upload_ref_photo') || 'Upload reference photo'}</span>
                                  </div>
                                  <p className="text-[10px] text-[#777]">{t('studio.photo_3d_hint') || 'Upload a face photo to guide the 3D style'}</p>
                                </div>
                              )}
                            </button>
                          )}
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center gap-2">
                            <Sparkles size={12} className="text-[#C9A84C]" />
                            <span className="text-xs text-[#C9A84C] font-bold uppercase tracking-wider">3D Avatar Description</span>
                          </div>
                          <textarea data-testid="avatar-3d-prompt-input" value={avatarPromptText}
                            onChange={e => setAvatarPromptText(e.target.value)}
                            placeholder={t('studio.avatar_3d_placeholder') || 'E.g.: Friendly 3D character, young man with glasses, wearing casual clothes, vibrant colors'}
                            className="w-full bg-[#0A0A0A] border border-[#1E1E1E] rounded-xl px-3 py-2.5 text-[10px] text-white placeholder-[#666] outline-none focus:border-[#C9A84C]/30 resize-none h-20" />
                        </div>
                        <div className="flex gap-2">
                          <div className="flex-1 space-y-1">
                            <span className="text-[11px] text-[#999] uppercase tracking-wider">{t('studio.gender') || 'Gender'}</span>
                            <div className="flex gap-1">
                              {[{id:'female', label:'F'}, {id:'male', label:'M'}].map(g => (
                                <button key={g.id} onClick={() => setAvatarPromptGender(g.id)}
                                  className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition ${avatarPromptGender === g.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                  {g.label}
                                </button>
                              ))}
                            </div>
                          </div>
                          <div className="flex-1 space-y-1">
                            <span className="text-[11px] text-[#999] uppercase tracking-wider">{t('studio.style') || 'Style'}</span>
                            <div className="flex gap-1">
                              {[{id:'3d_cartoon', label:'Cartoon'}, {id:'3d_pixar', label:'Pixar'}].map(s => (
                                <button key={s.id} onClick={() => setAvatarPromptStyle(s.id)}
                                  className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition ${avatarPromptStyle === s.id ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                                  {s.label}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>
                        <button data-testid="generate-avatar-3d-btn" onClick={generateAvatarFromPrompt}
                          disabled={generatingAvatar || !avatarPromptText.trim()}
                          className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-3 text-xs font-bold text-black hover:opacity-90 disabled:opacity-50 transition flex items-center justify-center gap-2">
                          {generatingAvatar ? (
                            <><Loader2 size={14} className="animate-spin" /> {accuracyProgress?.progress || t('studio.generating_avatar')}</>
                          ) : (
                            <><Sparkles size={14} /> Generate 3D Avatar</>
                          )}
                        </button>
                      </div>
                    )}
                  </>
                ) : (
                  /* CUSTOMIZE STAGE */
                  <>
                    {/* Avatar Name */}
                    <div className="flex items-center gap-2">
                      <input
                        data-testid="avatar-name-input"
                        type="text"
                        value={avatarName}
                        onChange={(e) => setAvatarName(e.target.value)}
                        placeholder={t('studio.avatar_name_placeholder') || 'Name your avatar...'}
                        className="flex-1 bg-[#0A0A0A] border border-[#1E1E1E] rounded-lg px-3 py-1.5 text-xs text-white placeholder:text-[#888] focus:border-[#C9A84C]/50 focus:outline-none"
                      />
                    </div>

                    {/* Avatar Preview - Photo/Video selector */}
                    <div className="flex flex-col items-center gap-2">
                      {/* Photo / Video toggle */}
                      {(previewVideoUrl || generatingPreviewVideo) && (
                        <div className="flex rounded-md border border-[#1E1E1E] overflow-hidden">
                          <button data-testid="media-tab-photo" onClick={() => setAvatarMediaTab('photo')}
                            className={`px-4 py-1 text-xs font-semibold flex items-center gap-1 transition ${
                              avatarMediaTab === 'photo' ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'text-[#999] hover:text-[#888]'}`}>
                            <Camera size={10} /> {t('studio.photo_tab') || 'Photo'}
                          </button>
                          <button data-testid="media-tab-video" onClick={() => setAvatarMediaTab('video')}
                            className={`px-4 py-1 text-xs font-semibold flex items-center gap-1 transition ${
                              avatarMediaTab === 'video' ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'text-[#999] hover:text-[#888]'}`}>
                            <Film size={10} /> {t('studio.video_tab') || 'Video'}
                          </button>
                        </div>
                      )}

                      {/* Media Display + History (left) + AI Edit Side Panel (right) */}
                      <div className="flex gap-3 items-start">
                      {/* Edit History Panel (Left, vertical scroll, last 2 visible) */}
                      {avatarEditHistory.length > 1 && (
                        <div className="w-32 shrink-0 flex flex-col gap-1.5" data-testid="avatar-edit-history">
                          <div className="flex items-center gap-1">
                            <History size={10} className="text-[#999]" />
                            <span className="text-[11px] text-[#999] uppercase tracking-wider font-semibold">{t('studio.history') || 'Historico'}</span>
                          </div>
                          <div className="flex flex-col gap-2 overflow-y-auto pr-1 scroll-smooth" style={{maxHeight: '356px'}}
                            ref={el => { if (el) el.scrollTop = el.scrollHeight; }}>
                            {avatarEditHistory.map((entry, idx) => {
                              const isCurrent = tempAvatar?.url === entry.url;
                              return (
                                <div key={idx} data-testid={`history-entry-${idx}`}
                                  className={`relative shrink-0 rounded-xl overflow-hidden border-2 cursor-pointer transition group ${
                                    isCurrent ? 'border-[#C9A84C] shadow-[0_0_8px_rgba(201,168,76,0.15)]' : 'border-[#1E1E1E] hover:border-[#333]'
                                  }`}
                                  onClick={() => setTempAvatar(p => ({ ...p, url: entry.url }))}>
                                  <img loading="lazy" decoding="async" src={resolveImageUrl(entry.url)} alt={`v${idx + 1}`}
                                    className="w-full aspect-[3/4] object-cover" />
                                  {entry.isBase && (
                                    <div className="absolute top-1 left-1 bg-[#C9A84C] rounded px-1.5 py-0.5">
                                      <span className="text-xs text-black font-bold uppercase">BASE</span>
                                    </div>
                                  )}
                                  <div className="absolute top-1 right-1 bg-black/70 rounded px-1.5 py-0.5">
                                    <span className="text-[10px] text-white font-bold">v{idx + 1}</span>
                                  </div>
                                  {isCurrent && (
                                    <div className="absolute bottom-1 right-1 h-4 w-4 rounded-full bg-[#C9A84C] flex items-center justify-center">
                                      <Check size={8} className="text-black" />
                                    </div>
                                  )}
                                  {/* Action buttons on hover */}
                                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/95 via-black/70 to-transparent pt-5 pb-1 px-1 opacity-0 group-hover:opacity-100 transition">
                                    <p className="text-[5px] text-white/70 line-clamp-1 leading-tight mb-1">{entry.instruction}</p>
                                    <div className="flex gap-1 justify-center">
                                      <button data-testid={`history-download-${idx}`} title="Download"
                                        onClick={async (e) => {
                                          e.stopPropagation();
                                          try {
                                            const response = await fetch(resolveImageUrl(entry.url));
                                            const blob = await response.blob();
                                            const blobUrl = window.URL.createObjectURL(blob);
                                            const a = document.createElement('a');
                                            a.href = blobUrl;
                                            a.download = `avatar_v${idx + 1}_${Date.now()}.png`;
                                            document.body.appendChild(a);
                                            a.click();
                                            document.body.removeChild(a);
                                            window.URL.revokeObjectURL(blobUrl);
                                          } catch { toast.error('Download failed'); }
                                        }}
                                        className="h-5 w-5 rounded bg-white/10 flex items-center justify-center hover:bg-white/25 transition">
                                        <Download size={8} className="text-white" />
                                      </button>
                                      <button data-testid={`history-edit-${idx}`} title="Editar a partir desta versão"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          setTempAvatar(p => ({ ...p, url: entry.url }));
                                          setAiEditAvatarId('temp');
                                          setAiEditInstruction('');
                                        }}
                                        className="h-5 w-5 rounded bg-purple-500/20 flex items-center justify-center hover:bg-purple-500/40 transition">
                                        <Sparkles size={8} className="text-purple-300" />
                                      </button>
                                      {!entry.isBase && (
                                        <button data-testid={`history-delete-${idx}`} title="Remover"
                                          onClick={async (e) => {
                                            e.stopPropagation();
                                            const newHistory = avatarEditHistory.filter((_, i) => i !== idx);
                                            setAvatarEditHistory(newHistory);
                                            // If we deleted the current version, switch to the last remaining
                                            if (isCurrent && newHistory.length > 0) {
                                              setTempAvatar(p => ({ ...p, url: newHistory[newHistory.length - 1].url }));
                                            }
                                            // Auto-save to server if editing existing avatar
                                            if (editingAvatarId) {
                                              try {
                                                await axios.delete(`${API}/data/avatars/${editingAvatarId}/history/${idx}`);
                                              } catch {}
                                            }
                                            toast.success('Versão removida');
                                          }}
                                          className="h-5 w-5 rounded bg-red-500/20 flex items-center justify-center hover:bg-red-500/40 transition">
                                          <Trash2 size={8} className="text-red-400" />
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      <div className="w-48 shrink-0">
                      <div className="relative aspect-[3/5]">
                        {avatarMediaTab === 'video' && previewVideoUrl ? (
                          <video
                            data-testid="avatar-preview-video"
                            src={previewVideoUrl}
                            controls autoPlay loop playsInline
                            className="w-full h-full rounded-2xl object-cover border-2 border-[#C9A84C]/30 shadow-lg bg-black"
                          />
                        ) : (
                          <div className="relative cursor-pointer group" onClick={() => setAvatarPreviewUrl(tempAvatar?.url)}>
                            <img src={resolveImageUrl(tempAvatar?.url)} alt="Avatar"
                              className="w-full h-full rounded-2xl object-contain border-2 border-[#C9A84C]/30 shadow-lg bg-[#0A0A0A]" />
                            <div className="absolute inset-0 rounded-2xl bg-black/0 group-hover:bg-black/30 transition flex items-center justify-center">
                              <Maximize2 size={16} className="text-white opacity-0 group-hover:opacity-100 transition" />
                            </div>
                            {applyingClothing && (
                              <div className="absolute inset-0 rounded-2xl bg-black/60 flex items-center justify-center">
                                <Loader2 size={24} className="animate-spin text-[#C9A84C]" />
                              </div>
                            )}
                          </div>
                        )}
                        {/* Generating video overlay */}
                        {avatarMediaTab === 'video' && generatingPreviewVideo && !previewVideoUrl && (
                          <div className="absolute inset-0 rounded-2xl bg-black/80 border-2 border-[#C9A84C]/30 flex flex-col items-center justify-center gap-2">
                            <Loader2 size={20} className="animate-spin text-[#C9A84C]" />
                            <p className="text-[11px] text-[#C9A84C]">{t('studio.generating_preview')}</p>
                          </div>
                        )}
                      </div>
                      {/* AI Edit button below avatar */}
                      {avatarMediaTab !== 'video' && (
                        <button data-testid="ai-edit-avatar-modal-btn" onClick={() => setAiEditAvatarId(aiEditAvatarId === 'temp' ? null : 'temp')}
                          className={`mt-1.5 w-full flex items-center justify-center gap-1.5 py-1.5 rounded-lg border border-dashed text-xs transition ${aiEditAvatarId === 'temp' ? 'border-purple-500/50 bg-purple-500/10 text-purple-300' : 'border-purple-500/30 text-purple-400 hover:bg-purple-500/10 hover:border-purple-500/50'}`}>
                          <Sparkles size={10} /> {t('studio.ai_edit') || 'Editar com IA'}
                        </button>
                      )}
                      </div>
                      {/* AI Edit Side Panel */}
                      {aiEditAvatarId === 'temp' && (
                        <div className="flex-1 min-w-[140px] bg-[#111] border border-[#1E1E1E] rounded-xl p-3 flex flex-col gap-2" onClick={e => e.stopPropagation()}>
                          <div className="flex items-center gap-1.5">
                            <Sparkles size={12} className="text-purple-400" />
                            <span className="text-xs text-purple-300 font-bold">{t('studio.ai_edit') || 'Editar com IA'}</span>
                          </div>
                          <textarea data-testid="ai-edit-modal-input"
                            value={aiEditInstruction} onChange={e => setAiEditInstruction(e.target.value)}
                            placeholder="Ex: mudar roupa para tunica bege, adicionar oculos, mudar fundo para praia..."
                            className="w-full text-xs bg-[#0A0A0A] border border-[#222] rounded-lg p-2 text-white placeholder-[#666] resize-none outline-none focus:border-purple-500/40"
                            rows={4} />
                          <div className="flex gap-1.5">
                            <button onClick={() => { setAiEditAvatarId(null); setAiEditInstruction(''); }}
                              className="flex-1 text-[11px] py-1.5 rounded-lg border border-[#333] text-[#888] hover:text-white transition">
                              {t('studio.cancel') || 'Cancelar'}
                            </button>
                            <button data-testid="ai-edit-modal-confirm" onClick={async () => {
                              if (!aiEditInstruction.trim() || aiEditLoading) return;
                              setAiEditLoading(true);
                              try {
                                const { data } = await axios.post(`${API}/campaigns/pipeline/edit-avatar`, {
                                  avatar_url: tempAvatar.url,
                                  instruction: aiEditInstruction,
                                  base_url: avatarBaseUrl || tempAvatar.url,
                                });
                                if (data.url) {
                                  setTempAvatar(p => ({ ...p, url: data.url }));
                                  const newEntry = {
                                    url: data.url,
                                    instruction: aiEditInstruction,
                                    timestamp: new Date().toISOString(),
                                    isBase: false,
                                  };
                                  setAvatarEditHistory(prev => {
                                    const updated = [...prev, newEntry];
                                    // Auto-save history to server
                                    if (editingAvatarId) {
                                      const av = avatars.find(a => a.id === editingAvatarId);
                                      if (av) {
                                        persistAvatarToServer({ ...av, url: data.url, edit_history: updated });
                                      }
                                    }
                                    return updated;
                                  });
                                  toast.success(t('studio.avatar_edited') || 'Avatar editado com IA!');
                                }
                              } catch (err) {
                                toast.error(err.response?.data?.detail || 'Erro ao editar avatar');
                              } finally {
                                setAiEditLoading(false);
                                setAiEditAvatarId(null);
                                setAiEditInstruction('');
                              }
                            }} disabled={aiEditLoading || !aiEditInstruction.trim()}
                              className="flex-1 text-[11px] py-1.5 rounded-lg bg-purple-600 text-white font-bold hover:bg-purple-500 transition disabled:opacity-40 flex items-center justify-center gap-1">
                              {aiEditLoading ? <RefreshCw size={10} className="animate-spin" /> : <Sparkles size={10} />}
                              {aiEditLoading ? (t('studio.editing') || 'Editando...') : (t('studio.apply') || 'Aplicar')}
                            </button>
                          </div>
                        </div>
                      )}
                      </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex rounded-lg border border-[#1A1A1A] bg-[#0A0A0A] p-0.5">
                      {[
                        ...(!isDirectedMode ? [{ id: 'clothing', icon: Shirt, label: t('studio.clothing') }] : []),
                        { id: 'view360', icon: RotateCw, label: t('studio.view_360') },
                        { id: 'voice', icon: Volume2, label: t('studio.voice') },
                      ].map(tab => (
                        <button key={tab.id} data-testid={`avatar-tab-${tab.id}`}
                          onClick={() => {
                            setCustomizeTab(tab.id);
                            // Auto-trigger 360° generation when switching to the tab if missing angles
                            if (tab.id === 'view360' && tempAvatar?.url && !auto360Progress) {
                              const loadedAngles = Object.values(angleImages).filter(Boolean).length;
                              if (loadedAngles < 4) {
                                const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
                                const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
                                const clothing360 = isDirectedMode ? 'keep_original' : (tempAvatar.clothing || 'company_uniform');
                                startAuto360(sourceUrl, clothing360, tempAvatar?.avatar_style || 'realistic');
                              }
                            }
                          }}
                          className={`flex-1 flex items-center justify-center gap-1.5 rounded-md py-2 text-[10px] font-semibold transition ${
                            effectiveTab === tab.id ? 'bg-[#C9A84C]/15 text-[#C9A84C]' : 'text-[#999] hover:text-[#888]'}`}>
                          <tab.icon size={12} /> {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* Clothing Tab */}
                    {effectiveTab === 'clothing' && (
                      <div className="space-y-3">
                        {/* Clothing gallery of generated variants */}
                        {Object.keys(clothingVariants).length > 1 && (
                          <div>
                            <p className="text-[11px] text-[#999] uppercase tracking-wider mb-1.5">{t('studio.my_avatars')}</p>
                            <div className="flex gap-2 flex-wrap">
                              {Object.entries(clothingVariants).map(([style, url]) => (
                                <button key={style} onClick={() => setTempAvatar(p => ({ ...p, url, clothing: style }))}
                                  className={`relative rounded-xl overflow-hidden border-2 transition ${
                                    tempAvatar?.clothing === style ? 'border-[#C9A84C] shadow-[0_0_8px_rgba(201,168,76,0.2)]' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}>
                                  <img src={resolveImageUrl(url)} alt={style} loading="lazy" decoding="async" className="w-14 h-20 object-cover" />
                                  {tempAvatar?.clothing === style && (
                                    <div className="absolute top-0.5 right-0.5 h-3.5 w-3.5 rounded-full bg-[#C9A84C] flex items-center justify-center">
                                      <Check size={7} className="text-black" />
                                    </div>
                                  )}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                        {/* Clothing style buttons */}
                        <div className="grid grid-cols-2 gap-2">
                          {[
                            { id: 'company_uniform', label: t('studio.clothing_uniform'), icon: Shirt },
                            { id: 'business_formal', label: t('studio.clothing_business'), icon: Briefcase },
                            { id: 'casual', label: t('studio.clothing_casual'), icon: Sun },
                            { id: 'streetwear', label: t('studio.clothing_streetwear'), icon: Layers },
                            { id: 'creative', label: t('studio.clothing_creative'), icon: Palette },
                          ].map(style => (
                            <button key={style.id} data-testid={`clothing-${style.id}`}
                              onClick={() => applyClothing(style.id)}
                              disabled={applyingClothing}
                              className={`rounded-xl border p-3 text-left transition ${
                                tempAvatar?.clothing === style.id ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'} disabled:opacity-40`}>
                              <div className="flex items-center gap-2">
                                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                                  tempAvatar?.clothing === style.id ? 'bg-[#C9A84C]/15' : 'bg-[#111] border border-[#222]'}`}>
                                  <style.icon size={14} className={tempAvatar?.clothing === style.id ? 'text-[#C9A84C]' : 'text-[#666]'} />
                                </div>
                                <div>
                                  <p className="text-[10px] text-white font-medium">{style.label}</p>
                                  {clothingVariants[style.id] && (
                                    <p className="text-[10px] text-green-400">{t('studio.avatar_ready')}</p>
                                  )}
                                </div>
                              </div>
                            </button>
                          ))}
                        </div>
                        {applyingClothing && (
                          <div className="text-center py-2">
                            <p className="text-xs text-[#C9A84C] flex items-center justify-center gap-1.5">
                              <Loader2 size={10} className="animate-spin" /> {t('studio.applying_style')}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* 360° View Tab */}
                    {effectiveTab === 'view360' && (
                      <div className="space-y-2">
                        {auto360Progress && (
                          <div className="flex items-center gap-2 text-xs text-[#C9A84C] bg-[#C9A84C]/10 rounded-lg px-3 py-1.5">
                            <Loader2 size={10} className="animate-spin" />
                            <span>{t('studio.auto_generating_360') || 'Generating 360°...'} {auto360Progress.completed}/4</span>
                            <div className="flex-1 h-1 bg-[#1E1E1E] rounded-full overflow-hidden">
                              <div className="h-full bg-[#C9A84C] transition-all duration-500 rounded-full" style={{width: `${(auto360Progress.completed / 4) * 100}%`}} />
                            </div>
                          </div>
                        )}
                        <div className="grid grid-cols-4 gap-2">
                        {[
                          { id: 'front', label: t('studio.angle_front') },
                          { id: 'left_profile', label: t('studio.angle_left') },
                          { id: 'right_profile', label: t('studio.angle_right') },
                          { id: 'back', label: t('studio.angle_back') },
                        ].map(angle => (
                          <div key={angle.id} data-testid={`angle-${angle.id}`}
                            className={`relative rounded-xl border overflow-hidden transition group/angle ${
                              angleImages[angle.id] ? 'border-[#C9A84C]/30' : 'border-[#1E1E1E] border-dashed'}`}>
                            <button
                              onClick={() => { if (angleImages[angle.id]) setTempAvatar(p => ({ ...p, url: angleImages[angle.id] })); else generateAngle(angle.id); }}
                              disabled={generatingAngle === angle.id}
                              className="w-full">
                              {angleImages[angle.id] ? (
                                <img src={resolveImageUrl(angleImages[angle.id])} alt={angle.label} loading="lazy" decoding="async" className="w-full aspect-[3/5] object-cover" />
                              ) : generatingAngle === angle.id ? (
                                <div className="w-full aspect-[3/5] flex items-center justify-center bg-[#111]">
                                  <Loader2 size={14} className="animate-spin text-[#C9A84C]" />
                                </div>
                              ) : (
                                <div className="w-full aspect-[3/5] flex items-center justify-center bg-[#0A0A0A]">
                                  <RotateCw size={14} className="text-[#777]" />
                                </div>
                              )}
                            </button>
                            {angleImages[angle.id] && generatingAngle !== angle.id && (
                              <button data-testid={`regen-angle-${angle.id}`}
                                onClick={(e) => { e.stopPropagation(); generateAngle(angle.id, true); }}
                                className="absolute top-1 right-1 h-5 w-5 rounded-full bg-black/70 border border-white/20 flex items-center justify-center opacity-0 group-hover/angle:opacity-100 transition"
                                title={t('studio.regenerate_angle')}>
                                <RefreshCw size={9} className="text-[#C9A84C]" />
                              </button>
                            )}
                            <p className="text-[11px] text-[#888] text-center py-1">{angle.label}</p>
                          </div>
                        ))}
                      </div>
                      {/* Regenerate All 360° button */}
                      {!auto360Progress && (
                        <button data-testid="regen-all-360-btn"
                          onClick={() => {
                            const is3d = tempAvatar?.avatar_style && tempAvatar.avatar_style !== 'realistic';
                            const sourceUrl = is3d ? tempAvatar.url : (tempAvatar.source_photo_url || tempAvatar.url);
                            setAngleImages({ front: tempAvatar.url });
                            startAuto360(sourceUrl, tempAvatar?.clothing || 'company_uniform', tempAvatar?.avatar_style || 'realistic');
                          }}
                          className="w-full rounded-lg border border-dashed border-[#C9A84C]/20 py-2 text-xs text-[#C9A84C] hover:bg-[#C9A84C]/5 transition flex items-center justify-center gap-1.5">
                          <RefreshCw size={10} /> {t('studio.regenerate_all_360') || 'Regenerate All 360°'}
                        </button>
                      )}
                      </div>
                    )}

                    {/* Voice Tab */}
                    {effectiveTab === 'voice' && (
                      <div className="space-y-3">
                        {/* Voice sub-tabs */}
                        <div className="flex gap-1">
                          <button onClick={() => setVoiceTab('bank')}
                            className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition ${voiceTab === 'bank' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                            {t('studio.voice_bank')}
                          </button>
                          <button onClick={() => setVoiceTab('premium')}
                            className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition flex items-center justify-center gap-1 ${voiceTab === 'premium' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                            <Crown size={9} /> {t('studio.premium_voices')}
                          </button>
                          <button onClick={() => setVoiceTab('record')}
                            className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition ${voiceTab === 'record' ? 'bg-[#C9A84C]/15 text-[#C9A84C] border border-[#C9A84C]/30' : 'border border-[#1E1E1E] text-[#999]'}`}>
                            {t('studio.custom_recording')}
                          </button>
                        </div>

                        {voiceTab === 'bank' ? (
                          <div className="space-y-1.5">
                            {[
                              { id: 'alloy', key: 'voice_alloy' },
                              { id: 'echo', key: 'voice_echo' },
                              { id: 'fable', key: 'voice_fable' },
                              { id: 'onyx', key: 'voice_onyx' },
                              { id: 'nova', key: 'voice_nova' },
                              { id: 'shimmer', key: 'voice_shimmer' },
                            ].map(v => (
                              <div key={v.id} data-testid={`voice-${v.id}`}
                                className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition ${
                                  tempAvatar?.voice?.type === 'openai' && tempAvatar?.voice?.voice_id === v.id
                                    ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}
                                onClick={() => setTempAvatar(p => ({ ...p, voice: { type: 'openai', voice_id: v.id } }))}>
                                <div className="flex-1">
                                  <p className="text-[10px] text-white font-medium capitalize">{v.id}</p>
                                  <p className="text-[11px] text-[#999]">{t(`studio.${v.key}`)}</p>
                                </div>
                                <button onClick={e => { e.stopPropagation(); previewVoice(v.id, 'openai'); }}
                                  disabled={loadingVoicePreview === v.id}
                                  className="h-7 w-7 rounded-lg border border-[#2A2A2A] flex items-center justify-center hover:bg-[#1A1A1A] transition disabled:opacity-40">
                                  {loadingVoicePreview === v.id ? (
                                    <Loader2 size={10} className="animate-spin text-[#C9A84C]" />
                                  ) : playingVoiceId === v.id ? (
                                    <Volume2 size={10} className="text-[#C9A84C]" />
                                  ) : (
                                    <Play size={10} className="text-[#999]" />
                                  )}
                                </button>
                                {tempAvatar?.voice?.type === 'openai' && tempAvatar?.voice?.voice_id === v.id && (
                                  <Check size={12} className="text-[#C9A84C] shrink-0" />
                                )}
                              </div>
                            ))}
                          </div>
                        ) : voiceTab === 'premium' ? (
                          <div className="space-y-1.5" data-testid="elevenlabs-voices-section">
                            {!elevenLabsAvailable && (
                              <div className="text-center py-3 border border-dashed border-[#2A2A2A] rounded-lg">
                                <Lock size={14} className="mx-auto text-[#999] mb-1" />
                                <p className="text-xs text-[#999]">ElevenLabs not configured</p>
                              </div>
                            )}
                            {elevenLabsAvailable && elevenLabsVoices.length === 0 && (
                              <div className="text-center py-3">
                                <Loader2 size={14} className="mx-auto text-[#C9A84C] animate-spin mb-1" />
                                <p className="text-xs text-[#999]">{t('studio.loading_voices')}</p>
                              </div>
                            )}
                            {elevenLabsVoices.map(v => (
                              <div key={v.id} data-testid={`voice-el-${v.name.toLowerCase()}`}
                                className={`flex items-center gap-2 rounded-lg border px-3 py-2 cursor-pointer transition ${
                                  tempAvatar?.voice?.type === 'elevenlabs' && tempAvatar?.voice?.voice_id === v.id
                                    ? 'border-[#C9A84C]/50 bg-[#C9A84C]/10' : 'border-[#1E1E1E] hover:border-[#2A2A2A]'}`}
                                onClick={() => setTempAvatar(p => ({ ...p, voice: { type: 'elevenlabs', voice_id: v.id } }))}>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-1.5">
                                    <p className="text-[10px] text-white font-medium">{v.name}</p>
                                    <Crown size={8} className="text-[#C9A84C] shrink-0" />
                                  </div>
                                  <p className="text-[11px] text-[#999] truncate">{v.style} · {v.accent} · {v.gender === 'female' ? '♀' : '♂'}</p>
                                </div>
                                <button onClick={e => { e.stopPropagation(); previewVoice(v.id, 'elevenlabs'); }}
                                  disabled={loadingVoicePreview === v.id}
                                  className="h-7 w-7 rounded-lg border border-[#2A2A2A] flex items-center justify-center hover:bg-[#1A1A1A] transition disabled:opacity-40">
                                  {loadingVoicePreview === v.id ? (
                                    <Loader2 size={10} className="animate-spin text-[#C9A84C]" />
                                  ) : playingVoiceId === v.id ? (
                                    <Volume2 size={10} className="text-[#C9A84C]" />
                                  ) : (
                                    <Play size={10} className="text-[#999]" />
                                  )}
                                </button>
                                {tempAvatar?.voice?.type === 'elevenlabs' && tempAvatar?.voice?.voice_id === v.id && (
                                  <Check size={12} className="text-[#C9A84C] shrink-0" />
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="space-y-3">
                            <div className="flex items-center justify-center gap-3 py-4">
                              {isRecording ? (
                                <button data-testid="stop-recording-btn" onClick={stopRecording}
                                  className="h-16 w-16 rounded-full bg-red-500 flex items-center justify-center animate-pulse hover:bg-red-600 transition">
                                  <Square size={20} className="text-white" />
                                </button>
                              ) : (
                                <button data-testid="start-recording-btn" onClick={startRecording}
                                  className="h-16 w-16 rounded-full border-2 border-[#C9A84C]/40 bg-[#C9A84C]/10 flex items-center justify-center hover:bg-[#C9A84C]/20 transition">
                                  <Mic size={24} className="text-[#C9A84C]" />
                                </button>
                              )}
                            </div>
                            <p className="text-xs text-center text-[#999]">
                              {isRecording ? t('studio.recording_in_progress') : recordedAudioUrl ? t('studio.play_preview') : t('studio.record')}
                            </p>
                            {recordedAudioUrl && (
                              <div className="space-y-2">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-[11px] text-[#C9A84C] font-medium uppercase tracking-wider">
                                    {avatarExtractedAudio ? t('studio.original_voice') : t('studio.recorded_voice')}
                                  </span>
                                </div>
                                <audio src={recordedAudioUrl} controls className="w-full h-8" style={{ filter: 'invert(1) hue-rotate(180deg)' }} />
                                <div className="flex gap-1.5">
                                  <button data-testid="master-voice-btn" onClick={async () => {
                                    let voiceUrl = tempAvatar?.voice?.url || recordedAudioUrl;
                                    if (!voiceUrl) return;
                                    setMasteringVoice(true);
                                    try {
                                      // If still a blob URL, upload first
                                      if (voiceUrl.startsWith('blob:') && recordedAudioBlob) {
                                        const ext = recordedAudioBlob.type.includes('mp4') ? 'mp4' : 'webm';
                                        const form = new FormData();
                                        form.append('file', recordedAudioBlob, `recording.${ext}`);
                                        const uploadRes = await axios.post(`${API}/campaigns/pipeline/upload-voice-recording`, form);
                                        if (uploadRes.data.audio_url) {
                                          voiceUrl = uploadRes.data.audio_url;
                                          setRecordedAudioUrl(voiceUrl);
                                          setTempAvatar(p => ({ ...p, voice: { type: 'custom', url: voiceUrl } }));
                                        } else { throw new Error('Upload failed'); }
                                      }
                                      const { data } = await axios.post(`${API}/campaigns/pipeline/master-voice`, { audio_url: voiceUrl });
                                      if (data.audio_url) {
                                        setRecordedAudioUrl(data.audio_url);
                                        setTempAvatar(p => ({ ...p, voice: { ...p?.voice, url: data.audio_url, mastered: true } }));
                                        toast.success(t('studio.voice_mastered'));
                                      }
                                    } catch (e) { toast.error(t('studio.err_generic')); }
                                    setMasteringVoice(false);
                                  }}
                                    disabled={masteringVoice || tempAvatar?.voice?.mastered}
                                    className={`flex-1 rounded-lg border py-2 text-xs font-bold flex items-center justify-center gap-1.5 transition disabled:opacity-40 ${
                                      tempAvatar?.voice?.mastered ? 'border-[#10B981]/30 text-[#10B981] bg-[#10B981]/5' : 'border-[#C9A84C]/30 text-[#C9A84C] hover:bg-[#C9A84C]/5'}`}>
                                    {masteringVoice ? <><Loader2 size={10} className="animate-spin" /> {t('studio.mastering')}</> :
                                     tempAvatar?.voice?.mastered ? <><Check size={10} /> {t('studio.mastered')}</> :
                                     <><Sparkles size={10} /> {t('studio.master_voice')}</>}
                                  </button>
                                  <button data-testid="save-recording-btn" onClick={saveRecordingAsVoice}
                                    disabled={uploadingRecording}
                                    className="flex-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2 text-xs font-bold text-black flex items-center justify-center gap-1.5 disabled:opacity-50">
                                    {uploadingRecording ? (
                                      <><Loader2 size={10} className="animate-spin" /> {t('studio.uploading_recording')}</>
                                    ) : (
                                      <><Check size={10} /> {t('studio.use') || 'Use'}</>
                                    )}
                                  </button>
                                </div>
                              </div>
                            )}
                            {tempAvatar?.voice?.type === 'custom' && (
                              <div className="flex items-center gap-1.5 text-xs text-green-400">
                                <Check size={10} /> {t('studio.recording_saved')}
                              </div>
                            )}
                          </div>
                        )}
                        {/* No voice option */}
                        <button onClick={() => setTempAvatar(p => ({ ...p, voice: null }))}
                          className={`w-full rounded-lg border px-3 py-2 text-xs text-center transition ${
                            !tempAvatar?.voice ? 'border-[#C9A84C]/30 bg-[#C9A84C]/5 text-[#C9A84C]' : 'border-[#1E1E1E] text-[#999] hover:border-[#2A2A2A]'}`}>
                          {t('studio.no_voice')}
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Video Preview Controls */}
              {avatarStage === 'customize' && tempAvatar?.url && (
                <div className="px-5 py-2 border-t border-[#151515]/50 shrink-0 space-y-2">
                  {/* Language Selector + Generate/Regenerate */}
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-[#999] uppercase tracking-wider">{t('studio.test_language') || 'Language'}:</span>
                    <div className="flex gap-1">
                      {[{id:'pt',label:'PT'},{id:'en',label:'EN'},{id:'es',label:'ES'}].map(lang => (
                        <button key={lang.id} onClick={() => setPreviewLanguage(lang.id)}
                          className={`px-2 py-0.5 rounded text-[11px] font-bold transition ${
                            previewLanguage === lang.id ? 'bg-[#C9A84C]/20 text-[#C9A84C] border border-[#C9A84C]/30' : 'text-[#999] border border-[#1E1E1E] hover:border-[#333]'}`}>
                          {lang.label}
                        </button>
                      ))}
                    </div>
                    {previewVideoUrl && (
                      <button onClick={() => { setPreviewVideoUrl(null); setAvatarMediaTab('photo'); }}
                        className="ml-auto text-[11px] text-[#C9A84C] hover:underline">{t('studio.regenerate') || 'Regenerate'}</button>
                    )}
                  </div>
                  <button data-testid="generate-preview-video-btn"
                    onClick={async () => {
                      setGeneratingPreviewVideo(true);
                      setAvatarMediaTab('video');
                      try {
                        const voice = tempAvatar?.voice;
                        const { data } = await axios.post(`${API}/campaigns/pipeline/avatar-video-preview`, {
                          avatar_url: tempAvatar.url,
                          voice_url: voice?.url || '',
                          voice_id: voice?.voice_id || '',
                          language: previewLanguage,
                        });
                        if (data.job_id) {
                          const pollInterval = setInterval(async () => {
                            try {
                              const { data: status } = await axios.get(`${API}/campaigns/pipeline/avatar-video-preview/${data.job_id}`);
                              if (status.status === 'completed' && status.video_url) {
                                clearInterval(pollInterval);
                                setPreviewVideoUrl(status.video_url);
                                setGeneratingPreviewVideo(false);
                                setAvatarMediaTab('video');
                                toast.success(t('studio.preview_generated'));
                              } else if (status.status === 'failed') {
                                clearInterval(pollInterval);
                                setGeneratingPreviewVideo(false);
                                setAvatarMediaTab('photo');
                                toast.error(status.error || t('studio.err_generic'));
                              }
                            } catch { /* keep polling */ }
                          }, 5000);
                        }
                      } catch (e) {
                        toast.error(t('studio.err_generic'));
                        setGeneratingPreviewVideo(false);
                        setAvatarMediaTab('photo');
                      }
                    }}
                    disabled={generatingPreviewVideo}
                    className="w-full rounded-lg border border-dashed border-[#C9A84C]/20 py-2 text-xs text-[#C9A84C] hover:bg-[#C9A84C]/5 transition flex items-center justify-center gap-1.5 disabled:opacity-40">
                    {generatingPreviewVideo ? <><Loader2 size={10} className="animate-spin" /> {t('studio.generating_preview')}</> :
                     previewVideoUrl ? <><Play size={10} /> {t('studio.regenerate_preview') || 'Regenerate Preview'}</> :
                     <><Play size={10} /> {t('studio.generate_video_preview')}</>}
                  </button>
                </div>
              )}

              {/* Footer */}
              {avatarStage === 'customize' && (
                <div className="px-5 py-3 border-t border-[#151515] shrink-0 flex gap-2">
                  {editingAvatarId ? (
                    <>
                      <button data-testid="save-avatar-as-new-btn" onClick={saveAvatarAsNew}
                        className="flex-1 rounded-lg border border-[#C9A84C]/40 py-2.5 text-xs font-bold text-[#C9A84C] hover:bg-[#C9A84C]/10 transition flex items-center justify-center gap-2">
                        <Plus size={14} /> {t('studio.save_as_new')}
                      </button>
                      <button data-testid="save-avatar-final-btn" onClick={saveAvatarAndClose}
                        className="flex-1 rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-xs font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2">
                        <Check size={14} /> {t('studio.update_avatar')}
                      </button>
                    </>
                  ) : (
                    <button data-testid="save-avatar-final-btn" onClick={saveAvatarAndClose}
                      className="w-full rounded-lg bg-gradient-to-r from-[#C9A84C] to-[#D4B85A] py-2.5 text-xs font-bold text-black hover:opacity-90 transition flex items-center justify-center gap-2">
                      <Check size={14} /> {t('studio.save_avatar')}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
  );
}
