import { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { PromptInput } from './PromptInput';
import { ModelSelector } from './ModelSelector';
import { GenerateButton } from './GenerateButton';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { apiClient } from '@/lib/api/client';
import { useGenerationProgress } from '@/lib/hooks/useGeneration';
import type { ClipResponse } from '@/lib/api/types';

interface VideoGenFormProps {
  projectId: string;
  onClipCreated?: (clip: ClipResponse) => void;
  _unused?: never;
}

export function VideoGenForm({ projectId, onClipCreated: _onClipCreated }: VideoGenFormProps) {
  const { toast } = useToast();
  const [prompt, setPrompt] = useState('');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [model, setModel] = useState('cogvideo-2b');
  const [numFrames, setNumFrames] = useState(24);
  const [guidanceScale, setGuidanceScale] = useState(7);
  const [steps, setSteps] = useState(50);
  const [seed, setSeed] = useState<number | undefined>(undefined);
  const [taskId, setTaskId] = useState<string | null>(null);

  const { progress, status } = useGenerationProgress(taskId);
  const isGenerating = status === 'generating' || status === 'queued';

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
