import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  redirect,
} from '@tanstack/react-router';
import { AppFrame } from '@/components/AppFrame/AppFrame';

import { MainEditor } from '@/components/MainEditor/MainEditor';
import { ModelsTab } from '@/components/ModelsTab/ModelsTab';
import { AboutPage } from '@/components/ServerTab/AboutPage';

import { GeneralPage } from '@/components/ServerTab/GeneralPage';
import { GenerationPage } from '@/components/ServerTab/GenerationPage';
import { MCPPage } from '@/components/ServerTab/MCPPage';
import { SettingsLayout } from '@/components/ServerTab/ServerTab';
import { Sidebar } from '@/components/Sidebar';
import { Toaster } from '@/components/ui/toaster';
import { VoicesTab } from '@/components/VoicesTab/VoicesTab';
import { useGenerationProgress } from '@/lib/hooks/useGenerationProgress';
import { useModelDownloadToast } from '@/lib/hooks/useModelDownloadToast';
import { MODEL_DISPLAY_NAMES, useRestoreActiveTasks } from '@/lib/hooks/useRestoreActiveTasks';
import { Landing } from '@/components/Landing/Landing';
import { ProjectDashboard } from '@/components/Dashboard/ProjectDashboard';
import { ProjectEditor } from '@/components/Editor/ProjectEditor';

// Simple platform check that works in both web and Tauri
const isMacOS = () => navigator.platform.toLowerCase().includes('mac');

// Root layout component
function RootLayout() {
  // Monitor active downloads/generations and show toasts for them
  const activeDownloads = useRestoreActiveTasks();

  // Subscribe to SSE for pending generations — handles completion, auto-play, and history refresh
  useGenerationProgress();

  return (
    <AppFrame>
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <Sidebar isMacOS={isMacOS()} />

        <main className="flex-1 ml-20 overflow-hidden flex flex-col">
          <div className="container mx-auto px-8 max-w-[1800px] h-full overflow-hidden flex flex-col">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Show download toasts for any active downloads (from anywhere) */}
      {activeDownloads.map((download) => {
        const displayName = MODEL_DISPLAY_NAMES[download.model_name] || download.model_name;
        return (
          <DownloadToastRestorer
            key={download.model_name}
            modelName={download.model_name}
            displayName={displayName}
          />
        );
      })}

      <Toaster />
    </AppFrame>
  );
}

/**
 * Component that restores a download toast for a specific model.
 */
function DownloadToastRestorer({
  modelName,
  displayName,
}: {
  modelName: string;
  displayName: string;
}) {
  // Use the download toast hook to restore the toast
  useModelDownloadToast({
    modelName,
    displayName,
    enabled: true,
  });

  return null;
}

// Root route with layout
const rootRoute = createRootRoute({
  component: RootLayout,
});

// Index route — landing page
const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: Landing,
});

// Projects dashboard
const projectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects',
  component: ProjectDashboard,
});

// Legacy voice generation (moved from / to /voice)
const voiceRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/voice',
  component: MainEditor,
});

// Voices route
const voicesRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/voices',
  component: VoicesTab,
});

// (captures and effects routes removed — not in Phase 4 plan)

// Models route
const modelsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/models',
  component: ModelsTab,
});

// Settings layout route (parent for sub-tabs)
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsLayout,
});

// Settings sub-routes
const settingsGeneralRoute = createRoute({
  getParentRoute: () => settingsRoute,
  path: '/',
  component: GeneralPage,
});

const settingsGenerationRoute = createRoute({
  getParentRoute: () => settingsRoute,
  path: '/generation',
  component: GenerationPage,
});

// (settings/captures removed — captures feature disabled)

const settingsMCPRoute = createRoute({
  getParentRoute: () => settingsRoute,
  path: '/mcp',
  component: MCPPage,
});

const settingsAboutRoute = createRoute({
  getParentRoute: () => settingsRoute,
  path: '/about',
  component: AboutPage,
});

// Redirect old /server path to /settings
const serverRedirectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/server',
  beforeLoad: () => {
    throw redirect({ to: '/settings' });
  },
});

// (empty — dashboard moved to /)

// Project editor route
const editorRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/projects/$projectId',
  component: ProjectEditor,
});

// Route tree
const routeTree = rootRoute.addChildren([
  indexRoute,
  projectsRoute,
  voiceRoute,
  editorRoute,
  voicesRoute,
  modelsRoute,
  settingsRoute.addChildren([
    settingsGeneralRoute,
    settingsGenerationRoute,
    settingsMCPRoute,
    settingsAboutRoute,
  ]),
  serverRedirectRoute,
]);

// Create router
export const router = createRouter({ routeTree });

// Register router for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}
