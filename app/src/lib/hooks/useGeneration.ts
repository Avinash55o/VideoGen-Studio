import { useMutation } from '@tanstack/react-query';
import { useEffect, useRef, useState } from 'react';
import { apiClient } from '@/lib/api/client';
import type { VideoGenerationRequest, ModelProgress } from '@/lib/api/types';

export function useGenerateVideo() {
  return useMutation({
    mutationFn: (data: VideoGenerationRequest) =>
      apiClient.generateVideo(data),
  });
}

// Keep backward compatibility for TTS generation callers
export function useGeneration() {
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.generateSpeech(data as unknown as Parameters<typeof apiClient.generateSpeech>[0]),
  });
}

export function useGenerationProgress(taskId: string | null) {
  const [progress, setProgress] = useState<ModelProgress | null>(null);
  const [status, setStatus] = useState<'idle' | 'queued' | 'generating' | 'complete' | 'error'>('idle');
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!taskId) {
      setProgress(null);
      setStatus('idle');
      return;
    }

    setStatus('queued');
    const url = apiClient.getGenerationProgressUrl(taskId);
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ModelProgress;
        setProgress(data);

        if (data.status === 'complete') {
          setStatus('complete');
          es.close();
        } else if (data.status === 'error') {
          setStatus('error');
          es.close();
        } else if (data.status === 'downloading' || data.status === 'extracting') {
          setStatus('generating');
        }
      } catch {
        // heartbeat or parse error
      }
    };

    es.onerror = () => {
      setStatus('error');
      es.close();
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [taskId]);

  return { progress, status };
}
