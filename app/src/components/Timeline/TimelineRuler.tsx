import { useTimelineContext, PIXELS_PER_SECOND } from './TimelineContext';

export function TimelineRuler() {
  const { durationMs, zoom } = useTimelineContext();
  const totalWidth = (durationMs / 1000) * PIXELS_PER_SECOND * zoom;
  const intervalMs = getRulerInterval(durationMs);

  const ticks: { ms: number; label: string }[] = [];
  for (let ms = 0; ms <= durationMs; ms += intervalMs) {
    const seconds = ms / 1000;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    ticks.push({ ms, label: mins > 0 ? `${mins}:${secs.toString().padStart(2, '0')}` : `${secs}s` });
  }

  return (
    <div className="relative h-6 border-b border-border shrink-0" style={{ width: totalWidth }}>
      {ticks.map((tick) => {
        const left = (tick.ms / durationMs) * 100;
        return (
          <div
            key={tick.ms}
            className="absolute top-0 flex flex-col items-center"
            style={{ left: `${left}%`, transform: 'translateX(-50%)' }}
          >
            <div className="w-px h-2 bg-border" />
            <span className="text-[10px] text-muted-foreground mt-0.5 whitespace-nowrap">
              {tick.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function getRulerInterval(totalMs: number): number {
  const totalSec = totalMs / 1000;
  if (totalSec <= 10) return 1000;
  if (totalSec <= 30) return 2000;
  if (totalSec <= 60) return 5000;
  return 10000;
}
