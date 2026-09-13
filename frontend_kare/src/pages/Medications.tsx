import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Pill, Plus, Trash2, X, Loader2, ShieldAlert } from 'lucide-react';
import { meds as medsApi } from '../services/api';
import type { Medication } from '../types';

const field = 'w-full input-field text-sm';

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
          <div className="text-xs font-semibold text-primary-ink/70 mb-2">Medications</div>
          <h1 className="text-4xl">Medications<span className="text-primary-ink">.</span></h1>
        </div>
        <button onClick={() => setModal(true)} className="btn-primary !py-3 !px-5"><Plus size={16} /> Add</button>
      </div>

      {items.length >= 2 && (
        <button onClick={runCheck} disabled={checking}
          className="w-full card card-hover flex items-center gap-4 disabled:opacity-50">
          {checking ? <Loader2 size={18} className="animate-spin text-primary-ink" /> : <ShieldAlert size={18} className="text-primary-ink" />}
          <span className="text-sm font-medium text-ink/70">Check my medications for interactions</span>
        </button>
      )}

      {check && (
        <div className="card">
          <h3 className="text-sm font-display font-bold text-primary-ink mb-3">
            {check.interactions_found ? `${check.interactions_found} interaction(s) found` : 'No major interactions found'}
          </h3>
          {(check.interactions || []).map((i: any, idx: number) => (
            <div key={idx} className="text-sm text-ink/60 mb-2">
              <span className="text-ink font-medium">{i.drug_1} + {i.drug_2}</span> — {i.description} <span className="text-primary-ink/70">({i.severity})</span>
            </div>
          ))}
          <p className="text-xs text-ink/35 mt-3">{check.disclaimer}</p>
        </div>
      )}

      <div className="card !p-0 divide-y divide-ink/8">
        {loading ? (
          <div className="p-16 text-center text-ink/30 text-sm font-medium">Loading…</div>
        ) : items.length === 0 ? (
          <div className="p-16 text-center text-ink/30 text-sm font-medium">No medications yet</div>
        ) : items.map((m) => (
          <div key={m.id} className="p-5 flex items-center justify-between group">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-sand flex items-center justify-center text-ink"><Pill size={20} /></div>
              <div>
                <div className="text-lg font-display font-bold text-ink">{m.drug_name}</div>
                <div className="text-sm text-ink/40">{[m.dosage, m.frequency].filter(Boolean).join(' · ') || m.status}</div>
              </div>
            </div>
            <button onClick={async () => { await medsApi.remove(m.id); load(); }}
              className="w-10 h-10 rounded-full flex items-center justify-center text-ink/25 hover:text-red-600 hover:bg-red-50 transition-all">
              <Trash2 size={16} />
            </button>
          </div>
        ))}
      </div>

      {modal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-ink/50 backdrop-blur-sm" onClick={() => setModal(false)}>
          <motion.form initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} onClick={(e) => e.stopPropagation()} onSubmit={add}
            className="w-full max-w-md card space-y-4">
            <div className="flex justify-between items-start mb-2">
              <h2 className="text-2xl">Add medication<span className="text-primary-ink">.</span></h2>
              <button type="button" onClick={() => setModal(false)} className="text-ink/30 hover:text-primary-ink"><X size={22} /></button>
            </div>
            <input required placeholder="Drug name" value={form.drug_name} onChange={(e) => setForm({ ...form, drug_name: e.target.value })} className={field} />
            <div className="grid grid-cols-2 gap-4">
              <input placeholder="Dosage e.g. 500mg" value={form.dosage} onChange={(e) => setForm({ ...form, dosage: e.target.value })} className={field} />
              <input placeholder="Frequency" value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })} className={field} />
            </div>
            <textarea rows={2} placeholder="Notes (optional)" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={`${field} resize-none`} />
            <button type="submit" disabled={saving} className="btn-primary w-full py-3.5 disabled:opacity-50">
              {saving ? <Loader2 size={16} className="animate-spin" /> : 'Save'}
            </button>
          </motion.form>
        </div>
      )}
    </motion.div>
  );
};

export default Medications;
