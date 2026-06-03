import { create } from 'zustand';
import type { ProjectResponse, ClipResponse, TimelineClipPosition } from '@/lib/api/types';

interface ProjectSnapshot {
  clips: ClipResponse[];
}

interface ProjectStore {
  project: ProjectResponse | null;
  clips: ClipResponse[];
  selectedClipId: string | null;
  isDirty: boolean;

  undoStack: ProjectSnapshot[];
  redoStack: ProjectSnapshot[];

  loadProject: (project: ProjectResponse, clips: ClipResponse[]) => void;
  unloadProject: () => void;

  setClips: (clips: ClipResponse[]) => void;
  addClip: (clip: ClipResponse) => void;
  updateClip: (id: string, updates: Partial<ClipResponse>) => void;
  removeClip: (id: string) => void;

  moveClipLocally: (id: string, track: number, startTimeMs: number) => void;
  resizeClipLocally: (id: string, endTimeMs: number) => void;
  batchUpdateLocally: (positions: TimelineClipPosition[]) => void;

  selectClip: (id: string | null) => void;

  pushSnapshot: () => void;
  undo: () => void;
  redo: () => void;
}

export const useProjectStore = create<ProjectStore>((set) => ({
  project: null,
  clips: [],
  selectedClipId: null,
  isDirty: false,

  undoStack: [],
  redoStack: [],

  loadProject: (project, clips) => set({
    project,
    clips,
    selectedClipId: null,
    isDirty: false,
    undoStack: [],
    redoStack: [],
  }),

  unloadProject: () => set({
    project: null,
    clips: [],
    selectedClipId: null,
    isDirty: false,
    undoStack: [],
    redoStack: [],
  }),

  setClips: (clips) => set({ clips }),

  addClip: (clip) => set((s) => ({ clips: [...s.clips, clip] })),

  updateClip: (id, updates) => set((s) => ({
    clips: s.clips.map((c) => (c.id === id ? { ...c, ...updates } : c)),
    isDirty: true,
  })),

  removeClip: (id) => set((s) => ({
    clips: s.clips.filter((c) => c.id !== id),
    selectedClipId: s.selectedClipId === id ? null : s.selectedClipId,
    isDirty: true,
  })),

  moveClipLocally: (id, track, startTimeMs) => set((s) => ({
    clips: s.clips.map((c) =>
      c.id === id ? { ...c, track, start_time_ms: startTimeMs } : c
    ),
    isDirty: true,
  })),

  resizeClipLocally: (id, endTimeMs) => set((s) => ({
    clips: s.clips.map((c) =>
      c.id === id ? { ...c, end_time_ms: endTimeMs } : c
    ),
    isDirty: true,
  })),

  batchUpdateLocally: (positions) => set((s) => {
    const posMap = new Map(positions.map((p) => [p.clip_id, p]));
    return {
      clips: s.clips.map((c) => {
        const pos = posMap.get(c.id);
        return pos ? { ...c, track: pos.track, start_time_ms: pos.start_time_ms } : c;
      }),
      isDirty: true,
    };
  }),

  selectClip: (id) => set({ selectedClipId: id }),

  pushSnapshot: () => set((s) => ({
    undoStack: [...s.undoStack.slice(-50), { clips: JSON.parse(JSON.stringify(s.clips)) }],
    redoStack: [],
  })),

  undo: () => set((s) => {
    if (s.undoStack.length === 0) return s;
    const prev = s.undoStack[s.undoStack.length - 1];
    return {
      clips: prev.clips,
      undoStack: s.undoStack.slice(0, -1),
      redoStack: [...s.redoStack, { clips: JSON.parse(JSON.stringify(s.clips)) }],
      isDirty: true,
    };
  }),

  redo: () => set((s) => {
    if (s.redoStack.length === 0) return s;
    const next = s.redoStack[s.redoStack.length - 1];
    return {
      clips: next.clips,
      redoStack: s.redoStack.slice(0, -1),
      undoStack: [...s.undoStack, { clips: JSON.parse(JSON.stringify(s.clips)) }],
      isDirty: true,
    };
  }),
}));
