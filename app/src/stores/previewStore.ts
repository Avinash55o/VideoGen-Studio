import { create } from 'zustand';

interface PreviewStore {
  isPlaying: boolean;
  currentTimeMs: number;

  play: () => void;
  pause: () => void;
  togglePlay: () => void;
  setCurrentTimeMs: (ms: number) => void;
}

export const usePreviewStore = create<PreviewStore>((set) => ({
  isPlaying: false,
  currentTimeMs: 0,

  play: () => set({ isPlaying: true }),
  pause: () => set({ isPlaying: false }),
  togglePlay: () => set((s) => ({ isPlaying: !s.isPlaying })),
  setCurrentTimeMs: (ms) => set({ currentTimeMs: Math.max(0, ms) }),
}));
