import { useState, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * useAvatarManager - SINGLE SOURCE OF TRUTH for all avatar/character operations
 * 
 * Used by:
 * - PipelineView.jsx (Campaign avatars)
 * - StudioPage.jsx (Global character gallery)
 * - DirectedStudio.jsx (Project characters)
 * 
 * This hook centralizes ALL avatar state and logic to avoid code duplication.
 */
export function useAvatarManager({ 
  onAvatarSaved,
  onAvatarDeleted,
  apiEndpoint = '/data/avatars',
  isDirectedMode = false
} = {}) {
  
  // ═══════════════════════════════════════════════════════════
  // STATE - All avatar-related state in one place
  // ═══════════════════════════════════════════════════════════
  
  const [showAvatarModal, setShowAvatarModal] = useState(false);
  const [editingAvatarId, setEditingAvatarId] = useState(null);
  const [tempAvatar, setTempAvatar] = useState(null);
  const [avatarName, setAvatarName] = useState('');
  
  // Creation/Upload
  const [avatarStage, setAvatarStage] = useState('upload');
  const [avatarCreationMode, setAvatarCreationMode] = useState('photo');
  const [avatarSourceType, setAvatarSourceType] = useState('video');
  const [avatarSourcePhoto, setAvatarSourcePhoto] = useState(null);
  const [avatarVideoUploading, setAvatarVideoUploading] = useState(false);
  const [avatarExtractedAudio, setAvatarExtractedAudio] = useState(null);
  const [avatarVideoFrames, setAvatarVideoFrames] = useState([]);
  const [avatarPhotoUploading, setAvatarPhotoUploading] = useState(false);
  
  // Prompt generation
  const [avatarPromptText, setAvatarPromptText] = useState('');
  const [avatarPromptGender, setAvatarPromptGender] = useState('female');
  const [avatarPromptStyle, setAvatarPromptStyle] = useState('realistic');
  const [generatingAvatar, setGeneratingAvatar] = useState(false);
  
  // Customization
  const [customizeTab, setCustomizeTab] = useState('clothing');
  const [clothingVariants, setClothingVariants] = useState({});
  const [applyingClothing, setApplyingClothing] = useState(false);
  const [angleImages, setAngleImages] = useState({});
  const [generatingAngle, setGeneratingAngle] = useState(false);
  const [auto360Progress, setAuto360Progress] = useState(null);
  
  // Voice
  const [voiceTab, setVoiceTab] = useState('bank');
  const [previewLanguage, setPreviewLanguage] = useState('pt');
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudioUrl, setRecordedAudioUrl] = useState(null);
  const [recordedAudioBlob, setRecordedAudioBlob] = useState(null);
  const [uploadingRecording, setUploadingRecording] = useState(false);
  const [loadingVoicePreview, setLoadingVoicePreview] = useState(null);
  const [playingVoiceId, setPlayingVoiceId] = useState(null);
  
  // AI Edit
  const [aiEditAvatarId, setAiEditAvatarId] = useState(null);
  const [aiEditInstruction, setAiEditInstruction] = useState('');
  const [aiEditLoading, setAiEditLoading] = useState(false);
  const [avatarEditHistory, setAvatarEditHistory] = useState([]);
  const [avatarBaseUrl, setAvatarBaseUrl] = useState(null);
  
  // Preview
  const [avatarMediaTab, setAvatarMediaTab] = useState('photo');
  const [generatingPreviewVideo, setGeneratingPreviewVideo] = useState(false);
  const [previewVideoUrl, setPreviewVideoUrl] = useState(null);
  const [avatarPreviewUrl, setAvatarPreviewUrl] = useState(null);
  const [masteringVoice, setMasteringVoice] = useState(false);
  const [accuracyProgress, setAccuracyProgress] = useState(null);
  
  // ═══════════════════════════════════════════════════════════
  // CORE FUNCTIONS - Avatar lifecycle operations
  // ═══════════════════════════════════════════════════════════
  
  const resetAvatarModal = useCallback(() => {
    setShowAvatarModal(false);
    setEditingAvatarId(null);
    setTempAvatar(null);
    setAvatarName('');
    setAvatarSourcePhoto(null);
    setAvatarSourceType('video');
    setAvatarVideoUploading(false);
    setAvatarExtractedAudio(null);
    setAvatarVideoFrames([]);
    setAvatarStage('upload');
    setAvatarCreationMode('photo');
    setAvatarPromptText('');
    setAvatarPromptGender('female');
    setAvatarPromptStyle('realistic');
    setCustomizeTab('clothing');
    setAvatarEditHistory([]);
    setAvatarBaseUrl(null);
    setAngleImages({});
    setClothingVariants({});
    setAuto360Progress(null);
    setRecordedAudioUrl(null);
    setRecordedAudioBlob(null);
    setPreviewVideoUrl(null);
    setPreviewLanguage('pt');
    setAvatarMediaTab('photo');
    setAccuracyProgress(null);
    setVoiceTab('bank');
    setAiEditAvatarId(null);
    setAiEditInstruction('');
  }, []);
  
  const openAvatarForEdit = useCallback((avatar) => {
    console.log('🎨 openAvatarForEdit:', avatar.name, avatar.id);
    
    setEditingAvatarId(avatar.id);
    
    // Infer avatar_style from creation_mode for avatars saved before the fix
    let inferredStyle = avatar.avatar_style || 'realistic';
    if (!avatar.avatar_style && avatar.creation_mode === '3d') {
      inferredStyle = '3d_pixar';
    }
    const is3dAvatar = inferredStyle !== 'realistic';
    
    setTempAvatar({
      url: avatar.url,
      source_photo_url: avatar.source_photo_url || '',
      clothing: avatar.clothing || 'company_uniform',
      voice: avatar.voice || null,
      avatar_style: inferredStyle,
      creation_mode: avatar.creation_mode || 'photo',
    });
    
    setAvatarName(avatar.name || '');
    setPreviewVideoUrl(avatar.video_url || null);
    setAvatarMediaTab(avatar.video_url ? 'photo' : 'photo');
    
    // For 3D avatars, only load angles that were generated with 3D style
    const savedAngles = avatar.angles || {};
    if (is3dAvatar && savedAngles.front && savedAngles.front !== avatar.url) {
      setAngleImages({ front: avatar.url });
    } else {
      setAngleImages(savedAngles.front ? savedAngles : { front: avatar.url });
    }
    
    setPreviewLanguage(avatar.language || 'pt');
    
    // Restore audio from saved voice
    if (avatar.voice?.url) {
      setRecordedAudioUrl(avatar.voice.url);
      setVoiceTab('record');
    } else if (avatar.voice?.type === 'elevenlabs' && avatar.voice?.voice_id) {
      setVoiceTab('premium');
    } else if (avatar.voice?.voice_id) {
      setVoiceTab('bank');
    }
    
    // Rebuild clothing variants from angles if available
    const variants = {};
    if (avatar.clothing && avatar.url) variants[avatar.clothing] = avatar.url;
    setClothingVariants(variants);
    
    setAvatarStage('customize');
    setCustomizeTab('clothing');
    setShowAvatarModal(true);
    
    // Load saved edit history or initialize with current avatar as base
    const savedHistory = avatar.edit_history && avatar.edit_history.length > 0 ? avatar.edit_history : [];
    if (savedHistory.length > 0) {
      setAvatarEditHistory(savedHistory);
      const baseEntry = savedHistory.find(e => e.isBase);
      setAvatarBaseUrl(baseEntry ? baseEntry.url : avatar.url);
    } else {
      setAvatarBaseUrl(avatar.url);
      setAvatarEditHistory([{ 
        url: avatar.url, 
        instruction: 'Base original', 
        timestamp: new Date().toISOString(), 
        isBase: true 
      }]);
    }
    
    console.log('✅ Avatar modal OPENED for editing');
  }, []);
  
  const saveAvatarAndClose = useCallback(async () => {
    console.log('💾 saveAvatarAndClose');
    
    if (!tempAvatar?.url) {
      toast.error('Nenhum avatar para salvar');
      return;
    }
    
    try {
      const payload = {
        id: editingAvatarId,
        url: tempAvatar.url,
        name: avatarName || 'Novo Personagem',
        avatar_style: tempAvatar.avatar_style || avatarPromptStyle || 'realistic',
        creation_mode: tempAvatar.creation_mode || avatarCreationMode || 'prompt',
        source_photo_url: tempAvatar.source_photo_url || avatarSourcePhoto || '',
        clothing: tempAvatar.clothing || 'keep_original',
        voice: tempAvatar.voice || null,
        angles: angleImages || {},
        video_url: previewVideoUrl || null,
        language: previewLanguage || 'pt',
        edit_history: avatarEditHistory || []
      };
      
      console.log('📡 Salvando avatar:', payload);
      const response = await axios.post(`${API}${apiEndpoint}`, payload);
      console.log('✅ Resposta do backend:', response.data);
      
      const entityLabel = isDirectedMode ? 'Personagem' : 'Avatar';
      toast.success(`✅ ${entityLabel} salvo com sucesso!`);
      
      resetAvatarModal();
      
      // Notify parent component
      if (onAvatarSaved) {
        onAvatarSaved(response.data);
      }
      
      return response.data;
    } catch (err) {
      console.error('❌ Error saving avatar:', err);
      console.error('❌ Error response:', err.response?.data);
      toast.error('Erro ao salvar: ' + (err.response?.data?.detail || err.message));
      return null;
    }
  }, [
    tempAvatar, avatarName, editingAvatarId, avatarPromptStyle, avatarCreationMode,
    avatarSourcePhoto, angleImages, previewVideoUrl, previewLanguage, avatarEditHistory,
    apiEndpoint, isDirectedMode, onAvatarSaved, resetAvatarModal
  ]);
  
  const deleteAvatar = useCallback(async (avatarId) => {
    try {
      await axios.delete(`${API}${apiEndpoint}/${avatarId}`);
      toast.success('Avatar excluído com sucesso!');
      
      if (onAvatarDeleted) {
        onAvatarDeleted(avatarId);
      }
      
      return true;
    } catch (err) {
      console.error('❌ Error deleting avatar:', err);
      toast.error('Erro ao excluir avatar');
      return false;
    }
  }, [apiEndpoint, onAvatarDeleted]);
  
  // ═══════════════════════════════════════════════════════════
  // RETURN - Expose all state and functions
  // ═══════════════════════════════════════════════════════════
  
  return {
    // State
    showAvatarModal,
    editingAvatarId,
    tempAvatar,
    avatarName,
    avatarStage,
    avatarCreationMode,
    avatarSourceType,
    avatarSourcePhoto,
    avatarVideoUploading,
    avatarExtractedAudio,
    avatarVideoFrames,
    avatarPhotoUploading,
    avatarPromptText,
    avatarPromptGender,
    avatarPromptStyle,
    generatingAvatar,
    customizeTab,
    clothingVariants,
    applyingClothing,
    angleImages,
    generatingAngle,
    auto360Progress,
    voiceTab,
    previewLanguage,
    isRecording,
    recordedAudioUrl,
    recordedAudioBlob,
    uploadingRecording,
    loadingVoicePreview,
    playingVoiceId,
    aiEditAvatarId,
    aiEditInstruction,
    aiEditLoading,
    avatarEditHistory,
    avatarBaseUrl,
    avatarMediaTab,
    generatingPreviewVideo,
    previewVideoUrl,
    avatarPreviewUrl,
    masteringVoice,
    accuracyProgress,
    
    // Setters (expose for modal to use)
    setShowAvatarModal,
    setEditingAvatarId,
    setTempAvatar,
    setAvatarName,
    setAvatarStage,
    setAvatarCreationMode,
    setAvatarSourceType,
    setAvatarSourcePhoto,
    setAvatarVideoUploading,
    setAvatarExtractedAudio,
    setAvatarVideoFrames,
    setAvatarPhotoUploading,
    setAvatarPromptText,
    setAvatarPromptGender,
    setAvatarPromptStyle,
    setGeneratingAvatar,
    setCustomizeTab,
    setClothingVariants,
    setApplyingClothing,
    setAngleImages,
    setGeneratingAngle,
    setAuto360Progress,
    setVoiceTab,
    setPreviewLanguage,
    setIsRecording,
    setRecordedAudioUrl,
    setRecordedAudioBlob,
    setUploadingRecording,
    setLoadingVoicePreview,
    setPlayingVoiceId,
    setAiEditAvatarId,
    setAiEditInstruction,
    setAiEditLoading,
    setAvatarEditHistory,
    setAvatarBaseUrl,
    setAvatarMediaTab,
    setGeneratingPreviewVideo,
    setPreviewVideoUrl,
    setAvatarPreviewUrl,
    setMasteringVoice,
    setAccuracyProgress,
    
    // Core functions
    resetAvatarModal,
    openAvatarForEdit,
    saveAvatarAndClose,
    deleteAvatar,
  };
}
