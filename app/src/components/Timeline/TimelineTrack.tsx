import type { ReactNode } from 'react';
import { TRACK_HEIGHT_PX } from './TimelineContext';

interface TimelineTrackProps {
  trackId: number;
  children: ReactNode;
}

const TRACK_LABELS: Record<number, string> = {
  0: 'Video',
  1: 'Voiceover',
  2: 'Music',
};

export function TimelineTrack({ trackId, children }: TimelineTrackProps) {
  const label = TRACK_LABELS[trackId] ?? `Track ${trackId}`;

  return (
    <div
      className="relative border-b border-border/50 flex group"
      style={{ height: TRACK_HEIGHT_PX }}
    >
      <div className="w-24 shrink-0 border-r border-border/50 flex items-center justify-between px-2 text-xs text-muted-foreground">
        <span>{label}</span>
      </div>
      <div className="flex-1 relative overflow-hidden">
        {children}
      </div>
    </div>
  );
}
