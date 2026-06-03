import { useNavigate } from '@tanstack/react-router';
import { Plus, Clapperboard, Search } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useProjects, useDeleteProject } from '@/lib/hooks/useProject';
import { ProjectCard } from './ProjectCard';
import { NewProjectDialog } from './NewProjectDialog';

export function ProjectDashboard() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useProjects();
  const deleteProject = useDeleteProject();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [search, setSearch] = useState('');

  const projects = data?.items ?? [];
  const filtered = search
    ? projects.filter((p) =>
        p.name.toLowerCase().includes(search.toLowerCase()),
      )
    : projects;

  function handleDelete(projectId: string) {
    deleteProject.mutate(projectId);
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-pulse text-muted-foreground">Loading projects...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-destructive">Failed to load projects</div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col py-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Projects</h1>
          <p className="text-sm text-muted-foreground mt-1">
            {projects.length} project{projects.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Project
        </Button>
      </div>

      {projects.length > 0 && (
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            className="pl-9"
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Clapperboard className="w-16 h-16 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium text-muted-foreground mb-2">
              {search ? 'No matching projects' : 'No projects yet'}
            </h3>
            <p className="text-sm text-muted-foreground/70 mb-4 max-w-sm">
              {search
                ? 'Try a different search term'
                : 'Create your first project to get started with video generation'}
            </p>
            {!search && (
              <Button onClick={() => setDialogOpen(true)} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Create Project
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filtered.map((project) => (
              <ProjectCard key={project.id} project={project} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>

      <NewProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onCreated={(project) => {
          navigate({ to: '/projects/$projectId', params: { projectId: project.id } });
        }}
      />
    </div>
  );
}
