import { useState } from 'react';
import { Music, Volume2, Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useAudioLibrary } from '@/lib/hooks/useAudioLibrary';
import { useToast } from '@/components/ui/use-toast';
import { apiClient } from '@/lib/api/client';
import type { AudioLibraryEntryResponse, ClipCreate, ClipResponse } from '@/lib/api/types';

interface AudioLibraryPanelProps {
  projectId: string;
  onClipCreated: (clip: ClipResponse) => void;
}

export function AudioLibraryPanel({ projectId, onClipCreated }: AudioLibraryPanelProps) {
  const { toast } = useToast();
  const { data: entries } = useAudioLibrary();
  const [search, setSearch] = useState('');
  const [adding, setAdding] = useState<string | null>(null);

  const filtered = (entries ?? []).filter(
    (e) =>
      e.name.toLowerCase().includes(search.toLowerCase()) ||
      e.tags?.some((t) => t.toLowerCase().includes(search.toLowerCase())),
  );

  async function addToTimeline(entry: AudioLibraryEntryResponse) {
    setAdding(entry.id);
    try {
      const clipData: ClipCreate = {
        track: 2,
        start_time_ms: 0,
        end_time_ms: Math.round((entry.duration_seconds ?? 10) * 1000),
        clip_type: 'music',
        source_path: entry.file_path,
        volume: 0.7,
        speed: 1,
        fade_in_ms: 500,
        fade_out_ms: 500,
      };
      const clip = await apiClient.createClip(projectId, clipData);
      onClipCreated(clip);
      toast({ title: `Added "${entry.name}" to timeline` });
    } catch (err) {
      toast({ title: 'Failed to add audio', description: String(err), variant: 'destructive' });
    } finally {
      setAdding(null);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-border">
        <Input
          placeholder="Search audio library..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 text-sm"
        />
      </div>

      <div className="flex-1 overflow-y-auto">
        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center h-32 text-muted-foreground text-sm p-4">
            <Music className="w-8 h-8 mb-2 opacity-50" />
            {entries?.length === 0
              ? 'No audio files yet. Import music or SFX to get started.'
              : 'No matches'}
          </div>
        )}

        {filtered.map((entry) => (
          <div
            key={entry.id}
            className="flex items-center gap-3 px-3 py-2.5 border-b border-border/50 hover:bg-muted/30 transition-colors group"
          >
            <Volume2 className="w-4 h-4 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm truncate">{entry.name}</p>
              <div className="flex items-center gap-2 mt-0.5">
                <Badge variant="outline" className="text-[10px] px-1 py-0">
                  {entry.category}
                </Badge>
                {entry.duration_seconds && (
                  <span className="text-[10px] text-muted-foreground">
                    {Math.round(entry.duration_seconds)}s
                  </span>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={() => addToTimeline(entry)}
              disabled={adding === entry.id}
            >
              <Plus className="h-3.5 w-3.5" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
