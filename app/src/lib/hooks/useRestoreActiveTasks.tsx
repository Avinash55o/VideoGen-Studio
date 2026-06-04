import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useGenerationStore } from '@/stores/generationStore';

/**
 * Hook to monitor active tasks (downloads and generations).
 * Polls the server periodically (dynamically throttled) to catch downloads triggered from anywhere.
 *
 * Returns the active downloads so components can render download toasts.
 */
export function useRestoreActiveTasks() {
  const setActiveGenerationId = useGenerationStore((state) => state.setActiveGenerationId);
  const addPendingGeneration = useGenerationStore((state) => state.addPendingGeneration);

  const { data: tasks } = useQuery({
    queryKey: ['activeTasks'],
    queryFn: () => apiClient.getActiveTasks(),
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasActive =
        data?.downloads.some((d) => d.status === 'downloading') ||
        (data?.generations && data.generations.length > 0);
      return hasActive ? 1000 : 5000;
    },
  });

  // Restore pending generations (e.g., after page refresh)
  useEffect(() => {
    if (!tasks) return;

    if (tasks.generations && tasks.generations.length > 0) {
      setActiveGenerationId(tasks.generations[0].task_id);
      for (const gen of tasks.generations) {
        addPendingGeneration(gen.task_id);
      }
    } else {
      const currentId = useGenerationStore.getState().activeGenerationId;
      if (currentId) {
        setActiveGenerationId(null);
      }
    }
  }, [tasks, setActiveGenerationId, addPendingGeneration]);

  return tasks?.downloads ?? [];
}

/**
 * Map model names to display names for download toasts.
 */
export const MODEL_DISPLAY_NAMES: Record<string, string> = {
  // Voice Models (Qwen)
  'qwen-tts-1.7B': 'Qwen TTS 1.7B',
  'qwen-tts-0.6B': 'Qwen TTS 0.6B',
  'qwen-custom-voice-1.7B': 'Qwen CustomVoice 1.7B',
  'qwen-custom-voice-0.6B': 'Qwen CustomVoice 0.6B',

  // Voice Models (Others)
  'luxtts': 'LuxTTS',
  'chatterbox-tts': 'Chatterbox TTS',
  'chatterbox-turbo': 'Chatterbox Turbo',
  'tada-1b': 'TADA 1B',
  'tada-3b-ml': 'TADA 3B Multilingual',
  'kokoro': 'Kokoro 82M',

  // Transcription
  'whisper-base': 'Whisper Base',
  'whisper-small': 'Whisper Small',
  'whisper-medium': 'Whisper Medium',
  'whisper-large': 'Whisper Large',
  'whisper-turbo': 'Whisper Large v3 Turbo',

  // Language Models
  'qwen3-0.6b': 'Qwen3 0.6B',
  'qwen3-1.7b': 'Qwen3 1.7B',
  'qwen3-4b': 'Qwen3 4B',

  // Video Models
  'cogvideo-5b-i2v': 'CogVideoX 5B I2V',
  'cogvideo-2b-t2v': 'CogVideoX 2B T2V',
  'wan-t2v-1.3b': 'Wan2.1 T2V 1.3B',
  'wan-i2v-14b': 'Wan2.1 I2V 14B',
  'ltx-video': 'LTX-Video',
  'hunyuan-video': 'HunyuanVideo',
  'mochi-1-preview': 'Mochi-1 Preview',
  'svd-xt': 'Stable Video Diffusion XT',
};
