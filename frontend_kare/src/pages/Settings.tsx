import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Bell, Globe, Trash2, Loader2, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { LANGUAGES, type LangCode } from '../types';
import { patient as patientApi, notifications } from '../services/api';
import { enableCheckIns, disableCheckIns, pushSupported } from '../services/notifications';
import { useAuthStore } from '../store/useAuthStore';

const Toggle = ({ on, onClick, busy }: { on: boolean; onClick: () => void; busy?: boolean }) => (
  <button onClick={onClick} disabled={busy}
    className={cn('w-16 h-8 border-4 relative transition-all', on ? 'bg-primary border-black' : 'bg-black border-white/10')}>
    {busy ? <Loader2 size={12} className="animate-spin absolute top-1.5 left-1.5 text-black" />
      : <motion.div animate={{ x: on ? 30 : 2 }} className={cn('absolute top-1 w-5 h-5', on ? 'bg-black' : 'bg-white/20')} />}
  </button>
);

const Settings = () => {
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const navigate = useNavigate();
  const [checkins, setCheckins] = useState(!!user?.followups_enabled);
  const [busy, setBusy] = useState(false);
  const [lang, setLang] = useState<LangCode>((user?.preferred_language as LangCode) || 'en');
  const [langSaved, setLangSaved] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    notifications.followups().then((r) => setCheckins(r.enabled)).catch(() => {});
  }, []);

  const toggleCheckins = async () => {
    setBusy(true);
    setMsg(null);
    try {
      if (!checkins) {
        if (!pushSupported()) { setMsg('This browser cannot receive notifications.'); return; }
        const res = await enableCheckIns();
        if (res === 'denied') { setMsg('Notifications were blocked. Enable them in your browser settings.'); return; }
        if (res === 'unsupported') { setMsg('This browser cannot receive notifications.'); return; }
        setCheckins(true);
        if (user) setUser({ ...user, followups_enabled: true });
        setMsg('Kare can now check in on you between visits.');
      } else {
        await disableCheckIns();
        setCheckins(false);
        if (user) setUser({ ...user, followups_enabled: false });
      }
    } finally {
      setBusy(false);
    }
  };

  const saveLang = async (l: LangCode) => {
    setLang(l);
    await patientApi.setLanguage(l).catch(() => {});
    if (user) setUser({ ...user, preferred_language: l });
    setLangSaved(true);
    setTimeout(() => setLangSaved(false), 1500);
  };

  const deleteAccount = async () => {
    if (!confirm('Permanently delete your account and all your data? This cannot be undone.')) return;
    await patientApi.deleteAccount().catch(() => {});
    useAuthStore.getState().logout();
    navigate('/');
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-2xl mx-auto space-y-10 p-6 md:p-8 pb-24">
      <div>
        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Settings</div>
        <h1 className="text-4xl font-display font-bold tracking-tighter uppercase">Settings<span className="text-primary">.</span></h1>
      </div>

      <section className="brutalist-card bg-surface border-2 border-white/10 divide-y-2 divide-white/10">
        <div className="p-6 flex items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <Bell size={22} className="text-primary mt-1 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-bold uppercase tracking-tight">Proactive check-ins</h3>
              <p className="text-[10px] text-white/40 uppercase tracking-widest mt-1 leading-relaxed">
                Kare follows up after a consultation to see how you're doing. You can turn this off any time.
              </p>
            </div>
          </div>
          <Toggle on={checkins} onClick={toggleCheckins} busy={busy} />
        </div>

        <div className="p-6 flex items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <Globe size={22} className="text-primary mt-1 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-bold uppercase tracking-tight">Language</h3>
              <p className="text-[10px] text-white/40 uppercase tracking-widest mt-1">Kare replies in this language</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {langSaved && <Check size={16} className="text-primary" />}
            <select value={lang} onChange={(e) => saveLang(e.target.value as LangCode)}
              className="bg-black border-2 border-white/10 px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-white outline-none focus:border-primary">
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>
        </div>
      </section>

      {msg && <p className="text-primary text-[10px] font-bold uppercase tracking-widest">{msg}</p>}

      <section className="brutalist-card bg-surface border-2 border-red-500/30 p-6">
        <div className="flex items-start gap-4">
          <Trash2 size={22} className="text-red-500 mt-1 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="text-sm font-bold uppercase tracking-tight text-red-500">Delete account</h3>
            <p className="text-[10px] text-white/40 uppercase tracking-widest mt-1 mb-4">Removes everything — profile, consultations, notes. Irreversible.</p>
            <button onClick={deleteAccount} className="text-[10px] font-bold uppercase tracking-widest text-red-500 border-2 border-red-500/40 px-4 py-2 hover:bg-red-500 hover:text-black transition-all">
              Delete my account
            </button>
          </div>
        </div>
      </section>
    </motion.div>
  );
};

export default Settings;
