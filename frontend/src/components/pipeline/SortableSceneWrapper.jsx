import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

/**
 * SortableSceneWrapper — drag-and-drop wrapper for scene cards.
 * Extracted from DirectedStudio.jsx.
 *
 * Usage:
 *   <SortableSceneWrapper id="scene-1" disabled={false}>
 *     {({ dragHandleProps, isDragging }) => <SceneCard ... />}
 *   </SortableSceneWrapper>
 */
export const SortableSceneWrapper = ({ id, disabled, children }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id, disabled });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
    position: 'relative',
    zIndex: isDragging ? 50 : 'auto',
  };
  return (
    <div ref={setNodeRef} style={style} data-testid={`sortable-${id}`}>
      {children({ dragHandleProps: { ...attributes, ...listeners }, isDragging })}
    </div>
  );
};

export default SortableSceneWrapper;
