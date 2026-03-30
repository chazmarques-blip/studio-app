# 🔧 Guia de Restauração Completa da Edição de Avatares

**Data**: 29/03/2026  
**Status**: Funcionalidade Parcialmente Implementada  
**Prioridade**: MÉDIA

---

## 📋 **Contexto**

A funcionalidade de **edição de avatares e personagens** no `DirectedStudio` está quebrada no `StudioPage.jsx` porque:

1. O `StudioPage` não implementa o `AvatarModal` completo
2. As funções `handleEditAvatar` e `handleAddAvatar` são apenas stubs
3. O `PipelineView.jsx` tem a implementação completa, mas não foi portada

---

## ✅ **O que JÁ está funcionando:**

- ✅ **Visualização/Zoom de avatares** → Modal funcional
- ✅ **Criação de avatares via botão "Criar"** → DirectedStudio gerencia internamente
- ✅ **Importação via "Acervo"** → AvatarLibraryModal funciona
- ✅ **Remoção de avatares**
- ✅ **Linking de avatares a personagens**

---

## ❌ **O que NÃO está funcionando:**

- ❌ **Botão "Editar" (ícone PenTool)** → Não abre modal de edição
- ❌ **Edição com IA de avatares** → `aiEditAvatarId` não ativa overlay
- ❌ **Customização de roupas/ângulos** → Requer AvatarModal completo
- ❌ **Gravação de voz para avatar** → Requer AvatarModal completo

---

## 🛠️ **Como Restaurar Completamente**

### **Opção 1: Implementação Completa (Recomendado para Produção)**

#### **Passo 1: Copiar Estados do PipelineView**

No `StudioPage.jsx`, adicionar TODOS os estados do avatar do `/app/frontend/src/components/PipelineView.jsx` (linhas 92-148):

```javascript
// Avatar Gallery states
const [avatars, setAvatars] = useState([]);
const [selectedAvatarId, setSelectedAvatarId] = useState(null);
const [showAvatarModal, setShowAvatarModal] = useState(false);
const [avatarSourcePhoto, setAvatarSourcePhoto] = useState(null);
const [avatarSourceType, setAvatarSourceType] = useState('video');
const [avatarVideoUploading, setAvatarVideoUploading] = useState(false);
const [avatarExtractedAudio, setAvatarExtractedAudio] = useState(null);
const [avatarVideoFrames, setAvatarVideoFrames] = useState([]);
const [masteringVoice, setMasteringVoice] = useState(false);
const [generatingPreviewVideo, setGeneratingPreviewVideo] = useState(false);
const [previewVideoUrl, setPreviewVideoUrl] = useState(null);
const [previewLanguage, setPreviewLanguage] = useState('pt');
const [avatarName, setAvatarName] = useState('');
const [avatarMediaTab, setAvatarMediaTab] = useState('photo');
const [accuracyProgress, setAccuracyProgress] = useState(null);
const [generatingAvatar, setGeneratingAvatar] = useState(false);
const [avatarPhotoUploading, setAvatarPhotoUploading] = useState(false);
const [avatarStage, setAvatarStage] = useState('upload');
const [avatarCreationMode, setAvatarCreationMode] = useState('photo');
const [avatarPromptText, setAvatarPromptText] = useState('');
const [avatarPromptGender, setAvatarPromptGender] = useState('female');
const [avatarPromptStyle, setAvatarPromptStyle] = useState('custom');
const [tempAvatar, setTempAvatar] = useState(null);
const [editingAvatarId, setEditingAvatarId] = useState(null);
const [customizeTab, setCustomizeTab] = useState('clothing');
const [applyingClothing, setApplyingClothing] = useState(false);
const [clothingVariants, setClothingVariants] = useState({});
const [generatingAngle, setGeneratingAngle] = useState(null);
const [angleImages, setAngleImages] = useState({});
const [auto360Progress, setAuto360Progress] = useState(null);
const [voiceTab, setVoiceTab] = useState('bank');
const [loadingVoicePreview, setLoadingVoicePreview] = useState(null);
const [playingVoiceId, setPlayingVoiceId] = useState(null);
const [elevenLabsVoices, setElevenLabsVoices] = useState([]);
const [elevenLabsAvailable, setElevenLabsAvailable] = useState(false);
const [isRecording, setIsRecording] = useState(false);
const [recordedAudioUrl, setRecordedAudioUrl] = useState(null);
const [recordedAudioBlob, setRecordedAudioBlob] = useState(null);
const [uploadingRecording, setUploadingRecording] = useState(false);
const [avatarEditHistory, setAvatarEditHistory] = useState([]);
const [avatarBaseUrl, setAvatarBaseUrl] = useState(null);

// Refs
const avatarInputRef = useRef(null);
const mediaRecorderRef = useRef(null);
const audioChunksRef = useRef([]);
const audioPlayerRef = useRef(null);
```

