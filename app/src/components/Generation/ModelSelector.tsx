import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const MODELS = [
  { value: 'cogvideo-2b', label: 'CogVideoX 2B (T2V)', description: 'Fast, good quality' },
  { value: 'wan-t2v', label: 'Wan2.1 T2V 1.3B', description: 'Lightweight, efficient' },
];

interface ModelSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export function ModelSelector({ value, onChange }: ModelSelectorProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor="model">Model</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="model">
          <SelectValue placeholder="Select a model" />
        </SelectTrigger>
        <SelectContent>
          {MODELS.map((model) => (
            <SelectItem key={model.value} value={model.value}>
              <div className="flex flex-col">
                <span>{model.label}</span>
                <span className="text-xs text-muted-foreground">{model.description}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
