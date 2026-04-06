import React from 'react';
import { Search, Bell, Calendar } from 'lucide-react';
import { motion } from 'motion/react';
import { useAuthStore } from '../store/useAuthStore';

const TopBar = () => {
  const user = useAuthStore(state => state.user);

  return (
    <header className="h-20 bg-black border-b border-white/10 px-8 flex items-center justify-between sticky top-0 z-40 ml-64">
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex items-center gap-4 bg-surface px-6 py-2 border border-white/10 w-96 group focus-within:border-primary transition-all"
      >
        <Search size={18} className="text-white/40 group-focus-within:text-primary" />
        <input 
          type="text" 
          placeholder="Search health records, symptoms..." 
          className="bg-transparent border-none outline-none text-[10px] font-bold uppercase tracking-[0.2em] w-full text-white placeholder:text-white/20"
        />
      </motion.div>

      <div className="flex items-center gap-8">
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex items-center gap-3 text-white/40 border border-white/10 px-4 py-2"
        >
          <Calendar size={18} />
          <span className="text-[10px] font-bold uppercase tracking-[0.2em]">{new Date().toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short' })}</span>
        </motion.div>

        <motion.button 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          className="w-10 h-10 border border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all relative group"
        >
          <Bell size={20} />
          <span className="absolute top-0 right-0 w-2 h-2 bg-primary animate-pulse"></span>
        </motion.button>

        <motion.div 
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="flex items-center gap-4 pl-8 border-l border-white/10"
        >
          <div className="text-right">
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] text-white">{user?.name || 'Matias Corea'}</p>
            <p className="text-[8px] font-bold uppercase tracking-[0.3em] text-primary">Patient Status: Active</p>
          </div>
          <motion.div 
            whileHover={{ scale: 1.1 }}
            className="w-10 h-10 bg-surface border border-white/10 overflow-hidden group hover:border-primary transition-all cursor-pointer"
          >
            <img 
              src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Matias'}`} 
              alt="Avatar" 
              className="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all"
            />
          </motion.div>
        </motion.div>
      </div>
    </header>
  );
};

export default TopBar;
