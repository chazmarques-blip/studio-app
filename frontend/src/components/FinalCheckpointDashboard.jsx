import { useState } from 'react';
import { Check, X, FileText, Image as ImageIcon, Volume2, DollarSign, ChevronRight, Play } from 'lucide-react';

/**
 * Final Checkpoint Dashboard
 * Shows complete project for user approval before video generation
 */
export function FinalCheckpointDashboard({ 
  projectId, 
  checkpoint, 
  onApprove, 
  onReject 
}) {
  const [activeTab, setActiveTab] = useState('screenplay');
  const [playingVoice, setPlayingVoice] = useState(null);

  const tabs = [
    { id: 'screenplay', label: 'Roteiro', icon: FileText },
    { id: 'storyboard', label: 'Storyboard', icon: ImageIcon },
    { id: 'voices', label: 'Vozes', icon: Volume2 },
    { id: 'cost', label: 'Custo & Timeline', icon: DollarSign },
  ];

  const bible = checkpoint?.bible || {};
  const screenplay = bible.screenplay || {};
  const scenes = screenplay.scenes || [];
  const dialogues = bible.dialogues || [];
  const narration = bible.narration || [];
  const voiceSamples = bible.voice_samples || [];
  const characters = bible.characters || [];
  const qualityScore = bible.quality_score || 0;

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-slate-900 mb-2">
              Aprovação Final
            </h2>
            <p className="text-slate-600">
              Revise todos os componentes antes de gerar os vídeos
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-slate-600 mb-1">Quality Score</div>
            <div className={`text-3xl font-bold ${
              qualityScore >= 90 ? 'text-green-600' : 'text-yellow-600'
            }`}>
              {qualityScore}%
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-200">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-3 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-violet-600 text-violet-600'
                    : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
              >
                <Icon size={20} />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Content */}
      <div className="mb-8">
        {/* Screenplay Tab */}
        {activeTab === 'screenplay' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">
                Roteiro Completo
              </h3>
              <div className="space-y-6">
                {scenes.map((scene, idx) => {
                  const sceneDialogues = dialogues.find(d => d.scene_number === scene.scene_number);
                  
                  return (
                    <div key={idx} className="border-l-4 border-violet-500 pl-6 py-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                            <span className="px-3 py-1 bg-violet-100 text-violet-800 rounded-full text-sm font-medium">
                              Cena {scene.scene_number}
                            </span>
                            <h4 className="text-lg font-semibold text-slate-900">
                              {scene.title}
                            </h4>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-slate-600">
                            <span>📍 {scene.location}</span>
                            <span>😊 {scene.emotion}</span>
                            <span>👥 {scene.characters_in_scene?.join(', ')}</span>
                          </div>
                        </div>
                        <span className="text-sm text-slate-500">{scene.duration || '5s'}</span>
                      </div>
                      
                      <p className="text-slate-700 mb-4">{scene.description}</p>
                      
                      {/* Dialogues */}
                      {sceneDialogues?.dialogues && sceneDialogues.dialogues.length > 0 && (
                        <div className="bg-slate-50 rounded-lg p-4 space-y-3">
                          <div className="text-sm font-medium text-slate-700 mb-2">Diálogos:</div>
                          {sceneDialogues.dialogues.map((dialogue, dIdx) => (
                            <div key={dIdx} className="flex gap-3">
                              <span className="font-semibold text-violet-900 min-w-[120px]">
                                {dialogue.character}:
                              </span>
                              <div className="flex-1">
                                <p className="text-slate-800 mb-1">"{dialogue.line}"</p>
                                <p className="text-xs text-slate-500 italic">{dialogue.action_note}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Narration */}
            {narration.length > 0 && (
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">
                  Narração
                </h3>
                {narration.map((block, idx) => (
                  <div key={idx} className="mb-4 last:mb-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm font-medium text-blue-700">
                        Cenas {block.scene_range?.join('-')} · {block.tone}
                      </span>
                    </div>
                    <p className="text-blue-900 italic leading-relaxed">"{block.text}"</p>
                    <p className="text-xs text-blue-600 mt-2">{block.voice_instruction}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Voices Tab */}
        {activeTab === 'voices' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {characters.map((char, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-slate-200 p-6">
                <div className="flex items-start gap-4 mb-4">
                  <div className="w-16 h-16 bg-violet-100 rounded-full flex items-center justify-center text-2xl">
                    {char.name?.[0] || '?'}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-lg text-slate-900">{char.name}</h4>
                    <p className="text-sm text-slate-600">{char.age}</p>
                  </div>
                </div>

                {char.voice_profile && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between px-4 py-3 bg-violet-50 rounded-lg">
                      <div>
                        <div className="font-medium text-violet-900">
                          {char.voice_profile.voice_name || 'Voice Sample'}
                        </div>
                        <div className="text-sm text-violet-600">
                          {char.voice_profile.voice_id}
                        </div>
                      </div>
                      <button
                        onClick={() => setPlayingVoice(playingVoice === char.id ? null : char.id)}
                        className="p-2 bg-violet-600 hover:bg-violet-700 text-white rounded-full transition-colors"
                      >
                        <Play size={16} />
                      </button>
                    </div>

                    {char.voice_profile.voice_sample_url && playingVoice === char.id && (
                      <audio
                        src={char.voice_profile.voice_sample_url}
                        controls
                        autoPlay
                        className="w-full"
                      />
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Cost Tab */}
        {activeTab === 'cost' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 p-8">
              <h3 className="text-2xl font-bold text-slate-900 mb-6">
                Estimativa de Custo
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="text-center p-6 bg-gradient-to-br from-violet-50 to-purple-50 rounded-xl">
                  <div className="text-sm text-violet-600 mb-2">Sora 2 (Vídeos)</div>
                  <div className="text-3xl font-bold text-violet-900">
                    ${checkpoint?.estimate?.breakdown?.sora_2 || '0.00'}
                  </div>
                </div>
                <div className="text-center p-6 bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl">
                  <div className="text-sm text-blue-600 mb-2">Vozes (ElevenLabs)</div>
                  <div className="text-3xl font-bold text-blue-900">
                    ${checkpoint?.estimate?.breakdown?.voices || '0.00'}
                  </div>
                </div>
                <div className="text-center p-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl">
                  <div className="text-sm text-green-600 mb-2">LLM (Claude)</div>
                  <div className="text-3xl font-bold text-green-900">
                    ${checkpoint?.estimate?.breakdown?.llm || '0.00'}
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-200 pt-6">
                <div className="flex items-center justify-between text-2xl font-bold">
                  <span className="text-slate-900">Total Estimado:</span>
                  <span className="text-violet-600">
                    ${checkpoint?.estimate?.total_usd || '0.00'} USD
                  </span>
                </div>
                <p className="text-sm text-slate-500 mt-2 text-right">
                  Custos podem variar baseado no uso real
                </p>
              </div>

              <div className="mt-8 grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="text-sm text-slate-600 mb-1">Cenas Planejadas</div>
                  <div className="text-2xl font-bold text-slate-900">
                    {checkpoint?.estimate?.details?.num_scenes || scenes.length}
                  </div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <div className="text-sm text-slate-600 mb-1">Duração Estimada</div>
                  <div className="text-2xl font-bold text-slate-900">
                    {Math.floor((checkpoint?.estimate?.details?.total_duration_seconds || 180) / 60)}min
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Actions */}
      <div className="flex justify-between items-center pt-6 border-t border-slate-200">
        <button
          onClick={() => onReject()}
          className="flex items-center gap-2 px-6 py-3 text-slate-600 hover:text-slate-900 transition-colors"
        >
          <X size={20} />
          <span>Ajustar Projeto</span>
        </button>
        <button
          onClick={() => onApprove()}
          className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white rounded-xl font-semibold shadow-lg transition-all"
        >
          <Check size={24} />
          <span>Aprovar e Gerar Vídeos</span>
          <ChevronRight size={20} />
        </button>
      </div>
    </div>
  );
}
