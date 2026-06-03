import { Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface GenerateButtonProps {
  onClick: () => void;
  isGenerating: boolean;
  progress: number;
}

export function GenerateButton({ onClick, isGenerating, progress }: GenerateButtonProps) {
  return (
    <div className="space-y-2">
      <Button
        onClick={onClick}
        disabled={isGenerating}
        className="w-full"
        size="lg"
      >
        {isGenerating ? (
          <>Generating... {Math.round(progress)}%</>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            Generate Video
          </>
        )}
      </Button>
      {isGenerating && <Progress value={progress} className="h-1" />}
    </div>
  );
}
