import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { resolveImageUrl } from '../utils/resolveImageUrl';
import {
  Mic, BookOpen, Users, Sparkles, Save, ChevronDown, ChevronUp,
  Loader2, Volume2, RefreshCw, MessageSquare
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

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

  const token = localStorage.getItem('agentzz_token');
  const headers = { Authorization: `Bearer ${token}` };

  // Load dialogues data and voices
  useEffect(() => {
    const loadData = async () => {
      try {
        const dialogueRes = await axios.get(`${API}/studio/projects/${projectId}/dialogues`, { headers });
        const d = dialogueRes.data;
        setScenesData(d.scenes || []);
        setCharacters(d.characters || []);

        // Auto-voices come pre-assigned from backend
        const autoVoices = d.character_voices || {};
        const voiceMap = {};
        Object.entries(autoVoices).forEach(([name, info]) => {
          voiceMap[name] = info.voice_id || '';
        });
        setCharacterVoices(voiceMap);
        setAutoVoiceInfo(autoVoices);

        if (d.narrator_voice) setNarratorVoice(d.narrator_voice);

        // Load available voices for manual override
        try {
          const voicesRes = await axios.get(`${API}/studio/voices`, { headers });
          setVoices(voicesRes.data.voices || []);
        } catch {
          setVoices([]);
        }
      } catch (e) {
        toast.error(lang === 'pt' ? 'Erro ao carregar diálogos' : 'Error loading dialogues');
      }
      setLoading(false);
    };
    loadData();
  }, [projectId]);

  // Get text field based on active tab
  const getTextField = (scene) => {
    if (activeTab === 'dubbed') return scene.dubbed_text || scene.dialogue || '';
    if (activeTab === 'narrated') return scene.narrated_text || scene.narration || '';
    return scene.book_text || '';
  };

  // Update text for a specific scene
  const updateSceneText = (sceneNumber, text) => {
    setScenesData(prev => prev.map(s => {
      if (s.scene_number !== sceneNumber) return s;
      const field = activeTab === 'dubbed' ? 'dubbed_text'
        : activeTab === 'narrated' ? 'narrated_text' : 'book_text';
      return { ...s, [field]: text };
    }));
    setHasChanges(true);
  };

  // Generate dialogues with AI for specific scenes or all
  const generateWithAI = async (sceneNumbers = []) => {
    const isAll = sceneNumbers.length === 0;
    if (isAll) setGenerating(true);
    else setGeneratingScene(sceneNumbers[0]);

    try {
      const res = await axios.post(`${API}/studio/projects/${projectId}/dialogues/generate`, {
        mode: activeTab,
        scene_numbers: sceneNumbers,
      }, { headers });

      const results = res.data.results || [];
      setScenesData(prev => prev.map(s => {
        const match = results.find(r => r.scene_number === s.scene_number);
        if (!match) return s;
        const field = activeTab === 'dubbed' ? 'dubbed_text'
          : activeTab === 'narrated' ? 'narrated_text' : 'book_text';
        return { ...s, [field]: match.generated_text };
      }));

      setHasChanges(true);
      toast.success(lang === 'pt'
        ? `${results.length} cena(s) gerada(s) com IA`
        : `${results.length} scene(s) generated with AI`);
    } catch (e) {
      toast.error(lang === 'pt' ? 'Erro ao gerar com IA' : 'AI generation error');
    }
    setGenerating(false);
    setGeneratingScene(null);
  };

  // Save all dialogues
  const saveDialogues = async () => {
    setSaving(true);
    try {
      await axios.patch(`${API}/studio/projects/${projectId}/dialogues/save`, {
        scenes_dialogue: scenesData.map(s => ({
          scene_number: s.scene_number,
          dubbed_text: s.dubbed_text || '',
          narrated_text: s.narrated_text || '',
          book_text: s.book_text || '',
          dialogue: s.dubbed_text || s.dialogue || '',
          narration: s.narrated_text || s.narration || '',
        })),
        character_voices: characterVoices,
        narrator_voice: narratorVoice,
      }, { headers });

      setHasChanges(false);
      toast.success(lang === 'pt' ? 'Diálogos salvos!' : 'Dialogues saved!');
    } catch (e) {
      toast.error(lang === 'pt' ? 'Erro ao salvar' : 'Save error');
    }
    setSaving(false);
  };

  // Assign voice to character
  const setVoiceForCharacter = (charName, voiceId) => {
    setCharacterVoices(prev => ({ ...prev, [charName]: voiceId }));
    setHasChanges(true);
  };

  const TABS = [
    { id: 'dubbed', icon: Users, label: lang === 'pt' ? 'Dublado' : 'Dubbed', desc: lang === 'pt' ? 'Vozes dos personagens' : 'Character voices' },
    { id: 'narrated', icon: Mic, label: lang === 'pt' ? 'Narrado' : 'Narrated', desc: lang === 'pt' ? 'Texto do narrador' : 'Narrator text' },
    { id: 'book', icon: BookOpen, label: lang === 'pt' ? 'Livro' : 'Book', desc: lang === 'pt' ? 'Texto literário' : 'Literary text' },
  ];

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 gap-3">
        <Loader2 size={24} className="animate-spin text-[#C9A84C]" />
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
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#C9A84C]/10 border border-[#C9A84C]/30 text-[#C9A84C] rounded-lg text-xs font-medium hover:bg-[#C9A84C]/20 transition disabled:opacity-50">
            {generating ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            {lang === 'pt' ? 'Gerar Tudo com IA' : 'Generate All with AI'}
          </button>
          <button onClick={saveDialogues} disabled={saving || !hasChanges}
            data-testid="save-dialogues"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-[#C9A84C] text-black rounded-lg text-xs font-medium hover:bg-[#B8973F] transition disabled:opacity-50">
            {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
            {lang === 'pt' ? 'Salvar' : 'Save'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-0.5 bg-[#111] rounded-xl border border-[#1A1A1A]">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            data-testid={`tab-${tab.id}`}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition ${
              activeTab === tab.id
                ? 'bg-[#1A1A1A] text-[#C9A84C] border border-[#C9A84C]/30'
                : 'text-[#666] hover:text-white'
            }`}>
            <tab.icon size={13} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab description */}
      <p className="text-[11px] text-[#555] px-1">
        {TABS.find(t => t.id === activeTab)?.desc}
      </p>

      {/* Voice Selection */}
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
              return (
                <div key={char.name} className="bg-[#111] rounded-lg p-2 border border-[#1A1A1A]">
                  <span className="text-[10px] text-white font-medium block truncate">{char.name}</span>
                  <span className="text-[8px] text-[#C9A84C]/60 block mb-1.5">
                    {info.voice_type || ''} {info.voice_name ? `(${info.voice_name})` : ''}
                  </span>
                  <select
                    value={characterVoices[char.name] || info.voice_id || ''}
                    onChange={e => setVoiceForCharacter(char.name, e.target.value)}
                    data-testid={`voice-select-${char.name}`}
                    className="w-full bg-[#0A0A0A] border border-[#222] rounded-md text-[9px] text-[#aaa] px-1.5 py-1 focus:border-[#C9A84C]/50 outline-none">
                    <option value={info.voice_id || ''}>
                      {info.voice_name ? `${info.voice_name} (Auto)` : (lang === 'pt' ? 'Auto (IA)' : 'Auto (AI)')}
                    </option>
                    {voices.filter(v => v.voice_id !== info.voice_id).map(v => (
                      <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'narrated' && (
        <div className="bg-[#0D0D0D] rounded-xl border border-[#1A1A1A] p-3">
          <h3 className="text-[11px] font-semibold text-[#888] uppercase tracking-wider flex items-center gap-1.5 mb-2">
            <Mic size={12} />
            {lang === 'pt' ? 'Voz do Narrador' : 'Narrator Voice'}
          </h3>
          <select
            value={narratorVoice}
            onChange={e => { setNarratorVoice(e.target.value); setHasChanges(true); }}
            data-testid="narrator-voice-select"
            className="w-full bg-[#111] border border-[#222] rounded-lg text-xs text-[#aaa] px-3 py-2 focus:border-[#C9A84C]/50 outline-none">
            {voices.map(v => (
              <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Scene List */}
      <div className="space-y-2">
        {scenesData.map(scene => {
          const isExpanded = expandedScene === scene.scene_number;
          const text = getTextField(scene);
          const hasText = text && text.trim().length > 0;

          return (
            <div key={scene.scene_number}
              data-testid={`dialogue-scene-${scene.scene_number}`}
              className={`rounded-xl border transition-all ${
                isExpanded ? 'border-[#C9A84C]/30 bg-[#0A0A0A]' : 'border-[#1A1A1A] bg-[#0D0D0D] hover:border-[#333]'
              }`}>
              {/* Scene Header (always visible) */}
              <button
                onClick={() => setExpandedScene(isExpanded ? null : scene.scene_number)}
                className="w-full flex items-center gap-2.5 p-2.5 text-left">
                {/* Thumbnail */}
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

                {/* Title + preview */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] bg-[#C9A84C]/10 text-[#C9A84C] px-1.5 py-0.5 rounded font-bold">
                      {scene.scene_number}
                    </span>
                    <span className="text-[11px] font-medium text-white truncate">{scene.title}</span>
                  </div>
                  <p className="text-[9px] text-[#555] truncate mt-0.5">
                    {hasText ? text.substring(0, 60) + '...' : (lang === 'pt' ? 'Sem texto — clique para editar' : 'No text — click to edit')}
                  </p>
                </div>

                {/* Status indicators */}
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  {hasText && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}
                  {!hasText && <span className="w-1.5 h-1.5 rounded-full bg-[#333]"></span>}
                  {isExpanded ? <ChevronUp size={12} className="text-[#666]" /> : <ChevronDown size={12} className="text-[#666]" />}
                </div>
              </button>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-2.5 pb-2.5 space-y-2 border-t border-[#1A1A1A]">
                  {/* Characters in scene */}
                  {scene.characters_in_scene?.length > 0 && (
                    <div className="flex items-center gap-1 pt-2">
                      <Users size={10} className="text-[#555]" />
                      <span className="text-[9px] text-[#555]">
                        {scene.characters_in_scene.join(', ')}
                      </span>
                    </div>
                  )}

                  {/* Text editor */}
                  <textarea
                    value={text}
                    onChange={e => updateSceneText(scene.scene_number, e.target.value)}
                    data-testid={`dialogue-text-${scene.scene_number}`}
                    placeholder={
                      activeTab === 'dubbed'
                        ? (lang === 'pt' ? 'Personagem: "diálogo..."' : 'Character: "dialogue..."')
                        : activeTab === 'narrated'
                          ? (lang === 'pt' ? 'Narrador: "texto..."' : 'Narrator: "text..."')
                          : (lang === 'pt' ? 'Texto literário da cena...' : 'Literary text for scene...')
                    }
                    rows={6}
                    className="w-full bg-[#111] border border-[#222] rounded-lg text-xs text-white p-2.5 resize-y focus:border-[#C9A84C]/50 outline-none placeholder:text-[#333] leading-relaxed"
                  />

                  {/* Scene Actions */}
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] text-[#444]">
                      {text.length} {lang === 'pt' ? 'caracteres' : 'chars'}
                    </span>
                    <button
                      onClick={() => generateWithAI([scene.scene_number])}
                      disabled={generatingScene === scene.scene_number}
                      data-testid={`generate-scene-${scene.scene_number}`}
                      className="flex items-center gap-1 px-2 py-1 bg-[#1A1A1A] border border-[#222] text-[#C9A84C] rounded-lg text-[10px] hover:bg-[#222] transition disabled:opacity-50">
                      {generatingScene === scene.scene_number
                        ? <Loader2 size={10} className="animate-spin" />
                        : <RefreshCw size={10} />}
                      {lang === 'pt' ? 'Gerar com IA' : 'Generate with AI'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-between pt-2 border-t border-[#1A1A1A]">
        <button onClick={onBack}
          data-testid="dialogue-back"
          className="px-4 py-2 text-xs text-[#888] hover:text-white transition">
          {lang === 'pt' ? 'Voltar ao Storyboard' : 'Back to Storyboard'}
        </button>
        <button
          onClick={async () => { if (hasChanges) await saveDialogues(); onComplete?.(); }}
          data-testid="dialogue-continue"
          className="px-4 py-2 bg-[#C9A84C] text-black rounded-lg text-xs font-semibold hover:bg-[#B8973F] transition">
          {lang === 'pt' ? 'Continuar para Produção' : 'Continue to Production'}
        </button>
      </div>
    </div>
  );
}
