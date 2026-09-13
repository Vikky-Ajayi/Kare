import React from 'react';
import { Calendar } from 'lucide-react';
import { motion } from 'motion/react';
import { useAuthStore } from '../store/useAuthStore';

const TopBar = () => {
  const user = useAuthStore((s) => s.user);
  const name = user?.name || user?.first_name || user?.email?.split('@')[0] || 'Patient';

  return (
    <header className="h-16 bg-background/90 backdrop-blur-sm border-b border-ink/8 pl-16 pr-4 lg:px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="text-xs font-semibold text-ink/40">Kare Health</div>
      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-2 text-ink/50 bg-ink/5 rounded-full px-4 py-2">
          <Calendar size={14} />
          <span className="text-xs font-medium">
            {new Date().toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' })}
          </span>
        </div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-xs font-semibold text-ink">{name}</p>
            <p className="text-[11px] font-medium text-primary-ink/70">
              {user?.has_active_pregnancy ? 'Pregnancy mode' : 'Active'}
            </p>
          </div>
          <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center text-primary-ink text-xs font-bold">
            {name.slice(0, 1).toUpperCase()}
          </div>
        </motion.div>
      </div>
    </header>
  );
};

export default TopBar;
