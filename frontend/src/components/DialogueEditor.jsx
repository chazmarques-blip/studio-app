import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import {
  Mic, BookOpen, Users, Sparkles, Save, ChevronDown, ChevronUp,
  Loader2, Volume2, RefreshCw, MessageSquare, Play, Square, Type, Move,
  AlignLeft, AlignCenter, AlignRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BOOK_FONTS = [
  { id: 'serif', label: 'Serif (Clássico)', css: 'Georgia, serif' },
  { id: 'sans', label: 'Sans (Moderno)', css: 'system-ui, sans-serif' },
  { id: 'handwrite', label: 'Handwritten', css: "'Comic Sans MS', cursive" },
  { id: 'mono', label: 'Monospace', css: "'Courier New', monospace" },
];

const FONT_SIZES = [
  { id: 'xs', label: 'P', px: 10 },
  { id: 'sm', label: 'M', px: 12 },
  { id: 'md', label: 'G', px: 14 },
  { id: 'lg', label: 'XG', px: 16 },
];

const TEXT_POSITIONS = [
  { id: 'top', label: 'Topo' },
  { id: 'center', label: 'Centro' },
  { id: 'bottom', label: 'Rodapé' },
];

export function DialogueEditor({ projectId, lang, scenes: propScenes, onComplete, onBack }) {
  const [activeTab, setActiveTab] = useState('dubbed');
  const [scenesData, setScenesData] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [voices, setVoices] = useState([]);
  const [characterVoices, setCharacterVoices] = useState({});
  const [autoVoiceInfo, setAutoVoiceInfo] = useState({});
  const [narratorVoice, setNarratorVoice] = useState('21m00Tcm4TlvDq8ikWAM');
  const [expandedScene, setExpandedScene] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [generatingScene, setGeneratingScene] = useState(null);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [hasChanges, setHasChanges] = useState(false);
  // Audio preview
  const [previewingVoice, setPreviewingVoice] = useState(null);
  const audioRef = useRef(null);
  // Book formatting per scene
  const [bookFormats, setBookFormats] = useState({});
  const [needsDubbedGen, setNeedsDubbedGen] = useState(0);

  const token = localStorage.getItem('studiox_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    const loadData = async () => {
      try {
        const dialogueRes = await axios.get(`${API}/studio/projects/${projectId}/dialogues`, { headers });
        const d = dialogueRes.data;
        setScenesData(d.scenes || []);
        setCharacters(d.characters || []);
        const autoVoices = d.character_voices || {};
        const voiceMap = {};
        Object.entries(autoVoices).forEach(([name, info]) => {
          voiceMap[name] = info.voice_id || '';
        });
        setCharacterVoices(voiceMap);
        setAutoVoiceInfo(autoVoices);
        if (d.narrator_voice) setNarratorVoice(d.narrator_voice);

        // Init book formats from saved data
        const formats = {};
        (d.scenes || []).forEach(s => {
          formats[s.scene_number] = s.book_format || { font: 'serif', size: 'sm', position: 'bottom', align: 'left' };
        });
        setBookFormats(formats);

        // Check if dubbed dialogues need generation
        const needsDubbed = d.scenes_needing_dubbed || 0;
        if (needsDubbed > 0 && activeTab === 'dubbed') {
          setNeedsDubbedGen(needsDubbed);
        }

        try {
          const voicesRes = await axios.get(`${API}/studio/voices`, { headers });
          setVoices(voicesRes.data.voices || []);
        } catch { setVoices([]); }
      } catch (e) {
        toast.error(lang === 'pt' ? 'Erro ao carregar diálogos' : 'Error loading dialogues');
      }
      setLoading(false);
    };
    loadData();
  }, [projectId]);

  const getTextField = (scene) => {
    if (activeTab === 'dubbed') {
      // Prioritize dubbed_text, then dialogue ONLY if it has character format (contains ":")
      const dubbed = scene.dubbed_text || '';
      if (dubbed.trim()) return dubbed;
      const dialogue = scene.dialogue || '';
      // Check if dialogue has character format (CharName: "text")
      if (dialogue.includes(':') && !dialogue.toLowerCase().startsWith('narraç')) return dialogue;
      return '';
    }
    if (activeTab === 'narrated') return scene.narrated_text || scene.narration || '';
    return scene.book_text || '';
  };

  const updateSceneText = (sceneNumber, text) => {
    setScenesData(prev => prev.map(s => {
      if (s.scene_number !== sceneNumber) return s;
      const field = activeTab === 'dubbed' ? 'dubbed_text' : activeTab === 'narrated' ? 'narrated_text' : 'book_text';
      return { ...s, [field]: text };
    }));
    setHasChanges(true);
  };

  const updateBookFormat = (sceneNumber, key, value) => {
    setBookFormats(prev => ({
      ...prev,
      [sceneNumber]: { ...(prev[sceneNumber] || {}), [key]: value }
    }));
    setHasChanges(true);
  };

  // Master Generate: Uses full story context for higher quality
  const masterGenerateWithAI = async () => {
    setGenerating(true);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/dialogues/master-generate`, {
        mode: activeTab,
        user_instructions: "", // Can be customized
        regenerate_all: true,
      }, { headers, timeout: 180000 }); // 3 minutes for full generation
      
      const dialogues = res.data.dialogues || [];
      setScenesData(prev => prev.map(s => {
        const match = dialogues.find(d => d.scene_number === s.scene_number);
        if (!match) return s;
        const field = activeTab === 'dubbed' ? 'dubbed_text' : activeTab === 'narrated' ? 'narrated_text' : 'book_text';
        return { ...s, [field]: match.dialogue };
      }));
      setHasChanges(true);
      toast.success(`${dialogues.length} ${lang === 'pt' ? 'cena(s) gerada(s) com Master AI!' : 'scene(s) generated with Master AI!'}`);
      if (activeTab === 'dubbed') setNeedsDubbedGen(0);
    } catch (e) {
      console.error('Master generate error:', e);
      // Fallback to regular generation
      toast.error(lang === 'pt' ? 'Usando geração alternativa...' : 'Using fallback generation...');
      await generateWithAI([]);
    }
    setGenerating(false);
  };

  const generateWithAI = async (sceneNumbers = []) => {
    const isAll = sceneNumbers.length === 0;
    
    // If generating all, use master generator for better quality
    if (isAll) {
      return masterGenerateWithAI();
    }
    
    setGeneratingScene(sceneNumbers[0]);
    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/dialogues/generate`, {
        mode: activeTab, scene_numbers: sceneNumbers,
      }, { headers, timeout: 120000 });
      const results = res.data.results || [];
      setScenesData(prev => prev.map(s => {
        const match = results.find(r => r.scene_number === s.scene_number);
        if (!match) return s;
        const field = activeTab === 'dubbed' ? 'dubbed_text' : activeTab === 'narrated' ? 'narrated_text' : 'book_text';
        return { ...s, [field]: match.generated_text };
      }));
      setHasChanges(true);
      toast.success(`${results.length} ${lang === 'pt' ? 'cena(s) gerada(s)' : 'scene(s) generated'}`);
      if (activeTab === 'dubbed') setNeedsDubbedGen(0);
    } catch (e) {
      toast.error(lang === 'pt' ? 'Erro ao gerar com IA' : 'AI generation error');
    }
    setGeneratingScene(null);
  };

  const saveDialogues = async () => {
    setSaving(true);
    try {
      await axios.patch(`${API}/studio/projects/${projectId}/dialogues/save`, {
        scenes_dialogue: scenesData.map(s => ({
          scene_number: s.scene_number,
          dubbed_text: s.dubbed_text || '', narrated_text: s.narrated_text || '',
          book_text: s.book_text || '', book_format: bookFormats[s.scene_number] || {},
          dialogue: s.dubbed_text || s.dialogue || '',
          narration: s.narrated_text || s.narration || '',
        })),
        character_voices: characterVoices, narrator_voice: narratorVoice,
      }, { headers });
      setHasChanges(false);
      toast.success(lang === 'pt' ? 'Diálogos salvos!' : 'Dialogues saved!');
    } catch (e) {
      toast.error(lang === 'pt' ? 'Erro ao salvar' : 'Save error');
    }
    setSaving(false);
  };

  // Audio Preview: generate a short TTS sample
  const previewVoice = async (voiceId, sampleText) => {
    if (previewingVoice) { // stop current
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      setPreviewingVoice(null);
      return;
    }
    setPreviewingVoice(voiceId);
    try {
      const res = await axios.post(`${API}/studio/voice-preview`, {
        voice_id: voiceId,
        text: sampleText || (lang === 'pt' ? 'Olá, esta é a minha voz.' : 'Hello, this is my voice.'),
      }, { headers, responseType: 'blob', timeout: 30000 });
      const url = URL.createObjectURL(res.data);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { setPreviewingVoice(null); URL.revokeObjectURL(url); };
      audio.play();
    } catch {
      toast.error(lang === 'pt' ? 'Erro ao gerar preview' : 'Preview error');
      setPreviewingVoice(null);
    }
  };

  const setVoiceForCharacter = (charName, voiceId) => {
    setCharacterVoices(prev => ({ ...prev, [charName]: voiceId }));
    setHasChanges(true);
  };

  const TABS = [
    { id: 'dubbed', icon: Users, label: lang === 'pt' ? 'Dublado' : 'Dubbed', desc: lang === 'pt' ? 'Vozes dos personagens' : 'Character voices' },
    { id: 'narrated', icon: Mic, label: lang === 'pt' ? 'Narrado' : 'Narrated', desc: lang === 'pt' ? 'Texto do narrador' : 'Narrator text' },
    { id: 'book', icon: BookOpen, label: lang === 'pt' ? 'Livro' : 'Book', desc: lang === 'pt' ? 'Texto literário + layout visual' : 'Literary text + visual layout' },
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 size={24} className="animate-spin text-[#8B5CF6]" />
        <p className="text-sm text-[#666]">{lang === 'pt' ? 'Carregando diálogos...' : 'Loading dialogues...'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3" data-testid="dialogue-editor">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-white">
          {lang === 'pt' ? 'Diálogos e Roteiro' : 'Dialogues & Script'}
        </h2>
        <div className="flex gap-2">
          <button onClick={() => generateWithAI([])} disabled={generating}
            data-testid="generate-all-dialogues"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8B5CF6]/10 border border-[#8B5CF6]/30 text-[#8B5CF6] rounded-lg text-xs font-medium hover:bg-[#8B5CF6]/20 transition disabled:opacity-50">
            {generating ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            {lang === 'pt' ? 'Gerar Tudo' : 'Generate All'}
          </button>
          <button onClick={saveDialogues} disabled={saving || !hasChanges}
            data-testid="save-dialogues"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#8B5CF6] text-black rounded-lg text-xs font-medium hover:bg-[#7C3AED] transition disabled:opacity-50">
            {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
            {lang === 'pt' ? 'Salvar' : 'Save'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-0.5 bg-[#111] rounded-xl border border-[#1A1A1A]">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)} data-testid={`tab-${tab.id}`}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition ${
              activeTab === tab.id ? 'bg-[#1A1A1A] text-[#8B5CF6] border border-[#8B5CF6]/30' : 'text-[#666] hover:text-white'
            }`}>
            <tab.icon size={13} /> {tab.label}
          </button>
        ))}
      </div>
      <p className="text-[11px] text-[#555] px-1">{TABS.find(t => t.id === activeTab)?.desc}</p>

      {/* Alert: Missing dubbed dialogues */}
      {activeTab === 'dubbed' && needsDubbedGen > 0 && !generating && (
        <div className="bg-[#8B5CF6]/5 border border-[#8B5CF6]/30 rounded-xl p-3 flex items-center justify-between" data-testid="dubbed-gen-alert">
          <div>
            <p className="text-xs font-medium text-[#8B5CF6]">
              {lang === 'pt'
                ? `${needsDubbedGen} cena(s) sem diálogos dublados`
                : `${needsDubbedGen} scene(s) missing dubbed dialogues`}
            </p>
            <p className="text-[10px] text-[#666] mt-0.5">
              {lang === 'pt'
                ? 'Os textos actuais são de narração. Gere diálogos por personagem para dublagem perfeita.'
                : 'Current texts are narration. Generate character dialogues for perfect dubbing.'}
            </p>
          </div>
          <button onClick={() => generateWithAI([])} disabled={generating}
            data-testid="generate-all-dubbed"
            className="shrink-0 flex items-center gap-1.5 px-3 py-2 bg-[#8B5CF6] text-black rounded-lg text-xs font-bold hover:bg-[#7C3AED] transition">
            <Sparkles size={12} />
            {lang === 'pt' ? 'Gerar Diálogos' : 'Generate Dialogues'}
          </button>
        </div>
      )}

      {/* ═══ DUBBED: Voice Selection with Preview ═══ */}
      {activeTab === 'dubbed' && characters.length > 0 && (
        <div className="bg-[#0D0D0D] rounded-xl border border-[#1A1A1A] p-3 space-y-2">
          <h3 className="text-[11px] font-semibold text-[#888] uppercase tracking-wider flex items-center gap-1.5">
            <Volume2 size={12} />
            {lang === 'pt' ? 'Vozes dos Personagens' : 'Character Voices'}
            <span className="text-[9px] text-[#555] font-normal normal-case ml-1">
              ({lang === 'pt' ? 'auto-atribuídas, altere se necessário' : 'auto-assigned, change if needed'})
            </span>
          </h3>
          <div className="grid grid-cols-2 gap-2">
            {characters.map(char => {
              const info = autoVoiceInfo[char.name] || {};
              const currentVoiceId = characterVoices[char.name] || info.voice_id || '';
              return (
                <div key={char.name} className="bg-[#111] rounded-lg p-2 border border-[#1A1A1A]">
                  <span className="text-[10px] text-white font-medium block truncate">{char.name}</span>
                  <span className="text-[8px] text-[#8B5CF6]/60 block mb-1">
                    {info.voice_type || ''} {info.voice_name ? `(${info.voice_name})` : ''}
                  </span>
                  <div className="flex gap-1">
                    <select value={currentVoiceId}
                      onChange={e => setVoiceForCharacter(char.name, e.target.value)}
                      data-testid={`voice-select-${char.name}`}
                      className="flex-1 bg-[#0A0A0A] border border-[#222] rounded-md text-[9px] text-[#aaa] px-1.5 py-1 focus:border-[#8B5CF6]/50 outline-none">
                      <option value={info.voice_id || ''}>
                        {info.voice_name ? `${info.voice_name} (Auto)` : 'Auto'}
                      </option>
                      {voices.filter(v => v.voice_id !== info.voice_id).map(v => (
                        <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
                      ))}
                    </select>
                    <button onClick={() => previewVoice(currentVoiceId)}
                      data-testid={`preview-voice-${char.name}`}
                      className="p-1 bg-[#0A0A0A] border border-[#222] rounded-md hover:border-[#8B5CF6]/40 transition">
                      {previewingVoice === currentVoiceId
                        ? <Square size={10} className="text-red-400" />
                        : <Play size={10} className="text-[#8B5CF6]" />}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ═══ NARRATED: Narrator Voice ═══ */}
      {activeTab === 'narrated' && (
        <div className="bg-[#0D0D0D] rounded-xl border border-[#1A1A1A] p-3">
          <h3 className="text-[11px] font-semibold text-[#888] uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Mic size={12} />
            {lang === 'pt' ? 'Voz do Narrador' : 'Narrator Voice'}
          </h3>
          <div className="flex gap-1.5">
            <select value={narratorVoice}
              onChange={e => { setNarratorVoice(e.target.value); setHasChanges(true); }}
              data-testid="narrator-voice-select"
              className="flex-1 bg-[#111] border border-[#222] rounded-lg text-xs text-[#aaa] px-3 py-2 focus:border-[#8B5CF6]/50 outline-none">
              {voices.map(v => (
                <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
              ))}
              {voices.length === 0 && <option value={narratorVoice}>Daniel (Auto)</option>}
            </select>
            <button onClick={() => previewVoice(narratorVoice)}
              data-testid="preview-narrator-voice"
              className="px-3 py-2 bg-[#111] border border-[#222] rounded-lg hover:border-[#8B5CF6]/40 transition">
              {previewingVoice === narratorVoice
                ? <Square size={12} className="text-red-400" />
                : <Play size={12} className="text-[#8B5CF6]" />}
            </button>
          </div>
        </div>
      )}

      {/* ═══ Scene List ═══ */}
      <div className="space-y-2">
        {scenesData.map(scene => {
          const isExpanded = expandedScene === scene.scene_number;
          const text = getTextField(scene);
          const hasText = text && text.trim().length > 0;
          const fmt = bookFormats[scene.scene_number] || { font: 'serif', size: 'sm', position: 'bottom', align: 'left' };

          return (
            <div key={scene.scene_number} data-testid={`dialogue-scene-${scene.scene_number}`}
              className={`rounded-xl border transition-all ${
                isExpanded ? 'border-[#8B5CF6]/30 bg-[#0A0A0A]' : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#333]'
              }`}>

              {/* Scene Header */}
              <button onClick={() => setExpandedScene(isExpanded ? null : scene.scene_number)}
                className="w-full flex items-center gap-2.5 p-2.5 text-left">
                <div className="w-14 h-9 rounded-md overflow-hidden flex-shrink-0 bg-[#111]">
                  {scene.thumbnail ? (
                    <img src={resolveImageUrl(scene.thumbnail)} alt={scene.title}
                      loading="lazy" decoding="async" className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <MessageSquare size={10} className="text-[#333]" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] bg-[#8B5CF6]/10 text-[#8B5CF6] px-1.5 py-0.5 rounded font-bold">{scene.scene_number}</span>
                    <span className="text-[11px] font-medium text-white truncate">{scene.title}</span>
                  </div>
                  <p className="text-[9px] text-[#555] truncate mt-0.5">
                    {hasText ? text.substring(0, 60) + '...' : (
                      activeTab === 'dubbed'
                        ? (lang === 'pt' ? 'Sem diálogos — clique "Gerar com IA"' : 'No dialogues — click "AI Generate"')
                        : (lang === 'pt' ? 'Sem texto' : 'No text')
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  {hasText ? <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> : <span className="w-1.5 h-1.5 rounded-full bg-[#333]" />}
                  {isExpanded ? <ChevronUp size={12} className="text-[#666]" /> : <ChevronDown size={12} className="text-[#666]" />}
                </div>
              </button>

              {/* Expanded */}
              {isExpanded && (
                <div className="px-2.5 pb-2.5 space-y-2 border-t border-[#1A1A1A]">
                  {scene.characters_in_scene?.length > 0 && (
                    <div className="flex items-center gap-1 pt-2">
                      <Users size={10} className="text-[#555]" />
                      <span className="text-[9px] text-[#555]">{scene.characters_in_scene.join(', ')}</span>
                    </div>
                  )}

                  {/* ── BOOK TAB: Visual Preview + Text Formatting ── */}
                  {activeTab === 'book' && (
                    <div className="space-y-2">
                      {/* Visual Book Page Preview */}
                      <div className="relative w-full aspect-[4/3] rounded-lg overflow-hidden border border-[#222] bg-[#111]">
                        {scene.thumbnail && (
                          <img src={resolveImageUrl(scene.thumbnail)} alt={scene.title}
                            loading="lazy" decoding="async" className="w-full h-full object-cover" />
                        )}
                        {/* Text overlay positioned according to format */}
                        <div className={`absolute left-0 right-0 px-3 py-2 ${
                          fmt.position === 'top' ? 'top-0' : fmt.position === 'center' ? 'top-1/2 -translate-y-1/2' : 'bottom-0'
                        }`}>
                          <div className={`bg-black/70 backdrop-blur-sm rounded-lg p-2 text-${fmt.align}`}
                            style={{ fontFamily: BOOK_FONTS.find(f => f.id === fmt.font)?.css, fontSize: `${FONT_SIZES.find(f => f.id === fmt.size)?.px || 12}px` }}>
                            <p className="text-white leading-relaxed">
                              {text || (lang === 'pt' ? 'Texto do livro aparecerá aqui...' : 'Book text will appear here...')}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Formatting Controls */}
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* Font */}
                        <div className="flex items-center gap-1">
                          <Type size={10} className="text-[#666]" />
                          <select value={fmt.font} onChange={e => updateBookFormat(scene.scene_number, 'font', e.target.value)}
                            data-testid={`book-font-${scene.scene_number}`}
                            className="bg-[#111] border border-[#222] rounded text-[9px] text-[#aaa] px-1.5 py-1 outline-none focus:border-[#8B5CF6]/50">
                            {BOOK_FONTS.map(f => <option key={f.id} value={f.id}>{f.label}</option>)}
                          </select>
                        </div>

                        {/* Size */}
                        <div className="flex gap-0.5">
                          {FONT_SIZES.map(sz => (
                            <button key={sz.id} onClick={() => updateBookFormat(scene.scene_number, 'size', sz.id)}
                              className={`px-1.5 py-0.5 rounded text-[9px] border transition ${
                                fmt.size === sz.id ? 'bg-[#8B5CF6]/10 border-[#8B5CF6]/30 text-[#8B5CF6]' : 'border-[#222] text-[#666] hover:text-white'
                              }`}>{sz.label}</button>
                          ))}
                        </div>

                        {/* Position */}
                        <div className="flex items-center gap-1">
                          <Move size={10} className="text-[#666]" />
                          {TEXT_POSITIONS.map(pos => (
                            <button key={pos.id} onClick={() => updateBookFormat(scene.scene_number, 'position', pos.id)}
                              data-testid={`book-pos-${pos.id}-${scene.scene_number}`}
                              className={`px-1.5 py-0.5 rounded text-[8px] border transition ${
                                fmt.position === pos.id ? 'bg-[#8B5CF6]/10 border-[#8B5CF6]/30 text-[#8B5CF6]' : 'border-[#222] text-[#666] hover:text-white'
                              }`}>{pos.label}</button>
                          ))}
                        </div>

                        {/* Align */}
                        <div className="flex gap-0.5">
                          {[
                            { id: 'left', Icon: AlignLeft },
                            { id: 'center', Icon: AlignCenter },
                            { id: 'right', Icon: AlignRight },
                          ].map(al => (
                            <button key={al.id} onClick={() => updateBookFormat(scene.scene_number, 'align', al.id)}
                              className={`p-1 rounded border transition ${
                                fmt.align === al.id ? 'bg-[#8B5CF6]/10 border-[#8B5CF6]/30 text-[#8B5CF6]' : 'border-[#222] text-[#666] hover:text-white'
                              }`}><al.Icon size={10} /></button>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Text Editor */}
                  <textarea value={text}
                    onChange={e => updateSceneText(scene.scene_number, e.target.value)}
                    data-testid={`dialogue-text-${scene.scene_number}`}
                    placeholder={
                      activeTab === 'dubbed' ? (lang === 'pt' ? 'Personagem: "diálogo..."' : 'Character: "dialogue..."')
                        : activeTab === 'narrated' ? (lang === 'pt' ? 'Narrador: "texto..."' : 'Narrator: "text..."')
                          : (lang === 'pt' ? 'Texto literário da cena...' : 'Literary text...')
                    }
                    rows={activeTab === 'book' ? 4 : 6}
                    className="w-full bg-[#111] border border-[#222] rounded-lg text-xs text-white p-2.5 resize-y focus:border-[#8B5CF6]/50 outline-none placeholder:text-[#333] leading-relaxed"
                  />

                  {/* Scene Actions */}
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-[#444]">{text.length} {lang === 'pt' ? 'caracteres' : 'chars'}</span>
                    <div className="flex gap-1.5">
                      {/* Audio preview for dubbed scenes */}
                      {activeTab === 'dubbed' && hasText && scene.characters_in_scene?.length > 0 && (
                        <button onClick={() => {
                          const charName = scene.characters_in_scene[0];
                          const voiceId = characterVoices[charName] || autoVoiceInfo[charName]?.voice_id;
                          if (voiceId) {
                            const firstLine = text.split('\n').find(l => l.includes(':'))?.split(':').slice(1).join(':').replace(/"/g, '').trim() || text.substring(0, 100);
                            previewVoice(voiceId, firstLine);
                          }
                        }}
                          data-testid={`preview-audio-scene-${scene.scene_number}`}
                          className="flex items-center gap-1 px-2 py-1 bg-[#1A1A1A] border border-[#222] text-[#888] rounded-lg text-[10px] hover:text-[#8B5CF6] hover:border-[#8B5CF6]/30 transition">
                          <Volume2 size={10} />
                          Preview
                        </button>
                      )}
                      <button onClick={() => generateWithAI([scene.scene_number])}
                        disabled={generatingScene === scene.scene_number}
                        data-testid={`generate-scene-${scene.scene_number}`}
                        className="flex items-center gap-1 px-2 py-1 bg-[#1A1A1A] border border-[#222] text-[#8B5CF6] rounded-lg text-[10px] hover:bg-[#222] transition disabled:opacity-50">
                        {generatingScene === scene.scene_number ? <Loader2 size={10} className="animate-spin" /> : <RefreshCw size={10} />}
                        {lang === 'pt' ? 'Gerar com IA' : 'AI Generate'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-[#1A1A1A]">
        <button onClick={onBack} data-testid="dialogue-back"
          className="px-4 py-2 text-xs text-[#888] hover:text-white transition">
          {lang === 'pt' ? 'Voltar aos Personagens' : 'Back to Characters'}
        </button>
        <button onClick={async () => { if (hasChanges) await saveDialogues(); onComplete?.(); }}
          data-testid="dialogue-continue"
          className="px-4 py-2 bg-[#8B5CF6] text-black rounded-lg text-xs font-semibold hover:bg-[#7C3AED] transition">
          {lang === 'pt' ? "Continuar para Director's Preview" : "Continue to Director's Preview"}
        </button>
      </div>
    </div>
  );
}
