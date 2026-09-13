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
    <aside className="w-64 h-screen bg-surface border-r border-ink/8 flex flex-col fixed left-0 top-0 z-50">
      <div className="p-7 flex items-center gap-3.5">
        <div className="w-11 h-11 bg-ink rounded-2xl flex items-center justify-center">
          <Activity size={22} className="text-primary" />
        </div>
        <span className="font-display text-2xl font-bold text-ink">Kare<span className="text-primary-ink">.</span></span>
      </div>

      <nav className="flex-1 py-6 px-3 flex flex-col gap-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink key={item.path} to={item.path} end={(item as any).end}
            className={({ isActive }) => cn(
              'px-5 py-3.5 flex items-center gap-4 rounded-2xl transition-all group',
              isActive ? 'bg-primary text-primary-ink font-semibold' : 'text-ink/45 hover:text-ink hover:bg-ink/5',
            )}>
            <item.icon size={19} className="group-hover:scale-110 transition-transform flex-shrink-0" />
            <span className="text-sm font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4">
        <motion.button whileHover={{ x: 4 }} whileTap={{ scale: 0.95 }} onClick={handleLogout}
          className="w-full flex items-center gap-4 px-5 py-3.5 rounded-2xl text-ink/35 hover:text-ink hover:bg-ink/5 transition-all group">
          <LogOut size={19} />
          <span className="text-sm font-medium">Logout</span>
        </motion.button>
      </div>
    </aside>
  );
};

export default Sidebar;
