import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Download, Share, SquarePlus } from 'lucide-react';
import { usePWAInstall } from '../hooks/usePWAInstall';

/** "Install app" affordance — renders nothing once installed, or on a
 * browser that never fires `beforeinstallprompt` and isn't iOS Safari
 * (there's nothing useful to offer there). `variant` picks a size that
 * fits the marketing navbar vs. the in-app top bar. */
const InstallButton = ({ variant = 'nav' }: { variant?: 'nav' | 'bar' }) => {
  const { canInstall, isIOS, promptInstall } = usePWAInstall();
  const [showIOSHelp, setShowIOSHelp] = useState(false);

  if (!canInstall && !isIOS) return null;

  const onClick = () => {
    if (isIOS) { setShowIOSHelp((v) => !v); return; }
    promptInstall();
  };

  const classes = variant === 'nav'
    ? 'btn-outline !py-3 !px-5 min-h-[44px]'
    : 'flex items-center gap-2 rounded-full bg-ink/5 hover:bg-ink/10 text-ink/70 hover:text-ink px-4 py-2.5 text-sm font-medium transition-all';

  return (
    <div className="relative">
      <button onClick={onClick} className={classes}>
        <Download size={variant === 'nav' ? 18 : 15} />
        Install app
      </button>

      <AnimatePresence>
        {showIOSHelp && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setShowIOSHelp(false)} />
            <motion.div
              initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
              className="absolute right-0 top-full mt-2 z-50 w-72 card !p-5 text-left"
            >
              <p className="text-sm font-display font-bold text-ink mb-3">Add Kare to your home screen</p>
              <ol className="space-y-2.5 text-sm text-ink/60">
                <li className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-full bg-mint flex items-center justify-center flex-shrink-0"><Share size={12} className="text-ink" /></span>
                  Tap the Share button in Safari
                </li>
                <li className="flex items-center gap-2.5">
                  <span className="w-6 h-6 rounded-full bg-mint flex items-center justify-center flex-shrink-0"><SquarePlus size={12} className="text-ink" /></span>
                  Choose "Add to Home Screen"
                </li>
              </ol>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default InstallButton;
