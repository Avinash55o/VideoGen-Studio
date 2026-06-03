import { FolderOpen, Mic, Video, Zap } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Toggle } from '@/components/ui/toggle';
import { useGenerationSettings } from '@/lib/hooks/useSettings';
import { usePlatform } from '@/platform/PlatformContext';
import { useServerStore } from '@/stores/serverStore';
import { SettingRow, SettingSection } from './SettingRow';

const RESOLUTIONS = [
  { value: '720p', label: '720p (1280×720)' },
  { value: '1080p', label: '1080p (1920×1080)' },
  { value: '1440p', label: '1440p (2560×1440)' },
  { value: '2160p', label: '4K (3840×2160)' },
];

const CODECS = [
  { value: 'h264', label: 'H.264' },
  { value: 'h265', label: 'H.265 / HEVC' },
  { value: 'vp9', label: 'VP9' },
];

export function GenerationPage() {
  const { t } = useTranslation();
  const platform = usePlatform();
  const serverUrl = useServerStore((state) => state.serverUrl);
  const { settings, update } = useGenerationSettings();
  const persistedMaxChunkChars = settings?.max_chunk_chars ?? 800;
  const persistedCrossfadeMs = settings?.crossfade_ms ?? 50;
  const persistNormalizeAudio = settings?.normalize_audio ?? true;
  const autoplayOnGenerate = settings?.autoplay_on_generate ?? true;
  const persistedOutputResolution = settings?.output_resolution ?? '1080p';
  const persistedOutputFps = settings?.output_fps ?? 30;
  const persistedVideoCodec = settings?.video_codec ?? 'h264';
  const persistedMaxDuration = settings?.max_render_duration_secs ?? 600;

  const [maxChunkChars, setMaxChunkChars] = useState(persistedMaxChunkChars);
  const [crossfadeMs, setCrossfadeMs] = useState(persistedCrossfadeMs);
  const [outputFps, setOutputFps] = useState(persistedOutputFps);
  const [maxDuration, setMaxDuration] = useState(persistedMaxDuration);
  useEffect(() => setMaxChunkChars(persistedMaxChunkChars), [persistedMaxChunkChars]);
  useEffect(() => setCrossfadeMs(persistedCrossfadeMs), [persistedCrossfadeMs]);
  useEffect(() => setOutputFps(persistedOutputFps), [persistedOutputFps]);
  useEffect(() => setMaxDuration(persistedMaxDuration), [persistedMaxDuration]);

  const [opening, setOpening] = useState(false);
  const [outputPath, setOutputPath] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${serverUrl}/health/filesystem`)
      .then((res) => res.json())
      .then((data) => {
        const genDir = data.directories?.find((d: { path: string }) =>
          d.path.includes('generations'),
        );
        if (genDir?.path) setOutputPath(genDir.path);
      })
      .catch(() => {});
  }, [serverUrl]);

  const openOutputFolder = useCallback(async () => {
    if (!outputPath) return;
    setOpening(true);
    try {
      await platform.filesystem.openPath(outputPath);
    } catch (e) {
      console.error('Failed to open output folder:', e);
    } finally {
      setOpening(false);
    }
  }, [platform, outputPath]);

  return (
    <div className="flex gap-8 items-start max-w-5xl">
      <div className="flex-1 min-w-0 max-w-2xl space-y-8">
        <SettingSection title={t('settings.generation.title')} description={t('settings.generation.description')}>
          <div className="mb-6">
            <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
              <Mic className="h-4 w-4 text-accent" />
              {t('settings.generation.voice.heading')}
            </h4>
            <div className="space-y-4">
              <SettingRow
                title={t('settings.generation.voice.chunkLimit.title')}
                description={t('settings.generation.voice.chunkLimit.description')}
                action={
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {t('settings.generation.voice.chunkLimit.value', { chars: maxChunkChars })}
                  </span>
                }
              >
                <Slider
                  id="maxChunkChars"
                  value={[maxChunkChars]}
                  onValueChange={([value]) => setMaxChunkChars(value)}
                  onValueCommit={([value]) => update({ max_chunk_chars: value })}
                  min={100}
                  max={5000}
                  step={50}
                  aria-label={t('settings.generation.voice.chunkLimit.title')}
                />
              </SettingRow>

              <SettingRow
                title={t('settings.generation.voice.crossfade.title')}
                description={t('settings.generation.voice.crossfade.description')}
                action={
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {crossfadeMs === 0
                      ? t('settings.generation.voice.crossfade.cut')
                      : t('settings.generation.voice.crossfade.ms', { ms: crossfadeMs })}
                  </span>
                }
              >
                <Slider
                  id="crossfadeMs"
                  value={[crossfadeMs]}
                  onValueChange={([value]) => setCrossfadeMs(value)}
                  onValueCommit={([value]) => update({ crossfade_ms: value })}
                  min={0}
                  max={200}
                  step={10}
                  aria-label={t('settings.generation.voice.crossfade.title')}
                />
              </SettingRow>

              <SettingRow
                title={t('settings.generation.voice.normalize.title')}
                description={t('settings.generation.voice.normalize.description')}
                htmlFor="normalizeAudio"
                action={
                  <Toggle
                    id="normalizeAudio"
                    checked={persistNormalizeAudio}
                    onCheckedChange={(v) => update({ normalize_audio: v })}
                  />
                }
              />
            </div>
          </div>

          <div className="mb-6">
            <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
              <Video className="h-4 w-4 text-accent" />
              {t('settings.generation.video.heading')}
            </h4>
            <div className="space-y-4">
              <SettingRow
                title={t('settings.generation.video.resolution.title')}
                description={t('settings.generation.video.resolution.description')}
                action={
                  <Select
                    value={persistedOutputResolution}
                    onValueChange={(v) => update({ output_resolution: v })}
                  >
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {RESOLUTIONS.map((r) => (
                        <SelectItem key={r.value} value={r.value}>{r.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                }
              />

              <SettingRow
                title={t('settings.generation.video.fps.title')}
                description={t('settings.generation.video.fps.description')}
                action={
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {t('settings.generation.video.fps.value', { fps: outputFps })}
                  </span>
                }
              >
                <Slider
                  id="outputFps"
                  value={[outputFps]}
                  onValueChange={([value]) => setOutputFps(value)}
                  onValueCommit={([value]) => update({ output_fps: value })}
                  min={12}
                  max={120}
                  step={6}
                  aria-label={t('settings.generation.video.fps.title')}
                />
              </SettingRow>

              <SettingRow
                title={t('settings.generation.video.codec.title')}
                description={t('settings.generation.video.codec.description')}
                action={
                  <Select
                    value={persistedVideoCodec}
                    onValueChange={(v) => update({ video_codec: v })}
                  >
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {CODECS.map((c) => (
                        <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                }
              />

              <SettingRow
                title={t('settings.generation.video.maxDuration.title')}
                description={t('settings.generation.video.maxDuration.description')}
                action={
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {t('settings.generation.video.maxDuration.value', { secs: maxDuration })}
                  </span>
                }
              >
                <Slider
                  id="maxDuration"
                  value={[maxDuration]}
                  onValueChange={([value]) => setMaxDuration(value)}
                  onValueCommit={([value]) => update({ max_render_duration_secs: value })}
                  min={30}
                  max={3600}
                  step={30}
                  aria-label={t('settings.generation.video.maxDuration.title')}
                />
              </SettingRow>
            </div>
          </div>

          <SettingRow
            title={t('settings.generation.autoplay.title')}
            description={t('settings.generation.autoplay.description')}
            htmlFor="autoplayOnGenerate"
            action={
              <Toggle
                id="autoplayOnGenerate"
                checked={autoplayOnGenerate}
                onCheckedChange={(v) => update({ autoplay_on_generate: v })}
              />
            }
          />

          <SettingRow
            title={t('settings.generation.folder.title')}
            description={outputPath ?? t('settings.generation.folder.description')}
            action={
              <Button
                variant="outline"
                size="sm"
                onClick={openOutputFolder}
                disabled={opening || !outputPath}
              >
                <FolderOpen className="h-3.5 w-3.5 mr-1.5" />
                {t('settings.generation.folder.open')}
              </Button>
            }
          />
        </SettingSection>
      </div>

      <aside className="hidden lg:block w-[280px] shrink-0 space-y-6 sticky top-0">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold">{t('settings.generation.sidebar.aboutTitle')}</h3>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {t('settings.generation.sidebar.aboutBody')}
          </p>
        </div>
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Sections</h3>
          <ul className="space-y-3 text-sm text-muted-foreground">
            <li className="flex gap-2.5">
              <Mic className="h-4 w-4 shrink-0 mt-0.5 text-accent" />
              <span className="leading-relaxed">
                <span className="text-foreground font-medium">
                  {t('settings.generation.sidebar.voice.title')}
                </span>{' '}
                {t('settings.generation.sidebar.voice.body')}
              </span>
            </li>
            <li className="flex gap-2.5">
              <Video className="h-4 w-4 shrink-0 mt-0.5 text-accent" />
              <span className="leading-relaxed">
                <span className="text-foreground font-medium">
                  {t('settings.generation.sidebar.video.title')}
                </span>{' '}
                {t('settings.generation.sidebar.video.body')}
              </span>
            </li>
            <li className="flex gap-2.5">
              <Zap className="h-4 w-4 shrink-0 mt-0.5 text-accent" />
              <span className="leading-relaxed">
                <span className="text-foreground font-medium">{t('settings.generation.sidebar.agentReady.title')}</span>{' '}
                {t('settings.generation.sidebar.agentReady.body')}
              </span>
            </li>
          </ul>
        </div>
      </aside>
    </div>
  );
}
