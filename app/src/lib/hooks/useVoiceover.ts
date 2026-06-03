import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

interface VoiceoverGenerateInput {
  project_id: string;
  profile_id: string;
  text: string;
  language?: string;
  engine?: string;
}

export function useGenerateVoiceover() {
  return useMutation({
    mutationFn: (data: VoiceoverGenerateInput) =>
      apiClient.generateVoiceover(data),
  });
}
