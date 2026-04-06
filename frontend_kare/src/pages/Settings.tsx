import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  Settings as SettingsIcon, 
  Bell, 
  Lock, 
  Globe, 
  Moon, 
  Smartphone,
  ChevronRight,
  ShieldCheck,
  Eye,
  ArrowRight
} from 'lucide-react';
import { cn } from '../lib/utils';

const Settings = () => {
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(true);

  const sections = [
    {
      title: 'General',
      items: [
        { icon: Bell, label: 'Notifications', desc: 'Manage your health alerts and reminders', toggle: true, value: notifications, setter: setNotifications },
        { icon: Globe, label: 'Language', desc: 'English (US)', action: true },
        { icon: Moon, label: 'Dark Mode', desc: 'Switch between light and dark themes', toggle: true, value: darkMode, setter: setDarkMode },
      ]
    },
    {
      title: 'Security',
      items: [
        { icon: Lock, label: 'Password', desc: 'Update your account password', action: true },
        { icon: ShieldCheck, label: 'Two-Factor Auth', desc: 'Add an extra layer of security', action: true },
        { icon: Eye, label: 'Privacy Settings', desc: 'Control who sees your health data', action: true },
      ]
    },
    {
      title: 'App',
      items: [
        { icon: Smartphone, label: 'Mobile App', desc: 'Download Kare for iOS and Android', action: true },
      ]
    }
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-4xl mx-auto space-y-12 p-8 pb-32"
    >
      <motion.div variants={itemVariants}>
        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">System Configuration</div>
        <h1 className="text-5xl font-display font-bold tracking-tighter uppercase">Settings<span className="text-primary">.</span></h1>
        <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-2">Customize your experience and manage your account.</p>
      </motion.div>

      <div className="space-y-16">
        {sections.map((section) => (
          <motion.div key={section.title} variants={itemVariants} className="space-y-8">
            <h2 className="text-[10px] font-bold text-white/20 uppercase tracking-[0.4em] px-4">{section.title}</h2>
            <div className="brutalist-card overflow-hidden bg-surface border-2 border-white/10 divide-y-2 divide-white/10">
              {section.items.map((item) => (
                <motion.div 
                  key={item.label} 
                  whileHover={{ x: 5 }}
                  className="p-10 flex items-center justify-between hover:bg-black transition-all group cursor-pointer"
                >
                  <div className="flex items-center gap-10">
                    <div className="w-16 h-16 bg-black border-2 border-white/10 flex items-center justify-center text-white/10 group-hover:text-primary group-hover:border-primary group-hover:bg-primary/10 transition-all">
                      <item.icon size={28} className="group-hover:scale-110 transition-transform" />
                    </div>
                    <div>
                      <h3 className="text-xl font-display font-bold uppercase tracking-tight group-hover:text-primary transition-all">{item.label}</h3>
                      <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.3em] mt-2">{item.desc}</p>
                    </div>
                  </div>
                  
                  {item.toggle ? (
                    <motion.button 
                      whileTap={{ scale: 0.9 }}
                      onClick={(e) => {
                        e.stopPropagation();
                        item.setter?.(!item.value);
                      }}
                      className={cn(
                        "w-20 h-10 border-4 transition-all duration-300 relative",
                        item.value ? "bg-primary border-black" : "bg-black border-white/10"
                      )}
                    >
                      <motion.div 
                        animate={{ x: item.value ? 40 : 4 }}
                        className={cn(
                          "absolute top-1 w-6 h-6 transition-colors",
                          item.value ? "bg-black" : "bg-white/20"
                        )}
                      />
                    </motion.button>
                  ) : (
                    <div className="w-14 h-14 border-2 border-white/10 flex items-center justify-center text-white/10 group-hover:text-primary group-hover:border-primary transition-all">
                      <ArrowRight size={28} className="group-hover:translate-x-1 transition-transform" />
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

export default Settings;
