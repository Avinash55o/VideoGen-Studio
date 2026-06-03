import type { ReactNode } from 'react';

interface EditorLayoutProps {
  topBar: ReactNode;
  preview: ReactNode;
  timeline: ReactNode;
  rightPanel: ReactNode;
}

export function EditorLayout({ topBar, preview, timeline, rightPanel }: EditorLayoutProps) {
  return (
    <div className="h-full flex flex-col">
      {topBar}

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 p-4 overflow-auto">
            {preview}
          </div>

          <div className="h-64 border-t border-border bg-muted/20">
            {timeline}
          </div>
        </div>

        {rightPanel}
      </div>
    </div>
  );
}
