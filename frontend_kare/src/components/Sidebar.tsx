import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'motion/react';
import { LayoutDashboard, Mic, Stethoscope, History, Pill, Baby, User, Settings, LogOut, Activity } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuthStore } from '../store/useAuthStore';
import { auth } from '../services/api';

const Sidebar = () => {
  const logout = useAuthStore((s) => s.logout);
  const refreshToken = useAuthStore((s) => s.refreshToken);
  const user = useAuthStore((s) => s.user);

  const handleLogout = async () => {
    if (refreshToken) await auth.logout(refreshToken);
    logout();
    window.location.href = '/';
  };

  const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard', end: true },
    { icon: Mic, label: 'Voice Doctor', path: '/dashboard/voice' },
    ...(user?.has_active_pregnancy ? [{ icon: Baby, label: 'Pregnancy', path: '/dashboard/pregnancy' }] : []),
    { icon: Stethoscope, label: 'Symptom Check', path: '/dashboard/symptoms' },
    { icon: Pill, label: 'Medications', path: '/dashboard/medications' },
    { icon: History, label: 'History', path: '/dashboard/history' },
    { icon: User, label: 'Profile', path: '/dashboard/profile' },
    { icon: Settings, label: 'Settings', path: '/dashboard/settings' },
  ];

  return (
    <aside className="w-64 h-screen bg-black border-r-2 border-white/10 flex flex-col fixed left-0 top-0 z-50">
      <div className="p-7 border-b-2 border-white/10 flex items-center gap-4">
        <div className="w-11 h-11 bg-primary flex items-center justify-center border-4 border-black shadow-[4px_4px_0px_0px_rgba(255,255,255,0.1)]">
          <Activity size={24} className="text-black" />
        </div>
        <span className="font-display text-3xl font-bold tracking-tighter uppercase">Kare<span className="text-primary">.</span></span>
      </div>

      <nav className="flex-1 py-8 flex flex-col gap-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink key={item.path} to={item.path} end={(item as any).end}
            className={({ isActive }) => cn(
              'px-8 py-4 flex items-center gap-5 transition-all border-l-4 group',
              isActive ? 'bg-primary/10 border-primary text-primary' : 'border-transparent text-white/25 hover:text-white hover:bg-white/5',
            )}>
            <item.icon size={20} className="group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-bold uppercase tracking-[0.25em]">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-6 border-t-2 border-white/10">
        <motion.button whileHover={{ x: 4 }} whileTap={{ scale: 0.95 }} onClick={handleLogout}
          className="w-full flex items-center gap-4 text-white/20 hover:text-red-500 transition-all group">
          <div className="w-10 h-10 border-2 border-white/10 flex items-center justify-center group-hover:border-red-500/50 transition-all">
            <LogOut size={18} />
          </div>
          <span className="text-[10px] font-bold uppercase tracking-[0.25em]">Logout</span>
        </motion.button>
      </div>
    </aside>
  );
};

export default Sidebar;
