import type { RefObject } from 'react';
import type { SubtitleItem } from '@/lib/api/types';

interface SubtitleOverlayProps {
  videoRef: RefObject<HTMLVideoElement | null>;
  subtitles: SubtitleItem[];
  style?: Record<string, unknown>;
}

export function SubtitleOverlay({ videoRef, subtitles, style: _style }: SubtitleOverlayProps) {
  const video = videoRef.current;
  if (!video || subtitles.length === 0) return null;

  const currentTimeMs = video.currentTime * 1000;
  const active = subtitles.find(
    (s) => currentTimeMs >= s.start_ms && currentTimeMs < s.end_ms,
  );

  if (!active) return null;

  return (
    <div className="absolute bottom-12 left-0 right-0 flex justify-center pointer-events-none">
      <div
        className="px-4 py-2 rounded-lg bg-black/60 text-white text-center text-sm max-w-[80%]"
        style={_style as React.CSSProperties}
      >
        {active.text}
      </div>
    </div>
  );
}
