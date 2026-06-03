import { useParams } from '@tanstack/react-router';
import { useEffect } from 'react';
import { EditorLayout } from './EditorLayout';
import { TopBar } from './TopBar';
import { VideoPreview } from '@/components/Preview/VideoPreview';
import { Timeline } from '@/components/Timeline/Timeline';
import { RightPanel } from './RightPanel';
import { useProject, useClips, useBatchUpdateTimeline } from '@/lib/hooks/useProject';
import { useProjectStore } from '@/stores/projectStore';
import { usePreviewStore } from '@/stores/previewStore';
import { useTimelineStore } from '@/stores/timelineStore';
import type { ClipResponse, TimelineClipPosition } from '@/lib/api/types';

export function ProjectEditor() {
  const { projectId } = useParams({ from: '/projects/$projectId' });
  const { data: project } = useProject(projectId);
  const { data: clips } = useClips(projectId);
  const batchUpdate = useBatchUpdateTimeline();

  const loadProject = useProjectStore((s) => s.loadProject);
  const unloadProject = useProjectStore((s) => s.unloadProject);
  const projectStoreClips = useProjectStore((s) => s.clips);

  const isPlaying = usePreviewStore((s) => s.isPlaying);
  const playheadMs = useTimelineStore((s) => s.playheadMs);
  const setPlayheadMs = useTimelineStore((s) => s.setPlayheadMs);
  const togglePlay = usePreviewStore((s) => s.togglePlay);

  useEffect(() => {
    if (project && clips) {
      loadProject(project, clips);
    }
    return () => unloadProject();
  }, [project, clips, loadProject, unloadProject]);

  function handleClipsReorder(positions: TimelineClipPosition[]) {
    if (!projectId) return;
    batchUpdate.mutate({ projectId, positions });
  }

  function handleClipResize(clipId: string, endTimeMs: number) {
    useProjectStore.getState().resizeClipLocally(clipId, endTimeMs);
  }

  function handleClipCreated(clip: ClipResponse) {
    useProjectStore.getState().addClip(clip);
  }

  const durationMs = project ? project.duration_seconds * 1000 : 10000;
  const fps = project?.fps ?? 24;

  return (
    <EditorLayout
      topBar={<TopBar />}
      preview={
        <VideoPreview
          clips={projectStoreClips}
          playheadMs={playheadMs}
          isPlaying={isPlaying}
          onTimeUpdate={setPlayheadMs}
          onPlayStateChange={(playing) => {
            if (playing) togglePlay();
            else togglePlay();
          }}
        />
      }
      timeline={
        <Timeline
          clips={projectStoreClips}
          durationMs={durationMs}
          fps={fps}
          onClipsReorder={handleClipsReorder}
          onClipSelect={(id) => useProjectStore.getState().selectClip(id)}
          onClipResize={handleClipResize}
        />
      }
      rightPanel={
        <RightPanel
          projectId={projectId ?? ''}
          onClipCreated={handleClipCreated}
        />
      }
    />
  );
}
