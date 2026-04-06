import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { 
  Activity, 
  Droplets, 
  Heart,
  Plus,
  Phone,
  Mic,
  ArrowRight,
  ChevronRight,
  Calendar
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import { cn } from '../lib/utils';
import { api } from '../services/api';

const Dashboard = () => {
  const { user, profile, setProfile } = useAuthStore(state => ({
    user: state.user,
    profile: state.profile,
    setProfile: state.setProfile
  }));
  const [consultations, setConsultations] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        const [profileRes, consultationsRes] = await Promise.all([
          api.get('/profile'),
          api.get('/consultations')
        ]);
        setProfile(profileRes.data);
        setConsultations(consultationsRes.data);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [setProfile]);

  const stats = [
    { label: 'Blood Sugar', value: '120', unit: 'mg/dL', trend: '+2.3%', icon: Droplets, color: 'text-primary' },
    { label: 'Heart Rate', value: '116/70', unit: 'BPM', trend: '-1.5%', icon: Heart, color: 'text-red-500' },
    { label: 'Blood Pressure', value: '175', unit: 'BPM', trend: '+0.8%', icon: Activity, color: 'text-primary' },
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
      className="space-y-12 p-8 pb-32"
    >
      <div className="flex justify-between items-end">
        <motion.div variants={itemVariants}>
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Patient Dashboard</div>
          <h1 className="text-6xl font-display font-bold tracking-tighter uppercase">
            Hello, {user?.name?.split(' ')[0] || 'Matias'}<span className="text-primary">.</span>
          </h1>
        </motion.div>
        <motion.div variants={itemVariants} className="flex gap-4">
          <Link to="/voice" className="btn-primary flex items-center gap-3 group">
            <Mic size={18} className="group-hover:scale-110 transition-transform" /> 
            <span className="tracking-widest">Voice Doctor</span>
          </Link>
          <button className="btn-outline flex items-center gap-3 group">
            <Calendar size={18} className="group-hover:text-primary transition-colors" />
            <span className="tracking-widest">Feb 01 - Feb 12</span>
          </button>
        </motion.div>
      </div>

      <div className="grid grid-cols-12 gap-8">
        {/* Main Content */}
        <div className="col-span-8 space-y-8">
          <motion.div 
            variants={itemVariants}
            className="brutalist-card p-12 bg-surface relative overflow-hidden group"
          >
            <div className="flex justify-between items-start mb-12">
              <h2 className="text-3xl font-display font-bold uppercase tracking-tight">Health Overview</h2>
              <button className="w-12 h-12 border border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all group/btn">
                <Plus size={24} className="group-hover/btn:rotate-90 transition-transform" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-12">
              <div className="space-y-8">
                <div className="flex items-center gap-6">
                  <motion.div 
                    whileHover={{ scale: 1.05 }}
                    className="w-20 h-20 bg-black border-2 border-white/10 overflow-hidden grayscale group-hover:grayscale-0 transition-all duration-500"
                  >
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Matias'}`} alt="Patient" />
                  </motion.div>
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-white/20 mb-1">Patient Name</div>
                    <div className="text-xl font-bold uppercase tracking-tight">{profile?.name || user?.name || 'Matias Corea'}</div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-primary mt-1">
                      {profile?.age || '36'} {profile?.gender || 'Male'} • {profile?.state || 'Lagos'}, {profile?.country || 'NG'}
                    </div>
                  </div>
                </div>

                <div className="p-8 border-2 border-white/10 bg-black/40 relative group/card overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                  <div className="text-[10px] font-bold uppercase tracking-widest text-white/20 mb-2">Current Condition</div>
                  <div className="text-lg font-bold uppercase tracking-tight group-hover/card:text-primary transition-colors">General Wellness</div>
                  <div className="text-[10px] font-bold uppercase tracking-widest text-white/40 mt-1">Last check: 2 days ago</div>
                </div>
              </div>

              <div className="relative h-full flex items-center justify-center bg-black/20 border-2 border-white/5 overflow-hidden">
                <motion.img 
                  whileHover={{ scale: 1.1 }}
                  src="https://images.unsplash.com/photo-1559757175-5700dde675bc?auto=format&fit=crop&q=80&w=800" 
                  alt="Medical Illustration" 
                  className="h-full object-contain grayscale opacity-20 group-hover:opacity-40 transition-all duration-700"
                  referrerPolicy="no-referrer"
                />
                <div className="absolute top-6 right-6 bg-primary text-black px-4 py-1 text-[10px] font-bold uppercase tracking-widest border-2 border-black">
                  Optimal Health
                </div>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-px bg-white/10 border-2 border-white/10 mt-12">
              {stats.map((stat, idx) => (
                <motion.div 
                  key={stat.label} 
                  whileHover={{ backgroundColor: 'rgba(0, 255, 209, 0.05)' }}
                  className="p-8 bg-black transition-all group/stat cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-6">
                    <div className={cn("w-12 h-12 border-2 border-white/10 flex items-center justify-center transition-all group-hover/stat:border-primary group-hover/stat:bg-primary/10", stat.color)}>
                      <stat.icon size={24} />
                    </div>
                    <span className="text-[10px] font-bold text-primary tracking-widest">{stat.trend}</span>
                  </div>
                  <div className="text-[10px] font-bold uppercase tracking-widest text-white/20 mb-2">{stat.label}</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-display font-bold">{stat.value}</span>
                    <span className="text-[8px] font-bold uppercase tracking-widest text-white/20">{stat.unit}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Sidebar Content */}
        <div className="col-span-4 space-y-8">
          <motion.div 
            variants={itemVariants}
            className="brutalist-card p-8 bg-surface"
          >
            <div className="flex justify-between items-center mb-8">
              <h2 className="text-xl font-display font-bold uppercase tracking-tight">Available Doctors</h2>
              <button className="text-[10px] font-bold uppercase tracking-widest text-primary hover:underline">See All</button>
            </div>
            
            <div className="space-y-4">
              {[
                { name: 'Dr. Amara Okafor', role: 'General Practitioner' },
                { name: 'Dr. Babatunde Lawal', role: 'Cardiologist' },
              ].map((doc) => (
                <motion.div 
                  key={doc.name} 
                  whileHover={{ x: 5 }}
                  className="flex items-center gap-4 p-4 border-2 border-white/5 hover:border-primary transition-all group cursor-pointer bg-black/20"
                >
                  <div className="w-12 h-12 bg-black border-2 border-white/10 overflow-hidden grayscale group-hover:grayscale-0 transition-all">
                    <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${doc.name}`} alt={doc.name} />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-bold uppercase tracking-tight group-hover:text-primary transition-colors">{doc.name}</div>
                    <div className="text-[10px] font-bold uppercase tracking-widest text-white/20">{doc.role}</div>
                  </div>
                  <div className="w-8 h-8 border border-white/10 flex items-center justify-center group-hover:border-primary group-hover:text-primary transition-all">
                    <ChevronRight size={14} />
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div 
            variants={itemVariants}
            whileHover={{ scale: 1.02 }}
            className="bg-primary p-10 text-black relative overflow-hidden group cursor-pointer border-4 border-black shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)]"
          >
            <div className="relative z-10">
              <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-black/40 mb-4">Emergency Service</div>
              <h2 className="text-5xl font-display font-bold mb-6 uppercase tracking-tighter leading-none">Immediate<br/>Assistance</h2>
              <p className="text-xs font-bold uppercase tracking-widest text-black/60 mb-10 max-w-[200px] leading-relaxed">Get help from our 24/7 medical team in Nigeria.</p>
              <button className="w-full py-5 bg-black text-primary font-bold uppercase tracking-[0.2em] flex items-center justify-center gap-4 hover:bg-white hover:text-black transition-all border-2 border-black">
                <Phone size={20} /> Call Now
              </button>
            </div>
            <div className="absolute -right-12 -bottom-12 w-48 h-48 bg-black/5 rounded-full blur-3xl group-hover:bg-black/10 transition-all"></div>
          </motion.div>
        </div>
      </div>
    </motion.div>
  );
};

export default Dashboard;
