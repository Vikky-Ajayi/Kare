import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Edit2, 
  Camera,
  Shield,
  CreditCard,
  ArrowRight,
  CheckCircle2,
  Save,
  X
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { cn } from '../lib/utils';
import { api } from '../services/api';

const Profile = () => {
  const { user, profile, setProfile } = useAuthStore(state => ({
    user: state.user,
    profile: state.profile,
    setProfile: state.setProfile
  }));
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState<any>({});
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const response = await api.get('/profile');
        setProfile(response.data);
        setFormData(response.data);
      } catch (error) {
        console.error('Error fetching profile:', error);
      }
    };

    if (!profile) {
      fetchProfile();
    } else {
      setFormData(profile);
    }
  }, [profile, setProfile]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const response = await api.put('/profile', formData);
      setProfile(response.data);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const profileInfo = [
    { icon: Mail, label: 'Email Address', value: user?.email || 'matias@example.com' },
    { icon: Phone, label: 'Emergency Contact', value: profile?.emergency_contact || 'None' },
    { icon: MapPin, label: 'Location', value: `${profile?.state || 'Lagos'}, ${profile?.country || 'Nigeria'}` },
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
      <div className="flex justify-between items-end">
        <motion.div variants={itemVariants}>
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">User Account</div>
          <h1 className="text-5xl font-display font-bold tracking-tighter uppercase">My Profile<span className="text-primary">.</span></h1>
          <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-2">Manage your personal information and preferences.</p>
        </motion.div>
        <motion.button 
          variants={itemVariants}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => isEditing ? handleUpdateProfile({ preventDefault: () => {} } as any) : setIsEditing(true)}
          disabled={isLoading}
          className="px-10 py-5 bg-primary text-black font-bold uppercase tracking-[0.2em] flex items-center gap-4 hover:bg-white transition-all border-4 border-black shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] group disabled:opacity-50"
        >
          {isEditing ? (
            <>
              <Save size={24} className="group-hover:scale-110 transition-transform" /> 
              {isLoading ? 'Saving...' : 'Save Profile'}
            </>
          ) : (
            <>
              <Edit2 size={24} className="group-hover:rotate-12 transition-transform" /> Edit Profile
            </>
          )}
        </motion.button>
      </div>

      <div className="grid md:grid-cols-12 gap-8">
        <div className="md:col-span-4 space-y-8">
          <motion.div 
            variants={itemVariants}
            className="brutalist-card p-12 flex flex-col items-center text-center bg-surface border-2 border-white/10"
          >
            {isEditing && (
              <button 
                onClick={() => setIsEditing(false)}
                className="absolute top-4 right-4 text-white/20 hover:text-red-500 transition-colors"
              >
                <X size={24} />
              </button>
            )}
            <div className="relative mb-10">
              <motion.div 
                whileHover={{ scale: 1.05 }}
                className="w-48 h-48 border-4 border-white overflow-hidden bg-black shadow-[12px_12px_0px_0px_rgba(0,0,0,0.3)]"
              >
                <img 
                  src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.name || 'Matias'}`} 
                  alt="Profile" 
                  className="w-full h-full object-cover grayscale hover:grayscale-0 transition-all duration-500"
                />
              </motion.div>
              <motion.button 
                whileHover={{ scale: 1.1, rotate: 15 }}
                whileTap={{ scale: 0.9 }}
                className="absolute -bottom-6 -right-6 w-14 h-14 bg-primary text-black border-4 border-black flex items-center justify-center hover:bg-white transition-colors"
              >
                <Camera size={24} />
              </motion.button>
            </div>
            <h2 className="text-4xl font-display font-bold uppercase tracking-tighter mb-3">{user?.name || 'Matias'}</h2>
            <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.4em]">ID: #KARE-98234</p>
            <div className="mt-10 flex gap-4">
              <span className="px-6 py-2 border-2 border-primary text-primary text-[10px] font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                <CheckCircle2 size={12} /> Verified
              </span>
              <span className="px-6 py-2 bg-primary text-black text-[10px] font-bold uppercase tracking-[0.2em]">Premium</span>
            </div>
          </motion.div>

          <motion.div 
            variants={itemVariants}
            className="brutalist-card p-10 space-y-8 bg-surface border-2 border-white/10"
          >
            <h3 className="text-[10px] font-bold text-white/20 uppercase tracking-[0.4em]">Health Overview</h3>
            <div className="space-y-6">
              <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-[0.2em] group cursor-pointer">
                <span className="text-white/20 group-hover:text-white transition-colors">Blood Type</span>
                <span className="text-primary">O+ Positive</span>
              </div>
              <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-[0.2em] group cursor-pointer">
                <span className="text-white/20 group-hover:text-white transition-colors">Height</span>
                <span className="text-white">178 cm</span>
              </div>
              <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-[0.2em] group cursor-pointer">
                <span className="text-white/20 group-hover:text-white transition-colors">Weight</span>
                <span className="text-white">72 kg</span>
              </div>
            </div>
          </motion.div>
        </div>

        <div className="md:col-span-8 space-y-8">
          <motion.div 
            variants={itemVariants}
            className="brutalist-card p-12 bg-surface border-2 border-white/10"
          >
            <h3 className="text-2xl font-display font-bold uppercase tracking-tight mb-12">Personal Information</h3>
            <div className="grid gap-12">
              {profileInfo.map((info) => (
                <motion.div 
                  key={info.label} 
                  whileHover={{ x: 10 }}
                  className="flex items-center gap-10 group cursor-pointer"
                >
                  <div className="w-20 h-20 bg-black border-2 border-white/10 flex items-center justify-center text-white/10 group-hover:text-primary group-hover:border-primary group-hover:bg-primary/10 transition-all">
                    <info.icon size={32} />
                  </div>
                  <div>
                    <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.3em] mb-3">{info.label}</p>
                    <p className="text-xl font-bold uppercase tracking-[0.2em] text-white group-hover:text-primary transition-all">{info.value}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-8">
            <motion.div 
              variants={itemVariants}
              whileHover={{ y: -5 }}
              className="brutalist-card p-10 flex items-center gap-8 bg-surface border-2 border-white/10 hover:bg-black hover:border-primary transition-all cursor-pointer group"
            >
              <div className="w-20 h-20 bg-black border-2 border-white/10 flex items-center justify-center text-white/10 group-hover:text-primary group-hover:border-primary transition-all">
                <Shield size={36} />
              </div>
              <div>
                <h4 className="text-xl font-display font-bold uppercase tracking-tight group-hover:text-primary transition-all">Security</h4>
                <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.3em]">Password & 2FA</p>
              </div>
            </motion.div>
            <motion.div 
              variants={itemVariants}
              whileHover={{ y: -5 }}
              className="brutalist-card p-10 flex items-center gap-8 bg-surface border-2 border-white/10 hover:bg-black hover:border-primary transition-all cursor-pointer group"
            >
              <div className="w-20 h-20 bg-black border-2 border-white/10 flex items-center justify-center text-white/10 group-hover:text-primary group-hover:border-primary transition-all">
                <CreditCard size={36} />
              </div>
              <div>
                <h4 className="text-xl font-display font-bold uppercase tracking-tight group-hover:text-primary transition-all">Billing</h4>
                <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.3em]">Manage Subscription</p>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default Profile;
