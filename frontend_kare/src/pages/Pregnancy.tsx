import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import { Baby, Heart, ArrowRight, Loader2, AlertTriangle, Mic } from 'lucide-react';
import { pregnancy as api, errMsg } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import type { Pregnancy as Preg } from '../types';

const Field = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div className="space-y-2">
    <label className="text-xs font-semibold text-ink/50">{label}</label>
    {children}
  </div>
);

const inputCls = 'w-full input-field text-sm';

function Onboard({ onDone }: { onDone: (p: Preg) => void }) {
  const [mode, setMode] = useState<'weeks' | 'lmp' | 'edd'>('weeks');
  const [weeks, setWeeks] = useState('');
  const [days, setDays] = useState('');
  const [lmp, setLmp] = useState('');
  const [edd, setEdd] = useState('');
  const [babySex, setBabySex] = useState('unknown');
  const [gravida, setGravida] = useState('');
  const [para, setPara] = useState('');
  const [history, setHistory] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const body: Record<string, unknown> = { baby_sex: babySex };
    if (mode === 'weeks' && weeks) { body.weeks = +weeks; if (days) body.days = +days; }
    if (mode === 'lmp' && lmp) body.lmp_date = lmp;
    if (mode === 'edd' && edd) body.edd = edd;
    if (gravida) body.gravida = +gravida;
    if (para) body.para = +para;
    if (history) body.history_notes = history;
    try {
      onDone(await api.start(body));
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.form initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} onSubmit={submit}
      className="max-w-lg mx-auto card space-y-6">
      <div>
        <div className="text-xs font-semibold text-primary-ink/70 mb-1">Pregnancy Companion</div>
        <h2 className="text-3xl">Let's set up<span className="text-primary-ink">.</span></h2>
        <p className="text-ink/45 text-sm mt-3 leading-relaxed">
          Kare will track your weeks, check in on you, and know the signs that need a midwife or doctor.
        </p>
      </div>

      <div className="flex gap-2 bg-background rounded-2xl p-1.5">
        {(['weeks', 'lmp', 'edd'] as const).map((m) => (
          <button key={m} type="button" onClick={() => setMode(m)}
            className={`flex-1 py-2 rounded-xl text-xs font-semibold transition-all ${
              mode === m ? 'bg-primary text-primary-ink' : 'text-ink/40 hover:text-ink'}`}>
            {m === 'weeks' ? 'I know my weeks' : m === 'lmp' ? 'Last period' : 'Due date'}
          </button>
        ))}
      </div>

      {mode === 'weeks' && (
        <div className="grid grid-cols-2 gap-4">
          <Field label="Weeks pregnant"><input type="number" min={0} max={44} value={weeks} onChange={(e) => setWeeks(e.target.value)} className={inputCls} required /></Field>
          <Field label="+ Days (optional)"><input type="number" min={0} max={6} value={days} onChange={(e) => setDays(e.target.value)} className={inputCls} /></Field>
        </div>
      )}
      {mode === 'lmp' && <Field label="First day of last period"><input type="date" value={lmp} onChange={(e) => setLmp(e.target.value)} className={inputCls} required /></Field>}
      {mode === 'edd' && <Field label="Expected due date"><input type="date" value={edd} onChange={(e) => setEdd(e.target.value)} className={inputCls} required /></Field>}

      <Field label="Baby's sex (optional)">
        <select value={babySex} onChange={(e) => setBabySex(e.target.value)} className={inputCls}>
          <option value="unknown">Don't know yet</option>
          <option value="female">Girl</option>
          <option value="male">Boy</option>
          <option value="undisclosed">Prefer not to say</option>
        </select>
      </Field>
      <div className="grid grid-cols-2 gap-4">
        <Field label="Pregnancies incl. this"><input type="number" min={1} value={gravida} onChange={(e) => setGravida(e.target.value)} className={inputCls} /></Field>
        <Field label="Previous births"><input type="number" min={0} value={para} onChange={(e) => setPara(e.target.value)} className={inputCls} /></Field>
      </div>
      <Field label="Anything relevant about this or past pregnancies">
        <textarea rows={3} value={history} onChange={(e) => setHistory(e.target.value)} className={`${inputCls} resize-none`} />
      </Field>

      {error && <p className="text-red-600 text-sm font-medium">{error}</p>}
      <button type="submit" disabled={loading} className="btn-primary w-full py-4 disabled:opacity-50">
        {loading ? <Loader2 className="animate-spin" size={18} /> : <>Start <ArrowRight size={18} /></>}
      </button>
    </motion.form>
  );
}

