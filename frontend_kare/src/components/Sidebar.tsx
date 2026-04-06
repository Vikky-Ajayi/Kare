import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'motion/react';
import { 
  LayoutDashboard, 
  Stethoscope, 
  History, 
  Pill, 
  User, 
  Settings, 
  LogOut,
  Activity
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuthStore } from '../store/useAuthStore';

import { api } from '../services/api';

const Sidebar = () => {
  const { logout, refreshToken } = useAuthStore(state => ({
    logout: state.logout,
    refreshToken: state.refreshToken
  }));

  const handleLogout = async () => {
    try {
      if (refreshToken) {
        await api.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      logout();
      window.location.href = '/';
    }
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Stethoscope, label: 'Symptom Check', path: '/symptoms' },
    { icon: History, label: 'History', path: '/history' },
    { icon: Pill, label: 'Meds', path: '/medications' },
    { icon: User, label: 'Profile', path: '/profile' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

  return (
    <aside className="w-64 h-screen bg-black border-r-2 border-white/10 flex flex-col fixed left-0 top-0 z-50">
      <div className="p-8 border-b-2 border-white/10 flex items-center gap-4">
        <motion.div 
          whileHover={{ scale: 1.1, rotate: 90 }}
          className="w-12 h-12 bg-primary flex items-center justify-center border-4 border-black shadow-[4px_4px_0px_0px_rgba(255,255,255,0.1)]"
        >
          <Activity size={28} className="text-black" />
        </motion.div>
        <span className="font-display text-3xl font-bold tracking-tighter uppercase">Kare<span className="text-primary">.</span></span>
      </div>

      <nav className="flex-1 py-12 flex flex-col gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              cn(
                "px-8 py-6 flex items-center justify-between transition-all border-l-4 relative group",
                isActive 
                  ? "bg-primary/10 border-primary text-primary" 
                  : "border-transparent text-white/20 hover:text-white hover:bg-white/5"
              )
            }
          >
            <div className="flex items-center gap-5">
              <item.icon size={24} className="group-hover:text-primary group-hover:scale-110 transition-all" />
              <span className="text-[10px] font-bold uppercase tracking-[0.3em]">{item.label}</span>
            </div>
            
            <motion.div
              initial={false}
              animate={{ 
                scale: 1,
                opacity: 1,
                x: 0
              }}
              className={cn(
                "w-2 h-2 bg-primary",
                "opacity-0 group-[.active]:opacity-100 transition-opacity"
              )}
            />
          </NavLink>
        ))}
      </nav>

      <div className="p-8 border-t-2 border-white/10">
        <motion.button 
          whileHover={{ x: 5 }}
          whileTap={{ scale: 0.95 }}
          onClick={handleLogout}
          className="w-full flex items-center gap-5 text-white/20 hover:text-red-500 transition-all group"
        >
          <div className="w-12 h-12 border-2 border-white/10 flex items-center justify-center group-hover:border-red-500/50 group-hover:bg-red-500/10 transition-all">
            <LogOut size={24} />
          </div>
          <span className="text-[10px] font-bold uppercase tracking-[0.3em]">Logout</span>
        </motion.button>
      </div>
    </aside>
  );
};

export default Sidebar;
