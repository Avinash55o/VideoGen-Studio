import { CheckCircle2, Loader2, XCircle } from 'lucide-react';
import { useCallback, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';
import { apiClient } from '@/lib/api/client';

interface UseModelDownloadToastOptions {
  modelName: string;
  displayName: string;
  enabled?: boolean;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

/**
 * Hook to show and update a toast notification with model download progress.
 * Monitors download progress via query polling, avoiding SSE connection limits.
 */
export function useModelDownloadToast({
  modelName,
  displayName,
  enabled = false,
  onComplete,
  onError,
}: UseModelDownloadToastOptions) {
  const { toast } = useToast();
  const toastIdRef = useRef<string | null>(null);
  // biome-ignore lint: Using any for toast update ref to handle complex toast types
  const toastUpdateRef = useRef<any>(null);
  const wasDownloadingRef = useRef<boolean>(false);
  const prevStatusRef = useRef<string | null>(null);

  const formatBytes = useCallback((bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / k ** i).toFixed(1)} ${sizes[i]}`;
  }, []);

  const { data: activeTasks } = useQuery({
    queryKey: ['activeTasks'],
    queryFn: () => apiClient.getActiveTasks(),
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasActive = data?.downloads.some((d) => d.status === 'downloading');
      return hasActive ? 1000 : 5000;
    },
    enabled: enabled && !!modelName,
  });

  const task = activeTasks?.downloads.find((d) => d.model_name === modelName);

  // Initialize toast when enabled
  useEffect(() => {
    if (!enabled || !modelName) {
      if (toastIdRef.current) {
        toastIdRef.current = null;
        toastUpdateRef.current = null;
      }
      wasDownloadingRef.current = false;
      prevStatusRef.current = null;
      return;
    }

    if (!toastIdRef.current) {
      console.log('[useModelDownloadToast] Creating initial toast for:', modelName);
      const toastResult = toast({
        title: displayName,
        description: (
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Connecting to download...</span>
          </div>
        ),
        duration: Infinity, // Don't auto-dismiss, we'll handle it manually
      });
      toastIdRef.current = toastResult.id;
      toastUpdateRef.current = toastResult.update;
    }
  }, [enabled, modelName, displayName, toast]);

  // Handle task updates
  useEffect(() => {
    if (!enabled || !modelName || !toastIdRef.current || !toastUpdateRef.current) {
      return;
    }

    if (task) {
      const isDownloading = task.status === 'downloading' || task.status === 'extracting';
      
      if (isDownloading) {
        wasDownloadingRef.current = true;
      }

      // Avoid redundant toast updates if status/progress hasn't changed
      const currentStatusKey = `${task.status}-${task.progress}-${task.filename}`;
      if (prevStatusRef.current === currentStatusKey) {
        return;
      }
      prevStatusRef.current = currentStatusKey;

      const progressPercent = task.total && task.total > 0 ? (task.progress ?? 0) : 0;
      const progressText =
        task.total && task.total > 0
          ? `${formatBytes(task.current ?? 0)} / ${formatBytes(task.total)} (${(task.progress ?? 0).toFixed(1)}%)`
          : '';

      let statusIcon: React.ReactNode = null;
      let statusText = 'Processing...';

      switch (task.status) {
        case 'complete':
          statusIcon = <CheckCircle2 className="h-4 w-4 text-green-500" />;
          statusText = 'Download complete';
          break;
        case 'error':
          statusIcon = <XCircle className="h-4 w-4 text-destructive" />;
          statusText = 'Download failed. See Problems panel for details.';
          break;
        case 'downloading':
          statusIcon = <Loader2 className="h-4 w-4 animate-spin" />;
          statusText = task.filename || 'Downloading...';
          break;
        case 'extracting':
          statusIcon = <Loader2 className="h-4 w-4 animate-spin" />;
          statusText = 'Extracting...';
          break;
      }

      toastUpdateRef.current({
        title: (
          <div className="flex items-center gap-2">
            {statusIcon}
            <span>{displayName}</span>
          </div>
        ),
        description: (
          <div className="space-y-2">
            <div className="text-sm">{statusText}</div>
            {task.total && task.total > 0 && (
              <>
                <Progress value={progressPercent} className="h-2" />
                <div className="text-xs text-muted-foreground">{progressText}</div>
              </>
            )}
          </div>
        ),
        duration: task.status === 'complete' || task.status === 'error' ? 5000 : Infinity,
      });

      if (task.status === 'complete') {
        toastIdRef.current = null;
        toastUpdateRef.current = null;
        if (onComplete) onComplete();
      } else if (task.status === 'error') {
        toastIdRef.current = null;
        toastUpdateRef.current = null;
        if (onError) onError(task.error || 'Unknown error');
      }
    } else {
      // Task is no longer in the active list.
      // If we were previously downloading, it means it completed and was deleted.
      if (wasDownloadingRef.current) {
        console.log('[useModelDownloadToast] Task disappeared while downloading - assuming complete:', modelName);
        
        toastUpdateRef.current({
          title: (
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span>{displayName}</span>
            </div>
          ),
          description: 'Download complete',
          duration: 3000,
        });

        toastIdRef.current = null;
        toastUpdateRef.current = null;
        wasDownloadingRef.current = false;
        if (onComplete) onComplete();
      }
    }
  }, [enabled, modelName, displayName, task, formatBytes, onComplete, onError]);

  return {
    isTracking: enabled && task !== undefined,
  };
}
