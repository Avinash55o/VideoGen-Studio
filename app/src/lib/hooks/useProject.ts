import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import type {
  ProjectCreate,
  ProjectUpdate,
  ProjectResponse,
  ProjectListResponse,
  ClipCreate,
  ClipUpdate,
  ClipResponse,
  TimelineClipPosition,
} from '@/lib/api/types';

export function useProjects() {
  return useQuery<ProjectListResponse>({
    queryKey: ['projects'],
    queryFn: () => apiClient.listProjects(),
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery<ProjectResponse>({
    queryKey: ['projects', projectId],
    queryFn: () => apiClient.getProject(projectId!),
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => apiClient.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useUpdateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectUpdate }) =>
      apiClient.updateProject(projectId, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['projects', vars.projectId] });
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => apiClient.deleteProject(projectId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useClips(projectId: string | undefined) {
  return useQuery<ClipResponse[]>({
    queryKey: ['projects', projectId, 'clips'],
    queryFn: () => apiClient.listClips(projectId!),
    enabled: !!projectId,
  });
}

export function useCreateClip() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ClipCreate }) =>
      apiClient.createClip(projectId, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['projects', vars.projectId, 'clips'] });
    },
  });
}

export function useUpdateClip() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, clipId, data }: { projectId: string; clipId: string; data: ClipUpdate }) =>
      apiClient.updateClip(projectId, clipId, data),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['projects', vars.projectId, 'clips'] });
    },
  });
}

export function useDeleteClip() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, clipId }: { projectId: string; clipId: string }) =>
      apiClient.deleteClip(projectId, clipId),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['projects', vars.projectId, 'clips'] });
    },
  });
}

export function useBatchUpdateTimeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ projectId, positions }: { projectId: string; positions: TimelineClipPosition[] }) =>
      apiClient.batchUpdateTimeline(projectId, positions),
    onSuccess: (_, vars) => {
      queryClient.invalidateQueries({ queryKey: ['projects', vars.projectId, 'clips'] });
    },
  });
}
