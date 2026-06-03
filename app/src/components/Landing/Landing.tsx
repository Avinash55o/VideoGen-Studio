import { Link } from '@tanstack/react-router';
import { Clapperboard, Box, Mic, Settings } from 'lucide-react';
import videogenLogo from '@/assets/videogen-logo.png';

export function Landing() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full gap-8 px-4">
      <div className="flex flex-col items-center gap-4">
        <img src={videogenLogo} alt="VideoGen Studio" className="w-auto h-60 object-contain" />
        <h1 className="text-3xl font-bold tracking-tight">VideoGen Studio</h1>
        <p className="text-muted-foreground text-center max-w-md">
          Local-first AI video generation. Create, edit, and export videos with AI-powered tools — all running on your machine.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 w-full max-w-lg">
        <Link
          to="/projects"
          className="flex flex-col items-center gap-2 p-6 rounded-xl border border-border bg-card hover:bg-accent/10 hover:border-accent/30 transition-all"
        >
          <Clapperboard className="h-8 w-8" />
          <span className="font-medium text-sm">Projects</span>
          <span className="text-xs text-muted-foreground text-center">Create and edit video projects</span>
        </Link>
        <Link
          to="/voice"
          className="flex flex-col items-center gap-2 p-6 rounded-xl border border-border bg-card hover:bg-accent/10 hover:border-accent/30 transition-all"
        >
          <Mic className="h-8 w-8" />
          <span className="font-medium text-sm">Voice</span>
          <span className="text-xs text-muted-foreground text-center">Generate speech and clone voices</span>
        </Link>
        <Link
          to="/models"
          className="flex flex-col items-center gap-2 p-6 rounded-xl border border-border bg-card hover:bg-accent/10 hover:border-accent/30 transition-all"
        >
          <Box className="h-8 w-8" />
          <span className="font-medium text-sm">Models</span>
          <span className="text-xs text-muted-foreground text-center">Download and manage AI models</span>
        </Link>
        <Link
          to="/settings"
          className="flex flex-col items-center gap-2 p-6 rounded-xl border border-border bg-card hover:bg-accent/10 hover:border-accent/30 transition-all"
        >
          <Settings className="h-8 w-8" />
          <span className="font-medium text-sm">Settings</span>
          <span className="text-xs text-muted-foreground text-center">Configure your studio</span>
        </Link>
      </div>
    </div>
  );
}
