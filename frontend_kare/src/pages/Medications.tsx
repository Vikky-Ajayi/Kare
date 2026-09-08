import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Pill, Plus, Trash2, X, Loader2, ShieldAlert } from 'lucide-react';
import { meds as medsApi } from '../services/api';
import type { Medication } from '../types';

const field = 'w-full bg-black border-2 border-white/10 px-4 py-2.5 text-sm text-white outline-none focus:border-primary';

const Medications = () => {
  const [items, setItems] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [check, setCheck] = useState<any>(null);
  const [checking, setChecking] = useState(false);
  const [form, setForm] = useState({ drug_name: '', dosage: '', frequency: '', notes: '' });

  const load = () => medsApi.list().then(setItems).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await medsApi.add(form);
      setForm({ drug_name: '', dosage: '', frequency: '', notes: '' });
      setModal(false);
      load();
    } finally { setSaving(false); }
  };

  const runCheck = async () => {
    setChecking(true);
    try { setCheck(await medsApi.myInteractions()); } finally { setChecking(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl mx-auto space-y-8 p-6 md:p-8 pb-24">
      <div className="flex justify-between items-end">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Medications</div>
          <h1 className="text-4xl font-display font-bold tracking-tighter uppercase">Medications<span className="text-primary">.</span></h1>
        </div>
        <button onClick={() => setModal(true)} className="btn-primary flex items-center gap-2"><Plus size={16} /> Add</button>
      </div>

      {items.length >= 2 && (
        <button onClick={runCheck} disabled={checking}
          className="w-full brutalist-card bg-surface border-2 border-white/10 p-5 flex items-center gap-4 hover:border-primary transition-all disabled:opacity-50">
          {checking ? <Loader2 size={18} className="animate-spin text-primary" /> : <ShieldAlert size={18} className="text-primary" />}
          <span className="text-[10px] font-bold uppercase tracking-widest text-white/60">Check my medications for interactions</span>
        </button>
      )}

      {check && (
        <div className="brutalist-card bg-surface border-2 border-white/10 p-6">
          <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-3">
            {check.interactions_found ? `${check.interactions_found} interaction(s) found` : 'No major interactions found'}
          </h3>
          {(check.interactions || []).map((i: any, idx: number) => (
            <div key={idx} className="text-xs text-white/60 mb-2">
              <span className="text-white">{i.drug_1} + {i.drug_2}</span> — {i.description} <span className="text-primary/60">({i.severity})</span>
            </div>
          ))}
          <p className="text-[9px] uppercase tracking-widest text-white/30 mt-3">{check.disclaimer}</p>
        </div>
      )}

      <div className="brutalist-card bg-surface border-2 border-white/10 divide-y-2 divide-white/10">
        {loading ? (
          <div className="p-16 text-center text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">Loading…</div>
        ) : items.length === 0 ? (
          <div className="p-16 text-center text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">No medications yet</div>
        ) : items.map((m) => (
          <div key={m.id} className="p-5 flex items-center justify-between group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-primary"><Pill size={20} /></div>
              <div>
                <div className="text-lg font-display font-bold uppercase tracking-tight">{m.drug_name}</div>
                <div className="text-[10px] font-bold uppercase tracking-widest text-white/30">{[m.dosage, m.frequency].filter(Boolean).join(' · ') || m.status}</div>
              </div>
            </div>
            <button onClick={async () => { await medsApi.remove(m.id); load(); }}
              className="w-10 h-10 border-2 border-white/10 flex items-center justify-center text-white/20 hover:text-red-500 hover:border-red-500 transition-all">
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>

      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm" onClick={() => setModal(false)}>
          <motion.form initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} onClick={(e) => e.stopPropagation()} onSubmit={add}
            className="w-full max-w-md bg-surface border-4 border-white/10 p-8 space-y-4">
            <div className="flex justify-between items-start mb-2">
              <h2 className="text-2xl font-display font-bold uppercase tracking-tighter">Add medication<span className="text-primary">.</span></h2>
              <button type="button" onClick={() => setModal(false)} className="text-white/20 hover:text-primary"><X size={22} /></button>
            </div>
            <input required placeholder="Drug name" value={form.drug_name} onChange={(e) => setForm({ ...form, drug_name: e.target.value })} className={field} style={{ textTransform: 'none' }} />
            <div className="grid grid-cols-2 gap-4">
              <input placeholder="Dosage e.g. 500mg" value={form.dosage} onChange={(e) => setForm({ ...form, dosage: e.target.value })} className={field} style={{ textTransform: 'none' }} />
              <input placeholder="Frequency" value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })} className={field} style={{ textTransform: 'none' }} />
            </div>
            <textarea rows={2} placeholder="Notes (optional)" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={`${field} resize-none`} style={{ textTransform: 'none' }} />
            <button type="submit" disabled={saving} className="btn-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-50">
              {saving ? <Loader2 size={16} className="animate-spin" /> : 'Save'}
            </button>
          </motion.form>
        </div>
      )}
    </motion.div>
  );
};

export default Medications;
