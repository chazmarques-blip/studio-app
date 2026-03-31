import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Check, X } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const API = import.meta.env.VITE_API_URL || '/api';

// Sortable Scene Item
function SortableSceneItem({ scene, index }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: scene.scene_number });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        flex items-center gap-3 p-4 rounded-xl border-2 bg-[#0A0A0A]
        ${isDragging ? 'border-[#8B5CF6] shadow-lg shadow-[#8B5CF6]/20 z-50' : 'border-[#222] hover:border-[#444]'}
        transition-all cursor-move
      `}
    >
      {/* Drag Handle */}
      <div
        {...attributes}
        {...listeners}
        className="flex items-center justify-center w-8 h-8 rounded-lg bg-[#222] hover:bg-[#333] cursor-grab active:cursor-grabbing transition"
      >
        <GripVertical size={18} className="text-[#888]" />
      </div>

      {/* Scene Number */}
      <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-[#8B5CF6]/10 border border-[#8B5CF6]/30">
        <span className="text-lg font-bold text-[#8B5CF6]">{index + 1}</span>
      </div>

      {/* Scene Info */}
      <div className="flex-1">
        <div className="font-bold text-white text-sm">
          {scene.title || `Cena ${scene.scene_number}`}
        </div>
        <div className="text-xs text-[#666] mt-0.5">
          Original: Cena {scene.scene_number}
        </div>
      </div>

      {/* Duration */}
      {scene.duration && (
        <div className="text-xs text-[#888] bg-[#1A1A1A] px-3 py-1.5 rounded-lg">
          {scene.duration}s
        </div>
      )}
    </div>
  );
}

export default function SceneReorderModal({ projectId, scenes, onClose, onReordered }) {
  const [items, setItems] = useState(scenes);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;

    if (active.id !== over.id) {
      setItems((items) => {
        const oldIndex = items.findIndex((item) => item.scene_number === active.id);
        const newIndex = items.findIndex((item) => item.scene_number === over.id);

        const newItems = arrayMove(items, oldIndex, newIndex);
        setHasChanges(true);
        return newItems;
      });
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    
    try {
      const token = localStorage.getItem('access_token');
      const newOrder = items.map(item => item.scene_number);
      
      const response = await axios.post(
        `${API}/studio/projects/${projectId}/scenes/reorder`,
        { scene_order: newOrder },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      toast.success('Ordem das cenas atualizada com sucesso!');
      
      if (onReordered) {
        onReordered(response.data);
      }
      
      onClose();
    } catch (error) {
      console.error('Erro ao reordenar cenas:', error);
      toast.error('Erro ao salvar nova ordem');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    if (hasChanges && !window.confirm('Descartar alterações na ordem das cenas?')) {
      return;
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#0F0F0F] rounded-2xl border border-[#222] max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-[#222]">
          <h2 className="text-2xl font-bold text-white mb-2">
            🎬 Reordenar Cenas
          </h2>
          <p className="text-sm text-[#888]">
            Arraste e solte para reorganizar. A ordem será atualizada em todo o projeto.
          </p>
        </div>

        {/* Scrollable Scene List */}
        <div className="flex-1 overflow-y-auto p-6">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={items.map(s => s.scene_number)}
              strategy={verticalListSortingStrategy}
            >
              <div className="space-y-3">
                {items.map((scene, index) => (
                  <SortableSceneItem
                    key={scene.scene_number}
                    scene={scene}
                    index={index}
                  />
                ))}
              </div>
            </SortableContext>
          </DndContext>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-[#222] flex items-center justify-between">
          <div className="text-sm text-[#888]">
            {hasChanges ? (
              <span className="text-[#8B5CF6]">✓ Ordem modificada</span>
            ) : (
              <span>Arraste as cenas para reordenar</span>
            )}
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={handleCancel}
              className="px-5 py-2.5 rounded-xl bg-[#1A1A1A] hover:bg-[#222] text-white font-medium transition flex items-center gap-2"
            >
              <X size={16} />
              Cancelar
            </button>
            
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className="px-5 py-2.5 rounded-xl bg-[#8B5CF6] hover:bg-[#7C3AED] disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Salvando...
                </>
              ) : (
                <>
                  <Check size={16} />
                  Salvar Ordem
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
