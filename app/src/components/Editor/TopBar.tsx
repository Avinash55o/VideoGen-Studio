import { ArrowLeft, Save } from 'lucide-react';
import { useNavigate } from '@tanstack/react-router';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useProjectStore } from '@/stores/projectStore';
import { ExportDialog } from './ExportDialog';

export function TopBar() {
  const navigate = useNavigate();
  const project = useProjectStore((s) => s.project);
  const isDirty = useProjectStore((s) => s.isDirty);

  if (!project) return null;

  return (
    <div className="flex items-center gap-3 px-4 py-2 border-b border-border bg-background">
      <Button
        variant="ghost"
        size="icon"
        className="h-8 w-8"
        onClick={() => navigate({ to: '/' })}
      >
        <ArrowLeft className="h-4 w-4" />
      </Button>

      <Input
        className="h-8 w-64 text-sm border-0 bg-transparent focus-visible:bg-muted/50"
        defaultValue={project.name}
      />

      <div className="flex-1" />

      {isDirty && <span className="text-xs text-muted-foreground">Unsaved changes</span>}

      <Button variant="outline" size="sm" className="h-8">
        <Save className="h-3.5 w-3.5 mr-1.5" />
        Save
      </Button>

      <ExportDialog projectId={project.id} />
    </div>
  );
}
