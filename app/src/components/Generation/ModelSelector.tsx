import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const MODELS = [
  { value: 'cogvideo-2b-t2v', label: 'CogVideoX 2B (T2V)', description: 'Fast, good quality text-to-video' },
  { value: 'cogvideo-5b-i2v', label: 'CogVideoX 5B (I2V)', description: 'High quality image continuation' },
  { value: 'wan-t2v-1.3b', label: 'Wan2.1 T2V 1.3B', description: 'Lightweight, state-of-the-art prompt following' },
  { value: 'wan-i2v-14b', label: 'Wan2.1 I2V 14B (480P)', description: 'Powerful image-to-video continuation' },
  { value: 'ltx-video', label: 'LTX-Video (T2V/I2V)', description: 'Ultra-fast, adjustable resolution' },
  { value: 'hunyuan-video', label: 'HunyuanVideo (T2V)', description: 'Highly realistic 720p movements' },
  { value: 'mochi-1-preview', label: 'Mochi-1 Preview (T2V)', description: 'High motion dynamics preview' },
  { value: 'svd-xt', label: 'Stable Video Diffusion XT', description: 'Stable, classic image-to-video' },
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
