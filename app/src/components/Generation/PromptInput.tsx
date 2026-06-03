import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

interface PromptInputProps {
  value: string;
  onChange: (value: string) => void;
}

export function PromptInput({ value, onChange }: PromptInputProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="prompt">Prompt</Label>
      <Textarea
        id="prompt"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Describe the video you want to generate..."
        className="min-h-[80px] resize-none"
      />
    </div>
  );
}