#### **Passo 2: Copiar Funções Helper**

Copiar as funções do PipelineView (linhas 550-700):
- `resetAvatarModal()`
- `openAvatarForEdit(av)`
- `saveAvatarAndClose()`
- `saveAvatarAsNew()`
- `generateAvatarFromPhoto()`
- `generateAvatarFromPrompt()`
- `applyClothing()`
- `generateAngle()`
- Etc...

#### **Passo 3: Importar e Renderizar AvatarModal**

```javascript
import { AvatarModal } from '../components/pipeline/AvatarModal';

// No JSX, antes de fechar o componente:
{showAvatarModal && (
  <AvatarModal ctx={{
    showAvatarModal,
    avatarStage,
    avatarCreationMode,
    // ... passar TODOS os estados e funções
    resetAvatarModal,
    generateAvatarFromPhoto,
    // etc...
  }} />
)}
```

#### **Passo 4: Atualizar Handlers**

```javascript
const handleEditAvatar = useCallback((av) => {
  openAvatarForEdit(av);
}, []);

const handleAddAvatar = useCallback((promptText) => {
  resetAvatarModal();
  if (promptText) {
    setAvatarPromptText(promptText);
    setAvatarCreationMode('prompt');
  }
  setShowAvatarModal(true);
}, []);
```

---

### **Opção 2: Solução Intermediária (Mais Rápida)**

Se o tempo for curto, implementar apenas edição inline com IA:

```javascript
const [showAiEditOverlay, setShowAiEditOverlay] = useState(false);
const [editingAvatar, setEditingAvatar] = useState(null);

const handleEditAvatar = useCallback((av) => {
  setEditingAvatar(av);
  setShowAiEditOverlay(true);
}, []);

// Criar modal simples de edição com IA:
{showAiEditOverlay && editingAvatar && (
  <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center">
    <div className="bg-[#0D0D0D] p-6 rounded-xl max-w-md">
      <h3>Editar Avatar: {editingAvatar.name}</h3>
      <textarea
        value={aiEditInstruction}
        onChange={(e) => setAiEditInstruction(e.target.value)}
        placeholder="Descreva as mudanças desejadas..."
        className="w-full p-3 bg-[#1A1A1A] rounded mt-3"
        rows={4}
      />
      <div className="flex gap-2 mt-4">
        <button onClick={applyAiEdit}>Aplicar</button>
        <button onClick={() => setShowAiEditOverlay(false)}>Cancelar</button>
      </div>
    </div>
  </div>
)}
```

---

## 📝 **Arquivos de Referência**

- **Implementação Completa**: `/app/frontend/src/components/PipelineView.jsx` (linhas 90-700)
- **Modal de Avatar**: `/app/frontend/src/components/pipeline/AvatarModal.jsx`
- **Modal de Biblioteca**: `/app/frontend/src/components/pipeline/AvatarLibraryModal.jsx`
- **Handlers**: `/app/frontend/src/components/PipelineView.jsx` (linhas 262-282)

---

## 🧪 **Como Testar Após Implementação**

1. Login → `/studio`
2. Abrir projeto
3. Ir para aba "PERSONAGENS"
4. Passar mouse sobre avatar
5. Clicar no ícone **PenTool (✏️)**
6. Modal de edição deve abrir
7. Customizar roupa/ângulo/voz
8. Salvar e verificar mudanças

---

## ⚠️ **Notas Importantes**

- O `DirectedStudio` usa **project-scoped avatars** (armazenados no projeto)
- O `PipelineView` usa **avatares globais** (compartilhados entre campanhas)
- A implementação deve respeitar essa diferença
- **Não** quebrar a funcionalidade de auto-geração de personagens que já funciona

---

## 🎯 **Estimativa de Esforço**

- **Opção 1 (Completa)**: ~3-4 horas
- **Opção 2 (Intermediária)**: ~1 hora

---

**Status Atual (29/03/2026):**
- ✅ Modal de zoom funciona
- ⚠️ Botão editar mostra toast informativo
- ❌ Modal de edição completo não implementado
