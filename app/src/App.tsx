import { RouterProvider } from '@tanstack/react-router';
import { useEffect, useRef, useState } from 'react';
import videogenLogo from '@/assets/videogen-logo.png';
import ShinyText from '@/components/ShinyText';
import { useAutoUpdater } from '@/hooks/useAutoUpdater';
import { useThemeSync } from '@/hooks/useThemeSync';
import { apiClient } from '@/lib/api/client';
import type { HealthResponse } from '@/lib/api/types';
import { TOP_SAFE_AREA_PADDING } from '@/lib/constants/ui';
import { cn } from '@/lib/utils/cn';
import { usePlatform } from '@/platform/PlatformContext';
import { router } from '@/router';
import { useLogStore } from '@/stores/logStore';
import {
  getDefaultServerUrl,
  isLoopbackServerUrl,
  useServerStore,
} from '@/stores/serverStore';

/**
 * Validate that a health response has the expected VideoGen Studio shape.
 * Prevents misidentifying an unrelated service on the same port.
 */
function isVideoGenHealthResponse(health: HealthResponse): boolean {
  return (
    health?.status === 'healthy' &&
    health?.app_name === 'videogen-studio' &&
    typeof health.model_loaded === 'boolean' &&
    typeof health.gpu_available === 'boolean'
  );
}

/**
 * Check whether a startup error indicates the port is occupied by an external
 * server (which we should try to reuse via health-check polling) vs. a real
 * failure (missing sidecar, signing issue, etc.) that should surface immediately.
 */
function isPortInUseError(error: unknown): boolean {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    msg.includes('already in use') ||
    msg.includes('port') ||
    msg.includes('EADDRINUSE') ||
    msg.includes('address already in use')
  );
}

const LOADING_MESSAGES = [
  'Warming up tensors...',
  'Initializing video generation engine...',
  'Loading diffusion models...',
  'Preparing video pipelines...',
  'Optimizing CUDA kernels...',
  'Building VAE decoders...',
  'Configuring transformer blocks...',
  'Syncing model weights...',
  'Establishing model connections...',
  'Preprocessing training data...',
  'Validating video samples...',
  'Compiling inference engines...',
  'Aligning latent spaces...',
  'Activating video synthesis...',
  'Fine-tuning attention layers...',
  'Preparing rendering pipelines...',
  'Initializing CogVideoX framework...',
];

function App() {
  useThemeSync();

  return <MainApp />;
}