const RED_FLAGS = [
  'Vaginal bleeding', 'Waters breaking or fluid leaking', 'Severe headache with blurred vision or swelling',
  'Severe belly pain', 'Fever', 'Baby moving less than usual (from 28 weeks)',
];

function Home({ p, reload }: { p: Preg; reload: () => void }) {
  const navigate = useNavigate();
  const weeks = Math.floor((p.gestational_age_days ?? 0) / 7);
  const pct = Math.min(100, ((p.gestational_age_days ?? 0) / 280) * 100);
  const babyWord = p.baby_sex === 'female' ? 'her' : p.baby_sex === 'male' ? 'him' : 'them';

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 pb-24">
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <div className="text-xs font-semibold text-primary-ink/70 mb-1">Pregnancy Companion</div>
          <h1 className="text-5xl">Week {weeks}<span className="text-primary-ink">.</span></h1>
        </div>
        <button onClick={() => navigate('/dashboard/voice')} className="btn-primary">
          <Mic size={18} /> Talk to Kare
        </button>
      </div>

      <div className="card">
        <div className="flex items-center gap-5 mb-6">
          <div className="w-16 h-16 rounded-2xl bg-pink flex items-center justify-center text-ink"><Baby size={30} /></div>
          <div>
            <div className="text-2xl font-display font-bold text-ink">{p.gestational_age}</div>
            <div className="text-sm text-ink/45">
              Trimester {p.trimester} · {p.baby_sex === 'female' ? 'a girl' : p.baby_sex === 'male' ? 'a boy' : 'baby on the way'}
            </div>
          </div>
        </div>
        <div className="h-2.5 bg-background rounded-full mb-2 overflow-hidden">
          <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${pct}%` }} />
        </div>
        <div className="flex justify-between text-xs font-medium text-ink/35">
          <span>Week 0</span>
          <span className="text-primary-ink font-semibold">{p.days_to_edd != null ? `${p.days_to_edd} days to go` : ''}</span>
          <span>Due {p.estimated_due_date}</span>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center gap-3 mb-3"><Heart size={16} className="text-primary-ink" />
            <h3 className="text-xs font-semibold text-ink/45 uppercase tracking-wide">This week</h3></div>
          <p className="text-sm text-ink/70 leading-relaxed">{p.this_week || `Take care of yourself and ${babyWord}.`}</p>
        </div>
        <div className="card border-red-200 bg-red-50/60">
          <div className="flex items-center gap-3 mb-3"><AlertTriangle size={16} className="text-red-600" />
            <h3 className="text-xs font-semibold text-red-700 uppercase tracking-wide">Go in straight away if</h3></div>
          <ul className="space-y-1.5">
            {RED_FLAGS.map((f) => <li key={f} className="text-sm text-red-700/70 flex gap-2"><span className="text-red-600">›</span> {f}</li>)}
          </ul>
        </div>
      </div>

      {p.history_notes && (
        <div className="card">
          <h3 className="text-xs font-semibold text-ink/45 uppercase tracking-wide mb-2">Your notes</h3>
          <p className="text-sm text-ink/60 whitespace-pre-line">{p.history_notes}</p>
        </div>
      )}

      <button onClick={async () => { if (confirm('Close the pregnancy companion?')) { await api.end('completed'); reload(); } }}
        className="text-sm font-medium text-ink/30 hover:text-ink/60 transition-colors">
        Close companion
      </button>
    </motion.div>
  );
}

const Pregnancy = () => {
  const [p, setP] = useState<Preg | null>(null);
  const [loading, setLoading] = useState(true);
  const setUser = useAuthStore((s) => s.setUser);
  const user = useAuthStore((s) => s.user);

  const load = async () => {
    setLoading(true);
    try { setP(await api.get()); } catch { setP(null); }
    setLoading(false);
  };
  useEffect(() => { load(); }, []);

  const onDone = (preg: Preg) => {
    setP(preg);
    if (user) setUser({ ...user, has_active_pregnancy: true });
  };
  const reload = () => {
    setP(null);
    if (user) setUser({ ...user, has_active_pregnancy: false });
  };

  if (loading) return <div className="p-8 text-center text-ink/30 text-sm font-medium">Loading…</div>;
  return <div className="p-6 md:p-8">{p ? <Home p={p} reload={reload} /> : <Onboard onDone={onDone} />}</div>;
};

export default Pregnancy;
