import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { Mic, Baby, Pill, Stethoscope, ArrowRight, Bell, Activity, Clock } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { patient as patientApi, voice, pregnancy as pregApi, notifications } from '../services/api';
import type { Conversation, PatientProfile, Pregnancy } from '../types';

const Dashboard = () => {
  const user = useAuthStore((s) => s.user);
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [convos, setConvos] = useState<Conversation[]>([]);
  const [preg, setPreg] = useState<Pregnancy | null>(null);
  const [followups, setFollowups] = useState<any[]>([]);

  useEffect(() => {
    patientApi.get().then(setProfile).catch(() => {});
    voice.conversations().then(setConvos).catch(() => {});
    notifications.followups().then((r) => setFollowups(r.items.filter((f) => f.status === 'sent'))).catch(() => {});
    if (user?.has_active_pregnancy) pregApi.get().then(setPreg).catch(() => {});
  }, [user?.has_active_pregnancy]);

  const first = user?.first_name || profile?.first_name || 'there';

  const item = { hidden: { y: 16, opacity: 0 }, visible: { y: 0, opacity: 1 } };

  return (
    <motion.div initial="hidden" animate="visible" transition={{ staggerChildren: 0.06 }}
      className="space-y-8 p-6 md:p-8 pb-24">
      <motion.div variants={item}>
        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Dashboard</div>
        <h1 className="text-4xl md:text-5xl font-display font-bold tracking-tighter uppercase">Hello, {first}<span className="text-primary">.</span></h1>
      </motion.div>

      {followups.length > 0 && (
        <motion.div variants={item}>
          <Link to={`/dashboard/voice?c=${followups[0].conversation_id}&f=${followups[0].id}`}
            className="block brutalist-card bg-primary text-black border-4 border-black p-6 shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] hover:-translate-y-1 transition-transform">
            <div className="flex items-center gap-3 mb-2"><Bell size={16} /><span className="text-[10px] font-bold uppercase tracking-[0.3em]">Kare checked in on you</span></div>
            <p className="text-sm font-medium leading-relaxed">{followups[0].message}</p>
            <div className="mt-3 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest">Reply <ArrowRight size={14} /></div>
          </Link>
        </motion.div>
      )}

      <motion.div variants={item} className="grid md:grid-cols-2 gap-6">
        <Link to="/dashboard/voice" className="brutalist-card bg-surface border-2 border-white/10 p-8 group hover:border-primary transition-all">
          <Mic size={32} className="text-primary mb-6 group-hover:scale-110 transition-transform" />
          <h2 className="text-2xl font-display font-bold uppercase tracking-tight mb-2">Voice Doctor</h2>
          <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Speak how you feel · Kare remembers you</p>
        </Link>
        {user?.has_active_pregnancy ? (
          <Link to="/dashboard/pregnancy" className="brutalist-card bg-surface border-2 border-white/10 p-8 group hover:border-primary transition-all">
            <Baby size={32} className="text-primary mb-6 group-hover:scale-110 transition-transform" />
            <h2 className="text-2xl font-display font-bold uppercase tracking-tight mb-2">{preg ? `Week ${Math.floor((preg.gestational_age_days ?? 0) / 7)}` : 'Pregnancy'}</h2>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">
              {preg?.days_to_edd != null ? `${preg.days_to_edd} days to go` : 'Your pregnancy companion'}
            </p>
          </Link>
        ) : (
          <Link to="/dashboard/pregnancy" className="brutalist-card bg-surface border-2 border-white/10 p-8 group hover:border-primary transition-all">
            <Baby size={32} className="text-white/30 mb-6 group-hover:text-primary transition-colors" />
            <h2 className="text-2xl font-display font-bold uppercase tracking-tight mb-2">Expecting?</h2>
            <p className="text-[10px] font-bold uppercase tracking-widest text-white/30">Set up the pregnancy companion</p>
          </Link>
        )}
      </motion.div>

      <motion.div variants={item} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Activity, label: 'Conditions', value: profile ? '—' : '', to: '/dashboard/history' },
          { icon: Pill, label: 'Medications', value: '', to: '/dashboard/medications' },
          { icon: Stethoscope, label: 'Symptom check', value: '', to: '/dashboard/symptoms' },
          { icon: Clock, label: 'Consultations', value: String(convos.length), to: '/dashboard/voice' },
        ].map((s) => (
          <Link key={s.label} to={s.to} className="bg-surface border-2 border-white/10 p-5 hover:border-primary transition-all group">
            <s.icon size={20} className="text-primary mb-4" />
            {s.value && <div className="text-2xl font-display font-bold">{s.value}</div>}
            <div className="text-[9px] font-bold uppercase tracking-widest text-white/30 mt-1">{s.label}</div>
          </Link>
        ))}
      </motion.div>

      {convos.length > 0 && (
        <motion.div variants={item} className="brutalist-card bg-surface border-2 border-white/10 overflow-hidden">
          <div className="p-6 border-b-2 border-white/10 text-[10px] font-bold uppercase tracking-[0.3em] text-white/40">Recent consultations</div>
          <div className="divide-y-2 divide-white/10">
            {convos.slice(0, 5).map((c) => (
              <Link key={c.id} to={`/dashboard/voice?c=${c.id}`} className="flex items-center justify-between p-5 hover:bg-white/5 transition-colors group">
                <div className="min-w-0">
                  <div className="text-sm text-white/80 truncate">{c.preview || 'Consultation'}</div>
                  <div className="text-[9px] font-bold uppercase tracking-widest text-white/25 mt-1">
                    {new Date(c.started_at).toLocaleDateString()} · {c.message_count} messages · {c.status}
                  </div>
                </div>
                <ArrowRight size={16} className="text-white/20 group-hover:text-primary group-hover:translate-x-1 transition-all flex-shrink-0" />
              </Link>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default Dashboard;
