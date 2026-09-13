import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { RefreshCw } from 'lucide-react';
import { SW_UPDATE_EVENT } from '../services/notifications';

/** Mounted once, globally. Silent until the service worker reports a new
 * version has taken over — see registerServiceWorker(). */
const UpdateToast = () => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const onReady = () => setReady(true);
    window.addEventListener(SW_UPDATE_EVENT, onReady);
    return () => window.removeEventListener(SW_UPDATE_EVENT, onReady);
  }, []);

  return (
    <AnimatePresence>
      {ready && (
        <motion.div
          initial={{ y: 60, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 60, opacity: 0 }}
          className="fixed bottom-5 left-1/2 -translate-x-1/2 z-[100] bg-ink text-white rounded-full pl-5 pr-2 py-2 flex items-center gap-3 shadow-xl"
        >
          <span className="text-sm font-medium whitespace-nowrap">A new version of Kare is ready</span>
          <button onClick={() => window.location.reload()}
            className="flex items-center gap-1.5 bg-primary text-primary-ink text-sm font-semibold rounded-full px-4 py-1.5 hover:bg-white transition-colors flex-shrink-0">
            <RefreshCw size={14} /> Refresh
          </button>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default UpdateToast;
