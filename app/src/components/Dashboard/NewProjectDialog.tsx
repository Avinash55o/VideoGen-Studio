import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useCreateProject } from '@/lib/hooks/useProject';
import type { ProjectResponse } from '@/lib/api/types';

const formSchema = z.object({
  name: z.string().min(1, 'Name is required').max(200),
  description: z.string().max(500).optional(),
  width: z.coerce.number().int().min(1).max(7680).default(1920),
  height: z.coerce.number().int().min(1).max(4320).default(1080),
  fps: z.coerce.number().int().min(1).max(120).default(24),
  duration_seconds: z.coerce.number().min(0.5).max(600).default(10),
});

type FormData = z.infer<typeof formSchema>;

interface NewProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated?: (project: ProjectResponse) => void;
}

export function NewProjectDialog({ open, onOpenChange, onCreated }: NewProjectDialogProps) {
  const createProject = useCreateProject();
  const form = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      description: '',
      width: 1920,
      height: 1080,
      fps: 24,
      duration_seconds: 10,
    },
  });

  async function handleSubmit(data: FormData) {
    try {
      const project = await createProject.mutateAsync(data);
      form.reset();
      onOpenChange(false);
      onCreated?.(project);
    } catch {
      // error handled by react-query
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New Project</DialogTitle>
          <DialogDescription>
            Create a new video project
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input id="name" {...form.register('name')} placeholder="My Video Project" />
            {form.formState.errors.name && (
              <p className="text-sm text-destructive">{form.formState.errors.name.message}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Input id="description" {...form.register('description')} placeholder="What's this project about?" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="width">Width</Label>
              <Input id="width" type="number" {...form.register('width')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="height">Height</Label>
              <Input id="height" type="number" {...form.register('height')} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="fps">FPS</Label>
              <Input id="fps" type="number" {...form.register('fps')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration (seconds)</Label>
              <Input id="duration" type="number" step="0.5" {...form.register('duration_seconds')} />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
