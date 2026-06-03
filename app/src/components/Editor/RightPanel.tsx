import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ClipInspector } from './ClipInspector';
import { VoiceoverPanel } from './VoiceoverPanel';
import { SubtitlePanel } from './SubtitlePanel';
import { VideoGenForm } from '@/components/Generation/VideoGenForm';
import { AudioLibraryPanel } from './AudioLibraryPanel';
import { useProjectStore } from '@/stores/projectStore';
import type { ClipResponse } from '@/lib/api/types';

interface RightPanelProps {
  projectId: string;
  onClipCreated: (clip: ClipResponse) => void;
}

export function RightPanel({ projectId, onClipCreated }: RightPanelProps) {
  const selectedClipId = useProjectStore((s) => s.selectedClipId);
  const [tab, setTab] = useState('generate');

  if (selectedClipId) {
    return (
      <div className="w-80 border-l border-border bg-background flex flex-col h-full">
        <ClipInspector />
      </div>
    );
  }

  return (
    <div className="w-80 border-l border-border bg-background flex flex-col h-full">
      <Tabs value={tab} onValueChange={setTab} className="flex flex-col h-full">
        <TabsList className="grid grid-cols-3 rounded-none border-b border-border px-1 py-0 h-10 bg-transparent">
          <TabsTrigger value="generate" className="text-xs data-[state=active]:bg-muted rounded-sm py-1.5">
            Generate
          </TabsTrigger>
          <TabsTrigger value="voiceover" className="text-xs data-[state=active]:bg-muted rounded-sm py-1.5">
            Voiceover
          </TabsTrigger>
          <TabsTrigger value="audio" className="text-xs data-[state=active]:bg-muted rounded-sm py-1.5">
            Audio
          </TabsTrigger>
        </TabsList>

        <TabsContent value="generate" className="flex-1 overflow-y-auto mt-0 data-[state=inactive]:hidden">
          <VideoGenForm projectId={projectId} />
        </TabsContent>

        <TabsContent value="voiceover" className="flex-1 overflow-y-auto mt-0 data-[state=inactive]:hidden">
          <VoiceoverPanel projectId={projectId} onClipCreated={onClipCreated} />
          <div className="border-t border-border mt-2">
            <div className="px-4 py-2 text-xs font-medium text-muted-foreground">
              Subtitles
            </div>
            <SubtitlePanel />
          </div>
        </TabsContent>

        <TabsContent value="audio" className="flex-1 overflow-y-auto mt-0 data-[state=inactive]:hidden p-0">
          <AudioLibraryPanel projectId={projectId} onClipCreated={onClipCreated} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
