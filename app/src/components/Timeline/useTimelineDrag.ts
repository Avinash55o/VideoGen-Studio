import { useCallback } from 'react';
import type { TimelineClipPosition } from '@/lib/api/types';

interface UseTimelineDragOptions {
  onBatchUpdate: (positions: TimelineClipPosition[]) => void;
}

export function useTimelineDrag({ onBatchUpdate }: UseTimelineDragOptions) {
  const handleClipsReorder = useCallback(
    (positions: TimelineClipPosition[]) => {
      onBatchUpdate(positions);
    },
    [onBatchUpdate],
  );

  return { handleClipsReorder };
}
