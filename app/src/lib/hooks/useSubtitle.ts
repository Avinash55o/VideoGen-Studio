import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { SubtitleTrackResponse, SubtitleTrackUpdate } from '@/lib/api/types';

interface SubtitleGenerateInput {
  clip_id: string;
  language?: string;
  stt_model?: string;
}

export function useGenerateSubtitles() {
  return useMutation({
    mutationFn: (data: SubtitleGenerateInput) =>
      apiClient.generateSubtitles(data),
  });
}

export function useUpdateSubtitleTrack() {
  return useMutation({
    mutationFn: ({ trackId, data }: { trackId: string; data: SubtitleTrackUpdate }) =>
      apiClient.updateSubtitleTrack(trackId, data),
  });
}

export type { SubtitleTrackResponse, SubtitleTrackUpdate };
