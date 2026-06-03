import { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { useGenerateSubtitles } from '@/lib/hooks/useSubtitle';
import { useProjectStore } from '@/stores/projectStore';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function SubtitlePanel() {
  const { toast } = useToast();
  const clips = useProjectStore((s) => s.clips);
  const generateSubtitles = useGenerateSubtitles();

  const voiceoverClips = clips.filter((c) => c.clip_type === 'voiceover' && c.source_path);
  const [clipId, setClipId] = useState('');
  const [sttModel, setSttModel] = useState('turbo');

  async function handleGenerate() {
    if (!clipId) {
      toast({ title: 'Select a voiceover clip', variant: 'destructive' });
      return;
    }

    try {
      const result = await generateSubtitles.mutateAsync({
        clip_id: clipId,
        stt_model: sttModel,
      });
      toast({
        title: 'Subtitles generated',
        description: `${result.items.length} subtitle segments created`,
      });
    } catch (err) {
      toast({ title: 'Subtitle generation failed', description: String(err), variant: 'destructive' });
    }
  }

  if (voiceoverClips.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Generate a voiceover clip first to create subtitles from it.
      </div>
    );
  }

  return (
    <div className="space-y-4 p-4">
      <h3 className="text-sm font-medium">Generate Subtitles</h3>

      <div className="space-y-2">
        <Label htmlFor="st-clip">Voiceover Clip</Label>
        <Select value={clipId} onValueChange={setClipId}>
          <SelectTrigger id="st-clip">
            <SelectValue placeholder="Select a clip" />
          </SelectTrigger>
          <SelectContent>
            {voiceoverClips.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.source_text?.slice(0, 50) || c.id.slice(0, 8)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="st-model">STT Model</Label>
        <Select value={sttModel} onValueChange={setSttModel}>
          <SelectTrigger id="st-model">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="turbo">Whisper Turbo (fast)</SelectItem>
            <SelectItem value="large">Whisper Large (accurate)</SelectItem>
            <SelectItem value="medium">Whisper Medium</SelectItem>
            <SelectItem value="base">Whisper Base</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button
        className="w-full"
        onClick={handleGenerate}
        disabled={generateSubtitles.isPending || !clipId}
      >
        {generateSubtitles.isPending ? 'Transcribing...' : 'Generate Subtitles'}
      </Button>
    </div>
  );
}
