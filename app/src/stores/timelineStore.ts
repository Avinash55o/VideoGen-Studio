import { create } from 'zustand';

interface TimelineStore {
  zoom: number;
  scrollX: number;
  playheadMs: number;

  setZoom: (zoom: number) => void;
  setScrollX: (scrollX: number) => void;
  setPlayheadMs: (ms: number) => void;
}

export const useTimelineStore = create<TimelineStore>((set) => ({
  zoom: 1,
  scrollX: 0,
  playheadMs: 0,

  setZoom: (zoom) => set({ zoom: Math.max(0.25, Math.min(4, zoom)) }),
  setScrollX: (scrollX) => set({ scrollX }),
  setPlayheadMs: (ms) => set({ playheadMs: Math.max(0, ms) }),
}));
