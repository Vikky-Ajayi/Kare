import { useCallback, useEffect, useState } from 'react';

/** Chrome/Edge/Android fire this instead of showing their own install UI,
 * so the page can offer its own button and trigger the native prompt later. */
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

function isStandalone(): boolean {
  return (
    window.matchMedia?.('(display-mode: standalone)').matches ||
    // iOS Safari's own flag — no `display-mode` media query support there.
    (window.navigator as unknown as { standalone?: boolean }).standalone === true
  );
}

function isIOS(): boolean {
  return /iphone|ipad|ipod/i.test(window.navigator.userAgent);
}

/**
 * Drives an "Install app" button anywhere in the UI.
 *
 *   const { canInstall, isIOS, isInstalled, promptInstall } = usePWAInstall();
 *
 * Chrome/Edge/Android: `canInstall` flips true once the browser decides the
 * page is installable; `promptInstall()` shows the native install dialog.
 * iOS Safari has no programmatic install API at all, so `isIOS` is exposed
 * for the caller to show "Add to Home Screen" instructions instead.
 */
export function usePWAInstall() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [installed, setInstalled] = useState(isStandalone);

  useEffect(() => {
    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
    };
    const onInstalled = () => {
      setInstalled(true);
      setDeferred(null);
    };
    window.addEventListener('beforeinstallprompt', onPrompt);
    window.addEventListener('appinstalled', onInstalled);
    return () => {
      window.removeEventListener('beforeinstallprompt', onPrompt);
      window.removeEventListener('appinstalled', onInstalled);
    };
  }, []);

  const promptInstall = useCallback(async (): Promise<'accepted' | 'dismissed' | 'unavailable'> => {
    if (!deferred) return 'unavailable';
    await deferred.prompt();
    const { outcome } = await deferred.userChoice;
    setDeferred(null);
    return outcome;
  }, [deferred]);

  return {
    canInstall: !!deferred && !installed,
    isInstalled: installed,
    isIOS: isIOS() && !installed,
    promptInstall,
  };
}
