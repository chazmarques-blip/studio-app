import { useState } from 'react';
import { Check, Edit, X, Plus, Volume2 } from 'lucide-react';
import { toast } from 'sonner';

/**
 * Character Approval Step
 * Shows generated characters for user approval before autonomous loop
 */
export function CharacterApprovalStep({ 
  projectId, 
  characters = [], 
  onApprove, 
  onCancel 
}) {
  const [editingChar, setEditingChar] = useState(null);
  const [approvedChars, setApprovedChars] = useState(
    characters.map(c => ({ ...c, approved: false }))
  );

  const handleApproveChar = (charId) => {
    setApprovedChars(prev =>
      prev.map(c => c.id === charId ? { ...c, approved: true } : c)
    );
  };

  const handleEditChar = (char) => {
    setEditingChar({ ...char });
  };

  const handleSaveEdit = () => {
    setApprovedChars(prev =>
      prev.map(c => c.id === editingChar.id ? { ...editingChar, approved: true } : c)
    );
    setEditingChar(null);
    toast.success('Personagem atualizado!');
  };

  const handleApproveAll = () => {
    const allApproved = approvedChars.every(c => c.approved);
    if (!allApproved) {
      toast.error('Aprove todos os personagens primeiro');
      return;
    }
    onApprove(approvedChars);
  };

  const allApproved = approvedChars.every(c => c.approved);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-900 mb-2">
          Aprovação de Personagens
        </h2>
        <p className="text-slate-600">
          Revise e aprove os personagens gerados. Os agentes usarão essas informações para criar o filme.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {approvedChars.map((char) => (
          <div
            key={char.id}
            className={`bg-white rounded-xl border-2 p-6 transition-all ${
              char.approved 
                ? 'border-green-500 shadow-lg' 
                : 'border-slate-200 hover:border-slate-300'
            }`}
          >
            {/* Character Avatar */}
            {char.reference_image_url || char.avatar_url ? (
              <div className="w-full h-48 bg-slate-100 rounded-lg mb-4 overflow-hidden">
                <img
                  src={char.reference_image_url || char.avatar_url}
                  alt={char.name}
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="w-full h-48 bg-gradient-to-br from-violet-100 to-purple-100 rounded-lg mb-4 flex items-center justify-center">
                <span className="text-6xl">{char.name?.[0] || '?'}</span>
              </div>
            )}

            {/* Character Info */}
            <h3 className="font-semibold text-lg text-slate-900 mb-1">
              {char.name}
            </h3>
            <p className="text-sm text-slate-600 mb-3">{char.age}</p>
            <p className="text-sm text-slate-700 mb-4 line-clamp-3">
              {char.physical_description || char.description}
            </p>

            {/* Voice Info */}
            {char.voice_profile && (
              <div className="flex items-center gap-2 mb-4 px-3 py-2 bg-violet-50 rounded-lg">
                <Volume2 size={16} className="text-violet-600" />
                <span className="text-sm text-violet-900">
                  {char.voice_profile.voice_name || 'Voz não atribuída'}
                </span>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2">
              {!char.approved ? (
                <>
                  <button
                    onClick={() => handleApproveChar(char.id)}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                  >
                    <Check size={18} />
                    <span>Aprovar</span>
                  </button>
                  <button
                    onClick={() => handleEditChar(char)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
                  >
                    <Edit size={18} />
                  </button>
                </>
              ) : (
                <div className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-100 text-green-800 rounded-lg">
                  <Check size={18} />
                  <span>Aprovado</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Bottom Actions */}
      <div className="flex justify-between items-center pt-6 border-t border-slate-200">
        <button
          onClick={onCancel}
          className="px-6 py-3 text-slate-600 hover:text-slate-900 transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={handleApproveAll}
          disabled={!allApproved}
          className={`flex items-center gap-2 px-8 py-3 rounded-lg font-medium transition-all ${
            allApproved
              ? 'bg-violet-600 hover:bg-violet-700 text-white shadow-lg'
              : 'bg-slate-200 text-slate-400 cursor-not-allowed'
          }`}
        >
          <Check size={20} />
          <span>Aprovar Todos e Continuar</span>
        </button>
      </div>

      {/* Edit Modal */}
      {editingChar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-8">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-slate-900">
                Editar Personagem
              </h3>
              <button
                onClick={() => setEditingChar(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X size={24} />
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Nome
                </label>
                <input
                  type="text"
                  value={editingChar.name}
                  onChange={(e) => setEditingChar({ ...editingChar, name: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Idade
                </label>
                <input
                  type="text"
                  value={editingChar.age}
                  onChange={(e) => setEditingChar({ ...editingChar, age: e.target.value })}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Descrição Física
                </label>
                <textarea
                  value={editingChar.physical_description || editingChar.description}
                  onChange={(e) => setEditingChar({ 
                    ...editingChar, 
                    physical_description: e.target.value,
                    description: e.target.value
                  })}
                  rows={4}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                onClick={() => setEditingChar(null)}
                className="px-6 py-2 text-slate-600 hover:text-slate-900"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveEdit}
                className="px-6 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg"
              >
                Salvar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
