import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type { AudioLibraryEntryResponse } from '@/lib/api/types';

export function useAudioLibrary() {
  return useQuery<AudioLibraryEntryResponse[]>({
    queryKey: ['audio-library'],
    queryFn: () => apiClient.listAudioLibrary(),
  });
}
