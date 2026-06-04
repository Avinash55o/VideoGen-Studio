import { useState, useEffect } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { PromptInput } from './PromptInput';
import { ModelSelector } from './ModelSelector';
import { GenerateButton } from './GenerateButton';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { apiClient } from '@/lib/api/client';
import { useGenerationProgress } from '@/lib/hooks/useGeneration';
import type { ClipResponse } from '@/lib/api/types';
import { useQueryClient } from '@tanstack/react-query';
import { useProjectStore } from '@/stores/projectStore';

interface VideoGenFormProps {
  projectId: string;
  onClipCreated?: (clip: ClipResponse) => void;
  _unused?: never;
}

export function VideoGenForm({ projectId, onClipCreated: _onClipCreated }: VideoGenFormProps) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const clips = useProjectStore((s) => s.clips);
  
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [model, setModel] = useState('cogvideo-2b-t2v');
  const [numFrames, setNumFrames] = useState(24);
  const [guidanceScale, setGuidanceScale] = useState(7);
  const [steps, setSteps] = useState(50);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [continueFromPrev, setContinueFromPrev] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);

  const { progress, status } = useGenerationProgress(taskId);
  const isGenerating = status === 'generating' || status === 'queued';

  // Filter video clips with valid generated media files
  const videoClips = clips
    .filter((c) => c.clip_type === 'video' && c.source_path)
    .sort((a, b) => b.end_time_ms - a.end_time_ms);
  const latestVideoClip = videoClips[0];

  useEffect(() => {
    if (status === 'complete') {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'clips'] });
      toast({
        title: 'Video generated successfully',
        description: 'The video clip has been added to your timeline.',
      });
      setTaskId(null);
      setPrompt('');
      setContinueFromPrev(false);
    } else if (status === 'error') {
      toast({
        title: 'Video generation failed',
        description: progress?.error || 'An unknown error occurred during video generation.',
        variant: 'destructive',
      });
      setTaskId(null);
    }
  }, [status, progress, projectId, queryClient, toast]);

  async function handleGenerate() {
    if (!prompt.trim()) return;

    try {
      const response = await apiClient.generateVideo({
        project_id: projectId,
        prompt,
        negative_prompt: negativePrompt || undefined,
        model,
        num_frames: numFrames,
        guidance_scale: guidanceScale,
        num_inference_steps: steps,
        seed,
        parent_clip_id: (continueFromPrev && latestVideoClip) ? latestVideoClip.id : undefined,
      });

      setTaskId(response.task_id);
    } catch (error) {
      toast({
        title: 'Generation failed',
        description: String(error),
        variant: 'destructive',
      });
    }
  }

  return (
    <div className="space-y-4 p-4">
      <h3 className="text-sm font-medium">Generate Video</h3>

      <PromptInput value={prompt} onChange={setPrompt} />

      <div className="space-y-2">
        <Label htmlFor="negative-prompt">Negative Prompt (optional)</Label>
        <Input
          id="negative-prompt"
          value={negativePrompt}
          onChange={(e) => setNegativePrompt(e.target.value)}
          placeholder="Things to avoid..."
        />
      </div>

      <ModelSelector value={model} onChange={setModel} />

      {latestVideoClip && (
        <div className="flex items-start space-x-2 py-2 bg-muted/40 p-2 rounded-md border border-border">
          <Checkbox
            id="continue-from-prev"
            checked={continueFromPrev}
            onCheckedChange={(checked) => setContinueFromPrev(!!checked)}
          />
          <div className="grid gap-1.5 leading-none">
            <label
              htmlFor="continue-from-prev"
              className="text-xs font-semibold leading-none cursor-pointer"
            >
              Continue from previous clip
            </label>
            <p className="text-[11px] text-muted-foreground leading-normal">
              Stitches generation to start from the last frame of the previous clip (ends at {(latestVideoClip.end_time_ms / 1000).toFixed(1)}s).
            </p>
          </div>
        </div>
      )}

      <div className="space-y-2">
        <Label>Frames: {numFrames}</Label>
        <Slider
          value={[numFrames]}
          onValueChange={([v]) => setNumFrames(v)}
          min={8}
          max={48}
          step={8}
        />
      </div>

      <div className="space-y-2">
        <Label>Guidance Scale: {guidanceScale}</Label>
        <Slider
          value={[guidanceScale]}
          onValueChange={([v]) => setGuidanceScale(v)}
          min={1}
          max={30}
          step={0.5}
        />
      </div>

      <div className="space-y-2">
        <Label>Steps: {steps}</Label>
        <Slider
          value={[steps]}
          onValueChange={([v]) => setSteps(v)}
          min={10}
          max={200}
          step={10}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="seed">Seed (optional)</Label>
        <Input
          id="seed"
          type="number"
          value={seed ?? ''}
          onChange={(e) => setSeed(e.target.value ? Number(e.target.value) : undefined)}
          placeholder="Random"
        />
      </div>

      <GenerateButton
        onClick={handleGenerate}
        isGenerating={isGenerating}
        progress={progress?.progress ?? 0}
      />
    </div>
  );
}
