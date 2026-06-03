import { useState, useEffect } from 'react';
import { Download, Loader2, CheckCircle2, AlertCircle, Film } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { apiClient } from '@/lib/api/client';
import { useProjectStore } from '@/stores/projectStore';

interface ExportDialogProps {
  projectId: string;
}

export function ExportDialog({ projectId }: ExportDialogProps) {
  const [open, setOpen] = useState(false);
  const [format, setFormat] = useState('mp4');
  const [resolution, setResolution] = useState('1920x1080');
  const [status, setStatus] = useState<'idle' | 'rendering' | 'complete' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const projectName = useProjectStore((s) => s.project?.name ?? 'video');

  const pollIntervalMs = 2000;

  useEffect(() => {
    if (status !== 'rendering') return;

    const interval = setInterval(async () => {
      try {
        const result = await apiClient.getRenderStatus(projectId);
        setProgress(result.progress);

        if (result.status === 'complete') {
          setStatus('complete');
          setProgress(1);
          clearInterval(interval);
        } else if (result.status === 'failed') {
          setStatus('error');
          clearInterval(interval);
        }
      } catch {
        clearInterval(interval);
        setStatus('error');
      }
    }, pollIntervalMs);

    return () => clearInterval(interval);
  }, [status, projectId]);

  async function handleExport() {
    setStatus('rendering');
    setProgress(0);
    try {
      await apiClient.startRender(projectId, {
        format,
        resolution: resolution !== '1920x1080' ? resolution : undefined,
      });
    } catch {
      setStatus('error');
    }
  }

  function handleDownload() {
    const url = apiClient.getRenderDownloadUrl(projectId);
    window.open(url, '_blank');
    setOpen(false);
    setTimeout(() => setStatus('idle'), 500);
  }

  function handleClose() {
    if (status === 'rendering') return;
    setOpen(false);
    setTimeout(() => setStatus('idle'), 300);
  }

  const resolutions = [
    { value: '1920x1080', label: '1080p (1920×1080)' },
    { value: '1280x720', label: '720p (1280×720)' },
    { value: '3840x2160', label: '4K (3840×2160)' },
  ];

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) handleClose(); else setOpen(true); }}>
      <DialogTrigger asChild>
        <Button variant="default" size="sm" className="h-8">
          <Download className="h-3.5 w-3.5 mr-1.5" />
          Export
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Export Project</DialogTitle>
          <DialogDescription>
            Compose all clips into a final video file.
          </DialogDescription>
        </DialogHeader>

        {status === 'idle' && (
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="export-format">Format</Label>
              <Select value={format} onValueChange={setFormat}>
                <SelectTrigger id="export-format">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mp4">MP4 (H.264)</SelectItem>
                  <SelectItem value="webm">WebM (VP9)</SelectItem>
                  <SelectItem value="mov">MOV (ProRes)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="export-resolution">Resolution</Label>
              <Select value={resolution} onValueChange={setResolution}>
                <SelectTrigger id="export-resolution">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {resolutions.map((r) => (
                    <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        )}

        {status === 'rendering' && (
          <div className="space-y-4 py-4 text-center">
            <Loader2 className="w-8 h-8 animate-spin mx-auto text-accent" />
            <p className="text-sm text-muted-foreground">Rendering video...</p>
            <Progress value={progress * 100} className="h-2" />
            <p className="text-xs text-muted-foreground">{Math.round(progress * 100)}%</p>
          </div>
        )}

        {status === 'complete' && (
          <div className="space-y-4 py-4 text-center">
            <CheckCircle2 className="w-10 h-10 mx-auto text-green-500" />
            <p className="text-sm font-medium">Render complete!</p>
            <p className="text-xs text-muted-foreground">Your video is ready to download.</p>
          </div>
        )}

        {status === 'error' && (
          <div className="space-y-4 py-4 text-center">
            <AlertCircle className="w-10 h-10 mx-auto text-destructive" />
            <p className="text-sm font-medium">Render failed</p>
            <p className="text-xs text-muted-foreground">
              Check the server logs for details. Ensure FFmpeg is installed.
            </p>
          </div>
        )}

        <DialogFooter className="gap-2">
          {status === 'idle' && (
            <>
              <Button variant="outline" onClick={() => setOpen(false)}>Cancel</Button>
              <Button onClick={handleExport}>
                <Film className="h-3.5 w-3.5 mr-1.5" />
                Start Export
              </Button>
            </>
          )}
          {status === 'rendering' && (
            <Button variant="outline" disabled className="w-full">
              <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
              Rendering...
            </Button>
          )}
          {status === 'complete' && (
            <Button onClick={handleDownload} className="w-full">
              <Download className="h-3.5 w-3.5 mr-1.5" />
              Download {projectName}.{format}
            </Button>
          )}
          {status === 'error' && (
            <Button variant="outline" onClick={() => setStatus('idle')} className="w-full">
              Try Again
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
