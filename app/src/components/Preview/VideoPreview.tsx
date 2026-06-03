import { useRef, useEffect, useState, useCallback } from 'react';
import { Clapperboard, Music, Mic } from 'lucide-react';
import { TransportControls } from './TransportControls';
import { SubtitleOverlay } from './SubtitleOverlay';
import type { ClipResponse, SubtitleItem } from '@/lib/api/types';

interface VideoPreviewProps {
  clips: ClipResponse[];
  playheadMs: number;
  isPlaying: boolean;
  onTimeUpdate: (timeMs: number) => void;
  onPlayStateChange: (playing: boolean) => void;
  subtitles?: SubtitleItem[];
  subtitleStyle?: Record<string, unknown>;
}

function getAudioUrl(clip: ClipResponse): string | null {
  if (!clip.source_path) return null;
  return `/api/projects/${clip.project_id}/clips/${clip.id}/audio`;
}

export function VideoPreview({
  clips,
  playheadMs,
  isPlaying,
  onTimeUpdate,
  onPlayStateChange,
  subtitles,
  subtitleStyle,
}: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [currentClip, setCurrentClip] = useState<ClipResponse | null>(null);
  const [duration, setDuration] = useState(0);

  useEffect(() => {
    const active = clips.find(
      (c) => playheadMs >= c.start_time_ms && playheadMs < c.end_time_ms,
    );
    setCurrentClip(active ?? null);
  }, [playheadMs, clips]);

  useEffect(() => {
    if (!currentClip) return;

    if (currentClip.clip_type === 'video' && currentClip.source_path) {
      const el = videoRef.current;
      if (!el) return;
      el.src = getAudioUrl(currentClip) ?? '';
      el.load();

      const relativeTime = (playheadMs - currentClip.start_time_ms) / 1000;
      el.currentTime = relativeTime;

      if (isPlaying) el.play().catch(() => {});
      else el.pause();
    } else if (currentClip.source_path) {
      const el = audioRef.current;
      if (!el) return;
      el.src = getAudioUrl(currentClip) ?? '';
      el.load();

      const relativeTime = (playheadMs - currentClip.start_time_ms) / 1000;
      el.currentTime = relativeTime;

      if (isPlaying) el.play().catch(() => {});
      else el.pause();
    }
  }, [currentClip, isPlaying]);

  const handleTimeUpdate = useCallback(() => {
    if (!currentClip) return;
    const el = currentClip.clip_type === 'video' ? videoRef.current : audioRef.current;
    if (!el) return;
    const timelineTimeMs = currentClip.start_time_ms + el.currentTime * 1000;
    onTimeUpdate(timelineTimeMs);
  }, [currentClip, onTimeUpdate]);

  const handleLoadedMetadata = useCallback(() => {
    const el = currentClip?.clip_type === 'video' ? videoRef.current : audioRef.current;
    if (el) setDuration(el.duration);
  }, [currentClip]);

  const clipIcon = currentClip?.clip_type === 'video'
    ? Clapperboard
    : currentClip?.clip_type === 'voiceover'
      ? Mic
      : Music;

  const Icon = clipIcon;

  return (
    <div className="relative bg-black rounded-lg overflow-hidden aspect-video">
      {currentClip?.clip_type === 'video' && currentClip?.source_path ? (
        <video
          ref={videoRef}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          className="w-full h-full object-contain"
          playsInline
        />
      ) : currentClip?.source_path ? (
        <div className="flex flex-col items-center justify-center h-full text-center p-8">
          <Icon className="w-16 h-16 text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground text-sm">
            {currentClip.clip_type === 'voiceover' ? 'Voiceover clip' : 'Audio clip'}
          </p>
          {currentClip.source_text && (
            <p className="text-muted-foreground/60 text-xs mt-1 max-w-md line-clamp-3">
              {currentClip.source_text}
            </p>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-center p-8">
          <Icon className="w-16 h-16 text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground text-sm">
            No clip at current playhead position
          </p>
        </div>
      )}

      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
      />

      {subtitles && subtitles.length > 0 && (
        <SubtitleOverlay
          videoRef={videoRef}
          subtitles={subtitles}
          style={subtitleStyle}
        />
      )}

      <TransportControls
        isPlaying={isPlaying}
        onPlayPause={() => onPlayStateChange(!isPlaying)}
        currentTimeMs={playheadMs}
        durationMs={duration * 1000 || 0}
      />
    </div>
  );
}
