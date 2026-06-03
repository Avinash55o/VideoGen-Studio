import { AlertTriangle, ExternalLink } from 'lucide-react';
import { useCallback, useState } from 'react';
import { Trans, useTranslation } from 'react-i18next';
import { Button } from '@/components/ui/button';

export function useAccessibilityPermission() {
  const [checking] = useState(false);

  const recheck = useCallback(async (): Promise<boolean> => {
    return true;
  }, []);

  const openSettings = useCallback(async () => {
    console.warn('[accessibility] open settings not available outside Tauri');
  }, []);

  return { needsPermission: false, checking, recheck, openSettings };
}

/**
 * Inline notice rendered next to the auto-paste setting when macOS
 * Accessibility permission is missing. Returns null when the permission is
 * already granted.
 */
export function AccessibilityNotice() {
  const { t } = useTranslation();
  const { needsPermission, checking, recheck, openSettings } = useAccessibilityPermission();
  const [stillMissing, setStillMissing] = useState(false);

  const handleRecheck = useCallback(async () => {
    setStillMissing(false);
    const trusted = await recheck();
    if (!trusted) setStillMissing(true);
  }, [recheck]);

  if (!needsPermission) return null;

  return (
    <div className="mt-3 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3.5 py-3">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-500" />
        <div className="flex-1 min-w-0 space-y-1">
          <p className="text-sm font-medium text-foreground">
            {t('captures.permissions.accessibility.title')}
          </p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            <Trans i18nKey="captures.permissions.accessibility.body" components={{ path: <span /> }} />
          </p>
          <div className="flex items-center gap-2 pt-1.5">
            <Button size="sm" onClick={openSettings} className="gap-1.5">
              <ExternalLink className="h-3.5 w-3.5" />
              {t('captures.permissions.accessibility.openSettings')}
            </Button>
            <Button variant="outline" size="sm" onClick={handleRecheck} disabled={checking}>
              {checking ? t('captures.permissions.accessibility.rechecking') : t('captures.permissions.accessibility.recheck')}
            </Button>
          </div>
          {stillMissing && !checking && (
            <p className="text-xs text-amber-600 dark:text-amber-400 pt-1">
              {t('captures.permissions.accessibility.stillMissing')}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
