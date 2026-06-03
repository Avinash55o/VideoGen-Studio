import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { useCallback, type CSSProperties } from 'react';
import { useTimelineContext, PIXELS_PER_SECOND } from './TimelineContext';
import type { ClipResponse } from '@/lib/api/types';
import { cn } from '@/lib/utils/cn';

interface ClipBlockProps {
  clip: ClipResponse;
  isSelected: boolean;
  onClick: () => void;
  onResize: (clipId: string, newEndMs: number) => void;
}

const CLIP_COLORS: Record<string, string> = {
  video: 'bg-blue-500/20 border-blue-500/40 hover:border-blue-500/60',
  voiceover: 'bg-green-500/20 border-green-500/40 hover:border-green-500/60',
  music: 'bg-purple-500/20 border-purple-500/40 hover:border-purple-500/60',
  subtitle: 'bg-yellow-500/20 border-yellow-500/40 hover:border-yellow-500/60',
  image: 'bg-orange-500/20 border-orange-500/40 hover:border-orange-500/60',
  text: 'bg-pink-500/20 border-pink-500/40 hover:border-pink-500/60',
};

export function ClipBlock({ clip, isSelected, onClick, onResize }: ClipBlockProps) {
  const { durationMs, zoom } = useTimelineContext();
  const totalWidth = (durationMs / 1000) * PIXELS_PER_SECOND * zoom;

  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: clip.id,
    data: { clip },
  });

  const style: CSSProperties = {
    left: `${(clip.start_time_ms / durationMs) * 100}%`,
    width: `${((clip.end_time_ms - clip.start_time_ms) / durationMs) * 100}%`,
    transform: CSS.Transform.toString(transform),
  };

  const colorClass = CLIP_COLORS[clip.clip_type] ?? 'bg-gray-500/20 border-gray-500/40';

  const handleResizeStart = useCallback((e: React.PointerEvent) => {
    e.stopPropagation();
    const startX = e.clientX;
    const startWidth = clip.end_time_ms - clip.start_time_ms;

    function onMove(ev: PointerEvent) {
      const deltaMs = ((ev.clientX - startX) / totalWidth) * durationMs;
      const newEnd = Math.max(clip.start_time_ms + 500, clip.start_time_ms + startWidth + deltaMs);
      onResize(clip.id, newEnd);
    }

    function onUp() {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
    }

    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
  }, [clip, totalWidth, durationMs, onResize]);

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'absolute top-1 bottom-1 rounded-md border text-xs overflow-hidden cursor-grab active:cursor-grabbing',
        colorClass,
        isSelected && 'ring-2 ring-accent',
      )}
      style={style}
      onClick={(e) => { e.stopPropagation(); onClick(); }}
      {...attributes}
      {...listeners}
    >
      <div className="p-1.5 truncate text-[10px] leading-tight text-foreground/80">
        {clip.source_text?.slice(0, 40) || clip.clip_type}
      </div>
      <div
        className="absolute right-0 top-0 bottom-0 w-2 cursor-col-resize hover:bg-white/10"
        onPointerDown={handleResizeStart}
      />
    </div>
  );
}
