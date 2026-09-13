import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { Save, Edit2, Loader2 } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { patient as patientApi } from '../services/api';
import type { PatientProfile } from '../types';

const Row = ({ label, value }: { label: string; value?: string | number | null }) => (
  <div className="flex items-center gap-6 py-4 border-b border-ink/8 last:border-0">
    <div className="text-xs font-semibold text-ink/40 w-40 flex-shrink-0">{label}</div>
    <div className="text-sm text-ink/80">{value ?? '—'}</div>
  </div>
);

const field = 'w-full input-field text-sm';

const Profile = () => {
  const user = useAuthStore((s) => s.user);
  const [p, setP] = useState<PatientProfile | null>(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<PatientProfile>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => { patientApi.get().then((d) => { setP(d); setForm(d); }).catch(() => {}); }, []);

  const save = async () => {
    setSaving(true);
    try {
      const updated = await patientApi.update({
        date_of_birth: form.date_of_birth, gender: form.gender, phone_number: form.phone_number,
        state: form.state, blood_group: form.blood_group, height_cm: form.height_cm ? +form.height_cm : undefined,
        weight_kg: form.weight_kg ? +form.weight_kg : undefined,
        emergency_contact_name: form.emergency_contact_name, emergency_contact_phone: form.emergency_contact_phone,
      });
      setP(updated); setForm(updated); setEditing(false);
    } finally { setSaving(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-2xl mx-auto space-y-8 p-6 md:p-8 pb-24">
      <div className="flex justify-between items-end">
        <div>
          <div className="text-xs font-semibold text-primary-ink/70 mb-2">Account</div>
          <h1 className="text-4xl">{p?.first_name || 'Profile'}<span className="text-primary-ink">.</span></h1>
        </div>
        <button onClick={() => (editing ? save() : setEditing(true))} disabled={saving}
          className="btn-primary !py-3 !px-5 disabled:opacity-50">
          {saving ? <Loader2 size={16} className="animate-spin" /> : editing ? <Save size={16} /> : <Edit2 size={16} />}
          {editing ? 'Save' : 'Edit'}
        </button>
      </div>

      <div className="card">
        <Row label="Email" value={user?.email} />
        {!editing ? (
          <>
            <Row label="Date of birth" value={p?.date_of_birth} />
            <Row label="Age" value={p?.age} />
            <Row label="Sex" value={p?.gender} />
            <Row label="Phone" value={p?.phone_number} />
            <Row label="State" value={p?.state} />
            <Row label="Blood group" value={p?.blood_group} />
            <Row label="Height / Weight" value={p?.height_cm ? `${p.height_cm} cm / ${p.weight_kg ?? '—'} kg` : '—'} />
            <Row label="BMI" value={p?.bmi} />
            <Row label="Emergency contact" value={p?.emergency_contact_name ? `${p.emergency_contact_name} · ${p.emergency_contact_phone ?? ''}` : '—'} />
            <Row label="Allergies" value={p?.allergies?.join(', ') || 'none reported'} />
          </>
        ) : (
          <div className="space-y-4 pt-4">
            <div className="grid grid-cols-2 gap-4">
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">Date of birth</span>
                <input type="date" value={form.date_of_birth || ''} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} className={field} /></label>
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">Sex</span>
                <select value={form.gender || ''} onChange={(e) => setForm({ ...form, gender: e.target.value })} className={field}>
                  <option value="">—</option><option value="female">Female</option><option value="male">Male</option><option value="other">Other</option>
                </select></label>
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">Phone</span>
                <input value={form.phone_number || ''} onChange={(e) => setForm({ ...form, phone_number: e.target.value })} className={field} /></label>
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">State</span>
                <input value={form.state || ''} onChange={(e) => setForm({ ...form, state: e.target.value })} className={field} /></label>
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">Height (cm)</span>
                <input type="number" value={form.height_cm || ''} onChange={(e) => setForm({ ...form, height_cm: +e.target.value })} className={field} /></label>
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">Weight (kg)</span>
                <input type="number" value={form.weight_kg || ''} onChange={(e) => setForm({ ...form, weight_kg: +e.target.value })} className={field} /></label>
              <label className="space-y-1.5 block"><span className="text-xs font-semibold text-ink/50">Blood group</span>
                <input value={form.blood_group || ''} onChange={(e) => setForm({ ...form, blood_group: e.target.value })} className={field} /></label>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default Profile;
