import { createContext, useContext } from 'react';
import type { ClipResponse } from '@/lib/api/types';

interface TimelineContextValue {
  zoom: number;
  scrollX: number;
  playheadMs: number;
  durationMs: number;
  fps: number;
  clips: ClipResponse[];
  selectedClipId: string | null;
  pixelsPerSecond: number;

  setZoom: (zoom: number) => void;
  setScrollX: (x: number) => void;
  setPlayheadMs: (ms: number) => void;
  selectClip: (id: string | null) => void;
}

export const TimelineContext = createContext<TimelineContextValue | null>(null);

export function useTimelineContext() {
  const ctx = useContext(TimelineContext);
  if (!ctx) throw new Error('useTimelineContext must be used within a Timeline');
  return ctx;
}

export const PIXELS_PER_SECOND = 100;
export const TRACK_HEIGHT_PX = 80;
