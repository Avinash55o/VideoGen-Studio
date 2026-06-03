import { useCallback, useRef } from 'react';
import { useTimelineContext, PIXELS_PER_SECOND } from './TimelineContext';

export function Playhead() {
  const { playheadMs, durationMs, zoom, setPlayheadMs, scrollX } = useTimelineContext();
  const isDragging = useRef(false);
  const rulerRef = useRef<HTMLDivElement | null>(null);

  const totalWidth = (durationMs / 1000) * PIXELS_PER_SECOND * zoom;
  const left = totalWidth > 0 ? (playheadMs / durationMs) * totalWidth : 0;

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;

    function onMove(ev: MouseEvent) {
      if (!isDragging.current) return;
      const container = rulerRef.current?.parentElement;
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const x = ev.clientX - rect.left + scrollX;
      const ms = Math.max(0, Math.min(durationMs, (x / totalWidth) * durationMs));
      setPlayheadMs(ms);
    }

    function onUp() {
      isDragging.current = false;
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
    }

    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
  }, [durationMs, totalWidth, scrollX, setPlayheadMs]);

  return (
    <div
      ref={rulerRef}
      className="absolute top-0 bottom-0 w-0.5 bg-accent z-20 pointer-events-none"
      style={{ left: `${left}px` }}
    >
      <div
        className="absolute -top-1 -left-1.5 w-3.5 h-3.5 bg-accent rounded-full pointer-events-auto cursor-grab active:cursor-grabbing"
        onPointerDown={handleMouseDown}
      />
    </div>
  );
}
