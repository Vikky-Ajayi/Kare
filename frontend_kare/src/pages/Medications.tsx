import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Pill, Plus, Trash2, X, Loader2, ShieldAlert, Camera, Sparkles, CircleAlert } from 'lucide-react';
import { meds as medsApi, images as imagesApi, type MedicationImageResult } from '../services/api';
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

  const [scanPreview, setScanPreview] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<MedicationImageResult | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement | null>(null);

  const load = () => medsApi.list().then(setItems).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); }, []);

  const closeModal = () => {
    setModal(false);
    setForm({ drug_name: '', dosage: '', frequency: '', notes: '' });
    setScanPreview(null); setScanResult(null); setScanError(null);
  };

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await medsApi.add(form);
      closeModal();
      load();
    } finally { setSaving(false); }
  };

  const runCheck = async () => {
    setChecking(true);
    try { setCheck(await medsApi.myInteractions()); } finally { setChecking(false); }
  };

  const scanPhoto = async (file: File) => {
    setScanPreview(URL.createObjectURL(file));
    setScanning(true);
    setScanError(null);
    setScanResult(null);
    try {
      const result = await imagesApi.analyzeMedication(file);
      setScanResult(result);
      const f = result.structured_findings;
      // Fill in what the photo told us, but never overwrite something the
      // patient already typed themselves — and never auto-submit either way.
      setForm((prev) => ({
        ...prev,
        drug_name: prev.drug_name || f.drug_name || prev.drug_name,
        dosage: prev.dosage || f.strength || prev.dosage,
      }));
    } catch {
      setScanError("Couldn't read that photo — you can still fill this in by hand.");
    } finally {
      setScanning(false);
    }
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

      <AnimatePresence>
        {modal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-ink/50 backdrop-blur-sm" onClick={closeModal}>
            <motion.form initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()} onSubmit={add}
              className="w-full max-w-md card space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-2">
                <h2 className="text-2xl">Add medication<span className="text-primary-ink">.</span></h2>
                <button type="button" onClick={closeModal} className="text-ink/30 hover:text-primary-ink"><X size={22} /></button>
              </div>

              <input ref={fileInput} type="file" accept="image/*" capture="environment" className="hidden"
                onChange={(e) => { const f = e.target.files?.[0]; if (f) scanPhoto(f); e.target.value = ''; }} />

              <button type="button" onClick={() => fileInput.current?.click()} disabled={scanning}
                className="w-full rounded-2xl border-2 border-dashed border-ink/15 hover:border-primary transition-colors p-4 flex items-center gap-4 text-left disabled:opacity-60">
                {scanPreview ? (
                  <img src={scanPreview} alt="" className="w-12 h-12 rounded-xl object-cover flex-shrink-0" />
                ) : (
                  <div className="w-12 h-12 rounded-xl bg-mint flex items-center justify-center flex-shrink-0">
                    <Camera size={20} className="text-ink" />
                  </div>
                )}
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-ink flex items-center gap-1.5">
                    <Sparkles size={13} className="text-primary-ink" />
                    {scanning ? 'Reading the photo…' : 'Scan the box or pack'}
                  </div>
                  <div className="text-xs text-ink/40">Optional — Kare fills in what it can read</div>
                </div>
                {scanning && <Loader2 size={16} className="animate-spin text-primary-ink flex-shrink-0 ml-auto" />}
              </button>

              {scanError && (
                <p className="text-xs text-red-600 flex items-center gap-1.5"><CircleAlert size={13} /> {scanError}</p>
              )}
              {scanResult && !scanning && (
                <div className="rounded-2xl bg-sand/40 p-4 text-xs text-ink/60 space-y-1.5">
                  {scanResult.structured_findings.drug_name ? (
                    <>
                      {scanResult.structured_findings.common_use && (
                        <p><span className="font-semibold text-ink">Typically used for:</span> {scanResult.structured_findings.common_use}</p>
                      )}
                      {scanResult.structured_findings.generic_name && (
                        <p><span className="font-semibold text-ink">Active ingredient:</span> {scanResult.structured_findings.generic_name}</p>
                      )}
                    </>
                  ) : (
                    <p>Couldn't make out a name or strength from that photo — go ahead and type it in below.</p>
                  )}
                  {scanResult.structured_findings.warnings && (
                    <p className="text-primary-ink/80">{scanResult.structured_findings.warnings}</p>
                  )}
                  <p className="text-ink/35 pt-1">{scanResult.confidence_note} Check the fields below before saving.</p>
                </div>
              )}

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
      </AnimatePresence>
    </motion.div>
  );
};

export default Medications;
