import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core';
import { SortableContext, horizontalListSortingStrategy } from '@dnd-kit/sortable';
import { useCallback, useMemo, useRef } from 'react';
import { TimelineContext, PIXELS_PER_SECOND } from './TimelineContext';
import { TimelineRuler } from './TimelineRuler';
import { TimelineTrack } from './TimelineTrack';
import { ClipBlock } from './ClipBlock';
import { Playhead } from './Playhead';
import type { ClipResponse, TimelineClipPosition } from '@/lib/api/types';
import { useTimelineStore } from '@/stores/timelineStore';
import { useProjectStore } from '@/stores/projectStore';

interface TimelineProps {
  clips: ClipResponse[];
  durationMs: number;
  fps: number;
  onClipsReorder: (positions: TimelineClipPosition[]) => void;
  onClipSelect: (clipId: string | null) => void;
  onClipResize: (clipId: string, endTimeMs: number) => void;
}

export function Timeline({
  clips,
  durationMs,
  fps,
  onClipsReorder,
  onClipSelect: _onClipSelect,
  onClipResize,
}: TimelineProps) {
  const zoom = useTimelineStore((s) => s.zoom);
  const scrollX = useTimelineStore((s) => s.scrollX);
  const playheadMs = useTimelineStore((s) => s.playheadMs);
  const setZoom = useTimelineStore((s) => s.setZoom);
  const setScrollX = useTimelineStore((s) => s.setScrollX);
  const setPlayheadMs = useTimelineStore((s) => s.setPlayheadMs);
  const selectedClipId = useProjectStore((s) => s.selectedClipId);
  const selectClip = useProjectStore((s) => s.selectClip);

  const scrollRef = useRef<HTMLDivElement>(null);

  const trackIds = useMemo(() => [...new Set(clips.map((c) => c.track))].sort(), [clips]);
  const tracks = useMemo(
    () =>
      trackIds.map((track) => ({
        id: track,
        clips: clips
          .filter((c) => c.track === track)
          .sort((a, b) => a.start_time_ms - b.start_time_ms),
        label: track === 0 ? 'Video' : track === 1 ? 'Voiceover' : track === 2 ? 'Music' : `Track ${track}`,
      })),
    [clips, trackIds],
  );

  const totalWidth = (durationMs / 1000) * PIXELS_PER_SECOND * zoom;

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;

    const clipId = active.id as string;
    const clip = clips.find((c) => c.id === clipId);
    if (!clip) return;

    const delta = active.rect.current.translated?.left ?? 0;
    const newStartMs = Math.max(0, Math.round((delta / totalWidth) * durationMs));

    onClipsReorder([{ clip_id: clipId, track: clip.track, start_time_ms: newStartMs }]);
  }

  function handleClipResize(clipId: string, newEndMs: number) {
    const snapMs = Math.round(1000 / fps);
    const snappedEnd = Math.round(newEndMs / snapMs) * snapMs;
    onClipResize(clipId, snappedEnd);
  }

  const handleScroll = useCallback(
    (e: React.UIEvent<HTMLDivElement>) => {
      setScrollX(e.currentTarget.scrollLeft);
    },
    [setScrollX],
  );

  return (
    <TimelineContext.Provider
      value={{
        zoom,
        scrollX,
        playheadMs,
        durationMs,
        fps,
        clips,
        selectedClipId,
        pixelsPerSecond: PIXELS_PER_SECOND,
        setZoom,
        setScrollX,
        setPlayheadMs,
        selectClip,
      }}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between px-3 py-1 border-b border-border">
          <span className="text-xs text-muted-foreground">Timeline</span>
          <div className="flex items-center gap-2">
            <button
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setZoom(zoom * 0.8)}
              disabled={zoom <= 0.25}
            >
              -
            </button>
            <span className="text-xs text-muted-foreground w-8 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <button
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={() => setZoom(zoom * 1.25)}
              disabled={zoom >= 4}
            >
              +
            </button>
          </div>
        </div>

        <div
          ref={scrollRef}
          className="flex-1 overflow-auto"
          onScroll={handleScroll}
        >
          <div className="relative" style={{ width: totalWidth, minHeight: '100%' }}>
            <TimelineRuler />

            {tracks.map((track) => (
              <TimelineTrack key={track.id} trackId={track.id}>
                <DndContext onDragEnd={handleDragEnd} collisionDetection={closestCenter}>
                  <SortableContext
                    items={track.clips.map((c) => c.id)}
                    strategy={horizontalListSortingStrategy}
                  >
                    {track.clips.map((clip) => (
                      <ClipBlock
                        key={clip.id}
                        clip={clip}
                        isSelected={clip.id === selectedClipId}
                        onClick={() => selectClip(clip.id)}
                        onResize={handleClipResize}
                      />
                    ))}
                  </SortableContext>
                </DndContext>
              </TimelineTrack>
            ))}

            <Playhead />
          </div>
        </div>
      </div>
    </TimelineContext.Provider>
  );
}
