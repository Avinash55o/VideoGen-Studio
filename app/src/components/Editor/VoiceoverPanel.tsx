import { useState } from 'react';
import { useToast } from '@/components/ui/use-toast';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useGenerateVoiceover } from '@/lib/hooks/useVoiceover';
import { useVoiceProfilesV2 } from '@/lib/hooks/useVoiceProfilesV2';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { ClipResponse } from '@/lib/api/types';

interface VoiceoverPanelProps {
  projectId: string;
  onClipCreated: (clip: ClipResponse) => void;
}

export function VoiceoverPanel({ projectId, onClipCreated }: VoiceoverPanelProps) {
  const { toast } = useToast();
  const { data: profiles } = useVoiceProfilesV2();
  const generateVoiceover = useGenerateVoiceover();

  const [profileId, setProfileId] = useState('');
  const [text, setText] = useState('');

  async function handleGenerate() {
    if (!profileId || !text.trim()) {
      toast({ title: 'Select a voice profile and enter text', variant: 'destructive' });
      return;
    }

    try {
      const result = await generateVoiceover.mutateAsync({
        project_id: projectId,
        profile_id: profileId,
        text: text.trim(),
      });

      toast({ title: 'Voiceover queued', description: `Clip ${result.clip_id} is generating` });

      onClipCreated({
        id: result.clip_id,
        project_id: projectId,
        track: 1,
        start_time_ms: 0,
        end_time_ms: 5000,
        clip_type: 'voiceover',
        source_text: text.trim(),
        volume: 1,
        speed: 1,
        fade_in_ms: 0,
        fade_out_ms: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as ClipResponse);

      setText('');
    } catch (err) {
      toast({ title: 'Voiceover failed', description: String(err), variant: 'destructive' });
    }
  }

  return (
    <div className="space-y-4 p-4">
      <h3 className="text-sm font-medium">Generate Voiceover</h3>

      <div className="space-y-2">
        <Label htmlFor="vo-profile">Voice Profile</Label>
        <Select value={profileId} onValueChange={setProfileId}>
          <SelectTrigger id="vo-profile">
            <SelectValue placeholder="Select a voice" />
          </SelectTrigger>
          <SelectContent>
            {profiles?.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="vo-text">Text to speak</Label>
        <Textarea
          id="vo-text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter narration text..."
          className="min-h-[100px] resize-none"
        />
      </div>

      <Button
        className="w-full"
        onClick={handleGenerate}
        disabled={generateVoiceover.isPending || !profileId || !text.trim()}
      >
        {generateVoiceover.isPending ? 'Generating...' : 'Generate Voiceover'}
      </Button>
    </div>
  );
}
