import { Play, Pause, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TransportControlsProps {
  isPlaying: boolean;
  onPlayPause: () => void;
  currentTimeMs: number;
  durationMs: number;
}

export function TransportControls({
  isPlaying,
  onPlayPause,
  currentTimeMs,
  durationMs,
}: TransportControlsProps) {
  const currentSec = Math.floor(currentTimeMs / 1000);
  const totalSec = Math.floor(durationMs / 1000);
  const timeStr = `${Math.floor(currentSec / 60)}:${(currentSec % 60).toString().padStart(2, '0')} / ${Math.floor(totalSec / 60)}:${(totalSec % 60).toString().padStart(2, '0')}`;

  return (
    <div className="flex items-center justify-center gap-2 px-3 py-1.5 bg-background/80 backdrop-blur border-t border-border">
      <span className="text-xs text-muted-foreground tabular-nums w-24 text-right">
        {timeStr}
      </span>

      <Button variant="ghost" size="icon" className="h-8 w-8">
        <SkipBack className="h-4 w-4" />
      </Button>

      <Button
        variant="default"
        size="icon"
        className="h-9 w-9 rounded-full"
        onClick={onPlayPause}
      >
        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4 ml-0.5" />}
      </Button>

      <Button variant="ghost" size="icon" className="h-8 w-8">
        <SkipForward className="h-4 w-4" />
      </Button>
    </div>
  );
}
