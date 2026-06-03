import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { VoiceProfileResponseV2 } from '@/lib/api/types';

export function useVoiceProfilesV2() {
  return useQuery<VoiceProfileResponseV2[]>({
    queryKey: ['voice-profiles-v2'],
    queryFn: () => apiClient.listVoiceProfilesV2(),
  });
}
