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
    className={cn('w-14 h-8 rounded-full relative transition-all flex-shrink-0', on ? 'bg-primary' : 'bg-ink/15')}>
    {busy ? <Loader2 size={14} className="animate-spin absolute top-1.5 left-1.5 text-ink/60" />
      : <motion.div animate={{ x: on ? 26 : 4 }} className={cn('absolute top-1 w-6 h-6 rounded-full', on ? 'bg-primary-ink' : 'bg-white')} />}
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
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-2xl mx-auto space-y-8 p-6 md:p-8 pb-24">
      <div>
        <div className="text-xs font-semibold text-primary-ink/70 mb-2">Settings</div>
        <h1 className="text-4xl">Settings<span className="text-primary-ink">.</span></h1>
      </div>

      <section className="card !p-0 divide-y divide-ink/8">
        <div className="p-6 flex items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-mint flex items-center justify-center flex-shrink-0">
              <Bell size={18} className="text-ink" />
            </div>
            <div>
              <h3 className="text-sm font-display font-bold text-ink">Proactive check-ins</h3>
              <p className="text-sm text-ink/45 mt-1 leading-relaxed">
                Kare follows up after a consultation to see how you're doing. You can turn this off any time.
              </p>
            </div>
          </div>
          <Toggle on={checkins} onClick={toggleCheckins} busy={busy} />
        </div>

        <div className="p-6 flex items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-lavender flex items-center justify-center flex-shrink-0">
              <Globe size={18} className="text-ink" />
            </div>
            <div>
              <h3 className="text-sm font-display font-bold text-ink">Language</h3>
              <p className="text-sm text-ink/45 mt-1">Kare replies in this language</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {langSaved && <Check size={16} className="text-primary-ink" />}
            <select value={lang} onChange={(e) => saveLang(e.target.value as LangCode)}
              className="bg-background border-2 border-ink/10 rounded-xl px-3 py-2 text-sm font-medium text-ink outline-none focus:border-primary">
              {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
            </select>
          </div>
        </div>
      </section>

      {msg && <p className="text-primary-ink text-sm font-medium">{msg}</p>}

      <section className="card border-red-200 bg-red-50/60">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0">
            <Trash2 size={18} className="text-red-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-display font-bold text-red-700">Delete account</h3>
            <p className="text-sm text-red-700/60 mt-1 mb-4">Removes everything — profile, consultations, notes. Irreversible.</p>
            <button onClick={deleteAccount} className="text-sm font-semibold text-red-700 border-2 border-red-300 rounded-full px-5 py-2 hover:bg-red-600 hover:text-white hover:border-red-600 transition-all">
              Delete my account
            </button>
          </div>
        </div>
      </section>
    </motion.div>
  );
};

export default Settings;
