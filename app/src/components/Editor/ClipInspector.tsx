import { X, Trash2, Type, Music, Video, Image, Volume2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { useProjectStore } from '@/stores/projectStore';
import { useToast } from '@/components/ui/use-toast';
import { useDeleteClip } from '@/lib/hooks/useProject';
import type { ClipResponse } from '@/lib/api/types';

const CLIP_ICONS: Record<string, typeof Video> = {
  video: Video,
  voiceover: Type,
  music: Music,
  image: Image,
  subtitle: Type,
  text: Type,
};

const CLIP_COLORS: Record<string, string> = {
  video: 'bg-blue-500/10 text-blue-500 border-blue-500/30',
  voiceover: 'bg-green-500/10 text-green-500 border-green-500/30',
  music: 'bg-purple-500/10 text-purple-500 border-purple-500/30',
};

export function ClipInspector() {
  const { toast } = useToast();
  const selectedClipId = useProjectStore((s) => s.selectedClipId);
  const clips = useProjectStore((s) => s.clips);
  const selectClip = useProjectStore((s) => s.selectClip);
  const updateClip = useProjectStore((s) => s.updateClip);
  const project = useProjectStore((s) => s.project);

  const deleteClip = useDeleteClip();
  const clip = clips.find((c) => c.id === selectedClipId);

  if (!clip) return null;

  const Icon = CLIP_ICONS[clip.clip_type] ?? Type;
  const colorClass = CLIP_COLORS[clip.clip_type] ?? 'bg-gray-500/10 text-gray-500 border-gray-500/30';

  async function handleDelete() {
    if (!project) return;
    try {
      await deleteClip.mutateAsync({ projectId: project.id, clipId: clip!.id });
      useProjectStore.getState().removeClip(clip!.id);
      toast({ title: 'Clip deleted' });
    } catch (err) {
      toast({ title: 'Delete failed', description: String(err), variant: 'destructive' });
    }
  }

  function updateField<K extends keyof ClipResponse>(key: K, value: ClipResponse[K]) {
    updateClip(clip!.id, { [key]: value } as Partial<ClipResponse>);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <div className={`p-1 rounded border ${colorClass}`}>
            <Icon className="h-3.5 w-3.5" />
          </div>
          <h3 className="text-sm font-medium">Clip Inspector</h3>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={handleDelete}>
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => selectClip(null)}>
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={colorClass}>
            {clip.clip_type}
          </Badge>
          {clip.source_path && (
            <Badge variant="secondary" className="text-[10px]">
              Has media
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-[11px]">Track</Label>
            <Input
              type="number"
              value={clip.track}
              onChange={(e) => updateField('track', Number(e.target.value))}
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-[11px]">Volume</Label>
            <div className="flex items-center gap-2">
              <Volume2 className="h-3 w-3 text-muted-foreground" />
              <Slider
                value={[clip.volume]}
                onValueChange={([v]) => updateField('volume', v)}
                min={0}
                max={2}
                step={0.1}
                className="flex-1"
              />
              <span className="text-xs text-muted-foreground w-6 text-right tabular-nums">
                {clip.volume.toFixed(1)}
              </span>
            </div>
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="text-[11px]">Start Time (ms)</Label>
          <Input
            type="number"
            value={clip.start_time_ms}
            onChange={(e) => updateField('start_time_ms', Number(e.target.value))}
            className="h-8 text-xs"
          />
        </div>

        <div className="space-y-1.5">
          <Label className="text-[11px]">End Time (ms)</Label>
          <Input
            type="number"
            value={clip.end_time_ms}
            onChange={(e) => updateField('end_time_ms', Number(e.target.value))}
            className="h-8 text-xs"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="text-[11px]">Fade In (ms)</Label>
            <Input
              type="number"
              value={clip.fade_in_ms}
              onChange={(e) => updateField('fade_in_ms', Number(e.target.value))}
              className="h-8 text-xs"
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-[11px]">Fade Out (ms)</Label>
            <Input
              type="number"
              value={clip.fade_out_ms}
              onChange={(e) => updateField('fade_out_ms', Number(e.target.value))}
              className="h-8 text-xs"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label className="text-[11px]">Speed: {clip.speed.toFixed(2)}x</Label>
          <Slider
            value={[clip.speed]}
            onValueChange={([v]) => updateField('speed', v)}
            min={0.25}
            max={4}
            step={0.25}
          />
        </div>

        {clip.source_text && (
          <div className="space-y-1.5">
            <Label className="text-[11px]">Text</Label>
            <p className="text-xs text-muted-foreground bg-muted/50 rounded p-2 leading-relaxed">
              {clip.source_text}
            </p>
          </div>
        )}

        {clip.model && (
          <div className="space-y-1.5">
            <Label className="text-[11px]">Generated with</Label>
            <p className="text-xs text-muted-foreground">{clip.model}</p>
          </div>
        )}
      </div>
    </div>
  );
}
