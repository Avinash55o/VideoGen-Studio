import { useNavigate } from '@tanstack/react-router';
import { Clapperboard, MoreHorizontal, Trash2 } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { ProjectResponse } from '@/lib/api/types';
import { cn } from '@/lib/utils/cn';

interface ProjectCardProps {
  project: ProjectResponse;
  onDelete: (projectId: string) => void;
}

export function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const navigate = useNavigate();
  const [isDeleting, setIsDeleting] = useState(false);

  function handleClick() {
    navigate({ to: '/projects/$projectId', params: { projectId: project.id } });
  }

  function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    setIsDeleting(true);
    onDelete(project.id);
  }

  return (
    <Card
      className={cn(
        'group cursor-pointer transition-all duration-200 hover:border-accent/50 hover:shadow-md',
        isDeleting && 'opacity-50 pointer-events-none',
      )}
      onClick={handleClick}
    >
      <CardHeader className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center shrink-0">
              <Clapperboard className="w-5 h-5 text-accent" />
            </div>
            <div className="min-w-0">
              <CardTitle className="text-base truncate">{project.name}</CardTitle>
              <CardDescription className="text-xs mt-0.5">
                {project.width}x{project.height} &middot; {project.fps}fps &middot;{' '}
                {project.duration_seconds}s &middot; {project.clip_count} clips
              </CardDescription>
            </div>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
              <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem className="text-destructive" onClick={handleDelete}>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
          <span className={cn(
            'px-1.5 py-0.5 rounded-full',
            project.render_status === 'draft' && 'bg-muted text-muted-foreground',
            project.render_status === 'complete' && 'bg-green-500/10 text-green-500',
            project.render_status === 'rendering' && 'bg-accent/10 text-accent',
            project.render_status === 'failed' && 'bg-destructive/10 text-destructive',
          )}>
            {project.render_status}
          </span>
          <span>{new Date(project.updated_at).toLocaleDateString()}</span>
        </div>
      </CardHeader>
    </Card>
  );
}
