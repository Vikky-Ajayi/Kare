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

  const item = {
    initial: { y: 12, opacity: 0 },
    animate: { y: 0, opacity: 1 },
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
      className="space-y-8 p-6 md:p-8 pb-24">
      <motion.div {...item}>
        <div className="text-xs font-semibold text-primary-ink/70 mb-2">Dashboard</div>
        <h1 className="text-4xl md:text-5xl">Hello, {first}<span className="text-primary-ink">.</span></h1>
      </motion.div>

      {followups.length > 0 && (
        <motion.div {...item}>
          <Link to={`/dashboard/voice?c=${followups[0].conversation_id}&f=${followups[0].id}`}
            className="block card card-hover bg-primary border-none">
            <div className="flex items-center gap-3 mb-2 text-primary-ink"><Bell size={16} /><span className="text-xs font-semibold uppercase tracking-wide">Kare checked in on you</span></div>
            <p className="text-sm font-medium leading-relaxed text-primary-ink">{followups[0].message}</p>
            <div className="mt-3 flex items-center gap-2 text-xs font-semibold text-primary-ink">Reply <ArrowRight size={14} /></div>
          </Link>
        </motion.div>
      )}

      <motion.div {...item} className="grid md:grid-cols-2 gap-6">
        <Link to="/dashboard/voice" className="card card-hover group">
          <div className="w-14 h-14 rounded-2xl bg-mint flex items-center justify-center mb-6 group-hover:scale-105 transition-transform">
            <Mic size={26} className="text-ink" />
          </div>
          <h2 className="text-2xl mb-2">Voice Doctor</h2>
          <p className="text-sm text-ink/45">Speak how you feel · Kare remembers you</p>
        </Link>
        {user?.has_active_pregnancy ? (
          <Link to="/dashboard/pregnancy" className="card card-hover group">
            <div className="w-14 h-14 rounded-2xl bg-pink flex items-center justify-center mb-6 group-hover:scale-105 transition-transform">
              <Baby size={26} className="text-ink" />
            </div>
            <h2 className="text-2xl mb-2">{preg ? `Week ${Math.floor((preg.gestational_age_days ?? 0) / 7)}` : 'Pregnancy'}</h2>
            <p className="text-sm text-ink/45">
              {preg?.days_to_edd != null ? `${preg.days_to_edd} days to go` : 'Your pregnancy companion'}
            </p>
          </Link>
        ) : (
          <Link to="/dashboard/pregnancy" className="card card-hover group">
            <div className="w-14 h-14 rounded-2xl bg-lavender flex items-center justify-center mb-6 group-hover:scale-105 transition-transform">
              <Baby size={26} className="text-ink" />
            </div>
            <h2 className="text-2xl mb-2">Expecting?</h2>
            <p className="text-sm text-ink/45">Set up the pregnancy companion</p>
          </Link>
        )}
      </motion.div>

      <motion.div {...item} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Activity, label: 'Conditions', value: profile ? '—' : '', to: '/dashboard/history', bg: 'bg-mint' },
          { icon: Pill, label: 'Medications', value: '', to: '/dashboard/medications', bg: 'bg-sand' },
          { icon: Stethoscope, label: 'Symptom check', value: '', to: '/dashboard/symptoms', bg: 'bg-lavender' },
          { icon: Clock, label: 'Consultations', value: String(convos.length), to: '/dashboard/voice', bg: 'bg-peach' },
        ].map((s) => (
          <Link key={s.label} to={s.to} className="bg-surface rounded-2xl border border-ink/8 p-5 hover:border-primary transition-all group">
            <div className={`w-9 h-9 rounded-xl ${s.bg} flex items-center justify-center mb-4`}>
              <s.icon size={17} className="text-ink" />
            </div>
            {s.value && <div className="text-2xl font-display font-bold text-ink">{s.value}</div>}
            <div className="text-xs font-medium text-ink/45 mt-1">{s.label}</div>
          </Link>
        ))}
      </motion.div>

      {convos.length > 0 && (
        <motion.div {...item} className="card overflow-hidden !p-0">
          <div className="p-6 border-b border-ink/8 text-xs font-semibold text-ink/40 uppercase tracking-wide">Recent consultations</div>
          <div className="divide-y divide-ink/8">
            {convos.slice(0, 5).map((c) => (
              <Link key={c.id} to={`/dashboard/voice?c=${c.id}`} className="flex items-center justify-between p-5 hover:bg-ink/[0.03] transition-colors group">
                <div className="min-w-0">
                  <div className="text-sm text-ink/80 truncate">{c.preview || 'Consultation'}</div>
                  <div className="text-xs text-ink/35 mt-1">
                    {new Date(c.started_at).toLocaleDateString()} · {c.message_count} messages · {c.status}
                  </div>
                </div>
                <ArrowRight size={16} className="text-ink/25 group-hover:text-primary-ink group-hover:translate-x-1 transition-all flex-shrink-0" />
              </Link>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default Dashboard;
