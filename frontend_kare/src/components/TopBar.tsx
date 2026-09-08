import React from 'react';
import { Calendar } from 'lucide-react';
import { motion } from 'motion/react';
import { useAuthStore } from '../store/useAuthStore';

const TopBar = () => {
  const user = useAuthStore((s) => s.user);
  const name = user?.name || user?.first_name || user?.email?.split('@')[0] || 'Patient';

  return (
    <header className="h-16 bg-black border-b border-white/10 pl-16 pr-4 lg:px-8 flex items-center justify-between sticky top-0 z-20">
      <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/30">Kare Health</div>
      <div className="flex items-center gap-6">
        <div className="hidden sm:flex items-center gap-2 text-white/40 border border-white/10 px-3 py-1.5">
          <Calendar size={14} />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em]">
            {new Date().toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' })}
          </span>
        </div>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white">{name}</p>
            <p className="text-[8px] font-bold uppercase tracking-[0.3em] text-primary">
              {user?.has_active_pregnancy ? 'Pregnancy mode' : 'Active'}
            </p>
          </div>
          <div className="w-9 h-9 bg-primary/10 border-2 border-primary flex items-center justify-center text-primary text-xs font-bold">
            {name.slice(0, 1).toUpperCase()}
          </div>
        </motion.div>
      </div>
    </header>
  );
};

export default TopBar;
