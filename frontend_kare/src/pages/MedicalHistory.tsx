import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { FileText, Plus, Trash2, X, Loader2, Calendar } from 'lucide-react';
import { history as historyApi } from '../services/api';
import type { MedicalCondition } from '../types';

const field = 'w-full bg-black border-2 border-white/10 px-4 py-2.5 text-sm text-white outline-none focus:border-primary';

const MedicalHistory = () => {
  const [items, setItems] = useState<MedicalCondition[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({ condition_name: '', status: 'active', diagnosed_date: '', notes: '', icd10_code: '' });

  const load = () => historyApi.list().then(setItems).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await historyApi.add({
        condition_name: form.condition_name, status: form.status,
        diagnosed_date: form.diagnosed_date || undefined, notes: form.notes || undefined,
        icd10_code: form.icd10_code || undefined,
      });
      setForm({ condition_name: '', status: 'active', diagnosed_date: '', notes: '', icd10_code: '' });
      setModal(false);
      load();
    } finally { setSaving(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl mx-auto space-y-8 p-6 md:p-8 pb-24">
      <div className="flex justify-between items-end">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Records</div>
          <h1 className="text-4xl font-display font-bold tracking-tighter uppercase">Medical History<span className="text-primary">.</span></h1>
        </div>
        <button onClick={() => setModal(true)} className="btn-primary flex items-center gap-2"><Plus size={16} /> Add</button>
      </div>

      <div className="space-y-4">
        {loading ? (
          <div className="p-16 text-center text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">Loading…</div>
        ) : items.length === 0 ? (
          <div className="p-16 text-center border-2 border-dashed border-white/10 text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">No conditions recorded</div>
        ) : items.map((c) => (
          <div key={c.id} className="brutalist-card bg-surface border-2 border-white/10 p-6 flex items-center justify-between group">
            <div className="flex items-center gap-5">
              <div className="w-14 h-14 border-2 border-white/10 flex items-center justify-center text-primary"><FileText size={22} /></div>
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <span className="text-[9px] font-bold uppercase tracking-[0.3em] text-primary">{c.status}</span>
                  {c.icd10_code && <span className="text-[9px] font-bold uppercase tracking-widest text-white/20">ICD-10 {c.icd10_code}</span>}
                </div>
                <h3 className="text-xl font-display font-bold uppercase tracking-tight">{c.condition_name}</h3>
                {c.diagnosed_date && (
                  <div className="text-[10px] text-white/30 font-bold uppercase tracking-widest mt-1 flex items-center gap-2">
                    <Calendar size={12} className="text-primary" /> {new Date(c.diagnosed_date).toLocaleDateString()}
                  </div>
                )}
                {c.notes && <p className="text-xs text-white/50 mt-2 max-w-md">{c.notes}</p>}
              </div>
            </div>
            <button onClick={async () => { await historyApi.remove(c.id); load(); }}
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
              <h2 className="text-2xl font-display font-bold uppercase tracking-tighter">Add condition<span className="text-primary">.</span></h2>
              <button type="button" onClick={() => setModal(false)} className="text-white/20 hover:text-primary"><X size={22} /></button>
            </div>
            <input required placeholder="Condition name" value={form.condition_name} onChange={(e) => setForm({ ...form, condition_name: e.target.value })} className={field} style={{ textTransform: 'none' }} />
            <div className="grid grid-cols-2 gap-4">
              <input type="date" value={form.diagnosed_date} onChange={(e) => setForm({ ...form, diagnosed_date: e.target.value })} className={field} />
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={field}>
                <option value="active">Active</option><option value="chronic">Chronic</option><option value="resolved">Resolved</option>
              </select>
            </div>
            <input placeholder="ICD-10 code (optional)" value={form.icd10_code} onChange={(e) => setForm({ ...form, icd10_code: e.target.value })} className={field} style={{ textTransform: 'none' }} />
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

export default MedicalHistory;