function MainApp() {
  const platform = usePlatform();
  const [serverReady, setServerReady] = useState(false);
  const [startupError, setStartupError] = useState<string | null>(null);
  const [loadingMessageIndex, setLoadingMessageIndex] = useState(0);
  const serverStartingRef = useRef(false);

  // Automatically check for app updates on startup and show toast notifications
  useAutoUpdater({ checkOnMount: true, showToast: true });

  // Sync stored setting to Rust on startup
  useEffect(() => {
    if (platform.metadata.isTauri) {
      const keepRunning = useServerStore.getState().keepServerRunningOnClose;
      platform.lifecycle.setKeepServerRunning(keepRunning).catch((error) => {
        console.error('Failed to sync initial setting to Rust:', error);
      });
    }
    // Empty dependency array - platform is stable from context, only run once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [platform.metadata.isTauri, platform.lifecycle]);

  // Setup lifecycle callbacks
  useEffect(() => {
    platform.lifecycle.onServerReady = () => {
      setServerReady(true);
    };
    // Empty dependency array - platform is stable from context, only run once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [platform.lifecycle]);

  // Subscribe to server logs
  useEffect(() => {
    const unsubscribe = platform.lifecycle.subscribeToServerLogs((entry) => {
      useLogStore.getState().addEntry(entry);
    });
    return unsubscribe;
  }, [platform.lifecycle]);

  // Setup window close handler and auto-start server when running in Tauri (production only)
  useEffect(() => {
    if (!platform.metadata.isTauri) {
      const serverUrl = getDefaultServerUrl();
      const currentServerUrl = useServerStore.getState().serverUrl;
      if (currentServerUrl !== serverUrl && isLoopbackServerUrl(currentServerUrl)) {
        useServerStore.getState().setServerUrl(serverUrl);
      }
      setServerReady(true); // Web assumes server is running
      return;
    }

    // Setup window close handler to check setting and stop server if needed
    // This works in both dev and prod, but will only stop server if it was started by the app
    platform.lifecycle.setupWindowCloseHandler().catch((error) => {
      console.error('Failed to setup window close handler:', error);
    });

    // Only auto-start server in production mode
    // In dev mode, user runs server separately
    if (!import.meta.env?.PROD) {
      console.log('Dev mode: Skipping auto-start of server (run it separately)');
      setServerReady(true); // Mark as ready so UI doesn't show loading screen
      // Mark that server was not started by app (so we don't try to stop it on close)
      window.__videogenServerStartedByApp = false;
      return;
    }

    // Auto-start server in production
    if (serverStartingRef.current) {
      return;
    }

    serverStartingRef.current = true;
    const isRemote = useServerStore.getState().mode === 'remote';
    const customModelsDir = useServerStore.getState().customModelsDir;
    console.log(`Production mode: Starting bundled server... (remote: ${isRemote})`);

    platform.lifecycle
      .startServer(isRemote, customModelsDir)
      .then((serverUrl) => {
        console.log('Server is ready at:', serverUrl);
        useServerStore.getState().setServerUrl(serverUrl);
        setServerReady(true);
        window.__videogenServerStartedByApp = true;
      })
      .catch((error) => {
        console.error('Failed to auto-start server:', error);
        serverStartingRef.current = false;
        window.__videogenServerStartedByApp = false;

        if (!isPortInUseError(error)) {
          const msg = error instanceof Error ? error.message : String(error);
          console.error('Real startup failure — not polling:', msg);
          setStartupError(msg);
          return;
        }

        // Fall back to polling: the server may already be running externally
        console.log('Falling back to health-check polling...');
        const pollInterval = setInterval(async () => {
          try {
            const health = await apiClient.getHealth();
            if (!isVideoGenHealthResponse(health)) {
              console.log('Health response is not from VideoGen Studio, keep polling...');
              return;
            }
            console.log('External VideoGen Studio server detected via health check');
            clearInterval(pollInterval);
            setServerReady(true);
          } catch {
            // Server not ready yet, keep polling
          }
        }, 2000);

        // Stop polling after 2 minutes and surface the failure
        setTimeout(() => {
          clearInterval(pollInterval);
          serverStartingRef.current = false;
          setStartupError(
            'Could not connect to a VideoGen Studio server within 2 minutes. ' +
              'Please check that the server is running and try again.',
          );
        }, 120_000);
      });

    // Cleanup: stop server on actual unmount (not StrictMode remount)
    // Note: Window close is handled separately in Tauri Rust code
    return () => {
      // Window close event handles server shutdown based on setting
      serverStartingRef.current = false;
    };
    // Empty dependency array - platform is stable from context, only run once
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [platform.metadata.isTauri, platform.lifecycle]);

  // Cycle through loading messages every 3 seconds
  useEffect(() => {
    if (!platform.metadata.isTauri || serverReady) {
      return;
    }

    const interval = setInterval(() => {
      setLoadingMessageIndex((prev) => (prev + 1) % LOADING_MESSAGES.length);
    }, 3000);

    return () => clearInterval(interval);
  }, [serverReady, platform.metadata.isTauri]);

  // Show loading screen while server is starting in Tauri
  if (platform.metadata.isTauri && !serverReady) {
    return (
      <div
        className={cn(
          'min-h-screen bg-background flex items-center justify-center',
          TOP_SAFE_AREA_PADDING,
        )}
      >
        <div className="text-center space-y-6">
          <div className="flex justify-center relative">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-48 h-48 rounded-full bg-accent/20 blur-3xl" />
            </div>
            <img
              src={videogenLogo}
              alt="VideoGen Studio"
              className="w-48 h-48 object-contain animate-fade-in-scale relative z-10"
            />
          </div>
          {startupError ? (
            <div className="animate-fade-in-delayed max-w-md mx-auto space-y-3">
              <p className="text-lg font-medium text-destructive">Server startup failed</p>
              <p className="text-sm text-muted-foreground">{startupError}</p>
              <button
                type="button"
                className="mt-2 px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                onClick={() => {
                  setStartupError(null);
                  serverStartingRef.current = false;
                  // Trigger a re-mount of the effect by toggling state
                  window.location.reload();
                }}
              >
                Retry
              </button>
            </div>
          ) : (
            <div className="animate-fade-in-delayed">
              <ShinyText
                text={LOADING_MESSAGES[loadingMessageIndex]}
                className="text-lg font-medium text-muted-foreground"
                speed={2}
                color="hsl(var(--muted-foreground))"
                shineColor="hsl(var(--foreground))"
              />
            </div>
          )}
        </div>
      </div>
    );
  }

  return <RouterProvider router={router} />;
}

export default App;
